"""Real, de-identified situations for the recognition check: cases shared by every universe,
and each universe's answers over them.

evals/situations/cases.yaml declares the tags, each value with its meaning, and holds each case
once: its id, its text, the field it comes from and its tags. evals/situations/<universe-id>.yaml
holds one universe's answers: for each frame (or <frame>.<facet>) and factor, the meaning of
each value the labels were made against, `ladder: true` when the values are steps (lowest
first), the fingerprint of that definition, and each case's value, as `value` or, for a ladder
case close to a neighbouring step, {value, near}. Its `absent` names the tag values its field
cannot offer, {<tag>: {<value>: {reason, source}}}, with a public source for each.

A fingerprint covers the set's id, its value ids in order and their meanings. Rewording a
question keeps the answers, since the wording is what recognition tests; adding, removing or
reordering a value makes them stale until they are relabelled. A universe holds no meanings,
so a value is redefined by editing its meaning in that set's `means` in each answers file: the
fingerprint then fails, and the set is stale until relabelled.

`case_problems` checks the pool: a meaning for each tag value, known fields and tags, unique ids
and texts, no vendor, product or identifier. `problems` checks one universe's answers against
the pool and the universe: real sets and values, nothing stale, at least four cases from the
universe's own field per value and twelve per set, every tag value not declared absent covered
twice per set, both sides of each ladder step, and no case sharing a word with the wording it
is filed under. Run for every universe, that last check covers each universe that uses a case.
`folder_problems` runs both over a folder.
"""

import hashlib
import json
import re
from itertools import pairwise
from pathlib import Path

import spec
from sort import shared_words

SCHEMA = "evals-answers/1"
CASES_SCHEMA = "evals-cases/1"
FOLDER = spec.EVALS / "situations"
POOL = "cases.yaml"
PER_VALUE, PER_SET, PER_TAG = 4, 12, 2
# A set of fewer values, such as a factor-only universe's placeholder ordering frame, offers a
# reader no choice, so recognition has nothing to test there.
CHOICES = 2
SECTIONS = {"frames": "frame", "factors": "factor"}
SET_FIELDS = {"ladder", "fingerprint", "means", "answers"}
CASE_FIELDS = {"id", "text", "field", "tags"}
ABSENT_FIELDS = ("reason", "source")
BRANDS = re.compile(
    r"\b(github|gitlab|sqlite|postgres|mysql|jira|trello|figma|salesforce|whatsapp|facebook"
    r"|instagram|linkedin|youtube|tiktok|google|microsoft|iphone|paypal|airbnb)\b",
    re.IGNORECASE,
)


def human(value):
    """A value id as the explorer shows it: across-sessions reads Across sessions."""
    text = str(value).replace("-", " ")
    return text[:1].upper() + text[1:]


def value_sets(node):
    """[(facet or None, [(value id, the value as the explorer shows it)])] for a frame's or a
    factor's values (one set) or facets (one set each): Approve: Does someone's yes come first?"""
    groups = node.items() if isinstance(node, dict) else [(None, node)]
    found = []
    for facet, listed in groups:
        shown = []
        for value in listed or []:
            ident = value.get("id") if isinstance(value, dict) else value
            asked = value.get("question") if isinstance(value, dict) else None
            shown.append((ident, f"{human(ident)}: {asked}" if asked else human(ident)))
        if shown:
            found.append((facet, shown))
    return found


def sets(universe_doc):
    """{(section, key): (value ids, the wording a reader sees)} for each frame, facet and factor
    with at least CHOICES values."""
    found = {}
    for section in SECTIONS:
        for dimension in universe_doc.get(section) or []:
            if not isinstance(dimension, dict):
                continue
            node = dimension.get("facets") or dimension.get("values")
            for facet, shown in value_sets(node):
                if len(shown) < CHOICES:
                    continue
                key = f"{dimension['id']}.{facet}" if facet else str(dimension["id"])
                words = [dimension.get("question") or "", *(t for _, t in shown)]
                found[(section, key)] = ([i for i, _ in shown], " ".join(words))
    return found


def fingerprint(key, means):
    """What fixes a set's right answers: its id, its value ids in order and their meanings."""
    data = [key, list((means or {}).items())]
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(text.encode()).hexdigest()[:16]


def answer_set(key, means, answers, ladder=False):
    """A set's block in an answers file, fingerprinted against the meanings it was labelled on."""
    return ({"ladder": True} if ladder else {}) | {
        "fingerprint": fingerprint(key, means),
        "means": dict(means),
        "answers": dict(answers),
    }


def answer_of(entry):
    """(value, near) of one answer: a value id, or {value, near} for a case near a step."""
    if isinstance(entry, dict):
        return entry.get("value"), entry.get("near")
    return entry, None


