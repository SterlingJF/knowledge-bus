"""Play the skills scenarios with a scripted owner, then grade the required behaviours.

    play.py [--scenario ID] [--agent claude|codex] [--model M] [--runs N] [--tiers T,...]
            [--judge-model M,...] [--max-turn-usd USD] [--label TEXT] [--out DIR]

For each scenario in evals/skills.yaml, or the one named: copy its fixture to a scratch folder,
start the agent with the prompt, then send each owner reply in order in the same session. Replies
are positional; a turn that ends a reply early without asking or seeking confirmation is marked
possible script drift, a hint for the owner to review that feeds no verdict. Afterwards the
folder is diffed and checked in code: the scenario's skill fired, writes stayed inside
.knowledge-bus/, no Write, Edit or Bash redirect named a path outside the work folder (Claude's
tool calls only; a Codex run reads none), no conforms_to changed, a fixture that validated still
validates with the bundled checker, and nothing loaded beside the skills under test. The required
behaviours are graded with the tiers on the turns, the files written and the transcript; proposed definitions are graded with the universe rules in wording/. A turn's last
message is a question to the owner when its closing request asks one, or when it asks which one
over a list of candidates, and a report otherwise. Questions, reports and files carry the owner
turns either side of them as context for the judges; Jev gets the text alone.

Each scenario runs n times (default n=1, said in the run's notes). The agent and the judges call
paid models. Results go to .evidence/<date>/evals/play-<time>/ (run.json, verdicts.jsonl,
report.md, and per scenario and run: events.jsonl, transcript.json, changes.json, checks.json).
"""

import argparse
import dataclasses
import hashlib
import itertools
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import grade
import spec as spec_module
import tiers
import yaml

ROOT = spec_module.ROOT
SKILLS = ROOT / "skills"
SKILL_NAMES = tuple(sorted(p.parent.name for p in SKILLS.glob("*/SKILL.md")))
KB = ".knowledge-bus/"
CHECKER = SKILLS / "kb-check/runtime/kbp.py"
HANDS_BACK = re.compile(
    r"\?|\b(confirm|go ahead|approve|let me know|tell me|shall i|should i)\b",
    re.IGNORECASE,
)
FENCED = re.compile(r"^\s*(```|~~~).*?(?:^\s*\1[^\n]*$|\Z)", re.MULTILINE | re.DOTALL)
SET_ASIDE = re.compile(r"^\s{0,3}(#{1,6}\s|>).*$", re.MULTILINE)
QUOTED = re.compile(r"`[^`\n]*`|\"[^\"\n]*\"|“[^”\n]*”")
CONFIRM_OR_CHOOSE = re.compile(
    r"(^|[.!:;]\s+)(confirm|approve|choose|pick)\b"
    r"|\b(please|can you|could you|would you|will you|if you|once you|when you)\s+"
    r"(confirm|approve|choose|pick|decide|answer|reply)\b"
    r"|\b(shall|should) i\b"
    r"|\btell me\b[^.]*\b(which|whether)\b"
    r"|\b(say so|let me know|tell me (which|if))\b",
    re.IGNORECASE,
)
LIST_ITEM = re.compile(r"^\s*([-*+]|\d+[.)])\s+")
REDIRECT = re.compile(r"(?<![-=>])>>?\s*[\"']?(/[^\s\"';|&<>()]+)")


def fixture_of(scenario):
    """The scenario's fixture path, "none" for an empty folder, or None while it is still to be
    built (fixture: {needs: ...})."""
    fixture = scenario.get("fixture", "none")
    return None if isinstance(fixture, dict) else fixture


def tree_digest(folder):
    """One digest over every file's path and content in the folder."""
    lines = [f"{path} {digest}" for path, digest in sorted(snapshot(folder).items())]
    return "sha256:" + hashlib.sha256("\n".join(lines).encode()).hexdigest()


def snapshot(folder):
    folder = Path(folder)
    return {
        p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in folder.rglob("*")
        if p.is_file()
    }


def diff(before, after, folder):
    """Created, modified and deleted paths, with the text of what is there now."""
    found = {}
    for path in sorted(set(before) | set(after)):
        if before.get(path) == after.get(path):
            continue
        change = (
            "created"
            if path not in before
            else "deleted"
            if path not in after
            else "modified"
        )
        content = None
        if change != "deleted":
            try:
                content = (Path(folder) / path).read_text()
            except UnicodeDecodeError:
                pass
        found[path] = {"change": change, "content": content}
    return found


