"""Nested folders: `.knowledge-bus/workspace.yaml` and its `from_parent` key.

Most folders under checker/tests/workspace/ hold `hall/.knowledge-bus/` and
`hall/committee/.knowledge-bus/`. `no-parent` has no `hall/.knowledge-bus/`, and
`grandparent` adds `hall/committee/finance/.knowledge-bus/`. REFUSALS lists the folder cases that must fail,
each for exactly one refusal. docs/knowledge-bus-directory.md describes the rules
for nested folders.
"""

import json
import shutil
from pathlib import Path

import pytest
import yaml

from kbp_conform import cli, workspace

ROOT = Path(__file__).resolve().parents[2]
CASES = Path(__file__).resolve().parent / "workspace"
ERROR_SCHEMA = "knowledge-bus/inspection-error/1"

F1 = "workspace.yaml: must be a mapping"
F2 = "workspace.yaml: unknown key"
F3 = "from_parent must be a list of universe spec ids, each named once"
F4 = "no .knowledge-bus/ is above this folder"
F5 = "which the parent folder does not declare"
F6 = "which this folder already declares"
F7 = "a universe spec from the parent folder"
F8 = "in the parent folder"
FRAGMENTS = (F1, F2, F3, F4, F5, F6, F7, F8)

# Commands run on each folder case; "check" is a bare `kbp <folder>`.
EVERY = ("check", "--mint", "--kinds", "--inspect", "--explore")
REFUSALS = {
    "empty": (F1, EVERY),
    "list": (F1, EVERY),
    "not-yaml": (F1, EVERY),
    "unknown-key": (F2, EVERY),
    "not-a-list": (F3, EVERY),
    "blank-id": (F3, EVERY),
    "repeated-id": (F3, EVERY),
    "no-parent": (F4, EVERY),
    "misnamed": (F5, EVERY),
    "grandparent": (F5, EVERY),
    "id-reuse": (F6, EVERY),
    "nested-guidance": (F7, ("check", "--kinds", "--inspect", "--explore")),
    "nested-marks": (F7, ("--inspect", "--explore")),
    "unreadable-parent": (F8, EVERY),
}


def run(capsys, *args):
    code = cli.main(list(args))
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def error_of(err):
    error = json.loads(err)
    assert error["schema"] == ERROR_SCHEMA
    assert error["status"] == "error"
    return error


@pytest.fixture
def elsewhere(tmp_path, monkeypatch):
    """Run from a folder whose parent folders hold no .knowledge-bus/."""
    folder = tmp_path / "elsewhere"
    folder.mkdir()
    monkeypatch.chdir(folder)
    return folder


def case(tmp_path, name):
    """Copy one folder case; return its `hall/` folder."""
    shutil.copytree(CASES / name, tmp_path / name)
    return tmp_path / name / "hall"


def checked_folder(hall):
    """The deepest folder holding a workspace.yaml in a folder case."""
    found = sorted(hall.rglob(workspace.FILE), key=lambda path: len(path.parts))
    return found[-1].parent.parent


def command(name, folder, tmp_path):
    return {
        "check": [str(folder)],
        "--mint": ["--mint", "element", "1", str(folder)],
        "--kinds": ["--kinds", str(folder)],
        "--inspect": ["--inspect", str(folder)],
        "--explore": [
            "--explore",
            str(folder),
            "--output",
            str(tmp_path / "out.html"),
        ],
    }[name]


def said(code, out, err):
    """Everything a refused command printed, as one string."""
    assert code == 1
    if err:
        assert out == ""
        return error_of(err)["message"]
    return out


def write_parent_guidance(hall):
    (hall / ".knowledge-bus" / "upkeep.type-guidance.kbp.yaml").write_text(
        (
            CASES
            / "nested-guidance/hall/committee/.knowledge-bus/upkeep.type-guidance.kbp.yaml"
        ).read_text()
    )


