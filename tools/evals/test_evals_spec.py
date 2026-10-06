"""The neutral eval spec: structure, tier vocabulary, reasons and labelled examples."""

import copy
import json
import shutil

import pytest
import spec
import yaml

UNIVERSE = {
    "schema": "evals/1",
    "slice": "universe",
    "subjects": {"element.question": "elements[].question"},
    "cases": {
        "default": {
            "skill": "kb-evolve",
            "ask": "Improve this text. Reply with it only.",
        },
        "element.question": {
            "skill": "kb-evolve",
            "ask": "Rewrite this question to meet the bar. Reply with the question only.",
        },
    },
    "rules": {
        "names-the-subject": {
            "rule": "A statement names its subject instead of a pronoun.",
            "why": "A reader who lands on one statement has nothing a pronoun can point back to.",
            "applies_to": ["element.question"],
            "deterministic": {
                "complete": False,
                "checks": [{"terms": ["it"], "then": "flag"}],
            },
            "decision": {
                "ask": "Does the text open with a pronoun?",
                "type": "yes-no",
                "fail_when": "yes",
            },
            "judgment": {
                "pass": "PASS if every subject is named.",
                "fail": "FAIL if a pronoun stands in.",
            },
            "examples": [
                {
                    "text": "It does not define the format.",
                    "verdict": "fail",
                    "note": "The pronoun hides what leaves the format undefined.",
                },
                {
                    "text": "They decide the order.",
                    "verdict": "fail",
                    "note": "The pronoun hides who decides.",
                },
                {
                    "text": "KBP does not define the format.",
                    "verdict": "pass",
                    "note": "The protocol is named.",
                },
                {
                    "text": "The owner decides the order.",
                    "verdict": "pass",
                    "note": "The person who decides is named.",
                    "subject": "element.question",
                    "context": {"id": "segments"},
                },
            ],
        }
    },
}
SKILLS = {
    "schema": "evals/1",
    "slice": "skills",
    "subjects": {"report-to-owner": "each report the agent gives the owner"},
    "behaviours": {
        "reports-plainly": {
            "behaviour": "Reports in plain terms.",
            "why": "The owner acts on a report only after understanding it.",
            "skills": ["kb-evolve"],
            "applies_to": ["report-to-owner"],
            "judgment": {"pass": "PASS if plain.", "fail": "FAIL if figurative."},
            "examples": [
                {
                    "text": "We marry the spectrum to the canonical model.",
                    "verdict": "fail",
                    "note": "A metaphor stands where the change should be.",
                },
                {
                    "text": "The tapestry of answers sings.",
                    "verdict": "fail",
                    "note": "Figurative words say nothing the owner can check.",
                },
                {
                    "text": "Two answers now cite the pricing note.",
                    "verdict": "pass",
                    "note": "It says what changed in literal words.",
                },
                {
                    "text": "One question is still open.",
                    "verdict": "pass",
                    "note": "It states the remaining work plainly.",
                },
            ],
        }
    },
    "scenarios": {
        "plain-report": {
            "skill": "kb-evolve",
            "prompt": "Summarise the change.",
            "fixture": "none",
            "owner": ["Plain terms, please."],
            "required": ["reports-plainly"],
        }
    },
}


def write(folder, universe=UNIVERSE, skills=SKILLS):
    for name, doc in (("universe", universe), ("skills", skills)):
        (folder / f"{name}.yaml").write_text(yaml.safe_dump(doc, sort_keys=False))
    return spec.load(folder)


@pytest.fixture
def skills_dir(tmp_path):
    folder = tmp_path / "skills"
    (folder / "kb-evolve").mkdir(parents=True)
    (folder / "kb-evolve" / "SKILL.md").write_text("---\nname: kb-evolve\n---\n")
    return folder


def problems_for(tmp_path, skills_dir, **docs):
    folder = tmp_path / "evals"
    folder.mkdir(exist_ok=True)
    return spec.problems(write(folder, **docs), skills_dir=skills_dir)


def test_a_complete_spec_has_no_problems(tmp_path, skills_dir):
    assert problems_for(tmp_path, skills_dir) == []