def validate(folder):
    """Whether the folder's .knowledge-bus/ passes the bundled checker; None without one."""
    target = Path(folder) / KB
    if not target.is_dir():
        return None
    done = subprocess.run(
        [sys.executable, str(CHECKER), "--validate", str(target)],
        capture_output=True,
        text=True,
        check=False,
    )
    return done.returncode == 0


def universes(folder):
    """{path: document} for each universe file in the folder's .knowledge-bus/."""
    found = {}
    for path in sorted((Path(folder) / KB).glob("**/*.kbp.yaml")):
        try:
            doc = yaml.safe_load(path.read_text())
        except yaml.YAMLError:
            continue
        if isinstance(doc, dict) and isinstance(doc.get("universe"), dict):
            found[path.relative_to(folder).as_posix()] = doc
    return found


def _conforms(docs):
    return {path: doc["universe"].get("conforms_to") for path, doc in docs.items()}


def hands_back(text):
    """Whether a turn gives the owner the turn back: a question, or a request to confirm."""
    return bool(HANDS_BACK.search(text or ""))


def asks_owner(text):
    """Whether a message asks the owner: with headings, quoted lines, code blocks and inline
    quotes set aside, its last paragraph ends with "?" or asks to confirm or choose, or a line
    that is not a list item ends with "?" and a list of candidates follows it (which one?)."""
    kept = QUOTED.sub("", SET_ASIDE.sub("", FENCED.sub("", text or "")))
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", kept) if p.strip()]
    if not paragraphs:
        return False
    last = paragraphs[-1]
    if last.rstrip(" *_)]").endswith("?") or CONFIRM_OR_CHOOSE.search(last):
        return True
    lines = [line for line in kept.splitlines() if line.strip()]
    return any(
        asked.rstrip(" *_)]").endswith("?")
        and not LIST_ITEM.match(asked)
        and LIST_ITEM.match(listed)
        for asked, listed in itertools.pairwise(lines)
    )


def written_outside(turns, work):
    """Paths outside the work folder that a Write or Edit call names, or that a Bash command
    redirects to (> or >>) by absolute path; /dev/ is left out."""
    work, found = Path(work).resolve(), []
    for step in (s for t in turns for s in t.steps if s["kind"] == "tool"):
        if step["name"] in ("Write", "Edit"):
            paths = [str(step["input"].get("file_path") or "")]
        elif step["name"] == "Bash":
            paths = REDIRECT.findall(str(step["input"].get("command") or ""))
        else:
            continue
        found += [
            p
            for p in paths
            if p
            and not p.startswith("/dev/")
            and not (work / p).resolve().is_relative_to(work)
        ]
    return found


def play(scenario, fixture, agent, scratch, validate=validate):
    """Play one scenario in a fresh copy of its fixture; the record of turns, transcript, changes
    and code checks. The fixture itself is never touched."""
    work = (Path(scratch) / "work").resolve()
    if fixture is None:
        work.mkdir(parents=True)
    else:
        shutil.copytree(fixture, work)
    files = sorted(snapshot(work))
    agent.install({n: SKILLS / n for n in SKILL_NAMES}, work, scratch)
    before, docs_before, valid_before = snapshot(work), universes(work), validate(work)
    turns, seen, written_in = [], before, {}
    for n, text in enumerate([scenario["prompt"], *scenario["owner"]]):
        if turns and turns[-1].error:
            break
        turns.append(
            agent.reply(work, turns[0].session, text) if n else agent.start(work, text)
        )
        now = snapshot(work)
        written_in.update(
            {p: n for p in set(seen) | set(now) if seen.get(p) != now.get(p)}
        )
        seen = now
    error = next((f"turn {n}: {t.error}" for n, t in enumerate(turns) if t.error), None)
    changes = diff(before, snapshot(work), work)
    conforms = _conforms(docs_before)
    now = _conforms(universes(work))
    valid_after = validate(work)
    checks = {
        "skill": scenario["skill"],
        "skill fired": agent.fired(turns, scenario["skill"]),
        "writes outside .knowledge-bus": [p for p in changes if not p.startswith(KB)],
        "writes outside the work folder (from tool calls)": written_outside(
            turns, work
        ),
        "conforms_to changed": [p for p, v in conforms.items() if now.get(p) != v],
        "validates": {
            "before": valid_before,
            "after": valid_after,
            "kept": valid_after is True if valid_before else None,
        },
        "loaded beside the skills under test": agent.extra(turns, SKILL_NAMES),
        "possible script drift": [
            n
            for n, turn in enumerate(turns[: len(scenario["owner"])], 1)
            if not hands_back(turn.final)
        ],
        "agent error": error,
    }
    transcript = []
    for n, turn in enumerate(turns):
        said = scenario["prompt"] if n == 0 else scenario["owner"][n - 1]
        transcript.append({"role": "owner", "text": said})
        transcript += [
            {"role": "agent", "text": s["text"]}
            if s["kind"] == "text"
            else {"role": "tool", **{k: v for k, v in s.items() if k != "kind"}}
            for s in turn.steps
        ]
    return {
        "turns": turns,
        "transcript": transcript,
        "changes": changes,
        "checks": checks,
        "fixture files": files,
        "universes": (docs_before, universes(work)),
        "work": work,
        "written in": written_in,
    }