def stale(key, block, values):
    """Why a set's answers no longer hold for the universe's values, or None."""
    labelled = list(block.get("means") or {})
    if labelled != values:
        return (
            f"{key}: stale answers: labelled against {', '.join(labelled) or 'nothing'}; "
            f"the universe now has {', '.join(values)}; relabel"
        )
    if not block.get("fingerprint"):
        return f"{key}: needs fingerprint"
    if block["fingerprint"] != fingerprint(key, block["means"]):
        return (
            f"{key}: stale answers: a value's meaning changed since labelling; relabel"
        )
    return None


def stale_sets(doc, universe_doc):
    """{key: why} for each of the universe's sets whose answers are stale."""
    known = sets(universe_doc)
    found = {}
    for section in SECTIONS:
        for key, block in (doc.get(section) or {}).items():
            if (section, key) in known:
                why = stale(key, block or {}, known[(section, key)][0])
                if why:
                    found[key] = why
    return found


class Situations:
    """Each value's situations, as a Sorter's probe source; empty without answers. Sets named
    in `stale` give none, so their values read not run."""

    def __init__(self, answers, cases, stale=()):
        self.answers = answers or {}
        self.texts = {
            c.get("id"): c.get("text") for c in (cases or {}).get("cases") or []
        }
        self.stale = set(stale)

    def _set(self, case):
        context = case.context
        section = "factors" if "factor" in context else "frames"
        key = str(context.get("factor") or context.get("frame"))
        if context.get("facet"):
            key = f"{key}.{context['facet']}"
        if key in self.stale:
            return {}
        return (self.answers.get(section) or {}).get(key) or {}

    def __call__(self, cases):
        return [
            [
                self.texts[ident]
                for ident, entry in (self._set(case).get("answers") or {}).items()
                if answer_of(entry)[0] == case.context.get("id") and ident in self.texts
            ]
            for case in cases
        ]

    def ladder(self, case):
        return bool(self._set(case).get("ladder"))


def _plural(n):
    return f"{n} situation{'' if n == 1 else 's'}"


def case_problems(doc):
    """Problems in the shared pool of cases."""
    found = (
        [] if doc.get("schema") == CASES_SCHEMA else [f"needs schema: {CASES_SCHEMA}"]
    )
    tags = doc.get("tags") or {}
    for tag, options in tags.items():
        if not isinstance(options, dict):
            found.append(f"tags: {tag}: needs a meaning for each value")
            continue
        found += [
            f"tags: {tag} {value}: needs a meaning"
            for value, means in options.items()
            if not str(means or "").strip()
        ]
    listed = doc.get("cases") or []
    for case in listed:
        at = case.get("id")
        found += [f"{at}: unknown field {f}" for f in sorted(set(case) - CASE_FIELDS)]
        found += [
            f"{at}: needs {f}" for f in ("id", "text", "field") if not case.get(f)
        ]
        given = case.get("tags") or {}
        found += [f"{at}: unknown tag {t}" for t in sorted(set(given) - set(tags))]
        for tag, options in tags.items():
            if not given.get(tag):
                found.append(f"{at}: needs tag {tag}")
            elif given[tag] not in options:
                found.append(f"{at}: {tag} must be one of {', '.join(options)}")
        text = str(case.get("text") or "")
        named = spec.VENDORS.search(text) or BRANDS.search(text)
        if named:
            found.append(f"{at}: names a vendor or product: {named.group(0)}")
        found += [
            f"{at}: holds {what}"
            for what, pattern in spec.IDENTIFIERS.items()
            if pattern.search(text)
        ]
    seen, texts = set(), {}
    for case in listed:
        if case.get("id") in seen:
            found.append(f"duplicate case id {case.get('id')}")
            continue
        seen.add(case.get("id"))
        text = " ".join(str(case.get("text") or "").lower().split())
        if text in texts:
            found.append(f"{case.get('id')}: same text as {texts[text]}")
        texts.setdefault(text, case.get("id"))
    return found


def problems(doc, universe_doc, cases_doc):
    """Problems in one universe's answers, against the shared pool and the universe."""
    found = [] if doc.get("schema") == SCHEMA else [f"needs schema: {SCHEMA}"]
    universe_id = (universe_doc.get("universe") or {}).get("id")
    if doc.get("universe") != universe_id:
        found.append(f"names universe {doc.get('universe')}, not {universe_id}")
    if not doc.get("field"):
        found.append("needs field: the field the universe's own cases come from")
    pool = {c.get("id"): c for c in (cases_doc or {}).get("cases") or []}
    tags = (cases_doc or {}).get("tags") or {}
    absent = doc.get("absent") or {}
    found += _absent(absent, tags)
    # a value the field cannot offer needs no cases; every other minimum stands
    wanted = {
        tag: [v for v in options if v not in (absent.get(tag) or {})]
        for tag, options in tags.items()
    }
    known = sets(universe_doc)
    for section in SECTIONS:
        for key, block in (doc.get(section) or {}).items():
            if (section, key) not in known:
                found.append(f"{key}: not a frame, facet or factor of the universe")
                continue
            values, wording = known[(section, key)]
            found += _set(
                key, block or {}, values, wording, pool, wanted, doc.get("field")
            )
    for section, key in known:
        if key not in (doc.get(section) or {}):
            found.append(f"{key}: has no situations")
    return found


