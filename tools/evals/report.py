"""Build evals/report.md from the run folders listed in evals/runs.yaml. Calls no model.

    report.py          summarise each listed run folder into evals/results/<run-id>.json, then write
                       evals/report.md from those summaries
    report.py --check  say what differs between the committed report and summaries and what
                       report.py builds from the committed summaries (no run folder is read)

evals/runs.yaml lists one run per entry: `side` (anthropic or openai), `folder`, a run folder
written by grade.py (or by the scenario runner), relative to the repository or absolute, and, for
a run that graded a universe, `universe` (the id; run.json names it when the run recorded one). A
folder that is not on this machine falls back to its committed summary, so the report can be
rebuilt from a clean checkout. A run counts for every measure it holds: calibration (one per
slice), the universe grade (by the tiers it ran), sorting and recognition (when it filed
something), and scenarios. A side
may list one run per measure, and per universe for the three universe measures. Calibration and
scenarios do not depend on a universe; the other three get one section per universe, and runs of
different universes are never compared. Each universe's frame fails the owner retired are read
from evals/retired/<universe-id>.yaml. Anything without a run reads "not run". Sides are compared
only when the inputs a measure depends on have the same digests. The universe grade counts only
rules no filing check (sort, recognise) settles, and only cases some tier of the
run could settle. A run's judge, light, filer and agent models must belong to its side's company,
as the adapters route them; Jev, the decision model, serves both sides. The top-level
`labelled_by` names, per universe, who wrote and labelled its situations on each side.
Recognition also counts its failing values with the careful readers only, a run's judgment models,
under the same bar (the rule's shares in evals/universe.yaml and sort.py's verdict); a run that
recorded another evals/universe.yaml gets no careful count, since its shares may differ.
"""

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import adapters
import sort
import yaml

ROOT = Path(__file__).resolve().parents[2]
EVALS = ROOT / "evals"
RUNS = EVALS / "runs.yaml"
RESULTS = EVALS / "results"
REPORT = EVALS / "report.md"
RETIRED = EVALS / "retired"
SPEC = (
    EVALS / "universe.yaml"
)  # the recognise block's shares, for the careful readers' count
SIDES = {"anthropic": "Anthropic side", "openai": "OpenAI side"}
TIERS = ("deterministic", "decision", "judgment", "sort", "recognise")
GRADED = ("deterministic", "decision", "judgment")
SHARED = ("deterministic", "decision")  # code and Jev: the same on both sides
FILED = ("sort", "recognise")
UNIVERSE_MEASURES = ("grade", "recognition", "sorting")  # one figure per universe
INDEPENDENT = ("calibration-universe", "calibration-skills", "scenarios")
NONE = (
    "none of the questions"  # how a filing check records "no option fits" (sort.NONE)
)
UNPLAYED = re.compile(
    r"^(\S+): not run, its fixture is still to be built$"
)  # play.py's note
CODES = {"pass": "p", "fail": "f"}
COST_BASIS = (
    "Dollar costs are API prices, as each CLI reports them. On a Claude or ChatGPT "
    "subscription, runs use the plan's limits instead."
)
EXAMPLES = "development examples (interim)"
SITUATIONS = "development situations (interim)"
MEASURES = {
    "calibration-universe": (
        "Calibration, universe rules (development examples, interim)",
        "Whether the tiers reproduce the owner's labelled examples of definitions that meet and miss the rules.",
    ),
    "calibration-skills": (
        "Calibration, skills behaviours (development examples, interim)",
        "Whether the tiers reproduce the owner's labelled examples of agent behaviour.",
    ),
    "grade": (
        "Universe grade",
        "How many of the universe's definitions meet each rule.",
    ),
    "recognition": (
        "Recognition by frame (development situations, interim)",
        "Whether readers place everyday situations under the right value of a frame or factor.",
    ),
    "sorting": (
        "Sorting",
        "Whether a passage that answers a question is filed under that question.",
    ),
    "scenarios": (
        "Agent scenarios",
        "Whether an agent working with a scripted owner shows the behaviours its scenario requires.",
    ),
}
PAIRS = (
    "Judge pairs across the sides",
    "Whether verdicts stand when one judge from each company must agree.",
)
RELATE = (
    "How the two sides relate: both sides use the same decision model, Jev, as the decision tier "
    "and as one of the readers in recognition and sorting. The recognition situations are "
    "written blind on one side and labelled blind on both sides, and a situation is kept only "
    "where both sides agree; each universe's recognition section says which side did what. "
    "The sorting passages are written by the "
    "Anthropic side's run and reused by the OpenAI side."
)
# What each measure depends on, by input kind; a measure's runs are compared only when these match.
USES = {
    "calibration-universe": {"spec"},
    "calibration-skills": {"skills-spec"},
    "grade": {"spec", "universe", "guidance"},
    "recognition": {"spec", "universe", "situations"},
    "sorting": {"spec", "universe", "probes"},
    "scenarios": {
        "spec",
        "skills-spec",
        "universe",
        "guidance",
        "situations",
        "probes",
    },
}
COMMANDS = """\
# 1. Calibration on the labelled examples, both slices
just evals-calibrate universe
just evals-calibrate skills
# 2. Universe grade and sorting, once per universe
just evals-grade <universe file> deterministic,decision,judgment,sort
# 3. Recognition of frame and factor values, once per universe
uv run --locked python tools/evals/grade.py universe --universe <universe file> \\
  --tiers recognise --rules values-recognised
# 4. Agent scenarios
just evals-play
# Summaries and this report
just evals-report"""


class ReportError(ValueError):
    pass


def digest(path):
    return "sha256:" + hashlib.sha256(Path(path).read_bytes()).hexdigest()


def input_kind(name, kinds=None):
    """The kind of input its run recorded; for a run recorded without kinds, read from the
    name."""
    if kinds and name in kinds:
        return kinds[name]
    if name == "evals/universe.yaml":
        return "spec"
    if name == "evals/skills.yaml":
        return "skills-spec"
    if name == "probes.json":
        return "probes"
    if "situations/" in name:
        return "situations"
    if "guidance" in Path(name).name:
        return "guidance"
    return "universe"


def plural(n, word):
    return f"{n} {word}{'' if n == 1 else 's'}"


def sets_named(recognition):
    """A recognition summary's sets by kind: 3 frames, 2 factors, or 8 frames and 1 factor."""
    kinds = Counter(r["kind"] for r in recognition.values())
    named = [plural(kinds[k], k) for k in ("frame", "factor") if kinds[k]]
    return " and ".join(named) or "0 frames"


