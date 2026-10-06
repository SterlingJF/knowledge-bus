"""The sort check: probes that answer one member's question are filed under it by every filer."""

import json

import sort
import tiers

RULE = {
    "rule": "Knowledge is filed under the question it answers.",
    "scope": "set",
    "sort": {"ask": "Which question does this passage answer?", "write": "Write two."},
}
SET = ["core: Who sings tonight?", "situational when hall is large: Which hall?"]


def member(text, probes=None, rule_id="sorts", members=SET, **context):
    context = {"set": members, **context}
    if probes is not None:
        context["probes"] = probes
    return tiers.Case(
        rule_id, RULE, "artifact.composition", f"ref[{text}]", text, context
    )


def filer(name, answers):
    """A filer that files each passage by a lookup, recording what it was shown."""
    seen = []

    def file(questions, passages, ask):
        seen.append((questions, passages, ask))
        return [answers.get(p, 1) for p in passages]

    return sort.Filer(name, file), seen


def test_content_words_skip_short_and_common_words_and_strip_endings():
    assert sort.content_words("Which singers sing in each concert?") == {
        "singers",
        "sing",
        "concert",
    }
    assert sort.shared_words("The altos noted it.", "Who notes the alto line?") == [
        "altos",
        "noted",
    ]
    assert sort.shared_words("Rehearsing starts at six.", "Who rehearses?") == [
        "rehearsing"
    ]
    assert sort.shared_words("Tenors open the evening.", "Who sings tonight?") == []


def test_the_set_questions_are_shown_without_strengths():
    assert sort.question(SET[1]) == "Which hall?"
    assert sort.question("Which hall?") == "Which hall?"


def test_a_member_passes_only_when_every_filer_files_every_probe_under_it():
    careful, seen = filer("careful", {})
    light, _ = filer("light", {"Basses fill the back row.": 2})
    sorter = sort.Sorter([careful, light], sort.given_probes)
    first, second = sorter(
        [
            member(
                "Who sings tonight?",
                ["Tenors open the evening.", "Basses fill the back row."],
            ),
            member("Which hall?", ["The old church nave."]),
        ]
    )
    assert seen == [
        (
            ["Who sings tonight?", "Which hall?"],
            [
                "Tenors open the evening.",
                "Basses fill the back row.",
                "The old church nave.",
            ],
            "Which question does this passage answer?",
        )
    ]
    assert first.verdict == "fail" and first.tier == "sort"
    assert first.detail["filings"] == {
        "Basses fill the back row.": {"light": "Which hall?"}
    }
    assert first.detail["reason"] == (
        'light filed "Basses fill the back row." under "Which hall?"'
    )
    assert second.verdict == "fail"
    assert second.detail["filings"] == {
        "The old church nave.": {
            "careful": "Who sings tonight?",
            "light": "Who sings tonight?",
        }
    }
    assert "and 1 more misfiling" in second.detail["reason"]


def test_a_member_with_every_probe_in_place_passes():
    good, _ = filer("careful", {"The old church nave.": 2})
    passed, _ = sort.Sorter([good], sort.given_probes)(
        [
            member("Which hall?", ["The old church nave."]),
            member("Who sings tonight?", ["Tenors open the evening."]),
        ]
    )
    assert passed.verdict == "pass"
    assert (
        passed.detail["reason"] == "Every filer filed all 1 probes under this question."
    )


def test_none_is_a_misfile_but_an_unsure_decision_model_leaves_it_undecided():
    probe = "Tenors open the evening."
    unsure, _ = filer("decision", {probe: "unsure"})
    none, _ = filer("light", {probe: 0})
    placed, _ = filer("light", {})
    (failed,) = sort.Sorter([unsure, none], sort.given_probes)(
        [member("Who sings tonight?", [probe])]
    )
    assert failed.verdict == "fail"
    assert failed.detail["filings"] == {probe: {"light": "none of the questions"}}
    (open_,) = sort.Sorter([unsure, placed], sort.given_probes)(
        [member("Who sings tonight?", [probe])]
    )
    assert open_.verdict == "undecided"
    assert (
        open_.detail["reason"]
        == "decision was unsure about 1 of 1 probes; no filer put one elsewhere."
    )


def test_the_universe_scope_is_shown_with_the_ask():
    shown, seen = filer("light", {})
    sort.Sorter([shown], sort.given_probes, scope="Scope: deliberate work.")(
        [member("Who sings tonight?", ["Tenors open the evening."])]
    )
    assert (
        seen[0][2]
        == "Scope: deliberate work.\n\nWhich question does this passage answer?"
    )


def test_no_valid_probe_or_a_failed_filer_leaves_the_member_undecided():
    good, _ = filer("careful", {})

    def broken(questions, passages, ask):
        raise RuntimeError("model call failed: overloaded")

    sorter = sort.Sorter([good, sort.Filer("light", broken)], sort.given_probes)
    bare, probed = sorter(
        [member("Which hall?", []), member("Who sings tonight?", ["Tenors."])]
    )
    assert bare.verdict == "undecided"
    assert bare.detail["reason"] == "No valid probe to file."
    assert probed.verdict == "undecided"
    assert probed.detail["reason"].startswith("light call failed: model call failed")


