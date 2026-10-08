# Risk assessment

Document type in the Product development universe spec (product-development 0.9).

- Also called: risk register
- Helps you: decide which risks to reduce, accept or watch, and who handles each
- Who uses it: the person accountable for the work
- When it is used: before the work starts, and while it runs
- No document needed when time-separation is none and reversibility is reversible. Depends on: Who has to reconstruct this reasoning without the author present? (time-separation); Can this step be undone, and at what cost? (reversibility)

## How to write it well

- Convention: The risk register is standard across PMBOK, PRINCE2 and ISO Guide 73 — a record of information about identified risks.

## Sections

### Risks and assumptions

Answers: What could harm the work if it happened or proved wrong?
Required.

- Heuristic: For an assumption, state what is being relied on and how it will be checked. For a risk, state what could happen, its significance, and the response.
- Boundary: Distinct from Opportunities & Threats: there an outside condition is judged for planning; here anything inside or outside that could harm the work gets a response and someone to handle it.
- Convention: Before committing, imagine the work has already failed and have each person write down why. This brings out risks people hesitate to raise.
- Convention: The RFC tradition records drawbacks — known, accepted costs — separately from risks, which are uncertainties.
- Heuristic, when authority is approve or statutory: Where an approver or regulator will review the work, date each entry and name its owner and response, so the record can be audited. Depends on: Who has to be asked or told before the work goes ahead? (authority)

### Affected and interested parties

Answers: Who does the work affect beyond those accountable for it?
Required.

- Heuristic: List everyone who bears a cost, hazard or loss from the work, including people who never use what it produces, such as the neighbours of a building site.
- Empty: If the work's effects fall only on those accountable for it, say so and leave the list empty for that reason. A blank list with no such note cannot show that anyone checked who else carries the work's risks.
- Heuristic: For each party, record what claim it has to be heard, such as a legal right, a contract or direct harm. That claim decides whether a risk it carries can be accepted without asking it.
- Boundary: Distinct from Decision Authority & Approvals: a party here is heard and weighed; an approver there decides whether the work goes ahead. If the work needs their yes, list them there.

### Guardrail health metrics

Answers: Which measures must stay within set ranges while we pursue other targets?
When applicable.
Kept in another document (Success metrics): link to that document. The notes below are for writing the section in that document.

- Heuristic: The counterweight to any target — latency, churn, quality, trust; burnout at personal scale.
- Convention: Guardrails that protect the organisation, such as page-load time or revenue, are largely shared across experiments. Define them once, for the whole organisation, and reuse them in every effort.
- Pitfall: Experimentation-heavy organisations formalise these as launch blockers; everywhere else they stay implicit until an incident. Write them down first.
- Boundary: Distinct from Input Metrics. Ask whether the number should move or hold: an input metric is pushed to move, a guardrail is held within its range. Neither the Business Model Canvas nor the Lean Canvas has a block for guardrails, so keep them in Success Metrics.

### Open questions

Answers: Which questions about the work remain open?
When applicable.

- Heuristic: Each wants an owner and a resolution path. An unowned question is a risk mislabelled.
- Boundary: Distinct from Risks & Assumptions: an open question is something to answer before a point can be settled; an assumption is a belief the work proceeds on and checks along the way. Proceeding without the answer turns the question into an assumption.
- Heuristic: Compare the list across drafts: it should get shorter. A list that keeps growing means the work is not yet ready to settle.
- Empty: Write 'none open' only when every question raised has been answered or recorded as an assumption, so a reader can tell it apart from a list nobody has drawn up.

## What the conditions mean

- authority is approve: Does someone's yes have to come first?
- authority is statutory: Does a law or regulator require a yes first?
