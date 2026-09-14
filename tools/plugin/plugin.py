"""Assemble and verify isolated host packages. Never installs or publishes plugins."""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import zipfile
from email.parser import BytesParser
from pathlib import Path, PurePosixPath

import yaml

ROOT = Path(__file__).resolve().parents[2]
HOSTS = ("claude", "codex", "pi", "opencode")
SKILLS = (
    "kb-check",
    "kb-evolve",
    "kb-ingest",
    "kb-uncover-decision",
    "kb-uncover-question",
)
REFERENCES = {
    "docs/agent-runtime.md": "references/agent-runtime.md",
    "docs/knowledge-bus-directory.md": "references/knowledge-bus-directory.md",
    "protocol/knowledge-bus-protocol.yaml": "references/knowledge-bus-protocol.yaml",
    "universes/product-development/universe.kbp.yaml": "references/product-development/universe.kbp.yaml",
    "universes/product-development/type-guidance.kbp.yaml": "references/product-development/type-guidance.kbp.yaml",
}


def run(*args, cwd=ROOT, env=None):
    return subprocess.run(
        args, cwd=cwd, env=env, check=True, text=True, capture_output=True
    ).stdout


def json_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def adapter(host, root=ROOT):
    if host not in HOSTS:
        raise ValueError(f"Unknown host: {host}")
    return root / "plugins" / host / "knowledge-bus"


def version_files(root=ROOT):
    return [adapter(host, root) / "package.json" for host in HOSTS] + [
        adapter(host, root) / f".{host}-plugin/plugin.json"
        for host in ("claude", "codex")
    ]


def check_versions(root=ROOT):
    version = tomllib.loads((root / "checker/pyproject.toml").read_text())["project"][
        "version"
    ]
    for path in version_files(root):
        if json.loads(path.read_text())["version"] != version:
            raise ValueError(f"Release versions differ: {path}")
    return version


def dependencies(root=ROOT):
    """Resolve pinned runtime dependencies; reject unreviewed dependency changes."""
    project = tomllib.loads((root / "checker/pyproject.toml").read_text())["project"]
    if project["dependencies"] != ["PyYAML>=6.0"]:
        raise ValueError(
            "Review plugin runtime dependencies after changing checker dependencies."
        )
    lock = tomllib.loads((root / "uv.lock").read_text())
    (pyyaml,) = [package for package in lock["package"] if package["name"] == "pyyaml"]
    if pyyaml.get("dependencies"):
        raise ValueError("Review new transitive runtime dependencies.")
    return [f"PyYAML=={pyyaml['version']}"]


def wheel_python_requirement(wheel):
    with zipfile.ZipFile(wheel) as archive:
        (metadata,) = [
            name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
        ]
        requirement = BytesParser().parsebytes(archive.read(metadata))[
            "Requires-Python"
        ]
    if not requirement or not re.fullmatch(r">=\d+\.\d+(?:\.\d+)?", requirement):
        raise ValueError(
            "Runtime requires a single inclusive Python minimum in wheel metadata."
        )
    return requirement


def runtime_requirements(wheel, root=ROOT):
    requirement = wheel_python_requirement(wheel)
    project = tomllib.loads((root / "checker/pyproject.toml").read_text())["project"]
    if requirement != project["requires-python"]:
        raise ValueError(
            "Checker wheel Python requirement differs from source metadata."
        )
    return {
        "version": project["version"],
        "wheel": wheel.name,
        "requires_python": requirement,
        "sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
        "dependencies": dependencies(root),
    }


def copy(source, destination, root):
    if source.is_symlink() or not source.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Source escapes the repository or is a symlink: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)


