# Development

How to make packaging, CI, dependency and docs-only changes, and the checks maintainers run.

## Other Changes

Open an issue first for packaging or CI. For dependency and docs-only changes, open a pull request. [Every Pull Request](../CONTRIBUTING.md#every-pull-request) still applies.

| Area | Edit | Also run |
| --- | --- | --- |
| Agent packages | `plugins/`, `tools/plugin/` | `just plugin-check all`, `just skills-install-check`, `just native-install-check` |
| CI | `.github/workflows/` | `just test` |
| Dependencies | `package.json`, `pyproject.toml`, `pnpm-lock.yaml`, `uv.lock` | `just scan_dependencies` |
| Docs only | `docs/`, `README.md` | `just lint` |
| CE Pattern tooling | `tools/ce-pattern/` | Follow its `UPSTREAM.md` |

## Releases

Maintainers release with `just release-prepare <version>`, `just release-check` and `just release-tag`. The tag stays local until a maintainer pushes the tag.

## Installation Checks

`just skills-install-check` and `just native-install-check` install the packages into throwaway folders, with telemetry turned off. They don't change your own agent setup.

CI also installs each agent's CLI on a throwaway runner and checks that the package registers and updates. None of these checks test live chat or the quality of an agent's answers.

## Dependency Updates

`just scan_dependencies` checks the locked npm and Python dependencies for known vulnerabilities. It needs network access and `osv-scanner` on your PATH. Any finding or scanner error fails the scan. It runs separately from `just check`.

Renovate opens dependency-update pull requests. Its settings are in `renovate.json`. Check that file with `just check_renovate_config`, which needs `renovate-config-validator` on your PATH.

If an update changes a file the skills bundle, rebuild the skills before merging. See [Generated Files](../CONTRIBUTING.md#generated-files).
