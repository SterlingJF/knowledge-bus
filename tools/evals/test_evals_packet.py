"""Desktop-app packets that mirror an Anthropic-side run, and the run folders built from replies."""

import json
import re
import shutil

import adapters
import grade
import packet
import pytest
import report
import spec as spec_module
import tiers
import yaml
from test_evals_grade import FAIR, FAIR_SITUATIONS, SET_DOC

OPUS, FABLE = "claude-opus-5-5", "claude-fable-5-1"
JUDGES, LIGHT = list(packet.JUDGES), packet.LIGHT
SESSIONS = {"gpt-6-astra": OPUS, "gpt-6.1-sol": FABLE, "gpt-6-luna": grade.LIGHT_MODEL}
SYSTEMS = {system: kind for kind, (system, _) in packet.KINDS.items()}
RUNS = ("calibration-universe", "calibration-skills", "universe")


def anthropic_call(sent):
    """The Anthropic side's models: each judge passes or fails by item and model, probes are
    written and kept, and every passage and situation is filed under the first question."""

    def call(prompt, model, schema, system):
        sent.append((model, system, prompt))
        (key,) = schema["required"]
        counted = re.search(r"each of the (\d+) (?:items|passages)", prompt)
        n = int(counted.group(1)) if counted else 1
        if key == "verdicts":
            out = {
                "verdicts": [
                    {
                        "item": i,
                        "verdict": "fail" if (i + len(model)) % 3 == 0 else "pass",
                        "critique": f"anthropic critique {i}",
                    }
                    for i in range(1, n + 1)
                ]
            }
        elif key == "passages":
            out = {"passages": ["Tenors and altos.", "Basses too."]}
        elif key == "answers":
            out = {
                "answers": [{"passage": i, "answers": True} for i in range(1, n + 1)]
            }
        elif key == "filings":
            out = {"filings": [{"passage": i, "question": 1} for i in range(1, n + 1)]}
        else:
            out = {"option": 1}
        return {"structured_output": out, "total_cost_usd": 0.01}

    return call


def jev_http(self, body):
    """The decision model: yes, no or unsure by the state's length; the last option, sometimes
    below its confidence."""
    size = len(json.dumps(body["state"]))
    answers = {}
    for name, q in body["questions"].items():
        if q["type"] == "noul":
            answers[name] = {"noul": (0.9, 0.1, 0.5)[size % 3]}
        elif q["type"] == "choice":
            answers[name] = {
                "choice": list(q["criteria"])[-1],
                "confidence": 0.3 if size % 4 == 0 else 0.9,
            }
        else:
            answers[name] = {"score": 3, "confidence": 0.9}
    return {"model": "jev-1.13.0", "answers": answers, "usage": {"input_tokens": 7}}


UNIVERSE_DOC = {
    **{k: v for k, v in yaml.safe_load(FAIR.read_text()).items()},
    "elements": SET_DOC["elements"],
    "artifacts": SET_DOC["artifacts"],
}


@pytest.fixture(scope="module")
def anthropic(tmp_path_factory):
    """Three Anthropic-side runs written by grade.main itself: both calibrations and a universe
    grade, with every prompt each model was sent."""
    root = tmp_path_factory.mktemp("anthropic")
    universe = root / "fair" / "summer-fair.universe.yaml"
    universe.parent.mkdir()
    universe.write_text(yaml.safe_dump(UNIVERSE_DOC, sort_keys=False))
    sent = {name: [] for name in RUNS}
    folders = {}
    argvs = {
        "calibration-universe": ["examples", "--slice", "universe"],
        "calibration-skills": ["examples", "--slice", "skills"],
        "universe": [
            "universe", "--universe", str(universe), "--situations", str(FAIR_SITUATIONS),
        ],
    }  # fmt: skip
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("TYPESAFE_API_KEY", "test")
        patch.setattr(adapters, "unavailable", lambda models: None)
        patch.setattr(adapters.Jev, "_http", jev_http)
        for name, argv in argvs.items():
            patch.setattr(adapters, "model_call", anthropic_call(sent[name]))
            folders[name] = root / name
            argv += ["--label", "anthropic-side", "--out", str(folders[name])]
            assert grade.main(argv) == 0
    return folders, sent, universe


def build(folders, out, *extra):
    argv = ["build", "--out", str(out), *extra]
    for name in RUNS:
        argv += ["--anthropic-run", str(folders[name])]
    return packet.main(argv)


