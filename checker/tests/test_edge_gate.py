"""Relation edge gates, by declared version.

kbp/0.8 keys an edge gate by the universe's own frames, each with a value that
frame declares, plus the reserved key `latency`, a duration written as one
nonblank string; no frame may be named latency. A kbp/0.7 edge gate keeps its
0.7 shape and is not checked.
"""

import copy
from pathlib import Path

import pytest
import yaml

from kbp_conform import checker
from kbp_conform.checker import check

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "protocol/knowledge-bus-protocol.yaml"
EDGE_GATE = ROOT / "protocol/conformance/pass/edge-gate.kbp.yaml"
PRODUCT_DEVELOPMENT = ROOT / "universes/product-development/universe.kbp.yaml"
WHERE = "relation the-question->the-record.gate"


@pytest.fixture
def protocol():
    return yaml.safe_load(PROTOCOL.read_text())


@pytest.fixture
def universe_0_8():
    document = yaml.safe_load(EDGE_GATE.read_text())
    assert document["universe"]["conforms_to"] == "kbp/0.8"
    assert "authority" not in {f["id"] for f in document["frames"]}
    return document


@pytest.fixture
def universe_0_7(universe_0_8):
    document = copy.deepcopy(universe_0_8)
    document["universe"]["conforms_to"] = "kbp/0.7"
    document["empty_composition"] = document.pop("no_artifact")
    return document


def gated(universe, gate):
    universe["relations"][0]["gate"] = gate
    return universe


def failures(output):
    return [line for line in output.splitlines() if line.startswith("  FAIL")]


@pytest.mark.parametrize(
    "gate",
    [
        {"review": "full"},
        {"review": ["light", "full"]},
        {"review": "full", "latency": "2d"},
        {"latency": "2d"},
        {},
    ],
)
def test_a_0_8_gate_names_any_declared_frame(protocol, universe_0_8, gate):
    assert check(protocol, gated(universe_0_8, gate), "fixture")


@pytest.mark.parametrize(
    "gate,reason",
    [
        ({"authority": "approve"}, f"{WHERE}: unknown frame 'authority'"),
        ({"review": "banana"}, f"{WHERE}.review: unknown predicate value 'banana'"),
        ({"review": ["banana"]}, f"{WHERE}.review: unknown predicate value 'banana'"),
        ("approve", f"{WHERE}: not a mapping of {{ <frame-id>: <value> }}"),
        ({"latency": ["2d"]}, f"{WHERE}.latency: must be a nonblank string"),
        ({"latency": 2}, f"{WHERE}.latency: must be a nonblank string"),
        ({"latency": " "}, f"{WHERE}.latency: must be a nonblank string"),
    ],
)
def test_a_0_8_gate_is_refused_for_its_own_reason(
    protocol, universe_0_8, capsys, gate, reason
):
    assert not check(protocol, gated(universe_0_8, gate), "fixture")
    output = capsys.readouterr().out
    assert reason in output
    assert len(failures(output)) == 1, output


def test_a_0_8_gate_may_not_name_a_factor(protocol, universe_0_8, capsys):
    universe_0_8["factors"] = [
        {
            "id": "budget",
            "code": "ka1a1",
            "question": "How much is there to spend?",
            "set_by": "scope",
            "values": ["small", "large"],
        }
    ]
    assert not check(protocol, gated(universe_0_8, {"budget": "small"}), "fixture")
    assert f"{WHERE}: factor 'budget' may not be referenced" in capsys.readouterr().out


@pytest.mark.parametrize(
    "gate",
    [
        {"authority": "approve", "latency": "2d"},
        {"review": "banana"},
        {"anything": ["at", "all"]},
        {"latency": ["2d"]},
        "approve",
    ],
)
def test_a_0_7_gate_is_not_checked(protocol, universe_0_7, gate):
    assert check(protocol, gated(universe_0_7, gate), "fixture")


def latency_frame(universe):
    universe["frames"].append(
        {
            "id": "latency",
            "code": "fa1a9",
            "role": "gating",
            "set_by": "scope",
            "attaches_to": "artifact",
            "values": ["fast", "slow"],
        }
    )
    return universe


def test_a_0_8_universe_may_not_name_a_frame_latency(protocol, universe_0_8, capsys):
    assert not check(protocol, latency_frame(universe_0_8), "fixture")
    output = capsys.readouterr().out
    assert "frame 'latency': reserved for an edge gate's duration" in output
    assert len(failures(output)) == 1, output


def test_a_0_7_universe_may_name_a_frame_latency(protocol, universe_0_7):
    assert check(protocol, latency_frame(universe_0_7), "fixture")


def test_product_development_keeps_its_authority_gate(protocol):
    universe = yaml.safe_load(PRODUCT_DEVELOPMENT.read_text())
    gates = [r["gate"] for r in universe["relations"] if "gate" in r]
    assert gates == [{"authority": "approve"}]
    assert check(protocol, universe, "product-development")


def test_the_edge_gate_reshape_keeps_the_protocol_sound(protocol):
    assert checker.self_check(protocol) == []


@pytest.mark.parametrize(
    "patch,reason",
    [
        (
            lambda r: r.update({"not-a-field": {"was": "x", "since": 0.8}}),
            "reshaped names ['not-a-field'], which the shape does not declare",
        ),
        (
            lambda r: r["gate"].update({"since": 0.9}),
            "reshaped.gate.since: 0.9 is later than protocol.version",
        ),
        (
            lambda r: r["gate"].pop("was"),
            "reshaped.gate: needs { was, since }",
        ),
    ],
)
def test_reshaped_must_describe_a_real_reshape(protocol, patch, reason):
    patch(protocol["relations"]["edge"]["reshaped"])
    assert any(reason in item for item in checker.self_check(protocol))


def test_reshaped_must_be_a_mapping(protocol):
    protocol["relations"]["edge"]["reshaped"] = ["gate"]
    assert any(
        "reshaped: not a mapping" in item for item in checker.self_check(protocol)
    )
