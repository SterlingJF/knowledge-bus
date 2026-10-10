# Design doc

Document type in the Product development universe spec (product-development 0.9).

- Also called: RFC / RFD
- Helps you: agree to or object to one proposed approach
- Who uses it: reviewer
- When it is used: before the work starts
- No document needed when time-separation is none and reversibility is reversible. Depends on: Who has to reconstruct this reasoning without the author present? (time-separation); Can this step be undone, and at what cost? (reversibility)

## How to write it well

- Convention: Canonical sections: context and scope, goals and non-goals, the actual design, alternatives considered, cross-cutting concerns. Skip the document when the solution is unambiguous.
- Convention: Most large projects start with a PRD to define the problem, followed by an RFC to propose a solution.
- Convention: The request-for-discussion is the same document family, inspired by the IETF's RFC series.
- Pitfall: Do not mistake this for a Solution Design Document, an enterprise-implementation deliverable whose content belongs in the Architecture Overview. A design doc proposes one approach for reviewers to agree to or object to.

## Sections

### Problem statement

Answers: What problem should the work solve?
Required.
Kept in another document (Lean canvas or Opportunity assessment): link to that document. The notes below are for writing the section in that document.

- Heuristic: Name the problem and whose problem it is, with no solution built in.
- Pitfall: Solution-shaped problems pre-commit the answer.
- Heuristic: One quantified pain beats five asserted ones.

### Goals and non goals

Answers: Which goals does the work pursue?
Required.

- Convention: List non-goals beside the goals. Each should be something that could reasonably be a goal and is explicitly chosen not to be; a plain negation such as 'the system should not crash' does not count.
- Boundary: Distinct from Success Criteria: a goal names what the work aims at; a success criterion sets the observable threshold, with a date, at which the work counts as having met it. A goal given a number and a date has become a success criterion.
- Boundary: Distinct from Scope (In / Out) and Trade-offs, which also set things aside. Ask what is being set aside: an aim of this work is a non-goal here; a part of the solution goes in Scope's excluded list; a promising direction for the offering as a whole goes in Trade-offs.

### Solution overview

Answers: What is the intended solution, in outline?
Required.

- Boundary: Distinct from Components & Responsibilities and the other architecture elements. Ask whether a line says what the solution does and how people use it, or how it technically holds together; the second belongs there.
- Convention: A Lean Canvas keeps this deliberately thin — top features only; a design document gives it a full section.
- Heuristic: State what the solution deliberately does not do. Pairs with Scope (In / Out).

### Alternatives considered

Answers: Which options do we consider?
Required.

- Boundary: Describe and compare the options here, including the chosen option. Decision records the commitment and why it was chosen.
- Convention: Standard in RFCs, decision documents and decision records. Describe the options considered, including the chosen option.
- Convention: Naming the rejected options is grammatically obligatory in the Y-statement form — 'and neglected …' — not an optional courtesy to the reader.
- Convention: Check that the options are feasible, diverse and comprehensive: each could really be done, none is a small variant of another, and together they cover the realistic ways to solve the problem.
- Pitfall: Flanking a preferred course with two deliberately unattractive alternatives simulates choice rather than offering it.
- Heuristic: Two honest alternatives beat five straw men. Absence invites re-litigation.

### Open questions

Answers: Which questions about the work remain open?
Required.

- Heuristic: Each wants an owner and a resolution path. An unowned question is a risk mislabelled.
- Boundary: Distinct from Risks & Assumptions: an open question is something to answer before a point can be settled; an assumption is a belief the work proceeds on and checks along the way. Proceeding without the answer turns the question into an assumption.
- Heuristic: Compare the list across drafts: it should get shorter. A list that keeps growing means the work is not yet ready to settle.
- Empty: Write 'none open' only when every question raised has been answered or recorded as an assumption, so a reader can tell it apart from a list nobody has drawn up.

### Constraints