def manifest_of(out):
    return json.loads((out / "manifest.json").read_text())


def answer_all(out, skip=()):
    """A valid reply to every packet: the careful models split on some items, every filer files
    each passage and situation under the first question."""
    for name, entry in manifest_of(out)["packets"].items():
        session, number = name.split("/")
        if name in skip:
            continue
        n, k = entry["items"], entry["choices"]
        if entry["kind"] == "judge":
            flip = session == "gpt-6.1-sol"
            reply = {
                "verdicts": [
                    {
                        "item": i,
                        "verdict": "fail"
                        if (i % 2 == 0) != (flip and i % 5 == 0)
                        else "pass",
                        "critique": f"{session} says {i}",
                    }
                    for i in range(1, n + 1)
                ]
            }
        elif entry["kind"] == "file":
            reply = {
                "filings": [{"passage": i, "question": 1} for i in range(1, n + 1)]
            }
        else:
            reply = {"option": 1 if k else 0}
        path = out / session / "replies" / f"{number}.json"
        path.write_text(json.dumps(reply))


def apply(folders, out, evals, *extra):
    argv = ["apply", "--replies", str(out), "--out", str(evals), *extra]
    for name in RUNS:
        argv += ["--anthropic-run", str(folders[name])]
    return packet.main(argv)


@pytest.fixture(scope="module")
def mirrored(anthropic, tmp_path_factory):
    """The packets for the three runs, a reply to each, and the run folders apply wrote."""
    folders, _, _ = anthropic
    root = tmp_path_factory.mktemp("openai")
    out, evals = root / "packets", root / "evals"
    assert build(folders, out) == 0
    answer_all(out)
    assert apply(folders, out, evals, "--effort", "codex:gpt-6-astra=high") == 0
    written = sorted(evals.iterdir())
    by_prefix = {
        "calibration-universe": next(p for p in written if p.name.startswith("examples-universe-")),
        "calibration-skills": next(p for p in written if p.name.startswith("examples-skills-")),
        "universe": next(p for p in written if p.name.startswith("universe-")),
    }  # fmt: skip
    assert len(written) == 3
    return out, by_prefix


def packets_of(out, session):
    """(kind, text) of each packet in a session folder, in number order."""
    found = []
    for path in sorted((out / session / "packets").iterdir()):
        _, kind = path.stem.split("-")
        found.append((kind, path.read_text()))
    return found


def test_each_packet_is_a_prompt_grade_py_sends_to_that_model(anthropic, mirrored):
    _, sent, _ = anthropic
    out, _ = mirrored
    for session, model in SESSIONS.items():
        expected = {
            (SYSTEMS[system], prompt)
            for name in RUNS
            for m, system, prompt in sent[name]
            if m == model and system in SYSTEMS
        }
        found = packets_of(out, session)
        assert set(found) == expected, session
        assert len(found) == len(expected), "each prompt is asked once"
    assert packets_of(out, "gpt-6-astra") == packets_of(out, "gpt-6.1-sol")
    assert {kind for kind, _ in packets_of(out, "gpt-6-luna")} == {"file", "pick"}


def test_packets_follow_grade_py_job_order(mirrored):
    out, _ = mirrored
    manifest = manifest_of(out)
    for session, patterns in (
        ("gpt-6-astra", (r"^j+f+p+j*$", r"^j+$", r"^j+f+p+$")),
        ("gpt-6-luna", (r"^f+p+$", r"^$", r"^f+p+$")),
    ):
        entries = [e for n, e in manifest["packets"].items() if n.startswith(session)]
        for run, pattern in enumerate(patterns):
            kinds = "".join(e["kind"][0] for e in entries if e["runs"][0] == run)
            assert re.match(pattern, kinds), (session, run, kinds)


