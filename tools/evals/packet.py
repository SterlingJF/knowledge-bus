"""Answer the OpenAI side's model calls in a desktop app: one session per model, every prompt
written out as a packet, and the replies turned back into ordinary run folders.

    packet.py build --anthropic-run FOLDER [--anthropic-run FOLDER ...] --out DIR
                    [--judge-model M,M] [--light-model M]
    packet.py apply --anthropic-run FOLDER [--anthropic-run FOLDER ...] --replies DIR
                    [--label TEXT] [--out DIR] [--effort MODEL=LEVEL ...]

build mirrors each Anthropic-side run folder (a calibration, or a universe grade) through
grade.py's own pipeline, keeping every prompt a careful or light model would be sent, in
grade.py's order, each prompt once. It writes, under DIR, one folder per model (named for the
model without `codex:`): packets/ (each file is exactly one prompt), PROMPT.md to paste into the
app, a reply-schema-<kind>.json per kind of packet, and an empty replies/. Careful models get
every packet, the light model only the filing ones. DIR/manifest.json is private: it links each
packet to its prompt and run, and never goes into a session.

apply checks every reply against its kind's schema and its packet's items, and the Anthropic
runs and their inputs against what build saw, then runs the same pipeline again, answering each
prompt from its reply, and writes one run folder per Anthropic run under
.evidence/<date>/evals/ (or --out). Only the judges and the model filers come from the replies.
The deterministic tier, the decision tier, the decision model's filings and a universe's sort
passages are the same on both sides, so they are taken from the Anthropic run, and the run's
notes say so. Calls no model.
"""

import argparse
import hashlib
import json
import re
import shutil
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import adapters
import grade
import report
import sort
import spec as spec_module
import tiers
import yaml

ROOT = grade.ROOT
SCHEMA = "evals-packets/1"
JUDGES = ("codex:gpt-6-astra", "codex:gpt-6.1-sol")
LIGHT = "codex:gpt-6-luna"
# kind: (the instructions grade.py sends as the system prompt, the reply's schema)
KINDS = {
    "judge": (adapters.JUDGE_SYSTEM, adapters.VERDICTS),
    "file": (adapters.FILE_SYSTEM, adapters.FILINGS),
    "pick": (adapters.RECOGNISE_SYSTEM, adapters.OPTION),
}
KIND_OF = {system: kind for kind, (system, _) in KINDS.items()}
WHATS = ("sort", "recognise", "sort and recognise")
NO_COST = "n/a (answered in the Codex app, which reports no cost)"
CASES_USED = " (cases used)"


class Refused(Exception):
    pass


class Unrecorded(LookupError):
    """A prompt no packet holds. Not a RuntimeError, so no retry and no judge swallows it; a
    sorter may, so apply also refuses when the prompts asked differ from the packets used."""


def digest(system, prompt):
    return "sha256:" + hashlib.sha256(f"{system}\n\n{prompt}".encode()).hexdigest()


def session_of(model):
    return model.removeprefix(adapters.CODEX)


def listed(parts):
    return ", ".join(parts[:-1]) + " and " + parts[-1] if len(parts) > 1 else parts[0]


@dataclass
class Source:
    """One Anthropic-side run folder: a calibration (`data`) or a universe grade (`rows`)."""

    folder: Path
    run: dict
    data: dict = None
    rows: list = None

    def files(self):
        names = (
            ["calibration.json"]
            if self.data is not None
            else ["run.json", "verdicts.jsonl", "probes.json"]
        )
        return {
            name: report.digest(self.folder / name)
            for name in names
            if (self.folder / name).exists()
        }


def load(folder):
    folder = Path(folder).resolve()
    if (folder / "calibration.json").exists():
        data = json.loads((folder / "calibration.json").read_text())
        return Source(folder, data["run"], data=data)
    if not (folder / "run.json").exists() or not (folder / "verdicts.jsonl").exists():
        raise Refused(f"{folder} holds no finished grade.py run")
    run = json.loads((folder / "run.json").read_text())
    if run["kind"] != "universe":
        raise Refused(
            f"{folder.name}: packets cover calibrations and universe grades only"
        )
    rows = [json.loads(line) for line in (folder / "verdicts.jsonl").open()]
    return Source(folder, run, rows=rows)


def _path(name):
    path = Path(name)
    return path if path.is_absolute() else ROOT / path


def _named(run, kind):
    """The input of a kind, as the run recorded it, or None."""
    kinds = run.get("kinds", {})
    return next(
        (
            n
            for n in run["inputs"]
            if report.input_kind(n, kinds) == kind and not n.endswith(CASES_USED)
        ),
        None,
    )


