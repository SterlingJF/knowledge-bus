"""Document type card contracts: expected cards, open conditions, refusals.

The expected cards in checker/tests/cards/ are written by `kbp --card` and
`kbp --kinds`. After an intended change to the card or to a universe spec,
rewrite them and review the diff:

    KBP_WRITE_CARDS=1 uv run --locked pytest checker/tests/test_card.py
"""

import ast
import builtins
import io
import json
import os
import re
import shutil
import sys
from pathlib import Path

import pytest
import yaml

from kbp_conform import cli

ROOT = Path(__file__).resolve().parents[2]
CARDS = Path(__file__).resolve().parent / "cards"
FIXTURE = Path(__file__).resolve().parent / "card-fixture"
REFERENCE = ROOT / "universes/product-development"
MINIMAL = ROOT / "protocol/conformance/pass/minimal.kbp.yaml"
CARD_SOURCE = ROOT / "checker/src/kbp_conform/card.py"
WRITE = os.environ.get("KBP_WRITE_CARDS") == "1"

SETS = {
    "product-development": REFERENCE / "universe.kbp.yaml",
    "card-fixture": FIXTURE / "universe.kbp.yaml",
    "minimal": MINIMAL,
}
SUFFIX = {"json": ".json", "markdown": ".md"}
CONDITION_LINE = re.compile(
    r"^(- Not used when |- No document needed when |Required when |"
    r"When applicable, available when |Applies only when |- [^:]+, when )"
)


def kind_ids(universe_path):
    document = yaml.safe_load(universe_path.read_text(encoding="utf-8"))
    return [artifact["id"] for artifact in document["artifacts"]]


CASES = [(name, kind) for name, path in SETS.items() for kind in kind_ids(path)]


@pytest.fixture(scope="module")
def targets(tmp_path_factory):
    """The minimal universe spec sits beside other test files, so copy it alone."""
    scope = tmp_path_factory.mktemp("minimal") / ".knowledge-bus"
    scope.mkdir()
    shutil.copy(MINIMAL, scope / MINIMAL.name)
    return {**SETS, "minimal": scope / MINIMAL.name}


def run(capsys, *args):
    code = cli.main(list(args))
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def card_output(capsys, target, kind, fmt):
    args = ["--card", kind, str(target)]
    if fmt == "markdown":
        args += ["--format", "markdown"]
    code, out, err = run(capsys, *args)
    assert code == 0, err
    assert err == ""
    return out


def kinds_output(capsys, target, fmt):
    args = ["--kinds", str(target)]
    if fmt == "markdown":
        args += ["--format", "markdown"]
    code, out, err = run(capsys, *args)
    assert code == 0, err
    assert err == ""
    return out


def compare_or_write(path, out, fmt):
    if fmt == "json":
        value = json.loads(out)
        text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    else:
        text = out
    if WRITE:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    assert path.is_file(), f"no expected card {path.name}; see this module's docstring"
    expected = path.read_text(encoding="utf-8")
    hint = "card differs from its expected card; see this module's docstring"
    if fmt == "json":
        assert json.loads(out) == json.loads(expected), hint
    else:
        assert out == expected, hint


@pytest.mark.parametrize("fmt", ["json", "markdown"])
@pytest.mark.parametrize(("name", "kind"), CASES)
def test_card_matches_its_expected_card(capsys, targets, name, kind, fmt):
    """Every document type's card, JSON and readable, matches the card under review."""
    out = card_output(capsys, targets[name], kind, fmt)
    compare_or_write(CARDS / name / f"{kind}{SUFFIX[fmt]}", out, fmt)


@pytest.mark.parametrize("fmt", ["json", "markdown"])
@pytest.mark.parametrize("name", list(SETS))
def test_kinds_matches_its_expected_list(capsys, targets, name, fmt):
    out = kinds_output(capsys, targets[name], fmt)
    compare_or_write(CARDS / name / f"kinds{SUFFIX[fmt]}", out, fmt)


