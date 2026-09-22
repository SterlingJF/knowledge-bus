"""Type checking — KBP documents against the Knowledge Bus Protocol.

The protocol is checked first, against itself. It is not a `*.kbp.yaml`
document and conforms to nothing, so the question is soundness rather than
conformance: do its own declarations agree with each other, and with the code
that reads them. An unsound protocol stops the run — a document verdict
computed against it would not be unreliable, it would be misleading.

A document declares its type by its top-level header key — `universe` or
`guidance` — per `declarations.document_types`. Universes are checked first,
then guidance documents against the universe each one guides.

Universe checks: sanctioned field names against `declarations`, required
fields, conditional requirements, composition-entry shape including the
declared shorthand, frame and factor value shapes, the `one_of` choice
between `values`, `facets` and `source`, frame predicates — including the
rule that a universe predicate may never name a factor — enums, codes,
relation edge shape, cycle legality, and referential integrity.

Guidance checks: sanctioned field names, required fields, key resolution
against the guided universe, declared kinds, source resolution including the
`sourced` obligation, and predicates against the frames *and factors* the
guided universe declares.

Codes are stable, unordered, machine-facing handles. The kind letter is the
set — `e` element, `a` artifact type, `f` frame, `k` factor — so a code is
unique universe-wide, and the tail is drawn from an alphabet no YAML resolver
reads as a number, a boolean or null.

Self-test note: injected violations must fail this. A check that reports
CONFORMS while violations are live is worse than no check — that is the
failure this module exists to prevent.

One convention this package holds itself to, and `self_check` enforces: a key
subscripted on a document is a key the protocol must require. Optional access
uses `.get()`. Where that holds an omission produces a verdict; where it does
not, it produces a traceback. `_package_source()` reads every module in the
package so that splitting the code cannot narrow the check without saying so.
"""

import ast
import os
import re
import secrets

from ._vendor import yaml

META = {
    "required",
    "one_of",
    "header_required",
    "document",
    "shorthand",
    "qualified_values_when",
}

ALPHABET = "0123456789abcdefghjkmnpqrstvwxyz"
CODE_PREFIX = {"element": "e", "artifact": "a", "frame": "f", "factor": "k"}
CODE_TAIL = r"[0-9a-hjkmnp-tv-z]{4}"
CODED = ("element", "artifact", "frame", "factor")


NEEDS = [
    ("protocol", "id"),
    ("protocol", "version"),
    ("declarations", "document_types", "kinds"),
    ("declarations", "universe", "document"),
    ("declarations", "universe", "required"),
    ("declarations", "universe", "header_required"),
    ("declarations", "guidance", "document"),
    ("declarations", "guidance", "required"),
    ("declarations", "guidance", "header_required"),
    ("declarations", "element", "required"),
    ("declarations", "artifact", "required"),
    ("declarations", "artifact", "alias", "kind"),
    ("declarations", "artifact", "composition"),
    ("declarations", "frame", "required"),
    ("declarations", "frame", "role"),
    ("declarations", "frame", "set_by"),
    ("declarations", "frame", "one_of"),
    ("declarations", "factor", "required"),
    ("declarations", "factor", "set_by"),
    ("declarations", "factor", "one_of"),
    ("declarations", "relation_kind", "required"),
    ("declarations", "guidance_kind", "required"),
    ("declarations", "guidance_entry", "required"),
    ("composition", "entry", "mode"),
    ("composition", "entry", "strength"),
    ("composition", "entry", "required"),
    ("relations", "edge", "required"),
]

SUBSCRIPTS = [("check", "u", "universe"), ("check_guidance", "g", "guidance")]


def sanc(shape):
    return {k for k in shape if k not in META}


def alts(value):
    return {x.strip().strip('"') for x in str(value).split("|")}


