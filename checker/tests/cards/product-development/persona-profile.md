# Persona profile

Document type in the Product development universe spec (product-development 0.9).

- Also called: persona profile
- Helps you: decide which kind of person, in which circumstance, to design the solution for
- Who uses it: whoever designs the solution or studies the people it is for
- When it is used: before designing the solution
- No document needed when time-separation is none and reversibility is reversible. Depends on: Who has to reconstruct this reasoning without the author present? (time-separation); Can this step be undone, and at what cost? (reversibility)

## Sections

### Jobs to be done

Answers: What is a person trying to achieve?
Required.

- Boundary: Distinct from User / Job Stories: a job holds whatever solution is chosen; a story says what the solution lets a person do. A when / want / so-that line written before any solution exists states a job.
- Convention: Jobs are circumstance-anchored and stable. Solutions churn; jobs do not.
- Convention: The when / want / so-that job-story form captures circumstance better than persona-attached stories.

### Pains and gains

Answers: What frustrations and hoped-for gains does each segment have?
Required.

- Convention: Osterwalder's value-proposition-canvas pairing — pains before, gains after.
- Boundary: Distinct from Problem Statement: this records what each segment finds frustrating and hopes for, many entries drawn from evidence; Problem Statement names the one problem the work chooses to solve.
- Boundary: Distinct from Jobs to Be Done: the job is the progress itself; pains are what gets in the way of making it today, and gains are what would make it better.
- Pitfall: Source from evidence — interviews, support logs — not empathy-map guessing. Rank by severity times frequency or the list flattens.

### Customer segments

Answers: Exactly which groups is the offering for?
Required.

- Pitfall: Segment by shared job or behaviour, not demographics alone — demographic-only segments are the classic false-precision trap.
- Pitfall: In B2B the buyer, the user and the payer differ; healthtech's patient/provider/payer triangle makes single-segment framing misleading.
- Pitfall, when maturity is unproven: One beachhead segment. A long segment list this early signals unvalidated focus. Depends on: How settled is the bet this work rests on? (maturity)
- Boundary: Distinct from Canonical Model: a segment here is a group of people the offering is for; a category there is one the system uses to sort its own data, such as account types. Ask whether it is about whom we serve or how the system files things.

### User job stories

Answers: What should the solution let a person do?
When applicable.

- Convention: A user story (as-a / I-want / so-that) presumes a persona; a job story (when / I-want / so-I-can) presumes a circumstance. Pick one per document; do not mix.
- Heuristic: Acceptance criteria turn a story from a conversation-starter into testable scope.
- Boundary: Distinct from Jobs to Be Done: ask whether the line names what the solution must let a person do. A story does, and acceptance criteria test it; the job behind it stays true whatever is built.

### Channels

Answers: How does the offering reach each segment?
When applicable.

- Convention: Cover every stage at which the offering meets the segment: how they hear of it, weigh it up, buy it, receive it and get support afterwards.
- Heuristic: Product-led versus sales-led growth is at bottom a channels choice. Regulated and enterprise markets often have imposed channels — brokers, distributors, procurement — that dominate the design.
- Heuristic: For physical goods, delivery and service channels drive cost structure. Link the two.
