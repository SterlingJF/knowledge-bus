"""Packaging boundaries and runtime isolation, without installing into an agent."""

import importlib.util
import io
import json
import os
import shutil
import sys
import tarfile
import tomllib
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


plugin = load("plugin_test_tools", ROOT / "tools/plugin/plugin.py")
runtime = load("plugin_runtime", ROOT / "plugins/shared/runtime/kbp.py")


@pytest.fixture(scope="module")
def wheel(tmp_path_factory):
    base = tmp_path_factory.mktemp("wheel")
    plugin.run(
        "uv",
        "build",
        "--package",
        "knowledge-bus",
        "--wheel",
        "--out-dir",
        str(base),
        env={**os.environ, "SOURCE_DATE_EPOCH": "315532800"},
    )
    (result,) = base.glob("*.whl")
    return result


@pytest.fixture
def assembled(tmp_path, wheel):
    path = tmp_path / "knowledge-bus"
    plugin.assemble("codex", path, wheel)
    return path


def test_all_adapters_share_skills_and_references(tmp_path, wheel):
    outputs = []
    for host in plugin.HOSTS:
        path = tmp_path / host / "knowledge-bus"
        report = plugin.assemble(host, path, wheel)
        assert len(report["skills"]) == 6
        assert report["context_measurement"].startswith("Static characters")
        outputs.append(path)
    for folder in ("skills", "references", "runtime"):
        left = {
            p.relative_to(outputs[0]).as_posix(): p.read_bytes()
            for p in (outputs[0] / folder).rglob("*")
            if p.is_file()
        }
        for output in outputs[1:]:
            right = {
                p.relative_to(output).as_posix(): p.read_bytes()
                for p in (output / folder).rglob("*")
                if p.is_file()
            }
            assert left == right


def test_host_package_carries_one_fresh_shared_viewer_bundle(assembled):
    """All six host skills share one verified prebuilt viewer payload."""
    viewers = list(assembled.rglob("explorer-viewer.js"))
    assert viewers == [assembled / "runtime/explorer-viewer.js"]
    assert (
        viewers[0].read_bytes() == (ROOT / "explorer/prebuilt/viewer.js").read_bytes()
    )


def test_opencode_hook_preserves_existing_config_and_registers_once(tmp_path, wheel):
    path = tmp_path / "knowledge-bus"
    plugin.assemble("opencode", path, wheel)
    script = """
      import assert from 'node:assert/strict';
      const {default: create} = await import(process.argv[1]);
      const hooks = await create();
      const config = {skills: {paths: ['/existing'], urls: ['https://example.com']}, model: 'existing'};
      await hooks.config(config);
      await hooks.config(config);
      assert.equal(config.skills.paths.length, 2);
      assert.equal(config.skills.paths[0], '/existing');
      assert.equal(config.skills.paths[1], process.argv[2]);
      assert.deepEqual(config.skills.urls, ['https://example.com']);
      assert.equal(config.model, 'existing');
      const empty = {};
      await hooks.config(empty);
      assert.deepEqual(empty, {skills: {paths: [process.argv[2]]}});
    """
    plugin.run(
        "node",
        "--input-type=module",
        "-e",
        script,
        (path / "index.js").as_uri(),
        str(path / "skills"),
    )


@pytest.mark.parametrize("host", plugin.HOSTS)
def test_agent_packages_do_not_claim_product_cli(host, tmp_path, wheel):
    path = tmp_path / "knowledge-bus"
    plugin.assemble(host, path, wheel)
    package = json.loads((path / "package.json").read_text())
    assert package["private"] is False
    assert "bin" not in package and "scripts" not in package
    assert package["publishConfig"]["access"] == "public"
    assert json.loads((ROOT / "package.json").read_text())["private"] is True


