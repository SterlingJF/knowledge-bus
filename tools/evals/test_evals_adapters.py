"""Adapters translate neutral tier blocks to vendor requests and back, without network calls here."""

import json
import os
import sys
import time

import adapters
import tiers

YES_NO = {"ask": "Does it need two answers?", "type": "yes-no", "fail_when": "yes"}
SCORE = {
    "ask": "How specific is the main noun?",
    "type": "score",
    "levels": ["placeholder", "generic", "domain term"],
    "fail_when": {"below": 2},
}
JUDGED = {
    "rule": "A question asks for one thing.",
    "judgment": {"pass": "PASS if one.", "fail": "FAIL if two."},
}


def case(rule, text, rule_id="r", context=None):
    return tiers.Case(
        rule_id, rule, "element.question", "elements[x].question", text, context or {}
    )


def test_one_request_per_text_carries_every_question_about_it():
    sent = []

    def post(body):
        sent.append(body)
        answers = {}
        for key, q in body["questions"].items():
            if q["type"] == "noul":
                answers[key] = {"type": "noul", "noul": 0.9}
            else:
                answers[key] = {
                    "type": "score",
                    "score": 0.9,
                    "confidence": 0.8,
                    "legend": {},
                    "probabilities": {},
                }
        return {
            "model": "jev-1.13.0",
            "answers": answers,
            "usage": {"input_tokens": 10, "output_tokens": 2},
        }

    jev = adapters.Jev("key", post=post)
    outcomes = jev(
        [
            case({"decision": YES_NO}, "Who, and how?", "one-job"),
            case({"decision": SCORE}, "Who, and how?", "precise"),
            case({"decision": YES_NO}, "Who?", "one-job"),
        ]
    )
    assert len(sent) == 2
    assert sorted(len(b["questions"]) for b in sent) == [1, 2]
    assert [o.verdict for o in outcomes] == ["fail", "fail", "fail"]
    assert jev.version == "jev-1.13.0" and jev.tokens == 24


def test_the_uncertain_middle_stays_undecided():
    def post(body):
        return {
            "answers": {k: {"type": "noul", "noul": 0.64} for k in body["questions"]}
        }

    (outcome,) = adapters.Jev("key", post=post)(
        [case({"decision": YES_NO}, "Who exactly is served, grouped how?")]
    )
    assert outcome.verdict == "undecided"
    assert outcome.detail["noul"] == 0.64


def test_context_moves_the_text_into_named_state():
    question = adapters.Jev.question(
        case({"decision": YES_NO}, "act", context={"id": "lean-canvas"})
    )
    assert question["instructions"].endswith("The text to judge is `text`.")
    assert adapters._state(case({}, "act", context={"id": "lean-canvas"})) == {
        "text": "act",
        "id": "lean-canvas",
    }


def test_the_owner_turns_either_side_reach_the_judges_but_not_jev():
    turns = {
        "owner turn before": "Explain it.",
        "owner turn after": "The bookings one.",
    }
    bare = case({"decision": YES_NO}, "Which one do you mean?", context=turns)
    assert adapters._state(bare) == "Which one do you mean?"
    assert adapters.Jev.question(bare)["instructions"] == YES_NO["ask"]
    filed = case({}, "Thursdays.", context={"question": "When?", **turns})
    assert adapters._state(filed) == {"text": "Thursdays.", "question": "When?"}
    judged = case(JUDGED, "Which one do you mean?", context=turns)
    assert json.dumps(turns, ensure_ascii=False) in adapters.Judge.prompt([judged])


def test_low_confidence_scores_stay_undecided_and_low_levels_fail():
    jev = adapters.Jev("key")
    sure_low = {"type": "score", "score": 0.9, "confidence": 0.8}
    unsure = {"type": "score", "score": 0.9, "confidence": 0.4}
    sure_high = {"type": "score", "score": 1.8, "confidence": 0.9}
    c = case({"decision": SCORE}, "thing")
    assert [jev.read(c, a).verdict for a in (sure_low, unsure, sure_high)] == [
        "fail",
        "undecided",
        "pass",
    ]


