# Knowledge Bus Directory

The `.knowledge-bus/` directory holds the definitions and supporting files for the folder that contains it. That containing folder can be a notes vault, document collection, project, or any other folder. This convention specifies where Knowledge Bus files live, not how to organize the surrounding files.

## Directory Contents

```text
my-folder/
├── ... source files ...
└── .knowledge-bus/
    ├── universe.kbp.yaml
    ├── type-guidance.kbp.yaml   # optional
    ├── marks.explorer.yaml      # optional presentation declarations
    ├── answers.yaml            # when recording answers
    ├── ingest-log.md           # when ingesting existing material
    ├── evolve-log.md           # when evolving a universe spec
    ├── workspace.yaml          # optional: settings for this folder, such as universe specs to use from the parent folder
    └── explorer/               # optional generated read-only projection
        └── <universe-id>/
            ├── index.html
            ├── model.json
            └── receipt.json
```

Any folder can contain a `.knowledge-bus/` directory. Git is not required. Define the structure before creating documents, or derive it from existing material through ingestion. Answers and an ingest log are not prerequisites for authoring a universe.

## Directory Selection

Explicit targets take precedence. Pass the folder, its `.knowledge-bus/` directory, or individual definition files:

```sh
kbp --validate path/to/my-folder
kbp --validate path/to/my-folder/.knowledge-bus/
kbp --validate path/to/universe.kbp.yaml path/to/type-guidance.kbp.yaml
```

