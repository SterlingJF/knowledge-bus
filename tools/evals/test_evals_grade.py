"""Grading a universe and calibrating tiers on the owner's labelled examples."""

import json
from pathlib import Path

import grade
import pytest
import spec as spec_module
import tiers
import yaml

UNIVERSE_DOC = {
    "elements": [
        {"id": "segments", "question": "Who exactly is served, grouped how?"},
        {"id": "vision", "question": "What future are we committing to?"},
    ],
    "artifacts": [
        {
            "id": "lean-canvas",
            "enablement": {
                "action": "judge a bet",
                "actor": "founder",
                "timing": "early",
            },
        },
        {"id": "legacy", "enablement": "a string enablement is skipped"},
    ],
    "frames": [
        {
            "id": "phase",
            "values": [{"id": "strategy", "question": "Who are we, and why?"}, "plain"],
        }
    ],
}
GUIDANCE_DOC = {
    "elements": {
        "vision": [{"kind": "convention", "claim": "Describe the change in the world."}]
    }
}


def test_subject_paths_select_texts_with_their_ids():
    picked = grade.select(UNIVERSE_DOC, "elements[].question")
    assert picked == [
        (
            "elements[segments].question",
            "Who exactly is served, grouped how?",
            {"id": "segments"},
        ),
        (
            "elements[vision].question",
            "What future are we committing to?",
            {"id": "vision"},
        ),
    ]
    (action,) = grade.select(UNIVERSE_DOC, "artifacts[].enablement.action")
    assert action[0] == "artifacts[lean-canvas].enablement.action"
    assert action[2] == {"id": "lean-canvas", "actor": "founder", "timing": "early"}
    assert [
        r for r, _, _ in grade.select(UNIVERSE_DOC, "frames[].values[].question")
    ] == ["frames[phase].values[strategy].question"]
    (claim,) = grade.select(GUIDANCE_DOC, "{elements,artifacts}.<id>[].claim")
    assert claim[:2] == (
        "elements.vision[0].claim",
        "Describe the change in the world.",
    )


def fake_spec():
    rule = {
        "rule": "A question asks for one thing.",
        "why": "A question that asks for two things gets half an answer.",
        "applies_to": ["element.question", "frame.question"],
        "deterministic": {
            "complete": False,
            "checks": [{"pattern": r",\s*\w+ how\?|, and", "then": "flag"}],
        },
        "judgment": {"pass": "PASS if one.", "fail": "FAIL if two."},
        "examples": [
            {"text": "Who, and how?", "verdict": "fail", "note": "It asks two things."},
            {
                "text": "Who is served, and why?",
                "verdict": "fail",
                "note": "It asks for a group and a reason.",
            },
            {"text": "Who?", "verdict": "pass", "note": "It asks one thing."},
            {
                "text": "Who is served first?",
                "verdict": "pass",
                "note": "One answer settles it.",
            },
        ],
    }
    universe = {
        "schema": "evals/1",
        "slice": "universe",
        "subjects": {
            "element.question": "elements[].question",
            "frame.question": "frames[].values[].question",
            "guidance.claim": "guidance: {elements,artifacts}.<id>[].claim",
        },
        "rules": {"one-job": rule},
    }
    return spec_module.Spec(universe=universe, skills={"behaviours": {}}, folder=None)


def judge(cases):
    return [
        tiers.Outcome(
            "fail" if "," in c.text else "pass", "judgment", {"critique": "c"}
        )
        for c in cases
    ]


def test_grading_builds_one_case_per_rule_and_subject_text():
    cases = grade.universe_cases(fake_spec(), UNIVERSE_DOC, GUIDANCE_DOC)
    assert [(c.rule_id, c.ref) for c in cases] == [
        ("one-job", "elements[segments].question"),
        ("one-job", "elements[vision].question"),
        ("one-job", "frames[phase].values[strategy].question"),
    ]


def test_a_pair_rule_compares_each_text_with_its_siblings_once():
    spec = fake_spec()
    spec.universe["rules"] = {
        "siblings-differ": {
            "rule": "Sibling definitions make different points.",
            "applies_to": ["element.question", "guidance.claim"],
            "scope": "pair",
            "judgment": {"pass": "PASS if different.", "fail": "FAIL if the same."},
        }
    }
    guidance = {
        "elements": {
            "vision": [{"claim": "Say the change."}, {"claim": "Name the change."}],
            "segments": [{"claim": "One claim has no sibling."}],
        }
    }
    cases = grade.universe_cases(spec, UNIVERSE_DOC, guidance)
    assert [(c.ref, c.text, c.context["sibling"]) for c in cases] == [
        (
            "elements[segments].question ~ elements[vision].question",
            "Who exactly is served, grouped how?",
            "What future are we committing to?",
        ),
        (
            "elements.vision[0].claim ~ elements.vision[1].claim",
            "Say the change.",
            "Name the change.",
        ),
    ]


