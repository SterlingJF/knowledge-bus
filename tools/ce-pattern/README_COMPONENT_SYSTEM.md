# The CE Pattern

Vendored from the SterlingJF/ce-pattern-kit README; edit it there.

## The Three Layers

```txt
src/
├── component-core/      # Untouched vendor components (e.g. Shadcn)
├── component-elements/  # Enriched UI vocabulary
└── component-patterns/  # Composed, purpose-specific combinations
```

| Layer        | What it is                                      | Import → export                                                                         |
| ------------ | ----------------------------------------------- | --------------------------------------------------------------------------------------- |
| **core**     | Vendor components                               | Exact support edges below.                                                              |
| **elements** | Your UI vocabulary — enriched variants of core. | 1 source, or an explicitly configured native root; at least as many exports as imports. |
| **patterns** | Composed, purpose-specific combinations.        | 2+ sources; fewer exports than imports.                                                 |

## Rules

The layer rules classify component implementations only. Colocated stories, story metadata, and fixtures
are treated as support artifacts rather than additional core capabilities.

### Rule 1 — Core is read-only

`component-core` contains only vendor files.
Nothing in core is hand-edited. If you need to change behaviour, wrap it in elements.
Imports emitted by the vendor may resolve to package support hooks or utilities; that does not move
the vendor file out of core.

### Rule 2 — Elements: one source (or configured native root), same or more out

A file belongs in `component-elements` if and only if:

1. It imports from **exactly one** source file (core or another elements file), and
2. For each kind (types/interfaces, functions/constants), it exports **at least as many** of that kind as it imported, and
3. Exports within each kind are **logically interchangeable** with what was imported — same kind, same contract. Locally-defined exports of the same kind count toward the total.

> A shadcn `Button` file that exports `ButtonPrimary`, `ButtonGhost`, and `ButtonLoading` is an element.
> Locally-defined exports of the same kind (e.g. a `BUTTON_SIZES` constant) also count toward the total.

Elements may chain: an elements file may wrap another elements file, as long as all conditions above still hold.

For a framework-neutral library configured with the `none` preset, a component element may instead
be a native root element built directly from platform APIs. This zero-layer-source exception is valid
only when the package's CE Pattern config explicitly selects `preset: "none"`; every other preset
continues to require exactly one core or elements source.

### Rule 3 — Patterns: multiple sources, fewer out

A file belongs in `component-patterns` if:

- It imports from **more than one** source, and
- It exports **fewer** things than it imports in total.

This applies regardless of whether the imports come from core, elements, or other patterns.
The collapse is the signal — you're combining parts into something specific.

> A `SearchBar` that imports `Input`, `Button`, and `Label` and exports only `SearchBar` is a pattern.
> Three things in, one thing out.

### Rule 4 — Patterns are sticky by default

Once a file is classified as a pattern, it **stays** a pattern.
The import/export ratio is not re-evaluated to reclassify it upward.
New imports or refactors don't move it to elements.

### Rule 5 — Dependencies only flow downward

| This layer... | May import from...       | May NOT import from... |
| ------------- | ------------------------ | ---------------------- |
| core          | vendor-declared imports  | elements, patterns     |
| elements      | core, elements           | patterns               |
| patterns      | core, elements, patterns | —                      |

Nothing in core or elements imports from patterns.

### Rule 6 — Prototypes are unsettled patterns

A **prototype** is a file in `component-patterns` placed there when a capability gap or new need has
been identified, but consumer-facing requirements and downstream use cases are not yet defined at
a UX or interaction design (IxD) level sufficient to:

- confidently place it in elements, or
- determine whether and what to pull from a vendor source into core.

A prototype's parts move out as they settle. Nothing waits for the whole file.

Prototypes resolve part by part. There are four valid paths:

1. **Swap parts out** — replace hand-built internals with core or elements components.
2. **Lift to elements** — if the prototype surfaces a genuinely distinct and user-focused capability with no vendor equivalent, extract that capability into a new element file.
3. **Pull from core** — if the vendor library now covers the capability, import it and remove the hand-built version.
4. **Reclassify to elements** — if on review the prototype turns out to be a single-source enrichment, move it to elements. Only valid if it doesn't import from other patterns.

A prototype that matures by relying on other patterns remains a pattern (Rule 4).

## Classification Quick Guide

When you're not sure where a new file belongs, ask in order:

```txt
1. Are the design requirements for this still being defined?
   └─ Yes → PATTERNS (prototype — see Rule 6)

2. Is it unmodified vendor code?
   └─ Yes → CORE

3. Is it a zero-layer-source native root under an explicit `none` preset?
   └─ Yes → ELEMENTS

4. Does it import from exactly one source?
   └─ Yes → Does it have at least as many exports as it imported?
              └─ Yes, and each kind of export matches its imported kind → ELEMENTS
              └─ No (exports fewer) → PATTERNS
   └─ No (zero or multiple sources) → PATTERNS
```

## Why this system works

The rules are mechanical on purpose — component classification follows a count, not a judgment call.

The layers also self-document. A file in `component-elements` promises a stable, reusable UI vocabulary.
A file in `component-patterns` promises a purposeful composition of lower-layer pieces.
