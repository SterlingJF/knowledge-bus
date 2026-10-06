"""Grade a universe against evals/universe.yaml, or calibrate each tier on the owner's labelled examples.

    grade.py universe [--universe PATH] [--guidance PATH] [--tiers T,...] [--probes FILE]
                      [--situations FILE] [--judge-model M,...] [--light-model M] [--label TEXT]
                      [--out DIR]
    grade.py examples [--slice universe|skills] [--tiers T,...] [--judge-model M,...]
                      [--light-model M] [--label TEXT] [--out DIR]
    grade.py report RUN_FOLDER   (rebuilds a run's report from its verdicts; no model calls)

Every verdict row carries the rule's why and the reason the settling tier gave for its verdict;
its trail keeps each judge's own vote (`votes`) and each filer's own placements (`placed`).
A model named codex:<model> runs through the Codex CLI, any other name through the claude CLI.
Rules with a sort block are settled by the sort check (tier "sort"), after any tiers they have.
Rules with a recognise block are settled by the recognition check (tier "recognise"), which files
the universe's answers, evals/situations/<universe-id>.yaml, over the shared cases beside them
(cases.yaml); without those files, or for a set whose answers are stale, values read "not run".
Results go to .evidence/<date>/evals/<run>/ (verdicts.jsonl, report.md, run.json, and for a
universe with sort rules, probes.json; pass it back with --probes to file the same passages).
"""

import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import situations
import sort
import spec as spec_module
import tiers
import yaml

from kbp_conform import explorer

ROOT = spec_module.ROOT
UNIVERSE = ROOT / "universes/product-development/universe.kbp.yaml"
ENABLEMENT = ("action", "actor", "timing")
ALL_TIERS = (*tiers.TIERS, "sort", "recognise")
FILED = ("sort", "recognise")
LIGHT_MODEL = "claude-haiku-4-5-20251001"


@dataclass
class Run:
    id: str
    kind: str
    inputs: dict
    adapters: dict
    tiers: list = field(default_factory=lambda: list(ALL_TIERS))
    notes: list = field(default_factory=list)
    label: str = ""
    universe: str = ""
    kinds: dict = field(
        default_factory=dict
    )  # each input's kind, as the report compares it


def select(doc, path):
    """(ref, text, context) for every string at a subject path such as elements[].question.

    Steps: key, key[] (each list item), {a,b} (either key), <id> (each mapping entry).
    A path ending in enablement renders each enablement as one line; one ending in composition
    yields one member per composition entry, its text the element's question; one ending in
    {values,facets} yields one member per frame or factor value, as the explorer shows it.
    """
    found = []
    last = path.rsplit(".", 1)[-1]

    def walk(node, steps, ref, ident, parent):
        if not steps:
            if last == "enablement" and isinstance(node, dict):
                found.append((ref, enablement(node), {"id": ident}))
            elif last == "composition" and isinstance(node, dict):
                found.extend(composition(doc, node, ref, ident, parent))
            elif last == "{values,facets}" and isinstance(parent, dict):
                found.extend(values(node, ref, parent))
            elif isinstance(node, str):
                context = {"id": ident} if ident is not None else {}
                if isinstance(parent, dict) and parent.get("term") not in (None, node):
                    context["term"] = parent["term"]
                if isinstance(parent, dict) and set(ENABLEMENT) & set(parent):
                    context.update(
                        {
                            k: v
                            for k, v in parent.items()
                            if k in ENABLEMENT and v != node
                        }
                    )
                found.append((ref, node, context))
            return
        step, rest = steps[0], steps[1:]
        listed = step.endswith("[]")
        name = step[:-2] if listed else step
        if name == "<id>":
            for key, child in node.items() if isinstance(node, dict) else ():
                if not listed:
                    walk(child, rest, f"{ref}.{key}", key, node)
                    continue
                for n, item in enumerate(child or []):
                    walk(item, rest, f"{ref}.{key}[{n}]", key, item)
            return
        for key in name[1:-1].split(",") if name.startswith("{") else [name]:
            if not isinstance(node, dict) or key not in node:
                continue
            here = f"{ref}.{key}" if ref else key
            if not listed:
                walk(node[key], rest, here, ident, node)
                continue
            for n, item in enumerate(node[key] or []):
                item_id = item.get("id", n) if isinstance(item, dict) else n
                walk(
                    item,
                    rest,
                    f"{here}[{item_id}]",
                    item_id if isinstance(item, dict) else ident,
                    item,
                )

    walk(doc, path.split("."), "", None, None)
    for ref, _, context in found:
        owner = re.match(r"(frames|factors)\[([^\]]+)\]\.(?:values|facets)\[", ref)
        if owner:
            frame = next(
                (
                    f
                    for f in doc.get(owner.group(1)) or []
                    if isinstance(f, dict) and str(f.get("id")) == owner.group(2)
                ),
                {},
            )
            if frame.get("question"):
                context["frame question"] = frame["question"]
    return found