def _check_inputs(source, spec):
    """Every input file the Anthropic run recorded still has the digest it graded; the
    situations, which also depend on the universe, are checked as the mirror reads them."""
    kinds, changed = source.run.get("kinds", {}), []
    for name, recorded in source.run["inputs"].items():
        if report.input_kind(name, kinds) == "situations":
            continue
        path = (
            spec.folder / Path(name).name if name.startswith("evals/") else _path(name)
        )
        if not path.exists() or grade._digest(path) != recorded:
            changed.append(name)
    if changed:
        raise Refused(
            f"{source.folder.name}: {listed(changed)} changed since the Anthropic-side run; "
            "check out the inputs it graded"
        )


def _rules(source, spec):
    """The rules the run graded: its slice's, or the ones its verdict rows hold."""
    if source.data is not None:
        doc = spec.universe if source.run["kind"] == "universe" else spec.skills
        return (
            doc.get("rules" if source.run["kind"] == "universe" else "behaviours") or {}
        )
    named = list(dict.fromkeys(r["rule"] for r in source.rows))
    gone = [r for r in named if r not in spec.universe["rules"]]
    if gone:
        raise Refused(f"{source.folder.name}: {listed(gone)} no longer in the spec")
    return {r: spec.universe["rules"][r] for r in named}


def _used(chosen, rules):
    return [t for t in chosen if any(t in r for r in rules.values())]


def _check(source, rules, judges):
    """Refuse a run this cannot mirror; return whether the decision model filed there, and
    its version."""
    run, name = source.run, source.folder.name
    for tier, model in report.models_of(run["adapters"]):
        if model.split()[0] != adapters.Jev.name and adapters.on_codex(model):
            raise Refused(
                f"{name} is not an Anthropic-side run: its {tier} model {model} runs through "
                "Codex"
            )
    for tier in _used(run["tiers"], rules):
        if tier != "deterministic" and tier not in run["adapters"]:
            off = [n for n in run["notes"] if tier in n and " off" in n]
            why = f" ({off[0]})" if off else ""
            raise Refused(f"{name}: its {tier} tier did not run{why}; rerun it first")
    both = [
        r
        for r, rule in rules.items()
        if "judgment" in rule and set(grade.FILED) & set(rule)
    ]
    if both:
        raise Refused(f"{name}: {listed(both)} has both judgment and a filing check")
    careful = {
        "judgment": run["adapters"]
        .get("judgment", "")
        .removeprefix("judges: ")
        .split(", ")
    }
    jev, version = False, None
    for tier in grade.FILED:
        if tier in run["adapters"]:
            names = run["adapters"][tier].removeprefix("filers: ").split(", ")
            decides = [n for n in names if n.split()[0] == adapters.Jev.name]
            careful[tier] = [n for n in names[:-1] if n not in decides]
            if decides:
                jev, version = True, (decides[0].split(" ", 1)[1:] or [None])[0]
    for tier, models in careful.items():
        if tier in run["adapters"] and len(models) != len(judges):
            raise Refused(
                f"{name}: its {tier} used {len(models)} careful models; give as many "
                "--judge-model"
            )
    return jev, version


def _detail(reason):
    """A decision reason, "noul 0.93" or "choice x, confidence 0.8", as the detail it came from;
    values stay as written, so grade._reason gives back the same reason."""
    return dict(part.split(" ", 1) for part in reason.split(", ")) if reason else {}


def _entry(outcome):
    """A trail entry as grade.write keeps it."""
    return {
        "tier": outcome.tier,
        "verdict": outcome.verdict,
        **grade._reason(outcome),
        **grade._own(outcome),
    }


@dataclass
class Mirror:
    source: Source
    run: grade.Run
    judge: object
    sorted_by: object
    jev: bool  # the decision model's filings were reused
    left_out: bool  # it filed on the Anthropic side, but its filings were not recorded
    used: list = None  # the run's tiers its rules use
    results: list = None
    calibration: dict = None
    probes: bool = False


def _jev_post(filings, version, name):
    """The decision model as a filer, answering each typed choice from where it filed the same
    passage among the same questions on the Anthropic side."""

    def post(body):
        q = body["questions"]["q"]
        questions = tuple(
            q["criteria"][str(n)] for n in range(1, len(q["criteria"]) + 1)
        )
        label = filings.get((questions, body["state"]))
        if label is None:
            raise RuntimeError(f"jev filed nothing for this set in {name}")
        if label == "unsure":
            answer = {"choice": "1", "confidence": 0.0}
        elif label == sort.NONE:
            answer = {"choice": "0", "confidence": 1.0}
        else:
            answer = {"choice": str(questions.index(label) + 1), "confidence": 1.0}
        return {"answers": {"q": answer}, **({"model": version} if version else {})}

    return post


