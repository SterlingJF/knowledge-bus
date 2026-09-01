---
name: kb-evolve
description: Add a document type a spec does not carry, or re-examine one
  about to become load-bearing, so that every declaration is earned by
  evidence and every refusal is recorded with its reason. Runs a 12-step
  procedure — state the suspicion, survey sources by enablement, run the
  identity tests, derive strength, update spec and guidance, verify with the
  bundled checker. Use when invoked via /kb-evolve, or when the user asks to
  extend, deepen, or audit a spec's structure.
---

# Evolve a Spec

**Purpose — add a type the spec does not carry, or deepen one it already declares, so that every declaration is earned by evidence, every refusal is recorded with its reason, and the framework stays cohesive rather than locally patched.**

Two entry points share one spine. Run the spine; take the branch that applies.

- **Path A — new type.** A form exists in the world and the spec does not carry it. Governing question: *does it enable something no declared type enables?*
- **Path B — re-evaluation.** A declared type is about to become load-bearing and its basis is unexamined. Governing question: *what in this type is inherited rather than earned?*

## Standing constraints

- **Deepen by sharpening questions, splits and cross-connections — never by growing per-cell density.** A fattening cell means the essence is not grasped yet.
- **Re-evaluate every row the new knowledge touches**, revising earlier depictions the evidence has outgrown. Cohesion over local patching.
- **A refusal is an output.** Record what you declined to add and why, so it is not re-litigated.
- **Nothing about a downstream app enters either file**, in any form.
- **Surface, do not hack.** Where the model cannot express something honestly, say so and file it — do not bend a declaration to fit.
- **Codes are stable.** Renaming an `id` is free; reusing or reassigning a code is not.

## The flow

- **1. State the suspicion before searching.** Write down what you expect to find wrong, then go looking. This is what stops a first-hit lineage from being confirmed rather than tested.
    - **A:** name the form and the gap it claims to fill.
    - **B:** name what looks inherited — a word in the id, a single-tradition guidance base, a question doing more than one job, an enablement promising something no element delivers.

- **2. Group candidate sources by enablement, not by discipline.** Families are "what does this let someone *do*" — decide, know-what-stands, calibrate, follow-an-argument. Discipline groupings smuggle in the lineage you are trying to test.

- **3. Fetch primary sources. Record every failed or degraded fetch.** Paywalled, rescinded, image-only, redirected — say so, and carry the caveat into the citation itself rather than leaving it for a reader to discover.

- **4. Run the artifact test per family.** Identity is `(action, actor)`; add timing to break ties.
    - **A:** if the enablement duplicates a declared type's, fold the form in as an alias — do not add a row.
    - **B:** ask whether any *surveyed family* deserves a type the spec lacks. Refusing one is an output, not an omission — record why.

- **5. Run the element test on every candidate field, against every declared question.** Identity is the question. Name the collision for each candidate and rule *sharpen existing / new / refused*.
    - **A:** decompose the external form into its documented sections; reconcile each — fold into an existing row, split one, or add. Never duplicate.
    - **B:** additionally audit the type's **existing** elements. A question with two conjunctions is usually two questions. A clause the instance layer already answers is a leak between levels, not a field.

- **6. Derive strength; do not choose it.** Core iff the enabled action cannot be taken without it. Where a frame decides, express it as `when:` on a core entry rather than as a second row.

- **7. Check the relation graph.**
    - **A:** add boundaries for the near-misses step 5 surfaced.
    - **B:** **re-point every edge naming a renamed or split declaration**, and promote any boundary that exists only as guidance prose into a `distinct-from` edge.

- **8. Write the spec file.** See § Outputs.
    - **A:** mint codes for everything new.
    - **B:** **retain the code on any declaration keeping its identity**; mint only for genuinely new ones. A rename with a stable code costs nothing downstream — that is what codes are for.

- **9. Write the guidance file.** See § Outputs.
    - **A:** guidance starts empty; author it.
    - **B:** guidance already exists and is keyed on ids you may have changed. Rekey it, and re-home entries whose subject moved — a boundary claim follows the element it is about.

- **10. Verify mechanically.** Run the checker; expect it to catch the rekeying you missed. Grep for downstream leakage. Count codes and entries against expectation. Confirm the protocol version did not move unless you meant it to.

- **11. Record the decision — including the refusals.** One record: what changed, why, what was refused and on what grounds, what would reverse it, what stayed ambiguous.

- **12. Raise what you surfaced but did not solve.** A gap found and left unfiled becomes an assumption. File it as an item.

## Outputs, by file

**Spec file — carries only what something reads.**

- Declarations: elements, artifact types, frames, factors — each with `id`, `code`, and its identity (`question` for an element, `enablement` for an artifact).
- Composition: `core` / `situational`, each entry's `mode` (`owns` | `links`) and any `when:` predicate.
- Relations: edges with `kind`, plus `legality`, `gate` or `freeze` where they apply.
- The `alias` — the external form(s) the composition aligns with, and its kind.
- Nothing advisory. Nothing about any app built on the spec. Nothing a reader is meant to weigh rather than resolve.

**Guidance file — carries everything else, and is advisory by rule.**

- One entry per claim: `kind`, `claim`, `source`, optional `when:`.
- `convention` must cite a registry source; `pitfall`, `heuristic`, `empty`, `refresh`, `boundary` may be `asserted`.
- Register each new source with `cite`, `url` and `checked`. **Put sourcing caveats inside the `cite` string** — rescinded, paywalled, secondary, abstract-only.
- Give every `distinct-from` edge a `boundary` entry saying why the distinction holds.
- Give every element you added an `empty` entry saying what an honest empty answer means.

**Split rule:** a value belongs in the spec because something reads it; everything else belongs in guidance. A spec must stay valid with no guidance file present.
