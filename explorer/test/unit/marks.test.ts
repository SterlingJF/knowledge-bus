import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { type ExplorerModel, validateModel } from '@/src/lib/model';
import { type Mark, marksOf, markableConcepts } from '@/src/lib/icons';

const model = validateModel(JSON.parse(readFileSync(new URL('../fixtures/product-development.json', import.meta.url), 'utf8')));
const undeclaredModel: ExplorerModel = { ...model, marks: null };
const concepts = markableConcepts(model);

const resolved = (holder: ExplorerModel, concept: { kind: string; sourceId: string; frameId?: string }): Mark =>
  concept.kind === 'option' ? marksOf(holder).value(concept.frameId ?? '', concept.sourceId) : marksOf(holder).frame(concept.sourceId);

const sameMark = (a: Mark, b: Mark) =>
  'monogram' in a ? 'monogram' in b && a.monogram === b.monogram : 'glyph' in b && a.glyph === b.glyph;

test('a concept the universe marks is drawn with the mark it declares, not one the explorer derives', () => {
  const declared = model.marks?.declared ?? {};
  assert.ok(Object.keys(declared).length > 0, 'the fixture must declare a mark for this to be able to fail');
  let differingFromDerivation = 0;
  for (const concept of concepts) {
    const own = declared[concept.id];
    if (!own) continue;
    assert.deepEqual(resolved(model, concept), own, `${concept.id} is not drawn with its declared mark`);
    if (!sameMark(resolved(undeclaredModel, concept), own)) differingFromDerivation += 1;
  }
  assert.ok(
    differingFromDerivation > 0,
    'every declared mark equals what derivation would have produced, so declaration could not be what won',
  );
});

test('a concept the universe leaves unmarked still reads as itself, by a monogram taken from its own label', () => {
  const declared = model.marks?.declared ?? {};
  const bare = concepts.filter((concept) => !declared[concept.id]);
  assert.ok(bare.length > 0, 'the universe must leave a concept unmarked for the empty case to be under test');
  for (const concept of bare) {
    const mark = resolved(model, concept);
    assert.ok('monogram' in mark, `${concept.id} declares no mark and derived no monogram`);
    assert.ok(mark.monogram.trim().length > 0, `${concept.id} derived a blank monogram`);
    const label = concept.label.toLowerCase();
    assert.ok([...mark.monogram.toLowerCase()].some((letter) => label.includes(letter)));
  }
});

const sourceRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../src');

const sourceFiles = (dir: string): string[] =>
  readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const full = path.join(dir, entry.name);
    return entry.isDirectory() ? sourceFiles(full) : entry.name.endsWith('.ts') ? [full] : [];
  });

const THE_RESOLVER = path.join(sourceRoot, 'lib/icons.ts');
const A_MARK_BUILT_IN_PLACE = /\{\s*(?:monogram|glyph)\s*:[^{}]*\}/;
const DRAWS_A_MARK = /\bmarkIcon\s*\(|\bdrawnMark\s*\(|\bMark\b/;

test('every mark drawn anywhere is decided in one place', () => {
  const files = sourceFiles(sourceRoot);
  assert.ok(files.length > 10, 'the source scan found almost nothing, so it could not find a stray mark either');
  const text = new Map(files.map((file) => [file, readFileSync(file, 'utf8')]));
  const importedBy = new Map<string, string[]>();
  for (const [file, source] of text)
    for (const match of source.matchAll(/from '(\.[^']+)'/g)) {
      const target = path.resolve(path.dirname(file), match[1]) + '.ts';
      if (text.has(target)) (importedBy.get(target) ?? importedBy.set(target, []).get(target)!).push(file);
    }
  const reachingTheResolver = new Set<string>([THE_RESOLVER]);
  const pending = [THE_RESOLVER];
  while (pending.length) {
    const reached = pending.pop()!;
    for (const importer of importedBy.get(reached) ?? [])
      if (!reachingTheResolver.has(importer)) {
        reachingTheResolver.add(importer);
        pending.push(importer);
      }
  }
  const drawing = files.filter((file) => DRAWS_A_MARK.test(text.get(file)!));
  assert.ok(drawing.length > 1, 'no module outside the resolver draws a mark, so this test measures nothing');
  const decidingForThemselves = files.filter((file) => file !== THE_RESOLVER && A_MARK_BUILT_IN_PLACE.test(text.get(file)!));
  const cutOffFromTheResolver = drawing.filter((file) => !reachingTheResolver.has(file));
  assert.deepEqual(
    decidingForThemselves.map((file) => path.relative(sourceRoot, file)),
    [],
  );
  assert.deepEqual(
    cutOffFromTheResolver.map((file) => path.relative(sourceRoot, file)),
    [],
  );
});