def write_parent_marks(hall):
    (hall / ".knowledge-bus" / "upkeep.marks.explorer.yaml").write_text(
        (
            CASES
            / "nested-marks/hall/committee/.knowledge-bus/upkeep.marks.explorer.yaml"
        ).read_text()
    )


# A nested folder with and without workspace.yaml.


def test_a_nested_folder_naming_its_parents_universe_spec(capsys, tmp_path, elsewhere):
    committee = case(tmp_path, "workspace-only") / "committee"
    scope = committee / ".knowledge-bus"
    code, out, err = run(capsys, "--kinds", str(scope))
    assert code == 0, err
    assert json.loads(out)["universe_spec"]["id"] == "hall-upkeep"
    code, out, err = run(capsys, "--card", "hirer-checklist", str(committee))
    assert code == 0, err
    assert json.loads(out)["universe_spec"]["id"] == "hall-upkeep"
    code, out, err = run(capsys, "--card", "booking-form", str(scope))
    assert code == 1
    assert error_of(err)["candidates"] == ["hirer-checklist"]


def test_kinds_found_from_inside_a_nested_folder_sees_named_universe_specs(
    capsys, tmp_path, monkeypatch
):
    committee = case(tmp_path, "workspace-only") / "committee"
    inside = committee / "2026"
    inside.mkdir()
    monkeypatch.chdir(inside)
    code, out, err = run(capsys, "--kinds")
    assert code == 0, err
    assert json.loads(out)["universe_spec"]["id"] == "hall-upkeep"


def test_a_nested_folder_without_workspace_stands_alone(capsys, tmp_path, elsewhere):
    scope = case(tmp_path, "workspace-only") / "committee" / ".knowledge-bus"
    (scope / workspace.FILE).unlink()
    for args in (["--kinds", str(scope)], ["--card", "hirer-checklist", str(scope)]):
        code, out, err = run(capsys, *args)
        assert code == 1
        assert out == ""
        assert error_of(err)["message"] == (
            "No Knowledge Bus definitions in the selected scope"
        )
    assert cli.main([str(scope)]) == 1
    assert "no documents to check" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("name", "passes", "says"),
    [
        ("upkeep", True, None),
        ("misnamed", False, "'hall-upkeepz'"),
        ("unknown-key", False, "unknown key 'inherits'"),
    ],
)
def test_a_bare_check_validates_workspace(capsys, tmp_path, name, passes, says):
    scope = case(tmp_path, name) / "committee" / ".knowledge-bus"
    code = cli.main([str(scope)])
    out = capsys.readouterr().out
    assert "=== workspace.yaml ===" in out
    assert code == (0 if passes else 1), out
    if says:
        assert "FAIL" in out and says in out


def test_a_bare_check_of_a_nested_folder_naming_nothing_has_no_documents(
    capsys, tmp_path
):
    scope = case(tmp_path, "workspace-only") / "committee" / ".knowledge-bus"
    (scope / workspace.FILE).write_text("from_parent: []\n")
    code = cli.main([str(scope)])
    out = capsys.readouterr().out
    assert code == 1
    assert "no documents to check" in out
    assert "workspace.yaml: CONFORMS" not in out


@pytest.mark.parametrize("listed", [None, "from_parent: []\n"])
def test_a_folder_naming_nothing_from_its_parent_never_reads_the_parent(
    capsys, tmp_path, elsewhere, listed
):
    scope = case(tmp_path, "names-nothing") / "committee" / ".knowledge-bus"
    if listed is None:
        (scope / workspace.FILE).unlink()
    code, out, err = run(capsys, "--kinds", str(scope))
    assert code == 0, err
    assert json.loads(out)["universe_spec"]["id"] == "hall-lettings"
    code, out, _ = run(capsys, str(scope))
    assert code == 0, out


