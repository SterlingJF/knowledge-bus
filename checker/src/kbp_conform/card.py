"""The card for one document type, built from a loaded universe spec and its guidance.

The card states conditions and never decides whether a condition holds. It takes documents that are
already loaded and checked, and it opens no files. docs/document-type-card.md describes
every field, where it comes from, and the readable wording.
"""

CARD_SCHEMA = "knowledge-bus/card/1"
KINDS_SCHEMA = "knowledge-bus/kinds/1"
KINDS_SET_SCHEMA = "knowledge-bus/kinds-set/1"
FROM_PARENT = "from the parent folder"
NOT_STATED = "not stated in the universe spec"
STRENGTHS = ("core", "situational")


def display_name(item):
    return item.get("label") or item["id"].replace("-", " ").capitalize()


def kind_ids(universe):
    return [artifact["id"] for artifact in universe.get("artifacts") or []]


def _text(value):
    return None if value is None else str(value)


def _universe_spec(universe):
    header = universe["universe"]
    return {
        "id": header["id"],
        "label": header.get("label") or display_name(header),
        "version": _text(header.get("version")),
    }


def _folded(value):
    return None if value is None else " ".join(str(value).split())


def _kinds_universe_spec(universe):
    overview = universe["universe"].get("overview")
    overview = overview if isinstance(overview, dict) else {}
    return {
        **_universe_spec(universe),
        "covers": _folded(overview.get("covers")),
        "for": _folded(overview.get("for")),
    }


def _alias(artifact):
    alias = artifact.get("alias")
    if not isinstance(alias, dict):
        return None
    return {key: alias[key] for key in ("kind", "form") if key in alias}


def _enablement(artifact):
    enablement = artifact.get("enablement")
    if isinstance(enablement, dict):
        return {key: enablement.get(key) for key in ("action", "actor", "timing")}
    return {"action": _text(enablement), "actor": None, "timing": None}


def _no_artifact(universe):
    rule = universe.get("no_artifact", universe.get("empty_composition")) or {}
    return rule.get("when") or {}


def _entries(artifact, strength):
    for raw in (artifact.get("composition") or {}).get(strength) or []:
        yield {"element": raw} if isinstance(raw, str) else raw


def _keepers(universe, element_id):
    return [
        {"kind": artifact["id"], "name": display_name(artifact)}
        for artifact in universe.get("artifacts") or []
        for strength in STRENGTHS
        for entry in _entries(artifact, strength)
        if entry["element"] == element_id and entry.get("mode", "owns") == "owns"
    ]


def _notes(entries):
    if entries is None:
        return None
    return [
        {"kind": entry["kind"], "claim": entry["claim"], "when": entry.get("when")}
        for entry in entries
    ]


def _named(predicate, names):
    for key, value in (predicate or {}).items():
        named = names.setdefault(key, set())
        if isinstance(value, dict):
            continue
        named.update(value if isinstance(value, list) else [value])


def _conditions(universe, names):
    conditions = []
    for item in [*(universe.get("frames") or []), *(universe.get("factors") or [])]:
        if item["id"] not in names:
            continue
        values = [
            {"value": value["id"], "question": value["question"]}
            for value in item.get("values") or []
            if isinstance(value, dict)
            and value.get("id") in names[item["id"]]
            and value.get("question")
        ]
        conditions.append(
            {"id": item["id"], "question": item.get("question"), "values": values}
        )
    return conditions


def _factor_values(factor):
    return [
        {"value": value.get("id"), "question": value.get("question")}
        if isinstance(value, dict)
        else {"value": value, "question": None}
        for value in factor.get("values") or []
    ]