def test_the_spec_is_two_files(tmp_path):
    folder = tmp_path / "evals"
    folder.mkdir()
    loaded = write(folder)
    assert (loaded.universe, loaded.skills, loaded.folder) == (UNIVERSE, SKILLS, folder)
    assert not hasattr(loaded, "evidence")


def test_every_rule_and_behaviour_says_why(tmp_path, skills_dir):
    universe, skills = copy.deepcopy(UNIVERSE), copy.deepcopy(SKILLS)
    del universe["rules"]["names-the-subject"]["why"]
    skills["behaviours"]["reports-plainly"]["why"] = ""
    found = problems_for(tmp_path, skills_dir, universe=universe, skills=skills)
    assert found == [
        "universe/names-the-subject: needs why",
        "skills/reports-plainly: needs why",
    ]


def test_every_example_has_a_text_and_a_note(tmp_path, skills_dir):
    universe = copy.deepcopy(UNIVERSE)
    examples = universe["rules"]["names-the-subject"]["examples"]
    del examples[1]["note"]
    examples[3]["text"] = ""
    found = problems_for(tmp_path, skills_dir, universe=universe)
    assert found == [
        "universe/names-the-subject: example 2 needs a note",
        "universe/names-the-subject: example 4 needs text",
    ]


def test_every_rule_needs_two_failing_and_two_passing_examples(tmp_path, skills_dir):
    universe, skills = copy.deepcopy(UNIVERSE), copy.deepcopy(SKILLS)
    universe["rules"]["names-the-subject"]["examples"].pop()
    skills["subjects"]["proposed-definition"] = "each definition the agent proposes"
    skills["behaviours"]["proposes-to-the-bar"] = {
        "behaviour": "Proposes definitions that meet the universe rules.",
        "why": "A proposal the owner must rewrite costs more than it saves.",
        "skills": ["kb-evolve"],
        "applies_to": ["proposed-definition"],
        "grade_with": "universe",
    }
    found = problems_for(tmp_path, skills_dir, universe=universe, skills=skills)
    assert found == ["universe/names-the-subject: needs at least two pass examples"]


def test_examples_have_a_closed_verdict_and_a_declared_subject(tmp_path, skills_dir):
    universe = copy.deepcopy(UNIVERSE)
    examples = universe["rules"]["names-the-subject"]["examples"]
    examples[0]["verdict"] = "maybe"
    examples[1]["subject"] = "artifact.action"
    found = problems_for(tmp_path, skills_dir, universe=universe)
    assert "universe/names-the-subject: example 1 verdict is pass or fail" in found
    assert "universe/names-the-subject: example 2 subject is not in applies_to" in found


def test_the_spec_carries_no_evidence_ids(tmp_path, skills_dir):
    universe, skills = copy.deepcopy(UNIVERSE), copy.deepcopy(SKILLS)
    rule = universe["rules"]["names-the-subject"]
    rule["evidence"] = ["ev-0001"]
    rule["examples"][0]["evidence"] = "ev-0001"
    skills["scenarios"]["plain-report"]["evidence"] = ["ev-0002"]
    found = problems_for(tmp_path, skills_dir, universe=universe, skills=skills)
    assert found == [
        "universe/names-the-subject: unknown field evidence",
        "universe/names-the-subject: example 1 has unknown field evidence",
        "skills/scenarios/plain-report: unknown field evidence",
    ]


def test_skills_and_grade_with_belong_to_the_skills_slice(tmp_path, skills_dir):
    universe = copy.deepcopy(UNIVERSE)
    rule = universe["rules"]["names-the-subject"]
    rule["skills"] = ["kb-evolve"]
    rule["grade_with"] = "universe"
    found = problems_for(tmp_path, skills_dir, universe=universe)
    assert found == [
        "universe/names-the-subject: unknown field grade_with",
        "universe/names-the-subject: unknown field skills",
    ]


def test_patterns_must_run_on_every_regex_engine(tmp_path, skills_dir):
    universe = copy.deepcopy(UNIVERSE)
    checks = universe["rules"]["names-the-subject"]["deterministic"]["checks"]
    checks.append({"pattern": r"(?<=a)b", "then": "fail"})
    checks.append({"pattern": r"(a)\1", "then": "fail"})
    checks.append({"pattern": r"[(?=]\\\\1", "then": "flag"})
    found = problems_for(tmp_path, skills_dir, universe=universe)
    assert sum("lookaround or backreference" in p for p in found) == 2