def test_every_product_development_kind_has_expected_cards():
    kinds = kind_ids(SETS["product-development"])
    assert len(kinds) == 19
    for kind in kinds:
        for suffix in SUFFIX.values():
            assert (CARDS / "product-development" / f"{kind}{suffix}").is_file()


def test_no_stale_expected_cards():
    """Every expected card belongs to a document type the universe spec still declares."""
    for name, path in SETS.items():
        wanted = {
            f"{stem}{suffix}"
            for stem in [*kind_ids(path), "kinds"]
            for suffix in SUFFIX.values()
        }
        present = {p.name for p in (CARDS / name).iterdir()}
        assert present == wanted, name


def named_ids(predicate):
    return list((predicate or {}).keys())


def predicates(card):
    yield card["disabled_when"]
    yield card["no_artifact"]
    for entry in card["guidance"] or []:
        yield entry["when"]
    for section in card["sections"]:
        yield section["when"]
        yield section["gate"]
        for entry in section["guidance"] or []:
            yield entry["when"]


def keys_anywhere(value):
    if isinstance(value, dict):
        for key, held in value.items():
            yield key
            yield from keys_anywhere(held)
    elif isinstance(value, list):
        for held in value:
            yield from keys_anywhere(held)


@pytest.mark.parametrize(("name", "kind"), CASES)
def test_every_condition_reads_depends_on(capsys, targets, name, kind):
    """The card states conditions with their questions and never decides them."""
    card = json.loads(card_output(capsys, targets[name], kind, "json"))
    readable = card_output(capsys, targets[name], kind, "markdown")
    condition_lines = [
        line for line in readable.splitlines() if CONDITION_LINE.match(line)
    ]
    for line in condition_lines:
        assert "Depends on: " in line, line
    named = [ids for ids in map(named_ids, predicates(card)) if ids]
    assert len(condition_lines) >= len(named)
    questions = {item["id"]: item["question"] for item in card["conditions"]}
    for ids in named:
        for identity in ids:
            asked = questions[identity] or "not stated in the universe spec"
            assert f"{asked} ({identity})" in readable
    assert not {"result", "evaluation", "status", "context"} & set(keys_anywhere(card))


def fixture_card(capsys, kind, fmt="markdown"):
    out = card_output(capsys, SETS["card-fixture"], kind, fmt)
    return json.loads(out) if fmt == "json" else out


def test_guidance_conditioned_on_a_factor_asks_the_factor_question(capsys):
    readable = fixture_card(capsys, "visit-plan")
    assert (
        "- Heuristic, when familiarity is new: Add directions from the nearest public road. "
        "Depends on: How well does the reader know the site? (familiarity)"
    ) in readable.splitlines()
    card = fixture_card(capsys, "visit-plan", "json")
    familiarity = next(
        item for item in card["conditions"] if item["id"] == "familiarity"
    )
    assert familiarity["question"] == "How well does the reader know the site?"
    assert familiarity["values"] == [
        {
            "value": "new",
            "question": "Is the reader visiting the site for the first time?",
        }
    ]


def test_fixture_covers_the_rarer_card_lines(capsys):
    plan = fixture_card(capsys, "visit-plan").splitlines()
    assert (
        "Required when risk is high; otherwise optional. Depends on: How costly is a mistake on this visit? (risk)"
        in plan
    )
    assert (
        "Applies only when risk is high. Depends on: How costly is a mistake on this visit? (risk)"
        in plan
    )
    assert (
        "When applicable, available when audience is public. Depends on: not stated in the universe spec (audience)"
        in plan
    )
    assert (
        "Kept in another document (Site permit): link to that document. "
        "The notes below are for writing the section in that document." in plan
    )
    assert "Kept in another document: link to that document." in plan
    assert "- risk is high: Could a mistake harm someone or the site?" in plan
    assert not any(line.startswith("- audience is ") for line in plan)

    permit = fixture_card(capsys, "site-permit").splitlines()
    assert (
        "- Its shape is set by an outside authority: County site access permit"
        in permit
    )
    assert (
        "- Not used when audience is team. Depends on: not stated in the universe spec (audience)"
        in permit
    )

    report = fixture_card(capsys, "visit-report")
    assert "Also called" not in report
    assert "outside authority" not in report
    assert "- When it is used: not stated in the universe spec" in report.splitlines()
    assert "## How to write it well" not in report
    assert fixture_card(capsys, "visit-report", "json")["guidance"] == []


