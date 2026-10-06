# Generated: Claude plugin eval cases

Written by `tools/evals/write_claude.py` from `evals/universe.yaml`. Do not edit; regenerate.

## What does not carry over

- Typed decisions are asked of the case's llm judge instead of a decision model: action-names-an-action, one-question.
- Flag checks only nominate cases for a model tier, so they have no grader: direct-statement, named-referents, one-point-terse, one-question, plain-words, present-state.
- Recognition checks are graded by the neutral runner only: values-recognised.
- Sort checks are graded by the neutral runner only: sorts-reliably.