Without an explicit target, the checker searches the current folder and then its parents for `.knowledge-bus/`. It uses the first one found and does not combine definitions from different directories. Calls from inside `.knowledge-bus/` use that directory. An empty or incomplete nearer directory does not fall back to a parent's `.knowledge-bus/`. To use universe specs of the parent folder in a nested folder, list their ids in the nested folder's `workspace.yaml`; see [Nested Folders](#nested-folders).

The checker reads the `*.kbp.yaml` files directly inside the selected `.knowledge-bus/` directory together, to check guidance against its universe. The checker also reads `workspace.yaml` in that directory and, for each id under `from_parent`, the universe spec file and guidance in the parent folder. Duplicate universe ids fail. Answers, the ingest and evolve logs, presentation marks, and Explorer outputs are not checker inputs. Explicit file targets select exactly those files; include the universe when checking guidance.

## Several Universes in One Scope

Several universes may be direct siblings in one `.knowledge-bus/`. Prefix filenames for people, but rely on semantic headers for identity and association:

```text
.knowledge-bus/
├── product-development.universe.kbp.yaml
├── product-development.type-guidance.kbp.yaml
├── product-development.marks.explorer.yaml
├── team-operations.universe.kbp.yaml
├── team-operations.type-guidance.kbp.yaml
├── team-operations.marks.explorer.yaml
└── explorer/
    ├── product-development/{index.html,model.json,receipt.json}
    └── team-operations/{index.html,model.json,receipt.json}
```

`universe.id` identifies a universe. `guidance.guides` and `marks.marks_for` associate its companion files. When the directory contains several universes, inspection requires an id or universe file. Duplicate ids and ambiguous companion files fail. Generated Explorers stay under their universe ids. A nested `.knowledge-bus/` stays separate unless its `workspace.yaml` lists universe specs of the parent folder.

A generic directory target without its own `.knowledge-bus/` still scans for `*.kbp.yaml` files, for example a reference collection or test corpus. It skips metadata directories and nested folders that contain their own `.knowledge-bus/`. Directory scans do not follow nested directory symlinks.

Missing definitions are an error when checking. Checking never creates a `.knowledge-bus/` directory.

## Nested Folders

A nested folder with its own `.knowledge-bus/` stands alone by default. To apply universe specs of the parent folder inside a nested folder, list their ids under `from_parent` in the nested folder's `.knowledge-bus/workspace.yaml`. The parent folder is the nearest folder above with its own `.knowledge-bus/`.

### Example

A village hall keeps two universe specs in `hall/.knowledge-bus/`: Hall bookings and Hall upkeep. The management committee keeps Committee minutes in `hall/committee/.knowledge-bus/`. The committee also signs off hirer checklists, so Hall upkeep applies in `hall/committee/` too.

```text
hall/
├── .knowledge-bus/
│   ├── hall-bookings.universe.kbp.yaml
│   └── hall-upkeep.universe.kbp.yaml
└── committee/
    └── .knowledge-bus/
        ├── committee-minutes.universe.kbp.yaml
        └── workspace.yaml
```

`hall/committee/.knowledge-bus/workspace.yaml`:

```yaml
from_parent:
  - hall-upkeep
```

`kbp` in `hall/committee/` checks `workspace.yaml`, then Committee minutes, then Hall upkeep from the parent folder, one block per file. Output with the protocol block and the per-section lines cut:

```text
=== workspace.yaml ===
  names hall-upkeep from ../.knowledge-bus/

workspace.yaml: CONFORMS

=== committee-minutes.universe.kbp.yaml against kbp/0.8 ===
…
committee-minutes.universe.kbp.yaml: CONFORMS

=== hall-upkeep.universe.kbp.yaml from the parent folder, against kbp/0.8 ===
…
hall-upkeep.universe.kbp.yaml: CONFORMS
```

`kbp --kinds --format markdown` in `hall/committee/` prints one group per universe spec:

```text
# Document types

## Committee minutes universe spec (committee-minutes 0.1)

- Minutes (minutes)
  - Helps you: record what the committee agreed

## Hall upkeep universe spec (hall-upkeep 0.1), from the parent folder

- Hirer checklist (hirer-checklist)
  - Helps you: leave the hall ready for the next hirer
```

`kbp --card hirer-checklist --universe hall-upkeep` in `hall/committee/` prints the same card as in `hall/`. `--card`, `--inspect` and `--explore` refuse without `--universe` and list the candidates:

```json
{"candidates": ["committee-minutes", "hall-upkeep"], "category": "selection", "from_parent": ["hall-upkeep"], "message": "Multiple universes require an explicit universe id or file", "schema": "knowledge-bus/inspection-error/1", "status": "error"}
```

Hall bookings stays out of `hall/committee/`.

### The File

- `workspace.yaml` holds settings for its folder. `from_parent` is the only key: a list of universe spec ids, each listed once. Other keys are refused.
- Without `workspace.yaml`, or with `from_parent: []`, no command reads the parent folder.
- A listed id must be declared in the parent folder's own universe spec files. Ids from the parent folder's own `workspace.yaml` are refused, so a nested folder can list only universe specs declared in the direct parent folder.
- A universe spec in the nested folder can reuse the id of a universe spec in the parent folder when the id is absent from `from_parent`.
- In a folder holding only `workspace.yaml`, the listed universe specs are the folder's universe specs.
- A factor-only universe spec can be listed like any other universe spec. `--kinds` prints its group with "No document types." and its factors.

### Reading

- Every command reads `workspace.yaml` when the command reads a whole `.knowledge-bus/`: with no target, a folder target, or a `.knowledge-bus/` target. `--inspect`, `--explore`, `--card` and `--kinds` also read `workspace.yaml` for a single universe spec file target.
- Commands skip `workspace.yaml` when check or `--mint` gets explicit definition file targets, when any other command gets several explicit file targets, and when a command scans a generic directory.
- For an explicit `.knowledge-bus/workspace.yaml` target, check and `--mint` apply the same rules as for a folder target. Check prints the same `=== workspace.yaml ===` block as a folder check, and adds no file from the parent folder.
- `--card`, `--kinds`, `--inspect` and `--explore` skip an explicit `workspace.yaml` target. With `workspace.yaml` or a marks file as the only target, the four commands refuse with "No universe definitions in the selected scope".
- For each listed id, commands read the parent folder's universe spec file and the parent folder's guidance for that universe spec. `--inspect` and `--explore` also read the parent folder's marks for that universe spec.
- The skills follow the same reading rules as `kbp`.
- Each universe spec keeps its own id, label, document types, guidance and marks. No command merges universe specs. Check prints one block per file and adds `from the parent folder` to the heading of each file read from the parent folder. With several universe specs, `--inspect`, `--explore` and `--card` refuse without `--universe`, list the candidates, and add `from_parent` to the refusal. With several universe specs, `--kinds` prints one group per universe spec.
- `--card` gives advice on presenting the document under "How to present it": one block for each universe spec in scope that declares a factor, the card's own universe spec first. Blocks for universe specs listed in `workspace.yaml` have headings ending with `, from the parent folder`.
- Check in the parent folder never reads nested folders.

### Refusals

- Check, `--card`, `--kinds`, `--inspect` and `--explore` refuse guidance in the nested folder for a listed universe spec. `--inspect` and `--explore` also refuse marks in the nested folder for a listed universe spec; the other commands skip marks.
- When a listed universe spec does not conform, check in the nested folder fails too, and read commands refuse with category `conformance`.
- When `from_parent` lists an id, commands run in the nested folder refuse on any unreadable `*.kbp.yaml` file in the parent folder. `--inspect` and `--explore` also refuse on an unreadable marks file in the parent folder. The refusal message includes the file name and the parent folder.
- After a listed id is renamed or removed in the parent folder, check in the nested folder fails with "which the parent folder does not declare". Before changing or removing a `universe.id`, `kb-evolve` lists every nested `workspace.yaml` that names the id under `from_parent`.

For each refusal below, a folder case under `checker/tests/workspace/` must fail with exactly that refusal. The `kb-check` skill gives the fix for each refusal.

| Refusal contains | Cause | Folder case |
| --- | --- | --- |
| `workspace.yaml: must be a mapping` | The file is empty, a list, or not YAML | `empty`, `list`, `not-yaml` |
| `workspace.yaml: unknown key` | A key other than `from_parent` | `unknown-key` |
| `from_parent must be a list of universe spec ids, each named once` | A string, a blank id, or a repeated id | `not-a-list`, `blank-id`, `repeated-id` |
| `no .knowledge-bus/ is above this folder` | `from_parent` lists ids, and no folder above has a `.knowledge-bus/` | `no-parent` |
| `which the parent folder does not declare` | A misspelled id, or an id from the parent folder's own `workspace.yaml` | `misnamed`, `grandparent` |
| `which this folder already declares` | A universe spec in the nested folder has a listed id | `id-reuse` |
| `a universe spec from the parent folder` | Guidance or marks in the nested folder for a listed universe spec | `nested-guidance`, `nested-marks` |
| `in the parent folder` | An unreadable file in the parent folder | `unreadable-parent` |

### Writing Changes

- Write a change to a universe spec or its guidance in the `.knowledge-bus/` holding the universe spec file. Skills name that `.knowledge-bus/` before writing.
- Add the `evolve-log.md` entry beside the changed universe spec.
- Keep answers, the ingest log and Explorer outputs in the selected `.knowledge-bus/`.
- During ingestion, `kb-ingest` files answers for listed universe specs in the selected `.knowledge-bus/`, and writes a change to a listed universe spec in the parent folder only after the user confirms the change.

## Creating and Updating Definitions

Create `.knowledge-bus/` when the user asks to set up definitions for a folder. There is no separate `kbp init` command. Keep writes inside the selected metadata directory and leave existing source files untouched. For a universe spec listed in `workspace.yaml`, write changes in the parent folder; see [Nested Folders](#nested-folders).

Inspect existing definitions, guidance, answers, and logs before writing. Reuse them or propose deliberate changes; do not reset or blindly overwrite them. Preserve decisions and history. Ask how to proceed if existing content is incompatible or ambiguous.

During ingestion, exclude every `.knowledge-bus/` directory from source material. Skip and report nested folders that contain their own `.knowledge-bus/`; ingest them separately only when explicitly targeted.

## Protocol and Examples

The installed checker carries its protocol. Knowledge Bus directory discovery does not search for a `protocol/` directory. An explicit protocol file can still override the bundled protocol.

In the implementation checkout, `protocol/` remains the protocol source and `universes/` remains the bundled example collection. A bare `uv run kbp` there validates the examples when no `.knowledge-bus/` directory is found. Those reference files do not move into `.knowledge-bus/`.

## Previous Locations

The sibling `<folder>-spec/` convention is no longer supported for discovery or output. There is no fallback or migration. Existing folders are not moved or deleted. An explicitly supplied file remains a valid checker target regardless of its location.
