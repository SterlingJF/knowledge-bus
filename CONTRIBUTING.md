# Contributing

## In Short

<!-- BEGIN AUTO-GENERATED PHILOSOPHY.md#in-short -->

Notes and documents work when everyone agrees on what they should answer. Usually, nobody writes that down. The same knowledge ends up under different headings, and the reason a document exists gets lost. AI agents now read and write these documents too.

Knowledge Bus exists to write that agreement down: the questions each document must answer, and the decision or action it supports. People and AI agents then work from the same expectations.

We hold to four values:

- **Human-in-the-loop**: Agents can draft and check. People decide what each definition means and review what agents or other humans write.
- **Evidence-based**: Eval examples are modelled and annotated from real-world sources. Every figure we publish comes from a recorded run.
- **Domain-agnostic**: The same approach works for any field. The product-development universe is one example.
- **Interdisciplinary**: Domain experts, researchers, data scientists and developers work on the same definitions. You do not need to code to contribute.

<!-- END AUTO-GENERATED PHILOSOPHY.md#in-short -->

## Start Here

1. Search open and closed issues and pull requests first.
2. Open an issue with a real example before you change a rule, the meaning of a definition or what a skill does. The table below says when you can skip the issue.
3. Say in the issue whether you will build the change. If not, another contributor may build it once the issue is accepted.
4. Keep one change per pull request. Open it as a draft while the scope is unsettled.
5. Keep secrets and personal data out of fixtures, logs and screenshots.

## Choose Your Contribution Path

Each guide says what is in scope and what proof to bring.

