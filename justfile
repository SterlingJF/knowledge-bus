default:
    @just --list

# Run one root package script, forwarding any trailing arguments to it.
[private]
_pnpm_run SCRIPT *ARGS:
    pnpm run {{quote(SCRIPT)}} {{ARGS}}

# Run repository checks.
check: (_pnpm_run 'check')

# Check the staged snapshot without changing the index or working tree.
check-staged:
    node tools/quality/snapshot.mjs staged

# Check outgoing branch tips supplied by Git's pre-push hook.
check-push:
    node tools/quality/snapshot.mjs push

# Report Python and Markdown lint findings without applying corrections.
lint: (_pnpm_run 'lint')

# Format authored Python files.
format: (_pnpm_run 'format')

# Apply safe lint corrections, format, and report remaining findings.
fix: (_pnpm_run 'fix')

# Scan resolved npm and Python dependencies; findings and errors fail the command.
scan_dependencies:
    osv-scanner scan source --lockfile pnpm-lock.yaml --lockfile uv.lock --config osv-scanner.toml

# Validate the dependency-update policy.
check_renovate_config:
    renovate-config-validator renovate.json

# Validate a spec against the format definition.
validate *ARGS:
    uv run kbp --validate {{ARGS}}

# Generate new unique keys (codes) for a given spec.
mint kind count="1":
    uv run kbp --mint {{kind}} {{count}}

# Run the test suite
test: (_pnpm_run 'test')

# Generate the supporting files committed beside individually installable skills.
skills-build:
    uv run --locked python tools/plugin/skills.py

# Refuse missing or stale generated skill files.
skills-check:
    uv run --locked python tools/plugin/skills.py --check

# Exercise the real skills CLI in disposable projects, with telemetry disabled.
skills-install-check:
    uv run --locked python tools/plugin/check_skills_install.py

# Assemble agent-only npm tarballs. Host: claude, codex, pi, opencode, or all.
plugin-build host="all":
    uv run --locked python tools/plugin/plugin.py build {{quote(host)}}

# Build in isolation, inspect package contents, and exercise the bundled checker.
plugin-check host="all":
    uv run --locked python tools/plugin/plugin.py check {{quote(host)}}

# Test npm install/reinstall, exact installed files, and runtime in disposable projects.
native-install-check:
    uv run --locked python tools/plugin/check_native_install.py

# Type-check the format definition itself
self-check:
    uv run kbp --self-check

# Prepare release metadata without committing or tagging.
release-prepare version:
    uv run --locked python tools/release/release.py prepare {{quote(version)}}

# Validate release metadata and distributions.
release-check:
    uv run --locked python tools/release/release.py check

# Verify clean main and create an annotated local tag. Never pushes.
release-tag:
    uv run --locked python tools/release/release.py tag

# Build the explorer library and standalone bundle.
explorer-build: (_pnpm_run 'build:explorer')

# Render the bundled universe to a self-contained page and a dual-theme SVG.
explorer-render: (_pnpm_run 'render:explorer')

# Regenerate the explorer token stylesheet from its authority.
explorer-tokens: (_pnpm_run 'generate:explorer:tokens')

# Format, comment, type, token, and CE layer checks for the explorer package.
explorer-check: (_pnpm_run 'check:explorer')

# Explorer unit, adapter, and browser tests plus generated-artifact checks.
explorer-test: (_pnpm_run 'test:explorer')

# Capture the step tier of explorer shots and their geometry into dist/explorer-shots/step.
explorer-capture-step: (_pnpm_run 'capture:explorer:step')

# Compare two captured shot directories pixel by pixel and by geometry.
explorer-compare LEFT RIGHT: (_pnpm_run 'compare:explorer:shots' LEFT RIGHT)
