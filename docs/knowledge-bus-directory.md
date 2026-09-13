# Knowledge Bus Directory

The `.knowledge-bus/` directory holds the definitions and supporting files for the folder that contains it. That containing folder can be a notes vault, document collection, project, or any other folder. This convention specifies where Knowledge Bus files live, not how to organize the surrounding files.

## Directory Contents

```text
my-folder/
├── ... source files ...
└── .knowledge-bus/
    ├── universe.kbp.yaml
    ├── type-guidance.kbp.yaml   # optional
    ├── answers.yaml            # when recording answers
    └── ingest-log.md           # when ingesting existing material
```

Any folder can contain a `.knowledge-bus/` directory. Git is not required. Define the structure before creating documents, or derive it from existing material through ingestion. Answers and an ingest log are not prerequisites for authoring a universe.

## Directory Selection

Explicit targets take precedence. Pass the folder, its `.knowledge-bus/` directory, or individual definition files:

```sh
kbp --validate path/to/my-folder
kbp --validate path/to/my-folder/.knowledge-bus/
kbp --validate path/to/universe.kbp.yaml path/to/type-guidance.kbp.yaml
```

Without an explicit target, the checker searches the current folder and then its parents for `.knowledge-bus/`. It uses the first one found and does not combine definitions from different directories. Calls from inside `.knowledge-bus/` use that directory. An empty or incomplete nearer directory does not fall back to a parent's `.knowledge-bus/`.

The selected Knowledge Bus directory supplies its directly contained `*.kbp.yaml` files together, so guidance can resolve its universe. Answers and logs are not checker inputs. Explicit file targets select exactly those files; include the universe when checking guidance.

A generic directory target without its own `.knowledge-bus/` still scans for `*.kbp.yaml` files, for example a reference collection or test corpus. It skips metadata directories and nested folders that contain their own `.knowledge-bus/`. Directory scans do not follow nested directory symlinks.

Missing definitions are an error when checking. Checking never creates a `.knowledge-bus/` directory.

## Creating and Updating Definitions

Create `.knowledge-bus/` when the user asks to set up definitions for a folder. There is no separate `kbp init` command. Keep writes inside the selected metadata directory and leave existing source files untouched.

Inspect existing definitions, guidance, answers, and logs before writing. Reuse them or propose deliberate changes; do not reset or blindly overwrite them. Preserve decisions and history. Ask how to proceed if existing content is incompatible or ambiguous.

During ingestion, exclude every `.knowledge-bus/` directory from source material. Skip and report nested folders that contain their own `.knowledge-bus/`; ingest them separately only when explicitly targeted.

## Protocol and Examples

The installed checker carries its protocol. Knowledge Bus directory discovery does not search for a `spec/` directory. An explicit protocol file can still override the bundled protocol.

In the implementation checkout, `spec/` remains the protocol source and `universes/` remains the bundled example collection. A bare `uv run kbp` there validates the examples when no `.knowledge-bus/` directory is found. Those reference files do not move into `.knowledge-bus/`.

## Previous Locations

The sibling `<folder>-spec/` convention is no longer supported for discovery or output. There is no fallback or migration. Existing folders are not moved or deleted. An explicitly supplied file remains a valid checker target regardless of its location.