def test_a_graded_run_writes_traced_verdicts_and_a_report(tmp_path):
    results = tiers.run(
        grade.universe_cases(fake_spec(), UNIVERSE_DOC, GUIDANCE_DOC), judge=judge
    )
    run = grade.Run(
        id="r1",
        kind="universe",
        inputs={"universe.kbp.yaml": "sha256:x"},
        adapters={"judgment": "fake 1"},
    )
    grade.write(tmp_path, run, fake_spec(), results)
    rows = [
        json.loads(line)
        for line in (tmp_path / "verdicts.jsonl").read_text().splitlines()
    ]
    assert [(r["ref"], r["verdict"], r["tier"]) for r in rows] == [
        ("elements[segments].question", "fail", "judgment"),
        ("elements[vision].question", "pass", "judgment"),
        ("frames[phase].values[strategy].question", "fail", "judgment"),
    ]
    assert rows[0]["run"] == "r1" and "evidence" not in rows[0]
    assert rows[0]["why"] == "A question that asks for two things gets half an answer."
    assert rows[0]["reason"] == "c"
    assert rows[0]["trail"] == [
        {
            "tier": "deterministic",
            "verdict": "undecided",
            "reason": "match ', grouped how?'",
        },
        {"tier": "judgment", "verdict": "fail", "reason": "c"},
    ]
    report = (tmp_path / "report.md").read_text()
    assert "## By definition" in report
    assert (
        '- `elements[segments].question`: "Who exactly is served, grouped how?" fails one-job'
        in report
    )
    assert grade.rebuild(tmp_path, fake_spec()) == report
    assert (
        "## one-job: A question asks for one thing.\n\n"
        "Why: A question that asks for two things gets half an answer.\n"
    ) in report
    assert "Owner's words" not in report
    assert (
        '- `elements[segments].question`: "Who exactly is served, grouped how?" (judgment: c)'
        in report
    )


def test_calibration_scores_each_tier_alone_against_the_owner_labels():
    table = grade.calibrate(fake_spec(), "universe", decide=None, judge=judge)
    by_tier = {row["tier"]: row for row in table if row["rule"] == "one-job"}
    assert by_tier["deterministic"] == {
        "rule": "one-job", "tier": "deterministic", "n": 4, "tp": 0, "fn": 0, "tn": 0, "fp": 0, "undecided": 4,
    }  # fmt: skip
    assert by_tier["judgment"]["tp"] == 2 and by_tier["judgment"]["tn"] == 2
    assert by_tier["chain"]["tp"] == 2 and by_tier["chain"]["tn"] == 2
    assert "decision" not in by_tier


def test_calibration_lists_each_disagreement_with_the_tier_reason():
    def strict(cases):
        return [
            tiers.Outcome("fail", "judgment", {"critique": "too broad"}) for _ in cases
        ]

    misses = []
    grade.calibrate(
        fake_spec(), "universe", judge=strict, only=("judgment",), misses=misses
    )
    assert [(m["tier"], m["text"], m["label"], m["reason"]) for m in misses] == [
        ("judgment", "Who?", "pass", "too broad"),
        ("judgment", "Who is served first?", "pass", "too broad"),
        ("chain", "Who?", "pass", "too broad"),
        ("chain", "Who is served first?", "pass", "too broad"),
    ]


def test_calibration_keeps_each_examples_chain_verdict_and_settling_tier():
    settled = []
    grade.calibrate(fake_spec(), "universe", judge=judge, settled=settled)
    assert [(s["verdict"], s["tier"]) for s in settled if s["rule"] == "one-job"] == [
        ("fail", "judgment"),
        ("fail", "judgment"),
        ("pass", "judgment"),
        ("pass", "judgment"),
    ]


def test_a_subject_that_selects_no_text_is_reported():
    spec = fake_spec()
    spec.universe["subjects"]["frame.question"] = "frames[].nothing[].question"
    empty = []
    grade.universe_cases(spec, UNIVERSE_DOC, GUIDANCE_DOC, empty=empty)
    assert empty == ["frame.question"]


def test_grading_can_be_limited_to_named_rules():
    spec = fake_spec()
    spec.universe["rules"]["other"] = dict(spec.universe["rules"]["one-job"])
    cases = grade.universe_cases(spec, UNIVERSE_DOC, GUIDANCE_DOC, rules=["other"])
    assert {c.rule_id for c in cases} == {"other"}


SET_DOC = {
    "elements": [
        {"id": "roster", "question": "Which singers sing in each concert?"},
        {"id": "venue", "question": "Which hall hosts the concert?"},
        {"id": "permit", "question": "Which permit allows the outdoor concert?"},
    ],
    "artifacts": [
        {
            "id": "concert-plan",
            "enablement": {
                "action": "decide the programme",
                "actor": "choir director",
                "timing": "before each season",
            },
            "composition": {
                "core": [
                    "roster",
                    {
                        "element": "permit",
                        "mode": "owns",
                        "when": {
                            "setting": ["outdoor", "street"],
                            "size": ["large"],
                        },
                    },
                ],
                "situational": [{"element": "venue", "mode": "links"}],
            },
        },
        {
            "id": "hall-booking",
            "enablement": {"action": "book a hall", "actor": "treasurer"},
            "composition": {
                "core": ["venue"],
                "situational": [
                    {"element": "roster", "when": {"setting": {"place": ["hall"]}}}
                ],
            },
        },
    ],
}
SET_SUBJECTS = {
    "element.question": "elements[].question",
    "artifact.enablement": "artifacts[].enablement",
    "artifact.composition": "artifacts[].composition",
}


