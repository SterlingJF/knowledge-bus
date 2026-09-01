# knowledge-bus

Convert a scattered knowledge base into validated specs that agents can consume.

[![ci](https://github.com/SterlingJF/knowledge-bus/actions/workflows/ci.yml/badge.svg)](https://github.com/SterlingJF/knowledge-bus/actions/workflows/ci.yml)

Scattered docs fail humans and agents the same way: plenty of information, no orientation. Humans
search stale files; agents re-read conflicting docs, bloat their context, and still miss
the finer points.

knowledge-bus restructures the folder into a spec: a registry of the questions your domain has to answer, each
with its sourced answers. Tools like [Understand Anything](https://github.com/Egonex-AI/Understand-Anything) already try to solve the current-state problem;
a knowledge-bus spec carries direction: what's answered, what's open, what to ask next. Fewer tokens to
ground an agent; less effort to orient a human.

## Install the plugin

```bash
/plugin marketplace add SterlingJF/knowledge-bus
/plugin install knowledge-bus
```

Or clone this repo and use the checker alone, no plugin:

```bash
uv run kbp
```

## Quick start

1. Run `/kb-ingest` on a folder of notes or docs — it surveys, interviews you, and writes a spec to `<folder>-spec/` beside it.
2. Review the coverage report: contested content first, then stale, refused, and gaps.
3. Run `/kb-check` after any edit.

## Commands

| Command | What it does |
| --- | --- |
| `/kb-ingest` | Converts a folder of scattered docs into a validated spec with sourced answers. |
| `/kb-evolve` | Adds a document type a spec lacks, or re-examines one before it becomes load-bearing. |
| `/kb-check` | Validates spec files and reports each failure with its registered reason. |
| `/kb-uncover-question` | Elicits a clear, distinct, non-overlapping question a spec should declare. |
| `/kb-uncover-decision` | Elicits a decision and the constraints that were live when it was made. |

## How it works

- **Identity by question.** Documents (artifacts) are decomposed into their main sections (elements). Each artifact
  and element is grouped and normalized by the questions it answers within the context of a domain (universe). Agents load
  answers keyed by question instead of re-reading source docs.
- **The spec/guidance split.** A universe spec holds the domain entities and relational mappings. A separate companion
  file provides contextual guidance for agent (and human) reasoning.
- **Mechanical validation.** 17 machine-checked validity clauses, plus a test corpus where every registered refusal
  has a file that must fail for exactly that reason.

## The built-in example

The built-in spec covers product development: 58 questions across 19 document types — strategy
canvas, lean canvas, decision record, design doc — with 45 relations between them. Its guidance
file carries 194 entries citing 51 registered sources (Pichler, Moore, Porter, Osterwalder,
Maurya, ...). A product or idea knowledge base can ingest against it today. Niche or
function-specific domains can still use it as a starting point.

See [docs/adapting-the-example.md](docs/adapting-the-example.md) for making it yours.

## Limits

- Skills are tested against Claude Opus 5 at high reasoning effort; other models are untested.
- Claude-native. The checker CLI runs anywhere; the skills are best-effort outside Claude models.
- The checker validates spec and guidance files; answers ship in a documented shape it does not yet check.
- The validation step requires [`uv`](https://docs.astral.sh/uv/).

## Docs

- [walkthrough.md](docs/walkthrough.md) — one messy folder through one ingest, start to finish.
- [how-ingest-works.md](docs/how-ingest-works.md) — what actually happens when `/kb-ingest` runs on a messy folder.
- [spec-anatomy.md](docs/spec-anatomy.md) — what is inside a spec file.
- [validation.md](docs/validation.md) — what the checker verifies, and what it refuses.
- [adapting-the-example.md](docs/adapting-the-example.md) — how to get a spec for your domain.
- [design-notes.md](docs/design-notes.md) — why identity-by-question, the split, and stable codes.

## Roadmap

Planned measurement, not claims:

- Round-trip context loss — express, regenerate, diff: how much of the reasoning survives?
- Authoring reliability — given a spec, its guidance, and a situation, does an agent produce a conforming document?
- Refusal trust — does an agent decline a question it has no basis for, or fill the field?
- Answer-file validation — extend the checker to the `answers.yaml` shape ingest writes.

## License

MIT. Issues welcome; PRs by discussion first.