def test_session_folders_hold_only_blind_packets_and_one_prompt(anthropic, mirrored):
    folders, _, _ = anthropic
    out, _ = mirrored
    assert sorted(p.name for p in out.iterdir()) == [
        "gpt-6-astra", "gpt-6-luna", "gpt-6.1-sol", "manifest.json",
    ]  # fmt: skip
    hidden = [
        json.loads((f / "run.json").read_text())["id"] for f in [folders["universe"]]
    ]
    hidden += [
        json.loads((folders[n] / "calibration.json").read_text())["run"]["id"]
        for n in RUNS[:2]
    ]
    hidden += ["anthropic critique", "anthropic-side", str(folders["universe"].parent)]
    for session in SESSIONS:
        folder = out / session
        names = sorted(p.name for p in folder.iterdir())
        kinds = (
            ["file", "judge", "pick"] if session != "gpt-6-luna" else ["file", "pick"]
        )
        schemas = [f"reply-schema-{k}.json" for k in kinds]
        assert names == ["PROMPT.md", "packets", "replies", *schemas]
        for path in folder.rglob("*"):
            if path.is_file() and path.parent.name != "replies":
                text = path.read_text()
                assert not spec_module.VENDORS.search(text), path
                assert not any(h in text for h in hidden), path


def test_the_prompt_names_the_files_present_and_gives_each_kind_its_instructions(
    mirrored,
):
    out, _ = mirrored
    astra = (out / "gpt-6-astra" / "PROMPT.md").read_text()
    luna = (out / "gpt-6-luna" / "PROMPT.md").read_text()
    count = len(list((out / "gpt-6-astra" / "packets").iterdir()))
    assert astra.startswith(
        f"There are {count} packets in packets/, numbered 0001 to {count:04d}. Each is a task "
        "of its own. Its name ends in -judge, -file or -pick, and that kind sets your "
        "instructions and reply shape below."
    )
    assert adapters.JUDGE_SYSTEM in astra and adapters.JUDGE_SYSTEM not in luna
    assert "ends in -file or -pick," in luna
    for kind in ("file", "pick"):
        system, schema = packet.KINDS[kind]
        assert system in astra and system in luna
        assert json.dumps(schema, indent=2) in luna
        shape = json.loads(
            (out / "gpt-6-luna" / f"reply-schema-{kind}.json").read_text()
        )
        assert shape == schema
    assert "If replies/<number>.json already exists, skip the packet." in luna


def test_apply_writes_openai_side_runs_the_report_compares_with_the_anthropic_runs(
    anthropic, mirrored
):
    folders, _, _ = anthropic
    _, written = mirrored
    held = {}
    for name in RUNS:
        a = report.summarise(folders[name], "anthropic")
        b = report.summarise(written[name], "openai")
        assert b["measures"] == a["measures"]
        for measure in b["measures"]:
            assert report.different(measure, a, b) is None, (name, measure)
            held.setdefault(measure, {}).update({"anthropic": a, "openai": b})
    rows, why = report.pair_rows(held["grade"])
    assert why is None and len(rows) == 4
    assert rows[0][0] == f"{OPUS} + codex:gpt-6-astra"


def test_shared_tiers_and_passages_are_the_anthropic_runs_own(anthropic, mirrored):
    folders, _, _ = anthropic
    _, written = mirrored

    def rows(folder):
        return [json.loads(line) for line in (folder / "verdicts.jsonl").open()]

    theirs, ours = rows(folders["universe"]), rows(written["universe"])
    assert [(r["rule"], r["ref"]) for r in ours] == [
        (r["rule"], r["ref"]) for r in theirs
    ]
    shared = ("deterministic", "decision")
    for a, b in zip(theirs, ours, strict=True):
        assert [t for t in b["trail"] if t["tier"] in shared] == [
            t for t in a["trail"] if t["tier"] in shared
        ]
        for a_step, b_step in zip(a["trail"], b["trail"], strict=True):
            if a_step["tier"] in grade.FILED and "jev" in a_step.get("placed", {}):
                assert b_step["placed"]["jev"] == a_step["placed"]["jev"]
                assert list(b_step["placed"]) == [*JUDGES, "jev", LIGHT]
            if a_step["tier"] == "judgment":
                assert list(b_step["votes"]) == JUDGES
    assert {r["tier"] for r in ours} >= {"decision", "judgment", "sort", "recognise"}
    assert (written["universe"] / "probes.json").read_bytes() == (
        folders["universe"] / "probes.json"
    ).read_bytes()
    run = json.loads((written["universe"] / "run.json").read_text())
    a_run = json.loads((folders["universe"] / "run.json").read_text())
    assert run["adapters"] == {
        "decision": "jev jev-1.13.0",
        "judgment": "judges: codex:gpt-6-astra, codex:gpt-6.1-sol",
        "sort": "filers: codex:gpt-6-astra, codex:gpt-6.1-sol, jev jev-1.13.0, codex:gpt-6-luna",
        "recognise": "filers: codex:gpt-6-astra, codex:gpt-6.1-sol, jev jev-1.13.0, codex:gpt-6-luna",
    }
    assert list(run["adapters"]) == list(a_run["adapters"])
    for key in ("kind", "inputs", "kinds", "tiers", "universe"):
        assert run[key] == a_run[key]
    assert run["label"] == "openai-side"


