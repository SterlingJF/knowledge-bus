# System context diagram

Document type in the Product development universe spec (product-development 0.9).

- Its shape is set by an outside authority: C4 level 1
- Helps you: find what the system is responsible for and which outside people and systems it works with
- Who uses it: anyone new to the system
- When it is used: when first working with the system
- No document needed when time-separation is none and reversibility is reversible. Depends on: Who has to reconstruct this reasoning without the author present? (time-separation); Can this step be undone, and at what cost? (reversibility)

## How to write it well

- Heuristic: Record only the flows that cross the system's boundary; flows between the system's own parts belong in the Architecture Overview.
- Convention: Show people and external systems at C4 level 1. Use the Architecture Overview for internal containers and their interactions at level 2. C4 component-level detail is a further level.

## Sections

### System boundary and context

Answers: What is the system itself responsible for?
Required.

- Convention: C4 level 1: the system, its users, and the external systems it exchanges with.
- Heuristic: The boundary is a security and ownership decision, not just a drawing choice.

### Data flows and integrations

Answers: What data moves where?
Required.

- Heuristic: Flows name the contract — API, event, file — and the contract's owner.
- Heuristic, when authority is approve or statutory: In regulated and privacy contexts flows are compliance surface. Annotate data classification — personally identifiable information, protected health information — where it applies. Depends on: Who has to be asked or told before the work goes ahead? (authority)

## What the conditions mean

- authority is approve: Does someone's yes have to come first?
- authority is statutory: Does a law or regulator require a yes first?
