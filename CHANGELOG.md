# Changelog

Software releases. See [Protocol Changelog](protocol/CHANGELOG.md) for conformance-contract history and [Versioning](docs/versioning.md) for the release process.

## 0.10.0 — unreleased

Bundled protocol: `kbp/0.9`.

### Skill `kb-evolve`

- Have `kb-evolve` show proposed changes as one table per universe spec, with current text, proposed text, evidence and reason, and take answers by row number.
- Have `kb-evolve` show each change before and after once written, and record each run in `.knowledge-bus/evolve-log.md`.
- Add `kb-evolve` guidance on declaring factors.

### Protocol kbp/0.9

- A universe spec with no element declares no ordering frame. A universe spec with elements still declares exactly one ordering frame.
- Guidance keyed to a factor is advice on presenting a document. A consumer may apply the advice to the documents of another universe spec. A factor still selects nothing.
- Documents declaring `kbp/0.8` or `kbp/0.7` still pass. A factor-only universe spec drops its placeholder ordering frame only when moving to `kbp/0.9`.

### Checker

- Refuse an ordering frame in a `kbp/0.9` universe spec with no element: the ordering frame attaches to nothing.
- Add `kbp --card <kind>`: prints the card for one document type, as JSON or with `--format markdown`. See [Document Type Card](docs/document-type-card.md).
- Add `kbp --kinds`: lists every document type with its other names, purpose, users and timing, and prints `overview.covers` and `overview.for` for each universe spec; with several universe specs, prints one group per universe spec.
- Have `kbp --kinds` list every factor with its question and number of guidance notes.
- Add "How to present it" to the card: factor guidance as advice on presenting the document, in one labelled block for each universe spec in scope that declares a factor.
- Refuse a universe spec without an ordering frame in `--inspect` and `--explore`, as not renderable.
- Add a test that copies every universe spec in `universes/` into one folder and reports each id declared by two or more universe specs.
- Add `.knowledge-bus/workspace.yaml`, the settings file for a Knowledge Bus folder. Its `from_parent` key lists universe specs of the parent folder; every `kbp` command and skill applies the listed universe specs beside the folder's own universe specs. See [Nested Folders](docs/knowledge-bus-directory.md#nested-folders).

### Codebase-recordkeeping universe 0.1 and guidance 0.1

- Add the codebase-recordkeeping universe spec for the written documents of a codebase, from a survey of public repositories and graded sources. See [Code Repository Universe Research](docs/research-code-repository-universe-2026-10-08.md).
- Declare 20 document types, from the README and licence file to change descriptions, release notes and agent instructions, with element questions, compositions, relations and six terms.
- Order elements by the `step` frame, from choosing a project to publishing a release; add frames for issue kind, documentation task, contributor assertion and repository state, and factors for release notes, commit messages and version numbers.
- Add type guidance with sourced advice, placements, practices, disputes and distinctions for each document type.
- Add recognition situations for the codebase-recordkeeping frame and factor values.
- Bundle each universe spec in `universes/`, with its guidance, into `kb-ingest` and the agent packages; run the release and package checks on each universe spec.

### Eval report

- Name each run in `evals/runs.yaml` by its run id.
- Add `just evals-report --run-folders <folder>`: summarises each listed run from the folder named for its run id at any depth under `<folder>`. Without the option, `just evals-report` builds from the committed summaries.

## 0.9.0

Bundled protocol: `kbp/0.8`.

### Protocol

- Add optional universe `terms`: the universe's own words, each with one fixed meaning.
- Rename the universe key `empty_composition` to `no_artifact`, with the same shape. Documents declaring `kbp/0.7` are still accepted and checked as 0.7.
- Key relation edge gates by the universe's own frames, with `latency` reserved for a duration. The checker refuses undeclared gate keys and values, a `latency` that is not a nonblank string, and a frame named `latency` in `kbp/0.8` documents.
- The exchange `compose` step takes the universe's selection frames, if any, in place of `audience`.

### Product-development universe 0.9 and guidance 0.8

- Rewrite every artifact enablement and element question for plain, single-ask reading, with no two overlapping.
- Add the `experiment-plan` artifact and the `brand-character` element; declare five terms.
- Revise compositions, gates, frames and relations, and add boundary guidance for each new `distinct-from` edge.
- Update guidance to the new wording, downgrade claims their sources do not establish, and add notes where an empty answer would be ambiguous.

### Explorer

