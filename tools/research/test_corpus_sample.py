"""The seeded reading sample: the same corpus and seed give the recorded 28 repositories."""

import json
import random
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


def cand(source, n, publisher):
    return {
        "list": "T",
        "index_source": source,
        "title": f"{source} {n}",
        "url": f"https://example.org/{source}/{n:03d}",
        "publisher": publisher,
    }


def test_seeded_order_sorts_by_url_then_shuffles_with_a_fresh_generator():
    cands = [cand("s", n, "P") for n in (5, 1, 3, 2, 4)]
    expected = sorted(cands, key=lambda c: c["url"])
    random.Random(20261017).shuffle(expected)
    assert corpus_sample.adaptation_order(cands) == expected
    assert corpus_sample.adaptation_order(list(reversed(cands))) == expected


def test_draw_alternates_sources_and_caps_each_publisher():
    cands = [cand("a", n, "OneOrg") for n in range(10)]
    cands += [cand("b", n, f"Org{n % 3}") for n in range(30)]
    labels = {c["url"]: {"url": c["url"], "status": "eligible"} for c in cands}
    result = corpus_sample.adaptation_draw(cands, labels, target=12, cap=5)
    assert result["size"] == 12
    assert result["picks_per_source"] == {"a": 5, "b": 7}
    assert max(result["picks_per_publisher"].values()) <= 5
    # the first ten picks alternate a, b while source a still has an uncapped publisher
    assert [p["source"] for p in result["picks"][:10]] == ["a", "b"] * 5
    assert "publisher cap" in result["sources_ended"]["a"]
    assert result["complete"] is True


def test_draw_stops_at_an_unread_candidate_and_lists_it_pending():
    cands = [cand("a", n, "P") for n in range(6)]
    order = corpus_sample.adaptation_order(cands)
    labels = {
        order[0]["url"]: {"status": "skip", "reason": "no original linked"},
        order[1]["url"]: {
            "status": "eligible",
            "original_url": "https://example.org/o",
        },
    }
    result = corpus_sample.adaptation_draw(cands, labels, target=3, cap=5, pending_n=2)
    assert result["size"] == 1
    assert result["picks"][0]["original_url"] == "https://example.org/o"
    assert result["skips"] == [
        {
            "source": "a",
            "url": order[0]["url"],
            "title": order[0]["title"],
            "status": "skip",
            "reason": "no original linked",
        }
    ]
    assert result["pending"] == {"a": [order[2]["url"], order[3]["url"]]}
    assert result["complete"] is False
    assert result["short"] is True


def test_draw_skips_capped_publishers_unread_and_counts_unreadable_and_no_original():
    cands = [cand("a", n, "Big" if n < 4 else "Small") for n in range(8)]
    order = corpus_sample.adaptation_order(cands)
    labels = {}
    for c in order:
        labels[c["url"]] = {"status": "eligible"}
    first_small = next(c for c in order if c["publisher"] == "Small")
    labels[first_small["url"]] = {"status": "unreadable", "reason": "HTTP 403"}
    result = corpus_sample.adaptation_draw(cands, labels, target=8, cap=2)
    statuses = [s["status"] for s in result["skips"]]
    assert "unreadable" in statuses
    assert result["picks_per_publisher"] == {"Big": 2, "Small": 2}
    assert all(
        "not read" in s["reason"] for s in result["skips"] if s["status"] == "skip"
    )


def test_second_reader_subsample_is_seeded_and_drawn_from_picks():
    cands = [cand("a", n, f"P{n}") for n in range(12)]
    labels = {c["url"]: {"status": "eligible"} for c in cands}
    one = corpus_sample.adaptation_draw(cands, labels, target=10)
    two = corpus_sample.adaptation_draw(list(reversed(cands)), labels, target=10)
    assert one["second_reader_subsample"] == two["second_reader_subsample"]
    assert len(one["second_reader_subsample"]) == 5
    assert set(one["second_reader_subsample"]) <= {p["url"] for p in one["picks"]}
