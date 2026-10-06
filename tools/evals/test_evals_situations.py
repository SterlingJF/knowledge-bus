"""Shared real cases, each universe's answers over them, and the checks on both."""

import copy
from pathlib import Path

import pytest
import situations
import spec
import tiers

FIXTURES = Path(__file__).parent / "fixtures"
UNIVERSE = spec.read(FIXTURES / "summer-fair.universe.yaml")
CASES = spec.read(FIXTURES / "situations" / "cases.yaml")
ANSWERS = spec.read(FIXTURES / "situations" / "summer-fair.yaml")
NIGHT_MARKET = {
    "universe": {"id": "night-market"},
    "frames": [
        {
            "id": "lighting",
            "question": "How is the pond lit?",
            "values": ["dark", "lamps"],
        }
    ],
}


def problems(change=None, universe=UNIVERSE):
    answers, cases = copy.deepcopy(ANSWERS), copy.deepcopy(CASES)
    if change:
        change(answers, cases)
    return situations.case_problems(cases) + situations.problems(
        answers, universe, cases
    )


def case(cases, ident):
    return next(c for c in cases["cases"] if c["id"] == ident)


def entry(answers):
    return answers["frames"]["entry"]["answers"]


def permission(answers):
    return answers["frames"]["permission"]["answers"]


def test_the_fixture_cases_and_answers_have_no_problems():
    assert problems() == []


def test_answers_name_real_frames_values_and_cases():
    def change(answers, cases):
        answers["universe"] = "night-market"
        answers["frames"]["parking"] = answers["frames"].pop("permission")
        entry(answers)["c01"] = "free"
        entry(answers)["c99"] = "open"

    assert problems(change) == [
        "names universe night-market, not summer-fair",
        "entry/c01: free is not a value of entry",
        "entry/c99: no such case in the pool",
        "entry: open has 3 situations from summer-fair; needs at least 4",
        "entry: has 11 situations from summer-fair; needs at least 12",
        "parking: not a frame, facet or factor of the universe",
        "permission: has no situations",
    ]


def test_each_value_has_four_own_field_situations_and_each_set_twelve():
    def fewer(answers, cases):
        del entry(answers)["c12"]

    assert problems(fewer) == [
        "entry: invited has 3 situations from summer-fair; needs at least 4",
        "entry: has 11 situations from summer-fair; needs at least 12",
    ]

    def borrowed(answers, cases):
        case(cases, "c02")["field"] = "night-market"

    assert problems(borrowed) == [
        "entry: open has 3 situations from summer-fair; needs at least 4",
        "entry: has 11 situations from summer-fair; needs at least 12",
    ]


def test_a_ladder_comes_from_the_answers_and_has_boundary_pairs():
    def unbounded(answers, cases):
        permission(answers)["c16"] = "nobody"
        permission(answers)["c21"] = {"value": "council", "near": "nobody"}
        entry(answers)["c02"] = {"value": "open", "near": "ticketed"}

    assert problems(unbounded) == [
        "entry/c02: near is only for a ladder, naming a neighbouring step",
        "permission/c21: near is only for a ladder, naming a neighbouring step",
        "permission: needs a nobody situation near organiser",
        "permission: needs a council situation near organiser",
    ]

    def flat(answers, cases):
        del answers["frames"]["permission"]["ladder"]

    assert problems(flat) == [
        f"permission/{c}: near is only for a ladder, naming a neighbouring step"
        for c in ("c16", "c17", "c19", "c21")
    ]

    def odd(answers, cases):
        answers["frames"]["permission"]["ladder"] = ["nobody", "council"]

    assert problems(odd) == ["permission: ladder must be true or false"]


def test_situations_cover_every_tag_twice_per_set():
    def change(answers, cases):
        case(cases, "c02")["tags"]["kind"] = "craft"
        case(cases, "c06")["tags"]["kind"] = "craft"
        case(cases, "c09")["tags"]["who"] = "village"
        del case(cases, "c03")["tags"]["who"]

    assert problems(change) == [
        "c03: needs tag who",
        "c09: who must be one of one, group, organisation",
        "entry: kind music has 1 situation from summer-fair; needs at least 2",
    ]


