"""Read the neutral eval spec under evals/ and report every structural problem.

The spec is two files: universe.yaml (rules over definitions) and skills.yaml (behaviours of
agents doing knowledge work). Each rule and behaviour says why it matters, and each labelled
example carries a note explaining its verdict.
"""

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
EVALS = ROOT / "evals"
SKILLS = ROOT / "skills"
SCHEMA = "evals/1"
TIERS = ("deterministic", "decision", "judgment")
CHECKS = ("words", "pattern", "terms", "paths")
DECISIONS = ("yes-no", "choice", "score")
SCOPES = ("item", "pair", "set")
SHARED = ("why", "applies_to", "scope", *TIERS, "examples")
FIELDS = {
    "universe": {"rule", "sort", "recognise", *SHARED},
    "skills": {"behaviour", "skills", "grade_with", *SHARED},
}
EXAMPLE_FIELDS = {"text", "verdict", "note", "subject", "context"}
SCENARIO_FIELDS = {"skill", "prompt", "fixture", "owner", "required"}
IDENTIFIERS = {
    "a UUID": re.compile(
        r"\b[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}\b",
        re.IGNORECASE,
    ),
    "an absolute path": re.compile(r"/Users/|/home/|~/"),
    "an email address": re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"),
}
VENDORS = re.compile(
    r"\b(claude|anthropic|openai|gpt|chatgpt|codex|jev|typesafe|vale|harper|mcpjam|sonnet|opus"
    r"|haiku)\b",
    re.IGNORECASE,
)


class SpecError(ValueError):
    pass


@dataclass(frozen=True)
class Spec:
    universe: dict
    skills: dict
    folder: Path


class _Loader(yaml.SafeLoader):
    pass


def _unique_mapping(loader, node, deep=False):
    keys = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in keys:
            raise SpecError(
                f"duplicate key {key} at line {key_node.start_mark.line + 1}"
            )
        keys.add(key)
    return loader.construct_mapping(node, deep=deep)


_Loader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _unique_mapping)


def read(path):
    return yaml.load(Path(path).read_text(), Loader=_Loader)


def load(folder=EVALS):
    folder = Path(folder)
    return Spec(
        universe=read(folder / "universe.yaml"),
        skills=read(folder / "skills.yaml"),
        folder=folder,
    )


def unportable(pattern):
    """True when a pattern uses lookaround or a backreference, which RE2 cannot run."""
    in_class = escaped = False
    for i, char in enumerate(pattern):
        if escaped:
            escaped = False
            if not in_class and char in "123456789":
                return True
        elif char == "\\":
            escaped = True
        elif in_class:
            in_class = char != "]"
        elif char == "[":
            in_class = True
        elif (
            char == "("
            and pattern[i + 1 : i + 3] in ("?=", "?!", "?<")
            and pattern[i + 1 : i + 4] != "?<P"
        ):
            return True
    return False


def _deterministic(where, block, slice_):
    found = []
    if not isinstance(block.get("complete"), bool):
        found.append(f"{where}: deterministic needs complete: true or false")
    kinds = CHECKS if slice_ == "skills" else CHECKS[:3]
    for n, check in enumerate(block.get("checks") or [], 1):
        at = f"{where}: check {n}"
        present = [k for k in kinds if k in check]
        if len(present) != 1 or set(check) - set(kinds) - {"then", "ignore_case"}:
            found.append(f"{at} must have exactly one of {', '.join(kinds)}")
            continue
        if check.get("then") not in ("fail", "flag"):
            found.append(f"{at} needs then: fail or flag")
        kind = present[0]
        if kind == "pattern":
            try:
                re.compile(check["pattern"])
            except re.error as error:
                found.append(f"{at} does not compile: {error}")
            if unportable(check["pattern"]):
                found.append(f"{at} uses lookaround or backreference")
        elif kind == "words":
            bounds = check["words"]
            if (
                not isinstance(bounds, dict)
                or not set(bounds)
                or set(bounds) - {"min", "max"}
            ):
                found.append(f"{at}: words takes min and/or max")
        elif kind == "terms":
            if not check["terms"] or not all(
                isinstance(t, str) for t in check["terms"]
            ):
                found.append(f"{at}: terms is a list of words or phrases")
        elif kind == "paths":
            if not set(check["paths"]) <= {"allow", "deny"}:
                found.append(f"{at}: paths takes allow and/or deny globs")
    if not block.get("checks"):
        found.append(f"{where}: deterministic has no checks")
    return found


