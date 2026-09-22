"""Evaluate validated declarations against context resolved to one scope."""


def validate_context(context, frames):
    """Validate local context; leave registry-backed values unresolved."""
    if not isinstance(context, dict):
        raise TypeError("Context must be a mapping")
    definitions = {frame["id"]: frame for frame in frames}

    def scalar(value, choices, path):
        if value is None:
            return None
        allowed = [item["id"] if isinstance(item, dict) else item for item in choices]
        if not isinstance(value, str) or value not in allowed:
            raise ValueError(f"{path}: invalid context value {value!r}")
        return value

    resolved = {}
    for key, value in context.items():
        if key not in definitions:
            raise ValueError(f"{key}: undeclared context frame")
        frame = definitions[key]
        if value is None or "source" in frame:
            resolved[key] = None
        elif "facets" in frame:
            if not isinstance(value, dict):
                raise ValueError(f"{key}: faceted context must be a mapping")
            resolved[key] = {}
            for facet, actual in value.items():
                if facet not in frame["facets"]:
                    raise ValueError(f"{key}.{facet}: undeclared context facet")
                resolved[key][facet] = scalar(
                    actual, frame["facets"][facet], f"{key}.{facet}"
                )
        else:
            resolved[key] = scalar(value, frame["values"], key)
    return resolved


def _all(values):
    values = list(values)
    if False in values:
        return False
    return None if None in values else True


def evaluate_predicate(predicate, context):
    """Return True, False or None (unknown), with AND across dimensions/facets."""

    def match(options, actual):
        if not options:
            return False
        if actual is None:
            return None
        if isinstance(actual, (dict, list, set, tuple)):
            raise TypeError("Context must resolve one value per dimension/facet")
        return actual in options

    results = []
    for dimension, condition in predicate.items():
        actual = context.get(dimension)
        if isinstance(condition, dict):
            if actual is not None and not isinstance(actual, dict):
                raise ValueError("Faceted context must be a mapping")
            results.append(
                _all(
                    match(options, (actual or {}).get(facet))
                    for facet, options in condition.items()
                )
            )
        else:
            results.append(match(condition, actual))
    return _all(results)


def artifact_availability(disabled_when, empty_when, context):
    """Resolve global suppression before evaluating any members."""
    disabled = (
        False if disabled_when is None else evaluate_predicate(disabled_when, context)
    )
    empty = evaluate_predicate(empty_when, context)
    if disabled is True:
        return "disabled"
    if empty is True:
        return "empty"
    if disabled is None or empty is None:
        return "unresolved"
    return "applicable"


def evaluate_member(entry, list_strength, context, gate=None):
    """Evaluate a member after its artifact has resolved as applicable."""
    entry = {"element": entry} if isinstance(entry, str) else entry
    if list_strength not in ("core", "situational"):
        raise ValueError("Unknown composition strength")
    if entry.get("strength", list_strength) != list_strength:
        raise ValueError("Explicit strength conflicts with composition list")
    allowed = True if gate is None else evaluate_predicate(gate, context)
    if allowed is False:
        return {"applicability": "excluded", "strength": None}
    if allowed is None:
        return {"applicability": "unresolved", "strength": None}
    condition = evaluate_predicate(entry.get("when", {}), context)
    if list_strength == "core":
        strength = (
            "core"
            if condition is True
            else "situational"
            if condition is False
            else None
        )
        return {"applicability": "available", "strength": strength}
    if condition is None:
        return {"applicability": "unresolved", "strength": None}
    if condition is False:
        return {"applicability": "excluded", "strength": None}
    return {"applicability": "available", "strength": "situational"}
