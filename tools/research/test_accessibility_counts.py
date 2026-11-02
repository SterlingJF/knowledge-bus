"""Regression checks for every frozen count, grade and seeded draw."""

import hashlib
import json
from pathlib import Path

import accessibility_counts as counts
import accessibility_leads as leads
import corpus_sample
import pytest

FIXTURES = counts.FIXTURES
DOC = (
    Path(__file__).resolve().parents[2]
    / "research/research-cognitive-accessibility-2026-10-17.md"
)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


# Every nested count and coded record from the original frozen run is covered.
# Direct comparisons below also tie the computed figures to the published tables.
RECORDED = {
    "captures": "e3fcbd2a2997101713781f84b5a3c1075fc8f62edff72031a01e6eff0ee8a7d7",
    "maintainer": "7c8b81d668f1ac910229c9c97b76bf9a054e0f694b947c29f40e31e49189d623",
    "corpus_a": "9bf357e2a633ddedee1f915d9179fd356e2dbe3f980549aa56fcb7414c8da3e5",
    "corpus_b": "e5823351df35d50ac5250610052335c4740c378c7c6a403030a8e89b339ccd8d",
    "situations": "c52d0c8d3c56bab8d305deb370c080076c9d9b2ddb20eca0b4d394d82df839fb",
    "sources": "7bc664cd2b6a659908bd52afa9f05cb29b91ab08ec330159b02c87f22d405dec",
}


@pytest.mark.parametrize("section", RECORDED)
def test_every_recorded_count_is_unchanged(section):
    assert digest(counts.run_all()[section]) == RECORDED[section]


def test_every_recorded_grade_and_support_count_is_unchanged():
    labels = counts.read_fixture(FIXTURES, "leads")
    result = leads.run(counts.run_all(), labels["values"], labels["factors"])
    assert (
        digest(result)
        == "c8ac7047230fc4b74dba5493365eb26ee42d2eb1617f3818ec66d7f48162e713"
    )


def test_draws_match_all_four_frozen_samples(tmp_path):
    expected = counts.read_fixture(FIXTURES, "draws")
    result = corpus_sample.adaptation_draws(
        FIXTURES / "adaptations-2026-10-17.jsonl", FIXTURES / "labels-2026-10-17.json"
    )
    assert result == expected
    assert [r["size"] for r in result.values()] == [19, 15, 5, 6]
    assert all(len(r["second_reader_subsample"]) == 5 for r in result.values())
    out = tmp_path / "draws.json"
    corpus_sample.main(
        [
            "--adaptations",
            str(FIXTURES / "adaptations-2026-10-17.jsonl"),
            "--labels",
            str(FIXTURES / "labels-2026-10-17.json"),
            "--out",
            str(out),
        ]
    )
    assert json.loads(out.read_text()) == expected


def test_count_and_grade_commands(tmp_path):
    assert counts.main(["--out", str(tmp_path)]) == 0
    assert json.loads((tmp_path / "counts.json").read_text()) == counts.run_all()
    assert (
        leads.main(["--counts", str(tmp_path / "counts.json"), "--out", str(tmp_path)])
        == 0
    )
    for name in (
        "corpus-a.tsv",
        "corpus-b.tsv",
        "situations.tsv",
        "factor-leads.tsv",
        "value-leads.tsv",
    ):
        assert (tmp_path / name).is_file()


def cells(line):
    return [v.strip() for v in line.strip("| ").split("|")]


def test_published_corpus_a_tables():
    result = counts.run_all()["corpus_a"]
    section = DOC.read_text().split("## Corpus A:")[1].split("## Corpus B:")[0]
    rows = [cells(line) for line in section.splitlines() if line.startswith("| A")]
    for row, (name, data) in zip(rows[:4], result.items(), strict=True):
        assert row[0].split()[0] == name[:2]
        assert list(map(int, row[2:6])) == [
            data["pairs_confirmed_by_reading"],
            data["pairs_unreadable"],
            len(data["publishers"]),
            data["need_stated_pairs"],
        ]
        for source, values in data["per_source"].items():
            assert (
                f"{source} {values['by_pattern']:,} by pattern, {values['read']} read"
                in row[1]
            )
    stated = section.split("Stated codes,")[1].split("Codes from sentences")[0]
    feature = section.split("Codes from sentences")[1].split("Presentation changes")[0]
    for table, key in [(stated, "coded_need_pairs"), (feature, "feature_code_pairs")]:
        for line in table.splitlines():
            if line.startswith(("| N", "| C", "| audience", "| none")):
                row = cells(line)
                code = row[0].split()[0] if row[0][0] in "NC" else row[0]
                if code not in counts.CODES and code not in (
                    counts.AUDIENCE_ONLY,
                    counts.NONE_STATED,
                ):
                    continue
                assert list(map(int, row[1:])) == [
                    d[key].get(code, 0) for d in result.values()
                ]


def test_published_situations_and_option_dimensions():
    result = counts.run_all()
    text = DOC.read_text()
    section = text.split("## Situation Candidates")[1]
    code_rows = [
        cells(line) for line in section.splitlines() if line.startswith(("| N", "| C"))
    ][:27]
    for row, data in zip(code_rows, result["situations"]["per_code"], strict=True):
        assert row[0].split()[0] == data["code"]
        assert list(map(int, row[1:4])) == [
            data["primary"],
            data["grades"].get("B", 0),
            data["any_mention"],
        ]
    for name, data in result["corpus_b"][
        "per_dimension_all_categories_listed_by_maker"
    ].items():
        assert f"| {name} | {data['options']} | {', '.join(data['makers'])} |" in text
    cats = list(result["corpus_b"]["per_category"].values())
    assert sum(c["included_confirmed_by_reading"] for c in cats) == 165
    assert sum(c["excluded_confirmed_by_reading"] for c in cats) == 26
    assert sum(s["rows"] for s in result["sources"].values()) == 136
    assert result["situations"]["total"] == 106
    assert result["situations"]["distinct_sources"] == 85


def test_bad_metadata_names_the_input(tmp_path):
    bad = tmp_path / "bad.jsonl"
    bad.write_text('{"url": "x"}\nnot json\n')
    with pytest.raises(counts.InputError, match="bad.jsonl line 2"):
        counts.read_jsonl(bad)
    table = tmp_path / "bad.tsv"
    table.write_text("id\n1\n")
    with pytest.raises(counts.InputError, match="missing columns"):
        counts.read_tsv(table, ("grade",))