def test_the_judge_batches_by_rule_and_maps_unknown_to_undecided():
    prompts = []

    def call(prompt, model):
        prompts.append(prompt)
        count = prompt.count("\n1. ") + prompt.count("\n2. ")
        verdicts = [{"item": 1, "verdict": "fail", "critique": "two jobs"}]
        if count == 2:
            verdicts.append({"item": 2, "verdict": "unknown", "critique": "unclear"})
        return {
            "structured_output": {"verdicts": verdicts},
            "total_cost_usd": 0.01,
            "modelUsage": {model: {}},
        }

    judge = adapters.Judge(models=("claude-x",), call=call)
    outcomes = judge(
        [
            case(JUDGED, "Who, and how?", "one-job"),
            case(JUDGED, "Who?", "one-job"),
            case(dict(JUDGED, rule="Names its subject."), "It works.", "names"),
        ]
    )
    assert len(prompts) == 2
    assert [o.verdict for o in outcomes] == ["fail", "undecided", "fail"]
    assert outcomes[0].detail["critique"] == "two jobs"
    assert judge.version == "claude-x" and round(judge.cost, 2) == 0.02


def test_a_panel_settles_only_when_every_judge_agrees():
    said = {"a": ["fail", "pass", "fail"], "b": ["fail", "fail", "unknown"]}

    def call(prompt, model):
        verdicts = [
            {"item": n, "verdict": v, "critique": f"{model} says {v}"}
            for n, v in enumerate(said[model], 1)
        ]
        return {
            "structured_output": {"verdicts": verdicts},
            "total_cost_usd": 0.01,
            "modelUsage": {model: {}},
        }

    judge = adapters.Judge(models=("a", "b"), call=call)
    outcomes = judge(
        [case(JUDGED, t, "one-job") for t in ("Who, and how?", "Who?", "Why?")]
    )
    assert [o.verdict for o in outcomes] == ["fail", "undecided", "undecided"]
    assert outcomes[1].detail["critique"] == "a: a says pass | b: b says fail"
    assert outcomes[1].detail["votes"] == {
        "a": {"verdict": "pass", "critique": "a says pass"},
        "b": {"verdict": "fail", "critique": "b says fail"},
    }
    assert outcomes[2].detail["votes"]["b"]["verdict"] == "unknown"
    assert judge.version == "a+b" and round(judge.cost, 2) == 0.02


def test_the_judge_prompt_states_the_rule_its_reason_and_both_criteria():
    rule = dict(JUDGED, why="A question with two asks gets half an answer.")
    prompt = adapters.Judge.prompt([case(rule, "Who?", context={"id": "segments"})])
    assert prompt.splitlines()[:4] == [
        "Rule: A question asks for one thing.",
        "Why it matters: A question with two asks gets half an answer.",
        "PASS if one.",
        "FAIL if two.",
    ]
    assert '1. "Who?"' in prompt and '"id": "segments"' in prompt


def test_a_failed_judge_call_is_retried_then_left_undecided():
    tries = {"a": 0, "b": 0}

    def call(prompt, model):
        tries[model] += 1
        if model == "b" or tries[model] < 3:
            raise RuntimeError("judge call failed: overloaded")
        return {
            "structured_output": {
                "verdicts": [{"item": 1, "verdict": "fail", "critique": "two"}]
            },
            "modelUsage": {model: {}},
        }

    judge = adapters.Judge(models=("a",), call=call, sleep=lambda s: None)
    (outcome,) = judge([case(JUDGED, "Who, and how?", "one-job")])
    assert outcome.verdict == "fail" and tries["a"] == 3

    judge = adapters.Judge(models=("a", "b"), call=call, sleep=lambda s: None)
    (outcome,) = judge([case(JUDGED, "Who, and how?", "one-job")])
    assert outcome.verdict == "undecided"
    assert "b call failed" in outcome.detail["critique"]
    assert judge.failures == 1


SET_RULE = {
    "rule": "Each question reads clearly within its set.",
    "scope": "set",
    "judgment": {"pass": "PASS if clear.", "fail": "FAIL if not."},
}


def member(text, members, rule_id="distinct", **context):
    return case(SET_RULE, text, rule_id, {"set": members, **context})


