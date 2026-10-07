# Evaluation report

Built by `tools/evals/report.py` from the runs in `evals/runs.yaml`; it calls no model. Anything without a run reads "not run". Sides are compared only when the inputs a measure depends on have the same digests. The universe grade, recognition and sorting are reported per universe, and runs of different universes are never compared.

Labels: calibrated on development examples (interim); recognition on development situations (interim); each scenario's figure says how many times it ran (n).

Latest run: 2026-10-06.

| Run | Side | Universe | Measures | Input | Digest |
| --- | --- | --- | --- | --- | --- |
| `examples-universe-20261006T060659282403Z` | Anthropic side | — | calibration-universe | `evals/skills.yaml` | sha256:9fbf6e93c67aa396 |
| `examples-universe-20261006T060659282403Z` | Anthropic side | — | calibration-universe | `evals/universe.yaml` | sha256:c60e8732e8686698 |
| `examples-skills-20261006T134912752473Z` | Anthropic side | — | calibration-skills | `evals/skills.yaml` | sha256:e3ec1d4224e88d87 |
| `examples-skills-20261006T134912752473Z` | Anthropic side | — | calibration-skills | `evals/universe.yaml` | sha256:c60e8732e8686698 |
| `universe-20261006T050614485618Z` | Anthropic side | product-development | grade, sorting, recognition | `evals/situations/cases.yaml (cases used)` | sha256:06966e147599b193 |
| `universe-20261006T050614485618Z` | Anthropic side | product-development | grade, sorting, recognition | `evals/situations/product-development.yaml` | sha256:06327a9fbb536657 |
| `universe-20261006T050614485618Z` | Anthropic side | product-development | grade, sorting, recognition | `evals/skills.yaml` | sha256:9fbf6e93c67aa396 |
| `universe-20261006T050614485618Z` | Anthropic side | product-development | grade, sorting, recognition | `evals/universe.yaml` | sha256:c60e8732e8686698 |
| `universe-20261006T050614485618Z` | Anthropic side | product-development | grade, sorting, recognition | `probes.json` | sha256:306161298bf56f8a |
| `universe-20261006T050614485618Z` | Anthropic side | product-development | grade, sorting, recognition | `universes/product-development/type-guidance.kbp.yaml` | sha256:effad3b412e4c553 |
| `universe-20261006T050614485618Z` | Anthropic side | product-development | grade, sorting, recognition | `universes/product-development/universe.kbp.yaml` | sha256:4b70294612aa9d56 |
| `play-20261006T134912768658Z` | Anthropic side | — | scenarios | `evals/fixtures/allotment-notes` | sha256:296037285d6e14a0 |
| `play-20261006T134912768658Z` | Anthropic side | — | scenarios | `evals/fixtures/bakery-orders` | sha256:493de179c433b34f |
| `play-20261006T134912768658Z` | Anthropic side | — | scenarios | `evals/fixtures/choir-notes` | sha256:37dc2f926e6ba40e |
| `play-20261006T134912768658Z` | Anthropic side | — | scenarios | `evals/fixtures/food-bank-parcels` | sha256:ae64368ce22a2310 |
| `play-20261006T134912768658Z` | Anthropic side | — | scenarios | `evals/fixtures/info-pages` | sha256:9c3323e5f3ea1e75 |
| `play-20261006T134912768658Z` | Anthropic side | — | scenarios | `evals/fixtures/permit-counter` | sha256:a21da5ae7cc30407 |
| `play-20261006T134912768658Z` | Anthropic side | — | scenarios | `evals/fixtures/village-hall` | sha256:9b770a4544dedb29 |
| `play-20261006T134912768658Z` | Anthropic side | — | scenarios | `evals/skills.yaml` | sha256:e3ec1d4224e88d87 |
| `play-20261006T134912768658Z` | Anthropic side | — | scenarios | `evals/universe.yaml` | sha256:c60e8732e8686698 |
| `play-20261006T134912768658Z` | Anthropic side | — | scenarios | `skills/kb-check/SKILL.md` | sha256:0af1f8a6e16870a1 |
| `play-20261006T134912768658Z` | Anthropic side | — | scenarios | `skills/kb-evolve/SKILL.md` | sha256:9b4f52eabf736ea9 |
| `play-20261006T134912768658Z` | Anthropic side | — | scenarios | `skills/kb-explore/SKILL.md` | sha256:909b393f273573b0 |
| `play-20261006T134912768658Z` | Anthropic side | — | scenarios | `skills/kb-ingest/SKILL.md` | sha256:e50b5fc789965bdf |
| `play-20261006T134912768658Z` | Anthropic side | — | scenarios | `skills/kb-uncover-decision/SKILL.md` | sha256:89234c0c5cfc5ece |
| `play-20261006T134912768658Z` | Anthropic side | — | scenarios | `skills/kb-uncover-question/SKILL.md` | sha256:5eb7ec44c20f89a3 |
| `examples-universe-20261006T132135450769Z` | OpenAI side | — | calibration-universe | `evals/skills.yaml` | sha256:9fbf6e93c67aa396 |
| `examples-universe-20261006T132135450769Z` | OpenAI side | — | calibration-universe | `evals/universe.yaml` | sha256:c60e8732e8686698 |
| `examples-skills-20261006T132135451472Z` | OpenAI side | — | calibration-skills | `evals/skills.yaml` | sha256:9fbf6e93c67aa396 |
| `examples-skills-20261006T132135451472Z` | OpenAI side | — | calibration-skills | `evals/universe.yaml` | sha256:c60e8732e8686698 |
| `universe-20261006T132135451825Z` | OpenAI side | product-development | grade, sorting, recognition | `evals/situations/cases.yaml (cases used)` | sha256:06966e147599b193 |
| `universe-20261006T132135451825Z` | OpenAI side | product-development | grade, sorting, recognition | `evals/situations/product-development.yaml` | sha256:06327a9fbb536657 |
| `universe-20261006T132135451825Z` | OpenAI side | product-development | grade, sorting, recognition | `evals/skills.yaml` | sha256:9fbf6e93c67aa396 |
| `universe-20261006T132135451825Z` | OpenAI side | product-development | grade, sorting, recognition | `evals/universe.yaml` | sha256:c60e8732e8686698 |
| `universe-20261006T132135451825Z` | OpenAI side | product-development | grade, sorting, recognition | `probes.json` | sha256:306161298bf56f8a |
| `universe-20261006T132135451825Z` | OpenAI side | product-development | grade, sorting, recognition | `universes/product-development/type-guidance.kbp.yaml` | sha256:effad3b412e4c553 |
| `universe-20261006T132135451825Z` | OpenAI side | product-development | grade, sorting, recognition | `universes/product-development/universe.kbp.yaml` | sha256:4b70294612aa9d56 |

## Headline

The figures this report stands behind.

How the two sides relate: both sides use the same decision model, Jev, as the decision tier and as one of the readers in recognition and sorting. The recognition situations are written blind on one side and labelled blind on both sides, and a situation is kept only where both sides agree; each universe's recognition section says which side did what. The sorting passages are written by the Anthropic side's run and reused by the OpenAI side.

| Measure | What it shows | Anthropic side | OpenAI side | Both agree |
| --- | --- | --- | --- | --- |
| Calibration, universe rules (development examples, interim) | Whether the tiers reproduce the owner's labelled examples of definitions that meet and miss the rules. | 91 examples: 44 fails caught, 0 missed, 47 passes kept, 0 wrongly failed, 0 undecided | 91 examples: 43 fails caught, 1 missed, 47 passes kept, 0 wrongly failed, 0 undecided | the two companies' judges agree on 66 of 66; 14 more settled the same way by shared code or Jev; 11 more settled by the filing checks, 10 of them the same |
| Calibration, skills behaviours (development examples, interim) | Whether the tiers reproduce the owner's labelled examples of agent behaviour. | not comparable: evals/skills.yaml differs | not comparable: evals/skills.yaml differs | not comparable |
| Agent scenarios | Whether an agent working with a scripted owner shows the behaviours its scenario requires. | 371 checks over 8 scenarios, each run 3 times (n=3): 289 pass, 32 fail, 50 undecided | not run | not run |

