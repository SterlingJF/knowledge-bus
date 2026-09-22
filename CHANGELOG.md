# Changelog

Software releases. See [Protocol Changelog](protocol/CHANGELOG.md) for conformance-contract history and [Versioning](docs/versioning.md) for the release process.

## 0.8.0

Bundled protocol: `kbp/0.7`.

- Remove the `working-note` artifact from product-development universe `0.8`.
- Add `kb-explore` for read-only universe inspection and offline Explorer artifacts.
- Add `@knowledge-bus/explorer`, a dependency-free universe viewer with a self-contained offline HTML artifact and a dual-theme SVG export.

## 0.7.0

Bundled protocol: `kbp/0.7`.

- Support optional universe-authored relation phrasing, with one phrase for unordered kinds and two for ordered kinds.
- Reject incomplete phrasing, invalid values and nonboolean relation ordering with field-specific diagnostics.
- Product-development universe 0.7 supplies "Context from" / "Context for" for `presupposes`, preserving all six edges.
- Guidance 0.7 updates its protocol reference; advisory content is unchanged.

## 0.6.0 — unreleased

Bundled protocol: `kbp/0.6`.

### Protocol and universe updates

- Define shared `distinct-from` and `feeds` relation contracts.
- Add context validation and three-valued predicate evaluation, including conditional composition and artifact suppression.
- Reject duplicate composition members, conflicting or invalid strengths, invalid predicate values and facets, and incompatible shared-relation ordering.
- Bundle product-development universe and guidance revisions `0.6`: correct feed direction and North Star ownership, refine advice and source attribution, and document the universe evolution.
- Refresh self-contained skills and native agent packages with the updated checker and definitions.

### Compatibility

- Protocol matching remains exact: documents declaring `kbp/0.5` do not conform to `kbp/0.6`. Review declarations against the new rules before updating `conforms_to`.
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
