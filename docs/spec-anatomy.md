# Spec anatomy

A spec is two files: the spec itself, which the checker enforces, and a guidance file, which is advisory.

## The two-file pair

A spec ships as a pair: the spec file, which the checker enforces, and a guidance file, which is
advisory by rule. The spec carries only what something reads, and must stay valid with no guidance
file present. The shipped pair to read: `universes/product-development/universe.kbp.yaml` and
`type-guidance.kbp.yaml`. In the files themselves the format's term for a spec is `universe` —
same thing, the format's internal name.

## What each key declares

| Key in the file | Prose name | What it declares |
| --- | --- | --- |
| `universe` | the header | id, version, `conforms_to`, ordering frame — what this spec is and which format version it obeys. |
| `elements` | questions | units of conclusion, each identified by the question its content answers. |
| `artifacts` | document types | compositions over elements, each identified by the decision or action it enables for a named actor. |
| `frames` | indexing dimensions | dimensions the spec is indexed by; a frame can select, promote to core, gate an element, disable an artifact, or return empty. |
| `factors` | declared-only dimensions | dimensions the spec declares and wires into nothing — whatever consumes the spec reads and sets them. |
| `relation_kinds`, `relations` | edge types, edges | typed edges over element and artifact identities. |
| `statuses` | answer lifecycle | the statuses an answer (one assertion by a party at a time) can carry. |
| `empty_composition` | honest-empty rule | the frame condition under which a document legitimately composes nothing. |

The guidance file carries its own five: `guidance` (header), `guidance_kinds`, `sources`, and per-`elements` / per-`artifacts` entries.

## Identity rules

An element is the question its content answers — two candidates answering the same question are
one element. A document type is the decision or action it enables for a named actor — identity is
`(action, actor)`, with timing to break ties. These rules are the collision tests that keep a spec
from accumulating duplicates: every proposed addition is checked against every declared identity
and ruled *sharpen existing / new / refused*.

## Codes

Every declaration carries a 5-character code, kind-prefixed, from an alphabet omitting `i l o u`
so no code parses as a bool, null, or number. Codes survive renames — an id is free to change; a
code is never reused or reassigned. Mint new ones with `just mint <kind>`.

## The split rule

A value belongs in the spec because something reads it; everything else belongs in guidance:
conventions (which must cite a registered source), pitfalls, heuristics, what an honest empty
answer means, refresh cadence, and boundary claims. Every guidance kind except convention may be
asserted — but must say so.
