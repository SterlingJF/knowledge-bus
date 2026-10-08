# Decision record

Document type in the Product development universe spec (product-development 0.9).

- Also called: ADR (Nygard) / MADR / record of decision
- Helps you: check whether a past decision still applies, and record a replacement when it no longer does
- Who uses it: future reader
- When it is used: any time after the decision
- No document needed when time-separation is none and reversibility is reversible. Depends on: Who has to reconstruct this reasoning without the author present? (time-separation); Can this step be undone, and at what cost? (reversibility)

## How to write it well

- Convention: One decision per record — context, decision, status, consequences — with status moving proposed to accepted to deprecated or superseded.
- Convention: The set of records is an append-only log. An accepted record is not edited; a changed decision is a new record that supersedes the old one, with the two linked, so the history of the thinking survives the change of direction.
- Heuristic: Write a record when someone will later need the reasoning without its author there to explain it, or when the decision would be costly to undo.
- Convention: ISO 42010 weighs a decision by impact and cost of change: many stakeholders affected, expensive to enforce, costly to reverse, non-obvious reasoning, major expenditure. Only one of those is about architecture.
- Convention: The form is not architecture-specific and never was. The same record shape serves a pricing, hiring or procurement decision; what changes with the domain is which decisions merit a record and what the record points at.
- Boundary: A decision record that grows into a design guide has stopped being a decision record.
- Refresh: Reassess when an observation named in the Reversal Condition occurs, or when the circumstances the decision rested on change. If the condition cannot be checked, find out what evidence is missing.

## Sections

### Decision

Answers: What did we decide?
Required.

- Boundary: Distinct from Accepted Consequences: the decision states what is chosen and why ('we drop the evening track because only four signed up'); a consequence is what the choice brings that we accept ('tutors lose Thursday income'). Stating what is chosen is the decision even when it reads as a loss.
- Convention: One decision per record, dated, and never edited in place: a stale decision is superseded by a new record.
- Convention: Bad rationale has a recognisable shape — 'everybody does it', 'we have always done it like that', 'this will look good on my resume'. Reasoning that survives none of those is not reasoning.
- Convention: Give the reasons beside the choice, and name the criteria the chosen option met best. MADR's template allows the outcome to cite its decision drivers in this way.
- Heuristic: Name the objective or requirement the decision serves. If it serves none, question whether it needs making at all.

### Accepted consequences

Answers: What consequences of the decision do we accept?
Required.

- Convention: All consequences belong here, not only the favourable ones — positive, negative and neutral alike. The consequences of one decision commonly become the context of the next.
- Boundary: Distinct from Reversal Condition: a consequence is what the decision brings, known and accepted when it is taken; a reversal condition is an observation not yet made that would reopen it. A consequence turning out worse than accepted is one such observation.
- Boundary: Distinct from Trade-offs: a trade-off is a promising direction the offering refuses as part of its strategy; a consequence follows from one decision already taken and is accepted with it. If the entry traces back to a specific decision, it belongs here.
- Boundary: Distinct from Risks & Assumptions: a consequence is accepted and expected, a risk is uncertain. Filing a known cost as a risk hides that someone chose it.
- Empty: An option can outperform every alternative and still have consequences. Distinguish none identified from not assessed; neither follows from the option dominating the comparison.

### Reversal condition

Answers: What observation would reopen the decision?
Required.

- Heuristic: An observable condition, not a review date: what would have to be seen for this to stop holding. 'Revisit in six months' is a calendar entry; 'if median latency exceeds the budget for two consecutive quarters' is a condition.
- Boundary: Checking that a decision was implemented and deciding whether it should change are different activities. Implementation compliance is not itself a condition for reconsideration.
- Convention: Record uncertainty that may warrant revisiting the decision. New evidence or changed circumstances can justify reconsideration regardless of its original confidence.
- Boundary: Distinct from Risks & Assumptions: a failing assumption is one trigger among several. A better alternative appearing, a constraint lifting, or an authority changing reopen the decision without any assumption having failed.
- Empty: State what would warrant reconsideration. If no trigger has been identified, say so; this does not establish that the commitment is irreversible.

