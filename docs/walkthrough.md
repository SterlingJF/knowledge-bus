# Walkthrough

Follow a small example folder through `/kb-ingest`. The example includes conflicting notes, outdated information, and content outside the project's scope.

## The Folder

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

## The Initial Findings

`/kb-ingest lunchbox-notes/` reports before it reads deeply:

> 8 files, all markdown. Dates 2025-03 to 2026-08. One pricing note is disputed by a newer one;
> two notes are old but undisputed; one file looks off-topic.

These initial findings flag potential issues. They do not settle which conflicting note to use.

## The Interview

The skill asks three questions that need the owner's input:

1. *Quick check I read the project right: a meal-prep planning app you're building solo. I'd
   organize your notes around the standard product questions and skip the corporate ones. Sound
   right?* — Confirmed.
2. *Your notes disagree about pricing. June 2025: $4.99/month, with reasoning. February 2026, a
   late-night note: one-time $30, but it says you didn't check the numbers. Where do you actually
   stand today?* — The rethink stands. The June note is superseded; the ruling and its reasoning
   go to the ingest log, and the rethink's own caveat — numbers unchecked — stays on the answer.
3. *Two notes are over a year old — are they still true?* — The vision holds. The personas don't;
   the persona question is recorded as unanswered.

The owner confirmed which information still held. The review considered both the dates and the content; a newer note did not automatically replace an older one.

## The Outputs

Outputs go into `lunchbox-notes/.knowledge-bus/`. The original notes remain untouched:

- the adopted spec and its guidance file, which the checker validates
- `answers.yaml` — each answer keyed to the question it answers, with source, date, and what it
  superseded
- `ingest-log.md` — each review decision, who made it, and why

The camping list and todo scratch did not match the chosen definitions and were listed for review. The auth decision
was filed, but flagged: it carries a conclusion with no alternatives, constraints, or reversal
condition — a candidate for `/kb-uncover-decision`.

## The Coverage Report

| Class | What landed there | The ask |
| --- | --- | --- |
| contested | none; the pricing conflict was resolved | no action needed |
| mapped | vision, pricing, competitors; auth (flagged) | spot-check |
| refused | packing list, todo scratch | confirm these are outside the chosen scope |
| gaps | personas, north-star metric | answer, or record why these remain unanswered |

The result gives a reader or agent answers organized by question, with sources and remaining gaps visible. The pricing answer includes the owner's decision and the caveat that the numbers are unchecked. The outdated personas remain an open question.

The checker validates the definition and guidance files. The answers and ingest log still need review; passing the check does not establish that their contents are correct.