def summary(checks):
    """The code checks as one line for the run's notes; hints are left to hints()."""
    validates = checks["validates"]
    parts = [
        f"skill fired {'yes' if checks['skill fired'] else 'no'}",
        "writes outside .knowledge-bus: "
        + (", ".join(checks["writes outside .knowledge-bus"]) or "none"),
        "writes outside the work folder (from tool calls): "
        + (
            ", ".join(checks["writes outside the work folder (from tool calls)"])
            or "none"
        ),
        "conforms_to changed: " + (", ".join(checks["conforms_to changed"]) or "none"),
        "validates: "
        + (
            "no .knowledge-bus/"
            if validates["before"] is None and validates["after"] is None
            else f"before {validates['before']}, after {validates['after']}"
            + ("" if validates["kept"] is not False else " (broken by the run)")
        ),
        "loaded beside the skills under test: "
        + (", ".join(checks["loaded beside the skills under test"]) or "none"),
    ]
    if checks["agent error"]:
        parts.append(f"agent error: {checks['agent error']}")
    return "; ".join(parts)


def hints(checks):
    """What the code saw for the owner to review: never a finding, and fed to no verdict."""
    drift = checks["possible script drift"]
    if not drift:
        return []
    replies = ", ".join(map(str, drift))
    return [
        f"possible script drift before owner reply {replies} (a hint for review, not a finding)"
    ]


def render(transcript):
    """The transcript as plain lines: who spoke, and each tool with its input and output."""
    lines = []
    for step in transcript:
        if step["role"] in ("owner", "agent"):
            lines.append(f"{step['role'].capitalize()}: {step['text']}")
            continue
        line = f"Tool {step['name']}: {json.dumps(step['input'], ensure_ascii=False)[:300]}"
        if step.get("output"):
            line += f" -> {step['output']}"
        lines.append(line)
    return "\n".join(lines)


def _answers(changes, docs):
    """(answer, question) for each answer record written, where its element's question is
    declared in the after-state."""
    questions = {
        e.get("id"): e.get("question")
        for doc in docs.values()
        for e in doc.get("elements") or []
        if isinstance(e, dict)
    }
    found = []
    for path, change in changes.items():
        if not (path.startswith(KB) and path.endswith("answers.yaml")):
            continue
        try:
            doc = yaml.safe_load(change["content"] or "")
        except yaml.YAMLError:
            continue
        records = doc.get("answers") if isinstance(doc, dict) else doc
        for record in records if isinstance(records, list) else []:
            if not isinstance(record, dict):
                continue
            question = questions.get(record.get("element"))
            if question and isinstance(record.get("answer"), str):
                found.append((record["answer"], question))
    return found