def test_card_and_kinds_say_document_type(capsys):
    plan = fixture_card(capsys, "visit-plan").splitlines()
    assert plan[2] == (
        "Document type in the Card fixture universe spec (card-fixture 0.1)."
    )
    assert "## What the conditions mean" in plan
    assert "## What the condition values mean" not in plan
    listing = kinds_output(capsys, SETS["card-fixture"], "markdown").splitlines()
    assert listing[:3] == [
        "# Document types",
        "",
        "In the Card fixture universe spec (card-fixture 0.1).",
    ]


def test_card_leaves_off_sources_codes_and_the_rest_of_the_universe_spec(capsys):
    for kind in kind_ids(SETS["card-fixture"]):
        for fmt in ("json", "markdown"):
            out = card_output(capsys, SETS["card-fixture"], kind, fmt)
            for absent in (
                "Example field handbook",
                "example.org",
                "handbook",
                "acrta",
                "ew374",
                "informs",
                "conjecture",
            ):
                assert absent not in out, (kind, fmt, absent)


def test_card_without_a_guidance_file(capsys, targets):
    target = targets["minimal"]
    card = json.loads(card_output(capsys, target, "the-record", "json"))
    assert card["guidance"] is None
    assert all(section["guidance"] is None for section in card["sections"])
    assert card["enablement"] == {
        "action": "Lets someone state a question and be held to it.",
        "actor": None,
        "timing": None,
    }
    readable = card_output(capsys, target, "the-record", "markdown").splitlines()
    assert "- Helps you: Lets someone state a question and be held to it." in readable
    assert "- Who uses it: not stated in the universe spec" in readable
    assert "- When it is used: not stated in the universe spec" in readable
    assert "- No document needed: in every situation." in readable
    assert "## How to write it well" not in readable


def error_of(err):
    error = json.loads(err)
    assert error["schema"] == "knowledge-bus/inspection-error/1"
    assert error["status"] == "error"
    return error


def test_unknown_kind_lists_every_kind_id(capsys):
    code, out, err = run(
        capsys, "--card", "no-such-kind", str(SETS["product-development"])
    )
    assert code == 1
    assert out == ""
    error = error_of(err)
    assert error["category"] == "selection"
    assert error["candidates"] == sorted(kind_ids(SETS["product-development"]))
    assert error["message"] == (
        "No document type 'no-such-kind' in universe spec 'product-development'"
    )


def test_a_card_without_a_document_type_is_refused(capsys):
    code, out, err = run(capsys, "--card")
    assert code == 1
    assert out == ""
    assert error_of(err)["message"] == "--card requires a document type id"


TARGET = "<target>"


@pytest.mark.parametrize(
    "args",
    [
        ["--card"],
        ["--card", "--format", "markdown"],
        ["--card", "visit-plan", TARGET, "--format", "html"],
        ["--card", "visit-plan", TARGET, "--format"],
        ["--card", "visit-plan", TARGET, "--output", "x"],
        ["--card", "visit-plan", TARGET, "--universe"],
        ["--kinds", TARGET, "--format", "yaml"],
    ],
)
def test_bad_card_options_are_refused_as_json(capsys, args):
    target = str(SETS["card-fixture"])
    code, out, err = run(capsys, *(target if arg == TARGET else arg for arg in args))
    assert code == 1
    assert out == ""
    assert error_of(err)["category"] == "selection"