def test_a_set_prompt_shows_the_set_once_then_each_item_with_its_strength():
    entries = ["core: Who sings?", "situational: Which hall?"]
    shared = {
        "artifact": "concert-plan",
        "enablement": "action: plan; actor: director",
    }
    prompt = adapters.Judge.prompt(
        [
            member("Who sings?", entries, id="roster", strength="core", **shared),
            member(
                "Which hall?", entries, id="venue", strength="situational", **shared
            ),
        ]
    )
    lines = prompt.splitlines()
    assert lines[:3] == [
        "Rule: Each question reads clearly within its set.",
        "PASS if clear.",
        "FAIL if not.",
    ]
    assert prompt.count("core: Who sings?") == 1
    at = lines.index("The whole set (2 items), for reference:")
    assert lines[at + 1 : at + 3] == [
        '1. "core: Who sings?"',
        '2. "situational: Which hall?"',
    ]
    assert "Artifact enablement: action: plan; actor: director" in lines
    assert prompt.count("action: plan") == 1
    at = lines.index("Items to judge, each as a member of the set above:")
    assert lines[at + 1 : at + 3] == [
        'Item 1: "Who sings?" (strength: core)',
        'Item 2: "Which hall?" (strength: situational)',
    ]
    assert "name that item by its text" in prompt
    assert "concert-plan" not in prompt and "roster" not in prompt
    assert prompt.endswith("Return one verdict for each of the 2 items.")


def test_a_set_prompt_without_strengths_lists_bare_items():
    questions = ["Who sings?", "Which hall?"]
    prompt = adapters.Judge.prompt([member("Which hall?", questions)])
    assert 'Item 1: "Which hall?"' in prompt.splitlines()
    assert "strength" not in prompt


def test_the_judge_never_mixes_two_sets_in_one_prompt():
    prompts = []

    def call(prompt, model):
        prompts.append(prompt)
        count = prompt.count("\nItem ")
        verdicts = [
            {"item": n, "verdict": "pass", "critique": "clear"}
            for n in range(1, count + 1)
        ]
        return {"structured_output": {"verdicts": verdicts}, "total_cost_usd": 0.0}

    one, two = ["Who sings?", "Which hall?"], ["Who pays?", "Which bank?"]
    judge = adapters.Judge(models=("a",), call=call, batch=20)
    outcomes = judge(
        [
            member("Who sings?", one),
            member("Who pays?", two),
            member("Which hall?", one),
            member("Which bank?", two, enablement="action: pay"),
        ]
    )
    assert len(prompts) == 3
    assert all(o.verdict == "pass" for o in outcomes)
    assert any("Who sings?" in p and "Which hall?" in p for p in prompts)
    assert not any("Who sings?" in p and "Who pays?" in p for p in prompts)


def test_claude_models_write_validate_and_file_with_structured_output():
    calls = []
    replies = {
        "passages": {"passages": ["Tenors open.", "Basses close."]},
        "answers": {
            "answers": [
                {"passage": 2, "answers": False},
                {"passage": 1, "answers": True},
            ]
        },
        "filings": {
            "filings": [{"passage": 1, "question": 2}, {"passage": 2, "question": 0}]
        },
    }

    def call(prompt, model, schema, system):
        calls.append((prompt, model, schema, system))
        (key,) = schema["required"]
        return {"structured_output": replies[key], "total_cost_usd": 0.5}

    models = adapters.Models(call=call)
    assert models.write("w", "Who sings?", "Write two.") == [
        "Tenors open.",
        "Basses close.",
    ]
    assert calls[0][0] == "Write two.\n\nQuestion: Who sings?"
    assert models.answers("v", "Who sings?", ["Tenors open.", "Basses close."]) == [
        True,
        False,
    ]
    assert "Which hall?" not in calls[1][0]
    assert models.file("f", ["Who sings?", "Which hall?"], ["A", "B"], "Which?") == [
        2,
        0,
    ]
    prompt = calls[2][0]
    assert prompt.startswith("Which?") and '2. "Which hall?"' in prompt
    assert [c[1] for c in calls] == ["w", "v", "f"] and models.cost == 1.5


