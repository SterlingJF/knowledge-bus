import { icon, markIcon } from '../component-elements/icon';
import { iconButton } from '../component-elements/icon-button';
import { holdingGlyph } from '../component-elements/relation-glyph';
import { disclosureList } from '../component-elements/disclosure-list';
import {
  type CompositionGroup,
  type CompositionMember,
  type CompositionRow,
  compositionGroups,
  holdingOf,
} from '../lib/composition-grouping';
import { type ExplorerModel, type Connection, type DisplayEdge, type Entity, type GuidanceEntry, human, relationKinds } from '../lib/model';
import {
  GUIDANCE_HEADING,
  compositionDetails,
  distinctFromCopy,
  freezeCopy,
  friendly,
  guidanceCountCopy,
  legalityCopy,
  relationPhrasing,
} from '../lib/phrasing';
import { marksOf } from '../lib/icons';

export interface CopyContext {
  model: ExplorerModel;
  select: (id: string) => void;
  owners: Map<string, string>;
  named: Map<string, Entity>;
}

export function section(title: string, body: Node[]): HTMLElement | null {
  if (!body.length) return null;
  const element = document.createElement('section');
  element.className = 'section';
  const heading = document.createElement('h3');
  heading.textContent = title;
  element.append(heading, ...body);
  return element;
}

export function paragraph(text: string, className?: string): HTMLElement {
  const p = document.createElement('p');
  if (className) p.className = className;
  p.textContent = text;
  return p;
}

export function frameName(context: CopyContext, id: string): HTMLElement {
  const span = document.createElement('span');
  span.className = 'frame-name';
  span.append(markIcon(marksOf(context.model).frame(id)));
  const text = document.createElement('span');
  text.textContent = human(id);
  span.append(text);
  return span;
}

export function conditions(context: CopyContext, value: unknown): HTMLElement {
  const box = document.createElement('div');
  box.className = 'conditions';
  const entries = Object.entries((value ?? {}) as Record<string, unknown>);
  entries.forEach(([key, inner], index) => {
    if (index) {
      const joiner = document.createElement('div');
      joiner.className = 'conjunction';
      joiner.textContent = 'and';
      box.append(joiner);
    }
    const row = document.createElement('div');
    row.append(frameName(context, key));
    if (Array.isArray(inner)) {
      const strong = document.createElement('strong');
      inner.forEach((item, position) => {
        if (position) {
          const or = document.createElement('em');
          or.className = 'conjunction';
          or.textContent = ' or ';
          strong.append(or);
        }
        strong.append(document.createTextNode(human(String(item))));
      });
      row.append(strong);
    } else if (inner && typeof inner === 'object') row.append(conditions(context, inner));
    else {
      const strong = document.createElement('strong');
      strong.textContent = String(inner);
      row.append(strong);
    }
    box.append(row);
  });
  return box;
}

export function reference(context: CopyContext, id: string, detail = '', lead?: Node): HTMLButtonElement {
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'reference';
  button.dataset.target = id;
  const label = document.createElement('span');
  if (lead) label.append(lead);
  label.append(document.createTextNode(nameOfEntity(context, id)));
  button.append(label);
  if (detail) {
    const small = document.createElement('small');
    small.textContent = detail;
    button.append(small);
  }
  button.append(icon('chevron'));
  button.addEventListener('click', (event) => {
    event.stopPropagation();
    context.select(id);
  });
  return button;
}

export function inlineReference(context: CopyContext, id: string): HTMLButtonElement {
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'inline-reference';
  button.dataset.target = id;
  button.textContent = nameOfEntity(context, id);
  button.addEventListener('click', (event) => {
    event.stopPropagation();
    context.select(id);
  });
  return button;
}

export const COPY_DEFINITION = 'Copy definition';

export function sourceDisclosure(value: unknown): HTMLElement {
  const details = document.createElement('details');
  details.className = 'source';
  const summary = document.createElement('summary');
  summary.textContent = 'Source definition';
  const definition = JSON.stringify(value, (key, inner) => (['code', 'path', 'type'].includes(key) ? undefined : inner), 2);
  const block = document.createElement('div');
  block.className = 'code-block';
  const copy = iconButton('copy', COPY_DEFINITION, () => void navigator.clipboard?.writeText(definition));
  copy.title = COPY_DEFINITION;
  const pre = document.createElement('pre');
  const code = document.createElement('code');
  code.textContent = definition;
  pre.append(code);
  block.append(copy, pre);
  details.append(summary, block);
  return details;
}

const nameOfEntity = (context: CopyContext, id: string): string => context.named.get(id)?.label ?? human(id.split(':').pop() ?? id);

export const countOf = (many: number, noun: string, plural = `${noun}s`): string => `${many} ${many === 1 ? noun : plural}`;

