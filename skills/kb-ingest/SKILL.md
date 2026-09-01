---
name: kb-ingest
description: Convert a folder of scattered or stale docs into a validated
  spec — a declared set of questions with sourced answers that agents can
  consume without re-reading the corpus. Surveys the source folder, adopts or
  adapts the built-in product-development spec (or derives a new one), files
  each finding as an answer to a declared question, flags stale or
  unanswerable content, and validates the result with the bundled kbp
  checker. Use when invoked via /kb-ingest, or when the user asks to
  restructure, consolidate, or spec-ify existing documentation or notes.
---

# Ingest a Knowledge Base

**Purpose — turn a folder the user no longer trusts into a spec they can trust, with every mapping decision visible and every refusal recorded.**

## Standing constraints

- **Sources are read-only.** Ingest never writes into the source folder; outputs land in a sibling directory.
- **Questions are earned.** Reason through everything gathered so far before asking; a question the corpus can answer is never put to the user. The interview carries judgment to the user, not work.
- **Interview in the user's language.** Format vocabulary — spec, collision, staleness marks, placement — never appears in a question. The user is asked about their project in its own terms; the mechanism stays in the reasoning and the log.
- **A forced mapping is worse than a refusal.**
- **Report before writing.** The user sees the survey and the spec choice before any answer is filed.

## The flow

- **1. Confirm scope.** Only the source folder is asked for. Output goes to the `<folder>-spec/` sibling by
    convention; the domain phrase is proposed after the survey and confirmed, never requested cold.

- **2. Survey before reading.** Inventory files, dates, and formats; report counts to the user before any deep read.
    Three staleness marks: **contradicted** (a newer source disputes it — mechanical), **unconfirmed**
    (older than the corpus's age threshold, nothing disputes it), **confirmed** (cleared during the interview).
    Confirmation questions come batched and informed — reason through the whole survey first so the user rules
    on genuine uncertainty, not on what the corpus already settles.

- **3. Position the domain, then choose the spec.** Reason over the folder
    and whatever the user supplied, calling `/kb-uncover-question` where the domain's questions are unclear,
    then interview to place the domain against the product-agnostic built-in: how regulated or commercial
    versus DIY, and where the abstraction layer sits — industry, company, product, or feature. Adopt, trim,
    or derive follows from that placement; structural changes hand off to `/kb-evolve`.

- **4. Extract answers.** Map each document section to a declared question; one answer per question per party and time.
    A collision — two docs answering the same question — is never resolved by recency. The older doc may be the
    forgotten original and the newer a lacking recollection; authority and authorship matter. Surface the collision
    with its provenance (age gap, authors, what each claims) and put an informed question to the user in the interview.
    Rulings live in the ingest log, not on answers: each entry records the collision, the ruling, who ruled, and the
    reasoning. Answers stay clean; a collision the user declines to rule is filed **contested**.

- **5. Refuse honestly.** Content answering no declared question is flagged, never forced into a near-fit; core questions with no answer are listed as gaps.
    Refusals repeating on one theme signal a missing question — offer `/kb-evolve` — rather than off-domain content.

- **6. Write the outputs.** Spec file, guidance deltas, answers, and the ingest log — all in `<folder>-spec/`
    beside the source folder. The source folder is never written. Answers go in `answers.yaml`, one record
    per answer: `element`, `party`, `date`, `status`, `answer`, `source`, and `supersedes` where a ruling
    displaced something; gaps list `element` and `reason`. The shape is fixed; the checker does not yet
    validate it.

- **7. Validate.** Run
    `UV_PROJECT_ENVIRONMENT="${CLAUDE_PLUGIN_DATA}/venv" uv run --project "${CLAUDE_PLUGIN_ROOT}" kbp --validate "${CLAUDE_PLUGIN_ROOT}/spec/knowledge-bus-protocol.yaml" <written files>`
    — the env var keeps uv's venv out of the read-only plugin cache. Fix or surface every refusal before
    reporting. In a clone of this repo, bare `uv run kbp` does the same.
    If `uv` is not installed, say so and point at the uv install docs — do not improvise an invocation.

- **8. Report coverage.** One table, **contested** first — unresolved collisions block trust — then mapped,
    stale (contradicted or merely unconfirmed), refused, gaps. Each class names its ask: rule it; spot-check;
    confirm or retire; accept as off-domain or add the question via `/kb-evolve`; answer, or record what an
    honest empty means.
