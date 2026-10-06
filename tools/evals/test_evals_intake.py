"""The situations method as tooling: the de-identification gate, the blind labelling packet,
and applying the other side's labels to the shared cases and a universe's answers."""

import json
from pathlib import Path

import intake
import situations
import spec
import yaml

FIXTURES = Path(__file__).parent / "fixtures"
FAIR = FIXTURES / "summer-fair.universe.yaml"
CASES = spec.read(FIXTURES / "situations" / "cases.yaml")
ANSWERS = spec.read(FIXTURES / "situations" / "summer-fair.yaml")
SOURCE = "Last year the fair committee met on the green to agree the stalls for summer."


def fixture_case(ident):
    return next(c for c in CASES["cases"] if c["id"] == ident)


def work(tmp_path):
    """A working folder outside the repository: the fixture's situations as a writer's draft,
    under the writer's own ids, and one saved source page."""
    folder = tmp_path / "work"
    (folder / "sources" / "pages").mkdir(parents=True)
    (folder / "sources" / "pages" / "committee.txt").write_text(SOURCE)
    frames = {}
    for key, block in ANSWERS["frames"].items():
        listed = []
        for ident, answer in block["answers"].items():
            value, near = situations.answer_of(answer)
            case = fixture_case(ident)
            listed.append(
                {"id": f"{key}-{ident}", "text": case["text"], "value": value}
                | ({"near": near} if near else {})
                | case["tags"]
            )
        frames[key] = {"means": block["means"], "situations": listed}
        if block.get("ladder"):
            frames[key]["ladder"] = list(block["means"])
    draft = {"universe": "summer-fair", "tags": CASES["tags"], "frames": frames}
    (folder / "draft.yaml").write_text(yaml.safe_dump(draft, sort_keys=False))
    return folder


def draft_of(folder):
    return yaml.safe_load((folder / "draft.yaml").read_text())


def edit(folder, change):
    draft = draft_of(folder)
    change(draft)
    (folder / "draft.yaml").write_text(yaml.safe_dump(draft, sort_keys=False))


def label_all(folder, change=None):
    """Labels that agree with every written value, under the packet's ids: a written
    situation's opaque id, a cited case's own id."""
    labels = {
        s.get("case") or intake.opaque(s["id"]): s["value"]
        for block in draft_of(folder)["frames"].values()
        for s in block["situations"]
    }
    if change:
        change(labels)
    (folder / "labels.json").write_text(json.dumps({"labels": labels}))
    return labels


NIGHT = (
    "Lanterns hang over the noodle carts after dusk, and strollers drift between them."
)


def other_pool(out):
    """A pool another universe started: the fixture's tags and one case from its own field."""
    out.mkdir(parents=True, exist_ok=True)
    case = {"id": "n01", "text": NIGHT, "field": "night-market"}
    pool = {"schema": situations.CASES_SCHEMA, "tags": CASES["tags"], "cases": [case]}
    case["tags"] = {"kind": "food", "who": "group"}
    (out / "cases.yaml").write_text(yaml.safe_dump(pool, sort_keys=False))
    return (out / "cases.yaml").read_text()


def apply(folder, out, *extra):
    return intake.main(
        ["apply", "summer-fair", "--folder", str(folder), "--universe", str(FAIR)]
        + ["--situations", str(out), *extra]
    )


def test_ids_and_order_match_the_packet_the_owner_already_has():
    assert intake.opaque("phase-strategy-1") == "s-1d2f7fa"
    assert intake.opaque("entry-01") == "s-d1c0679"
    order = intake.shuffled([{"id": i} for i in "abcde"])
    assert [s["id"] for s in order] == ["b", "e", "d", "a", "c"]


def test_the_gate_passes_a_clean_draft_and_names_each_leak(tmp_path, capsys):
    folder = work(tmp_path)
    assert intake.main(["gate", "summer-fair", "--folder", str(folder)]) == 0
    assert (
        "24 situations checked against 1 saved source; 0 hits"
        in capsys.readouterr().out
    )

    def leaky(draft):
        listed = draft["frames"]["entry"]["situations"]
        listed[0]["text"] = "The fair committee met on the green to agree the cakes."
        listed[1]["text"] = "Our neighbour Hale pays 5 pounds in March for a pitch."
        listed[2]["text"] = (
            "The club posts its rota on GitHub and www.fair.org for Claude."
        )

    edit(folder, leaky)
    assert intake.main(["gate", "summer-fair", "--folder", str(folder)]) == 1
    out = capsys.readouterr().out
    for hit in (
        (
            "entry-c01: shares a 7-word run with pages/committee.txt: "
            "'the fair committee met on the green'"
        ),
        "entry-c02: capitalised word: Hale",
        "entry-c02: a digit (date, year, amount, reference, postcode or address): '5'",
        "entry-c02: a month name: 'March'",
        "entry-c03: a web address: 'www.'",
        "entry-c03: vendor or brand word: GitHub",
        "entry-c03: vendor or brand word: Claude",
    ):
        assert hit in out
    assert "24 situations checked against 1 saved source; " in out