def _presentation(universe, guidance, from_parent):
    """One universe spec's factors, each with its values and the guidance keyed to the factor."""
    on_factors = (guidance or {}).get("factors") or {}
    factors, names = [], {}
    for factor in universe.get("factors") or []:
        notes = None if guidance is None else _notes(on_factors.get(factor["id"]) or [])
        for note in notes or []:
            _named(note["when"], names)
        factors.append(
            {
                "factor": factor["id"],
                "name": display_name(factor),
                "question": factor.get("question"),
                "values": _factor_values(factor),
                "guidance": notes,
            }
        )
    return {
        "universe_spec": _universe_spec(universe),
        "from_parent": from_parent,
        "factors": factors,
        "conditions": _conditions(universe, names),
    }


def build_card(universe, guidance, kind, others=(), from_parent=False):
    """Return the card for one document type; `guidance` is None when there is no file.

    `others` lists (universe, guidance, from_parent) for every other universe spec
    in scope. Each universe spec that declares a factor gives one presentation
    block, the card's own universe spec first.
    """
    artifact = next(item for item in universe["artifacts"] if item["id"] == kind)
    elements = {item["id"]: item for item in universe.get("elements") or []}
    on_kinds = (guidance or {}).get("artifacts") or {}
    on_sections = (guidance or {}).get("elements") or {}

    sections = []
    for strength in STRENGTHS:
        for entry in _entries(artifact, strength):
            element = elements[entry["element"]]
            mode = entry.get("mode", "owns")
            sections.append(
                {
                    "element": element["id"],
                    "name": display_name(element),
                    "question": element["question"],
                    "strength": strength,
                    "mode": mode,
                    "when": entry.get("when"),
                    "gate": element.get("gate"),
                    "kept_in": _keepers(universe, element["id"])
                    if mode == "links"
                    else None,
                    "guidance": None
                    if guidance is None
                    else _notes(on_sections.get(element["id"]) or []),
                }
            )

    card = {
        "schema": CARD_SCHEMA,
        "universe_spec": _universe_spec(universe),
        "kind": artifact["id"],
        "name": display_name(artifact),
        "alias": _alias(artifact),
        "enablement": _enablement(artifact),
        "disabled_when": artifact.get("disabled_when"),
        "no_artifact": _no_artifact(universe),
        "guidance": None if guidance is None else _notes(on_kinds.get(kind) or []),
        "sections": sections,
    }
    names = {}
    _named(card["disabled_when"], names)
    _named(card["no_artifact"], names)
    for note in card["guidance"] or []:
        _named(note["when"], names)
    for section in sections:
        _named(section["when"], names)
        _named(section["gate"], names)
        for note in section["guidance"] or []:
            _named(note["when"], names)
    card["conditions"] = _conditions(universe, names)
    card["presentation"] = [
        _presentation(*block)
        for block in [(universe, guidance, from_parent), *others]
        if block[0].get("factors")
    ]
    return card


def _factor_counts(universe, guidance):
    """Each factor with its question and its number of guidance entries; None without a guidance file."""
    on_factors = (guidance or {}).get("factors") or {}
    return [
        {
            "factor": factor["id"],
            "name": display_name(factor),
            "question": factor.get("question"),
            "guidance": None
            if guidance is None
            else len(on_factors.get(factor["id"]) or []),
        }
        for factor in universe.get("factors") or []
    ]


def build_kinds(universe, guidance=None):
    """Id, name, other names, purpose, users and timing of every document type, in declared order.

    `universe_spec` also gives `covers` and `for` from the universe spec overview.
    `factors` lists each factor with its guidance count; `guidance` is None when
    the universe spec has no guidance file.
    """
    kinds = []
    for artifact in universe.get("artifacts") or []:
        enablement = _enablement(artifact)
        kinds.append(
            {
                "kind": artifact["id"],
                "name": display_name(artifact),
                "alias": _alias(artifact),
                "action": enablement["action"],
                "actor": enablement["actor"],
                "timing": enablement["timing"],
            }
        )
    return {
        "schema": KINDS_SCHEMA,
        "universe_spec": _kinds_universe_spec(universe),
        "kinds": kinds,
        "factors": _factor_counts(universe, guidance),
    }


