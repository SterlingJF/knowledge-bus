"""Generated-resource ownership and read-only verification."""

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def generator(monkeypatch, tmp_path):
    monkeypatch.syspath_prepend(str(ROOT / "tools/plugin"))
    spec = importlib.util.spec_from_file_location(
        "ownership_skills", ROOT / "tools/plugin/skills.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    directory = tmp_path / "skills/example"
    directory.mkdir(parents=True)
    (directory / "SKILL.md").write_text("# Authored\n")
    files = {
        "references/current.md": b"# Current\n",
        "generated.json": b'{"files": {"references/current.md": "test"}}\n',
    }
    monkeypatch.setattr(module, "payloads", lambda root: iter([("example", files)]))
    return module, directory, files


def snapshot(root):
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def test_prunes_owned_stale_files_and_preserves_authored_skill(generator, tmp_path):
    module, directory, files = generator
    (directory / "stale.txt").write_text("old")
    (directory / "generated.json").write_text(
        json.dumps({"files": {"stale.txt": "old"}})
    )
    module.generate(tmp_path)
    assert not (directory / "stale.txt").exists()
    assert (directory / "SKILL.md").read_text() == "# Authored\n"
    assert all((directory / name).read_bytes() == data for name, data in files.items())
    before = snapshot(directory)
    module.generate(tmp_path)
    assert snapshot(directory) == before


def test_unknown_file_refusal_preserves_directory(generator, tmp_path):
    module, directory, _ = generator
    (directory / "personal.txt").write_text("not generated")
    before = snapshot(directory)
    with pytest.raises(ValueError, match="Unexpected files"):
        module.generate(tmp_path)
    assert snapshot(directory) == before


def test_payload_failure_precedes_all_output_writes(generator, tmp_path, monkeypatch):
    module, _, files = generator

    def broken(root):
        yield "example", files
        raise RuntimeError("payload failed")

    monkeypatch.setattr(module, "payloads", broken)
    before = snapshot(tmp_path)
    with pytest.raises(RuntimeError, match="payload failed"):
        module.generate(tmp_path)
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize("mutation", ["stale", "missing", "extra"])
def test_check_mode_never_changes_files(generator, tmp_path, mutation):
    module, directory, _ = generator
    module.generate(tmp_path)
    path = directory / "references/current.md"
    if mutation == "stale":
        path.write_text("stale")
    elif mutation == "missing":
        path.unlink()
    else:
        (directory / "extra.txt").write_text("extra")
    before = snapshot(tmp_path)
    with pytest.raises(ValueError, match="Stale generated"):
        module.generate(tmp_path, check=True)
    assert snapshot(tmp_path) == before


def test_symlink_is_refused_without_touching_target(generator, tmp_path):
    module, directory, _ = generator
    outside = tmp_path / "outside.txt"
    outside.write_text("preserve")
    (directory / "link.txt").symlink_to(outside)
    with pytest.raises(ValueError, match="symlink"):
        module.generate(tmp_path)
    assert outside.read_text() == "preserve"
    assert (directory / "link.txt").is_symlink()


@pytest.mark.parametrize("link", ["missing.md", "../../outside.md"])
def test_broken_or_escaping_links_are_refused(generator, tmp_path, link):
    module, directory, _ = generator
    (tmp_path / "outside.md").write_text("# Outside\n")
    (directory / "SKILL.md").write_text(f"# Authored\n\n[Reference]({link})\n")
    with pytest.raises(ValueError, match="reference escapes or is missing"):
        module.generate(tmp_path)
    assert (tmp_path / "outside.md").read_text() == "# Outside\n"


def test_explorer_viewer_bytes_belong_only_to_explore_standalone_skill():
    """Unrelated standalone skills do not absorb the optional viewer payload."""
    for directory in (ROOT / "skills").iterdir():
        if not directory.is_dir():
            continue
        assets = {
            path.relative_to(directory).as_posix()
            for path in directory.rglob("explorer-viewer.*")
        }
        if directory.name == "kb-explore":
            assert assets == {
                "runtime/explorer-viewer.js",
                "runtime/explorer-viewer.json",
            }
        else:
            assert assets == set()