def assemble(host, destination, wheel, root=ROOT):
    """Assemble a self-contained host package without lifecycle scripts."""
    version = check_versions(root)
    destination.mkdir(parents=True, exist_ok=False)
    if host in ("claude", "codex"):
        manifest = f".{host}-plugin/plugin.json"
        copy(adapter(host, root) / manifest, destination / manifest, root)
    if host == "opencode":
        copy(adapter(host, root) / "index.js", destination / "index.js", root)
    package = json.loads((adapter(host, root) / "package.json").read_text())
    package.pop("scripts", None)
    package["private"] = False
    package["publishConfig"] = {
        "access": "public",
        "registry": "https://registry.npmjs.org/",
    }
    package["repository"] = {
        "type": "git",
        "url": "git+https://github.com/SterlingJF/knowledge-bus.git",
        "directory": f"plugins/{host}/knowledge-bus",
    }
    package["homepage"] = "https://github.com/SterlingJF/knowledge-bus#readme"
    package["packageManager"] = json.loads((root / "package.json").read_text())[
        "packageManager"
    ]
    json_write(destination / "package.json", package)
    copy(root / "LICENSE", destination / "LICENSE", root)
    for source, target in REFERENCES.items():
        copy(root / source, destination / target, root)
    for name in SKILLS:
        source = root / "skills" / name / "SKILL.md"
        target = destination / "skills" / name / "SKILL.md"
        copy(source, target, root)
        text = target.read_text()
        for original, bundled in REFERENCES.items():
            text = text.replace("../../" + original, "../../" + bundled)
            text = text.replace("(" + bundled + ")", "(../../" + bundled + ")")
        target.write_text(text)
    copy(root / "plugins/shared/runtime/kbp.py", destination / "runtime/kbp.py", root)
    shutil.copyfile(wheel, destination / "runtime" / wheel.name)
    json_write(
        destination / "runtime/requirements.json", runtime_requirements(wheel, root)
    )
    return inspect(destination, host, version)


def inspect(plugin, host, version):
    config = json.loads((plugin / "runtime/requirements.json").read_text())
    expected = {
        "package.json",
        "LICENSE",
        "runtime/kbp.py",
        "runtime/requirements.json",
        "runtime/" + config["wheel"],
        *REFERENCES.values(),
        *(f"skills/{name}/SKILL.md" for name in SKILLS),
    }
    if host in ("claude", "codex"):
        expected.add(f".{host}-plugin/plugin.json")
    if host == "opencode":
        expected.add("index.js")
    paths = list(plugin.rglob("*"))
    if any(path.is_symlink() for path in paths):
        raise ValueError("Plugin contains a symlink.")
    actual = {path.relative_to(plugin).as_posix() for path in paths if path.is_file()}
    if actual != expected:
        raise ValueError(
            f"Artifact inventory mismatch: missing {expected - actual}; unexpected {actual - expected}"
        )
    package = json.loads((plugin / "package.json").read_text())
    versions = [package, config]
    if host in ("claude", "codex"):
        manifest = json.loads((plugin / f".{host}-plugin/plugin.json").read_text())
        if manifest["name"] != "knowledge-bus" or manifest["skills"] != "./skills/":
            raise ValueError("Unexpected host discovery manifest.")
        versions.append(manifest)
    if host == "pi" and package.get("pi") != {"skills": ["./skills"]}:
        raise ValueError("Unexpected Pi discovery manifest.")
    if host == "opencode" and (
        package.get("type") != "module"
        or package.get("exports", {}).get("./server") != "./index.js"
    ):
        raise ValueError("Unexpected OpenCode entry point.")
    if package.get("private") is not False or package.get("bin"):
        raise ValueError(
            "Built agent packages must be publishable and must not reserve CLI commands."
        )
    if not all(item["version"] == version for item in versions):
        raise ValueError("Artifact versions differ.")
    if (
        package.get("scripts")
        or package.get("dependencies")
        or package.get("devDependencies")
    ):
        raise ValueError(
            "Delivered packages must not need npm dependencies or lifecycle scripts."
        )
    wheel = plugin / "runtime" / config["wheel"]
    if hashlib.sha256(wheel.read_bytes()).hexdigest() != config["sha256"]:
        raise ValueError("Wheel checksum mismatch.")
    if config.get("requires_python") != wheel_python_requirement(wheel):
        raise ValueError(
            "Runtime Python requirement differs from bundled wheel metadata."
        )
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        if "kbp_conform/knowledge-bus-protocol.yaml" not in names:
            raise ValueError("Checker wheel lacks its protocol.")
        if any(
            not name.startswith(("kbp_conform/", f"knowledge_bus-{version}.dist-info/"))
            for name in names
        ):
            raise ValueError("Checker wheel contains unrelated files.")
    for path in plugin.rglob("*.md"):
        for link in re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text()):
            if re.match(r"[a-z]+://|#", link):
                continue
            target = (path.parent / link.split("#")[0]).resolve()
            if not target.is_relative_to(plugin.resolve()) or not target.exists():
                raise ValueError(f"Broken or escaping reference: {path}: {link}")
    context = []
    for name in SKILLS:
        text = (plugin / "skills" / name / "SKILL.md").read_text()
        _, header, body = text.split("---", 2)
        metadata = yaml.safe_load(header)
        if metadata["name"] != name or not metadata.get("description"):
            raise ValueError(f"Invalid skill metadata: {name}")
        if "CLAUDE_PLUGIN_" in text or "CODEX_" in text:
            raise ValueError(f"Host-specific instructions in shared skill: {name}")
        context.append(
            {
                "skill": name,
                "discovery_characters": len(name) + len(metadata["description"]),
                "body_characters": len(body),
                "linked_references": re.findall(r"\]\(([^)]+)\)", body),
            }
        )
    return {
        "host": host,
        "version": version,
        "files": sorted(actual),
        "package": package["name"],
        "file_hashes": {
            name: hashlib.sha256((plugin / name).read_bytes()).hexdigest()
            for name in sorted(actual)
        },
        "skills": context,
        "context_measurement": "Static characters, not model tokens or a live context trace.",
    }


