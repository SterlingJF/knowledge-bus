"""The sort check: knowledge that answers one member's question is filed under that member.

For each set, every valid probe of every member is filed among the set's questions by each
filer. A member passes when every filer files every one of its probes under it. Filers, the
probe writer and the validity judges are callables supplied by adapters, so this module names
no vendor.

The recognition check reuses the same filing: its probes are everyday situations, its members
are frame values, each situation goes to each filer in a call of its own, and a value passes
when every filer clears the rule's shares (see `recognition`).

Probes come from an example's context.probes, or, for a universe, from a writer: passages that
answer one element's question without using its content words, kept only when every judge says
they answer it. Probes are cached per element and can be saved and reused, so before and after
grades file the same passages.
"""

import json
import math
import re
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from tiers import Outcome, set_key

SCHEMA = "evals-probes/1"
STRENGTH = re.compile(r"^(?:core|situational)(?: when [^:]*)?: ")
STOPWORDS = frozenset(
    {
        "what", "which", "when", "where", "whom", "whose", "does", "this", "that", "these",
        "those", "with", "from", "into", "onto", "each", "every", "have", "been", "were",
        "will", "would", "should", "could", "must", "they", "them", "their", "there",
        "then", "than", "about", "over", "under", "after", "before", "also", "only",
        "more", "most", "other", "some", "such", "your", "ours", "very", "just", "much",
        "many", "being", "here", "upon", "same", "need", "needs",
    }
)  # fmt: skip


def question(entry):
    """A set entry without its strength label: "core: Who?" reads "Who?"."""
    return STRENGTH.sub("", entry, count=1)


def content_words(text):
    """Lowercased words of four or more letters, less common words."""
    return {
        w
        for w in re.findall(r"[a-z]+", text.lower())
        if len(w) >= 4 and w not in STOPWORDS
    }


