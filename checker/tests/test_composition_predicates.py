"""Composition and predicate conformance."""

import copy
from pathlib import Path

import pytest
import yaml

from kbp_conform import cli
from kbp_conform.checker import check, check_guidance, check_pred

ROOT = Path(__file__).resolve().parents[2]


def test_validation_preserves_universe():
    protocol = yaml.safe_load(
        (ROOT / "protocol/knowledge-bus-protocol.yaml").read_text()
    )
    universe = yaml.safe_load(
        (ROOT / "protocol/conformance/pass/minimal.kbp.yaml").read_text()
    )
    before = copy.deepcopy(universe)
    assert check(protocol, universe, "minimal")
    assert universe == before


@pytest.fixture(params=["strength", "mode"])
def member_field(request):
    return request.param


@pytest.fixture(params=["banana", None, True, 7, ["core"], {"value": "core"}])
def invalid_member(request, member_field):
    universe = yaml.safe_load(
        (ROOT / "protocol/conformance/pass/minimal.kbp.yaml").read_text()
    )
    universe["artifacts"][0]["composition"] = {
        "core": [{"element": "the-question", member_field: request.param}]
    }
    return universe


def test_member_enum_rejects_invalid_value(invalid_member, member_field, capsys):
    p_path = ROOT / "protocol/knowledge-bus-protocol.yaml"
    p = yaml.safe_load(p_path.read_text())
    assert not check(p, invalid_member, "malformed-member")
    output = capsys.readouterr().out
    assert f"the-record/the-question: {member_field}" in output
    assert "not in" in output


def test_cli_refuses_invalid_member(invalid_member, member_field, tmp_path, capsys):
    p_path = ROOT / "protocol/knowledge-bus-protocol.yaml"
    path = tmp_path / "malformed.kbp.yaml"
    path.write_text(yaml.safe_dump(invalid_member))
    assert cli.main(["--validate", str(p_path), str(path)]) == 1
    output = capsys.readouterr().out
    assert "NON-CONFORMING" in output
    assert f"the-record/the-question: {member_field}" in output
    assert "Traceback" not in output


@pytest.mark.parametrize("other_list", ["core", "situational"])
@pytest.mark.parametrize("first", ["the-question", {"element": "the-question"}])
@pytest.mark.parametrize("second", ["the-question", {"element": "the-question"}])
def test_duplicate_members_in_either_representation(other_list, first, second, capsys):
    p = yaml.safe_load((ROOT / "protocol/knowledge-bus-protocol.yaml").read_text())
    u = yaml.safe_load(
        (ROOT / "protocol/conformance/pass/minimal.kbp.yaml").read_text()
    )
    composition = u["artifacts"][0]["composition"]
    composition["core"] = [first]
    composition.setdefault(other_list, []).append(second)
    assert not check(p, u, "duplicate")
    assert "duplicate composition member" in capsys.readouterr().out


@pytest.mark.parametrize(
    "definition,value,expected",
    [
        ({"values": ["approve"]}, ["approve"], None),
        ({"values": ["approve"]}, ["banana"], "unknown predicate value"),
        ({"values": [{"id": "only", "question": "Where?"}]}, ["only"], None),
        (
            {"values": [{"id": "only", "question": "Where?"}]},
            ["banana"],
            "unknown predicate value",
        ),
        ({"facets": {"form": ["claim"]}}, {"form": ["claim"]}, None),
        (
            {"facets": {"form": ["claim"]}},
            {"form": ["banana"]},
            "unknown predicate value",
        ),
        ({"facets": {"form": ["claim"]}}, {"banana": ["claim"]}, "unknown facet"),
        ({"source": "external"}, ["not-locally-enumerated"], None),
    ],
)
def test_predicate_declared_values(definition, value, expected):
    failures = []
    check_pred(
        {"context": value},
        "test",
        {"context"},
        failures,
        definitions={"context": definition},
    )
    if expected:
        assert any(expected in failure for failure in failures)
    else:
        assert failures == []


def test_guidance_uses_same_predicate_validation(capsys):
    p = yaml.safe_load((ROOT / "protocol/knowledge-bus-protocol.yaml").read_text())
    u = yaml.safe_load(
        (ROOT / "universes/product-development/universe.kbp.yaml").read_text()
    )
    g = yaml.safe_load(
        (ROOT / "universes/product-development/type-guidance.kbp.yaml").read_text()
    )
    g = copy.deepcopy(g)
    next(iter(g["elements"].values()))[0]["when"] = {"authority": ["banana"]}
    assert not check_guidance(p, g, {u["universe"]["id"]: u}, "guidance")
    assert "unknown predicate value" in capsys.readouterr().out


def test_valid_conditional_strengths_remain_accepted(capsys):
    p = yaml.safe_load((ROOT / "protocol/knowledge-bus-protocol.yaml").read_text())
    u = yaml.safe_load(
        (ROOT / "protocol/conformance/pass/minimal.kbp.yaml").read_text()
    )
    for strength in ["core", "situational"]:
        u["artifacts"][0]["composition"] = {
            strength: [
                {
                    "element": "the-question",
                    "strength": strength,
                    "when": {"stage": ["only"]},
                }
            ]
        }
        assert check(p, u, "valid-strength"), capsys.readouterr().out


@pytest.mark.parametrize(
    "kind,ordered",
    [
        ("feeds", True),
        ("distinct-from", False),
        ("custom-kind", True),
        ("custom-kind", False),
    ],
)
def test_shared_contracts_preserve_custom_kinds(kind, ordered, capsys):
    p = yaml.safe_load((ROOT / "protocol/knowledge-bus-protocol.yaml").read_text())
    u = yaml.safe_load(
        (ROOT / "protocol/conformance/pass/minimal.kbp.yaml").read_text()
    )
    u["relation_kinds"] = [{"id": kind, "ordered": ordered}]
    assert check(p, u, "kind"), capsys.readouterr().out


@pytest.mark.parametrize(
    "list_strength,explicit",
    [
        ("core", "situational"),
        ("situational", "core"),
    ],
)
def test_conflicting_strength_is_rejected(list_strength, explicit, capsys):
    p = yaml.safe_load((ROOT / "protocol/knowledge-bus-protocol.yaml").read_text())
    u = yaml.safe_load(
        (ROOT / "protocol/conformance/pass/minimal.kbp.yaml").read_text()
    )
    u["artifacts"][0]["composition"] = {
        list_strength: [{"element": "the-question", "strength": explicit}],
    }
    assert not check(p, u, "conflict")
    assert "conflicts with composition list" in capsys.readouterr().out