def _absent(absent, tags):
    """Problems in the tag values declared absent: each a known tag and value, with a reason
    and the public source that supports it."""
    found = []
    for tag, listed in absent.items():
        if tag not in tags:
            found.append(f"absent: unknown tag {tag}")
            continue
        for value, entry in (listed or {}).items():
            at = f"absent: {tag} {value}"
            if value not in tags[tag]:
                found.append(f"{at}: not a value of {tag}")
                continue
            entry = entry if isinstance(entry, dict) else {}
            found += [
                f"{at}: unknown field {f}"
                for f in sorted(set(entry) - set(ABSENT_FIELDS))
            ]
            found += [
                f"{at}: needs {f}"
                for f in ABSENT_FIELDS
                if not str(entry.get(f) or "").strip()
            ]
    return found


def _set(key, block, values, wording, pool, tags, field):
    found = [f"{key}: unknown field {f}" for f in sorted(set(block) - SET_FIELDS)]
    if block.get("ladder") not in (None, True, False):
        found.append(f"{key}: ladder must be true or false")
    why = stale(key, block, values)
    if why:
        return [*found, why]
    stepped = bool(block.get("ladder"))
    own = []
    for ident, entry in (block.get("answers") or {}).items():
        at = f"{key}/{ident}"
        value, near = answer_of(entry)
        if isinstance(entry, dict):
            found += [
                f"{at}: unknown field {f}"
                for f in sorted(set(entry) - {"value", "near"})
            ]
        if ident not in pool:
            found.append(f"{at}: no such case in the pool")
            continue
        if value not in values:
            found.append(f"{at}: {value} is not a value of {key}")
            continue
        if near is not None:
            step = values.index(value)
            neighbours = values[max(step - 1, 0) : step] + values[step + 1 : step + 2]
            if not stepped or near not in neighbours:
                found.append(
                    f"{at}: near is only for a ladder, naming a neighbouring step"
                )
                near = None
        shared = shared_words(str(pool[ident].get("text") or ""), wording)
        if shared:
            found.append(f"{at}: shares {', '.join(shared)} with the wording")
        if pool[ident].get("field") == field:
            own.append((value, near, pool[ident].get("tags") or {}))
    for value in values:
        n = sum(v == value for v, _, _ in own)
        if n < PER_VALUE:
            found.append(
                f"{key}: {value} has {_plural(n)} from {field}; needs at least {PER_VALUE}"
            )
    if len(own) < PER_SET:
        found.append(
            f"{key}: has {_plural(len(own))} from {field}; needs at least {PER_SET}"
        )
    if stepped:
        for low, high in pairwise(values):
            for value, near in ((low, high), (high, low)):
                if (value, near) not in {(v, n) for v, n, _ in own}:
                    found.append(f"{key}: needs a {value} situation near {near}")
    for tag, options in tags.items():
        for option in options:
            n = sum(given.get(tag) == option for _, _, given in own)
            if n < PER_TAG:
                found.append(
                    f"{key}: {tag} {option} has {_plural(n)} from {field}; "
                    f"needs at least {PER_TAG}"
                )
    return found


def _repo_universe(universe_id):
    path = spec.ROOT / "universes" / str(universe_id) / "universe.kbp.yaml"
    return spec.read(path) if path.exists() else None


def folder_problems(folder=FOLDER, universe_for=_repo_universe):
    """Every problem in a situations folder, each led by its file name: the pool, then each
    universe's answers against the pool and the universe's current definition."""
    folder = Path(folder)
    named = sorted(p for p in folder.glob("*.yaml") if p.name != POOL)
    if not (folder / POOL).exists():
        return [f"{POOL}: missing, though {named[0].name} needs it"] if named else []
    cases = spec.read(folder / POOL) or {}
    found = [f"{POOL}: {p}" for p in case_problems(cases)]
    for path in named:
        doc = spec.read(path) or {}
        universe_id = doc.get("universe")
        if path.stem != universe_id:
            found.append(f"{path.name}: names universe {universe_id}; rename it")
        universe = universe_for(universe_id)
        if universe is None:
            found.append(f"{path.name}: no universe file for {universe_id}")
            continue
        found += [f"{path.name}: {p}" for p in problems(doc, universe, cases)]
    return found
