"""Generate `claude plugin eval` cases from the universe slice, or check that they are current.

    write_claude.py [--check]

Each rule's first failing example becomes one case: the case's skill is asked to fix the text,
and the rule grades the reply. For a set rule the case shows the whole set and asks for a member
that reads clearly within it. Sort checks have no case; the neutral runner grades them. Output
goes to evals/generated/claude/; the runner's own results/ and mocks/ folders are left alone.
"""

import argparse
import sys
from pathlib import Path

import sort
import spec as spec_module
import yaml

OUT = spec_module.EVALS / "generated" / "claude"
KEPT = ("results/", "mocks/")
WORD = r"[\w'’-]"
PLUGIN = "knowledge-bus"


def word_cap(limit):
    """A JavaScript-compatible pattern that matches text with more than `limit` words."""
    return rf"(?:{WORD}+[^\w'’-]+){{{limit}}}{WORD}*\w"


def _markdown(fields, body=""):
    header = yaml.safe_dump(fields, sort_keys=False, allow_unicode=True, width=10**6)
    return f"---\n{header}---\n" + (f"\n{body.strip()}\n" if body else "")


def _graders(rule_id, rule, approximations, within=""):
    graders = {}
    checks = (rule.get("deterministic") or {}).get("checks", [])
    for n, check in enumerate(checks, 1):
        name = f"{rule_id}-check-{n}"
        if check["then"] == "flag":
            approximations.add(("flag", rule_id))
            continue
        if "pattern" in check:
            fields = {"type": "regex", "pattern": check["pattern"]}
            if check.get("ignore_case"):
                fields["flags"] = "i"
        elif "terms" in check:
            alternatives = "|".join(_escape(t) for t in check["terms"])
            fields = {
                "type": "regex",
                "pattern": f"(?<!{WORD})(?:{alternatives})(?!{WORD})",
                "flags": "i",
            }
        elif "max" in check["words"]:
            fields = {"type": "regex", "pattern": word_cap(check["words"]["max"])}
        else:
            approximations.add(("min-words", rule_id))
            continue
        fields["match"] = "not_contains"
        graders[name] = _markdown(fields)
    if "decision" in rule:
        block = rule["decision"]
        approximations.add(("decision", rule_id))
        graders[f"{rule_id}-decision"] = _markdown(
            {"type": "llm", "focus": "last_message"}, _decision_criteria(block)
        )
    if "judgment" in rule:
        criteria = f"{within}{rule['judgment']['pass']}\n{rule['judgment']['fail']}"
        graders[f"{rule_id}-judgment"] = _markdown(
            {"type": "llm", "focus": "last_message"}, criteria
        )
    return graders


def _escape(term):
    return "".join("\\" + c if c in r".^$*+?()[]{}|\/" else c for c in term)


def _decision_criteria(block):
    question = f"Question about the reply: {block['ask']}"
    if block["type"] == "yes-no":
        good = "no" if block["fail_when"] == "yes" else "yes"
        return f"{question}\nPASS if the answer is {good}.\nFAIL if the answer is {block['fail_when']}."
    if block["type"] == "choice":
        options = "\n".join(f"- {k}: {v}" for k, v in block["criteria"].items())
        return f"{question}\nOptions:\n\n{options}\n\nFAIL if the best option is one of: {', '.join(block['fail_when'])}. Otherwise PASS."
    levels = "\n".join(f"{n}. {level}" for n, level in enumerate(block["levels"]))
    return f"{question}\nLevels, worst to best:\n\n{levels}\n\nFAIL if the reply sits below level {block['fail_when']['below']}. Otherwise PASS."


