"""Protocol preconditions and deterministic code-minting contracts."""

import copy
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from kbp_conform import checker, cli

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def protocol():
    return yaml.safe_load((ROOT / "protocol/knowledge-bus-protocol.yaml").read_text())


@pytest.mark.parametrize("path", checker.NEEDS, ids=lambda path: ".".join(path))
def test_each_registered_prerequisite_is_reported(protocol, path):
    node = protocol
    for key in path[:-1]:
        node = node[key]
    del node[path[-1]]
    failures = checker.self_check(protocol)
    assert any(f"protocol is missing `{'.'.join(path)}`" in item for item in failures)


@pytest.mark.parametrize("field", ["required", "one_of", "header_required"])
@pytest.mark.parametrize("invalid", [7, None, "not-a-list"])
def test_malformed_requirement_lists_are_refused(protocol, field, invalid):
    shape = "frame" if field == "one_of" else "universe"
    protocol["declarations"][shape][field] = invalid
    failures = checker.self_check(protocol)
    assert any(f"{field}: not a list" in item for item in failures)


@pytest.mark.parametrize("field", ["required", "header_required"])
@pytest.mark.parametrize("invalid", [7, None, "not-a-list"])
@pytest.mark.parametrize("shape", ["universe", "guidance"])
def test_cli_reports_malformed_requirements_without_document_verdict(
    protocol, tmp_path, field, invalid, shape
):
    protocol["declarations"][shape][field] = invalid
    path = tmp_path / "protocol.yaml"
    path.write_text(yaml.safe_dump(protocol))
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "kbp_conform.cli",
            "--validate",
            str(path),
            str(ROOT / "protocol/conformance/pass/minimal.kbp.yaml"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 1, output
    assert f"{shape}.{field}: not a list" in output
    assert "UNSOUND" in output
    assert "Traceback" not in output
    assert "CONFORMS" not in output
    assert "NON-CONFORMING" not in output


def test_malformed_requirements_do_not_hide_independent_findings(protocol):
    protocol["declarations"]["universe"]["required"] = 7
    protocol["declarations"]["universe"]["header_required"] = None
    protocol["declarations"]["frame"]["one_of"] = "not-a-list"
    failures = checker.self_check(protocol)
    for expected in (
        "universe.required: not a list",
        "universe.header_required: not a list",
        "frame.one_of: not a list",
    ):
        assert any(expected in item for item in failures)


@pytest.mark.parametrize("field,shape", [("required", "element"), ("one_of", "frame")])
def test_requirement_names_must_belong_to_the_shape(protocol, field, shape):
    protocol["declarations"][shape][field].append("undeclared-test-key")
    failures = checker.self_check(protocol)
    assert any(field in item and "undeclared-test-key" in item for item in failures)


@pytest.mark.parametrize("direction", ["missing-shape", "missing-kind"])
def test_document_kinds_and_shapes_agree(protocol, direction):
    declarations = protocol["declarations"]
    if direction == "missing-shape":
        declarations["document_types"]["kinds"].append("extra")
        expected = "declare no `document` shape"
    else:
        declarations["extra"] = {"document": {}}
        expected = "not in document_types.kinds"
    assert any(expected in item for item in checker.self_check(protocol))


def test_header_requirements_need_a_declared_header_shape(protocol):
    del protocol["declarations"]["universe"]["document"]["universe"]
    assert any(
        "header_required: no `document.universe`" in item
        for item in checker.self_check(protocol)
    )


@pytest.mark.parametrize("function,variable", [("check", "u"), ("check_guidance", "g")])
def test_subscript_requires_declared_precondition_but_get_does_not(
    protocol, function, variable
):
    subscript = f"def {function}({variable}):\n    return {variable}['new-key']\n"
    optional = f"def {function}({variable}):\n    return {variable}.get('new-key')\n"
    assert any("new-key" in item for item in checker.self_check(protocol, subscript))
    assert checker.self_check(protocol, optional) == []


def test_unsound_protocol_stops_before_document_verdict(
    protocol, tmp_path, capsys, monkeypatch
):
    del protocol["protocol"]["id"]
    path = tmp_path / "protocol.yaml"
    path.write_text(yaml.safe_dump(protocol))

    def unexpected(*args):
        pytest.fail("Document checking ran against an unsound protocol")

    monkeypatch.setattr(cli, "check", unexpected)
    monkeypatch.setattr(cli, "check_guidance", unexpected)
    assert (
        cli.main(
            [
                "--validate",
                str(path),
                str(ROOT / "protocol/conformance/pass/minimal.kbp.yaml"),
            ]
        )
        == 1
    )
    output = capsys.readouterr().out
    assert "UNSOUND" in output
    assert "CONFORMS" not in output
    assert "NON-CONFORMING" not in output


def test_runtime_protocol_fields_are_guarded_without_using_needs(protocol):
    # These are behavioral access points, not another copy of NEEDS.
    for path in [
        ("declarations", "element", "cardinality"),
        ("declarations", "frame", "values"),
        ("relations", "edge"),
    ]:
        damaged = copy.deepcopy(protocol)
        node = damaged
        for key in path[:-1]:
            node = node[key]
        del node[path[-1]]
        assert checker.self_check(damaged), f"Missing runtime shape accepted: {path}"


@pytest.mark.parametrize(
    "kind,prefix",
    [("element", "e"), ("artifact", "a"), ("frame", "f"), ("factor", "k")],
)
def test_minted_codes_are_yaml_strings_for_each_character_position(
    kind, prefix, monkeypatch
):
    # Fixed contract alphabet prevents a changed implementation constant from blessing itself.
    alphabet = "0123456789abcdefghjkmnpqrstvwxyz"
    tails = sorted(
        {
            "0" * position + char + "0" * (3 - position)
            for position in range(4)
            for char in alphabet
        }
    )
    choices = iter("".join(tails))
    monkeypatch.setattr(checker.secrets, "choice", lambda allowed: next(choices))
    codes = checker.mint(kind, len(tails))
    assert codes == [prefix + tail for tail in tails]
    assert set(checker.ALPHABET) == set(alphabet)
    for code in codes:
        assert len(code) == 5
        assert yaml.safe_load(code) == code
        assert yaml.safe_load("code: " + code)["code"] == code


def test_mint_retries_existing_and_batch_collisions_without_writing(
    tmp_path, monkeypatch
):
    paths = []
    for number, section in enumerate(["elements", "artifacts", "frames", "factors"]):
        path = tmp_path / f"{number}.yaml"
        path.write_text(yaml.safe_dump({section: [{"code": f"e000{number}"}]}))
        paths.append(path)
    before = {path: path.read_bytes() for path in paths}
    choices = iter("0000000100020003000400040005")
    monkeypatch.setattr(checker.secrets, "choice", lambda allowed: next(choices))
    assert checker.mint("element", 2, paths) == ["e0004", "e0005"]
    assert {path: path.read_bytes() for path in paths} == before


def test_mint_zero_does_not_draw_randomness(monkeypatch):
    def unexpected(*args):
        pytest.fail("Randomness requested for an empty batch")

    monkeypatch.setattr(checker.secrets, "choice", unexpected)
    assert checker.mint("element", 0) == []