def check_pred(
    pred,
    where,
    allowed,
    fail,
    forbidden=frozenset(),
    noun="frame",
    definitions=None,
):
    """Validate predicate values, distinguishing forbidden factors from unknown IDs."""

    def check_values(values, declared, location):
        # Source-backed dimensions have no local enumeration to validate against.
        if declared is None or not isinstance(values, list):
            return
        known = [v.get("id") if isinstance(v, dict) else v for v in declared]
        for value in values:
            if value not in known:
                fail.append(f"{location}: unknown predicate value {value!r}")

    for fid, val in pred.items():
        if fid in forbidden:
            fail.append(f"{where}: factor '{fid}' may not be referenced by a universe")
        elif fid not in allowed:
            fail.append(f"{where}: unknown {noun} '{fid}'")
        definition = (definitions or {}).get(fid, {})
        if isinstance(val, dict):
            for facet, fv in val.items():
                if not isinstance(fv, list):
                    fail.append(f"{where}.{fid}.{facet}: not a list")
                if definition:
                    facets = definition.get("facets", {})
                    if facet not in facets:
                        fail.append(f"{where}.{fid}: unknown facet '{facet}'")
                    else:
                        check_values(fv, facets.get(facet), f"{where}.{fid}.{facet}")
        elif not isinstance(val, list):
            fail.append(f"{where}: predicate '{fid}' value is a scalar, must be a list")
        else:
            if definition.get("facets"):
                fail.append(f"{where}.{fid}: faceted predicate must name facets")
            check_values(val, definition.get("values"), f"{where}.{fid}")


def _walk_shapes(node, path=()):
    """Every mapping in the protocol, with the path that reaches it."""
    if isinstance(node, dict):
        yield path, node
        for k, v in node.items():
            yield from _walk_shapes(v, path + (k,))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _walk_shapes(v, path + (str(i),))


def _package_source():
    """Read all Python modules for document-subscript analysis."""
    here = os.path.dirname(os.path.abspath(__file__))
    return "\n".join(
        open(os.path.join(here, fn), encoding="utf-8").read()
        for fn in sorted(os.listdir(here))
        if fn.endswith(".py")
    )


def _document_keys(source):
    """Collect required-key assumptions; optional document access must use get()."""
    tree = ast.parse(source)
    funcs = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    out = {}
    for fname, var, shape in SUBSCRIPTS:
        keys = set()
        for n in ast.walk(funcs[fname]) if fname in funcs else ():
            if not isinstance(n, ast.Subscript):
                continue
            if not (isinstance(n.value, ast.Name) and n.value.id == var):
                continue
            sl = n.slice
            sl = sl.value if isinstance(sl, getattr(ast, "Index", ())) else sl
            if isinstance(sl, ast.Constant) and isinstance(sl.value, str):
                keys.add(sl.value)
        out[shape] = (fname, var, keys)
    return out


def self_check(p, source=None):
    """The protocol against itself. Soundness, not conformance."""
    fail = []
    d = p.get("declarations") or {}

    relations = p.get("relations", {})
    if isinstance(relations, dict):
        contracts = relations.get("kind_contracts")
        if not isinstance(contracts, dict):
            fail.append("relations.kind_contracts: must be a mapping")
        else:
            for kind, ordered in (("distinct-from", False), ("feeds", True)):
                contract = contracts.get(kind)
                if (
                    not isinstance(contract, dict)
                    or contract.get("ordered") is not ordered
                ):
                    fail.append(
                        f"relations.kind_contracts.{kind}.ordered: must be {ordered}"
                    )

    for path in NEEDS:
        node = p
        for step in path:
            node = node.get(step) if isinstance(node, dict) else None
            if node is None:
                fail.append(
                    f"protocol is missing `{'.'.join(path)}`, which this checker reads"
                )
                break

    for path, shape in _walk_shapes(p):
        where = ".".join(path) or "<root>"
        if "required" in shape:
            target = (
                shape["document"] if isinstance(shape.get("document"), dict) else shape
            )
            known = sanc(target) if target is not shape else sanc(shape)
            req = shape["required"]
            if not isinstance(req, list):
                fail.append(f"{where}.required: not a list")
            else:
                bad = [k for k in req if k not in known]
                if bad:
                    fail.append(
                        f"{where}.required names {bad}, which "
                        f"{'the document' if target is not shape else 'the shape'} "
                        f"does not declare"
                    )
        if "one_of" in shape:
            choices = shape["one_of"]
            if not isinstance(choices, list):
                fail.append(f"{where}.one_of: not a list")
            else:
                bad = [k for k in choices if k not in sanc(shape)]
                if bad:
                    fail.append(
                        f"{where}.one_of names {bad}, which the shape does not declare"
                    )
        if "header_required" in shape:
            required = shape["header_required"]
            if not isinstance(required, list):
                fail.append(f"{where}.header_required: not a list")
                continue
            own = path[-1] if path else ""
            header = (shape.get("document") or {}).get(own)
            if not isinstance(header, dict):
                fail.append(
                    f"{where}.header_required: no `document.{own}` to resolve against"
                )
            else:
                bad = [k for k in required if k not in header]
                if bad:
                    fail.append(
                        f"{where}.header_required names {bad}, which "
                        f"`document.{own}` does not declare"
                    )

    declared = {k for k, v in d.items() if isinstance(v, dict) and "document" in v}
    kinds = set((d.get("document_types") or {}).get("kinds") or [])
    if kinds - declared:
        fail.append(
            f"document_types.kinds names {sorted(kinds - declared)}, "
            f"which declare no `document` shape"
        )
    if declared - kinds:
        fail.append(
            f"{sorted(declared - kinds)} declares a `document` shape but is not in "
            f"document_types.kinds"
        )

    if source is None:
        source = _package_source()
    for shape, (fname, var, keys) in _document_keys(source).items():
        required = (d.get(shape) or {}).get("required")
        if not isinstance(required, list):
            continue
        req = set(required)
        for k in sorted(keys - req):
            fail.append(
                f"{fname}() subscripts {var}['{k}'] but `{shape}.required` does not "
                f"promise it — subscript it and require it, or read it with .get()"
            )
    return fail