def _filers(chosen, kind, run, rules, judges, light, call, jev, version, name, **extra):
    """grade.sorting's filers, one job at a time, so prompts are recorded in grade.py's order."""
    filings = {}
    sorted_by = grade.sorting(
        _used(chosen, rules), kind, run, list(judges), light, key="reused" if jev else None,
        call=call, post=_jev_post(filings, version, name) if jev else None, **extra,
    )  # fmt: skip
    for check in (sorted_by.sorter, sorted_by.recogniser) if sorted_by else ():
        if check:
            check.workers = 1
    return sorted_by, filings


def _filed_by_jev(filings, placed, sorted_by, name):
    """Fill `filings`, {(questions, passage): label}, from (case, tier, placed) on the Anthropic
    side."""
    for case, tier, by in placed:
        if "jev" not in by:
            continue
        check = sorted_by.sorter if tier == "sort" else sorted_by.recogniser
        passages = check.probes([case])[0]
        if len(passages) != len(by["jev"]):
            raise Refused(f"{name}: {case.ref} files other passages than it did there")
        questions = tuple(sort.question(e) for e in case.context["set"])
        for passage, label in zip(passages, by["jev"], strict=True):
            if filings.setdefault((questions, passage), label) != label:
                raise Refused(f"{name}: jev filed one passage two ways in {case.ref}")


def _judge(source, judges, call):
    if "judgment" not in source.run["adapters"]:
        return None
    return adapters.Judge(
        judges,
        workers=1,
        attempts=1,
        call=lambda prompt, model: call(
            prompt, model, adapters.VERDICTS, adapters.JUDGE_SYSTEM
        ),
    )


def _mirror(source, spec, judges, light, call):
    """grade.py's pipeline for one Anthropic run, with `call` answering the careful and light
    models, and everything else taken from the run."""
    _check_inputs(source, spec)
    rules = _rules(source, spec)
    jev, version = _check(source, rules, judges)
    a = source.run
    run = grade.Run(
        id="", kind=a["kind"], inputs=dict(a["inputs"]), adapters={}, tiers=list(a["tiers"]),
        universe=a.get("universe", ""), kinds=dict(a.get("kinds", {})),
    )  # fmt: skip
    judge = _judge(source, judges, call)
    used = _used(a["tiers"], rules)
    if source.data is not None:
        recorded = all(
            "placed" in e
            for e in source.data["settled"]
            if set(grade.FILED) & set(rules.get(e["rule"], {}))
        )
        mirror = Mirror(
            source, run, judge, None, jev and recorded, jev and not recorded, used
        )
        _calibration(mirror, spec, rules, judges, light, call, version)
    else:
        mirror = Mirror(source, run, judge, None, jev, False, used)
        _universe(mirror, spec, rules, judges, light, call, version)
    return mirror


def _calibration(mirror, spec, rules, judges, light, call, version):
    source, run = mirror.source, mirror.run
    data, name = source.data, source.folder.name
    chosen = tuple(run.tiers)
    cases, labels = grade.example_cases(spec, run.kind)
    if [e["rule"] for e in data["settled"]] != [c.rule_id for c in cases]:
        raise Refused(f"{name}: the examples differ from the ones it calibrated")
    mirror.sorted_by, filings = _filers(
        chosen, "examples", run, rules, judges, light, call, mirror.jev, version, name
    )
    if mirror.jev:
        _filed_by_jev(
            filings,
            [
                (case, e["tier"], e["placed"])
                for case, e in zip(cases, data["settled"], strict=True)
                if e["tier"] in grade.FILED
            ],
            mirror.sorted_by,
            name,
        )
    at = {case.ref: i for i, case in enumerate(cases)}
    reasons = {
        (m["rule"], m["text"], m["label"]): m["reason"]
        for m in data["misses"]
        if m["tier"] == "chain"
    }

    def decide(batch):
        """The chain's decision tier as it ran there: its verdict where it settled the example,
        with the reason it gave where that was a miss."""
        found = []
        for case in batch:
            i = at[case.ref]
            e = data["settled"][i]
            if e["tier"] != "decision":
                found.append(tiers.Outcome("undecided", "decision", {}))
                continue
            reason = reasons.get((case.rule_id, case.text, labels[i]), "")
            found.append(tiers.Outcome(e["verdict"], "decision", _detail(reason)))
        return found

    sorted_by = mirror.sorted_by
    misses, settled = [], []
    table = grade.calibrate(
        spec, run.kind, decide=decide, judge=mirror.judge, only=chosen,
        alone=[t for t in chosen if t != "decision"], misses=misses,
        sorter=sorted_by and sorted_by.sorter, recogniser=sorted_by and sorted_by.recogniser,
        settled=settled,
    )  # fmt: skip

    def spliced(ours, theirs):
        return [
            r
            for tier in (*chosen, "chain")
            for r in (theirs if tier == "decision" else ours)
            if r["tier"] == tier
        ]

    code = [r for r in table if r["tier"] == "deterministic"]
    if code != [r for r in data["table"] if r["tier"] == "deterministic"]:
        raise Refused(
            f"{name}: the deterministic tier no longer scores as it did there"
        )
    for theirs, ours in zip(data["settled"], settled, strict=True):
        if theirs["tier"] in report.SHARED and any(
            theirs[k] != ours[k] for k in ("rule", "verdict", "tier")
        ):
            raise Refused(f"{name}: {theirs['rule']} no longer settles as it did there")
    mirror.calibration = {
        "table": spliced(table, data["table"]),
        "misses": spliced(misses, data["misses"]),
        "settled": settled,
    }