def build_kinds_set(listings, from_parent):
    """One kinds/1 group per universe spec, never merged, in the given order.

    `from_parent` lists the ids from the nested folder's workspace.yaml.
    """
    return {
        "schema": KINDS_SET_SCHEMA,
        "from_parent": list(from_parent),
        "universe_specs": list(listings),
    }


def _values(values):
    if not values:
        return "no value"
    return " or ".join(map(str, values))


def say(predicate):
    """Read a condition aloud without deciding whether the condition holds."""
    parts = []
    for key, value in predicate.items():
        if isinstance(value, dict):
            parts.extend(
                f"{key} {facet} is {_values(held)}" for facet, held in value.items()
            )
        else:
            parts.append(
                f"{key} is {_values(value if isinstance(value, list) else [value])}"
            )
    return " and ".join(parts)


def _depends(card, predicate):
    questions = {item["id"]: item["question"] for item in card["conditions"]}
    asks = [f"{questions.get(key) or NOT_STATED} ({key})" for key in predicate]
    return " Depends on: " + "; ".join(asks)


def _note(card, note):
    kind = note["kind"].capitalize()
    if not note["when"]:
        return f"- {kind}: {note['claim']}"
    when = note["when"]
    return f"- {kind}, when {say(when)}: {note['claim']}{_depends(card, when)}"


def _status(card, section):
    when = section["when"]
    if section["strength"] == "core":
        if not when:
            return "Required."
        return f"Required when {say(when)}; otherwise optional.{_depends(card, when)}"
    if not when:
        return "When applicable."
    return f"When applicable, available when {say(when)}.{_depends(card, when)}"


def _spec_name(spec):
    return f"{spec['label']} universe spec ({spec['id']} {spec['version']})"


def render_card(card):
    """The readable card as Markdown."""
    spec = card["universe_spec"]
    enablement = card["enablement"]
    lines = [
        f"# {card['name']}",
        "",
        f"Document type in the {_spec_name(spec)}.",
        "",
    ]
    alias = card["alias"] or {}
    if alias.get("kind") == "descriptive":
        lines.append(f"- Also called: {alias.get('form') or NOT_STATED}")
    elif alias.get("kind") == "normative":
        lines.append(
            f"- Its shape is set by an outside authority: {alias.get('form') or NOT_STATED}"
        )
    lines += [
        f"- Helps you: {enablement['action'] or NOT_STATED}",
        f"- Who uses it: {enablement['actor'] or NOT_STATED}",
        f"- When it is used: {enablement['timing'] or NOT_STATED}",
    ]
    disabled = card["disabled_when"]
    if disabled is not None:
        lines.append(
            f"- Not used when {say(disabled)}.{_depends(card, disabled)}"
            if disabled
            else "- Not used: in every situation."
        )
    empty = card["no_artifact"]
    lines.append(
        f"- No document needed when {say(empty)}.{_depends(card, empty)}"
        if empty
        else "- No document needed: in every situation."
    )
    if card["guidance"]:
        lines += ["", "## How to write it well", ""]
        lines += [_note(card, note) for note in card["guidance"]]
    lines += ["", "## Sections"]
    for section in card["sections"]:
        lines += [
            "",
            f"### {section['name']}",
            "",
            f"Answers: {section['question']}",
            _status(card, section),
        ]
        if section["gate"]:
            gate = section["gate"]
            lines.append(f"Applies only when {say(gate)}.{_depends(card, gate)}")
        if section["mode"] == "links":
            kept = " or ".join(keeper["name"] for keeper in section["kept_in"])
            where = f" ({kept})" if kept else ""
            tail = (
                " The notes below are for writing the section in that document."
                if section["guidance"]
                else ""
            )
            lines.append(
                f"Kept in another document{where}: link to that document.{tail}"
            )
        if section["guidance"]:
            lines.append("")
            lines += [_note(card, note) for note in section["guidance"]]
    lines += _presentation_lines(card)
    meanings = [
        f"- {item['id']} is {value['value']}: {value['question']}"
        for item in card["conditions"]
        for value in item["values"]
    ]
    if meanings:
        lines += ["", "## What the conditions mean", ""]
        lines += meanings
    return "\n".join(lines) + "\n"