const countingWhatTheRowsAre = (context: CopyContext, targets: string[]): string => {
  const kinds = new Set(targets.map((target) => context.named.get(target)?.kind).filter(Boolean));
  return countOf(targets.length, kinds.size === 1 ? [...kinds][0]! : 'entry');
};

export function groupBox(heading: string, body: Node[]): HTMLElement {
  const block = document.createElement('div');
  block.className = 'group';
  const stated = document.createElement('h4');
  stated.textContent = heading;
  block.append(stated, ...body);
  return block;
}

function semanticRow(context: CopyContext, target: string): HTMLElement {
  const entity = context.named.get(target);
  const entry = document.createElement('div');
  entry.className = 'entry semantic-row';
  entry.dataset.semanticId = target;
  const name = document.createElement('p');
  name.className = 'semantic-name';
  name.textContent = nameOfEntity(context, target);
  entry.append(name);
  if (entity?.description.trim()) {
    const description = document.createElement('p');
    description.className = 'semantic-description';
    description.textContent = entity.description;
    entry.append(description);
  }
  return entry;
}

export function semanticGroup(context: CopyContext, targets: string[], disclosureLimit?: number): HTMLElement {
  const rows = targets.map((target) => semanticRow(context, target));
  if (disclosureLimit === undefined) return groupBox(countingWhatTheRowsAre(context, targets), rows);
  const list = disclosureList(rows, disclosureLimit);
  list.className = 'semantic-list';
  return groupBox(countingWhatTheRowsAre(context, targets), [list]);
}

export function listedGroup(heading: string, names: string[]): HTMLElement {
  return groupBox(
    heading,
    names.map((name) => {
      const entry = document.createElement('div');
      entry.className = 'entry';
      entry.textContent = name;
      return entry;
    }),
  );
}

export function rowsGroup(context: CopyContext, targets: string[], rows: HTMLElement[]): HTMLElement {
  return groupBox(countingWhatTheRowsAre(context, targets), [disclosureList(rows)]);
}

function compositionMemberRow(context: CopyContext, row: CompositionRow): HTMLElement {
  const entry = document.createElement('div');
  entry.className = 'entry';
  entry.dataset.holding = row.holding;
  const destination = row.destination ? `Kept in ${nameOfEntity(context, row.destination)}` : '';
  entry.append(reference(context, row.target, destination, holdingGlyph(row.holding)));
  return entry;
}

export function gatingBlock(
  context: CopyContext,
  gate: { conditionTitle: string | null; when: unknown; fallback: string | null },
): HTMLElement | null {
  if (!gate.conditionTitle) return null;
  const body: Node[] = [conditions(context, gate.when)];
  if (gate.fallback) body.push(paragraph(gate.fallback));
  return section(gate.conditionTitle, body);
}

export function compositionGroupBlock(context: CopyContext, group: CompositionGroup): HTMLElement {
  const heading = `${group.predicate} \u00b7 ${countingWhatTheRowsAre(
    context,
    group.rows.map((row) => row.target),
  )}`;
  const gate = gatingBlock(context, group);
  return groupBox(heading, [...(gate ? [gate] : []), disclosureList(group.rows.map((row) => compositionMemberRow(context, row)))]);
}

export function guidanceDisclosure(context: CopyContext, entries: GuidanceEntry[]): HTMLElement | null {
  if (!entries.length) return null;
  const details = document.createElement('details');
  details.className = 'guidance';
  const summary = document.createElement('summary');
  const heading = document.createElement('span');
  heading.textContent = GUIDANCE_HEADING;
  const count = document.createElement('span');
  count.className = 'muted';
  count.textContent = ` \u00b7 ${guidanceCountCopy(entries.length)}`;
  summary.append(heading, count);
  details.append(summary);
  for (const entry of entries) {
    const held = document.createElement('div');
    held.className = 'entry claim';
    held.append(paragraph(entry.claim));
    if (entry.when && Object.keys(entry.when).length) {
      const block = section('Applies when', [conditions(context, entry.when)]);
      if (block) held.append(block);
    }
    details.append(held);
  }
  return details;
}

export function compositionRow(context: CopyContext, entry: Connection, target: string, heading = true): HTMLElement {
  const copy = compositionDetails(entry);
  const holding = holdingOf(entry);
  const row = document.createElement('div');
  row.className = 'entry';
  row.dataset.holding = holding;
  if (heading) row.append(reference(context, target, copy.requirement, holdingGlyph(holding)));
  else {
    const line = paragraph('', 'muted');
    line.append(holdingGlyph(holding), document.createTextNode(copy.requirement));
    row.append(line);
  }
  const gate = gatingBlock(context, { ...copy, when: entry.when });
  if (gate) row.append(gate);
  return row;
}