def test_sets_are_filed_apart_and_repeated_runs_reuse_the_filings():
    careful, seen = filer("careful", {})
    sorter = sort.Sorter([careful], sort.given_probes)
    other = ["Who pays?", "Which bank?"]
    cases = [
        member("Who sings tonight?", ["Tenors."]),
        member("Who pays?", ["The treasurer."], members=other),
    ]
    assert [o.verdict for o in sorter(cases)] == ["pass", "pass"]
    assert [o.verdict for o in sorter(cases)] == ["pass", "pass"]
    assert [q for q, _, _ in seen] == [
        ["Who sings tonight?", "Which hall?"],
        ["Who pays?", "Which bank?"],
    ]


def writer(replies):
    calls = []

    def write(question, instruction):
        calls.append((question, instruction))
        return replies.pop(0)

    return write, calls


def test_probes_drop_passages_sharing_a_word_and_regenerate_up_to_twice():
    write, calls = writer(
        [
            ["The tenors sing first.", "Altos close tonight."],
            ["Singing starts by six.", "A tenor solo opens."],
            ["Hymns ring out."],
        ]
    )
    prober = sort.Prober(write, {"a": lambda q, ps: [True] * len(ps)})
    (probes,) = prober([member("Who sings tonight?", id="roster")])
    assert len(calls) == 3
    assert calls[0] == ("Who sings tonight?", "Write two.")
    assert probes == ["A tenor solo opens.", "Hymns ring out."]
    dropped = prober.known["roster"]["dropped"]
    assert dropped == [
        {"probe": "The tenors sing first.", "why": "shares sing with the question"},
        {"probe": "Altos close tonight.", "why": "shares tonight with the question"},
        {"probe": "Singing starts by six.", "why": "shares singing with the question"},
    ]


def test_a_probe_stays_only_when_every_judge_says_it_answers():
    write, _ = writer([["Tenors open.", "Bread rises slowly."]])
    judges = {
        "a": lambda q, ps: [True, True],
        "b": lambda q, ps: [True, False],
    }
    prober = sort.Prober(write, judges)
    (probes,) = prober([member("Who sings tonight?", id="roster")])
    assert probes == ["Tenors open."]
    assert prober.known["roster"]["dropped"] == [
        {"probe": "Bread rises slowly.", "why": "b: does not answer the question"}
    ]


def test_probes_are_written_once_per_element_and_reused_from_a_file(tmp_path):
    write, calls = writer([["Tenors open."]])
    prober = sort.Prober(write, {"a": lambda q, ps: [True] * len(ps)})
    cases = [
        member("Who sings tonight?", id="roster", artifact="plan"),
        member("Who sings tonight?", id="roster", artifact="booking"),
    ]
    assert prober(cases) == [["Tenors open."], ["Tenors open."]]
    assert len(calls) == 1
    path = tmp_path / "probes.json"
    sort.save(path, prober.known)
    assert json.loads(path.read_text())["probes"]["roster"]["probes"] == [
        "Tenors open."
    ]

    def never(question, instruction):
        raise AssertionError("a reused probe file needs no writer")

    again = sort.Prober(never, {}, known=sort.load(path))
    edited = member("Which singers perform tonight?", id="roster")
    assert again([edited]) == [["Tenors open."]]
    assert again.notes == [
        "probes for roster were reused from a file written for a different question"
    ]


def test_a_failed_writer_leaves_the_element_without_probes():
    def write(question, instruction):
        raise RuntimeError("model call failed")

    prober = sort.Prober(write, {})
    assert prober([member("Who sings tonight?", id="roster")]) == [[]]
    assert prober.known["roster"]["error"] == "writer: model call failed"


RECOGNISE = {
    "rule": "Every kind of reader files each everyday situation under its frame value.",
    "scope": "set",
    "recognise": {
        "ask": "Which of these fits the situation best?",
        "value_share": 0.75,
        "frame_share": 0.9,
    },
}
VALUES = ["Indoors", "Outdoors", "Online"]


def values(members=VALUES, n=4, **context):
    """One case per value, with n situations each named '<value> <k>'."""
    return [
        tiers.Case(
            "values-recognised",
            RECOGNISE,
            "frame.value",
            f"frames[venue].values[{m.lower()}]",
            m,
            {
                "id": m.lower(),
                "frame": "venue",
                "set": members,
                "probes": [f"{m} {k}" for k in range(1, n + 1)],
                **context,
            },
        )
        for m in members
    ]


def reader(name, slips=None):
    """Files each situation under its own value, except slips: {situation: answer}."""
    calls = []

    def file(questions, passages, ask):
        calls.append((passages, ask))
        return [
            (slips or {}).get(p, questions.index(p.rsplit(" ", 1)[0]) + 1)
            for p in passages
        ]

    return sort.Filer(name, file), calls


def recognise(filers, cases, **options):
    sorter = sort.Sorter(
        filers, sort.given_probes, verdicts=sort.recognition(), batch=False, **options
    )
    return sorter(cases)


