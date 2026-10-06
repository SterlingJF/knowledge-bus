"""The scenario runner plays a scripted owner against fake agent executables; no model is called."""

import json
import os
import sys
import tomllib
from pathlib import Path

import adapters
import play
import pytest
import spec as spec_module
import tiers

FAKE = """#!{python}
import json, os, sys, uuid
from pathlib import Path

args, stdin = sys.argv[1:], sys.stdin.read()
if args == ["--version"]:
    print("{version}")
    sys.exit(0)
with open(os.environ["FAKE_LOG"], "a") as log:
    log.write(json.dumps({{"args": args, "stdin": stdin, "cwd": os.getcwd(),
        "cache": os.environ.get("KNOWLEDGE_BUS_CACHE_DIR"),
        "auto memory off": os.environ.get("CLAUDE_CODE_DISABLE_AUTO_MEMORY")}}) + "\\n")
state = Path(os.environ["FAKE_LOG"] + ".n")
n = int(state.read_text()) if state.exists() else 0
state.write_text(str(n + 1))
turn = json.loads(Path(os.environ["FAKE_PLAN"]).read_text())[n]
for path, content in (turn.get("write") or {{}}).items():
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(content)
"""

FAKE_CLAUDE = (
    FAKE
    + """
def say(event):
    print(json.dumps(event))
session = args[args.index("--session-id") + 1] if "--session-id" in args else args[args.index("--resume") + 1]
plugin = args[args.index("--plugin-dir") + 1]
say({{"type": "system", "subtype": "init", "session_id": session,
     "plugins": [{{"name": "knowledge-bus", "path": plugin}}] + turn.get("plugins", []),
     "skills": ["knowledge-bus:kb-ingest", "simplify"] + turn.get("skills", [])}})
if turn.get("notice"):
    say({{"type": "system", "subtype": "notice", "message": turn["notice"]}})
if turn.get("skill"):
    say({{"type": "assistant", "message": {{"content": [{{"type": "tool_use", "id": "s1",
         "name": "Skill", "input": {{"skill": "knowledge-bus:" + turn["skill"]}}}}]}}}})
    say({{"type": "user", "message": {{"content": [{{"type": "tool_result", "tool_use_id": "s1",
         "content": "Launching skill"}}]}}}})
for path in turn.get("write") or {{}}:
    say({{"type": "assistant", "message": {{"content": [{{"type": "tool_use", "id": "w1",
         "name": "Write", "input": {{"file_path": path, "content": "..."}}}}]}}}})
for command in turn.get("bash") or []:
    say({{"type": "assistant", "message": {{"content": [{{"type": "tool_use", "id": "b1",
         "name": "Bash", "input": {{"command": command}}}}]}}}})
say({{"type": "assistant", "message": {{"content": [{{"type": "text", "text": turn["text"]}}]}}}})
say({{"type": "result", "subtype": "success", "is_error": False, "result": turn["text"],
     "session_id": session, "total_cost_usd": 0.25}})
"""
)

FAKE_CODEX = (
    FAKE
    + """
def say(event):
    print(json.dumps(event))
say({{"type": "thread.started", "thread_id": "thread-7"}})
if turn.get("skill"):
    say({{"type": "item.completed", "item": {{"id": "i1", "type": "command_execution",
         "command": "cat .agents/skills/" + turn["skill"] + "/SKILL.md",
         "aggregated_output": "# skill", "exit_code": 0}}}})
for path in turn.get("write") or {{}}:
    say({{"type": "item.completed", "item": {{"id": "i2", "type": "file_change",
         "changes": [{{"path": path, "kind": "add"}}]}}}})
say({{"type": "item.completed", "item": {{"id": "i3", "type": "agent_message", "text": turn["text"]}}}})
say({{"type": "turn.completed", "usage": {{"input_tokens": 100, "cached_input_tokens": 60,
     "output_tokens": 20}}}})
"""
)

UNIVERSE = """universe:
  id: choir-operations
  label: Choir operations
  version: 0.1
  conforms_to: kbp/0.7
elements:
  - id: rehearsal-schedule
    question: What weekday, hour and room does the choir rehearse in?
"""