export function relationStatement(context: CopyContext, edge: Connection, subject = edge.from, linked = true): HTMLElement {
  const statement = paragraph('', 'statement');
  const kinds = relationKinds(context.model);
  const kind = kinds.find((k) => k.id === edge.kind);
  const item = (id: string) =>
    linked ? inlineReference(context, id) : document.createTextNode(context.model.entities.find((e) => e.id === id)?.label ?? human(id));
  const phrasing = relationPhrasing(edge, kind, subject);
  if (phrasing) {
    const predicate = document.createElement('span');
    predicate.className = 'muted';
    predicate.textContent = phrasing.phrase;
    statement.append(item(phrasing.subject), document.createTextNode(' '), predicate, document.createTextNode(' '), item(phrasing.object));
    return statement;
  }
  const from = context.model.entities.find((e) => e.id === edge.from);
  const to = context.model.entities.find((e) => e.id === edge.to);
  if (edge.kind === 'feeds') {
    statement.append(
      document.createTextNode('Knowledge from '),
      item(edge.from),
      document.createTextNode(' can inform '),
      item(edge.to),
      document.createTextNode('.'),
    );
    return statement;
  }
  if (edge.kind === 'distinct-from') {
    statement.append(
      item(edge.from),
      document.createTextNode(' and '),
      item(edge.to),
      document.createTextNode(` ${distinctFromCopy(from, to)}. One should not substitute for the other.`),
    );
    return statement;
  }
  const predicate = document.createElement('span');
  predicate.className = 'muted';
  predicate.textContent = friendly(edge.kind, kinds);
  statement.append(item(edge.from), document.createTextNode(' '), predicate, document.createTextNode(' '), item(edge.to));
  return statement;
}

export function relationRestrictions(
  context: CopyContext,
  edge: Connection & { legality?: string; freeze?: string; gate?: unknown },
): Node[] {
  const raw = (edge.raw ?? {}) as { legality?: string; freeze?: string; gate?: unknown };
  const blocks: Node[] = [];
  if (edge.when) {
    const block = section('Applies when', [conditions(context, edge.when)]);
    if (block) blocks.push(block);
  }
  if (raw.gate) {
    const block = section('Conditions', [conditions(context, raw.gate)]);
    if (block) blocks.push(block);
  }
  if (raw.legality) {
    const block = section('Use of this connection', [paragraph(legalityCopy(raw.legality) ?? '')]);
    if (block) blocks.push(block);
  }
  if (raw.freeze) {
    const block = section('Change rule', [paragraph(freezeCopy(raw.freeze) ?? '')]);
    if (block) blocks.push(block);
  }
  return blocks;
}

export function relationRow(context: CopyContext, edge: Connection, subject?: string, heading = true): HTMLElement {
  const row = document.createElement('div');
  row.className = 'relation entry';
  const kinds = relationKinds(context.model);
  const kind = kinds.find((k) => k.id === edge.kind);
  if (subject) {
    const other = edge.from === subject ? edge.to : edge.from;
    const own = context.model.entities.find((e) => e.id === subject)?.label ?? human(subject);
    const copy = relationPhrasing(edge, kind, other);
    let phrase = copy ? copy.phrase : '';
    if (!copy && edge.kind === 'feeds') phrase = edge.from === subject ? 'Can be informed by knowledge from' : 'Knowledge here can inform';
    if (!copy && edge.kind === 'distinct-from') phrase = 'Distinct from';
    if (!phrase) row.append(relationStatement(context, edge, subject));
    else if (heading) row.append(reference(context, other, `${phrase} ${own}`));
    else row.append(paragraph(phrase, 'muted'));
  } else row.append(relationStatement(context, edge));
  if (edge.kind === 'distinct-from') {
    const from = context.model.entities.find((e) => e.id === edge.from);
    const to = context.model.entities.find((e) => e.id === edge.to);
    const meaning = document.createElement('details');
    meaning.className = 'meaning';
    const summary = document.createElement('summary');
    summary.textContent = 'Meaning';
    meaning.append(summary, paragraph(`These ${distinctFromCopy(from, to)}; one should not substitute for the other.`));
    row.append(meaning);
  }
  row.append(...relationRestrictions(context, edge));
  return row;
}

export function sharedElementRow(
  context: CopyContext,
  provenance: { composition: { from: string; to: string; strength?: string; mode?: string; when?: unknown }[] },
): HTMLElement {
  const row = document.createElement('div');
  row.className = 'relation-block';
  const element = provenance.composition[0]?.to;
  if (!element) return row;
  const heading = document.createElement('h3');
  heading.append(inlineReference(context, element));
  row.append(heading);
  const members: CompositionMember[] = provenance.composition.map((entry) => ({
    target: entry.from,
    answer: entry.to,
    strength: entry.strength,
    mode: entry.mode,
    when: entry.when,
  }));
  for (const group of compositionGroups(members, context.owners)) row.append(compositionGroupBlock(context, group));
  return row;
}

export { disclosureList };