def set_spec(subjects, **extra):
    rule = {
        "rule": "Each reads clearly within its set.",
        "applies_to": subjects,
        "scope": "set",
        "judgment": {"pass": "PASS if clear.", "fail": "FAIL if not."},
        **extra,
    }
    universe = {"subjects": SET_SUBJECTS, "rules": {"distinct": rule}}
    return spec_module.Spec(universe=universe, skills={}, folder=None)


def test_enablements_render_as_one_line_each():
    picked = grade.select(SET_DOC, "artifacts[].enablement")
    assert picked == [
        (
            "artifacts[concert-plan].enablement",
            "action: decide the programme; actor: choir director; timing: before each season",
            {"id": "concert-plan"},
        ),
        (
            "artifacts[hall-booking].enablement",
            "action: book a hall; actor: treasurer",
            {"id": "hall-booking"},
        ),
    ]


def test_each_composition_entry_is_one_member_with_its_strength():
    picked = grade.select(SET_DOC, "artifacts[].composition")
    assert [(ref, text, c["strength"]) for ref, text, c in picked] == [
        (
            "artifacts[concert-plan].composition.core[roster]",
            "Which singers sing in each concert?",
            "core",
        ),
        (
            "artifacts[concert-plan].composition.core[permit]",
            "Which permit allows the outdoor concert?",
            "core when setting is outdoor or street and size is large",
        ),
        (
            "artifacts[concert-plan].composition.situational[venue]",
            "Which hall hosts the concert?",
            "situational",
        ),
        (
            "artifacts[hall-booking].composition.core[venue]",
            "Which hall hosts the concert?",
            "core",
        ),
        (
            "artifacts[hall-booking].composition.situational[roster]",
            "Which singers sing in each concert?",
            "situational when setting place is hall",
        ),
    ]
    first = picked[0][2]
    assert first == {
        "id": "roster",
        "artifact": "concert-plan",
        "enablement": "action: decide the programme; actor: choir director; timing: before each season",
        "strength": "core",
        "set": [
            "core: Which singers sing in each concert?",
            "core when setting is outdoor or street and size is large: Which permit allows the outdoor concert?",
            "situational: Which hall hosts the concert?",
        ],
    }
    assert picked[3][2]["set"] == [
        "core: Which hall hosts the concert?",
        "situational when setting place is hall: Which singers sing in each concert?",
    ]


def test_a_set_rule_makes_one_set_of_every_question_and_every_enablement():
    cases = grade.universe_cases(
        set_spec(["element.question", "artifact.enablement"]), SET_DOC
    )
    questions = [q["question"] for q in SET_DOC["elements"]]
    assert [c.context["set"] for c in cases[:3]] == [questions] * 3
    assert cases[0].context["id"] == "roster"
    assert [c.subject for c in cases] == ["element.question"] * 3 + [
        "artifact.enablement"
    ] * 2
    assert cases[3].context["set"] == [cases[3].text, cases[4].text]


def test_a_set_rule_on_compositions_makes_one_set_per_artifact():
    cases = grade.universe_cases(set_spec(["artifact.composition"]), SET_DOC)
    assert [len(c.context["set"]) for c in cases] == [3, 3, 3, 2, 2]
    assert {c.context["artifact"] for c in cases[3:]} == {"hall-booking"}


SORT = {"ask": "Which question does this passage answer?", "write": "Write two."}


def fake_call(prompt, model, schema, system):
    """Writes probes that share no word, says every probe answers, files each one first."""
    (key,) = schema["required"]
    section = prompt.split("Passages:\n")[-1].split("\n\n")[0]
    count = len(section.splitlines())
    if key == "passages":
        out = {"passages": ["Tenors and altos.", "Basses too."]}
    elif key == "answers":
        out = {"answers": [{"passage": n, "answers": True} for n in range(1, 3)]}
    elif key == "option":
        out = {"option": 1}
    else:
        out = {"filings": [{"passage": n, "question": 1} for n in range(1, count + 1)]}
    return {"structured_output": out, "total_cost_usd": 0.25}


