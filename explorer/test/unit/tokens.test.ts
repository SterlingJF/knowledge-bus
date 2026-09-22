import test from 'node:test';
import assert from 'node:assert/strict';
import { tokenNumber, tokenValue } from '@/src/lib/tokens';
import { boundaryScale, grow, labelScale, motionDuration } from '@/src/lib/camera';

test('a token that changes with the theme has no one number to read, and says which token', () => {
  assert.throws(() => tokenNumber('--kb-canvas'), /--kb-canvas/);
  assert.throws(() => tokenNumber('--kb-canvas'), /theme/i);
});

test('the refusal follows the alias chain, so a name one hop from the theme is refused too', () => {
  assert.equal(tokenValue('--kb-count-edge'), 'var(--kb-border)');
  assert.throws(() => tokenNumber('--kb-count-edge'), /--kb-count-edge/);
  assert.throws(() => tokenNumber('--kb-count-edge'), /theme/i);
});

test('the refusal reaches a theme nested inside a value, not only one that opens it', () => {
  assert.equal(tokenValue('--kb-card-selected-ring-element'), '0 0 0 5px color-mix(in srgb,var(--kb-element) 12%,transparent)');
  assert.throws(() => tokenNumber('--kb-card-selected-ring-element'), /--kb-card-selected-ring-element/);
  assert.throws(() => tokenNumber('--kb-card-selected-ring-element'), /theme/i);
});

test('a theme-independent token still reads as a number, directly and through an alias', () => {
  assert.equal(tokenNumber('--kb-space-2'), 8);
  assert.equal(tokenValue('--kb-count-zoom-growth'), 'var(--kb-zoom-growth-sm)');
  assert.equal(tokenNumber('--kb-count-zoom-growth'), parseFloat(tokenValue('--kb-zoom-growth-sm')));
});

test('the growth limits the camera reads through a variable survive the guard', () => {
  const zoom = 1;
  for (const limit of ['--kb-heading-zoom-growth', '--kb-label-zoom-growth', '--kb-count-zoom-growth'] as const)
    assert.ok(Number.isFinite(grow(zoom, limit)));
  assert.ok(Number.isFinite(boundaryScale(zoom)));
  assert.ok(Number.isFinite(labelScale(zoom)));
  assert.ok(Number.isFinite(motionDuration()));
});
