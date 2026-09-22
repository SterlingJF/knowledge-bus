import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import {
  type DisplayEdge,
  type Provenance,
  compositionEdges,
  compositionEntries,
  relationEdges,
  validateModel,
  wiringEdges,
} from '@/src/lib/model';
import { artifactEdges, collapseCardPairs } from '@/src/lib/rollup';
import { definitionsBehind, wireDrawingOf } from '@/src/lib/connection-reading';

const model = validateModel(JSON.parse(readFileSync(new URL('../fixtures/product-development.json', import.meta.url), 'utf8')));

const artifactIds = model.entities.filter((entity) => entity.kind === 'artifact').map((entity) => entity.id);

interface Panel {
  edge: DisplayEdge;
  provenances: Provenance[];
}

const panelsEveryConnectionSubjectOpens = (): Panel[] => {
  const panels: Panel[] = [];
  for (const mode of ['composition', 'relations'] as const) {
    const drawn = mode === 'composition' ? compositionEdges(model) : [...relationEdges(model), ...wiringEdges(model)];
    for (const edge of drawn) panels.push({ edge, provenances: [{ source: edge, composition: [] }] });
    const rolled = collapseCardPairs(
      artifactEdges(
        drawn.filter((edge) => !edge.targetPair),
        compositionEntries(model),
        artifactIds,
        mode,
      ),
    );
    for (const edge of rolled) panels.push({ edge, provenances: edge.sources ?? [] });
  }
  return panels;
};

const pathsOnlyTheSourceDocumentNames = new Set(
  [...model.connections.map((c) => c.sourcePath), ...model.wiring.map((w) => w.sourcePath)].filter(
    (path): path is string => typeof path === 'string' && path.length > 0,
  ),
);

const wiringPaths = new Set(model.wiring.map((w) => w.sourcePath));

test('P20 every connection panel draws what the board drew, and its disclosure names no pointer the reader cannot use', () => {
  const panels = panelsEveryConnectionSubjectOpens();
  const provenances = panels.flatMap((panel) => panel.provenances);
  assert.ok(panels.length > model.connections.length, 'the enumeration must reach more panels than there are connections');
  assert.ok(pathsOnlyTheSourceDocumentNames.size > 0, 'the model must name paths for a pointer leak to be detectable');

  const undrawable = provenances.filter((provenance) => wireDrawingOf(model, provenance) === null);
  assert.deepEqual(
    [...new Set(undrawable.map((provenance) => provenance.source.path))].filter((path) => !wiringPaths.has(path)),
    [],
    'a provenance the source document defines must draw',
  );
  assert.ok(undrawable.length < provenances.length, 'some provenance must draw for this to be able to fail');

  const leaked = panels.flatMap((panel) => {
    const disclosed = JSON.stringify(definitionsBehind(model, panel.provenances));
    const pointers = [...pathsOnlyTheSourceDocumentNames].filter((path) => disclosed.includes(path));
    const synthetic = disclosed.includes('|') ? ['a key joined from two paths'] : [];
    return [...pointers, ...synthetic].map((hit) => `${panel.edge.path}: ${hit}`);
  });
  assert.deepEqual(leaked, []);
});

test('a connection panel discloses a definition exactly when the source document defines one', () => {
  for (const panel of panelsEveryConnectionSubjectOpens()) {
    const drawable = panel.provenances.filter((provenance) => wireDrawingOf(model, provenance) !== null);
    const disclosed = definitionsBehind(model, panel.provenances);
    assert.equal(
      disclosed.length > 0,
      drawable.length > 0,
      `${panel.edge.path} discloses ${disclosed.length} definitions for ${drawable.length} drawable connections`,
    );
  }
});

const SHARED_ELEMENT_LABEL = 'Shared element';

const endpointsDrawnBy = (panel: Panel): Set<string> =>
  new Set(
    panel.provenances.flatMap((provenance) => {
      const drawing = wireDrawingOf(model, provenance);
      return drawing ? [drawing.from.id, drawing.to.id] : [];
    }),
  );

test('a rolled-up relation panel names the endpoints its own subject cannot name, and a shared-element panel names its own', () => {
  const rolled = panelsEveryConnectionSubjectOpens().filter((panel) => panel.edge.rolled && panel.provenances.length > 0);
  const overSharedElements = rolled.filter((panel) => panel.provenances.every((p) => p.source.label === SHARED_ELEMENT_LABEL));
  const overRelations = rolled.filter((panel) => panel.provenances.every((p) => p.source.label !== SHARED_ELEMENT_LABEL));
  assert.ok(overSharedElements.length > 0, 'the enumeration must reach a shared-element panel for this to be able to fail');
  assert.ok(overRelations.length > 0, 'the enumeration must reach a rolled-up relation panel for this to be able to fail');
  assert.deepEqual(
    overSharedElements.filter((panel) => [...endpointsDrawnBy(panel)].some((id) => id !== panel.edge.from && id !== panel.edge.to)),
    [],
  );
  assert.deepEqual(
    overRelations
      .filter((panel) => endpointsDrawnBy(panel).size > 0)
      .filter((panel) => ![...endpointsDrawnBy(panel)].some((id) => id !== panel.edge.from && id !== panel.edge.to))
      .map((panel) => panel.edge.path),
    [],
  );
});