@pytest.mark.skipif(
    not hasattr(os, "geteuid") or os.geteuid() == 0,
    reason="needs a folder the current user cannot read",
)
def test_an_unreadable_scope_is_refused_as_json(capsys, tmp_path):
    scope = tmp_path / ".knowledge-bus"
    write_scope(scope, "one")
    scope.chmod(0)
    try:
        for args in (["--card", "visit-plan"], ["--kinds"]):
            code, out, err = run(capsys, *args, str(scope))
            assert code == 1
            assert out == ""
            assert error_of(err)["category"] == "selection"
    finally:
        scope.chmod(0o755)


def write_scope(scope, universe_id, *, prefix="", guidance=True, marks=None):
    scope.mkdir(parents=True, exist_ok=True)
    universe = yaml.safe_load((FIXTURE / "universe.kbp.yaml").read_text())
    universe["universe"]["id"] = universe_id
    path = scope / f"{prefix}universe.kbp.yaml"
    path.write_text(yaml.safe_dump(universe, sort_keys=False))
    if guidance:
        document = yaml.safe_load((FIXTURE / "type-guidance.kbp.yaml").read_text())
        document["guidance"]["id"] = f"{universe_id}-guidance"
        document["guidance"]["guides"] = universe_id
        (scope / f"{prefix}type-guidance.kbp.yaml").write_text(
            yaml.safe_dump(document, sort_keys=False)
        )
    if marks is not None:
        (scope / f"{prefix}marks.explorer.yaml").write_text(marks)
    return path


def test_several_universe_specs_need_a_choice(capsys, tmp_path):
    scope = tmp_path / ".knowledge-bus"
    write_scope(scope, "beta", prefix="beta.")
    write_scope(scope, "alpha", prefix="alpha.")
    code, out, err = run(capsys, "--card", "visit-plan", str(scope))
    assert code == 1
    assert out == ""
    assert error_of(err)["candidates"] == ["alpha", "beta"]
    code, out, _ = run(capsys, "--card", "visit-plan", str(scope), "--universe", "beta")
    assert code == 0
    assert json.loads(out)["universe_spec"]["id"] == "beta"
    code, out, _ = run(capsys, "--kinds", str(scope), "--universe", "alpha")
    assert code == 0
    assert json.loads(out)["universe_spec"]["id"] == "alpha"


def test_a_universe_spec_that_does_not_conform_is_refused(capsys, tmp_path):
    scope = tmp_path / ".knowledge-bus"
    path = write_scope(scope, "broken")
    universe = yaml.safe_load(path.read_text())
    del universe["universe"]["ordering_frame"]
    path.write_text(yaml.safe_dump(universe, sort_keys=False))
    for args in (["--card", "visit-plan"], ["--kinds"]):
        code, out, err = run(capsys, *args, str(scope))
        assert code == 1
        assert out == ""
        assert error_of(err)["category"] == "conformance"


def test_guidance_that_does_not_conform_is_refused(capsys, tmp_path):
    scope = tmp_path / ".knowledge-bus"
    write_scope(scope, "one")
    guidance_path = scope / "type-guidance.kbp.yaml"
    guidance = yaml.safe_load(guidance_path.read_text())
    guidance["elements"]["no-such-element"] = [
        {"kind": "heuristic", "source": "asserted", "claim": "x"}
    ]
    guidance_path.write_text(yaml.safe_dump(guidance, sort_keys=False))
    code, out, err = run(capsys, "--card", "visit-plan", str(scope))
    assert code == 1
    assert out == ""
    assert error_of(err)["category"] == "conformance"


@pytest.mark.parametrize(
    "marks",
    [
        "marks: [this will not parse\n",
        "marks: { id: m, version: 1, marks_for: elsewhere }\n",
    ],
)
def test_a_broken_marks_file_never_blocks_a_card(capsys, tmp_path, marks):
    scope = tmp_path / ".knowledge-bus"
    write_scope(scope, "one", marks=marks)
    assert run(capsys, "--inspect", str(scope))[0] == 1
    code, out, err = run(capsys, "--card", "visit-plan", str(scope))
    assert code == 0, err
    assert json.loads(out)["kind"] == "visit-plan"
    assert run(capsys, "--kinds", str(scope))[0] == 0