def test_calibration_takes_the_decision_tier_from_the_anthropic_run(
    anthropic, mirrored
):
    folders, _, _ = anthropic
    _, written = mirrored
    for name in RUNS[:2]:
        a = json.loads((folders[name] / "calibration.json").read_text())
        b = json.loads((written[name] / "calibration.json").read_text())
        for tier in ("decision", "deterministic"):
            assert [r for r in b["table"] if r["tier"] == tier] == [
                r for r in a["table"] if r["tier"] == tier
            ]
        assert [m for m in b["misses"] if m["tier"] == "decision"] == [
            m for m in a["misses"] if m["tier"] == "decision"
        ]
        assert [r["tier"] for r in b["table"]] == [r["tier"] for r in a["table"]]
        for x, y in zip(a["settled"], b["settled"], strict=True):
            if x["tier"] in ("deterministic", "decision"):
                assert (y["rule"], y["verdict"], y["tier"]) == (
                    x["rule"], x["verdict"], x["tier"],
                )  # fmt: skip
        cases, labels = grade.example_cases(spec_module.load(), a["run"]["kind"])
        for case, label, x in zip(cases, labels, a["settled"], strict=True):
            if x["tier"] == "decision" and x["verdict"] != label:
                miss = next(
                    m
                    for m in a["misses"]
                    if m["tier"] == "chain"
                    and (m["rule"], m["text"]) == (case.rule_id, case.text)
                )
                assert miss in b["misses"]
        assert (written[name] / "report.md").read_text() == grade._calibration_report(
            grade.Run(**b["run"]), b["table"], b["misses"]
        )


def test_the_notes_say_what_was_reused_and_how_the_packets_were_answered(
    anthropic, mirrored
):
    folders, sent, _ = anthropic
    _, written = mirrored
    a = json.loads((folders["calibration-universe"] / "calibration.json").read_text())
    b = json.loads((written["calibration-universe"] / "calibration.json").read_text())
    a_id = a["run"]["id"]
    tokens = dict(n.split(": ", 1) for n in a["run"]["notes"] if "tokens" in n)
    asked = [
        p for m, s, p in sent["calibration-universe"] if m == OPUS and s in SYSTEMS
    ]
    repeats = len({p for p in asked if asked.count(p) > 1})
    assert repeats
    assert b["run"]["notes"] == [
        f"decision tokens: {tokens['decision tokens']}, spent by {a_id} and reused here",
        "judgment cost: n/a (answered in the Codex app, which reports no cost)",
        "sort and recognise cost: n/a (answered in the Codex app, which reports no cost)",
        (
            f"sort and recognise decision tokens: {tokens['sort and recognise decision tokens']}, "
            f"spent by {a_id} and reused here"
        ),
        "sort and recognise: the decision model is unsure below confidence 0.6",
        (
            f"reused from {a_id}, the Anthropic-side run of the same inputs (digests checked): "
            "the deterministic tier, the decision tier (Jev) and Jev's filings"
        ),
        (
            "judgment, sort and recognise answered in the Codex desktop app, one session per "
            "model (codex:gpt-6-astra, codex:gpt-6.1-sol, codex:gpt-6-luna), every packet in one "
            "prompt rather than one CLI call per batch; each packet is the prompt grade.py "
            "sends, in grade.py's order, and the instructions grade.py sends as the system "
            "prompt are given once at the top of the session"
        ),
        (
            f"prompts grade.py sends more than once ({repeats}) were asked once and the "
            "answer serves each"
        ),
        "reasoning effort set in the app: codex:gpt-6-astra high",
    ]
    u = json.loads((written["universe"] / "run.json").read_text())
    u_id = json.loads((folders["universe"] / "run.json").read_text())["id"]
    assert (
        f"reused from {u_id}, the Anthropic-side run of the same inputs (digests checked): "
        "the deterministic tier, the decision tier (Jev), Jev's filings and the sort passages "
        "(probes.json)"
    ) in u["notes"]
    assert not [n for n in u["notes"] if "failed after retries" in n or "$" in n]
    s = json.loads((written["calibration-skills"] / "calibration.json").read_text())
    assert any(
        n.startswith("judgment answered in the Codex desktop app, one session per model "
                     "(codex:gpt-6-astra, codex:gpt-6.1-sol), ")
        for n in s["run"]["notes"]
    )  # fmt: skip