def _decision(where, block):
    found = []
    kind = block.get("type")
    if not block.get("ask"):
        found.append(f"{where}: decision needs ask")
    if kind not in DECISIONS:
        found.append(f"{where}: decision type must be one of {', '.join(DECISIONS)}")
    elif kind == "yes-no":
        if block.get("fail_when") not in ("yes", "no"):
            found.append(f"{where}: yes-no decision needs fail_when: yes or no")
    elif kind == "choice":
        options = block.get("criteria") or {}
        fail = block.get("fail_when")
        if len(options) < 2:
            found.append(f"{where}: choice needs at least two criteria")
        if not isinstance(fail, list) or not set(fail) <= set(options):
            found.append(f"{where}: choice fail_when must list criteria options")
    else:
        levels = block.get("levels") or []
        below = (
            (block.get("fail_when") or {}).get("below")
            if isinstance(block.get("fail_when"), dict)
            else None
        )
        if not 2 <= len(levels) <= 10:
            found.append(f"{where}: score needs 2 to 10 levels")
        if not isinstance(below, int) or not 0 < below < len(levels):
            found.append(f"{where}: score fail_when needs below: a level index")
    return found


def _item(where, item, slice_, subjects, label):
    found = []
    for field in (label, "why"):
        if not item.get(field):
            found.append(f"{where}: needs {field}")
    for field in sorted(set(item) - FIELDS[slice_]):
        found.append(f"{where}: unknown field {field}")
    applies = item.get("applies_to") or []
    if not applies:
        found.append(f"{where}: needs applies_to")
    for subject in applies:
        if subject not in subjects:
            found.append(f"{where}: {subject} is not a declared subject")
    scope = item.get("scope", "item")
    if scope not in SCOPES:
        found.append(f"{where}: scope is item, pair or set")
    sort = item.get("sort")
    if sort is not None:
        if scope != "set":
            found.append(f"{where}: sort is allowed only with scope set")
        if (
            not isinstance(sort, dict)
            or set(sort) != {"ask", "write"}
            or not all(isinstance(v, str) and v for v in sort.values())
        ):
            found.append(f"{where}: sort takes ask and write, each a text")
    recognise = item.get("recognise")
    if recognise is not None:
        found += _recognise(where, recognise, scope)
    filed = sort is not None or recognise is not None
    delegated = item.get("grade_with") == "universe"
    if not delegated and not filed and not any(t in item for t in TIERS):
        found.append(
            f"{where}: needs at least one tier"
            + (", a sort block or a recognise block" if slice_ == "universe" else "")
        )
    if "deterministic" in item:
        found += _deterministic(where, item["deterministic"], slice_)
    if "decision" in item:
        found += _decision(where, item["decision"])
    if "judgment" in item and not (
        item["judgment"].get("pass") and item["judgment"].get("fail")
    ):
        found.append(f"{where}: judgment needs pass and fail")
    examples = item.get("examples") or []
    for verdict in ("fail", "pass"):
        if not delegated and sum(e.get("verdict") == verdict for e in examples) < 2:
            found.append(f"{where}: needs at least two {verdict} examples")
    for n, example in enumerate(examples, 1):
        at = f"{where}: example {n}"
        if example.get("verdict") not in ("pass", "fail"):
            found.append(f"{at} verdict is pass or fail")
        if not example.get("text"):
            found.append(f"{at} needs text")
        if not example.get("note"):
            found.append(f"{at} needs a note")
        if "subject" in example and example["subject"] not in applies:
            found.append(f"{at} subject is not in applies_to")
        for field in sorted(set(example) - EXAMPLE_FIELDS):
            found.append(f"{at} has unknown field {field}")
        context = example.get("context") or {}
        member = example.get("text")
        if context.get("strength"):
            member = f"{context['strength']}: {member}"
        if scope == "set" and not (
            _texts(context.get("set")) and member in context["set"]
        ):
            found.append(f"{at} needs context.set, a list of texts holding its text")
        if filed and not _texts(context.get("probes")):
            found.append(f"{at} needs context.probes, a list of passages")
    checks = (item.get("deterministic") or {}).get("checks") or []
    for c, check in enumerate(checks, 1):
        if check.get("then") != "fail":
            continue
        for n, example in enumerate(examples, 1):
            if example.get("verdict") == "pass" and _fires(
                check, example.get("text", "")
            ):
                found.append(f"{where}: check {c} fails pass example {n}")
    found += _vendors(where, _prose(item, label))
    return found


def _recognise(where, block, scope):
    found = []
    if scope != "set":
        found.append(f"{where}: recognise is allowed only with scope set")
    shares = ("value_share", "frame_share")
    if (
        not isinstance(block, dict)
        or set(block) != {"ask", *shares}
        or not (isinstance(block["ask"], str) and block["ask"])
        or not all(_share(block[k]) for k in shares)
    ):
        found.append(
            f"{where}: recognise takes ask, a text, and value_share and frame_share, "
            "each above 0 and at most 1"
        )
    return found


def _share(value):
    return (
        isinstance(value, int | float)
        and not isinstance(value, bool)
        and 0 < value <= 1
    )