def enablement(block):
    """An enablement as one line: action: ...; actor: ...; timing: ..."""
    return "; ".join(f"{k}: {block[k]}" for k in ENABLEMENT if block.get(k))


def predicate(when):
    """A frame predicate in compact words: frame is a or b and frame facet is c."""
    parts = []
    for frame, values in (when or {}).items():
        facets = values.items() if isinstance(values, dict) else [(None, values)]
        for facet, options in facets:
            name = f"{frame} {facet}" if facet else frame
            parts.append(f"{name} is {' or '.join(str(o) for o in options)}")
    return " and ".join(parts)


def values(node, ref, owner):
    """(ref, text, context) for each value of one frame or factor; each facet is its own set."""
    kind = "factor" if ref.startswith("factors") else "frame"
    members = []
    for facet, shown in situations.value_sets(node):
        here = f"{ref}[{facet}]" if facet else ref
        entries = [text for _, text in shown]
        for ident, text in shown:
            context = {"id": ident, kind: owner.get("id")}
            if facet:
                context["facet"] = facet
            members.append((f"{here}[{ident}]", text, {**context, "set": entries}))
    return members


def composition(doc, block, ref, artifact, parent):
    """(ref, question, context) for each core then situational entry of one artifact."""
    questions = {
        e.get("id"): e.get("question", "")
        for e in doc.get("elements") or []
        if isinstance(e, dict)
    }
    action = (parent or {}).get("enablement")
    rendered = enablement(action) if isinstance(action, dict) else str(action or "")
    members = []
    for strength in ("core", "situational"):
        for entry in block.get(strength) or []:
            entry = entry if isinstance(entry, dict) else {"element": entry}
            element = entry.get("element")
            label = strength
            if entry.get("when"):
                label = f"{strength} when {predicate(entry['when'])}"
            members.append(
                (
                    f"{ref}.{strength}[{element}]",
                    questions.get(element) or str(element),
                    {
                        "id": element,
                        "artifact": artifact,
                        "enablement": rendered,
                        "strength": label,
                    },
                )
            )
    entries = [f"{c['strength']}: {text}" for _, text, c in members]
    for _, _, context in members:
        context["set"] = entries
    return members


def universe_cases(spec, universe_doc, guidance_doc=None, empty=None, rules=None):
    """One case per rule and text; a pair rule makes one case per two texts in the same list.

    A set rule gives each case its set as context.set: every text the subject selects, or, for
    compositions, the members of the same artifact.

    The one-term-per-concept rule gives each case the universe's declared terms as
    context.terms, when it declares any. A recognise rule skips a set of one value, which
    offers no choice (see situations.CHOICES).

    Subjects whose path selects no text are appended to `empty`.
    """
    subjects = spec.universe["subjects"]
    terms = ((universe_doc or {}).get("universe") or {}).get("terms") or []
    cases = []
    for rule_id, rule in spec.universe["rules"].items():
        if rules and rule_id not in rules:
            continue
        for subject in rule["applies_to"]:
            path = subjects[subject]
            doc = universe_doc
            if path.startswith("guidance:"):
                doc, path = guidance_doc, path.split(":", 1)[1].strip()
            if doc is None:
                continue
            picked = select(doc, path)
            if not picked and empty is not None and subject not in empty:
                empty.append(subject)
            if "recognise" in rule:
                picked = [
                    p
                    for p in picked
                    if len(p[2].get("set") or ()) >= situations.CHOICES
                ]
            if rule_id == "one-term-per-concept" and terms:
                picked = [(r, t, {**c, "terms": terms}) for r, t, c in picked]
            scope = rule.get("scope", "item")
            if scope == "item":
                cases += [tiers.Case(rule_id, rule, subject, *p) for p in picked]
                continue
            if scope == "set":
                every = [text for _, text, _ in picked]
                cases += [
                    tiers.Case(
                        rule_id,
                        rule,
                        subject,
                        ref,
                        text,
                        context if "set" in context else {**context, "set": every},
                    )
                    for ref, text, context in picked
                ]
                continue
            groups = {}
            for ref, text, context in picked:
                groups.setdefault(ref.rsplit("[", 1)[0], []).append(
                    (ref, text, context)
                )
            for siblings in groups.values():
                for i, (ref, text, context) in enumerate(siblings):
                    for other_ref, other, _ in siblings[i + 1 :]:
                        pair = {**context, "sibling": other}
                        cases.append(
                            tiers.Case(
                                rule_id,
                                rule,
                                subject,
                                f"{ref} ~ {other_ref}",
                                text,
                                pair,
                            )
                        )
    return cases