def test_decision_and_check_vocabulary_is_closed(tmp_path, skills_dir):
    universe = copy.deepcopy(UNIVERSE)
    rule = universe["rules"]["names-the-subject"]
    rule["decision"]["type"] = "maybe"
    rule["deterministic"]["checks"].append({"vibes": 3, "then": "fail"})
    found = problems_for(tmp_path, skills_dir, universe=universe)
    assert any("decision type" in p for p in found)
    assert any("one of words, pattern, terms" in p for p in found)


def test_a_fail_check_never_fires_on_a_passing_example(tmp_path, skills_dir):
    universe = copy.deepcopy(UNIVERSE)
    checks = universe["rules"]["names-the-subject"]["deterministic"]["checks"]
    checks.append({"terms": ["define"], "then": "fail"})
    found = problems_for(tmp_path, skills_dir, universe=universe)
    assert found == ["universe/names-the-subject: check 2 fails pass example 3"]


def test_vendor_names_stay_out_of_the_spec(tmp_path, skills_dir):
    universe, skills = copy.deepcopy(UNIVERSE), copy.deepcopy(SKILLS)
    rule = universe["rules"]["names-the-subject"]
    rule["why"] = "Sonnet misreads pronouns."
    rule["judgment"]["pass"] = "PASS if Claude agrees."
    scenario = skills["scenarios"]["plain-report"]
    scenario["prompt"] = "Ask OpenAI to summarise the change."
    scenario["owner"].append("GPT said otherwise.")
    found = problems_for(tmp_path, skills_dir, universe=universe, skills=skills)
    assert found == [
        "universe/names-the-subject: why names a vendor: Sonnet",
        "universe/names-the-subject: judgment pass names a vendor: Claude",
        "skills/scenarios/plain-report: prompt names a vendor: OpenAI",
        "skills/scenarios/plain-report: owner reply 2 names a vendor: GPT",
    ]


def test_the_chatgpt_side_and_its_cli_are_vendor_names_too(tmp_path, skills_dir):
    universe = copy.deepcopy(UNIVERSE)
    rule = universe["rules"]["names-the-subject"]
    rule["why"] = "ChatGPT misreads pronouns."
    rule["judgment"]["pass"] = "PASS if Codex agrees."
    assert problems_for(tmp_path, skills_dir, universe=universe) == [
        "universe/names-the-subject: why names a vendor: ChatGPT",
        "universe/names-the-subject: judgment pass names a vendor: Codex",
    ]


def test_vendor_names_stay_out_of_example_notes(tmp_path, skills_dir):
    universe = copy.deepcopy(UNIVERSE)
    examples = universe["rules"]["names-the-subject"]["examples"]
    examples[2]["note"] = "Claude would name the protocol too."
    found = problems_for(tmp_path, skills_dir, universe=universe)
    assert found == [
        "universe/names-the-subject: example 3 note names a vendor: Claude"
    ]


def test_no_string_names_a_session_a_machine_or_a_person(tmp_path, skills_dir):
    universe, skills = copy.deepcopy(UNIVERSE), copy.deepcopy(SKILLS)
    examples = universe["rules"]["names-the-subject"]["examples"]
    examples[0]["context"] = {"session": "3f2a9c1e-7b4d-4e8a-9c2f-1a2b3c4d5e6f"}
    examples[1]["note"] = "Copied from /Users/someone/notes.md."
    skills["subjects"]["0f1e2d3c4b5a69788796a5b4c3d2e1f0"] = "a session id as a key"
    scenario = skills["scenarios"]["plain-report"]
    scenario["prompt"] = "Summarise the change for owner@example.com."
    scenario["owner"] += ["Read ~/notes first.", "See /home/someone/notes."]
    found = problems_for(tmp_path, skills_dir, universe=universe, skills=skills)
    assert found == [
        "universe.yaml: rules.names-the-subject.examples[1].context.session holds a UUID",
        "universe.yaml: rules.names-the-subject.examples[2].note holds an absolute path",
        "skills.yaml: subjects.0f1e2d3c4b5a69788796a5b4c3d2e1f0 holds a UUID",
        "skills.yaml: scenarios.plain-report.prompt holds an email address",
        "skills.yaml: scenarios.plain-report.owner[2] holds an absolute path",
        "skills.yaml: scenarios.plain-report.owner[3] holds an absolute path",
    ]


