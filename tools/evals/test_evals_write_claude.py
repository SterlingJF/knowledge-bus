"""Claude's plugin-eval files are generated from the universe slice and never edited by hand."""

import copy
import json
import re

import spec as spec_module
import write_claude
import yaml


def fake_spec():
    rule = {
        "rule": "A question asks for one thing.",
        "why": "A question that asks for two things gets half an answer.",
        "applies_to": ["element.question"],
        "deterministic": {
            "complete": False,
            "checks": [
                {"pattern": r"\?.*\?", "then": "fail"},
                {"terms": ["and how"], "then": "fail"},
                {"words": {"max": 12}, "then": "fail"},
                {"pattern": r"\band\b", "ignore_case": True, "then": "flag"},
            ],
        },
        "decision": {
            "ask": "Does it need two answers?",
            "type": "yes-no",
            "fail_when": "yes",
        },
        "judgment": {"pass": "PASS if one answer.", "fail": "FAIL if two."},
        "examples": [
            {
                "text": "Who, and how?",
                "verdict": "fail",
                "note": "It asks for a group and a method.",
                "subject": "element.question",
                "context": {"id": "segments"},
            },
            {"text": "Who and why?", "verdict": "fail", "note": "It asks two things."},
            {"text": "Who?", "verdict": "pass", "note": "It asks one thing."},
            {"text": "Who is served first?", "verdict": "pass", "note": "One answer."},
        ],
    }
    universe = {
        "subjects": {"element.question": "elements[].question"},
        "cases": {
            "default": {"skill": "kb-evolve", "ask": "Improve this text."},
            "element.question": {
                "skill": "kb-uncover-question",
                "ask": "Tighten this question. Reply with it only.",
            },
        },
        "rules": {"one-job": rule},
    }
    return spec_module.Spec(universe=universe, skills={}, folder=None)


def front(text):
    _, header, body = text.split("---", 2)
    return yaml.safe_load(header), body.strip()


def test_each_rule_becomes_one_case_from_its_first_failing_example():
    files, approximations = write_claude.render(fake_spec())
    assert sorted(files) == [
        ".markdownlint-cli2.jsonc",
        "README.md",
        "universe/one-job/graders/one-job-check-1.md",
        "universe/one-job/graders/one-job-check-2.md",
        "universe/one-job/graders/one-job-check-3.md",
        "universe/one-job/graders/one-job-decision.md",
        "universe/one-job/graders/one-job-judgment.md",
        "universe/one-job/graders/skill-fired.md",
        "universe/one-job/prompt.md",
    ]
    case = "universe/one-job"
    fields, body = front(files[f"{case}/prompt.md"])
    assert fields["name"] == "one-job"
    assert fields["description"] == "Improve a text that fails one-job."
    assert fields["tags"] == ["universe", "one-job"]
    assert (
        body
        == "Tighten this question. Reply with it only.\n\nid: segments\n\nWho, and how?"
    )
    regex, _ = front(files[f"{case}/graders/one-job-check-1.md"])
    assert regex == {"type": "regex", "pattern": r"\?.*\?", "match": "not_contains"}
    terms, _ = front(files[f"{case}/graders/one-job-check-2.md"])
    assert (
        terms["pattern"] == r"(?<![\w'’-])(?:and how)(?![\w'’-])"
        and terms["flags"] == "i"
    )
    llm, criteria = front(files[f"{case}/graders/one-job-judgment.md"])
    assert llm == {"type": "llm", "focus": "last_message"}
    assert criteria == "PASS if one answer.\nFAIL if two."
    skill, _ = front(files[f"{case}/graders/skill-fired.md"])
    assert skill["tool"] == "Skill" and "kb-uncover-question" in skill["input_match"]
    assert (
        "Flag checks only nominate cases for a model tier, so they have no grader: one-job."
        in approximations
    )
    assert any(a.startswith("Typed decisions") for a in approximations)


def test_the_word_cap_regex_matches_only_beyond_the_cap():
    import re

    pattern = write_claude.word_cap(3)
    assert not re.search(pattern, "Who is served?")
    assert re.search(pattern, "Who exactly is served?")


def test_check_reports_drift_without_touching_runner_folders(tmp_path):
    files, _ = write_claude.render(fake_spec())
    write_claude.write(tmp_path, files)
    (tmp_path / "results").mkdir()
    (tmp_path / "results" / "aggregate-result.json").write_text("{}")
    assert write_claude.drift(tmp_path, files) == []
    (tmp_path / "README.md").write_text("edited")
    (tmp_path / "universe" / "stale").mkdir()
    (tmp_path / "universe" / "stale" / "prompt.md").write_text("old")
    assert write_claude.drift(tmp_path, files) == [
        "changed: README.md",
        "unexpected: universe/stale/prompt.md",
    ]
    write_claude.write(tmp_path, files)
    assert write_claude.drift(tmp_path, files) == []
    assert (tmp_path / "results" / "aggregate-result.json").exists()


def test_the_repository_files_are_current():
    files, _ = write_claude.render(spec_module.load())
    assert write_claude.drift(write_claude.OUT, files) == []