@pytest.mark.parametrize(
    "mutation",
    ["extra", "missing", "escape", "symlink", "wheel", "lifecycle", "version"],
)
def test_artifact_check_rejects_broken_or_excess_payload(assembled, mutation):
    skill = assembled / "skills/kb-check/SKILL.md"
    if mutation == "extra":
        (assembled / "contributor-notes.md").write_text("Not plugin content")
    elif mutation == "missing":
        skill.unlink()
    elif mutation == "escape":
        skill.write_text(skill.read_text() + "\n[escape](../../../../outside.md)\n")
    elif mutation == "symlink":
        (assembled / "external").symlink_to(ROOT / "README.md")
    elif mutation == "wheel":
        (path,) = (assembled / "runtime").glob("*.whl")
        path.write_bytes(b"invalid")
    else:
        path = assembled / "package.json"
        metadata = json.loads(path.read_text())
        if mutation == "version":
            metadata["version"] = "99.0.0"
        else:
            metadata["scripts"] = {"install": "unsafe"}
        plugin.json_write(path, metadata)
    with pytest.raises(ValueError):
        plugin.inspect(assembled, "codex", plugin.check_versions())


@pytest.mark.parametrize(
    "name,kind",
    [
        ("package/../../escape", "file"),
        ("/outside", "file"),
        ("package/link", "symlink"),
        ("package/link", "hardlink"),
    ],
)
def test_unpack_rejects_unsafe_members(tmp_path, name, kind):
    archive = tmp_path / "bad.tgz"
    with tarfile.open(archive, "w:gz") as tar:
        member = tarfile.TarInfo(name)
        if kind != "file":
            member.type = tarfile.SYMTYPE if kind == "symlink" else tarfile.LNKTYPE
            member.linkname = "../../outside"
        tar.addfile(member, io.BytesIO(b""))
    with pytest.raises(ValueError):
        plugin.unpack(archive, tmp_path / "unpacked")
    assert not (tmp_path / "escape").exists()


def test_launcher_uses_bundled_runtime_external_cache_and_preserves_arguments(
    assembled, tmp_path
):
    env = {
        **os.environ,
        "KNOWLEDGE_BUS_CACHE_DIR": str(tmp_path / "cache"),
        "UV_PROJECT_ENVIRONMENT": "/wrong/venv",
        "UV_NO_SYNC": "1",
        "PYTHONPATH": "/wrong/modules",
    }
    arguments = ["--validate", "/notes with spaces/.knowledge-bus"]
    command, actual = runtime.command(arguments, assembled / "runtime", env)
    assert command[-2:] == arguments
    assert "--no-project" in command and "--isolated" in command
    assert "UV_PROJECT_ENVIRONMENT" not in actual and "UV_NO_SYNC" not in actual
    assert "PYTHONPATH" not in actual
    assert actual["UV_CACHE_DIR"] == str(tmp_path / "cache")
    assert any(str(assembled / "runtime") in part for part in command)
    assert "UV_PROJECT_ENVIRONMENT" in env
    assert command[command.index("--python") + 1] == sys.executable
    assert actual["UV_PYTHON_DOWNLOADS"] == "never"
    assert actual["UV_OFFLINE"] == "1"
    assert "--offline" in command
    assert not json.loads((assembled / "runtime/requirements.json").read_text())[
        "dependencies"
    ]
    assert actual["KNOWLEDGE_BUS_EXPLORER_BUNDLE"] == str(
        assembled / "runtime/explorer-viewer.js"
    )


def test_python_configuration_is_consistent():
    project = tomllib.loads((ROOT / "checker/pyproject.toml").read_text())["project"]
    selected = (ROOT / ".python-version").read_text().strip()
    config = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert project["requires-python"] == ">=" + selected
    assert config["tool"]["ruff"]["target-version"] == "py" + selected.replace(".", "")
    import yaml

    for file in ("ci.yml", "release.yml"):
        workflow = yaml.safe_load((ROOT / ".github/workflows" / file).read_text())
        assert workflow["env"]["UV_MANAGED_PYTHON"] == "true"
        for job in workflow["jobs"].values():
            steps = job["steps"]
            assert any(step.get("run") == "uv python install" for step in steps)
            assert not any("python-version" in step.get("with", {}) for step in steps)


