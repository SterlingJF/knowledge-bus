"""Which universe specs cover a file: the shared cases, `kbp --cover`, and what it changes.

checker/tests/cover/cases.json holds the cases. Each runs through cover.py and
through `kbp --cover` on folders built from the case files. docs/universe-spec-coverage.md
describes the rule.
"""

import ast
import builtins
import io
import json
import shutil
import sys
from pathlib import Path

import pytest
import yaml

from kbp_conform import cli

ROOT = Path(__file__).resolve().parents[2]
COVER = Path(__file__).resolve().parent / "cover"
CASES = json.loads((COVER / "cases.json").read_text(encoding="utf-8"))["cases"]
CARDS = Path(__file__).resolve().parent / "cards" / "product-development"
COVER_SOURCE = ROOT / "checker/src/kbp_conform/cover.py"
PRESET = "universes/product-development/universe.kbp.yaml"
HALL = ROOT / "evals/fixtures/village-hall/.knowledge-bus"
ERROR_SCHEMA = "knowledge-bus/inspection-error/1"
IDS = [case["name"] for case in CASES]


def load(repo_path):
    return yaml.safe_load((ROOT / repo_path).read_text(encoding="utf-8"))


def rule_inputs(case):
    """Load a case's files. A folder without coverage.yaml has no "coverage" key."""
    folders = [
        {
            "at": folder["at"],
            "universe_specs": [load(path) for path in folder["universe_specs"]],
            **({"coverage": load(folder["coverage"])} if folder["coverage"] else {}),
        }
        for folder in case["knowledge_bus"]
    ]
    presets = [load(path) for path in case["presets"]]
    return folders, presets


def expected_error(case):
    return {"schema": ERROR_SCHEMA, "status": "error", **case["error"]}


def apply_rule(case, folders, presets):
    from kbp_conform import cover

    try:
        return cover.cover(
            case["file"],
            folders,
            presets,
            top=case["top"],
            document_type=case["document_type"],
            no_fit=case["no_fit"],
            hat=case["hat"],
        )
    except cover.CoverError as error:
        return error.as_dict()


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_cover_py_gives_the_expected_answer(case):
    answer = apply_rule(case, *rule_inputs(case))
    assert answer == (expected_error(case) if "error" in case else case["expected"])


def within_top(case, at):
    top = case["top"]
    return not top or at == top or at.startswith(top + "/")


def build(case, root):
    """Lay out each .knowledge-bus/ at or below the case's top folder.

    `kbp` searches to the top of the disk, so a folder above the case's top is left out.
    """
    for folder in case["knowledge_bus"]:
        if not within_top(case, folder["at"]):
            continue
        scope = root / folder["at"] / ".knowledge-bus"
        scope.mkdir(parents=True, exist_ok=True)
        for path in folder["universe_specs"]:
            shutil.copyfile(ROOT / path, scope / Path(path).name)
        if folder["coverage"]:
            shutil.copyfile(ROOT / folder["coverage"], scope / "coverage.yaml")
    return root / case["file"]


def cover_args(case, file):
    args = ["--cover", str(file)]
    if case["document_type"]:
        args += ["--type", case["document_type"]]
    if case["no_fit"]:
        args.append("--no-fit")
    if case["hat"]:
        args += ["--hat", case["hat"]]
    return args


def run(capsys, *args):
    code = cli.main(list(args))
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def kbp_answer(capsys, case, file):
    code, out, err = run(capsys, *cover_args(case, file))
    if code == 0:
        assert err == ""
        return json.loads(out)
    assert code == 1
    assert out == ""
    return json.loads(err)


@pytest.fixture
def elsewhere(tmp_path, monkeypatch):
    """Run from a folder with no .knowledge-bus/ above it."""
    folder = tmp_path / "elsewhere"
    folder.mkdir()
    monkeypatch.chdir(folder)
    return folder


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_kbp_cover_gives_the_expected_answer(capsys, tmp_path, elsewhere, case):
    assert case["presets"] == [PRESET], "kbp carries product-development as its preset"
    file = build(case, tmp_path / "work")
    answer = kbp_answer(capsys, case, file)
    assert answer == (expected_error(case) if "error" in case else case["expected"])


ABOUT = json.loads((COVER / "cases.json").read_text(encoding="utf-8"))["about"]
DOC = (ROOT / "docs/universe-spec-coverage.md").read_text(encoding="utf-8")
COMPARED = "for each expected error the same category and candidates"
ERROR_CASES = [case for case in CASES if "error" in case]