def cases(spec, scenario, record, prefix):
    """(behaviour cases, wording cases, notes) for one played scenario."""
    said = [scenario["prompt"], *scenario["owner"]]

    def around(n):
        """The owner turns just before and just after turn n, for the judges' reference only."""
        before, after = tiers.JUDGES_ONLY
        found = {before: said[n]}
        if n + 1 < len(record["turns"]):
            found[after] = said[n + 1]
        return found

    finals = [(t.final, around(n)) for n, t in enumerate(record["turns"])]
    replies = len(scenario["owner"])
    questions = [f for f in finals[:replies] if asks_owner(f[0])]
    reports = [f for f in finals[:replies] if not asks_owner(f[0])] + finals[replies:][
        -1:
    ]
    written = {
        p: (c["content"], around(record["written in"][p]))
        for p, c in record["changes"].items()
        if c["change"] != "deleted"
        and c["content"] is not None
        and not p.endswith(".kbp.yaml")
    }
    _, after = record["universes"]
    texts = {
        "question-to-owner": questions,
        "report-to-owner": reports,
        "files-written": [(f"Path: {p}\n\n{c}", a) for p, (c, a) in written.items()],
        "transcript": [
            (
                render(record["transcript"]),
                {
                    "owner script": [scenario["prompt"], *scenario["owner"]],
                    "fixture files": record["fixture files"],
                    "files written": sorted(record["changes"]),
                    "code checks": summary(record["checks"]),
                },
            )
        ],
    }
    behaviours, made, notes = spec.skills["behaviours"], [], []
    for name in scenario["required"]:
        rule = behaviours[name]
        if rule.get("grade_with") == "universe":
            continue
        before = len(made)
        for subject in rule["applies_to"]:
            picked = texts[subject]
            if name == "answers-the-question-it-is-filed-under":
                picked = [
                    (a, {"question": q}) for a, q in _answers(record["changes"], after)
                ]
            made += [
                tiers.Case(
                    name, rule, subject, f"{prefix}/{subject}[{n}]", text, context
                )
                for n, (text, context) in enumerate(picked, 1)
            ]
        if len(made) == before:
            notes.append(f"{prefix}: {name} had nothing to grade")
    wording = []
    if "wording-meets-the-bar" in scenario["required"]:
        wording = _wording(spec, record, prefix)
        notes.append(
            f"{prefix}: wording-meets-the-bar graded on proposed definitions only "
            f"({len(wording)} changed texts), not on questions, reports or files"
        )
    return made, wording, notes


def _wording(spec, record, prefix):
    """Universe-rule cases for each definition text the run changed, on rules with a tier."""
    before, after = record["universes"]
    rules = [
        r for r, rule in spec.universe["rules"].items() if set(tiers.TIERS) & set(rule)
    ]
    found = []
    for path, doc in after.items():
        guidance = (record["work"] / path).with_name("type-guidance.kbp.yaml")
        guidance_doc = (
            yaml.safe_load(guidance.read_text()) if guidance.exists() else None
        )
        old = {
            (c.ref, c.text)
            for c in grade.universe_cases(spec, before.get(path), guidance_doc, rules=rules)
        } if path in before else set()  # fmt: skip
        found += [
            dataclasses.replace(c, ref=f"{prefix}/{path}:{c.ref}")
            for c in grade.universe_cases(spec, doc, guidance_doc, rules=rules)
            if (c.ref, c.text) not in old
        ]
    return found


def _save(folder, record):
    folder.mkdir(parents=True, exist_ok=True)
    with open(folder / "events.jsonl", "w") as out:
        for n, turn in enumerate(record["turns"]):
            out.writelines(
                json.dumps({"turn": n, **e}, ensure_ascii=False) + "\n"
                for e in turn.events
            )
    for name, value in (
        ("transcript.json", record["transcript"]),
        ("changes.json", record["changes"]),
        ("checks.json", record["checks"]),
    ):
        (folder / name).write_text(
            json.dumps(value, indent=2, ensure_ascii=False) + "\n"
        )


def _inputs(spec):
    found = {
        f"evals/{name}.yaml": grade._digest(spec.folder / f"{name}.yaml")
        for name in ("skills", "universe")
    }
    found.update(
        {
            f"skills/{n}/SKILL.md": grade._digest(SKILLS / n / "SKILL.md")
            for n in SKILL_NAMES
        }
    )
    found.update(
        {
            f"evals/fixtures/{f.name}": tree_digest(f)
            for f in sorted((spec.folder / "fixtures").iterdir())
            if f.is_dir()
        }
    )
    return found