@pytest.mark.parametrize("delta,allowed", [(-1, False), (0, True), (1, True)])
def test_launcher_enforces_packaged_minimum(assembled, monkeypatch, delta, allowed):
    config = json.loads((assembled / "runtime/requirements.json").read_text())
    minimum = tuple(map(int, config["requires_python"][2:].split(".")))
    version = (minimum[0], minimum[1] + delta, 0)
    monkeypatch.setattr(
        runtime,
        "sys",
        SimpleNamespace(
            version_info=version, executable=sys.executable, platform=sys.platform
        ),
    )
    if allowed:
        runtime.command([], assembled / "runtime")
    else:
        with pytest.raises(ValueError) as error:
            runtime.command([], assembled / "runtime", {"PATH": ""})
        assert config["requires_python"] in str(error.value)
        assert ".".join(map(str, version)) in str(error.value)


def test_launcher_requirement_is_not_hardcoded(assembled, monkeypatch):
    path = assembled / "runtime/requirements.json"
    config = json.loads(path.read_text())
    config["requires_python"] = ">=9.2.1"
    plugin.json_write(path, config)
    monkeypatch.setattr(runtime, "sys", SimpleNamespace(version_info=(9, 2, 0)))
    with pytest.raises(ValueError, match=r"Python >=9\.2\.1"):
        runtime.command([], assembled / "runtime")


@pytest.mark.parametrize("requirement", [None, "", ">=3.14,<4", "garbage"])
def test_launcher_rejects_invalid_python_metadata(assembled, requirement):
    path = assembled / "runtime/requirements.json"
    config = json.loads(path.read_text())
    if requirement is None:
        config.pop("requires_python")
    else:
        config["requires_python"] = requirement
    plugin.json_write(path, config)
    with pytest.raises(ValueError, match="missing or unsupported"):
        runtime.command([], assembled / "runtime")


def test_inspection_rejects_python_requirement_drift(assembled):
    path = assembled / "runtime/requirements.json"
    config = json.loads(path.read_text())
    config["requires_python"] = ">=9.0"
    plugin.json_write(path, config)
    with pytest.raises(ValueError, match="differs from bundled wheel"):
        plugin.inspect(assembled, "codex", config["version"])


def test_launcher_rejects_missing_uv_and_internal_cache(assembled):
    with pytest.raises(ValueError, match="requires uv"):
        runtime.command([], assembled / "runtime", {"PATH": ""})
    with pytest.raises(ValueError, match="outside"):
        runtime.command(
            [],
            assembled / "runtime",
            {**os.environ, "KNOWLEDGE_BUS_CACHE_DIR": str(assembled / "cache")},
        )


def test_source_copy_rejects_symlink(tmp_path):
    source = tmp_path / "source"
    source.symlink_to(ROOT / "README.md")
    with pytest.raises(ValueError, match="symlink"):
        plugin.copy(source, tmp_path / "target", ROOT)


def test_pnpm_pack_is_reproducible_and_matches_verified_inventory(tmp_path):
    first, second = tmp_path / "first", tmp_path / "second"
    plugin.build(plugin.HOSTS, output=first)
    plugin.build(plugin.HOSTS, output=second)
    for archive in first.glob("*.tgz"):
        assert archive.read_bytes() == (second / archive.name).read_bytes()
        report = json.loads((first / (archive.stem + ".report.json")).read_text())
        with tarfile.open(archive) as tar:
            assert {
                m.name.removeprefix("package/") for m in tar.getmembers() if m.isfile()
            } == set(report["files"])


def test_runtime_in_read_only_plugin_preserves_user_files(assembled):
    plugin.runtime_check(assembled)


def test_version_drift_is_rejected(tmp_path):
    for path in plugin.version_files():
        target = tmp_path / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    (tmp_path / "checker").mkdir()
    shutil.copyfile(
        ROOT / "checker/pyproject.toml", tmp_path / "checker/pyproject.toml"
    )
    path = plugin.version_files(tmp_path)[0]
    data = json.loads(path.read_text())
    data["version"] = "99.0.0"
    plugin.json_write(path, data)
    with pytest.raises(ValueError, match="versions differ"):
        plugin.check_versions(tmp_path)