def example_cases(spec, slice_):
    doc, key = (
        (spec.universe, "rules")
        if slice_ == "universe"
        else (spec.skills, "behaviours")
    )
    cases, labels = [], []
    for rule_id, rule in (doc.get(key) or {}).items():
        for n, example in enumerate(rule.get("examples") or [], 1):
            subject = example.get("subject", rule["applies_to"][0])
            cases.append(
                tiers.Case(
                    rule_id,
                    rule,
                    subject,
                    f"{rule_id}#example-{n}",
                    example["text"],
                    example.get("context") or {},
                )
            )
            labels.append(example["verdict"])
    return cases, labels


def _score(rule_id, tier, verdicts, labels):
    row = {
        "rule": rule_id,
        "tier": tier,
        "n": len(labels),
        "tp": 0,
        "fn": 0,
        "tn": 0,
        "fp": 0,
        "undecided": 0,
    }
    for verdict, label in zip(verdicts, labels, strict=True):
        if verdict == "undecided":
            row["undecided"] += 1
        else:
            row[
                {
                    ("fail", "fail"): "tp",
                    ("pass", "fail"): "fn",
                    ("pass", "pass"): "tn",
                    ("fail", "pass"): "fp",
                }[(verdict, label)]
            ] += 1
    return row


def settle(results, sorter, block="sort"):
    """Give each case of a sort (or recognise) rule that no tier settled the check's verdict."""
    picked = [
        r for r in results if block in r.case.rule and r.final.verdict == "undecided"
    ]
    if sorter is None or not picked:
        return
    for result, outcome in zip(picked, sorter([r.case for r in picked]), strict=True):
        result.trail.append(outcome)
        result.final = outcome


def calibrate(
    spec, slice_, decide=None, judge=None, only=ALL_TIERS, misses=None, sorter=None,
    recogniser=None, settled=None, alone=None,
):  # fmt: skip
    """Each tier alone (or only the tiers in `alone`), then the whole chain, on every labelled
    example of the slice. `settled` gains each example's chain verdict, the tier that settled
    it and that tier's own votes or placements, in example order."""
    cases, labels = example_cases(spec, slice_)
    table = []
    runs = [(t, (t,)) for t in (only if alone is None else alone)] + [("chain", only)]
    for name, chosen in runs:
        results = tiers.run(cases, decide=decide, judge=judge, only=chosen)
        if "sort" in chosen:
            settle(results, sorter)
        if "recognise" in chosen:
            settle(results, recogniser, "recognise")
        by_rule = {}
        for result, label in zip(results, labels, strict=True):
            if name != "chain" and not any(o.tier == name for o in result.trail):
                continue
            by_rule.setdefault(result.case.rule_id, []).append((result, label))
            if name == "chain" and settled is not None:
                settled.append(
                    {
                        "rule": result.case.rule_id,
                        "verdict": result.final.verdict,
                        "tier": result.final.tier,
                        **_own(result.final),
                    }
                )
            if misses is not None and result.final.verdict not in ("undecided", label):
                misses.append(
                    {
                        "tier": name,
                        "rule": result.case.rule_id,
                        "text": result.case.text,
                        "label": label,
                        **_reason(result.final),
                    }
                )
        for rule_id, pairs in by_rule.items():
            table.append(
                _score(
                    rule_id,
                    name,
                    [r.final.verdict for r, _ in pairs],
                    [label for _, label in pairs],
                )
            )
    return table


def _reason(outcome):
    detail = outcome.detail
    if outcome.tier == "deterministic":
        return {
            "reason": "; ".join(
                f"{k} {c.get(k)!r}"
                for c in detail.get("fired", [])
                for k in ("match", "count", "path")
                if k in c
            )
        }
    if outcome.tier in FILED:
        return {"reason": detail.get("reason", "")}
    if outcome.tier == "decision":
        return {
            "reason": ", ".join(
                f"{k} {v}"
                for k, v in detail.items()
                if k in ("noul", "choice", "score", "confidence")
            )
        }
    return {"reason": detail.get("critique", "")}


