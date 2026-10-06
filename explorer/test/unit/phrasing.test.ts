import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { relationPhrasing, compositionDetails, cardinalityCopy, cardinalityDetail, kindNoun, limitsCopy } from '@/src/lib/phrasing';
import { type Connection, type ExplorerModel, universeTerms, validateModel } from '@/src/lib/model';

const edge = { from: 'constraints', to: 'authority', kind: 'custom' } as Connection;
const directional = { id: 'custom', ordered: true, phrasing: { forward: 'Context from', reverse: 'Context for' } };

test('the phrase follows the displayed subject', () => {
  assert.deepEqual(relationPhrasing(edge, directional, 'constraints'), {
    subject: 'constraints',
    object: 'authority',
    phrase: 'Context from',
  });
  assert.deepEqual(relationPhrasing(edge, directional, 'authority'), {
    subject: 'authority',
    object: 'constraints',
    phrase: 'Context for',
  });
});

test('an unordered phrase reads the same from either endpoint', () => {
  const kind = { id: 'peer', ordered: false, phrasing: { forward: 'Alongside' } };
  assert.equal(relationPhrasing(edge, kind, 'authority')!.phrase, 'Alongside');
  assert.equal(relationPhrasing(edge, kind, 'constraints')!.phrase, 'Alongside');
});

test('a missing inverse is never invented, and authored text is never transformed', () => {
  assert.equal(relationPhrasing(edge, { id: 'custom', ordered: true }, 'authority'), null);
  assert.equal(
    relationPhrasing(
      edge,
      { id: 'c', ordered: true, phrasing: { forward: 'Context <from> & beyond', reverse: 'Context for' } },
      'constraints',
    )!.phrase,
    'Context <from> & beyond',
  );
});

test('a subject that is not an endpoint cannot silently reverse an edge', () => {
  assert.throws(() => relationPhrasing(edge, directional, 'unrelated'), /endpoint/);
});

test('composition copy states requirement, condition and fallback', () => {
  assert.deepEqual(compositionDetails({ strength: 'core', when: { authority: ['approve'] } }), {
    requirement: 'Required when applicable',
    conditionTitle: 'Required when',
    fallback: 'Otherwise optional, if the element applies.',
  });
  assert.deepEqual(compositionDetails({ strength: 'situational', when: { authority: ['approve'] } }), {
    requirement: 'When applicable',
    conditionTitle: 'Available when',
    fallback: null,
  });
  for (const strength of ['core', 'situational'])
    for (const when of [undefined, {}])
      assert.deepEqual(compositionDetails({ strength, when }), {
        requirement: strength === 'core' ? 'Required' : 'When applicable',
        conditionTitle: null,
        fallback: null,
      });
});

test('membership mode and cardinality read as audience copy', () => {
  assert.equal(cardinalityCopy('singleton'), 'One answer');
  assert.equal(cardinalityCopy('per-segment'), 'One per segment');
  assert.equal(cardinalityDetail('singleton'), 'Not divided into separate answers');
  assert.equal(cardinalityDetail(undefined), 'Not specified');
});

const fixture = validateModel(JSON.parse(readFileSync(new URL('../fixtures/product-development.json', import.meta.url), 'utf8')));

test('a frame value reads as a value, whatever the model calls its kind', () => {
  assert.equal(kindNoun('option'), 'value');
  for (const kind of ['artifact', 'element', 'frame', 'factor']) assert.equal(kindNoun(kind), kind);
});

test('the universe terms reach the reader verbatim, and a universe declaring none has none', () => {
  assert.deepEqual(universeTerms(fixture), fixture.universe.terms);
  const untermed = structuredClone(fixture) as ExplorerModel;
  delete (untermed.universe as { terms?: unknown }).terms;
  assert.deepEqual(universeTerms(validateModel(untermed)), []);
  const terms = [
    { term: 'Offering', means: 'Whatever the work puts in front of a recipient.' },
    { term: 'Recipient', means: 'Whoever receives the offering.' },
  ];
  const termed = structuredClone(fixture) as ExplorerModel;
  termed.universe.terms = terms;
  assert.deepEqual(universeTerms(validateModel(termed)), terms);
});

test('the limits line says the explorer shows declarations and evaluates nothing, as one sentence', () => {
  assert.equal(fixture.evaluation.status, 'unresolved');
  const line = limitsCopy(fixture);
  assert.ok(line, 'an unresolved model states its limits');
  assert.match(line!, /declares/);
  assert.match(line!, /does not evaluate/);
  assert.equal(line!.split(/[.!?](\s|$)/).filter((part) => part && part.trim()).length, 1);
});
