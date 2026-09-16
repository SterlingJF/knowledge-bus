"""Release safeguards without publishing or tagging the working repository."""

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "release_tools", ROOT / "tools/release/release.py"
)
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


@pytest.fixture
def project(tmp_path, monkeypatch):
    for name in (
        "checker/pyproject.toml",
        "plugins/claude/knowledge-bus/.claude-plugin/plugin.json",
        "uv.lock",
        "protocol/knowledge-bus-protocol.yaml",
        "pnpm-lock.yaml",
        *(p.relative_to(ROOT).as_posix() for p in release.plugins.version_files(ROOT)),
    ):
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    # Keep release-transition fixtures stable after the project itself advances.
    protocol_file = tmp_path / "protocol/knowledge-bus-protocol.yaml"
    protocol_file.write_text(
        protocol_file.read_text().replace(
            f"version: {release.metadata(ROOT)[2].split('/')[1]}",
            "version: 0.5",
            1,
        )
    )
    project_file = tmp_path / "checker/pyproject.toml"
    project_file.write_text(
        project_file.read_text().replace(
            f'version = "{release.metadata(ROOT)[0]}"', 'version = "0.5.0"', 1
        )
    )
    plugin_file = tmp_path / "plugins/claude/knowledge-bus/.claude-plugin/plugin.json"
    plugin = json.loads(plugin_file.read_text())
    plugin["version"] = "0.5.0"
    plugin_file.write_text(json.dumps(plugin))
    for path in release.plugins.version_files(tmp_path):
        document = json.loads(path.read_text())
        document["version"] = "0.5.0"
        path.write_text(json.dumps(document))
    (tmp_path / "CHANGELOG.md").write_text(
        "# Changelog\n\n## Historical Release Notes\n\n- Kept.\n"
    )
    monkeypatch.setattr(release, "git", lambda *args, **kwargs: "")
    monkeypatch.setattr(release, "run", lambda *args, **kwargs: None)
    return tmp_path


def finish_notes(project):
    path = project / "CHANGELOG.md"
    path.write_text(
        path.read_text().replace(
            "TODO: Describe the user-facing changes.", "Add automatic discovery."
        )
    )


