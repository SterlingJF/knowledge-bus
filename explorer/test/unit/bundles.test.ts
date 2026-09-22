import test from 'node:test';
import assert from 'node:assert/strict';
import { bundleExpandedPairs, bundleFocusCard } from '@/src/lib/bundles';
import type { DisplayEdge } from '@/src/lib/model';

const edge = (from: string, to: string, label: string, path: string, ordered = true): DisplayEdge => ({ from, to, label, path, ordered });
const a = edge('A', 'B', 'feeds', 'a');
const b = edge('B', 'A', 'requires', 'b');
const c = edge('A', 'C', 'feeds', 'c');
const d = edge('D', 'E', 'feeds', 'd');
const e = edge('D', 'E', 'requires', 'e');
const loop = edge('A', 'A', 'feeds', 'loop');
const target: DisplayEdge = { ...edge('A', 'B', 'gate', 'target'), targetPair: ['B', 'C'] };
const source = [a, b, c, d, e, loop, target];

test('two edges to one neighbour bundle, and nothing else moves', () => {
  const result = bundleExpandedPairs(source, 'A');
  assert.equal(result.length, 6);
  assert.equal(result[0].members!.length, 2);
  assert.equal(result[0].sources!.length, 2);
  assert.equal(result[0].sources![0].source, a);
  assert.equal(result[0].label, 'feeds · requires');
  assert.equal(result[0].ordered, false);
  assert.equal(result[1], c);
  for (const untouched of [d, e, loop, target]) assert.ok(result.includes(untouched));
  assert.equal(source.length, 7);
});

test('no focus leaves the source untouched, and bundling is stable', () => {
  assert.equal(bundleExpandedPairs(source, ''), source);
  assert.equal(JSON.stringify(bundleExpandedPairs(source, 'A')), JSON.stringify(bundleExpandedPairs(source, 'A')));
});

test('focus precedence: selection, then bundle, then hover; a kind suppresses hover', () => {
  assert.equal(bundleFocusCard('A', 'D', '', ''), 'A');
  assert.equal(bundleFocusCard('', 'A', '', ''), 'A');
  assert.equal(bundleFocusCard('', 'A', '', 'single-edge'), '');
  assert.equal(bundleFocusCard('', 'D', '', 'bundle:' + JSON.stringify(['A', 'B'])), 'A');
  assert.equal(bundleFocusCard('', 'A', 'feeds', ''), '');
});

test('direction survives bundling only when every member agrees', () => {
  assert.equal(bundleExpandedPairs([a, { ...a, path: 'second' }], 'A')[0].ordered, true);
  assert.equal(bundleExpandedPairs([a, { ...b, ordered: false }], 'A')[0].ordered, false);
});
