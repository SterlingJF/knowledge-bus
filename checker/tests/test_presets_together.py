"""Every shipped universe spec in one folder.

Each folder under `universes/` ships one universe spec and its guidance. Copied
into one `.knowledge-bus/` folder, the universe specs must still conform, and
`--kinds` must list one group for each universe spec. The universe spec id plus
the declaration id identify a declaration, so two universe specs may declare
the same id. The test reports every shared id as a warning and never fails on a
shared id.
"""

import collections
import json
import shutil
import subprocess
import sys
import warnings
from pathlib import Path

import pytest
import yaml

from kbp_conform import cli

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "protocol/knowledge-bus-protocol.yaml"
UNIVERSES = ROOT / "universes"
SECTIONS = ("elements", "artifacts", "frames", "factors", "relation_kinds")


def shipped():
    return sorted(
        path.parent for path in UNIVERSES.glob("*/universe.kbp.yaml") if path.is_file()
    )


@pytest.fixture(scope="module")
def together(tmp_path_factory):
    folder = tmp_path_factory.mktemp("shipped") / ".knowledge-bus"
    folder.mkdir()
    for preset in shipped():
        for path in preset.glob("*.kbp.yaml"):
            shutil.copy(path, folder / f"{preset.name}.{path.name}")
    return folder


def shared_ids(universe_specs):
    """{section: {id: [universe spec ids]}} for each id declared by two or more universe specs."""
    shared = {}
    for section in SECTIONS:
        owners = collections.defaultdict(list)
        for spec in universe_specs:
            for item in spec.get(section) or []:
                if isinstance(item, dict) and isinstance(item.get("id"), str):
                    owners[item["id"]].append(spec["universe"]["id"])
        found = {key: ids for key, ids in sorted(owners.items()) if len(ids) > 1}
        if found:
            shared[section] = found
    return shared


def test_at_least_two_universe_specs_ship():
    assert len(shipped()) >= 2


def test_shipped_universe_specs_conform_in_one_folder(together):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "kbp_conform.cli",
            "--validate",
            str(PROTOCOL),
            str(together),
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    )
    assert result.returncode == 0, result.stdout
    assert "NON-CONFORMING" not in result.stdout


def test_kinds_lists_each_shipped_universe_spec_as_its_own_group(capsys, together):
    assert cli.main(["--kinds", str(together)]) == 0
    listing = json.loads(capsys.readouterr().out)
    ids = [
        yaml.safe_load((preset / "universe.kbp.yaml").read_text())["universe"]["id"]
        for preset in shipped()
    ]
    assert [group["universe_spec"]["id"] for group in listing["universe_specs"]] == (
        sorted(ids)
    )


def test_shared_ids_are_reported_and_never_refused(together):
    specs = [
        yaml.safe_load(path.read_text())
        for path in sorted(together.glob("*.universe.kbp.yaml"))
    ]
    shared = shared_ids(specs)
    for section, ids in shared.items():
        for key, owners in ids.items():
            warnings.warn(
                f"{section} id {key!r} is declared by {', '.join(owners)}",
                stacklevel=1,
            )
    assert isinstance(shared, dict)


def test_shared_ids_names_each_section_and_universe_spec():
    first = {
        "universe": {"id": "one"},
        "artifacts": [{"id": "minutes"}],
        "frames": [{"id": "stage"}],
    }
    second = {
        "universe": {"id": "two"},
        "artifacts": [{"id": "minutes"}],
        "frames": [{"id": "phase"}],
    }
    assert shared_ids([first, second]) == {"artifacts": {"minutes": ["one", "two"]}}
