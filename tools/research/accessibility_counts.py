"""Recount the frozen cognitive-accessibility coding metadata, without page captures."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

CODES = [f"N{i}" for i in range(1, 18)] + [f"C{i}" for i in range(1, 11)]
CODE_RE = re.compile(r"\b([NC]\d{1,2})\b")
NONE_STATED = "none stated"
AUDIENCE_ONLY = "audience named, no need stated"
CHANGE_FIELDS = [
    "wording_level",
    "length",
    "order",
    "summary_first",
    "images_beside_text",
    "chunking",
    "audio",
]
# A presentation change that serves a coded need (rules.md section 10, "state or
# serve"). The order field serves no single need, so it maps to nothing.
CHANGE_SERVES = {
    "wording_level": "N1",
    "length": "N3",
    "summary_first": "N2",
    "images_beside_text": "N5",
    "chunking": "N7",
    "audio": "N6",
}
# Keyword rule over the coder's "other" cell: the adaptation drops part of the
# original's content. A count from this rule is "by pattern" over coder notes.
CONTENT_CUT = re.compile(
    r"\b(content cut|cuts? in detail|drops?|leaves out)\b", re.IGNORECASE
)
MIN_CANDIDATES = 4
# The time scale over which the same reader's need changes, labelled per candidate.
CHANGE_SCALES = (
    "within one reading",
    "between readings",
    "per document",
    "over weeks or months",
)
# Scales that count as a value changing from moment to moment (the candidate
# protocol item); a per-document change is set_by evidence for `instance`.
MOMENT_SCALES = ("within one reading", "between readings")


class InputError(ValueError):
    """A list file or table that cannot be read as the rules describe."""


# ---------------------------------------------------------------- files


def read_jsonl(path: Path) -> list[dict]:
    """One JSON object per line; blank lines are skipped; a bad line names its number."""
    if not path.exists():
        raise InputError(f"missing list file: {path}")
    rows = []
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as err:
                raise InputError(
                    f"{path.name} line {number}: not JSON ({err.msg})"
                ) from err
            if not isinstance(row, dict):
                raise InputError(f"{path.name} line {number}: not a JSON object")
            rows.append(row)
    return rows


def read_tsv(path: Path, required: tuple[str, ...] = ()) -> list[dict]:
    if not path.exists():
        raise InputError(f"missing table: {path}")
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        missing = [c for c in required if c not in (reader.fieldnames or [])]
        if missing:
            raise InputError(f"{path.name}: missing columns {missing}")
        return list(reader)


def split_codes(cell: str) -> list[str]:
    """Codes in a coded-need cell, plus the two codes that name no need."""
    cell = (cell or "").strip()
    if not cell:
        return []
    out = []
    lowered = cell.lower()
    if AUDIENCE_ONLY in lowered:
        out.append(AUDIENCE_ONLY)
    if NONE_STATED in lowered and not CODE_RE.search(cell):
        out.append(NONE_STATED)
    out += [c for c in CODE_RE.findall(cell) if c in CODES]
    return list(dict.fromkeys(out))


def change_value(cell: str) -> str:
    """yes, no or unclear from a cell such as 'yes: 539 words against 7,668'."""
    head = (cell or "").split(":")[0].split(",")[0].strip().lower()
    for word in ("yes", "no", "unclear"):
        if head == word or head.startswith(word + " "):
            return word
    return "blank" if not head else "other"


def confirmed(row: dict) -> bool:
    return row.get("confirmation", "").startswith("confirmed by reading")


# ---------------------------------------------------------------- Corpus A


def pair_record(row: dict, policy_codes: dict[tuple[str, str], set[str]]) -> dict:
    stated = [c for c in split_codes(row["coded_need"]) if c in CODES]
    # A code from a sentence describing the edition's features is a need the
    # edition serves, never a stated need (coding rule (a), step 2).
    feature = [c for c in split_codes(row.get("feature_codes", "")) if c in CODES]
    served = sorted(
        {
            code
            for field, code in CHANGE_SERVES.items()
            if change_value(row.get(field, "")) == "yes"
        }
        | set(feature)
    )
    by_policy = sorted(policy_codes.get((row["list"], row["publisher"]), set()))
    return {
        "pair_id": row["pair_id"],
        "list": row["list"],
        "publisher": row["publisher"],
        "stated": stated,
        "stated_by_policy": by_policy,
        "feature": feature,
        "served": served,
        "set_by_level": row.get("set_by_level", ""),
        "content_cut_by_pattern": bool(CONTENT_CUT.search(row.get("other", ""))),
    }


def corpus_a(
    lists: dict[str, list[dict]],
    labels: dict[str, list[dict]],
    pairs: list[dict],
    policies: list[dict],
) -> dict:
    """Counts per list: candidates by pattern and read, pairs confirmed by reading,
    coded needs, units covered, presentation changes, and policy rows apart."""
    policy_codes: dict[tuple[str, str], set[str]] = defaultdict(set)
    for pol in policies:
        for code in split_codes(pol["coded_need"]):
            if code in CODES:
                policy_codes[(pol["list"], pol["publisher"])].add(code)
    out: dict[str, dict] = {}
    for list_id in sorted(set(lists) | {p["list"] for p in pairs}):
        cands = lists.get(list_id, [])
        labs = {lab["url"]: lab for lab in labels.get(list_id, [])}
        per_source = {}
        for src in sorted({c["index_source"] for c in cands}):
            urls = {c["url"] for c in cands if c["index_source"] == src}
            status = Counter(labs[u]["status"] for u in urls if u in labs)
            method = Counter(labs[u].get("method", "read") for u in urls if u in labs)
            screened = sum(n for m, n in method.items() if m.startswith("screened"))
            per_source[src] = {
                "by_pattern": len(urls),
                "labelled": sum(status.values()),
                "read": sum(status.values()) - screened,
                "screened_by_pattern": screened,
                "method": dict(sorted(method.items())),
                "label_status": dict(sorted(status.items())),
            }
        rows = [r for r in pairs if r["list"] == list_id]
        good = [r for r in rows if confirmed(r)]
        unreadable = [r for r in rows if not confirmed(r)]
        coded = Counter()
        feature_coded = Counter()
        for r in good:
            for code in split_codes(r["coded_need"]) or [NONE_STATED]:
                coded[code] += 1
            for code in split_codes(r.get("feature_codes", "")):
                if code in CODES:
                    feature_coded[code] += 1
        records = [pair_record(r, policy_codes) for r in good]
        stated_pubs: dict[str, set[str]] = defaultdict(set)
        for rec in records:
            for code in rec["stated"]:
                stated_pubs[code].add(rec["publisher"])
        changes = {
            f: dict(sorted(Counter(change_value(r.get(f, "")) for r in good).items()))
            for f in CHANGE_FIELDS
        }
        pols = [p for p in policies if p["list"] == list_id]
        out[list_id] = {
            "candidates_by_pattern": len(cands),
            "candidates_read": sum(s["read"] for s in per_source.values()),
            "per_source": per_source,
            "pairs_confirmed_by_reading": len(good),
            "pairs_unreadable": len(unreadable),
            "short": len(good) < 10,
            "publishers": dict(sorted(Counter(r["publisher"] for r in good).items())),
            "coded_need_pairs": dict(sorted(coded.items())),
            "feature_code_pairs": dict(sorted(feature_coded.items())),
            "need_stated_pairs": sum(1 for rec in records if rec["stated"]),
            "stated_publishers": {c: sorted(p) for c, p in sorted(stated_pubs.items())},
            "set_by_from_pairs": dict(
                sorted(Counter(r.get("set_by_level", "") for r in good).items())
            ),
            "presentation_changes": changes,
            "content_cut_by_pattern": sum(
                1 for rec in records if rec["content_cut_by_pattern"]
            ),
            "policy_rows": len(pols),
            "set_by_from_policies": dict(
                sorted(Counter(p["set_by_level"] for p in pols).items())
            ),
            "policy_reach_by_pattern_only": sum(
                1 for p in pols if "by pattern" in p.get("reach", "")
            ),
            "pairs": records,
            "policies": [
                {
                    "policy_id": p.get("policy_id", ""),
                    "publisher": p["publisher"],
                    "set_by_level": p["set_by_level"],
                    "codes": [c for c in split_codes(p["coded_need"]) if c in CODES],
                    "reach_by_pattern_only": "by pattern" in p.get("reach", ""),
                }
                for p in pols
            ],
        }
    return out


# ---------------------------------------------------------------- Corpus B


def behaviour(cell: str) -> str:
    cell = (cell or "").lower()
    if cell.startswith("none found"):
        return "none found"
    if cell.startswith("related"):
        return "related study only"
    return cell or "blank"


def option_codes(row: dict) -> list[str]:
    return [c for c in CODE_RE.findall(row.get("need_code", "")) if c in CODES]


def corpus_b(options: list[dict]) -> dict:
    """Counts per product category: dimensions, where set, carries across documents,
    changed during use (affordance and behaviour kept apart), and need codes."""
    cats: dict[str, dict] = {}
    for cat in sorted({o["category"] for o in options}):
        rows = [o for o in options if o["category"] == cat]
        inc = [o for o in rows if o["status"] == "included"]
        exc = [o for o in rows if o["status"] == "excluded"]
        makers_by_dim: dict[str, set[str]] = defaultdict(set)
        for o in inc:
            makers_by_dim[o["presentation_dimension"]].add(o["maker"])
        cats[cat] = {
            "products": sorted({o["product"] for o in rows}),
            "makers": sorted({o["maker"] for o in rows}),
            "included_confirmed_by_reading": sum(1 for o in inc if confirmed(o)),
            "excluded_confirmed_by_reading": sum(1 for o in exc if confirmed(o)),
            "excluded_classes": dict(
                Counter(o["exclusion_class"] for o in exc).most_common()
            ),
            "per_dimension": dict(
                Counter(o["presentation_dimension"] for o in inc).most_common()
            ),
            "makers_per_dimension": {
                d: sorted(m) for d, m in sorted(makers_by_dim.items())
            },
            "perceptual_flagged": sum(1 for o in inc if o.get("perceptual_flag")),
            "setting_place": dict(
                Counter(o["setting_place"] for o in inc).most_common()
            ),
            "option_kind": dict(Counter(o["option_kind"] for o in inc).most_common()),
            "carries_across_documents": dict(
                Counter(o["carries_across_documents"] for o in inc).most_common()
            ),
            "changed_during_use_affordance": dict(
                Counter(o["changed_during_use_affordance"] for o in inc).most_common()
            ),
            "changed_during_use_behaviour": dict(
                Counter(
                    behaviour(o["changed_during_use_behaviour"]) for o in inc
                ).most_common()
            ),
        }
    inc_all = [o for o in options if o["status"] == "included"]
    codes: dict[str, dict] = {}
    for code in CODES:
        hits = [o for o in inc_all if code in option_codes(o)]
        if hits:
            codes[code] = {
                "options": len(hits),
                "makers": sorted({o["maker"] for o in hits}),
                "basis": dict(Counter(o.get("need_basis") or "blank" for o in hits)),
            }
    dims: dict[str, dict] = {}
    for dim in sorted({o["presentation_dimension"] for o in inc_all}):
        hits = [o for o in inc_all if o["presentation_dimension"] == dim]
        dims[dim] = {
            "options": len(hits),
            "makers": sorted({o["maker"] for o in hits}),
            "setting_place": dict(
                Counter(o["setting_place"] for o in hits).most_common()
            ),
            "carries_across_documents": dict(
                Counter(o["carries_across_documents"] for o in hits).most_common()
            ),
            "changed_during_use_affordance": dict(
                Counter(o["changed_during_use_affordance"] for o in hits).most_common()
            ),
        }
    return {
        "denominator": "options confirmed by reading on the maker's own help page; no count by pattern",
        "per_category": cats,
        "need_codes": codes,
        "per_dimension_all_categories_listed_by_maker": dims,
        "options": [
            {
                "option_id": o["option_id"],
                "category": o["category"],
                "maker": o["maker"],
                "dimension": o["presentation_dimension"],
                "codes": option_codes(o),
                "setting_place": o["setting_place"],
                "affordance": o["changed_during_use_affordance"],
            }
            for o in inc_all
        ],
    }


# ---------------------------------------------------------------- situations


def primary_code(cell: str) -> str:
    found = CODE_RE.search(cell or "")
    if not found or found.group(1) not in CODES:
        raise InputError(f"draft value without a section 3 code: {cell!r}")
    return found.group(1)


def situations(
    rows: list[dict],
    private: list[dict] | None = None,
    values: dict[str, list[str]] | None = None,
) -> dict:
    """Candidates per draft value (primary code) and per tag value. With a value map
    (value id to codes), also per value lead and per value lead and tag."""
    deidentified = bool(rows) and "grade" in rows[0]
    if deidentified:
        grade = {r["id"]: r.get("grade") or "?" for r in rows}
        also = {
            r["id"]: [c for c in (r.get("also") or "").split() if c in CODES]
            for r in rows
        }
    else:
        grade = {c["id"]: c.get("grade") or "?" for c in (private or [])}
        also = {c["id"]: c.get("also") or [] for c in (private or [])}
    known = deidentified or private is not None
    per_code = []
    prim = Counter(primary_code(r["draft_value"]) for r in rows)
    mention = Counter()
    graded: dict[str, Counter] = defaultdict(Counter)
    for r in rows:
        code = primary_code(r["draft_value"])
        graded[code][grade.get(r["id"], "?")] += 1
        for c in {code, *also.get(r["id"], [])}:
            mention[c] += 1
    for code in CODES:
        per_code.append(
            {
                "code": code,
                "primary": prim[code],
                "any_mention": mention[code] if known else None,
                "grades": dict(sorted(graded[code].items())),
                "short": prim[code] < MIN_CANDIDATES,
            }
        )
    out = {
        "total": len(rows),
        "per_code": per_code,
        "kind": dict(sorted(Counter(r["kind"] for r in rows).items())),
        "who": dict(sorted(Counter(r["who"] for r in rows).items())),
        "short_codes": [v["code"] for v in per_code if v["short"]],
    }
    if deidentified:
        out["grade"] = dict(sorted(Counter(grade[r["id"]] for r in rows).items()))
        out["distinct_sources"] = len({r["source_group"] for r in rows})
        out["source_type"] = dict(
            sorted(Counter(r.get("source_type") or "?" for r in rows).items())
        )
        scale = {r["id"]: (r.get("change_scale") or "-") for r in rows}
    elif private is not None:
        out["grade"] = dict(
            sorted(Counter(grade.get(r["id"], "?") for r in rows).items())
        )
        by_id = {c["id"]: c for c in private}
        kept = [by_id[r["id"]] for r in rows if r["id"] in by_id]
        out["distinct_sources"] = len(
            {f"{c.get('url', '')}#{c.get('record', '')}" for c in kept}
        )
        out["source_type"] = dict(
            sorted(Counter(c.get("source_type") or "?" for c in kept).items())
        )
        scale = {c["id"]: (c.get("change_scale") or "-") for c in kept}
    else:
        scale = None
    if scale is not None:
        per_scale = {
            s: sorted(i for i, v in scale.items() if v == s) for s in CHANGE_SCALES
        }
        unknown = sorted(
            {v for v in scale.values() if v not in CHANGE_SCALES and v != "-"}
        )
        if unknown:
            raise InputError(f"unknown change scale {unknown}")
        out["change_scale"] = {s: len(ids) for s, ids in per_scale.items()}
        out["change_scale_ids"] = per_scale
        out["change_during_use"] = sum(len(per_scale[s]) for s in CHANGE_SCALES)
        out["moment_to_moment"] = sum(len(per_scale[s]) for s in MOMENT_SCALES)
    if values:
        per_value = {}
        for value_id, codes in values.items():
            hits = [r for r in rows if primary_code(r["draft_value"]) in codes]
            per_value[value_id] = {
                "codes": codes,
                "primary": len(hits),
                "b_or_better": sum(1 for r in hits if grade.get(r["id"]) in ("A", "B"))
                if known
                else None,
                "kind": dict(sorted(Counter(r["kind"] for r in hits).items())),
                "who": dict(sorted(Counter(r["who"] for r in hits).items())),
                "ids": sorted(r["id"] for r in hits),
                "short": len(hits) < MIN_CANDIDATES,
            }
        out["per_value_lead"] = per_value
    return out


# ---------------------------------------------------------------- sources


def source_table(rows: list[dict]) -> dict:
    """Grades and read scope for one graded-source table, whichever lane wrote it."""

    def grade_of(r: dict) -> str:
        g = (r.get("grade") or "").strip()
        return g if g in ("A", "B", "C") else "ungraded"

    def scope_of(r: dict) -> str:
        return (r.get("readable") or r.get("scope") or "").strip() or "blank"

    return {
        "rows": len(rows),
        "grade": dict(sorted(Counter(grade_of(r) for r in rows).items())),
        "read_scope": dict(sorted(Counter(scope_of(r) for r in rows).items())),
    }


# ---------------------------------------------------------------- captures


def write_tables(counts: dict, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    with (out / "corpus-a.tsv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["list", "measure", "value", "count"])
        for list_id, c in counts["corpus_a"].items():
            w.writerow(
                [list_id, "candidates", "by pattern", c["candidates_by_pattern"]]
            )
            w.writerow([list_id, "candidates", "read", c["candidates_read"]])
            w.writerow(
                [
                    list_id,
                    "pairs",
                    "confirmed by reading",
                    c["pairs_confirmed_by_reading"],
                ]
            )
            w.writerow([list_id, "pairs", "unreadable", c["pairs_unreadable"]])
            w.writerow([list_id, "pairs", "need stated", c["need_stated_pairs"]])
            for k, v in c["coded_need_pairs"].items():
                w.writerow([list_id, "coded need", k, v])
            for k, v in c["set_by_from_pairs"].items():
                w.writerow([list_id, "set_by from pairs", k, v])
            for k, v in c["set_by_from_policies"].items():
                w.writerow([list_id, "set_by from policies", k, v])
            for f, vals in c["presentation_changes"].items():
                for k, v in vals.items():
                    w.writerow([list_id, f"change: {f}", k, v])
            w.writerow(
                [
                    list_id,
                    "content cut (by pattern over coder notes)",
                    "pairs",
                    c["content_cut_by_pattern"],
                ]
            )
    with (out / "corpus-b.tsv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["category", "measure", "value", "count"])
        for cat, c in counts["corpus_b"]["per_category"].items():
            w.writerow([cat, "options", "included", c["included_confirmed_by_reading"]])
            w.writerow([cat, "options", "excluded", c["excluded_confirmed_by_reading"]])
            for key in (
                "per_dimension",
                "setting_place",
                "carries_across_documents",
                "changed_during_use_affordance",
                "changed_during_use_behaviour",
            ):
                for k, v in c[key].items():
                    w.writerow([cat, key, k, v])
    with (out / "situations.tsv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["table", "value", "primary", "grades", "flag"])
        for v in counts["situations"]["per_code"]:
            grades = " ".join(f"{g}:{n}" for g, n in v["grades"].items())
            w.writerow(
                [
                    "draft value",
                    v["code"],
                    v["primary"],
                    grades,
                    "short (<4)" if v["short"] else "",
                ]
            )
        for tag in ("kind", "who"):
            for k, n in counts["situations"][tag].items():
                w.writerow([tag, k, n, "", "absent" if n == 0 else ""])
        for vid, v in (counts["situations"].get("per_value_lead") or {}).items():
            w.writerow(
                [
                    "value lead",
                    vid,
                    v["primary"],
                    f"B or better: {v['b_or_better']}",
                    "short (<4)" if v["short"] else "",
                ]
            )


DATE = "2026-10-17"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def read_fixture(root: Path, name: str):
    return json.loads((root / f"{name}-{DATE}.json").read_text(encoding="utf-8"))


def run_all(root: Path = FIXTURES) -> dict:
    lists = defaultdict(list)
    for row in read_jsonl(root / f"adaptations-{DATE}.jsonl"):
        lists[row["list"]].append(row)
    labels = read_fixture(root, "labels")
    values = {
        v["value_id"]: v["codes"].split() for v in read_fixture(root, "leads")["values"]
    }
    maintainer = read_fixture(root, "maintainer-counts")
    return {
        "captures": maintainer["captures"],
        "maintainer": {"coga_pattern_files": maintainer["coga_pattern_files"]},
        "corpus_a": corpus_a(
            lists,
            labels,
            read_tsv(root / f"pairs-{DATE}.tsv"),
            read_tsv(root / f"policies-{DATE}.tsv"),
        ),
        "corpus_b": corpus_b(read_tsv(root / f"options-{DATE}.tsv")),
        "situations": situations(
            read_tsv(root / f"situations-{DATE}.tsv"), values=values
        ),
        "sources": {
            name: source_table(rows)
            for name, rows in read_fixture(root, "sources").items()
        },
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=FIXTURES)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    result = run_all(args.fixtures)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "counts.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    write_tables(result, args.out)
    print(
        "Recounted Corpus A, Corpus B, situations and sources; capture totals are recorded metadata."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