Rules whose calibration chain missed an owner label, so their figures carry that caveat: Anthropic side: none; OpenAI side: `sorts-reliably`.

## Calibration

Calibrated on development examples (interim).

### Calibration, universe rules, Anthropic side

Run `examples-universe-20261006T060659282403Z` (anthropic-side).

Per tier, over every rule:

| Tier | n | Caught fails | Missed fails | Kept passes | Wrongly failed | Undecided |
| --- | --- | --- | --- | --- | --- | --- |
| deterministic | 40 | 4 | 0 | 0 | 0 | 36 |
| decision | 12 | 5 | 0 | 6 | 0 | 1 |
| judgment | 80 | 39 | 0 | 41 | 0 | 0 |
| sort | 6 | 3 | 0 | 3 | 0 | 0 |
| recognise | 5 | 2 | 0 | 3 | 0 | 0 |
| chain | 91 | 44 | 0 | 47 | 0 | 0 |

Per rule, all tiers together:

| Rule | n | Caught fails | Missed fails | Kept passes | Wrongly failed | Undecided |
| --- | --- | --- | --- | --- | --- | --- |
| `one-question` | 6 | 3 | 0 | 3 | 0 | 0 |
| `named-referents` | 5 | 2 | 0 | 3 | 0 | 0 |
| `direct-statement` | 6 | 3 | 0 | 3 | 0 | 0 |
| `plain-words` | 6 | 3 | 0 | 3 | 0 | 0 |
| `one-point-terse` | 5 | 2 | 0 | 3 | 0 | 0 |
| `point-first` | 6 | 3 | 0 | 3 | 0 | 0 |
| `holds-across-scope` | 6 | 3 | 0 | 3 | 0 | 0 |
| `one-term-per-concept` | 6 | 3 | 0 | 3 | 0 | 0 |
| `present-state` | 6 | 3 | 0 | 3 | 0 | 0 |
| `siblings-differ` | 4 | 2 | 0 | 2 | 0 | 0 |
| `action-names-an-action` | 6 | 3 | 0 | 3 | 0 | 0 |
| `questions-distinct` | 6 | 3 | 0 | 3 | 0 | 0 |
| `enablements-distinct` | 6 | 3 | 0 | 3 | 0 | 0 |
| `strength-follows-the-action` | 6 | 3 | 0 | 3 | 0 | 0 |
| `sorts-reliably` | 6 | 3 | 0 | 3 | 0 | 0 |
| `values-recognised` | 5 | 2 | 0 | 3 | 0 | 0 |

No disagreements with the owner.

### Calibration, universe rules, OpenAI side

Run `examples-universe-20261006T132135450769Z` (openai-side).

Per tier, over every rule:

| Tier | n | Caught fails | Missed fails | Kept passes | Wrongly failed | Undecided |
| --- | --- | --- | --- | --- | --- | --- |
| deterministic | 40 | 4 | 0 | 0 | 0 | 36 |
| decision | 12 | 5 | 0 | 6 | 0 | 1 |
| judgment | 80 | 39 | 0 | 41 | 0 | 0 |
| sort | 6 | 2 | 1 | 3 | 0 | 0 |
| recognise | 5 | 2 | 0 | 3 | 0 | 0 |
| chain | 91 | 43 | 1 | 47 | 0 | 0 |

Per rule, all tiers together:

| Rule | n | Caught fails | Missed fails | Kept passes | Wrongly failed | Undecided |
| --- | --- | --- | --- | --- | --- | --- |
| `one-question` | 6 | 3 | 0 | 3 | 0 | 0 |
| `named-referents` | 5 | 2 | 0 | 3 | 0 | 0 |
| `direct-statement` | 6 | 3 | 0 | 3 | 0 | 0 |
| `plain-words` | 6 | 3 | 0 | 3 | 0 | 0 |
| `one-point-terse` | 5 | 2 | 0 | 3 | 0 | 0 |
| `point-first` | 6 | 3 | 0 | 3 | 0 | 0 |
| `holds-across-scope` | 6 | 3 | 0 | 3 | 0 | 0 |
| `one-term-per-concept` | 6 | 3 | 0 | 3 | 0 | 0 |
| `present-state` | 6 | 3 | 0 | 3 | 0 | 0 |
| `siblings-differ` | 4 | 2 | 0 | 2 | 0 | 0 |
| `action-names-an-action` | 6 | 3 | 0 | 3 | 0 | 0 |
| `questions-distinct` | 6 | 3 | 0 | 3 | 0 | 0 |
| `enablements-distinct` | 6 | 3 | 0 | 3 | 0 | 0 |
| `strength-follows-the-action` | 6 | 3 | 0 | 3 | 0 | 0 |
| `sorts-reliably` | 6 | 2 | 1 | 3 | 0 | 0 |
| `values-recognised` | 5 | 2 | 0 | 3 | 0 | 0 |

Disagreements with the owner:

- `sorts-reliably` (sort): "Which ingredients go into the loaf?" labelled fail
- `sorts-reliably` (chain): "Which ingredients go into the loaf?" labelled fail

### Calibration, skills behaviours, Anthropic side

Run `examples-skills-20261006T134912752473Z` (anthropic-side).

Per tier, over every rule:

| Tier | n | Caught fails | Missed fails | Kept passes | Wrongly failed | Undecided |
| --- | --- | --- | --- | --- | --- | --- |
| deterministic | 6 | 0 | 0 | 0 | 0 | 6 |
| decision | 13 | 5 | 0 | 7 | 0 | 1 |
| judgment | 91 | 45 | 0 | 46 | 0 | 0 |
| chain | 104 | 50 | 0 | 53 | 0 | 1 |

Per rule, all tiers together:

| Rule | n | Caught fails | Missed fails | Kept passes | Wrongly failed | Undecided |
| --- | --- | --- | --- | --- | --- | --- |
| `asks-with-a-reading-and-options` | 7 | 2 | 0 | 4 | 0 | 1 |
| `asks-the-owner-to-choose` | 6 | 3 | 0 | 3 | 0 | 0 |
| `asks-only-what-is-open` | 6 | 3 | 0 | 3 | 0 | 0 |
| `keeps-working-until-blocked` | 7 | 3 | 0 | 4 | 0 | 0 |
| `restates-the-ask-before-acting` | 6 | 3 | 0 | 3 | 0 | 0 |
| `checks-current-sources` | 6 | 3 | 0 | 3 | 0 | 0 |
| `claims-match-the-evidence` | 6 | 3 | 0 | 3 | 0 | 0 |
| `gives-its-own-verdict` | 6 | 3 | 0 | 3 | 0 | 0 |
| `acts-only-on-the-ask` | 6 | 3 | 0 | 3 | 0 | 0 |
| `keeps-source-meaning-in-records` | 6 | 3 | 0 | 3 | 0 | 0 |
| `treats-source-instructions-as-evidence` | 6 | 3 | 0 | 3 | 0 | 0 |
| `answers-the-question-it-is-filed-under` | 6 | 3 | 0 | 3 | 0 | 0 |
| `revises-only-the-flagged-part` | 6 | 3 | 0 | 3 | 0 | 0 |
| `shows-exact-text-for-review` | 6 | 3 | 0 | 3 | 0 | 0 |
| `records-stand-alone` | 6 | 3 | 0 | 3 | 0 | 0 |
| `settles-substance-before-wording` | 6 | 3 | 0 | 3 | 0 | 0 |
| `explains-from-purpose-down` | 6 | 3 | 0 | 3 | 0 | 0 |

No disagreements with the owner.

