"""Run each rule's tiers on its cases: deterministic in code, then decision, then judgment.

The first tier that returns pass or fail settles a case. A case still undecided after the last
tier goes to the owner. Decision and judgment are callables supplied by adapters, so this module
names no vendor.
"""

import fnmatch
import json
import re
from dataclasses import dataclass, field

TIERS = ("deterministic", "decision", "judgment")
PER_ITEM = ("id", "strength", "set", "probes", "artifact")
# context the decision tier never sees
JUDGES_ONLY = ("owner turn before", "owner turn after")
WORD = re.compile(r"[\w'’-]+")
EDGE = r"[\w'’-]"


@dataclass(frozen=True)
class Case:
    rule_id: str
    rule: dict
    subject: str
    ref: str
    text: str
    context: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Outcome:
    verdict: str  # pass | fail | undecided
    tier: str
    detail: dict = field(default_factory=dict)


@dataclass
class Result:
    case: Case
    trail: list = field(default_factory=list)
    final: Outcome = None


def set_key(case):
    """The set a case belongs to, with what its members share; empty for item and pair cases."""
    if "set" not in case.context:
        return ""
    shared = {k: v for k, v in case.context.items() if k not in PER_ITEM}
    return json.dumps([case.context["set"], shared], sort_keys=True)


def words(text):
    """Runs of letters, digits, apostrophes and hyphens that contain a letter or digit."""
    return [w for w in WORD.findall(text) if re.search(r"[^\W_]", w)]


def _fires(check, text):
    if "words" in check:
        count, bounds = len(words(text)), check["words"]
        if count > bounds.get("max", count) or count < bounds.get("min", count):
            return {"count": count}
    elif "pattern" in check:
        match = re.search(
            check["pattern"], text, re.IGNORECASE if check.get("ignore_case") else 0
        )
        if match:
            return {"match": match.group(0)}
    elif "terms" in check:
        for term in check["terms"]:
            if re.search(
                f"(?<!{EDGE}){re.escape(term)}(?!{EDGE})", text, re.IGNORECASE
            ):
                return {"match": term}
    elif "paths" in check:
        allow, deny = check["paths"].get("allow"), check["paths"].get("deny", [])
        if (allow and not any(fnmatch.fnmatch(text, g) for g in allow)) or any(
            fnmatch.fnmatch(text, g) for g in deny
        ):
            return {"path": text}
    return None


def deterministic(block, text):
    fired = []
    for check in block["checks"]:
        hit = _fires(check, text)
        if hit is not None:
            fired.append({**check, **hit})
    if any(c["then"] == "fail" for c in fired):
        verdict = "fail"
    elif fired or not block.get("complete"):
        verdict = "undecided"
    else:
        verdict = "pass"
    return Outcome(verdict, "deterministic", {"fired": fired})


def run(cases, decide=None, judge=None, only=TIERS):
    """Settle every case, tier by tier, batching each model tier across all pending cases."""
    results = [Result(c) for c in cases]
    pending = list(range(len(cases)))
    for tier in TIERS:
        batch = [i for i in pending if tier in only and tier in cases[i].rule]
        if not batch:
            continue
        if tier == "deterministic":
            outcomes = [
                deterministic(cases[i].rule[tier], cases[i].text) for i in batch
            ]
        else:
            adapter = decide if tier == "decision" else judge
            if adapter is None:
                continue
            outcomes = adapter([cases[i] for i in batch])
        for i, outcome in zip(batch, outcomes, strict=True):
            results[i].trail.append(outcome)
            if outcome.verdict != "undecided":
                results[i].final = outcome
        pending = [i for i in pending if results[i].final is None]
    for result in results:
        if result.final is None:
            result.final = Outcome("undecided", "owner", {})
    return results