def test_inspect_reads_workspace(capsys, tmp_path):
    hall = case(tmp_path, "workspace-only")
    scope = hall / "committee" / ".knowledge-bus"
    code, out, err = run(capsys, "--inspect", str(scope))
    assert code == 0, err
    nested = json.loads(out)
    assert nested["layers"]["universe"]["id"] == "hall-upkeep"
    code, out, err = run(capsys, "--inspect", str(hall), "--universe", "hall-upkeep")
    assert code == 0, err
    assert nested == json.loads(out)


# Every command agrees on the folder's universe specs, each listed separately.


def test_check_covers_named_universe_specs(capsys, tmp_path):
    committee = case(tmp_path, "upkeep") / "committee"
    code, out, _ = run(capsys, str(committee))
    assert code == 0, out
    blocks = [line for line in out.splitlines() if line.startswith("=== ")]
    assert blocks[1:] == [
        "=== workspace.yaml ===",
        "=== committee-minutes.universe.kbp.yaml against kbp/0.8 ===",
        "=== hall-upkeep.universe.kbp.yaml from the parent folder, against kbp/0.8 ===",
    ]
    assert "  names hall-upkeep from ../.knowledge-bus/" in out
    assert "workspace.yaml: CONFORMS" in out
    assert "committee-minutes.universe.kbp.yaml: CONFORMS" in out
    assert "hall-upkeep.universe.kbp.yaml: CONFORMS" in out
    assert "hall-bookings" not in out


def test_check_adds_the_parent_folders_guidance_for_a_named_universe_spec(
    capsys, tmp_path
):
    hall = case(tmp_path, "upkeep")
    write_parent_guidance(hall)
    code, out, _ = run(capsys, str(hall / "committee"))
    assert code == 0, out
    assert (
        "=== upkeep.type-guidance.kbp.yaml from the parent folder, against kbp/0.8 ==="
        in out
    )
    assert "upkeep.type-guidance.kbp.yaml: CONFORMS" in out


def test_a_named_universe_spec_that_fails_its_check_fails_the_nested_folder(
    capsys, tmp_path
):
    hall = case(tmp_path, "upkeep")
    path = hall / ".knowledge-bus" / "hall-upkeep.universe.kbp.yaml"
    universe = yaml.safe_load(path.read_text())
    del universe["universe"]["ordering_frame"]
    path.write_text(yaml.safe_dump(universe, sort_keys=False))
    committee = hall / "committee"
    code, out, _ = run(capsys, str(committee))
    assert code == 1
    assert "hall-upkeep.universe.kbp.yaml: NON-CONFORMING" in out
    for args in (
        ["--kinds", str(committee)],
        ["--card", "hirer-checklist", str(committee), "--universe", "hall-upkeep"],
        ["--inspect", str(committee), "--universe", "hall-upkeep"],
    ):
        code, out, err = run(capsys, *args)
        assert code == 1
        assert error_of(err)["category"] == "conformance"


def test_inspect_and_explore_honour_the_file(capsys, tmp_path):
    hall = case(tmp_path, "upkeep")
    write_parent_guidance(hall)
    write_parent_marks(hall)
    committee = hall / "committee"
    code, out, err = run(capsys, "--inspect", str(committee))
    assert code == 1
    assert out == ""
    error = error_of(err)
    assert error["message"] == (
        "Multiple universes require an explicit universe id or file"
    )
    assert error["candidates"] == ["committee-minutes", "hall-upkeep"]
    assert error["from_parent"] == ["hall-upkeep"]
    code, out, err = run(
        capsys, "--inspect", str(committee), "--universe", "hall-upkeep"
    )
    assert code == 0, err
    nested = json.loads(out)
    assert nested["layers"]["guidance"]["forUniverse"] == "hall-upkeep"
    assert nested["layers"]["marks"]["forUniverse"] == "hall-upkeep"
    code, out, err = run(capsys, "--inspect", str(hall), "--universe", "hall-upkeep")
    assert code == 0, err
    assert nested == json.loads(out)
    code, out, err = run(
        capsys,
        "--explore",
        str(committee),
        "--universe",
        "hall-upkeep",
        "--output",
        str(tmp_path / "out.html"),
    )
    assert code == 0, err
    assert (tmp_path / "out.html").exists()