def matches_like_other_code(answer, case):
    """Other code is compared on an answer by value, and on an error by category and candidates only."""
    if "error" not in case:
        return answer == case["expected"]
    return (
        answer.get("status") == "error"
        and answer.get("category") == case["error"]["category"]
        and answer.get("candidates") == case["error"].get("candidates")
    )


def test_other_code_is_compared_on_category_and_candidates_not_message():
    assert COMPARED in ABOUT
    assert "kbp's wording, for reference" in ABOUT
    other_code = DOC.split("## Checking Other Code", 1)[1]
    assert COMPARED in other_code
    assert "need not match" in other_code
    assert ERROR_CASES
    for case in ERROR_CASES:
        error = case["error"]
        assert error["category"] in {"selection", "conformance"}, case["name"]
        assert error["message"], case["name"]
        assert "candidates" not in error or error["candidates"], case["name"]
        kbp = expected_error(case)
        assert matches_like_other_code(kbp, case)
        assert matches_like_other_code({**kbp, "message": "Reworded."}, case)
        assert not matches_like_other_code({**kbp, "category": "other"}, case)
        assert not matches_like_other_code({**kbp, "candidates": ["other"]}, case)
        if "candidates" in error:
            dropped = {key: value for key, value in kbp.items() if key != "candidates"}
            assert not matches_like_other_code(dropped, case)
    answer = next(case for case in CASES if "expected" in case)
    assert matches_like_other_code(answer["expected"], answer)
    assert not matches_like_other_code({**answer["expected"], "settled": None}, answer)


def test_an_existing_file_is_covered_as_a_new_one(capsys, tmp_path, elsewhere):
    case = next(case for case in CASES if case["file"] == "committee/minutes.md")
    file = build(case, tmp_path / "work")
    before = kbp_answer(capsys, case, file)
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text("Minutes.\n")
    assert kbp_answer(capsys, case, file) == before


def test_folder_names_starting_or_ending_with_a_dot(capsys, tmp_path, elsewhere):
    case = next(case for case in CASES if case["file"] == "committee/minutes.md")
    file = build(case, tmp_path / ".vault" / "hall.")
    assert kbp_answer(capsys, case, file) == case["expected"]


SETTLED_IN_A_FOLDER = [
    case
    for case in CASES
    if "expected" in case and case["expected"]["source"] == "folder"
]


@pytest.mark.parametrize(
    "case", SETTLED_IN_A_FOLDER, ids=[case["name"] for case in SETTLED_IN_A_FOLDER]
)
def test_kinds_and_card_given_knowledge_bus_dir_reach_the_same_universe_specs(
    capsys, tmp_path, elsewhere, case
):
    file = build(case, tmp_path / "work")
    answer = kbp_answer(capsys, case, file)
    target = str(file.parent / answer["knowledge_bus_dir"])
    for spec in answer["universe_specs"]:
        code, out, err = run(capsys, "--kinds", target, "--universe", spec["id"])
        assert code == 0, err
        assert json.loads(out)["universe_spec"]["id"] == spec["id"]
        if case["document_type"]:
            code, out, err = run(
                capsys,
                "--card",
                case["document_type"],
                target,
                "--universe",
                spec["id"],
            )
            assert code == 0, err
            card = json.loads(out)
            assert card["kind"] == case["document_type"]
            assert card["universe_spec"]["id"] == spec["id"]


def nested(tmp_path, coverage=None):
    root = tmp_path / "hall"
    shutil.copytree(HALL, root / ".knowledge-bus")
    scope = root / "committee" / ".knowledge-bus"
    scope.mkdir(parents=True)
    if coverage:
        shutil.copyfile(COVER / coverage, scope / "coverage.yaml")
    return root, scope


def test_a_nested_folder_naming_its_parents_universe_spec(capsys, tmp_path, elsewhere):
    _, scope = nested(tmp_path, "from-parent-upkeep.coverage.yaml")
    code, out, err = run(capsys, "--kinds", str(scope))
    assert code == 0, err
    assert json.loads(out)["universe_spec"]["id"] == "hall-upkeep"
    code, out, err = run(capsys, "--card", "hirer-checklist", str(scope.parent))
    assert code == 0, err
    assert json.loads(out)["universe_spec"]["id"] == "hall-upkeep"
    code, out, err = run(capsys, "--card", "booking-form", str(scope))
    assert code == 1
    assert json.loads(err)["candidates"] == ["hirer-checklist"]


