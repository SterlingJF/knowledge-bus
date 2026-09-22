"""Deterministic, read-only Explorer inspection contracts."""

import json
from pathlib import Path

import pytest
import yaml

from kbp_conform import cli, explorer

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "protocol/knowledge-bus-protocol.yaml"
REFERENCE = ROOT / "universes/product-development"


def write_set(scope, universe_id="one", *, guidance=True, marks=True, prefix=""):
    scope.mkdir(parents=True, exist_ok=True)
    universe = yaml.safe_load((REFERENCE / "universe.kbp.yaml").read_text())
    universe["universe"]["id"] = universe_id
    universe["universe"]["label"] = universe_id.title()
    universe_path = scope / f"{prefix}universe.kbp.yaml"
    universe_path.write_text(yaml.safe_dump(universe, sort_keys=False))
    if guidance:
        document = yaml.safe_load((REFERENCE / "type-guidance.kbp.yaml").read_text())
        document["guidance"]["id"] = f"{universe_id}-guidance"
        document["guidance"]["guides"] = universe_id
        (scope / f"{prefix}type-guidance.kbp.yaml").write_text(
            yaml.safe_dump(document, sort_keys=False)
        )
    if marks:
        document = yaml.safe_load((REFERENCE / "marks.explorer.yaml").read_text())
        document["marks"]["id"] = f"{universe_id}-marks"
        document["marks"]["marks_for"] = universe_id
        (scope / f"{prefix}marks.explorer.yaml").write_text(
            yaml.safe_dump(document, sort_keys=False)
        )
    return universe_path


def inspect(scope, universe_id=None):
    return explorer.inspect_paths(
        PROTOCOL,
        explorer.scope_documents(scope),
        universe_id=universe_id,
        release_version="0.7.0",
    )


def snapshot(path):
    return {
        p.relative_to(path).as_posix(): p.read_bytes()
        for p in path.rglob("*")
        if p.is_file()
    }


def test_single_universe_inspection_is_deterministic_portable_and_read_only(tmp_path):
    """Inspection identifies every selected input without mutating its scope."""
    scope = tmp_path / ".knowledge-bus"
    write_set(scope)
    (scope / "answers.yaml").write_text("review_only: true\n")
    before = snapshot(tmp_path)
    first = inspect(scope)
    second = inspect(scope)
    assert snapshot(tmp_path) == before
    assert first == second
    assert first["schema"] == "knowledge-bus/explorer-model/1"
    assert first["universe"]["id"] == "one"
    assert first["sourceDigest"].startswith("sha256:")
    assert first["modelDigest"].startswith("sha256:")
    assert first["input"]["digest"].startswith("sha256:")
    assert [item["role"] for item in first["input"]["documents"]] == [
        "protocol",
        "universe",
        "guidance",
        "marks",
    ]
    assert first["checks"]["conformance"] == "passed"
    assert first["checks"]["explorerRenderability"] == "passed"
    encoded = json.dumps(first)
    assert str(tmp_path) not in encoded
    assert "answers.yaml" not in encoded


def test_model_identity_ignores_release_but_tracks_semantic_input(tmp_path):
    """Packaging identity cannot stale an otherwise unchanged semantic model."""
    scope = tmp_path / ".knowledge-bus"
    universe_path = write_set(scope)
    paths = explorer.scope_documents(scope)
    first = explorer.inspect_paths(PROTOCOL, paths, release_version="0.7.0")
    repackaged = explorer.inspect_paths(PROTOCOL, paths, release_version="0.7.1")
    assert first["modelDigest"] == repackaged["modelDigest"]
    assert (
        first["layers"]["knowledgeBusRelease"]
        != repackaged["layers"]["knowledgeBusRelease"]
    )
    universe = yaml.safe_load(universe_path.read_text())
    universe["universe"]["label"] = "Semantically changed"
    universe_path.write_text(yaml.safe_dump(universe, sort_keys=False))
    assert inspect(scope)["modelDigest"] != first["modelDigest"]


def test_multiple_universes_list_candidates_and_require_selection(tmp_path):
    """A scope never picks one of several universes implicitly."""
    scope = tmp_path / ".knowledge-bus"
    write_set(scope, "beta", prefix="beta.")
    write_set(scope, "alpha", prefix="alpha.")
    with pytest.raises(explorer.InspectionError) as raised:
        inspect(scope)
    assert raised.value.category == "selection"
    assert raised.value.candidates == ["alpha", "beta"]
    assert inspect(scope, "beta")["universe"]["id"] == "beta"


def test_duplicate_universe_id_is_refused_before_guidance_resolution(tmp_path):
    """Semantic identity collisions cannot silently shadow a universe."""
    scope = tmp_path / ".knowledge-bus"
    write_set(scope, "same", prefix="a.", guidance=False, marks=False)
    write_set(scope, "same", prefix="b.", guidance=False, marks=False)
    with pytest.raises(explorer.InspectionError, match="Duplicate universe id"):
        inspect(scope, "same")