def test_release_checks_run_full_suite_before_building(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(release, "check_metadata", lambda root: ("0.5.0", "notes"))
    monkeypatch.setattr(release, "run", lambda *args, **kwargs: calls.append(args))
    monkeypatch.setattr(release, "build_check", lambda *args: calls.append(("build",)))
    monkeypatch.setattr(
        release.plugins, "build", lambda *args, **kwargs: calls.append(("plugins",))
    )
    release.check(tmp_path)
    assert calls[:3] == [
        ("uv", "lock", "--check"),
        ("pnpm", "install", "--frozen-lockfile", "--ignore-scripts"),
        ("pnpm", "run", "check"),
    ]
    assert calls.index(("pnpm", "run", "check")) < calls.index(("build",))
    for script in ("check_skills_install.py", "check_native_install.py"):
        assert ("uv", "run", "--locked", "python", f"tools/plugin/{script}") in calls
    assert ("plugins",) in calls


def test_prepare_synchronizes_without_changing_protocol(project):
    protocol = (project / "protocol/knowledge-bus-protocol.yaml").read_bytes()
    release.prepare("0.6.0", project)
    assert release.metadata(project) == ("0.6.0", "0.6.0", "kbp/0.5")
    assert all(
        json.loads(p.read_text())["version"] == "0.6.0"
        for p in release.plugins.version_files(project)
    )
    assert (project / "protocol/knowledge-bus-protocol.yaml").read_bytes() == protocol
    assert "Historical Release Notes" in (project / "CHANGELOG.md").read_text()
    with pytest.raises(ValueError, match="Finish"):
        release.check_metadata(project)
    finish_notes(project)
    assert release.check_metadata(project)[0] == "0.6.0"


@pytest.mark.parametrize(
    "version", ["v0.6.0", "0.6", "01.6.0", "0.6.0-rc1", "0.5.0", "0.4.0"]
)
def test_prepare_rejects_invalid_or_non_increasing_versions(project, version):
    before = (project / "checker/pyproject.toml").read_bytes()
    with pytest.raises(ValueError):
        release.prepare(version, project)
    assert (project / "checker/pyproject.toml").read_bytes() == before


def test_prepare_rejects_dirty_tree(project, monkeypatch):
    monkeypatch.setattr(release, "git", lambda *args, **kwargs: " M README.md")
    with pytest.raises(ValueError, match="working-tree"):
        release.prepare("0.6.0", project)


def test_prepare_rejects_existing_tag(project, monkeypatch):
    monkeypatch.setattr(
        release, "git", lambda *args, **kwargs: "v0.6.0" if args[0] == "tag" else ""
    )
    with pytest.raises(ValueError, match="already exists"):
        release.prepare("0.6.0", project)


def test_prepare_rolls_back_failed_lock(project, monkeypatch):
    before = {p: p.read_bytes() for p in project.rglob("*") if p.is_file()}

    def fail(*args, **kwargs):
        raise subprocess.CalledProcessError(1, args)

    monkeypatch.setattr(release, "run", fail)
    with pytest.raises(subprocess.CalledProcessError):
        release.prepare("0.6.0", project)
    assert {p: p.read_bytes() for p in before} == before


def test_metadata_rejects_mismatched_manifest_and_protocol_notes(project):
    release.prepare("0.6.0", project)
    finish_notes(project)
    path = project / "plugins/claude/knowledge-bus/.claude-plugin/plugin.json"
    plugin = json.loads(path.read_text())
    plugin["version"] = "0.1.0"
    path.write_text(json.dumps(plugin))
    with pytest.raises(ValueError, match="versions differ"):
        release.check_metadata(project)
    plugin["version"] = "0.6.0"
    path.write_text(json.dumps(plugin))
    changelog = project / "CHANGELOG.md"
    changelog.write_text(changelog.read_text().replace("kbp/0.5", "kbp/0.4"))
    with pytest.raises(ValueError, match="Bundled protocol"):
        release.check_metadata(project)


def test_tag_refuses_feature_branch(project, monkeypatch):
    monkeypatch.setattr(
        release, "git", lambda *args, **kwargs: "feature" if args[0] == "branch" else ""
    )
    with pytest.raises(ValueError, match="from main"):
        release.tag(project)


def test_tag_requires_synced_main_and_only_creates_local_annotated_tag(
    project, monkeypatch
):
    calls = []
    remote = ["behind"]

    def git(*args, **kwargs):
        if args[0] == "branch":
            return "main"
        if args[:2] == ("rev-parse", "HEAD"):
            return "abc"
        if args[:2] == ("rev-parse", "refs/remotes/origin/main"):
            return remote[0]
        return ""

    monkeypatch.setattr(release, "git", git)
    monkeypatch.setattr(release, "run", lambda *args, **kwargs: calls.append(args))
    monkeypatch.setattr(release, "check", lambda root: None)
    with pytest.raises(ValueError, match="match origin/main"):
        release.tag(project)
    remote[0] = "abc"
    release.tag(project)
    assert calls[-1] == (
        "git",
        "tag",
        "-a",
        "v0.5.0",
        "abc",
        "-m",
        "Knowledge Bus 0.5.0",
    )
    assert not any("push" in args for args in calls)


def test_verify_tag_checks_name_annotation_commit_and_ancestry(project, monkeypatch):
    release.prepare("0.6.0", project)
    finish_notes(project)
    with pytest.raises(ValueError, match="does not match"):
        release.verify_tag("v0.7.0", project)
    with pytest.raises(ValueError, match="annotated"):
        release.verify_tag("v0.6.0", project)
    monkeypatch.setattr(
        release,
        "git",
        lambda *args, **kwargs: "tag" if args[0] == "cat-file" else "abc",
    )
    calls = []
    monkeypatch.setattr(release, "run", lambda *args, **kwargs: calls.append(args))
    assert "Add automatic discovery." in release.verify_tag("v0.6.0", project)
    assert calls[-1] == (
        "git",
        "merge-base",
        "--is-ancestor",
        "abc",
        "refs/remotes/origin/main",
    )


def test_version_without_user_directory(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "kbp_conform.cli", "--version"],
        check=False,
        cwd=tmp_path,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert (
        result.stdout
        == f"Knowledge Bus {release.metadata(ROOT)[0]}\nBundled protocol: {release.metadata(ROOT)[2]}\n"
    )


def test_repository_release_versions_agree():
    package, plugin, _ = release.metadata(ROOT)
    assert package == plugin


def test_tag_check_failure_never_creates_tag(project, monkeypatch):
    def git(*args, **kwargs):
        if args[0] == "branch":
            return "main"
        if args[0] == "rev-parse":
            return "abc"
        return ""

    calls = []
    monkeypatch.setattr(release, "git", git)
    monkeypatch.setattr(release, "run", lambda *args, **kwargs: calls.append(args))

    def failed_check(root):
        raise ValueError("Checks failed")

    monkeypatch.setattr(release, "check", failed_check)
    with pytest.raises(ValueError, match="Checks failed"):
        release.tag(project)
    assert not any(args[:2] == ("git", "tag") for args in calls)


def test_unmerged_tag_is_rejected(project, monkeypatch):
    release.prepare("0.6.0", project)
    finish_notes(project)
    monkeypatch.setattr(
        release,
        "git",
        lambda *args, **kwargs: "tag" if args[0] == "cat-file" else "abc",
    )

    def not_an_ancestor(*args, **kwargs):
        raise subprocess.CalledProcessError(1, args)

    monkeypatch.setattr(release, "run", not_an_ancestor)
    with pytest.raises(subprocess.CalledProcessError):
        release.verify_tag("v0.6.0", project)


def test_prepare_restores_generated_resources_after_generation_failure(
    project, monkeypatch
):
    old = project / "skills/kb-check/runtime/checker.whl"
    old.parent.mkdir(parents=True)
    old.write_bytes(b"original")
    created = old.parent / "new.whl"

    def fail_generation(*args, **kwargs):
        if "tools/plugin/skills.py" in args:
            old.write_bytes(b"partial")
            created.write_bytes(b"new")
            raise subprocess.CalledProcessError(1, args)

    monkeypatch.setattr(release, "run", fail_generation)
    with pytest.raises(subprocess.CalledProcessError):
        release.prepare("0.6.0", project)
    assert old.read_bytes() == b"original"
    assert not created.exists()
    assert release.metadata(project)[0] == "0.5.0"