def test_a_recognition_reader_is_asked_which_option_fits_the_situation():
    calls = []

    def call(prompt, model, schema, system):
        calls.append((prompt, schema, system))
        return {"structured_output": {"option": 2}}

    models = adapters.Models(call=call)
    options = ["Open: Can anyone wander up?", "Ticketed"]
    assert models.recognise("m", options, ["A baker sells flapjacks."], "Which?") == [2]
    ((prompt, schema, system),) = calls
    assert prompt == (
        'Which?\n\nOptions:\n1. "Open: Can anyone wander up?"\n2. "Ticketed"\n\n'
        'Situation: "A baker sells flapjacks."\n\n'
        "Give the number of the option that fits the situation, or 0 if none fits."
    )
    assert schema == adapters.OPTION and system == adapters.RECOGNISE_SYSTEM
    for text in (prompt, system):
        assert "question it answers" not in text and "passage" not in text.lower()


def test_judge_costs_add_up_when_its_calls_run_in_parallel():
    class Slow(float):
        """A reported cost that takes a moment to add, as a busy thread might."""

        def __radd__(self, other):
            time.sleep(0.002)
            return float(other) + float(self)

    def call(prompt, model):
        verdicts = [{"item": 1, "verdict": "pass", "critique": "ok"}]
        return {"structured_output": {"verdicts": verdicts}, "total_cost_usd": Slow(1)}

    judge = adapters.Judge(models=("a", "b"), batch=1, workers=8, call=call)
    judge([case(JUDGED, f"Who is {n}?", f"rule-{n}") for n in range(20)])
    assert judge.cost == 40


def test_a_filing_with_a_passage_missing_is_a_failed_call():
    def call(prompt, model, schema, system):
        return {"structured_output": {"filings": [{"passage": 1, "question": 1}]}}

    models = adapters.Models(call=call, sleep=lambda s: None)
    try:
        models.file("f", ["Who?"], ["A", "B"], "Which?")
    except RuntimeError as error:
        assert "no filing for passage 2" in str(error)
    else:
        raise AssertionError("a missing filing must fail the call")
    assert models.failures == 1


def test_the_decision_filer_asks_one_choice_per_passage_and_marks_low_confidence():
    sent = []

    def post(body):
        sent.append(body)
        sure = body["state"] == "Tenors open."
        return {
            "model": "jev-1.13.0",
            "answers": {
                "q": {
                    "type": "choice",
                    "choice": "2",
                    "confidence": 0.9 if sure else 0.4,
                }
            },
            "usage": {"input_tokens": 3},
        }

    choice = adapters.JevChoice("key", post=post)
    assert choice.file(["Who?", "Which hall?"], ["Tenors open.", "B"], "Which?") == [
        2,
        "unsure",
    ]
    assert len(sent) == 2
    assert sent[0]["questions"]["q"] == {
        "type": "choice",
        "instructions": "Which?",
        "criteria": {"1": "Who?", "2": "Which hall?"},
    }
    assert choice.version == "jev-1.13.0" and choice.tokens == 6


def test_the_writer_and_the_validity_check_read_the_question_within_the_universe_scope():
    calls = []

    def call(prompt, model, schema, system):
        calls.append(prompt)
        (key,) = schema["required"]
        out = {
            "passages": ["Tenors open."],
            "answers": [{"passage": 1, "answers": True}],
        }
        return {"structured_output": {key: out[key]}}

    models = adapters.Models(call=call)
    models.write("w", "Who sings?", "Write two.", scope="Scope: choirs.")
    models.answers("v", "Who sings?", ["Tenors open."], scope="Scope: choirs.")
    assert calls[0] == "Scope: choirs.\n\nWrite two.\n\nQuestion: Who sings?"
    assert calls[1].startswith("Scope: choirs.\n\nQuestion: ")


def test_spend_counts_dollars_or_tokens_as_reported_and_is_none_otherwise():
    replies = iter(
        [
            {"structured_output": {"passages": ["A."]}, "total_cost_usd": 0.5},
            {"structured_output": {"passages": ["B."]}, "tokens": 120},
        ]
    )
    models = adapters.Models(call=lambda *args: next(replies))
    assert models.cost is None and models.tokens is None
    models.write("m", "Who?", "Write one.")
    assert models.cost == 0.5 and models.tokens is None
    models.write("codex:m", "Who?", "Write one.")
    assert models.cost == 0.5 and models.tokens == 120


