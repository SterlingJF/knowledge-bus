---
name: kb-uncover-decision
description: Recover a decision's alternatives, constraints, authority, and reversal conditions when its record lacks context.
---

# Uncover a Decision

**Purpose — recover the constraints that were live when the decision was made, not just its output. A record that carries only the conclusion reads as true and is unusable.**

## Knowledge Bus Directory

Follow [Knowledge Bus Directory](references/knowledge-bus-directory.md). Use an explicit target when supplied; otherwise resolve the nearest `.knowledge-bus/` from the user's working directory. Inspect existing files before proposing changes and preserve existing definitions and decision history. Do not combine definitions from different Knowledge Bus directories. Write only inside the selected `.knowledge-bus/`; leave source files untouched. If definitions are absent, ask the user to select or explicitly create a set rather than inventing one silently.

## Standing constraints

- **Past tense throughout.** What was live, not what is sensible now.
- **Reconstruction is flagged as reconstruction.** Memory is not evidence.
- **Do not fill missing history.**

## The flow

- **1. State the decision as recorded.** Name what is missing from it.

- **2. Recover the provenance.** Who was in the room, whose call it was, and on what authority. This feeds later collision rulings — an ingest weighing two conflicting docs needs to know which carried the authority.

- **3. Recover the live alternatives.** What was actually on the table, not what could have been.

- **4. Recover the binding constraints.** What ruled options out, in force at the time.

- **5. Seek the reversal condition.** Record it when supported; otherwise mark it unknown.

- **6. File as answers** against declared questions; label fact, recollection, reconstruction, and missing evidence. Flag what stayed ambiguous.
