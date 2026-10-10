# Architecture overview

Document type in the Product development universe spec (product-development 0.9).

- Also called: C4 levels 1–2
- Helps you: find which parts of the system a change will affect
- Who uses it: whoever will change the system
- When it is used: before changing the system
- No document needed when time-separation is none and reversibility is reversible. Depends on: Who has to reconstruct this reasoning without the author present? (time-separation); Can this step be undone, and at what cost? (reversibility)

## How to write it well

- Convention: C4 levels 1 and 2 — system context and containers.

## Sections

### System boundary and context

Answers: What is the system itself responsible for?
Required.
Kept in another document (System context diagram): link to that document. The notes below are for writing the section in that document.

- Convention: C4 level 1: the system, its users, and the external systems it exchanges with.
- Heuristic: The boundary is a security and ownership decision, not just a drawing choice.

### Components and responsibilities

Answers: What is each part of the system responsible for?
Required.
Applies only when outcome form is creation or service. Depends on: What kind of thing does this work produce? (outcome)

- Heuristic: Give each part one responsibility you can state in a single sentence. If the sentence needs an 'and', consider splitting the part.
- Pitfall: Drawing the parts of the system on a diagram meant to show only the system and its surroundings makes that diagram hard to read. Keep the system context diagram to the system as one box, and show its parts in the Architecture Overview.
- Boundary: Components run and own behaviour. The named categories the system reasons with are Canonical Model.

### Data flows and integrations

Answers: What data moves where?
Required.

- Heuristic: Flows name the contract — API, event, file — and the contract's owner.
- Heuristic, when authority is approve or statutory: In regulated and privacy contexts flows are compliance surface. Annotate data classification — personally identifiable information, protected health information — where it applies. Depends on: Who has to be asked or told before the work goes ahead? (authority)

### Constraints

Answers: What imposed limits apply to the work?
When applicable.
Kept in another document (Design doc or Brand identity guide or Decision brief or Decision record): link to that document. The notes below are for writing the section in that document.

- Heuristic: Imposed, not chosen: regulation, budget, deadline, platform, physics.
- Boundary: Distinct from Cross-Cutting Concerns: a constraint is an imposed limit on the work that no design choice moves — budget, deadline, platform, what the law allows; a cross-cutting concern is an obligation every part of the solution must be designed to meet — security, privacy, accessibility. One law can supply both: a limit here, a property demanded throughout there.
- Boundary: Distinct from Trade-offs. Mislabelling a choice as a constraint hides a decision.

### Risks and assumptions

Answers: What could harm the work if it happened or proved wrong?
When applicable.
Kept in another document (Opportunity assessment or Risk assessment): link to that document. The notes below are for writing the section in that document.

- Heuristic: For an assumption, state what is being relied on and how it will be checked. For a risk, state what could happen, its significance, and the response.
- Boundary: Distinct from Opportunities & Threats: there an outside condition is judged for planning; here anything inside or outside that could harm the work gets a response and someone to handle it.
- Convention: Before committing, imagine the work has already failed and have each person write down why. This brings out risks people hesitate to raise.
- Convention: The RFC tradition records drawbacks — known, accepted costs — separately from risks, which are uncertainties.
- Heuristic, when authority is approve or statutory: Where an approver or regulator will review the work, date each entry and name its owner and response, so the record can be audited. Depends on: Who has to be asked or told before the work goes ahead? (authority)

### Canonical model

Answers: Which named categories does the system use?
When applicable.

- Heuristic: Give each category its identifier and the fields its entries carry, so the model fixes the shape of an entry and not only its name.
- Convention: Use each category's name the same way everywhere: in conversation, in documents and in the system itself. Keep it stable once other parts depend on it.
- Heuristic: Record the categories and their fields, with only as many example entries as a reader needs to understand them. A full list of entries is the offering's data and belongs with it.
- Heuristic: Documents that use these categories refer to this model for them, so each category is defined in one place.

### As built survey

Answers: What do measurements of the existing state show?
When applicable.

- Heuristic: Record each finding with how precisely it was measured and when it was observed. An undated survey cannot say whether it still holds.
- Boundary: Distinct from Constraints: the survey records what is actually in place; a constraint is a limit imposed on the work. A measured clearance is a finding here; a rule forbidding building into it is a constraint.

## What the conditions mean

- authority is approve: Does someone's yes have to come first?
- authority is statutory: Does a law or regulator require a yes first?