def test_each_tag_value_has_a_written_meaning():
    def change(answers, cases):
        cases["tags"]["kind"]["craft"] = " "
        cases["tags"]["kind"]["music"] = None
        cases["tags"]["who"] = list(cases["tags"]["who"])

    assert problems(change) == [
        "tags: kind music: needs a meaning",
        "tags: kind craft: needs a meaning",
        "tags: who: needs a meaning for each value",
    ]


SHORT = {"reason": "The fair books no bands.", "source": "https://example.org/fair"}


def test_a_tag_value_the_field_cannot_offer_is_declared_absent():
    def change(answers, cases):
        case(cases, "c02")["tags"]["kind"] = "craft"
        case(cases, "c06")["tags"]["kind"] = "craft"

    assert problems(change) == [
        "entry: kind music has 1 situation from summer-fair; needs at least 2"
    ]

    def declared(answers, cases):
        change(answers, cases)
        answers["absent"] = {"kind": {"music": SHORT}}

    assert problems(declared) == []

    def fewer(answers, cases):
        declared(answers, cases)
        del entry(answers)["c12"]

    assert problems(fewer) == [
        "entry: invited has 3 situations from summer-fair; needs at least 4",
        "entry: has 11 situations from summer-fair; needs at least 12",
    ]


def test_an_absent_value_names_a_known_tag_and_value_with_a_reason_and_a_source():
    def change(answers, cases):
        answers["absent"] = {
            "colour": {"red": SHORT},
            "kind": {"juggling": SHORT, "music": {"reason": " ", "note": "x"}},
            "who": {"group": SHORT | {"source": None}},
        }

    assert problems(change) == [
        "absent: unknown tag colour",
        "absent: kind juggling: not a value of kind",
        "absent: kind music: unknown field note",
        "absent: kind music: needs reason",
        "absent: kind music: needs source",
        "absent: who group: needs source",
    ]


def test_a_case_sharing_a_word_with_any_universe_using_it_is_refused():
    def change(answers, cases):
        case(cases, "c04")["text"] = "Two sisters open a lemonade stand for visitors."
        case(cases, "c14")["text"] = (
            "Three friends play fiddles before the fair starts."
        )

    assert problems(change) == [
        "entry/c04: shares open, visitors with the wording",
        "permission/c14: shares starts with the wording",
    ]
    night = {
        "schema": situations.SCHEMA,
        "universe": "night-market",
        "field": "night-market",
        "frames": {
            "lighting": situations.answer_set(
                "lighting", {"dark": "No light.", "lamps": "Lit."}, {"c01": "dark"}
            )
        },
    }
    found = situations.problems(night, NIGHT_MARKET, CASES)
    assert "lighting/c01: shares pond with the wording" in found
    assert not [p for p in problems() if "pond" in p]


def test_cases_name_no_vendor_brand_or_identifier():
    def change(answers, cases):
        case(cases, "c01")["text"] = "A baker posts the flapjack rota on GitHub."
        case(cases, "c02")["text"] = (
            "The band leader emails rota@example.org with the set."
        )
        case(cases, "c13")["text"] = "I ask Claude to price the lollies."

    assert problems(change) == [
        "c01: names a vendor or product: GitHub",
        "c02: holds an email address",
        "c13: names a vendor or product: Claude",
    ]


def test_case_ids_are_unique_and_fields_known():
    def change(answers, cases):
        case(cases, "c03")["mood"] = "sunny"
        cases["cases"].append(copy.deepcopy(case(cases, "c01")))
        del case(cases, "c05")["field"]
        answers["frames"]["entry"]["order"] = "random"

    assert problems(change) == [
        "c03: unknown field mood",
        "c05: needs field",
        "duplicate case id c01",
        "entry: unknown field order",
        "entry: ticketed has 3 situations from summer-fair; needs at least 4",
        "entry: has 11 situations from summer-fair; needs at least 12",
    ]


def test_each_case_text_is_held_once():
    def change(answers, cases):
        again = case(cases, "c01") | {"id": "c25", "field": "night-market"}
        again["text"] = "  " + again["text"].upper().replace(" ", "\n ")
        cases["cases"].append(again)

    assert problems(change) == ["c25: same text as c01"]


def test_the_schemas_are_named():
    def change(answers, cases):
        answers["schema"] = "situations/0"
        cases["schema"] = "cases/0"

    assert problems(change)[:2] == [
        "needs schema: evals-cases/1",
        "needs schema: evals-answers/1",
    ]