def write(folder, run, spec, results):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "run": run.id, "rule": r.case.rule_id, "subject": r.case.subject, "ref": r.case.ref,
            "text": r.case.text, "verdict": r.final.verdict, "tier": r.final.tier,
            "adapter": run.adapters.get(r.final.tier, "code" if r.final.tier == "deterministic" else ""),
            **_reason(r.final), "why": r.case.rule.get("why", ""),
            "trail": [{"tier": o.tier, "verdict": o.verdict, **_reason(o), **_own(o)} for o in r.trail],
            **_recognition(r.final),
        }
        for r in results
    ]  # fmt: skip
    with open(folder / "verdicts.jsonl", "w") as out:
        out.writelines(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
    (folder / "run.json").write_text(json.dumps(asdict(run), indent=2) + "\n")
    (folder / "report.md").write_text(_report(run, spec, rows))


def _own(outcome):
    """Each judge's own vote or each filer's own placements, so any pairing can be worked out
    from the row later without calling a model."""
    return {k: outcome.detail[k] for k in ("votes", "placed") if k in outcome.detail}


def _recognition(outcome):
    """A recognition verdict's counts, kept on its row for the recognition table."""
    if outcome.tier != "recognise" or "set" not in outcome.detail:
        return {}
    kept = {k: v for k, v in outcome.detail.items() if k not in ("reason", "placed")}
    return {"recognition": kept}


def rebuild(folder, spec):
    """The report of a finished run, rebuilt from its verdicts without calling any model."""
    folder = Path(folder)
    run = Run(**json.loads((folder / "run.json").read_text()))
    rows = [
        json.loads(line)
        for line in (folder / "verdicts.jsonl").read_text().splitlines()
    ]
    return _report(run, spec, rows)


def _report(run, spec, rows):
    doc, key = (
        (spec.universe, "rules")
        if run.kind != "skills"
        else (spec.skills, "behaviours")
    )
    rules = doc[key]
    by_rule = {}
    for row in rows:
        by_rule.setdefault(row["rule"], []).append(row)
    graded = [p for p in run.inputs if not p.startswith("evals/")]
    lines = [f"# Grade: {', '.join(graded)}", ""]
    tier_names = " → ".join(
        f"{t} ({run.adapters.get(t, 'code' if t == 'deterministic' else 'off')})"
        for t in run.tiers
    )
    lines.append(f"Run `{run.id}`. Tiers: {tier_names}.")
    lines += [f"Input `{name}`: `{digest}`." for name, digest in run.inputs.items()]
    lines += [f"Note: {note}" for note in run.notes]
    lines += [
        "",
        "| Rule | Pass | Fail | Undecided | Settled by deterministic / decision / judgment / sort / recognise |",
        "|---|---|---|---|---|",
    ]
    for rule_id, rs in by_rule.items():
        count = Counter(r["verdict"] for r in rs)
        settled = " / ".join(
            str(sum(r["tier"] == t and r["verdict"] != "undecided" for r in rs))
            for t in ALL_TIERS
        )
        lines.append(
            f"| `{rule_id}` | {count['pass']} | {count['fail']} | {count['undecided']} | {settled} |"
        )
    lines += _recognition_table(rows)
    lines += [
        "",
        "## By definition",
        "",
        "Each text that falls short, with every rule it fails.",
        "",
    ]
    failing = {}
    for row in rows:
        if row["verdict"] == "fail" and " ~ " not in row["ref"]:
            failing.setdefault((row["subject"], row["ref"], row["text"]), []).append(
                row["rule"]
            )
    for subject in dict.fromkeys(s for s, _, _ in failing):
        lines += [f"### {subject}", ""]
        lines += [
            f'- `{ref}`: "{text}" fails {", ".join(names)}'
            for (s, ref, text), names in failing.items()
            if s == subject
        ]
        lines.append("")
    for rule_id, rs in by_rule.items():
        rule = rules[rule_id]
        lines += ["", f"## {rule_id}: {rule.get('rule') or rule.get('behaviour')}", ""]
        if rule.get("why"):
            lines += [f"Why: {rule['why'].strip()}", ""]
        for verdict, title in (
            ("fail", "Falls short"),
            ("undecided", "Undecided, for the owner"),
        ):
            picked = [r for r in rs if r["verdict"] == verdict]
            if not picked:
                continue
            lines.append(f"{title}:")
            lines += [
                f'- `{r["ref"]}`: "{r["text"]}" ({r["tier"]}: {r["reason"] or "no tier settled it"})'
                for r in picked
            ]
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _recognition_table(rows):
    """One row per frame or facet: each filer's right / situations, with unsure, none and
    off-by-one-step misses apart; the value with the lowest share; the set's verdict."""
    sets = {}
    for row in rows:
        if "recognition" in row:
            sets.setdefault(row["recognition"]["set"], []).append(row)
    if not sets:
        return []
    filers = list(
        dict.fromkeys(
            f for rs in sets.values() for r in rs for f in r["recognition"]["filers"]
        )
    )
    lines = [
        "",
        "## Recognition by frame",
        "",
        (
            "Each filer's right / situations in the set, with unsure, none and, on a ladder, "
            "off-by-one-step misses counted apart. Unsure and none count as misses."
        ),
        "",
        f"| Set | Values | Situations | {' | '.join(filers)} | Lowest value | Verdict |",
        "|---|---|---|" + "---|" * len(filers) + "---|---|",
    ]
    for name, rs in sets.items():
        shown = rs[0]["recognition"]["filers"]
        cells = []
        for filer in filers:
            count = shown.get(filer)
            if not count or not count["n"]:
                cells.append("not run")
                continue
            apart = f"{count['unsure']} unsure, {count['none']} none"
            if "off_by_one" in count:
                apart += f", {count['off_by_one']} off by one"
            cells.append(f"{count['right']}/{count['n']} ({apart})")
        shares = [
            (right / r["recognition"]["situations"], r["recognition"], filer)
            for r in rs
            for filer, right in r["recognition"]["right"].items()
            if r["recognition"]["situations"]
        ]
        lowest = "—"
        if shares:
            _, low, filer = min(shares, key=lambda s: s[0])
            lowest = (
                f"{low['value']} {low['right'][filer]}/{low['situations']} ({filer})"
            )
        verdicts = {r["verdict"] for r in rs}
        verdict = next((v for v in ("fail", "undecided") if v in verdicts), "pass")
        situations_n = sum(r["recognition"]["situations"] for r in rs)
        if not situations_n:
            verdict = "not run"
        lines.append(
            f"| {name} | {len(rs)} | {situations_n} | {' | '.join(cells)} | {lowest} | {verdict} |"
        )
    went = [
        f"- {name}: {r['text']} → {placed} ({', '.join(f'{f} {n}' for f, n in by.items())})"
        for name, rs in sets.items()
        for r in rs
        for placed, by in missed(r["recognition"]["misses"]).items()
    ]
    if went:
        lines += [
            "",
            "Where misses went, expected → placed, with each filer's count:",
            "",
            *went,
        ]
    return lines


def missed(misses):
    """{where a value's situations went instead: {filer: how many}}, from its misses."""
    found = {}
    for by in misses.values():
        for filer, placed in by.items():
            shown = "none" if placed == sort.NONE else placed
            found.setdefault(shown, Counter())[filer] += 1
    return {placed: dict(by) for placed, by in found.items()}


def _calibration_report(run, table, misses):
    lines = [
        "# Calibration on the owner's labelled examples",
        "",
        f"Run `{run.id}`. A fail example caught is a true positive.",
        "",
    ]
    lines += [
        "| Rule | Tier | n | Caught fails (TP) | Missed fails (FN) | Kept passes (TN) | Wrong fails (FP) | Undecided |",
        "|---|---|---|---|---|---|---|---|",
    ]
    lines += [
        f"| `{r['rule']}` | {r['tier']} | {r['n']} | {r['tp']} | {r['fn']} | {r['tn']} | {r['fp']} | {r['undecided']} |"
        for r in table
    ]
    if misses:
        lines += ["", "## Disagreements with the owner", ""]
        lines += [
            f'- `{m["rule"]}` ({m["tier"]}): "{m["text"]}" labelled {m["label"]}; {m["reason"]}'
            for m in misses
        ]
    return "\n".join(lines) + "\n"


def _digest(path):
    return "sha256:" + hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _input(run, name, digest, kind):
    run.inputs[name] = digest
    run.kinds[name] = kind


def _adapters(chosen, judge_model, run):
    import adapters  # vendor code loads only when a model tier runs

    decide = judge = None
    if "decision" in chosen:
        key = os.environ.get("TYPESAFE_API_KEY")
        if key:
            decide = adapters.Jev(key)
        else:
            run.notes.append("decision tier off: TYPESAFE_API_KEY is not set")
    if "judgment" in chosen:
        models = judge_model.split(",")
        problem = adapters.unavailable(models)
        if problem:
            run.notes.append(f"judgment tier off: {problem}")
        else:
            judge = adapters.Judge(models=models)
    return decide, judge


def guidance_for(universe):
    """The guidance document that guides this universe, or None.

    The checker's own scope rules: the definition files beside the universe file are its scope,
    and a guidance belongs to the universe its `guides` names, whatever the file is called.
    """
    paths, universe_id = explorer.resolve_inspection_targets([universe])
    found = [
        path
        for path in paths
        if ((yaml.safe_load(path.read_text()) or {}).get("guidance") or {}).get(
            "guides"
        )
        == universe_id
    ]
    if len(found) > 1:
        raise ValueError(
            f"universe {universe_id!r} has multiple guidance documents: "
            + ", ".join(p.name for p in found)
        )
    return found[0] if found else None


def _relative(path):
    path = Path(path)
    return str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)