def test_a_codex_model_goes_to_the_codex_cli_and_any_other_to_the_claude_cli(
    monkeypatch,
):
    calls = []
    for name in ("claude_cli", "codex_cli"):
        monkeypatch.setattr(
            adapters, name, lambda *args, name=name: calls.append((name, *args)) or {}
        )
    adapters.model_call("p", "codex:gpt-x", {"type": "object"}, "s")
    adapters.model_call("p", "claude-x", {"type": "object"}, "s")
    assert calls == [
        ("codex_cli", "p", "gpt-x", {"type": "object"}, "s"),
        ("claude_cli", "p", "claude-x", {"type": "object"}, "s"),
    ]


def test_the_default_judge_and_models_route_through_model_call(monkeypatch):
    seen = []

    def call(prompt, model, schema, system):
        seen.append((model, schema["required"]))
        if schema is adapters.VERDICTS:
            return {
                "structured_output": {
                    "verdicts": [{"item": 1, "verdict": "pass", "critique": "ok"}]
                }
            }
        return {"structured_output": {"passages": ["A."]}}

    monkeypatch.setattr(adapters, "model_call", call)
    adapters.Judge(models=("codex:a",))([case(JUDGED, "Who?")])
    adapters.Models().write("codex:b", "Who?", "Write one.")
    assert seen == [("codex:a", ["verdicts"]), ("codex:b", ["passages"])]


def test_every_schema_suits_strict_structured_output():
    """Strict mode wants every object closed and every property required."""

    def objects(node):
        if isinstance(node, dict):
            if node.get("type") == "object":
                yield node
            for child in node.values():
                yield from objects(child)

    for schema in (
        adapters.VERDICTS,
        adapters.PASSAGES,
        adapters.ANSWERS,
        adapters.FILINGS,
        adapters.OPTION,
    ):
        for node in objects(schema):
            assert node["additionalProperties"] is False
            assert sorted(node["required"]) == sorted(node["properties"])


FAKE_CODEX = """#!{python}
import json, os, sys
args = sys.argv[1:]
log = {{"args": args, "cwd": os.getcwd(), "files": os.listdir("."), "stdin": sys.stdin.read()}}
log["schema"] = json.load(open(args[args.index("--output-schema") + 1]))
json.dump(log, open(os.environ["FAKE_CODEX_LOG"], "w"))
if os.environ.get("FAKE_CODEX_FAIL"):
    print(json.dumps({{"type": "turn.failed", "error": {{"message": "usage limit reached"}}}}))
    sys.exit(1)
open(args[args.index("-o") + 1], "w").write(os.environ["FAKE_CODEX_REPLY"])
print(json.dumps({{"type": "thread.started", "thread_id": "t"}}))
usage = os.environ.get("FAKE_CODEX_USAGE")
if usage:
    print(json.dumps({{"type": "turn.completed", "usage": json.loads(usage)}}))
"""


def fake_codex(tmp_path, monkeypatch, reply, usage=None, fail=False):
    """A codex executable on PATH that logs how it was called and answers `reply`."""
    folder = tmp_path / "bin"
    folder.mkdir()
    script = folder / "codex"
    script.write_text(FAKE_CODEX.format(python=sys.executable))
    script.chmod(0o755)
    monkeypatch.setenv("PATH", f"{folder}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_CODEX_LOG", str(tmp_path / "log.json"))
    monkeypatch.setenv("FAKE_CODEX_REPLY", reply)
    if usage:
        monkeypatch.setenv("FAKE_CODEX_USAGE", json.dumps(usage))
    if fail:
        monkeypatch.setenv("FAKE_CODEX_FAIL", "1")
    return tmp_path / "log.json"


