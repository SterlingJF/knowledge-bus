# Adapting the Example

Start with the included product-development definitions, keep what fits your work, and change what does not. You can do this before writing any documents.

## What the Starter Contains

The starter defines 58 questions across 19 document types, with 45 relationships and guidance citing 51 registered sources. It covers documents such as strategy canvases, decision records, and design documents.

Its questions can be useful at different scales, from a personal project to a company. Review the definitions against your own purpose, audience, and requirements before adopting them.

## Choose a Starting Point

| Approach | When it fits |
| --- | --- |
| Adopt | The questions, document purposes, and requirements fit your work. |
| Trim | The definitions fit, but your work needs only part of them. |
| Extend | The structure fits, but a question, document type, or relationship is missing. |
| Develop your own | Your subject or work needs substantially different questions and document purposes. |

For example, a solo project may need a decision record without the full set of product-planning documents. A research project may need definitions for evidence and methods that the starter does not cover.

When trimming, check references between definitions. Removing one may affect the document types, relationships, or guidance that use it.

## Add or Review a Document Type

Use [`/kb-evolve`](../skills/kb-evolve/SKILL.md) when a document type is missing or when you want to examine an existing type before relying on it.

The skill helps establish:

- what decision or action the document supports, and for whom;
- which questions its contents answer;
- whether those questions or document purposes already exist;
- which information is required and which depends on the situation;
- which relationships and guidance need to change.

It researches the proposed type, checks the resulting files, and records the changes and their reasons, including proposed additions it rejected.

Use `/kb-uncover-question` when you need help clarifying a question or distinguishing it from existing ones.

Guided creation of an entire new set of definitions remains planned work. You can author one directly using [Spec Anatomy](spec-anatomy.md) and check it with the current tools.

## Apply Definitions to Existing Notes

If you already have notes, `/kb-ingest` reviews them and proposes whether to adopt, adapt, or develop definitions for that material. It asks you to confirm the proposed approach.

Content that does not fit may indicate a missing definition or material outside the chosen scope. Review the reason before changing the structure.

See [How Ingest Works](how-ingest-works.md).

## Assign Stable Codes

Each new element, document type, frame, or factor needs a code. From the repository root, generate three element codes with:

```bash
just mint element 3
```

Use `artifact`, `frame`, or `factor` for the other declaration kinds. Check generated codes against your own definitions if they are outside the repository's default search location.

Keep the code when renaming the same definition. Never reuse or reassign a retired code. Update any references that use the renamed id.

## Add Guidance and Check the Result

In the included guidance, a `convention` must cite a registered source. Other kinds can use `asserted` to identify advice supplied without an external citation. Preserve sourcing limitations, such as abstract-only access or a rescinded source, in the citation.

Run the checker with both the definition and guidance files after editing. A passing result checks supported structural rules; you still need to review whether the definitions and advice fit your work.

See [Validation](validation.md) for commands and coverage.