def _forms(word):
    forms = {word}
    for suffix in ("s", "es", "d", "ed", "ing"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            forms.add(word[: -len(suffix)])
    if word.endswith("ing") and len(word) >= 6:
        forms.add(word[:-3] + "e")
    return forms


def shared_words(passage, asked):
    """The passage's content words that share a form with a content word of the question."""
    theirs = set().union(*(_forms(w) for w in content_words(asked)))
    seen = []
    for word in re.findall(r"[a-z]+", passage.lower()):
        if word in content_words(word) and _forms(word) & theirs and word not in seen:
            seen.append(word)
    return seen


@dataclass(frozen=True)
class Filer:
    """file(questions, passages, ask) -> per passage: a question number from 1, 0 for none,
    or "unsure". Raises when the call fails after its retries."""

    name: str
    file: Callable


def given_probes(cases):
    """Example probes, taken as valid."""
    return [list(c.context.get("probes") or []) for c in cases]


NONE = "none of the questions"


def _label(answer, questions):
    if answer == "unsure":
        return "unsure"
    if isinstance(answer, int) and 1 <= answer <= len(questions):
        return questions[answer - 1]
    return NONE


def _short(text, limit=80):
    return text if len(text) <= limit else text[: limit - 1] + "…"


class Sorter:
    """Files every probe of a set among the set's questions with every filer, then gives each
    member its verdict.

    verdicts(group, members, placed, failed) -> one Outcome per member, where placed holds, per
    member, {filer: [where each of its probes went]}. batch=False files one probe per call."""

    def __init__(
        self,
        filers,
        probes=given_probes,
        workers=4,
        scope="",
        verdicts=None,
        batch=True,
    ):
        self.filers, self.probes, self.workers = list(filers), probes, workers
        self.scope, self._done = scope, {}
        self.verdicts, self.batch = verdicts or _verdicts, batch

    def __call__(self, cases):
        probes = self.probes(cases)
        groups = {}
        for i, case in enumerate(cases):
            groups.setdefault((case.rule_id, set_key(case)), []).append(i)
        outcomes = [None] * len(cases)
        jobs = []
        for (rule_id, key), indexes in groups.items():
            members = [(cases[i].text, tuple(probes[i])) for i in indexes]
            memo = (rule_id, key, json.dumps(members))
            if memo not in self._done:
                jobs.append((memo, [cases[i] for i in indexes], members))
        with ThreadPoolExecutor(self.workers) as pool:
            for memo, verdicts in pool.map(lambda job: self._file(*job), jobs):
                self._done[memo] = verdicts
        for (rule_id, key), indexes in groups.items():
            members = [(cases[i].text, tuple(probes[i])) for i in indexes]
            verdicts = self._done[(rule_id, key, json.dumps(members))]
            for i, outcome in zip(indexes, verdicts, strict=True):
                outcomes[i] = outcome
        return outcomes

    def _file(self, memo, group, members):
        first = group[0]
        questions = [question(e) for e in first.context["set"]]
        passages = [p for _, ps in members for p in ps]
        ask = (first.rule.get("sort") or first.rule["recognise"])["ask"]
        if first.context.get("frame question"):
            ask = f"Question: {first.context['frame question']}\n\n{ask}"
        if self.scope:
            ask = f"{self.scope}\n\n{ask}"
        filed, failed = {}, {}
        for filer in self.filers:
            try:
                answers = (
                    self._answers(filer, questions, passages, ask) if passages else []
                )
                if len(answers) != len(passages):
                    raise RuntimeError(
                        f"{len(answers)} filings for {len(passages)} passages"
                    )
                filed[filer.name] = [_label(a, questions) for a in answers]
            except Exception as error:  # noqa: BLE001 - any failure leaves it undecided
                failed[filer.name] = str(error)
        placed, start = [], 0
        for _, ps in members:
            placed.append(
                {
                    name: labels[start : start + len(ps)]
                    for name, labels in filed.items()
                }
            )
            start += len(ps)
        return memo, self.verdicts(group, members, placed, failed)

    def _answers(self, filer, questions, passages, ask):
        if self.batch:
            return list(filer.file(questions, passages, ask))
        with ThreadPoolExecutor(self.workers) as pool:
            calls = pool.map(lambda p: list(filer.file(questions, [p], ask)), passages)
            return [answer for answers in calls for answer in answers]


def _verdicts(group, members, placed, failed):
    return [
        _verdict(text, ps, filed, failed)
        for (text, ps), filed in zip(members, placed, strict=True)
    ]


def _verdict(text, probes, filed, failed):
    """filed: {filer: [the question each of this member's probes went under]}, kept on the
    outcome as `placed`."""
    if not probes:
        reason = "No valid probe to file."
        return Outcome("undecided", "sort", {"reason": reason, "placed": filed})
    if failed:
        name, error = next(iter(failed.items()))
        reason = f"{name} call failed: {_short(error, 200)}"
        return Outcome("undecided", "sort", {"reason": reason, "placed": filed})
    misfiled, unsure = {}, {}
    for n, probe in enumerate(probes):
        for name, placed in filed.items():
            if placed[n] == "unsure":
                unsure[name] = unsure.get(name, 0) + 1
            elif placed[n] != text:
                misfiled.setdefault(probe, {})[name] = placed[n]
    if not misfiled and unsure:
        said = ", ".join(f"{name} was unsure about {n}" for name, n in unsure.items())
        return Outcome(
            "undecided",
            "sort",
            {
                "reason": f"{said} of {len(probes)} probes; no filer put one elsewhere.",
                "probes": len(probes),
                "placed": filed,
            },
        )
    if not misfiled:
        return Outcome(
            "pass",
            "sort",
            {
                "reason": f"Every filer filed all {len(probes)} probes under this question.",
                "probes": len(probes),
                "placed": filed,
            },
        )
    count = sum(len(v) for v in misfiled.values())
    probe, by = next(iter(misfiled.items()))
    name, where = next(iter(by.items()))
    reason = f'{name} filed "{_short(probe)}" under "{where}"'
    if count > 1:
        reason += f" (and {count - 1} more misfiling{'s' if count > 2 else ''})"
    detail = {"reason": reason, "filings": misfiled, "probes": len(probes)}
    return Outcome("fail", "sort", {**detail, "placed": filed})


def _needed(share, n):
    return math.ceil(share * n - 1e-9)


def recognition(ladder=lambda case: bool(case.context.get("ladder"))):
    """The recognition verdict, for a Sorter: verdicts=recognition(ladder).

    Per filer, a value's situations filed under it must reach the rule's value_share, and the
    set's situations filed rightly its frame_share. Unsure and none are misses, counted apart,
    and on a ladder (ladder(case) is true) a miss one step away is counted apart too. A value
    fails when a filer misses its value share, or misses the frame share having misplaced one of
    this value's situations. With no situations, or a failed call, it is undecided.
    """

    def verdicts(group, members, placed, failed):
        first = group[0]
        block = first.rule["recognise"]
        order = [question(e) for e in first.context["set"]]
        stepped = ladder(first)
        context = first.context
        name = context.get("frame") or context.get("factor") or ""
        if context.get("facet"):
            name = f"{name}.{context['facet']}"
        totals = {}
        for (text, _), filed in zip(members, placed, strict=True):
            for filer, labels in filed.items():
                count = totals.setdefault(
                    filer,
                    {"right": 0, "n": 0, "unsure": 0, "none": 0}
                    | ({"off_by_one": 0} if stepped else {}),
                )
                for label in labels:
                    count["n"] += 1
                    if label == text:
                        count["right"] += 1
                    elif label == "unsure":
                        count["unsure"] += 1
                    elif label == NONE:
                        count["none"] += 1
                    elif stepped and abs(order.index(label) - order.index(text)) == 1:
                        count["off_by_one"] += 1
        outcomes = []
        for case, (text, situations), filed in zip(group, members, placed, strict=True):
            right = {f: sum(label == text for label in ls) for f, ls in filed.items()}
            misses = {}
            for n, situation in enumerate(situations):
                for filer, labels in filed.items():
                    if labels[n] != text:
                        misses.setdefault(situation, {})[filer] = labels[n]
            detail = {
                "set": name,
                "value": case.context.get("id"),
                "situations": len(situations),
                "right": right,
                "filers": totals,
                "misses": misses,
                "placed": filed,
            }
            outcomes.append(
                _recognised(situations, right, totals, misses, failed, block, detail)
            )
        return outcomes

    return verdicts


def _recognised(situations, right, totals, misses, failed, block, detail):
    if failed:
        filer, error = next(iter(failed.items()))
        reason = f"{filer} call failed: {_short(error, 200)}"
        return Outcome("undecided", "recognise", {"reason": reason, **detail})
    if not situations:
        reason = "Not run: no situations for this value."
        return Outcome("undecided", "recognise", {"reason": reason, **detail})
    here = _needed(block["value_share"], len(situations))
    n = next(iter(totals.values()))["n"] if totals else 0
    whole = _needed(block["frame_share"], n)
    short = [
        f"{filer} filed {right[filer]} of {len(situations)} here and {count['right']} of {n} in the set"
        for filer, count in totals.items()
        if right[filer] < here
        or (count["right"] < whole and right[filer] < len(situations))
    ]
    bar = f"{here} of {len(situations)} here and {whole} of {n} in the set"
    if not short:
        return Outcome(
            "pass",
            "recognise",
            {"reason": f"Every filer met the bar: at least {bar}.", **detail},
        )
    situation, by = next(iter(misses.items()))
    filer, where = next(iter(by.items()))
    reason = (
        f"{'; '.join(short)}; the bar is {bar}. "
        f'First miss: {filer} put "{_short(situation)}" under "{where}".'
    )
    return Outcome("fail", "recognise", {"reason": reason, **detail})


class Prober:
    """Writes, filters and validates probes per element, caching them by element id.

    write(question, instruction) -> passages; judges: {name: answers(question, passages) ->
    [bool]}. A passage sharing a content word with the question is dropped and the writer asked
    again, at most `regenerations` more times. A passage stays only when every judge says it
    answers the question.
    """

    def __init__(self, write, judges, known=None, regenerations=2, workers=4):
        self.write, self.judges = write, dict(judges)
        self.known = dict(known or {})
        self.regenerations, self.workers = regenerations, workers
        self.notes, self._lock = [], threading.Lock()

    def __call__(self, cases):
        wanted = {}
        for case in cases:
            key = case.context.get("id") or case.text
            wanted.setdefault(key, (case.text, case.rule["sort"]["write"]))
        missing = []
        for key, (asked, instruction) in wanted.items():
            entry = self.known.get(key)
            if entry is None:
                missing.append((key, asked, instruction))
            elif entry.get("question") != asked:
                note = f"probes for {key} were reused from a file written for a different question"
                if note not in self.notes:
                    self.notes.append(note)
        with ThreadPoolExecutor(self.workers) as pool:
            for key, entry in pool.map(lambda job: self._make(*job), missing):
                with self._lock:
                    self.known[key] = entry
        return [
            list(self.known[case.context.get("id") or case.text].get("probes") or [])
            for case in cases
        ]

    def _make(self, key, asked, instruction):
        entry = {"question": asked, "probes": [], "dropped": []}
        clean, target = [], None
        try:
            for _ in range(1 + self.regenerations):
                written = [p for p in self.write(asked, instruction) if p.strip()]
                target = target or max(len(written), 1)
                for passage in written:
                    shared = shared_words(passage, asked)
                    if shared:
                        why = f"shares {', '.join(shared)} with the question"
                        entry["dropped"].append({"probe": passage, "why": why})
                    elif len(clean) < target:
                        clean.append(passage)
                if len(clean) >= target:
                    break
        except Exception as error:  # noqa: BLE001
            entry["error"] = f"writer: {error}"
            return key, entry
        verdicts = {}
        for name, answers in self.judges.items():
            try:
                verdicts[name] = list(answers(asked, clean)) if clean else []
            except Exception as error:  # noqa: BLE001
                entry["error"] = f"{name}: {error}"
                return key, entry
        for n, passage in enumerate(clean):
            refused = [
                name for name, said in verdicts.items() if said[n : n + 1] != [True]
            ]
            if refused:
                why = "; ".join(
                    f"{name}: does not answer the question" for name in refused
                )
                entry["dropped"].append({"probe": passage, "why": why})
            else:
                entry["probes"].append(passage)
        return key, entry


def save(path, known):
    Path(path).write_text(
        json.dumps({"schema": SCHEMA, "probes": known}, indent=2, ensure_ascii=False)
        + "\n"
    )


def load(path):
    doc = json.loads(Path(path).read_text())
    if doc.get("schema") != SCHEMA:
        raise ValueError(f"{path} is not a probes file ({SCHEMA})")
    return doc["probes"]
