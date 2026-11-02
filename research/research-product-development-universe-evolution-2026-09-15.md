# Product Development Universe Evolution

Date: 2026-09-15

## Why this slice

The product-development universe already connects familiar artifacts through shared questions and context-sensitive composition. Three ambiguities remain: strategy canvases imply ownership of a shared metric, assumption guidance applies risk scoring indiscriminately, and decision guidance treats missing evidence as staleness. Correcting these ambiguities makes the existing universe more dependable to adopt without adding concepts or prescribing more paperwork.

## Primary-source comparison

### Amplitude North Star Framework

[Amplitude's North Star framework](https://amplitude.com/books/north-star/about-the-north-star-framework) connects a measure of delivered value with the input metrics that influence it, giving strategy and product work a shared measurement focus.

- **Borrow:** Connect strategic direction to its measurement framework.
- **Adapt:** Success Metrics owns the North Star Metric definition; Product Strategy Canvas and Startup Canvas reference the definition as core content.
- **Skip:** Treating inclusion in several artifacts as separate ownership. This ownership arrangement is a universe design choice, not an Amplitude prescription.

### Rust RFCs

The [Rust RFC template](https://github.com/rust-lang/rfcs/blob/master/0000-template.md) distinguishes drawbacks, rationale, alternatives, and unresolved questions rather than treating every concern as the same kind of uncertainty.

- **Borrow:** Preserve distinctions between concerns that require different reasoning.
- **Adapt:** Document assumptions with their verification methods, and risks with their potential consequences and responses.
- **Skip:** Applying impact-times-likelihood scoring to every assumption. The revised guidance is a local heuristic, not a rule prescribed by the RFC template.

### Nygard and Azure Decision Records

[Nygard](https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions) explains the importance of understanding a decision's context before accepting or reversing it. [Azure](https://learn.microsoft.com/en-us/azure/well-architected/architect-role/architecture-decision-record) preserves accepted records and links subsequent decisions that supersede them.

- **Borrow:** Retain the reasoning behind a commitment when circumstances change.
- **Adapt:** Reassess a decision when a reconsideration trigger occurs or supporting circumstances change. Identify missing evidence when a trigger cannot be evaluated.
- **Skip:** Treating an unevaluable trigger as proof that a decision is stale or invalid.

## Chosen direction: Clarify ownership and judgment

### North Star ownership

Product Strategy Canvas and Startup Canvas retain the North Star Metric as core content but explicitly reference its definition. Success Metrics retains ownership.

Required membership and ownership serve different purposes: the canvases need the metric to express strategic direction; Success Metrics defines the metric alongside its input and guardrail metrics.

The metric remains required when applicable. Its question, identity, gate, and cardinality remain unchanged.

### Assumptions and risks

Risks and Assumptions retains its existing element definition. Its guidance distinguishes the information needed to document assumptions and risks:

- An assumption names a premise the work depends on and a method for checking that premise.
- A risk names a potential event or circumstance, its significance, and the response.

An assumption may expose a risk, but numerical risk scoring is not appropriate for every assumption. Authors may use individual files, tables, or another suitable form; the storage arrangement does not determine the knowledge's identity.

### Decision reassessment

A decision warrants reassessment when a reconsideration trigger occurs or its supporting circumstances change.

An unevaluable trigger identifies an evidence gap, not a reason for automatic reversal. Reassessment may confirm the decision or justify changing it. A superseding record preserves the original reasoning when the decision changes.

## Borrow / later / skip

### Borrow now

- Reference shared knowledge without weakening required membership.
- Distinguish assumption verification from risk assessment.
- Reassess decisions without equating uncertainty with invalidity.
- Preserve historical reasoning when a decision changes.

### Later, after evidence

- Split Risks and Assumptions if concrete uses establish a need for independently defined elements.
- Add context-specific assessment or review requirements where the relevant practice warrants them.

Neither extension is necessary to correct the present guidance.

### Deliberately skip

- Making the North Star Metric situational to solve an ownership problem.
- Requiring a register, separate files, or numerical scoring for assumptions.
- Limiting decision reassessment to predefined triggers.
- Automatically invalidating decisions when evidence is unavailable.
- Changing element identities or protocol behavior to express corrections already supported by the existing model.

## Stability contract

1. The North Star Metric remains core in both canvases and Success Metrics.
2. Both canvases reference the metric; Success Metrics owns its definition.
3. No element question, stable code, cardinality, or gate changes.
4. Assumption and decision advice remains guidance, not an additional validation requirement.
5. File and table arrangements do not determine knowledge identity.
6. Reassessment does not imply reversal; supersession preserves the original record.

## Acceptance evidence

The ownership test checks that the North Star Metric appears exactly once as unconditional core membership in each relevant artifact, with reference mode in both canvases and ownership mode in Success Metrics.

The revised guidance preserves two distinctions obscured by the previous wording:

- Assumption verification does not require numerical risk scoring.
- A decision may require further evidence or reassessment without already being invalid.

The automated check establishes composition consistency. Semantic review supports the guidance distinctions; structural tests do not establish their suitability for every context.
