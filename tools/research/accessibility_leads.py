"""Grade cognitive-accessibility leads from counts and recorded reader labels."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

from accessibility_counts import FIXTURES, InputError, read_fixture

PAIR_FLOOR, PAIR_PUBLISHERS, PAIR_VALUES = 10, 3, 2
USE_TIME_MAKERS = 3
VALUE_UNITS, VALUE_MAKERS = 5, 2
VALUE_SITUATIONS = 4
GRADE_ORDER = {"High": 3, "Medium": 2, "Low": 1, "Excluded": 0}


def codes_of(cell: str) -> list[str]:
    return [] if cell.strip() in ("", "-") else cell.split()


def yes(cell: str) -> bool:
    return cell.strip().lower().startswith("yes")


def value_corpus(value: dict, counts: dict) -> dict:
    codes = set(codes_of(value["codes"]))
    b_cell = value.get("b_codes", "-").strip()
    b_codes = set() if b_cell == "none" else (set(codes_of(b_cell)) or codes)
    b_dims = set(codes_of(value.get("b_dims", "-").replace(" ", "_")))
    per_list = {}
    for list_id, lst in counts["corpus_a"].items():
        hits = [
            p
            for p in lst["pairs"]
            if codes
            & (set(p["stated"]) | set(p["stated_by_policy"]) | set(p["served"]))
        ]
        basis = Counter()
        for p in hits:
            if codes & set(p["stated"]):
                basis["stated in pair"] += 1
            elif codes & set(p["stated_by_policy"]):
                basis["stated by publisher policy"] += 1
            else:
                basis["served by a presentation change"] += 1
        pubs = sorted({p["publisher"] for p in hits})
        per_list[list_id] = {
            "pairs": len(hits),
            "publishers": len(pubs),
            "basis": dict(basis),
            "met": len(hits) >= VALUE_UNITS and len(pubs) >= VALUE_MAKERS,
            "short": bool(lst.get("short")),
        }
    opts = [
        o
        for o in counts["corpus_b"]["options"]
        if b_codes & set(o["codes"]) or o["dimension"].replace(" ", "_") in b_dims
    ]
    makers = sorted({o["maker"] for o in opts})
    b = {
        "options": len(opts),
        "makers": makers,
        "met": len(opts) >= VALUE_UNITS and len(makers) >= VALUE_MAKERS,
    }
    met = any(v["met"] for v in per_list.values()) or b["met"]
    full = any(v["met"] and not v["short"] for v in per_list.values()) or b["met"]
    return {
        "met": met,
        "short_list_only": met and not full,
        "corpus_a": per_list,
        "corpus_b": b,
    }


def value_situations(value: dict, counts: dict) -> dict:
    codes = set(codes_of(value["codes"]))
    rows = [v for v in counts["situations"]["per_code"] if v["code"] in codes]
    primary = sum(v["primary"] for v in rows)
    graded = Counter()
    for v in rows:
        graded.update(v["grades"])
    b_or_better = graded.get("A", 0) + graded.get("B", 0)
    return {
        "candidates": primary,
        "b_or_better": b_or_better,
        "grades": dict(sorted(graded.items())),
        "met": primary >= VALUE_SITUATIONS,
    }


def grade_value(value: dict, counts: dict) -> dict:
    corpus = value_corpus(value, counts)
    sits = value_situations(value, counts)
    lit = yes(value["literature"])
    met = sum([lit, corpus["met"], sits["met"]])
    excluded = value.get("exclusion", "-").strip() not in ("", "-")
    grade = "Excluded" if excluded else {3: "High", 2: "Medium"}.get(met, "Low")
    if grade == "High" and corpus["short_list_only"]:
        grade = "Medium"
    return {
        "value_id": value["value_id"],
        "factor_id": value["factor_id"],
        "kind": value["kind"],
        "label": value["label"],
        "codes": codes_of(value["codes"]),
        "grade": grade,
        "literature": lit,
        "literature_evidence": value["literature_evidence"],
        "corpus": corpus,
        "situations": sits,
        "conditions_met": met,
        "note": value.get("note", "-"),
    }


def factor_codes(factor: dict, values: dict[str, dict]) -> dict[str, set[str]]:
    rows = {}
    for vid in codes_of(factor["values"]):
        rows[vid] = set(codes_of(values[vid]["codes"])) if vid in values else set()
    for code in codes_of(factor["conditions"]):
        rows.setdefault(code, set()).add(code)
    return rows


def factor_corpus(factor: dict, values: dict[str, dict], counts: dict) -> dict:
    rows = factor_codes(factor, values)
    allc = set().union(*rows.values()) if rows else set()
    per_list = {}
    for list_id, lst in counts["corpus_a"].items():
        hits = [p for p in lst["pairs"] if allc & set(p["stated"])]
        covered = sorted(
            r for r, cs in rows.items() if any(cs & set(p["stated"]) for p in hits)
        )
        pubs = sorted({p["publisher"] for p in hits})
        per_list[list_id] = {
            "pairs": len(hits),
            "publishers": len(pubs),
            "rows_covered": covered,
            "met": len(hits) >= PAIR_FLOOR
            and len(pubs) >= PAIR_PUBLISHERS
            and len(covered) >= PAIR_VALUES,
            "set_by_from_stated_pairs": dict(Counter(p["set_by_level"] for p in hits)),
            "set_by_from_pairs_under_a_policy": dict(
                Counter(
                    p["set_by_level"]
                    for p in lst["pairs"]
                    if allc & set(p["stated_by_policy"]) and not allc & set(p["stated"])
                )
            ),
            "set_by_from_policies": dict(
                Counter(
                    pol["set_by_level"]
                    for pol in lst["policies"]
                    if allc & set(pol["codes"])
                )
            ),
        }
    makers: set[str] = set()
    n_opts = 0
    for vid in codes_of(factor["values"]):
        if vid in values:
            vc = value_corpus(values[vid], counts)["corpus_b"]
            makers |= set(vc["makers"])
            n_opts += vc["options"]
    use_time = yes(factor["use_time"])
    b = {
        "options": n_opts,
        "makers": sorted(makers),
        "met": use_time and len(makers) >= USE_TIME_MAKERS,
    }
    return {
        "met": any(v["met"] for v in per_list.values()) or b["met"],
        "corpus_a": per_list,
        "corpus_b": b,
    }


def grade_factor(
    factor: dict, values: dict[str, dict], graded_values: dict[str, dict], counts: dict
) -> dict:
    excluded = factor["exclusion"].strip() not in ("", "-")
    c1 = yes(factor["cond1"])
    corpus = factor_corpus(factor, values, counts)
    c2 = corpus["met"]
    proposed = codes_of(factor["values"])
    value_grades = {
        v: graded_values[v]["grade"] for v in proposed if v in graded_values
    }
    c3 = bool(value_grades) and all(GRADE_ORDER[g] >= 2 for g in value_grades.values())
    c4 = yes(factor["cond4"])
    gain_all = yes(factor["gain_for_every_reader"])
    if excluded:
        grade = "Excluded"
    elif gain_all and not c1:
        grade = "Low"
    elif c1 and c2 and c3 and c4:
        grade = "High"
    elif c1 or c2:
        grade = "Medium"
    else:
        grade = "Low"
    return {
        "factor_id": factor["factor_id"],
        "name": factor["name"],
        "gist": factor["gist"],
        "grade": grade,
        "conditions": {"1": c1, "2": c2, "3": c3, "4": c4},
        "cond1_evidence": factor["cond1_evidence"],
        "cond4_note": factor["cond4_note"],
        "value_grades": value_grades,
        "corpus": corpus,
        "gain_for_every_reader": factor["gain_for_every_reader"],
        "moment_to_moment": yes(factor["moment_to_moment"]),
        "moment_label": factor["moment_to_moment"],
        "moment_evidence": factor["moment_evidence"],
        "set_by_evidence": factor.get("set_by_evidence", "-"),
        "set_by_lead": factor.get("set_by_lead", "-"),
        "exclusion": factor["exclusion"],
        "protocol_note": factor["protocol_note"],
    }


def run(counts: dict, values_rows: list[dict], factor_rows: list[dict]) -> dict:
    values = {v["value_id"]: v for v in values_rows}
    for f in factor_rows:
        for vid in codes_of(f["values"]):
            if vid not in values:
                raise InputError(f"{f['factor_id']} names unknown value {vid}")
    graded_values = {vid: grade_value(v, counts) for vid, v in values.items()}
    graded_factors = [
        grade_factor(f, values, graded_values, counts) for f in factor_rows
    ]
    moment = [
        {"factor_id": f["factor_id"], "grade": f["grade"]}
        for f in graded_factors
        if f["moment_to_moment"] and f["grade"] in ("High", "Medium")
    ]
    return {
        "values": list(graded_values.values()),
        "factors": graded_factors,
        "moment_to_moment_high_or_medium": moment,
    }


def write_tsv(result: dict, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    with (out / "factor-leads.tsv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(
            [
                "factor",
                "name",
                "grade",
                "c1",
                "c2",
                "c3",
                "c4",
                "values",
                "best list (pairs/publishers)",
                "Corpus B makers",
                "moment_to_moment",
            ]
        )
        for f in result["factors"]:
            lists = f["corpus"]["corpus_a"]
            best = (
                max(lists.items(), key=lambda kv: (kv[1]["pairs"], kv[1]["publishers"]))
                if lists
                else ("-", {"pairs": 0, "publishers": 0})
            )
            w.writerow(
                [
                    f["factor_id"],
                    f["name"],
                    f["grade"],
                    *("yes" if f["conditions"][k] else "no" for k in "1234"),
                    " ".join(f"{k}:{v}" for k, v in f["value_grades"].items()),
                    f"{best[0]} {best[1]['pairs']}/{best[1]['publishers']}",
                    len(f["corpus"]["corpus_b"]["makers"]),
                    "yes" if f["moment_to_moment"] else "no",
                ]
            )
    with (out / "value-leads.tsv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(
            [
                "value",
                "factor",
                "kind",
                "codes",
                "grade",
                "literature",
                "corpus",
                "best list (pairs/publishers)",
                "Corpus B options/makers",
                "situations (B or better)",
            ]
        )
        for v in result["values"]:
            lists = v["corpus"]["corpus_a"]
            best = max(
                lists.items(),
                key=lambda kv: (kv[1]["met"], kv[1]["pairs"], kv[1]["publishers"]),
            )
            b = v["corpus"]["corpus_b"]
            w.writerow(
                [
                    v["value_id"],
                    v["factor_id"],
                    v["kind"],
                    " ".join(v["codes"]) or "-",
                    v["grade"],
                    "yes" if v["literature"] else "no",
                    "yes" if v["corpus"]["met"] else "no",
                    f"{best[0]} {best[1]['pairs']}/{best[1]['publishers']}",
                    f"{b['options']}/{len(b['makers'])}",
                    f"{v['situations']['candidates']} ({v['situations']['b_or_better']})",
                ]
            )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--counts", type=Path, required=True)
    parser.add_argument("--fixtures", type=Path, default=FIXTURES)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    labels = read_fixture(args.fixtures, "leads")
    result = run(
        json.loads(args.counts.read_text(encoding="utf-8")),
        labels["values"],
        labels["factors"],
    )
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "leads.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    write_tsv(result, args.out)
    print(json.dumps({f["factor_id"]: f["grade"] for f in result["factors"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
