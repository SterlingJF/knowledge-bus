"""Atomic installed static Explorer artifact contracts."""

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from kbp_conform import artifact, explorer

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "universes/product-development"
PROTOCOL = ROOT / "protocol/knowledge-bus-protocol.yaml"
BUNDLE = ROOT / "explorer/prebuilt/viewer.js"
BUNDLE_MANIFEST = ROOT / "explorer/prebuilt/viewer.json"


def model():
    return explorer.inspect_paths(
        PROTOCOL,
        [
            REFERENCE / "universe.kbp.yaml",
            REFERENCE / "type-guidance.kbp.yaml",
            REFERENCE / "marks.explorer.yaml",
        ],
        release_version="0.7.0",
    )


def sha(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def snapshot(path):
    return {
        p.relative_to(path).as_posix(): p.read_bytes()
        for p in path.rglob("*")
        if p.is_file()
    }


def generate(
    target, prepared=None, *, replace=False, bundle=BUNDLE, manifest=BUNDLE_MANIFEST
):
    return artifact.generate(
        prepared or model(),
        target,
        bundle_path=bundle,
        bundle_manifest_path=manifest,
        replace=replace,
    )


def test_static_artifact_is_complete_offline_and_receipted(tmp_path):
    """One atomic set binds HTML, model, viewer, inputs, and release identity."""
    target = tmp_path / "outside-checkout/product-development"
    receipt = generate(target)
    assert sorted(path.name for path in target.iterdir()) == [
        "index.html",
        "model.json",
        "receipt.json",
    ]
    held_model = json.loads((target / "model.json").read_text())
    held_receipt = json.loads((target / "receipt.json").read_text())
    html = (target / "index.html").read_text()
    assert receipt == held_receipt
    assert held_receipt["schema"] == "knowledge-bus/explorer-artifact/1"
    assert held_receipt["readOnly"] is True
    assert held_receipt["knowledgeBus"]["release"] == "0.7.0"
    assert held_receipt["knowledgeBus"]["build"] == {
        "distribution": "knowledge-bus",
        "version": "0.7.0",
    }
    assert held_receipt["protocol"]["id"] == "kbp"
    assert held_receipt["universe"]["id"] == "product-development"
    assert held_receipt["explorerModel"]["digest"] == held_model["modelDigest"]
    assert held_model["modelDigest"] in html
    assert "<script src=" not in html and "<link href=" not in html
    assert "fetch(" not in html and "WebSocket" not in html
    assert str(ROOT) not in html + json.dumps(held_receipt) + json.dumps(held_model)
    for name, declared in held_receipt["outputs"].items():
        data = (target / name).read_bytes()
        assert declared["bytes"] == len(data)
        assert declared["digest"] == sha(data)


def test_generation_refuses_overwrite_by_default_and_replaces_explicitly(tmp_path):
    """Existing portable evidence survives unless replacement is explicit."""
    target = tmp_path / "artifact"
    generate(target)
    before = snapshot(target)
    with pytest.raises(artifact.ArtifactError, match="already exists"):
        generate(target)
    assert snapshot(target) == before
    prepared = model()
    prepared["universe"]["label"] = "Changed label"
    prepared["modelDigest"] = explorer.model_digest(prepared)
    generate(target, prepared, replace=True)
    assert "Changed label" in (target / "index.html").read_text()


def test_stale_viewer_is_refused_before_touching_previous_output(tmp_path):
    """A bundle whose bytes disagree with its manifest is never reused."""
    target = tmp_path / "artifact"
    generate(target)
    before = snapshot(target)
    stale = tmp_path / "viewer.js"
    manifest = tmp_path / "viewer.json"
    shutil.copyfile(BUNDLE, stale)
    shutil.copyfile(BUNDLE_MANIFEST, manifest)
    stale.write_text(stale.read_text() + "\n// stale\n")
    with pytest.raises(artifact.ArtifactError, match="viewer bundle"):
        generate(target, replace=True, bundle=stale, manifest=manifest)
    assert snapshot(target) == before


def test_viewer_identity_changes_without_changing_model_identity(tmp_path):
    """Presentation bytes have their own identity, separate from the model."""
    prepared = model()
    first = generate(tmp_path / "first", prepared)
    changed_bundle = tmp_path / "viewer.js"
    changed_manifest = tmp_path / "viewer.json"
    data = BUNDLE.read_bytes() + b"\n// presentation-only fixture\n"
    changed_bundle.write_bytes(data)
    manifest = json.loads(BUNDLE_MANIFEST.read_text())
    manifest["digest"] = sha(data)
    manifest["bytes"] = len(data)
    changed_manifest.write_text(json.dumps(manifest))
    second = generate(
        tmp_path / "second",
        prepared,
        bundle=changed_bundle,
        manifest=changed_manifest,
    )
    assert first["explorerModel"]["digest"] == second["explorerModel"]["digest"]
    assert first["viewer"]["digest"] != second["viewer"]["digest"]


def test_unsupported_or_modified_model_is_refused_without_partial_output(tmp_path):
    """Generation consumes exactly one supported, digest-verified inspected model."""
    for mutation in ("schema", "digest"):
        prepared = model()
        if mutation == "schema":
            prepared["schema"] = "knowledge-bus/explorer-model/999"
        else:
            prepared["universe"]["label"] = "Changed without reinspection"
        target = tmp_path / mutation
        with pytest.raises(artifact.ArtifactError):
            generate(target, prepared)
        assert not target.exists()


def test_generating_one_universe_does_not_modify_another(tmp_path):
    """Universe-id output isolation supports several siblings in one scope."""
    root = tmp_path / ".knowledge-bus/explorer"
    first = root / "first"
    second = root / "second"
    generate(first)
    before = snapshot(first)
    generate(second)
    assert snapshot(first) == before