def test_kinds_found_from_inside_a_nested_folder_sees_named_universe_specs(
    capsys, tmp_path, monkeypatch
):
    _, scope = nested(tmp_path, "from-parent-upkeep.coverage.yaml")
    inside = scope.parent / "2026"
    inside.mkdir()
    monkeypatch.chdir(inside)
    code, out, err = run(capsys, "--kinds")
    assert code == 0, err
    assert json.loads(out)["universe_spec"]["id"] == "hall-upkeep"


def test_a_nested_folder_without_coverage_stands_alone(capsys, tmp_path, elsewhere):
    _, scope = nested(tmp_path)
    for args in (["--kinds", str(scope)], ["--card", "hirer-checklist", str(scope)]):
        code, out, err = run(capsys, *args)
        assert code == 1
        assert out == ""
        assert json.loads(err)["message"] == (
            "No Knowledge Bus definitions in the selected scope"
        )
    assert cli.main([str(scope)]) == 1
    assert "no documents to check" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("coverage", "passes", "says"),
    [
        ("from-parent-upkeep.coverage.yaml", True, None),
        ("from-parent-misnamed.coverage.yaml", False, "'hall-bookingz'"),
        ("version-2.coverage.yaml", False, "needs a newer checker"),
        ("unknown-key.coverage.yaml", False, "unknown key 'inherits'"),
    ],
)
def test_a_bare_check_validates_coverage(capsys, tmp_path, coverage, passes, says):
    _, scope = nested(tmp_path, coverage)
    code = cli.main([str(scope)])
    out = capsys.readouterr().out
    assert "=== coverage.yaml ===" in out
    assert code == (0 if passes else 1), out
    if says:
        assert "FAIL" in out and says in out


def test_a_bare_check_of_a_nested_folder_naming_nothing_has_no_documents(
    capsys, tmp_path
):
    _, scope = nested(tmp_path, "version-only.coverage.yaml")
    code = cli.main([str(scope)])
    out = capsys.readouterr().out
    assert code == 1
    assert "no documents to check" in out
    assert "coverage.yaml: CONFORMS" not in out


def broken_parent(tmp_path, coverage=None):
    """A nested folder with its own universe spec, under a parent that cannot be parsed."""
    root = tmp_path / "hall"
    (root / ".knowledge-bus").mkdir(parents=True)
    (root / ".knowledge-bus" / "broken.universe.kbp.yaml").write_text("universe: [\n")
    scope = root / "committee" / ".knowledge-bus"
    scope.mkdir(parents=True)
    shutil.copyfile(
        COVER / "hall-lettings.universe.kbp.yaml",
        scope / "hall-lettings.universe.kbp.yaml",
    )
    if coverage:
        shutil.copyfile(COVER / coverage, scope / "coverage.yaml")
    return scope


@pytest.mark.parametrize("coverage", [None, "version-only.coverage.yaml"])
def test_a_folder_naming_nothing_from_its_parent_never_reads_the_parent(
    capsys, tmp_path, elsewhere, coverage
):
    scope = broken_parent(tmp_path, coverage)
    code, out, err = run(capsys, "--cover", str(scope.parent / "minutes.md"))
    assert code == 0, err
    assert [spec["id"] for spec in json.loads(out)["universe_specs"]] == [
        "hall-lettings"
    ]
    code, out, err = run(capsys, "--kinds", str(scope))
    assert code == 0, err
    assert json.loads(out)["universe_spec"]["id"] == "hall-lettings"
    code, out, _ = run(capsys, str(scope))
    assert code == 0, out


@pytest.mark.parametrize(
    ("coverage", "passes"),
    [("paths.coverage.yaml", True), ("paths-unknown-id.coverage.yaml", False)],
)
def test_a_bare_check_validates_paths(capsys, tmp_path, coverage, passes):
    root = tmp_path / "hall"
    shutil.copytree(HALL, root / ".knowledge-bus")
    shutil.copyfile(COVER / coverage, root / ".knowledge-bus" / "coverage.yaml")
    code = cli.main([str(root)])
    out = capsys.readouterr().out
    assert "hall-bookings.universe.kbp.yaml: CONFORMS" in out
    assert code == (0 if passes else 1), out