def render(spec):
    """One case per rule: its first failing example, to be fixed by a skill and graded by the rule."""
    universe = spec.universe
    cases = universe.get("cases") or {}
    files, approximations = {}, set()
    for rule_id, rule in universe["rules"].items():
        for check in ("sort", "recognise"):
            if check in rule:
                approximations.add((check, rule_id))
        if not any(t in rule for t in spec_module.TIERS):
            continue
        example = next(e for e in rule["examples"] if e["verdict"] == "fail")
        subject = example.get("subject", "default")
        case = cases.get(subject) or cases["default"]
        folder = f"universe/{rule_id}"
        within = ""
        if rule.get("scope") == "set":
            body, within = _set_case(case["ask"], example)
        else:
            context = "".join(
                f"{k}: {v}\n" for k, v in (example.get("context") or {}).items()
            )
            body = (
                f"{case['ask']}\n\n{context}\n{example['text']}"
                if context
                else f"{case['ask']}\n\n{example['text']}"
            )
        fields = {
            "name": rule_id,
            "description": f"Improve a text that fails {rule_id}.",
            "tags": ["universe", rule_id],
            "max_turns": 10,
            "allowed_tools": ["Read", "Glob", "Grep", "Skill"],
        }
        files[f"{folder}/prompt.md"] = _markdown(fields, body)
        files[f"{folder}/graders/skill-fired.md"] = _markdown(
            {
                "type": "tool_used",
                "tool": "Skill",
                "input_match": rf'"skill"\s*:\s*"(?:[\w-]+:)?{case["skill"]}"',
            }
        )
        for grader, text in _graders(rule_id, rule, approximations, within).items():
            files[f"{folder}/graders/{grader}.md"] = text
    lines = _approximations(approximations)
    files["README.md"] = _readme(lines)
    files[".markdownlint-cli2.jsonc"] = LINT_WAIVER
    return files, lines


def _set_case(ask, example):
    """The prompt body and grader preamble for a member of a set."""
    context = example.get("context") or {}
    members = context["set"]
    at = next(
        n
        for n, entry in enumerate(members, 1)
        if example["text"] in (entry, sort.question(entry))
    )
    listed = "".join(f"{n}. {m}\n" for n, m in enumerate(members, 1))
    shared = "".join(
        f"{k}: {v}\n" for k, v in context.items() if k not in ("set", "probes")
    )
    body = f"{ask}\n\nThe whole set it belongs to:\n\n{listed}\n"
    body += f"{shared}\n" if shared else ""
    body += f"Improve item {at} so it reads clearly within the set. Item {at}:\n\n"
    body += example["text"]
    within = f"The reply is a new version of item {at} in this set:\n\n{listed}\n"
    within += f"{shared}\n" if shared else ""
    return body, within


LINT_WAIVER = """{
  // Generated by tools/evals/write_claude.py. The runner sends each case body verbatim as the
  // prompt or the grader's criteria, and prompt.md front matter refuses unknown keys such as
  // title, so these files cannot open with a heading. Every other rule still applies.
  "config": { "MD041": false }
}
"""

APPROXIMATED = {
    "flag": "Flag checks only nominate cases for a model tier, so they have no grader",
    "decision": "Typed decisions are asked of the case's llm judge instead of a decision model",
    "min-words": "Minimum word counts have no regex grader",
    "sort": "Sort checks are graded by the neutral runner only",
    "recognise": "Recognition checks are graded by the neutral runner only",
}


def _approximations(pairs):
    by_kind = {}
    for kind, rule_id in pairs:
        by_kind.setdefault(kind, []).append(rule_id)
    return [
        f"{APPROXIMATED[k]}: {', '.join(sorted(v))}."
        for k, v in sorted(by_kind.items())
    ]


def _readme(approximations):
    lines = [
        "# Generated: Claude plugin eval cases",
        "",
        "Written by `tools/evals/write_claude.py` from `evals/universe.yaml`. Do not edit; regenerate.",
        "",
        "## What does not carry over",
        "",
    ]
    lines += [f"- {a}" for a in approximations] or ["- Nothing."]
    return "\n".join(lines) + "\n"


def write(folder, files):
    folder = Path(folder)
    for path in _owned(folder):
        if str(path.relative_to(folder)) not in files:
            path.unlink()
    for relative, text in files.items():
        target = folder / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    for path in sorted(folder.rglob("*"), reverse=True):
        if path.is_dir() and not any(path.iterdir()):
            path.rmdir()


def _owned(folder):
    return [
        p
        for p in folder.rglob("*")
        if p.is_file() and not str(p.relative_to(folder)).startswith(KEPT)
    ]


def drift(folder, files):
    folder = Path(folder)
    found = []
    on_disk = (
        {str(p.relative_to(folder)): p for p in _owned(folder)}
        if folder.exists()
        else {}
    )
    for relative in sorted(set(files) | set(on_disk)):
        if relative not in on_disk:
            found.append(f"missing: {relative}")
        elif relative not in files:
            found.append(f"unexpected: {relative}")
        elif on_disk[relative].read_text() != files[relative]:
            found.append(f"changed: {relative}")
    return found


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if the generated files are out of date",
    )
    args = parser.parse_args(argv)
    files, approximations = render(spec_module.load())
    if args.check:
        found = drift(OUT, files)
        for line in found:
            print(line, file=sys.stderr)
        return 1 if found else 0
    write(OUT, files)
    for line in approximations:
        print(f"approximated: {line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
