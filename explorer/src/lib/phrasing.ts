import { type Connection, type Entity, type RelationKind, human } from './model';

export interface Phrasing {
  subject: string;
  object: string;
  phrase: string;
}

export function relationPhrasing(edge: Connection, kind: RelationKind | undefined, subject = edge.from): Phrasing | null {
  if (subject !== edge.from && subject !== edge.to) throw new Error('Displayed subject must be an edge endpoint');
  if (!kind?.phrasing) return null;
  const reversed = subject !== edge.from;
  const phrase = kind.phrasing[kind.ordered && reversed ? 'reverse' : 'forward'];
  if (!phrase) return null;
  return { subject, object: reversed ? edge.from : edge.to, phrase };
}

export interface CompositionCopy {
  requirement: string;
  conditionTitle: string | null;
  fallback: string | null;
}

export function compositionDetails(entry: { strength?: string; when?: unknown }): CompositionCopy {
  const conditional = !!entry.when && Object.keys(entry.when as object).length > 0;
  const core = entry.strength === 'core';
  return {
    requirement: core ? (conditional ? 'Required when applicable' : 'Required') : 'When applicable',
    conditionTitle: conditional ? (core ? 'Required when' : 'Available when') : null,
    fallback: conditional && core ? 'Otherwise optional, if the element applies.' : null,
  };
}

export const GUIDANCE_HEADING = 'How to do this well';

export const guidanceCountCopy = (count: number) => `${count} ${count === 1 ? 'note' : 'notes'}`;

export const cardinalityCopy = (cardinality?: string) =>
  cardinality === 'singleton'
    ? 'One answer'
    : cardinality?.startsWith('per-')
      ? 'One per ' + cardinality.slice(4).replaceAll('-', ' ')
      : cardinality
        ? 'Answers'
        : '';

export const cardinalityDetail = (cardinality?: string) =>
  cardinality === 'singleton'
    ? 'Not divided into separate answers'
    : cardinality?.startsWith('per-')
      ? 'One per ' + cardinality.slice(4).replaceAll('-', ' ')
      : cardinality || 'Not specified';

export const roleCopy = (role?: string) =>
  ({
    ordering: 'Organizes elements in a declared order',
    applicability: 'Determines whether an artifact is needed',
    gating: 'Controls which content applies',
    selection: 'Selects content for context',
  })[role ?? ''] ??
  role ??
  '';

export const setByCopy = (setBy?: string) =>
  ({
    universe: 'Fixed for this universe',
    instance: 'Set for each piece of work',
    scope: 'Set for the relevant scope',
  })[setBy ?? ''] ?? '';

export const legalityCopy = (legality?: string) =>
  ({ permitted: 'Permitted', 'permitted-if-logged': 'Permitted only if recorded', forbidden: 'Not permitted' })[legality ?? ''] ?? legality;

export const freezeCopy = (freeze?: string) =>
  ({ open: 'Open', baselined: 'Changes must be recorded as new events, not edits.', superseded: 'Superseded' })[freeze ?? ''] ?? freeze;

export const relationKindCopy = (id: string, kinds: RelationKind[]) =>
  kinds.find((k) => k.id === id)?.phrasing?.forward || 'Related knowledge';

export const friendly = (id: string, kinds: RelationKind[]) =>
  kinds.some((k) => k.id === id) ? relationKindCopy(id, kinds) : human(String(id));

export function distinctFromCopy(from: Entity | undefined, to: Entity | undefined): string {
  const bothArtifacts = from?.kind === 'artifact' && to?.kind === 'artifact';
  const bothElements = from?.kind === 'element' && to?.kind === 'element';
  return bothArtifacts
    ? 'enable different actions'
    : bothElements
      ? 'answer different questions'
      : 'answer different questions or enable different actions';
}