def unpack(archive, destination):
    destination.mkdir(parents=True, exist_ok=False)
    with tarfile.open(archive) as tar:
        seen = set()
        for member in tar.getmembers():
            parts = PurePosixPath(member.name).parts
            if (
                not parts
                or parts[0] != "package"
                or ".." in parts
                or member.name in seen
            ):
                raise ValueError(f"Invalid or duplicate tar member: {member.name}")
            seen.add(member.name)
            if member.isdir():
                continue
            if not member.isfile():
                raise ValueError(f"Non-file tar member: {member.name}")
            target = destination.joinpath(*parts[1:])
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(tar.extractfile(member).read())


def runtime_check(plugin, root=ROOT):
    before = {
        p.relative_to(plugin).as_posix(): p.read_bytes()
        for p in plugin.rglob("*")
        if p.is_file()
    }
    paths = [plugin, *plugin.rglob("*")]
    modes = {p: p.stat().st_mode for p in paths}
    try:
        for p in paths:
            p.chmod(0o555 if p.is_dir() else 0o444)
        with tempfile.TemporaryDirectory(prefix="knowledge-bus-runtime-") as temporary:
            base = Path(temporary)
            env = {**os.environ, "KNOWLEDGE_BUS_CACHE_DIR": str(base / "cache")}
            launcher = str(plugin / "runtime/kbp.py")
            version = json.loads((plugin / "package.json").read_text())["version"]
            if f"Knowledge Bus {version}\n" not in run(
                sys.executable, launcher, "--version", cwd=base, env=env
            ):
                raise ValueError("Runtime reports wrong release version.")
            run(sys.executable, launcher, "--self-check", cwd=base, env=env)
            target = base / "notes/.knowledge-bus"
            shutil.copytree(root / "universes/product-development", target)
            source = base / "notes/source.md"
            source.write_text("User content is untouched.\n")
            snapshot = {
                p: p.read_bytes() for p in target.parent.rglob("*") if p.is_file()
            }
            nested = target.parent / "nested"
            nested.mkdir()
            run(sys.executable, launcher, cwd=nested, env=env)
            run(
                sys.executable,
                launcher,
                "--mint",
                "element",
                "2",
                str(target),
                cwd=base,
                env=env,
            )
            for fixture in sorted(
                (root / "protocol/conformance/pass").glob("*.kbp.yaml")
            ):
                run(
                    sys.executable,
                    launcher,
                    "--validate",
                    str(fixture),
                    cwd=base,
                    env=env,
                )
            for fixture in sorted(
                (root / "protocol/conformance/fail").glob("*.kbp.yaml")
            ):
                result = subprocess.run(
                    [sys.executable, launcher, "--validate", str(fixture)],
                    check=False,
                    cwd=base,
                    env=env,
                    capture_output=True,
                )
                if result.returncode == 0:
                    raise ValueError(
                        f"Runtime accepted invalid fixture: {fixture.name}"
                    )
            missing = subprocess.run(
                [sys.executable, launcher],
                cwd=base,
                env=env,
                capture_output=True,
                check=False,
            )
            if missing.returncode == 0 or (base / ".knowledge-bus").exists():
                raise ValueError(
                    "Runtime silently accepted or initialized missing definitions."
                )
            if {
                p: p.read_bytes() for p in target.parent.rglob("*") if p.is_file()
            } != snapshot:
                raise ValueError("Runtime changed user files.")
    finally:
        for p, mode in modes.items():
            p.chmod(mode)
    after = {
        p.relative_to(plugin).as_posix(): p.read_bytes()
        for p in plugin.rglob("*")
        if p.is_file()
    }
    if before != after:
        raise ValueError("Runtime wrote into the installed plugin.")