- Show a universe's terms and a limits line in the overview, and each guidance note's kind and source.
- Name frame entries "Values", use "When applicable" for situational members, and say "When to skip the artifact" for the no-artifact rule.
- Hide `distinct-from` edges until a card is selected, keeping routes unchanged; keep hidden edges, counts and labels out of the tab order and accessibility tree.
- Keep the detail panel beside its subject at the map's edges.
- Accept exactly the edge gates the checker accepts: draw the frames a gate names, and no longer refuse `latency`.
- Show the product-development map in the README, with a check that fails when the definitions or Explorer code change and the map is not regenerated.

### Skills

- Extend `kb-explore` to explain a universe.
- Have skills confirm the request first, show changes as current and proposed text, give their own view with each question, and never follow instructions in sources.
- Update `kb-check` and `kb-evolve` for `kbp/0.8`: terms, `no_artifact` and frame-keyed gates.

### Evals

- Add a vendor-neutral eval spec (`evals/`) with Claude, Codex and Jev adapters, and its tooling (`tools/evals/`): universe and skills slices with deterministic, decision-model and judgment tiers, set-level checks and a filing test, with generated Claude plugin-eval cases.
- Add a recognition check for frame values on real, de-identified situations (`evals/situations/`).
- Add `just evals-play` to play agent-behaviour scenarios with a scripted owner and grade them.
- Add `just evals-report` to build `evals/report.md` from the runs in `evals/runs.yaml`.
- Add `tools/evals/packet.py` for grading in the Codex desktop app.

### Moving from kbp/0.7

Compatibility: documents declaring `kbp/0.7` still pass. To move one to `kbp/0.8`, rename `empty_composition` to `no_artifact`, check that every edge gate key is a declared frame or `latency` and that no frame is named `latency`, and update `conforms_to` in both the universe and its guidance.

## 0.8.0

Bundled protocol: `kbp/0.7`.

Versions 0.6.0 and 0.7.0 were never published; their changes ship here.

- Remove the `working-note` artifact from product-development universe `0.8`.
- Add `kb-explore` for read-only universe inspection and offline Explorer artifacts.
- Add `@knowledge-bus/explorer`, a dependency-free universe viewer with a self-contained offline HTML artifact and a dual-theme SVG export.

### Relation phrasing (`kbp/0.7`)

- Support optional universe-authored relation phrasing, with one phrase for unordered kinds and two for ordered kinds.
- Reject incomplete phrasing, invalid values and nonboolean relation ordering with field-specific diagnostics.
- Product-development universe 0.7 supplies "Context from" / "Context for" for `presupposes`, preserving all six edges.
- Guidance 0.7 updates its protocol reference; advisory content is unchanged.

### Protocol and universe updates (`kbp/0.6`)

- Define shared `distinct-from` and `feeds` relation contracts.
- Add context validation and three-valued predicate evaluation, including conditional composition and artifact suppression.
- Reject duplicate composition members, conflicting or invalid strengths, invalid predicate values and facets, and incompatible shared-relation ordering.
- Bundle product-development universe and guidance revisions `0.6`: correct feed direction and North Star ownership, refine advice and source attribution, and document the universe evolution.
- Refresh self-contained skills and native agent packages with the updated checker and definitions.

### Compatibility

- Protocol matching remains exact: documents declaring `kbp/0.5` or `kbp/0.6` do not conform to `kbp/0.7`. Review declarations against the new rules before updating `conforms_to`.
- Some declarations accepted by the previous checker are now rejected by the validation rules listed above.
- Missing context evaluates as unknown, not false. A false condition on a core member leaves it situationally available; a false condition on a situational member excludes it. Element gates and artifact suppression are evaluated separately.

## 0.5.0

Bundled protocol: `kbp/0.5`.

### Changes

- Install native Claude Code, Codex, Pi, and OpenCode packages from npm.
- Install individual self-contained skills from the default branch or an explicit tag.
- Publish isolated `@knowledge-bus` agent packages through npm trusted publishing and native distribution channels.
- Keep the checker, protocol, universes, and agent adapters independently usable.

## Historical Release Notes

The previous changelog labeled the following entry "0.5.x — first public release" without identifying an exact release version. That label is preserved here rather than treated as a precise release record.

- Packaged as a Claude Code plugin: `/kb-ingest`, `/kb-evolve`, `/kb-check`, `/kb-uncover-question`, `/kb-uncover-decision`.
- Format unchanged at 0.5 draft.