def _presentation_lines(card):
    if not card["presentation"]:
        return []
    lines = [
        "",
        "## How to present it",
        "",
        "Factors change presentation and focus only. The sections stay the same.",
    ]
    for block in card["presentation"]:
        origin = f", {FROM_PARENT}" if block["from_parent"] else ""
        lines += ["", f"### {_spec_name(block['universe_spec'])}{origin}"]
        for factor in block["factors"]:
            lines += [
                "",
                f"#### {factor['name']}",
                "",
                f"Asks: {factor['question'] or NOT_STATED}",
            ]
            if factor["values"]:
                lines += ["", "Values:", ""]
                lines += [
                    f"- {value['value']}: {value['question']}"
                    if value["question"]
                    else f"- {value['value']}"
                    for value in factor["values"]
                ]
            if factor["guidance"]:
                lines += ["", "Advice:", ""]
                lines += [_note(block, note) for note in factor["guidance"]]
    return lines


def render_kinds(listing):
    """Every document type as a Markdown list."""
    spec = listing["universe_spec"]
    lines = [
        "# Document types",
        "",
        f"In the {_spec_name(spec)}.",
        "",
    ]
    lines += _overview_lines(spec)
    lines += _kind_lines(listing)
    if listing.get("factors"):
        while lines[-1] == "":
            lines.pop()
        lines += _factor_lines(listing)
    return "\n".join(lines) + "\n"


def render_kinds_set(listing_set):
    """Every document type as Markdown, one section per universe spec."""
    lines = ["# Document types"]
    for listing in listing_set["universe_specs"]:
        spec = listing["universe_spec"]
        origin = f", {FROM_PARENT}" if spec["id"] in listing_set["from_parent"] else ""
        lines += ["", f"## {_spec_name(spec)}{origin}", ""]
        lines += _overview_lines(spec)
        lines += _kind_lines(listing) or ["No document types."]
        lines += _factor_lines(listing)
    return "\n".join(lines) + "\n"


def _overview_lines(spec):
    lines = []
    for label, key in (("Covers", "covers"), ("For", "for")):
        if spec.get(key):
            lines += [f"{label}: {spec[key]}", ""]
    return lines


def _kind_lines(listing):
    lines = []
    for item in listing["kinds"]:
        lines.append(f"- {item['name']} ({item['kind']})")
        alias = item["alias"] or {}
        if alias.get("kind") == "descriptive":
            lines.append(f"  - Also called: {alias.get('form') or NOT_STATED}")
        elif alias.get("kind") == "normative":
            lines.append(
                f"  - Its shape is set by an outside authority: {alias.get('form') or NOT_STATED}"
            )
        lines.append(f"  - Helps you: {item['action'] or NOT_STATED}")
        if item.get("actor"):
            lines.append(f"  - Who uses it: {item['actor']}")
        if item.get("timing"):
            lines.append(f"  - When it is used: {item['timing']}")
    return lines


def _count(number):
    if number == 0:
        return "No guidance notes"
    return f"{number} guidance note{'' if number == 1 else 's'}"


def _factor_lines(listing):
    factors = listing.get("factors") or []
    if not factors:
        return []
    lines = ["", "Factors:", ""]
    for item in factors:
        lines.append(f"- {item['name']} ({item['factor']})")
        lines.append(f"  - Asks: {item['question'] or NOT_STATED}")
        if item["guidance"] is not None:
            lines.append(f"  - {_count(item['guidance'])}")
    return lines