def situations_for(path, universe_doc, run):
    """The universe's answers and the shared cases beside them, recorded on the run: the
    answers file's digest, and a digest of only the cases it uses, so cases another universe
    adds leave the run comparable. With no answers file, or one for another universe, an empty
    source and a note that recognition did not run; a set whose answers are stale files
    nothing, and the run notes why."""
    universe_id = (universe_doc.get("universe") or {}).get("id")
    path = Path(path or situations.FOLDER / f"{universe_id}.yaml")
    pool = path.with_name(situations.POOL)
    if not path.exists() or not pool.exists():
        missing = "situations" if not path.exists() else "shared cases"
        run.notes.append(f"recognition not run: no {missing} file for {universe_id}")
        return situations.Situations(None, None)
    answers = spec_module.read(path)
    if answers.get("universe") != universe_id:
        run.notes.append(
            f"recognition not run: {_relative(path)} holds answers for "
            f"{answers.get('universe')}, not {universe_id}"
        )
        return situations.Situations(None, None)
    cases = spec_module.read(pool)
    used = {
        ident
        for section in situations.SECTIONS
        for block in (answers.get(section) or {}).values()
        for ident in (block or {}).get("answers") or {}
    }
    listed = sorted(
        (c for c in cases.get("cases") or [] if c.get("id") in used),
        key=lambda c: str(c.get("id")),
    )
    text = json.dumps(listed, sort_keys=True, ensure_ascii=False)
    _input(run, _relative(path), _digest(path), "situations")
    _input(
        run,
        f"{_relative(pool)} (cases used)",
        "sha256:" + hashlib.sha256(text.encode()).hexdigest(),
        "situations",
    )
    stale = situations.stale_sets(answers, universe_doc)
    run.notes += [f"recognition not run for {why}" for why in stale.values()]
    return situations.Situations(answers, cases, stale)


