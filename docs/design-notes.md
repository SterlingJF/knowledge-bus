# Design notes

## Identity by question

An element is the question it answers, not a label.
Two specs sharing no vocabulary can still exchange answers keyed by question.

The most useful person in a meeting is not necessarily the one holding the most information, but rather it's the one
who asks the question that points everyone at the right work. A knowledge base should be built out
of those questions, not out of the information.

Corroborating work:

- **Collingwood (1939)** — the logic of question and answer: a proposition's meaning and truth are relative to the question it answers; knowledge stripped of its question is unintelligible. *An Autobiography*, ch. V; *An Essay on Metaphysics* (1940). The anchor citation.
- **Hamblin (1958)** — knowing what counts as an answer is equivalent to knowing the question; the formal converse of identity-by-question, and the foundation of modern question semantics. "Questions," *Australasian Journal of Philosophy* 36(3).
- **Grüninger & Fox (1995)** — competency questions in ontology engineering: a knowledge artifact is specified and judged by the questions it can answer, built for interchange between parties with disjoint vocabularies. IJCAI-95 Workshop on Basic Ontological Issues in Knowledge Sharing. The closest design precedent.

Secondary: Bromberger (1992), *On What We Know We Don't Know* — ignorance too is question-shaped;
Roberts (1996/2012), *Semantics and Pragmatics* 5(6) — discourse already exchanges information
keyed to questions under discussion.

<!-- slot: cautions, verified — fold into prose or leave as authoring notes:
- Frame Collingwood as alignment with the correlativity thesis, not endorsement of his attack on
  propositional logic (regarded as overreach).
- Hamblin: cite the 1958 AJP paper, not 1973; postulate 3 (exhaustive, exclusive answers) is
  contested — don't lean on it.
- Bromberger disputes Hamblin on answerhood and calls question-individuation unsolved; one honest
  sentence noting the identity criterion is a live research question strengthens the doc. -->

## The spec/guidance split

A value belongs in the spec because something reads it.
Guidance constrains authoring without intervening in validation.

The split follows Brézillon's model of context: context is what constrains an activity without
intervening in it explicitly. The spec is what the mechanism reads — knowledge mobilized into
composition and validation. Guidance is contextual: it shapes how a question gets answered well,
and on whose authority, without the checker ever requiring it. The filing diagnostic: does
something read this, or does it only inform the author?

Corroborating work:

- **Pomerol & Brézillon (1999)** — contextual knowledge versus proceduralized context: the same
  material splits by whether it is mobilized into the decision or merely conditions it.
  "Dynamics between contextual knowledge and proceduralized context," CONTEXT-99, LNAI 1688.
- **Bazire & Brézillon (2005)** — 150 definitions of context yield no consensus; adopt a
  stipulated, task-indexed model rather than waiting for a general one. "Understanding Context
  Before Using It," CONTEXT 2005, LNCS 3554.

The deeper reason is change rate. How to answer a question well — the literature, conventions,
and connotations underneath it — evolves rapidly and is unbounded; a search can surface new
material the same day. The questions themselves are more stable, more structured, and easier to
evaluate for cohesion. The split keeps the stable layer enforceable while the unbounded layer
stays free to move.

## Stable short codes

Codes are 5 characters from an alphabet omitting i, l, o, u, so no code parses as a bool, null, or number.
Codes survive renames; questions do not.

Three alternatives were refused. Ids as the stable handle: a question is distinct within its
spec's scope but shifts as the spec matures — inherently not character-stable. Sequential markers,
issue-tracker style: elements and artifacts present in parallel and nonlinear ways; an ordering
implies a sequence that doesn't exist. UUIDs: uniqueness is only ever needed within one spec's
scope, so the length buys nothing.