def test_a_sort_rule_is_settled_by_the_sort_check_and_reported(tmp_path):
    spec = set_spec(["artifact.composition"], sort=SORT)
    del spec.universe["rules"]["distinct"]["judgment"]
    run = grade.Run(id="r", kind="universe", inputs={}, adapters={}, tiers=["sort"])
    sorting = grade.sorting(
        ("sort",), "universe", run, ["judge-a"], "light", call=fake_call
    )
    assert run.notes == [
        "sort: the decision-model filer is off: TYPESAFE_API_KEY is not set"
    ]
    results = tiers.run(grade.universe_cases(spec, SET_DOC), only=("sort",))
    grade.settle(results, sorting.sorter)
    assert [r.final.tier for r in results] == ["sort"] * 5
    assert [r.final.verdict for r in results] == [
        "pass", "fail", "fail", "pass", "fail",
    ]  # fmt: skip
    grade.finish(run, None, None, sorting, tmp_path)
    assert run.adapters["sort"] == "filers: judge-a, light"
    assert any(n.startswith("sort cost: $") for n in run.notes)
    probes = json.loads((tmp_path / "probes.json").read_text())["probes"]
    assert set(probes) == {"roster", "permit", "venue"}
    grade.write(tmp_path, run, spec, results)
    rows = [
        json.loads(line)
        for line in (tmp_path / "verdicts.jsonl").read_text().splitlines()
    ]
    assert rows[1]["tier"] == "sort" and rows[1]["adapter"] == "filers: judge-a, light"
    assert rows[1]["reason"].startswith('judge-a filed "Tenors and altos." under')
    report = (tmp_path / "report.md").read_text()
    assert "deterministic / decision / judgment / sort / recognise |" in report
    assert "| `distinct` | 2 | 3 | 0 | 0 / 0 / 0 / 5 / 0 |" in report


def test_a_probes_file_is_reused_and_the_decision_filer_joins_with_a_key(tmp_path):
    path = tmp_path / "probes.json"
    known = {
        "roster": {
            "question": "Which singers sing in each concert?",
            "probes": ["Tenors."],
        }
    }
    import sort

    sort.save(path, known)

    def no_writing(prompt, model, schema, system):
        assert schema["required"] != ["passages"], "reused probes need no writer"
        return fake_call(prompt, model, schema, system)

    run = grade.Run(id="r", kind="universe", inputs={}, adapters={})
    sorting = grade.sorting(
        ("sort",), "universe", run, ["judge-a"], "light", probes=path, key="k",
        call=no_writing,
        post=lambda body: {"answers": {"q": {"choice": "1", "confidence": 0.9}}},
    )  # fmt: skip
    assert [f.name for f in sorting.sorter.filers] == ["judge-a", "jev", "light"]
    assert sorting.prober(
        [
            tiers.Case(
                "s",
                {"sort": SORT},
                "x",
                "r",
                "Which singers sing in each concert?",
                {"id": "roster"},
            )
        ]
    ) == [["Tenors."]]
    grade.finish(run, None, None, sorting, tmp_path)
    assert "sort: the decision model is unsure below confidence 0.6" in run.notes


def test_examples_file_their_own_probes():
    rule = {
        "rule": "Knowledge is filed under its question.",
        "applies_to": ["artifact.composition"],
        "scope": "set",
        "sort": SORT,
        "examples": [
            {
                "text": text,
                "verdict": verdict,
                "note": "n",
                "context": {
                    "set": ["core: Who sings?", "core: Which hall?"],
                    "probes": ["P"],
                },
            }
            for text, verdict in (("Who sings?", "pass"), ("Which hall?", "fail"))
        ],
    }
    spec = spec_module.Spec(
        universe={"subjects": SET_SUBJECTS, "rules": {"sorts": rule}},
        skills={},
        folder=None,
    )
    run = grade.Run(id="r", kind="universe", inputs={}, adapters={})
    sorting = grade.sorting(("sort",), "examples", run, ["a"], "light", call=fake_call)
    table = grade.calibrate(spec, "universe", only=("sort",), sorter=sorting.sorter)
    by_tier = {row["tier"]: row for row in table}
    assert by_tier["sort"]["tn"] == 1 and by_tier["sort"]["tp"] == 1
    assert by_tier["chain"]["tn"] == 1
    assert sorting.models.cost == 0.5


def test_the_sort_scope_is_the_universe_overview():
    doc = {
        "universe": {
            "overview": {"covers": "Choir work.\n", "for": "Section leaders.\n"}
        }
    }
    assert grade.scope_of(doc) == (
        "These questions belong to a universe that covers: Choir work. It is for: Section leaders."
    )
    assert grade.scope_of({"universe": {}}) == ""


TERMS = [
    {"term": "section", "means": "One voice part of the choir."},
    {"term": "call", "means": "A rehearsal the director schedules."},
]


def test_one_term_per_concept_cases_see_the_universe_terms():
    spec = fake_spec()
    spec.universe["subjects"]["universe.term"] = "universe.terms[].means"
    rule = spec.universe["rules"]["one-job"]
    spec.universe["rules"]["one-term-per-concept"] = {
        **rule,
        "applies_to": ["element.question", "universe.term"],
    }
    doc = {**UNIVERSE_DOC, "universe": {"terms": TERMS}}
    cases = grade.universe_cases(spec, doc, GUIDANCE_DOC)
    terms = [c for c in cases if c.rule_id == "one-term-per-concept"]
    assert [c.ref for c in terms] == [
        "elements[segments].question",
        "elements[vision].question",
        "universe.terms[0].means",
        "universe.terms[1].means",
    ]
    assert all(c.context["terms"] == TERMS for c in terms)
    assert all("terms" not in c.context for c in cases if c.rule_id == "one-job")


