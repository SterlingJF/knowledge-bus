"""Universe-authored terms, and the protocol versions a document may declare."""

import copy
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from kbp_conform import checker
from kbp_conform.checker import check

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "protocol/knowledge-bus-protocol.yaml"
MINIMAL = ROOT / "protocol/conformance/pass/minimal.kbp.yaml"


@pytest.fixture
def protocol():
    return yaml.safe_load(PROTOCOL.read_text())


@pytest.fixture
def universe():
    document = yaml.safe_load(MINIMAL.read_text())
    document["universe"]["conforms_to"] = "kbp/0.8"
    document["no_artifact"] = document.pop("empty_composition")
    return document


def failures(output):
    return [line for line in output.splitlines() if line.startswith("  FAIL")]


def test_terms_are_optional(protocol, universe):
    assert check(protocol, universe, "fixture")


def test_an_empty_terms_list_conforms(protocol, universe):
    universe["universe"]["terms"] = []
    assert check(protocol, universe, "fixture")


def test_terms_declared_in_0_8_conform(protocol, universe):
    universe["universe"]["terms"] = [
        {"term": "question", "means": "What an element's content answers."},
        {"term": "the record", "means": "The artifact that holds a question."},
    ]
    assert check(protocol, universe, "fixture")


@pytest.mark.parametrize(
    "terms,reason",
    [
        *[
            (value, "universe terms: not a list of { term, means }")
            for value in [None, "question", {"question": "answers"}, 1]
        ],
        *[
            (
                [value],
                "universe terms[0]: not a mapping of { term, means }",
            )
            for value in [None, "question", ["question", "answers"]]
        ],
        ([{"term": "question"}], "universe terms[0]: missing required ['means']"),
        (
            [{"means": "answers"}],
            "universe terms[0]: missing required ['term']",
        ),
        (
            [{"term": "question", "means": "answers", "example": "x"}],
            "universe terms[0]: unsanctioned ['example']",
        ),
        *[
            (
                [{"term": value, "means": "answers"}],
                "universe terms[0].term: must be a nonblank string",
            )
            for value in [None, 1, [], "", "  \n"]
        ],
        *[
            (
                [{"term": "question", "means": value}],
                "universe terms[0].means: must be a nonblank string",
            )
            for value in [None, 1, {}, "", " "]
        ],
        (
            [
                {"term": "question", "means": "answers"},
                {"term": "Record", "means": "holds"},
                {"term": "QUESTION", "means": "again"},
            ],
            "universe terms: duplicate term 'QUESTION'",
        ),
    ],
)
def test_rejects_invalid_terms(protocol, universe, capsys, terms, reason):
    universe["universe"]["terms"] = terms
    assert not check(protocol, universe, "fixture")
    output = capsys.readouterr().out
    assert reason in output
    assert len(failures(output)) == 1, output


def test_terms_are_unsanctioned_in_a_0_7_document(protocol, universe, capsys):
    universe["universe"]["conforms_to"] = "kbp/0.7"
    universe["empty_composition"] = universe.pop("no_artifact")
    universe["universe"]["terms"] = [{"term": "question", "means": "answers"}]
    assert not check(protocol, universe, "fixture")
    output = capsys.readouterr().out
    assert "universe header: unsanctioned ['terms']" in output
    assert len(failures(output)) == 1, output


def test_a_0_7_document_without_terms_still_conforms(protocol, universe):
    universe["universe"]["conforms_to"] = "kbp/0.7"
    universe["empty_composition"] = universe.pop("no_artifact")
    assert check(protocol, universe, "fixture")


def test_accepted_versions_name_the_current_version_first(protocol):
    assert checker.accepted_versions(protocol) == ["kbp/0.8", "kbp/0.7"]


def run(*paths):
    return subprocess.run(
        [sys.executable, "-m", "kbp_conform.cli", "--validate", str(PROTOCOL)]
        + [str(path) for path in paths],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    )


@pytest.mark.parametrize("declared", ["kbp/0.7", "kbp/0.8"])
def test_the_cli_checks_each_accepted_version_as_itself(tmp_path, declared):
    document = yaml.safe_load(MINIMAL.read_text())
    document["universe"]["conforms_to"] = declared
    if declared == "kbp/0.8":
        document["no_artifact"] = document.pop("empty_composition")
    path = tmp_path / "universe.kbp.yaml"
    path.write_text(yaml.safe_dump(document))
    result = run(path)
    assert result.returncode == 0, result.stdout
    assert f"against {declared} ===" in result.stdout


@pytest.mark.parametrize("declared", ["kbp/0.6", "kbp/0.9", "other/0.8"])
def test_the_cli_refuses_versions_the_protocol_does_not_accept(tmp_path, declared):
    document = yaml.safe_load(MINIMAL.read_text())
    document["universe"]["conforms_to"] = declared
    path = tmp_path / "universe.kbp.yaml"
    path.write_text(yaml.safe_dump(document))
    result = run(path)
    assert result.returncode != 0
    assert f"conforms_to '{declared}' does not match 'kbp/0.8'" in result.stdout


def test_header_since_must_name_a_declared_header_key(protocol):
    broken = copy.deepcopy(protocol)
    broken["declarations"]["universe"]["header_since"]["not-a-header-key"] = 0.8
    assert any(
        "header_since names ['not-a-header-key']" in item
        for item in checker.self_check(broken)
    )


@pytest.mark.parametrize("invalid", [7, None, "0.7"])
def test_accepts_must_be_a_list(protocol, invalid):
    protocol["protocol"]["accepts"] = invalid
    assert any(
        "protocol.accepts: not a list" in item for item in checker.self_check(protocol)
    )