def test_inspect_never_reads_coverage(capsys, tmp_path):
    mode = "--inspect"
    root = tmp_path / "hall"
    shutil.copytree(HALL, root / ".knowledge-bus")
    args = [mode, str(root / ".knowledge-bus"), "--universe", "hall-upkeep"]
    without = run(capsys, *args)
    shutil.copyfile(
        COVER / "paths-unknown-id.coverage.yaml",
        root / ".knowledge-bus" / "coverage.yaml",
    )
    assert run(capsys, *args) == without
    assert without[0] == 0
    _, scope = nested(tmp_path / "nested", "from-parent-upkeep.coverage.yaml")
    code, _, err = run(capsys, mode, str(scope))
    assert code == 1
    assert json.loads(err)["message"] == (
        "No Knowledge Bus definitions in the selected scope"
    )


@pytest.mark.parametrize("fmt", ["json", "markdown"])
def test_card_and_kinds_with_no_knowledge_bus_dir_use_the_preset(
    capsys, elsewhere, fmt
):
    suffix = ".json" if fmt == "json" else ".md"
    extra = [] if fmt == "json" else ["--format", "markdown"]
    for args, expected in (
        (["--card", "decision-record"], CARDS / f"decision-record{suffix}"),
        (["--kinds"], CARDS / f"kinds{suffix}"),
    ):
        code, out, err = run(capsys, *args, *extra)
        assert code == 0, err
        text = expected.read_text(encoding="utf-8")
        if fmt == "json":
            assert json.loads(out) == json.loads(text)
        else:
            assert out == text


def test_a_bare_check_with_no_knowledge_bus_dir_is_unchanged(capsys, elsewhere):
    assert cli.main([]) == 1
    assert "no .knowledge-bus/ found" in capsys.readouterr().out


def snapshot(path):
    return {
        p.relative_to(path).as_posix(): p.read_bytes()
        for p in path.rglob("*")
        if p.is_file()
    }


def test_cover_is_read_only_repeatable_and_names_no_paths(capsys, tmp_path, elsewhere):
    for index, case in enumerate(CASES):
        file = build(case, tmp_path / "work" / str(index))
        before = snapshot(tmp_path / "work")
        first = run(capsys, *cover_args(case, file))
        second = run(capsys, *cover_args(case, file))
        assert first == second
        assert str(tmp_path) not in first[1] + first[2]
        assert str(ROOT) not in first[1] + first[2]
        assert snapshot(tmp_path / "work") == before


@pytest.mark.parametrize(
    "args",
    [
        ["--cover"],
        ["--cover", "a.md", "b.md"],
        ["--cover", "a.md", "--type"],
        ["--cover", "a.md", "--hat"],
        ["--cover", "a.md", "--no-fit", "--no-fit"],
        ["--cover", "a.md", "--universe", "x"],
        ["--cover", "a.md", "--hat", "--"],
        ["--cover", "a.md", "--hat", "!!"],
    ],
)
def test_bad_cover_options_are_refused_as_json(capsys, elsewhere, args):
    code, out, err = run(capsys, *args)
    assert code == 1
    assert out == ""
    error = json.loads(err)
    assert error["schema"] == ERROR_SCHEMA
    assert error["category"] == "selection"


def test_cover_refuses_a_folder_and_a_file_inside_knowledge_bus(
    capsys, tmp_path, elsewhere
):
    root = tmp_path / "hall"
    shutil.copytree(HALL, root / ".knowledge-bus")
    for target in (root, root / ".knowledge-bus" / "notes.md"):
        code, out, err = run(capsys, "--cover", str(target))
        assert code == 1
        assert out == ""
        assert json.loads(err)["category"] == "selection"


def test_cover_code_takes_loaded_data_and_uses_the_standard_library_only(monkeypatch):
    from kbp_conform import cover

    tree = ast.parse(COVER_SOURCE.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0, "cover.py imports nothing from the package"
            imported.add(node.module.split(".")[0])
    assert imported <= sys.stdlib_module_names
    functions = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }
    assert not {"check", "check_guidance"} & functions

    loaded = [(case, rule_inputs(case)) for case in CASES]

    def refuse(*args, **kwargs):
        raise AssertionError("cover code opened a file")

    monkeypatch.setattr(builtins, "open", refuse)
    monkeypatch.setattr(io, "open", refuse)
    monkeypatch.setattr(Path, "open", refuse)
    monkeypatch.setattr(Path, "read_text", refuse)
    monkeypatch.setattr(Path, "read_bytes", refuse)
    for case, (folders, presets) in loaded:
        answer = apply_rule(case, folders, presets)
        assert answer == (expected_error(case) if "error" in case else case["expected"])
    assert cover.__name__ == "kbp_conform.cover"
