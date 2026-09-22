---
name: kb-check
description: Validate Knowledge Bus definitions and guidance after edits, and explain each failure and its fix.
---

# Check Spec Files

**Purpose — answer "is this still valid?" with the clause that failed and the fix it calls for, never a bare pass/fail.**

## The flow

- **1. Locate.** The installed package supplies the checker and protocol. Explicit file or directory targets take precedence. Without a target, use the nearest `.knowledge-bus/` from the user's working directory upward. Pass the resolved absolute Knowledge Bus directory path when the agent host runs commands from a different directory. Never combine definitions from different Knowledge Bus directories. If no `.knowledge-bus/` exists, report it; checking never creates one. See [Knowledge Bus Directory](references/knowledge-bus-directory.md). The implementation checkout retains its bundled-example default when no `.knowledge-bus/` directory is found.

- **2. Run.** Follow [Checker for Agent Workflows](references/agent-runtime.md). Run the bundled checker with `--validate <resolved-target>`. The format self-check runs first; an unsound format stops the run.

- **3. Interpret.** Every refusal names its clause. Translate each into the edit it calls for; see [Checker for Agent Workflows](references/agent-runtime.md) for the clause families.

- **4. Report.** Per-file pass/fail, then refusals grouped by fix, not by file. If Explorer inspection was also requested, report renderability separately.

## Common failures

Each row is a registered refusal; every one has a corpus file that must fail for exactly this reason.

| Refusal contains                      | Fix                                                                                                            |
| ------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `already carried by`                  | The code is taken. Mint a fresh one (`kbp --mint <kind> 1 <resolved-target>`); never reuse or reassign a code. |
| `missing required`                    | The declaration lacks a required key (`id`, `code`, its identity). Add it; the message names which.            |
| `may not be referenced by a universe` | A `when:` predicate names a factor. Factors are unwired by design — predicate on a frame instead.              |
| `composition refs unknown elements`   | A composition entry names an element the spec never declares. Declare it or correct the id.                    |
| `does not match`                      | `conforms_to` disagrees with the format version. Update it deliberately, against the changelog.                |
