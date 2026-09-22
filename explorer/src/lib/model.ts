import type { Mark } from './icons';

export type EntityKind = 'artifact' | 'element' | 'frame' | 'factor' | 'option';

export interface Entity {
  id: string;
  sourceId: string;
  kind: EntityKind;
  label: string;
  description: string;
  frameValues: Record<string, unknown>;
  raw: Record<string, any>;
  sourcePath?: string;
  frameId?: string;
  facet?: string | null;
}

export interface Connection {
  id: string;
  from: string;
  to: string;
  kind: string;
  ordered: boolean;
  phrasing: { forward: string; reverse?: string };
  strength?: string;
  mode?: string;
  when?: Record<string, string[]> | null;
  raw: unknown;
  sourcePath?: string;
}

export interface Wiring {
  id: string;
  from: string;
  sourceFrameId: string;
  to: string;
  kind: 'gate' | 'ordering' | 'disabled_when' | 'composition.when' | 'relation.gate' | 'empty_composition.when';
  value: string[];
  sourcePath: string;
  targetPair?: [string, string];
  targetLabel?: string;
}

export interface Rule {
  id: string;
  kind: string;
  raw: any;
  sourcePath: string;
}

export interface GuidanceEntry {
  id: string;
  subject: string;
  kind: string;
  claim: string;
  source: string;
  when?: Record<string, unknown> | null;
  sourcePath: string;
}

export interface GuidanceSource {
  cite: string;
  url?: string;
  checked?: string;
}

export interface Guidance {
  id: string;
  label: string;
  version: string;
  guides: string;
  kinds: { id: string; sourced: boolean }[];
  sources: Record<string, GuidanceSource>;
  entries: GuidanceEntry[];
}

const DRAWABLE_PATH_DATA = /^[Mm][0-9eE,.\-+ \t]*[0-9][MmZzLlHhVvCcSsQqTtAa0-9,.\-+eE \t]*$/;
const A_MONOGRAM_FITS_THE_ICON_BOX = /^[\p{L}\p{N}]{1,2}$/u;

export const drawable = (mark: object): boolean => {
  const held = mark as { glyph?: unknown; monogram?: unknown };
  if (typeof held.monogram === 'string') return A_MONOGRAM_FITS_THE_ICON_BOX.test(held.monogram);
  return typeof held.glyph === 'string' && DRAWABLE_PATH_DATA.test(held.glyph);
};

export interface DeclaredMarks {
  id: string;
  label: string;
  version: string;
  marksFor: string;
  declared: Record<string, Mark>;
}

export interface RelationKind {
  id: string;
  ordered: boolean;
  phrasing?: { forward?: string; reverse?: string };
}

export interface ExplorerModel {
  schema: 'knowledge-bus/explorer-model/1';
  protocolVersion: string;
  sourceDigest: string;
  universe: {
    id: string;
    label: string;
    version: string | number;
    conforms_to?: string;
    ordering_frame: string;
    overview?: Record<string, string>;
  };
  orderingFrameId: string;
  entities: Entity[];
  connections: Connection[];
  wiring: Wiring[];
  rules: Rule[];
  guidance?: Guidance | null;
  marks?: DeclaredMarks | null;
  source: Record<string, any>;
  evaluation: { status: string; context: unknown };
}

export interface CompositionEntry {
  from: string;
  to: string;
  strength?: string;
  mode?: string;
  when?: Record<string, string[]> | null;
  path: string;
}

export interface Provenance {
  source: DisplayEdge;
  composition: CompositionEntry[];
}

export interface DisplayEdge {
  path: string;
  from: string;
  to: string;
  label: string;
  ordered: boolean;
  kind?: string;
  strength?: string;
  mode?: string;
  when?: Record<string, string[]> | null;
  rolled?: boolean;
  mixedRollup?: boolean;
  bundled?: boolean;
  targetPair?: [string, string];
  targetLabel?: string;
  value?: string[];
  members?: DisplayEdge[];
  sources?: Provenance[];
  provenance?: Provenance;
  nub?: boolean;
}

