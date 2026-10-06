"""The report builder: run folders in, small summaries and evals/report.md out, no model calls."""

import json
import re
from pathlib import Path

import pytest
import report
import yaml

ROOT = Path(__file__).resolve().parents[2]
NO_FAILS = {"decision": "d", "graded_in": "run-0", "fails": []}
RETIRED = {"x": NO_FAILS}
INPUTS = {
    "evals/universe.yaml": "sha256:u1",
    "evals/skills.yaml": "sha256:s1",
    "universes/x/universe.kbp.yaml": "sha256:x1",
    "universes/x/type-guidance.kbp.yaml": "sha256:g1",
    "evals/situations/x.yaml": "sha256:sit1",
}


def run_json(
    run_id,
    kind,
    inputs=None,
    tiers=(),
    adapters=None,
    notes=(),
    label="",
    universe=None,
):
    return {
        "id": run_id,
        "kind": kind,
        "inputs": dict(INPUTS if inputs is None else inputs),
        "adapters": adapters or {},
        "tiers": list(tiers),
        "notes": list(notes),
        "label": label,
        **({"universe": universe} if universe else {}),
    }


def row(rule, ref, verdict, tier, votes=None, **extra):
    trail = []
    if votes:
        said = {m: {"verdict": v, "critique": ""} for m, v in votes.items()}
        trail.append({"tier": "judgment", "verdict": verdict, "votes": said})
    return {
        "rule": rule,
        "ref": ref,
        "text": extra.pop("text", ref),
        "verdict": verdict,
        "tier": tier,
        "trail": trail,
        **extra,
    }