def test_a_universe_without_terms_selects_no_term_and_adds_no_context():
    spec = fake_spec()
    spec.universe["subjects"]["universe.term"] = "universe.terms[].means"
    spec.universe["rules"]["one-term-per-concept"] = {
        **spec.universe["rules"]["one-job"],
        "applies_to": ["element.question", "universe.term"],
    }
    empty = []
    cases = grade.universe_cases(spec, UNIVERSE_DOC, GUIDANCE_DOC, empty=empty)
    assert "universe.term" in empty
    assert not any("terms" in c.context for c in cases)


def test_the_repository_rules_grade_each_term_meaning():
    doc = {"universe": {"terms": TERMS}}
    cases = grade.universe_cases(spec_module.load(), doc)
    assert {c.rule_id for c in cases if c.subject == "universe.term"} == {
        "named-referents",
        "direct-statement",
        "plain-words",
        "one-point-terse",
        "holds-across-scope",
        "one-term-per-concept",
    }
    assert {c.ref for c in cases} == {
        "universe.terms[0].means",
        "universe.terms[1].means",
    }


def test_a_term_meaning_is_judged_with_the_term_it_defines():
    doc = {"universe": {"terms": TERMS}}
    cases = grade.universe_cases(spec_module.load(), doc)
    by_ref = {
        c.ref: c.context.get("term") for c in cases if c.subject == "universe.term"
    }
    assert by_ref == {
        "universe.terms[0].means": TERMS[0]["term"],
        "universe.terms[1].means": TERMS[1]["term"],
    }


def test_a_value_question_is_judged_with_the_question_of_its_frame():
    doc = {
        "frames": [
            {
                "id": "uptake",
                "question": "How does the offering reach the people it is for?",
                "values": [{"id": "given", "question": "Does it arrive unasked?"}],
            }
        ]
    }
    ((ref, _, context),) = grade.select(doc, "frames[].values[].question")
    assert ref == "frames[uptake].values[given].question"
    assert (
        context["frame question"] == "How does the offering reach the people it is for?"
    )


def test_frame_values_render_as_the_explorer_shows_them():
    doc = {
        "frames": [
            {
                "id": "uptake",
                "question": "How does the offering reach people?",
                "values": [
                    {"id": "given", "question": "Does it arrive unasked?"},
                    "word-of-mouth",
                ],
            },
            {
                "id": "outcome",
                "facets": {"form": ["creation", "service"], "mutability": ["fixed"]},
            },
        ],
        "factors": [{"id": "crowd", "values": ["small"]}],
    }
    uptake = ["Given: Does it arrive unasked?", "Word of mouth"]
    asked = {"frame question": "How does the offering reach people?"}
    assert grade.select(doc, "frames[].{values,facets}") == [
        (
            "frames[uptake].values[given]",
            uptake[0],
            {"id": "given", "frame": "uptake", "set": uptake, **asked},
        ),
        (
            "frames[uptake].values[word-of-mouth]",
            uptake[1],
            {"id": "word-of-mouth", "frame": "uptake", "set": uptake, **asked},
        ),
        (
            "frames[outcome].facets[form][creation]",
            "Creation",
            {"id": "creation", "frame": "outcome", "facet": "form", "set": ["Creation", "Service"]},
        ),
        (
            "frames[outcome].facets[form][service]",
            "Service",
            {"id": "service", "frame": "outcome", "facet": "form", "set": ["Creation", "Service"]},
        ),
        (
            "frames[outcome].facets[mutability][fixed]",
            "Fixed",
            {"id": "fixed", "frame": "outcome", "facet": "mutability", "set": ["Fixed"]},
        ),
    ]  # fmt: skip
    assert grade.select(doc, "factors[].{values,facets}") == [
        ("factors[crowd].values[small]", "Small", {"id": "small", "factor": "crowd", "set": ["Small"]})
    ]  # fmt: skip


def test_frames_are_graded_only_by_the_rules_that_still_apply():
    def dimension(name, value):
        return {
            "id": name,
            "question": f"Which {name} applies?",
            "values": [{"id": value, "question": f"Is it {value}?"}, "other"],
        }

    doc = {
        "frames": [dimension("venue", "indoors"), dimension("season", "summer")],
        "factors": [dimension("crowd", "small"), dimension("weather", "dry")],
    }
    by_subject = {}
    for case in grade.universe_cases(spec_module.load(), doc):
        by_subject.setdefault(case.subject, set()).add(case.rule_id)
    assert by_subject == {
        "frame.own_question": {"one-term-per-concept", "siblings-differ"},
        "frame.question": {"one-term-per-concept"},
        "frame.value": {"values-recognised"},
        "factor.own_question": {"one-term-per-concept", "siblings-differ"},
        "factor.question": {"one-term-per-concept"},
        "factor.value": {"values-recognised"},
    }


