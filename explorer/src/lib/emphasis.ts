import { type Selection } from './model';
import { type Scene, cardWithKin, edgeTouches, nubOwnerCard } from './scene';

export type CardEmphasis = 'active' | 'idle' | 'hushed' | 'dimmed';
export type EdgeEmphasis = 'active' | 'rest' | 'hidden';

export interface Emphasis {
  cards: Map<string, CardEmphasis>;
  edges: Map<string, EdgeEmphasis>;
  nubs: Map<string, EdgeEmphasis>;
  preview: string;
  settled: boolean;
}

export function emphasise(scene: Scene, selection: Selection, hover: string): Emphasis {
  const cards = new Map<string, CardEmphasis>();
  const edges = new Map<string, EdgeEmphasis>();
  const nubs = new Map<string, EdgeEmphasis>();
  const edgeIds = new Set(scene.edges.map((e) => e.path));
  const ownedByNub = nubOwnerCard(selection.connection);
  const selectedCard = selection.entity || selection.option || ownedByNub;
  const hoveredEdge = edgeIds.has(hover) ? hover : '';
  const hoveredCard = hoveredEdge ? '' : hover;
  const subjectEdge = (ownedByNub ? '' : selection.connection) || (selectedCard ? '' : hoveredEdge);
  const subjectCard = selectedCard || (subjectEdge ? '' : hoveredCard);
  const settled = !!selectedCard || !!selection.connection;
  const preview = hoveredCard && hoveredCard !== selectedCard && !subjectEdge ? hoveredCard : '';
  const quietest: CardEmphasis = settled ? 'dimmed' : 'hushed';
  const faintest: EdgeEmphasis = settled ? 'hidden' : 'rest';
  const hoveredInsideSubjectSet =
    !subjectEdge && subjectCard && scene.edges.some((e) => e.path === hoveredEdge && edgeTouches(e, subjectCard)) ? hoveredEdge : '';

  const kin = new Set<string>();
  if (subjectEdge) {
    const edge = scene.edges.find((e) => e.path === subjectEdge);
    if (edge) for (const id of [edge.from, edge.to, ...(edge.targetPair ?? [])]) kin.add(id);
  } else if (subjectCard) for (const id of cardWithKin(scene.edges, subjectCard)) kin.add(id);

  for (const card of scene.layout.cards)
    cards.set(card.id, settled && !subjectEdge && card.id === subjectCard ? 'active' : !kin.size || kin.has(card.id) ? 'idle' : quietest);

  for (const edge of scene.edges) {
    if (subjectEdge) edges.set(edge.path, edge.path === subjectEdge ? 'active' : faintest);
    else if (subjectCard)
      edges.set(
        edge.path,
        edgeTouches(edge, subjectCard) ? (!hoveredInsideSubjectSet || edge.path === hoveredInsideSubjectSet ? 'active' : 'rest') : faintest,
      );
    else edges.set(edge.path, 'rest');
  }

  const subject = subjectCard || subjectEdge;
  for (const nub of scene.nubs)
    nubs.set(nub.id, !subject ? 'active' : nub.id === subjectCard ? 'active' : kin.has(nub.id) ? 'rest' : faintest);

  return { cards, edges, nubs, preview, settled };
}
