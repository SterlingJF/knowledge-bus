import test from 'node:test';
import assert from 'node:assert/strict';
import { artifactEdges, collapseCardPairs } from '@/src/lib/rollup';
import type { CompositionEntry, DisplayEdge } from '@/src/lib/model';

const composition: CompositionEntry[] = [
  { from: 'A', to: 'x', strength: 'core', path: 'a' },
  { from: 'B', to: 'x', strength: 'situational', path: 'b' },
  { from: 'B', to: 'y', strength: 'core', path: 'c' },
];

test('shared elements join artifacts, keeping the weaker membership', () => {
  const shared = artifactEdges([], composition, ['A', 'B'], 'composition');
  assert.equal(shared.length, 1);
  assert.equal(shared[0].strength, 'situational');
  assert.equal(shared[0].ordered, false);
  assert.equal(shared[0].label, 'Shared element');
});

test('element relations project onto artifacts and record their path', () => {
  const projected = artifactEdges(
    [{ from: 'x', to: 'y', kind: 'feeds', ordered: true, path: 'r', label: 'feeds' } as DisplayEdge],
    composition,
    ['A', 'B'],
    'relations',
  );
  assert.equal(projected.length, 1);
  assert.equal(projected[0].from, 'A');
  assert.equal(projected[0].to, 'B');
  assert.equal(projected[0].rolled, true);
  assert.equal(projected[0].sources![0].composition.length, 2);
  assert.equal(projected[0].label, 'feeds');
  const direct = artifactEdges(
    [{ from: 'A', to: 'B', path: 'd', label: 'feeds', ordered: true } as DisplayEdge],
    composition,
    ['A', 'B'],
    'relations',
  );
  assert.equal(direct[0].rolled, false);
});

test('a card pair collapses to one edge with mixed direction and strength', () => {
  const projected = artifactEdges(
    [{ from: 'x', to: 'y', kind: 'feeds', ordered: true, path: 'r', label: 'feeds' } as DisplayEdge],
    composition,
    ['A', 'B'],
    'relations',
  );
  const combined = collapseCardPairs([...projected, { ...projected[0], from: 'B', to: 'A', label: 'requires', strength: 'situational' }]);
  assert.equal(combined.length, 1);
  assert.equal(combined[0].members!.length, 2);
  assert.equal(combined[0].sources!.length, 2);
  assert.equal(combined[0].ordered, false);
  assert.equal(combined[0].strength, 'mixed');
  assert.equal(combined[0].label, 'feeds · requires');
});

test('rollup never produces a self-loop on a card', () => {
  const self = artifactEdges(
    [{ from: 'x', to: 'x', kind: 'feeds', ordered: true, path: 'r', label: 'feeds' } as DisplayEdge],
    composition,
    ['A', 'B'],
    'relations',
  );
  assert.ok(self.every((edge) => edge.from !== edge.to));
  assert.ok(self.every((edge) => ['A', 'B'].includes(edge.from) && ['A', 'B'].includes(edge.to)));
});