def test_scenarios_name_real_skills_and_known_behaviours(tmp_path, skills_dir):
    skills = copy.deepcopy(SKILLS)
    skills["scenarios"]["plain-report"]["skill"] = "kb-imagined"
    skills["scenarios"]["plain-report"]["required"] = ["reports-plainly", "ghost"]
    found = problems_for(tmp_path, skills_dir, skills=skills)
    assert any("kb-imagined is not a skill" in p for p in found)
    assert any("ghost is not a behaviour" in p for p in found)


def test_a_scenario_needs_a_prompt_owner_replies_and_required_behaviours(
    tmp_path, skills_dir
):
    skills = copy.deepcopy(SKILLS)
    scenario = skills["scenarios"]["plain-report"]
    scenario["prompt"] = ""
    scenario["owner"] = "Plain terms, please."
    del scenario["required"]
    found = problems_for(tmp_path, skills_dir, skills=skills)
    assert found == [
        "skills/scenarios/plain-report: needs prompt",
        "skills/scenarios/plain-report: needs required",
        "skills/scenarios/plain-report: owner is a list of replies",
    ]


def test_a_fixture_is_none_a_repository_folder_or_a_stated_need(tmp_path, skills_dir):
    skills = copy.deepcopy(SKILLS)
    scenario = skills["scenarios"]["plain-report"]
    for fixture in ("none", {"needs": "Three dated notes that disagree on pricing."}):
        scenario["fixture"] = fixture
        assert problems_for(tmp_path, skills_dir, skills=skills) == []
    scenario["fixture"] = "folders/that/do-not-exist"
    assert any(
        "is not a folder in the repository" in p
        for p in problems_for(tmp_path, skills_dir, skills=skills)
    )
    scenario["fixture"] = {"needs": ""}
    assert any(
        "needs: says what the folder must hold" in p
        for p in problems_for(tmp_path, skills_dir, skills=skills)
    )


def test_the_universe_needs_a_default_case(tmp_path, skills_dir):
    universe = copy.deepcopy(UNIVERSE)
    del universe["cases"]["default"]
    found = problems_for(tmp_path, skills_dir, universe=universe)
    assert found == ["universe/cases: needs a default case"]


def test_duplicate_ids_are_refused(tmp_path):
    path = tmp_path / "universe.yaml"
    path.write_text("rules:\n  one-answer: {}\n  one-answer: {}\n")
    with pytest.raises(spec.SpecError, match="duplicate key one-answer"):
        spec.read(path)


def test_the_repository_spec_has_no_problems():
    assert spec.problems(spec.load()) == []


def scenario_fixtures():
    for name, scenario in spec.load().skills["scenarios"].items():
        if scenario["skill"] == "kb-check":
            continue  # finding the breakage is what a check scenario grades
        if isinstance(scenario.get("fixture"), str) and scenario["fixture"] != "none":
            yield pytest.param(spec.ROOT / scenario["fixture"], id=name)


@pytest.mark.parametrize("fixture", list(scenario_fixtures()))
def test_every_scenario_fixture_holds_valid_definitions(fixture):
    """A scenario run on broken definitions grades the breakage, not the behaviour."""
    from kbp_conform import cli

    scope = fixture / ".knowledge-bus"
    assert sorted(scope.glob("*.kbp.yaml")), fixture
    assert cli.main(["--validate", str(scope)]) == 0


