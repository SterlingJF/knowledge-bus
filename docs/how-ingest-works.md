# How ingest works

What `/kb-ingest` decides at each step, and what its report means.

## What it assumes about your folder

Markdown and plain text read best; other formats are inventoried and flagged rather than skipped
silently. No structure is required — mixed dates, duplicate topics, and half-finished notes are the
expected case, not a failure mode. The folder is never written; everything ingest produces lands in
`<folder>-spec/` beside it.

## The eight steps

**1. Confirm scope.** Only the source folder is asked for. The output location is convention, and
the domain phrase is proposed later, from evidence — asking for it cold would put the burden of
work on you before the skill has earned the right to ask anything.

**2. Survey before reading.** Files, dates, and formats are counted and reported before any deep
read. Every doc gets one of three staleness marks: **contradicted** (a newer source disputes it —
mechanical), **unconfirmed** (old, but nothing disputes it), **confirmed** (you cleared it in the
interview). The judgment here is restraint: confirmation questions come batched, after the whole
survey, so you rule on genuine uncertainty rather than on what the corpus already settles.

**3. Position the domain, then choose the spec.** The skill reasons over the folder and whatever
you supplied, calls `/kb-uncover-question` where the domain's questions are unclear, then
interviews to place your domain against the built-in product-development spec: how regulated or
commercial versus DIY, and where the abstraction layer sits — industry, company, product, or
feature. Adopt, trim, or derive follows from that placement, not from a mapping-count threshold.

**4. Extract answers.** Each document section maps to a declared question — one answer per
question per party and time. A collision (two docs answering the same question) is never resolved
by recency: the older doc may be the forgotten original and the newer a lacking recollection.
The collision is surfaced with its provenance and put to you as an informed question. Your ruling
lands in the ingest log with its reasoning; answers stay clean. Decline to rule and the question
files as **contested**.

**5. Refuse honestly.** Content answering no declared question is flagged, never forced into a
near-fit. Refusals repeating on one theme signal a missing question — the skill offers
`/kb-evolve` — rather than off-domain content.

**6. Write the outputs.** Spec file, guidance deltas, answers, and the ingest log, all in
`<folder>-spec/`.

**7. Validate.** The bundled checker runs over everything written; every refusal is fixed or
surfaced before you see a report.

**8. Report coverage.** One table, contested first.

## Reading the coverage report

| Class | What it means | Your move |
| --- | --- | --- |
| contested | a collision you declined to rule | rule it |
| mapped | filed against a declared question | spot-check |
| stale | contradicted, or merely unconfirmed | confirm or retire |
| refused | answers no declared question | accept as off-domain, or add the question via `/kb-evolve` |
| gap | a core question with no answer | answer it, or record what an honest empty means |

Contested rows sit at the top because they block trust the most: until they are ruled, the spec
carries two answers to one question.

