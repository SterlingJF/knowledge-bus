"""Validate a universe and prepare deterministic, unresolved Explorer input."""

import argparse
import collections
import contextlib
import datetime
import hashlib
import io
import json
import re
import sys
from pathlib import Path

from ._vendor import yaml
from .checker import check, check_guidance, self_check

ROOT = Path(__file__).resolve().parents[3]
SCHEMA = "knowledge-bus/explorer-model/1"
SOURCE_FIELD_A_SELF_CONTAINED_ARTIFACT_CANNOT_CARRY = "url"

MARK_SECTIONS = ("frames", "factors", "options")
MARK_HEADER_REQUIRED = ("id", "version", "marks_for")
DRAWABLE_PATH_DATA = re.compile(
    r"[Mm][0-9eE,.\-+ \t]*[0-9][MmZzLlHhVvCcSsQqTtAa0-9,.\-+eE \t]*"
)
A_MONOGRAM_FITS_THE_ICON_BOX = re.compile(r"[^\W_]{1,2}\Z", re.UNICODE)


class InspectionError(ValueError):
    """A structured inspection refusal that never carries a partial model."""

    def __init__(self, category, message, *, diagnostics=None, candidates=None):
        super().__init__(message)
        self.category = category
        self.diagnostics = list(diagnostics or [])
        self.candidates = sorted(candidates or [])

    def as_dict(self):
        result = {
            "schema": "knowledge-bus/inspection-error/1",
            "status": "error",
            "category": self.category,
            "message": str(self),
        }
        if self.diagnostics:
            result["diagnostics"] = self.diagnostics
        if self.candidates:
            result["candidates"] = self.candidates
        return result


