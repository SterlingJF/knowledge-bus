# Knowledge Bus

A protocol for structuring knowledge so humans and AI agents can work from the same understanding.

[![Release](https://img.shields.io/github/v/release/SterlingJF/knowledge-bus?label=release)](https://github.com/SterlingJF/knowledge-bus/releases/latest)
[![CI](https://github.com/SterlingJF/knowledge-bus/actions/workflows/ci.yml/badge.svg?branch=main&event=push)](https://github.com/SterlingJF/knowledge-bus/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/SterlingJF/knowledge-bus)](LICENSE)

Define the questions your notes and documents need to answer, how their contents connect, and the decisions and actions they should support. Use those expectations to guide new work, review contributions, and exchange knowledge.

## What is Knowledge Bus?

Knowledge Bus is a protocol for describing what knowledge means and how it fits together. It gives people and AI agents a common reference for writing, reading, and using notes and documents.

For a project, subject, or area of responsibility, you can define:

- the questions the content needs to answer;
- the decisions or actions each document supports;
- the information required for that purpose;
- how information connects across documents;
- which requirements change with the audience or situation;
- guidance for answering well;
- who supplied an answer, when it was established, and whether it is settled or disputed.

These definitions can guide a personal notebook, a shared project folder, or documentation across teams. They give contributors clear expectations and help later readers understand the thinking behind the content.

A template gives a document its sections. Knowledge Bus also defines what those sections mean, why they belong, and how their contents relate to other documents. Different documents can refer to the same knowledge, reducing the need to repeat the thinking or maintain separate copies.

Tools such as [Understand Anything](https://github.com/Egonex-AI/Understand-Anything) analyze existing material to explain its contents and connections. Knowledge Bus lets people and agents agree on the questions the content needs to answer, what belongs in each document, and how the pieces relate—even before the first document is written. Those same definitions can then guide new contributions and help interpret existing material.

## Where It Helps

- **Personal notes:** decide what you want to capture and keep enough context to understand it later.
- **Everyday projects:** record decisions, unanswered questions, and the information someone needs to take over.
- **Team documentation:** give contributors shared expectations across briefs, plans, decisions, and handovers.
- **AI collaboration:** give agents explicit definitions and guidance to follow when asking questions, drafting, or reviewing.
- **Knowledge exchange:** describe how information can move between people and tools while retaining its meaning and context.

You can adopt an existing set of definitions or develop one for your own work. The included product-development example provides a starting point; the protocol supports other subjects and uses.

## Features

- **Knowledge definitions** — identify each piece of knowledge by the question it answers, so different headings and filenames do not give it different meanings.
- **Document composition rules** — define the decision or action a document supports, then specify the information someone needs to make that decision or take that action.
- **Authoring guidance** — attach advice and its sources to relevant definitions, keeping recommendations separate from requirements.
- **Attribution and history** — record who stated something, who is bound by it, its status, and when it was established. Preserve earlier versions when new assertions replace them.
- **Knowledge exchange rules** — define how to share knowledge between different structures while preserving its meaning, source, and status. Keep disagreements visible for the receiver to resolve.
- **Product-development starter** — adopt or adapt definitions for 19 document types, including briefs, plans, and decision records.
- **Agent skills** — clarify questions and check for overlap, recover a decision's reasoning and the conditions for reconsidering it, and add or re-examine document types.
- **Folder ingestion** — map existing notes to sourced answers, surface conflicts for your review, and report gaps without changing the originals.
- **Conformance checker** — check definition and guidance files for missing declarations, unresolved references, and other structural errors.

## The Built-in Example

The included product-development definitions cover 58 questions across 19 document types, including strategy canvases, lean canvases, decision records, and design documents. They declare 45 relationships between those types and their contents.

The companion guidance provides 194 entries citing 51 registered sources, including Pichler, Moore, Porter, Osterwalder, and Maurya.

Use this as a starting point for your own work. You can adopt it, trim it, extend it, or develop a different set of definitions.

See [Adapting the Example](docs/adapting-the-example.md).

Definitions live in `.knowledge-bus/` inside the folder they describe. Checking from a nested directory uses the nearest `.knowledge-bus/` directory. See [Knowledge Bus Directory](docs/knowledge-bus-directory.md) for discovery and write rules.

## Installation

Requires your agent's CLI and Node.js/npm. Checker-backed skills also require [uv](https://docs.astral.sh/uv/getting-started/installation/) and Python compatible with the [checker package requirement](checker/pyproject.toml).

### Claude Code

In Claude Code chat:

```text
/plugin marketplace add SterlingJF/knowledge-bus
/plugin install knowledge-bus@knowledge-bus
```

Or in your terminal:

```sh
claude plugin marketplace add SterlingJF/knowledge-bus
claude plugin install knowledge-bus@knowledge-bus
```

### Codex

In your terminal:

```sh
codex plugin marketplace add SterlingJF/knowledge-bus
codex plugin add knowledge-bus@knowledge-bus
```

Start a new session after installation.

### Pi

In your terminal:

```sh
pi install npm:@knowledge-bus/pi@latest
```

Run `/reload` in an existing Pi chat to load the skills.

### OpenCode

In your terminal:

```sh
opencode plugin @knowledge-bus/opencode@latest
```

Start a new session after installation. Add `--global` to use it across projects.

### Other Agents or Individual Skills

Choose your agent and skills:

```sh
npx skills add SterlingJF/knowledge-bus
```

Or select a specific skill:

```sh
npx skills add SterlingJF/knowledge-bus --skill kb-check
```

These commands use the default branch, not the latest release. Add `--global` to use the skills across projects. Choose either the plugin or individual skills for each agent to avoid duplicate entries.

[Updates and troubleshooting](docs/agent-plugins.md)

### Standalone Checker

The checker also works without an agent:

```sh
git clone https://github.com/SterlingJF/knowledge-bus.git
cd knowledge-bus
uv run kbp
```

## Quick Start

### Working With Existing Notes

Knowledge Bus can also help recover structure from existing files. The ingestion skill reads a folder, maps its contents to the questions they answer, and flags disagreements and missing information. It asks you to resolve uncertainty and writes its outputs in `.knowledge-bus/` inside that folder.

1. Ask your agent to use `kb-ingest` with the path to a folder of notes or documents.
2. Review its initial findings and proposed definitions. Answer any questions about conflicts or uncertain information.
3. Review the outputs in `<folder>/.knowledge-bus/`: definitions, guidance, sourced answers, and a record of decisions made during ingestion.
4. Review unresolved conflicts, potentially outdated content, material that did not fit, and unanswered questions.
5. Use `kb-check` after editing definition or guidance files.

Your existing source files remain unchanged.

See the [Walkthrough](docs/walkthrough.md) for a complete example.

## Limits

- Formal testing for the skills is limited to Claude Opus 5 at high reasoning effort; other models are supported on a best-effort basis.
- The checker validates definition and guidance files. It does not yet validate the `answers.yaml` files produced by ingestion.
- Structural validation does not establish that an answer is true or that a definition captures the right question.
- The protocol defines composition and exchange rules. Tools for composing documents and interpreting incoming knowledge remain planned work.

## Roadmap

### Planned

- [ ] Universe visualizer for understanding and working with knowledge structures
- [ ] Guided authoring of definitions for your own subject or work
- [ ] Document composition from shared knowledge, purpose, and audience
- [ ] Markdown interchange format
- [x] A standard `.knowledge-bus/` directory so tools can discover shared definitions
- [ ] Validation of answer files

### Further Exploration

- Knowledge exchange between different sets of definitions
- Forms and surveys designed around the decisions their answers support

### Evaluation

- How much reasoning is preserved when knowledge is extracted and turned back into a document?
- How reliably do agents follow the definitions and guidance?
- Do agents leave questions unanswered when they lack supporting information?

## Commands

| Command                | What it does                                                                                       |
| ---------------------- | -------------------------------------------------------------------------------------------------- |
| `/kb-uncover-question` | Clarifies a question and checks that it does not duplicate an existing one.                        |
| `/kb-uncover-decision` | Recovers a decision's alternatives, constraints, authority, and conditions for reconsidering it.   |
| `/kb-evolve`           | Adds or re-examines a document type, including its purpose, contents, relationships, and guidance. |
| `/kb-ingest`           | Maps existing notes to sourced answers and reports conflicts, outdated information, and gaps.      |
| `/kb-check`            | Checks definition and guidance files and explains any conformance failures.                        |

## How It Works

### Questions Identify Knowledge

A knowledge element is defined by the question its content answers. Two sections answering the same question refer to the same element, even if their headings differ.

The protocol calls a declared set of knowledge elements, document types, and their relationships a **universe**.

### Purpose Determines Document Contents

A document type is called an **artifact** in the protocol. It is defined by the decision or action it enables and the person who needs to take it.

Its core contents are the information that person needs to make the decision or take the action. Other contents depend on the situation.

### Context Changes What Is Needed

Context rules can change which information is included or required, or disable a document type. The rules must also allow for situations where no document is needed.

Relationships declare dependencies, distinctions, and other connections between knowledge elements and document types.

### Guidance Stays Separate From Requirements

The universe file holds the definitions and structural rules. A companion guidance file explains how to answer well and identifies the sources or assertions behind that advice.

Guidance is advisory. You can depart from the advice and still follow the protocol's requirements.

### Assertions Retain Their Context

An **instance** records an asserted answer and who stated it. Its status indicates how the assertion should be treated; its timestamp records when the value was established, not when it expires. The protocol separately records who is bound by the assertion. For example, one person may state a requirement that another person must follow.

Multiple assertions can coexist. A new assertion can replace an earlier one, while the earlier version remains available for reference.

### Exchange Preserves Differences

The protocol defines four steps: compose, transmit, decode, and reconcile.

A sender composes knowledge for a purpose and audience. The receiver interprets it within their own definitions and context. The receiver matches information by the question it answers and records disagreements rather than silently overwriting them.

### The Checker Verifies Structure

The checker validates the protocol against itself, then checks definition and guidance files against supported conformance rules. It reports failures such as missing declarations, unresolved references, and invalid structural relationships.

People still need to review the meaning: a definition can pass the checks and still ask the wrong question.

## Repository Map

```text
knowledge-bus/
├── protocol/                       authored conformance contract
│   ├── knowledge-bus-protocol.yaml
│   ├── CHANGELOG.md                 protocol history
│   └── conformance/                 shared valid and invalid examples
├── checker/                        installable Python package: knowledge-bus
│   ├── pyproject.toml               package metadata and release version
│   ├── hatch_build.py               includes the protocol in distributions
│   ├── src/kbp_conform/             validation library and kbp command
│   └── tests/                       conformance and discovery tests
├── universes/                      maintained reference definitions
│   └── product-development/
├── skills/                         authored workflows and generated portable resources
├── plugins/                        agent adapters and shared runtime
├── tools/
│   ├── plugin/                     package assembly, inspection, and tests
│   └── release/                    release commands and their tests
├── docs/                           usage guides and explanations
├── CONTRIBUTING.md                 development setup and checks
├── .github/workflows/
├── package.json                    pnpm orchestration only
├── pnpm-workspace.yaml             agent package workspace
├── pnpm-lock.yaml                  shared JS dependency lock
├── pyproject.toml                  uv orchestration only
├── uv.lock                         shared Python dependency lock
├── justfile                        development commands
└── CHANGELOG.md                    product release history
```

The protocol defines conformance; the checker implements it. Universes provide reference definitions, and skills guide agents in working with them.

The checker distribution includes the protocol. Agent packages include their skills and runtime; individually installed skills carry their own required resources.

See [Contributing](CONTRIBUTING.md) for development setup, source layout, and checks.

## Docs

- [Agent Packages and Skills](docs/agent-plugins.md) — updates, requirements, and troubleshooting.

- [Versioning](docs/versioning.md) — version meanings, compatibility, and installation versions.

- [Knowledge Bus Directory](docs/knowledge-bus-directory.md) — where definitions live and how tools find them.

- [Walkthrough](docs/walkthrough.md) — one folder through ingestion, start to finish.
- [How Ingest Works](docs/how-ingest-works.md) — the steps, decisions, and coverage report.
- [Spec Anatomy](docs/spec-anatomy.md) — the structure of a definition file.
- [Validation](docs/validation.md) — what the checker verifies and rejects.
- [Adapting the Example](docs/adapting-the-example.md) — adopt, trim, or extend the included definitions.
- [Design Notes](docs/design-notes.md) — the reasoning behind question identity, separate guidance, and stable codes.

## License

MIT. Issues welcome; PRs by discussion first.
