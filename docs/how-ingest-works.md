# How Ingest Works

What `/kb-ingest` does with your folder, when it needs your input, and how to read the results.

## Before You Start

Markdown and plain text work best. Other formats are listed and flagged so you know which material needs attention. Your folder can contain mixed dates, overlapping topics, and unfinished notes.

The source folder remains unchanged. Outputs go into a sibling folder named `<folder>-spec/`.

## The Eight Steps

### 1. Choose the Folder

Provide the source folder. The skill reviews the material before proposing what subject or work the definitions should cover.

### 2. Review the Survey

The skill reports files, dates, and formats before reading in depth. It flags documents using three labels:

- **Contradicted:** another, newer source disputes the content.
- **Unconfirmed:** the content is old enough to need review, but nothing found disputes it.
- **Confirmed:** you have confirmed that the content still holds.

Age alone does not establish that information is wrong. The skill groups questions so you can review the uncertainties together.

### 3. Confirm the Definitions

The skill proposes whether to adopt the product-development starter, adapt it, or develop definitions for the material. It considers the work's purpose, audience, scale, and requirements.

It may use `/kb-uncover-question` to clarify missing questions or `/kb-evolve` to change document types. You review the survey and proposed approach before answers are filed.

### 4. Map Answers and Resolve Conflicts

Each relevant section is mapped to a declared question. The skill keeps track of who supplied an answer and when.

When files provide competing answers, it presents the claims and their sources for your review. A newer file does not automatically replace an older one.

Your decision and reasoning go into `ingest-log.md`. If you leave a conflict unresolved, it remains marked **contested**.

### 5. Review Material That Does Not Fit

Content that answers no declared question is flagged rather than assigned to an approximate match.

Repeated gaps around one topic may indicate that the definitions need extending. Other material may simply fall outside the scope. The skill explains the distinction and can offer `/kb-evolve`.

### 6. Write the Outputs

The sibling folder contains:

- the adopted or adapted definitions;
- companion guidance;
- `answers.yaml`, containing sourced answers and gaps;
- `ingest-log.md`, recording decisions made during the review.

### 7. Check the Definition Files

The bundled checker validates the definition and guidance files. Failures are corrected or reported before the final coverage report.

The checker does not yet validate `answers.yaml` or the ingest log. Review those outputs for accuracy.

### 8. Review Coverage

The report lists unresolved conflicts first, followed by mapped content, potentially outdated content, material that did not fit, and unanswered questions.

## Reading the Coverage Report

| Class | What it means | What to do |
| --- | --- | --- |
| contested | Competing answers remain unresolved. | Decide which applies, or leave the disagreement recorded. |
| mapped | Content was assigned to a declared question. | Spot-check the answer and source. |
| stale | Content is contradicted or needs confirmation. | Confirm, revise, or retire it. |
| refused | Content answers no declared question. | Accept that it is outside scope, or review whether a definition is missing. |
| gap | A required question has no answer. | Supply an answer, or record why it remains unanswered. |

Unresolved conflicts appear first so you can see where the material does not yet provide an agreed answer.
