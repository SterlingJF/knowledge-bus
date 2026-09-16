"""Validation of resolved frame context."""

import copy

import pytest

from kbp_conform import evaluation

FRAMES = [
    {"id": "authority", "values": ["approve", "notify"]},
    {"id": "outcome", "facets": {"form": ["service", "artifact", "claim"]}},
    {"id": "registry", "source": "external"},
]


@pytest.mark.parametrize(
    "context,message",
    [
        ({"authority": "banana"}, "authority: invalid context value"),
        ({"authority": ["approve"]}, "authority: invalid context value"),
        ({"outcome": "service"}, "outcome: faceted context must be a mapping"),
        (
            {"outcome": {"unknown": "service"}},
            "outcome.unknown: undeclared context facet",
        ),
        ({"outcome": {"form": "banana"}}, "outcome.form: invalid context value"),
        ({"unknown": "approve"}, "unknown: undeclared context frame"),
    ],
)
def test_context_rejects_invalid_frame_value(context, message):
    with pytest.raises(ValueError, match=message):
        evaluation.validate_context(context, FRAMES)


@pytest.mark.parametrize("context", [None, [], "approve", 1])
def test_context_requires_mapping(context):
    with pytest.raises(TypeError, match="Context must be a mapping"):
        evaluation.validate_context(context, FRAMES)


def test_registry_value_remains_unresolved():
    assert evaluation.validate_context({"registry": "unverified"}, FRAMES) == {
        "registry": None
    }


def test_context_preserves_missing_values():
    assert evaluation.validate_context({}, FRAMES) == {}
    assert evaluation.validate_context({"authority": None, "outcome": {}}, FRAMES) == {
        "authority": None,
        "outcome": {},
    }


def test_context_accepts_declared_option_ids():
    assert evaluation.validate_context(
        {"stage": "only"},
        [{"id": "stage", "values": [{"id": "only", "question": "When?"}]}],
    ) == {"stage": "only"}


def test_context_validation_preserves_inputs():
    original = {
        "authority": "notify",
        "outcome": {"form": "service"},
        "registry": "unverified",
    }
    before = copy.deepcopy((original, FRAMES))
    actual = evaluation.validate_context(original, FRAMES)
    assert actual == {
        "authority": "notify",
        "outcome": {"form": "service"},
        "registry": None,
    }
    assert (original, FRAMES) == before
    actual["outcome"]["form"] = "artifact"
    assert original["outcome"]["form"] == "service"
