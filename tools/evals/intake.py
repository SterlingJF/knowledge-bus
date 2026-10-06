"""Add real situations for a universe: gate a writer's draft, build the blind labelling packet,
and apply the other side's labels to the shared cases and the universe's answers.

    intake.py gate   UNIVERSE --folder DIR [--draft FILE]
    intake.py packet UNIVERSE --folder DIR [--draft FILE] [--out FILE] [--situations DIR]
    intake.py apply  UNIVERSE --folder DIR [--draft FILE] [--labels FILE] [--universe FILE]
                     [--field NAME] [--situations DIR] [--dry-run]

The working folder sits outside the repository, since it holds the saved sources: draft.yaml
(the written situations; see "Adding situations for a universe" in evals/README.md), sources/
(each source page saved as text, at any depth), packet.md and labels.json. Only `apply` writes
into the repository: the kept cases join evals/situations/cases.yaml and the universe's answers
go to evals/situations/<universe-id>.yaml.

gate: no run of 7 or more words shared with any saved source, no identifying term (a capitalised
word inside a sentence, a digit, money, a month or spelled year, an email or web address), and
no vendor or brand word. Exits 1 on any hit.
packet: each set's value meanings, then its situation texts under opaque ids in a fixed shuffled
order; no written values, tags, near steps, sources or universe wording. A draft may cite a case
already in the pool, from any field, as {case: <id>, value: ...}: it is shown under its own id
and its pool text, and never added again. A written situation whose opaque id is already another
case in the pool is refused, so ids never collide across universes.
apply: keeps a situation only where its label equals the written value, then writes nothing
while the result has any problem, such as a value below its minimum. --dry-run reports only.
A set the draft leaves out keeps its stored answers; a set labelled against other meanings than
the stored ones (a relabel) has its answers replaced; any other set must keep every answer.
The pool's tag meanings and the stored `absent` block are kept as they are; a draft's tags need
only name the same values, unless there is no pool yet: then they give each value its meaning,
as the new pool's tags. A word shared with the universe's wording is reported as a count, so the
wording never shows.
"""

import argparse
import hashlib
import json
import re
import sys
import textwrap
from pathlib import Path

import situations
import spec
import yaml