def test_a_universe_spec_file_target_reads_workspace(capsys, tmp_path):
    scope = case(tmp_path, "misnamed") / "committee" / ".knowledge-bus"
    target = str(scope / "committee-minutes.universe.kbp.yaml")
    for args in (
        ["--inspect", target],
        ["--kinds", target],
        ["--card", "minutes", target],
    ):
        code, out, err = run(capsys, *args)
        assert F5 in said(code, out, err)


def test_card_matches_the_card_printed_in_the_parent_folder(capsys, tmp_path):
    hall = case(tmp_path, "upkeep")
    write_parent_guidance(hall)
    for fmt in ("json", "markdown"):
        cards = [
            run(
                capsys,
                "--card",
                "hirer-checklist",
                str(folder),
                "--universe",
                "hall-upkeep",
                "--format",
                fmt,
            )
            for folder in (hall / "committee", hall)
        ]
        assert cards[0][0] == 0, cards[0][2]
        assert cards[0] == cards[1]
        if fmt == "json":
            claims = [note["claim"] for note in json.loads(cards[0][1])["guidance"]]
            assert claims == ["Name the caretaker on the rota."]


def test_card_without_universe_lists_the_candidates_and_from_parent(capsys, tmp_path):
    committee = case(tmp_path, "upkeep") / "committee"
    code, out, err = run(capsys, "--card", "hirer-checklist", str(committee))
    assert code == 1
    assert out == ""
    error = error_of(err)
    assert error["message"] == (
        "Multiple universes require an explicit universe id or file"
    )
    assert error["candidates"] == ["committee-minutes", "hall-upkeep"]
    assert error["from_parent"] == ["hall-upkeep"]


def test_kinds_lists_each_universe_spec_separately(capsys, tmp_path):
    committee = case(tmp_path, "upkeep") / "committee"
    code, out, err = run(capsys, "--kinds", str(committee))
    assert code == 0, err
    listing = json.loads(out)
    assert listing["schema"] == "knowledge-bus/kinds-set/1"
    assert listing["from_parent"] == ["hall-upkeep"]
    assert [group["schema"] for group in listing["universe_specs"]] == [
        "knowledge-bus/kinds/1",
        "knowledge-bus/kinds/1",
    ]
    assert [group["universe_spec"]["id"] for group in listing["universe_specs"]] == [
        "committee-minutes",
        "hall-upkeep",
    ]
    code, out, err = run(capsys, "--kinds", str(committee), "--format", "markdown")
    assert code == 0, err
    assert (
        "## Hall upkeep universe spec (hall-upkeep 0.1), from the parent folder"
        in out.splitlines()
    )
    assert "## Committee minutes universe spec (committee-minutes 0.1)" in (
        out.splitlines()
    )
    code, out, err = run(capsys, "--kinds", str(committee), "--universe", "hall-upkeep")
    assert code == 0, err
    assert json.loads(out)["schema"] == "knowledge-bus/kinds/1"
    assert "from_parent" not in json.loads(out)


def test_mint_reads_the_named_universe_specs(capsys, tmp_path):
    hall = case(tmp_path, "upkeep")
    committee = hall / "committee"
    documents = cli.resolve([str(committee)])[1]
    assert [Path(path).name for path in documents] == [
        "committee-minutes.universe.kbp.yaml",
        "hall-upkeep.universe.kbp.yaml",
    ]
    code, out, _ = run(capsys, "--mint", "element", "2", str(committee))
    assert code == 0, out
    assert len(out.split()) == 2


# Refusals; explicit file targets and plain-folder scans.


