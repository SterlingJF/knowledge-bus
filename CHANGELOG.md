# Changelog

Format versions. The built-in spec carries its own version, tracked separately.

## 0.5.x — first public release

- Packaged as a Claude Code plugin: `/kb-ingest`, `/kb-evolve`, `/kb-check`, `/kb-uncover-question`, `/kb-uncover-decision`.
- Format unchanged at 0.5 draft.

## 0.5 — draft

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