def test_the_tools_refuse_a_folder_inside_the_repository_or_without_sources(
    tmp_path, capsys
):
    inside = intake.main(["gate", "summer-fair", "--folder", str(FIXTURES)])
    assert inside == 2
    assert "outside the repository" in capsys.readouterr().err
    folder = work(tmp_path)
    (folder / "sources" / "pages" / "committee.txt").unlink()
    assert intake.main(["gate", "summer-fair", "--folder", str(folder)]) == 2
    assert "no saved source texts" in capsys.readouterr().err
    out = ["--out", str(FIXTURES / "packet.md")]
    assert intake.main(["packet", "summer-fair", "--folder", str(folder), *out]) == 2
    assert not (FIXTURES / "packet.md").exists()


def test_a_draft_for_another_universe_is_refused(tmp_path, capsys):
    folder = work(tmp_path)
    assert intake.main(["packet", "night-market", "--folder", str(folder)]) == 2
    assert "is for summer-fair, not night-market" in capsys.readouterr().err


def test_the_packet_shows_meanings_and_texts_under_opaque_ids_only(tmp_path):
    folder = work(tmp_path)
    assert intake.main(["packet", "summer-fair", "--folder", str(folder)]) == 0
    packet = (folder / "packet.md").read_text()
    assert packet.index("## Group: entry") < packet.index("## Group: permission")
    assert packet.count("The values are ordered lowest first.") == 1
    assert "- `ticketed`: Money changes hands before a person is let in." in packet
    draft = draft_of(folder)
    for key, block in draft["frames"].items():
        shown = [
            line.split("`")[1]
            for line in packet.split(f"## Group: {key}\n")[1]
            .split("## ")[0]
            .splitlines()
            if line.startswith("- `s-")
        ]
        assert shown == [
            intake.opaque(s["id"]) for s in intake.shuffled(block["situations"])
        ]
    assert "entry-c" not in packet and "near" not in packet
    assert "How does a visitor get in" not in packet
    assert intake.main(["packet", "summer-fair", "--folder", str(folder)]) == 0
    assert (folder / "packet.md").read_text() == packet


def test_a_dry_run_reports_agreement_and_writes_nothing(tmp_path, capsys):
    folder, out = work(tmp_path), tmp_path / "situations"
    label_all(folder)
    assert apply(folder, out, "--dry-run") == 0
    text = capsys.readouterr().out
    assert "entry: 12/12 agree" in text and "TOTAL: 24/24 agree" in text
    assert "DRY RUN: would write 24 cases and 2 sets" in text
    assert not out.exists()


def test_applied_labels_write_shared_cases_and_the_universes_answers(tmp_path):
    folder, out = work(tmp_path), tmp_path / "situations"
    label_all(folder)
    assert apply(folder, out) == 0
    cases, answers = spec.read(out / "cases.yaml"), spec.read(out / "summer-fair.yaml")
    assert situations.folder_problems(out, {"summer-fair": spec.read(FAIR)}.get) == []
    assert {c["field"] for c in cases["cases"]} == {"summer-fair"}
    assert answers["field"] == "summer-fair"
    assert answers["frames"]["permission"]["ladder"] is True
    assert "ladder" not in answers["frames"]["entry"]
    text = {c["id"]: c["text"] for c in cases["cases"]}
    for key, block in ANSWERS["frames"].items():
        written = {text[i]: a for i, a in answers["frames"][key]["answers"].items()}
        expected = {fixture_case(i)["text"]: a for i, a in block["answers"].items()}
        assert written == expected
        assert answers["frames"][key]["fingerprint"] == block["fingerprint"]
    assert (
        "sources and provenance are kept privately" in (out / "cases.yaml").read_text()
    )
    before = [(out / n).read_text() for n in ("cases.yaml", "summer-fair.yaml")]
    assert apply(folder, out) == 0
    assert [(out / n).read_text() for n in ("cases.yaml", "summer-fair.yaml")] == before


def test_new_cases_join_an_existing_pool_after_its_last_case(tmp_path):
    folder, out = work(tmp_path), tmp_path / "situations"
    pool = other_pool(out)
    label_all(folder)
    assert apply(folder, out) == 0
    grown = (out / "cases.yaml").read_text()
    assert grown.startswith(pool)
    assert len(spec.read(out / "cases.yaml")["cases"]) == 25