def test_changed_values_or_meanings_make_answers_stale_and_rewording_does_not():
    grown = copy.deepcopy(UNIVERSE)
    grown["frames"][0]["values"].append({"id": "raffle", "question": "Is it a draw?"})
    assert problems(universe=grown) == [
        (
            "entry: stale answers: labelled against open, ticketed, invited; the universe"
            " now has open, ticketed, invited, raffle; relabel"
        )
    ]

    def redefined(answers, cases):
        answers["frames"]["entry"]["means"]["open"] = "Anyone may walk in."

    assert problems(redefined) == [
        "entry: stale answers: a value's meaning changed since labelling; relabel"
    ]
    reworded = copy.deepcopy(UNIVERSE)
    reworded["frames"][0]["question"] = "Which way leads inside?"
    reworded["frames"][0]["values"][0]["question"] = "Is it free to all?"
    assert not [p for p in problems(universe=reworded) if "stale" in p]


def test_a_fingerprint_covers_the_set_its_values_in_order_and_their_meanings():
    means = {"low": "Little.", "high": "Much."}
    mark = situations.fingerprint("level", means)
    assert mark.startswith("sha256:")
    assert situations.fingerprint("level", dict(means)) == mark
    assert situations.fingerprint("grade", means) != mark
    assert situations.fingerprint("level", {"high": "Much.", "low": "Little."}) != mark
    assert situations.fingerprint("level", {**means, "low": "Few."}) != mark


def recognition_case(frame, value, **context):
    return tiers.Case(
        "values-recognised",
        {},
        "frame.value",
        f"frames[{frame}].values[{value}]",
        value.capitalize(),
        {"id": value, "frame": frame, "set": [], **context},
    )


def test_situations_are_given_per_value_and_ladders_come_from_the_answers():
    source = situations.Situations(ANSWERS, CASES)
    cases = [
        recognition_case("entry", "invited"),
        recognition_case("permission", "council"),
    ]
    given = source(cases)
    assert [len(g) for g in given] == [4, 4]
    assert given[0][0].startswith("The silver band's rehearsal tent")
    assert [source.ladder(c) for c in cases] == [False, True]
    stale = situations.Situations(ANSWERS, CASES, stale=["entry"])
    assert [len(g) for g in stale(cases)] == [0, 4]
    empty = situations.Situations(None, None)
    assert empty(cases) == [[], []]
    assert not empty.ladder(cases[1])


def test_a_folder_is_checked_against_every_universe_that_uses_its_cases(tmp_path):
    folder = tmp_path / "situations"
    folder.mkdir()
    for name in ("cases.yaml", "summer-fair.yaml"):
        (folder / name).write_text((FIXTURES / "situations" / name).read_text())
    (folder / "night-market.yaml").write_text(
        "schema: evals-answers/1\nuniverse: night-market\nfield: night-market\n"
    )
    universes = {"summer-fair": UNIVERSE, "night-market": NIGHT_MARKET}.get
    assert situations.folder_problems(folder, universes) == [
        "night-market.yaml: lighting: has no situations"
    ]
    (folder / "lost.yaml").write_text("schema: evals-answers/1\nuniverse: lost\n")
    assert "lost.yaml: no universe file for lost" in situations.folder_problems(
        folder, universes
    )


def test_the_repository_situations_have_no_problems():
    assert situations.folder_problems() == []


def test_the_product_development_ladders_are_the_four_the_owner_named():
    path = situations.FOLDER / "product-development.yaml"
    if not path.exists():
        pytest.skip(
            "evals/situations/product-development.yaml is not frozen yet: "
            "the owner's blind labels are pending"
        )
    answers = spec.read(path)
    declared = sorted(
        key
        for section in situations.SECTIONS
        for key, block in (answers.get(section) or {}).items()
        if block.get("ladder")
    )
    assert declared == ["authority", "maturity", "reversibility", "time-separation"]


def test_no_universe_is_named_in_the_generic_code():
    """Only grade.py's default for --universe names one."""
    default = 'UNIVERSE = ROOT / "universes/product-development/universe.kbp.yaml"'
    assert default in (Path(__file__).parent / "grade.py").read_text()
    for module in sorted(Path(__file__).parent.glob("*.py")):
        if module.name.startswith("test_"):
            continue
        text = module.read_text().replace(default, "")
        assert "product-development" not in text and "LADDERS" not in text, module.name
