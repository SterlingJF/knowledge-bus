import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import {
  type ExplorerModel,
  type ViewOptions,
  validateModel,
  relationEdges,
  relationKinds,
  initialOptions,
  updateOptions,
} from '@/src/lib/model';
import { layoutFor } from '@/src/lib/layout';
import { cardAnatomy } from '@/src/lib/card';

const model = validateModel(JSON.parse(readFileSync(new URL('../fixtures/product-development.json', import.meta.url), 'utf8')));

test('relation edges are labelled with authored phrasing, never a raw relation kind', () => {
  const edges = relationEdges(model);
  const kinds = new Set(relationKinds(model).map((k) => k.id));
  const phrases = new Set(relationKinds(model).flatMap((k) => [k.phrasing?.forward, k.phrasing?.reverse].filter(Boolean)));
  assert.notEqual(edges.length, 0, 'authored relations must be exercised');
  for (const edge of edges) {
    assert.ok(!kinds.has(edge.label), `edge ${edge.path} shows the raw kind ${edge.label}`);
    assert.ok(phrases.has(edge.label), `edge ${edge.path} shows ${edge.label}, which is not authored phrasing`);
  }
});

test('an ordered relation reads forward from its declared subject', () => {
  const ordered = relationKinds(model).find((k) => k.ordered && k.phrasing?.reverse)!;
  const edge = relationEdges(model).find((e) => e.kind === ordered.id)!;
  assert.equal(edge.label, ordered.phrasing!.forward);
});

const SCHEMA_VOCABULARY = ['gating', 'applicability', 'ordering', 'scope', 'role', 'option', 'rule', 'empty_composition'];

const WORDS_A_UNIVERSE_AUTHORS = ['label', 'description', 'forward', 'reverse'];

const RENAMED = 'Renamedword';

const EVERY_VIEW: Partial<ViewOptions>[] = [
  { view: 'frames' },
  { view: 'artifacts' },
  { view: 'elements', group: true },
  { view: 'elements', group: false },
];

const mapCopy = (universe: ExplorerModel): string[] =>
  EVERY_VIEW.flatMap((patch) => {
    const layout = layoutFor(universe, updateOptions(initialOptions(), patch));
    return [
      ...layout.boundaries.flatMap((b) => [b.title, b.caption]),
      ...layout.cards.flatMap((card) => {
        const anatomy = cardAnatomy(card, universe);
        return [anatomy.title, anatomy.subtitle];
      }),
    ];
  }).filter(Boolean);

const schemaWordsIn = (copy: string[]): string[] => [
  ...new Set(
    copy.flatMap((line) =>
      SCHEMA_VOCABULARY.filter((word) => new RegExp(`\\b${word}\\b`, 'i').test(line)).map((word) => `${word} in "${line}"`),
    ),
  ),
];

const withTheUniverseRenamed = (universe: ExplorerModel): ExplorerModel => {
  let renamed = 0;
  const walk = (value: unknown): unknown =>
    Array.isArray(value)
      ? value.map(walk)
      : value && typeof value === 'object'
        ? Object.fromEntries(
            Object.entries(value as Record<string, unknown>).map(([key, held]) => [
              key,
              WORDS_A_UNIVERSE_AUTHORS.includes(key) && typeof held === 'string' && held ? `${RENAMED}${(renamed += 1)}` : walk(held),
            ]),
          )
        : value;
  return walk(universe) as ExplorerModel;
};

const copyExplorerAuthors = (): string[] =>
  mapCopy(withTheUniverseRenamed(model)).map((line) => line.replaceAll(new RegExp(`${RENAMED}\\d+`, 'g'), ''));

test('renaming every word the universe authors leaves none of them in the copy the map draws', () => {
  const authored = [...new Set(model.entities.flatMap((e) => [e.label, e.description]).filter(Boolean))];
  assert.notEqual(authored.length, 0, 'authored words must be exercised');
  const survivors = copyExplorerAuthors().filter((line) => authored.some((word) => new RegExp(`\\b${word}\\b`).test(line)));
  assert.deepEqual(survivors, []);
});

test('a schema word a universe puts in its own label reaches the map, and is not explorer copy to police', () => {
  const label = model.entities.find((e) => SCHEMA_VOCABULARY.some((word) => new RegExp(`\\b${word}\\b`, 'i').test(e.label)))!;
  assert.ok(mapCopy(model).includes(label.label), `${label.label} must reach the map for this case to be able to fail`);
  assert.ok(
    schemaWordsIn(mapCopy(model)).some((hit) => hit.includes(label.label)),
    'a check that does not separate the two reports the universe for its own label',
  );
  assert.deepEqual(
    schemaWordsIn(copyExplorerAuthors()).filter((hit) => hit.includes(label.label)),
    [],
  );
});

test('the copy explorer authors for the map never shows schema vocabulary, only the product nouns', () => {
  assert.notEqual(copyExplorerAuthors().length, 0, 'Explorer copy must be exercised');
  assert.deepEqual(schemaWordsIn(copyExplorerAuthors()), []);
});
