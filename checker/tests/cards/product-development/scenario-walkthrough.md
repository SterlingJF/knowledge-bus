# Scenario walkthrough

Document type in the Product development universe spec (product-development 0.9).

- Also called: key path scenario
- Helps you: check, step by step, that one person can reach one goal through the solution
- Who uses it: reviewer
- When it is used: before the work starts
- No document needed when time-separation is none and reversibility is reversible. Depends on: Who has to reconstruct this reasoning without the author present? (time-separation); Can this step be undone, and at what cost? (reversibility)

## How to write it well

- Convention: Follow one person pursuing one goal, step by step. Use it early to settle what the solution should do, and leave detailed interface design out.
- Pitfall: Three unrelated practices share the name: a live usability test with users, an architecture review of quality attributes (ATAM), and a document or code inspection meeting. The walkthrough meant here is a written step-by-step trace of one person reaching one goal; if yours is a meeting or a test session, it is one of the others.

## Sections

### Stepwise trace

Answers: What happens at each step of one path through the solution?
Required.

- Boundary: Distinct from User / Job Stories: a story says what the solution should let a person do, one capability at a time; a trace follows one person through the solution in one circumstance, step by step, joins included.
- Heuristic: The joins are the content. No single story contains a seam, and a set of stories does not sum to one trace.
- Boundary: Distinct from Solution Overview: a trace follows one person in one concrete circumstance in full detail; the overview outlines all the behaviour at once. Ask whether the text follows one path or covers them all. In a design document, refer to the trace where the RFC template puts its guide-level explanation.

### User job stories

Answers: What should the solution let a person do?
Required.

- Convention: A user story (as-a / I-want / so-that) presumes a persona; a job story (when / I-want / so-I-can) presumes a circumstance. Pick one per document; do not mix.
- Heuristic: Acceptance criteria turn a story from a conversation-starter into testable scope.
- Boundary: Distinct from Jobs to Be Done: ask whether the line names what the solution must let a person do. A story does, and acceptance criteria test it; the job behind it stays true whatever is built.

### Data flows and integrations

Answers: What data moves where?
When applicable.
Kept in another document (Architecture overview or System context diagram): link to that document. The notes below are for writing the section in that document.

- Heuristic: Flows name the contract — API, event, file — and the contract's owner.
- Heuristic, when authority is approve or statutory: In regulated and privacy contexts flows are compliance surface. Annotate data classification — personally identifiable information, protected health information — where it applies. Depends on: Who has to be asked or told before the work goes ahead? (authority)

### Constraints

Answers: What imposed limits apply to the work?
When applicable.
Kept in another document (Design doc or Brand identity guide or Decision brief or Decision record): link to that document. The notes below are for writing the section in that document.

- Heuristic: Imposed, not chosen: regulation, budget, deadline, platform, physics.
- Boundary: Distinct from Cross-Cutting Concerns: a constraint is an imposed limit on the work that no design choice moves — budget, deadline, platform, what the law allows; a cross-cutting concern is an obligation every part of the solution must be designed to meet — security, privacy, accessibility. One law can supply both: a limit here, a property demanded throughout there.
- Boundary: Distinct from Trade-offs. Mislabelling a choice as a constraint hides a decision.

## What the conditions mean

- authority is approve: Does someone's yes have to come first?
- authority is statutory: Does a law or regulator require a yes first?