def _universe(mirror, spec, rules, judges, light, call, version):
    source, run = mirror.source, mirror.run
    name, chosen = source.folder.name, tuple(run.tiers)
    universe_doc = yaml.safe_load(_path(_named(source.run, "universe")).read_text())
    guidance = _named(source.run, "guidance")
    guidance_doc = yaml.safe_load(_path(guidance).read_text()) if guidance else None
    cases = grade.universe_cases(spec, universe_doc, guidance_doc, [], list(rules))
    if [(c.rule_id, c.ref, c.text) for c in cases] != [
        (r["rule"], r["ref"], r["text"]) for r in source.rows
    ]:
        raise Refused(f"{name}: the universe gives other cases than it graded")
    situations = None
    if "recognise" in chosen:
        scratch = grade.Run(id="", kind="universe", inputs={}, adapters={})
        answers = _named(source.run, "situations")
        situations = grade.situations_for(
            _path(answers) if answers else None, universe_doc, scratch
        )
        kinds = source.run.get("kinds", {})
        theirs = {
            n: d
            for n, d in source.run["inputs"].items()
            if report.input_kind(n, kinds) == "situations"
        }
        if scratch.inputs != theirs:
            raise Refused(
                f"{name}: the situations changed since the Anthropic-side run"
            )
    every = spec.universe["rules"]
    probes = None
    if "sort" in _used(chosen, every):
        probes = source.folder / "probes.json"
        if not probes.exists():
            raise Refused(f"{name} holds no probes.json to file")
        mirror.probes = True
    mirror.sorted_by, filings = _filers(
        chosen, "universe", run, every, judges, light, call, mirror.jev, version, name,
        probes=probes, scope=grade.scope_of(universe_doc), situations=situations,
    )  # fmt: skip
    prober = mirror.sorted_by and mirror.sorted_by.prober
    if prober:
        missing = [
            c.context.get("id") or c.text
            for c in cases
            if "sort" in c.rule and (c.context.get("id") or c.text) not in prober.known
        ]
        if missing:
            raise Refused(f"{name}: probes.json has no passages for {listed(missing)}")
    if mirror.jev:
        _filed_by_jev(
            filings,
            [
                (case, step["tier"], step.get("placed", {}))
                for case, row in zip(cases, source.rows, strict=True)
                for step in row["trail"]
                if step["tier"] in grade.FILED
            ],
            mirror.sorted_by,
            name,
        )
    decided = {
        (r["rule"], r["ref"]): step
        for r in source.rows
        for step in r["trail"]
        if step["tier"] == "decision"
    }

    def decide(batch):
        """The decision tier's own outcomes there, case by case."""
        found = []
        for case in batch:
            step = decided.get((case.rule_id, case.ref))
            if step is None:
                raise Refused(f"{name}: {case.ref} reaches the decision tier only here")
            found.append(
                tiers.Outcome(step["verdict"], "decision", _detail(step["reason"]))
            )
        return found

    results = tiers.run(cases, decide=decide, judge=mirror.judge, only=chosen)
    grade.settle(results, mirror.sorted_by and mirror.sorted_by.sorter)
    grade.settle(results, mirror.sorted_by and mirror.sorted_by.recogniser, "recognise")
    for result, row in zip(results, source.rows, strict=True):
        ours = [_entry(o) for o in result.trail if o.tier in report.SHARED]
        if ours != [t for t in row["trail"] if t["tier"] in report.SHARED]:
            raise Refused(f"{name}: {row['ref']} no longer settles as it did there")
    mirror.results = results


# Build