def test_the_codex_cli_runs_isolated_and_reads_its_last_message(tmp_path, monkeypatch):
    log = fake_codex(
        tmp_path,
        monkeypatch,
        json.dumps({"passages": ["Tenors open."]}),
        usage={"input_tokens": 100, "cached_input_tokens": 80, "output_tokens": 20},
    )
    reply = adapters.codex_cli("-Write one.", "gpt-x", adapters.PASSAGES, "Be brief.")
    assert reply == {"structured_output": {"passages": ["Tenors open."]}, "tokens": 120}
    called = json.loads(log.read_text())
    args = called["args"]
    for flag in (
        "exec", "--ephemeral", "--ignore-user-config", "--ignore-rules",
        "--skip-git-repo-check", "--json",
    ):  # fmt: skip
        assert flag in args
    assert args[0] == "exec" and args[-1] == "-"
    assert args[args.index("-m") + 1] == "gpt-x"
    assert args[args.index("-s") + 1] == "read-only"
    folder = args[args.index("-C") + 1]
    assert os.path.realpath(folder) == called["cwd"] and called["files"] == []
    assert "project_doc_max_bytes=0" in args
    assert 'developer_instructions="Be brief."' in args
    assert args[args.index("skills.include_instructions=false") - 1] == "-c"
    assert called["schema"] == adapters.PASSAGES
    assert called["stdin"] == "-Write one."
    assert disabled(args) == FEATURES_OFF


FEATURES_OFF = {
    "apps", "browser_use", "computer_use", "hooks", "image_generation", "multi_agent",
    "plugins",
}  # fmt: skip


def disabled(args):
    """The features a codex command line switches off."""
    return {args[n + 1] for n, a in enumerate(args) if a == "--disable"}


def test_a_codex_reply_without_usage_records_no_tokens(tmp_path, monkeypatch):
    fake_codex(tmp_path, monkeypatch, json.dumps({"passages": []}))
    assert adapters.codex_cli("p", "m", adapters.PASSAGES, "s") == {
        "structured_output": {"passages": []}
    }


def test_a_failed_or_unreadable_codex_call_raises(tmp_path, monkeypatch):
    fake_codex(tmp_path, monkeypatch, "", fail=True)
    try:
        adapters.codex_cli("p", "m", adapters.PASSAGES, "s")
    except RuntimeError as error:
        assert "usage limit reached" in str(error)
    else:
        raise AssertionError("a failed codex call must raise")
    monkeypatch.delenv("FAKE_CODEX_FAIL")
    monkeypatch.setenv("FAKE_CODEX_REPLY", "not json")
    try:
        adapters.codex_cli("p", "m", adapters.PASSAGES, "s")
    except RuntimeError as error:
        assert "not json" in str(error)
    else:
        raise AssertionError("an unreadable last message must raise")


def test_a_cli_is_needed_only_for_the_models_named(tmp_path, monkeypatch):
    fake_codex(tmp_path, monkeypatch, "{}")
    monkeypatch.setenv("PATH", str(tmp_path / "bin"))
    home = tmp_path / "codex-home"
    (home / "skills" / ".system").mkdir(parents=True)
    monkeypatch.setenv("CODEX_HOME", str(home))
    assert adapters.unavailable(["codex:a", "codex:b"]) is None
    assert adapters.unavailable(["codex:a", "claude-x"]) == (
        "the claude CLI is not on PATH"
    )
    monkeypatch.setenv("PATH", str(tmp_path))
    assert adapters.unavailable(["codex:a"]) == "the codex CLI is not on PATH"


def test_a_codex_home_with_skills_is_accepted_and_one_with_instructions_refused(
    tmp_path, monkeypatch
):
    fake_codex(tmp_path, monkeypatch, "{}")
    home = tmp_path / "codex-home"
    (home / "skills" / "pets").mkdir(parents=True)
    (home / "skills" / "pets" / "SKILL.md").write_text("# pets")
    monkeypatch.setenv("CODEX_HOME", str(home))
    assert adapters.unavailable(["codex:a"]) is None
    (home / "AGENTS.md").write_text("Always answer in French.")
    assert adapters.unavailable(["codex:a"]) == (
        f"the Codex home {home} holds AGENTS.md, which would reach every call; set "
        "CODEX_HOME to a folder holding only a login (CODEX_HOME=<folder> codex login)"
    )
    (home / "AGENTS.md").write_text("")
    assert adapters.unavailable(["codex:a"]) is None


def test_the_claude_agent_is_told_its_shell_in_an_appended_note():
    note = adapters.ClaudeAgent.note
    for rule in adapters.ClaudeAgent.allowed:
        if rule.startswith("Bash("):
            assert rule.removeprefix("Bash(").removesuffix(":*)") in note
    for said in (
        "one simple command at a time",
        "loops",
        "chaining",
        "cd",
        "variables",
    ):
        assert said in note
    assert "does not mean the shell is unavailable" in note
