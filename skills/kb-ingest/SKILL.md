---
name: kb-ingest
description: Map existing notes or documents into Knowledge Bus definitions and sourced answers, surfacing conflicts and gaps without changing source files.
---

# Ingest a Knowledge Base

**Purpose — turn a folder the user no longer trusts into a spec they can trust, with every mapping decision visible and every refusal recorded.**

## Standing constraints

- **Source files are read-only.** Write only within `<target>/.knowledge-bus/`; never modify existing source files.
- **Separate target folders.** Exclude every `.knowledge-bus/` directory from source discovery. Skip and report nested folders with their own `.knowledge-bus/`; ingest those separately only when explicitly targeted.
- **Review existing outputs.** Before writing, inspect existing definitions, guidance, answers, and logs. Reuse the established definitions or propose deliberate changes. Preserve prior decisions and history; do not reset or blindly overwrite files. Stop on incompatible or ambiguous existing content and ask how to proceed.
- **Directory contract.** Follow [Knowledge Bus Directory](references/knowledge-bus-directory.md). No sibling-output discovery or migration is performed.
- **Questions are earned.** Reason through everything gathered so far before asking; a question the corpus can answer is never put to the user. The interview carries judgment to the user, not work.
- **Interview in the user's language.** Format vocabulary — spec, collision, staleness marks, placement — never appears in a question. The user is asked about their project in its own terms; the mechanism stays in the reasoning and the log.
- **A forced mapping is worse than a refusal.**
- **Report before writing.** The user sees the survey and the spec choice before any answer is filed.

## The flow

- **1. Confirm the target folder.** Only the source folder is asked for. Output goes to `<target>/.knowledge-bus/` by
  convention. Inspect that directory if it already exists; the domain phrase is proposed after the survey and confirmed, never requested cold.

- **2. Survey before reading.** Inventory files, dates, and formats; report counts to the user before any deep read.
  Three staleness marks: **contradicted** (a newer source disputes it — mechanical), **unconfirmed**
  (older than the corpus's age threshold, nothing disputes it), **confirmed** (cleared during the interview).
  Confirmation questions come batched and informed — reason through the whole survey first so the user rules
  on genuine uncertainty, not on what the corpus already settles.

- **3. Position the domain, then choose the spec.** Locate the starter using [Checker for Agent Workflows](references/agent-runtime.md). Reason over the folder
  and whatever the user supplied, clarifying unclear questions by probing what answering each would enable and checking for overlap,
  then interview to place the domain against the product-agnostic built-in: how regulated or commercial
  versus DIY, and where the abstraction layer sits — industry, company, product, or feature. Adopt, trim,
  or derive follows from that placement; structural changes require the user's review. If `kb-evolve` is installed, offer it; otherwise explain the proposed change and stop before changing the structure.

- **4. Extract answers.** Map each document section to a declared question; one answer per question per party and time.
  A collision — two docs answering the same question — is never resolved by recency. The older doc may be the
  forgotten original and the newer a lacking recollection; authority and authorship matter. Surface the collision
  with its provenance (age gap, authors, what each claims) and put an informed question to the user in the interview.
  Rulings live in the ingest log, not on answers: each entry records the collision, the ruling, who ruled, and the
  reasoning. Answers stay clean; a collision the user declines to rule is filed **contested**.

- **5. Refuse honestly.** Content answering no declared question is flagged, never forced into a near-fit; core questions with no answer are listed as gaps.
  Refusals repeating on one theme signal a missing question — offer structural review (`kb-evolve` if installed) — rather than off-domain content.

- **6. Write the outputs.** The universe (`universe.kbp.yaml`), optional guidance (`type-guidance.kbp.yaml`), answers, and the ingest log all go in `<target>/.knowledge-bus/`.
  Existing source files remain untouched. Answers go in `answers.yaml`, one record
  per answer: `element`, `party`, `date`, `status`, `answer`, `source`, and `supersedes` where a ruling
  displaced something; gaps list `element` and `reason`. The shape is fixed; the checker does not yet
  validate it.

- **7. Validate.** Follow [Checker for Agent Workflows](references/agent-runtime.md) and run the bundled checker with `--validate <target>/.knowledge-bus/`. Fix or surface every refusal before reporting. Only definition and guidance files are checked; answers and the log require review.

- **8. Report coverage.** One table, **contested** first — unresolved collisions block trust — then mapped,
  stale (contradicted or merely unconfirmed), refused, gaps. Each class names its ask: rule it; spot-check;
  confirm or retire; accept as off-domain or review a proposed new question; answer, or record what an
  honest empty means.
