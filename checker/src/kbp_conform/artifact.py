"""Atomic generation of a self-contained, read-only Explorer artifact set."""

import hashlib
import html
import json
import os
import shutil
import tempfile
from pathlib import Path

from .explorer import SCHEMA, model_digest

RECEIPT_SCHEMA = "knowledge-bus/explorer-artifact/1"
PACKAGE_DIR = Path(__file__).resolve().parent
CHECKOUT_ROOT = PACKAGE_DIR.parent.parent.parent


def default_bundle_paths():
    """Use launcher-provided installed assets or the repository prebuilt asset."""
    supplied = os.environ.get("KNOWLEDGE_BUS_EXPLORER_BUNDLE")
    supplied_manifest = os.environ.get("KNOWLEDGE_BUS_EXPLORER_BUNDLE_MANIFEST")
    if supplied or supplied_manifest:
        if not supplied or not supplied_manifest:
            raise ArtifactError("Installed Explorer bundle configuration is incomplete")
        return Path(supplied), Path(supplied_manifest)
    return (
        CHECKOUT_ROOT / "explorer/prebuilt/viewer.js",
        CHECKOUT_ROOT / "explorer/prebuilt/viewer.json",
    )


class ArtifactError(ValueError):
    pass


def _file_identity(data, mime_type):
    return {
        "mimeType": mime_type,
        "bytes": len(data),
        "digest": "sha256:" + hashlib.sha256(data).hexdigest(),
    }


def _verified_model(model):
    if not isinstance(model, dict) or model.get("schema") != SCHEMA:
        raise ArtifactError(f"Only {SCHEMA} is supported")
    claimed = model.get("modelDigest")
    if not isinstance(claimed, str) or claimed != model_digest(model):
        raise ArtifactError(
            "Explorer model digest does not match its inspected content"
        )
    required = ("layers", "input", "checks", "limitations")
    if any(key not in model for key in required):
        raise ArtifactError("Explorer model lacks installed inspection metadata")


def _verified_bundle(bundle_path, manifest_path):
    try:
        data = Path(bundle_path).read_bytes()
        manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ArtifactError(
            f"Cannot load the installed viewer bundle: {error}"
        ) from error
    identity = _file_identity(data, "text/javascript")
    if (
        manifest.get("digest") != identity["digest"]
        or manifest.get("bytes") != identity["bytes"]
        or not manifest.get("id")
        or not manifest.get("version")
    ):
        raise ArtifactError("Installed viewer bundle does not match its manifest")
    text = data.decode("utf-8")
    if "</script" in text.lower():
        raise ArtifactError("Installed viewer bundle cannot be embedded safely")
    return text, {
        "id": manifest["id"],
        "version": str(manifest["version"]),
        "digest": manifest["digest"],
        "bytes": manifest["bytes"],
    }


def _embedded_json(model):
    encoded = json.dumps(
        model, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return (
        encoded.replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def _html(model, bundle):
    label = html.escape(str(model["universe"].get("label", model["universe"]["id"])))
    model_digest = html.escape(model["modelDigest"], quote=True)
    return (
        "<!doctype html>\n"
        '<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'<meta name="knowledge-bus-model-digest" content="{model_digest}">\n'
        f"<title>{label} · Knowledge Bus Explorer</title>\n"
        "<style>html,body{margin:0;height:100%;background:#171e22;color:#e5eceb;font:14px system-ui,sans-serif}"
        "@media(prefers-color-scheme:light){html,body{background:#f5f5f1;color:#263638}}"
        "#explorer{position:fixed;inset:0}noscript{display:block;padding:24px}</style>\n"
        "</head>\n<body>\n"
        "<noscript>This read-only universe map is self-contained and works offline once scripts are allowed.</noscript>\n"
        '<div id="explorer"></div>\n'
        f'<script type="application/json" id="explorer-model">{_embedded_json(model)}</script>\n'
        f"<script>{bundle}</script>\n"
        "</body>\n</html>\n"
    ).encode()


def _receipt(model, viewer, outputs):
    layers = model["layers"]
    return {
        "schema": RECEIPT_SCHEMA,
        "readOnly": True,
        "knowledgeBus": {
            "release": layers["knowledgeBusRelease"],
            "build": {
                "distribution": "knowledge-bus",
                "version": layers["knowledgeBusRelease"],
            },
        },
        "protocol": layers["protocol"],
        "universe": layers["universe"],
        "guidance": layers["guidance"],
        "marks": layers["marks"],
        "explorerModel": {
            "schema": model["schema"],
            "digest": model["modelDigest"],
        },
        "viewer": viewer,
        "input": model["input"],
        "outputs": outputs,
        "checks": model["checks"],
        "limitations": model["limitations"],
    }


def generate(
    model,
    output,
    *,
    bundle_path=None,
    bundle_manifest_path=None,
    replace=False,
):
    """Write one complete artifact set, preserving any previous set on failure."""
    _verified_model(model)
    if bundle_path is None and bundle_manifest_path is None:
        bundle_path, bundle_manifest_path = default_bundle_paths()
    elif bundle_path is None or bundle_manifest_path is None:
        raise ArtifactError("Viewer bundle and manifest must be supplied together")
    bundle, viewer = _verified_bundle(bundle_path, bundle_manifest_path)
    output = Path(output).resolve()
    if output.exists() and not replace:
        raise ArtifactError(f"Output already exists: {output.name}")
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}.stage-", dir=output.parent))
    backup = None
    try:
        model_bytes = (
            json.dumps(model, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
        html_bytes = _html(model, bundle)
        outputs = {
            "index.html": _file_identity(html_bytes, "text/html; charset=utf-8"),
            "model.json": _file_identity(
                model_bytes, "application/json; charset=utf-8"
            ),
        }
        receipt = _receipt(model, viewer, outputs)
        receipt_bytes = (
            json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
        (stage / "index.html").write_bytes(html_bytes)
        (stage / "model.json").write_bytes(model_bytes)
        (stage / "receipt.json").write_bytes(receipt_bytes)
        if {path.name for path in stage.iterdir()} != {
            "index.html",
            "model.json",
            "receipt.json",
        }:
            raise ArtifactError("Staged Explorer artifact is incomplete")
        if output.exists():
            backup = output.parent / f".{output.name}.previous-{os.getpid()}"
            if backup.exists():
                raise ArtifactError("Cannot reserve an atomic replacement path")
            os.replace(output, backup)
        try:
            os.replace(stage, output)
        except Exception:
            if backup is not None and backup.exists() and not output.exists():
                os.replace(backup, output)
            raise
        if backup is not None:
            shutil.rmtree(backup)
        return receipt
    finally:
        if stage.exists():
            shutil.rmtree(stage)