FIXTURES = Path(__file__).parent / "fixtures"
FAIR = FIXTURES / "summer-fair.universe.yaml"
FAIR_SITUATIONS = FIXTURES / "situations" / "summer-fair.yaml"


def recognition_run(run, source, call=fake_call):
    sorting = grade.sorting(
        ("recognise",), "universe", run, ["judge-a"], "light", call=call,
        situations=source, scope=grade.scope_of(spec_module.read(FAIR)),
    )  # fmt: skip
    cases = grade.universe_cases(
        spec_module.load(), spec_module.read(FAIR), rules=["values-recognised"]
    )
    results = tiers.run(cases, only=("recognise",))
    grade.settle(results, sorting.recogniser, "recognise")
    return sorting, results


def test_a_recognise_rule_is_settled_by_the_recognition_check_and_reported(tmp_path):
    run = grade.Run(
        id="r", kind="universe", inputs={}, adapters={}, tiers=["recognise"]
    )
    source = grade.situations_for(FAIR_SITUATIONS, spec_module.read(FAIR), run)
    assert list(run.inputs) == [
        "tools/evals/fixtures/situations/summer-fair.yaml",
        "tools/evals/fixtures/situations/cases.yaml (cases used)",
    ]
    assert run.inputs["tools/evals/fixtures/situations/summer-fair.yaml"] == (
        grade._digest(FAIR_SITUATIONS)
    )
    assert set(run.kinds.values()) == {"situations"}
    sorting, results = recognition_run(run, source)
    assert [r.case.ref for r in results] == [
        "frames[entry].values[open]",
        "frames[entry].values[ticketed]",
        "frames[entry].values[invited]",
        "frames[permission].values[nobody]",
        "frames[permission].values[organiser]",
        "frames[permission].values[council]",
    ]
    assert [r.final.tier for r in results] == ["recognise"] * 6
    assert [r.final.verdict for r in results] == ["pass", "fail", "fail"] * 2
    assert sorting.models.cost == 0.25 * 48  # 24 situations, one call each, two filers
    grade.finish(run, None, None, sorting, tmp_path)
    assert run.adapters["recognise"] == "filers: judge-a, light"
    grade.write(tmp_path, run, spec_module.load(), results)
    rows = [
        json.loads(line)
        for line in (tmp_path / "verdicts.jsonl").read_text().splitlines()
    ]
    assert rows[1]["recognition"]["right"] == {"judge-a": 0, "light": 0}
    assert "placed" not in rows[1]["recognition"]
    assert rows[1]["trail"][-1]["placed"]["light"] == [rows[0]["text"]] * 4
    report = (tmp_path / "report.md").read_text()
    assert grade.rebuild(tmp_path, spec_module.load()) == report
    assert (
        "## Recognition by frame\n\n"
        "Each filer's right / situations in the set, with unsure, none and, on a ladder, "
        "off-by-one-step misses counted apart. Unsure and none count as misses.\n\n"
        "| Set | Values | Situations | judge-a | light | Lowest value | Verdict |\n"
        "|---|---|---|---|---|---|---|\n"
        "| entry | 3 | 12 | 4/12 (0 unsure, 0 none) | 4/12 (0 unsure, 0 none) "
        "| ticketed 0/4 (judge-a) | fail |\n"
        "| permission | 3 | 12 | 4/12 (0 unsure, 0 none, 4 off by one) "
        "| 4/12 (0 unsure, 0 none, 4 off by one) | organiser 0/4 (judge-a) | fail |\n"
    ) in report
    assert (
        "Where misses went, expected → placed, with each filer's count:\n\n"
        "- entry: Ticketed: Is a paid pass needed? → Open: Can anyone wander up? "
        "(judge-a 4, light 4)\n"
        "- entry: Invited: Is it only for people on a list? → Open: Can anyone wander up? "
        "(judge-a 4, light 4)\n"
        "- permission: Organiser → Nobody (judge-a 4, light 4)\n"
        "- permission: Council → Nobody (judge-a 4, light 4)\n"
    ) in report


def test_recognition_readers_are_asked_which_option_fits_the_situation():
    seen = []

    def capture(prompt, model, schema, system):
        seen.append((prompt, system))
        return fake_call(prompt, model, schema, system)

    run = grade.Run(id="r", kind="universe", inputs={}, adapters={})
    source = grade.situations_for(FAIR_SITUATIONS, spec_module.read(FAIR), run)
    recognition_run(run, source, call=capture)
    assert len(seen) == 48
    prompt = next(p for p, _ in seen if "a visitor" in p)
    assert prompt.startswith("These options belong to a universe that covers: ")
    assert (
        "\n\nQuestion: How does a visitor get in to see it?\n\n"
        "Which of these fits the situation best?\n\n"
        'Options:\n1. "Open: Can anyone wander up?"\n'
    ) in prompt
    for prompt, system in seen:
        assert "\nSituation: " in prompt
        assert "Questions:" not in prompt and "Passages:" not in prompt
        assert "question it answers" not in prompt + system


