"""Guidance keyed to a factor is advice on presenting a document.

From kbp/0.9 a consumer may apply one universe spec's factor guidance to the
documents of another universe spec in the same folder. A factor still selects
nothing: guidance keys and `when` predicates resolve within the guided universe
spec only, and no factor changes a document type's sections.
"""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "protocol/knowledge-bus-protocol.yaml"
HALL_READERS = Path(__file__).resolve().parent / "hall-readers"
VILLAGE_HALL = ROOT / "evals/fixtures/village-hall/.knowledge-bus"


@pytest.fixture
def protocol():
    return yaml.safe_load(PROTOCOL.read_text())


@pytest.fixture
def scope(tmp_path):
    folder = tmp_path / ".knowledge-bus"
    shutil.copytree(VILLAGE_HALL, folder)
    for path in HALL_READERS.glob("*.kbp.yaml"):
        shutil.copy(path, folder / path.name)
    return folder


def validate(*paths):
    return subprocess.run(
        [sys.executable, "-m", "kbp_conform.cli", "--validate", str(PROTOCOL)]
        + [str(path) for path in paths],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    )


def test_the_protocol_calls_factor_guidance_presentation_advice(protocol):
    factor = protocol["concepts"]["factor"]
    assert factor["powers"] == []
    rules = " ".join(factor["rules"])
    assert "advice on presenting a document" in rules
    assert "another universe" in rules
    assert "still selects nothing" in rules
    guidance = protocol["concepts"]["guidance"]["definition"]
    assert "for a factor on presenting a document" in guidance


def test_a_factor_only_universe_spec_beside_others_conforms(scope):
    result = validate(scope)
    assert result.returncode == 0, result.stdout
    assert "hall-readers.type-guidance.kbp.yaml: CONFORMS" in result.stdout


def edit_guidance(scope, change):
    path = scope / "hall-readers.type-guidance.kbp.yaml"
    document = yaml.safe_load(path.read_text())
    change(document)
    path.write_text(yaml.safe_dump(document, sort_keys=False))


def test_factor_guidance_keys_only_its_own_universe_spec(scope):
    edit_guidance(
        scope,
        lambda document: document.setdefault("elements", {}).update(
            {"key-return": [{"kind": "heuristic", "source": "asserted", "claim": "x"}]}
        ),
    )
    result = validate(scope)
    assert result.returncode == 1
    assert "elements.key-return: resolves to no declared id in 'hall-readers'" in (
        result.stdout
    )


def test_factor_guidance_conditions_only_on_its_own_universe_spec(scope):
    edit_guidance(
        scope,
        lambda document: document["factors"]["hirer-experience"][1].update(
            {"when": {"hirer-kind": ["single-event"]}}
        ),
    )
    result = validate(scope)
    assert result.returncode == 1
    assert "unknown frame or factor 'hirer-kind'" in result.stdout