def main(argv=None):
    import adapters  # vendor code loads only when the runner runs

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--scenario", help="play only this scenario id")
    parser.add_argument("--agent", choices=sorted(adapters.AGENTS), default="claude")
    parser.add_argument(
        "--model",
        help="the agent's model (claude default: claude-opus-5-5; codex: required)",
    )
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--tiers", default=",".join(tiers.TIERS))
    parser.add_argument(
        "--judge-model",
        default="claude-opus-5-5,claude-fable-5-1",
        help="one model, or several separated by commas: a verdict stands only when all "
        "agree; codex:<model> runs through the Codex CLI",
    )
    parser.add_argument(
        "--max-turn-usd", type=float, default=3.0, help="claude: budget per agent turn"
    )
    parser.add_argument(
        "--label", default="", help="a name for the run, kept in run.json"
    )
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    spec = spec_module.load()
    scenarios = spec.skills.get("scenarios") or {}
    if args.scenario and args.scenario not in scenarios:
        sys.exit(f"No scenario {args.scenario} in evals/skills.yaml.")
    if args.agent == "codex" and not args.model:
        sys.exit("Name the Codex model with --model.")
    agent = (
        adapters.ClaudeAgent(args.model or "claude-opus-5-5", budget=args.max_turn_usd)
        if args.agent == "claude"
        else adapters.CodexAgent(args.model)
    )
    problem = agent.unavailable()
    if problem:
        sys.exit(f"The {args.agent} agent cannot run: {problem}.")
    chosen = tuple(t for t in args.tiers.split(",") if t)
    stamp = datetime.now(UTC)
    run = grade.Run(
        id=f"play-{stamp:%Y%m%dT%H%M%S%fZ}",
        kind="skills",
        inputs=_inputs(spec),
        adapters={"agent": f"{agent.name} {agent.version()}, model {agent.model}"},
        tiers=list(chosen),
        label=args.label,
        notes=[
            f"each scenario ran {args.runs} time(s) (n={args.runs}); "
            + "sort and recognise do not run in play"
        ],
    )
    if getattr(agent, "allowed", None):
        run.notes.append(
            "the agent may run without asking: " + ", ".join(agent.allowed)
        )
    if getattr(agent, "note", None):
        run.notes.append("the agent's appended system prompt: " + agent.note)
    if getattr(agent, "env", None):
        run.notes.append(
            "the agent's environment adds: "
            + ", ".join(f"{k}={v}" for k, v in agent.env)
        )
    decide, judge = grade._adapters(chosen, args.judge_model, run)
    out = args.out or ROOT / ".evidence" / f"{stamp:%Y-%m-%d}" / "evals" / run.id
    out.mkdir(parents=True, exist_ok=args.out is not None)
    results, worded = [], []
    for name, scenario in scenarios.items():
        if args.scenario and name != args.scenario:
            continue
        fixture = fixture_of(scenario)
        if fixture is None:
            run.notes.append(f"{name}: not run, its fixture is still to be built")
            continue
        for n in range(1, args.runs + 1):
            prefix = f"{name}/run-{n}"
            with tempfile.TemporaryDirectory(prefix="evals-play-") as scratch:
                record = play(
                    scenario,
                    None if fixture == "none" else ROOT / fixture,
                    agent,
                    scratch,
                    validate=validate,
                )
                _save(out / prefix, record)
                run.notes.append(f"{name} run {n}: {summary(record['checks'])}")
                run.notes += [f"{name} run {n}: {h}" for h in hints(record["checks"])]
                if record["checks"]["agent error"]:
                    run.notes.append(f"{prefix}: not graded, the agent stopped early")
                    continue
                made, wording, notes = cases(spec, scenario, record, prefix)
            run.notes += notes
            only = [t for t in chosen if t in tiers.TIERS]
            results += [
                _shown(r, prefix) for r in tiers.run(made, decide, judge, only=only)
            ]
            worded += tiers.run(wording, decide, judge, only=only)
    run.notes.append(f"agent cost: {grade._spent(agent)}")
    grade._record(run, decide, judge)
    grade.write(out, run, spec, results)
    if worded:
        grade.write(
            out / "wording", dataclasses.replace(run, kind="universe"), spec, worded
        )
    print(out)
    return 0


def _shown(result, prefix):
    """A transcript row names the saved transcript instead of carrying it."""
    if result.case.subject != "transcript":
        return result
    text = f"(transcript: {prefix}/transcript.json)"
    result.case = dataclasses.replace(result.case, text=text)
    return result


if __name__ == "__main__":
    sys.exit(main())