@pytest.mark.parametrize("kind", ["guidance", "marks"])
def test_ambiguous_semantic_companions_are_refused(tmp_path, kind):
    """Matching companion documents are associated by headers, never merged."""
    scope = tmp_path / ".knowledge-bus"
    write_set(scope, marks=kind != "marks", guidance=kind != "guidance")
    source = (
        REFERENCE / "type-guidance.kbp.yaml"
        if kind == "guidance"
        else REFERENCE / "marks.explorer.yaml"
    )
    for index in range(2):
        document = yaml.safe_load(source.read_text())
        header = document[kind]
        header["id"] = f"copy-{index}"
        header["guides" if kind == "guidance" else "marks_for"] = "one"
        suffix = (
            "type-guidance.kbp.yaml" if kind == "guidance" else "marks.explorer.yaml"
        )
        (scope / f"copy-{index}.{suffix}").write_text(
            yaml.safe_dump(document, sort_keys=False)
        )
    with pytest.raises(explorer.InspectionError, match=f"multiple {kind}"):
        inspect(scope)


def test_invalid_or_unrenderable_inputs_return_no_model(tmp_path):
    """Conformance and renderability failures remain distinct diagnostics."""
    scope = tmp_path / ".knowledge-bus"
    universe_path = write_set(scope, guidance=False, marks=False)
    universe = yaml.safe_load(universe_path.read_text())
    del universe["universe"]["ordering_frame"]
    universe_path.write_text(yaml.safe_dump(universe, sort_keys=False))
    with pytest.raises(explorer.InspectionError) as structural:
        inspect(scope)
    assert structural.value.category == "conformance"
    universe["universe"]["ordering_frame"] = "phase"
    universe["relation_kinds"][0].pop("phrasing", None)
    universe_path.write_text(yaml.safe_dump(universe, sort_keys=False))
    with pytest.raises(explorer.InspectionError) as renderability:
        inspect(scope)
    assert renderability.value.category == "renderability"


def test_explicit_universe_file_selects_its_semantic_siblings(tmp_path):
    """A selected file identifies one universe even in a multi-universe scope."""
    scope = tmp_path / ".knowledge-bus"
    chosen = write_set(scope, "chosen", prefix="chosen.")
    write_set(scope, "other", prefix="other.")
    paths, selected = explorer.resolve_inspection_targets([str(chosen)])
    assert selected == "chosen"
    assert (
        explorer.inspect_paths(PROTOCOL, paths, universe_id=selected)["universe"]["id"]
        == "chosen"
    )


def test_nearest_empty_scope_does_not_fall_through_for_inspection(
    tmp_path, monkeypatch
):
    """Nearest-scope isolation is identical for checking and inspection."""
    write_set(tmp_path / ".knowledge-bus")
    nearer = tmp_path / "child/.knowledge-bus"
    nearer.mkdir(parents=True)
    monkeypatch.chdir(nearer.parent)
    paths, selected = explorer.resolve_inspection_targets([])
    assert paths == []
    assert selected is None


def test_checker_refuses_duplicate_universe_ids(tmp_path, capsys):
    """The ordinary checker shares the no-shadowing scope invariant."""
    scope = tmp_path / ".knowledge-bus"
    write_set(scope, "same", prefix="a.", guidance=False, marks=False)
    write_set(scope, "same", prefix="b.", guidance=False, marks=False)
    assert cli.main([str(scope)]) == 1
    assert "duplicate universe id 'same'" in capsys.readouterr().out.lower()


def test_inspect_cli_emits_model_only_on_success(tmp_path, capsys):
    """The installed machine interface is JSON and keeps failures model-free."""
    single = tmp_path / "single/.knowledge-bus"
    write_set(single)
    assert cli.main(["--inspect", str(single)]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["schema"] == explorer.SCHEMA
    multiple = tmp_path / "multiple/.knowledge-bus"
    write_set(multiple, "one", prefix="one.")
    write_set(multiple, "two", prefix="two.")
    assert cli.main(["--inspect", str(multiple)]) == 1
    error = json.loads(capsys.readouterr().err)
    assert error["category"] == "selection"
    assert error["candidates"] == ["one", "two"]
    assert "model" not in error


def test_explore_cli_requires_explicit_output_and_overwrite_intent(tmp_path, capsys):
    """Static generation has no implicit destination and no implicit replacement."""
    scope = tmp_path / ".knowledge-bus"
    write_set(scope)
    assert cli.main(["--explore", str(scope)]) == 1
    assert "--output is required" in json.loads(capsys.readouterr().err)["message"]
    target = tmp_path / "portable"
    args = ["--explore", "--output", str(target), str(scope)]
    assert cli.main(args) == 0
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["schema"] == "knowledge-bus/explorer-artifact/1"
    assert cli.main(args) == 1
    assert "already exists" in json.loads(capsys.readouterr().err)["message"]
    assert (
        cli.main(["--explore", "--replace", "--output", str(target), str(scope)]) == 0
    )
