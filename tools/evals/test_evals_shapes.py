"""The whole eval pipeline on universes shaped unlike product-development, with only the model
transports faked: a factor-only universe (notice-readers, with the one placeholder ordering frame
the protocol requires) and a research universe (field-study) with a ladder and a relation edge
gated on a frame other than authority. Each is graded on every tier, recognised over shared cases
and its own answers, sorted, and reported in a section of its own, with and without a retired
list."""

import json
import re
import subprocess
import sys
import zlib
from pathlib import Path

import adapters
import grade
import play
import report
import situations
import spec as spec_module
import yaml

SHAPES = Path(__file__).parent / "fixtures" / "shapes"
FOLDER = SHAPES / "situations"
UNIVERSES = {
    name: SHAPES / f"{name}.universe.kbp.yaml"
    for name in ("notice-readers", "field-study")
}
LIGHT = {grade.LIGHT_MODEL, "codex:light"}
MISREAD = {
    "Full board": "Expedited"
}  # the light model reads this ladder step one lower
OPENAI = ["--judge-model", "codex:careful-a,codex:careful-b", "--light-model", "codex:light"]  # fmt: skip


def shown(value):
    """A value as a reader sees it among the options: Newcomer: Is the subject new to them?"""
    ident = value["id"] if isinstance(value, dict) else value
    name = ident.replace("-", " ").capitalize()
    return f"{name}: {value['question']}" if isinstance(value, dict) else name


def labelled():
    """{(the options as shown, a situation): the number of its right option}, read straight from
    the fixture answers, so the fake readers know the labels without the code under test."""
    pool = {
        c["id"]: c["text"] for c in spec_module.read(FOLDER / "cases.yaml")["cases"]
    }
    right = {}
    for name, path in UNIVERSES.items():
        doc = spec_module.read(path)
        answers = spec_module.read(FOLDER / f"{name}.yaml")
        for section in situations.SECTIONS:
            declared = {d["id"]: d["values"] for d in doc.get(section) or []}
            for key, block in (answers.get(section) or {}).items():
                options = tuple(shown(v) for v in declared[key])
                ids = [v["id"] if isinstance(v, dict) else v for v in declared[key]]
                for case, entry in block["answers"].items():
                    value = entry["value"] if isinstance(entry, dict) else entry
                    right[(options, pool[case])] = ids.index(value) + 1
    return right


def tag(question):
    """A made-up word standing for one question, so a probe can be traced back to it."""
    n = zlib.crc32(question.encode())
    return "".join(chr(97 + (n >> (5 * i)) % 26) for i in range(6))


def numbered(prompt, header):
    """The quoted items listed under a header such as Options: in a prompt."""
    block = prompt.split(f"{header}\n", 1)[1].split("\n\n", 1)[0]
    return [json.loads(line.split(". ", 1)[1]) for line in block.splitlines()]


def pick(options, text, right, model=""):
    """The number of the option a fake reader picks for a situation or a probe."""
    if (tuple(options), text) not in right:  # a probe: the question it was written for
        return next((n for n, q in enumerate(options, 1) if tag(q) in text), 0)
    chosen = options[right[(tuple(options), text)] - 1]
    if model in LIGHT and chosen in MISREAD:
        return options.index(MISREAD[chosen]) + 1
    return right[(tuple(options), text)]


def fake_call(right):
    """The CLI transport: judges pass every item; the writer writes two probes per question;
    every validity judge accepts them; filers and readers pick as `pick` says."""

    def call(prompt, model, schema, system):
        (key,) = schema["required"]
        if key == "verdicts":
            n = int(re.search(r"each of the (\d+) items", prompt).group(1))
            out = [
                {"item": i, "verdict": "pass", "critique": "Meets the rule."}
                for i in range(1, n + 1)
            ]
        elif key == "passages":
            word = tag(prompt.rsplit("Question: ", 1)[1])
            out = [f"Ask {word} now.", f"See {word} now."]
        elif key == "answers":
            out = [
                {"passage": n, "answers": True}
                for n in range(1, len(numbered(prompt, "Passages:")) + 1)
            ]
        elif key == "filings":
            questions = numbered(prompt, "Questions:")
            out = [
                {"passage": n, "question": pick(questions, p, right)}
                for n, p in enumerate(numbered(prompt, "Passages:"), 1)
            ]
        else:
            situation = json.loads(prompt.split("Situation: ", 1)[1].split("\n", 1)[0])
            out = pick(numbered(prompt, "Options:"), situation, right, model)
        return {"structured_output": {key: out}, "total_cost_usd": 0.01}

    return call