# Summaries


def summarise(folder, side, universe=None):
    """A run folder reduced to counts, digests, models and the few cases that differ.

    `universe` is the entry's id for a run that graded one; run.json's own id wins when both
    are given and must agree."""
    folder = Path(folder)
    calibrated = folder / "calibration.json"
    if calibrated.exists():
        data = json.loads(calibrated.read_text())
        run = data["run"]
        kept = ("tier", "rule", "text", "label")
        body = {
            "kind": "calibration",
            "slice": run["kind"],
            "measures": [f"calibration-{run['kind']}"],
            "table": data["table"],
            "misses": [{k: m[k] for k in kept} for m in data["misses"]],
            "chain": _chain(data.get("settled", [])),
        }
    else:
        run = json.loads((folder / "run.json").read_text())
        rows = [
            json.loads(line)
            for line in (folder / "verdicts.jsonl").read_text().splitlines()
        ]
        body = _graded(run, rows)
        if body["kind"] == "scenarios":
            body.update(_played(folder, run, rows))
    inputs = dict(run["inputs"])
    if (folder / "probes.json").exists():
        inputs["probes.json"] = digest(folder / "probes.json")
    named = run.get("universe") or universe
    if run.get("universe") and universe and run["universe"] != universe:
        raise ReportError(
            f"{folder.name} graded {run['universe']}, evals/runs.yaml says {universe}"
        )
    graded = bool(set(body["measures"]) & set(UNIVERSE_MEASURES))
    if graded and not named:
        raise ReportError(
            f"{folder.name} graded a universe: add `universe: <id>` to its entry in evals/runs.yaml"
        )
    found = {
        "id": folder.name,
        "side": side,
        "label": run.get("label", ""),
        "universe": named if graded else None,
        **body,
        "inputs": inputs,
        "kinds": run.get("kinds", {}),
        "adapters": run["adapters"],
        "tiers": run["tiers"],
        "notes": run["notes"],
    }
    on_side(found)
    return found


def _chain(settled):
    """{rule: [[verdict, tier], ...]}: each example's chain verdict and settling tier, in order."""
    found = {}
    for e in settled:
        found.setdefault(e["rule"], []).append([e["verdict"], e["tier"]])
    return found


def models_of(recorded):
    """(tier, model) for each model a run's adapters recorded, named as the adapters route it: an
    agent that ran on the Codex CLI reads codex:<model>."""
    for tier, said in recorded.items():
        if tier == "agent":  # "<cli> <version>, model <model>", as play.py records it
            model = said.rpartition(", model ")[2]
            codex = said.split()[0] == adapters.CodexAgent.name
            yield tier, adapters.CODEX + model if codex else model
            continue
        for name in said.removeprefix("judges: ").removeprefix("filers: ").split(", "):
            yield tier, name


def on_side(s):
    """Refuse a run whose models belong to the other side's company; Jev serves both sides."""
    for tier, model in models_of(s["adapters"]):
        if model.split()[0] == adapters.Jev.name:
            continue
        if adapters.on_codex(model) != (s["side"] == "openai"):
            raise ReportError(
                f"{s['id']} is listed on the {SIDES[s['side']]}, but its {tier} model "
                f"{model} belongs to the other company"
            )


def _graded(run, rows):
    scenarios = run["kind"] == "skills"
    ran = set(run["tiers"])
    # a case no tier of this run touched (its rule's tiers were not chosen) is left out
    rows = [r for r in rows if r["trail"] or r["verdict"] != "undecided"]
    measures = (
        ["scenarios"]
        if scenarios
        else [
            m
            for m, shown in (
                ("grade", ran & set(GRADED)),
                # a filing check counts only when it filed something: a universe
                # with no artifact has nothing to sort
                ("sorting", any(t["tier"] == "sort" for r in rows for t in r["trail"])),
                ("recognition", any("recognition" in r for r in rows)),
            )
            if shown
        ]
    )
    votes = [
        next(
            (
                t["votes"]
                for t in r["trail"]
                if t["tier"] == "judgment" and "votes" in t
            ),
            None,
        )
        for r in rows
    ]
    judges = list(dict.fromkeys(m for v in votes if v for m in v))
    rules, cases, judged, settled_by = {}, {}, Counter(), {}
    for r, said in zip(rows, votes, strict=True):
        count = rules.setdefault(
            r["rule"], {"pass": 0, "fail": 0, "undecided": 0, "settled": {}}
        )
        count[r["verdict"]] += 1
        if r["verdict"] != "undecided":
            count["settled"][r["tier"]] = count["settled"].get(r["tier"], 0) + 1
            settled_by.setdefault(r["rule"], {})[r["ref"]] = r["tier"]
        coded = ""
        if said is not None:
            judged[r["rule"]] += 1
            coded = "".join(
                CODES.get(said[m]["verdict"], "u") if m in said else "u" for m in judges
            )
        if r["verdict"] != "pass" or set(coded) - {"p"}:
            cases.setdefault(r["rule"], {})[r["ref"]] = [r["verdict"], r["tier"], coded]
    body = {
        "kind": "scenarios" if scenarios else "grade",
        "measures": measures,
        "rules": rules,
        "cases": cases,
        "settled_by": settled_by,
        "judged": dict(judged),
        "judges": judges,
        "filed": sorted(
            {
                r["rule"]
                for r in rows
                if r["tier"] in FILED or any(t["tier"] in FILED for t in r["trail"])
            }
        ),
    }
    if scenarios:
        return body
    careful = run["adapters"].get("judgment", "")
    careful = careful.removeprefix("judges: ").split(", ") if careful else None
    if run["inputs"].get("evals/universe.yaml") != digest(SPEC):
        # graded under other shares: the current bar is not the run's bar
        careful = None
    return {
        **body,
        "recognition": _recognition(rows, careful),
        "sorting": _sorting(rows),
    }