@dataclass
class Sorting:
    sorter: object
    prober: object = None
    models: object = None
    choice: object = None
    recogniser: object = None


def scope_of(universe_doc):
    """The universe's overview as one line for the sort check's writer, validity check and
    filers, so a question is read within the universe it belongs to."""
    overview = (universe_doc.get("universe") or {}).get("overview") or {}
    parts = [
        f"{label} {' '.join(str(overview[key]).split())}"
        for key, label in (
            ("covers", "covers:"),
            ("for", "It is for:"),
            ("excludes", "It excludes:"),
        )
        if overview.get(key)
    ]
    if not parts:
        return ""
    return "These questions belong to a universe that " + " ".join(parts)


def sorting(
    chosen, kind, run, judge_models, light_model, probes=None, key=None, call=None,
    post=None, scope="", situations=None,
):  # fmt: skip
    """The sort and recognition checks' filers and sources, or None when neither is chosen.

    Filers: each judgment model as a careful reader, the decision model when `key` is set, and
    the light model. A universe's probes are written by the first judgment model and validated
    by all of them; examples bring their own. Recognition readers pick the option that fits each
    of a universe's `situations` (or an example's own), one situation per call.
    """
    picked = [t for t in FILED if t in chosen]
    if not picked:
        return None
    import adapters  # vendor code loads only when a model tier runs

    problem = None if call else adapters.unavailable([*judge_models, light_model])
    if problem:
        run.notes.append(f"{' and '.join(picked)} off: {problem}")
        return None
    models = adapters.Models(call=call)

    choice = None
    if key:
        choice = adapters.JevChoice(key, post=post)
    else:
        run.notes.append(
            f"{' and '.join(picked)}: the decision-model filer is off: "
            "TYPESAFE_API_KEY is not set"
        )

    def readers(call):
        """Each judgment model, the decision model when it is on, then the light model; the
        models answer through `call` (models.file sorts passages, models.recognise picks the
        option that fits a situation)."""

        def reader(model):
            return sort.Filer(model, lambda q, p, a: call(model, q, p, a))

        decides = [sort.Filer(choice.name, choice.file)] if choice else []
        return [*map(reader, judge_models), *decides, reader(light_model)]

    filers = readers(models.file)
    prober = recogniser = None
    if "recognise" in chosen:
        source = situations if kind == "universe" else None
        recogniser = sort.Sorter(
            readers(models.recognise),
            source or sort.given_probes,
            # a recognition reader picks among options, not questions
            scope=scope.replace("These questions", "These options", 1),
            verdicts=sort.recognition(source.ladder) if source else sort.recognition(),
            batch=False,
        )
    if kind == "universe" and "sort" in chosen:
        prober = sort.Prober(
            lambda q, w: models.write(judge_models[0], q, w, scope),
            {
                m: (lambda q, ps, m=m: models.answers(m, q, ps, scope))
                for m in judge_models
            },
            known=sort.load(probes) if probes else None,
        )
    sorter = None
    if "sort" in chosen:
        sorter = sort.Sorter(filers, prober or sort.given_probes, scope=scope)
    return Sorting(
        sorter,
        prober,
        models,
        choice,
        recogniser,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=["universe", "examples", "report"])
    parser.add_argument(
        "run", nargs="?", type=Path, help="for report: a finished run folder"
    )
    parser.add_argument("--universe", type=Path, default=UNIVERSE)
    parser.add_argument("--guidance", type=Path)
    parser.add_argument("--slice", choices=["universe", "skills"], default="universe")
    parser.add_argument(
        "--rules",
        default="",
        help="universe: grade only these rule ids, separated by commas",
    )
    parser.add_argument("--tiers", default=",".join(ALL_TIERS))
    parser.add_argument(
        "--judge-model",
        default="claude-opus-5-5,claude-fable-5-1",
        help="one model, or several separated by commas: a verdict stands only when all "
        "agree; codex:<model> runs through the Codex CLI",
    )
    parser.add_argument(
        "--light-model",
        default=LIGHT_MODEL,
        help="sort and recognition: the light model that files; codex:<model> as above",
    )
    parser.add_argument(
        "--label", default="", help="a name for the run, kept in run.json"
    )
    parser.add_argument(
        "--probes",
        type=Path,
        help="universe sort: reuse the probes.json of an earlier run",
    )
    parser.add_argument(
        "--situations",
        type=Path,
        help="universe recognition: the answers file, beside its cases.yaml "
        "(default evals/situations/<id>.yaml)",
    )
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    chosen = tuple(t for t in args.tiers.split(",") if t)
    spec = spec_module.load()
    if args.command == "report":
        (args.run / "report.md").write_text(rebuild(args.run, spec))
        print(args.run / "report.md")
        return 0
    stamp = datetime.now(UTC)
    run = Run(
        id=f"{args.command if args.command == 'universe' else 'examples-' + args.slice}-{stamp:%Y%m%dT%H%M%S%fZ}",
        kind=args.command if args.command == "universe" else args.slice,
        inputs={},
        adapters={},
        tiers=list(chosen),
        label=args.label,
    )
    decide, judge = _adapters(chosen, args.judge_model, run)
    graded = (
        spec.skills.get("behaviours")
        if args.command == "examples" and args.slice == "skills"
        else spec.universe.get("rules")
    )
    universe_doc = (
        yaml.safe_load(args.universe.read_text())
        if args.command == "universe"
        else None
    )
    sorted_by = sorting(
        [t for t in chosen if any(t in r for r in (graded or {}).values())],
        "universe" if args.command == "universe" else "examples",
        run,
        args.judge_model.split(","),
        args.light_model,
        probes=args.probes,
        key=os.environ.get("TYPESAFE_API_KEY"),
        scope=scope_of(universe_doc) if args.command == "universe" else "",
        situations=situations_for(args.situations, universe_doc, run)
        if args.command == "universe" and "recognise" in chosen
        else None,
    )
    out = args.out or ROOT / ".evidence" / f"{stamp:%Y-%m-%d}" / "evals" / run.id
    out.mkdir(parents=True, exist_ok=args.out is not None)
    for name, kind in (("universe", "spec"), ("skills", "skills-spec")):
        _input(run, f"evals/{name}.yaml", _digest(spec.folder / f"{name}.yaml"), kind)
    if args.command == "universe":
        try:
            guidance = args.guidance or guidance_for(args.universe)
        except ValueError as error:
            parser.error(str(error))
        run.universe = (universe_doc.get("universe") or {}).get("id", "")
        _input(run, _relative(args.universe), _digest(args.universe), "universe")
        guidance_doc = None
        if guidance and guidance.exists():
            _input(run, _relative(guidance), _digest(guidance), "guidance")
            guidance_doc = yaml.safe_load(guidance.read_text())
        empty = []
        results = tiers.run(
            universe_cases(
                spec,
                universe_doc,
                guidance_doc,
                empty,
                [r for r in args.rules.split(",") if r] or None,
            ),
            decide=decide,
            judge=judge,
            only=chosen,
        )
        settle(results, sorted_by and sorted_by.sorter)
        settle(results, sorted_by and sorted_by.recogniser, "recognise")
        run.notes += [f"subject {name} selected no text" for name in empty]
        finish(run, decide, judge, sorted_by, out)
        write(out, run, spec, results)
    else:
        misses, settled = [], []
        table = calibrate(
            spec,
            args.slice,
            decide=decide,
            judge=judge,
            only=chosen,
            misses=misses,
            sorter=sorted_by and sorted_by.sorter,
            recogniser=sorted_by and sorted_by.recogniser,
            settled=settled,
        )
        finish(run, decide, judge, sorted_by, out)
        out.mkdir(parents=True, exist_ok=True)
        data = {
            "run": asdict(run),
            "table": table,
            "misses": misses,
            "settled": settled,
        }
        (out / "calibration.json").write_text(json.dumps(data, indent=2) + "\n")
        (out / "report.md").write_text(_calibration_report(run, table, misses))
    print(out)
    return 0


