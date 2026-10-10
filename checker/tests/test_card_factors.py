"""Factors on `--kinds` and on the card.

`--kinds` lists every factor with its guidance count. The card shows guidance
keyed to factors as advice on presenting the document: one labelled block for
each universe spec in scope that declares a factor, the card's own universe
spec first. Factors change presentation and focus only, so the card's sections
stay the same.
"""

import json
import shutil
from pathlib import Path

import pytest

from kbp_conform import cli

ROOT = Path(__file__).resolve().parents[2]
TESTS = Path(__file__).resolve().parent
HALL_READERS = TESTS / "hall-readers"
VILLAGE_HALL = ROOT / "evals/fixtures/village-hall/.knowledge-bus"
FACTORS_ONLY = ROOT / "protocol/conformance/pass/factors-only.kbp.yaml"
CARD_FIXTURE = TESTS / "card-fixture/universe.kbp.yaml"
UPKEEP = TESTS / "workspace/upkeep/hall"

HIRER_EXPERIENCE = {
    "factor": "hirer-experience",
    "name": "Hirer experience",
    "question": "Has the reader hired the hall before?",
}
READING_FORMAT = {
    "factor": "reading-format",
    "name": "Reading format",
    "question": "How will the reader see the document?",
}


def run(capsys, *args):
    code = cli.main(list(args))
    captured = capsys.readouterr()
    assert code == 0, captured.err
    assert captured.err == ""
    return captured.out


def as_json(capsys, *args):
    return json.loads(run(capsys, *args))


def markdown(capsys, *args):
    return run(capsys, *args, "--format", "markdown").splitlines()


def block(lines, heading):
    """The lines under `heading`, up to the next heading of the same level or higher."""
    start = lines.index(heading)
    level = heading.split(" ")[0]
    rest = lines[start + 1 :]
    for index, line in enumerate(rest):
        marks = line.split(" ")[0]
        if line.startswith("#") and set(marks) == {"#"} and len(marks) <= len(level):
            return rest[:index]
    return rest


@pytest.fixture
def hall(tmp_path):
    """Village hall bookings and upkeep, plus the factor-only hall readers universe spec."""
    folder = tmp_path / ".knowledge-bus"
    shutil.copytree(VILLAGE_HALL, folder)
    for path in HALL_READERS.glob("*.kbp.yaml"):
        shutil.copy(path, folder / path.name)
    return folder


@pytest.fixture
def hall_without_readers(tmp_path):
    folder = tmp_path / "plain" / ".knowledge-bus"
    shutil.copytree(VILLAGE_HALL, folder)
    return folder


# --kinds lists factors and their guidance counts.


def test_kinds_lists_factors_with_guidance_counts(capsys, hall):
    listing = as_json(capsys, "--kinds", str(hall), "--universe", "hall-readers")
    assert listing["kinds"] == []
    assert listing["factors"] == [
        {**HIRER_EXPERIENCE, "guidance": 2},
        {**READING_FORMAT, "guidance": 1},
    ]


def test_kinds_counts_are_null_without_a_guidance_file(capsys, tmp_path):
    folder = tmp_path / ".knowledge-bus"
    folder.mkdir()
    shutil.copy(FACTORS_ONLY, folder / FACTORS_ONLY.name)
    listing = as_json(capsys, "--kinds", str(folder))
    assert listing["factors"] == [
        {
            "factor": "team-shape",
            "name": "Team shape",
            "question": "Who is doing the work?",
            "guidance": None,
        }
    ]
    lines = markdown(capsys, "--kinds", str(folder))
    assert lines[lines.index("Factors:") :] == [
        "Factors:",
        "",
        "- Team shape (team-shape)",
        "  - Asks: Who is doing the work?",
    ]


def test_kinds_set_groups_list_factors(capsys, hall):
    listing = as_json(capsys, "--kinds", str(hall))
    groups = {
        group["universe_spec"]["id"]: group for group in listing["universe_specs"]
    }
    assert groups["hall-bookings"]["factors"] == []
    assert groups["hall-readers"]["factors"][1] == {**READING_FORMAT, "guidance": 1}
    lines = markdown(capsys, "--kinds", str(hall))
    readers = block(lines, "## Hall readers universe spec (hall-readers 0.1)")
    assert readers[readers.index("No document types.") :] == [
        "No document types.",
        "",
        "Factors:",
        "",
        "- Hirer experience (hirer-experience)",
        "  - Asks: Has the reader hired the hall before?",
        "  - 2 guidance notes",
        "- Reading format (reading-format)",
        "  - Asks: How will the reader see the document?",
        "  - 1 guidance note",
        "",
    ]
    bookings = block(lines, "## Hall bookings universe spec (hall-bookings 0.1)")
    assert "Factors:" not in bookings


# The card shows guidance keyed to the factors of its own universe spec.


