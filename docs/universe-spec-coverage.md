# Universe Spec Coverage

`kbp --cover <file>` says which universe specs cover one file. An agent runs it before writing a file. An editor applies the same rule to say what a file is for.

The file need not exist yet. To place a passage brought in from outside, cover it as a new file in its target folder.

## Command

```sh
kbp --cover notes/new.md
kbp --cover bookings/june-form.md --type booking-form
kbp --cover notes/hirer-faq.md --no-fit --hat hirer
```

- `--type <id>`: the file's document type, when known.
- `--no-fit`: no document type fits the file.
- `--hat <name>`: the role of the person working on the file, such as caretaker.

`--type` and `--no-fit` cannot be given together. `--hat` needs at least one word. A bad option is reported before any other error.

The command prints one JSON object and writes nothing. It does not check the universe specs. `--card` and `--kinds` check the chosen universe spec.

## The Rule

Inputs:

- the file's path from the top folder;
- each `.knowledge-bus/` on that path, with its files;
- the presets;
- when known, the document type id or no fit, and the hat.

The top folder is the workspace or vault for an editor, and the top of the disk for `kbp`. A `.knowledge-bus/` above the top folder is not used.

1. Find the folder: the nearest `.knowledge-bus/` at or above the file's folder.
2. No folder found: the presets are the candidates. Reason: `preset`. `kbp` carries product-development as its preset.
3. The folder's own universe specs are candidates. Reason: `in-folder`.
4. A nested folder's `coverage.yaml` may list universe specs under `from_parent`. They come from the parent, the next `.knowledge-bus/` up, and join the folder's own. Only the parent's own universe specs can be named. Reason: `named-by-nested-folder`. The parent is read only when `from_parent` names universe specs.
5. A folder with no universe specs, and none named from its parent, is an error.
6. Path: a universe spec listed under `paths` in `coverage.yaml` covers only the files those paths include. Reason: `listed-path`. A universe spec not listed covers every file. If no candidate is left, all stay, with no `listed-path` reason.
7. Document type: given an id, keep the candidates that declare it. Reason: `declares-document-type`. If none declares it, the answer is an error listing their document type ids. Given no fit, all stay.
8. Hat, only when several remain: keep the candidates that name the hat. Reason: `names-hat`. If none names it, all stay.
9. Result: always a list, with reasons. It is settled when one universe spec remains, or when a document type or no fit was given.

Each candidate's reasons appear in rule order.

A universe spec names a hat when the hat's words appear in order, side by side, in one of:

- its overview `for` line;
- a document type's `enablement.actor`, the card's "Who uses it";
- a frame's values; a value written as an object counts by its `id`.

Letter case is ignored. Letters and digits, in any script, form words; every other character, hyphens included, separates words. There are no plurals or stems: `hirers` does not match `hirer`.

When the answer is not settled, the agent recognises the document type, and the hat if it can, and covers the file again. It asks the person only when it still cannot tell, showing each candidate's label and `covers` line. The host keeps the person's choice for the session. `kbp` keeps nothing.

## Fields Read

From each universe spec:

- `universe`: `id`, `label`, `version`, `overview.covers`, `overview.for`;
- `artifacts`: each document type's `id` and `enablement.actor`;
- `frames`: each frame's `values`.

## Answer

Schema `knowledge-bus/cover/1`. The answer has no absolute paths.

| Field | Value |
| --- | --- |
| `settled` | `true` or `false` |
| `source` | `folder` or `presets` |
| `knowledge_bus_dir` | The `.knowledge-bus/` used, relative to the file's folder: `.knowledge-bus` for a file in the folder holding it, with `../` added for each folder level below, such as `../.knowledge-bus`. Null for presets |
| `document_type`, `no_fit`, `hat` | The inputs as given |
| `universe_specs` | Each candidate, ordered by id: `id`, `label`, `version`, `covers` and `reasons` |

For each candidate:

- `label`: its label; with none, its id with hyphens as spaces and only the first letter capitalised;
- `version`: as text, as `--card` shows it;
- `covers`: its overview `covers` text, with leading and trailing whitespace removed.

An error is one JSON object on stderr with schema `knowledge-bus/inspection-error/1`. The exit code is 1 and stdout is empty. Its fields:

- `status`: `error`;
- `category`: see the table below;
- `message`: for people, and may be reworded; `cases.json` gives the current text;
- `candidates`: sorted, and left out when empty.

| Category | When |
| --- | --- |
| `selection` | A bad option, a folder as the file, a file inside `.knowledge-bus/`, a folder with no universe specs, a document type no candidate declares |
| `conformance` | A file that cannot be parsed, a universe spec without an id, two universe specs with one id, a `coverage.yaml` problem |

Errors with candidates:

- a document type no candidate declares: the candidates' document type ids, each once;
- a `from_parent` name the parent lacks: the parent's universe spec ids;
- a `paths` id not in the folder: the folder's universe spec ids, its own and those named from its parent.

## Using the Answer

With the bundled checker:

```sh
kbp --cover notes/new.md
kbp --kinds <knowledge_bus_dir> --universe <id>
kbp --cover notes/new.md --type <document type id>
kbp --card <document type id> <knowledge_bus_dir> --universe <id>
```

Run `--kinds` for each candidate to recognise the document type. Join `knowledge_bus_dir` to the file's folder and pass the result as the target. Without a target, `--kinds` and `--card` search from where they run and can reach a different `.knowledge-bus/`. When `knowledge_bus_dir` is null, run them from the file's folder with no target; they use the preset.

Given a nested folder's `.knowledge-bus/`, `--card` and `--kinds` also see the universe specs its `coverage.yaml` names.

## coverage.yaml

Optional, inside `.knowledge-bus/`:

```yaml
version: 1
from_parent: [hall-upkeep]
paths:
  hall-bookings: [bookings/, notes/hirer-faq.md]
  hall-upkeep: [notes/checklists/, upkeep/]
```

- `version`: required, a whole number. This checker reads version 1 and refuses a higher version as needing a newer checker.
- Any other key is refused.
- `from_parent`: ids of the parent's own universe specs this folder uses. Refused: no `.knowledge-bus/` above, a name the parent lacks, an id this folder already has.
- `paths`: for each universe spec, the folders and files it covers. A folder ends in `/` and covers every file below it; any other entry is an exact file. Paths are relative to the folder holding `.knowledge-bus/`. Refused: `*`, `?`, `\`, a leading `/`, an empty path or segment, a `.` or `..` segment. Each list is sorted by code point, with each path once. Only universe specs in this folder, its own or named from its parent, can be listed.

An empty `coverage.yaml`, or one holding only comments, is refused as not a mapping. Problems are checked in the order of this list: `from_parent` names in the order written, `paths` ids sorted. The error names the first problem. Only the nearest `.knowledge-bus/` has its `coverage.yaml` read.

An agent, led by a person, keeps `paths` up to date as files are created, deleted or moved. `kbp` only reads and checks `paths`.

`coverage.yaml` sits outside the protocol, like marks files, so it does not change the protocol version. A bare `kbp` check validates `coverage.yaml`. `--inspect` and `--explore` never read the file.

## Checking Other Code

Other code can apply the same rule to files handed to it. `checker/tests/cover/cases.json` lists the cases. Each case gives:

- the top folder;
- the file's path;
- each `.knowledge-bus/` on the path, with its files;
- the presets;
- the document type, no fit and the hat;
- the expected answer or error.

File paths are relative to the repository root.

Copy `cases.json` with every file it names, keeping relative paths. Code is correct when it gives every expected answer, compared by value, and for each expected error the same category and candidates. Other code need not match the message.