def set_spec():
    entries = ["core: Who sings?", "situational: Which singers perform?"]
    examples = [
        {
            "text": "Which singers perform?",
            "verdict": verdict,
            "note": "n",
            "subject": "artifact.composition",
            "context": {
                "enablement": "action: plan; actor: director",
                "strength": "situational",
                "set": entries,
                "probes": ["Tenors."],
            },
        }
        for verdict in ("fail", "fail", "pass", "pass")
    ]
    judged = {
        "rule": "Strength follows the action.",
        "applies_to": ["artifact.composition"],
        "scope": "set",
        "judgment": {"pass": "PASS if right.", "fail": "FAIL if wrong."},
        "examples": examples,
    }
    sorted_ = {
        "rule": "Knowledge is filed under its question.",
        "applies_to": ["artifact.composition"],
        "scope": "set",
        "sort": {"ask": "Which?", "write": "Write two."},
        "examples": examples,
    }
    universe = {
        "subjects": {"artifact.composition": "artifacts[].composition"},
        "cases": {"default": {"skill": "kb-evolve", "ask": "Improve this text."}},
        "rules": {"strength": judged, "sorts": sorted_},
    }
    return spec_module.Spec(universe=universe, skills={}, folder=None)


def test_a_set_rule_case_shows_the_set_and_asks_for_a_member_that_reads_clearly_in_it():
    files, approximations = write_claude.render(set_spec())
    assert sorted(f for f in files if f.startswith("universe/")) == [
        "universe/strength/graders/skill-fired.md",
        "universe/strength/graders/strength-judgment.md",
        "universe/strength/prompt.md",
    ]
    _, body = front(files["universe/strength/prompt.md"])
    assert body == (
        "Improve this text.\n\n"
        "The whole set it belongs to:\n\n"
        "1. core: Who sings?\n"
        "2. situational: Which singers perform?\n\n"
        "enablement: action: plan; actor: director\n"
        "strength: situational\n\n"
        "Improve item 2 so it reads clearly within the set. Item 2:\n\n"
        "Which singers perform?"
    )
    _, criteria = front(files["universe/strength/graders/strength-judgment.md"])
    assert criteria.startswith(
        "The reply is a new version of item 2 in this set:\n\n1. core: Who sings?\n"
    )
    assert criteria.endswith("PASS if right.\nFAIL if wrong.")
    assert "Sort checks are graded by the neutral runner only: sorts." in approximations
    assert "Sort checks are graded" in files["README.md"]


LIST_ITEM = re.compile(r"^(?:[-*+]|\d+\.) ")


def _lists_not_set_off(body):
    """Lines where a list touches a line outside it (markdownlint MD032, blanks-around-lists)."""
    lines = body.split("\n")
    found = []
    for n, line in enumerate(lines):
        if not LIST_ITEM.match(line):
            continue
        before = lines[n - 1] if n else ""
        after = lines[n + 1] if n + 1 < len(lines) else ""
        if before.strip() and not LIST_ITEM.match(before):
            found.append(f"no blank line before: {line}")
        if after.strip() and not LIST_ITEM.match(after):
            found.append(f"no blank line after: {line}")
    return found


def decision_spec(block):
    spec = fake_spec()
    universe = copy.deepcopy(spec.universe)
    universe["rules"]["one-job"]["decision"] = block
    return spec_module.Spec(universe=universe, skills={}, folder=None)


def test_every_generated_list_is_set_off_by_blank_lines():
    specs = [
        fake_spec(),
        set_spec(),
        decision_spec(
            {
                "ask": "Which fits best?",
                "type": "choice",
                "criteria": {"one": "It asks one thing.", "two": "It asks two."},
                "fail_when": ["two"],
            }
        ),
        decision_spec(
            {
                "ask": "How focused is it?",
                "type": "score",
                "levels": ["Scattered.", "Mixed.", "Focused."],
                "fail_when": {"below": 2},
            }
        ),
        spec_module.load(),
    ]
    found = []
    for spec in specs:
        files, _ = write_claude.render(spec)
        for name, text in files.items():
            if not name.endswith(".md"):
                continue
            body = front(text)[1] if text.startswith("---") else text
            found += [f"{name}: {line}" for line in _lists_not_set_off(body)]
    assert found == []


def test_case_bodies_stay_verbatim_so_the_folder_waives_only_the_first_line_heading_rule():
    files, _ = write_claude.render(fake_spec())
    _, body = front(files["universe/one-job/prompt.md"])
    assert body.startswith("Tighten this question.")
    waiver = "\n".join(
        line
        for line in files[".markdownlint-cli2.jsonc"].splitlines()
        if not line.lstrip().startswith("//")
    )
    assert json.loads(waiver) == {"config": {"MD041": False}}


def test_recognise_rules_are_listed_as_not_carried():
    spec = set_spec()
    rule = spec.universe["rules"].pop("sorts")
    del rule["sort"]
    rule["recognise"] = {"ask": "Which fits?", "value_share": 0.75, "frame_share": 0.9}
    spec.universe["rules"]["recognised"] = rule
    files, approximations = write_claude.render(spec)
    assert (
        "Recognition checks are graded by the neutral runner only: recognised."
        in approximations
    )
    assert not any(path.startswith("universe/recognised/") for path in files)