def _texts(value):
    """True for a non-empty list of strings."""
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(v, str) for v in value)
    )


def _fires(check, text):
    import tiers  # the same engine the grader runs

    try:
        return (
            tiers.deterministic({"complete": False, "checks": [check]}, text).verdict
            == "fail"
        )
    except re.error, KeyError, TypeError:
        return False


def _prose(item, label):
    yield label, item.get(label)
    yield "why", item.get("why")
    yield "decision ask", (item.get("decision") or {}).get("ask")
    sort = item.get("sort") if isinstance(item.get("sort"), dict) else {}
    yield "sort ask", sort.get("ask")
    yield "sort write", sort.get("write")
    recognise = item.get("recognise")
    yield "recognise ask", recognise.get("ask") if isinstance(recognise, dict) else None
    for verdict, text in (item.get("judgment") or {}).items():
        yield f"judgment {verdict}", text
    for n, example in enumerate(item.get("examples") or [], 1):
        yield f"example {n} note", example.get("note")


def _vendors(where, parts):
    found = []
    for part, text in parts:
        vendor = VENDORS.search(str(text or ""))
        if vendor:
            found.append(f"{where}: {part} names a vendor: {vendor.group(0)}")
    return found


def _strings(node, path=""):
    """(path, text) for every key and string value in a spec file."""
    if isinstance(node, dict):
        for key, value in node.items():
            here = f"{path}.{key}" if path else str(key)
            yield here, str(key)
            yield from _strings(value, here)
    elif isinstance(node, list):
        for n, value in enumerate(node, 1):
            yield from _strings(value, f"{path}[{n}]")
    elif isinstance(node, str):
        yield path, node


def problems(spec, skills_dir=SKILLS):
    found = []
    known_skills = {p.parent.name for p in Path(skills_dir).glob("*/SKILL.md")}
    for slice_, doc, key, label in (
        ("universe", spec.universe, "rules", "rule"),
        ("skills", spec.skills, "behaviours", "behaviour"),
    ):
        if doc.get("schema") != SCHEMA or doc.get("slice") != slice_:
            found.append(f"{slice_}.yaml: needs schema: {SCHEMA} and slice: {slice_}")
        subjects = doc.get("subjects") or {}
        for name, item in (doc.get(key) or {}).items():
            found += _item(f"{slice_}/{name}", item, slice_, subjects, label)
    cases = spec.universe.get("cases") or {}
    if spec.universe.get("rules") and "default" not in cases:
        found.append("universe/cases: needs a default case")
    for subject, case in cases.items():
        if subject != "default" and subject not in (
            spec.universe.get("subjects") or {}
        ):
            found.append(f"universe/cases: {subject} is not a declared subject")
        if case.get("skill") not in known_skills:
            found.append(
                f"universe/cases/{subject}: {case.get('skill')} is not a skill"
            )
        if not case.get("ask"):
            found.append(f"universe/cases/{subject}: needs ask")
    behaviours = spec.skills.get("behaviours") or {}
    for name, scenario in (spec.skills.get("scenarios") or {}).items():
        where = f"skills/scenarios/{name}"
        if scenario.get("skill") not in known_skills:
            found.append(f"{where}: {scenario.get('skill')} is not a skill")
        for ref in scenario.get("required") or []:
            if ref not in behaviours:
                found.append(f"{where}: {ref} is not a behaviour")
        for field in ("prompt", "owner", "required"):
            if not scenario.get(field):
                found.append(f"{where}: needs {field}")
        for field in sorted(set(scenario) - SCENARIO_FIELDS):
            found.append(f"{where}: unknown field {field}")
        owner = scenario.get("owner") or []
        if not isinstance(owner, list) or not all(isinstance(r, str) for r in owner):
            found.append(f"{where}: owner is a list of replies")
            owner = []
        fixture = scenario.get("fixture", "none")
        if isinstance(fixture, dict):
            if set(fixture) != {"needs"} or not fixture["needs"]:
                found.append(f"{where}: fixture needs: says what the folder must hold")
        elif fixture != "none" and not (spec.folder.parent / fixture).is_dir():
            found.append(
                f"{where}: fixture {fixture} is not a folder in the repository"
            )
        found += _vendors(
            where,
            [("prompt", scenario.get("prompt"))]
            + [(f"owner reply {n}", r) for n, r in enumerate(owner, 1)],
        )
    for name, item in (spec.skills.get("behaviours") or {}).items():
        for skill in item.get("skills") or []:
            if skill not in known_skills:
                found.append(f"skills/{name}: {skill} is not a skill")
    for name, doc in (("universe", spec.universe), ("skills", spec.skills)):
        for path, text in _strings(doc):
            for what, pattern in IDENTIFIERS.items():
                if pattern.search(text):
                    found.append(f"{name}.yaml: {path} holds {what}")
    return found