def fake_jev(right):
    """The decision model's HTTP transport: a yes-no answer is settled for some texts and unsure
    for others, so both the decision and the judgment tier settle cases; a choice files as
    `pick` says."""

    def post(self, body):
        answers = {}
        for key, asked in body["questions"].items():
            if asked["type"] == "noul":
                state = json.dumps(body["state"], sort_keys=True)
                answers[key] = {"noul": 0.5 if zlib.crc32(state.encode()) % 2 else 0.1}
                continue
            criteria = asked["criteria"]
            options = [criteria[str(n)] for n in range(1, len(criteria) + 1)]
            choice = pick(options, body["state"], right)
            answers[key] = {"choice": str(choice), "confidence": 0.9}
        return {"model": "jev-fake", "usage": {"tokens": 1}, "answers": answers}

    return post


def fake_models(monkeypatch):
    right = labelled()
    monkeypatch.setattr(adapters, "model_call", fake_call(right))
    monkeypatch.setattr(adapters.Jev, "_http", fake_jev(right))
    monkeypatch.setattr(adapters, "unavailable", lambda models: None)
    monkeypatch.setenv("TYPESAFE_API_KEY", "fake")


def graded(tmp_path, name, side, *extra):
    """One run of every tier on a fixture universe; its run.json and verdict rows."""
    out = tmp_path / f"{side}-{name}"
    args = [
        "universe", "--universe", str(UNIVERSES[name]),
        "--situations", str(FOLDER / f"{name}.yaml"), "--label", side, "--out", str(out),
    ]  # fmt: skip
    assert grade.main([*args, *extra]) == 0
    rows = [json.loads(line) for line in (out / "verdicts.jsonl").open()]
    return out, json.loads((out / "run.json").read_text()), rows


def recognised(rows):
    """{set: {value: verdict}} of a run's recognition rows."""
    found = {}
    for r in rows:
        if r["tier"] == "recognise":
            seen = r["recognition"]
            found.setdefault(seen["set"], {})[seen["value"]] = r["verdict"]
    return found