class Recorder:
    """The careful and light models at build: keeps each prompt, once per model, in the order
    grade.py sends it, and answers with a blank of the right shape."""

    def __init__(self):
        self.prompts, self.order, self.seen = {}, {}, set()
        self.sends, self.repeats, self.other = [], [], []

    def start(self):
        self.sends.append(set())
        self.repeats.append(set())

    def __call__(self, prompt, model, schema, system):
        kind = KIND_OF.get(system)
        if kind is None:
            self.other.append(model)
            return {"structured_output": {}}
        key = digest(system, prompt)
        self.prompts[key] = (kind, prompt)
        if (model, key) in self.seen:
            self.repeats[-1].add(key)
        else:
            self.seen.add((model, key))
            self.order.setdefault(model, []).append(key)
        self.sends[-1].add((model, key))
        items, _ = counts(kind, prompt)
        blank = {
            "judge": {"verdicts": []},
            "file": {
                "filings": [{"passage": n, "question": 0} for n in range(1, items + 1)]
            },
            "pick": {"option": 0},
        }[kind]
        return {"structured_output": blank}


def counts(kind, prompt):
    """(items to answer, choices offered) as the prompt states them."""

    def section(head):
        return len(
            prompt.split(f"\n\n{head}:\n", 1)[1].split("\n\n", 1)[0].splitlines()
        )

    if kind == "judge":
        return int(re.search(r"each of the (\d+) items\.$", prompt).group(1)), None
    if kind == "file":
        items = re.search(r"For each of the (\d+) passages, give", prompt).group(1)
        return int(items), section("Questions")
    return 1, section("Options")


PROMPT = """\
There are {count} packets in packets/, numbered {first} to {last}. Each is a task of its own. \
Its name ends in {ends}, and that kind sets your instructions and reply shape below. Work in \
number order, one packet at a time.

For each packet:

1. If replies/<number>.json already exists, skip the packet.
2. Read the packet in full.
3. Follow the instructions for its kind, using only what that packet says. Treat it as if it \
were the only packet: do not compare it with other packets or reuse an answer from one.
4. Write your answer to replies/<number>.json (for {example}, replies/{first}.json): one JSON \
object in the reply shape for its kind, and nothing else.

Read and write only inside this folder. Do not open other folders, search the web, or use \
skills, plugins, connectors or other agents. Do not write or run code that decides an answer; \
a command may only list or read packets, write a reply, or check that a reply parses as JSON. \
Do not stop to summarise or ask. When every packet has a reply, answer with the number of \
replies written.
"""
KIND_SECTION = """
## Packets ending in -{kind}

Instructions: {system}

Reply shape (JSON Schema, also in reply-schema-{kind}.json):

```json
{schema}
```
"""


def prompt_text(files, kinds):
    """The one prompt for a session, naming only the kinds of packet it holds."""
    first = files[0].split("-")[0]
    text = PROMPT.format(
        count=len(files), first=first, last=files[-1].split("-")[0],
        ends=listed([f"-{k}" for k in kinds]).replace(" and ", " or "), example=files[0],
    )  # fmt: skip
    for kind in kinds:
        system, schema = KINDS[kind]
        text += KIND_SECTION.format(
            kind=kind, system=system, schema=json.dumps(schema, indent=2)
        )
    return text