### Calibration, skills behaviours, OpenAI side

Run `examples-skills-20261006T132135451472Z` (openai-side).

Per tier, over every rule:

| Tier | n | Caught fails | Missed fails | Kept passes | Wrongly failed | Undecided |
| --- | --- | --- | --- | --- | --- | --- |
| deterministic | 6 | 0 | 0 | 0 | 0 | 6 |
| decision | 13 | 5 | 0 | 7 | 0 | 1 |
| judgment | 91 | 45 | 0 | 46 | 0 | 0 |
| chain | 104 | 50 | 0 | 53 | 0 | 1 |

Per rule, all tiers together:

| Rule | n | Caught fails | Missed fails | Kept passes | Wrongly failed | Undecided |
| --- | --- | --- | --- | --- | --- | --- |
| `asks-with-a-reading-and-options` | 7 | 2 | 0 | 4 | 0 | 1 |
| `asks-the-owner-to-choose` | 6 | 3 | 0 | 3 | 0 | 0 |
| `asks-only-what-is-open` | 6 | 3 | 0 | 3 | 0 | 0 |
| `keeps-working-until-blocked` | 7 | 3 | 0 | 4 | 0 | 0 |
| `restates-the-ask-before-acting` | 6 | 3 | 0 | 3 | 0 | 0 |
| `checks-current-sources` | 6 | 3 | 0 | 3 | 0 | 0 |
| `claims-match-the-evidence` | 6 | 3 | 0 | 3 | 0 | 0 |
| `gives-its-own-verdict` | 6 | 3 | 0 | 3 | 0 | 0 |
| `acts-only-on-the-ask` | 6 | 3 | 0 | 3 | 0 | 0 |
| `keeps-source-meaning-in-records` | 6 | 3 | 0 | 3 | 0 | 0 |
| `treats-source-instructions-as-evidence` | 6 | 3 | 0 | 3 | 0 | 0 |
| `answers-the-question-it-is-filed-under` | 6 | 3 | 0 | 3 | 0 | 0 |
| `revises-only-the-flagged-part` | 6 | 3 | 0 | 3 | 0 | 0 |
| `shows-exact-text-for-review` | 6 | 3 | 0 | 3 | 0 | 0 |
| `records-stand-alone` | 6 | 3 | 0 | 3 | 0 | 0 |
| `settles-substance-before-wording` | 6 | 3 | 0 | 3 | 0 | 0 |
| `explains-from-purpose-down` | 6 | 3 | 0 | 3 | 0 | 0 |

No disagreements with the owner.

## Agent scenarios

### Agent scenarios, Anthropic side

Run `play-20261006T134912768658Z` (anthropic-side).

Each scenario ran 3 times (n=3).

Scenarios: add-terms-to-the-choir-spec, check-the-food-bank-spec, explain-the-reader-spec, explain-the-village-hall-definitions, ingest-allotment-notes, ingest-choir-notes, recover-the-counter-hours-decision, sharpen-the-cake-request-question.

| Behaviour | Pass | Fail | Undecided |
| --- | --- | --- | --- |
| `acts-only-on-the-ask` | 33 | 5 | 1 |
| `answers-the-question-it-is-filed-under` | 9 | 0 | 1 |
| `asks-only-what-is-open` | 9 | 1 | 2 |
| `asks-the-owner-to-choose` | 3 | 0 | 0 |
| `asks-with-a-reading-and-options` | 22 | 1 | 1 |
| `checks-current-sources` | 60 | 0 | 18 |
| `claims-match-the-evidence` | 48 | 0 | 9 |
| `explains-from-purpose-down` | 4 | 4 | 1 |
| `gives-its-own-verdict` | 5 | 0 | 3 |
| `keeps-source-meaning-in-records` | 11 | 0 | 4 |
| `keeps-working-until-blocked` | 17 | 1 | 0 |
| `records-stand-alone` | 3 | 2 | 1 |
| `restates-the-ask-before-acting` | 21 | 8 | 4 |
| `revises-only-the-flagged-part` | 14 | 0 | 0 |
| `settles-substance-before-wording` | 0 | 3 | 0 |
| `shows-exact-text-for-review` | 24 | 7 | 5 |
| `treats-source-instructions-as-evidence` | 6 | 0 | 0 |

Skills exercised:

| Skill | Runs | Fired in |
| --- | --- | --- |
| kb-check | 3 | 3 |
| kb-evolve | 3 | 3 |
| kb-explore | 6 | 3 |
| kb-ingest | 6 | 6 |
| kb-uncover-decision | 3 | 3 |
| kb-uncover-question | 3 | 3 |

Code checks, per run:

| Run | Skill fired | Writes outside .knowledge-bus | Writes outside the work folder (Claude tool calls) | conforms_to changed | Validates | Loaded beside the skills under test | Possible script drift | Agent error |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `add-terms-to-the-choir-spec/run-1` | yes | none | none | .knowledge-bus/universe.kbp.yaml | before yes, after yes | none | before owner reply 3 | none |
| `add-terms-to-the-choir-spec/run-2` | yes | none | none | .knowledge-bus/universe.kbp.yaml | before yes, after yes | none | none | none |
| `add-terms-to-the-choir-spec/run-3` | yes | none | none | .knowledge-bus/universe.kbp.yaml | before yes, after yes | none | none | none |
| `check-the-food-bank-spec/run-1` | yes | none | none | none | before no, after yes | none | before owner reply 2 | none |
| `check-the-food-bank-spec/run-2` | yes | none | none | none | before no, after yes | none | before owner reply 2 | none |
| `check-the-food-bank-spec/run-3` | yes | none | none | none | before no, after yes | none | before owner reply 1, 2 | none |
| `explain-the-reader-spec/run-1` | no | none | ~/.claude/projects/-private-var-folders-5v-9mr9q8-d3qsccjt9-2n5vmk00000gn-T-evals-play-c9-il6oj-work/memory/written-answers-no-page.md, ~/.claude/projects/-private-var-folders-5v-9mr9q8-d3qsccjt9-2n5vmk00000gn-T-evals-play-c9-il6oj-work/memory/MEMORY.md | none | before yes, after yes | none | before owner reply 1 | none |
| `explain-the-reader-spec/run-2` | no | none | none | none | before yes, after yes | none | before owner reply 1 | none |
| `explain-the-reader-spec/run-3` | no | none | ~/.claude/projects/-private-var-folders-5v-9mr9q8-d3qsccjt9-2n5vmk00000gn-T-evals-play-sogi18g3-work/memory/explanations-in-text.md, ~/.claude/projects/-private-var-folders-5v-9mr9q8-d3qsccjt9-2n5vmk00000gn-T-evals-play-sogi18g3-work/memory/MEMORY.md | none | before yes, after yes | none | none | none |
| `explain-the-village-hall-definitions/run-1` | yes | none | none | none | before yes, after yes | none | none | none |
| `explain-the-village-hall-definitions/run-2` | yes | none | none | none | before yes, after yes | none | none | none |
| `explain-the-village-hall-definitions/run-3` | yes | none | none | none | before yes, after yes | none | none | none |
| `ingest-allotment-notes/run-1` | yes | none | none | none | before yes, after yes | none | none | none |
| `ingest-allotment-notes/run-2` | yes | none | none | none | before yes, after yes | none | none | none |
| `ingest-allotment-notes/run-3` | yes | none | none | none | before yes, after yes | none | before owner reply 3 | none |
| `ingest-choir-notes/run-1` | yes | none | none | none | before yes, after yes | none | before owner reply 2 | none |
| `ingest-choir-notes/run-2` | yes | none | none | none | before yes, after yes | none | before owner reply 2 | none |
| `ingest-choir-notes/run-3` | yes | none | none | none | before yes, after yes | none | before owner reply 2 | none |
| `recover-the-counter-hours-decision/run-1` | yes | none | none | none | before yes, after yes | none | before owner reply 2, 4 | none |
| `recover-the-counter-hours-decision/run-2` | yes | none | none | none | before yes, after yes | none | before owner reply 4 | none |
| `recover-the-counter-hours-decision/run-3` | yes | none | none | none | before yes, after yes | none | before owner reply 2, 3, 4 | none |
| `sharpen-the-cake-request-question/run-1` | yes | none | none | none | before yes, after yes | none | none | none |
| `sharpen-the-cake-request-question/run-2` | yes | none | none | none | before yes, after yes | none | none | none |
| `sharpen-the-cake-request-question/run-3` | yes | none | none | none | before yes, after yes | none | none | none |

