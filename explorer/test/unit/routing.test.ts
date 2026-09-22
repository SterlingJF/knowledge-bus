import test from 'node:test';
import assert from 'node:assert/strict';
import { Router } from '@/src/lib/routing';

const boxes = Array.from({ length: 19 }, (_, i) => ({
  x: 60 + (i % 5) * 290 + (Math.floor(i / 5) % 2) * 45,
  y: 480 + Math.floor(i / 5) * 180,
  w: 230,
  h: 104,
}));
const rects = new Map(boxes.map((b, i) => [String(i), b]));

function points(path: string) {
  const numbers = (path.match(/-?\d+(?:\.\d+)?/g) ?? []).map(Number);
  return Array.from({ length: numbers.length / 2 }, (_, n) => ({ x: numbers[n * 2], y: numbers[n * 2 + 1] }));
}

test('routes are orthogonal, avoid every card, and repeat exactly', () => {
  const router = new Router();
  let checked = 0;
  for (let i = 0; i < boxes.length; i += 1)
    for (let j = 0; j < boxes.length; j += 1)
      if (i !== j)
        for (const strength of ['core', 'situational']) {
          const edge = { from: String(i), to: String(j), strength };
          router.begin();
          const path = router.path(boxes[i], boxes[j], rects, edge);
          router.begin();
          assert.equal(path, router.path(boxes[i], boxes[j], rects, edge));
          assert.doesNotMatch(path, /[HVQC]/);
          const route = points(path);
          for (let n = 1; n < route.length; n += 1) {
            const p = route[n - 1];
            const q = route[n];
            assert.ok(p.x === q.x || p.y === q.y);
            for (const r of boxes)
              assert.ok(
                !(p.x === q.x
                  ? p.x > r.x && p.x < r.x + r.w && Math.max(p.y, q.y) > r.y && Math.min(p.y, q.y) < r.y + r.h
                  : p.y > r.y && p.y < r.y + r.h && Math.max(p.x, q.x) > r.x && Math.min(p.x, q.x) < r.x + r.w),
                'route crosses a card',
              );
          }
          checked += 1;
        }
  assert.equal(checked, 684);
});

test('parallel edges between the same pair take separate ports', () => {
  const router = new Router();
  router.begin();
  const a = router.path(boxes[0], boxes[7], rects, { from: '0', to: '7', kind: 'feeds' });
  const b = router.path(boxes[0], boxes[7], rects, { from: '0', to: '7', kind: 'requires' });
  assert.notEqual(a, b);
});