def fake_cli(tmp_path, monkeypatch, name, plan):
    """`name` on PATH as a fake agent CLI that plays `plan`, one turn per call, and logs each call."""
    folder = tmp_path / "bin"
    folder.mkdir(exist_ok=True)
    template = FAKE_CLAUDE if name == "claude" else FAKE_CODEX
    version = "2.1.280 (Claude Code)" if name == "claude" else "codex-cli 0.149.0"
    script = folder / name
    script.write_text(template.format(python=sys.executable, version=version))
    script.chmod(0o755)
    (tmp_path / "plan.json").write_text(json.dumps(plan))
    monkeypatch.setenv("PATH", f"{folder}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_PLAN", str(tmp_path / "plan.json"))
    monkeypatch.setenv("FAKE_LOG", str(tmp_path / "log.jsonl"))
    monkeypatch.delenv("CLAUDE_CODE_DISABLE_AUTO_MEMORY", raising=False)
    return tmp_path / "log.jsonl"


def calls(log):
    return [json.loads(line) for line in log.read_text().splitlines()]


def fixture(tmp_path):
    folder = tmp_path / "fixture"
    (folder / ".knowledge-bus").mkdir(parents=True)
    (folder / ".knowledge-bus/universe.kbp.yaml").write_text(UNIVERSE)
    (folder / "2025-09-04-rehearsals.md").write_text("Rehearsals: Thursdays.\n")
    return folder


SCENARIO = {
    "skill": "kb-ingest",
    "prompt": "Map my choir notes into the choir spec.",
    "owner": ["Yes. Go ahead."],
    "required": ["asks-only-what-is-open", "records-stand-alone"],
}
ANSWERS = (
    "- element: rehearsal-schedule\n  answer: Thursdays at 7 pm in the library annex.\n"
)


def played(tmp_path, monkeypatch, plan, scenario=SCENARIO, agent="claude"):
    fake_cli(tmp_path, monkeypatch, agent, plan)
    made = (
        adapters.ClaudeAgent("claude-test")
        if agent == "claude"
        else adapters.CodexAgent("gpt-test")
    )
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    source = fixture(tmp_path)
    record = play.play(scenario, source, made, scratch, validate=lambda folder: True)
    return record, source, made


def test_an_event_whose_message_is_plain_text_is_read_past(tmp_path, monkeypatch):
    plan = [
        {"text": "Mapped the rehearsal schedule.", "notice": "Retrying the request."}
    ]
    record, _, _ = played(tmp_path, monkeypatch, plan, {**SCENARIO, "owner": []})
    assert record["transcript"][-1]["text"] == "Mapped the rehearsal schedule."


