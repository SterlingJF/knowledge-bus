# Protocol Changelog

Conformance-contract history. Software releases are tracked in the [release changelog](../CHANGELOG.md).

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