Proposed definitions, graded with the universe rules (`wording/`):

| Rule | Pass | Fail | Undecided |
| --- | --- | --- | --- |
| `direct-statement` | 10 | 0 | 1 |
| `holds-across-scope` | 6 | 1 | 4 |
| `named-referents` | 6 | 2 | 3 |
| `one-point-terse` | 4 | 6 | 1 |
| `one-question` | 0 | 3 | 0 |
| `one-term-per-concept` | 11 | 0 | 0 |
| `plain-words` | 11 | 0 | 0 |
| `questions-distinct` | 3 | 0 | 0 |
| `strength-follows-the-action` | 2 | 0 | 1 |

### Agent scenarios, OpenAI side

Not run.

## Where the sides disagree

### Case by case

Agent scenarios: not run on both sides.

## Universe `product-development`

### Headline of `product-development`

| Measure | What it shows | Anthropic side | OpenAI side | Both agree |
| --- | --- | --- | --- | --- |
| Universe grade | How many of the universe's definitions meet each rule. | 3378 cases: 2720 pass, 441 fail, 217 undecided | 3378 cases: 2640 pass, 591 fail, 147 undecided | the two companies' judges agree on 2774 of 2950; 90 more settled the same way by shared code or Jev |
| Recognition by frame (development situations, interim) | Whether readers place everyday situations under the right value of a frame or factor. | 10 frames: 1 pass, 9 fail, 0 undecided, 0 not run; 21 of 38 values fail (all readers); 6 of 38 (careful readers only) | 10 frames: 1 pass, 9 fail, 0 undecided, 0 not run; 19 of 38 values fail (all readers); 5 of 38 (careful readers only) | same verdict on 10 of 10 frames |
| Sorting | Whether a passage that answers a question is filed under that question. | 135 members: 123 pass, 8 fail, 4 undecided | 135 members: 128 pass, 4 fail, 3 undecided | same verdict on 126 of 131 cases both sides settled |
| Judge pairs across the sides | Whether verdicts stand when one judge from each company must agree. | judges: claude-opus-5-5, claude-fable-5-1 | judges: codex:gpt-6-astra, codex:gpt-6.1-sol | 4 pairs, 2936 cases each: 2257 to 2357 pass, 262 to 338 fail, 308 to 348 undecided |

### Universe grade of `product-development`, Anthropic side

Run `universe-20261006T050614485618Z` (anthropic-side).

Tiers: deterministic, decision, judgment, sort, recognise.

| Rule | Pass | Fail | Undecided | Settled by deterministic / decision / judgment / sort / recognise |
| --- | --- | --- | --- | --- |
| `action-names-an-action` | 19 | 0 | 0 | 0 / 19 / 0 / 0 / 0 |
| `direct-statement` | 217 | 131 | 16 | 17 / 0 / 331 / 0 / 0 |
| `enablements-distinct` | 17 | 0 | 2 | 0 / 0 / 17 / 0 / 0 |
| `holds-across-scope` | 334 | 12 | 18 | 0 / 0 / 346 / 0 / 0 |
| `named-referents` | 244 | 70 | 50 | 0 / 0 / 314 / 0 / 0 |
| `one-point-terse` | 279 | 55 | 30 | 0 / 0 / 334 / 0 / 0 |
| `one-question` | 56 | 3 | 0 | 0 / 54 / 5 / 0 / 0 |
| `one-term-per-concept` | 378 | 4 | 4 | 0 / 0 / 382 / 0 / 0 |
| `plain-words` | 169 | 144 | 51 | 0 / 0 / 313 / 0 / 0 |
| `point-first` | 216 | 6 | 21 | 0 / 0 / 222 / 0 / 0 |
| `present-state` | 239 | 4 | 0 | 0 / 0 / 243 / 0 / 0 |
| `questions-distinct` | 48 | 5 | 6 | 0 / 0 / 53 / 0 / 0 |
| `siblings-differ` | 390 | 1 | 4 | 0 / 0 / 391 / 0 / 0 |
| `sorts-reliably` | 123 | 8 | 4 | 0 / 0 / 0 / 131 / 0 |
| `strength-follows-the-action` | 114 | 6 | 15 | 0 / 0 / 120 / 0 / 0 |
| `values-recognised` | 17 | 21 | 0 | 0 / 0 / 0 / 0 / 38 |

### Universe grade of `product-development`, OpenAI side

Run `universe-20261006T132135451825Z` (openai-side).

Tiers: deterministic, decision, judgment, sort, recognise.

| Rule | Pass | Fail | Undecided | Settled by deterministic / decision / judgment / sort / recognise |
| --- | --- | --- | --- | --- |
| `action-names-an-action` | 19 | 0 | 0 | 0 / 19 / 0 / 0 / 0 |
| `direct-statement` | 218 | 136 | 10 | 17 / 0 / 337 / 0 / 0 |
| `enablements-distinct` | 19 | 0 | 0 | 0 / 0 / 19 / 0 / 0 |
| `holds-across-scope` | 313 | 26 | 25 | 0 / 0 / 339 / 0 / 0 |
| `named-referents` | 226 | 112 | 26 | 0 / 0 / 338 / 0 / 0 |
| `one-point-terse` | 229 | 96 | 39 | 0 / 0 / 325 / 0 / 0 |
| `one-question` | 57 | 2 | 0 | 0 / 54 / 5 / 0 / 0 |
| `one-term-per-concept` | 383 | 0 | 3 | 0 / 0 / 383 / 0 / 0 |
| `plain-words` | 209 | 144 | 11 | 0 / 0 / 353 / 0 / 0 |
| `point-first` | 196 | 42 | 5 | 0 / 0 / 238 / 0 / 0 |
| `present-state` | 239 | 4 | 0 | 0 / 0 / 243 / 0 / 0 |
| `questions-distinct` | 47 | 8 | 4 | 0 / 0 / 55 / 0 / 0 |
| `siblings-differ` | 389 | 0 | 6 | 0 / 0 / 389 / 0 / 0 |
| `sorts-reliably` | 128 | 4 | 3 | 0 / 0 / 0 / 132 / 0 |
| `strength-follows-the-action` | 96 | 21 | 18 | 0 / 0 / 117 / 0 / 0 |
| `values-recognised` | 19 | 19 | 0 | 0 / 0 / 0 / 0 / 38 |

### Recognition by frame of `product-development`, Anthropic side

Run `universe-20261006T050614485618Z` (anthropic-side).

21 of 38 values fail (all readers); 6 of 38 (careful readers only). The careful readers are this side's judgment models: claude-opus-5-5, claude-fable-5-1.

Each reader's right / situations in the set; unsure and none count as misses, and on a ladder a miss one step away is counted as off by one.