RUN = 7
# Kept as first used, so a packet already handed out keeps its ids and order.
ID_SALT = "chatgpt-labelling-ids/1|"
ORDER_SALT = "chatgpt-labelling-order/1|"
ALLOW = {"I"}  # capitalised words that identify nobody
NUMBER_WORDS = (
    r"one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|twenty|thirty|forty|fifty"
    r"|sixty|seventy|eighty|ninety|hundred|thousand|million|billion|a few|several|dozen"
)
IDENTIFYING = {
    "a digit (date, year, amount, reference, postcode or address)": re.compile(r"\d"),
    "a currency symbol": re.compile(r"[£$€¥]"),
    "a spelled amount of money": re.compile(
        rf"\b(?:{NUMBER_WORDS})[\w\s-]{{0,20}}?\b(?:pounds?|pence|dollars?|cents?|euros?|quid"
        r"|bucks)\b",
        re.IGNORECASE,
    ),
    "an email address": re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"),
    "a web address": re.compile(
        r"https?://|www\.|\b[\w-]+\.(?:com|org|net|gov|uk|io|edu|info|co|ac|eu|int)\b",
        re.IGNORECASE,
    ),
    "a spelled year": re.compile(
        r"\b(?:nineteen|twenty)[\s-](?:hundred|oh|ten|eleven|twelve|thirteen|fourteen|fifteen"
        r"|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty"
        r"|ninety)\b",
        re.IGNORECASE,
    ),
    "a month name": re.compile(
        r"\b(?:january|february|march|april|june|july|august|september|october|november"
        r"|december)\b",
        re.IGNORECASE,
    ),
}
SHARED = re.compile(r"^(.*): shares (.*) with the wording$")
CASES_HEADER = """\
# Real situations for the recognition check, shared by every universe and stored once each,
# with the field each comes from and its tags. Of the tags, kind says what the work produces,
# and who is the party whose situation or decision it is, not the other side. Each is a
# de-identified paraphrase of one real public case: no names, places, dates or identifiers, and
# no run of 7 words shared with its source; sources and provenance are kept privately outside
# the repository. Each universe's answers sit beside this file in <universe-id>.yaml. Written
# by tools/evals/intake.py apply.
"""
ANSWERS_HEADER = (
    "The {universe} universe's answers for the recognition check: for each set, the value each"
    " shared case in cases.yaml belongs to, labelled against the meanings below. Labelled blind"
    " on both sides; a case is kept only where both agree. Written by tools/evals/intake.py"
    " apply. Changing a meaning, or the universe's values, makes a set's answers stale until"
    " relabelled. The last apply kept {kept} of {total}. Answers per set: {counts}. Status:"
    " development situations, interim."
)
HOW_TO = """# Labelling packet

## How to use

1. Open a fresh chat with a reasoning model that has not seen this work.
2. Paste this whole file as one message. Add nothing to it.
3. Save the reply as `labels.json` beside this packet (the reply is only JSON; a code fence around it is fine).
4. If the reply is cut off, ask for the rest of the JSON and join the pieces before saving.

---

## Instructions for the labeller

Below are groups of short everyday situations. Each group has a set of values, each with a meaning. The meanings are the only definitions you may use. For every situation, choose the one value whose meaning fits it best.

Rules:
- Label each situation on its own, using only its text and the meanings of the values in its own group. Use no outside assumptions about where the situations came from or what they are for.
- Choose exactly one value id from the group the situation is in, copied exactly as written.
- If no value fits well, or two fit equally well, label it "unsure". Never guess: "unsure" is a good answer when it is the honest one.
- Some groups say their values are ordered lowest first and that a case belongs to the highest step that applies to it. Follow that where it appears.
- Label every situation, even if you are unsure of many. Do not skip, merge or reorder them.
- Do not explain. Reply only with JSON in the exact shape given at the very end.
"""
REPLY = """## Reply shape

Reply with only this JSON object, one entry for every situation id above and nothing else (no explanations, no extra keys). Each value is a value id from that situation's own group, or "unsure".

```json
{"labels": {"<situation id>": "<value id or unsure>"}}
```

Example of the shape only (ids and values here are not real): {"labels": {"s-0000000": "valueid", "s-1111111": "unsure"}}
"""


class Refused(Exception):
    """A usage problem: the command does nothing."""


class _Flow(dict):
    """A short mapping written on one line: a case's tags, an answer with its near step."""


class _Dumper(yaml.SafeDumper):
    pass


_Dumper.add_representer(
    _Flow, lambda d, data: d.represent_mapping("tag:yaml.org,2002:map", data, True)
)


def _dump(data):
    return yaml.dump(
        data, Dumper=_Dumper, sort_keys=False, allow_unicode=True, width=100
    )


def opaque(draft_id):
    """The packet's id for a draft situation, which also becomes its case id: it says nothing
    about the written value, the set or the draft's order."""
    return "s-" + hashlib.sha256((ID_SALT + draft_id).encode()).hexdigest()[:7]


def shuffled(listed):
    """A set's situations in a fixed order unrelated to value, source or draft order."""
    return sorted(
        listed,
        key=lambda s: hashlib.sha256((ORDER_SALT + s["id"]).encode()).hexdigest(),
    )


def words(text):
    """Normalised words: lowercase, apostrophes dropped, any other punctuation a word break."""
    return re.findall(r"[a-z0-9]+", re.sub(r"['’‘]", "", str(text).lower()))


