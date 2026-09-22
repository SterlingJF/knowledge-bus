"""Generate and verify the supporting files shipped beside each canonical skill."""

import argparse
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

import plugin

ROOT = plugin.ROOT


def payloads(root=ROOT):
    with tempfile.TemporaryDirectory(prefix="knowledge-bus-skills-") as folder:
        base = Path(folder)
        plugin.run(
            "uv",
            "build",
            "--package",
            "knowledge-bus",
            "--wheel",
            "--out-dir",
            str(base),
            cwd=root,
            env={**os.environ, "SOURCE_DATE_EPOCH": "315532800"},
        )
        (wheel,) = base.glob("*.whl")
        version = plugin.check_versions(root)
        for name in plugin.SKILLS:
            files = {
                "references/knowledge-bus-directory.md": (
                    root / "docs/knowledge-bus-directory.md"
                ).read_bytes(),
                "LICENSE": (root / "LICENSE").read_bytes(),
            }
            if name != "kb-uncover-decision":
                files.update(
                    {
                        "references/agent-runtime.md": (
                            root / "docs/agent-runtime.md"
                        ).read_bytes(),
                        "references/knowledge-bus-protocol.yaml": (
                            root / "protocol/knowledge-bus-protocol.yaml"
                        ).read_bytes(),
                        "runtime/kbp.py": (
                            root / "plugins/shared/runtime/kbp.py"
                        ).read_bytes(),
                        "runtime/" + wheel.name: wheel.read_bytes(),
                        "runtime/requirements.json": (
                            json.dumps(
                                plugin.runtime_requirements(wheel, root), indent=2
                            )
                            + "\n"
                        ).encode(),
                    }
                )
            if name == "kb-explore":
                for source, target in plugin.EXPLORER_ASSETS.items():
                    files[target] = (root / source).read_bytes()
            if name == "kb-ingest":
                for path in sorted(
                    (root / "universes/product-development").glob("*.kbp.yaml")
                ):
                    files["references/product-development/" + path.name] = (
                        path.read_bytes()
                    )
            manifest = {
                "generated_by": "just skills-build",
                "version": version,
                "files": {
                    path: hashlib.sha256(data).hexdigest()
                    for path, data in sorted(files.items())
                },
            }
            files["generated.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
            yield name, files


def snapshot(root=ROOT):
    return {
        p: p.read_bytes()
        for name in plugin.SKILLS
        for p in (root / "skills" / name).rglob("*")
        if p.is_file() and p.name != "SKILL.md"
    }


def restore(before, root=ROOT):
    for path in set(snapshot(root)) - set(before):
        path.unlink()
    for path, data in before.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def generate(root=ROOT, check=False):
    """Generate or verify skill resources, rejecting unknown files and escaping links."""
    expected = dict(payloads(root))
    for name, files in expected.items():
        directory = root / "skills" / name
        for path in directory.rglob("*"):
            if path.is_symlink():
                raise ValueError(f"Skill symlink is not supported: {path}")
        actual = {
            p.relative_to(directory).as_posix(): p.read_bytes()
            for p in directory.rglob("*")
            if p.is_file() and p.name != "SKILL.md"
        }
        if check:
            if actual != files:
                raise ValueError(
                    f"Stale generated skill files: {name}. Run just skills-build and commit the results."
                )
        else:
            old_manifest = directory / "generated.json"
            owned = (
                set(json.loads(old_manifest.read_text())["files"]) | {"generated.json"}
                if old_manifest.exists()
                else set()
            )
            unknown = set(actual) - set(files) - owned
            if unknown:
                raise ValueError(f"Unexpected files in {name}: {sorted(unknown)}")
            for path in set(actual) - set(files):
                (directory / path).unlink()
            for path, data in files.items():
                target = directory / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
        for path in directory.rglob("*.md"):
            for link in re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text()):
                if re.match(r"[a-z]+://|#", link):
                    continue
                target = (path.parent / link.split("#")[0]).resolve()
                if (
                    not target.is_relative_to(directory.resolve())
                    or not target.exists()
                ):
                    raise ValueError(
                        f"Skill reference escapes or is missing: {path}: {link}"
                    )
    print(
        "Self-contained skills "
        + (
            "verified."
            if check
            else "generated; leave SKILL.md authored and commit generated files."
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    generate(check=args.check)