def grade_folder(path, rows, probes=None, **kwargs):
    path.mkdir(parents=True)
    kwargs.setdefault("tiers", ["deterministic", "decision", "judgment"])
    kwargs.setdefault("universe", "x")
    (path / "run.json").write_text(
        json.dumps(run_json(path.name, "universe", **kwargs))
    )
    (path / "verdicts.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    if probes is not None:
        (path / "probes.json").write_text(probes)
    return path


def calibration_folder(
    path, table, misses=(), slice_="universe", inputs=None, settled=None
):
    path.mkdir(parents=True)
    run = run_json(path.name, slice_, inputs=inputs, tiers=["judgment"])
    data = {"run": run, "table": table, "misses": list(misses)}
    if settled is not None:
        data["settled"] = settled
    (path / "calibration.json").write_text(json.dumps(data))
    return path


def chain(rule, n, tp, fn, tn, fp, undecided):
    return {
        "rule": rule, "tier": "chain", "n": n, "tp": tp, "fn": fn, "tn": tn,
        "fp": fp, "undecided": undecided,
    }  # fmt: skip


ANTHROPIC_ROWS = [
    row("r1", "c1", "pass", "judgment", {"a": "pass", "b": "pass"}),
    row("r1", "c2", "fail", "judgment", {"a": "fail", "b": "fail"}),
    row("r1", "c3", "undecided", "judgment", {"a": "pass", "b": "fail"}),
    row("r1", "c4", "pass", "decision"),
]
OPENAI_ROWS = [
    row("r1", "c1", "pass", "judgment", {"c": "pass", "d": "pass"}),
    row("r1", "c2", "undecided", "judgment", {"c": "fail", "d": "pass"}),
    row("r1", "c3", "pass", "judgment", {"c": "pass", "d": "pass"}),
    row("r1", "c4", "pass", "decision"),
]


def summary(path, side="anthropic"):
    return report.summarise(path, side)


def test_a_grade_run_is_summarised_in_counts_and_only_the_cases_that_matter(tmp_path):
    folder = grade_folder(
        tmp_path / "grade-1",
        ANTHROPIC_ROWS,
        probes='{"p": 1}',
        adapters={"judgment": "judges: a, b"},
        notes=["judgment cost: $1.50"],
        label="anthropic-side",
    )
    s = summary(folder)
    assert (s["id"], s["side"], s["kind"], s["label"]) == (
        "grade-1", "anthropic", "grade", "anthropic-side",
    )  # fmt: skip
    assert s["measures"] == ["grade"]
    assert s["rules"] == {
        "r1": {
            "pass": 2, "fail": 1, "undecided": 1,
            "settled": {"judgment": 2, "decision": 1},
        }
    }  # fmt: skip
    assert s["judges"] == ["a", "b"]
    assert s["judged"] == {"r1": 3}
    assert s["cases"] == {
        "r1": {
            "c2": ["fail", "judgment", "ff"],
            "c3": ["undecided", "judgment", "pf"],
        }
    }
    assert s["settled_by"] == {
        "r1": {"c1": "judgment", "c2": "judgment", "c4": "decision"}
    }
    assert s["inputs"]["probes.json"].startswith("sha256:")
    assert s["adapters"] == {"judgment": "judges: a, b"}
    assert s["notes"] == ["judgment cost: $1.50"]
    assert "pass" not in json.dumps(s["cases"])


def test_a_run_with_sort_and_recognise_tiers_also_counts_as_those_measures(tmp_path):
    rows = [
        row(
            "sorts-reliably", "m1", "fail", "sort", text="Q1",
            trail=[{"tier": "sort", "verdict": "fail", "placed": {"f1": ["Q1", "Q2", "unsure"], "f2": ["Q1", "Q1", "Q1"]}}],
        ),
        row(
            "sorts-reliably", "m2", "pass", "sort", text="Q2",
            trail=[{"tier": "sort", "verdict": "pass"}],
        ),
        row(
            "values-recognised", "frames[entry].values[open]", "pass", "recognise",
            recognition={
                "set": "entry", "value": "open", "situations": 4,
                "right": {"f1": 4, "f2": 3},
                "filers": {
                    "f1": {"right": 8, "n": 8, "unsure": 0, "none": 0},
                    "f2": {"right": 6, "n": 8, "unsure": 1, "none": 1},
                },
                "misses": {},
            },
        ),
        row(
            "values-recognised", "frames[entry].values[ticketed]", "fail", "recognise",
            recognition={
                "set": "entry", "value": "ticketed", "situations": 4,
                "right": {"f1": 4, "f2": 1},
                "filers": {
                    "f1": {"right": 8, "n": 8, "unsure": 0, "none": 0},
                    "f2": {"right": 6, "n": 8, "unsure": 1, "none": 1},
                },
                "misses": {},
            },
        ),
    ]  # fmt: skip
    s = summary(grade_folder(tmp_path / "g", rows, tiers=["sort", "recognise"]))
    assert s["measures"] == ["sorting", "recognition"]
    assert s["sorting"] == {
        "rules": ["sorts-reliably"],
        "members": {"pass": 1, "fail": 1, "undecided": 0},
        "filers": {
            "f1": {"right": 1, "n": 3, "unsure": 1},
            "f2": {"right": 3, "n": 3, "unsure": 0},
        },
    }
    assert s["recognition"] == {
        "entry": {
            "kind": "frame",
            "values": 2,
            "situations": 8,
            "filers": {
                "f1": {"right": 8, "n": 8, "unsure": 0, "none": 0},
                "f2": {"right": 6, "n": 8, "unsure": 1, "none": 1},
            },
            "lowest": {"value": "ticketed", "right": 1, "situations": 4, "filer": "f2"},
            "misses": [],
            "verdict": "fail",
            "fails": 1,
            "careful": None,
        }
    }


def test_a_recognition_set_with_no_situations_reads_not_run(tmp_path):
    rows = [
        row(
            "values-recognised", "frames[entry].values[open]", "undecided", "recognise",
            trail=[{"tier": "recognise", "verdict": "undecided"}],
            recognition={
                "set": "entry", "value": "open", "situations": 0,
                "right": {"f1": 0}, "filers": {"f1": {"right": 0, "n": 0, "unsure": 0, "none": 0}},
                "misses": {},
            },
        )
    ]  # fmt: skip
    s = summary(grade_folder(tmp_path / "g", rows, tiers=["recognise"]))
    assert s["recognition"]["entry"]["verdict"] == "not run"
    assert s["recognition"]["entry"]["lowest"] is None


def test_a_calibration_run_keeps_its_table_and_misses(tmp_path):
    table = [
        {**chain("r1", 6, 3, 0, 3, 0, 0), "tier": "judgment"},
        chain("r1", 6, 3, 0, 3, 0, 0),
    ]
    miss = {
        "tier": "judgment",
        "rule": "r1",
        "text": "t",
        "label": "fail",
        "reason": "long",
    }
    s = summary(calibration_folder(tmp_path / "cal", table, [miss]), "openai")
    assert (s["kind"], s["slice"], s["measures"], s["side"]) == (
        "calibration", "universe", ["calibration-universe"], "openai",
    )  # fmt: skip
    assert s["table"] == table
    assert s["misses"] == [
        {"tier": "judgment", "rule": "r1", "text": "t", "label": "fail"}
    ]
    skills = summary(calibration_folder(tmp_path / "cal2", table, slice_="skills"))
    assert skills["measures"] == ["calibration-skills"]


CHECKS = {
    "skill": "kb-ingest",
    "skill fired": True,
    "writes outside .knowledge-bus": [],
    "conforms_to changed": [],
    "validates": {"before": True, "after": True, "kept": True},
    "loaded beside the skills under test": [],
    "possible script drift": [],
    "agent error": None,
}


def play_folder(path, rows, checks=None, wording=(), notes=()):
    """A play run folder: its verdicts, each run's checks.json and the wording/ verdicts."""
    path.mkdir(parents=True)
    run = run_json(path.name, "skills", notes=notes)
    (path / "run.json").write_text(json.dumps(run))
    (path / "verdicts.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    for prefix, found in (checks or {}).items():
        (path / prefix).mkdir(parents=True)
        (path / prefix / "checks.json").write_text(json.dumps(found))
    if wording:
        (path / "wording").mkdir()
        (path / "wording/verdicts.jsonl").write_text(
            "".join(json.dumps(r) + "\n" for r in wording)
        )
    return path


def test_a_skills_run_is_a_scenario_run(tmp_path):
    rows = [row("asks", "choir/run-1/transcript[1]", "pass", "judgment")]
    broken = {**CHECKS, "skill": "kb-check", "agent error": "turn 0: exit code 1"}
    folder = play_folder(
        tmp_path / "play",
        rows,
        checks={"choir/run-1": CHECKS, "permits/run-1": broken},
        wording=[
            row("one-job", "choir/run-1/x:elements[a].question", "fail", "judgment"),
            row("one-job", "choir/run-1/x:elements[b].question", "pass", "judgment"),
        ],
        notes=["bakery: not run, its fixture is still to be built"],
    )
    s = summary(folder)
    assert (s["kind"], s["measures"], s["scenarios"], s["n"]) == (
        "scenarios",
        ["scenarios"],
        ["choir", "permits"],
        1,
    )
    assert s["checks"] == {"choir/run-1": CHECKS, "permits/run-1": broken}
    assert s["ungraded"] == ["bakery", "permits/run-1"]
    assert s["wording"] == {"one-job": {"pass": 1, "fail": 1, "undecided": 0}}


def test_the_scenarios_section_shows_behaviours_skills_code_checks_and_wording(
    tmp_path,
):
    drifted = {
        **CHECKS,
        "possible script drift": [1],
        "writes outside .knowledge-bus": ["a.md"],
    }
    folder = play_folder(
        tmp_path / "play",
        [row("asks", "choir/run-1/transcript[1]", "pass", "judgment")],
        checks={"choir/run-1": drifted},
        wording=[row("one-job", "choir/run-1/x:e", "fail", "judgment")],
        notes=["bakery: not run, its fixture is still to be built"],
    )
    section = (
        build(summary(folder)).split("\n## Agent scenarios\n")[1].split("\n## ")[0]
    )
    assert "Each scenario ran once (n=1).\n" in section
    assert "not a rate" not in section
    assert "| `asks` | 1 | 0 | 0 |" in section
    assert "| kb-ingest | 1 | 1 |" in section
    assert (
        "| `choir/run-1` | yes | a.md | n/a | none | before yes, after yes | none "
        "| before owner reply 1 | none |"
    ) in section
    assert "Not graded: `bakery`." in section
    assert "| `one-job` | 0 | 1 | 0 |" in section


def test_home_folder_paths_in_tool_writes_are_shown_from_the_home_folder(
    tmp_path, monkeypatch
):
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    outside = [f"{home}/.claude/projects/x/a.jsonl", f"{home}2/b.md", "/tmp/c.md"]
    folder = play_folder(
        tmp_path / "play",
        [row("asks", "choir/run-1/transcript[1]", "pass", "judgment")],
        checks={"choir/run-1": {**CHECKS, report.TOOL_WRITES: outside}},
    )
    s = summary(folder)
    assert s["checks"]["choir/run-1"][report.TOOL_WRITES] == [
        "~/.claude/projects/x/a.jsonl",
        f"{home}2/b.md",
        "/tmp/c.md",
    ]
    assert str(home) + "/" not in build(s)


def test_a_run_played_before_the_drift_check_was_renamed_still_shows_its_drift(
    tmp_path,
):
    old = {k: v for k, v in CHECKS.items() if k != "possible script drift"}
    folder = play_folder(
        tmp_path / "play",
        [row("asks", "choir/run-1/transcript[1]", "pass", "judgment")],
        checks={"choir/run-1": {**old, "script drift": [2]}},
    )
    section = (
        build(summary(folder)).split("\n## Agent scenarios\n")[1].split("\n## ")[0]
    )
    assert "| Possible script drift |" in section
    assert "| before owner reply 2 | none |" in section


def entries_file(tmp_path, *entries):
    path = tmp_path / "runs.yaml"
    path.write_text(yaml.safe_dump({"runs": list(entries)}))
    return path


def build(*summaries, retired=None):
    return report.build(list(summaries), RETIRED if retired is None else retired)


def two_sides(tmp_path, openai_inputs=None):
    anthropic = summary(
        grade_folder(tmp_path / "anthropic-run", ANTHROPIC_ROWS, probes="[]"),
        "anthropic",
    )
    openai = summary(
        grade_folder(
            tmp_path / "openai-run", OPENAI_ROWS, probes="[]", inputs=openai_inputs
        ),
        "openai",
    )
    return anthropic, openai


def headline(text, universe=None):
    """The headline table: the universe-independent one, or the named universe's."""
    mark = f"### Headline of `{universe}`" if universe else "## Headline"
    block = re.split(r"\n#{2,3} ", text.split(mark)[1])[0]
    return {
        cells[0]: cells[1:]
        for cells in (
            [c.strip() for c in line.strip("|").split("|")]
            for line in block.splitlines()
            if line.startswith("|") and "---" not in line
        )
        if cells[0] != "Measure"
    }


def test_with_no_runs_every_measure_reads_not_run():
    text = build()
    tables = [headline(text), headline(text, "x")]
    assert [len(t) for t in tables] == [3, 4]
    for measure, cells in {**tables[0], **tables[1]}.items():
        assert cells[1:] == ["not run", "not run", "not run"], measure
    assert "No run is listed in `evals/runs.yaml`." in text
    assert "development examples (interim)" in text
    assert "development situations (interim)" in text
    assert "each scenario's figure says how many times it ran (n)" in text


def test_the_report_has_the_designed_sections_in_order():
    headings = [line for line in build().splitlines() if line.startswith("## ")]
    assert headings == [
        "## Headline",
        "## Calibration",
        "## Agent scenarios",
        "## Where the sides disagree",
        "## Universe `x`",
        "## Cost and models",
        "## Not measured here",
        "## How to reproduce",
    ]


def test_the_report_says_sides_are_compared_and_what_is_not_measured():
    text = build()
    assert (
        "Sides are compared only when the inputs a measure depends on have the same "
        "digests." in text
    )
    assert "side by side" not in text
    unmeasured = text.split("\n## Not measured here\n")[1].split("\n## ")[0]
    assert unmeasured.strip().splitlines() == [
        "- Effect on outcomes: whether these universes and skills change what people get done.",
        "- How often agent behaviours pass over many runs.",
        "- Owners who go off script, and whether the definitions fit real work.",
        "- Whether wording is plain to people rather than models.",
    ]


def test_the_docstring_says_sides_and_universes_are_compared_not_put_side_by_side():
    doc = " ".join(report.__doc__.split())
    assert "runs of different universes are never compared." in doc
    assert (
        "Sides are compared only when the inputs a measure depends on have the same "
        "digests." in doc
    )
    assert "side by side" not in doc


def test_one_side_shows_its_figure_and_the_other_reads_not_run(tmp_path):
    anthropic, _ = two_sides(tmp_path)
    cells = headline(build(anthropic), "x")["Universe grade"]
    assert cells[1] == "4 cases: 2 pass, 1 fail, 1 undecided"
    assert cells[2:] == ["not run", "not run"]


def test_comparable_sides_are_put_side_by_side_with_their_agreement(tmp_path):
    anthropic, openai = two_sides(tmp_path)
    text = build(anthropic, openai)
    cells = headline(text, "x")["Universe grade"]
    assert cells[1:] == [
        "4 cases: 2 pass, 1 fail, 1 undecided",
        "4 cases: 3 pass, 0 fail, 1 undecided",
        "the two companies' judges agree on 1 of 1; 1 more settled the same way by shared code or Jev",
    ]
    assert (
        "- `r1` `c2`: Anthropic side fail (judgment), OpenAI side undecided (judgment)"
        in text
    )
    assert "- `r1` `c3`: Anthropic side undecided (judgment), OpenAI side pass" in text


def test_sides_with_different_inputs_are_never_put_side_by_side(tmp_path):
    other = {**INPUTS, "universes/x/universe.kbp.yaml": "sha256:changed"}
    anthropic, openai = two_sides(tmp_path, openai_inputs=other)
    text = build(anthropic, openai)
    cells = headline(text, "x")["Universe grade"]
    assert cells[1:] == [
        "not comparable: universes/x/universe.kbp.yaml differs",
        "not comparable: universes/x/universe.kbp.yaml differs",
        "not comparable",
    ]
    assert "4 cases: 2 pass" not in text
    disagree = text.split("### Where the sides disagree on `x`")[1].split("\n## ")[0]
    assert "`c2`" not in disagree
    assert "not comparable: universes/x/universe.kbp.yaml differs" in disagree


def test_an_inputs_kind_is_the_one_its_run_recorded(tmp_path):
    notes = "universes/x/notes.kbp.yaml"
    folder = grade_folder(tmp_path / "g", ANTHROPIC_ROWS)
    stored = json.loads((folder / "run.json").read_text())
    stored["kinds"] = {notes: "guidance"}
    (folder / "run.json").write_text(json.dumps(stored))
    a = summary(folder) | {"recognition": {}, "inputs": {**INPUTS, notes: "sha256:n1"}}
    assert a["kinds"] == {notes: "guidance"}
    b = a | {"inputs": {**INPUTS, notes: "sha256:n2"}}
    assert report.different("recognition", a, b) is None
    assert report.different("recognition", a | {"kinds": {}}, b | {"kinds": {}}) == (
        f"{notes} differs"
    )


def test_a_changed_guidance_does_not_stop_the_sorting_figures_being_compared(tmp_path):
    changed = {**INPUTS, "universes/x/type-guidance.kbp.yaml": "sha256:other"}
    anthropic, openai = two_sides(tmp_path, openai_inputs=changed)
    cells = headline(build(anthropic, openai), "x")
    assert cells["Universe grade"][3] == "not comparable"
    assert cells["Sorting"][1:] == ["not run"] * 3


def test_sorting_is_compared_only_on_the_same_probes(tmp_path):
    def sorted_run(name, probes):
        rows = [
            row("sorts-reliably", "m1", "pass", "sort", text="Q",
                trail=[{"tier": "sort", "verdict": "pass", "placed": {"f": ["Q"]}}]),
        ]  # fmt: skip
        return summary(
            grade_folder(tmp_path / name, rows, probes=probes, tiers=["sort"])
        )

    same = build(sorted_run("a", "[1]"), {**sorted_run("b", "[1]"), "side": "openai"})
    assert headline(same, "x")["Sorting"][1:] == [
        "1 member: 1 pass, 0 fail, 0 undecided",
        "1 member: 1 pass, 0 fail, 0 undecided",
        "same verdict on 1 of 1 cases both sides settled",
    ]
    other = {**sorted_run("c", "[2]"), "side": "openai"}
    assert (
        headline(build(sorted_run("d", "[1]"), other), "x")["Sorting"][3]
        == "not comparable"
    )
    assert "probes.json differs" in build(sorted_run("e", "[1]"), other)


def test_calibration_is_labelled_interim_and_compared_by_rule(tmp_path):
    table = [chain("r1", 6, 3, 0, 3, 0, 0), chain("r2", 4, 1, 1, 2, 0, 0)]
    a = summary(calibration_folder(tmp_path / "a", table), "anthropic")
    b = summary(
        calibration_folder(tmp_path / "b", [table[0], chain("r2", 4, 2, 0, 2, 0, 0)]),
        "openai",
    )
    text = build(a, b)
    cells = headline(text)[
        "Calibration, universe rules (development examples, interim)"
    ]
    assert cells[1:] == [
        "10 examples: 4 fails caught, 1 missed, 5 passes kept, 0 wrongly failed, 0 undecided",
        "10 examples: 5 fails caught, 0 missed, 5 passes kept, 0 wrongly failed, 0 undecided",
        "same on 1 of 2 rules",
    ]
    assert "calibrated on development examples (interim)" in text


def test_cross_vendor_judge_pairs_are_worked_out_from_each_judges_vote(tmp_path):
    anthropic, openai = two_sides(tmp_path)
    text = build(anthropic, openai)
    pairs = text.split("Judge pairs across the sides on `x`")[1].split("\n### ")[0]
    rows = {
        cells[0]: cells[1:]
        for cells in (
            [c.strip() for c in line.strip("|").split("|")]
            for line in pairs.splitlines()
            if line.startswith("|") and "---" not in line
        )
    }
    assert rows == {
        "Pair": ["Cases", "Pass", "Fail", "Undecided"],
        "a + c": ["3", "2", "1", "0"],
        "a + d": ["3", "2", "0", "1"],
        "b + c": ["3", "1", "1", "1"],
        "b + d": ["3", "1", "0", "2"],
    }


def test_judge_pairs_need_votes_on_both_sides(tmp_path):
    old = [row("r1", "c1", "pass", "judgment")]
    anthropic = summary(grade_folder(tmp_path / "x", old), "anthropic")
    openai = summary(grade_folder(tmp_path / "y", old), "openai")
    pairs = build(anthropic, openai).split("Judge pairs across the sides on `x`")[1]
    assert "not run" in pairs.split("\n## ")[0]


def test_a_scenario_figure_says_how_many_times_each_scenario_ran(tmp_path):
    once = [row("asks", "choir/run-1/transcript[1]", "pass", "judgment")]
    cells = headline(build(summary(play_folder(tmp_path / "a", once))))
    assert cells["Agent scenarios"][1] == (
        "1 check over 1 scenario, each run once (n=1): 1 pass, 0 fail, 0 undecided"
    )
    twice = [*once, row("asks", "choir/run-2/transcript[1]", "fail", "judgment")]
    cells = headline(build(summary(play_folder(tmp_path / "b", twice))))
    assert cells["Agent scenarios"][1] == (
        "2 checks over 1 scenario, each run 2 times (n=2): 1 pass, 1 fail, 0 undecided"
    )


def reproduce(text):
    return text.split("\n## How to reproduce\n")[1]


def test_the_reproduce_command_plays_as_many_runs_as_the_recorded_scenario_run(
    tmp_path,
):
    thrice = [
        row("asks", f"choir/run-{n}/transcript[1]", "pass", "judgment")
        for n in (1, 2, 3)
    ]
    three = summary(play_folder(tmp_path / "a", thrice))
    assert "\njust evals-play --runs 3\n" in reproduce(build(three))
    also_three = summary(play_folder(tmp_path / "b", thrice), "openai")
    assert "\njust evals-play --runs 3\n" in reproduce(build(three, also_three))
    once = summary(play_folder(tmp_path / "c", thrice[:1]), "openai")
    assert "\njust evals-play\n" in reproduce(build(three, once))
    assert "\njust evals-play\n" in reproduce(build())


def test_the_grade_counts_only_rules_no_filing_check_settles(tmp_path):
    recognised = row(
        "values-recognised", "frames[a].values[x]", "pass", "recognise",
        trail=[{"tier": "recognise", "verdict": "pass"}],
    )  # fmt: skip
    unsettled = row("values-recognised", "frames[a].values[x]", "undecided", "owner")
    anthropic = summary(
        grade_folder(
            tmp_path / "anthropic", [*ANTHROPIC_ROWS, recognised], probes="[]",
            tiers=["deterministic", "decision", "judgment", "recognise"],
        )
    )  # fmt: skip
    openai = summary(
        grade_folder(tmp_path / "openai", [*OPENAI_ROWS, unsettled], probes="[]"),
        "openai",
    )
    assert anthropic["filed"] == ["values-recognised"] and openai["filed"] == []
    assert "values-recognised" not in openai["rules"]
    cells = headline(build(anthropic, openai), "x")["Universe grade"]
    assert cells[1:] == [
        "4 cases: 2 pass, 1 fail, 1 undecided",
        "4 cases: 3 pass, 0 fail, 1 undecided",
        "the two companies' judges agree on 1 of 1; 1 more settled the same way by shared code or Jev",
    ]


def test_a_filing_check_that_filed_nothing_reads_not_run(tmp_path):
    s = summary(
        grade_folder(
            tmp_path / "g", ANTHROPIC_ROWS, tiers=["judgment", "sort", "recognise"]
        )
    )
    cells = headline(build(s), "x")
    assert cells["Sorting"][1] == "not run"
    assert cells["Recognition by frame (development situations, interim)"][1] == (
        "not run"
    )


def test_where_recognition_misses_went_is_summarised_and_shown(tmp_path):
    misses = {
        "s1": {"f1": "Open", "f2": "unsure"},
        "s2": {"f1": "Open", "f2": "none of the questions"},
    }
    rows = [
        row(
            "values-recognised", "frames[entry].values[ticketed]", "fail", "recognise",
            text="Ticketed",
            recognition={
                "set": "entry", "value": "ticketed", "situations": 4,
                "right": {"f1": 2, "f2": 2},
                "filers": {"f1": {"right": 2, "n": 4, "unsure": 0, "none": 0}},
                "misses": misses,
            },
        )
    ]  # fmt: skip
    s = summary(grade_folder(tmp_path / "g", rows, tiers=["recognise"]))
    assert s["recognition"]["entry"]["misses"] == [
        ["Ticketed", "Open", {"f1": 2}],
        ["Ticketed", "unsure", {"f2": 1}],
        ["Ticketed", "none", {"f2": 1}],
    ]
    section = build(s).split("### Recognition by frame of `x`, Anthropic side")[1]
    assert "- entry: Ticketed → Open (f1 2)\n" in section
    assert "- entry: Ticketed → none (f2 1)\n" in section


def recognised(value, text, verdict, placed):
    """A recognition row of the set `entry` whose trail keeps each reader's placements."""
    situations = len(next(iter(placed.values())))
    return row(
        "values-recognised", f"frames[entry].values[{value}]", verdict, "recognise",
        text=text,
        trail=[{"tier": "recognise", "verdict": verdict, "placed": placed}],
        recognition={
            "set": "entry", "value": value, "situations": situations,
            "right": {f: ls.count(text) for f, ls in placed.items()},
            "filers": {}, "misses": {},
        },
    )  # fmt: skip


# Only the light reader misses: it files three of the four Ticketed situations under Open.
LIGHT_MISSES = [
    recognised(
        "open", "Open", "pass",
        {"a": ["Open"] * 4, "b": ["Open"] * 4, "jev": ["Open"] * 4, "light": ["Open"] * 4},
    ),
    recognised(
        "ticketed", "Ticketed", "fail",
        {
            "a": ["Ticketed"] * 4, "b": ["Ticketed"] * 4, "jev": ["Ticketed"] * 4,
            "light": ["Open", "Open", "Open", "Ticketed"],
        },
    ),
]  # fmt: skip
CAREFUL = {
    "judgment": "judges: a, b",
    "recognise": "filers: a, b, jev jev-1.0, light",
}
# the careful count reuses the shares in evals/universe.yaml only for a run graded under it
SAME_SPEC = {**INPUTS, "evals/universe.yaml": report.digest(report.SPEC)}
RECOGNITION = "Recognition by frame (development situations, interim)"


def test_recognition_counts_the_failing_values_again_with_the_careful_readers_only(
    tmp_path,
):
    s = summary(
        grade_folder(
            tmp_path / "g",
            LIGHT_MISSES,
            tiers=["judgment", "recognise"],
            adapters=CAREFUL,
            inputs=SAME_SPEC,
        )
    )
    assert s["recognition"]["entry"]["fails"] == 1
    assert s["recognition"]["entry"]["careful"] == {"readers": ["a", "b"], "fails": 0}
    text = build(s)
    assert headline(text, "x")[RECOGNITION][1] == (
        "1 frame: 0 pass, 1 fail, 0 undecided, 0 not run; "
        "1 of 2 values fail (all readers); 0 of 2 (careful readers only)"
    )
    section = text.split("### Recognition by frame of `x`, Anthropic side")[1]
    assert (
        "1 of 2 values fail (all readers); 0 of 2 (careful readers only). "
        "The careful readers are this side's judgment models: a, b.\n"
    ) in section


def test_the_careful_readers_verdict_is_the_recognition_rule_of_sort_py(tmp_path):
    # a careful reader that misfiles fails the value under the same bar as every reader
    rows = [
        LIGHT_MISSES[0],
        recognised(
            "ticketed", "Ticketed", "fail",
            {"a": ["Open", "Open", "Ticketed", "Ticketed"], "b": ["Ticketed"] * 4},
        ),
    ]  # fmt: skip
    s = summary(
        grade_folder(
            tmp_path / "g",
            rows,
            tiers=["judgment", "recognise"],
            adapters=CAREFUL,
            inputs=SAME_SPEC,
        )
    )
    assert s["recognition"]["entry"]["careful"] == {"readers": ["a", "b"], "fails": 1}


def test_a_careful_reader_with_no_placements_leaves_the_careful_count_undecided(
    tmp_path,
):
    rows = [
        recognised("open", "Open", "undecided", {"a": ["Open"] * 4, "light": ["Open"] * 4}),
        recognised("ticketed", "Ticketed", "undecided", {"a": ["Ticketed"] * 4}),
    ]  # fmt: skip
    s = summary(
        grade_folder(
            tmp_path / "g",
            rows,
            tiers=["judgment", "recognise"],
            adapters=CAREFUL,
            inputs=SAME_SPEC,
        )
    )
    assert s["recognition"]["entry"]["careful"] == {"readers": ["a", "b"], "fails": 0}


def test_a_run_graded_under_other_shares_gets_no_careful_count(tmp_path):
    # INPUTS records another evals/universe.yaml, whose shares may set a different bar
    s = summary(
        grade_folder(
            tmp_path / "g",
            LIGHT_MISSES,
            tiers=["judgment", "recognise"],
            adapters=CAREFUL,
        )
    )
    assert s["recognition"]["entry"]["fails"] == 1
    assert s["recognition"]["entry"]["careful"] is None


def test_a_run_that_recorded_no_judges_says_its_careful_readers_are_not_recorded(
    tmp_path,
):
    s = summary(grade_folder(tmp_path / "g", LIGHT_MISSES, tiers=["recognise"]))
    assert s["recognition"]["entry"]["careful"] is None
    assert headline(build(s), "x")[RECOGNITION][1].endswith(
        "; 1 of 2 values fail (all readers); careful readers not recorded"
    )


def test_rules_whose_calibration_missed_an_owner_label_are_marked_in_the_headline(
    tmp_path,
):
    miss = {"tier": "chain", "rule": "r1", "text": "t", "label": "fail", "reason": ""}
    alone = {**miss, "tier": "judgment", "rule": "r2"}
    table = [chain("r1", 6, 2, 1, 3, 0, 0)]
    calibrated = summary(calibration_folder(tmp_path / "c", table, [miss, alone]))
    block = build(calibrated).split("## Headline")[1].split("\n## ")[0]
    assert (
        "Rules whose calibration chain missed an owner label, so their figures carry "
        "that caveat: Anthropic side: `r1`; OpenAI side: calibration not run."
    ) in block


def test_costs_and_models_come_from_each_runs_adapters_and_notes(tmp_path):
    anthropic = summary(
        grade_folder(
            tmp_path / "g",
            ANTHROPIC_ROWS,
            adapters={"judgment": "judges: a, b"},
            notes=["judgment cost: $1.50", "decision tokens: 99", "other"],
        )
    )
    section = build(anthropic).split("## Cost and models")[1].split("\n## ")[0]
    assert (
        "| `g` | Anthropic side | judgment: judges: a, b | judgment cost: $1.50; decision tokens: 99 |"
        in section
    )


def test_the_retired_frame_fails_are_listed_once_with_the_owner_decision():
    retired = {
        "decision": "Owner, then: frames go by recognition.",
        "graded_in": "run-1",
        "fails": [
            {"rule": "one-question", "ref": "frames[a].question", "text": "Q | x?"}
        ],
    }
    section = (
        report.build([], {"x": retired})
        .split("### Retired for frames of `x`")[1]
        .split("\n## ")[0]
    )
    assert "Owner, then: frames go by recognition." in section
    assert "| `one-question` | `frames[a].question` | Q \\| x? |" in section
    assert section.count("frames[a].question") == 1


def test_the_committed_retired_file_lists_the_26_frame_fails():
    retired = report.load_retired()["product-development"]
    assert len(retired["fails"]) == 26
    assert "Owner, 2026-10-05" in retired["decision"]


def two_universes(tmp_path):
    """The Anthropic side graded universe x and both sides graded universe y."""
    x = summary(
        grade_folder(tmp_path / "x-run", ANTHROPIC_ROWS, probes="[]"), "anthropic"
    )
    y_anthropic = summary(
        grade_folder(tmp_path / "y-anthropic", ANTHROPIC_ROWS, universe="y"),
        "anthropic",
    )
    y_openai = summary(
        grade_folder(tmp_path / "y-openai", OPENAI_ROWS, universe="y"), "openai"
    )
    return x, y_anthropic, y_openai


def test_each_universe_has_its_own_section_and_the_universes_are_never_compared(
    tmp_path,
):
    x, y_anthropic, y_openai = two_universes(tmp_path)
    text = build(x, y_anthropic, y_openai)
    headings = [line for line in text.splitlines() if line.startswith("## Universe")]
    assert headings == ["## Universe `x`", "## Universe `y`"]
    on_x = headline(text, "x")["Universe grade"]
    assert on_x[1:] == ["4 cases: 2 pass, 1 fail, 1 undecided", "not run", "not run"]
    on_y = headline(text, "y")["Universe grade"]
    assert on_y[1:] == [
        "4 cases: 2 pass, 1 fail, 1 undecided",
        "4 cases: 3 pass, 0 fail, 1 undecided",
        "the two companies' judges agree on 1 of 1; 1 more settled the same way by shared code or Jev",
    ]
    x_section = text.split("## Universe `x`")[1].split("## Universe `y`")[0]
    assert "y-openai" not in x_section and "y-anthropic" not in x_section


def test_a_universe_with_runs_and_no_retired_list_still_gets_a_section(tmp_path):
    x, _, _ = two_universes(tmp_path)
    text = report.build([x], {})
    assert "## Universe `x`" in text and "Retired for frames" not in text


def test_the_universe_comes_from_run_json_or_the_runs_entry(tmp_path):
    named = grade_folder(tmp_path / "named", ANTHROPIC_ROWS, universe="x")
    assert summary(named)["universe"] == "x"
    plain = grade_folder(tmp_path / "plain", ANTHROPIC_ROWS, universe="")
    with pytest.raises(report.ReportError, match="plain.*universe"):
        report.summarise(plain, "anthropic")
    assert report.summarise(plain, "anthropic", "y")["universe"] == "y"
    with pytest.raises(report.ReportError, match="graded x.*says y"):
        report.summarise(named, "anthropic", "y")
    calibrated = calibration_folder(tmp_path / "cal", [chain("r1", 1, 1, 0, 0, 0, 0)])
    assert report.summarise(calibrated, "anthropic")["universe"] is None
    played = play_folder(tmp_path / "play", [])
    assert report.summarise(played, "anthropic")["universe"] is None


def test_one_run_per_measure_per_side_holds_for_each_universe_separately(tmp_path):
    for name, universe in (("a", "x"), ("b", "y"), ("c", "x")):
        grade_folder(tmp_path / name, ANTHROPIC_ROWS, universe=universe)
    one = entries_file(
        tmp_path,
        {"side": "anthropic", "folder": "a"},
        {"side": "anthropic", "folder": "b"},
    )
    assert [s["universe"] for s in report.collect(one, tmp_path / "r", tmp_path)] == [
        "x",
        "y",
    ]
    two = entries_file(
        tmp_path,
        {"side": "anthropic", "folder": "a"},
        {"side": "anthropic", "folder": "c"},
    )
    with pytest.raises(report.ReportError, match="grade of x.*anthropic"):
        report.collect(two, tmp_path / "r", tmp_path)


def test_retired_fails_are_read_one_file_per_universe(tmp_path):
    (tmp_path / "x.yaml").write_text(yaml.safe_dump(NO_FAILS))
    (tmp_path / "y.yaml").write_text(yaml.safe_dump({**NO_FAILS, "graded_in": "run-9"}))
    found = report.load_retired(tmp_path)
    assert sorted(found) == ["x", "y"] and found["y"]["graded_in"] == "run-9"


def test_the_same_inputs_give_the_same_bytes(tmp_path):
    anthropic, openai = two_sides(tmp_path)
    assert build(anthropic, openai) == build(anthropic, openai)
    assert report.summary_text(anthropic) == report.summary_text(
        json.loads(report.summary_text(anthropic))
    )


def test_collect_summarises_folders_or_falls_back_to_committed_summaries(tmp_path):
    folder = grade_folder(tmp_path / "grade-1", ANTHROPIC_ROWS)
    results = tmp_path / "results"
    runs = entries_file(tmp_path, {"side": "anthropic", "folder": "grade-1"})
    (first,) = report.collect(runs, results, root=tmp_path)
    assert first["id"] == "grade-1"
    report.write_all(
        runs,
        results,
        tmp_path / "report.md",
        RETIRED,
        root=tmp_path,
    )
    assert json.loads((results / "grade-1.json").read_text()) == first
    for name in ("run.json", "verdicts.jsonl"):
        (folder / name).unlink()
    folder.rmdir()
    (again,) = report.collect(runs, results, root=tmp_path)
    assert again == first
    (results / "grade-1.json").unlink()
    with pytest.raises(report.ReportError, match="grade-1"):
        report.collect(runs, results, root=tmp_path)


def test_two_runs_of_one_measure_on_one_side_are_refused(tmp_path):
    grade_folder(tmp_path / "one", ANTHROPIC_ROWS)
    grade_folder(tmp_path / "two", ANTHROPIC_ROWS)
    runs = entries_file(
        tmp_path,
        {"side": "anthropic", "folder": "one"},
        {"side": "anthropic", "folder": "two"},
    )
    with pytest.raises(report.ReportError, match="grade.*anthropic"):
        report.collect(runs, tmp_path / "results", root=tmp_path)


def test_an_unknown_side_is_refused(tmp_path):
    runs = entries_file(tmp_path, {"side": "gemini", "folder": "one"})
    with pytest.raises(report.ReportError, match="side"):
        report.collect(runs, tmp_path / "results", root=tmp_path)


def test_writing_removes_summaries_of_runs_no_longer_listed(tmp_path):
    grade_folder(tmp_path / "grade-1", ANTHROPIC_ROWS)
    results = tmp_path / "results"
    results.mkdir()
    (results / "old.json").write_text("{}")
    runs = entries_file(tmp_path, {"side": "anthropic", "folder": "grade-1"})
    report.write_all(
        runs,
        results,
        tmp_path / "report.md",
        RETIRED,
        root=tmp_path,
    )
    assert [p.name for p in results.iterdir()] == ["grade-1.json"]


def test_drift_reports_a_stale_report_or_summaries(tmp_path):
    grade_folder(tmp_path / "grade-1", ANTHROPIC_ROWS)
    results, out = tmp_path / "results", tmp_path / "report.md"
    retired = RETIRED
    runs = entries_file(tmp_path, {"side": "anthropic", "folder": "grade-1"})
    report.write_all(runs, results, out, retired, root=tmp_path)
    assert report.drift(runs, results, out, retired) == []
    out.write_text("edited\n")
    assert report.drift(runs, results, out, retired) == [
        f"{out} is not what report.py builds"
    ]
    report.write_all(runs, results, out, retired, root=tmp_path)
    (results / "stray.json").write_text("{}")
    assert report.drift(runs, results, out, retired) == [
        f"{results / 'stray.json'} belongs to no listed run"
    ]
    (results / "stray.json").unlink()
    (results / "grade-1.json").write_text(
        (results / "grade-1.json").read_text().replace('"anthropic"', '"openai"')
    )
    assert any("side" in p for p in report.drift(runs, results, out, retired))


def test_drift_reports_a_run_whose_summary_names_another_universe_than_runs_yaml(
    tmp_path,
):
    grade_folder(tmp_path / "grade-1", ANTHROPIC_ROWS)
    results, out = tmp_path / "results", tmp_path / "report.md"
    runs = entries_file(
        tmp_path, {"side": "anthropic", "folder": "grade-1", "universe": "x"}
    )
    report.write_all(runs, results, out, RETIRED, root=tmp_path)
    assert report.drift(runs, results, out, RETIRED) == []
    other = entries_file(
        tmp_path, {"side": "anthropic", "folder": "grade-1", "universe": "y"}
    )
    assert any("universe" in p for p in report.drift(other, results, out, RETIRED))


def test_the_committed_report_and_summaries_match_what_report_py_builds():
    assert report.drift() == []


def test_the_committed_report_with_no_runs_reads_not_run_everywhere():
    entries = yaml.safe_load((ROOT / "evals/runs.yaml").read_text())["runs"]
    if entries:
        pytest.skip(
            "runs are listed; the committed report is checked by the drift test"
        )
    text = (ROOT / "evals/report.md").read_text()
    assert text.count("| not run | not run | not run |") == 7


def test_the_just_recipe_and_runbook_exist():
    assert "evals-report:" in (ROOT / "justfile").read_text()
    readme = (ROOT / "evals/README.md").read_text()
    section = readme.split("## Running on another vendor")[1].split("\n## ")[0]
    for name in (
        "--probes",
        "--label",
        "codex:",
        "TYPESAFE_API_KEY",
        "CODEX_HOME",
        "--slice skills",
        "play.py",
        "--rules values-recognised",
    ):
        assert name in section, name
    assert "evals/runs.yaml" in section
    assert "The Anthropic side runs the same four steps" in section
    assert "side: openai" in section and "--label openai-side" in section
    judgment = next(
        line for line in readme.splitlines() if line.startswith("| `judgment`")
    )
    assert "Judge pairs across the sides" in judgment
    for command in (
        "just evals-calibrate universe",
        "just evals-calibrate skills",
        "deterministic,decision,judgment,sort",
        "--tiers recognise --rules values-recognised",
        "just evals-play",
        "just evals-report",
    ):
        assert command in report.COMMANDS, command


def test_the_universe_grade_counts_the_judges_apart_from_the_shared_tiers(tmp_path):
    a = [
        row("r1", "d1", "fail", "deterministic"),
        row("r1", "j1", "pass", "judgment", {"a": "pass", "b": "pass"}),
        row("r1", "j2", "fail", "judgment", {"a": "fail", "b": "fail"}),
        row("r1", "m1", "pass", "decision"),
    ]
    b = [
        row("r1", "d1", "fail", "deterministic"),
        row("r1", "j1", "pass", "judgment", {"c": "pass", "d": "pass"}),
        row("r1", "j2", "pass", "judgment", {"c": "pass", "d": "pass"}),
        # the decision model was unsure on this side, so the judges settled it
        row("r1", "m1", "pass", "judgment", {"c": "pass", "d": "pass"}),
    ]
    anthropic = summary(grade_folder(tmp_path / "a", a), "anthropic")
    openai = summary(grade_folder(tmp_path / "b", b), "openai")
    cells = headline(build(anthropic, openai), "x")["Universe grade"]
    assert cells[3] == (
        "the two companies' judges agree on 1 of 2; "
        "1 more settled the same way by shared code or Jev; "
        "1 more settled by different tiers, 1 of them the same"
    )


def test_the_judged_apart_cell_accounts_for_every_case_both_sides_settled(tmp_path):
    a = [
        row("r1", "j1", "fail", "judgment", {"a": "fail", "b": "fail"}),
        row("r1", "j2", "pass", "judgment", {"a": "pass", "b": "pass"}),
        row("r1", "j3", "pass", "judgment", {"a": "pass", "b": "pass"}),
        row("r1", "m1", "fail", "decision"),
    ]
    b = [
        row("r1", "j1", "pass", "decision"),
        row("r1", "j2", "pass", "judgment", {"c": "pass", "d": "pass"}),
        row("r1", "j3", "fail", "decision"),
        row("r1", "m1", "pass", "decision"),
    ]
    anthropic = summary(grade_folder(tmp_path / "a", a), "anthropic")
    openai = summary(grade_folder(tmp_path / "b", b), "openai")
    assert report.agreement("grade", anthropic, openai) == (4, 1)
    cells = headline(build(anthropic, openai), "x")["Universe grade"]
    assert cells[3] == (
        "the two companies' judges agree on 1 of 1; "
        "1 more settled by shared code or Jev, 0 of them the same; "
        "2 more settled by different tiers, 0 of them the same"
    )


def test_calibration_counts_the_judges_apart_from_the_shared_tiers(tmp_path):
    table = [chain("r1", 4, 2, 0, 2, 0, 0), chain("r2", 1, 0, 0, 1, 0, 0)]

    def settled(*tiers):
        return [
            *({"rule": "r1", "verdict": v, "tier": t} for v, t in tiers),
            {"rule": "r2", "verdict": "pass", "tier": "sort"},
        ]

    a = summary(
        calibration_folder(
            tmp_path / "a", table,
            settled=settled(("fail", "deterministic"), ("pass", "judgment"), ("fail", "judgment"), ("pass", "decision")),
        ),
        "anthropic",
    )  # fmt: skip
    b = summary(
        calibration_folder(
            tmp_path / "b", table,
            settled=settled(("fail", "deterministic"), ("pass", "judgment"), ("pass", "judgment"), ("pass", "judgment")),
        ),
        "openai",
    )  # fmt: skip
    assert a["chain"] == {
        "r1": [
            ["fail", "deterministic"], ["pass", "judgment"], ["fail", "judgment"],
            ["pass", "decision"],
        ],
        "r2": [["pass", "sort"]],
    }  # fmt: skip
    cells = headline(build(a, b))[
        "Calibration, universe rules (development examples, interim)"
    ]
    assert cells[3] == (
        "the two companies' judges agree on 1 of 2; "
        "1 more settled the same way by shared code or Jev; "
        "1 more settled the same way by the filing checks; "
        "1 more settled by different tiers, 1 of them the same"
    )


@pytest.mark.parametrize(
    ("side", "adapters", "tier", "model"),
    [
        ("anthropic", {"judgment": "judges: claude-a, codex:b"}, "judgment", "codex:b"),
        ("anthropic", {"agent": "codex codex-cli 1.0, model m"}, "agent", "codex:m"),
        ("openai", {"judgment": "judges: codex:a, claude-b"}, "judgment", "claude-b"),
        ("openai", {"sort": "filers: codex:a, jev v1, claude-light"}, "sort", "claude-light"),
        ("openai", {"agent": "claude 2.0 (Claude Code), model claude-o"}, "agent", "claude-o"),
    ],
)  # fmt: skip
def test_a_run_whose_models_belong_to_the_other_company_is_refused(
    tmp_path, side, adapters, tier, model
):
    folder = grade_folder(tmp_path / "g", ANTHROPIC_ROWS, adapters=adapters)
    with pytest.raises(report.ReportError) as refused:
        report.summarise(folder, side)
    said = str(refused.value)
    assert (
        "g " in said and report.SIDES[side] in said and f"{tier} model {model}" in said
    )


def test_a_committed_summary_whose_models_belong_to_the_other_company_is_refused(
    tmp_path,
):
    """The side check holds on a clean checkout too, where only the summary is committed."""
    folder = grade_folder(
        tmp_path / "g", ANTHROPIC_ROWS, adapters={"judgment": "judges: codex:a"}
    )
    moved = {**summary(folder, "openai"), "side": "anthropic"}
    results, out = tmp_path / "results", tmp_path / "report.md"
    results.mkdir()
    (results / "g.json").write_text(report.summary_text(moved))
    out.write_text(report.build([moved], RETIRED, {}))
    for name in ("run.json", "verdicts.jsonl"):
        (folder / name).unlink()
    folder.rmdir()
    runs = entries_file(tmp_path, {"side": "anthropic", "folder": "g"})
    said = "judgment model codex:a belongs to the other company"
    with pytest.raises(report.ReportError, match=said):
        report.collect(runs, results, root=tmp_path)
    assert any(said in p for p in report.drift(runs, results, out, RETIRED))


def test_jev_serves_both_sides_as_the_decision_tier_and_a_filer(tmp_path):
    for side, careful, light in (
        ("anthropic", "claude-a", "claude-light"),
        ("openai", "codex:a", "codex:light"),
    ):
        adapters = {
            "decision": "jev jev-1",
            "judgment": f"judges: {careful}",
            "sort": f"filers: {careful}, jev jev-1, {light}",
            "recognise": f"filers: {careful}, jev, {light}",
        }
        folder = grade_folder(tmp_path / side, ANTHROPIC_ROWS, adapters=adapters)
        assert report.summarise(folder, side)["side"] == side


def test_the_headline_says_how_the_two_sides_relate():
    block = build().split("## Headline")[1].split("\n## ")[0]
    assert "How the two sides relate:" in block
    for said in (
        (
            "same decision model, Jev, as the decision tier and as one of the readers in "
            "recognition and sorting"
        ),
        "written blind on one side and labelled blind on both sides",
        "kept only where both sides agree",
        "each universe's recognition section says which side did what",
        "written by the Anthropic side's run and reused by the OpenAI side",
    ):
        assert said in block, said
    assert "extracted and written on the Anthropic side" not in block


LABELLED = ["Anthropic side: reader a", "OpenAI side: reader b"]


def test_who_labelled_the_situations_is_shown_with_that_universes_recognition(
    tmp_path,
):
    runs = tmp_path / "runs.yaml"
    runs.write_text(yaml.safe_dump({"runs": [], "labelled_by": {"x": LABELLED}}))
    assert report.labelled_by(runs) == {"x": LABELLED}
    text = report.build([], RETIRED, {"x": LABELLED})
    section = text.split("Recognition by frame of `x`", 1)[1].split("Sorting of `x`")[0]
    assert (
        "Who wrote and labelled the situations: Anthropic side: reader a; "
        "OpenAI side: reader b."
    ) in section
    assert "Who wrote and labelled the situations" not in build()


@pytest.mark.parametrize(
    "bad",
    [
        ["x"],
        {"x": "Anthropic side: reader a"},
        {"x": []},
        {"x": ["Anthropic side: "]},
        {"x": ["Gemini side: reader c"]},
    ],
)
def test_a_malformed_labelled_by_is_refused(tmp_path, bad):
    runs = tmp_path / "runs.yaml"
    runs.write_text(yaml.safe_dump({"runs": [], "labelled_by": bad}))
    with pytest.raises(report.ReportError, match="labelled_by"):
        report.labelled_by(runs)


def test_the_committed_runs_file_says_who_labelled_product_development():
    assert report.labelled_by()["product-development"] == [
        (
            "Anthropic side: extracted and written, and labelled blind, by Claude Fable 5.1 "
            "and Claude Opus 5.5"
        ),
        (
            "OpenAI side: labelled blind by GPT-6-Astra at xhigh, in the Codex app for rounds "
            "1 and 2 and through the Codex CLI for round 3"
        ),
    ]


def test_the_universe_headline_has_a_row_for_the_judge_pairs(tmp_path):
    anthropic, openai = two_sides(tmp_path)
    pairs = "Judge pairs across the sides"
    assert headline(build(anthropic, openai), "x")[pairs][1:] == [
        "judges: a, b",
        "judges: c, d",
        "4 pairs, 3 cases each: 1 to 2 pass, 0 to 1 fail, 0 to 2 undecided",
    ]
    assert headline(build(anthropic), "x")[pairs][1:] == [
        "judges: a, b",
        "not run",
        "not run",
    ]