export type View = 'frames' | 'artifacts' | 'elements';
export type ConnectionMode = '' | 'relations' | 'composition';
export type Display = 'lines' | 'counts';
export type LineStyle = 'uniform' | 'distinct';
export type Theme = 'auto' | 'light' | 'dark';

export interface ViewOptions {
  view: View;
  connections: ConnectionMode;
  display: Display;
  lineStyle: LineStyle;
  group: boolean;
  emphasis: string[];
  frames: string[];
  theme: Theme;
}

export interface Camera {
  x: number;
  y: number;
  z: number;
}

export interface Selection {
  entity: string;
  connection: string;
  option: string;
}

export interface ViewerState {
  options: ViewOptions;
  selection: Selection;
  camera: Camera;
}

export const aViewGroupsItsElements = (view: View): boolean => view === 'elements';

export const theDisplayAViewOpensOn = (view: View): Display => (view === 'elements' ? 'counts' : 'lines');

export const initialOptions = (view: View = 'elements'): ViewOptions => ({
  view,
  connections: 'composition',
  display: theDisplayAViewOpensOn(view),
  lineStyle: 'distinct',
  group: aViewGroupsItsElements(view),
  emphasis: [],
  frames: [],
  theme: 'auto',
});

export const emptySelection = (): Selection => ({ entity: '', connection: '', option: '' });

const turningToLines = (current: ViewOptions, patch: Partial<ViewOptions>): boolean =>
  patch.display === 'lines' && current.display !== 'lines' && patch.lineStyle === undefined;

export function updateOptions(current: ViewOptions, patch: Partial<ViewOptions>): ViewOptions {
  const next: ViewOptions = {
    ...current,
    ...patch,
    lineStyle: turningToLines(current, patch) ? 'distinct' : (patch.lineStyle ?? current.lineStyle),
    emphasis: [...(patch.emphasis ?? current.emphasis)],
    frames: [...(patch.frames ?? current.frames)],
  };
  const valid =
    ['frames', 'artifacts', 'elements'].includes(next.view) &&
    ['', 'relations', 'composition'].includes(next.connections) &&
    ['lines', 'counts'].includes(next.display) &&
    ['uniform', 'distinct'].includes(next.lineStyle) &&
    ['auto', 'light', 'dark'].includes(next.theme) &&
    typeof next.group === 'boolean' &&
    next.emphasis.every((v) => typeof v === 'string') &&
    next.frames.every((v) => typeof v === 'string');
  if (!valid) throw new Error('Invalid view options');
  return next;
}