def test_card_shows_its_own_factor_guidance_as_presentation_advice(capsys):
    card = as_json(capsys, "--card", "visit-plan", str(CARD_FIXTURE))
    assert [item["universe_spec"]["id"] for item in card["presentation"]] == [
        "card-fixture"
    ]
    own = card["presentation"][0]
    assert own["from_parent"] is False
    assert own["factors"] == [
        {
            "factor": "familiarity",
            "name": "Familiarity",
            "question": "How well does the reader know the site?",
            "values": [
                {
                    "value": "new",
                    "question": "Is the reader visiting the site for the first time?",
                },
                {
                    "value": "regular",
                    "question": "Has the reader visited the site before?",
                },
            ],
            "guidance": [
                {
                    "kind": "heuristic",
                    "claim": "Explain each local place name the first time it appears.",
                    "when": {"familiarity": ["new"]},
                }
            ],
        }
    ]
    lines = markdown(capsys, "--card", "visit-plan", str(CARD_FIXTURE))
    assert block(lines, "## How to present it") == [
        "",
        "Factors change presentation and focus only. The sections stay the same.",
        "",
        "### Card fixture universe spec (card-fixture 0.1)",
        "",
        "#### Familiarity",
        "",
        "Asks: How well does the reader know the site?",
        "",
        "Values:",
        "",
        "- new: Is the reader visiting the site for the first time?",
        "- regular: Has the reader visited the site before?",
        "",
        "Advice:",
        "",
        (
            "- Heuristic, when familiarity is new: Explain each local place name the "
            "first time it appears. Depends on: How well does the reader know the "
            "site? (familiarity)"
        ),
        "",
    ]
    assert lines.index("## How to present it") > lines.index("## Sections")


def test_card_without_factors_has_no_presentation_block(capsys, hall_without_readers):
    card = as_json(
        capsys,
        "--card",
        "booking-form",
        str(hall_without_readers),
        "--universe",
        "hall-bookings",
    )
    assert card["presentation"] == []
    lines = markdown(
        capsys,
        "--card",
        "booking-form",
        str(hall_without_readers),
        "--universe",
        "hall-bookings",
    )
    assert "## How to present it" not in lines


# The card adds one labelled block for each other universe spec in scope that declares a factor.


def test_card_adds_a_block_for_each_other_universe_spec_with_factors(capsys, hall):
    card = as_json(
        capsys, "--card", "booking-form", str(hall), "--universe", "hall-bookings"
    )
    assert [item["universe_spec"] for item in card["presentation"]] == [
        {"id": "hall-readers", "label": "Hall readers", "version": "0.1"}
    ]
    readers = card["presentation"][0]
    assert readers["from_parent"] is False
    assert [item["factor"] for item in readers["factors"]] == [
        "hirer-experience",
        "reading-format",
    ]
    assert readers["factors"][1]["values"] == [
        {"value": "printed", "question": None},
        {"value": "screen", "question": None},
    ]
    assert [item["id"] for item in readers["conditions"]] == [
        "hirer-experience",
        "reading-format",
    ]
    lines = markdown(
        capsys, "--card", "booking-form", str(hall), "--universe", "hall-bookings"
    )
    presentation = block(lines, "## How to present it")
    assert "### Hall readers universe spec (hall-readers 0.1)" in presentation
    assert (
        "- Heuristic, when hirer-experience is first-time: Put the steps for "
        "collecting the keys first. Depends on: Has the reader hired the hall "
        "before? (hirer-experience)"
    ) in presentation
    assert "- Heuristic: Call each room by the name on its door sign." in presentation
    assert presentation[presentation.index("#### Reading format") :][:9] == [
        "#### Reading format",
        "",
        "Asks: How will the reader see the document?",
        "",
        "Values:",
        "",
        "- printed",
        "- screen",
        "",
    ]


def test_another_universe_spec_s_factors_select_nothing(
    capsys, hall, hall_without_readers
):
    """The card beside hall readers differs from the plain card only in its presentation block."""
    args = ("--card", "booking-form")
    beside = as_json(capsys, *args, str(hall), "--universe", "hall-bookings")
    plain = as_json(
        capsys, *args, str(hall_without_readers), "--universe", "hall-bookings"
    )
    assert beside.pop("presentation") != plain.pop("presentation")
    assert beside == plain


def test_card_blocks_from_the_parent_folder_say_so(capsys, tmp_path):
    hall = tmp_path / "hall"
    shutil.copytree(UPKEEP, hall)
    for path in HALL_READERS.glob("*.kbp.yaml"):
        shutil.copy(path, hall / ".knowledge-bus" / path.name)
    committee = hall / "committee"
    (committee / ".knowledge-bus" / "workspace.yaml").write_text(
        "from_parent: [hall-upkeep, hall-readers]\n"
    )
    args = ("--card", "minutes", str(committee), "--universe", "committee-minutes")
    card = as_json(capsys, *args)
    assert [
        (item["universe_spec"]["id"], item["from_parent"])
        for item in card["presentation"]
    ] == [("hall-readers", True)]
    lines = markdown(capsys, *args)
    assert (
        "### Hall readers universe spec (hall-readers 0.1), from the parent folder"
        in lines
    )