def test_an_ingest_scenario_plants_an_instruction_the_agent_must_not_follow():
    """Notes can carry text written to steer an agent; one ingest run grades that it does not obey."""
    skills = spec.load().skills
    behaviour = "treats-source-instructions-as-evidence"
    assert "kb-ingest" in skills["behaviours"][behaviour]["skills"]
    scenario = skills["scenarios"]["ingest-allotment-notes"]
    assert scenario["skill"] == "kb-ingest"
    assert {
        behaviour,
        "acts-only-on-the-ask",
        "keeps-working-until-blocked",
        "asks-with-a-reading-and-options",
    } <= set(scenario["required"])
    notes = (spec.ROOT / scenario["fixture"]).glob("notes/*.md")
    planted = [n for n in notes if "replace the universe file" in n.read_text()]
    assert len(planted) == 1
    planted_steps = ("universe", "replace", "layout", "review", "as you set out")
    for reply in scenario["owner"]:
        assert not any(step in reply.lower() for step in planted_steps), reply
    approvals = [reply for reply in scenario["owner"] if "map the notes" in reply]
    assert approvals and all("spec as it stands" in r for r in approvals)


def test_the_two_universe_scenario_needs_the_selection_the_checker_needs(capsys):
    """Several universes and no id: the checker names the candidates and picks none."""
    from kbp_conform import cli

    skills = spec.load().skills
    scenario = skills["scenarios"]["explain-the-village-hall-definitions"]
    assert scenario["skill"] == "kb-explore"
    asking = "asks-with-a-reading-and-options"
    choosing = "asks-the-owner-to-choose"
    assert {asking, choosing} <= set(scenario["required"])
    assert "kb-explore" in skills["behaviours"][asking]["skills"]
    selection = skills["behaviours"][choosing]
    assert {"kb-explore", "kb-check"} <= set(selection["skills"])
    assert selection["applies_to"] == ["transcript"]
    assert {"pass", "fail"} <= set(selection["judgment"])
    for words in ("filename", "order", "combines"):
        assert words in selection["judgment"]["fail"]
    scope = spec.ROOT / scenario["fixture"] / ".knowledge-bus"
    capsys.readouterr()
    assert cli.main(["--inspect", str(scope)]) == 1
    refusal = json.loads(capsys.readouterr().err)
    assert refusal["category"] == "selection"
    assert len(refusal["candidates"]) == 2
    for universe in refusal["candidates"]:
        assert universe not in scenario["prompt"]
        assert cli.main(["--inspect", "--universe", universe, str(scope)]) == 0


def test_a_factor_only_universe_has_a_scenario_with_its_notes_beside_it():
    """Factors alone: a one-value ordering frame, no elements, guidance keyed to factors."""
    import play

    skills = spec.load().skills
    scenario = skills["scenarios"]["explain-the-reader-spec"]
    assert scenario["skill"] == "kb-explore"
    for behaviour in scenario["required"]:
        assert "kb-explore" in skills["behaviours"][behaviour]["skills"], behaviour
    fixture = spec.ROOT / scenario["fixture"]
    assert sorted(fixture.glob("notes/*.md"))
    docs = [
        yaml.safe_load(p.read_text())
        for p in sorted((fixture / ".knowledge-bus").glob("*.kbp.yaml"))
    ]
    (universe,) = [doc for doc in docs if "universe" in doc]
    assert universe["universe"]["conforms_to"] == "kbp/0.8"
    for empty in ("statuses", "elements", "artifacts", "relations", "relation_kinds"):
        assert universe[empty] == [], empty
    (ordering,) = universe["frames"]
    assert ordering["role"] == "ordering" and len(ordering["values"]) == 1
    declared = {factor["id"] for factor in universe["factors"]}
    (guidance,) = [doc for doc in docs if "guidance" in doc]
    assert guidance["factors"] and set(guidance["factors"]) <= declared
    assert play.validate(fixture) is True


def test_a_neutral_list_of_candidates_passes_when_nothing_points_to_one():
    """Asking which of several candidates the owner means needs no invented favourite."""
    behaviour = spec.load().skills["behaviours"]["asks-with-a-reading-and-options"]
    decision = behaviour["decision"]
    assert {"options-only", "open"} <= set(decision["fail_when"])
    assert "which-one" in decision["criteria"]
    assert "which-one" not in decision["fail_when"]
    neutral = [
        example
        for example in behaviour["examples"]
        if example["verdict"] == "pass" and "points to" in example["note"]
    ]
    assert len(neutral) == 1
    assert "nothing" in neutral[0]["context"]["sources"]


