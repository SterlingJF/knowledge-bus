import { type CompositionEntry, type Connection, type DisplayEdge, type ExplorerModel, type Provenance, human } from './model';

export interface WireEnd {
  id: string;
  label: string;
}

export interface WireDrawing {
  from: WireEnd;
  to: WireEnd;
  ordered: boolean;
  paint: 'element' | 'rolled';
  requirement: 'core' | 'situational' | null;
}

const SHARED_ELEMENT_LABEL = 'Shared element';

export const labelOfEntity = (model: ExplorerModel, id: string): string =>
  model.entities.find((entity) => entity.id === id)?.label ?? human(id.split(':').pop() ?? id);

const endOf = (model: ExplorerModel, id: string): WireEnd => ({ id, label: labelOfEntity(model, id) });

const connectionDefining = (model: ExplorerModel, path: string | undefined): Connection | undefined =>
  path === undefined ? undefined : model.connections.find((connection) => connection.sourcePath === path);

const appliesOnlySometimes = (strength: string | undefined): boolean => strength === 'situational' || strength === 'mixed';

const requirementAcross = (steps: CompositionEntry[], own: string | undefined): WireDrawing['requirement'] => {
  const strengths = [own, ...steps.map((step) => step.strength)].filter((strength) => strength !== undefined);
  if (!strengths.length) return null;
  return strengths.some(appliesOnlySometimes) ? 'situational' : 'core';
};

export function wireDrawingOf(model: ExplorerModel, provenance: Provenance): WireDrawing | null {
  const steps = provenance.composition;
  if (provenance.source.label === SHARED_ELEMENT_LABEL) {
    const [owner, peer] = steps;
    if (!owner || !peer) return null;
    return {
      from: endOf(model, owner.from),
      to: endOf(model, peer.from),
      ordered: false,
      paint: 'rolled',
      requirement: requirementAcross(steps, undefined),
    };
  }
  const connection = connectionDefining(model, provenance.source.path);
  if (!connection) return null;
  return {
    from: endOf(model, connection.from),
    to: endOf(model, connection.to),
    ordered: connection.ordered,
    paint: steps.length ? 'rolled' : 'element',
    requirement: requirementAcross(steps, connection.strength),
  };
}

export interface PanelEnds {
  anchor: string;
  other: string | null;
}

export function endsOfConnectionPanel(model: ExplorerModel, edge: DisplayEdge, provenances: Provenance[]): PanelEnds {
  const anchor = edge.from;
  const others = new Set<string>();
  for (const provenance of provenances) {
    const drawing = wireDrawingOf(model, provenance);
    const ends = drawing ? [drawing.from.id, drawing.to.id] : [provenance.source.from, provenance.source.to];
    for (const id of ends) if (id !== anchor) others.add(id);
    if (others.size > 1) return { anchor, other: null };
  }
  return { anchor, other: others.size === 1 ? [...others][0] : null };
}

export function definitionsBehind(model: ExplorerModel, provenances: Provenance[]): unknown[] {
  return provenances.flatMap((provenance) => {
    const direct = connectionDefining(model, provenance.source.path);
    if (direct) return [direct.raw];
    if (provenance.source.label !== SHARED_ELEMENT_LABEL) return [];
    return provenance.composition
      .map((step) => connectionDefining(model, step.path))
      .filter((step): step is Connection => step !== undefined)
      .map((step) => step.raw);
  });
}