def test_nested_guidance_for_a_named_universe_spec_is_refused_by_every_command(
    capsys, tmp_path
):
    committee = case(tmp_path, "nested-guidance") / "committee"
    code, out, _ = run(capsys, str(committee))
    assert code == 1
    assert "upkeep.type-guidance.kbp.yaml: NON-CONFORMING" in out
    assert (
        "  FAIL  guides 'hall-upkeep', a universe spec from the parent folder; "
        "move the guidance to the parent folder"
    ) in out.splitlines()
    for args in (
        ["--kinds", str(committee)],
        ["--card", "minutes", str(committee), "--universe", "committee-minutes"],
        ["--card", "hirer-checklist", str(committee), "--universe", "hall-upkeep"],
        ["--inspect", str(committee), "--universe", "committee-minutes"],
    ):
        code, out, err = run(capsys, *args)
        assert code == 1
        error = error_of(err)
        assert error["category"] == "conformance"
        assert error["message"].startswith("upkeep.type-guidance.kbp.yaml: ")
        assert F7 in error["message"]


def test_nested_marks_for_a_named_universe_spec_block_only_inspect_and_explore(
    capsys, tmp_path
):
    committee = case(tmp_path, "nested-marks") / "committee"
    code, _, err = run(capsys, "--inspect", str(committee), "--universe", "hall-upkeep")
    assert code == 1
    assert F7 in error_of(err)["message"]
    assert run(capsys, str(committee))[0] == 0
    assert run(capsys, "--kinds", str(committee))[0] == 0
    args = ["--card", "hirer-checklist", str(committee), "--universe", "hall-upkeep"]
    assert run(capsys, *args)[0] == 0


def test_a_nested_universe_spec_may_reuse_an_unnamed_parent_id(capsys, tmp_path):
    hall = case(tmp_path, "upkeep")
    shutil.copyfile(
        hall / ".knowledge-bus" / "hall-bookings.universe.kbp.yaml",
        hall / "committee" / ".knowledge-bus" / "hall-bookings.universe.kbp.yaml",
    )
    code, out, _ = run(capsys, str(hall / "committee"))
    assert code == 0, out


def test_a_parent_check_never_reads_nested_folders(capsys, tmp_path):
    hall = case(tmp_path, "misnamed")
    code, out, _ = run(capsys, str(hall))
    assert code == 0, out
    assert "workspace.yaml" not in out
    assert "committee-minutes" not in out


def test_explicit_file_targets_and_plain_folder_scans_skip_workspace(capsys, tmp_path):
    hall = case(tmp_path, "misnamed")
    target = str(
        hall / "committee" / ".knowledge-bus" / "committee-minutes.universe.kbp.yaml"
    )
    code, out, _ = run(capsys, target)
    assert code == 0, out
    assert "workspace.yaml" not in out
    code, out, _ = run(capsys, "--mint", "element", "1", target)
    assert code == 0, out
    code, out, _ = run(capsys, str(hall.parent))
    assert code == 1
    assert "workspace.yaml" not in out
    assert "no documents to check" in out


# An explicit workspace.yaml target.


def workspace_block(out):
    """The lines of the `=== workspace.yaml ===` block in check output."""
    lines = out.splitlines()
    start = lines.index(f"=== {workspace.FILE} ===")
    end = next(
        (
            index
            for index in range(start + 1, len(lines))
            if lines[index].startswith("=== ")
        ),
        len(lines),
    )
    return lines[start:end]


@pytest.mark.parametrize(
    "name", sorted(path.name for path in CASES.iterdir() if path.is_dir())
)
def test_check_prints_the_same_workspace_block_for_an_explicit_workspace_target_as_for_its_folder(
    capsys, tmp_path, name
):
    scope = checked_folder(case(tmp_path, name)) / ".knowledge-bus"
    _, folder_out, _ = run(capsys, str(scope))
    expected = workspace_block(folder_out)
    code, out, _ = run(capsys, str(scope / workspace.FILE))
    assert workspace_block(out) == expected
    assert "document type unknown" not in out
    conforms = f"{workspace.FILE}: CONFORMS" in expected
    assert code == (0 if conforms else 1), out


