# Design Notes

Why the protocol uses questions to identify knowledge, separates guidance from requirements, and gives definitions stable codes.

## Identity by Question

Headings alone do not tell you whether two sections describe the same knowledge. Different documents can use different labels for the same question, or use the same label for different questions.

Knowledge Bus identifies each element by the question its content answers. This gives authors a way to check for overlap and gives receivers a basis for matching knowledge across different sets of definitions.

The research below informs that choice; it does not establish that identifying equivalent questions is a solved problem.

Related research:

- **Collingwood (1939)** — the logic of question and answer: a proposition's meaning and truth are relative to the question it answers; knowledge stripped of its question is unintelligible. *An Autobiography*, ch. V; *An Essay on Metaphysics* (1940).
- **Hamblin (1958)** — knowing what counts as an answer is equivalent to knowing the question; the formal converse of identity-by-question, and the foundation of modern question semantics. "Questions," *Australasian Journal of Philosophy* 36(3).
- **Grüninger & Fox (1995)** — competency questions in ontology engineering: a knowledge artifact is specified and judged by the questions it can answer, built for interchange between parties with disjoint vocabularies. IJCAI-95 Workshop on Basic Ontological Issues in Knowledge Sharing.

Bromberger (1992), *On What We Know We Don't Know*, also examines questions and ignorance. Roberts (1996/2012), *Semantics and Pragmatics* 5(6), examines how questions under discussion organize discourse.

These references have limits. The use of Collingwood concerns the relationship between questions and answers, not his broader criticism of propositional logic. Hamblin's account of exhaustive, exclusive answers is contested; the protocol does not rely on that claim. Bromberger's treatment also leaves the identification of questions unresolved.

## Separate Definitions and Guidance

Requirements and writing advice serve different purposes. If they share one undifferentiated list, readers cannot easily tell which statements determine document structure and which help them exercise judgment.

Knowledge Bus puts declarations and composition rules in the universe file. Guidance carries advice, its sources, and the reasoning behind those rules. A universe remains valid without guidance, and departing from advice does not itself violate the protocol.

For example, a requirement to include decision criteria belongs in the document definition. Advice on explaining those criteria belongs in guidance.

Research on context informs this design, particularly the distinction between knowledge that helps people understand a situation and knowledge they draw on to act.

Related research:

- **Pomerol & Brézillon (1999)** distinguish knowledge relevant to a situation from the portion organized and used to address the current problem. That distinction changes as the problem develops. "Dynamics between contextual knowledge and proceduralized context," CONTEXT-99, LNAI 1688.
- **Bazire & Brézillon (2005)** compare definitions of context across disciplines and propose a working model that relates context to the person, task, and situation. "Understanding Context Before Using It," CONTEXT 2005, LNCS 3554.

These studies concern how knowledge is used, not whether following it is mandatory. Knowledge Bus makes that separate distinction explicit: requirements determine whether an artifact meets its definition; guidance supports judgment without imposing additional requirements.

The split also lets advice evolve without making every change a structural requirement. A new source can improve guidance without changing the question being answered. If new evidence does change a requirement or relationship, the universe must be updated too.

## Stable Codes

Readable ids and question wording can change as definitions improve. Tools need a reference that survives editorial changes to the same definition.

Each element, artifact type, frame, and factor therefore receives a stable five-character code. A code is never reused or reassigned. It does not establish equivalence between universes; that still depends on the question.

The alphabet omits `i`, `l`, `o`, and `u` to avoid codes that parsers could interpret as booleans, nulls, or numbers.

Alternatives considered:

- **Readable ids:** useful to people, but changing an id would also change the stable reference.
- **Sequential numbers:** can suggest an order that the definitions do not have.
- **UUIDs:** provide broader uniqueness than needed for codes scoped to one universe.

Codes solve reference stability. They do not remove the need to review whether an edited definition still means the same thing.