def _played(folder, run, rows):
    """A scenario run's code checks per played run, the scenarios not graded, how many times each
    ran, and the counts of its wording/ grade of proposed definitions."""
    checks = {
        p.parent.relative_to(folder).as_posix(): json.loads(p.read_text())
        for p in sorted(Path(folder).glob("*/run-*/checks.json"))
    }
    # the scenario runner refs each case <scenario>/run-<n>/<subject>
    refs = [r["ref"] for r in rows if "/run-" in r["ref"]] + list(checks)
    runs = [int(m.group(1)) for ref in refs if (m := re.search(r"/run-(\d+)", ref))]
    wording = {}
    graded = Path(folder) / "wording/verdicts.jsonl"
    for line in graded.read_text().splitlines() if graded.exists() else []:
        r = json.loads(line)
        count = wording.setdefault(r["rule"], {"pass": 0, "fail": 0, "undecided": 0})
        count[r["verdict"]] += 1
    unplayed = [m.group(1) for n in run["notes"] if (m := UNPLAYED.match(n))]
    home = str(Path.home()) + "/"
    for c in checks.values():
        if c.get(TOOL_WRITES):
            c[TOOL_WRITES] = [
                "~/" + w.removeprefix(home) if w.startswith(home) else w
                for w in c[TOOL_WRITES]
            ]
    return {
        "scenarios": sorted({ref.split("/run-")[0] for ref in refs}),
        "n": max(runs, default=None),
        "checks": checks,
        "ungraded": sorted(
            [p for p, c in checks.items() if c.get("agent error")] + unplayed
        ),
        "wording": wording,
    }


def _recognition(rows, careful=None):
    sets = {}
    for r in rows:
        if "recognition" in r:
            sets.setdefault(r["recognition"]["set"], []).append(r)
    found = {}
    for name, rs in sets.items():
        shares = [
            (right / r["recognition"]["situations"], r["recognition"], filer)
            for r in rs
            for filer, right in r["recognition"]["right"].items()
            if r["recognition"]["situations"]
        ]
        lowest = None
        if shares:
            _, low, filer = min(shares, key=lambda s: s[0])
            lowest = {
                "value": low["value"],
                "right": low["right"][filer],
                "situations": low["situations"],
                "filer": filer,
            }
        verdicts = {r["verdict"] for r in rs}
        situations = sum(r["recognition"]["situations"] for r in rs)
        found[name] = {
            "kind": "factor" if rs[0]["ref"].startswith("factors") else "frame",
            "values": len(rs),
            "situations": situations,
            "filers": rs[0]["recognition"]["filers"],
            "lowest": lowest,
            "misses": [
                [r["text"], placed, by]
                for r in rs
                for placed, by in _went(r["recognition"]["misses"]).items()
            ],
            "verdict": next((v for v in ("fail", "undecided") if v in verdicts), "pass")
            if situations
            else "not run",
            "fails": sum(r["verdict"] == "fail" for r in rs),
            "careful": _careful(rs, careful),
        }
    return found


def _careful(rs, readers):
    """{readers, fails}: how many of a set's values fail when only `readers` (the run's judgment
    models) file, by sort.py's recognition verdict over the placements each row's trail kept and
    the rule's shares in evals/universe.yaml; None when the run recorded no judges, was graded
    under another evals/universe.yaml, or a row kept no placements. A reader with no placements
    leaves the set undecided, as a failed call does."""
    filed = [
        next((t.get("placed") for t in r["trail"] if t["tier"] == "recognise"), None)
        for r in rs
    ]
    if not readers or None in filed:
        return None
    rules = yaml.safe_load(SPEC.read_text())["rules"]
    group = [
        SimpleNamespace(
            rule={"recognise": rules[r["rule"]]["recognise"]},
            context={"set": [], "id": r["recognition"]["value"]},
        )
        for r in rs
    ]
    members = [
        (
            r["text"],
            tuple(f"situation {n + 1}" for n in range(r["recognition"]["situations"])),
        )
        for r in rs
    ]
    placed = [{f: p[f] for f in readers if f in p} for p in filed]
    failed = {
        f: "no placements recorded" for f in readers if any(f not in p for p in filed)
    }
    outcomes = sort.recognition(lambda case: False)(group, members, placed, failed)
    return {"readers": readers, "fails": sum(o.verdict == "fail" for o in outcomes)}


def _went(misses):
    """{where a value's situations went instead: {filer: how many}}."""
    found = {}
    for by in misses.values():
        for filer, placed in by.items():
            shown = "none" if placed == NONE else placed
            found.setdefault(shown, Counter())[filer] += 1
    return {placed: dict(by) for placed, by in found.items()}


def _sorting(rows):
    members = [(r, t) for r in rows for t in r["trail"] if t["tier"] == "sort"]
    filers = {}
    for r, t in members:
        for filer, labels in t.get("placed", {}).items():
            count = filers.setdefault(filer, {"right": 0, "n": 0, "unsure": 0})
            count["n"] += len(labels)
            count["right"] += sum(label == r["text"] for label in labels)
            count["unsure"] += sum(label == "unsure" for label in labels)
    counted = Counter(r["verdict"] for r, _ in members)
    return {
        "rules": sorted({r["rule"] for r, _ in members}),
        "members": {v: counted[v] for v in ("pass", "fail", "undecided")},
        "filers": filers,
    }