export function validateModel(input: unknown): ExplorerModel {
  const model = input as ExplorerModel;
  if (
    !model ||
    model.schema !== 'knowledge-bus/explorer-model/1' ||
    !Array.isArray(model.entities) ||
    !Array.isArray(model.connections) ||
    !Array.isArray(model.wiring) ||
    !Array.isArray(model.rules) ||
    !model.universe?.label ||
    !model.source
  )
    throw new Error('Unsupported Explorer model');
  const ids = new Set<string>();
  for (const entity of model.entities) {
    if (
      typeof entity.id !== 'string' ||
      ids.has(entity.id) ||
      typeof entity.label !== 'string' ||
      !['artifact', 'element', 'frame', 'factor', 'option'].includes(entity.kind) ||
      !entity.raw ||
      !entity.frameValues
    )
      throw new Error('Malformed Explorer entity');
    ids.add(entity.id);
  }
  const edges = new Set<string>();
  for (const c of model.connections) {
    if (
      edges.has(c.id) ||
      !ids.has(c.from) ||
      !ids.has(c.to) ||
      typeof c.phrasing?.forward !== 'string' ||
      !c.phrasing.forward.trim() ||
      (c.ordered && (typeof c.phrasing.reverse !== 'string' || !c.phrasing.reverse.trim()))
    )
      throw new Error('Malformed Explorer connection');
    edges.add(c.id);
  }
  const ruleIds = new Set(model.rules.map((r) => r.id));
  for (const w of model.wiring)
    if (!ids.has(w.from) || (!ids.has(w.to) && !ruleIds.has(w.to)) || !Array.isArray(w.value)) throw new Error('Malformed Explorer wiring');
  if (model.guidance) {
    if (!Array.isArray(model.guidance.entries) || !Array.isArray(model.guidance.kinds)) throw new Error('Malformed Explorer guidance');
    const declaredKinds = new Set(model.guidance.kinds.map((k) => k.id));
    for (const entry of model.guidance.entries)
      if (!ids.has(entry.subject) || !declaredKinds.has(entry.kind) || typeof entry.claim !== 'string' || !entry.claim.trim())
        throw new Error('Malformed Explorer guidance entry');
  }
  if (model.marks) {
    const declared = model.marks.declared;
    if (!declared || typeof declared !== 'object' || Array.isArray(declared)) throw new Error('Malformed Explorer marks');
    for (const mark of Object.values(declared))
      if (!mark || typeof mark !== 'object' || Object.keys(mark).length !== 1 || !drawable(mark))
        throw new Error('Malformed Explorer mark');
  }
  return model;
}

export function phraseFor(c: Connection, subject: string): string {
  if (subject !== c.from && subject !== c.to) throw new Error('Subject is not an endpoint');
  return c.ordered && subject === c.to ? c.phrasing.reverse! : c.phrasing.forward;
}

export const human = (s: string) => (s ? s.replaceAll('-', ' ').replace(/^./, (c) => c.toUpperCase()) : '');

export const relationKinds = (model: ExplorerModel): RelationKind[] => (model.source.relation_kinds ?? []) as RelationKind[];

export const compositionEntries = (model: ExplorerModel): CompositionEntry[] =>
  model.connections
    .filter((c) => c.kind === 'composition')
    .map((c) => ({ from: c.from, to: c.to, strength: c.strength, mode: c.mode, when: c.when, path: c.sourcePath! }));

export const relationEdges = (model: ExplorerModel): DisplayEdge[] =>
  model.connections
    .filter((c) => c.kind !== 'composition')
    .map((c) => ({
      path: c.sourcePath!,
      from: c.from,
      to: c.to,
      kind: c.kind,
      ordered: c.ordered,
      label: phraseFor(c, c.from),
      when: c.when,
    }));

const compositionLabel = (c: Connection) =>
  c.strength === 'core' ? (c.when ? 'Required when applicable' : 'Required') : 'When applicable';

export const compositionEdges = (model: ExplorerModel): DisplayEdge[] =>
  model.connections
    .filter((c) => c.kind === 'composition')
    .map((c) => ({
      path: c.sourcePath!,
      from: c.from,
      to: c.to,
      kind: 'composition',
      ordered: true,
      label: compositionLabel(c),
      strength: c.strength,
      mode: c.mode,
      when: c.when,
    }));

export const wiringEdges = (model: ExplorerModel): DisplayEdge[] =>
  model.wiring
    .filter((w) => w.kind !== 'ordering')
    .map((w) => ({
      path: w.sourcePath,
      from: w.from,
      to: w.to,
      kind: w.kind,
      ordered: true,
      label: w.kind,
      value: w.value,
      targetPair: w.targetPair,
      targetLabel: w.targetLabel,
    }));

export const byId = (model: ExplorerModel) => new Map(model.entities.map((e) => [e.id, e]));

export function referencedFrames(model: ExplorerModel, id: string): string[] {
  const direct = model.wiring.filter((w) => w.kind !== 'ordering' && (w.to === id || w.targetPair?.includes(id)));
  return [...new Set(direct.map((w) => w.sourceFrameId))];
}
