"""Real wheel and source-archive protocol isolation."""

import shutil
import subprocess
import tomllib
import zipfile
from email.parser import BytesParser
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL_NAME = "knowledge-bus-protocol.yaml"


def test_build_backend_is_exactly_pinned_for_generated_wheel_freshness():
    """A backend upgrade must be an intentional generated-resource change."""
    build = tomllib.loads((ROOT / "checker/pyproject.toml").read_text())["build-system"]
    assert build["requires"] == ["hatchling==1.32.4"]


@pytest.fixture
def project(tmp_path):
    checker = tmp_path / "workspace/checker"
    shutil.copytree(
        ROOT / "checker",
        checker,
        ignore=shutil.ignore_patterns("__pycache__", "*.egg-info", "dist"),
    )
    shutil.copyfile(ROOT / "LICENSE", checker.parent / "LICENSE")
    bundled = checker / "src/kbp_conform" / PROTOCOL_NAME
    bundled.unlink(missing_ok=True)
    adjacent = checker.parent / "protocol" / PROTOCOL_NAME
    adjacent.parent.mkdir()
    return checker, bundled, adjacent


def build(source, destination, kind):
    return subprocess.run(
        ["uv", "build", str(source), "--" + kind, "--out-dir", str(destination)],
        cwd=destination.parent,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def protocol_bytes(output):
    (wheel,) = output.glob("*.whl")
    with zipfile.ZipFile(wheel) as archive:
        return archive.read("kbp_conform/" + PROTOCOL_NAME)


def test_wheel_vendors_runtime_yaml_without_external_requirement(project, tmp_path):
    """Installed checking has no dependency left to resolve from a registry."""
    checker, _, adjacent = project
    adjacent.write_bytes((ROOT / "protocol" / PROTOCOL_NAME).read_bytes())
    output = tmp_path / "wheel"
    result = build(checker, output, "wheel")
    assert result.returncode == 0, result.stdout + result.stderr
    (wheel,) = output.glob("*.whl")
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        assert "kbp_conform/_vendor/yaml/__init__.py" in names
        assert "kbp_conform/_vendor/PyYAML-LICENSE" in names
        (metadata_path,) = [
            name for name in names if name.endswith(".dist-info/METADATA")
        ]
        metadata = BytesParser().parsebytes(archive.read(metadata_path))
        assert not metadata.get_all("Requires-Dist")


@pytest.mark.parametrize("bundled_present", [True, False])
def test_wheel_prefers_bundled_protocol_and_falls_back_to_workspace(
    project, tmp_path, bundled_present
):
    checker, bundled, adjacent = project
    adjacent.write_bytes(b"workspace protocol\n")
    if bundled_present:
        bundled.write_bytes(b"bundled protocol\n")
    output = tmp_path / "wheel"
    result = build(checker, output, "wheel")
    assert result.returncode == 0, result.stdout + result.stderr
    assert protocol_bytes(output) == (
        b"bundled protocol\n" if bundled_present else b"workspace protocol\n"
    )


def test_missing_protocol_refuses_build(project, tmp_path):
    checker, _, _ = project
    result = build(checker, tmp_path / "wheel", "wheel")
    assert result.returncode != 0
    assert "Missing protocol" in result.stdout + result.stderr


def test_sdist_rebuild_uses_its_protocol_despite_adjacent_conflict(project, tmp_path):
    checker, _, adjacent = project
    expected = (ROOT / "protocol" / PROTOCOL_NAME).read_bytes()
    adjacent.write_bytes(expected)
    output = tmp_path / "sdist"
    result = build(checker, output, "sdist")
    assert result.returncode == 0, result.stdout + result.stderr
    (archive,) = output.glob("*.tar.gz")
    extracted = tmp_path / "extracted"
    extracted.mkdir()
    shutil.unpack_archive(archive, extracted, filter="data")
    (source,) = extracted.iterdir()
    conflict = extracted / "protocol"
    conflict.mkdir()
    (conflict / PROTOCOL_NAME).write_bytes(b"wrong adjacent protocol\n")
    rebuilt = tmp_path / "rebuilt"
    result = build(source, rebuilt, "wheel")
    assert result.returncode == 0, result.stdout + result.stderr
    assert protocol_bytes(rebuilt) == expected