def canonical_bytes(value):
    return json.dumps(
        as_json_scalar(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def digest(value):
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def model_digest(model):
    """Identify semantic model content independently of its producing release."""
    content = {key: value for key, value in model.items() if key != "modelDigest"}
    layers = content.get("layers")
    if isinstance(layers, dict):
        content["layers"] = {
            key: value for key, value in layers.items() if key != "knowledgeBusRelease"
        }
    return digest(content)


def scope_documents(scope):
    """List only supported direct definition and presentation documents."""
    scope = Path(scope).resolve()
    if not scope.is_dir():
        raise InspectionError("selection", "Inspection scope is not a directory")
    return sorted(
        path
        for path in scope.iterdir()
        if path.is_file()
        and (path.name.endswith(".kbp.yaml") or path.name.endswith(".explorer.yaml"))
    )


def _nearest_scope(start=None):
    here = Path(start or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if candidate.name == ".knowledge-bus" and candidate.is_dir():
            return candidate
        nested = candidate / ".knowledge-bus"
        if nested.is_dir():
            return nested
    return None


def resolve_inspection_targets(targets):
    """Resolve an explicit scope or the nearest scope, with optional file selection."""
    targets = list(targets)
    if not targets:
        scope = _nearest_scope()
        return (scope_documents(scope), None) if scope else ([], None)
    paths = [Path(value).resolve() for value in targets]
    missing = next((path for path in paths if not path.exists()), None)
    if missing:
        raise InspectionError("selection", f"Target does not exist: {missing.name}")
    selected = None
    if len(paths) == 1 and paths[0].is_file():
        try:
            document = yaml.safe_load(paths[0].read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError) as error:
            raise InspectionError(
                "conformance", f"Cannot read target: {error}"
            ) from error
        if isinstance(document, dict) and isinstance(document.get("universe"), dict):
            selected = document["universe"].get("id")
            return scope_documents(paths[0].parent), selected
    if len(paths) == 1 and paths[0].is_dir():
        scope = (
            paths[0]
            if paths[0].name == ".knowledge-bus"
            else paths[0] / ".knowledge-bus"
        )
        if scope.is_dir():
            return scope_documents(scope), None
    if any(path.is_dir() for path in paths):
        raise InspectionError(
            "selection", "Pass one scoped directory or explicit definition files"
        )
    return sorted(paths), selected


def display_label(item):
    return item.get("label") or item["id"].replace("-", " ").capitalize()


def as_json_scalar(value):
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: as_json_scalar(held) for key, held in value.items()}
    if isinstance(value, list):
        return [as_json_scalar(held) for held in value]
    return value


def guidance_sections(protocol):
    shape = protocol["declarations"]["guidance"]["document"]
    sections = []
    for kind in protocol["concepts"]["guidance"]["attaches_to"]:
        plural = kind + "s"
        if plural not in shape:
            raise ValueError(
                f"Protocol declares guidance attaching to {kind} but its document shape has no {plural}"
            )
        sections.append((plural, kind))
    return sections


def prepare_guidance(source, guidance, protocol):
    diagnostics = io.StringIO()
    with contextlib.redirect_stdout(diagnostics):
        if not isinstance(guidance, dict) or not isinstance(
            guidance.get("guidance"), dict
        ):
            raise TypeError("Guidance input must be a guidance document")
        universe_id = source["universe"].get("id")
        valid = check_guidance(
            protocol, guidance, {universe_id: source}, "explorer guidance"
        )
    if not valid:
        raise ValueError("Guidance conformance failed:\n" + diagnostics.getvalue())
    if guidance["guidance"].get("guides") != source["universe"].get("id"):
        raise ValueError(
            "Guidance guides a different universe than the one being prepared"
        )

    entries = []
    for plural, kind in guidance_sections(protocol):
        for subject_id, declared in (guidance.get(plural) or {}).items():
            for position, entry in enumerate(declared):
                entries.append(
                    {
                        "id": f"guidance:{len(entries)}",
                        "subject": f"{kind}:{subject_id}",
                        "kind": entry["kind"],
                        "claim": entry["claim"],
                        "source": entry["source"],
                        "when": entry.get("when"),
                        "sourcePath": f"{plural}.{subject_id}[{position}]",
                    }
                )
    header = guidance["guidance"]
    return {
        "id": header.get("id"),
        "label": header.get("label", ""),
        "version": str(header.get("version", "")),
        "guides": header.get("guides"),
        "kinds": [dict(kind) for kind in guidance["guidance_kinds"]],
        "sources": {
            name: {
                field: as_json_scalar(value)
                for field, value in declared.items()
                if field != SOURCE_FIELD_A_SELF_CONTAINED_ARTIFACT_CANNOT_CARRY
            }
            for name, declared in (guidance.get("sources") or {}).items()
        },
        "entries": entries,
    }


def checked_mark(mark, where):
    if not isinstance(mark, dict):
        raise TypeError(f"{where}: a mark must be a mapping, not {type(mark).__name__}")
    keys = set(mark)
    if keys != {"glyph"} and keys != {"monogram"}:
        raise ValueError(
            f"{where}: a mark declares exactly one of glyph or monogram, not {sorted(keys) or 'nothing'}"
        )
    key = next(iter(keys))
    value = mark[key]
    if not isinstance(value, str):
        raise TypeError(f"{where}: {key} must be a string")
    if key == "monogram":
        if not A_MONOGRAM_FITS_THE_ICON_BOX.fullmatch(value):
            raise ValueError(
                f"{where}: a monogram is one or two letters or digits, not {value!r}"
            )
    elif not DRAWABLE_PATH_DATA.fullmatch(value):
        raise ValueError(
            f"{where}: a glyph is SVG path data drawn inside the icon box, not a reference to {value!r}"
        )
    return {key: value}


def mark_subjects(entities):
    """Every concept the explorer draws a mark for, by the section that names it."""
    subjects = {section: {} for section in MARK_SECTIONS}
    for entity in entities:
        if entity["kind"] == "frame":
            subjects["frames"][entity["sourceId"]] = entity["id"]
        elif entity["kind"] == "factor":
            subjects["factors"][entity["sourceId"]] = entity["id"]
        elif entity["kind"] == "option":
            frame = entity["frameId"].split(":", 1)[1]
            subjects["options"].setdefault(frame, {}).setdefault(
                entity["sourceId"], []
            ).append(entity["id"])
    return subjects


def prepare_marks(source, marks, entities):
    if not isinstance(marks, dict) or not isinstance(marks.get("marks"), dict):
        raise TypeError("Marks input must be a marks document")
    header = marks["marks"]
    for key in MARK_HEADER_REQUIRED:
        if key not in header:
            raise ValueError(f"marks header: missing required '{key}'")
    if header["marks_for"] != source["universe"].get("id"):
        raise ValueError("Marks mark a different universe than the one being prepared")
    unsanctioned = set(marks) - {"marks", *MARK_SECTIONS}
    if unsanctioned:
        raise ValueError(f"marks document: unsanctioned {sorted(unsanctioned)}")

    subjects = mark_subjects(entities)
    declared = {}
    for section in MARK_SECTIONS:
        for subject, held in (marks.get(section) or {}).items():
            if section != "options":
                if subject not in subjects[section]:
                    raise ValueError(
                        f"{section}.{subject}: no {section[:-1]} of this universe carries that id"
                    )
                declared[subjects[section][subject]] = checked_mark(
                    held, f"{section}.{subject}"
                )
                continue
            if subject not in subjects["options"]:
                raise ValueError(
                    f"options.{subject}: no frame or factor of this universe carries that id"
                )
            if not isinstance(held, dict):
                raise TypeError(f"options.{subject}: must map value ids to marks")
            for value, mark in held.items():
                found = subjects["options"][subject].get(value, [])
                if len(found) != 1:
                    raise ValueError(
                        f"options.{subject}.{value}: names {len(found)} values of {subject}, not one"
                    )
                declared[found[0]] = checked_mark(mark, f"options.{subject}.{value}")

    drawn = collections.Counter(
        json.dumps(mark, sort_keys=True) for mark in declared.values()
    )
    shared = sorted(mark for mark, times in drawn.items() if times > 1)
    if shared:
        raise ValueError(f"marks: two concepts declare one mark — {shared}")

    return {
        "id": header["id"],
        "label": header.get("label", ""),
        "version": str(header["version"]),
        "marksFor": header["marks_for"],
        "declared": dict(sorted(declared.items())),
    }


def prepare_model(source, protocol, guidance=None, marks=None):
    diagnostics = io.StringIO()
    with contextlib.redirect_stdout(diagnostics):
        unsound = self_check(protocol)
        if unsound:
            raise ValueError("Unsound protocol: " + "; ".join(map(str, unsound)))
        expected = f"{protocol['protocol']['id']}/{protocol['protocol']['version']}"
        if not isinstance(source, dict) or not isinstance(source.get("universe"), dict):
            raise TypeError("Input must be a universe document")
        if source["universe"].get("conforms_to") != expected:
            raise ValueError(f"Universe conforms_to must match {expected}")
        valid = check(protocol, source, "explorer input")
    if not valid:
        raise ValueError("Universe conformance failed:\n" + diagnostics.getvalue())

    entities = []
    endpoints = {}
    frames = source.get("frames", [])
    frame_ids = [frame["id"] for frame in frames]
    for plural, kind in [
        ("frames", "frame"),
        ("factors", "factor"),
        ("artifacts", "artifact"),
        ("elements", "element"),
    ]:
        for index, item in enumerate(source.get(plural) or []):
            identity = f"{kind}:{item['id']}"
            entities.append(
                {
                    "id": identity,
                    "sourceId": item["id"],
                    "kind": kind,
                    "label": display_label(item),
                    "description": item.get("question", item.get("description", "")),
                    "frameValues": {key: item[key] for key in frame_ids if key in item},
                    "sourcePath": f"{plural}[{index}]",
                    "raw": item,
                }
            )
            if kind in ("artifact", "element"):
                if item["id"] in endpoints:
                    raise ValueError(f"Ambiguous relation endpoint: {item['id']}")
                endpoints[item["id"]] = identity
            if kind != "frame":
                continue
            groups = [(None, item.get("values", []))]
            groups.extend(
                (facet, values) for facet, values in item.get("facets", {}).items()
            )
            for facet, values in groups:
                for position, value in enumerate(values):
                    option = value if isinstance(value, dict) else {"id": value}
                    suffix = f"{facet}:" if facet else ""
                    entities.append(
                        {
                            "id": f"option:{item['id']}:{suffix}{option['id']}",
                            "sourceId": option["id"],
                            "kind": "option",
                            "label": display_label(option),
                            "description": option.get("question", ""),
                            "frameId": identity,
                            "facet": facet,
                            "frameValues": {
                                item["id"]: {facet: option["id"]}
                                if facet
                                else option["id"]
                            },
                            "sourcePath": f"{plural}[{index}]."
                            + (f"facets.{facet}" if facet else "values")
                            + f"[{position}]",
                            "raw": value,
                        }
                    )

    connections = []
    definitions = {item["id"]: item for item in source.get("relation_kinds", [])}
    for index, relation in enumerate(source.get("relations", [])):
        definition = definitions[relation["kind"]]
        phrasing = definition.get("phrasing", {})
        required = ("forward", "reverse") if definition["ordered"] else ("forward",)
        if any(
            not isinstance(phrasing.get(key), str) or not phrasing[key].strip()
            for key in required
        ):
            raise ValueError(
                f"Relation kind {definition['id']} lacks audience phrasing"
            )
        connections.append(
            {
                "id": f"relation:{index}",
                "from": endpoints[relation["from"]],
                "to": endpoints[relation["to"]],
                "kind": relation["kind"],
                "ordered": definition["ordered"],
                "phrasing": {key: phrasing[key] for key in required},
                "sourcePath": f"relations[{index}]",
                "raw": relation,
            }
        )
    for artifact_index, artifact in enumerate(source.get("artifacts", [])):
        for strength, entries in artifact["composition"].items():
            for index, entry in enumerate(entries):
                member = {"element": entry} if isinstance(entry, str) else entry
                connections.append(
                    {
                        "id": f"composition:{artifact['id']}:{strength}:{index}",
                        "from": f"artifact:{artifact['id']}",
                        "to": f"element:{member['element']}",
                        "kind": "composition",
                        "ordered": True,
                        "phrasing": {"forward": "Includes", "reverse": "Included in"},
                        "strength": strength,
                        "mode": member.get("mode", "owns"),
                        "when": member.get("when"),
                        "sourcePath": f"artifacts[{artifact_index}].composition.{strength}[{index}]",
                        "raw": entry,
                    }
                )
    wiring = build_wiring(source, connections, endpoints, frame_ids)
    canonical = json.dumps(
        source, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return {
        "schema": SCHEMA,
        "sourceDigest": "sha256:" + hashlib.sha256(canonical.encode()).hexdigest(),
        "protocolVersion": str(protocol["protocol"]["version"]),
        "universe": source["universe"],
        "orderingFrameId": "frame:" + source["universe"]["ordering_frame"],
        "entities": entities,
        "connections": connections,
        "guidance": prepare_guidance(source, guidance, protocol)
        if guidance is not None
        else None,
        "marks": prepare_marks(source, marks, entities) if marks is not None else None,
        "wiring": wiring,
        "rules": [
            {
                "id": "rule:empty-composition",
                "kind": "empty-composition",
                "raw": source["empty_composition"],
                "sourcePath": "empty_composition",
            }
        ],
        "source": source,
        "evaluation": {"status": "unresolved", "context": None},
    }


def _loaded_documents(paths):
    loaded = []
    for path in paths:
        path = Path(path)
        try:
            document = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as error:
            raise InspectionError(
                "conformance", f"Cannot parse {path.name}: {error}"
            ) from error
        if not isinstance(document, dict):
            raise InspectionError(
                "conformance", f"{path.name}: document must be a mapping"
            )
        kinds = [kind for kind in ("universe", "guidance", "marks") if kind in document]
        if len(kinds) != 1:
            raise InspectionError(
                "conformance",
                f"{path.name}: expected exactly one universe, guidance, or marks header",
            )
        loaded.append((path.name, kinds[0], document))
    return loaded


def _identity(role, document):
    header = document[role]
    link = "guides" if role == "guidance" else "marks_for" if role == "marks" else None
    result = {
        "role": role,
        "id": str(header.get("id", "")),
        "version": str(header.get("version", "")),
        "digest": digest(document),
    }
    if link:
        result["forUniverse"] = str(header.get(link, ""))
    return result


def inspect_paths(protocol_path, paths, *, universe_id=None, release_version=None):
    """Validate and project one universe without writing source or output files."""
    try:
        protocol = yaml.safe_load(Path(protocol_path).read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise InspectionError(
            "protocol", f"Cannot load the protocol: {error}"
        ) from error
    diagnostics = io.StringIO()
    with contextlib.redirect_stdout(diagnostics):
        unsound = self_check(protocol)
    if unsound:
        raise InspectionError(
            "protocol",
            "Bundled protocol is unsound",
            diagnostics=list(map(str, unsound)),
        )

    loaded = _loaded_documents(paths)
    universes = [(name, doc) for name, kind, doc in loaded if kind == "universe"]
    ids = [doc["universe"].get("id") for _, doc in universes]
    counts = collections.Counter(identity for identity in ids if identity)
    duplicates = sorted(identity for identity, count in counts.items() if count > 1)
    if duplicates:
        raise InspectionError(
            "conformance", f"Duplicate universe id values: {', '.join(duplicates)}"
        )
    available = sorted(identity for identity in ids if isinstance(identity, str))
    if not available:
        raise InspectionError(
            "selection", "No universe definitions in the selected scope"
        )
    if universe_id is None:
        if len(available) != 1:
            raise InspectionError(
                "selection",
                "Multiple universes require an explicit universe id or file",
                candidates=available,
            )
        universe_id = available[0]
    if universe_id not in available:
        raise InspectionError(
            "selection",
            f"Universe {universe_id!r} is not in the selected scope",
            candidates=available,
        )

    guidance_by_universe = {}
    marks_by_universe = {}
    for name, kind, document in loaded:
        if kind not in ("guidance", "marks"):
            continue
        header = document[kind]
        key = "guides" if kind == "guidance" else "marks_for"
        target = header.get(key)
        if target not in available:
            raise InspectionError(
                "conformance",
                f"{name}: {kind}.{key} names no universe in the selected scope",
            )
        grouped = guidance_by_universe if kind == "guidance" else marks_by_universe
        grouped.setdefault(target, []).append((name, document))
    for kind, grouped in (
        ("guidance", guidance_by_universe),
        ("marks", marks_by_universe),
    ):
        matching = grouped.get(universe_id, [])
        if len(matching) > 1:
            raise InspectionError(
                "conformance",
                f"Universe {universe_id!r} has multiple {kind} documents",
            )

    source = next(
        doc for _, doc in universes if doc["universe"].get("id") == universe_id
    )
    guidance = (
        guidance_by_universe.get(universe_id, [(None, None)])[0][1]
        if guidance_by_universe.get(universe_id)
        else None
    )
    marks = (
        marks_by_universe.get(universe_id, [(None, None)])[0][1]
        if marks_by_universe.get(universe_id)
        else None
    )
    structural = io.StringIO()
    expected = f"{protocol['protocol']['id']}/{protocol['protocol']['version']}"
    with contextlib.redirect_stdout(structural):
        declared = source.get("universe", {}).get("conforms_to")
        valid = declared == expected and check(protocol, source, "selected universe")
        if guidance is not None:
            valid = (
                check_guidance(
                    protocol, guidance, {universe_id: source}, "selected guidance"
                )
                and valid
            )
    if not valid:
        findings = [
            line.strip() for line in structural.getvalue().splitlines() if line.strip()
        ]
        if declared != expected:
            findings.insert(0, f"conforms_to {declared!r} does not match {expected!r}")
        raise InspectionError(
            "conformance",
            "Selected definitions do not conform to the bundled protocol",
            diagnostics=findings,
        )
    try:
        model = prepare_model(source, protocol, guidance, marks)
    except (ValueError, TypeError, KeyError) as error:
        raise InspectionError("renderability", str(error)) from error

    identities = [
        {
            "role": "protocol",
            "id": str(protocol["protocol"]["id"]),
            "version": str(protocol["protocol"]["version"]),
            "digest": digest(protocol),
        },
        _identity("universe", source),
    ]
    if guidance is not None:
        identities.append(_identity("guidance", guidance))
    if marks is not None:
        identities.append(_identity("marks", marks))
    model["layers"] = {
        "knowledgeBusRelease": str(release_version or "unknown"),
        "protocol": identities[0],
        "universe": identities[1],
        "guidance": next(
            (item for item in identities if item["role"] == "guidance"), None
        ),
        "marks": next((item for item in identities if item["role"] == "marks"), None),
        "explorerModel": {"schema": SCHEMA},
    }
    model["input"] = {
        "documents": identities,
        "digest": digest(identities),
    }
    model["checks"] = {
        "scope": "selected universe and semantic companions",
        "conformance": "passed",
        "explorerRenderability": "passed",
    }
    model["limitations"] = [
        "Structural conformance and Explorer renderability do not establish truth or usefulness.",
        "Answers and ingestion logs are not checker-validated inputs.",
        "Guidance is advisory; factors have no structural power.",
    ]
    model["modelDigest"] = model_digest(model)
    return model


def build_wiring(source, connections, endpoints, frame_ids):
    wiring = []
    known = set(frame_ids) | {factor["id"] for factor in source.get("factors") or []}

    def reference(predicate, target, path, kind, **extra):
        for frame, value in (predicate or {}).items():
            if frame not in known:
                raise ValueError(f"{path}: {frame} is not a declared frame or factor")
            wiring.append(
                {
                    "id": f"wiring:{len(wiring)}",
                    "from": f"frame:{frame}",
                    "sourceFrameId": frame,
                    "to": target,
                    "kind": kind,
                    "value": value if isinstance(value, list) else [value],
                    "sourcePath": path,
                    **extra,
                }
            )

    ordering = source["universe"]["ordering_frame"]
    for index, element in enumerate(source.get("elements") or []):
        reference(
            element.get("gate"),
            f"element:{element['id']}",
            f"elements[{index}].gate",
            "gate",
        )
        if ordering in element:
            reference(
                {ordering: element[ordering]},
                f"element:{element['id']}",
                f"elements[{index}].{ordering}",
                "ordering",
            )
    for index, artifact in enumerate(source.get("artifacts") or []):
        reference(
            artifact.get("disabled_when"),
            f"artifact:{artifact['id']}",
            f"artifacts[{index}].disabled_when",
            "disabled_when",
        )
    for connection in connections:
        if connection["kind"] == "composition" and connection.get("when"):
            reference(
                connection["when"],
                connection["from"],
                connection["sourcePath"] + ".when",
                "composition.when",
                targetPair=[connection["from"], connection["to"]],
                targetLabel=f"{connection['strength']} · {connection['mode']}",
            )
    for index, relation in enumerate(source.get("relations") or []):
        if relation.get("gate"):
            reference(
                relation["gate"],
                endpoints[relation["from"]],
                f"relations[{index}].gate",
                "relation.gate",
                targetPair=[endpoints[relation["from"]], endpoints[relation["to"]]],
                targetLabel=relation["kind"],
            )
    reference(
        source["empty_composition"].get("when"),
        "rule:empty-composition",
        "empty_composition.when",
        "empty_composition.when",
    )
    return wiring


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--guidance", type=Path, default=None)
    parser.add_argument("--marks", type=Path, default=None)
    parser.add_argument(
        "--protocol", type=Path, default=ROOT / "protocol/knowledge-bus-protocol.yaml"
    )
    args = parser.parse_args(argv)
    try:
        source = yaml.safe_load(args.input.read_text(encoding="utf-8"))
        protocol = yaml.safe_load(args.protocol.read_text(encoding="utf-8"))
        guidance = (
            yaml.safe_load(args.guidance.read_text(encoding="utf-8"))
            if args.guidance
            else None
        )
        marks = (
            yaml.safe_load(args.marks.read_text(encoding="utf-8"))
            if args.marks
            else None
        )
        model = prepare_model(source, protocol, guidance, marks)
        encoded = json.dumps(model, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    except (OSError, ValueError, TypeError, KeyError, yaml.YAMLError) as error:
        print(f"Explorer input error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