### Alternatives considered

Answers: Which options do we consider?
Required.

- Boundary: Describe and compare the options here, including the chosen option. Decision records the commitment and why it was chosen.
- Convention: Standard in RFCs, decision documents and decision records. Describe the options considered, including the chosen option.
- Convention: Naming the rejected options is grammatically obligatory in the Y-statement form — 'and neglected …' — not an optional courtesy to the reader.
- Convention: Check that the options are feasible, diverse and comprehensive: each could really be done, none is a small variant of another, and together they cover the realistic ways to solve the problem.
- Pitfall: Flanking a preferred course with two deliberately unattractive alternatives simulates choice rather than offering it.
- Heuristic: Two honest alternatives beat five straw men. Absence invites re-litigation.

### Problem statement

Answers: What problem should the work solve?
Required.
Kept in another document (Lean canvas or Opportunity assessment): link to that document. The notes below are for writing the section in that document.

- Heuristic: Name the problem and whose problem it is, with no solution built in.
- Pitfall: Solution-shaped problems pre-commit the answer.
- Heuristic: One quantified pain beats five asserted ones.

### Decision criteria

Answers: By what criteria do we judge the options?
Required when authority is approve or statutory; otherwise optional. Depends on: Who has to be asked or told before the work goes ahead? (authority)
Kept in another document (Decision brief): link to that document. The notes below are for writing the section in that document.

- Heuristic: Give each criterion its weight or rank, so a reader can see how conflicting criteria were balanced. State it before the options are scored, not inside the decision's reasoning.
- Convention: Criteria are a first-class object, not prose inside the rationale: options are assessed against them, and the assessment carries a sign. That is what lets a later reader see that two decisions were judged against the same criterion, or against conflicting ones.
- Convention: Where an outside body may review the decision, name every factor that was balanced and say how each entered the decision. A US Record of Decision had to do exactly this.
- Boundary: Distinct from Goals & Non-Goals and from Constraints: a criterion is a dimension options are compared along, a goal is an outcome aimed for, and a constraint is a fixed limit that admits no trade-off.
- Empty: Honestly empty means the choice was made on one dominant consideration already stated in the decision — not that the criteria were never articulated.

### Constraints

Answers: What imposed limits apply to the work?
When applicable.

- Heuristic: Imposed, not chosen: regulation, budget, deadline, platform, physics.
- Boundary: Distinct from Cross-Cutting Concerns: a constraint is an imposed limit on the work that no design choice moves — budget, deadline, platform, what the law allows; a cross-cutting concern is an obligation every part of the solution must be designed to meet — security, privacy, accessibility. One law can supply both: a limit here, a property demanded throughout there.
- Boundary: Distinct from Trade-offs. Mislabelling a choice as a constraint hides a decision.

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

### Risks and assumptions

Answers: What could harm the work if it happened or proved wrong?
When applicable.
Kept in another document (Opportunity assessment or Risk assessment): link to that document. The notes below are for writing the section in that document.

- Heuristic: For an assumption, state what is being relied on and how it will be checked. For a risk, state what could happen, its significance, and the response.
- Boundary: Distinct from Opportunities & Threats: there an outside condition is judged for planning; here anything inside or outside that could harm the work gets a response and someone to handle it.
- Convention: Before committing, imagine the work has already failed and have each person write down why. This brings out risks people hesitate to raise.
- Convention: The RFC tradition records drawbacks — known, accepted costs — separately from risks, which are uncertainties.
- Heuristic, when authority is approve or statutory: Where an approver or regulator will review the work, date each entry and name its owner and response, so the record can be audited. Depends on: Who has to be asked or told before the work goes ahead? (authority)

## What the conditions mean

- authority is approve: Does someone's yes have to come first?
- authority is statutory: Does a law or regulator require a yes first?