Answers: What imposed limits apply to the work?
Required when authority is approve or statutory; otherwise optional. Depends on: Who has to be asked or told before the work goes ahead? (authority)

- Heuristic: Imposed, not chosen: regulation, budget, deadline, platform, physics.
- Boundary: Distinct from Cross-Cutting Concerns: a constraint is an imposed limit on the work that no design choice moves — budget, deadline, platform, what the law allows; a cross-cutting concern is an obligation every part of the solution must be designed to meet — security, privacy, accessibility. One law can supply both: a limit here, a property demanded throughout there.
- Boundary: Distinct from Trade-offs. Mislabelling a choice as a constraint hides a decision.

### Cross cutting concerns

Answers: Which requirements must every part of the solution meet?
Required when authority is approve or statutory; otherwise optional. Depends on: Who has to be asked or told before the work goes ahead? (authority)

- Convention: At minimum, say how the solution handles security, privacy and observability (how you will see what it is doing once it runs). Design docs at Google use this section to make sure these are always taken into consideration.
- Heuristic, when authority is approve or statutory: Regulated domains extend the list — compliance, audit, accessibility. Depends on: Who has to be asked or told before the work goes ahead? (authority)
- Heuristic: Exists so these get weighed while change is still cheap.
- Convention: Take accessibility requirements from WCAG 2.2, whose success criteria can each be tested; normal text, for example, needs a contrast ratio of at least 4.5:1. They apply to the brand's colours and type like everything else.

### Risks and assumptions

Answers: What could harm the work if it happened or proved wrong?
Required when authority is approve or statutory; otherwise optional. Depends on: Who has to be asked or told before the work goes ahead? (authority)
Kept in another document (Opportunity assessment or Risk assessment): link to that document. The notes below are for writing the section in that document.

- Heuristic: For an assumption, state what is being relied on and how it will be checked. For a risk, state what could happen, its significance, and the response.
- Boundary: Distinct from Opportunities & Threats: there an outside condition is judged for planning; here anything inside or outside that could harm the work gets a response and someone to handle it.
- Convention: Before committing, imagine the work has already failed and have each person write down why. This brings out risks people hesitate to raise.
- Convention: The RFC tradition records drawbacks — known, accepted costs — separately from risks, which are uncertainties.
- Heuristic, when authority is approve or statutory: Where an approver or regulator will review the work, date each entry and name its owner and response, so the record can be audited. Depends on: Who has to be asked or told before the work goes ahead? (authority)

### Sequence and foreclosure

Answers: In what order must the work proceed?
Required when reversibility is costly or irreversible; otherwise optional. Depends on: Can this step be undone, and at what cost? (reversibility)

- Convention: Sort the steps by whether they can be walked back. A step you can reverse is a two-way door and deserves speed; a step you cannot is a one-way door and deserves deliberation. Applying the heavy process to everything is as costly a mistake as applying the light one to the irreversible.
- Heuristic: Name what each step forecloses, not merely what it enables. An order that closes no doors is a preference, not a sequence.
- Empty: Honestly empty means every step is independently reversible in any order — in which case say so, because that is the licence to move fast.

### Rollout and phasing

Answers: In what stages do we introduce the solution?
When applicable.

- Heuristic: Give each stage its audience, such as a pilot group, a wider beta or everyone, and the observation that would stop or roll back the rollout before the next stage.
- Boundary: Distinct from Sequence & Foreclosure: rollout stages how widely the solution is introduced, with a stopping condition per stage; sequence orders the work's own steps by what each forecloses.
- Heuristic: Enterprise implementation practice treats this as a core deliverable section. Product briefs include it only when release risk warrants.

### Prior art

Answers: How have others solved problems like ours?
When applicable.

- Heuristic: Say what each precedent teaches the work: what to copy and what to avoid. A list of look-alikes with no lesson is not prior art.
- Convention: A standard RFC section: precedent survey across other systems, organisations or communities.
- Boundary: Distinct from Competitor Profile: that grades how well each alternative serves the people the offering is for; this draws lessons from how others solved similar problems, whether or not they compete. Absence invites reinvention.

