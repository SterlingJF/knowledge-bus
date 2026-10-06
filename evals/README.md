# Evals

These files define what good looks like for Knowledge Bus: rules for definitions, behaviours for
agents, and examples from real cases showing each one passing and failing.

## Layout

| Path                | Holds                                                                                                                           |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `universe.yaml`     | The universe slice: rules for the text of definitions                                                                           |
| `skills.yaml`       | The skills slice: behaviours of an agent doing knowledge work with the owner                                                    |
| `fixtures/`         | Small folders, set in unrelated fields, that the skills scenarios run against                                                   |
| `situations/`       | Real cases shared by every universe, and each universe's answers over them                                                      |
| `runs.yaml`         | The run folders behind the report                                                                                               |
| `results/`          | One small summary per run, written by `tools/evals/report.py`                                                                   |
| `report.md`         | The report built from the summaries; never edited by hand                                                                       |
| `retired/`          | Per universe (`<universe-id>.yaml`), the frame fails the owner retired                                                          |
| `generated/claude/` | `claude plugin eval` cases written from `universe.yaml`; never edited by hand                                                   |
| `../tools/evals/`   | The reader, tier engine, adapters, grader, generator, scenario player, report builder, situation intake and desktop-app packets |

The spec, fixture, situations and retired files name no tool or vendor.
Run records name sides and models by design: `runs.yaml`, `results/` and `report.md` say which side
and which models produced each figure. Vendor code lives only in `tools/evals/adapters.py`,
`tools/evals/packet.py` and the generators.

## Two slices

- **Universe** grades definitions: element questions, artifact actions, actors and timings,
  guidance claims, the universe overview and the meanings of its terms. Frames and factors are
  measured by whether readers recognise their values (see the recognition check); their questions
  keep only `one-term-per-concept`, and `siblings-differ` between frames or between factors. It
  runs on any universe file, with no agent involved. Each one-term-per-concept case also sees the
  universe's declared terms, for reference. For runners that test the plugin, each rule's first
  failing example becomes one outcome case: a skill improves the text, and the rule grades the
  reply.
- **Skills** grades what an agent does while it works with the owner: the questions it asks, the
  reports it gives, how it uses evidence, what it writes and where. When a skill proposes a
  definition, the skills slice grades that definition with the universe rules.

Each skills scenario is modelled on a session: the owner's opening request, the owner's replies in
order, and the behaviours the run must show. Its `fixture` is `none`, a folder in this
repository, or `needs:`, which states what the folder must hold until someone builds it.

## Scope

A rule's `scope` says what one case is:

- `item` (the default): one text, judged alone.
- `pair`: two sibling texts in the same list, compared.
- `set`: one member, judged as part of its whole set. Element questions form one set, and so do
  artifact enablements. Each artifact's composition is its own set, and so are each frame's or
  factor's values, or each facet's.

Two subjects exist for set rules. `artifact.enablement` renders each enablement as one line,
`action: ...; actor: ...; timing: ...`. `artifact.composition` makes one member per core or
situational entry. Its text is the element's question, and it carries the artifact's enablement
and its strength: `core`, `situational`, or either one followed by `when` and the frame
condition, as in `core when authority is approve or statutory`. `frame.value` and `factor.value`
make one member per value, shown as the explorer shows it: the id in words, then its question
when it has one, as in `Approve: Does someone's yes have to come first?` or `Across sessions`.

A set example's `context.set` lists the whole set in order, including the example's own text. A
composition example lists each member as `<strength>: <question>`, as the grader shows it.

## The sort check

A set rule may have a `sort` block (`ask` and `write`) in place of tiers. It tests whether a
passage that answers one member's question gets filed under that member:

1. Probes. A writer model gets the member's question and `write`, and returns passages. Any
   passage that shares a content word with the question is dropped and the writer asked again,
   at most twice. A passage stays only when every judgment model, seeing it and the question
   alone, says it answers the question. Examples bring their own probes in `context.probes`.
   In a universe run, the writer, the validity check and every model filer also see the
   universe's overview (what it covers, who it is for, what it excludes), so each question is
   read within the universe it belongs to.
2. Filing. Each probe is filed among the set's questions, shown without strengths, by each
   judgment model, by the decision model as a typed choice, and by a light model
   (`--light-model`).
3. Verdict. A member passes when every filer files every probe under it. Otherwise it fails,
   and the reason names where a probe went. With no valid probe, or a filer call that failed,
   it is undecided, and so it is when the decision model was unsure and no filer put a probe
   elsewhere. Without `TYPESAFE_API_KEY` the decision-model filer is skipped and the
   report says so.

