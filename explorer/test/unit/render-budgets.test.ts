import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { polylineCrossings } from '@/src/lib/geometry';
import { renderStates, sceneFor } from './render-states';

const visualCeilings = JSON.parse(readFileSync(new URL('../fixtures/render-budgets.json', import.meta.url), 'utf8')) as Record<
  string,
  { length: number; crossings: number }
>;

const states = renderStates();

function measure(state: (typeof states)[number]) {
  const scene = sceneFor(state);
  const drawn = scene.edges.filter((e) => e.drawn);
  const length = drawn.reduce(
    (total, edge) =>
      total + edge.points.slice(1).reduce((n, p, i) => n + Math.abs(p.x - edge.points[i].x) + Math.abs(p.y - edge.points[i].y), 0),
    0,
  );
  return { length: Math.round(length), crossings: polylineCrossings(drawn.map((e) => e.points)).length };
}

test('canonical product-development visual states stay within reviewed route-length and crossing ceilings', () => {
  const regressions = states
    .map((state) => ({ name: state.name, now: measure(state), was: visualCeilings[state.name] }))
    .filter((row) => !row.was || row.now.length > row.was.length || row.now.crossings > row.was.crossings)
    .map(
      (row) =>
        `${row.name}: length ${row.now.length}/${row.was?.length ?? '—'}, crossings ${row.now.crossings}/${row.was?.crossings ?? '—'}`,
    );
  assert.deepEqual(regressions, [], 'update explorer/test/fixtures/render-budgets.json deliberately when a change earns a higher budget');
});