def test_mint_checks_an_explicit_workspace_target(capsys, tmp_path):
    good = case(tmp_path, "upkeep") / "committee" / ".knowledge-bus" / workspace.FILE
    code, out, _ = run(capsys, "--mint", "element", "1", str(good))
    assert code == 0, out
    assert out.startswith("e")
    bad = case(tmp_path, "misnamed") / "committee" / ".knowledge-bus" / workspace.FILE
    code, out, _ = run(capsys, "--mint", "element", "1", str(bad))
    assert code == 1
    assert F5 in out


def test_check_reads_no_parent_file_for_a_universe_spec_file_and_a_workspace_target(
    capsys, tmp_path
):
    scope = case(tmp_path, "upkeep") / "committee" / ".knowledge-bus"
    code, out, _ = run(
        capsys,
        str(scope / "committee-minutes.universe.kbp.yaml"),
        str(scope / workspace.FILE),
    )
    assert code == 0, out
    blocks = [line for line in out.splitlines() if line.startswith("=== ")]
    assert blocks[1:] == [
        "=== workspace.yaml ===",
        "=== committee-minutes.universe.kbp.yaml against kbp/0.8 ===",
    ]


def test_check_reads_the_parent_folder_for_a_folder_target_beside_its_workspace_target(
    capsys, tmp_path
):
    committee = case(tmp_path, "upkeep") / "committee"
    target = str(committee / ".knowledge-bus" / workspace.FILE)
    _, expected, _ = run(capsys, str(committee))
    code, out, _ = run(capsys, target, str(committee))
    assert code == 0, out
    assert out == expected


@pytest.mark.parametrize("name", ["upkeep", "misnamed", "not-yaml"])
def test_read_commands_refuse_a_workspace_target_like_a_marks_target(
    capsys, tmp_path, name
):
    marks = (
        case(tmp_path, "nested-marks")
        / "committee"
        / ".knowledge-bus"
        / "upkeep.marks.explorer.yaml"
    )
    target = case(tmp_path, name) / "committee" / ".knowledge-bus" / workspace.FILE
    for args in (
        ["--card", "minutes"],
        ["--kinds"],
        ["--inspect"],
        ["--explore", "--output", str(tmp_path / "out.html")],
    ):
        expected = run(capsys, *args, str(marks))
        assert run(capsys, *args, str(target)) == expected, args
        assert error_of(expected[2])["message"] == (
            "No universe definitions in the selected scope"
        )
    assert not (tmp_path / "out.html").exists()


def test_read_commands_skip_a_workspace_target_beside_a_universe_spec_file(
    capsys, tmp_path
):
    scope = case(tmp_path, "misnamed") / "committee" / ".knowledge-bus"
    targets = [
        str(scope / "committee-minutes.universe.kbp.yaml"),
        str(scope / workspace.FILE),
    ]
    code, out, err = run(capsys, "--kinds", *targets)
    assert code == 0, err
    assert json.loads(out)["universe_spec"]["id"] == "committee-minutes"
    code, out, err = run(capsys, "--inspect", *targets)
    assert code == 0, err
    assert json.loads(out)["layers"]["universe"]["id"] == "committee-minutes"


def test_an_explicit_workspace_target_that_is_not_utf8_is_refused(capsys, tmp_path):
    target = case(tmp_path, "upkeep") / "committee" / ".knowledge-bus" / workspace.FILE
    target.write_bytes(b"from_parent: [\xff\xfe]\n")
    for args in ([], ["--mint", "element", "1"]):
        code, out, _ = run(capsys, *args, str(target))
        assert code == 1
        assert F1 in out and "codec can't decode" in out, (args, out)
    code, out, err = run(capsys, "--kinds", str(target))
    assert code == 1
    assert error_of(err)["message"] == "No universe definitions in the selected scope"


def test_an_unreadable_parent_file_is_named_with_the_parent_folder(capsys, tmp_path):
    committee = case(tmp_path, "unreadable-parent") / "committee"
    code, out, _ = run(capsys, str(committee))
    assert code == 1
    assert (
        "  FAIL  Cannot parse broken.universe.kbp.yaml in the parent folder "
        "../.knowledge-bus/: "
    ) in out
    code, out, err = run(capsys, "--kinds", str(committee))
    assert code == 1
    assert error_of(err)["message"].startswith(
        "Cannot parse broken.universe.kbp.yaml in the parent folder ../.knowledge-bus/: "
    )


