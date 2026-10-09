# Document Type Card

A document type card describes one document type from one universe spec: the document type's purpose, who uses it and when, its sections, the guidance on writing it, and when no document is needed. The card also gives advice on presenting the document from each universe spec in scope that declares a factor. The card uses only the universe specs in scope and their guidance files. The card lists conditions and never checks whether a condition holds.

## Commands

```sh
kbp --card decision-record path/to/.knowledge-bus/
kbp --card decision-record path/to/.knowledge-bus/ --format markdown
kbp --kinds path/to/.knowledge-bus/
```

- `--card <kind>` prints the card for the document type with that id, as JSON. `--format markdown` prints the readable card.
- `--kinds` prints the id, name, other names, purpose, users and timing of every document type, and `overview.covers` and `overview.for` for each universe spec. `--kinds` also prints each factor with its question and number of guidance notes. Use `--kinds` to see the document types and factors in a universe spec.
- Targets work as for `--inspect`: a `.knowledge-bus/` folder, one universe spec file, or explicit files. Without a target, the nearest `.knowledge-bus/` is used.
- When the scope holds several universe specs, choose one for `--card` with `--universe <id>` or target its file. Without `--universe`, `--kinds` prints one group per universe spec.
- In a nested folder, the scope includes the universe specs listed under `from_parent` in `.knowledge-bus/workspace.yaml`. See [Nested Folders](knowledge-bus-directory.md#nested-folders).

Both commands check the chosen universe spec and its guidance file. `--card` also checks every other universe spec in scope and its guidance file. Both commands skip marks files (`*.explorer.yaml`) and run no Explorer drawing checks, so a broken marks file never blocks a card. They write nothing.

## Errors

An error is one JSON object on stderr with schema `knowledge-bus/inspection-error/1`. The exit code is 1 and stdout is empty.

| Category | When |
| --- | --- |
| `selection` | A bad option, no document type given, a missing or unreadable target, no definitions in scope, several universe specs and none chosen, an unknown document type |
| `conformance` | A file cannot be parsed; two universe specs share an id; the chosen universe spec has two guidance files; the chosen universe spec or its guidance file does not conform; for `--card`, another universe spec in scope or its guidance file does not conform; a guidance file names a universe spec outside the scope |
| `protocol` | The bundled protocol cannot be loaded or is unsound |

For an unknown document type, `candidates` lists every document type id. For several universe specs with none chosen, `candidates` lists their ids. In a nested folder with ids under `from_parent`, the error also has `from_parent`, the list of those ids.

## Card Fields

The JSON card has schema `knowledge-bus/card/1`. Every field is present in every card.

| Field | Comes from | Readable line |
| --- | --- | --- |
| `schema` | Always `knowledge-bus/card/1` | None |
| `universe_spec` | `universe.id`, `universe.label` (made from the id when absent) and `universe.version` as text | `Document type in the <label> universe spec (<id> <version>).` |
| `kind` | `artifacts[].id` | None |
| `name` | The document type's `label`, or else its id with hyphens as spaces and the first letter capitalised | `# <name>` |
| `alias` | `alias.kind` and `alias.form`; null when the document type has no alias | `descriptive`: `- Also called: <form>`. `normative`: `- Its shape is set by an outside authority: <form>`. `none`: no line |
| `enablement.action` | `enablement.action`, or the whole `enablement` when it is one string | `- Helps you: <action>` |
| `enablement.actor` | `enablement.actor` | `- Who uses it: <actor>` |
| `enablement.timing` | `enablement.timing` | `- When it is used: <timing>` |
| `disabled_when` | `disabled_when`; null when absent | `- Not used when <condition>. Depends on: …` |
| `no_artifact` | `no_artifact.when`, or `empty_composition.when` in a kbp/0.7 universe spec | `- No document needed when <condition>. Depends on: …`, or `- No document needed: in every situation.` when empty |
| `guidance` | The guidance file's `artifacts.<kind>` entries in file order, each as `kind`, `claim` and `when` (null when absent). Null with no guidance file; `[]` with no entries | One item per entry under `## How to write it well` |
| `sections` | `composition.core`, then `composition.situational`, in declared order | One `### <name>` per section under `## Sections` |
| `sections[].element`, `name`, `question` | The element's `id` and `question`; the name is made from the id as for `name` | `### <name>`, then `Answers: <question>` |
| `sections[].strength`, `when` | The entry's composition list (`core` or `situational`) and the entry's `when` (null when absent) | See [Section Status](#section-status) |
| `sections[].gate` | The element's `gate`; null when absent | `Applies only when <condition>. Depends on: …` |
| `sections[].mode`, `kept_in` | The entry's `mode`, `owns` when absent. For `links`, `kept_in` lists every document type with an `owns` entry for the element, in declared order, each as `kind` and `name`. Null for `owns` | `Kept in another document (<names joined by "or">): link to that document.` When no document type keeps the section: `Kept in another document: link to that document.` |
| `sections[].guidance` | The guidance file's `elements.<element>` entries, as for `guidance` | One item per entry after a blank line. When a section kept in another document has guidance, the section's `Kept in another document` line ends with `The notes below are for writing the section in that document.` |
| `conditions` | Each frame, then each factor, named in any condition on the card outside `presentation`, in declared order: `id`, `question` (null when absent) and `values`. `values` lists each named value that has a question, as `value` and `question` | The `Depends on:` text. Values go under `## What the conditions mean` as `- <id> is <value>: <question>` |
| `presentation` | One block for each universe spec in scope that declares a factor: the card's own universe spec first, then the folder's other universe specs sorted by id, then the universe specs listed under `from_parent`. `[]` when no universe spec in scope declares a factor | One `### <label> universe spec (<id> <version>)` per block under `## How to present it`. See [Presentation Blocks](#presentation-blocks) |
| `presentation[].universe_spec`, `from_parent` | The block's universe spec, as `universe_spec` on the card; `from_parent` is true for a universe spec listed in `workspace.yaml` | The heading ends with `, from the parent folder` when `from_parent` is true |
| `presentation[].factors` | Every factor of the block's universe spec, in declared order: `factor`, `name` (made as for the card's `name`), `question`, and `values`, each declared value as `value` and `question` (null for a plain value) | `#### <name>`, then `Asks: <question>`, then `Values:` with `- <value>: <question>`, or `- <value>` for a plain value |
| `presentation[].factors[].guidance` | The entries under `factors.<factor>` in the block's guidance file, as for `guidance`. Null when the block's universe spec has no guidance file | `Advice:`, then one item per entry |
| `presentation[].conditions` | As `conditions`, for the frames and factors named in the block's guidance | The `Depends on:` text of the block's guidance lines |

## Readable Wording

Conditions are printed in words:

- `{ authority: [approve, statutory] }` reads `authority is approve or statutory`.
- Several keys join with `and`: `time-separation is none and reversibility is reversible`.
- A facet reads `<id> <facet> is <values>`: `outcome form is creation or service`.
- An empty value list reads `no value`.

Every condition is followed by `Depends on:` and, for each key, `<question> (<id>)`, joined by semicolons. A frame with no question reads `not stated in the universe spec (<id>)`. The card has no file to judge, so it never says whether a condition holds.

### Section Status

| Entry | Line |
| --- | --- |
| Core, no `when` | `Required.` |
| Core with `when` | `Required when <condition>; otherwise optional. Depends on: …` |
| Situational, no `when` | `When applicable.` |
| Situational with `when` | `When applicable, available when <condition>. Depends on: …` |

### Guidance Lines

- `- <Label>: <claim>`
- `- <Label>, when <condition>: <claim> Depends on: …`

`<Label>` is the guidance entry's `kind`, such as `heuristic` or `convention`, with its first letter capitalised.

### Fallbacks

- A missing `action`, `actor` or `timing` reads `not stated in the universe spec`.
- An empty condition (`{}`) on a section, a gate or a guidance entry reads as no condition.
- An empty `disabled_when` reads `- Not used: in every situation.`
- Quote `version` in the universe spec. An unquoted `0.10` is read as the number 0.1 and prints as `0.1`.

### Layout

1. `# <name>`
2. The universe spec line.
3. A list: other names, `Helps you`, `Who uses it`, `When it is used`, `Not used when`, `No document needed`.
4. `## How to write it well`, only when the document type has guidance.
5. `## Sections`, with `### <name>` for each section: `Answers`, the status line, the gate line, the `Kept in another document` line, then the section's guidance.
6. `## How to present it`, only when `presentation` holds a block: the line `Factors change presentation and focus only. The sections stay the same.`, then each block.
7. `## What the conditions mean`, only when a named value has a question.

Blocks are separated by one blank line. The file ends with one newline. Text from the universe spec and guidance file is copied as written. Example: [the decision record card](../checker/tests/cards/product-development/decision-record.md).

### Presentation Blocks

Guidance keyed to a factor is advice on presenting the document: wording, emphasis and focus. A factor selects nothing, so the sections stay the same with or without a presentation block. The card lists every factor of each universe spec in scope that declares a factor, with the factor's values and guidance, and never says which value applies. Example: [the visit plan card](../checker/tests/cards/card-fixture/visit-plan.md).

## Document Type List

The JSON list has schema `knowledge-bus/kinds/1`: `universe_spec` as on the card plus `covers` and `for`; `kinds`, one entry per document type in declared order with `kind`, `name`, `alias`, `action`, `actor` and `timing`; and `factors`, one entry per factor in declared order with `factor`, `name`, `question` and `guidance`. `guidance` counts the entries under `factors.<factor>` in the guidance file and is null when the universe spec has no guidance file. `covers` and `for` copy `universe.overview.covers` and `universe.overview.for` with leading and trailing whitespace removed and each inner run of spaces and line breaks reduced to one space. `actor` and `timing` match the card's `enablement.actor` and `enablement.timing`. `covers`, `for`, `actor` and `timing` are null when the universe spec gives no value.

With several universe specs and no `--universe`, the JSON list has schema `knowledge-bus/kinds-set/1`: `universe_specs`, one `knowledge-bus/kinds/1` object per universe spec, and `from_parent`, the ids listed in `workspace.yaml` (`[]` without the file). The folder's own universe specs come first, sorted by id, then the listed universe specs in `from_parent` order.

The readable list starts with `# Document types`, `In the <label> universe spec (<id> <version>).`, `Covers: <covers>` and `For: <for>`, then gives each document type as `- <name> (<id>)` with indented `Also called` or `Its shape is set by an outside authority`, `Helps you`, `Who uses it` and `When it is used`. After the document types, `Factors:` gives each factor as `- <name> (<id>)` with indented `Asks: <question>` and the number of guidance notes, such as `2 guidance notes` or `No guidance notes`. The list leaves out the line for a null `covers`, `for`, `actor` or `timing`, the count line for a null `guidance`, and `Factors:` for a universe spec without factors.

With several universe specs, the readable list starts with `# Document types`, then gives each universe spec as `## <label> universe spec (<id> <version>)` followed by its `Covers` and `For` lines and its document types. A heading for a universe spec listed in `workspace.yaml` ends with `, from the parent folder`. For a universe spec without document types, the group holds the line `No document types.` Example: [a nested folder's list](../checker/tests/cards/kinds-set-from-parent/kinds.md).

## Left Off the Card

- The rest of the universe spec: overview, terms, statuses, relations and other document types.
- Whether a condition holds.
- Guidance sources, citations and links.
- Codes on document types, sections, frames and factors.
- The number of answers per section, and whether a section's answers can ever be complete.

## Expected Cards

Expected cards are in `checker/tests/cards/`. Tests compare the output of `kbp --card` and `kbp --kinds` with the expected cards: JSON by value, Markdown byte for byte.

| Folder | Universe spec | Covers |
| --- | --- | --- |
| `product-development` | `universes/product-development/` | Every document type |
| `card-fixture` | `checker/tests/card-fixture/` | Guidance conditioned on a factor, guidance keyed to a factor, gates, sections kept in another document with and without a document type that keeps the section, a frame with no question, values with no question, a document type with no guidance |
| `minimal` | `protocol/conformance/pass/minimal.kbp.yaml` | No guidance file, enablement as one string, an empty no-document condition |
| `kinds-set` | `evals/fixtures/village-hall/` and `protocol/conformance/pass/factors-only.kbp.yaml` | `--kinds` with several universe specs, one of them without document types and with a factor |
| `kinds-set-from-parent` | `checker/tests/workspace/upkeep/` and `protocol/conformance/pass/factors-only.kbp.yaml` | `--kinds` in a nested folder with two universe specs of the parent folder under `from_parent` |

After a change to the card or to one of these universe specs, rewrite the expected cards and review the diff:

```sh
KBP_WRITE_CARDS=1 uv run --locked pytest checker/tests/test_card.py
```
