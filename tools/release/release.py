"""Explicit release preparation, verification, and local tagging. Never pushes."""

import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
_plugin_spec = importlib.util.spec_from_file_location(
    "plugin_tools", ROOT / "tools/plugin/plugin.py"
)
plugins = importlib.util.module_from_spec(_plugin_spec)
_plugin_spec.loader.exec_module(plugins)
VERSION = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")


def run(*args, root=ROOT, capture=False):
    return subprocess.run(
        args,
        cwd=root,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
    ).stdout


def git(*args, root=ROOT):
    return run("git", *args, root=root, capture=True).strip()


def version_tuple(value):
    if not VERSION.fullmatch(value):
        raise ValueError(
            "Use a release version X.Y.Z without a v prefix or prerelease suffix."
        )
    return tuple(map(int, value.split(".")))


def metadata(root=ROOT):
    project = tomllib.loads((root / "checker/pyproject.toml").read_text())["project"]
    plugin = json.loads(
        (root / "plugins/claude/knowledge-bus/.claude-plugin/plugin.json").read_text()
    )
    protocol = yaml.safe_load(
        (root / "protocol/knowledge-bus-protocol.yaml").read_text()
    )["protocol"]
    version_tuple(project["version"])
    return (
        project["version"],
        plugin["version"],
        f"{protocol['id']}/{protocol['version']}",
    )


def require_clean(root=ROOT):
    if git("status", "--porcelain", root=root):
        raise ValueError(
            "Commit or set aside working-tree changes first; nothing was changed."
        )


def require_unused(version, root=ROOT):
    if git("tag", "--list", f"v{version}", root=root):
        raise ValueError(
            f"Tag v{version} already exists; release tags must not be reused."
        )


def release_notes(version, root=ROOT):
    text = (root / "CHANGELOG.md").read_text()
    matches = list(
        re.finditer(r"^## " + re.escape(version) + r"\s*$", text, re.MULTILINE)
    )
    if len(matches) != 1:
        raise ValueError(f"CHANGELOG.md must contain exactly one '## {version}' entry.")
    body = text[matches[0].end() :]
    body = re.split(r"^## ", body, maxsplit=1, flags=re.MULTILINE)[0].strip()
    if re.search(r"\b(TODO|TBD)\b", body, re.IGNORECASE) or not re.search(
        r"^- \S", body, re.MULTILINE
    ):
        raise ValueError(
            "Finish the release changelog: include changes and remove TODO/TBD placeholders."
        )
    return body


def check_metadata(root=ROOT):
    version, plugin, protocol = metadata(root)
    if plugin != version:
        raise ValueError(f"Package {version} and plugin {plugin} versions differ.")
    plugins.check_versions(root)
    notes = release_notes(version, root)
    if f"Bundled protocol: `{protocol}`." not in notes:
        raise ValueError(f"Release notes must state: Bundled protocol: `{protocol}`.")
    return version, notes


def prepare(version, root=ROOT):
    version_tuple(version)
    require_clean(root)
    current, _, protocol = metadata(root)
    if version_tuple(version) <= version_tuple(current):
        raise ValueError(f"Choose a release version greater than {current}.")
    require_unused(version, root)
    changelog = (root / "CHANGELOG.md").read_text()
    if re.search(r"^## " + re.escape(version) + r"\s*$", changelog, re.MULTILINE):
        raise ValueError(f"Release {version} already has a changelog entry.")
    paths = [
        root / p
        for p in (
            "checker/pyproject.toml",
            "plugins/claude/knowledge-bus/.claude-plugin/plugin.json",
            "uv.lock",
            "CHANGELOG.md",
        )
    ]
    adapter_paths = plugins.version_files(root)
    paths.extend([*adapter_paths, root / "pnpm-lock.yaml"])
    originals = {p: p.read_bytes() for p in paths}
    generated_before = {
        p: p.read_bytes()
        for p in (root / "skills").rglob("*")
        if p.is_file() and p.name != "SKILL.md"
    }
    try:
        project = paths[0].read_text()
        section = re.search(r"(?ms)^\[project\]\s*\n(.*?)(?=^\[|\Z)", project)
        body, count = re.subn(
            r'(?m)^version\s*=\s*"[^"]+"', f'version = "{version}"', section[1]
        )
        if count != 1:
            raise ValueError(
                "Expected one static project.version in checker/pyproject.toml."
            )
        paths[0].write_text(
            project[: section.start(1)] + body + project[section.end(1) :]
        )
        plugin = json.loads(paths[1].read_text())
        plugin["version"] = version
        paths[1].write_text(json.dumps(plugin, indent=2) + "\n")
        for path in adapter_paths:
            document = json.loads(path.read_text())
            document["version"] = version
            path.write_text(json.dumps(document, indent=2) + "\n")
        entry = f"## {version}\n\nBundled protocol: `{protocol}`.\n\n### Changes\n\n- TODO: Describe the user-facing changes.\n\n"
        first = re.search(r"^## ", changelog, re.MULTILINE)
        offset = first.start() if first else len(changelog)
        paths[3].write_text(changelog[:offset] + entry + changelog[offset:])
        run("uv", "lock", root=root)
        run("pnpm", "install", "--lockfile-only", "--ignore-scripts", root=root)
        run("uv", "run", "--locked", "python", "tools/plugin/skills.py", root=root)
    except Exception:
        for path in (root / "skills").rglob("*"):
            if (
                path.is_file()
                and path.name != "SKILL.md"
                and path not in generated_before
            ):
                path.unlink()
        for path, contents in generated_before.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(contents)
        for path, contents in originals.items():
            path.write_bytes(contents)
        raise
    print(
        f"Prepared {version}, unstaged. Finish CHANGELOG.md, then run just release-check."
    )