def test_explorer_drawing_problems_never_block_a_card(capsys, tmp_path):
    """Relation wording matters to the explorer only."""
    scope = tmp_path / ".knowledge-bus"
    scope.mkdir()
    universe = yaml.safe_load((REFERENCE / "universe.kbp.yaml").read_text())
    universe["relation_kinds"][0].pop("phrasing", None)
    (scope / "universe.kbp.yaml").write_text(yaml.safe_dump(universe, sort_keys=False))
    shutil.copy(REFERENCE / "type-guidance.kbp.yaml", scope / "type-guidance.kbp.yaml")
    code, _, err = run(capsys, "--inspect", str(scope))
    assert code == 1
    assert error_of(err)["category"] == "renderability"
    code, out, err = run(capsys, "--card", "decision-record", str(scope))
    assert code == 0, err
    expected = json.loads(
        (CARDS / "product-development/decision-record.json").read_text()
    )
    assert json.loads(out) == expected


def snapshot(path):
    return {
        p.relative_to(path).as_posix(): p.read_bytes()
        for p in path.rglob("*")
        if p.is_file()
    }


def test_card_is_read_only_repeatable_and_names_no_paths(capsys, tmp_path):
    scope = tmp_path / ".knowledge-bus"
    write_scope(scope, "one")
    (scope / "answers.yaml").write_text("review_only: true\n")
    before = snapshot(tmp_path)
    for args in (
        ["--card", "visit-plan"],
        ["--card", "visit-plan", "--format", "markdown"],
        ["--kinds"],
        ["--kinds", "--format", "markdown"],
    ):
        first = run(capsys, *args, str(scope))
        second = run(capsys, *args, str(scope))
        assert first[0] == 0
        assert first == second
        assert str(tmp_path) not in first[1]
        assert "answers.yaml" not in first[1]
    assert snapshot(tmp_path) == before


def test_card_finds_the_nearest_scope(capsys, tmp_path, monkeypatch):
    write_scope(tmp_path / ".knowledge-bus", "one")
    monkeypatch.chdir(tmp_path)
    code, out, err = run(capsys, "--card", "visit-plan")
    assert code == 0, err
    assert json.loads(out)["universe_spec"]["id"] == "one"


def test_kinds_lists_name_other_names_and_purpose(capsys):
    listing = json.loads(kinds_output(capsys, SETS["product-development"], "json"))
    assert listing["schema"] == "knowledge-bus/kinds/1"
    assert [item["kind"] for item in listing["kinds"]] == kind_ids(
        SETS["product-development"]
    )
    brand = next(
        item for item in listing["kinds"] if item["kind"] == "brand-identity-guide"
    )
    assert brand["name"] == "Brand identity guide"
    assert brand["alias"] == {
        "kind": "descriptive",
        "form": "brand guidelines / style guide / DESIGN.md",
    }
    assert brand["action"] == "apply the brand's look and wording correctly on your own"


def test_card_code_takes_loaded_data_and_uses_the_standard_library_only(monkeypatch):
    from kbp_conform import card

    tree = ast.parse(CARD_SOURCE.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0, "card.py imports nothing from the package"
            imported.add(node.module.split(".")[0])
    assert imported <= sys.stdlib_module_names
    functions = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }
    assert not {"check", "check_guidance"} & functions

    universe = yaml.safe_load((FIXTURE / "universe.kbp.yaml").read_text())
    guidance = yaml.safe_load((FIXTURE / "type-guidance.kbp.yaml").read_text())

    def refuse(*args, **kwargs):
        raise AssertionError("card code opened a file")

    monkeypatch.setattr(builtins, "open", refuse)
    monkeypatch.setattr(io, "open", refuse)
    monkeypatch.setattr(Path, "open", refuse)
    monkeypatch.setattr(Path, "read_text", refuse)
    for kind in ("visit-plan", "site-permit", "visit-report"):
        built = card.build_card(universe, guidance, kind)
        assert card.render_card(built).startswith("# ")
    listing = card.build_kinds(universe)
    assert card.render_kinds(listing).startswith("# ")
