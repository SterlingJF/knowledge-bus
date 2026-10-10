"""The universe key that says when no artifact is needed, by declared version.

kbp/0.8 names it `no_artifact`. A kbp/0.7 document still names it
`empty_composition`, with the same shape, and is checked as 0.7.
"""

import copy
from pathlib import Path

import pytest
import yaml

from kbp_conform import checker
from kbp_conform.checker import check

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "protocol/knowledge-bus-protocol.yaml"
MINIMAL_0_7 = ROOT / "protocol/conformance/pass/minimal.kbp.yaml"


@pytest.fixture
def protocol():
    return yaml.safe_load(PROTOCOL.read_text())


@pytest.fixture
def universe_0_7():
    document = yaml.safe_load(MINIMAL_0_7.read_text())
    assert document["universe"]["conforms_to"] == "kbp/0.7"
    assert "empty_composition" in document
    return document


@pytest.fixture
def universe_0_8(universe_0_7):
    document = copy.deepcopy(universe_0_7)
    document["universe"]["conforms_to"] = "kbp/0.8"
    document["no_artifact"] = document.pop("empty_composition")
    return document


def failures(output):
    return [line for line in output.splitlines() if line.startswith("  FAIL")]


def test_a_0_8_document_says_when_no_artifact_is_needed(protocol, universe_0_8):
    assert check(protocol, universe_0_8, "fixture")


def test_a_0_7_document_keeps_empty_composition(protocol, universe_0_7):
    assert check(protocol, universe_0_7, "fixture")


def test_a_0_8_document_refuses_the_old_name(protocol, universe_0_8, capsys):
    universe_0_8["empty_composition"] = universe_0_8.pop("no_artifact")
    assert not check(protocol, universe_0_8, "fixture")
    output = capsys.readouterr().out
    assert "document: missing required 'no_artifact'" in output
    assert "kbp/0.8 renamed 'empty_composition' to 'no_artifact'" in output
    assert len(failures(output)) == 1, output


def test_a_0_8_document_refuses_both_names(protocol, universe_0_8, capsys):
    universe_0_8["empty_composition"] = copy.deepcopy(universe_0_8["no_artifact"])
    assert not check(protocol, universe_0_8, "fixture")
    output = capsys.readouterr().out
    assert "document: unsanctioned ['empty_composition']" in output
    assert "kbp/0.8 renamed 'empty_composition' to 'no_artifact'" in output


def test_a_0_7_document_refuses_the_new_name(protocol, universe_0_7, capsys):
    universe_0_7["no_artifact"] = universe_0_7.pop("empty_composition")
    assert not check(protocol, universe_0_7, "fixture")
    output = capsys.readouterr().out
    assert "document: missing required 'empty_composition'" in output
    assert "a kbp/0.7 document names it 'empty_composition'" in output
    assert len(failures(output)) == 1, output


def test_a_0_7_document_refuses_both_names(protocol, universe_0_7, capsys):
    universe_0_7["no_artifact"] = copy.deepcopy(universe_0_7["empty_composition"])
    assert not check(protocol, universe_0_7, "fixture")
    output = capsys.readouterr().out
    assert "document: unsanctioned ['no_artifact']" in output


@pytest.mark.parametrize(
    "fixture,key",
    [("universe_0_7", "empty_composition"), ("universe_0_8", "no_artifact")],
)
def test_predicate_failures_name_the_key_the_document_uses(
    protocol, request, capsys, fixture, key
):
    universe = request.getfixturevalue(fixture)
    universe[key]["when"] = {"not-a-frame": ["yes"]}
    assert not check(protocol, universe, "fixture")
    output = capsys.readouterr().out
    assert f"{key}.when: unknown frame 'not-a-frame'" in output


@pytest.mark.parametrize(
    "version,key", [("0.7", "empty_composition"), ("0.8", "no_artifact")]
)
def test_document_key_names_the_key_each_version_uses(protocol, version, key):
    assert checker.document_key(protocol, "universe", "no_artifact", version) == key


def test_the_rename_keeps_the_protocol_sound(protocol):
    assert checker.self_check(protocol) == []


@pytest.mark.parametrize(
    "patch,reason",
    [
        (
            lambda r: r.update({"not-a-key": {"was": "x", "since": 0.8}}),
            "renamed names ['not-a-key'], which `document` does not declare",
        ),
        (
            lambda r: r["no_artifact"].update({"was": "frames"}),
            "renamed.no_artifact.was: 'frames' is still a document key",
        ),
        (
            lambda r: r["no_artifact"].update({"since": 9.9}),
            "renamed.no_artifact.since: 9.9 is later than protocol.version",
        ),
        (
            lambda r: r["no_artifact"].pop("was"),
            "renamed.no_artifact: needs { was, since }",
        ),
    ],
)
def test_renamed_must_describe_a_real_rename(protocol, patch, reason):
    patch(protocol["declarations"]["universe"]["renamed"])
    assert any(reason in item for item in checker.self_check(protocol))


def test_renamed_must_be_a_mapping(protocol):
    protocol["declarations"]["universe"]["renamed"] = ["no_artifact"]
    assert any(
        "renamed: not a mapping" in item for item in checker.self_check(protocol)
    )