def test_missing_situations_leave_values_undecided_and_say_not_run(tmp_path):
    run = grade.Run(
        id="r", kind="universe", inputs={}, adapters={}, tiers=["recognise"]
    )
    source = grade.situations_for(tmp_path / "none.yaml", spec_module.read(FAIR), run)
    assert run.notes == ["recognition not run: no situations file for summer-fair"]
    assert run.inputs == {}

    def never(prompt, model, schema, system):
        raise AssertionError("nothing to file")

    sorting, results = recognition_run(run, source, call=never)
    assert {r.final.verdict for r in results} == {"undecided"}
    assert {r.final.detail["reason"] for r in results} == {
        "Not run: no situations for this value."
    }
    grade.finish(run, None, None, sorting, tmp_path)
    grade.write(tmp_path, run, spec_module.load(), results)
    report = (tmp_path / "report.md").read_text()
    assert "| entry | 3 | 0 | not run | not run | — | not run |" in report


def test_the_cases_digest_covers_only_the_cases_the_answers_use(tmp_path):
    answers, pool = tmp_path / "summer-fair.yaml", tmp_path / "cases.yaml"
    answers.write_text(FAIR_SITUATIONS.read_text())
    text = FAIR_SITUATIONS.with_name("cases.yaml").read_text()

    def recorded(pool_text):
        pool.write_text(pool_text)
        run = grade.Run(id="r", kind="universe", inputs={}, adapters={})
        grade.situations_for(answers, spec_module.read(FAIR), run)
        return run.inputs[f"{pool} (cases used)"]

    first = recorded(text)
    another = (
        "- id: n01\n  text: Lanterns hang over the carts.\n  field: night-market\n"
    )
    assert recorded(text + another + "  tags: {kind: food, who: group}\n") == first
    assert recorded(text.replace("A retired baker", "A young baker")) != first


def test_answers_for_another_universe_are_not_filed(tmp_path):
    run = grade.Run(id="r", kind="universe", inputs={}, adapters={})
    night = {"universe": {"id": "night-market"}}
    source = grade.situations_for(FAIR_SITUATIONS, night, run)
    assert run.notes == [
        (
            "recognition not run: tools/evals/fixtures/situations/summer-fair.yaml holds "
            "answers for summer-fair, not night-market"
        )
    ]
    assert run.inputs == {} and source.answers == {}


def test_stale_answers_are_not_filed_and_say_not_run(tmp_path):
    answers = tmp_path / "summer-fair.yaml"
    answers.write_text(
        FAIR_SITUATIONS.read_text().replace(
            "Only people asked in advance", "Only people named in advance"
        )
    )
    (tmp_path / "cases.yaml").write_text(
        FAIR_SITUATIONS.with_name("cases.yaml").read_text()
    )
    run = grade.Run(
        id="r", kind="universe", inputs={}, adapters={}, tiers=["recognise"]
    )
    source = grade.situations_for(answers, spec_module.read(FAIR), run)
    assert run.notes == [
        (
            "recognition not run for entry: stale answers: a value's meaning changed "
            "since labelling; relabel"
        )
    ]
    _, results = recognition_run(run, source)
    assert [r.final.verdict for r in results][:3] == ["undecided"] * 3
    assert {r.final.tier for r in results[3:]} == {"recognise"}


def test_each_judge_vote_and_filer_placement_is_kept_in_the_verdict_row(tmp_path):
    case = tiers.Case(
        "one-job", fake_spec().universe["rules"]["one-job"], "element.question",
        "elements[x].question", "Who?",
    )  # fmt: skip
    votes = {
        "a": {"verdict": "pass", "critique": "one ask"},
        "b": {"verdict": "fail", "critique": "two asks"},
    }
    placed = {"a": ["Who?"], "light": ["Why?"]}
    result = tiers.Result(
        case,
        [
            tiers.Outcome(
                "undecided", "judgment", {"critique": "a | b", "votes": votes}
            ),
            tiers.Outcome("fail", "sort", {"reason": "light filed", "placed": placed}),
        ],
    )
    result.final = result.trail[-1]
    run = grade.Run(id="r", kind="universe", inputs={}, adapters={})
    grade.write(tmp_path, run, fake_spec(), [result])
    (row,) = [json.loads(line) for line in (tmp_path / "verdicts.jsonl").open()]
    assert row["trail"] == [
        {"tier": "judgment", "verdict": "undecided", "reason": "a | b", "votes": votes},
        {"tier": "sort", "verdict": "fail", "reason": "light filed", "placed": placed},
    ]