def copied(anthropic, tmp_path):
    folders, _, _ = anthropic
    found = {}
    for name in RUNS:
        found[name] = tmp_path / "a" / name
        shutil.copytree(folders[name], found[name])
    return found


def refused(capsys, code):
    assert code == 2
    return capsys.readouterr().err


def test_a_missing_or_malformed_reply_is_refused_with_a_plain_message(
    anthropic, tmp_path, capsys
):
    folders, _, _ = anthropic
    out = tmp_path / "packets"
    assert build(folders, out) == 0
    names = list(manifest_of(out)["packets"])
    kinds = {n: e["kind"] for n, e in manifest_of(out)["packets"].items()}
    judge = next(n for n in names if kinds[n] == "judge")
    pick = next(n for n in names if kinds[n] == "pick")
    answer_all(out, skip={names[-1]})
    session, number = judge.split("/")
    path = out / session / "replies" / f"{number}.json"
    reply = json.loads(path.read_text())
    reply["verdicts"] = reply["verdicts"][1:] + [dict(reply["verdicts"][0], item=99)]
    path.write_text(json.dumps(reply))
    session, number = pick.split("/")
    (out / session / "replies" / f"{number}.json").write_text(
        '```json\n{"option": 1}\n```'
    )
    err = refused(capsys, apply(folders, out, tmp_path / "evals"))
    last_session, last_number = names[-1].split("/")
    assert f"{last_session}/replies/{last_number}.json: no reply" in err
    assert (
        f"{judge.split('/')[0]}/replies/{judge.split('/')[1]}.json: item 1 is missing"
        in err
    )
    assert "item 99 is extra" in err
    assert (
        f"{pick.split('/')[1]}.json: not one JSON object alone (no prose or code fences)"
        in err
    )
    assert not (tmp_path / "evals").exists()


def test_a_reply_off_its_schema_is_refused(anthropic, tmp_path, capsys):
    folders, _, _ = anthropic
    out = tmp_path / "packets"
    assert build(folders, out) == 0
    answer_all(out)
    manifest = manifest_of(out)
    first, second = [n for n, e in manifest["packets"].items() if e["kind"] == "file"][
        :2
    ]

    def edit(name, change):
        session, number = name.split("/")
        path = out / session / "replies" / f"{number}.json"
        reply = json.loads(path.read_text())
        change(reply)
        path.write_text(json.dumps(reply))
        return number

    one = edit(first, lambda reply: reply.update(note="x"))
    k = manifest["packets"][second]["choices"]
    two = edit(second, lambda reply: reply["filings"][0].update(question=k + 1))
    err = refused(capsys, apply(folders, out, tmp_path / "evals"))
    assert f"{one}.json: reply has an extra key, note" in err
    assert (
        f"{two}.json: passage 1 is filed under question {k + 1}, but there are {k}"
        in err
    )


def test_apply_refuses_a_changed_input_a_changed_run_and_a_drifted_prompt(
    anthropic, tmp_path, capsys, monkeypatch
):
    folders = copied(anthropic, tmp_path)
    out = tmp_path / "packets"
    assert build(folders, out) == 0
    answer_all(out)
    evals = tmp_path / "evals"

    real = grade._digest
    with monkeypatch.context() as patch:
        patch.setattr(
            grade,
            "_digest",
            lambda p: "sha256:0" if p.name == "universe.yaml" else real(p),
        )
        err = refused(capsys, apply(folders, out, evals))
    assert "evals/universe.yaml changed since the Anthropic-side run" in err

    with monkeypatch.context() as patch:
        prompt = adapters.Judge.prompt
        patch.setattr(
            adapters.Judge, "prompt", staticmethod(lambda cases: prompt(cases) + " ")
        )
        err = refused(capsys, apply(folders, out, evals))
    assert "grade.py now sends a prompt no packet holds" in err

    with monkeypatch.context() as patch:
        file = adapters.Models.file
        patch.setattr(
            adapters.Models,
            "file",
            lambda self, model, questions, passages, ask: file(
                self, model, questions, passages, ask + " "
            ),
        )
        err = refused(capsys, apply(folders, out, evals))
    assert "grade.py now sends a prompt no packet holds" in err

    rows = folders["universe"] / "verdicts.jsonl"
    rows.write_text(rows.read_text().replace('"why": ', '"why":  ', 1))
    err = refused(capsys, apply(folders, out, evals))
    assert "universe changed since the packets were built: verdicts.jsonl" in err
    assert not evals.exists()