def test_a_scripted_two_turn_run_resumes_one_session_and_records_it(
    tmp_path, monkeypatch
):
    plan = [
        {"text": "I read one note. Shall I map the rehearsal note into the spec?", "skill": "kb-ingest"},
        {"text": "Mapped the rehearsal schedule.", "write": {".knowledge-bus/answers.yaml": ANSWERS}},
    ]  # fmt: skip
    record, source, agent = played(tmp_path, monkeypatch, plan)
    first, second = calls(tmp_path / "log.jsonl")
    assert first["auto memory off"] == second["auto memory off"] == "1"
    assert first["stdin"] == SCENARIO["prompt"]
    assert second["stdin"] == "Yes. Go ahead."
    session = first["args"][first["args"].index("--session-id") + 1]
    assert second["args"][second["args"].index("--resume") + 1] == session
    for args in (first["args"], second["args"]):
        assert args[0] == "-p"
        assert args[args.index("--setting-sources") + 1] == ""
        assert "--strict-mcp-config" in args
        assert args[args.index("--model") + 1] == "claude-test"
        assert args[args.index("--output-format") + 1] == "stream-json"
        allowed = args[
            args.index("--allowedTools") + 1 : args.index("--permission-mode")
        ]
        assert [a for a in allowed if a.startswith("Bash")] == [
            "Bash(python3:*)", "Bash(ls:*)", "Bash(cat:*)", "Bash(head:*)",
            "Bash(tail:*)", "Bash(wc:*)", "Bash(grep:*)",
        ]  # fmt: skip
        assert (
            args[args.index("--append-system-prompt") + 1] == adapters.ClaudeAgent.note
        )
        plugin = Path(args[args.index("--plugin-dir") + 1])
    assert (plugin / ".claude-plugin/plugin.json").is_file()
    assert sorted(p.parent.name for p in plugin.glob("skills/*/SKILL.md")) == sorted(
        play.SKILL_NAMES
    )
    assert first["cwd"] == second["cwd"] != str(source)
    assert first["cache"] and not first["cache"].startswith(first["cwd"])
    roles = [(s["role"], s.get("text", s.get("name"))) for s in record["transcript"]]
    assert roles[0] == ("owner", SCENARIO["prompt"])
    assert ("owner", "Yes. Go ahead.") in roles and ("tool", "Skill") in roles
    assert roles[-1] == ("agent", "Mapped the rehearsal schedule.")
    assert record["changes"] == {
        ".knowledge-bus/answers.yaml": {"change": "created", "content": ANSWERS}
    }
    checks = record["checks"]
    assert checks["skill"] == "kb-ingest" and checks["skill fired"] is True
    assert checks["writes outside .knowledge-bus"] == []
    assert checks["writes outside the work folder (from tool calls)"] == []
    assert checks["conforms_to changed"] == []
    assert checks["possible script drift"] == []
    assert checks["loaded beside the skills under test"] == []
    assert checks["validates"] == {"before": True, "after": True, "kept": True}
    assert not (source / ".knowledge-bus/answers.yaml").exists()
    assert agent.cost == 0.5


def test_a_turn_that_neither_asks_nor_restates_before_a_reply_is_a_hint_not_a_finding(
    tmp_path, monkeypatch
):
    plan = [
        {"text": "I mapped the notes.", "write": {".knowledge-bus/answers.yaml": ANSWERS}},
        {"text": "Done."},
    ]  # fmt: skip
    record, _, _ = played(tmp_path, monkeypatch, plan)
    checks = record["checks"]
    assert "script drift" not in checks
    assert checks["possible script drift"] == [1]
    assert checks["skill fired"] is False
    assert play.hints(checks) == [
        "possible script drift before owner reply 1 (a hint for review, not a finding)"
    ]
    assert "drift" not in play.summary(checks)
    scenario = {**SCENARIO, "required": ["restates-the-ask-before-acting"]}
    behaviour, _, _ = play.cases(spec_module.load(), scenario, record, "s/run-1")
    assert behaviour and not any(
        "drift" in json.dumps(c.context) or "drift" in c.text for c in behaviour
    )


def test_a_write_outside_the_knowledge_bus_folder_is_flagged(tmp_path, monkeypatch):
    moved = UNIVERSE.replace("kbp/0.7", "kbp/0.8")
    plan = [
        {"text": "Shall I tidy the notes?", "skill": "kb-ingest"},
        {"text": "Tidied.", "write": {
            "2025-09-04-rehearsals.md": "Rehearsals moved.\n",
            ".knowledge-bus/universe.kbp.yaml": moved,
        }},
    ]  # fmt: skip
    record, source, _ = played(tmp_path, monkeypatch, plan)
    checks = record["checks"]
    assert checks["writes outside .knowledge-bus"] == ["2025-09-04-rehearsals.md"]
    assert checks["conforms_to changed"] == [".knowledge-bus/universe.kbp.yaml"]
    assert record["changes"]["2025-09-04-rehearsals.md"]["change"] == "modified"
    assert (
        source / "2025-09-04-rehearsals.md"
    ).read_text() == "Rehearsals: Thursdays.\n"


