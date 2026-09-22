"""Exercise the real pinned skills CLI in disposable project folders, with telemetry disabled."""

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import plugin

REPOSITORY = "SterlingJF/knowledge-bus"
SKILLS_CLI = "1.5.26"


def skills_command(tag=None, agent="codex"):
    source = f"https://github.com/{REPOSITORY}/tree/{tag}/skills" if tag else REPOSITORY
    return [
        "npx",
        "--yes",
        f"skills@{SKILLS_CLI}",
        "add",
        source,
        "--skill",
        "kb-check",
        "--agent",
        agent,
    ]


def file_hashes(directory):
    return {
        p.relative_to(directory).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in directory.rglob("*")
        if p.is_file()
    }


def exercise_runtime(installed, project, env, *, explore=False):
    """Run a read-only installed skill from an empty cache with network denied."""
    paths = [installed, *installed.rglob("*")]
    modes = {path: path.stat().st_mode for path in paths}
    runtime_env = {
        **env,
        "KNOWLEDGE_BUS_CACHE_DIR": str(project / "cold-runtime-cache"),
        "UV_OFFLINE": "1",
        "UV_NO_INDEX": "1",
        "HTTP_PROXY": "http://127.0.0.1:9",
        "HTTPS_PROXY": "http://127.0.0.1:9",
        "ALL_PROXY": "http://127.0.0.1:9",
        "NO_PROXY": "",
    }
    try:
        for path in paths:
            path.chmod(0o555 if path.is_dir() else 0o444)
        launcher = installed / "runtime/kbp.py"
        subprocess.run(
            [sys.executable, str(launcher), "--self-check"],
            cwd=project,
            env=runtime_env,
            check=True,
            capture_output=True,
            timeout=60,
        )
        if explore:
            scope = project / "notes/.knowledge-bus"
            shutil.copytree(plugin.ROOT / "universes/product-development", scope)
            inspected = subprocess.run(
                [sys.executable, str(launcher), "--inspect", str(scope)],
                cwd=project,
                env=runtime_env,
                check=True,
                capture_output=True,
                text=True,
                timeout=60,
            )
            if "knowledge-bus/explorer-model/1" not in inspected.stdout:
                raise ValueError("Standalone inspection did not return a model.")
            output = project / "portable"
            subprocess.run(
                [
                    sys.executable,
                    str(launcher),
                    "--explore",
                    "--output",
                    str(output),
                    str(scope),
                ],
                cwd=project,
                env=runtime_env,
                check=True,
                capture_output=True,
                timeout=60,
            )
            if {path.name for path in output.iterdir()} != {
                "index.html",
                "model.json",
                "receipt.json",
            }:
                raise ValueError("Standalone Explorer output is incomplete.")
    finally:
        for path, mode in modes.items():
            path.chmod(mode)