def test_the_fixture_universes_conform_and_gate_an_edge_on_their_own_frame():
    files = [str(p) for p in sorted(SHAPES.glob("*.kbp.yaml"))]
    done = subprocess.run(
        [sys.executable, str(play.CHECKER), "--validate", *files],
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 0, done.stdout + done.stderr
    study = spec_module.read(UNIVERSES["field-study"])
    frames = {f["id"] for f in study["frames"]}
    gates = [r["gate"] for r in study["relations"] if r.get("gate")]
    assert "authority" not in frames
    assert gates == [{"setting": "field", "latency": "7d"}]
    readers = spec_module.read(UNIVERSES["notice-readers"])
    assert readers["elements"] == [] and [f["values"] for f in readers["frames"]] == [
        ["only"]
    ]


def test_the_shared_cases_and_each_universes_answers_have_no_problems():
    universes = {n: spec_module.read(p) for n, p in UNIVERSES.items()}.get
    assert situations.folder_problems(FOLDER, universes) == []
    pool = spec_module.read(FOLDER / "cases.yaml")
    shared = next(c for c in pool["cases"] if c["id"] == "n13")
    study = spec_module.read(FOLDER / "field-study.yaml")
    assert (
        shared["field"] == "notice-readers"
        and "n13" in study["frames"]["review"]["answers"]
    )


def test_a_factor_only_universe_is_graded_recognised_and_has_nothing_to_sort(
    tmp_path, monkeypatch
):
    fake_models(monkeypatch)
    out, run, rows = graded(tmp_path, "notice-readers", "claude")
    assert run["universe"] == "notice-readers"
    assert run["tiers"] == list(grade.ALL_TIERS)
    assert set(run["adapters"]) == set(grade.ALL_TIERS) - {"deterministic"}
    guidance = "tools/evals/fixtures/shapes/notice-readers.guidance.kbp.yaml"
    assert guidance in run["inputs"]
    assert (
        "tools/evals/fixtures/shapes/situations/cases.yaml (cases used)"
        in run["inputs"]
    )
    assert "subject artifact.composition selected no text" in run["notes"]
    assert not [n for n in run["notes"] if "not run" in n]
    # the placeholder ordering frame has one value: no choice, so nothing to recognise
    assert recognised(rows) == {
        "familiarity": dict.fromkeys(("newcomer", "regular", "specialist"), "pass"),
        "attention": dict.fromkeys(("glance", "close-reading"), "pass"),
    }
    assert not [r for r in rows if r["tier"] == "sort"]
    assert {r["subject"] for r in rows if r["tier"] in ("decision", "judgment")} >= {
        "guidance.claim",
        "factor.own_question",
    }
    assert "owner" not in {r["tier"] for r in rows}
    text = (out / "report.md").read_text()
    assert "| familiarity | 3 | 13 |" in text and "| stage |" not in text


def test_a_universe_with_a_ladder_and_a_gated_edge_is_graded_recognised_and_sorted(
    tmp_path, monkeypatch
):
    fake_models(monkeypatch)
    out, run, rows = graded(tmp_path, "field-study", "claude")
    assert run["universe"] == "field-study"
    assert not [name for name in run["inputs"] if "guidance" in name]
    assert (out / "probes.json").exists()
    sorted_rows = [r for r in rows if r["tier"] == "sort"]
    assert [r["verdict"] for r in sorted_rows] == ["pass"] * 5
    assert {r["ref"].split(".")[0] for r in sorted_rows} == {
        "artifacts[study-protocol]",
        "artifacts[results-summary]",
    }
    assert recognised(rows) == {
        "stage": dict.fromkeys(("plan", "collect", "analyse"), "pass"),
        "review": {"exempt": "pass", "expedited": "pass", "full-board": "fail"},
        "setting": dict.fromkeys(("laboratory", "field"), "pass"),
    }
    review = {r["recognition"]["value"]: r for r in rows if r.get("recognition", {}).get("set") == "review"}  # fmt: skip
    # the case from notice-readers' field is filed here too, beside the four of this field
    assert review["expedited"]["recognition"]["situations"] == 5
    light = review["full-board"]["recognition"]["filers"][grade.LIGHT_MODEL]
    assert light["off_by_one"] == 4 and light["right"] == 13 - 4
    assert "owner" not in {r["tier"] for r in rows}
    text = (out / "report.md").read_text()
    assert "| review | 3 | 13 |" in text and "4 off by one" in text


def retired_for(folder, universe):
    folder.mkdir()
    (folder / f"{universe}.yaml").write_text(
        yaml.safe_dump(
            {
                "decision": "Owner: the review frame's question was reworded.",
                "graded_in": "an-earlier-run",
                "fails": [
                    {
                        "rule": "one-question",
                        "ref": "frames[review].question",
                        "text": "Who reviews the study, and how?",
                    }
                ],
            }
        )
    )
    return report.load_retired(folder)


def test_each_universe_gets_its_own_report_section_and_retired_list(
    tmp_path, monkeypatch
):
    fake_models(monkeypatch)
    entries = []
    for name in UNIVERSES:
        anthropic, _, _ = graded(tmp_path, name, "anthropic")
        probes = ["--probes", str(anthropic / "probes.json")] if name == "field-study" else []  # fmt: skip
        openai, _, _ = graded(tmp_path, name, "openai", *OPENAI, *probes)
        entries += [
            {"side": "anthropic", "id": anthropic.name},
            {"side": "openai", "id": openai.name},
        ]
    runs = tmp_path / "runs.yaml"
    runs.write_text(yaml.safe_dump({"runs": entries}))
    results, out = tmp_path / "results", tmp_path / "report.md"
    retired = retired_for(tmp_path / "retired", "field-study")
    report.write_all(runs, results, out, retired, run_folders=tmp_path)
    assert report.drift(runs, results, out, retired) == []
    text = out.read_text()
    study = text.split("\n## Universe `field-study`")[1].split("\n## ")[0]
    readers = text.split("\n## Universe `notice-readers`")[1].split("\n## ")[0]
    assert text.index("## Universe `field-study`") < text.index(
        "## Universe `notice-readers`"
    )
    for section, name in ((study, "field-study"), (readers, "notice-readers")):
        assert f"`openai-{name}`" in section and f"`anthropic-{name}`" in section
        other = "notice-readers" if name == "field-study" else "field-study"
        assert other not in section
        assert "not comparable" not in section
    assert (
        "| 3 frames: 2 pass, 1 fail, 0 undecided, 0 not run; "
        "1 of 8 values fail (all readers); 0 of 8 (careful readers only) |"
    ) in study
    assert "same verdict on 3 of 3 frames" in study
    assert (
        "| 2 factors: 2 pass, 0 fail, 0 undecided, 0 not run; "
        "0 of 5 values fail (all readers); 0 of 5 (careful readers only) |"
    ) in readers
    assert "same verdict on 2 of 2 factors" in readers
    assert "The sides differ on 0 of 2 factors." in readers
    assert re.search(
        r"\| Sorting \| [^|]+ \| 5 members: 5 pass, 0 fail, 0 undecided \|", study
    )
    # a universe with no artifact has nothing to sort, so no run holds a sorting figure
    assert re.search(
        r"\| Sorting \| [^|]+ \| not run \| not run \| not run \|", readers
    )
    assert "Sorting of `notice-readers`: not run on either side." in readers
    assert "### Retired for frames of `field-study`" in study
    assert "Who reviews the study, and how?" in study
    assert "Retired" not in readers
    assert "jev None" not in text  # a decision model asked nothing has no version
    assert "product-development" not in text
