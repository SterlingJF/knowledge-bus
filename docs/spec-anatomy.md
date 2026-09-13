# Spec Anatomy

A definition file describes the knowledge for a subject or area of work. The protocol calls this a **universe**. Companion guidance explains how to answer its questions well.

User definitions live in `.knowledge-bus/` inside the folder they describe. See [Knowledge Bus Directory](knowledge-bus-directory.md) for directory selection rules.

## Definition and Guidance Files

The included example has two files:

- [universe.kbp.yaml](../universes/product-development/universe.kbp.yaml): questions, document purposes, composition rules, and relationships.
- [type-guidance.kbp.yaml](../universes/product-development/type-guidance.kbp.yaml): advice and sources attached to those definitions.

Guidance is optional. The universe must remain valid without it. When guidance is supplied, the checker validates its structure and references, not whether its advice is correct.

## Field Reference

| Key | Purpose |
| --- | --- |
| `universe` | Identifies the definition set, its version, the protocol version it follows, and its ordering frame. |
| `elements` | Defines knowledge units by the questions their contents answer. |
| `artifacts` | Defines document types by the action or decision they enable for someone, and lists their contents. |
| `frames` | Defines context used to organize or select content. A frame can make content required, exclude it, or determine that no document is needed. |
| `factors` | Declares context that applications can use, without giving it control over document composition in the universe. Guidance can use a factor to select advice. |
| `relation_kinds`, `relations` | Names the kinds of connections and the definitions they connect, such as dependencies or distinctions. |
| `statuses` | Declares the statuses an assertion can carry. |
| `empty_composition` | States the context in which no document is needed. |
| `instances` | Holds asserted answers with their party, status, time, and other instance details. |

For example, a frame could make a section required in one situation and unnecessary in another. A factor could select relevant writing advice without changing the required sections.

The guidance file has a header (`guidance`), declared advice kinds (`guidance_kinds`), a source registry (`sources`), and entries attached to `elements`, `artifacts`, or `factors`.

## Defining Elements and Artifacts

An element is identified by its question. Two candidate sections answering the same question refer to the same element, regardless of their headings.

A document type is identified by the action or decision it enables and the actor who needs it. Its required contents are the information that actor needs to proceed. Other contents depend on the situation.

Before adding a definition, compare it with existing questions and document purposes. You may need to clarify an existing definition rather than add another. `/kb-uncover-question` and `/kb-evolve` support that review.

## Stable Codes

Elements, artifact types, frames, and factors each carry a five-character code. The first character identifies the kind; the rest is an opaque handle. Codes do not encode meaning or order.

People and agents use the readable id and question. Tools use the code to keep a stable reference when the same definition is renamed. Preserve its code and update references that use the changed id. Never reuse or reassign a retired code.

From the repository root:

```bash
uv run kbp --mint element 3 path/to/project/.knowledge-bus/
```

Replace the example path with your `.knowledge-bus/` directory. This generates three element codes checked against its definitions. Use `artifact`, `frame`, or `factor` for other kinds. See [Adapting the Example](adapting-the-example.md) for use with your own definitions.

## Requirements vs. Recommendations

Put declarations and structural rules in the universe file. Put recommendations and their reasoning in guidance.

For example, a rule requiring a section belongs in the document's composition. Advice on writing that section clearly belongs in guidance.

In the included guidance, conventions require registered sources. Other kinds, such as pitfalls and heuristics, may be marked `asserted`. Each guidance document declares which of its advice kinds require sources.

## Validation Scope

The checker validates supported structural rules in universe and guidance files. It does not yet provide a complete instance-validation path or validate ingestion's separate `answers.yaml` format.

See [Validation](validation.md) for commands and limitations.