def test_showing_a_change_for_approval_is_a_needed_stop():
    """Showing exact text for approval is a stop the review behaviours expect, not a needless one."""
    behaviour = spec.load().skills["behaviours"]["keeps-working-until-blocked"]
    assert (
        "to show a proposed change for an approval the task or skill requires"
        in behaviour["judgment"]["pass"]
    )
    assert "approval it does not need" in behaviour["judgment"]["fail"]
    approval_stops = [
        example
        for example in behaviour["examples"]
        if example["verdict"] == "pass" and "Current:" in example["text"]
    ]
    assert len(approval_stops) == 1
    assert "approval" in approval_stops[0]["context"]["owner_turn"]


def test_a_logged_ruling_is_part_of_a_standalone_record():
    """Who ruled and why, kept in a log, is the record's content, not a session reference."""
    behaviour = spec.load().skills["behaviours"]["records-stand-alone"]
    assert behaviour["judgment"]["pass"].endswith(
        "A log's record of a ruling, with who ruled and the reasoning, is part of the"
        " record and not a reference to the session."
    )
    assert [(e["subject"], e["verdict"]) for e in behaviour["examples"]] == [
        ("files-written", "fail"),
        ("files-written", "fail"),
        ("files-written", "fail"),
        ("files-written", "pass"),
        ("files-written", "pass"),
        ("files-written", "pass"),
    ]


def test_a_question_that_proposes_text_must_show_it_exactly():
    """Proposals often end as a question to the owner, so questions are graded for exact text too."""
    behaviour = spec.load().skills["behaviours"]["shows-exact-text-for-review"]
    assert behaviour["applies_to"] == ["question-to-owner", "report-to-owner"]
    assert behaviour["judgment"]["pass"].endswith(
        "A report with no draft, defect or change has no text to show. A question that"
        " shows no draft, defect or change has no text to show."
    )
    assert "proposes no change passes" not in behaviour["judgment"]["pass"]
    assert [(e["subject"], e["verdict"]) for e in behaviour["examples"]] == [
        ("report-to-owner", "fail"),
        ("report-to-owner", "fail"),
        ("report-to-owner", "fail"),
        ("report-to-owner", "pass"),
        ("report-to-owner", "pass"),
        ("report-to-owner", "pass"),
    ]


def validate(scope, capsys):
    """The checker's exit code and its FAIL lines for one scope."""
    from kbp_conform import cli

    capsys.readouterr()
    code = cli.main(["--validate", str(scope)])
    output = capsys.readouterr().out
    return code, [line for line in output.splitlines() if line.startswith("  FAIL")]


def test_adding_terms_to_the_choir_spec_moves_it_to_kbp_0_8(tmp_path, capsys):
    """Terms need kbp/0.8, and the choir fixture declares kbp/0.7, so the change moves it."""
    scenario = spec.load().skills["scenarios"]["add-terms-to-the-choir-spec"]
    assert scenario["skill"] == "kb-evolve"
    assert {
        "restates-the-ask-before-acting",
        "shows-exact-text-for-review",
        "gives-its-own-verdict",
        "acts-only-on-the-ask",
    } <= set(scenario["required"])
    terms, synonym, approval = scenario["owner"]
    wanted = ("section", "concert", "rehearsal")
    assert all(f"'{term}'" in terms.lower() for term in wanted)
    assert "'gig'" in synonym and "concert" in synonym
    assert approval.startswith("Yes")

    scope = spec.ROOT / scenario["fixture"] / ".knowledge-bus"
    assert [p.name for p in scope.glob("*.kbp.yaml")] == ["universe.kbp.yaml"]
    original = yaml.safe_load((scope / "universe.kbp.yaml").read_text())
    assert original["universe"]["conforms_to"] == "kbp/0.7"
    declared = [{"term": term, "means": f"The choir's {term}."} for term in wanted]
    as_0_7 = copy.deepcopy(original)
    as_0_7["universe"]["terms"] = declared
    moved = copy.deepcopy(as_0_7)
    moved["universe"]["conforms_to"] = "kbp/0.8"
    moved["universe"]["version"] = 0.2
    moved["no_artifact"] = moved.pop("empty_composition")
    for name, document in (("as-0-7", as_0_7), ("moved", moved)):
        shutil.copytree(scope, tmp_path / name)
        target = tmp_path / name / "universe.kbp.yaml"
        target.write_text(yaml.safe_dump(document, sort_keys=False))

    code, refusals = validate(tmp_path / "as-0-7", capsys)
    assert code == 1
    assert len(refusals) == 1 and "unsanctioned ['terms']" in refusals[0]
    assert validate(tmp_path / "moved", capsys) == (0, [])


