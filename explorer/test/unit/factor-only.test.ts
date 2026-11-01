import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { layoutFor } from '@/src/lib/layout';
import {
  type ExplorerModel,
  type View,
  initialOptions,
  orderingKey,
  theViewAModelOpensOn,
  updateOptions,
  validateModel,
} from '@/src/lib/model';
import { cardAnatomy } from '@/src/lib/card';
import { setByCopy } from '@/src/lib/phrasing';
import { model as productDevelopment } from './render-states';

const readers: ExplorerModel = validateModel(JSON.parse(readFileSync(new URL('../fixtures/hall-readers.json', import.meta.url), 'utf8')));

const views: View[] = ['frames', 'artifacts', 'elements'];

test('a universe spec with no ordering frame lays out in every view', () => {
  assert.equal(readers.orderingFrameId, null);
  assert.equal(orderingKey(readers), '');
  for (const view of views) {
    const layout = layoutFor(readers, updateOptions(initialOptions(), { view }));
    for (const card of layout.cards) cardAnatomy(card, readers);
  }
});

test('a universe spec with only factors opens on its factors', () => {
  assert.equal(theViewAModelOpensOn(readers), 'frames');
  assert.equal(theViewAModelOpensOn(productDevelopment), 'elements');
  const layout = layoutFor(readers, updateOptions(initialOptions(), { view: 'frames' }));
  const factors = readers.entities.filter((entity) => entity.kind === 'factor').map((entity) => entity.id);
  assert.deepEqual(layout.cards.map((card) => card.id).sort(), [...factors].sort());
});

test('set_by copy names the place where the value is set', () => {
  assert.equal(setByCopy('universe'), 'Set once for this universe spec');
  assert.equal(setByCopy('scope'), 'Set per folder');
  assert.equal(setByCopy('instance'), 'Set per document');
});
