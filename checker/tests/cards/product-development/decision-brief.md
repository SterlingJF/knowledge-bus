# Decision brief

Document type in the Product development universe spec (product-development 0.9).

- Also called: options paper / decision document (DACI, SPADE)
- Helps you: choose one of several options by a set date
- Who uses it: the person accountable for the choice
- When it is used: before anyone commits to an option
- No document needed when time-separation is none and reversibility is reversible. Depends on: Who has to reconstruct this reasoning without the author present? (time-separation); Can this step be undone, and at what cost? (reversibility)

## How to write it well

- Convention: Exactly one named decider. Without one, a brief produces discussion rather than a decision.
- Convention, when authority is approve or statutory: Beside the decider, list who contributes and who is only informed: contributors give input, those informed do not. Neither decides. Depends on: Who has to be asked or told before the work goes ahead? (authority)
- Convention: The framing carries a date and the reason for that date. Without a deadline, the brief is only a discussion document.
- Convention: Quality is judged before the outcome is known, on the frame, the alternatives, the information, the criteria and trade-offs, the reasoning, and the commitment to act — and is no better than the weakest of them.
- Convention: Finish with a commitment step: until the choice is voiced it is not taken.
- Convention, when authority is approve or statutory: Agreement obtained privately and never voiced does not bind, and the decision reopens the first time it meets friction. Depends on: Who has to be asked or told before the work goes ahead? (authority)
- Boundary: Distinct from the Decision Record, which it feeds. Ask whether the choice is still to be made: while it is, the criteria and options belong in this brief; once it is made, the Decision Record keeps the options that were rejected and why.
- Boundary: Distinct from the Opportunity Assessment, which asks whether to pursue one thing at all, and from the Design Doc, which offers one approach to react to. This one picks among several.
- Refresh: It goes stale the moment the decision is taken. Stop editing it then: changing it afterwards reopens a settled choice against criteria that have since moved.

## Sections

### Alternatives considered

Answers: Which options do we consider?
Required.

- Boundary: Describe and compare the options here, including the chosen option. Decision records the commitment and why it was chosen.
- Convention: Standard in RFCs, decision documents and decision records. Describe the options considered, including the chosen option.
- Convention: Naming the rejected options is grammatically obligatory in the Y-statement form — 'and neglected …' — not an optional courtesy to the reader.
- Convention: Check that the options are feasible, diverse and comprehensive: each could really be done, none is a small variant of another, and together they cover the realistic ways to solve the problem.
- Pitfall: Flanking a preferred course with two deliberately unattractive alternatives simulates choice rather than offering it.
- Heuristic: Two honest alternatives beat five straw men. Absence invites re-litigation.

### Decision criteria

Answers: By what criteria do we judge the options?
Required.

- Heuristic: Give each criterion its weight or rank, so a reader can see how conflicting criteria were balanced. State it before the options are scored, not inside the decision's reasoning.
- Convention: Criteria are a first-class object, not prose inside the rationale: options are assessed against them, and the assessment carries a sign. That is what lets a later reader see that two decisions were judged against the same criterion, or against conflicting ones.
- Convention: Where an outside body may review the decision, name every factor that was balanced and say how each entered the decision. A US Record of Decision had to do exactly this.
- Boundary: Distinct from Goals & Non-Goals and from Constraints: a criterion is a dimension options are compared along, a goal is an outcome aimed for, and a constraint is a fixed limit that admits no trade-off.
- Empty: Honestly empty means the choice was made on one dominant consideration already stated in the decision — not that the criteria were never articulated.

### Decision authority and approvals

Answers: Whose approval does the work need?
Required when authority is approve or statutory; otherwise optional. Depends on: Who has to be asked or told before the work goes ahead? (authority)

- Heuristic: For each approval, name who gives it and who gave them the right to give it. If nobody holds that right, close the gap before relying on the approval.
- Boundary: Distinct from Consent & Authority: an approval is a decision someone takes over whether the work goes ahead; a licence, permit, consent or legal basis is the permission the work holds. A regulator can appear in both: as an approval here, as its clearance there.
- Empty: If the work needs no one's approval, say so and say how you know, for example that the spend is within your own authority. A blank list with no such note reads as not yet checked.

### Problem statement

Answers: What problem should the work solve?
Required.
Kept in another document (Lean canvas or Opportunity assessment): link to that document. The notes below are for writing the section in that document.

- Heuristic: Name the problem and whose problem it is, with no solution built in.
- Pitfall: Solution-shaped problems pre-commit the answer.
- Heuristic: One quantified pain beats five asserted ones.

### Constraints

Answers: What imposed limits apply to the work?
When applicable.

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

### Prior art

Answers: How have others solved problems like ours?
When applicable.

- Heuristic: Say what each precedent teaches the work: what to copy and what to avoid. A list of look-alikes with no lesson is not prior art.
- Convention: A standard RFC section: precedent survey across other systems, organisations or communities.
- Boundary: Distinct from Competitor Profile: that grades how well each alternative serves the people the offering is for; this draws lessons from how others solved similar problems, whether or not they compete. Absence invites reinvention.

### Open questions

Answers: Which questions about the work remain open?
When applicable.

- Heuristic: Each wants an owner and a resolution path. An unowned question is a risk mislabelled.
- Boundary: Distinct from Risks & Assumptions: an open question is something to answer before a point can be settled; an assumption is a belief the work proceeds on and checks along the way. Proceeding without the answer turns the question into an assumption.
- Heuristic: Compare the list across drafts: it should get shorter. A list that keeps growing means the work is not yet ready to settle.
- Empty: Write 'none open' only when every question raised has been answered or recorded as an assumption, so a reader can tell it apart from a list nobody has drawn up.

### Scope in out

Answers: What do we include in the solution now, defer, or exclude?
When applicable.

- Heuristic: Three lists, not two: included, deferred with a revisit trigger, and excluded with the reason.
- Boundary: Distinct from Trade-offs: scope excludes parts of the solution for this work; Trade-offs refuses directions for the offering as a whole.
- Heuristic: The excluded list is the valuable one — it prevents silent re-expansion.
- Convention: The deferred list is where natural extensions land — the RFC tradition's future possibilities.

## What the conditions mean

- authority is approve: Does someone's yes have to come first?
- authority is statutory: Does a law or regulator require a yes first?