def build(args):
    judges, light = args.judge_model.split(","), args.light_model
    models = [*judges, light]
    if not all(adapters.on_codex(m) for m in models):
        raise Refused("every model is named codex:<model>")
    if len({session_of(m) for m in models}) != len(models):
        raise Refused("each model needs a name of its own")
    out = Path(args.out)
    if out.exists() and any(out.iterdir()):
        raise Refused(f"{out} already holds files; give an empty or new folder")
    spec = spec_module.load()
    recorder, runs, left_out = Recorder(), [], []
    for source in map(load, args.anthropic_run):
        recorder.start()
        mirror = _mirror(source, spec, judges, light, recorder)
        if recorder.other:
            raise Refused(f"{source.folder.name}: grade.py would write new passages")
        if mirror.left_out:
            left_out.append(source.folder.name)
        runs.append(
            {
                "from": str(source.folder),
                "kind": "calibration" if source.data is not None else "universe",
                "files": source.files(),
                "inputs": source.run["inputs"],
                "sends": sorted(map(list, recorder.sends[-1])),
                "repeats": len(recorder.repeats[-1]),
            }
        )
    order = recorder.order
    if any(order.get(m, []) != order.get(judges[0], []) for m in judges):
        raise Refused("the careful models would not be asked the same prompts")
    manifest = {
        "schema": SCHEMA,
        "judges": judges,
        "light": light,
        "runs": runs,
        "packets": {},
    }
    first_run = {}  # each packet's runs, by digest
    for n, entry in enumerate(runs):
        for _, key in entry["sends"]:
            if n not in first_run.setdefault(key, []):
                first_run[key].append(n)
    written = []
    for model in models:
        keys = order.get(model, [])
        if not keys:
            continue
        folder = out.resolve() / session_of(model)
        (folder / "packets").mkdir(parents=True)
        (folder / "replies").mkdir()
        files = []
        for n, key in enumerate(keys, 1):
            kind, prompt = recorder.prompts[key]
            number = f"{n:04d}"
            files.append(f"{number}-{kind}.md")
            (folder / "packets" / files[-1]).write_text(prompt, encoding="utf-8")
            items, choices = counts(kind, prompt)
            manifest["packets"][f"{session_of(model)}/{number}"] = {
                "model": model, "kind": kind, "digest": key, "runs": first_run[key],
                "items": items, "choices": choices,
            }  # fmt: skip
        kinds = [k for k in KINDS if any(f.endswith(f"-{k}.md") for f in files)]
        for kind in kinds:
            shape = json.dumps(KINDS[kind][1], indent=2) + "\n"
            (folder / f"reply-schema-{kind}.json").write_text(shape)
        (folder / "PROMPT.md").write_text(prompt_text(files, kinds), encoding="utf-8")
        written.append((model, folder, len(files)))
    out.mkdir(parents=True, exist_ok=True)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    _instructions(written, args, left_out, out.resolve())
    return 0


def _instructions(written, args, left_out, out):
    """What the owner does next; printed here, never written into a session."""
    lines = [
        (
            "Keep these folders outside any repository checkout (move them now if need be), "
            "so the app loads no project instructions, skills or plugins with them."
        ),
        "One Codex desktop session per model; open its folder as the project:",
    ]
    lines += [
        f"  {model}: {folder} ({count} packets); paste {folder / 'PROMPT.md'}"
        for model, folder, count in written
    ]
    lines += [
        (
            "Before starting: pick the model's default reasoning effort (say which with "
            "--effort at apply), and check the app has no global AGENTS.md, skills, plugins "
            "or MCP servers in force."
        ),
        (
            "If a session stops, start a fresh one in the same folder with the same prompt; "
            "it skips packets that have a reply."
        ),
        (
            "Afterwards: check each session's log shows it read and wrote only inside its "
            "own folder. Never open manifest.json in a session."
        ),
        *[
            f"Note: {name} did not record the decision model's filings, so it does not file "
            "in that calibration; rerun the Anthropic calibration with this grade.py to "
            "include it."
            for name in left_out
        ],
        "Then:",
        "  uv run --locked python tools/evals/packet.py apply "
        + " ".join(f"--anthropic-run {Path(f).resolve()}" for f in args.anthropic_run)
        + f" --replies {out} --label openai-side",
    ]
    print("\n".join(lines))


# Apply


class Replay:
    """The careful and light models at apply: each prompt answered from its packet's reply."""

    def __init__(self, answers):
        self.answers, self.used, self.unknown = answers, set(), 0

    def __call__(self, prompt, model, schema, system):
        key = (model, digest(system, prompt))
        self.used.add(key)
        if key not in self.answers:
            self.unknown += 1
            raise Unrecorded(f"no packet holds this prompt for {model}")
        return {"structured_output": self.answers[key]}


def shape_problem(value, schema, at="reply"):
    """Why a value does not fit one of the adapters' reply schemas, or None."""
    kind = schema["type"]
    if kind == "object":
        if not isinstance(value, dict):
            return f"{at} is not an object"
        extra = sorted(set(value) - set(schema["properties"]))
        if extra:
            return f"{at} has an extra key, {extra[0]}"
        missing = [k for k in schema["required"] if k not in value]
        if missing:
            return f"{at} lacks {missing[0]}"
        for key, item in value.items():
            found = shape_problem(item, schema["properties"][key], f"{at}.{key}")
            if found:
                return found
        return None
    if kind == "array":
        if not isinstance(value, list):
            return f"{at} is not a list"
        for n, item in enumerate(value):
            found = shape_problem(item, schema["items"], f"{at}[{n}]")
            if found:
                return found
        return None
    fits = {
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "string": isinstance(value, str),
        "boolean": isinstance(value, bool),
    }[kind]
    if not fits:
        return f"{at} is not {'an' if kind == 'integer' else 'a'} {kind}"
    if "enum" in schema and value not in schema["enum"]:
        return f"{at} is not one of {', '.join(schema['enum'])}"
    return None


