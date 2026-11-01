"""leads.py grades value and factor leads from counts and labels, per rules.md section 10."""

import accessibility_counts as counts
import accessibility_leads as leads
import pytest


def pair(pid, lst, pub, stated=(), policy=(), served=(), level="instance"):
    return {
        "pair_id": pid,
        "list": lst,
        "publisher": pub,
        "stated": list(stated),
        "stated_by_policy": list(policy),
        "served": list(served),
        "set_by_level": level,
    }


def make_counts(lists, options=(), situation_codes=None, policies=None):
    per_code = []
    for code in counts.CODES:
        n, grades = (situation_codes or {}).get(code, (0, {}))
        per_code.append({"code": code, "primary": n, "grades": grades, "short": n < 4})
    return {
        "corpus_a": {
            lst: {"pairs": rows, "policies": (policies or {}).get(lst, [])}
            for lst, rows in lists.items()
        },
        "corpus_b": {"options": list(options)},
        "situations": {"per_code": per_code},
    }


def value(
    vid="V", fid="F", codes="N3", lit="yes", b_codes="-", b_dims="-", exclusion="-"
):
    return {
        "value_id": vid,
        "factor_id": fid,
        "kind": "need",
        "label": vid,
        "codes": codes,
        "b_codes": b_codes,
        "b_dims": b_dims,
        "literature": lit,
        "literature_evidence": "-",
        "exclusion": exclusion,
        "note": "-",
    }


def factor(
    fid="F",
    values="V",
    conditions="-",
    c1="yes",
    c4="yes",
    use_time="no",
    gain="no",
    exclusion="-",
):
    return {
        "factor_id": fid,
        "name": fid,
        "gist": "-",
        "values": values,
        "conditions": conditions,
        "cond1": c1,
        "cond1_evidence": "-",
        "cond4": c4,
        "cond4_note": "-",
        "use_time": use_time,
        "gain_for_every_reader": gain,
        "moment_to_moment": "no",
        "moment_evidence": "-",
        "exclusion": exclusion,
        "protocol_note": "-",
    }


def five_pairs(lst, code, pubs=("P1", "P2")):
    return [
        pair(f"{lst}-{n}", lst, pubs[n % len(pubs)], served=[code]) for n in range(5)
    ]


def test_a_value_meeting_all_three_conditions_is_high():
    c = make_counts(
        {"L1": five_pairs("L1", "N3")}, situation_codes={"N3": (4, {"B": 4})}
    )
    g = leads.grade_value(value(), c)
    assert g["grade"] == "High" and g["corpus"]["corpus_a"]["L1"]["basis"] == {
        "served by a presentation change": 5
    }


def test_value_corpus_support_is_never_pooled_across_lists():
    c = make_counts(
        {"L1": five_pairs("L1", "N3")[:3], "L2": five_pairs("L2", "N3")[:3]},
        situation_codes={"N3": (4, {"B": 2, "C": 2})},
    )
    g = leads.grade_value(value(), c)
    assert not g["corpus"]["met"] and g["grade"] == "Medium"
    assert g["situations"] == {
        "candidates": 4,
        "b_or_better": 2,
        "grades": {"B": 2, "C": 2},
        "met": True,
    }


def test_value_corpus_needs_two_publishers_and_reads_policy_statements():
    one_pub = make_counts({"L1": five_pairs("L1", "N3", pubs=("P1",))})
    assert not leads.value_corpus(value(), one_pub)["met"]
    by_policy = make_counts(
        {"L1": [pair(f"p{n}", "L1", f"P{n % 2}", policy=["N3"]) for n in range(5)]}
    )
    vc = leads.value_corpus(value(), by_policy)
    assert vc["met"] and vc["corpus_a"]["L1"]["basis"] == {
        "stated by publisher policy": 5
    }


def test_value_corpus_from_options_by_code_or_by_dimension_only():
    opts = [
        {"maker": m, "codes": ["N9"], "dimension": "order or layout"}
        for m in ("A", "B", "C", "A", "B")
    ]
    opts += [{"maker": "A", "codes": [], "dimension": "motion"}]
    c = make_counts({}, options=opts)
    assert leads.value_corpus(value(codes="N9"), c)["corpus_b"] == {
        "options": 5,
        "makers": ["A", "B", "C"],
        "met": True,
    }
    only_dim = leads.value_corpus(
        value(codes="N9", b_codes="none", b_dims="motion"), c
    )["corpus_b"]
    assert only_dim == {"options": 1, "makers": ["A"], "met": False}


def test_literature_alone_is_low_and_an_exclusion_wins():
    c = make_counts({})
    assert leads.grade_value(value(), c)["grade"] == "Low"
    assert (
        leads.grade_value(value(exclusion="names a diagnosis"), c)["grade"]
        == "Excluded"
    )


