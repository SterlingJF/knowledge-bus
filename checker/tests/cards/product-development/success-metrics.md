# Success metrics

Document type in the Product development universe spec (product-development 0.9).

- Also called: North Star framework
- Helps you: decide which numbers to improve next and which to keep where they are
- Who uses it: whoever runs the offering day to day
- When it is used: at each regular review of the offering
- No document needed when time-separation is none and reversibility is reversible. Depends on: Who has to reconstruct this reasoning without the author present? (time-separation); Can this step be undone, and at what cost? (reversibility)

## How to write it well

- Convention: The North Star Metric and the input metrics that drive it.

## Sections

### North star metric

Answers: What one measure best shows the value people get from the offering?
Required.

- Convention: Proxies customer value, not company results. Revenue is an outcome, not a North Star.
- Convention: One per space, at any abstraction, tested by real users, needs and strategy — never by the org chart. Distinct metrics only for genuinely distinct divisions and customer bases.
- Convention: A single effort does not get its own North Star. It sets its success criteria on a change in what people do that the effort can influence and that drives the North Star, which Torres calls a product outcome.
- Convention: A North Star tracks customer value within its framework. The One Metric That Matters identifies the current metric to focus on and may change with the business stage or bottleneck; the names are not interchangeable.
- Convention: Represents vision and strategy without being either — a strong metric statement lets a reader recover both at a high level.
- Pitfall: A North Star without input metrics is not actionable.
- Boundary: Success Metrics owns the definition. A strategy canvas records the choice and links back rather than restating it, because copies drift.

### Input metrics

Answers: Which measures within our control predict the value people get from the offering?
Required.

- Convention: Leading and team-influenceable, or it is an output someone mislabelled.
- Heuristic: Few and causal beats many and correlated.
- Convention: Where a team already reports KPIs, sort them before reusing any here. Parmenter separates result indicators, which sum up the input of more than one team, from performance indicators, which can be tied to one team; only the second kind can serve as input metrics.

### Guardrail health metrics

Answers: Which measures must stay within set ranges while we pursue other targets?
Required.

- Heuristic: The counterweight to any target — latency, churn, quality, trust; burnout at personal scale.
- Convention: Guardrails that protect the organisation, such as page-load time or revenue, are largely shared across experiments. Define them once, for the whole organisation, and reuse them in every effort.
- Pitfall: Experimentation-heavy organisations formalise these as launch blockers; everywhere else they stay implicit until an incident. Write them down first.
- Boundary: Distinct from Input Metrics. Ask whether the number should move or hold: an input metric is pushed to move, a guardrail is held within its range. Neither the Business Model Canvas nor the Lean Canvas has a block for guardrails, so keep them in Success Metrics.

### Success criteria

Answers: What observable result counts as success for the work?
When applicable.

- Pitfall: 'Improve X' invites post-hoc rationalisation. Set a threshold and a measurement date.
- Heuristic: Per-initiative acceptance, set before the work, expiring with the effort — unlike metrics that run continuously.
- Heuristic: A product requirements document's launch 'success metrics' and an OKR's key results belong here: each is a threshold with a date, usually on an input metric.
- Heuristic: Point to the shared measures the work must not break instead of copying them, and state in full each threshold this work commits to.