def test_a_tool_call_that_writes_outside_the_work_folder_is_flagged(
    tmp_path, monkeypatch
):
    elsewhere = tmp_path / "elsewhere/.knowledge-bus/universe.kbp.yaml"
    plan = [
        {"text": "Shall I tidy the spec?", "skill": "kb-ingest"},
        {
            "text": "Tidied.",
            "write": {str(elsewhere): UNIVERSE, ".knowledge-bus/notes.md": "Thursdays.\n"},
            "bash": [
                f"cat .knowledge-bus/universe.kbp.yaml > {tmp_path}/copy.yaml",
                "python3 kbp.py --validate .knowledge-bus > .knowledge-bus/out.txt 2>&1",
            ],
        },
    ]  # fmt: skip
    record, _, _ = played(tmp_path, monkeypatch, plan)
    checks = record["checks"]
    assert checks["writes outside .knowledge-bus"] == []
    assert checks["writes outside the work folder (from tool calls)"] == [
        str(elsewhere),
        f"{tmp_path}/copy.yaml",
    ]
    assert (
        f"writes outside the work folder (from tool calls): {elsewhere}, {tmp_path}/copy.yaml"
        in play.summary(checks)
    )


@pytest.mark.parametrize(
    ("step", "outside"),
    [
        ({"name": "Write", "input": {"file_path": "/tmp/scratch/universe.kbp.yaml"}}, True),
        ({"name": "Edit", "input": {"file_path": "../notes.md"}}, True),
        ({"name": "Edit", "input": {"file_path": ".knowledge-bus/universe.kbp.yaml"}}, False),
        ({"name": "Write", "input": {"file_path": "WORK/.knowledge-bus/answers.yaml"}}, False),
        ({"name": "Read", "input": {"file_path": "/etc/hosts"}}, False),
        ({"name": "Bash", "input": {"command": "echo hi >> /tmp/log.txt"}}, True),
        ({"name": "Bash", "input": {"command": "cat a.md >'/tmp/b.md'"}}, True),
        ({"name": "Bash", "input": {"command": "python3 x.py > /dev/null 2>&1"}}, False),
        ({"name": "Bash", "input": {"command": "cat a.md > b.md"}}, False),
        ({"name": "Bash", "input": {"command": "cat a.md > WORK/b.md"}}, False),
        ({"name": "Bash", "input": {"command": "grep -c x /tmp/a.md"}}, False),
    ],
)  # fmt: skip
def test_writes_outside_the_work_folder_are_read_from_write_edit_and_bash_redirects(
    tmp_path, step, outside
):
    work = tmp_path / "work"
    work.mkdir()
    shown = json.loads(json.dumps(step).replace("WORK", str(work)))
    turn = adapters.Turn(steps=[{"kind": "tool", **shown}])
    found = play.written_outside([turn], work)
    assert bool(found) is outside