def test_a_draft_cites_a_pool_case_from_another_field_without_adding_it_again(
    tmp_path, capsys
):
    folder, out = work(tmp_path), tmp_path / "situations"
    other_pool(out)
    cited = {"case": "n01", "value": "open"}
    edit(folder, lambda d: d["frames"]["entry"]["situations"].append(cited))
    assert intake.main(["gate", "summer-fair", "--folder", str(folder)]) == 0
    assert "24 situations checked" in capsys.readouterr().out
    packet = [
        "packet",
        "summer-fair",
        "--folder",
        str(folder),
        "--situations",
        str(out),
    ]
    assert intake.main(packet) == 0
    group = (folder / "packet.md").read_text().split("## Group: entry")[1]
    assert f"- `n01`: {NIGHT}" in group.split("## Group:")[0]
    label_all(folder)
    assert apply(folder, out) == 0
    cases = spec.read(out / "cases.yaml")["cases"]
    assert len(cases) == 25 and [c["id"] for c in cases].count("n01") == 1
    answers = spec.read(out / "summer-fair.yaml")
    assert answers["frames"]["entry"]["answers"]["n01"] == "open"
    assert situations.folder_problems(out, {"summer-fair": spec.read(FAIR)}.get) == []
    edit(folder, lambda d: d["frames"]["entry"]["situations"][-1].update(case="n99"))
    assert apply(folder, out, "--dry-run") == 2
    assert "n99: no such case in" in capsys.readouterr().err


def test_the_packet_refuses_a_writer_id_whose_packet_id_is_another_case(
    tmp_path, capsys
):
    folder, out = work(tmp_path), tmp_path / "situations"
    label_all(folder)
    assert apply(folder, out) == 0
    packet = [
        "packet",
        "summer-fair",
        "--folder",
        str(folder),
        "--situations",
        str(out),
    ]
    assert intake.main(packet) == 0
    edit(folder, lambda d: d["frames"]["entry"]["situations"][0].update(text=NIGHT))
    assert intake.main(packet) == 2
    assert (
        f"entry-c01 becomes {intake.opaque('entry-c01')}, already another case in"
        in capsys.readouterr().err
    )


def test_a_relabelled_set_replaces_its_answers_and_sets_left_out_are_kept(tmp_path):
    folder, out = work(tmp_path), tmp_path / "situations"
    extra = {"id": "permission-c25", "value": "nobody", "kind": "food", "who": "one"}
    extra["text"] = "A gran sells jars of jam from a trestle under the oak."
    edit(folder, lambda d: d["frames"]["permission"]["situations"].append(extra))
    label_all(folder)
    assert apply(folder, out) == 0
    stored, universes = out / "summer-fair.yaml", {"summer-fair": spec.read(FAIR)}.get
    old, new = "A licence from the local", "A permit from the local"
    stored.write_text(stored.read_text().replace(old, new))
    assert situations.folder_problems(out, universes) == [
        (
            "summer-fair.yaml: permission: stale answers: a value's meaning changed since "
            "labelling; relabel"
        )
    ]

    def redefine(draft):
        means = draft["frames"]["permission"]["means"]
        means["council"] = means["council"].replace(old, new)

    edit(folder, redefine)
    label_all(folder, lambda l: l.update({intake.opaque("permission-c25"): "unsure"}))
    assert apply(folder, out) == 0
    answers = spec.read(stored)
    assert (
        intake.opaque("permission-c25")
        not in answers["frames"]["permission"]["answers"]
    )
    assert situations.folder_problems(out, universes) == []
    edit(folder, lambda d: d["frames"].pop("entry"))
    label_all(folder)
    assert apply(folder, out) == 0
    assert spec.read(stored)["frames"]["entry"] == answers["frames"]["entry"]
    assert list(spec.read(stored)["frames"]) == ["entry", "permission"]


def test_a_set_left_out_of_the_draft_is_written_back_byte_for_byte(tmp_path):
    folder, out = work(tmp_path), tmp_path / "situations"
    label_all(folder)
    assert apply(folder, out) == 0
    stored = out / "summer-fair.yaml"
    before = stored.read_text().split("\nschema:", 1)[1]
    assert ": {value: nobody, near: organiser}\n" in before
    edit(folder, lambda d: d["frames"].pop("permission"))
    label_all(folder)
    assert apply(folder, out) == 0
    assert stored.read_text().split("\nschema:", 1)[1] == before


def test_disagreements_are_dropped_and_a_set_below_its_minimums_is_refused(
    tmp_path, capsys
):
    folder, out = work(tmp_path), tmp_path / "situations"

    def disagree(labels):
        labels[intake.opaque("entry-c01")] = "ticketed"
        labels[intake.opaque("permission-c13")] = "unsure"

    label_all(folder, disagree)
    assert apply(folder, out) == 1
    text = capsys.readouterr().out
    assert "entry: 11/12 agree (91.7%); 1 disagree" in text
    assert "[entry] entry-c01: written open; label ticketed (disagree)" in text
    assert "[permission] permission-c13: written nobody; label unsure (unsure)" in text
    assert "entry: open has 3 situations from summer-fair; needs at least 4" in text
    assert "REFUSED, nothing written" in text
    assert not out.exists()


