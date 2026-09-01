# Adapting the example

The built-in spec is a starting point, not a requirement. Trim it, extend it, or derive your own.

## What the built-in spec covers

Product development: 58 questions across 19 document types, 45 relations, guidance citing 51
registered sources. It intentionally assumes no type of project and no level of abstraction — the
same questions do their job for a company, a product, or a homelab effort. Adapting is therefore
optimization, not repair: you trim or evolve to favor an industry's conventions, a level of
abstraction, or one kind of work over others.

## Trim or derive

The decision follows domain positioning, not a mapping-count threshold. During ingest the skill
interviews to place your domain: how regulated or commercial versus DIY, and where the
abstraction layer sits — industry, company, product, or feature. Near the built-in's
assumption-free center, adopt or trim; optimizing for an industry's conventions or a different
layer, derive. `/kb-ingest` proposes the placement; you rule.

## Extending with /kb-evolve

When a document type is missing, or one you already declare is about to become load-bearing, hand
it to [`/kb-evolve`](../skills/kb-evolve/SKILL.md) — a 12-step procedure where every declaration
is earned by evidence and every refusal is recorded with its reason. Repeated ingest refusals on
one theme are the usual trigger.

## Minting codes

```bash
just mint element 3
```

Every new declaration needs a code; never reuse or reassign one. Renaming an id is free — the
code is what keeps downstream references stable.

## Keeping guidance honest

A convention must cite a registered source; every other guidance kind may be asserted, but must
say so. Sourcing caveats — paywalled, rescinded, secondary, abstract-only — live inside the
citation string itself, not in a footnote a reader has to find.