### Scope in out

Answers: What do we include in the solution now, defer, or exclude?
When applicable.

- Heuristic: Three lists, not two: included, deferred with a revisit trigger, and excluded with the reason.
- Boundary: Distinct from Trade-offs: scope excludes parts of the solution for this work; Trade-offs refuses directions for the offering as a whole.
- Heuristic: The excluded list is the valuable one — it prevents silent re-expansion.
- Convention: The deferred list is where natural extensions land — the RFC tradition's future possibilities.

### Success criteria

Answers: What observable result counts as success for the work?
When applicable.
Kept in another document (Opportunity assessment or Success metrics): link to that document. The notes below are for writing the section in that document.

- Pitfall: 'Improve X' invites post-hoc rationalisation. Set a threshold and a measurement date.
- Heuristic: Per-initiative acceptance, set before the work, expiring with the effort — unlike metrics that run continuously.
- Heuristic: A product requirements document's launch 'success metrics' and an OKR's key results belong here: each is a threshold with a date, usually on an input metric.
- Heuristic: Point to the shared measures the work must not break instead of copying them, and state in full each threshold this work commits to.

### User job stories

Answers: What should the solution let a person do?
When applicable.

- Convention: A user story (as-a / I-want / so-that) presumes a persona; a job story (when / I-want / so-I-can) presumes a circumstance. Pick one per document; do not mix.
- Heuristic: Acceptance criteria turn a story from a conversation-starter into testable scope.
- Boundary: Distinct from Jobs to Be Done: ask whether the line names what the solution must let a person do. A story does, and acceptance criteria test it; the job behind it stays true whatever is built.

### Stepwise trace

Answers: What happens at each step of one path through the solution?
When applicable.
Kept in another document (Scenario walkthrough): link to that document. The notes below are for writing the section in that document.

- Boundary: Distinct from User / Job Stories: a story says what the solution should let a person do, one capability at a time; a trace follows one person through the solution in one circumstance, step by step, joins included.
- Heuristic: The joins are the content. No single story contains a seam, and a set of stories does not sum to one trace.
- Boundary: Distinct from Solution Overview: a trace follows one person in one concrete circumstance in full detail; the overview outlines all the behaviour at once. Ask whether the text follows one path or covers them all. In a design document, refer to the trace where the RFC template puts its guide-level explanation.

### Canonical model

Answers: Which named categories does the system use?
When applicable.
Kept in another document (Architecture overview): link to that document. The notes below are for writing the section in that document.

- Heuristic: Give each category its identifier and the fields its entries carry, so the model fixes the shape of an entry and not only its name.
- Convention: Use each category's name the same way everywhere: in conversation, in documents and in the system itself. Keep it stable once other parts depend on it.
- Heuristic: Record the categories and their fields, with only as many example entries as a reader needs to understand them. A full list of entries is the offering's data and belongs with it.
- Heuristic: Documents that use these categories refer to this model for them, so each category is defined in one place.

### As built survey

Answers: What do measurements of the existing state show?
When applicable.

- Heuristic: Record each finding with how precisely it was measured and when it was observed. An undated survey cannot say whether it still holds.
- Boundary: Distinct from Constraints: the survey records what is actually in place; a constraint is a limit imposed on the work. A measured clearance is a finding here; a rule forbidding building into it is a constraint.

### Consent and authority

Answers: What licence, permit, consent or legal basis allows the work?
When applicable.
Applies only when authority is discretionary or notify or approve or statutory. Depends on: Who has to be asked or told before the work goes ahead? (authority)
Kept in another document (Opportunity assessment): link to that document.

## What the conditions mean

- authority is discretionary: Is asking someone first a courtesy you may skip?
- authority is notify: Must someone be told first, with no yes needed?
- authority is approve: Does someone's yes have to come first?
- authority is statutory: Does a law or regulator require a yes first?
