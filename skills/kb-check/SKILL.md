---
name: kb-check
description: Validate spec files against the format and report each failure
  with its registered reason. Locates the format definition and every
  .kbp.yaml file (or takes explicit paths), runs the bundled kbp checker, and
  translates each refusal into the fix it calls for. Use when invoked via
  /kb-check, or when the user asks whether their knowledge files are still
  valid after an edit.
---

# Check Spec Files

**Purpose — answer "is this still valid?" with the clause that failed and the fix it calls for, never a bare pass/fail.**

## The flow

- **1. Locate.** Installed as a plugin, the checker and the format definition live at `${CLAUDE_PLUGIN_ROOT}`;
    the files to check are wherever the user's spec lives. In a clone of this repo, the checker walks up from
    the working directory looking for `spec/` and finds everything itself.

- **2. Run.**
    `UV_PROJECT_ENVIRONMENT="${CLAUDE_PLUGIN_DATA}/venv" uv run --project "${CLAUDE_PLUGIN_ROOT}" kbp --validate "${CLAUDE_PLUGIN_ROOT}/spec/knowledge-bus-protocol.yaml" <files>`
    — the env var keeps uv's venv out of the read-only plugin cache; from a repo clone, bare `uv run kbp`
    works. The format self-check runs first; an unsound format stops the run. If `uv` is not installed, say
    so and point at the uv install docs — do not improvise an invocation.

- **3. Interpret.** Every refusal names its clause. Translate each into the edit it calls for; see [docs/validation.md](../../docs/validation.md) for the clause families.

- **4. Report.** Per-file pass/fail, then refusals grouped by fix, not by file.

## Common failures

Each row is a registered refusal; every one has a corpus file that must fail for exactly this reason.

| Refusal contains | Fix |
| --- | --- |
| `already carried by` | The code is taken. Mint a fresh one (`just mint <kind>`); never reuse or reassign a code. |
| `missing required` | The declaration lacks a required key (`id`, `code`, its identity). Add it; the message names which. |
| `may not be referenced by a universe` | A `when:` predicate names a factor. Factors are unwired by design — predicate on a frame instead. |
| `composition refs unknown elements` | A composition entry names an element the spec never declares. Declare it or correct the id. |
| `does not match` | `conforms_to` disagrees with the format version. Update it deliberately, against the changelog. |
