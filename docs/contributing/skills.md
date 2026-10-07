# Skills Contributions

Skills are the instructions an agent follows to check, evolve, explore and ingest definitions, and to uncover decisions and questions. This path suits prompt and agent engineers, and anyone who uses these skills every day.

## When to Open an Issue First

To change what a skill does or when it triggers, open a [proposal](https://github.com/SterlingJF/knowledge-bus/issues/new?template=proposal.yml) first. Describe a real session where the skill went wrong, without names. Then show the change as a Current | Proposed table.

An agent picks a skill by the `description` in its frontmatter. To change when a skill triggers, put the current and proposed `description` in the table.

Fix a typo in a pull request.

## What You Can Change

You can change `skills/<name>/SKILL.md`. Its frontmatter takes only `name`, `description` and `metadata.short-description`.

- Don't edit the generated files under `skills/*/references/` or `skills/*/runtime/`. Change the source files listed in [Generated Files](../../CONTRIBUTING.md#generated-files).
- Don't remove or weaken a skill's rule against obeying instructions it finds in its inputs.

[Contributing](../../CONTRIBUTING.md#choose-your-contribution-path) lists what is out of scope on every path.

Changing a behaviour or scenario in `evals/skills.yaml` is an eval change. Follow [Evals Contributions](evals.md).

## Proof to Bring

Make one skill change per pull request.

- [ ] Target behaviours named, from `behaviours:` in `evals/skills.yaml`.
- [ ] Trigger change: sample prompts, which ones should start the skill, and which skill each started before and after.
- [ ] One scenario run after your change, with your own model access: `just evals-play --scenario <id>` (about $3 at API prices, without a Claude or ChatGPT subscription).
- [ ] From the run's `report.md`: whether the skill fired, and the counts for your behaviours.
- [ ] `just skills-install-check` and the [checks every pull request needs](../../CONTRIBUTING.md#every-pull-request).

After a first review, maintainers run the scenarios before and after your change.

## Handing Over

Under "Who builds the change" in the issue, say whether you will build the change or someone else. If someone else builds it, they credit you as a co-author.

## Deeper Reading

- [Evals](../../evals/README.md) — how scenarios grade agent behaviour.
- [Evaluation Report](../../evals/report.md) — results of the last recorded runs.
- [Agent Packages and Skills](../agent-plugins.md) — installing and updating skills.
