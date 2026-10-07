# Methodology

Knowledge Bus evals check two things against written rules:

- how a universe is worded;
- how an agent behaves while it uses a skill.

A universe is the set of definitions for one subject. A skill is a set of instructions an agent follows. Measured figures are in the [Evaluation Report](evals/report.md). Commands and file formats are in [Evals](evals/README.md). The [Glossary](#glossary) at the end names the models and tools behind each role.

## What the Evals Measure

- **Universe wording.** Each question asks one thing. No two questions ask for the same knowledge. Readers file each passage under the question it answers. A frame or factor is a dimension with named values, such as audience. Readers place each everyday case under the right value.
- **Agent behaviour.** An agent uses a skill in a scenario. The scenario lists the behaviours the agent must show, such as which questions it asks and where it writes. A scripted owner sends the person's replies.

## What They Do Not Measure

- Whether a universe helps people or agents get work done.
- Whether a definition fits a given team's work.
- Whether an answer is true.
- Whether wording reads plainly to people. Only code and models grade wording.
- How often an agent behaviour holds over many trials.
- How an agent copes when a person goes off script.

## Where Eval Cases Come From

Every example restates a real case, with identifying details removed. No example is made up.

- A rule example comes from a conversation between people. An AI may have taken notes silently. No other source counts for a rule.
- A behaviour example comes from such a conversation, or from one person's working session with an AI agent. Each scenario follows such a session.
- A situation is an everyday case for a frame value. It comes from a public page in the universe's own field.

A model writes the sorting passages from the definitions. They are the only eval input that does not come from a real case.

Each example moves to an unrelated field, such as a choir or a bakery. It shares no run of 7 words with its source. It identifies no person, project or session.

Before an example joins a rule, it gets a blind check. A reader who has not seen the source judges the example against the rule. The decision model also judges the example. The example stays only if the reader agrees with its intended verdict and the decision model does not confidently disagree.

Each situation goes through these steps:

1. A writer restates the source case using only the value meanings.
2. Code rejects a restatement that copies 7 words in a row from its source or contains an identifying term.
3. A reader labels the situation using only the value meanings, without knowing which value it was written for.
4. A model from the other provider labels it again, from a shuffled list.
5. The situation stays only if both labels match the value it was written for.

Sources stay outside the repository. Contributors keep their sources for 12 months. They show a source on a screen share if a maintainer asks. Maintainers copy nothing. They check the source of:

- each contributor's first eval pull request;
- any pull request where the blind reader and the decision model disagreed;
- about 1 in 5 other eval pull requests.

## How a Case Is Graded

A rule states what passes and why it matters. It has at least two failing and two passing examples. An eval case is one text, a pair of texts from one list, or one text compared with the rest of its list.

Grading runs in tiers. Each rule uses up to three tiers, in this order. The first tier to return pass or fail decides the case.

| Tier | Who decides |
| --- | --- |
| Deterministic | Code checks patterns, terms, word counts and paths. It fails a case or passes it to the next tier. |
| Decision | The decision model answers one typed question. It reads literally and cannot count. |
| Judgment | Two LLM judges read the rule's pass and fail criteria. A verdict stands only when all judges agree. |

If no tier decides a case, the case is undecided and goes to a person for review.

Some rules use a filing test on a whole set:

- **Sorting.** A model writes passages that answer each question without using that question's content words. The LLM judges, the decision model and a small model each file every passage under one of the set's questions. A question passes when every model files all of its passages under that question.
- **Recognition.** The same models file each situation under one of a frame's values. A value passes when each model correctly places enough of its situations, and enough of the whole frame's situations. An unsure answer counts as a miss.

Scenarios get two checks. First, code checks that the skill ran, that the agent wrote only inside `.knowledge-bus/`, and that every file that passed the checker before still passes. Then the tiers grade the required behaviours from the transcript and the files the agent wrote.

## Checking the Graders

The calibration set is the examples that maintainers labelled pass or fail by hand. Calibration checks the tiers against the calibration set. Run `just evals-calibrate universe` or `just evals-calibrate skills`. Calibration scores each tier on its own, then the tiers together. For each rule, it counts fails caught, fails missed, passes kept, passes wrongly failed and undecided cases. It also lists every disagreement. The report flags any rule where the tiers together missed a label.

A calibration run never fails. A pull request must show no disagreement on the rules it changed. If a tier disagrees, it gets a sharper question or is removed from the rule.

The calibration set both tunes and checks the tiers. The report therefore labels them "development examples (interim)".

## Comparing Two Providers

Each measure runs once with each provider's models: its LLM judges, its small model and its agent. Both runs use the same decision model and the same code checks. Both runs file the same sorting passages, which one provider's model wrote.

The report compares two runs only if both graded the same universe and the files each measure uses have the same content hashes.

The report's "Judge pairs across the sides" table pairs one judge from each provider. A verdict counts there only when both judges agree.

## Adding or Removing a Model

To add or remove a model, start with an accepted issue and follow [Evals Contributions](docs/contributing/evals.md). A model change gets its own pull request. It adds or removes one model or provider and changes nothing else. A third provider needs code first.

## Reporting

`just evals-report` builds the report from the runs listed in `evals/runs.yaml`. It calls no model. A measure with no run reads "not run". `just evals-check` fails when the committed report is out of date.

The report counts pass, fail and undecided. It gives no weighted score and no intervals. It counts every listed run equally and states how many trials each scenario had. Each run records its models, the decision model and harness versions, and a hash of every input. When a method change retires a rule, the report lists that rule's earlier failures once. The report shows only listed runs, so Method Versions gives the date of each change.

## Limitations

- **Judges from one provider.** By default, both LLM judges come from the same provider. Agreement between providers shows only in the report's "Judge pairs across the sides" table.
- **No human baseline.** No person grades the same cases for comparison.
- **No held-out set.** The calibration set both tunes and checks the tiers.
- **Few trials.** Each scenario runs one trial by default.
- **Fixed replies.** The scripted owner's replies come in a fixed order.
- **Same models write and label.** One provider's models both wrote and labelled the situations.
- **Shared decision model.** Both providers' runs use the same decision model. A case it decides gets the same verdict in both runs, so that case shows nothing about how the two providers' models differ.
- **Model-written passages.** One provider's model writes the sorting passages that both providers' runs use.
- **Unrecorded checks.** The blind check and the 7-word check on examples leave no record. Code runs the 7-word check only on situations.
- **Lost detail.** Moving a case to another field can drop detail that mattered.
- **Effort unrecorded.** A run through a harness records no reasoning-effort setting.

## Conflict of Interest

The maintainers wrote the universe, the rules and the calibration labels. Agreement with those labels cannot show that the labels are right. The default LLM judges, and the models that wrote the situations and the sorting passages, all come from one provider.

## Method Versions

Each change to what the evals measure, or to their models, adds a dated line.

| Date | Change |
| --- | --- |
| 2026-10-05 | Frame and factor questions measured by recognition. Six wording rules no longer apply to them, and one applies only between frames or between factors. |
| 2026-10-06 | Baseline: spec `schema: evals/1`, graded in the runs listed in `evals/runs.yaml`. |

## Reproduce

[Evals](evals/README.md#commands) lists the commands, keys and CLIs. The report's "How to reproduce" gives the steps behind its figures. To grade a universe in code only, at no cost:

```sh
just evals-grade universes/product-development/universe.kbp.yaml deterministic
```

## Glossary

Each role, with the term the references use where one exists, and what fills it today.

| Term | Meaning | Today |
| --- | --- | --- |
| Agent | The system under test: a model using a skill inside a harness. ReactBench's term. | Claude Opus 5.5 (Anthropic). No OpenAI model has run the scenarios yet. |
| Harness | The tool that runs the agent and gives it tools. ReactBench's term. | Claude Code; Codex |
| LLM judge | A model that grades a case against a rule's pass and fail criteria. KWBench's term. | Claude Opus 5.5 and Claude Fable 5.1 (Anthropic); GPT-6-Astra and GPT-6.1-Sol (OpenAI) |
| Decision model | A model that answers one typed question about a text, literally. | Jev, used in both providers' runs |
| Small model | A fast, low-cost model that files passages and situations alongside the judges. | Claude Haiku 4.5 (Anthropic); GPT-6-Luna (OpenAI) |
| Provider | A company whose models run the evals. | Anthropic; OpenAI |
| Side | The report's name for one provider's LLM judges, small model and agent. | Anthropic side; OpenAI side |
| Calibration set | Eval cases that maintainers labelled by hand, used to check the graders. | The examples in `evals/universe.yaml` and `evals/skills.yaml` |
| Eval case | One item a rule grades. kapa's term. | — |
| Trial | One run of a scenario. ReactBench's term. The report gives the count as n. | — |
| Scripted owner | The script that sends the person's replies in a scenario. | — |

## Credits

- Draws on [ReactBench](https://github.com/millionco/reactbench/tree/f7c35e3cc53408099a8dffb7452c56b508c28440): recording every setting that can change between runs.
- Draws on [KWBench](https://arxiv.org/abs/2604.15760): a flat limitations list that names the missing human baseline and the judge setup.
- Draws on [kapa's Company Knowledge Bench](https://www.kapa.ai/blog/company-knowledge-bench): a calibration set labelled by people, and a note on who built the thing being measured.