def summary_text(summary):
    return json.dumps(summary, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


# Collecting and writing


def entries(runs_file):
    runs = (yaml.safe_load(Path(runs_file).read_text()) or {}).get("runs") or []
    for entry in runs:
        if entry.get("side") not in SIDES:
            raise ReportError(
                f"side must be one of {', '.join(SIDES)}, not {entry.get('side')!r}"
            )
        if not entry.get("folder"):
            raise ReportError(f"a {entry['side']} run has no folder")
    return runs


def labelled_by(runs_file=RUNS):
    """{universe id: who wrote and labelled its situations, one '<side>: <who>' line per side}."""
    found = (yaml.safe_load(Path(runs_file).read_text()) or {}).get("labelled_by") or {}
    shape = (
        "labelled_by maps each universe id to a list of lines, each naming a side and who "
        "labelled on it, as in 'Anthropic side: <who>'"
    )
    if not isinstance(found, dict):
        raise ReportError(shape)
    for universe, lines in found.items():
        if not isinstance(lines, list) or not lines or not all(map(_labeller, lines)):
            raise ReportError(f"{shape}; {universe} does not")
    return found


def _labeller(line):
    return isinstance(line, str) and any(
        line.startswith(f"{name}: ") and line.removeprefix(f"{name}: ").strip()
        for name in SIDES.values()
    )


def collect(runs_file=RUNS, results=RESULTS, root=ROOT):
    """One summary per listed run: from its folder when it is here, else its committed summary."""
    found, held = [], {}
    for entry in entries(runs_file):
        folder = Path(root) / entry["folder"]
        saved = Path(results) / f"{folder.name}.json"
        if folder.is_dir():
            found_summary = summarise(folder, entry["side"], entry.get("universe"))
        elif saved.exists():
            found_summary = json.loads(saved.read_text())
            on_side(found_summary)
        else:
            raise ReportError(
                f"{entry['folder']} is not on this machine and {saved} is not committed"
            )
        for measure in found_summary["measures"]:
            key = (entry["side"], measure, found_summary["universe"])
            if key in held:
                of = f" of {key[2]}" if key[2] else ""
                raise ReportError(
                    f"two runs of {measure}{of} on the {entry['side']} side: "
                    f"{held[key]} and {found_summary['id']}"
                )
            held[key] = found_summary["id"]
        found.append(found_summary)
    return found


def load_retired(folder=RETIRED):
    """{universe id: its retired-fails document}, one file per universe, named by its id."""
    return {
        p.stem: yaml.safe_load(p.read_text())
        for p in sorted(Path(folder).glob("*.yaml"))
    }


def write_all(runs_file, results, out, retired, root=ROOT):
    # build from the summaries exactly as they are written, so --check builds the same report
    summaries = [json.loads(summary_text(s)) for s in collect(runs_file, results, root)]
    results = Path(results)
    for kept in summaries:
        results.mkdir(parents=True, exist_ok=True)
        (results / f"{kept['id']}.json").write_text(summary_text(kept))
    for stale in results.glob("*.json") if results.is_dir() else ():
        if stale.stem not in {s["id"] for s in summaries}:
            stale.unlink()
    Path(out).write_text(build(summaries, retired, labelled_by(runs_file)))


def drift(runs_file=RUNS, results=RESULTS, out=REPORT, retired=None):
    """What differs between the committed report and summaries and what they build; no folder is read."""
    retired = load_retired() if retired is None else retired
    results = Path(results)
    problems, summaries = [], []
    for entry in entries(runs_file):
        saved = results / f"{Path(entry['folder']).name}.json"
        if not saved.exists():
            problems.append(f"{saved} is missing")
            continue
        text = saved.read_text()
        kept = json.loads(text)
        if text != summary_text(kept):
            problems.append(f"{saved} is not in the form report.py writes")
        if kept["side"] != entry["side"]:
            problems.append(
                f"{saved} says side {kept['side']}, evals/runs.yaml says {entry['side']}"
            )
        try:
            on_side(kept)
        except ReportError as refused:
            problems.append(str(refused))
        if entry.get("universe") and kept["universe"] not in (None, entry["universe"]):
            problems.append(
                f"{saved} says universe {kept['universe']}, evals/runs.yaml says {entry['universe']}"
            )
        summaries.append(kept)
    known = {s["id"] for s in summaries}
    problems += [
        f"{p} belongs to no listed run"
        for p in sorted(results.glob("*.json") if results.is_dir() else ())
        if p.stem not in known
    ]
    if problems:
        return problems
    if Path(out).read_text() != build(summaries, retired, labelled_by(runs_file)):
        return [f"{out} is not what report.py builds"]
    return []


# Rendering


def cell(value):
    return " ".join(str(value).replace("|", "\\|").split())


def table(header, rows):
    lines = [f"| {' | '.join(header)} |", f"| {' | '.join(['---'] * len(header))} |"]
    lines += [f"| {' | '.join(cell(c) for c in row)} |" for row in rows]
    return lines


def by_measure(summaries, universe=None):
    """{measure: {side: summary}}, in the order of the sides and measures. The universe
    measures hold only the runs of `universe`, so runs of two universes never meet."""
    held = {m: {} for m in MEASURES}
    for s in summaries:
        for m in s["measures"]:
            if m not in UNIVERSE_MEASURES or s["universe"] == universe:
                held[m][s["side"]] = s
    return held


def different(measure, a, b):
    """Why two runs of one measure cannot be put side by side, or None."""
    uses = USES[measure]
    kinds = {**b.get("kinds", {}), **a.get("kinds", {})}
    names = sorted(
        n
        for n in {*a["inputs"], *b["inputs"]}
        if input_kind(n, kinds) in uses and a["inputs"].get(n) != b["inputs"].get(n)
    )
    if names:
        return f"{', '.join(names)} {'differs' if len(names) == 1 else 'differ'}"
    if measure in ("grade", "scenarios", "sorting"):
        rules = _rules(measure, a, b)
        odd = [r for r in rules if _n(a, r) != _n(b, r)]
        if odd:
            return f"cases differ for {', '.join(odd)}"
    if measure == "recognition" and set(a["recognition"]) != set(b["recognition"]):
        return "frames differ"
    return None


def _n(s, rule):
    count = s["rules"].get(rule)
    return count and count["pass"] + count["fail"] + count["undecided"]


def _rules(measure, a, b):
    if measure == "sorting":
        return sorted({*a["sorting"]["rules"], *b["sorting"]["rules"]})
    return sorted({*graded_rules(a), *graded_rules(b)})


def graded_rules(s):
    """The rules the grade (or scenarios) figure counts: those no filing check settles."""
    return [rule for rule in s["rules"] if rule not in s["filed"]]


def verdict_of(s, rule, ref):
    entry = s["cases"].get(rule, {}).get(ref)
    return (entry[0], entry[1]) if entry else ("pass", "")


def agreement(measure, a, b):
    """(cases both sides settled, cases with the same verdict) over the measure's rules."""
    both = same = 0
    for rule in _rules(measure, a, b):
        n = _n(a, rule)
        keys = {*a["cases"].get(rule, {}), *b["cases"].get(rule, {})}
        unsettled = {
            k
            for k in keys
            if "undecided" in (verdict_of(a, rule, k)[0], verdict_of(b, rule, k)[0])
        }
        settled = {k for k in keys if k not in unsettled}
        both += n - len(unsettled)
        same += (
            n
            - len(unsettled)
            - sum(
                verdict_of(a, rule, k)[0] != verdict_of(b, rule, k)[0] for k in settled
            )
        )
    return both, same


def settled_pairs(measure, a, b):
    """((verdict, tier) on side a, (verdict, tier) on side b) for each case both sides settled.
    Calibration pairs examples by their order, since both runs read the same spec."""
    if measure.startswith("calibration"):
        for rule in sorted(set(a["chain"]) & set(b["chain"])):
            yield from zip(
                map(tuple, a["chain"][rule]), map(tuple, b["chain"][rule]), strict=True
            )
        return
    for rule in _rules(measure, a, b):
        ta, tb = a["settled_by"].get(rule, {}), b["settled_by"].get(rule, {})
        for ref in sorted(set(ta) & set(tb)):
            yield (
                (verdict_of(a, rule, ref)[0], ta[ref]),
                (verdict_of(b, rule, ref)[0], tb[ref]),
            )


def judged_apart(measure, a, b):
    """Agreement with the judges counted apart from the tiers both sides share (code and Jev),
    the filing checks and the cases the two sides settled by different tiers."""
    found, same = Counter(), Counter()
    for (va, ta), (vb, tb) in settled_pairs(measure, a, b):
        if "undecided" in (va, vb):
            continue
        if ta == tb == "judgment":
            kind = "judged"
        elif {ta, tb} <= set(SHARED):
            kind = "shared"
        elif {ta, tb} <= set(FILED):
            kind = "filed"
        else:
            kind = "mixed"
        found[kind] += 1
        same[kind] += va == vb

    def more(kind, by):
        if found[kind] == same[kind]:
            return f"{found[kind]} more settled the same way by {by}"
        return f"{found[kind]} more settled by {by}, {same[kind]} of them the same"

    said = (
        f"the two companies' judges agree on {same['judged']} of {found['judged']}; "
        f"{more('shared', 'shared code or Jev')}"
    )
    if found["filed"]:
        said += f"; {more('filed', 'the filing checks')}"
    if found["mixed"]:
        said += f"; {found['mixed']} more settled by different tiers, {same['mixed']} of them the same"
    return said


def counts(s, rules=None):
    total = Counter()
    for rule, count in s["rules"].items():
        if rules is None or rule in rules:
            total.update({v: count[v] for v in ("pass", "fail", "undecided")})
    return total


def figure(measure, s):
    if measure.startswith("calibration"):
        sums = Counter()
        for r in s["table"]:
            if r["tier"] == "chain":
                sums.update(
                    {k: r[k] for k in ("n", "tp", "fn", "tn", "fp", "undecided")}
                )
        return (
            f"{plural(sums['n'], 'example')}: {sums['tp']} fails caught, {sums['fn']} missed, "
            f"{sums['tn']} passes kept, {sums['fp']} wrongly failed, {sums['undecided']} undecided"
        )
    if measure == "recognition":
        if not s["recognition"]:
            return "not run"
        sets = Counter(r["verdict"] for r in s["recognition"].values())
        return (
            f"{sets_named(s['recognition'])}: {sets['pass']} pass, {sets['fail']} fail, "
            f"{sets['undecided']} undecided, {sets['not run']} not run"
            f"; {values_failing(s['recognition'])}"
        )
    if measure == "sorting":
        total = counts(s, s["sorting"]["rules"])
        if not sum(total.values()):
            return "not run"
        return f"{plural(sum(total.values()), 'member')}: {_verdicts(total)}"
    total = counts(s, graded_rules(s))
    if measure == "scenarios":
        if s["n"] is None:
            return "not run"
        over = (
            f"over {plural(len(s['scenarios']), 'scenario')}, each run {times(s['n'])}"
        )
        return f"{plural(sum(total.values()), 'check')} {over}: {_verdicts(total)}"
    return f"{plural(sum(total.values()), 'case')}: {_verdicts(total)}"


def values_failing(recognition):
    """How many values fail with every reader, then with the careful readers only."""
    values = sum(r["values"] for r in recognition.values())
    said = f"{sum(r['fails'] for r in recognition.values())} of {values} values fail (all readers)"
    careful = [r["careful"] for r in recognition.values()]
    if not all(careful):
        return f"{said}; careful readers not recorded"
    return (
        f"{said}; {sum(c['fails'] for c in careful)} of {values} (careful readers only)"
    )


def times(n):
    return "once (n=1)" if n == 1 else f"{n} times (n={n})"


def _verdicts(total):
    return f"{total['pass']} pass, {total['fail']} fail, {total['undecided']} undecided"


def headline(held, measures, extra=()):
    rows = []
    for measure in measures:
        name, shows = MEASURES[measure]
        a, b = held[measure].get("anthropic"), held[measure].get("openai")
        if not a or not b:
            cells = [figure(measure, s) if s else "not run" for s in (a, b)]
            rows.append([name, shows, *cells, "not run"])
            continue
        reason = different(measure, a, b)
        if reason:
            same = f"not comparable: {reason}"
            rows.append([name, shows, same, same, "not comparable"])
            continue
        rows.append(
            [name, shows, figure(measure, a), figure(measure, b), _agree(measure, a, b)]
        )
    return table(
        ["Measure", "What it shows", SIDES["anthropic"], SIDES["openai"], "Both agree"],
        [*rows, *extra],
    )


def calibration_caveat(held):
    """Per side, the rules and behaviours whose calibration chain missed an owner label."""
    parts = []
    for side, name in SIDES.items():
        runs = [
            held[m].get(side) for m in ("calibration-universe", "calibration-skills")
        ]
        if not any(runs):
            parts.append(f"{name}: calibration not run")
            continue
        missed = sorted(
            {m["rule"] for s in runs if s for m in s["misses"] if m["tier"] == "chain"}
        )
        parts.append(f"{name}: {', '.join(f'`{r}`' for r in missed) or 'none'}")
    return (
        "Rules whose calibration chain missed an owner label, so their figures carry that "
        f"caveat: {'; '.join(parts)}."
    )


def _agree(measure, a, b):
    if measure.startswith("calibration") and a["chain"] and b["chain"]:
        return judged_apart(measure, a, b)
    if measure.startswith("calibration"):  # runs that kept no example's tier
        chains = [
            {r["rule"]: r for r in s["table"] if r["tier"] == "chain"} for s in (a, b)
        ]
        rules = sorted(set(chains[0]) & set(chains[1]))
        same = sum(chains[0][r] == chains[1][r] for r in rules)
        return f"same on {same} of {len(rules)} rules"
    if measure == "recognition":
        sets = sorted(a["recognition"])
        same = sum(
            a["recognition"][s]["verdict"] == b["recognition"][s]["verdict"]
            for s in sets
        )
        return f"same verdict on {same} of {sets_named(a['recognition'])}"
    if measure == "grade":
        return judged_apart(measure, a, b)
    both, same = agreement(measure, a, b)
    return f"same verdict on {same} of {both} cases both sides settled"


def run_line(s):
    label = f" ({s['label']})" if s["label"] else ""
    return f"Run `{s['id']}`{label}."


def per_side(held, measure, render, universe=None):
    """One subsection per side for a measure: its own figures, or "not run"."""
    title = MEASURES[measure][0].split(" (")[0]
    if universe:
        title += f" of `{universe}`"
    if not held[measure]:
        return [f"{title}: not run on either side.", ""]
    lines = []
    for side, name in SIDES.items():
        s = held[measure].get(side)
        lines += [f"### {title}, {name}", ""]
        lines += [run_line(s), "", *render(s)] if s else ["Not run.", ""]
    return lines


def calibration_body(s):
    chain = [r for r in s["table"] if r["tier"] == "chain"]
    columns = [
        "n",
        "Caught fails",
        "Missed fails",
        "Kept passes",
        "Wrongly failed",
        "Undecided",
    ]
    keys = ("n", "tp", "fn", "tn", "fp", "undecided")
    lines = ["Per tier, over every rule:", ""]
    tiers = list(dict.fromkeys(r["tier"] for r in s["table"]))
    lines += table(
        ["Tier", *columns],
        [
            [t, *(sum(r[k] for r in s["table"] if r["tier"] == t) for k in keys)]
            for t in tiers
        ],
    )
    lines += ["", "Per rule, all tiers together:", ""]
    lines += table(
        ["Rule", *columns], [[f"`{r['rule']}`", *(r[k] for k in keys)] for r in chain]
    )
    lines.append("")
    if s["misses"]:
        lines += ["Disagreements with the owner:", ""]
        lines += [
            f'- `{m["rule"]}` ({m["tier"]}): "{m["text"]}" labelled {m["label"]}'
            for m in s["misses"]
        ]
        lines.append("")
    else:
        lines += ["No disagreements with the owner.", ""]
    return lines


def grade_body(s):
    lines = [f"Tiers: {', '.join(s['tiers'])}.", ""]
    rows = []
    for rule, count in sorted(s["rules"].items()):
        settled = " / ".join(str(count["settled"].get(t, 0)) for t in TIERS)
        rows.append(
            [f"`{rule}`", count["pass"], count["fail"], count["undecided"], settled]
        )
    lines += table(
        [
            "Rule",
            "Pass",
            "Fail",
            "Undecided",
            "Settled by deterministic / decision / judgment / sort / recognise",
        ],
        rows,
    )
    return [*lines, ""]


def recognition_body(s):
    filers = list(
        dict.fromkeys(f for r in s["recognition"].values() for f in r["filers"])
    )
    rows = []
    for name, r in sorted(s["recognition"].items()):
        cells = []
        for filer in filers:
            count = r["filers"].get(filer)
            if not count or not count["n"]:
                cells.append("not run")
                continue
            apart = f"{count['unsure']} unsure, {count['none']} none"
            if "off_by_one" in count:
                apart += f", {count['off_by_one']} off by one"
            cells.append(f"{count['right']}/{count['n']} ({apart})")
        low = r["lowest"]
        lowest = (
            f"{low['value']} {low['right']}/{low['situations']} ({low['filer']})"
            if low
            else "—"
        )
        rows.append([name, r["values"], r["situations"], *cells, lowest, r["verdict"]])
    went = [
        f"- {name}: {expected} → {placed} ({', '.join(f'{f} {n}' for f, n in by.items())})"
        for name, r in sorted(s["recognition"].items())
        for expected, placed, by in r["misses"]
    ]
    careful = [r["careful"] for r in s["recognition"].values()]
    named = (
        f" The careful readers are this side's judgment models: {', '.join(careful[0]['readers'])}."
        if careful and all(careful)
        else ""
    )
    return [
        f"{values_failing(s['recognition'])}.{named}",
        "",
        "Each reader's right / situations in the set; unsure and none count as misses, and on a ladder a miss one step away is counted as off by one.",
        "",
        *table(
            ["Set", "Values", "Situations", *filers, "Lowest value", "Verdict"], rows
        ),
        "",
        *(
            [
                "Where misses went, expected → placed, with each reader's count:",
                "",
                *went,
                "",
            ]
            if went
            else []
        ),
    ]


def sorting_body(s):
    sort = s["sorting"]
    lines = [f"Members: {_verdicts(counts(s, sort['rules']))}.", ""]
    if sort["filers"]:
        lines += table(
            ["Reader", "Probes", "Filed right", "Unsure", "Filed elsewhere"],
            [
                [f, c["n"], c["right"], c["unsure"], c["n"] - c["right"] - c["unsure"]]
                for f, c in sort["filers"].items()
            ],
        )
    else:
        lines.append("Each reader's own placements were not recorded in this run.")
    return [*lines, ""]


def scenarios_body(s):
    n = s["n"]
    lines = (
        [
            f"Each scenario ran {times(n)}.",
            "",
        ]
        if n
        else ["No scenario was played.", ""]
    )
    if s["scenarios"]:
        lines += [f"Scenarios: {', '.join(s['scenarios'])}.", ""]
    rows = [
        [f"`{rule}`", c["pass"], c["fail"], c["undecided"]]
        for rule, c in sorted(s["rules"].items())
    ]
    lines += [*table(["Behaviour", "Pass", "Fail", "Undecided"], rows), ""]
    skills = {}
    for c in s["checks"].values():
        runs = skills.setdefault(c["skill"], [0, 0])
        runs[0] += 1
        runs[1] += bool(c["skill fired"])
    lines += ["Skills exercised:", ""]
    lines += [
        *table(
            ["Skill", "Runs", "Fired in"], [[k, *v] for k, v in sorted(skills.items())]
        ),
        "",
    ]
    lines += ["Code checks, per run:", ""]
    lines += table(
        [
            "Run", "Skill fired", "Writes outside .knowledge-bus",
            "Writes outside the work folder (Claude tool calls)", "conforms_to changed",
            "Validates", "Loaded beside the skills under test", "Possible script drift", "Agent error",
        ],
        [[f"`{run}`", *_checked(c)] for run, c in s["checks"].items()],
    )  # fmt: skip
    lines.append("")
    if s["ungraded"]:
        shown = ", ".join(f"`{u}`" for u in s["ungraded"])
        lines += [f"Not graded: {shown}.", ""]
    lines += ["Proposed definitions, graded with the universe rules (`wording/`):", ""]
    if s["wording"]:
        rows = [
            [f"`{rule}`", c["pass"], c["fail"], c["undecided"]]
            for rule, c in sorted(s["wording"].items())
        ]
        lines += [*table(["Rule", "Pass", "Fail", "Undecided"], rows), ""]
    else:
        lines += ["No proposed definition was graded.", ""]
    return lines


TOOL_WRITES = "writes outside the work folder (from tool calls)"


def _checked(c):
    """One played run's code checks as table cells."""

    def yes(value):
        return {True: "yes", False: "no", None: "n/a"}[value]

    def listed(values):
        return ", ".join(map(str, values)) or "none"

    v = c["validates"]
    validates = (
        "no .knowledge-bus/"
        if v["before"] is None and v["after"] is None
        else f"before {yes(v['before'])}, after {yes(v['after'])}"
    )
    # Runs played before the check was renamed recorded it as "script drift".
    drift = c.get("possible script drift", c.get("script drift"))
    return [
        yes(c["skill fired"]),
        listed(c["writes outside .knowledge-bus"]),
        # Runs played before this check existed did not record it.
        listed(outside) if (outside := c.get(TOOL_WRITES)) is not None else "n/a",
        listed(c["conforms_to changed"]),
        validates,
        listed(c["loaded beside the skills under test"]),
        f"before owner reply {listed(drift)}" if drift else "none",
        c["agent error"] or "none",
    ]


def case_by_case(held, measures, heading):
    lines = [heading, ""]
    for measure in measures:
        name = MEASURES[measure][0].split(" (")[0]
        a, b = held[measure].get("anthropic"), held[measure].get("openai")
        if not a or not b:
            lines += [f"{name}: not run on both sides.", ""]
            continue
        reason = different(measure, a, b)
        if reason:
            lines += [f"{name}: not comparable: {reason}.", ""]
            continue
        found = []
        for rule in _rules(measure, a, b):
            for ref in sorted({*a["cases"].get(rule, {}), *b["cases"].get(rule, {})}):
                (va, ta), (vb, tb) = verdict_of(a, rule, ref), verdict_of(b, rule, ref)
                if va != vb:
                    found.append(
                        f"- `{rule}` `{ref}`: {SIDES['anthropic']} {va}{f' ({ta})' if ta else ''}, "
                        f"{SIDES['openai']} {vb}{f' ({tb})' if tb else ''}"
                    )
        both, _ = agreement(measure, a, b)
        lines += [
            f"{name}: the sides settled {both} cases and differ on {len(found)}.",
            "",
        ]
        lines += [*found[:50], ""] if found else []
        if len(found) > 50:
            lines += [f"And {len(found) - 50} more.", ""]
    return lines


def frame_disagreements(held, heading):
    lines = [heading, ""]
    a, b = held["recognition"].get("anthropic"), held["recognition"].get("openai")
    if not a or not b:
        lines += ["Recognition: not run on both sides.", ""]
    elif different("recognition", a, b):
        lines += [f"Recognition: not comparable: {different('recognition', a, b)}.", ""]
    else:
        found = [
            f"- `{f}`: {SIDES['anthropic']} {a['recognition'][f]['verdict']}, {SIDES['openai']} {b['recognition'][f]['verdict']}"
            for f in sorted(a["recognition"])
            if a["recognition"][f]["verdict"] != b["recognition"][f]["verdict"]
        ]
        lines += [
            f"The sides differ on {len(found)} of {sets_named(a['recognition'])}.",
            "",
            *found,
            *([""] if found else []),
        ]
    return lines


def pair_rows(grade):
    """Each Anthropic-side judge with each OpenAI-side judge, from the votes both runs kept: a
    verdict stands only when both agree. Cases no run recorded a split on count as passes, so
    the runs must have judged the same number of cases for a rule. (rows, None), or (None, why
    the runs are not comparable), or (None, None) when the pairs were not run."""
    a, b = grade.get("anthropic"), grade.get("openai")
    if not a or not b or not a["judges"] or not b["judges"]:
        return None, None
    reason = different("grade", a, b)
    if reason:
        return None, reason
    rows = []
    for i, ja in enumerate(a["judges"]):
        for j, jb in enumerate(b["judges"]):
            total = Counter()
            for rule in sorted(a["judged"]):
                n, keys = (
                    a["judged"][rule],
                    {*a["cases"].get(rule, {}), *b["cases"].get(rule, {})},
                )
                recorded = [
                    s["cases"].get(rule, {}).get(k) for s in (a, b) for k in keys
                ]
                if (
                    b["judged"].get(rule) != n
                    or len(keys) > n
                    or not all(e[2] for e in recorded if e)
                ):
                    continue
                total["n"] += n
                total["pass"] += n - len(keys)
                for k in keys:
                    votes = "".join(
                        (s["cases"].get(rule, {}).get(k) or ["", "", "pppp"])[2][x]
                        for s, x in ((a, i), (b, j))
                    )
                    total[{"pp": "pass", "ff": "fail"}.get(votes, "undecided")] += 1
            rows.append(
                [
                    f"{ja} + {jb}",
                    total["n"],
                    total["pass"],
                    total["fail"],
                    total["undecided"],
                ]
            )
    return rows, None


def judge_pairs(grade, heading):
    lines = [heading, ""]
    rows, reason = pair_rows(grade)
    if reason:
        return [*lines, f"Not comparable: {reason}.", ""]
    if rows is None:
        return [
            *lines,
            "Pairs not run: they need a grade run on each side with each judge's vote kept.",
            "",
        ]
    return [*lines, *table(["Pair", "Cases", "Pass", "Fail", "Undecided"], rows), ""]


def pairs_row(grade):
    """The universe headline's row for the judge pairs: each side's judges, then the spread of
    the pairs' verdicts."""
    sides = [grade.get(side) for side in SIDES]
    cells = [
        f"judges: {', '.join(s['judges'])}" if s and s["judges"] else "not run"
        for s in sides
    ]
    rows, reason = pair_rows(grade)
    if reason or rows is None:
        return [*PAIRS, *cells, "not comparable" if reason else "not run"]
    spread = []
    for i, verdict in ((2, "pass"), (3, "fail"), (4, "undecided")):
        low, high = min(r[i] for r in rows), max(r[i] for r in rows)
        spread.append(f"{low if low == high else f'{low} to {high}'} {verdict}")
    shown = f"{plural(len(rows), 'pair')}, {plural(rows[0][1], 'case')} each: {', '.join(spread)}"
    return [*PAIRS, *cells, shown]


def retired_section(retired, universe):
    fails = retired["fails"]
    lines = [
        f"### Retired for frames of `{universe}`",
        "",
        retired["decision"],
        "",
        f"The {len(fails)} fails below were found in `{retired['graded_in']}`, the last full grade before the change, and are listed once here, not hidden.",
        "",
    ]
    return [
        *lines,
        *table(
            ["Rule", "Where", "Wording"],
            [[f"`{f['rule']}`", f"`{f['ref']}`", f["text"]] for f in fails],
        ),
        "",
    ]


def universe_section(summaries, universe, retired, labelled=None):
    """Everything one universe's runs measure: headline, grade, recognition (with who labelled its
    situations), sorting, where the sides disagree and the frame fails retired for it."""
    held = by_measure(summaries, universe)
    lines = [
        f"## Universe `{universe}`",
        "",
        f"### Headline of `{universe}`",
        "",
        *headline(held, UNIVERSE_MEASURES, [pairs_row(held["grade"])]),
        "",
    ]
    for measure, render in (
        ("grade", grade_body),
        ("recognition", recognition_body),
        ("sorting", sorting_body),
    ):
        lines += per_side(held, measure, render, universe)
        if measure == "recognition" and labelled:
            title = MEASURES[measure][0].split(" (")[0]
            # its own heading only after the sides' subsections, so it is not read as one side's
            heading = [f"### {title} of `{universe}`, who labelled the situations", ""]
            lines += [
                *(heading if held[measure] else []),
                f"Who wrote and labelled the situations: {'; '.join(labelled)}.",
                "",
            ]
    lines += [
        f"### Where the sides disagree on `{universe}`",
        "",
        *case_by_case(held, ("grade", "sorting"), f"#### Case by case on `{universe}`"),
        *frame_disagreements(held, f"#### Frames and factors of `{universe}`"),
        *judge_pairs(
            held["grade"], f"#### Judge pairs across the sides on `{universe}`"
        ),
    ]
    return [*lines, *retired_section(retired, universe)] if retired else lines


def cost_section(summaries):
    rows = []
    for s in summaries:
        models = "; ".join(f"{t}: {a}" for t, a in s["adapters"].items())
        costs = "; ".join(n for n in s["notes"] if "cost:" in n or "tokens" in n)
        label = f" ({s['label']})" if s["label"] else ""
        rows.append(
            [f"`{s['id']}`{label}", SIDES[s["side"]], models or "n/a", costs or "n/a"]
        )
    if not rows:
        return ["No run is listed.", ""]
    return [COST_BASIS, "", *table(["Run", "Side", "Models", "Cost"], rows), ""]


def date_of(summaries):
    dates = [
        m.group(1) for s in summaries if (m := re.search(r"(\d{8})T\d{6}", s["id"]))
    ]
    return f"{max(dates)[:4]}-{max(dates)[4:6]}-{max(dates)[6:]}" if dates else None


def build(summaries, retired, labelled=None):
    """The report; `retired` maps a universe id to its retired-fails document and `labelled` to
    who labelled its situations. Each universe with a run, a retired list or labellers gets a
    section."""
    held = by_measure(summaries)
    labelled = labelled or {}
    universes = sorted(
        {s["universe"] for s in summaries if s["universe"]}
        | set(retired)
        | set(labelled)
    )
    latest = date_of(summaries)
    played = {s["n"] for s in summaries if "scenarios" in s["measures"]}
    commands = (
        COMMANDS.replace("just evals-play", f"just evals-play --runs {n}")
        if len(played) == 1 and (n := next(iter(played)))
        else COMMANDS
    )
    lines = [
        "# Evaluation report",
        "",
        (
            "Built by `tools/evals/report.py` from the runs in `evals/runs.yaml`; it calls no model. "
            'Anything without a run reads "not run". Sides are compared only when the inputs '
            "a measure depends on have the same digests. The universe grade, recognition and sorting are "
            "reported per universe, and runs of different universes are never compared."
        ),
        "",
        f"Labels: calibrated on {EXAMPLES}; recognition on {SITUATIONS}; each scenario's figure says how many times it ran (n).",
        "",
        f"Latest run: {latest}."
        if latest
        else "Runs are listed in `evals/runs.yaml`."
        if summaries
        else "No run is listed in `evals/runs.yaml`.",
        "",
    ]
    if summaries:
        lines += table(
            ["Run", "Side", "Universe", "Measures", "Input", "Digest"],
            [
                [
                    f"`{s['id']}`",
                    SIDES[s["side"]],
                    s["universe"] or "—",
                    ", ".join(s["measures"]),
                    f"`{name}`",
                    digest[:23],
                ]
                for s in summaries
                for name, digest in sorted(s["inputs"].items())
            ],
        )
        lines.append("")
    lines += [
        "## Headline",
        "",
        "The figures this report stands behind.",
        "",
        RELATE,
        "",
        *headline(held, INDEPENDENT),
        "",
        calibration_caveat(held),
        "",
    ]
    lines += ["## Calibration", "", f"Calibrated on {EXAMPLES}.", ""]
    for measure in ("calibration-universe", "calibration-skills"):
        lines += per_side(held, measure, calibration_body)
    lines += ["## Agent scenarios", ""]
    lines += per_side(held, "scenarios", scenarios_body)
    lines += [
        "## Where the sides disagree",
        "",
        *case_by_case(held, ("scenarios",), "### Case by case"),
    ]
    for universe in universes:
        lines += universe_section(
            summaries, universe, retired.get(universe), labelled.get(universe)
        )
    lines += ["## Cost and models", "", *cost_section(summaries)]
    lines += [
        "## Not measured here",
        "",
        "- Effect on outcomes: whether these universes and skills change what people get done.",
        "- How often agent behaviours pass over many runs.",
        "- Owners who go off script, and whether the definitions fit real work.",
        "- Whether wording is plain to people rather than models.",
        "",
        "## How to reproduce",
        "",
        "```sh",
        commands,
        "```",
        "",
        (
            "List each run folder in `evals/runs.yaml` before `just evals-report`. "
            'The runbook for the OpenAI side is in `evals/README.md`, under "Running on another vendor".'
        ),
        "",
    ]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.check:
            problems = drift()
            print("\n".join(problems))
            return 1 if problems else 0
        write_all(RUNS, RESULTS, REPORT, load_retired())
    except ReportError as error:
        print(error, file=sys.stderr)
        return 1
    print(REPORT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
