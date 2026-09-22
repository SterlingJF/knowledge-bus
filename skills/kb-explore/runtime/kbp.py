"""Run the bundled checker without writing into the plugin or changing scope."""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


def command(arguments, runtime=None, environ=None):
    """Build an isolated checker invocation from verified bundled dependencies."""
    runtime = (runtime or Path(__file__).resolve().parent).resolve()
    env = dict(os.environ if environ is None else environ)
    config = json.loads((runtime / "requirements.json").read_text())
    requirement = config.get("requires_python", "")
    match = re.fullmatch(r">=(\d+)\.(\d+)(?:\.(\d+))?", requirement)
    if not match:
        raise ValueError("Bundled Python requirement is missing or unsupported.")
    minimum = tuple(int(part or 0) for part in match.groups())
    if sys.version_info[:3] < minimum:
        raise ValueError(
            f"Knowledge Bus requires Python {requirement}; "
            f"this interpreter is {'.'.join(map(str, sys.version_info[:3]))}."
        )
    uv = shutil.which("uv", path=env.get("PATH"))
    if not uv:
        raise ValueError("Knowledge Bus requires uv. See https://docs.astral.sh/uv/.")
    wheel = runtime / config["wheel"]
    if wheel.parent != runtime or not wheel.is_file():
        raise ValueError("Bundled checker wheel is missing or outside the runtime.")
    if hashlib.sha256(wheel.read_bytes()).hexdigest() != config["sha256"]:
        raise ValueError("Bundled checker wheel does not match its recorded checksum.")
    default = (
        Path.home() / "Library/Caches"
        if sys.platform == "darwin"
        else Path(env.get("LOCALAPPDATA", str(Path.home() / "AppData/Local")))
        if os.name == "nt"
        else Path(env.get("XDG_CACHE_HOME", str(Path.home() / ".cache")))
    )
    cache = (
        Path(env.get("KNOWLEDGE_BUS_CACHE_DIR", str(default / "knowledge-bus")))
        .expanduser()
        .resolve()
    )
    if cache == runtime.parent or runtime.parent in cache.parents:
        raise ValueError("The runtime cache must be outside the installed plugin.")
    env["UV_CACHE_DIR"] = str(cache)
    env["UV_PYTHON_DOWNLOADS"] = "never"
    env["UV_OFFLINE"] = "1"
    env["UV_NO_INDEX"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    for key in (
        "UV_PROJECT_ENVIRONMENT",
        "UV_PROJECT",
        "UV_WORKING_DIRECTORY",
        "UV_CONFIG_FILE",
        "UV_NO_SYNC",
        "UV_FROZEN",
        "VIRTUAL_ENV",
        "PYTHONPATH",
        "PYTHONHOME",
        "KNOWLEDGE_BUS_EXPLORER_BUNDLE",
        "KNOWLEDGE_BUS_EXPLORER_BUNDLE_MANIFEST",
    ):
        env.pop(key, None)
    viewer = runtime / "explorer-viewer.js"
    viewer_manifest = runtime / "explorer-viewer.json"
    if viewer.is_file() or viewer_manifest.is_file():
        if not viewer.is_file() or not viewer_manifest.is_file():
            raise ValueError("Bundled Explorer viewer is incomplete.")
        declared = json.loads(viewer_manifest.read_text())
        actual = "sha256:" + hashlib.sha256(viewer.read_bytes()).hexdigest()
        if (
            declared.get("digest") != actual
            or declared.get("bytes") != viewer.stat().st_size
        ):
            raise ValueError("Bundled Explorer viewer does not match its manifest.")
        env["KNOWLEDGE_BUS_EXPLORER_BUNDLE"] = str(viewer)
        env["KNOWLEDGE_BUS_EXPLORER_BUNDLE_MANIFEST"] = str(viewer_manifest)
    args = [
        uv,
        "run",
        "--offline",
        "--no-index",
        "--no-project",
        "--no-config",
        "--isolated",
        "--python",
        sys.executable,
        "--with",
        str(wheel),
    ]
    for requirement in config["dependencies"]:
        args.extend(["--with", requirement])
    return args + ["python", "-I", "-m", "kbp_conform.cli", *arguments], env


def main():
    try:
        args, env = command(sys.argv[1:])
        return subprocess.run(args, env=env, check=False).returncode
    except (ValueError, OSError, KeyError) as error:
        print(f"Knowledge Bus: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