def test_factor_high_needs_ten_pairs_three_publishers_and_two_values_in_one_list():
    rows = [
        pair(f"a{n}", "L1", f"P{n % 3}", stated=["N2" if n % 2 else "N3"])
        for n in range(10)
    ]
    c = make_counts(
        {"L1": rows}, situation_codes={"N2": (4, {"B": 4}), "N3": (4, {"B": 4})}
    )
    vals = [value("V1", codes="N2"), value("V2", codes="N3")]
    out = leads.run(c, vals, [factor(values="V1 V2")])
    f = out["factors"][0]
    assert (
        f["conditions"] == {"1": True, "2": True, "3": True, "4": True}
        and f["grade"] == "High"
    )
    assert f["corpus"]["corpus_a"]["L1"]["rows_covered"] == ["V1", "V2"]
    assert f["corpus"]["corpus_a"]["L1"]["set_by_from_stated_pairs"] == {"instance": 10}
    assert f["corpus"]["corpus_a"]["L1"]["set_by_from_pairs_under_a_policy"] == {}


def test_factor_set_by_keeps_policy_rows_and_pairs_under_a_policy_apart():
    rows = [pair(f"a{n}", "L1", "P1", policy=["C3"]) for n in range(4)]
    pols = {
        "L1": [
            {"set_by_level": "universe", "codes": ["C3"]},
            {"set_by_level": "scope", "codes": ["N1"]},
        ]
    }
    c = make_counts({"L1": rows}, policies=pols)
    out = leads.run(
        c, [value("V1", codes="N12")], [factor(values="V1", conditions="C3")]
    )
    lst = out["factors"][0]["corpus"]["corpus_a"]["L1"]
    assert lst["pairs"] == 0 and lst["set_by_from_stated_pairs"] == {}
    assert lst["set_by_from_pairs_under_a_policy"] == {"instance": 4}
    assert lst["set_by_from_policies"] == {"universe": 1}


def test_factor_floor_counts_pair_codes_only_and_never_pools():
    rows1 = [pair(f"a{n}", "L1", f"P{n % 3}", stated=["N2"]) for n in range(6)]
    rows2 = [pair(f"b{n}", "L2", f"P{n % 3}", stated=["N3"]) for n in range(6)]
    served = [pair(f"c{n}", "L3", f"P{n % 3}", served=["N2", "N3"]) for n in range(12)]
    c = make_counts({"L1": rows1, "L2": rows2, "L3": served})
    out = leads.run(
        c, [value("V1", codes="N2"), value("V2", codes="N3")], [factor(values="V1 V2")]
    )
    assert (
        out["factors"][0]["conditions"]["2"] is False
        and out["factors"][0]["grade"] == "Medium"
    )


def test_use_time_factor_meets_condition_two_with_three_makers():
    opts = [{"maker": m, "codes": [], "dimension": "motion"} for m in ("A", "B", "C")]
    c = make_counts({}, options=opts)
    v = value("V1", codes="N9", b_codes="none", b_dims="motion")
    timed = leads.run(c, [v], [factor(values="V1", use_time="yes")])["factors"][0]
    untimed = leads.run(c, [v], [factor(values="V1", use_time="no")])["factors"][0]
    assert timed["conditions"]["2"] and not untimed["conditions"]["2"]


def test_gain_for_every_reader_caps_a_factor_without_condition_one_at_low():
    opts = [{"maker": m, "codes": ["N9"], "dimension": "x"} for m in ("A", "B", "C")]
    c = make_counts({}, options=opts)
    v = value("V1", codes="N9")
    plain = leads.run(c, [v], [factor(values="V1", c1="no", use_time="yes")])[
        "factors"
    ][0]
    capped = leads.run(
        c, [v], [factor(values="V1", c1="no", use_time="yes", gain="yes: a source")]
    )["factors"][0]
    assert plain["grade"] == "Medium" and capped["grade"] == "Low"


def test_unknown_value_in_a_factor_row_is_refused():
    with pytest.raises(counts.InputError, match="unknown value V9"):
        leads.run(make_counts({}), [value("V1")], [factor(values="V1 V9")])


def test_moment_to_moment_list_names_only_high_or_medium_factors():
    c = make_counts({})
    f1 = factor("F1", values="V1", c1="yes")
    f1["moment_to_moment"] = "yes"
    f2 = factor("F2", values="V2", c1="no")
    f2["moment_to_moment"] = "yes"
    out = leads.run(c, [value("V1", "F1"), value("V2", "F2")], [f1, f2])
    assert out["moment_to_moment_high_or_medium"] == [
        {"factor_id": "F1", "grade": "Medium"}
    ]


def test_a_value_supported_only_by_a_short_list_grades_medium_at_most():
    c = make_counts(
        {"L1": five_pairs("L1", "N3")}, situation_codes={"N3": (4, {"B": 4})}
    )
    c["corpus_a"]["L1"]["short"] = True
    g = leads.grade_value(value(), c)
    assert g["corpus"]["met"] and g["corpus"]["short_list_only"]
    assert g["grade"] == "Medium"