| Path | Covers | Suits | Start with |
| --- | --- | --- | --- |
| [Protocol](docs/contributing/protocol.md) | The Knowledge Bus Protocol: what a universe is and how knowledge moves between universes | Spec writers, Python developers | An issue, always |
| [Universe](docs/contributing/universe.md) | The definitions and guidance in `universes/` | Domain specialists, researchers, writers | An issue for new or changed meaning; a pull request for typos |
| [Evals](docs/contributing/evals.md) | The rules, examples and models that grade wording and agent behaviour | Evaluators, anyone with a real case | An accepted issue, always |
| [Checker](docs/contributing/checker.md) | The command that validates files and issues codes | Python developers, QA | A failing test; an issue if an existing file would start failing |
| [Explorer](docs/contributing/explorer.md) | The offline map of a universe | Frontend, accessibility, design | A screenshot for a bug; an issue for a new view |
| [Skills](docs/contributing/skills.md) | The agent workflows, such as turning notes into definitions | Prompt and agent engineers | An issue to change what a skill does or when it runs; a pull request for typos |
| [Other](docs/development.md#other-changes) | Packaging, CI, dependencies, docs-only edits | Developers, devops, writers | An issue for packaging or CI; a pull request for dependencies or docs |

Out of scope on every path: MCP servers, chat interfaces, and universe wording tuned to a benchmark.

## Every Pull Request

- Link the issue. If your path needs no issue, name the path.
- Run `just check`. Name any check you skipped; reviewers count it as not run.
- Include generated files rebuilt from their source.
- Say how you used AI.

## Development Setup

Install [uv](https://docs.astral.sh/uv/), Node.js 22 or newer, pnpm and [just](https://just.systems/). [.python-version](.python-version) selects Python, and [package.json](package.json) pins pnpm. From the repository root:

```sh
uv python install
uv sync --locked --managed-python
pnpm install --frozen-lockfile --ignore-scripts
pnpm run prepare
pnpm exec playwright install chromium
```

`pnpm run prepare` installs the git hooks. Playwright's Chromium runs the explorer browser tests inside `just check`.

Run the checker from source with `uv run kbp`. Build its wheel and source archive with `uv build --package knowledge-bus`.

## Commits

Write commit messages as `type(scope): subject`. The scope is optional. Keep the subject short and imperative, and use the body to say why.

| Type | Use |
| --- | --- |
| `feat` | New capability |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `refactor` | Restructures code without changing behaviour |
| `test` | Tests only |
| `chore` / `ci` | Tooling, dependencies, workflows |
| `eval` | Add new or modify existing evals |
| `model` | Adds or removes a model or provider |

Scopes: `protocol`, `universe`, `checker`, `explorer`, `skills`, `evals`, `plugins`, `release`. `eval` and `model` take no scope.

When you build someone else's issue, credit them with a `Co-authored-by:` line.

There is no style guide. Run `just fix` before you commit.

## Review

Maintainers end a review with one of these outcomes:

- **Blocking defect:** something breaks, and the review says what must change.
- **Evidence or decision needed:** the review names the smallest check or decision that would settle the open question.
- **Suggestion:** an optional improvement.
- **Ready:** the change does what the issue agreed on, and the proof covers the change.

## Evals

Maintainers may close a pull request that changes `evals/` or `tools/evals/` if it has no accepted issue or lacks the proof in [Evals Contributions](docs/contributing/evals.md). They close it without review or a personal reply. Closing is not a judgement of you or your idea. To reopen, update the issue, add what was missing, and ask.

Before you open the pull request, run the free `just evals-check`, then `just evals-calibrate universe` or `just evals-calibrate skills` for the part you changed, with your own model access. Maintainers run the full grade after a first review. Keep your sources for 12 months, and show them on a screen share if a maintainer asks.

## AI Use

AI tools are welcome. You answer for everything you post. Agents never commit, push, open issues or pull requests, or post comments on your behalf. Read the [AI Policy](AI_POLICY.md) before you start.

## Source Layout

| Path                             | Edit here for                                                                               |
| -------------------------------- | ------------------------------------------------------------------------------------------- |
| `protocol/`                      | Conformance rules and shared valid/invalid examples                                         |
| `checker/`                       | Validation, code minting, and checker tests                                                 |
| `universes/`                     | Reference definitions and guidance                                                          |
| `skills/<name>/SKILL.md`         | Agent workflow instructions                                                                 |
| `plugins/<agent>/knowledge-bus/` | Agent-specific adapters                                                                     |
| `plugins/shared/runtime/`        | The shared checker launcher                                                                 |
| `tools/plugin/`                  | Package assembly, generated skill resources, and installation checks                        |
| `evals/`                         | Eval rules, agent behaviours, fixtures, and situations                                      |
| `tools/evals/`                   | Eval reader, tier engine, grader, scenario player, report builder, and runner generators    |
| `explorer/`                      | Universe viewer package, its design tokens, and its tests                                   |
| `tools/explorer/`                | Model adapter, build and render commands, and explorer checks                               |
| `tools/ce-pattern/`              | Vendored CE Pattern tooling; update through its `UPSTREAM.md`                               |
| `tools/docs/`                    | Doc section sync and its tests                                                              |
| `docs/`                          | Usage guides, explanations, and contribution guides                                         |
| `PHILOSOPHY.md`                  | The project's aim and priorities, and the source of In Short                                |

Agent packages combine an adapter with the shared skills, references and runtime files. Build them with `just plugin-build <agent>`, or `just plugin-build all` for every configured agent.

## Generated Files

The files under `skills/*/references/` and `skills/*/runtime/` are generated. Edit their source instead: `protocol/`, `universes/`, `docs/knowledge-bus-directory.md`, `docs/agent-runtime.md`, the checker or the shared launcher. Then rebuild:

```sh
just skills-build
just skills-check
```

Commit the generated files with their source, so a skill installed on its own gets the same content. `SKILL.md` files are written by hand.

The In Short section is copied from [Philosophy](PHILOSOPHY.md). Edit it there, then run `just docs-build`.

## Checks

| Command                     | Checks                                                                                      |
| --------------------------- | ------------------------------------------------------------------------------------------- |
| `just check`                | Formatting, lint, protocol, generated files, explorer, packages, and regression tests       |
| `just test`                 | Checker, packaging, release-tool, doc-sync, and eval-spec regression tests                  |
| `just explorer-check`       | Explorer formatting, comments, types, design tokens, and component layers                   |
| `just explorer-test`        | Explorer unit, adapter, and browser tests plus generated-artifact checks                    |
| `just self-check`           | Protocol soundness                                                                          |
| `just skills-check`         | Generated resources and skill references                                                    |
| `just docs-check`           | Generated doc sections                                                                      |
| `just skills-install-check` | Individual-skill installation and updates using the skills CLI                              |
| `just plugin-check all`     | Package contents, versions, references, and bundled checker execution                       |
| `just native-install-check` | npm installation, repeat installation, and installed file integrity                         |
| `just release-check`        | Combined checks, lockfile consistency, and built distributions                              |

`pnpm run render:explorer:release-example` builds the release example. It uses a browser only to export the SVG map.

`just explorer-gallery` redraws the README map and its cropped preview in `docs/assets/`. Run it after you change the definitions or the explorer code; otherwise `just explorer-test` and CI fail.

### Git Hooks

| Entry point | Content checked | Checks |
| --- | --- | --- |
| `just check` | Working tree | Full suite |
| `just check-staged` / pre-commit | Staged snapshot | Formatting, lint, protocol, generated files, explorer checks, doc sections |
| Pre-push | Each distinct outgoing branch tip | Full suite |
| CI | Checked-out commit | Full suite |

Git hooks do not load your shell profile, so they can pick up an older Node, often when you commit from a desktop app. Husky reads `~/.config/husky/init.sh` before every hook. Load your version manager in that file. For nvm, add `export NVM_DIR="$HOME/.nvm"` and source `"$NVM_DIR/nvm.sh"`, with Node 22 or newer as the default: `nvm alias default 22`.

### Lint and Formatting

| Operation | Workspace command | Ruff (Python) | Markdownlint (Markdown) |
| --- | --- | --- | --- |
| Check formatting | `pnpm run check:format` | `pnpm run check:format:python` | — |
| Report lint | `just lint` | `pnpm run lint:python` | `pnpm run lint:markdown` |
| Format files | `just format` | `pnpm run format:python` | — |
| Apply lint fixes | `just fix` | `pnpm run fix:python` | `pnpm run fix:markdown` |

Prettier formats only the explorer package and its tools, with `pnpm run format:explorer`. Explorer source has no comments. `check:explorer:source` fails on any comment.

## Credits

- Draws on [Handy's CONTRIBUTING](https://github.com/cjpais/Handy/blob/b710ff27c99550bd02c3da19fbecb1acc7be1a04/CONTRIBUTING.md): searching first, commit type prefixes, and a short philosophy up front.
- Draws on [the AEA data and code policy](https://www.aeaweb.org/journals/data/data-code-policy): contributors keep their sources privately and show them on request.

---

Adapted from [Archify's CONTRIBUTING](https://github.com/tt-a1i/archify/blob/fae6186f20bf56106e68252a607aa8a9fb0e8f9e/CONTRIBUTING.md) and [Archify's REVIEWING](https://github.com/tt-a1i/archify/blob/72e5ea2e852e59c0f31a293397ce754d90708f22/REVIEWING.md).