def finish(run, decide, judge, sorted_by, out):
    """Record adapters, costs and notes on the run; write a universe's probes.json."""
    _record(run, decide, judge)
    if not sorted_by:
        return
    names = [
        f"{f.name} {sorted_by.choice.version}"
        if sorted_by.choice
        and f.name == sorted_by.choice.name
        and sorted_by.choice.version
        else f.name
        for f in (sorted_by.sorter or sorted_by.recogniser).filers
    ]
    checks = (("sort", sorted_by.sorter), ("recognise", sorted_by.recogniser))
    ran = [tier for tier, check in checks if check]
    for tier in ran:
        run.adapters[tier] = "filers: " + ", ".join(names)
    what = " and ".join(ran)
    run.notes.append(f"{what} cost: {_spent(sorted_by.models)}")
    if sorted_by.choice:
        run.notes.append(f"{what} decision tokens: {sorted_by.choice.tokens}")
        run.notes.append(
            f"{what}: the decision model is unsure below confidence "
            f"{sorted_by.choice.confidence}"
        )
    if sorted_by.models.failures:
        run.notes.append(
            f"{what} calls that failed after retries: {sorted_by.models.failures}"
        )
    prober = sorted_by.prober
    if prober:
        run.notes += prober.notes
        kept = sum(len(e.get("probes") or []) for e in prober.known.values())
        dropped = sum(len(e.get("dropped") or []) for e in prober.known.values())
        run.notes.append(
            f"sort probes: {kept} kept, {dropped} dropped, for {len(prober.known)} "
            "element questions (see probes.json)"
        )
        Path(out).mkdir(parents=True, exist_ok=True)
        sort.save(Path(out) / "probes.json", prober.known)


def _spent(models):
    """What model calls cost as their CLIs reported it: dollars, tokens, or n/a."""
    parts = [f"${models.cost:.2f}"] if models.cost is not None else []
    parts += [f"{models.tokens} tokens"] if models.tokens is not None else []
    return ", ".join(parts) or "n/a"


def _record(run, decide, judge):
    if decide:
        # the version is known only once the decision model has been asked something
        run.adapters["decision"] = " ".join(filter(None, (decide.name, decide.version)))
        run.notes.append(f"decision tokens: {decide.tokens}")
    if judge:
        run.adapters["judgment"] = "judges: " + ", ".join(judge.models)
        run.notes.append(f"judgment cost: {_spent(judge)}")
        if judge.failures:
            run.notes.append(
                f"judgment calls that failed after retries: {judge.failures} (their items are undecided)"
            )


if __name__ == "__main__":
    sys.exit(main())
