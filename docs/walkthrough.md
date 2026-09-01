# Walkthrough

One folder through one ingest, start to finish. The folder is small and staged so every judgment
is visible; yours will be bigger and messier, and the shape of the run stays the same.

## The folder

Eight files for a solo side project — a meal-prep planning app:

```txt
lunchbox-notes/
├── product-vision.md     2025-03  one screen, this week's prep
├── personas.md           2025-05  over a year old
├── pricing-v1.md         2025-06  freemium $4.99/mo, reasoned
├── decision-auth.md      2025-11  conclusion only, no reasoning
├── competitor-notes.md   2026-01  Mealime, Paprika, AnyList
├── pricing-rethink.md    2026-02  one-time $30, "did not check numbers"
├── packing-list.md                camping gear
└── todo-scratch.md                half-finished todos
```

A familiar folder.

## The survey

`/kb-ingest lunchbox-notes/` reports before it reads deeply:

> 8 files, all markdown. Dates 2025-03 to 2026-08. One pricing note is disputed by a newer one;
> two notes are old but undisputed; one file looks off-topic.

Nothing has been decided yet. The skill has only counted, dated, and noticed.

## The interview

Three questions come in one batch — each one earned, none answerable from the folder itself, and
none requiring you to know what a spec is:

1. *Quick check I read the project right: a meal-prep planning app you're building solo. I'd
   organize your notes around the standard product questions and skip the corporate ones. Sound
   right?* — Confirmed.
2. *Your notes disagree about pricing. June 2025: $4.99/month, with reasoning. February 2026, a
   late-night note: one-time $30, but it says you didn't check the numbers. Where do you actually
   stand today?* — The rethink stands. The June note is superseded; the ruling and its reasoning
   go to the ingest log, and the rethink's own caveat — numbers unchecked — stays on the answer.
3. *Two notes are over a year old — are they still true?* — The vision holds. The personas don't;
   that question becomes an open gap instead of a stale answer pretending to be current.

Notice what did not happen: the newer pricing note did not silently win because it was newer, and
the old vision was not retired because it was old. Both were put to the owner, with the evidence.

## The outputs

`lunchbox-notes-spec/` appears beside the folder — the folder itself is untouched:

- the adopted spec and its guidance file, which the checker validates
- `answers.yaml` — each answer keyed to the question it answers, with source, date, and what it
  superseded
- `ingest-log.md` — every ruling, who ruled it, and why

The camping list and the todo scratch were refused, not forced into a near-fit. The auth decision
was filed, but flagged: it carries a conclusion with no alternatives, constraints, or reversal
condition — a candidate for `/kb-uncover-decision`.

## The coverage report

| Class | What landed there | The ask |
| --- | --- | --- |
| contested | nothing — the one conflict was ruled | — |
| mapped | vision, pricing, competitors; auth (flagged) | spot-check |
| refused | packing list, todo scratch | accept |
| gaps | personas, north-star metric | answer, or record an honest empty |

An agent grounding itself on this project now loads a handful of answers keyed by question —
current, sourced, with the one open conflict visible — instead of re-reading eight files and
guessing which pricing note is real.