def missing_preconditions(d, doc, shape, name):
    """Report missing document or header keys before dependent checks."""
    fail = [
        f"document: missing required '{k}'"
        for k in d[shape]["required"]
        if k not in doc
    ]
    if not fail:
        fail = [
            f"header: missing required '{k}'"
            for k in d[shape]["header_required"]
            if k not in doc[shape]
        ]
    if fail:
        print()
        for f_ in fail:
            print(f"  FAIL  {f_}")
        print()
        print(f"{name}: NON-CONFORMING")
    return fail


def check(p, u, name):
    """Validate a universe and report conformance failures."""
    d = p["declarations"]
    fail, warn = [], []
    if missing_preconditions(d, u, "universe", name):
        return False
    ordering = u["universe"]["ordering_frame"]
    entry = p["composition"]["entry"]
    factors = u.get("factors") or []

    doc_shape = d["universe"]["document"]
    for label, used, allowed in [
        ("document", set(u), set(doc_shape)),
        ("universe header", set(u["universe"]), set(doc_shape["universe"])),
        *(
            [
                (
                    "universe overview",
                    set(u["universe"]["overview"]),
                    set(doc_shape["universe"]["overview"]),
                )
            ]
            if isinstance(u["universe"].get("overview"), dict)
            else []
        ),
        (
            "element",
            set().union(*[set(e) for e in u["elements"]]),
            (sanc(d["element"]) - {"<ordering-frame-id>"}) | {ordering},
        ),
        (
            "artifact",
            set().union(*[set(a) for a in u["artifacts"]]),
            sanc(d["artifact"]),
        ),
        ("frame", set().union(*[set(f) for f in u["frames"]]), sanc(d["frame"])),
        *(
            [("factor", set().union(*[set(k) for k in factors]), sanc(d["factor"]))]
            if factors
            else []
        ),
        (
            "relation_kind",
            set().union(*[set(r) for r in u["relation_kinds"]]),
            sanc(d["relation_kind"]),
        ),
    ]:
        bad = used - allowed
        print(f"  {label:18} unsanctioned={sorted(bad) or 'none'}")
        if bad:
            fail.append(f"{label}: unsanctioned {sorted(bad)}")
    if "overview" in u["universe"] and not isinstance(u["universe"]["overview"], dict):
        fail.append("universe overview: not a mapping of { covers, for, excludes }")

    roles = alts(d["frame"]["role"])
    set_bys = alts(d["frame"]["set_by"])
    for f in u["frames"]:
        if f.get("role") not in roles:
            fail.append(
                f"frame {f['id']}: role '{f.get('role')}' not in {sorted(roles)}"
            )
        if f.get("set_by") not in set_bys:
            fail.append(
                f"frame {f['id']}: set_by '{f.get('set_by')}' not in {sorted(set_bys)}"
            )
    ord_frames = [f["id"] for f in u["frames"] if f.get("role") == "ordering"]
    if ord_frames != [ordering]:
        fail.append(
            f"frames with role ordering {ord_frames} != header ordering_frame ['{ordering}']"
        )

    factor_set_bys = alts(d["factor"]["set_by"])
    for k in factors:
        if k.get("set_by") not in factor_set_bys:
            fail.append(
                f"factor {k.get('id')}: set_by '{k.get('set_by')}' "
                f"not in {sorted(factor_set_bys)}"
            )

    for kind, items in [("frame", u["frames"]), ("factor", factors)]:
        choices = d[kind]["one_of"]
        for i in items:
            present = [c for c in choices if c in i]
            if len(present) != 1:
                fail.append(
                    f"{kind} {i.get('id')}: declares {sorted(present) or 'none'} "
                    f"— exactly one of {choices} is required"
                )

    required_fail = []
    for key, items in [
        ("element", u["elements"]),
        ("artifact", u["artifacts"]),
        ("frame", u["frames"]),
        ("factor", factors),
        ("relation_kind", u["relation_kinds"]),
    ]:
        req = set(d[key]["required"])
        if key == "element":
            req = (req - {"<ordering-frame-id>"}) | {ordering}
        missing = [i.get("id") for i in items if req - set(i)]
        if missing:
            required_fail.append(f"{key}: missing required {missing}")
    if required_fail:
        fail.extend(required_fail)
        print()
        for f_ in fail:
            print(f"  FAIL  {f_}")
        print()
        print(f"{name}: NON-CONFORMING")
        return False

    kinds = alts(d["artifact"]["alias"]["kind"])
    for a in u["artifacts"]:
        al = a.get("alias", {})
        if al.get("kind") not in kinds:
            fail.append(
                f"{a['id']}: alias.kind '{al.get('kind')}' not in {sorted(kinds)}"
            )
        if al.get("kind") == "none" and "reason" not in al:
            fail.append(f"{a['id']}: alias.kind none without reason")

    entry_keys = sanc(entry)
    modes = alts(entry["mode"])
    strengths = alts(entry["strength"])
    declared_lists = set(d["artifact"]["composition"])
    for a in u["artifacts"]:
        members = set()
        for lst in a["composition"]:
            if lst not in declared_lists:
                fail.append(f"{a['id']}: composition list '{lst}' not declared")
            for it in a["composition"].get(lst) or []:
                member = it.get("element") if isinstance(it, dict) else it
                if isinstance(member, str):
                    if member in members:
                        fail.append(
                            f"{a['id']}: duplicate composition member '{member}'"
                        )
                    members.add(member)
                if isinstance(it, str):
                    continue
                if not isinstance(it, dict):
                    fail.append(f"{a['id']}/{lst}: entry is neither string nor object")
                    continue
                bad = set(it) - entry_keys
                if bad:
                    fail.append(
                        f"{a['id']}/{lst}/{it.get('element')}: "
                        f"unsanctioned entry keys {sorted(bad)}"
                    )
                if "mode" in it and (
                    not isinstance(it["mode"], str) or it["mode"] not in modes
                ):
                    fail.append(
                        f"{a['id']}/{it.get('element')}: "
                        f"mode '{it['mode']}' not in {sorted(modes)}"
                    )
                if "strength" in it and (
                    not isinstance(it["strength"], str)
                    or it["strength"] not in strengths
                ):
                    fail.append(
                        f"{a['id']}/{it.get('element')}: "
                        f"strength '{it['strength']}' not in {sorted(strengths)}"
                    )
                elif "strength" in it and it["strength"] != lst:
                    fail.append(
                        f"{a['id']}/{it.get('element')}: explicit strength "
                        f"'{it['strength']}' conflicts with composition list '{lst}'"
                    )

    for kind, items in [("frame", u["frames"]), ("factor", factors)]:
        for f in items:
            if "values" not in f:
                continue
            types = {type(v).__name__ for v in f["values"]}
            if types == {"str"}:
                continue
            if types == {"dict"}:
                for v in f["values"]:
                    if set(v) != {"id", "question"}:
                        fail.append(
                            f"{kind} {f['id']}: qualified value keys "
                            f"{sorted(v)} != [id, question]"
                        )
            else:
                fail.append(f"{kind} {f['id']}: mixed value types {sorted(types)}")

    frame_ids = {f["id"] for f in u["frames"]}
    factor_ids = {k["id"] for k in factors if "id" in k}

    def pred(p_, where):
        check_pred(
            p_,
            where,
            frame_ids,
            fail,
            forbidden=factor_ids,
            definitions={f["id"]: f for f in u["frames"]},
        )

    pred(u["empty_composition"]["when"], "empty_composition.when")
    for e in u["elements"]:
        if "gate" in e:
            pred(e["gate"], f"element {e['id']}.gate")
    for a in u["artifacts"]:
        if "disabled_when" in a:
            pred(a["disabled_when"], f"artifact {a['id']}.disabled_when")
        for lst in a["composition"]:
            for it in a["composition"].get(lst) or []:
                if isinstance(it, dict) and "when" in it:
                    pred(it["when"], f"{a['id']}/{it['element']}.when")

    for e in u["elements"]:
        if not re.fullmatch(r"singleton|per-[a-z-]+", str(e["cardinality"])):
            fail.append(
                f"element {e['id']}: cardinality '{e['cardinality']}' malformed"
            )
        if "closable" in e and not isinstance(e["closable"], bool):
            fail.append(f"element {e['id']}: closable not boolean")

    minted = {}
    for kind, items in [
        ("element", u["elements"]),
        ("artifact", u["artifacts"]),
        ("frame", u["frames"]),
        ("factor", factors),
    ]:
        shape = re.compile(CODE_PREFIX[kind] + CODE_TAIL)
        for i in items:
            if "code" not in i:
                continue
            c = i["code"]
            if not isinstance(c, str):
                fail.append(
                    f"{kind} {i.get('id')}: code {c!r} loaded as "
                    f"{type(c).__name__}, not a string"
                )
                continue
            if not shape.fullmatch(c):
                fail.append(
                    f"{kind} {i.get('id')}: code '{c}' does not match "
                    f"'{CODE_PREFIX[kind]}{CODE_TAIL}'"
                )
            if c in minted:
                fail.append(
                    f"{kind} {i.get('id')}: code '{c}' already carried by "
                    f"{minted[c][0]} {minted[c][1]}"
                )
            else:
                minted[c] = (kind, i.get("id"))

    ids = {e["id"] for e in u["elements"]}
    if len(ids) != len(u["elements"]):
        fail.append("duplicate element ids")
    for kind, items in [
        ("artifact", u["artifacts"]),
        ("frame", u["frames"]),
        ("factor", factors),
        ("relation_kind", u["relation_kinds"]),
    ]:
        declared = [i.get("id") for i in items]
        if len(set(declared)) != len(declared):
            fail.append(f"duplicate {kind} ids")
    questions = [e["question"] for e in u["elements"]]
    if len(set(questions)) != len(questions):
        fail.append("duplicate element questions")
    req_entry = set(p["composition"]["entry"]["required"])
    composed = set()
    for a in u["artifacts"]:
        for lst in a["composition"]:
            for it in a["composition"].get(lst) or []:
                if not isinstance(it, dict):
                    composed.add(it)
                    continue
                if req_entry - set(it):
                    fail.append(
                        f"{a['id']}/{lst}: composition entry missing required "
                        f"{sorted(req_entry - set(it))}"
                    )
                    continue
                composed.add(it["element"])
    if composed - ids:
        fail.append(f"composition refs unknown elements: {sorted(composed - ids)}")
    edge_keys = sanc(p["relations"]["edge"])
    req_edge = set(p["relations"]["edge"]["required"])
    edges = []
    for r in u["relations"]:
        bad = set(r) - edge_keys
        if bad:
            fail.append(
                f"relation {r.get('from')}->{r.get('to')}: "
                f"unsanctioned edge keys {sorted(bad)}"
            )
        if req_edge - set(r):
            fail.append(
                f"relation {r.get('from')}->{r.get('to')}: "
                f"missing required {sorted(req_edge - set(r))}"
            )
            continue
        edges.append(r)

    known = ids | {a["id"] for a in u["artifacts"]}
    dangling = [
        (r["from"], r["to"])
        for r in edges
        if r["from"] not in known or r["to"] not in known
    ]
    if dangling:
        fail.append(f"dangling relation refs: {dangling}")
    declared_kinds = {k["id"] for k in u["relation_kinds"]}
    contracts = p.get("relations", {}).get("kind_contracts", {})
    for kind in u["relation_kinds"]:
        where = f"relation kind '{kind.get('id')}'"
        if not isinstance(kind.get("ordered"), bool):
            fail.append(f"{where}.ordered: must be a boolean")
            continue
        if "phrasing" in kind:
            phrasing = kind["phrasing"]
            location = f"{where}.phrasing"
            if not isinstance(phrasing, dict):
                fail.append(f"{location}: must be a mapping")
            else:
                expected = {"forward", "reverse"} if kind["ordered"] else {"forward"}
                missing = expected - phrasing.keys()
                extra = phrasing.keys() - expected
                if missing:
                    fail.append(f"{location}: missing required {sorted(missing)}")
                if extra:
                    fail.append(f"{location}: unexpected keys {sorted(extra, key=str)}")
                for direction in sorted(expected & phrasing.keys()):
                    value = phrasing[direction]
                    if not isinstance(value, str) or not value.strip():
                        fail.append(
                            f"{location}.{direction}: must be a nonblank string"
                        )
        contract = contracts.get(kind.get("id"))
        if isinstance(contract, dict) and kind.get("ordered") is not contract.get(
            "ordered"
        ):
            fail.append(
                f"relation kind '{kind.get('id')}': ordered must be "
                f"{contract.get('ordered')} under its shared contract"
            )
    undeclared = {r["kind"] for r in edges} - declared_kinds
    if undeclared:
        fail.append(f"undeclared relation kinds in use: {sorted(undeclared)}")

    ordered = {k["id"] for k in u["relation_kinds"] if k.get("ordered")}
    adj = {}
    for r in edges:
        if r["kind"] in ordered:
            adj.setdefault(r["from"], set()).add(r["to"])

    def reaches(start, target, seen=None):
        seen = seen if seen is not None else set()
        for nxt in adj.get(start, ()):
            if nxt == target:
                return True
            if nxt not in seen:
                seen.add(nxt)
                if reaches(nxt, target, seen):
                    return True
        return False

    for r in edges:
        if r["kind"] not in ordered:
            continue
        if (
            r["to"] == r["from"] or reaches(r["to"], r["from"])
        ) and "legality" not in r:
            fail.append(
                f"relation {r['from']}->{r['to']} ({r['kind']}) "
                f"is on a cycle and declares no legality"
            )

    unused = declared_kinds - {r["kind"] for r in edges}
    if unused:
        warn.append(f"relation kinds declared but unused: {sorted(unused)}")
    orphans = ids - composed
    if orphans:
        warn.append(f"elements with no host artifact: {sorted(orphans)}")

    print()
    print(
        f"  counts: {len(u['elements'])} elements, {len(u['artifacts'])} artifacts, "
        f"{len(u['frames'])} frames, {len(factors)} factors, "
        f"{len(u['relations'])} relations, "
        f"{len(u['relation_kinds'])} relation kinds"
    )
    print()
    for w in warn:
        print(f"  NOTE  {w}")
    for f_ in fail:
        print(f"  FAIL  {f_}")
    print()
    print(f"{name}: {'NON-CONFORMING' if fail else 'CONFORMS'}")
    return not fail