| Set | Values | Situations | claude-fable-5-1 | claude-haiku-4-5-20251001 | claude-opus-5-5 | jev | Lowest value | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| audience | 5 | 28 | 27/28 (0 unsure, 0 none) | 28/28 (0 unsure, 0 none) | 27/28 (0 unsure, 0 none) | 27/28 (1 unsure, 0 none) | internal 4/5 (claude-opus-5-5) | pass |
| authority | 5 | 40 | 40/40 (0 unsure, 0 none, 0 off by one) | 40/40 (0 unsure, 0 none, 0 off by one) | 40/40 (0 unsure, 0 none, 0 off by one) | 36/40 (4 unsure, 0 none, 0 off by one) | discretionary 3/5 (jev) | fail |
| maturity | 3 | 25 | 23/25 (0 unsure, 0 none, 2 off by one) | 21/25 (0 unsure, 0 none, 3 off by one) | 23/25 (0 unsure, 0 none, 2 off by one) | 22/25 (1 unsure, 0 none, 2 off by one) | proven 3/6 (jev) | fail |
| outcome.form | 3 | 20 | 20/20 (0 unsure, 0 none) | 20/20 (0 unsure, 0 none) | 20/20 (0 unsure, 0 none) | 18/20 (2 unsure, 0 none) | finding 5/7 (jev) | fail |
| outcome.mutability | 3 | 16 | 15/16 (0 unsure, 0 none) | 13/16 (0 unsure, 0 none) | 16/16 (0 unsure, 0 none) | 10/16 (6 unsure, 0 none) | field-updatable 4/7 (jev) | fail |
| outcome.replication | 3 | 18 | 16/18 (0 unsure, 0 none) | 16/18 (0 unsure, 0 none) | 17/18 (0 unsure, 0 none) | 12/18 (3 unsure, 0 none) | unbounded 0/6 (jev) | fail |
| phase | 6 | 36 | 26/36 (0 unsure, 1 none) | 23/36 (0 unsure, 0 none) | 26/36 (0 unsure, 1 none) | 18/36 (15 unsure, 0 none) | strategy 1/5 (jev) | fail |
| reversibility | 3 | 19 | 19/19 (0 unsure, 0 none, 0 off by one) | 18/19 (0 unsure, 0 none, 1 off by one) | 19/19 (0 unsure, 0 none, 0 off by one) | 16/19 (3 unsure, 0 none, 0 off by one) | costly 4/5 (jev) | fail |
| time-separation | 4 | 31 | 30/31 (0 unsure, 0 none, 0 off by one) | 20/31 (0 unsure, 0 none, 10 off by one) | 30/31 (0 unsure, 0 none, 1 off by one) | 10/31 (15 unsure, 0 none, 5 off by one) | across-organisations 0/11 (jev) | fail |
| uptake | 3 | 19 | 19/19 (0 unsure, 0 none) | 18/19 (0 unsure, 0 none) | 19/19 (0 unsure, 0 none) | 17/19 (2 unsure, 0 none) | given 5/7 (jev) | fail |

Where misses went, expected → placed, with each reader's count:

- audience: Internal → Self (claude-fable-5-1 1, claude-opus-5-5 1)
- audience: Internal → unsure (jev 1)
- authority: None: Can the work go ahead without asking or telling anyone? → unsure (jev 2)
- authority: Discretionary: Is asking someone first a courtesy you may skip? → unsure (jev 2)
- maturity: Unproven → Scaling (claude-haiku-4-5-20251001 1)
- maturity: Proven → Scaling (claude-fable-5-1 2, claude-haiku-4-5-20251001 2, claude-opus-5-5 2, jev 2)
- maturity: Proven → unsure (jev 1)
- maturity: Scaling → Proven (claude-haiku-4-5-20251001 1)
- outcome.form: Finding → unsure (jev 2)
- outcome.mutability: Fixed at delivery → Field updatable (claude-haiku-4-5-20251001 1)
- outcome.mutability: Fixed at delivery → unsure (jev 1)
- outcome.mutability: Field updatable → unsure (jev 3)
- outcome.mutability: Field updatable → Fixed at delivery (claude-fable-5-1 1, claude-haiku-4-5-20251001 1)
- outcome.mutability: Field updatable → Continuously deployed (claude-haiku-4-5-20251001 1)
- outcome.mutability: Continuously deployed → unsure (jev 2)
- outcome.replication: Unbounded → Serial (claude-fable-5-1 1, claude-haiku-4-5-20251001 2, claude-opus-5-5 1, jev 3)
- outcome.replication: Unbounded → unsure (jev 3)
- outcome.replication: Unbounded → Singular (claude-fable-5-1 1)
- phase: Strategy: Who are we, where are we going, and why that way? → Discovery: What is worth solving, for whom, and is it viable? (claude-fable-5-1 2, claude-haiku-4-5-20251001 4, claude-opus-5-5 1, jev 3)
- phase: Strategy: Who are we, where are we going, and why that way? → unsure (jev 1)
- phase: Strategy: Who are we, where are we going, and why that way? → Operate: How is this carried out and kept working? (claude-opus-5-5 1)
- phase: Design: What are we building and how does it behave? → Strategy: Who are we, where are we going, and why that way? (claude-fable-5-1 1, claude-opus-5-5 1)
- phase: Design: What are we building and how does it behave? → unsure (jev 4)
- phase: Design: What are we building and how does it behave? → Architecture: How does it technically hold together? (claude-fable-5-1 1, claude-opus-5-5 1)
- phase: Design: What are we building and how does it behave? → Discovery: What is worth solving, for whom, and is it viable? (claude-haiku-4-5-20251001 2)
- phase: Design: What are we building and how does it behave? → Validation: How do we know it works? (claude-fable-5-1 1, claude-opus-5-5 1)
- phase: Validation: How do we know it works? → unsure (jev 3)
- phase: Validation: How do we know it works? → Design: What are we building and how does it behave? (claude-haiku-4-5-20251001 1)
- phase: Validation: How do we know it works? → Operate: How is this carried out and kept working? (claude-fable-5-1 2, claude-opus-5-5 2)
- phase: Architecture: How does it technically hold together? → Operate: How is this carried out and kept working? (claude-fable-5-1 2, claude-opus-5-5 1)
- phase: Architecture: How does it technically hold together? → unsure (jev 4)
- phase: Architecture: How does it technically hold together? → Design: What are we building and how does it behave? (claude-haiku-4-5-20251001 3, claude-opus-5-5 1)
- phase: Architecture: How does it technically hold together? → none (claude-fable-5-1 1, claude-opus-5-5 1)
- phase: Architecture: How does it technically hold together? → Discovery: What is worth solving, for whom, and is it viable? (claude-haiku-4-5-20251001 1)
- phase: Operate: How is this carried out and kept working? → unsure (jev 3)
- phase: Operate: How is this carried out and kept working? → Discovery: What is worth solving, for whom, and is it viable? (claude-haiku-4-5-20251001 2)
- reversibility: Reversible → unsure (jev 1)
- reversibility: Reversible → Costly (claude-haiku-4-5-20251001 1)
- reversibility: Costly → unsure (jev 1)
- reversibility: Irreversible → unsure (jev 1)
- time-separation: None → unsure (jev 6)
- time-separation: None → Across sessions (claude-haiku-4-5-20251001 3, claude-opus-5-5 1)
- time-separation: None → Across people (claude-fable-5-1 1, claude-haiku-4-5-20251001 1)
- time-separation: Across people → unsure (jev 4)
- time-separation: Across organisations → unsure (jev 5)
- time-separation: Across organisations → Across people (claude-haiku-4-5-20251001 7, jev 5)
- time-separation: Across organisations → Across sessions (jev 1)
- uptake: Given: Does it arrive whether or not they'd choose it? → unsure (jev 2)
- uptake: Given: Does it arrive whether or not they'd choose it? → Bought: Is paying how they take it up? (claude-haiku-4-5-20251001 1)

### Recognition by frame of `product-development`, OpenAI side

Run `universe-20261006T132135451825Z` (openai-side).

19 of 38 values fail (all readers); 5 of 38 (careful readers only). The careful readers are this side's judgment models: codex:gpt-6-astra, codex:gpt-6.1-sol.

Each reader's right / situations in the set; unsure and none count as misses, and on a ladder a miss one step away is counted as off by one.

