"""Knowledge Bus directory selection, isolation, and installed-protocol discovery."""
from pathlib import Path
import shutil

import pytest

from kbp_conform import cli

ROOT = Path(__file__).resolve().parent.parent


def knowledge_bus_dir(folder, *, populated=True):
    metadata = folder / ".knowledge-bus"
    metadata.mkdir(parents=True)
    if populated:
        for name in ("universe.kbp.yaml", "type-guidance.kbp.yaml"):
            shutil.copyfile(ROOT / "universes/product-development" / name, metadata / name)
    return metadata


def selected(target):
    return sorted(str(p) for p in target.glob("*.kbp.yaml"))


def test_nearest_knowledge_bus_dir_and_calls_inside_metadata(tmp_path, monkeypatch):
    parent = knowledge_bus_dir(tmp_path)
    child = tmp_path / "notes" / "deep"
    child.mkdir(parents=True)
    monkeypatch.chdir(child)
    assert cli.find_knowledge_bus_dir() == parent
    assert cli.resolve([])[1] == selected(parent)
    monkeypatch.chdir(parent)
    assert cli.find_knowledge_bus_dir() == parent


def test_nested_empty_knowledge_bus_dir_does_not_fall_back(tmp_path, monkeypatch, capsys):
    knowledge_bus_dir(tmp_path)
    nested = knowledge_bus_dir(tmp_path / "child", populated=False)
    monkeypatch.chdir(nested.parent)
    assert cli.find_knowledge_bus_dir() == nested
    assert cli.resolve([])[1] == []
    assert cli.main([]) == 1
    assert "no documents to check" in capsys.readouterr().out


@pytest.mark.parametrize("metadata_target", [False, True])
def test_explicit_target_overrides_current_knowledge_bus_dir(tmp_path, monkeypatch, metadata_target):
    current = knowledge_bus_dir(tmp_path / "current")
    other = knowledge_bus_dir(tmp_path / "other")
    monkeypatch.chdir(current.parent)
    target = other if metadata_target else other.parent
    assert cli.resolve([str(target)])[1] == selected(other)


def test_explicit_files_are_exact_even_in_old_named_folder(tmp_path, monkeypatch):
    current = knowledge_bus_dir(tmp_path)
    legacy = tmp_path / "notes-spec"
    legacy.mkdir()
    document = legacy / "universe.kbp.yaml"
    shutil.copyfile(current / "universe.kbp.yaml", document)
    monkeypatch.chdir(tmp_path)
    assert cli.resolve([str(document)])[1] == [str(document)]


def test_missing_knowledge_bus_dir_never_initializes_or_discovers_sibling(tmp_path, monkeypatch):
    source = tmp_path / "notes"
    source.mkdir()
    knowledge_bus_dir(tmp_path / "notes-spec")
    monkeypatch.chdir(source)
    before = sorted(tmp_path.rglob("*"))
    assert cli.resolve([])[2] is not None
    assert cli.main([]) == 1
    assert sorted(tmp_path.rglob("*")) == before


def test_explicit_empty_target_does_not_fall_back(tmp_path, monkeypatch):
    knowledge_bus_dir(tmp_path)
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.chdir(tmp_path)
    assert cli.resolve([str(empty)])[1] == []
    assert cli.main([str(empty)]) == 1


def test_missing_explicit_target_reports_error(tmp_path, monkeypatch):
    knowledge_bus_dir(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert "target does not exist" in cli.resolve(["missing"])[2]
    assert cli.main(["missing"]) == 1


def test_generic_directory_scan_skips_nested_knowledge_bus_directories(tmp_path):
    ordinary = tmp_path / "reference"
    ordinary.mkdir()
    document = ordinary / "universe.kbp.yaml"
    shutil.copyfile(ROOT / "tests/conformance/pass/minimal.kbp.yaml", document)
    nested = knowledge_bus_dir(tmp_path / "nested")
    shutil.copyfile(document, nested.parent / "not-a-parent-input.kbp.yaml")
    assert cli.expand([str(tmp_path)]) == [str(document)]


def test_knowledge_bus_dir_loads_guidance_but_not_ingestion_outputs(tmp_path, monkeypatch, capsys):
    metadata = knowledge_bus_dir(tmp_path)
    (metadata / "answers.yaml").write_text("not checker input")
    (metadata / "ingest-log.md").write_text("not checker input")
    before = {p: p.read_bytes() for p in metadata.iterdir()}
    monkeypatch.chdir(tmp_path)
    assert cli.resolve([])[1] == selected(metadata)
    assert cli.main([]) == 0
    output = capsys.readouterr().out
    assert "type-guidance.kbp.yaml" in output
    assert {p: p.read_bytes() for p in metadata.iterdir()} == before


def test_explicit_protocol_uses_current_knowledge_bus_dir(tmp_path, monkeypatch):
    metadata = knowledge_bus_dir(tmp_path)
    monkeypatch.chdir(tmp_path)
    protocol = ROOT / "spec" / cli.PROTOCOL_NAME
    assert cli.resolve([str(protocol)]) == (str(protocol), selected(metadata), None)


def test_self_check_needs_no_user_knowledge_bus_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert cli.main(["--self-check"]) == 0
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("relative", [".", "src/kbp_conform"])
def test_checkout_default_keeps_bundled_examples(monkeypatch, relative):
    monkeypatch.chdir(ROOT / relative)
    monkeypatch.setattr(cli, "find_knowledge_bus_dir", lambda: None)
    assert cli.resolve([])[1] == cli.expand([str(ROOT / "universes")])


def test_packaged_protocol_is_independent_of_current_directory(tmp_path, monkeypatch):
    package = tmp_path / "installed"
    package.mkdir()
    protocol = package / cli.PROTOCOL_NAME
    shutil.copyfile(ROOT / "spec" / cli.PROTOCOL_NAME, protocol)
    monkeypatch.setattr(cli, "PACKAGE_DIR", package)
    monkeypatch.setattr(cli, "CHECKOUT_ROOT", tmp_path / "not-a-checkout")
    monkeypatch.chdir(tmp_path)
    assert cli.default_protocol() == str(protocol)
    assert cli.main(["--self-check"]) == 0


def test_mint_uses_selected_knowledge_bus_dir(tmp_path, monkeypatch, capsys):
    knowledge_bus_dir(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert cli.main(["--mint", "element", "2"]) == 0
    codes = capsys.readouterr().out.splitlines()
    assert len(codes) == len(set(codes)) == 2
