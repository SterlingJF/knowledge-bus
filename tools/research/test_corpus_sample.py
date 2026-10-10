"""The seeded reading sample: the same corpus and seed give the recorded 28 repositories."""

import json
from pathlib import Path

import corpus_sample

FIXTURES = Path(__file__).parent / "fixtures"
SEED = 20261008


def corpus():
    lines = (FIXTURES / "corpus-2026-10-08.jsonl").read_text().splitlines()
    return [json.loads(line) for line in lines]


def recorded():
    return json.loads((FIXTURES / "reading-slices-2026-10-08.json").read_text())


def test_two_runs_draw_the_same_sample():
    assert corpus_sample.slices(corpus(), SEED) == corpus_sample.slices(corpus(), SEED)


def test_input_order_leaves_the_sample_unchanged():
    assert corpus_sample.slices(corpus()[::-1], SEED) == corpus_sample.slices(
        corpus(), SEED
    )


def test_sample_matches_the_recorded_slices():
    drawn = corpus_sample.slices(corpus(), SEED)
    assert drawn == recorded()
    assert [len(s) for s in drawn["slices"]] == [7, 7, 7, 7]
    assert len({name for s in drawn["slices"] for name in s}) == 28


def test_another_seed_draws_another_sample():
    assert corpus_sample.slices(corpus(), SEED + 1)["slices"] != recorded()["slices"]
