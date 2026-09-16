"""Shared relation contract validation."""

from pathlib import Path

import pytest
import yaml

from kbp_conform.checker import self_check

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def protocol():
    return yaml.safe_load((ROOT / "protocol/knowledge-bus-protocol.yaml").read_text())


def test_shared_contracts_are_required(protocol):
    del protocol["relations"]["kind_contracts"]
    assert self_check(protocol) == ["relations.kind_contracts: must be a mapping"]


@pytest.mark.parametrize("value", [None, [], "contracts", 1])
def test_shared_contracts_reject_non_mapping(protocol, value):
    protocol["relations"]["kind_contracts"] = value
    assert self_check(protocol) == ["relations.kind_contracts: must be a mapping"]


@pytest.mark.parametrize("kind,ordered", [("feeds", True), ("distinct-from", False)])
@pytest.mark.parametrize(
    "value", [None, [], {}, {"ordered": "true"}, {"ordered": 1}, {"ordered": 0}]
)
def test_shared_kind_rejects_invalid_order(protocol, kind, ordered, value):
    protocol["relations"]["kind_contracts"][kind] = value
    assert self_check(protocol) == [
        f"relations.kind_contracts.{kind}.ordered: must be {ordered}"
    ]


@pytest.mark.parametrize("kind,ordered", [("feeds", True), ("distinct-from", False)])
def test_shared_kind_rejects_reversed_order(protocol, kind, ordered):
    protocol["relations"]["kind_contracts"][kind]["ordered"] = not ordered
    assert self_check(protocol) == [
        f"relations.kind_contracts.{kind}.ordered: must be {ordered}"
    ]


def test_declared_shared_contracts_are_sound(protocol):
    assert self_check(protocol) == []
