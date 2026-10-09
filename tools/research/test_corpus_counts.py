"""corpus_counts.py computes the kind counts and the repository list from the list fields alone."""

import json
from pathlib import Path

import corpus_counts

FIXTURES = Path(__file__).parent / "fixtures"


def corpus(tmp_path):
    rows = [
        json.loads(line)
        for line in (FIXTURES / "corpus-2026-10-08.jsonl").read_text().splitlines()
    ]
    repos = [
        {**r, "archived": False, "files": {}, "listing": {}, "releases": {}}
        for r in rows
    ]
    return corpus_counts.Corpus(
        root=tmp_path, min_stars=3000, stars=rows, repos=repos, labels=FIXTURES
    )


def test_kinds_come_from_the_list_without_a_label_file(tmp_path):
    kinds = corpus_counts.repo_kinds(corpus(tmp_path))
    assert kinds["kinds"] == {"D": 74, "O": 33, "E": 30, "C": 5, "R": 4}
    assert kinds["developer_or_operator"] == 107


def test_first_pass_flag_marks_the_repositories_starred_later(tmp_path):
    later = corpus_counts.corpus_counts(corpus(tmp_path), "2026-10-03T18:00:00Z")
    assert later["starred_after_earlier_run"] == [
        "dolthub/dolt",
        "gastownhall/gastown",
        "harbor-framework/harbor",
    ]


def test_label_files_load_from_the_labels_folder(tmp_path):
    data = corpus(tmp_path)
    assert data.optional("of2-security-channel.json") == (
        FIXTURES / "of2-security-channel.json"
    )
    senses = corpus_counts.terms(data)["senses"]
    assert senses["maintainer"]["MP"] == 28


def test_repository_list_has_one_row_per_repository(tmp_path):
    table = corpus_counts.repo_list(corpus(tmp_path)).splitlines()
    assert len(table) == 2 + 146
    assert table[2].startswith("| AGWA/git-crypt | no | 9,944 | C++ | developer tool")