def test_guidance_and_marks_for_an_unlisted_parent_universe_spec_stay_out(
    capsys, tmp_path
):
    hall = case(tmp_path, "upkeep")
    parent = hall / ".knowledge-bus"
    (parent / "bookings.type-guidance.kbp.yaml").write_text(
        "guidance:\n"
        "  id: hall-bookings-guidance\n"
        "  label: Note on hall bookings\n"
        "  version: 0.1\n"
        "  conforms_to: kbp/0.8\n"
        "  guides: hall-bookings\n"
        "\n"
        "guidance_kinds:\n"
        "  - { id: heuristic, sourced: false }\n"
        "\n"
        "artifacts:\n"
        "  booking-form:\n"
        "    - kind: heuristic\n"
        "      claim: Confirm the date in writing.\n"
        "      source: asserted\n"
    )
    (parent / "bookings.marks.explorer.yaml").write_text(
        "marks:\n"
        "  id: hall-bookings-marks\n"
        "  version: 0.1\n"
        "  marks_for: hall-bookings\n"
        "\n"
        "frames:\n"
        "  booking-stage: { monogram: BS }\n"
    )
    code, out, err = run(capsys, "--inspect", str(hall), "--universe", "hall-bookings")
    assert code == 0, err
    committee = hall / "committee"
    for args in (
        [str(committee)],
        ["--kinds", str(committee)],
        ["--card", "hirer-checklist", str(committee), "--universe", "hall-upkeep"],
        ["--inspect", str(committee), "--universe", "hall-upkeep"],
    ):
        code, out, err = run(capsys, *args)
        assert code == 0, (args, out, err)
        assert "hall-bookings" not in out + err, args
        assert "bookings." not in out + err, args


def test_an_unreadable_parent_marks_file_blocks_only_inspect_and_explore(
    capsys, tmp_path
):
    hall = case(tmp_path, "upkeep")
    (hall / ".knowledge-bus" / "broken.marks.explorer.yaml").write_text(
        "marks: [broken\n"
    )
    committee = hall / "committee"
    for args in (
        ["--inspect", str(committee), "--universe", "hall-upkeep"],
        [
            "--explore",
            str(committee),
            "--universe",
            "hall-upkeep",
            "--output",
            str(tmp_path / "out.html"),
        ],
    ):
        code, out, err = run(capsys, *args)
        assert F8 in said(code, out, err), args
    assert not (tmp_path / "out.html").exists()
    for args in (
        [str(committee)],
        ["--kinds", str(committee)],
        ["--card", "hirer-checklist", str(committee), "--universe", "hall-upkeep"],
    ):
        code, out, err = run(capsys, *args)
        assert code == 0, (args, out, err)


@pytest.mark.parametrize(
    ("where", "fragment"),
    [
        ("committee/.knowledge-bus/workspace.yaml", F1),
        (".knowledge-bus/z.kbp.yaml", F8),
    ],
)
def test_a_file_that_is_not_utf8_is_refused(capsys, tmp_path, where, fragment):
    hall = case(tmp_path, "upkeep")
    (hall / where).write_bytes(b"from_parent: [\xff\xfe]\n")
    for each in EVERY:
        text = said(*run(capsys, *command(each, hall / "committee", tmp_path)))
        assert fragment in text, (each, text)
        assert "codec can't decode" in text, (each, text)
    assert not (tmp_path / "out.html").exists()


def test_a_folder_holding_only_workspace_checks_the_named_universe_specs(
    capsys, tmp_path
):
    committee = case(tmp_path, "workspace-only") / "committee"
    code, out, _ = run(capsys, str(committee))
    assert code == 0, out
    assert "hall-upkeep.universe.kbp.yaml: CONFORMS" in out