def test_the_check_scenario_fixture_fails_on_a_rename_and_an_unknown_element(
    tmp_path, capsys
):
    """The checker stops at a missing required key, so the unknown element shows after the rename."""
    scenario = spec.load().skills["scenarios"]["check-the-food-bank-spec"]
    assert scenario["skill"] == "kb-check"
    assert {
        "checks-current-sources",
        "claims-match-the-evidence",
        "shows-exact-text-for-review",
        "acts-only-on-the-ask",
        "keeps-working-until-blocked",
    } <= set(scenario["required"])
    for planted in ("empty_composition", "no_artifact", "dietary"):
        assert planted not in scenario["prompt"]

    scope = tmp_path / ".knowledge-bus"
    shutil.copytree(spec.ROOT / scenario["fixture"] / ".knowledge-bus", scope)
    universe = scope / "universe.kbp.yaml"
    code, refusals = validate(scope, capsys)
    assert code == 1
    assert len(refusals) == 1
    assert "renamed 'empty_composition' to 'no_artifact'" in refusals[0]

    text = universe.read_text()
    universe.write_text(text.replace("\nempty_composition:", "\nno_artifact:"))
    code, refusals = validate(scope, capsys)
    assert code == 1
    assert refusals == ["  FAIL  composition refs unknown elements: ['dietary-need']"]

    universe.write_text(universe.read_text().replace("dietary-need,", "dietary-needs,"))
    assert validate(scope, capsys) == (0, [])


SET = ["Which choir member keeps the robe fund?", "Which room hosts rehearsals?"]


def set_rule(**extra):
    examples = [
        {
            "text": text,
            "verdict": verdict,
            "note": "Constructed.",
            "context": {"set": list(SET), "probes": ["The alto treasurer."]},
        }
        for text, verdict in zip(SET * 2, ["fail", "fail", "pass", "pass"])
    ]
    return {
        "rule": "Each question reads clearly within its set.",
        "why": "Overlapping questions file answers twice.",
        "applies_to": ["element.question"],
        "scope": "set",
        "examples": examples,
        **extra,
    }


def test_a_set_rule_may_sort_instead_of_using_a_tier(tmp_path, skills_dir):
    universe = copy.deepcopy(UNIVERSE)
    universe["rules"]["sorts"] = set_rule(
        sort={"ask": "Which question does this answer?", "write": "Write a passage."}
    )
    assert problems_for(tmp_path, skills_dir, universe=universe) == []


def test_scope_is_item_pair_or_set_and_sort_needs_a_set(tmp_path, skills_dir):
    universe = copy.deepcopy(UNIVERSE)
    rule = universe["rules"]["names-the-subject"]
    rule["scope"] = "group"
    universe["rules"]["sorts"] = set_rule(
        scope="item", sort={"ask": "Which?", "write": 3, "extra": "x"}
    )
    universe["rules"]["bare"] = set_rule()
    found = problems_for(tmp_path, skills_dir, universe=universe)
    assert found == [
        "universe/names-the-subject: scope is item, pair or set",
        "universe/sorts: sort is allowed only with scope set",
        "universe/sorts: sort takes ask and write, each a text",
        "universe/bare: needs at least one tier, a sort block or a recognise block",
    ]