def check_guidance(p, g, universes, name):
    """Validate guidance against its declared universe."""
    d = p["declarations"]
    fail, warn = [], []
    if missing_preconditions(d, g, "guidance", name):
        return False

    doc_shape = d["guidance"]["document"]
    for label, used, allowed in [
        ("document", set(g), set(doc_shape)),
        ("guidance header", set(g["guidance"]), set(doc_shape["guidance"])),
        (
            "guidance_kind",
            set().union(*[set(k) for k in g["guidance_kinds"]]),
            sanc(d["guidance_kind"]),
        ),
    ]:
        bad = used - allowed
        print(f"  {label:18} unsanctioned={sorted(bad) or 'none'}")
        if bad:
            fail.append(f"{label}: unsanctioned {sorted(bad)}")

    req_kind = set(d["guidance_kind"]["required"])
    missing = [k.get("id") for k in g["guidance_kinds"] if req_kind - set(k)]
    if missing:
        fail.append(f"guidance_kind: missing required {missing}")

    guides = g["guidance"].get("guides")
    u = universes.get(guides)
    if u is None:
        fail.append(f"guides '{guides}' resolves to no universe beside this document")
        print()
        print(f"{name}: NON-CONFORMING")
        for f_ in fail:
            print(f"  FAIL  {f_}")
        return False
    if u["universe"].get("conforms_to") != g["guidance"].get("conforms_to"):
        fail.append(
            f"conforms_to '{g['guidance'].get('conforms_to')}' does not match "
            f"guided universe '{u['universe'].get('conforms_to')}'"
        )

    element_ids = {e["id"] for e in u["elements"]}
    artifact_ids = {a["id"] for a in u["artifacts"]}
    frame_ids = {f["id"] for f in u["frames"]}
    factor_ids = {k["id"] for k in (u.get("factors") or []) if "id" in k}
    kinds = {k["id"]: k for k in g["guidance_kinds"]}
    sources = set(g.get("sources") or {})
    entry_keys = sanc(d["guidance_entry"])
    req_entry = set(d["guidance_entry"]["required"])

    total = 0
    for section, valid in [
        ("elements", element_ids),
        ("artifacts", artifact_ids),
        ("factors", factor_ids),
    ]:
        for key, entries in (g.get(section) or {}).items():
            if key not in valid:
                fail.append(
                    f"{section}.{key}: resolves to no declared id in '{guides}'"
                )
            for i, it in enumerate(entries or []):
                total += 1
                where = f"{section}.{key}[{i}]"
                if not isinstance(it, dict):
                    fail.append(f"{where}: entry is not an object")
                    continue
                bad = set(it) - entry_keys
                if bad:
                    fail.append(f"{where}: unsanctioned entry keys {sorted(bad)}")
                if req_entry - set(it):
                    fail.append(
                        f"{where}: missing required {sorted(req_entry - set(it))}"
                    )
                    continue
                kind = kinds.get(it["kind"])
                if kind is None:
                    fail.append(f"{where}: kind '{it['kind']}' not in guidance_kinds")
                elif kind.get("sourced") and it["source"] == "asserted":
                    fail.append(
                        f"{where}: kind '{it['kind']}' is sourced "
                        f"and may not be satisfied by asserted"
                    )
                if it["source"] != "asserted" and it["source"] not in sources:
                    fail.append(f"{where}: source '{it['source']}' not in sources")
                if "when" in it:
                    check_pred(
                        it["when"],
                        f"{where}.when",
                        frame_ids | factor_ids,
                        fail,
                        noun="frame or factor",
                        definitions={
                            f.get("id"): f
                            for f in u["frames"] + (u.get("factors") or [])
                        },
                    )

    unused = sources - {
        it["source"]
        for section in ("elements", "artifacts", "factors")
        for entries in (g.get(section) or {}).values()
        for it in (entries or [])
        if isinstance(it, dict) and "source" in it
    }
    if unused:
        warn.append(f"sources declared but uncited: {sorted(unused)}")
    unsourced = sorted(k for k, v in (g.get("sources") or {}).items() if "url" not in v)
    if unsourced:
        warn.append(f"sources with no url, needing verification: {unsourced}")
    bare = sorted(element_ids - set(g.get("elements") or {}))
    if bare:
        warn.append(f"elements with no guidance: {bare}")
    bare_factors = sorted(factor_ids - set(g.get("factors") or {}))
    if bare_factors:
        warn.append(f"factors with no guidance: {bare_factors}")

    print()
    print(
        f"  counts: {total} entries over {len(g.get('elements') or {})} elements, "
        f"{len(g.get('artifacts') or {})} artifacts and "
        f"{len(g.get('factors') or {})} factors, "
        f"{len(sources)} sources, {len(kinds)} guidance kinds"
    )
    print()
    for w in warn:
        print(f"  NOTE  {w}")
    for f_ in fail:
        print(f"  FAIL  {f_}")
    print()
    print(f"{name}: {'NON-CONFORMING' if fail else 'CONFORMS'}")
    return not fail


def mint(kind, count, doc_paths=()):
    """Mint random YAML-safe codes without collisions in the supplied documents."""
    taken = set()
    for path in sorted(doc_paths):
        with open(path) as stream:
            doc = yaml.safe_load(stream) or {}
        for section in ("elements", "artifacts", "frames", "factors"):
            for item in doc.get(section) or []:
                if isinstance(item, dict) and isinstance(item.get("code"), str):
                    taken.add(item["code"])
    out = []
    while len(out) < count:
        code = CODE_PREFIX[kind] + "".join(secrets.choice(ALPHABET) for _ in range(4))
        if code not in taken:
            taken.add(code)
            out.append(code)
    return out
