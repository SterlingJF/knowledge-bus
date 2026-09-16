"""Predicate and membership evaluation."""

import copy
import itertools

import pytest

from kbp_conform.evaluation import (
    artifact_availability,
    evaluate_member,
    evaluate_predicate,
)


@pytest.mark.parametrize("a,b", list(itertools.product([True, False, None], repeat=2)))
def test_three_valued_and(a, b):
    context = {
        key: "yes" if value is True else "no"
        for key, value in [("a", a), ("b", b)]
        if value is not None
    }
    expected = False if False in (a, b) else None if None in (a, b) else True
    assert evaluate_predicate({"a": ["yes"], "b": ["yes"]}, context) is expected


@pytest.mark.parametrize(
    "context,expected",
    [
        ({"outcome": {"form": "service", "replication": "serial"}}, True),
        ({"outcome": {"form": "artifact"}}, None),
        ({"outcome": {"form": "claim"}}, False),
    ],
)
def test_facets_require_all_conditions(context, expected):
    predicate = {
        "outcome": {"form": ["artifact", "service"], "replication": ["serial"]}
    }
    assert evaluate_predicate(predicate, context) is expected


def test_empty_predicate_is_true():
    assert evaluate_predicate({}, {}) is True


def test_empty_alternatives_are_false():
    assert evaluate_predicate({"a": []}, {}) is False


@pytest.mark.parametrize(
    "actual,expected", [("yes", "core"), ("no", "situational"), (None, None)]
)
def test_conditional_core_remains_available(actual, expected):
    assert evaluate_member(
        {"element": "x", "when": {"a": ["yes"]}}, "core", {"a": actual}
    ) == {
        "applicability": "available",
        "strength": expected,
    }


@pytest.mark.parametrize(
    "actual,expected", [("yes", "available"), ("no", "excluded"), (None, "unresolved")]
)
def test_conditional_situational_availability(actual, expected):
    result = evaluate_member(
        {"element": "x", "when": {"a": ["yes"]}}, "situational", {"a": actual}
    )
    assert result["applicability"] == expected
    assert result["strength"] == ("situational" if expected == "available" else None)


@pytest.mark.parametrize("strength", ["core", "situational"])
def test_gate_precedes_membership(strength):
    entry = {"element": "x", "when": {"a": ["yes"]}}
    assert (
        evaluate_member(entry, strength, {"gate": "no"}, {"gate": ["yes"]})[
            "applicability"
        ]
        == "excluded"
    )
    assert (
        evaluate_member(entry, strength, {}, {"gate": ["yes"]})["applicability"]
        == "unresolved"
    )


@pytest.mark.parametrize("strength", ["core", "situational"])
def test_unconditional_member_keeps_declared_strength(strength):
    assert evaluate_member("x", strength, {}) == {
        "applicability": "available",
        "strength": strength,
    }


@pytest.mark.parametrize(
    "disabled,empty,expected",
    [
        (True, True, "disabled"),
        (True, False, "disabled"),
        (True, None, "disabled"),
        (False, True, "empty"),
        (False, False, "applicable"),
        (False, None, "unresolved"),
        (None, True, "empty"),
        (None, False, "unresolved"),
        (None, None, "unresolved"),
    ],
)
def test_artifact_suppression_precedes_membership(disabled, empty, expected):
    context = {
        key: "yes" if value else "no"
        for key, value in [("disabled", disabled), ("empty", empty)]
        if value is not None
    }
    assert (
        artifact_availability({"disabled": ["yes"]}, {"empty": ["yes"]}, context)
        == expected
    )


def test_artifact_without_disable_condition_is_applicable():
    assert (
        artifact_availability(None, {"empty": ["yes"]}, {"empty": "no"}) == "applicable"
    )


def test_predicate_rejects_multiple_context_values():
    with pytest.raises(TypeError, match="one value per dimension"):
        evaluate_predicate(
            {"outcome": ["artifact"]}, {"outcome": ["artifact", "service"]}
        )


def test_member_rejects_conflicting_strength():
    with pytest.raises(ValueError, match="Explicit strength conflicts"):
        evaluate_member({"element": "x", "strength": "situational"}, "core", {})


@pytest.mark.parametrize(
    "gate,condition,expected",
    [
        ("yes", "yes", {"applicability": "available", "strength": "core"}),
        ("yes", "no", {"applicability": "available", "strength": "situational"}),
        ("yes", None, {"applicability": "available", "strength": None}),
        ("no", "yes", {"applicability": "excluded", "strength": None}),
        ("no", "no", {"applicability": "excluded", "strength": None}),
        ("no", None, {"applicability": "excluded", "strength": None}),
        (None, "yes", {"applicability": "unresolved", "strength": None}),
        (None, "no", {"applicability": "unresolved", "strength": None}),
        (None, None, {"applicability": "unresolved", "strength": None}),
    ],
)
def test_gate_precedes_conditional_core(gate, condition, expected):
    assert (
        evaluate_member(
            {"element": "x", "when": {"required": ["yes"]}},
            "core",
            {"allowed": gate, "required": condition},
            {"allowed": ["yes"]},
        )
        == expected
    )


def test_member_evaluation_preserves_inputs():
    entry = {"element": "x", "mode": "links", "when": {"authority": ["approve"]}}
    context = {"authority": "notify"}
    before = copy.deepcopy((entry, context))
    evaluate_member(entry, "core", context)
    assert (entry, context) == before


@pytest.mark.parametrize("first,second", [("yes", "no"), ("no", "yes")])
def test_predicate_dimension_order_does_not_change_result(first, second):
    context = {"a": first, "b": second}
    assert evaluate_predicate({"a": ["yes"], "b": ["yes"]}, context) is False
    assert evaluate_predicate({"b": ["yes"], "a": ["yes"]}, context) is False