def test_missing_labels_are_refused_and_a_fenced_reply_is_read(tmp_path, capsys):
    folder, out = work(tmp_path), tmp_path / "situations"
    labels = label_all(folder, lambda labels: labels.pop(intake.opaque("entry-c05")))
    assert apply(folder, out, "--dry-run") == 1
    assert "1 situation(s) have no label" in capsys.readouterr().out
    labels[intake.opaque("entry-c05")] = "ticketed"
    fenced = "Here you go:\n```json\n" + json.dumps({"labels": labels}) + "\n```\n"
    (folder / "labels.json").write_text(fenced)
    assert apply(folder, out, "--dry-run") == 0


def test_a_missing_labels_file_is_refused(tmp_path, capsys):
    assert apply(work(tmp_path), tmp_path / "situations", "--dry-run") == 2
    assert "no labels at" in capsys.readouterr().err


def test_the_universes_wording_is_never_printed(tmp_path, capsys):
    folder, out = work(tmp_path), tmp_path / "situations"

    def leak(draft):
        draft["frames"]["entry"]["situations"][3]["text"] = (
            "Visitors queue for lemonade."
        )

    edit(folder, leak)
    label_all(folder)
    assert apply(folder, out) == 1
    text = capsys.readouterr().out
    assert (
        f"entry/{intake.opaque('entry-c04')}: shares 1 word(s) with the wording" in text
    )
    assert "visitors" not in text.replace("Visitors queue", "")


def test_a_conflicting_case_or_a_lost_answer_is_refused(tmp_path, capsys):
    folder, out = work(tmp_path), tmp_path / "situations"
    label_all(folder)
    assert apply(folder, out) == 0
    answers = (out / "summer-fair.yaml").read_text()
    first = intake.opaque("entry-c01")
    (out / "summer-fair.yaml").write_text(
        answers.replace("    answers:\n", "    answers:\n      s-0000000: open\n", 1)
    )
    assert apply(folder, out) == 1
    assert "would drop 1 answer(s) already in" in capsys.readouterr().out
    (out / "summer-fair.yaml").write_text(answers)
    pool = (out / "cases.yaml").read_text()
    (out / "cases.yaml").write_text(pool.replace("A retired baker", "A young baker"))
    assert apply(folder, out) == 1
    assert f"case {first} is already in the pool with other content" in (
        capsys.readouterr().out
    )


def test_apply_keeps_the_tag_meanings_and_the_values_declared_absent(tmp_path, capsys):
    folder, out = work(tmp_path), tmp_path / "situations"
    label_all(folder)
    assert apply(folder, out) == 0
    assert spec.read(out / "cases.yaml")["tags"] == CASES["tags"]
    absent = {"kind": {"music": {"reason": "No bands.", "source": "a fair guide"}}}
    stored = out / "summer-fair.yaml"
    stored.write_text(stored.read_text() + yaml.safe_dump({"absent": absent}))
    pool = (out / "cases.yaml").read_text()
    listed = {tag: list(values) for tag, values in CASES["tags"].items()}
    edit(folder, lambda d: d.update(tags=listed))
    assert apply(folder, out) == 0
    assert (out / "cases.yaml").read_text() == pool
    assert spec.read(stored)["absent"] == absent
    assert list(spec.read(stored))[:5] == [
        "schema",
        "universe",
        "field",
        "absent",
        "frames",
    ]
    edit(folder, lambda d: d["tags"]["who"].remove("group"))
    assert apply(folder, out) == 1
    assert "the draft's tags differ from the pool's" in capsys.readouterr().out


def test_a_new_pool_needs_the_tag_meanings_from_the_draft(tmp_path, capsys):
    folder, out = work(tmp_path), tmp_path / "situations"
    label_all(folder)
    listed = {tag: list(values) for tag, values in CASES["tags"].items()}
    edit(folder, lambda d: d.update(tags=listed))
    assert apply(folder, out) == 2
    assert "a new pool needs a meaning for each tag value" in capsys.readouterr().err
    assert not out.exists()


def test_the_repository_pool_is_what_apply_writes():
    path = situations.FOLDER / situations.POOL
    pool = spec.read(path)
    cases = [c | {"tags": intake._Flow(c["tags"])} for c in pool["cases"]]
    written = intake.CASES_HEADER + intake._dump(pool | {"cases": cases})
    assert written == path.read_text()
