"""Tier semantics: what each tier decides, and how undecided cases escalate."""

import tiers

TERSE = {
    "rule": "A question has at most eight words.",
    "deterministic": {
        "complete": True,
        "checks": [{"words": {"max": 8}, "then": "fail"}],
    },
}
ONE_JOB = {
    "rule": "A question asks for one thing.",
    "deterministic": {
        "complete": False,
        "checks": [{"pattern": r"\b(and|or)\b", "ignore_case": True, "then": "flag"}],
    },
    "decision": {
        "ask": "Does it need two answers?",
        "type": "yes-no",
        "fail_when": "yes",
    },
    "judgment": {"pass": "PASS if one answer.", "fail": "FAIL if two."},
}


def case(rule, text, rule_id="r"):
    return tiers.Case(
        rule_id=rule_id,
        rule=rule,
        subject="element.question",
        ref="element:x",
        text=text,
    )


def test_words_are_runs_of_letters_digits_apostrophes_and_hyphens():
    assert tiers.words("Who's served, by a well-known 3-step plan?") == [
        "Who's",
        "served",
        "by",
        "a",
        "well-known",
        "3-step",
        "plan",
    ]


def test_a_complete_check_set_passes_when_nothing_fires():
    outcome = tiers.deterministic(TERSE["deterministic"], "Who exactly is served?")
    assert (outcome.verdict, outcome.tier) == ("pass", "deterministic")


def test_a_fail_check_fails_and_names_the_check():
    outcome = tiers.deterministic(
        TERSE["deterministic"],
        "What future are we committing to and why is it worth wanting?",
    )
    assert outcome.verdict == "fail"
    assert outcome.detail["fired"] == [
        {"words": {"max": 8}, "then": "fail", "count": 12}
    ]


def test_a_flag_or_an_incomplete_set_leaves_the_case_undecided():
    flagged = tiers.deterministic(ONE_JOB["deterministic"], "Who is served, and how?")
    quiet = tiers.deterministic(ONE_JOB["deterministic"], "Who is served?")
    assert flagged.verdict == quiet.verdict == "undecided"
    assert flagged.detail["fired"] and not quiet.detail["fired"]


def test_terms_match_whole_words_case_insensitively():
    block = {
        "complete": True,
        "checks": [{"terms": ["it", "this thing"], "then": "fail"}],
    }
    assert tiers.deterministic(block, "It does not define").verdict == "fail"
    assert tiers.deterministic(block, "Use this thing well").verdict == "fail"
    assert tiers.deterministic(block, "Iterate on items").verdict == "pass"


def test_paths_fail_outside_the_allowed_globs():
    block = {
        "complete": True,
        "checks": [{"paths": {"allow": [".knowledge-bus/**"]}, "then": "fail"}],
    }
    assert tiers.deterministic(block, ".knowledge-bus/answers.yaml").verdict == "pass"
    assert tiers.deterministic(block, "notes/pricing.md").verdict == "fail"


def test_escalation_stops_at_the_first_settled_tier():
    calls = {"decide": 0, "judge": 0}

    def decide(cases):
        calls["decide"] += len(cases)
        return [
            tiers.Outcome("undecided" if "how" in c.text else "pass", "decision", {})
            for c in cases
        ]

    def judge(cases):
        calls["judge"] += len(cases)
        return [
            tiers.Outcome("fail", "judgment", {"critique": "two answers"})
            for _ in cases
        ]

    cases = [
        case(ONE_JOB, "Who is served, and how?"),
        case(ONE_JOB, "Who is served?"),
        case(TERSE, "Who is served?"),
    ]
    results = tiers.run(cases, decide=decide, judge=judge)
    assert [r.final.verdict for r in results] == ["fail", "pass", "pass"]
    assert [r.final.tier for r in results] == ["judgment", "decision", "deterministic"]
    assert calls == {"decide": 2, "judge": 1}
    assert [o.tier for o in results[0].trail] == [
        "deterministic",
        "decision",
        "judgment",
    ]


def test_a_definite_deterministic_fail_never_reaches_a_model():
    rule = dict(
        ONE_JOB,
        deterministic={
            "complete": False,
            "checks": [{"pattern": r"\?.*\?", "then": "fail"}],
        },
    )

    def refuse(cases):
        raise AssertionError("no model call expected")

    (result,) = tiers.run([case(rule, "Who? And why?")], decide=refuse, judge=refuse)
    assert (result.final.verdict, result.final.tier) == ("fail", "deterministic")


def test_tiers_can_be_limited_and_undecided_goes_to_the_owner():
    (result,) = tiers.run(
        [case(ONE_JOB, "Who is served, and how?")], only=("deterministic",)
    )
    assert result.final.verdict == "undecided"
    assert result.final.tier == "owner"


def test_each_tier_can_run_alone_for_calibration():
    def decide(cases):
        return [tiers.Outcome("fail", "decision", {}) for _ in cases]

    (result,) = tiers.run(
        [case(ONE_JOB, "Who is served?")], decide=decide, only=("decision",)
    )
    assert [o.tier for o in result.trail] == ["decision"]
    assert result.final.verdict == "fail"
