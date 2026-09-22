import { panel } from '../component-elements/panel';
import { disclosureList } from '../component-elements/disclosure-list';
import { relationGlyph } from '../component-elements/relation-glyph';
import { type ExplorerModel, type Connection, type DisplayEdge, type Provenance, byId, human } from '../lib/model';
import { type WireDrawing, definitionsBehind, endsOfConnectionPanel, labelOfEntity, wireDrawingOf } from '../lib/connection-reading';
import { compositionDetails } from '../lib/phrasing';
import { answerOwners } from '../lib/composition-grouping';
import { legendRowCopy } from './chrome';
import {
  type CopyContext,
  gatingBlock,
  groupBox,
  inlineReference,
  paragraph,
  relationRow,
  sharedElementRow,
  sourceDisclosure,
} from './detail-copy';

const readingOf = (drawing: WireDrawing, requirement: string): string =>
  [legendRowCopy[drawing.paint === 'rolled' ? 'rolled' : 'direct'], requirement].filter(Boolean).join(' · ');

const requirementBehind = (drawing: WireDrawing, connection: Connection | undefined): string => {
  if (connection?.kind === 'composition') return compositionDetails(connection).requirement;
  return drawing.requirement ? compositionDetails({ strength: drawing.requirement, when: null }).requirement : '';
};

export function connectionOverlay(model: ExplorerModel, edge: DisplayEdge, close: () => void, select: (id: string) => void): HTMLElement {
  const context: CopyContext = {
    model,
    select,
    owners: answerOwners(model.connections.filter((c) => c.kind === 'composition')),
    named: byId(model),
  };
  const surface = panel('detail', 'Connection details', close);
  const anchor = edge.from;
  const provenances: Provenance[] = edge.sources ?? [{ source: edge, composition: [] }];
  const ends = endsOfConnectionPanel(model, edge, provenances);
  surface.title.textContent = ends.other
    ? `${labelOfEntity(model, ends.anchor)} · ${labelOfEntity(model, ends.other)}`
    : labelOfEntity(model, ends.anchor);
  const shared = provenances.every((p) => p.source.label === 'Shared element');
  const caption = paragraph(
    `${provenances.length} ${shared ? `shared ${provenances.length === 1 ? 'element' : 'elements'}` : provenances.length === 1 ? 'connection' : 'connections'}`,
    'detail-kind',
  );
  surface.body.append(caption);

  const rows = provenances.map((provenance) => {
    const source = provenance.source;
    if (source.label === 'Shared element') return sharedElementRow(context, provenance);
    const connection = model.connections.find((c) => c.sourcePath === source.path);
    const inside: Node[] = [];
    if (connection?.kind === 'composition') {
      const gate = gatingBlock(context, { ...compositionDetails(connection), when: connection.when });
      if (gate) inside.push(gate);
    } else if (connection) inside.push(relationRow(context, connection, edge.nub ? anchor : connection.from, false));
    else inside.push(paragraph(`${human(source.from.split(':').pop() ?? '')} · ${source.label}`, 'statement'));
    const drawing = wireDrawingOf(model, provenance);
    if (!drawing) {
      const unresolved = document.createElement('div');
      unresolved.className = 'relation';
      unresolved.append(...inside);
      return unresolved;
    }
    const reading = readingOf(drawing, requirementBehind(drawing, connection));
    inside.unshift(relationGlyph(drawing, inlineReference(context, drawing.from.id), inlineReference(context, drawing.to.id), reading));
    return groupBox(reading, inside);
  });
  surface.body.append(disclosureList(rows));
  const definitions = definitionsBehind(model, provenances);
  if (definitions.length) surface.body.append(sourceDisclosure(definitions));
  return surface.root;
}