def runs(tokens, n=RUN):
    return [" ".join(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]


def capitalised(text):
    """Capitalised words that do not open a sentence and are not on the allowlist."""
    hits = []
    for sentence in re.split(r"(?<=[.!?])[\"')\]]*\s+", text.strip()):
        tokens = re.findall(r"[A-Za-z][A-Za-z'’-]*", sentence)
        hits += [t for t in tokens[1:] if t[0].isupper() and t not in ALLOW]
    return hits


def gate_hits(text, sources):
    """Each way a written situation could identify its source or anyone in it."""
    hits = []
    mine = runs(words(text))
    for name, theirs in sources.items():
        shared = [r for r in mine if r in theirs]
        if shared:
            more = f" (+{len(shared) - 1} more)" if len(shared) > 1 else ""
            hits.append(f"shares a {RUN}-word run with {name}: {shared[0]!r}{more}")
    hits += [f"capitalised word: {token}" for token in capitalised(text)]
    for what, pattern in IDENTIFYING.items():
        match = pattern.search(text)
        if match:
            hits.append(f"{what}: {match.group(0)!r}")
    for pattern in (spec.VENDORS, situations.BRANDS):
        match = pattern.search(text)
        if match:
            hits.append(f"vendor or brand word: {match.group(0)}")
    return hits


def _outside(path, what):
    path = Path(path).resolve()
    if path.is_relative_to(spec.ROOT.resolve()):
        raise Refused(f"{what} must be outside the repository: {path}")
    return path


def _draft(args):
    path = Path(args.draft or Path(args.folder) / "draft.yaml")
    if not path.exists():
        raise Refused(f"no draft at {path}")
    draft = spec.read(path) or {}
    if draft.get("universe") != args.universe_id:
        raise Refused(
            f"{path.name} is for {draft.get('universe')}, not {args.universe_id}"
        )
    seen = {}
    for _, key, block in _blocks(draft):
        if not isinstance(block.get("means"), dict):
            raise Refused(f"{key}: needs means, each value's meaning")
        ladder = block.get("ladder")
        if isinstance(ladder, list) and ladder != list(block.get("means") or {}):
            raise Refused(f"{key}: ladder must list the meanings' values, lowest first")
        for s in block.get("situations") or []:
            ident = s.get("case") or opaque(str(s.get("id")))
            if ident in seen:
                raise Refused(f"{s.get('id')} and {seen[ident]} share the id {ident}")
            seen[ident] = s.get("id") or ident
    return draft


def _pool(folder):
    """The shared pool in a situations folder, or an empty one."""
    path = Path(folder) / situations.POOL
    return spec.read(path) if path.exists() else {"cases": []}


def _resolved(block, known):
    """A set's situations, each with its packet id: a written one under its opaque id, a cited
    pool case under its own id, with its text from the pool."""
    listed = []
    for s in block.get("situations") or []:
        if "case" not in s:
            listed.append({**s, "ident": opaque(str(s.get("id")))})
            continue
        case = known.get(s["case"])
        if case is None:
            raise Refused(f"{s['case']}: no such case in {situations.POOL}")
        listed.append({**s, "id": s["case"], "ident": s["case"], "text": case["text"]})
    return listed


def _blocks(draft):
    for section in situations.SECTIONS:
        for key, block in (draft.get(section) or {}).items():
            yield section, key, block or {}


def gate(args):
    folder = _outside(args.folder, "the working folder")
    draft = _draft(args)
    files = sorted(p for p in (folder / "sources").rglob("*") if p.is_file())
    if not files:
        raise Refused(f"no saved source texts under {folder / 'sources'}")
    sources = {
        str(p.relative_to(folder / "sources")): set(
            runs(words(p.read_text(errors="replace")))
        )
        for p in files
    }
    checked = flagged = total = 0
    for _, _, block in _blocks(draft):
        for s in block.get("situations") or []:
            if "case" in s:
                continue  # already in the pool, gated when it was written
            hits = gate_hits(str(s.get("text") or ""), sources)
            checked, flagged, total = (
                checked + 1,
                flagged + bool(hits),
                total + len(hits),
            )
            for hit in hits:
                print(f"{s.get('id')}: {hit}")
    noun = "source" if len(sources) == 1 else "sources"
    print(
        f"{checked} situations checked against {len(sources)} saved {noun}; "
        f"{total} hits in {flagged} situations"
    )
    return 1 if total else 0


def packet(args):
    folder = _outside(args.folder, "the working folder")
    out = _outside(args.out or folder / "packet.md", "the packet")
    draft = _draft(args)
    known = {c.get("id"): c for c in _pool(args.situations).get("cases") or []}
    lines, n = [HOW_TO], 0
    for _, key, block in _blocks(draft):
        listed = _resolved(block, known)
        for s in listed:
            text = " ".join(str(s.get("text")).split())
            if (
                "case" not in s
                and s["ident"] in known
                and known[s["ident"]]["text"] != text
            ):
                raise Refused(
                    f"{s['id']} becomes {s['ident']}, already another case in "
                    f"{situations.POOL}: give it a new id, led by the universe id"
                )
        lines.append(f"## Group: {key}\n")
        if block.get("ladder"):
            lines.append(
                "The values are ordered lowest first. "
                "A case belongs to the highest step that applies to it.\n"
            )
        lines.append('Values (choose exactly one id, or "unsure"):\n')
        lines += [f"- `{value}`: {means}" for value, means in block["means"].items()]
        lines += ["", f"Situations in group {key}:\n"]
        for s in shuffled(listed):
            lines.append(f"- `{s['ident']}`: {' '.join(str(s['text']).split())}")
            n += 1
        lines.append("")
    lines.append(REPLY)
    out.write_text("\n".join(lines))
    print(f"wrote {out}: {n} situations")
    return 0


def read_labels(path):
    """{opaque id: label} from the saved reply, with or without a fence or prose around it."""
    if not Path(path).exists():
        raise Refused(f"no labels at {path}: save the other side's reply there")
    raw = Path(path).read_text()
    start, end = raw.find("{"), raw.rfind("}")
    try:
        labels = json.loads(raw[start : end + 1]).get("labels") if start >= 0 else None
    except (json.JSONDecodeError, AttributeError) as error:
        raise Refused(f"{path}: not a JSON object ({error})") from error
    if not isinstance(labels, dict):
        raise Refused(
            f'{path}: needs {{"labels": {{"<situation id>": "<value or unsure>"}}}}'
        )
    return {str(k): str(v).strip() for k, v in labels.items()}


def _status(s, label, values):
    if label is None:
        return "missing"
    if label.lower() == "unsure":
        return "unsure"
    if label not in values:
        return "invalid"
    return "agree" if label == s.get("value") else "disagree"


def _report(rows):
    print("Agreement per set (the label equals the written value)")
    agreed = total = 0
    for key, listed in rows.items():
        n, a = len(listed), sum(st == "agree" for _, st, _ in listed)
        rest = ("disagree", "unsure", "invalid", "missing")
        counts = [(sum(st == x for _, st, _ in listed), x) for x in rest]
        extra = "; " + ", ".join(f"{c} {x}" for c, x in counts if c) if a < n else ""
        print(f"  {key}: {a}/{n} agree ({a / n:.1%}){extra}")
        agreed, total = agreed + a, total + n
    print(f"  TOTAL: {agreed}/{total} agree ({agreed / max(total, 1):.1%})")
    print("\nEvery situation not kept")
    dropped = [
        (k, s, st, lb) for k, ls in rows.items() for s, st, lb in ls if st != "agree"
    ]
    for key, s, status, label in dropped:
        near = f", near {s['near']}" if s.get("near") else ""
        print(
            f"  [{key}] {s['id']}: written {s.get('value')}{near}; "
            f"label {label or '(none)'} ({status})"
        )
        print(f"      {' '.join(str(s.get('text')).split())}")
    if not dropped:
        print("  none")


def apply(args):
    folder = _outside(args.folder, "the working folder")
    draft = _draft(args)
    universe_path = args.universe or (
        spec.ROOT / "universes" / args.universe_id / "universe.kbp.yaml"
    )
    if not Path(universe_path).exists():
        raise Refused(f"no universe file at {universe_path}; pass --universe")
    universe = spec.read(universe_path)
    labels = read_labels(args.labels or folder / "labels.json")
    field = args.field or draft.get("field") or args.universe_id
    tags = draft.get("tags") or {}
    out = Path(args.situations)
    pool_path = out / situations.POOL
    pool = (
        spec.read(pool_path)
        if pool_path.exists()
        else {"schema": situations.CASES_SCHEMA, "tags": tags, "cases": []}
    )
    if not pool_path.exists() and situations.case_problems(pool):
        raise Refused(
            "a new pool needs a meaning for each tag value in the draft's tags"
        )
    known = {c.get("id"): c for c in pool.get("cases") or []}

    rows, answers = {}, {"schema": situations.SCHEMA, "universe": args.universe_id}
    answers["field"] = field
    new, used = [], set()
    for section, key, block in _blocks(draft):
        rows[key], kept = [], {}
        for s in _resolved(block, known):
            ident = s["ident"]
            used.add(ident)
            label = labels.get(ident)
            status = _status(s, label, list(block["means"]))
            rows[key].append((s, status, label))
            if status != "agree":
                continue
            near = s.get("near")
            kept[ident] = _Flow(value=s["value"], near=near) if near else s["value"]
            if "case" in s:
                continue  # a cited case is in the pool already
            new.append(
                {"id": ident, "text": " ".join(str(s["text"]).split()), "field": field}
                | {"tags": _Flow((t, s.get(t)) for t in tags)}
            )
        answers.setdefault(section, {})[key] = situations.answer_set(
            key, block["means"], kept, ladder=bool(block.get("ladder"))
        )
    _report(rows)

    refuse = []
    missing = sum(st == "missing" for listed in rows.values() for _, st, _ in listed)
    if missing:
        refuse.append(f"{missing} situation(s) have no label")
    stray = sorted(set(labels) - used)
    if stray:
        print(f"\nLabels matching no situation ({len(stray)}): {', '.join(stray[:10])}")

    if _tag_values(pool.get("tags")) != _tag_values(tags):
        refuse.append("the draft's tags differ from the pool's")
    added = []
    for case in new:
        if case["id"] not in known:
            added.append(case)
        elif known[case["id"]] != case:
            refuse.append(
                f"case {case['id']} is already in the pool with other content"
            )
    answers_path = out / f"{args.universe_id}.yaml"
    stored = spec.read(answers_path) if answers_path.exists() else {}
    answers, lost, relabelled = _merged(answers, stored)
    if relabelled:
        print(
            f"\nRelabelled, so their stored answers are replaced: {', '.join(relabelled)}"
        )
    if lost:
        refuse.append(
            f"would drop {len(lost)} answer(s) already in {answers_path.name}"
        )

    grown = {**pool, "cases": [*(pool.get("cases") or []), *added]}
    found = situations.case_problems(grown) + situations.problems(
        answers, universe, grown
    )
    found = [_masked(p) for p in found]
    print(f"\nProblems in what would be written: {len(found)}")
    for problem in found:
        print(f"  {problem}")
    if found:
        refuse.append(
            f"{len(found)} problem(s); fix them with more real cases, never invented"
        )

    kept_n = sum(st == "agree" for listed in rows.values() for _, st, _ in listed)
    total = sum(len(listed) for listed in rows.values())
    sets_n = sum(len(answers.get(s) or {}) for s in situations.SECTIONS)
    if refuse:
        print("\nREFUSED, nothing written:")
        for reason in refuse:
            print(f"  - {reason}")
        return 1
    if args.dry_run:
        print(
            f"\nDRY RUN: would write {len(added)} cases and {sets_n} sets; nothing written."
        )
        return 0
    counts = "; ".join(
        f"{key} {len(block.get('answers') or {})}"
        for section in situations.SECTIONS
        for key, block in (answers.get(section) or {}).items()
    )
    said = ANSWERS_HEADER.format(
        universe=args.universe_id, kept=kept_n, total=total, counts=counts
    )
    header = "".join(f"# {line}\n" for line in textwrap.wrap(said, 96))
    out.mkdir(parents=True, exist_ok=True)
    if pool_path.exists():
        text = pool_path.read_text()
        text = (
            text
            + ("" if text.endswith("\n") else "\n")
            + (_dump(added) if added else "")
        )
        if yaml.safe_load(text).get("cases") != grown["cases"]:
            raise Refused(f"cannot add to {pool_path}: its cases list must come last")
    else:
        text = CASES_HEADER + _dump({**pool, "tags": tags, "cases": added})
    pool_path.write_text(text)
    answers_path.write_text(header + _dump(answers))
    print(f"\nWrote {len(added)} new cases to {pool_path} and {answers_path}")
    return 0


def _merged(answers, stored):
    """(answers, lost, relabelled): the draft's sets over the stored ones. A stored set the
    draft leaves out is kept. A set labelled against other meanings than the stored ones is
    relabelled, so its answers are replaced. Any other set must keep every stored answer; the
    ones it would drop are `lost`. A stored `absent` block is kept as it is."""
    merged = {k: answers[k] for k in ("schema", "universe", "field")}
    if stored.get("absent"):
        merged["absent"] = stored["absent"]
    lost, relabelled = set(), []
    for section in situations.SECTIONS:
        drafted, before = answers.get(section) or {}, stored.get(section) or {}
        for key, block in drafted.items():
            old = before.get(key) or {}
            if not old:
                continue
            if old.get("fingerprint") != block["fingerprint"]:
                relabelled.append(key)
            else:
                lost |= _answers(key, old) - _answers(key, block)
        if before or drafted:
            kept = {key: _flowed(block) for key, block in before.items()}
            merged[section] = {**kept, **drafted}
    return merged, lost, relabelled


def _flowed(block):
    """A stored set as apply writes it, so a set the draft leaves out is written back
    unchanged: each answer with its near step on one line."""
    answers = (block or {}).get("answers") or {}
    flowed = {k: _Flow(a) if isinstance(a, dict) else a for k, a in answers.items()}
    return {**block, "answers": flowed} if answers else block


def _tag_values(tags):
    """{tag: [value ids]}, whether the values are listed alone or with their meanings."""
    return {tag: list(values or []) for tag, values in (tags or {}).items()}


def _answers(key, block):
    """{(set, case id, value, near)} for every answer in one set."""
    return {
        (key, ident, *situations.answer_of(entry))
        for ident, entry in ((block or {}).get("answers") or {}).items()
    }


def _masked(problem):
    match = SHARED.match(problem)
    if not match:
        return problem
    return f"{match.group(1)}: shares {len(match.group(2).split(', '))} word(s) with the wording"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("gate", "packet", "apply"):
        command = commands.add_parser(name)
        command.add_argument("universe_id", metavar="UNIVERSE")
        command.add_argument("--folder", required=True, help="the working folder")
        command.add_argument("--draft", help="default: <folder>/draft.yaml")
        if name == "packet":
            command.add_argument("--out", help="default: <folder>/packet.md")
            command.add_argument("--situations", default=str(situations.FOLDER))
        if name == "apply":
            command.add_argument("--labels", help="default: <folder>/labels.json")
            command.add_argument(
                "--universe", help="default: the repository's universe file"
            )
            command.add_argument(
                "--field", help="the cases' field (default: the universe id)"
            )
            command.add_argument("--situations", default=str(situations.FOLDER))
            command.add_argument("--dry-run", action="store_true", help="report only")
    args = parser.parse_args(argv)
    try:
        return {"gate": gate, "packet": packet, "apply": apply}[args.command](args)
    except Refused as problem:
        print(f"intake.py {args.command}: {problem}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
