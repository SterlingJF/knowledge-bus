# Lean canvas

Document type in the Product development universe spec (product-development 0.9).

- Its shape is set by an outside authority: Lean Canvas (Maurya)
- Helps you: choose which assumption in a new venture's business model to test next
- Who uses it: whoever is starting the venture
- When it is used: before the venture has shown that customers will pay for it
- Not used when uptake is given or chosen. Depends on: How do people come to take up the offering? (uptake)
- No document needed when time-separation is none and reversibility is reversible. Depends on: Who has to reconstruct this reasoning without the author present? (time-separation); Can this step be undone, and at what cost? (reversibility)

## How to write it well

- Convention: A one-page adaptation of the Business Model Canvas for ventures under extreme uncertainty.
- Convention: Fill in each of these blocks: problem, customer segments, unique value proposition, solution, channels, revenue streams, cost structure, key metrics and unfair advantage.
- Heuristic: When a block does not apply, keep it and write in it why it does not apply.

## Sections

### Problem statement

Answers: What problem should the work solve?
Required.

- Heuristic: Name the problem and whose problem it is, with no solution built in.
- Pitfall: Solution-shaped problems pre-commit the answer.
- Heuristic: One quantified pain beats five asserted ones.

### Customer segments

Answers: Exactly which groups is the offering for?
Required.

- Pitfall: Segment by shared job or behaviour, not demographics alone — demographic-only segments are the classic false-precision trap.
- Pitfall: In B2B the buyer, the user and the payer differ; healthtech's patient/provider/payer triangle makes single-segment framing misleading.
- Pitfall, when maturity is unproven: One beachhead segment. A long segment list this early signals unvalidated focus. Depends on: How settled is the bet this work rests on? (maturity)
- Boundary: Distinct from Canonical Model: a segment here is a group of people the offering is for; a category there is one the system uses to sort its own data, such as account types. Ask whether it is about whom we serve or how the system files things.

### Value proposition

Answers: Why would a segment choose the offering over its alternatives?
Required.
Applies only when uptake is chosen or bought. Depends on: How do people come to take up the offering? (uptake)

- Heuristic: Always relative to the segment's current alternative, including doing nothing.
- Pitfall: One per segment. A single all-segment value proposition usually means the segments were never really split.
- Heuristic, when uptake is bought: Quantify in time, cost or risk. Where there is no market, qualitative is fine — but still name the alternative. Depends on: How do people come to take up the offering? (uptake)

### Solution overview

Answers: What is the intended solution, in outline?
Required.

- Boundary: Distinct from Components & Responsibilities and the other architecture elements. Ask whether a line says what the solution does and how people use it, or how it technically holds together; the second belongs there.
- Convention: A Lean Canvas keeps this deliberately thin — top features only; a design document gives it a full section.
- Heuristic: State what the solution deliberately does not do. Pairs with Scope (In / Out).

### Channels

Answers: How does the offering reach each segment?
Required.

- Convention: Cover every stage at which the offering meets the segment: how they hear of it, weigh it up, buy it, receive it and get support afterwards.
- Heuristic: Product-led versus sales-led growth is at bottom a channels choice. Regulated and enterprise markets often have imposed channels — brokers, distributors, procurement — that dominate the design.
- Heuristic: For physical goods, delivery and service channels drive cost structure. Link the two.

### Revenue streams

Answers: How does the offering earn money?
Required.
Applies only when uptake is bought. Depends on: How do people come to take up the offering? (uptake)

- Convention: Core to the Business Model Canvas and the Lean Canvas. Strategy canvases often omit it, treating monetisation as downstream of positioning.
- Heuristic: In regulated industries this is often fixed by regulation or reimbursement codes. Record it as a constraint, not a choice.
- Heuristic, when maturity is unproven: A hypothesis to test, not a plan. Deep tech and hardware commonly defer it until technical maturity. Depends on: How settled is the bet this work rests on? (maturity)

### Cost structure

Answers: What mainly determines the cost of providing the offering?
Required.

- Heuristic: The dominant driver is the insight, not the line items — services and construction run on per-project labour, software on headcount, hardware on cost of goods sold and capex.
- Heuristic: Distinguish fixed from variable and note what scales with growth. The growth mechanism can invert the shape.
- Heuristic, when uptake is given: Still applies at personal and household scale, where time is the usual dominant cost. Depends on: How do people come to take up the offering? (uptake)

### Input metrics

Answers: Which measures within our control predict the value people get from the offering?
Required.

- Convention: Leading and team-influenceable, or it is an output someone mislabelled.
- Heuristic: Few and causal beats many and correlated.
- Convention: Where a team already reports KPIs, sort them before reusing any here. Parmenter separates result indicators, which sum up the input of more than one team, from performance indicators, which can be tied to one team; only the second kind can serve as input metrics.

### Unfair advantage

Answers: What advantage of ours is hard for others to copy or buy?
Required.
Applies only when uptake is chosen or bought. Depends on: How do people come to take up the offering? (uptake)

- Heuristic: Test each candidate against the question: could a rival copy it or buy it? Forms that often pass are network effects, proprietary data, switching costs, regulatory protection, patents and brand.
- Pitfall: The Lean Canvas's hardest block — 'first mover' and 'passion' do not qualify.
- Empty, when maturity is unproven: Early on there is usually none yet. Write 'none yet' when you looked and found nothing, so a reader can tell it apart from one nobody has considered. Depends on: How settled is the bet this work rests on? (maturity)

## What the conditions mean

- uptake is given: Does it arrive whether or not they'd choose it?
- uptake is chosen: Do they take it up only by deciding to, with nothing to pay?
- uptake is bought: Is paying how they take it up?