| Set | Values | Situations | codex:gpt-6-astra | codex:gpt-6-luna | codex:gpt-6.1-sol | jev | Lowest value | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| audience | 5 | 28 | 28/28 (0 unsure, 0 none) | 28/28 (0 unsure, 0 none) | 28/28 (0 unsure, 0 none) | 27/28 (1 unsure, 0 none) | internal 4/5 (jev) | pass |
| authority | 5 | 40 | 40/40 (0 unsure, 0 none, 0 off by one) | 40/40 (0 unsure, 0 none, 0 off by one) | 40/40 (0 unsure, 0 none, 0 off by one) | 36/40 (4 unsure, 0 none, 0 off by one) | discretionary 3/5 (jev) | fail |
| maturity | 3 | 25 | 23/25 (0 unsure, 0 none, 2 off by one) | 23/25 (0 unsure, 0 none, 2 off by one) | 23/25 (0 unsure, 0 none, 2 off by one) | 22/25 (1 unsure, 0 none, 2 off by one) | proven 3/6 (jev) | fail |
| outcome.form | 3 | 20 | 20/20 (0 unsure, 0 none) | 20/20 (0 unsure, 0 none) | 20/20 (0 unsure, 0 none) | 18/20 (2 unsure, 0 none) | finding 5/7 (jev) | fail |
| outcome.mutability | 3 | 16 | 16/16 (0 unsure, 0 none) | 14/16 (0 unsure, 0 none) | 16/16 (0 unsure, 0 none) | 10/16 (6 unsure, 0 none) | field-updatable 4/7 (jev) | fail |
| outcome.replication | 3 | 18 | 18/18 (0 unsure, 0 none) | 18/18 (0 unsure, 0 none) | 15/18 (0 unsure, 0 none) | 12/18 (3 unsure, 0 none) | unbounded 0/6 (jev) | fail |
| phase | 6 | 36 | 30/36 (0 unsure, 0 none) | 31/36 (0 unsure, 0 none) | 32/36 (0 unsure, 0 none) | 18/36 (15 unsure, 0 none) | strategy 1/5 (jev) | fail |
| reversibility | 3 | 19 | 19/19 (0 unsure, 0 none, 0 off by one) | 17/19 (0 unsure, 0 none, 1 off by one) | 19/19 (0 unsure, 0 none, 0 off by one) | 16/19 (3 unsure, 0 none, 0 off by one) | reversible 5/7 (codex:gpt-6-luna) | fail |
| time-separation | 4 | 31 | 31/31 (0 unsure, 0 none, 0 off by one) | 28/31 (0 unsure, 0 none, 3 off by one) | 31/31 (0 unsure, 0 none, 0 off by one) | 10/31 (15 unsure, 0 none, 5 off by one) | across-organisations 0/11 (jev) | fail |
| uptake | 3 | 19 | 19/19 (0 unsure, 0 none) | 19/19 (0 unsure, 0 none) | 19/19 (0 unsure, 0 none) | 17/19 (2 unsure, 0 none) | given 5/7 (jev) | fail |

Where misses went, expected → placed, with each reader's count:

- audience: Internal → unsure (jev 1)
- authority: None: Can the work go ahead without asking or telling anyone? → unsure (jev 2)
- authority: Discretionary: Is asking someone first a courtesy you may skip? → unsure (jev 2)
- maturity: Proven → Scaling (codex:gpt-6-astra 2, codex:gpt-6-luna 2, codex:gpt-6.1-sol 2, jev 2)
- maturity: Proven → unsure (jev 1)
- outcome.form: Finding → unsure (jev 2)
- outcome.mutability: Fixed at delivery → Field updatable (codex:gpt-6-luna 1)
- outcome.mutability: Fixed at delivery → unsure (jev 1)
- outcome.mutability: Field updatable → unsure (jev 3)
- outcome.mutability: Field updatable → Fixed at delivery (codex:gpt-6-luna 1)
- outcome.mutability: Continuously deployed → unsure (jev 2)
- outcome.replication: Unbounded → Serial (codex:gpt-6.1-sol 3, jev 3)
- outcome.replication: Unbounded → unsure (jev 3)
- phase: Strategy: Who are we, where are we going, and why that way? → Discovery: What is worth solving, for whom, and is it viable? (codex:gpt-6-astra 3, codex:gpt-6-luna 3, codex:gpt-6.1-sol 3, jev 3)
- phase: Strategy: Who are we, where are we going, and why that way? → unsure (jev 1)
- phase: Design: What are we building and how does it behave? → unsure (jev 4)
- phase: Design: What are we building and how does it behave? → Architecture: How does it technically hold together? (codex:gpt-6-astra 1)
- phase: Design: What are we building and how does it behave? → Validation: How do we know it works? (codex:gpt-6-astra 1, codex:gpt-6-luna 1, codex:gpt-6.1-sol 1)
- phase: Validation: How do we know it works? → unsure (jev 3)
- phase: Architecture: How does it technically hold together? → Operate: How is this carried out and kept working? (codex:gpt-6-astra 1)
- phase: Architecture: How does it technically hold together? → unsure (jev 4)
- phase: Architecture: How does it technically hold together? → Design: What are we building and how does it behave? (codex:gpt-6-luna 1)
- phase: Operate: How is this carried out and kept working? → unsure (jev 3)
- reversibility: Reversible → Irreversible (codex:gpt-6-luna 1)
- reversibility: Reversible → unsure (jev 1)
- reversibility: Reversible → Costly (codex:gpt-6-luna 1)
- reversibility: Costly → unsure (jev 1)
- reversibility: Irreversible → unsure (jev 1)
- time-separation: None → unsure (jev 6)
- time-separation: None → Across sessions (codex:gpt-6-luna 1)
- time-separation: Across people → unsure (jev 4)
- time-separation: Across organisations → unsure (jev 5)
- time-separation: Across organisations → Across people (codex:gpt-6-luna 2, jev 5)
- time-separation: Across organisations → Across sessions (jev 1)
- uptake: Given: Does it arrive whether or not they'd choose it? → unsure (jev 2)

### Recognition by frame of `product-development`, who labelled the situations

Who wrote and labelled the situations: Anthropic side: extracted and written, and labelled blind, by Claude Fable 5.1 and Claude Opus 5.5; OpenAI side: labelled blind by GPT-6-Astra at xhigh, in the Codex app for rounds 1 and 2 and through the Codex CLI for round 3.

### Sorting of `product-development`, Anthropic side

Run `universe-20261006T050614485618Z` (anthropic-side).

Members: 123 pass, 8 fail, 4 undecided.

| Reader | Probes | Filed right | Unsure | Filed elsewhere |
| --- | --- | --- | --- | --- |
| claude-fable-5-1 | 270 | 270 | 0 | 0 |
| claude-haiku-4-5-20251001 | 270 | 265 | 0 | 5 |
| claude-opus-5-5 | 270 | 269 | 0 | 1 |
| jev | 270 | 261 | 6 | 3 |

### Sorting of `product-development`, OpenAI side

Run `universe-20261006T132135451825Z` (openai-side).

Members: 128 pass, 4 fail, 3 undecided.

| Reader | Probes | Filed right | Unsure | Filed elsewhere |
| --- | --- | --- | --- | --- |
| codex:gpt-6-astra | 270 | 270 | 0 | 0 |
| codex:gpt-6-luna | 270 | 269 | 0 | 1 |
| codex:gpt-6.1-sol | 270 | 270 | 0 | 0 |
| jev | 270 | 261 | 6 | 3 |

### Where the sides disagree on `product-development`

#### Case by case on `product-development`

Universe grade: the sides settled 3040 cases and differ on 488.

