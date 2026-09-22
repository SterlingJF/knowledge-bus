---
name: kb-uncover-question
description: Clarify a question a Knowledge Bus universe should declare, testing its purpose and overlap with existing questions.
---

# Uncover a Question

**Purpose — arrive at a question worth declaring: one job, no overlap with any declared question, stated tersely enough to key answers on.**

## Knowledge Bus Directory

Follow [Knowledge Bus Directory](references/knowledge-bus-directory.md). Use an explicit target when supplied; otherwise resolve the nearest `.knowledge-bus/` from the user's working directory. Inspect existing files before proposing changes and preserve existing definitions and decision history. Do not combine definitions from different Knowledge Bus directories. Write only inside the selected `.knowledge-bus/`; leave source files untouched. If definitions are absent, ask the user to select or explicitly create a set rather than inventing one silently.

## Standing constraints

- **Questions are earned.** Reason through everything held before asking; a question the material can answer is never put to the interviewee.
- **Batches, not a stream.** Ask in small batches; reflect on the answers before the next. One or two follow-up batches usually land in the same sitting.
- **One question, one job.** A candidate with two conjunctions is two candidates.
- **A near-duplicate is refused, not merged silently.**
- **The interviewer supplies pressure, not answers.**
- **Interview in the interviewee's language.** Format vocabulary never appears in a question; the tests run in the reasoning, not in the asking.

## The loop

Repeat only while a follow-up can resolve stated uncertainty. Stop when the tests settle the candidate or when resolution requires missing evidence or another person.

- **1. Reason first.** Re-read everything held — the material, prior answers, every declared question. Draft what the next batch must uncover; discard whatever the record already settles.

- **2. Ask one batch.** A few pointed questions on the enablement — what does answering this let someone do? — never on wording. Wording anchors the interviewee; enablement doesn't.

- **3. Reflect and test.** Against the answers, run the tests: an enablement a declared question already covers is a collision — rule *sharpen existing / new / refused*; two jobs is a split; a candidate with no honest empty answer is not load-bearing.

- **4. Follow up or stop.** Ask another batch only when it can resolve stated ambiguity. A round that changes nothing ends the loop; unresolved uncertainty stays unresolved.

- **5. Declare.** Freeze the wording last. Mint a code using [Checker for Agent Workflows](references/agent-runtime.md); record every refusal with its reason.