def test_the_codex_agent_runs_the_skills_from_the_project_folder_and_resumes_its_thread(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.delenv("CODEX_HOME", raising=False)
    plan = [
        {"text": "Shall I map the rehearsal note?", "skill": "kb-ingest"},
        {"text": "Mapped.", "write": {".knowledge-bus/answers.yaml": ANSWERS}},
    ]  # fmt: skip
    record, _, agent = played(tmp_path, monkeypatch, plan, agent="codex")
    first, second = calls(tmp_path / "log.jsonl")
    assert first["args"][:1] == ["exec"] and first["args"][-1] == "-"
    assert second["args"][:2] == ["exec", "resume"]
    assert second["args"][-2:] == ["thread-7", "-"]
    assert first["auto memory off"] is None and second["auto memory off"] is None
    for args in (first["args"], second["args"]):
        for flag in (
            "--json",
            "--skip-git-repo-check",
            "--ignore-user-config",
            "--ignore-rules",
        ):
            assert flag in args
        assert args[args.index("-m") + 1] == "gpt-test"
        assert 'sandbox_mode="workspace-write"' in args
        assert 'approval_policy="never"' in args
        assert (
            f"sandbox_workspace_write.writable_roots={json.dumps([first['cache']])}"
            in args
        )
        assert {args[n + 1] for n, a in enumerate(args) if a == "--disable"} == {
            "apps", "browser_use", "computer_use", "hooks", "image_generation",
            "multi_agent", "plugins",
        }  # fmt: skip
        assert not any(a.startswith("skills.") for a in args)
    assert first["args"][first["args"].index("-C") + 1] == first["cwd"]
    assert second["cwd"] == first["cwd"]
    installed = Path(first["cwd"]) / ".agents/skills"
    assert sorted(p.parent.name for p in installed.glob("*/SKILL.md")) == sorted(
        play.SKILL_NAMES
    )
    assert record["checks"]["skill fired"] is True
    assert record["checks"]["writes outside .knowledge-bus"] == []
    assert record["checks"]["loaded beside the skills under test"] == []
    assert record["fixture files"] == [
        ".knowledge-bus/universe.kbp.yaml",
        "2025-09-04-rehearsals.md",
    ]
    assert agent.tokens == 240 and agent.cost is None


def test_codex_user_skills_are_reported_as_loaded_beside_the_skills_under_test(
    tmp_path, monkeypatch
):
    (tmp_path / "home/.agents/skills/kb-check").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    plan = [{"text": "Shall I?", "skill": "kb-ingest"}, {"text": "Done."}]
    record, _, _ = played(tmp_path, monkeypatch, plan, agent="codex")
    assert record["checks"]["loaded beside the skills under test"] == [
        f"{tmp_path / 'home/.agents/skills'}/kb-check"
    ]


def test_codex_home_skills_are_disabled_per_call_and_not_reported_as_loaded(
    tmp_path, monkeypatch
):
    home = tmp_path / "codex-home"
    for name in ("pets", "kb-check", "pets-\U0001f431", ".system/imagegen"):
        (home / "skills" / name).mkdir(parents=True)
        (home / "skills" / name / "SKILL.md").write_text("# skill")
    (home / "skills/notes").mkdir()
    monkeypatch.setenv("CODEX_HOME", str(home))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    plan = [{"text": "Shall I?", "skill": "kb-ingest"}, {"text": "Done."}]
    record, _, _ = played(tmp_path, monkeypatch, plan, agent="codex")
    off = ",".join(
        f"{{path={json.dumps(str(home / 'skills' / name / 'SKILL.md'), ensure_ascii=False)},enabled=false}}"
        for name in ("kb-check", "pets", "pets-\U0001f431")
    )
    for call in calls(tmp_path / "log.jsonl"):
        args = call["args"]
        settings = [a for a in args if a.startswith("skills.")]
        assert settings == [f"skills.config=[{off}]"]
        assert args[args.index(settings[0]) - 1] == "-c"
        assert tomllib.loads(settings[0])["skills"]["config"] == [
            {"path": str(home / "skills" / name / "SKILL.md"), "enabled": False}
            for name in ("kb-check", "pets", "pets-\U0001f431")
        ]
    assert record["checks"]["loaded beside the skills under test"] == []


def test_another_copy_of_a_skill_under_test_is_reported_for_claude(
    tmp_path, monkeypatch
):
    plan = [
        {"text": "Shall I?", "skill": "kb-ingest", "skills": ["kb-check"], "plugins": [{"name": "other"}]},
        {"text": "Done."},
    ]  # fmt: skip
    record, _, _ = played(tmp_path, monkeypatch, plan)
    assert record["checks"]["loaded beside the skills under test"] == [
        "plugin other",
        "skill kb-check",
    ]


def test_a_second_knowledge_bus_plugin_is_reported_for_claude(tmp_path, monkeypatch):
    installed = "/home/owner/.claude/plugins/cache/knowledge-bus"
    plan = [
        {"text": "Shall I?", "skill": "kb-ingest",
         "plugins": [{"name": "knowledge-bus", "path": installed}]},
        {"text": "Done."},
    ]  # fmt: skip
    record, _, _ = played(tmp_path, monkeypatch, plan)
    assert record["checks"]["loaded beside the skills under test"] == [
        f"plugin knowledge-bus ({installed})"
    ]


def test_cases_cover_questions_reports_files_answers_and_the_transcript(
    tmp_path, monkeypatch
):
    plan = [
        {"text": "Shall I map the rehearsal note?", "skill": "kb-ingest"},
        {"text": "Mapped the rehearsal schedule.", "write": {
            ".knowledge-bus/answers.yaml": ANSWERS,
            ".knowledge-bus/universe.kbp.yaml": UNIVERSE.replace(
                "What weekday, hour and room does the choir rehearse in?",
                "When and where does the choir rehearse each week?"),
        }},
    ]  # fmt: skip
    scenario = {
        **SCENARIO,
        "required": [
            "asks-with-a-reading-and-options",
            "restates-the-ask-before-acting",
            "records-stand-alone",
            "answers-the-question-it-is-filed-under",
            "wording-meets-the-bar",
        ],
    }
    record, _, _ = played(tmp_path, monkeypatch, plan, scenario)
    spec = spec_module.load()
    behaviour, wording, notes = play.cases(spec, scenario, record, "s/run-1")
    by = {}
    for case in behaviour:
        by.setdefault((case.rule_id, case.subject), []).append(case)
    asked = by[("asks-with-a-reading-and-options", "question-to-owner")]
    assert [c.text for c in asked] == ["Shall I map the rehearsal note?"]
    assert [
        c.text for c in by[("restates-the-ask-before-acting", "report-to-owner")]
    ] == ["Mapped the rehearsal schedule."]
    (transcript,) = by[("restates-the-ask-before-acting", "transcript")]
    assert transcript.text.startswith("Owner: Map my choir notes")
    assert transcript.context["owner script"] == [SCENARIO["prompt"], "Yes. Go ahead."]
    (record_case,) = by[("records-stand-alone", "files-written")]
    assert record_case.text == f"Path: .knowledge-bus/answers.yaml\n\n{ANSWERS}"
    (answer,) = by[("answers-the-question-it-is-filed-under", "files-written")]
    assert answer.text == "Thursdays at 7 pm in the library annex."
    assert answer.context == {
        "question": "When and where does the choir rehearse each week?"
    }
    assert all(c.ref.startswith("s/run-1/") for c in behaviour + wording)
    assert wording and {c.text for c in wording} == {
        "When and where does the choir rehearse each week?"
    }
    assert not any(c.rule_id == "wording-meets-the-bar" for c in behaviour)
    assert any("wording-meets-the-bar" in n for n in notes)


def test_a_run_folder_records_the_agent_digests_costs_and_verdicts(
    tmp_path, monkeypatch
):
    turn = {"text": "Shall I go on with the mapping?", "skill": "kb-ingest"}
    fake_cli(tmp_path, monkeypatch, "claude", [turn] * 4)
    monkeypatch.setattr(play, "validate", lambda folder: True)
    out = tmp_path / "out"
    code = play.main(
        [
            "--scenario", "ingest-choir-notes", "--model", "claude-test",
            "--tiers", "deterministic", "--label", "dry run", "--out", str(out),
        ]
    )  # fmt: skip
    assert code == 0
    run = json.loads((out / "run.json").read_text())
    assert run["kind"] == "skills" and run["label"] == "dry run"
    assert run["tiers"] == ["deterministic"]
    assert run["adapters"]["agent"] == "claude 2.1.280 (Claude Code), model claude-test"
    inputs = run["inputs"]
    assert inputs["evals/skills.yaml"].startswith("sha256:")
    for name in play.SKILL_NAMES:
        assert inputs[f"skills/{name}/SKILL.md"].startswith("sha256:")
    for folder in (spec_module.ROOT / "evals/fixtures").iterdir():
        assert inputs[f"evals/fixtures/{folder.name}"].startswith("sha256:")
    assert "agent cost: $1.00" in run["notes"]
    assert any(
        n.startswith("ingest-choir-notes run 1: skill fired") for n in run["notes"]
    )
    assert any("n=1" in n for n in run["notes"])
    assert (
        "the agent may run without asking: " + ", ".join(adapters.ClaudeAgent.allowed)
        in run["notes"]
    )
    assert (
        "the agent's appended system prompt: " + adapters.ClaudeAgent.note
        in run["notes"]
    )
    assert (
        "the agent's environment adds: CLAUDE_CODE_DISABLE_AUTO_MEMORY=1"
        in run["notes"]
    )
    assert all(c["auto memory off"] == "1" for c in calls(tmp_path / "log.jsonl"))
    assert not any("drift" in n for n in run["notes"])
    rows = [
        json.loads(line) for line in (out / "verdicts.jsonl").read_text().splitlines()
    ]
    assert rows and all(r["ref"].startswith("ingest-choir-notes/run-1/") for r in rows)
    transcript_rows = [r for r in rows if r["subject"] == "transcript"]
    assert transcript_rows and all(
        r["text"] == "(transcript: ingest-choir-notes/run-1/transcript.json)"
        for r in transcript_rows
    )
    folder = out / "ingest-choir-notes/run-1"
    for name in ("events.jsonl", "transcript.json", "changes.json", "checks.json"):
        assert (folder / name).is_file()
    assert (out / "report.md").read_text().startswith("# Grade")


def test_the_digest_of_a_folder_follows_its_paths_and_contents(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "a/x.md").write_text("one")
    first = play.tree_digest(tmp_path)
    assert first == play.tree_digest(tmp_path)
    (tmp_path / "a/x.md").write_text("two")
    assert play.tree_digest(tmp_path) != first


@pytest.mark.parametrize(
    ("text", "hands_back"),
    [
        ("Shall I go ahead?", True),
        (
            "I will map the three notes into the spec. Confirm and I will write them.",
            True,
        ),
        ("I mapped the notes.", False),
        ("", False),
    ],
)
def test_a_turn_hands_back_when_it_asks_or_seeks_confirmation(text, hands_back):
    assert play.hands_back(text) is hands_back


def test_a_fixture_still_to_be_built_is_not_played():
    assert play.fixture_of({"fixture": {"needs": "two universes"}}) is None
    assert play.fixture_of({}) == "none"


def test_tiers_run_settles_the_played_cases_with_the_engine(tmp_path, monkeypatch):
    plan = [
        {"text": "Shall I map it?", "skill": "kb-ingest"},
        {"text": "Mapped.", "write": {".knowledge-bus/notes.md": "As discussed earlier, rehearsals are on Thursdays.\n"}},
    ]  # fmt: skip
    record, _, _ = played(tmp_path, monkeypatch, plan)
    behaviour, _, _ = play.cases(spec_module.load(), SCENARIO, record, "s/run-1")
    judged = []

    def judge(cases):
        judged.extend(cases)
        return [tiers.Outcome("pass", "judgment", {"critique": "ok"}) for _ in cases]

    results = tiers.run(behaviour, judge=judge)
    flagged = next(r for r in results if r.case.rule_id == "records-stand-alone")
    assert flagged.trail[0].verdict == "undecided" and flagged.final.verdict == "pass"
    assert {c.subject for c in judged} == {"transcript", "files-written"}


EDIT_REPORT = (
    "I've shortened the question in `.knowledge-bus/universe.kbp.yaml:40` to:\n\n"
    "> **What cake should the kitchen make?**\n\n"
    'The code stays `ea4y3`, and the comment still says why "When do they need it?" went.\n\n'
    "I haven't run the checker. Running `kbp --validate` will confirm it still passes."
)
HEADED_EXPLANATION = (
    "### The one question it asks: how much does the reader already know?\n\n"
    "**Purpose:** it covers what a writer needs to know about the reader.\n\n"
    "```yaml\nquestion: How much does the reader already know?\n```\n\n"
    "If you'd like, I can bring these notes into the spec with `kb-ingest`."
)
CLOSING_QUESTION = (
    "**Two things I can't settle from the notes**\n\n"
    "1. Should the piped message be its own question? Keep it in, or split it out?\n"
    "2. Is a budget ever recorded? Drop it, or add a budget question?\n\n"
    "Once you answer, I'll update `.knowledge-bus/universe.kbp.yaml`."
)
WHICH_ONE = (
    "I found two sets of village hall definitions in `.knowledge-bus/`. Which one do you mean?\n\n"
    "1. **Hall bookings** covers what the hall records for each booking.\n"
    "2. **Hall upkeep** covers the cleaning, checks and repairs.\n\n"
    "I couldn't run the inspector because shell commands aren't allowed in this session. "
    "If you allow Bash, I'll run the inspection as well."
)
OPEN_POINTS = (
    "I recorded the bookings.\n\n"
    "Two points stay open in the notes:\n\n"
    "- Is a deposit always taken?\n"
    "- Who returns the keys?\n\n"
    "Both are filed as gaps."
)


@pytest.mark.parametrize(
    ("text", "asks"),
    [
        (EDIT_REPORT, False),
        (HEADED_EXPLANATION, False),
        (CLOSING_QUESTION, True),
        (WHICH_ONE, True),
        (WHICH_ONE.replace("mean?\n\n", "mean?\n"), True),
        (OPEN_POINTS, False),
        (
            "Why does it matter?\n\nBecause hirers pay by the hour.\n\nI read both files.",
            False,
        ),
        ("I read one note. Shall I map the rehearsal note into the spec?", True),
        ("I will map the three notes. Confirm and I will write them.", True),
        ("Keep it in, or split it out?**", True),
        ('The question now reads "What cake should the kitchen make?"', False),
        ("Mapped the rehearsal schedule.", False),
        ("", False),
        ("1. Keep it.\n2. Split it.\n\nIf you agree with all three, say so.", True),
        ("Let me know and I'll file it as written.", True),
        ("If you only meant one, tell me which.", True),
        ("Tell me if a deposit is always taken.", True),
    ],
)
def test_a_message_asks_the_owner_by_its_closing_request(text, asks):
    assert play.asks_owner(text) is asks


def test_reports_and_questions_are_filed_by_their_closing_request(
    tmp_path, monkeypatch
):
    plan = [
        {"text": HEADED_EXPLANATION, "skill": "kb-ingest"},
        {"text": CLOSING_QUESTION},
        {"text": EDIT_REPORT},
    ]
    scenario = {
        **SCENARIO,
        "owner": ["Explain it.", "Yes. Go ahead."],
        "required": [
            "asks-with-a-reading-and-options",
            "restates-the-ask-before-acting",
        ],
    }
    record, _, _ = played(tmp_path, monkeypatch, plan, scenario)
    behaviour, _, _ = play.cases(spec_module.load(), scenario, record, "s/run-1")
    by = {}
    for case in behaviour:
        by.setdefault(case.subject, set()).add(case.text)
    assert by["question-to-owner"] == {CLOSING_QUESTION}
    assert by["report-to-owner"] == {HEADED_EXPLANATION, EDIT_REPORT}


def test_judges_see_the_owner_turns_either_side_of_an_item_for_reference_only(
    tmp_path, monkeypatch
):
    plan = [
        {"text": "Shall I map the rehearsal note?", "skill": "kb-ingest"},
        {"text": "Mapped the rehearsal schedule.", "write": {".knowledge-bus/notes.md": "Thursdays.\n"}},
    ]  # fmt: skip
    scenario = {
        **SCENARIO,
        "required": [
            "asks-with-a-reading-and-options",
            "restates-the-ask-before-acting",
            "records-stand-alone",
        ],
    }
    record, _, _ = played(tmp_path, monkeypatch, plan, scenario)
    behaviour, _, _ = play.cases(spec_module.load(), scenario, record, "s/run-1")
    by = {(c.rule_id, c.subject): c for c in behaviour}
    question = by[("asks-with-a-reading-and-options", "question-to-owner")]
    assert question.context == {
        "owner turn before": SCENARIO["prompt"],
        "owner turn after": "Yes. Go ahead.",
    }
    # Jev, the decision tier, gets the bare question, as in its calibration examples
    assert adapters._state(question) == question.text
    assert (
        adapters.Jev.question(question)["instructions"]
        == question.rule["decision"]["ask"]
    )
    report = by[("restates-the-ask-before-acting", "report-to-owner")]
    written = by[("records-stand-alone", "files-written")]
    assert report.context == written.context == {"owner turn before": "Yes. Go ahead."}
    for case in (report, written):
        shown = "   context, for reference only (judge the quoted text): " + json.dumps(
            case.context, ensure_ascii=False
        )
        assert shown in adapters.Judge.prompt([case]).splitlines()