- `direct-statement` `artifacts.brand-identity-guide[0].claim`: Anthropic side pass, OpenAI side fail (judgment)
- `direct-statement` `artifacts.brand-identity-guide[1].claim`: Anthropic side undecided (owner), OpenAI side fail (judgment)
- `direct-statement` `artifacts.scenario-walkthrough[0].claim`: Anthropic side undecided (owner), OpenAI side pass
- `direct-statement` `artifacts.scenario-walkthrough[1].claim`: Anthropic side undecided (owner), OpenAI side pass
- `direct-statement` `artifacts[decision-record].enablement.action`: Anthropic side pass, OpenAI side undecided (owner)
- `direct-statement` `elements.alternatives-considered[0].claim`: Anthropic side fail (judgment), OpenAI side undecided (owner)
- `direct-statement` `elements.canonical-model[0].claim`: Anthropic side fail (judgment), OpenAI side undecided (owner)
- `direct-statement` `elements.canonical-model[3].claim`: Anthropic side undecided (owner), OpenAI side fail (judgment)
- `direct-statement` `elements.channels[0].claim`: Anthropic side pass, OpenAI side undecided (owner)
- `direct-statement` `elements.components-and-responsibilities[1].claim`: Anthropic side undecided (owner), OpenAI side pass
- `direct-statement` `elements.decision-criteria[2].claim`: Anthropic side fail (judgment), OpenAI side undecided (owner)
- `direct-statement` `elements.growth-mechanism[1].claim`: Anthropic side undecided (owner), OpenAI side fail (judgment)
- `direct-statement` `elements.guardrail-health-metrics[1].claim`: Anthropic side undecided (owner), OpenAI side fail (judgment)
- `direct-statement` `elements.input-metrics[2].claim`: Anthropic side undecided (owner), OpenAI side fail (judgment)
- `direct-statement` `elements.key-partnerships[2].claim`: Anthropic side pass, OpenAI side fail (judgment)
- `direct-statement` `elements.macro-environment-factors[4].claim`: Anthropic side undecided (owner), OpenAI side fail (judgment)
- `direct-statement` `elements.measurement-protocol[0].claim`: Anthropic side fail (judgment), OpenAI side undecided (owner)
- `direct-statement` `elements.open-questions[0].claim`: Anthropic side undecided (owner), OpenAI side pass
- `direct-statement` `elements.product-vision[0].claim`: Anthropic side undecided (owner), OpenAI side pass
- `direct-statement` `elements.product-vision[2].claim`: Anthropic side fail (judgment), OpenAI side pass
- `direct-statement` `elements.risks-and-assumptions[0].claim`: Anthropic side fail (judgment), OpenAI side undecided (owner)
- `direct-statement` `elements.scope-in-out[3].claim`: Anthropic side undecided (owner), OpenAI side fail (judgment)
- `direct-statement` `elements.verbal-identity-rules[1].claim`: Anthropic side undecided (owner), OpenAI side fail (judgment)
- `direct-statement` `universe.overview.covers`: Anthropic side pass, OpenAI side fail (judgment)
- `enablements-distinct` `artifacts[business-model-canvas].enablement`: Anthropic side undecided (owner), OpenAI side pass
- `enablements-distinct` `artifacts[startup-canvas].enablement`: Anthropic side undecided (owner), OpenAI side pass
- `holds-across-scope` `artifacts.brand-identity-guide[4].claim`: Anthropic side pass, OpenAI side undecided (owner)
- `holds-across-scope` `artifacts.decision-brief[1].claim`: Anthropic side pass, OpenAI side undecided (owner)
- `holds-across-scope` `artifacts.decision-brief[4].claim`: Anthropic side pass, OpenAI side fail (judgment)
- `holds-across-scope` `artifacts.decision-brief[5].claim`: Anthropic side pass, OpenAI side fail (judgment)
- `holds-across-scope` `artifacts.decision-record[4].claim`: Anthropic side pass, OpenAI side fail (judgment)
- `holds-across-scope` `artifacts.opportunity-assessment[0].claim`: Anthropic side pass, OpenAI side undecided (owner)
- `holds-across-scope` `artifacts.scenario-walkthrough[0].claim`: Anthropic side pass, OpenAI side undecided (owner)
- `holds-across-scope` `artifacts.success-metrics[0].claim`: Anthropic side fail (judgment), OpenAI side pass
- `holds-across-scope` `artifacts[business-model-canvas].enablement.action`: Anthropic side pass, OpenAI side undecided (owner)
- `holds-across-scope` `artifacts[lean-canvas].enablement.action`: Anthropic side pass, OpenAI side undecided (owner)
- `holds-across-scope` `artifacts[lean-canvas].enablement.timing`: Anthropic side undecided (owner), OpenAI side pass
- `holds-across-scope` `artifacts[product-strategy-canvas].enablement.timing`: Anthropic side pass, OpenAI side fail (judgment)
- `holds-across-scope` `artifacts[startup-canvas].enablement.action`: Anthropic side pass, OpenAI side undecided (owner)
- `holds-across-scope` `elements.capabilities[0].claim`: Anthropic side pass, OpenAI side fail (judgment)
- `holds-across-scope` `elements.case-for-change[1].claim`: Anthropic side pass, OpenAI side undecided (owner)
- `holds-across-scope` `elements.channels[1].claim`: Anthropic side pass, OpenAI side undecided (owner)
- `holds-across-scope` `elements.competitor-profile[2].claim`: Anthropic side fail (judgment), OpenAI side undecided (owner)
- `holds-across-scope` `elements.components-and-responsibilities[2].claim`: Anthropic side pass, OpenAI side undecided (owner)
- `holds-across-scope` `elements.customer-relationships[1].claim`: Anthropic side pass, OpenAI side fail (judgment)
- `holds-across-scope` `elements.data-flows-and-integrations[0].claim`: Anthropic side undecided (owner), OpenAI side fail (judgment)
- `holds-across-scope` `elements.decision[0].claim`: Anthropic side pass, OpenAI side undecided (owner)
- `holds-across-scope` `elements.decision[1].claim`: Anthropic side undecided (owner), OpenAI side pass
- `holds-across-scope` `elements.external-opportunities-threats[1].claim`: Anthropic side pass, OpenAI side undecided (owner)
- `holds-across-scope` `elements.growth-mechanism[0].claim`: Anthropic side undecided (owner), OpenAI side fail (judgment)

And 438 more.

Sorting: the sides settled 131 cases and differ on 6.

- `sorts-reliably` `artifacts[decision-record].composition.core[reversal-condition]`: Anthropic side fail (sort), OpenAI side pass
- `sorts-reliably` `artifacts[design-doc].composition.core[goals-and-non-goals]`: Anthropic side fail (sort), OpenAI side pass
- `sorts-reliably` `artifacts[design-doc].composition.core[problem-statement]`: Anthropic side fail (sort), OpenAI side pass
- `sorts-reliably` `artifacts[lean-canvas].composition.core[problem-statement]`: Anthropic side fail (sort), OpenAI side pass
- `sorts-reliably` `artifacts[scenario-walkthrough].composition.core[user-job-stories]`: Anthropic side fail (sort), OpenAI side pass
- `sorts-reliably` `artifacts[success-metrics].composition.core[north-star-metric]`: Anthropic side undecided (sort), OpenAI side fail (sort)

#### Frames and factors of `product-development`

The sides differ on 0 of 10 frames.

#### Judge pairs across the sides on `product-development`

| Pair | Cases | Pass | Fail | Undecided |
| --- | --- | --- | --- | --- |
| claude-opus-5-5 + codex:gpt-6-astra | 2936 | 2257 | 338 | 341 |
| claude-opus-5-5 + codex:gpt-6.1-sol | 2936 | 2298 | 330 | 308 |
| claude-fable-5-1 + codex:gpt-6-astra | 2936 | 2317 | 271 | 348 |
| claude-fable-5-1 + codex:gpt-6.1-sol | 2936 | 2357 | 262 | 317 |

### Retired for frames of `product-development`