def _numbered(noun, said, items):
    problems = [f"{noun} {n} is missing" for n in range(1, items + 1) if n not in said]
    problems += [
        f"{noun} {n} is extra" for n in dict.fromkeys(said) if not 1 <= n <= items
    ]
    problems += [
        f"{noun} {n} is given twice" for n in dict.fromkeys(said) if said.count(n) > 1
    ]
    return problems


def reply_problems(kind, reply, items, choices):
    """Why a reply cannot stand for its packet: off its schema, or its items not the packet's."""
    found = shape_problem(reply, KINDS[kind][1])
    if found:
        return [found]
    if kind == "judge":
        return _numbered("item", [v["item"] for v in reply["verdicts"]], items)
    if kind == "file":
        filings = reply["filings"]
        return _numbered("passage", [f["passage"] for f in filings], items) + [
            f"passage {f['passage']} is filed under question {f['question']}, but there are "
            f"{choices}"
            for f in filings
            if not 0 <= f["question"] <= choices
        ]
    if not 0 <= reply["option"] <= choices:
        return [f"option {reply['option']} is not 0 to {choices}"]
    return []


def read_replies(folder, manifest):
    """{(model, digest): reply} for every packet, or the problems found, packet by packet."""
    answers, problems = {}, []
    for name, entry in manifest["packets"].items():
        session, number = name.split("/")
        at = f"{session}/replies/{number}.json"
        path = folder / session / "replies" / f"{number}.json"
        if not path.exists():
            problems.append(f"{at}: no reply")
            continue
        try:
            reply = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            problems.append(
                f"{at}: not one JSON object alone (no prose or code fences)"
            )
            continue
        found = reply_problems(entry["kind"], reply, entry["items"], entry["choices"])
        problems += [f"{at}: {p}" for p in found]
        answers[(entry["model"], entry["digest"])] = reply
    return answers, problems


def notes(mirror, models, repeats, effort):
    """The Anthropic run's notes, with costs the app does not report and failures that did not
    happen here taken out, then what was reused and how the packets were answered."""
    a = mirror.source.run
    name = a["id"]
    found = []
    for note in a["notes"]:
        head, _, rest = note.partition(": ")
        if head in ("judgment cost", *(f"{w} cost" for w in WHATS)):
            found.append(f"{head}: {NO_COST}")
        elif head in ("decision tokens", *(f"{w} decision tokens" for w in WHATS)):
            if head == "decision tokens" or not mirror.left_out:
                found.append(f"{note}, spent by {name} and reused here")
        elif head.endswith("calls that failed after retries"):
            continue
        elif head in WHATS and rest.startswith("the decision model is unsure"):
            if not mirror.left_out:
                found.append(note)
        else:
            found.append(note)
    filed = [t for t in grade.FILED if t in a["adapters"]]
    if mirror.left_out:
        found.append(
            f"{' and '.join(filed)}: the decision-model filer is left out: {name} did not "
            "record its filings"
        )
    used = mirror.used
    reused = [
        part
        for part, kept in (
            ("the deterministic tier", "deterministic" in used),
            ("the decision tier (Jev)", "decision" in used),
            ("Jev's filings", mirror.jev),
            ("the sort passages (probes.json)", mirror.probes),
        )
        if kept
    ]
    if reused:
        found.append(
            f"reused from {name}, the Anthropic-side run of the same inputs (digests checked): "
            + listed(reused)
        )
    answered = [t for t in ("judgment", *grade.FILED) if t in mirror.run.adapters]
    if answered:
        found.append(
            f"{listed(answered)} answered in the Codex desktop app, one session per model "
            f"({', '.join(models)}), every packet in one prompt rather than one CLI call per "
            "batch; each packet is the prompt grade.py sends, in grade.py's order, and the "
            "instructions grade.py sends as the system prompt are given once at the top of the "
            "session"
        )
    if repeats:
        found.append(
            f"prompts grade.py sends more than once ({repeats}) were asked once and the answer "
            "serves each"
        )
    efforts = [f"{m} {effort[m]}" for m in models if m in effort]
    if efforts:
        found.append(f"reasoning effort set in the app: {', '.join(efforts)}")
    return found