def build(hosts, root=ROOT, output=None, exercise=False):
    version = check_versions(root)
    with tempfile.TemporaryDirectory(prefix="knowledge-bus-plugin-") as temporary:
        base = Path(temporary)
        env = {**os.environ, "SOURCE_DATE_EPOCH": "315532800"}
        run(
            "uv",
            "build",
            "--package",
            "knowledge-bus",
            "--wheel",
            "--out-dir",
            str(base / "wheel"),
            cwd=root,
            env=env,
        )
        (wheel,) = (base / "wheel").glob("*.whl")
        for host in hosts:
            plugin = base / host / "knowledge-bus"
            assemble(host, plugin, wheel, root)
            archive = base / f"knowledge-bus-plugin-{host}-{version}.tgz"
            run("pnpm", "pack", "--out", str(archive), cwd=plugin, env=env)
            installed = base / f"unpacked-{host}" / "knowledge-bus"
            unpack(archive, installed)
            report = inspect(installed, host, version)
            if exercise:
                runtime_check(installed, root)
            report["runtime_checked"] = exercise
            report["sha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
            report["bytes"] = archive.stat().st_size
            if output:
                output = Path(output).resolve()
                output.mkdir(parents=True, exist_ok=True)
                target = output / archive.name
                if target.exists():
                    raise ValueError(
                        f"Refusing to overwrite {target}; choose a fresh --output directory."
                    )
                shutil.copyfile(archive, target)
                json_write(output / (archive.stem + ".report.json"), report)
            print(
                json.dumps(
                    {
                        key: report[key]
                        for key in (
                            "host",
                            "version",
                            "bytes",
                            "runtime_checked",
                            "sha256",
                        )
                    }
                )
            )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "check"))
    parser.add_argument("host", choices=(*HOSTS, "all"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output
    if args.command == "build" and output is None:
        output = Path(tempfile.mkdtemp(prefix="build-", dir=make_dist()))
    try:
        build(
            HOSTS if args.host == "all" else (args.host,),
            output=output,
            exercise=args.command == "check",
        )
        if output:
            print(f"Artifacts: {output}")
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        detail = (
            error.stderr
            if isinstance(error, subprocess.CalledProcessError)
            else str(error)
        )
        parser.exit(1, f"Plugin packaging stopped: {detail}\n")


def make_dist():
    path = ROOT / "dist/plugins"
    path.mkdir(parents=True, exist_ok=True)
    return path


if __name__ == "__main__":
    main()
