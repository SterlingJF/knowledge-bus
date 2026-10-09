# Agents

Read [CONTRIBUTING.md](CONTRIBUTING.md) and the [AI Policy](AI_POLICY.md) first. Set up as in [Development Setup](CONTRIBUTING.md#development-setup).

## Commands

Run commands from the repository root.

| Command | Does |
| --- | --- |
| `just check` | Every check a pull request needs |
| `just test` | Regression tests |
| `just lint` | Python and Markdown lint |
| `just fix` | Formats files and applies lint fixes |
| `just validate <files>` | Checks definition and guidance files |
| `just mint <kind> [count]` | New definition codes; `kind` is `element`, `artifact`, `frame` or `factor` |
| `just skills-check`, `just docs-check` | Checks that generated files are current |
| `just evals-check` | Checks the eval files; calls no model |
| `just explorer-check`, `just explorer-test` | Explorer checks and tests |

`just evals-calibrate`, `just evals-grade`, `just evals-play` and `just evals-run-claude` call paid models. Run them only when the person asks you to.

## Regenerate After Editing

| You edited | Run |
| --- | --- |
| `protocol/`, `checker/`, `plugins/shared/runtime/`, `docs/knowledge-bus-directory.md`, `docs/agent-runtime.md` | `just skills-build` |
| `universes/product-development/` | `just skills-build`, the fixture command below, then `just explorer-gallery` |
| `explorer/src/` or `explorer/styles/` | `just explorer-build`, `just skills-build`, then `just explorer-gallery` |
| `explorer/styles/visual-tokens.json` | `just explorer-tokens` first, then the row above |
| `evals/universe.yaml` | `just evals-write` |
| `evals/runs.yaml` | `just evals-report`; for an added run, `just evals-report --run-folders <folder>` |
| The In Short section of `PHILOSOPHY.md` | `just docs-build` |

Fixture command:

```sh
uv run --locked python tools/explorer/prepare_model.py --input universes/product-development/universe.kbp.yaml --guidance universes/product-development/type-guidance.kbp.yaml --marks universes/product-development/marks.explorer.yaml --output explorer/test/fixtures/product-development.json
```

Never edit the files these commands write. In a skill folder, edit only `SKILL.md`.

Run `just check`. The person commits the generated files with their source change.

## Rules

- Never commit, push, open issues or pull requests, or post comments on the person's behalf.
- When drafting a pull request description, write `TODO` in "In Your Own Words", "AI Use", "Source kind", "People present" and "Origin statement". The person fills in those fields.
- When drafting an issue, leave these to the person: the problem or case, its source, the people present, and the consent boxes.
- Leave replies to maintainers to the person. Never write in their voice.
- Draft from the pull request template and the matching issue form. Fill the other sections that apply.
- An eval or model change needs an issue a maintainer has accepted. Before its pull request, run `just evals-check`. The person runs `just evals-calibrate` on the part they changed, and one `just evals-play` scenario after a skill change.
- Never invent an eval example, scenario or situation. Each must come from real cases. AI can help you restate and de-identify a case. It must not invent one.
- Keep transcript text, names and local paths out of the repository, issues and pull requests. From `tools/evals/intake.py gate`, paste only the last line. The others quote private sources.
- Keep one change per pull request. Draft commit messages as in [Commits](CONTRIBUTING.md#commits).
- Add no runtime dependency to the checker. Write no comments in explorer source.

---

Adapted from [Handy's AGENTS.md](https://github.com/cjpais/Handy/blob/2c5c7601d8db493feeb251702e950f11c8326728/AGENTS.md).
