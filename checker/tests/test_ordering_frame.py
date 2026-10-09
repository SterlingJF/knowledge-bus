"""The ordering frame, by declared version.

From kbp/0.9 a universe spec with no element declares no ordering frame. An
ordering frame in such a universe spec attaches to nothing and is refused.
kbp/0.8 and kbp/0.7 require an ordering frame in every universe spec, so their
factor-only universe specs keep a placeholder ordering frame and still conform.
"""

import copy
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from kbp_conform.checker import check, self_check

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "protocol/knowledge-bus-protocol.yaml"
CORPUS = ROOT / "protocol/conformance"
FACTORS_ONLY = CORPUS / "pass/factors-only-without-ordering-frame.kbp.yaml"
MINIMAL = CORPUS / "pass/minimal.kbp.yaml"
PLACEHOLDER_SPECS = [
    CORPUS / "pass/factors-only.kbp.yaml",
    ROOT / "evals/fixtures/info-pages/.knowledge-bus/universe.kbp.yaml",
    ROOT / "tools/evals/fixtures/shapes/notice-readers.universe.kbp.yaml",
]
STAGE = {
    "id": "stage",
    "code": "fnp7n",
    "role": "ordering",
    "set_by": "universe",
    "attaches_to": "element",
    "values": [{"id": "only", "question": "Where in the sequence does this sit?"}],
}


@pytest.fixture
def protocol():
    return yaml.safe_load(PROTOCOL.read_text())


@pytest.fixture
def factor_only():
    document = yaml.safe_load(FACTORS_ONLY.read_text())
    assert document["universe"]["conforms_to"] == "kbp/0.9"
    assert "ordering_frame" not in document["universe"]
    return document


@pytest.fixture
def with_elements():
    document = yaml.safe_load(MINIMAL.read_text())
    document["universe"]["conforms_to"] = "kbp/0.9"
    document["no_artifact"] = document.pop("empty_composition")
    return document


def failures(capsys):
    out = capsys.readouterr().out
    return [line.strip() for line in out.splitlines() if line.startswith("  FAIL")]


def test_a_universe_spec_with_no_element_declares_no_ordering_frame(
    protocol, factor_only
):
    assert check(protocol, factor_only, "fixture")


def test_a_universe_spec_with_elements_declares_an_ordering_frame(
    protocol, with_elements, capsys
):
    assert check(protocol, copy.deepcopy(with_elements), "fixture")
    capsys.readouterr()
    del with_elements["universe"]["ordering_frame"]
    assert not check(protocol, with_elements, "fixture")
    assert failures(capsys) == [
        (
            "FAIL  header: missing required 'ordering_frame' "
            "(a universe spec with elements declares an ordering frame)"
        )
    ]


def test_an_ordering_frame_with_no_element_attaches_to_nothing(
    protocol, factor_only, capsys
):
    factor_only["universe"]["ordering_frame"] = "stage"
    factor_only["frames"] = [STAGE]
    assert not check(protocol, factor_only, "fixture")
    assert failures(capsys) == [
        (
            "FAIL  ordering frame 'stage' attaches to nothing: "
            "the universe spec declares no element"
        )
    ]


def test_an_ordering_role_without_the_header_key_attaches_to_nothing(
    protocol, factor_only, capsys
):
    factor_only["frames"] = [STAGE]
    assert not check(protocol, factor_only, "fixture")
    assert failures(capsys) == [
        (
            "FAIL  ordering frame 'stage' attaches to nothing: "
            "the universe spec declares no element"
        )
    ]


def test_a_header_ordering_frame_naming_no_frame_attaches_to_nothing(
    protocol, factor_only, capsys
):
    factor_only["universe"]["ordering_frame"] = "stage"
    assert not check(protocol, factor_only, "fixture")
    assert (
        "FAIL  ordering frame 'stage' attaches to nothing: "
        "the universe spec declares no element"
    ) in failures(capsys)


@pytest.mark.parametrize("version", ["0.7", "0.8"])
def test_earlier_versions_require_an_ordering_frame_in_every_universe_spec(
    protocol, factor_only, version, capsys
):
    factor_only["universe"]["conforms_to"] = f"kbp/{version}"
    if version == "0.7":
        factor_only["empty_composition"] = factor_only.pop("no_artifact")
    assert not check(protocol, factor_only, "fixture")
    assert failures(capsys) == [
        (
            f"FAIL  header: missing required 'ordering_frame' (kbp/{version} requires "
            "an ordering frame in every universe spec; from kbp/0.9, a universe spec "
            "with no element declares no ordering frame)"
        )
    ]


@pytest.mark.parametrize("version", ["0.7", "0.8"])
def test_earlier_versions_accept_a_placeholder_ordering_frame(
    protocol, factor_only, version
):
    factor_only["universe"]["conforms_to"] = f"kbp/{version}"
    factor_only["universe"]["ordering_frame"] = "stage"
    factor_only["frames"] = [STAGE]
    if version == "0.7":
        factor_only["empty_composition"] = factor_only.pop("no_artifact")
    assert check(protocol, factor_only, "fixture")


@pytest.mark.parametrize("path", PLACEHOLDER_SPECS, ids=lambda path: path.parent.name)
def test_factor_only_universe_specs_with_a_placeholder_still_conform(path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "kbp_conform.cli",
            "--validate",
            str(PROTOCOL),
            str(path),
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    )
    assert result.returncode == 0, result.stdout


def test_the_protocol_states_the_ordering_rule_by_version(protocol):
    universe = protocol["declarations"]["universe"]
    assert "ordering_frame" not in universe["header_required"]
    assert universe["header_required_before"] == {"ordering_frame": 0.9}
    assert any(
        "declares no element" in rule
        for rule in protocol["conformance"]["universe_valid_if"]
    )


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (
            lambda shape: shape["header_required_before"].update({"not-a-key": 0.9}),
            "header_required_before names ['not-a-key']",
        ),
        (
            lambda shape: shape["header_required_before"].update(
                {"ordering_frame": 9.9}
            ),
            "header_required_before.ordering_frame: 9.9 is later than protocol.version",
        ),
        (
            lambda shape: shape["header_required"].append("ordering_frame"),
            "header_required_before names ['ordering_frame'], which header_required also lists",
        ),
        (
            lambda shape: shape.update({"header_required_before": ["ordering_frame"]}),
            "header_required_before: not a mapping",
        ),
    ],
)
def test_header_required_before_is_checked_for_soundness(protocol, change, message):
    broken = copy.deepcopy(protocol)
    change(broken["declarations"]["universe"])
    found = self_check(broken)
    assert any(message in line for line in found), found


def test_the_explorer_refuses_a_universe_spec_without_an_ordering_frame(tmp_path):
    from kbp_conform import explorer

    scope = tmp_path / ".knowledge-bus"
    scope.mkdir()
    shutil.copy(FACTORS_ONLY, scope / FACTORS_ONLY.name)
    with pytest.raises(explorer.InspectionError) as refused:
        explorer.inspect_paths(str(PROTOCOL), sorted(scope.glob("*.kbp.yaml")))
    assert refused.value.category == "renderability"
    assert "declares no ordering frame" in str(refused.value)