def build_check(version, root=ROOT, output=None):
    with tempfile.TemporaryDirectory(prefix="knowledge-bus-release-") as temporary:
        base = Path(temporary)
        dist = base / "dist"
        run(
            "uv",
            "build",
            "--package",
            "knowledge-bus",
            "--out-dir",
            str(dist),
            root=root,
        )
        (wheel,) = dist.glob("*.whl")
        (sdist,) = dist.glob("*.tar.gz")
        environment = base / "venv"
        run("uv", "venv", "--python", sys.executable, str(environment), root=base)
        python = environment / (
            "Scripts/python.exe" if os.name == "nt" else "bin/python"
        )
        run("uv", "pip", "install", "--python", str(python), str(wheel), root=base)
        displayed = run(
            str(python),
            "-I",
            "-m",
            "kbp_conform.cli",
            "--version",
            root=base,
            capture=True,
        )
        protocol = metadata(root)[2]
        if (
            displayed.strip()
            != f"Knowledge Bus {version}\nBundled protocol: {protocol}"
        ):
            raise ValueError(f"Built wheel reports unexpected versions: {displayed}")
        run(str(python), "-I", "-m", "kbp_conform.cli", "--self-check", root=base)
        target = base / "notes" / ".knowledge-bus"
        shutil.copytree(root / "universes/product-development", target)
        run(str(python), "-I", "-m", "kbp_conform.cli", root=target.parent)
        rebuilt = base / "rebuilt"
        run("uv", "build", str(sdist), "--wheel", "--out-dir", str(rebuilt), root=base)
        (rebuilt_wheel,) = rebuilt.glob("*.whl")
        run(
            "uv",
            "pip",
            "install",
            "--reinstall",
            "--python",
            str(python),
            str(rebuilt_wheel),
            root=base,
        )
        run(str(python), "-I", "-m", "kbp_conform.cli", "--self-check", root=base)
        if output:
            output = Path(output).resolve()
            output.mkdir(parents=True, exist_ok=True)
            for artifact in (wheel, sdist):
                destination = output / artifact.name
                if destination.exists():
                    raise ValueError(f"Refusing to overwrite {destination}")
                shutil.copyfile(artifact, destination)


def check(root=ROOT, output=None):
    version, _ = check_metadata(root)
    run("uv", "lock", "--check", root=root)
    run("pnpm", "install", "--frozen-lockfile", "--ignore-scripts", root=root)
    run(
        "uv",
        "run",
        "--locked",
        "python",
        "tools/plugin/skills.py",
        "--check",
        root=root,
    )
    run("uv", "run", "--locked", "pytest", "-q", root=root)
    run(
        "uv",
        "run",
        "--locked",
        "python",
        "tools/plugin/check_skills_install.py",
        root=root,
    )
    run("uv", "run", "--locked", "kbp", "--self-check", root=root)
    run(
        "uv",
        "run",
        "--locked",
        "kbp",
        "--validate",
        str(root / "protocol/knowledge-bus-protocol.yaml"),
        str(root / "universes"),
        root=root,
    )
    build_check(version, root, output)
    plugins.build(plugins.HOSTS, root=root, output=output, exercise=True)
    run(
        "uv",
        "run",
        "--locked",
        "python",
        "tools/plugin/check_native_install.py",
        root=root,
    )
    print(f"Release {version} checks passed.")
    return version


def tag(root=ROOT):
    require_clean(root)
    if git("branch", "--show-current", root=root) != "main":
        raise ValueError("Release tags must be created from main.")
    run("git", "fetch", "origin", "main", "--tags", root=root)
    head = git("rev-parse", "HEAD", root=root)
    if head != git("rev-parse", "refs/remotes/origin/main", root=root):
        raise ValueError("Local main must match origin/main before tagging.")
    version = metadata(root)[0]
    require_unused(version, root)
    check(root)
    require_clean(root)
    if head != git("rev-parse", "HEAD", root=root):
        raise ValueError("HEAD changed during release checks.")
    run(
        "git",
        "tag",
        "-a",
        f"v{version}",
        head,
        "-m",
        f"Knowledge Bus {version}",
        root=root,
    )
    print(
        f"Created local tag v{version}. Publish with: git push origin refs/tags/v{version}"
    )


def verify_tag(name, root=ROOT):
    version, notes = check_metadata(root)
    if name != f"v{version}":
        raise ValueError("Tag does not match the release version.")
    if git("cat-file", "-t", f"refs/tags/{name}", root=root) != "tag":
        raise ValueError("Release tags must be annotated.")
    commit = git("rev-parse", f"refs/tags/{name}^{{commit}}", root=root)
    if commit != git("rev-parse", "HEAD", root=root):
        raise ValueError("Checkout does not match the release tag.")
    run(
        "git",
        "merge-base",
        "--is-ancestor",
        commit,
        "refs/remotes/origin/main",
        root=root,
    )
    return notes


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("prepare").add_argument("version")
    checking = commands.add_parser("check")
    checking.add_argument("--output", type=Path)
    commands.add_parser("tag")
    verifying = commands.add_parser("verify-tag")
    verifying.add_argument("name")
    commands.add_parser("notes")
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            prepare(args.version)
        elif args.command == "check":
            check(output=args.output)
        elif args.command == "tag":
            tag()
        elif args.command == "verify-tag":
            verify_tag(args.name)
        else:
            print(check_metadata()[1])
    except (ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Release stopped: {error}\n")


if __name__ == "__main__":
    main()
