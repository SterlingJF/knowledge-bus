# Protocol Changelog

Conformance-contract history. Software releases are tracked in the [release changelog](../CHANGELOG.md).

## 0.8 — draft

- The universe header may declare `terms`: a list of `{ term, means }`, the universe's own words with one fixed meaning in its definitions.
- Require both fields as nonblank strings, no other fields, and each term unique within the universe, compared case-insensitively.
- Terms carry no structure and do not affect correspondence between universes, which remains by question.
- Rename the universe key `empty_composition` to `no_artifact`, with the same shape: `{ when: <frame-predicate> }`. When every frame it names matches, no artifact is needed. Prose that said "return the empty composition" now says "no artifact is needed".
- Key a relation edge gate by the universe's own frames: `{ <frame-id>: <frame-value>, latency: <duration> }`. Each value takes a frame predicate's value forms, and a single value may be written bare. `latency` stays reserved for a duration, written as one nonblank string, and no frame may be named `latency`. The checker now refuses a gate key that is not a declared frame or `latency`, a value that frame does not declare, a `latency` that is not a nonblank string, and a frame named `latency`.
- The exchange `compose` step takes the universe's selection frames, if any, in place of `audience`.

Declarations may name `kbp/0.8`, or `kbp/0.7` through `protocol.accepts`. A `kbp/0.7` document is checked as 0.7, so `terms` is unsanctioned there, the key is still `empty_composition`, edge gates are not checked, and a frame may be named `latency`. `header_since` records the version that introduced a header key; `renamed` records a document key's earlier name and the version that renamed it; `reshaped` records a field's earlier shape and the version that changed it.

Breaking for `kbp/0.8` documents only: write `no_artifact`, and key edge gates by declared frames. A `kbp/0.8` document using `empty_composition`, or a `kbp/0.7` document using `no_artifact`, is refused with a message naming the right key.

## 0.7 — draft

- Relation kinds may declare plain-text phrasing: one forward phrase for unordered kinds, or forward and reverse phrases for ordered kinds.
- Validate the complete phrasing shape and nonblank values; require boolean ordering.
- Choose copy by displayed subject. Phrasing preserves shared meaning and attached restrictions.

Declarations must name `kbp/0.7` exactly. Phrasing remains optional.

## 0.6 — draft

- Define true, false, and unknown predicate results, with AND across dimensions and facets and OR across alternatives. Invalid local values are errors; missing or unresolved context is unknown.
- Specify artifact suppression and element-gate precedence before member evaluation.
- Distinguish conditional core requiredness from conditional situational availability. A false core condition leaves the member situationally available rather than excluding it.
- Require unique composition membership and agreement between explicit strength and the containing list.
- Define shared meanings and ordering for `distinct-from` and `feeds`, without transitive inference or generated edges.

Breaking: declarations must name `kbp/0.6` exactly and satisfy the stricter predicate, composition, and shared-relation rules. Updating `conforms_to` alone does not establish conformance.

## 0.5

The checker validates the protocol against itself before any document, and an unsound protocol
stops the run. One convention binds the checker: a key the code subscripts must be a key the
protocol requires, checked before anything reads it.

## 0.4

Factors — a top-level universe declaration beside `frames:` that the universe wires into nothing,
left for whatever consumes the universe to factor in. Short codes on every declaration: stable,
unordered, machine-facing handles, prefixed by kind. Breaking, since `code` became required.

## 0.3

Frames declare `role` and `set_by` in place of `scope`. Five runtime-context frames removed as
passengers. The `uptake` frame replaced `exchange` with question-qualified values. The universe
header gained an `overview`.

## 0.2

Type guidance as a second document type, dispatched on the file's top-level header key.

## 0.1

Initial primitives — concepts, identity, composition, relations, instances, guidance, exchange,
conformance.
