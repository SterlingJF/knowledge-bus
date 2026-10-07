# Evals Contributions

This path suits data scientists, evaluators, and anyone with a real case.

Eval and model changes start with an issue a maintainer has accepted. Maintainers may close a pull request that changes `evals/` or `tools/evals/` if it has no accepted issue or lacks the proof below. They close it without review or a personal reply. Closing is not a judgement of you or your idea. To reopen, update the issue, add what was missing, and ask.

## When to Open an Issue First

Open an [eval or model issue](https://github.com/SterlingJF/knowledge-bus/issues/new?template=eval-or-model.yml), describing the case without names. Wait for a maintainer to accept the issue.

## Where Cases Come From

Every example restates one real case. Each kind has its own sources:

- Rule examples come only from conversations between people, with or without an AI silently taking notes.
- Skill behaviours come from those conversations or from a person's working session with an AI agent.
- Situations come only from public pages. A situation is an everyday scene that readers place under a frame value, such as the `design` stage.

Move each example to an unrelated field, such as a bakery. Remove names, and don't copy 7 words in a row from the source.

Before an example joins a rule, someone who didn't write the example judges it against the rule, without seeing the source. Calibration later asks the decision model the same question. If the person and the model disagree, name the example in your pull request.

Keep your source outside the repository for 12 months.

The sorting check's passages are the one exception: a model writes them from the definitions.

## What You Can Change

You can change `evals/universe.yaml`, `evals/skills.yaml`, `evals/fixtures/`, `evals/situations/` and `tools/evals/`.

Never post transcript text, names, local paths or any line the copy check flags.

[Contributing](../../CONTRIBUTING.md#choose-your-contribution-path) lists what is out of scope on every path.

## Proof to Bring

Keep one change per pull request, and follow [Commits](../../CONTRIBUTING.md#commits) for commit messages. A model change never shares a commit with a rule or example.

Run these yourself, with your own model access. If you skipped a grading step because you have no `TYPESAFE_API_KEY` or `claude` CLI, say which.

- [ ] `just evals-check` (free).
- [ ] `just evals-calibrate universe` for rules and examples (about $4 at API prices, without a Claude or ChatGPT subscription), or `just evals-calibrate skills` for behaviours and scenarios (about $3).
- [ ] No disagreement on a changed rule or behaviour in calibration's `report.md`.
- [ ] Skill behaviour: one scenario run after your change, `just evals-play --scenario <id>`.
- [ ] Changed `evals/universe.yaml`: `just evals-write` run, rewritten files included.
- [ ] [Checks every pull request needs](../../CONTRIBUTING.md#every-pull-request).

The copy check fails any situation that contains a name, or 7 words in a row from a source in your working folder:

```sh
uv run --locked python tools/evals/intake.py gate <universe-id> --folder <working-folder>
# <n> situations checked against <m> saved sources; <t> hits in <f> situations
```

Then fill in the Evidence Card:

1. **Issue and items:** the accepted issue and the ids you changed.
2. **Source kind:** which source above each case came from.
3. **People present:** the roles of the people in the source, no names.
4. **Gate:** for situations, the copy check's count line with 0 hits. For examples, write "checked by reading", then list any example where your reader and the decision model disagreed.
5. **Run summary:** each command you ran, with the counts, models, costs and input hashes from its run folder.
6. **Origin statement:** the text below.

> I confirm each case is real and everyone present agreed to this use. My checked paraphrase shares no 7 words in a row with the source and identifies no person. I keep the source for 12 months. I ran the commands above myself.

After a first review, maintainers run the full grade and before-and-after scenarios.

## Spot Checks

Maintainers check the source in these cases:

- your first eval pull request;
- any pull request where the blind reader and the decision model disagreed;
- about 1 in 5 other eval pull requests.

You show the source on a screen share. Maintainers copy nothing.

## Adding or Removing a Model

The report compares models from two providers: Anthropic and OpenAI. A new provider needs code first, in its own `feat(evals):` pull request with no results.

A `model:` pull request changes one model or provider and brings:

- [ ] Calibration on `universe` and `skills` with the model, as in [Running on another vendor](../../evals/README.md#running-on-another-vendor).
- [ ] Runs added to `evals/runs.yaml` with `side:` set to `anthropic` or `openai`. Report rebuilt with `just evals-report`.
- [ ] A config row instead of Source kind and People present: provider, model id, date, effort setting, tools, grading step.

Its origin statement is "I ran the commands above myself."

## Deeper Reading

- [Evals](../../evals/README.md)
- [Evaluation Report](../../evals/report.md)

---

Origin statement adapted from [the Developer Certificate of Origin](https://developercertificate.org/).