def test_recognition_files_one_situation_per_call():
    light, calls = reader("light")
    recognise([light], values())
    assert sorted(p for p, _ in calls) == sorted(
        [[f"{m} {k}"] for m in VALUES for k in range(1, 5)]
    )


def test_the_frame_question_is_shown_with_the_ask():
    light, calls = reader("light")
    recognise(
        [light],
        values(**{"frame question": "Where does the rehearsal happen?"}),
        scope="Scope: choir work.",
    )
    assert calls[0][1] == (
        "Scope: choir work.\n\nQuestion: Where does the rehearsal happen?\n\n"
        "Which of these fits the situation best?"
    )


def test_a_value_passes_with_one_slip_in_four_and_fails_with_two():
    careful, _ = reader("careful")
    one, _ = reader("light", {"Indoors 1": 2})
    outcomes = recognise([careful, one], values())
    assert [o.verdict for o in outcomes] == ["pass", "pass", "pass"]
    assert outcomes[0].tier == "recognise"
    assert outcomes[0].detail["right"] == {"careful": 4, "light": 3}
    assert outcomes[0].detail["reason"] == (
        "Every filer met the bar: at least 3 of 4 here and 11 of 12 in the set."
    )
    two, _ = reader("light", {"Indoors 1": 2, "Indoors 2": 2})
    first, second, third = recognise([careful, two], values())
    assert [first.verdict, second.verdict, third.verdict] == ["fail", "pass", "pass"]
    assert first.detail["misses"] == {
        "Indoors 1": {"light": "Outdoors"},
        "Indoors 2": {"light": "Outdoors"},
    }
    assert first.detail["reason"] == (
        "light filed 2 of 4 here and 10 of 12 in the set; the bar is 3 of 4 here and "
        '11 of 12 in the set. First miss: light put "Indoors 1" under "Outdoors".'
    )
    assert first.detail["set"] == "venue" and first.detail["value"] == "indoors"


def test_a_frame_below_the_bar_fails_only_its_values_that_lost_situations():
    light, _ = reader("light", {"Indoors 1": 2, "Online 1": 1})
    outcomes = recognise([light], values())
    assert [o.verdict for o in outcomes] == ["fail", "pass", "fail"]
    assert outcomes[1].detail["filers"] == {
        "light": {"right": 10, "n": 12, "unsure": 0, "none": 0}
    }


def test_unsure_and_none_count_as_misses_in_recognition():
    unsure = {f"Outdoors {k}": "unsure" for k in (1, 2, 3)}
    decision, _ = reader("decision", unsure)
    light, _ = reader("light", {"Online 1": 0})
    outcomes = recognise([decision, light], values(n=8))
    assert [o.verdict for o in outcomes] == ["pass", "fail", "pass"]
    assert outcomes[1].detail["filers"] == {
        "decision": {"right": 21, "n": 24, "unsure": 3, "none": 0},
        "light": {"right": 23, "n": 24, "unsure": 0, "none": 1},
    }
    assert outcomes[1].detail["misses"]["Outdoors 1"] == {"decision": "unsure"}


def test_ladder_misses_report_off_by_one_step():
    steps = ["Nobody", "Organiser", "Council"]
    light, _ = reader("light", {"Council 1": 2, "Council 2": 1})
    outcomes = recognise([light], values(steps, ladder=True))
    assert outcomes[2].verdict == "fail"
    assert outcomes[2].detail["filers"]["light"] == {
        "right": 10, "n": 12, "unsure": 0, "none": 0, "off_by_one": 1,
    }  # fmt: skip


def test_no_situations_or_a_failed_call_leave_a_value_undecided():
    light, _ = reader("light")
    (bare,) = recognise([light], values(["Indoors"], n=0))
    assert bare.verdict == "undecided" and bare.tier == "recognise"
    assert bare.detail["reason"] == "Not run: no situations for this value."

    def broken(questions, passages, ask):
        raise RuntimeError("overloaded")

    (failed,) = recognise([sort.Filer("light", broken)], values(["Indoors"]))
    assert failed.verdict == "undecided"
    assert failed.detail["reason"] == "light call failed: overloaded"


def test_each_filers_own_placements_are_kept_on_every_outcome():
    careful, _ = filer("careful", {})
    light, _ = filer("light", {"Basses fill the back row.": 2})
    first, second = sort.Sorter([careful, light], sort.given_probes)(
        [
            member("Who sings tonight?", ["Tenors.", "Basses fill the back row."]),
            member("Which hall?", []),
        ]
    )
    assert first.detail["placed"] == {
        "careful": ["Who sings tonight?", "Who sings tonight?"],
        "light": ["Who sings tonight?", "Which hall?"],
    }
    assert second.detail["placed"] == {"careful": [], "light": []}
    one, _ = reader("light", {"Indoors 1": "unsure"})
    (indoors, *_) = recognise([one], values())
    assert indoors.detail["placed"] == {
        "light": ["unsure", "Indoors", "Indoors", "Indoors"]
    }