Owner, 2026-10-05: the wording rules one-question, named-referents, direct-statement, plain-words, one-point-terse and holds-across-scope no longer apply to the questions of frames or factors, and siblings-differ applies only between frames or between factors. Frames are measured by whether readers recognise their values (values-recognised), because recognition is what frames are for.

The 26 fails below were found in `universe-20261005T045435502585Z`, the last full grade before the change, and are listed once here, not hidden.

| Rule | Where | Wording |
| --- | --- | --- |
| `one-question` | `frames[reversibility].question` | Can this step be undone, and at what cost? |
| `one-question` | `frames[phase].values[strategy].question` | Who are we, where are we going, and why that way? |
| `one-question` | `frames[phase].values[discovery].question` | What is worth solving, for whom, and is it viable? |
| `one-question` | `frames[phase].values[design].question` | What are we building and how does it behave? |
| `one-question` | `frames[phase].values[operate].question` | How is this carried out and kept working? |
| `named-referents` | `frames[phase].question` | Which stage of the work is this part of? |
| `named-referents` | `frames[phase].values[validation].question` | How do we know it works? |
| `named-referents` | `frames[phase].values[architecture].question` | How does it technically hold together? |
| `named-referents` | `frames[phase].values[operate].question` | How is this carried out and kept working? |
| `named-referents` | `frames[uptake].values[given].question` | Does it arrive whether or not they'd choose it? |
| `named-referents` | `frames[uptake].values[chosen].question` | Do they take it up only by deciding to, with nothing to pay? |
| `named-referents` | `frames[uptake].values[bought].question` | Is paying how they take it up? |
| `direct-statement` | `frames[reversibility].question` | Can this step be undone, and at what cost? |
| `direct-statement` | `frames[authority].question` | Who has to be asked or told before the work goes ahead? |
| `direct-statement` | `frames[phase].values[operate].question` | How is this carried out and kept working? |
| `direct-statement` | `frames[uptake].values[chosen].question` | Do they take it up only by deciding to, with nothing to pay? |
| `direct-statement` | `frames[authority].values[notify].question` | Must someone be told first, with no yes needed? |
| `plain-words` | `frames[maturity].question` | How settled is the bet this work rests on? |
| `plain-words` | `frames[audience].question` | Who is this artifact going to? |
| `plain-words` | `frames[phase].values[strategy].question` | Who are we, where are we going, and why that way? |
| `plain-words` | `frames[phase].values[architecture].question` | How does it technically hold together? |
| `holds-across-scope` | `frames[phase].values[design].question` | What are we building and how does it behave? |
| `holds-across-scope` | `frames[phase].values[architecture].question` | How does it technically hold together? |
| `siblings-differ` | `frames[phase].values[strategy].question ~ frames[phase].values[discovery].question` | Who are we, where are we going, and why that way? |
| `siblings-differ` | `frames[authority].values[none].question ~ frames[authority].values[discretionary].question` | Can the work go ahead without asking or telling anyone? |
| `siblings-differ` | `frames[authority].values[approve].question ~ frames[authority].values[statutory].question` | Does someone's yes have to come first? |

## Cost and models

Dollar costs are API prices, as each CLI reports them. On a Claude or ChatGPT subscription, runs use the plan's limits instead.

| Run | Side | Models | Cost |
| --- | --- | --- | --- |
| `examples-universe-20261006T060659282403Z` (anthropic-side) | Anthropic side | decision: jev jev-1.13.0; judgment: judges: claude-opus-5-5, claude-fable-5-1; recognise: filers: claude-opus-5-5, claude-fable-5-1, jev jev-1.13.0, claude-haiku-4-5-20251001; sort: filers: claude-opus-5-5, claude-fable-5-1, jev jev-1.13.0, claude-haiku-4-5-20251001 | decision tokens: 8337; judgment cost: $3.38; sort and recognise cost: $0.85; sort and recognise decision tokens: 9434 |
| `examples-skills-20261006T134912752473Z` (anthropic-side) | Anthropic side | decision: jev jev-1.13.0; judgment: judges: claude-opus-5-5, claude-fable-5-1 | decision tokens: 14010; judgment cost: $3.01 |
| `universe-20261006T050614485618Z` (anthropic-side) | Anthropic side | decision: jev jev-1.13.0; judgment: judges: claude-opus-5-5, claude-fable-5-1; recognise: filers: claude-opus-5-5, claude-fable-5-1, jev jev-1.13.0, claude-haiku-4-5-20251001; sort: filers: claude-opus-5-5, claude-fable-5-1, jev jev-1.13.0, claude-haiku-4-5-20251001 | decision tokens: 31028; judgment cost: $44.27; sort and recognise cost: $22.88; sort and recognise decision tokens: 363972 |
| `play-20261006T134912768658Z` (anthropic-side) | Anthropic side | agent: claude 2.1.280 (Claude Code), model claude-opus-5-5; decision: jev jev-1.13.0; judgment: judges: claude-opus-5-5, claude-fable-5-1 | agent cost: $24.58; decision tokens: 31898; judgment cost: $46.28 |
| `examples-universe-20261006T132135450769Z` (openai-side) | OpenAI side | decision: jev jev-1.13.0; judgment: judges: codex:gpt-6-astra, codex:gpt-6.1-sol; recognise: filers: codex:gpt-6-astra, codex:gpt-6.1-sol, jev jev-1.13.0, codex:gpt-6-luna; sort: filers: codex:gpt-6-astra, codex:gpt-6.1-sol, jev jev-1.13.0, codex:gpt-6-luna | decision tokens: 8337, spent by examples-universe-20261006T060659282403Z and reused here; judgment cost: n/a (answered in the Codex app, which reports no cost); sort and recognise cost: n/a (answered in the Codex app, which reports no cost); sort and recognise decision tokens: 9434, spent by examples-universe-20261006T060659282403Z and reused here |
| `examples-skills-20261006T132135451472Z` (openai-side) | OpenAI side | decision: jev jev-1.13.0; judgment: judges: codex:gpt-6-astra, codex:gpt-6.1-sol | decision tokens: 14010, spent by examples-skills-20261006T050332458585Z and reused here; judgment cost: n/a (answered in the Codex app, which reports no cost) |
| `universe-20261006T132135451825Z` (openai-side) | OpenAI side | decision: jev jev-1.13.0; judgment: judges: codex:gpt-6-astra, codex:gpt-6.1-sol; recognise: filers: codex:gpt-6-astra, codex:gpt-6.1-sol, jev jev-1.13.0, codex:gpt-6-luna; sort: filers: codex:gpt-6-astra, codex:gpt-6.1-sol, jev jev-1.13.0, codex:gpt-6-luna | decision tokens: 31028, spent by universe-20261006T050614485618Z and reused here; judgment cost: n/a (answered in the Codex app, which reports no cost); sort and recognise cost: n/a (answered in the Codex app, which reports no cost); sort and recognise decision tokens: 363972, spent by universe-20261006T050614485618Z and reused here |

## Not measured here

- Effect on outcomes: whether these universes and skills change what people get done.
- How often agent behaviours pass over many runs.
- Owners who go off script, and whether the definitions fit real work.
- Whether wording is plain to people rather than models.

## How to reproduce

```sh
# 1. Calibration on the labelled examples, both slices
just evals-calibrate universe
just evals-calibrate skills
# 2. Universe grade and sorting, once per universe
just evals-grade <universe file> deterministic,decision,judgment,sort
# 3. Recognition of frame and factor values, once per universe
uv run --locked python tools/evals/grade.py universe --universe <universe file> \
  --tiers recognise --rules values-recognised
# 4. Agent scenarios
just evals-play --runs 3
# Summaries and this report
just evals-report
```

List each run folder in `evals/runs.yaml` before `just evals-report`. The runbook for the OpenAI side is in `evals/README.md`, under "Running on another vendor".