A universe run writes its probes to `probes.json`. Pass that file back with `--probes` so a
before and an after grade file the same passages.

## The recognition check

A set rule may have a `recognise` block (`ask`, `value_share`, `frame_share`) in place of tiers.
It tests whether readers place an everyday situation under the right frame value:

1. Situations. Real cases, de-identified, are shared by every universe and stored once in
   `evals/situations/cases.yaml`, each with its text, the field it comes from and its tags.
   The right answers are kept per universe in `evals/situations/<universe-id>.yaml`: for each
   frame, facet or factor, the value meanings the labels were made against, `ladder: true` when
   the values are steps (lowest first), a fingerprint, and each case's value (with `near` for a
   ladder case close to a neighbouring step). The fingerprint covers the set's id, its value
   ids in order and their meanings. Rewording a question keeps the answers, since the wording
   is what recognition tests; adding, removing or redefining a value makes them stale, and
   stale sets read "not run" until relabelled. The universe file holds no meanings, so a
   value is redefined by editing its meaning in that set's `means` in each answers file that
   has the set; the fingerprint then fails until the set is relabelled (see "Adding situations
   for a universe"). Counting only cases from the universe's own
   field, each value needs at least 4 and each set at least 12, every tag value not declared
   absent in the universe's answers file appears at least twice per set, and on a ladder each
   pair of neighbouring steps has a `near` case on each side. No case shares a content word
   with the wording it is filed under, in any universe that uses it, or names a vendor,
   product or identifier. A set of one value, such as
   the placeholder ordering frame a factor-only universe declares, offers no choice, so it has
   no answers and is not checked. `just evals-check` refuses files that fall short. Writers
   and labellers never see the wording. Every run records the answers file's digest and a
   digest of only the cases it uses, so cases another universe adds leave runs comparable.
   Examples bring their own situations in `context.probes`. A universe without an answers
   file, or with one that names another universe, reads "not run", never pass.
2. Filing. The same filers as the sort check each get one situation per call, under the
   frame's question, with the set's values as the options.
3. Verdict. A value passes when every filer files at least `value_share` of its situations under
   it and at least `frame_share` of the set's situations rightly. A value fails when a filer
   misses its share, or misses the set's share having misplaced one of the value's own
   situations. Unsure and none count as misses. The run report's "Recognition by frame" table
   counts them apart, and counts a ladder miss one step away as off by one.

## Three tiers

Each rule or behaviour uses the tiers that add something, in this order. The first tier that
returns pass or fail settles the case; a case no tier settles goes to the owner.

| Tier            | Decides with                                                                                                                                                                                                                                                   | Suits                                         |
| --------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------- |
| `deterministic` | code: portable regex, whole-word terms, word counts, path globs                                                                                                                                                                                                | conditions visible in the text                |
| `decision`      | one typed question (yes-no, choice or score) to a fast classifier                                                                                                                                                                                              | a literal reading of the text alone           |
| `judgment`      | two Claude models by default (see Model selection), reading PASS and FAIL criteria; within a side both come from one company and are a consistency check, and the two-company rule is applied across the sides, in the report's "Judge pairs across the sides" | nuance; a verdict stands only when both agree |

A deterministic check either fails a case (`then: fail`) or flags it for the next tier
(`then: flag`). The decision model reads literally and cannot count, so counts stay in code.
A decision question suits a rule only when one literal question about the text settles it; where
literal reading misfires, the rule has no decision tier. When the two judgment models split, the
case is undecided and goes to the owner.

## Commands

| Command                 | Does                                                                     |
| ----------------------- | ------------------------------------------------------------------------ |
| `just evals-check`      | Checks structure and generated files. Free; runs with the test suite     |
| `just evals-grade`      | Grades the product-development universe: all tiers, sort and recognition |
| `just evals-calibrate`  | Scores each tier alone on the owner's labelled examples                  |
| `just evals-write`      | Regenerates `generated/claude/`                                          |
| `just evals-run-claude` | Runs the generated cases against the assembled plugin                    |
| `just evals-play`       | Plays the skills scenarios with a scripted owner, then grades them       |
| `just evals-report`     | Writes `report.md` and `results/` from the runs in `runs.yaml`. Free     |

`evals-grade`, `evals-calibrate`, `evals-run-claude` and `evals-play` call paid models and write to
`.evidence/<date>/evals/<run>/`. The decision tier reads `TYPESAFE_API_KEY`; the judgment tier
uses the CLI of each model it names. Without either, that tier is skipped and the report says so.
To grade in code only, run
`just evals-grade universes/product-development/universe.kbp.yaml deterministic`.

### Model selection

`grade.py` takes `--judge-model` (one model, or several separated by commas) and `--light-model`.
A name such as `codex:<model>` runs through `codex exec`; any other name runs through the `claude`
CLI. A CLI is needed only when one of its models is named. Codex calls switch off the Codex
home's own skills per call. A home with its own `AGENTS.md` is still refused, since nothing turns
it off per call. Only then is a separate login needed (`CODEX_HOME=<folder> codex login`).
`--label` names the run in `run.json`. Each
verdict row's trail keeps every judge's vote and every filer's placements, and costs are recorded
as each CLI reports them (dollars, tokens, or n/a).

## How examples are made

Standards come from the owner's corrections and standing rules, restated in plain words. Texts the
owner only accepted do not count as passes: acceptance can mean the owner gave up. Nothing is
invented: each example starts from a specific real case, restated in an unrelated field such as a
choir, a bakery or a permit office, shares no run of 7 words with its source, and identifies no
person, project or session; its provenance stays privately outside the repository. With no real
case there is no example. Before an example joins a rule, a blind reader and a decision model each
judge it against the rule's statement alone; it stays only when the reader agrees with its verdict
and the decision model does not confidently disagree.

## Add a rule

1. State the bar in at most 14 words, and say in `why` what goes wrong without it.
2. Extract examples from real cases and de-identify them as above, at least two failing and two
   passing, each with a `note` that says why.
3. Run `just evals-check`, then `just evals-calibrate`. A tier that disagrees with the examples
   gets a sharper question, or leaves the rule.

## Adding situations for a universe

Situations come from real cases, never invented ones. Work in a folder outside the repository:
it holds the source pages and the provenance, which never enter the repository. The tool is
`tools/evals/intake.py`, run as `uv run --locked python tools/evals/intake.py`.

1. Extract. For each value of each frame, facet or factor, find real public cases from the
   universe's own field: help pages, decision records, service pages, published case studies.
   Save each source page as text under `<folder>/sources/`, and keep its provenance (address,
   type, date, why it fits) in the folder too. Leave out the owner's private sessions.
2. Rewrite blind. A writer who sees only the value meanings, never the universe's wording,
   restates each case in new words in `<folder>/draft.yaml`, with no names, organisations,
   products, places, dates or identifiers:

   ```yaml
   universe: <universe-id>
   field: <field> # optional; the cases' field, by default the universe id
   tags: { kind: [creation, service, finding], who: [one, group, organisation] }
   frames:
     <frame or frame.facet>:
       ladder: true # only when the values are steps, lowest first
       means: { <value>: <what the value means>, ... }
       situations:
         - { id: <universe-id>-<n>, text: ..., value: <value>, near: <neighbouring step>, kind: ..., who: ... }
         - { case: <id of a case already in cases.yaml>, value: <value> }
   ```

   `near` marks a ladder case close to a neighbouring step; each pair of steps needs one on
   each side. Lead each writer id with the universe id: a situation's packet id, which becomes
   its case id, is made from the writer id alone, and the packet refuses one that is already
   another case in the pool. A `case:` entry reuses a case from another field, which is the
   point of sharing them: it goes into the packet under its own id and pool text, its answer
   is kept, and the case is not added again. Such cases never count toward the minimums, which
   need the universe's own field. The pool's `tags` are shared by every universe, and
   `cases.yaml` gives each tag value a one-line meaning to tag by: every case carries every tag,
   so a draft uses the tags `cases.yaml` already declares (today the two above). Changing them
   is an owner decision, since it means retagging every case. Only a draft that starts a new
   pool, where no `cases.yaml` exists yet, writes each tag value with its meaning
   (`{ kind: { creation: <meaning>, ... }, ... }`); those become the pool's `tags`.
3. Gate. `intake.py gate <universe-id> --folder <folder>` fails any situation that shares a run
   of 7 words with a saved source, holds an identifying term or names a vendor or brand. Reword
   until it passes, without bending the facts.
4. Label blind, this side. A reader who did not write the situations labels them from the
   meanings alone. Drop each one the reader places elsewhere.
5. Select, quality first. Keep only the clearest cases: one value plainly fits, the source was
   re-read and supports it, and nothing was bent to remove identifying detail. Stop at the
   minimums. A tag value the field cannot offer is declared absent in `<universe-id>.yaml`, as
   `absent: {<tag>: {<value>: {reason, source}}}` with a public source that supports it. A frame
   or factor value that runs short is reported to the owner, and its set cannot be saved until
   real cases are found; it is never padded.
6. Label blind, the other side. `intake.py packet <universe-id> --folder <folder>` writes
   `packet.md`: the meanings, and the texts under opaque ids in a fixed shuffled order. The
   owner gives it to the other side's model and saves the reply as `<folder>/labels.json`.
   The packet tells labellers that on a ladder a case belongs to the highest step that
   applies; recognition readers are not told, and the report counts one-step-off misses
   apart.
7. Apply. `intake.py apply <universe-id> --folder <folder> --dry-run` reports agreement and
   every dropped situation; without `--dry-run` it writes. A situation stays only where the
   other side's label equals the written value. Kept cases join `cases.yaml` under their
   packet id, with the universe id as their field unless `--field` (or the draft's `field`)
   names another, and the universe's answers go to `<universe-id>.yaml`. A set the draft
   leaves out keeps its stored answers. A set whose meanings differ from the stored ones is a
   relabel, and its answers are replaced; any other set must keep every stored answer. Apply
   writes nothing while a label is missing (set one the reply left out to `unsure`) or any
   check fails, such as a value below its minimum: find more real cases. Then run
   `just evals-check`.

To relabel a set after redefining or adding a value, put the new meanings in a draft that names
that set, with its situations (cited `case:` entries for the ones already in the pool), and run
steps 6 and 7 again.

No shared frame library exists yet. A frame joins one only when two or more presets ask the same
question independently and it passes blind recognition with a real spread of values across
fields, not one value covering every case.

## Running on another vendor

The OpenAI side runs the same measures with its own models through the Codex CLI, on a
subscription, and brings back run folders. It needs no code change. Use the same checkout as the
Anthropic side: the report puts the sides next to each other only when the input digests match.

Set up once:

- The `codex` CLI on `PATH`, logged in. The Codex home's own skills are switched off per call. A
  home with its own `AGENTS.md` is still refused, since nothing turns it off per call. Only then
  log in from a separate home, `CODEX_HOME=<folder> codex login`, and keep `CODEX_HOME=<folder>`
  set.
- `TYPESAFE_API_KEY` set, for the decision model (Jev). Without it the decision tier and the
  decision-model filer are skipped, and the run's notes say so.
- Two careful models and one light model, named below as `<careful-a>`, `<careful-b>` and
  `<light>`. Every model is passed as `codex:<name>`.

From the repository root, each command prints the run folder it wrote:

```sh
# 1. Calibration on the labelled examples, both slices
uv run --locked python tools/evals/grade.py examples --slice universe \
  --judge-model codex:<careful-a>,codex:<careful-b> --light-model codex:<light> --label openai-side
uv run --locked python tools/evals/grade.py examples --slice skills \
  --judge-model codex:<careful-a>,codex:<careful-b> --light-model codex:<light> --label openai-side

# 2. Universe grade, filing the passages the Anthropic side wrote (its run's probes.json)
uv run --locked python tools/evals/grade.py universe --tiers deterministic,decision,judgment,sort \
  --judge-model codex:<careful-a>,codex:<careful-b> --light-model codex:<light> \
  --probes <anthropic-side-run-folder>/probes.json --label openai-side

# 3. Recognition of frame values, on the frozen situations in evals/situations/
uv run --locked python tools/evals/grade.py universe --tiers recognise --rules values-recognised \
  --judge-model codex:<careful-a>,codex:<careful-b> --light-model codex:<light> --label openai-side

# 4. Scenarios, <n> runs each, matching the Anthropic side in the report
uv run --locked python tools/evals/play.py --agent codex --model <agent-model> --runs <n> \
  --judge-model codex:<careful-a>,codex:<careful-b> --label openai-side
```

The Anthropic side runs the same four steps with its default models, so each grade figure covers
the same rules on both sides; `evals/report.md` lists those commands under "How to reproduce".
Steps 2 and 3 grade product-development by default; for another universe, add
`--universe <its file>` to both, and step 3 reads its answers from
`evals/situations/<universe-id>.yaml`.

Bring back the run folders themselves, one per command (`calibration.json` or `verdicts.jsonl`,
`run.json`, `report.md` and, for step 2, `probes.json`), and the models you chose. They hold no
credentials. Copy them under `.evidence/<date>/evals/` in the consolidating checkout, add each to
`evals/runs.yaml` with `side: openai` (and `universe: <id>` for a universe grade, if `run.json`
does not name it), and run `just evals-report`. A run listed on the OpenAI side is refused if any
judge, light, filer or agent model is not `codex:<model>`, and the reverse on the Anthropic side;
Jev serves both. A step that was not run reads "not run" in the
report. The report keeps one section per universe and never compares runs of different universes.

### In a desktop app, one session per model

Steps 1 to 3 can instead be answered in the Codex desktop app, one session per model, with every
packet in one prompt. `tools/evals/packet.py` mirrors the Anthropic side's finished run folders
(both calibrations and each universe grade) and needs no `codex` CLI:

```sh
# 1. Packets: a folder per model, each with PROMPT.md to paste into one session
uv run --locked python tools/evals/packet.py build \
  --anthropic-run <anthropic-run-folder> --anthropic-run <anthropic-run-folder> ... \
  --out <packets-folder>

# 2. Once every session has written its replies: one run folder per Anthropic run
uv run --locked python tools/evals/packet.py apply \
  --anthropic-run <the same folders, in the same order> --replies <packets-folder> \
  --label openai-side [--effort codex:<model>=<level> ...]
```

Put the packets folder outside any repository checkout, so the app loads no project
instructions, skills or plugins with it; it can be moved before the sessions start. Open each
model's folder as its own project, pick that model, and paste its `PROMPT.md`. The two
careful models get every packet; the light model gets only the filing ones. Each packet is exactly
a prompt `grade.py` sends, in `grade.py`'s order, and holds no answer, verdict, run id or model
name; the instructions `grade.py` sends as the system prompt are given once in `PROMPT.md`.
`manifest.json`, beside the folders, never goes into a session. `--effort` records the reasoning effort chosen in the app for each model. `apply` refuses while any reply is
missing, does not fit its schema or answers other items than its packet holds, and when an
Anthropic run or its inputs changed since `build`.

Only the judges and the model filers come from the replies. The deterministic tier, the decision
tier (Jev), Jev's filings and a universe's sort passages (`probes.json`) are the same on both
sides, so they are reused from the Anthropic run, and each run's notes say so and how the packets
were answered. A calibration written before `grade.py` kept each example's placements has no Jev
filings to reuse: Jev then does not file in it, and its notes say so. Add the run folders to
`evals/runs.yaml` as above. Step 4, the scenarios, still needs the CLI.

## Runners

The spec is written once and translated per runner. Each translation states what it drops.

| Spec                          | Claude (`claude plugin eval`)                                 | OpenAI Evals API                                                     | MCPJam eval suites                                                              |
| ----------------------------- | ------------------------------------------------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| A rule on a declared text     | graded by `tools/evals/grade.py` directly                     | one data item per text; graders as below                             | out of scope: suites test MCP tool calls, and Knowledge Bus ships no MCP server |
| An outcome case               | generated: a skill fixes a failing example                    | item is the prompt; grades a bare model, without the plugin's skills | a case judged on `expectedOutput`, hosted runs only                             |
| `deterministic`, `then: fail` | `regex` grader, `match: not_contains`                         | `python` grader                                                      | not carried                                                                     |
| `deterministic`, `then: flag` | no grader; flags only nominate                                | no grader                                                            | not carried                                                                     |
| `decision`                    | asked of the `llm` grader (approximated)                      | `label_model` grader with the typed labels                           | judge rubric (approximated)                                                     |
| `judgment`                    | `llm` grader                                                  | `label_model` grader with pass and fail labels                       | judge rubric                                                                    |
| `judgment` on a set rule      | `llm` grader; the case prompt shows the set                   | model grader, with the set in the data item                          | judge rubric, with the set in the prompt                                        |
| `sort`                        | not carried; graded by `tools/evals/grade.py` only            | classification eval of probes; see below                             | no mapping                                                                      |
| `recognise`                   | not carried; graded by `tools/evals/grade.py` only            | classification eval of situations; see below                         | no mapping                                                                      |
| A skills scenario             | played by `tools/evals/play.py`, not by `claude plugin eval`  | multi-turn runs are not native; recorded transcripts can be items    | out of scope                                                                    |

On the OpenAI Evals API a sort rule is a classification eval: each data item is a probe with
the question it should be filed under, the light model is the model under test, and a
`string_check` grader compares its answer with that question. A recognise rule is the same, with
one data item per situation and its expected value. A set judgment rule uses a model grader and
carries the set in the data item. MCPJam has no mapping for sort or recognise.

Only the Claude translation is generated today. `generated/claude/README.md` lists what it
approximates.