def main():
    with tempfile.TemporaryDirectory(prefix="knowledge-bus-skills-cli-") as temporary:
        base = Path(temporary).resolve()
        source = base / "source/skills"
        shutil.copytree(plugin.ROOT / "skills", source)
        env = {
            **os.environ,
            "DISABLE_TELEMETRY": "1",
            "DO_NOT_TRACK": "1",
            "CI": "1",
            "XDG_STATE_HOME": str(base / "state"),
            "npm_config_cache": str(base / "npm-cache"),
            "KNOWLEDGE_BUS_CACHE_DIR": str(base / "runtime-cache"),
        }
        for name in plugin.SKILLS:
            project = base / name
            project.mkdir()
            command = [
                "npx",
                "--yes",
                f"skills@{SKILLS_CLI}",
                "add",
                str(source),
                "--skill",
                name,
                "--agent",
                "codex",
                "--copy",
                "--yes",
            ]
            # No HOME or agent-config overrides. macOS additionally denies writes outside disposable/system temporary locations.
            if sys.platform == "darwin":
                profile = f'(version 1)(allow default)(deny file-write*)(allow file-write* (subpath "{base}") (subpath "{Path(tempfile.gettempdir()).resolve()}") (subpath "/dev"))'
                command = ["sandbox-exec", "-p", profile, *command]
            for attempt in range(2):
                result = subprocess.run(
                    command,
                    cwd=project,
                    env=env,
                    text=True,
                    capture_output=True,
                    timeout=120,
                    check=False,
                )
                if result.returncode:
                    raise RuntimeError(result.stdout + result.stderr)
                installed = project / ".agents/skills" / name
                if not installed.is_dir():
                    raise ValueError(
                        f"The CLI did not install {name} in the expected project location."
                    )
                if {p.name for p in installed.parent.iterdir()} != {name}:
                    raise ValueError("The CLI installed an unselected skill.")
                if file_hashes(installed) != file_hashes(source / name):
                    raise ValueError(
                        f"Installed skill content differs from source: {name}"
                    )
            if name != "kb-uncover-decision":
                exercise_runtime(installed, project, env, explore=name == "kb-explore")
            print(
                f"{name}: selection, file closure, repeat installation, and applicable runtime passed."
            )

        # Exercise the real GitHub-source parser against a local tagged fixture.
        # Git's per-process URL rewrite changes transport only, not the source recorded by skills.
        fixture = base / "tagged-source"
        shutil.copytree(base / "source", fixture)
        for args in (
            ["init", "-b", "main"],
            ["add", "."],
            [
                "-c",
                "user.name=Fixture",
                "-c",
                "user.email=fixture@example.invalid",
                "commit",
                "-m",
                "fixture",
            ],
            ["tag", "v0.5.0"],
        ):
            subprocess.run(["git", *args], cwd=fixture, check=True, capture_output=True)
        tagged_project = base / "tagged-project"
        tagged_project.mkdir()
        git_env = {
            **env,
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "url." + fixture.as_uri() + ".insteadOf",
            "GIT_CONFIG_VALUE_0": "https://github.com/" + REPOSITORY + ".git",
        }

        def tagged_add(tag, agent="codex"):
            command = skills_command(tag, agent) + ["--copy", "--yes"]
            if sys.platform == "darwin":
                profile = f'(version 1)(allow default)(deny file-write*)(allow file-write* (subpath "{base}") (subpath "{Path(tempfile.gettempdir()).resolve()}") (subpath "/dev"))'
                command = ["sandbox-exec", "-p", profile, *command]
            result = subprocess.run(
                command,
                cwd=tagged_project,
                env=git_env,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            if result.returncode:
                raise RuntimeError(result.stdout + result.stderr)

        tagged_add("v0.5.0")
        installed = tagged_project / ".agents/skills/kb-check"
        original = file_hashes(installed)
        lock = (tagged_project / "skills-lock.json").read_text()
        if REPOSITORY not in lock:
            raise ValueError("The skills CLI lost repository attribution.")
        changed = fixture / "skills/kb-check/SKILL.md"
        changed.write_text(changed.read_text() + "\nFixture unreleased change.\n")
        subprocess.run(
            ["git", "add", "."], cwd=fixture, check=True, capture_output=True
        )
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Fixture",
                "-c",
                "user.email=fixture@example.invalid",
                "commit",
                "-m",
                "next fixture",
            ],
            cwd=fixture,
            check=True,
            capture_output=True,
        )
        tagged_add("v0.5.0")
        if file_hashes(installed) != original:
            raise ValueError("A tagged installation picked up unreleased main changes.")
        tagged_add(None)
        if file_hashes(installed) != file_hashes(fixture / "skills/kb-check"):
            raise ValueError("Repository shorthand did not follow the default branch.")
        subprocess.run(
            ["git", "tag", "v0.6.0"], cwd=fixture, check=True, capture_output=True
        )
        tagged_add("v0.6.0")
        if file_hashes(installed) != file_hashes(fixture / "skills/kb-check"):
            raise ValueError("The skills CLI did not update to the selected newer tag.")
        tagged_add("v0.6.0", "claude-code")
        claude_skill = tagged_project / ".claude/skills/kb-check"
        if not claude_skill.is_dir() or file_hashes(claude_skill) != file_hashes(
            fixture / "skills/kb-check"
        ):
            raise ValueError(
                "The Claude Code route did not install the selected tagged skill."
            )
        if {path.name for path in claude_skill.parent.iterdir()} != {"kb-check"}:
            raise ValueError("The Claude Code route installed an unselected skill.")
        print("Claude Code: tagged skill selection and file closure passed.")
        for agent, directory in (("pi", ".pi/skills"), ("opencode", ".agents/skills")):
            tagged_add(None, agent)
            target = tagged_project / directory / "kb-check"
            if file_hashes(target) != file_hashes(fixture / "skills/kb-check"):
                raise ValueError(f"{agent}: selected skill contents differ.")
        print(
            "Tagged Git source: repository attribution, unreleased-change exclusion, and version update passed."
        )
        print("No live agent sessions or public telemetry were used.")


if __name__ == "__main__":
    main()
