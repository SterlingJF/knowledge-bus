# Agent Packages and Skills

Use the [installation commands](../README.md#installation) for your agent. Native packages come from npm; individual skills come directly from GitHub.

## Updates

### Claude Code

In Claude Code chat:

```text
/plugin marketplace update knowledge-bus
/plugin update knowledge-bus@knowledge-bus
```

Or in your terminal:

```sh
claude plugin marketplace update knowledge-bus
claude plugin update knowledge-bus@knowledge-bus
```

Follow any reload prompt, or start a new session. Third-party automatic updates are controlled by Claude Code's marketplace settings.

### Codex

In your terminal:

```sh
codex plugin marketplace upgrade knowledge-bus
codex plugin add knowledge-bus@knowledge-bus
```

Start a new session afterward.

### Pi

In your terminal:

```sh
pi update --extension npm:@knowledge-bus/pi@latest
```

Run `/reload` in an existing chat. An explicitly numbered package remains pinned; install a new version explicitly to change that pin.

### OpenCode

In your terminal:

```sh
opencode plugin @knowledge-bus/opencode@latest --force
```

Include `--global` if that was your installation scope. Start a new session afterward.

### Individual Skills

Repeat your `npx skills add` command to install the current default-branch content. An explicit Git tag selects that version instead:

```sh
npx skills add https://github.com/SterlingJF/knowledge-bus/tree/v0.5.0/skills --skill kb-check
```

The skills CLI collects optional installation telemetry. Set `DISABLE_TELEMETRY=1` to opt out. Knowledge Bus adds no separate telemetry.

## Scope and Requirements

Claude and Codex use their native default installation scope. Pi defaults to user scope; use `-l` for the current project. OpenCode and the skills CLI default to project scope; use `--global` for user-wide installation.

Native packages require the relevant agent CLI and Node.js/npm. Checker-backed workflows also need uv and Python compatible with the [checker package requirement](../checker/pyproject.toml). The installed runtime reports its required Python version if the invoking interpreter is too old. First use may download the pinned checker dependency. Users do not need pnpm or a development checkout.

Do not install both a full package and standalone copies of the same skills in one agent.

## Package Contents

Each native package includes the Knowledge Bus skills, shared references, and bundled checker. It installs only the selected agent's integration.

Pi discovers the bundled skills through its package manifest. OpenCode adds the bundled skill directory to its in-memory configuration without copying files, changing user config on disk, or injecting all skill bodies into every conversation.

Individual skills carry their own required resources. Only ingestion includes the product-development starter; the decision-interview skill has no checker runtime.

Tests, contributor docs, build tools, and release tools stay out of packages. Installed packages have no npm lifecycle scripts or npm runtime dependencies. The checker cache stays outside the installed package.

## Versions

Native packages install the latest published stable release. Individual skills installed with `npx skills add SterlingJF/knowledge-bus` come from the default branch and can include unreleased changes.

Updates follow the agent's native refresh and cache behavior. Installing again does not universally guarantee a refresh, so use the host-specific update instructions above.

See [Versioning](versioning.md) for version meanings and compatibility.

## Troubleshooting

- **Command not found:** install the relevant agent CLI and Node.js/npm. Checker errors may also indicate missing Python or uv.
- **Package not found:** check registry connectivity and that the requested version has been published.
- **Skills not visible:** reload or start a new session, check installation scope, and check the agent's plugin/skill settings.
- **Duplicate skills:** choose either the full package or standalone skills and remove the duplicate through its owning installer.
- **Update did not load:** use the update commands for your host, then reload. Version pinning and native caches can retain an older package.

No installation step should create or modify the knowledge folder's `.knowledge-bus/` definitions.
