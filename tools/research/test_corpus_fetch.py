"""Given the repository list, corpus_fetch.py keeps the listed corpus and the frozen star counts."""

import json
from pathlib import Path

import corpus_fetch
import pytest

LIST = Path(__file__).parent / "fixtures" / "corpus-2026-10-08.jsonl"


def listed():
    return [json.loads(line) for line in LIST.read_text().splitlines()]


class FakeGitHub:
    """Answers `repos/{name}` with live-looking values and records every call."""

    def __init__(self, missing=()):
        self.paths = []
        self.missing = set(missing)

    def json(self, path):
        self.paths.append(path)
        name = path.removeprefix("repos/")
        if name in self.missing:
            return None
        return {
            "full_name": name,
            "stargazers_count": 1,
            "language": "Live",
            "default_branch": "main",
            "archived": False,
            "fork": False,
            "license": {"spdx_id": "MIT"},
        }

    def run(self, *args):
        self.paths.append(args[-1])
        raise RuntimeError("stop after the first tree call")


def test_list_gives_the_146_repositories_with_frozen_values(tmp_path):
    gh = FakeGitHub()
    corpus_fetch.stage_listed(gh, tmp_path, LIST, 3000)
    rows = corpus_fetch.corpus(tmp_path, 3000)
    want = listed()
    assert len(rows) == len(want) == 146
    assert gh.paths == [f"repos/{r['full_name']}" for r in want]
    frozen = {r["full_name"]: r for r in want}
    for row in rows:
        listed_row = frozen[row["full_name"]]
        assert row["stars"] == listed_row["stars"]
        assert row["language"] == listed_row["language"]
        assert row["kind"] == listed_row["kind"]
        assert row["first_pass"] == listed_row["first_pass"]
        assert row["default_branch"] == "main"
    info = json.loads((tmp_path / "run-info.json").read_text())
    assert info["listed"] == info["corpus"] == 146


def test_missing_repository_stays_in_the_corpus(tmp_path):
    gone = listed()[0]["full_name"]
    corpus_fetch.stage_listed(FakeGitHub(missing={gone}), tmp_path, LIST, 3000)
    rows = {r["full_name"]: r for r in corpus_fetch.corpus(tmp_path, 3000)}
    assert gone in rows
    assert rows[gone]["default_branch"] is None


def test_tree_fetch_falls_back_to_head(tmp_path):
    (tmp_path / "repos").mkdir()
    record = {"full_name": "owner/name", "default_branch": None}
    (tmp_path / "repos" / "owner__name.json").write_text(json.dumps(record))
    gh = FakeGitHub()
    with pytest.raises(RuntimeError):
        corpus_fetch.stage_trees(gh, tmp_path)
    assert gh.paths == ["repos/owner/name/git/trees/HEAD?recursive=1"]


def test_stars_stage_takes_account_or_list(tmp_path):
    with pytest.raises(SystemExit):
        corpus_fetch.main(["--out", str(tmp_path)])
    with pytest.raises(SystemExit):
        corpus_fetch.main(
            ["--account", "a", "--repos", str(LIST), "--out", str(tmp_path)]
        )
