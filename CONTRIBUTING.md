# Contributing

## Before You Start

Issues are welcome. Please discuss proposed changes before opening a pull request.

## Development Setup

Run commands from the repository root. Development uses [uv](https://docs.astral.sh/uv/), Node.js, pnpm, and [just](https://just.systems/). Python is selected by [.python-version](.python-version); Node.js requirements and the pnpm version are specified in [package.json](package.json).

```sh
uv python install
uv sync --locked --managed-python
pnpm install --frozen-lockfile --ignore-scripts
pnpm run prepare
```

Run the checker from source with `uv run kbp`. Build its wheel and source archive with `uv build --package knowledge-bus`.

## Source Layout

| Path                             | Edit here for                                                        |
| -------------------------------- | -------------------------------------------------------------------- |
| `protocol/`                      | Conformance rules and shared valid/invalid examples                  |
| `checker/`                       | Validation, code minting, and checker tests                          |
| `universes/`                     | Reference definitions and guidance                                   |
| `skills/<name>/SKILL.md`         | Agent workflow instructions                                          |
| `plugins/<agent>/knowledge-bus/` | Agent-specific adapters                                              |
| `plugins/shared/runtime/`        | The shared checker launcher                                          |
| `tools/plugin/`                  | Package assembly, generated skill resources, and installation checks |
| `explorer/`                      | Universe viewer package, its token authority, and its tests          |
| `tools/explorer/`                | Model adapter, build and render commands, and explorer checks        |
| `tools/ce-pattern/`              | Vendored CE Pattern tooling; update through its `UPSTREAM.md`        |
| `docs/`                          | Usage guides and explanations                                        |

Agent packages combine their adapter with shared skills, references, and runtime files. `just plugin-build <agent>` builds an isolated package; `just plugin-build all` builds the configured integrations. Build packages through these commands rather than packing source adapter directories directly.

## Generated Files

Edit shared resources at their source, not inside `skills/*/references/` or `skills/*/runtime/`. The generator takes its inputs from `protocol/`, `universes/`, `docs/knowledge-bus-directory.md`, `docs/agent-runtime.md`, the checker, and the shared launcher.

After changing those inputs, regenerate the self-contained skill resources:

```sh
just skills-build
just skills-check
```

Include the generated changes with the source changes so individually installed skills receive the same content. Keep `SKILL.md` authored.

## Checks

| Command                     | Checks                                                                          |
| --------------------------- | ------------------------------------------------------------------------------- |
| `just check`                | Formatting, lint, protocol, generated resources, packages, and regression tests |
| `just test`                 | Checker, packaging, and release-tool regression tests                           |
| `just explorer-check`       | Explorer formatting, comments, types, visual tokens, and CE layers              |
| `just explorer-test`        | Explorer unit, adapter, and browser tests plus generated-artifact checks        |
| `just self-check`           | Protocol soundness                                                              |
| `just skills-check`         | Generated resources and skill references                                        |
| `just skills-install-check` | Individual-skill installation and updates using the skills CLI                  |
| `just plugin-check all`     | Package contents, versions, references, and bundled checker execution           |
| `just native-install-check` | npm installation, repeat installation, and installed file integrity             |
| `just release-check`        | Combined checks, lockfile consistency, and built distributions                  |

`pnpm run render:explorer:release-example` builds the release example. Browser automation is used only for SVG export.

### Git Hooks

| Entry point | Content checked | Checks |
| --- | --- | --- |
| `just check` | Working tree | Full suite |
| `just check-staged` / pre-commit | Staged snapshot | Formatting, lint, protocol, generated resources |
| Pre-push | Each distinct outgoing branch tip | Full suite |
| CI | Checked-out commit | Full suite |

### Lint and Formatting

| Operation | Workspace command | Ruff (Python) | Markdownlint (Markdown) |
| --- | --- | --- | --- |
| Check formatting | `pnpm run check:format` | `pnpm run check:format:python` | — |
| Report lint | `just lint` | `pnpm run lint:python` | `pnpm run lint:markdown` |
| Format files | `just format` | `pnpm run format:python` | — |
| Apply lint fixes | `just fix` | `pnpm run fix:python` | `pnpm run fix:markdown` |

Prettier formats the explorer package and its tools only (`pnpm run format:explorer`); Markdown stays with Markdownlint. Explorer source carries no comments: `check:explorer:source` fails on one, because a claim that matters belongs in a name, a type or a test. The explorer browser tests need a Playwright Chromium: `pnpm exec playwright install chromium` locally, `--with-deps` in CI.

### Installation Checks

Installation checks use disposable directories. Skills-CLI checks disable telemetry. Local package checks do not install integrations into your personal agent setup.

CI also tests native agent registration and refresh in disposable runners. Packaging and installation checks do not evaluate live chat behavior or the quality of an agent's answers.

### Dependency Maintenance

| Operation                     | OSV Scanner              | Renovate                     |
| ----------------------------- | ------------------------ | ---------------------------- |
| Scan resolved dependencies    | `just scan_dependencies` | —                            |
| Validate update configuration | —                        | `just check_renovate_config` |
| Configuration                 | `osv-scanner.toml`       | `renovate.json`              |

These commands require `osv-scanner` and `renovate-config-validator` on your PATH. Scanning checks project dependencies for known vulnerabilities and requires network access. Findings and scanner errors fail the command; scanning is separate from `just check`.

Renovate proposes dependency updates. If an update changes bundled runtime resources, regenerate them before merging; see [Generated Files](#generated-files).
