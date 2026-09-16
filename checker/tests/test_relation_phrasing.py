"""Universe-authored relation phrasing."""

from pathlib import Path

import pytest
import yaml

from kbp_conform.checker import check

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def documents():
    protocol = yaml.safe_load(
        (ROOT / "protocol/knowledge-bus-protocol.yaml").read_text()
    )
    universe = yaml.safe_load(
        (ROOT / "protocol/conformance/pass/minimal.kbp.yaml").read_text()
    )
    return protocol, universe


@pytest.mark.parametrize("ordered", [False, True])
def test_phrasing_is_optional(documents, ordered):
    protocol, universe = documents
    universe["relation_kinds"] = [{"id": "context", "ordered": ordered}]
    assert check(protocol, universe, "fixture")


@pytest.mark.parametrize(
    "ordered,phrasing",
    [
        (False, {"forward": "Alongside"}),
        (True, {"forward": "Context from", "reverse": "Context for"}),
    ],
)
def test_accepts_phrasing(documents, ordered, phrasing):
    protocol, universe = documents
    universe["relation_kinds"] = [
        {"id": "context", "ordered": ordered, "phrasing": phrasing}
    ]
    assert check(protocol, universe, "fixture")


@pytest.mark.parametrize(
    "ordered,phrasing,reason",
    [
        (True, {}, "missing required ['forward', 'reverse']"),
        (True, {"forward": "Context from"}, "missing required ['reverse']"),
        (True, {"reverse": "Context for"}, "missing required ['forward']"),
        (
            False,
            {"forward": "Alongside", "reverse": "Alongside"},
            "unexpected keys ['reverse']",
        ),
        (
            False,
            {"forward": "Alongside", "label": "Other"},
            "unexpected keys ['label']",
        ),
        *[
            (False, value, "must be a mapping")
            for value in [None, [], "phrase", 1, False]
        ],
        *[
            (False, {"forward": value}, "forward: must be a nonblank string")
            for value in [None, [], {}, 1, False, "", "  \n"]
        ],
        (
            True,
            {"forward": "Context from", "reverse": " "},
            "reverse: must be a nonblank string",
        ),
    ],
)
def test_rejects_invalid_phrasing(documents, capsys, ordered, phrasing, reason):
    protocol, universe = documents
    universe["relation_kinds"] = [
        {"id": "context", "ordered": ordered, "phrasing": phrasing}
    ]
    assert not check(protocol, universe, "fixture")
    output = capsys.readouterr().out
    assert "relation kind 'context'.phrasing" in output
    assert reason in output
    assert len([line for line in output.splitlines() if line.startswith("  FAIL")]) == 1
    assert "unsanctioned=[" not in output


@pytest.mark.parametrize("value", [None, "false", 0, [], {}])
def test_ordered_requires_boolean(documents, capsys, value):
    protocol, universe = documents
    universe["relation_kinds"] = [{"id": "context", "ordered": value}]
    assert not check(protocol, universe, "fixture")
    assert (
        "relation kind 'context'.ordered: must be a boolean" in capsys.readouterr().out
    )