def test_a_run_label_is_stored_and_old_runs_without_one_still_load(tmp_path):
    out = tmp_path / "run"
    assert (
        grade.main(
            [
                "universe", "--universe", str(FAIR), "--tiers", "deterministic",
                "--label", "chatgpt-side", "--out", str(out),
            ]
        )
        == 0
    )  # fmt: skip
    stored = json.loads((out / "run.json").read_text())
    assert stored["label"] == "chatgpt-side"
    del stored["label"]
    (out / "run.json").write_text(json.dumps(stored))
    assert grade.rebuild(out, spec_module.load()) == (out / "report.md").read_text()
    assert grade.Run(id="r", kind="universe", inputs={}, adapters={}).label == ""


def test_a_cli_is_required_only_when_one_of_its_models_is_named(tmp_path, monkeypatch):
    folder = tmp_path / "bin"
    folder.mkdir()
    (folder / "codex").write_text("#!/bin/sh\nexit 1\n")
    (folder / "codex").chmod(0o755)
    monkeypatch.setenv("PATH", str(folder))
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex-home"))
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    run = grade.Run(id="r", kind="universe", inputs={}, adapters={})
    _, judge = grade._adapters(("judgment",), "codex:a,codex:b", run)
    assert judge.models == ("codex:a", "codex:b") and run.notes == []
    sorting = grade.sorting(("sort",), "universe", run, ["codex:a"], "codex:light")
    assert [f.name for f in sorting.sorter.filers] == ["codex:a", "codex:light"]
    grade.finish(run, None, judge, sorting, tmp_path)
    assert run.adapters["judgment"] == "judges: codex:a, codex:b"
    assert "judgment cost: n/a" in run.notes and "sort cost: n/a" in run.notes
    run = grade.Run(id="r", kind="universe", inputs={}, adapters={})
    assert grade._adapters(("judgment",), "codex:a,claude-x", run) == (None, None)
    assert grade.sorting(("sort",), "universe", run, ["codex:a"], "claude-x") is None
    assert run.notes == [
        "judgment tier off: the claude CLI is not on PATH",
        "sort off: the claude CLI is not on PATH",
    ]


def shared_scope(tmp_path, guidance_names):
    """A .knowledge-bus/ holding universes alpha and beta; guidance_names maps each file name
    to the universe that guidance guides."""
    scope = tmp_path / ".knowledge-bus"
    scope.mkdir()
    for name in ("alpha", "beta"):
        (scope / f"{name}.universe.kbp.yaml").write_text(
            yaml.safe_dump({"universe": {"id": name}, "elements": []})
        )
    for file, guides in guidance_names.items():
        (scope / file).write_text(
            yaml.safe_dump({"guidance": {"id": f"{guides}-guidance", "guides": guides}})
        )
    return scope


def test_guidance_is_the_document_that_guides_the_universe_whatever_its_file_name(
    tmp_path,
):
    scope = shared_scope(
        tmp_path,
        {"alpha.type-guidance.kbp.yaml": "beta", "notes.kbp.yaml": "alpha"},
    )
    assert grade.guidance_for(scope / "alpha.universe.kbp.yaml") == (
        scope / "notes.kbp.yaml"
    )
    assert grade.guidance_for(scope / "beta.universe.kbp.yaml") == (
        scope / "alpha.type-guidance.kbp.yaml"
    )


def test_a_universe_no_guidance_guides_has_none_and_two_guidances_are_refused(
    tmp_path,
):
    scope = shared_scope(tmp_path, {"a.kbp.yaml": "alpha"})
    assert grade.guidance_for(scope / "beta.universe.kbp.yaml") is None
    (scope / "b.kbp.yaml").write_text(
        yaml.safe_dump({"guidance": {"id": "again", "guides": "alpha"}})
    )
    with pytest.raises(ValueError, match="alpha.*multiple"):
        grade.guidance_for(scope / "alpha.universe.kbp.yaml")


def test_a_graded_run_records_its_universe_and_the_guidance_that_guides_it(tmp_path):
    scope = shared_scope(tmp_path, {"notes.kbp.yaml": "alpha"})
    out = tmp_path / "run"
    universe = scope / "alpha.universe.kbp.yaml"
    args = ["universe", "--universe", str(universe), "--tiers", "deterministic"]
    assert grade.main([*args, "--out", str(out)]) == 0
    stored = json.loads((out / "run.json").read_text())
    assert stored["universe"] == "alpha"
    assert str(scope / "notes.kbp.yaml") in stored["inputs"]
    assert stored["kinds"] == {
        "evals/universe.yaml": "spec",
        "evals/skills.yaml": "skills-spec",
        str(universe): "universe",
        str(scope / "notes.kbp.yaml"): "guidance",
    }
    other = tmp_path / "other"
    beta = scope / "beta.universe.kbp.yaml"
    assert grade.main(["universe", "--universe", str(beta), "--tiers", "deterministic", "--out", str(other)]) == 0  # fmt: skip
    inputs = json.loads((other / "run.json").read_text())["inputs"]
    assert not [name for name in inputs if "guidance" in name]
