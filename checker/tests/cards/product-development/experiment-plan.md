# Experiment plan

Document type in the Product development universe spec (product-development 0.9).

- Also called: experiment plan / pre-registration / study protocol
- Helps you: commit to a test's prediction and its measures in advance
- Who uses it: whoever runs the test
- When it is used: before collecting any data for the test
- Not used when outcome form is creation or service. Depends on: What kind of thing does this work produce? (outcome)
- No document needed when time-separation is none and reversibility is reversible. Depends on: Who has to reconstruct this reasoning without the author present? (time-separation); Can this step be undone, and at what cost? (reversibility)

## Sections

### Hypothesis

Answers: What testable prediction do we make?
Required.
Applies only when outcome form is finding. Depends on: What kind of thing does this work produce? (outcome)

- Heuristic: Name the observation that would show the prediction wrong. A prediction no observation could contradict is not testable.
- Boundary: Distinct from Success Criteria: a success criterion says what counts as the work succeeding; a hypothesis says what the world will show. A test that refutes its hypothesis can still succeed as work, by settling the question.
- Boundary: Distinct from Risks & Assumptions: an assumption is something the work relies on; a hypothesis is a prediction stated so a test can show it wrong. Testing an assumption states it as a hypothesis here; the assumption stays in the register until the test settles it.

### Measurement protocol

Answers: How do we measure each thing the prediction names?
Required.
Applies only when outcome form is finding. Depends on: What kind of thing does this work produce? (outcome)

- Heuristic: Fix the procedure before any data are collected, and say for each thing the prediction names how it becomes a measured quantity: instrument, unit, sample and who records it. A procedure changed after the data arrive turns the test into exploration.

### Guardrail health metrics

Answers: Which measures must stay within set ranges while we pursue other targets?
When applicable.
Kept in another document (Success metrics): link to that document. The notes below are for writing the section in that document.

- Heuristic: The counterweight to any target — latency, churn, quality, trust; burnout at personal scale.
- Convention: Guardrails that protect the organisation, such as page-load time or revenue, are largely shared across experiments. Define them once, for the whole organisation, and reuse them in every effort.
- Pitfall: Experimentation-heavy organisations formalise these as launch blockers; everywhere else they stay implicit until an incident. Write them down first.
- Boundary: Distinct from Input Metrics. Ask whether the number should move or hold: an input metric is pushed to move, a guardrail is held within its range. Neither the Business Model Canvas nor the Lean Canvas has a block for guardrails, so keep them in Success Metrics.