def apply(args):
    folder = Path(args.replies)
    if not (folder / "manifest.json").is_file():
        raise Refused(
            f"{folder} holds no manifest.json; move the whole packets folder, manifest included"
        )
    manifest = json.loads((folder / "manifest.json").read_text())
    if manifest.get("schema") != SCHEMA:
        raise Refused(f"{folder} holds no packets ({SCHEMA})")
    effort = dict(e.split("=", 1) for e in args.effort or [])
    judges, light = manifest["judges"], manifest["light"]
    unknown = sorted(set(effort) - {*judges, light})
    if unknown:
        raise Refused(f"--effort names a model no session used: {listed(unknown)}")
    sources = list(map(load, args.anthropic_run))
    if [str(s.folder) for s in sources] != [r["from"] for r in manifest["runs"]]:
        raise Refused(
            "give the same Anthropic-side runs, in the same order, as at build: "
            + ", ".join(r["from"] for r in manifest["runs"])
        )
    spec = spec_module.load()
    for source, entry in zip(sources, manifest["runs"], strict=True):
        files = source.files()
        changed = [
            n
            for n in {**files, **entry["files"]}
            if files.get(n) != entry["files"].get(n)
        ]
        if changed:
            raise Refused(
                f"{source.folder.name} changed since the packets were built: {listed(changed)}"
            )
        _check_inputs(source, spec)
    answers, problems = read_replies(folder, manifest)
    if problems:
        shown = problems[:40] + (
            [f"... and {len(problems) - 40} more"] if len(problems) > 40 else []
        )
        raise Refused("some replies cannot be used yet:\n" + "\n".join(shown))
    replay, done = Replay(answers), []
    for source, entry in zip(sources, manifest["runs"], strict=True):
        replay.used, replay.unknown = set(), 0
        try:
            mirror = _mirror(source, spec, judges, light, replay)
        except Unrecorded:
            replay.unknown += 1
        asked = {tuple(pair) for pair in entry["sends"]}
        if replay.unknown or replay.used != asked:
            raise Refused(
                f"{source.folder.name}: grade.py now sends a prompt no packet holds; the spec, "
                "the universe or the grader changed since build, so build the packets again"
            )
        done.append((mirror, entry))
    out = args.out or ROOT / ".evidence" / f"{datetime.now(UTC):%Y-%m-%d}" / "evals"
    for mirror, entry in done:
        print(_write(mirror, Path(out), args.label, entry, judges, light, effort, spec))
    print("Add each to evals/runs.yaml with side: openai, then run just evals-report.")
    return 0


def _write(mirror, out, label, entry, judges, light, effort, spec):
    source, run = mirror.source, mirror.run
    stamp = datetime.now(UTC)
    run.id = f"{source.run['id'].rsplit('-', 1)[0]}-{stamp:%Y%m%dT%H%M%S%fZ}"
    run.label = label
    folder = out / run.id
    folder.mkdir(parents=True)
    grade.finish(run, None, mirror.judge, mirror.sorted_by, folder)
    theirs = source.run["adapters"]
    run.adapters = {
        k: theirs[k] if k == "decision" else run.adapters[k]
        for k in theirs
        if k == "decision" or k in run.adapters
    }
    models = [m for m in judges if "judgment" in run.adapters]
    if set(grade.FILED) & set(run.adapters):
        models = [*judges, light]
    run.notes = notes(mirror, models, entry["repeats"], effort)
    if mirror.results is not None:
        if mirror.probes:
            kept = sort.load(source.folder / "probes.json")
            if mirror.sorted_by.prober.known != kept:
                raise Refused(
                    f"{source.folder.name}: the passages filed are not its own"
                )
        grade.write(folder, run, spec, mirror.results)
        if mirror.probes:
            shutil.copyfile(source.folder / "probes.json", folder / "probes.json")
    else:
        data = {"run": asdict(run), **mirror.calibration}
        (folder / "calibration.json").write_text(json.dumps(data, indent=2) + "\n")
        table, misses = mirror.calibration["table"], mirror.calibration["misses"]
        (folder / "report.md").write_text(grade._calibration_report(run, table, misses))
    return folder


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("build", "apply"):
        command = commands.add_parser(name)
        command.add_argument(
            "--anthropic-run",
            action="append",
            required=True,
            help="an Anthropic-side run folder; repeat for each, in the same order at apply",
        )
        if name == "build":
            command.add_argument(
                "--out", required=True, help="a new folder for the packets"
            )
            command.add_argument("--judge-model", default=",".join(JUDGES))
            command.add_argument("--light-model", default=LIGHT)
        else:
            command.add_argument(
                "--replies", required=True, help="the folder build wrote"
            )
            command.add_argument("--label", default="openai-side")
            command.add_argument(
                "--out", type=Path, help="default: .evidence/<date>/evals/"
            )
            command.add_argument(
                "--effort",
                action="append",
                help="MODEL=LEVEL, the reasoning effort picked in the app for a model",
            )
    args = parser.parse_args(argv)
    try:
        return {"build": build, "apply": apply}[args.command](args)
    except Refused as problem:
        print(f"packet.py {args.command}: {problem}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