def test_misnamed_lists_the_parent_folders_ids(capsys, tmp_path):
    committee = case(tmp_path, "misnamed") / "committee"
    code, out, _ = run(capsys, str(committee))
    assert code == 1
    assert (
        "  FAIL  workspace.yaml: from_parent names 'hall-upkeepz', which the parent "
        "folder does not declare; the parent folder declares "
        "['hall-bookings', 'hall-upkeep']"
    ) in out.splitlines()
    code, out, err = run(capsys, "--kinds", str(committee))
    assert error_of(err)["candidates"] == ["hall-bookings", "hall-upkeep"]


@pytest.mark.parametrize(
    ("document", "own", "parent", "fragment"),
    [
        (None, [], ["a"], F1),
        (["a"], [], ["a"], F1),
        ({"from_parent": ["a"], "version": 1}, [], ["a"], F2),
        ({"from_parent": "a"}, [], ["a"], F3),
        ({"from_parent": [""]}, [], ["a"], F3),
        ({"from_parent": ["a", "a"]}, [], ["a"], F3),
        ({"from_parent": [7]}, [], ["a"], F3),
        ({"from_parent": ["a"]}, [], None, F4),
        ({"from_parent": ["b"]}, [], ["a"], F5),
        ({"from_parent": ["a"]}, ["a"], ["a"], F6),
    ],
)
def test_problem_names_the_first_refusal(document, own, parent, fragment):
    message, _ = workspace.problem(document, own, parent)
    assert fragment in message


@pytest.mark.parametrize(
    "document",
    [{}, {"from_parent": []}, {"from_parent": ["a"]}],
)
def test_problem_accepts_a_conforming_file(document):
    assert workspace.problem(document, ["own"], ["a"]) is None


# One test per folder refusal (F1 to F8): each folder case fails for exactly one refusal.


@pytest.mark.parametrize("name", list(REFUSALS))
def test_each_folder_case_fails_for_exactly_one_refusal(capsys, tmp_path, name):
    fragment, commands = REFUSALS[name]
    folder = checked_folder(case(tmp_path, name))
    for each in commands:
        text = said(*run(capsys, *command(each, folder, tmp_path)))
        assert fragment in text, (each, text)
        others = [f for f in FRAGMENTS if f != fragment and f in text]
        assert not others, (each, text)
    assert not (tmp_path / "out.html").exists()


def test_every_folder_refusal_has_a_folder_case():
    assert sorted({fragment for fragment, _ in REFUSALS.values()}) == sorted(FRAGMENTS)
    folders = sorted(path.name for path in CASES.iterdir() if path.is_dir())
    passing = {"upkeep", "workspace-only", "names-nothing"}
    assert folders == sorted({*REFUSALS, *passing})


def refusal_rows(path, heading):
    """The table under `heading` in `path`: {fragment: folder cases}."""
    lines = path.read_text(encoding="utf-8").splitlines()
    start = lines.index(heading)
    rows = {}
    for line in lines[start + 1 :]:
        if line.startswith("#"):
            break
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not line.startswith("|") or not cells[0].startswith("`"):
            continue
        folders = cells[1] if "kb-check" in str(path) else cells[2]
        rows[cells[0].strip("`")] = sorted(
            name.strip().strip("`") for name in folders.split(",")
        )
    return rows


@pytest.mark.parametrize(
    ("path", "heading"),
    [
        (ROOT / "docs" / "knowledge-bus-directory.md", "### Refusals"),
        (ROOT / "skills" / "kb-check" / "SKILL.md", "## Folder refusals"),
    ],
    ids=["directory-doc", "kb-check"],
)
def test_the_refusal_tables_match_the_folder_cases(path, heading):
    expected = {
        fragment: sorted(
            name for name, (each, _) in REFUSALS.items() if each == fragment
        )
        for fragment in FRAGMENTS
    }
    assert refusal_rows(path, heading) == expected