def test_apply_refuses_replies_moved_without_their_manifest(
    anthropic, tmp_path, capsys
):
    folders = copied(anthropic, tmp_path)
    out = tmp_path / "packets"
    assert build(folders, out) == 0
    answer_all(out)
    moved = tmp_path / "moved"
    for session in (p for p in out.iterdir() if p.is_dir()):
        shutil.copytree(session, moved / session.name)
    evals = tmp_path / "evals"
    err = refused(capsys, apply(folders, moved, evals))
    assert "manifest.json" in err
    assert not evals.exists()


def test_build_refuses_runs_from_the_other_side_and_runs_whose_tiers_did_not_run(
    anthropic, tmp_path, capsys
):
    folders = copied(anthropic, tmp_path)
    path = folders["calibration-skills"] / "calibration.json"
    data = json.loads(path.read_text())
    data["run"]["adapters"]["judgment"] = "judges: codex:a, codex:b"
    path.write_text(json.dumps(data))
    err = refused(capsys, build(folders, tmp_path / "p1"))
    assert "is not an Anthropic-side run: its judgment model codex:a" in err
    del data["run"]["adapters"]["judgment"]
    path.write_text(json.dumps(data))
    err = refused(capsys, build(folders, tmp_path / "p2"))
    assert "its judgment tier did not run" in err


def test_a_calibration_without_the_decision_models_filings_files_without_it(
    anthropic, tmp_path, capsys
):
    folders = copied(anthropic, tmp_path)
    path = folders["calibration-universe"] / "calibration.json"
    data = json.loads(path.read_text())
    data["settled"] = [
        {k: e[k] for k in ("rule", "verdict", "tier")} for e in data["settled"]
    ]
    path.write_text(json.dumps(data))
    out, evals = tmp_path / "packets", tmp_path / "evals"
    assert build(folders, out) == 0
    assert "did not record the decision model's filings" in capsys.readouterr().out
    answer_all(out)
    assert apply(folders, out, evals) == 0
    (folder,) = evals.glob("examples-universe-*")
    run = json.loads((folder / "calibration.json").read_text())["run"]
    assert run["adapters"]["sort"] == (
        "filers: codex:gpt-6-astra, codex:gpt-6.1-sol, codex:gpt-6-luna"
    )
    a_id = data["run"]["id"]
    assert (
        f"sort and recognise: the decision-model filer is left out: {a_id} did not record "
        "its filings"
    ) in run["notes"]
    assert not [
        n for n in run["notes"] if n.startswith("sort and recognise decision tokens")
    ]
    report.summarise(folder, "openai")


def test_calibration_can_score_some_tiers_alone_and_keeps_each_examples_votes():
    from test_evals_grade import fake_spec, judge

    def decide(cases):
        return [tiers.Outcome("pass", "decision", {}) for _ in cases]

    spec = fake_spec()
    spec.universe["rules"]["one-job"]["decision"] = {"ask": "?", "type": "yes-no"}
    settled = []
    table = grade.calibrate(
        spec,
        "universe",
        decide=decide,
        judge=judge,
        alone=["judgment"],
        settled=settled,
    )
    assert [r["tier"] for r in table] == ["judgment", "chain"]
    assert {s["tier"] for s in settled} == {"decision"}

    def voted(cases):
        votes = {"a": {"verdict": "pass", "critique": "c"}}
        return [
            tiers.Outcome("pass", "judgment", {"critique": "c", "votes": votes})
            for _ in cases
        ]

    settled = []
    grade.calibrate(fake_spec(), "universe", judge=voted, settled=settled)
    assert settled[0]["votes"] == {"a": {"verdict": "pass", "critique": "c"}}