def test_set_examples_carry_their_set_and_sort_examples_their_probes(
    tmp_path, skills_dir
):
    universe = copy.deepcopy(UNIVERSE)
    rule = set_rule(sort={"ask": "Which?", "write": "Write."})
    examples = rule["examples"]
    del examples[0]["context"]["set"]
    examples[1]["context"]["set"] = ["Another question?"]
    examples[2]["context"]["probes"] = []
    examples[3]["context"]["probes"] = "The alto treasurer."
    universe["rules"]["sorts"] = rule
    found = problems_for(tmp_path, skills_dir, universe=universe)
    assert found == [
        "universe/sorts: example 1 needs context.set, a list of texts holding its text",
        "universe/sorts: example 2 needs context.set, a list of texts holding its text",
        "universe/sorts: example 3 needs context.probes, a list of passages",
        "universe/sorts: example 4 needs context.probes, a list of passages",
    ]


def test_vendor_names_stay_out_of_the_sort_block(tmp_path, skills_dir):
    universe = copy.deepcopy(UNIVERSE)
    universe["rules"]["sorts"] = set_rule(
        sort={"ask": "Ask Haiku which question.", "write": "Write as GPT would."}
    )
    found = problems_for(tmp_path, skills_dir, universe=universe)
    assert found == [
        "universe/sorts: sort ask names a vendor: Haiku",
        "universe/sorts: sort write names a vendor: GPT",
    ]


def test_a_composition_member_sits_in_its_set_under_its_strength(tmp_path, skills_dir):
    universe = copy.deepcopy(UNIVERSE)
    rule = set_rule(judgment={"pass": "PASS if clear.", "fail": "FAIL if not."})
    for example in rule["examples"]:
        context = example["context"]
        context["strength"] = "core"
        context["set"] = [
            f"core: {t}" if t == example["text"] else t for t in context["set"]
        ]
    rule["examples"][0]["context"]["strength"] = "situational"
    universe["rules"]["members"] = rule
    found = problems_for(tmp_path, skills_dir, universe=universe)
    assert found == [
        "universe/members: example 1 needs context.set, a list of texts holding its text"
    ]


RECOGNISE = {
    "ask": "Which of these fits the situation best?",
    "value_share": 0.75,
    "frame_share": 0.9,
}


def test_a_set_rule_may_recognise_instead_of_using_a_tier(tmp_path, skills_dir):
    universe = copy.deepcopy(UNIVERSE)
    universe["rules"]["recognised"] = set_rule(recognise=dict(RECOGNISE))
    assert problems_for(tmp_path, skills_dir, universe=universe) == []


def test_recognise_needs_a_set_an_ask_and_shares_between_0_and_1(tmp_path, skills_dir):
    universe = copy.deepcopy(UNIVERSE)
    universe["rules"]["item"] = set_rule(scope="item", recognise=dict(RECOGNISE))
    universe["rules"]["shares"] = set_rule(
        recognise={"ask": "", "value_share": 1.5, "frame_share": 0}
    )
    universe["rules"]["extra"] = set_rule(recognise={**RECOGNISE, "write": "Two."})
    found = problems_for(tmp_path, skills_dir, universe=universe)
    takes = "recognise takes ask, a text, and value_share and frame_share, each above 0 and at most 1"
    assert found == [
        "universe/item: recognise is allowed only with scope set",
        f"universe/shares: {takes}",
        f"universe/extra: {takes}",
    ]


def test_recognise_examples_carry_their_set_and_situations(tmp_path, skills_dir):
    universe = copy.deepcopy(UNIVERSE)
    rule = set_rule(recognise=dict(RECOGNISE))
    del rule["examples"][0]["context"]["set"]
    rule["examples"][1]["context"]["probes"] = []
    universe["rules"]["recognised"] = rule
    found = problems_for(tmp_path, skills_dir, universe=universe)
    assert found == [
        "universe/recognised: example 1 needs context.set, a list of texts holding its text",
        "universe/recognised: example 2 needs context.probes, a list of passages",
    ]


def test_vendor_names_stay_out_of_the_recognise_block(tmp_path, skills_dir):
    universe = copy.deepcopy(UNIVERSE)
    universe["rules"]["recognised"] = set_rule(
        recognise={**RECOGNISE, "ask": "Ask Jev which value fits."}
    )
    found = problems_for(tmp_path, skills_dir, universe=universe)
    assert found == ["universe/recognised: recognise ask names a vendor: Jev"]
