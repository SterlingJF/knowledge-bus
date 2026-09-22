import test from 'node:test';
import assert from 'node:assert/strict';
import { relationPhrasing, compositionDetails, cardinalityCopy, cardinalityDetail } from '@/src/lib/phrasing';
import type { Connection } from '@/src/lib/model';

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
