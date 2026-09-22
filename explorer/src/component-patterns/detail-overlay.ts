import { panel } from '../component-elements/panel';
import { segmented } from '../component-elements/segmented';
import { type ExplorerModel, type Connection, byId, human, relationKinds } from '../lib/model';
import { cardinalityDetail, friendly, roleCopy } from '../lib/phrasing';
import { answerOwners, compositionGroups, type CompositionMember } from '../lib/composition-grouping';
import {
  type CopyContext,
  compositionGroupBlock,
  compositionRow,
  conditions,
  guidanceDisclosure,
  countOf,
  listedGroup,
  rowsGroup,
  semanticGroup,
  paragraph,
  relationRow,
  section,
  sourceDisclosure,
} from './detail-copy';
import { guidanceFor } from '../lib/guidance-reading';

export interface DetailOverlay {
  root: HTMLElement;
  subject: string;
}

const SECTION_TITLES = { contents: ['Contents', 'Used in', 'Options'], related: ['Related knowledge'] };

function facts(rows: [string, string][]): HTMLElement {
  const list = document.createElement('dl');
  list.className = 'facts';
  for (const [term, value] of rows) {
    const row = document.createElement('div');
    const dt = document.createElement('dt');
    dt.textContent = term;
    const dd = document.createElement('dd');
    dd.textContent = value;
    row.append(dt, dd);
    list.append(row);
  }
  return list;
}

export function detailOverlay(model: ExplorerModel, subject: string, close: () => void, select: (id: string) => void): DetailOverlay {
  const context: CopyContext = {
    model,
    select,
    owners: answerOwners(model.connections.filter((c) => c.kind === 'composition')),
    named: byId(model),
  };
  const entity = model.entities.find((e) => e.id === subject);
  const rule = model.rules.find((r) => r.id === subject);
  const surface = panel('detail', 'Definition details', close);
  surface.title.textContent = entity?.label ?? 'No artifact needed';

  const body = surface.body;
  if (!entity) body.append(paragraph('Rule', 'detail-kind'));
  if (entity?.description) body.append(paragraph(entity.description, 'detail-question'));

  const ordering = model.orderingFrameId.split(':').slice(1).join(':');
  const composition = model.connections.filter((c) => c.kind === 'composition');

  if (entity?.kind === 'element') {
    body.append(
      facts([
        [human(ordering), human(String(entity.frameValues[ordering] ?? entity.raw[ordering] ?? ''))],
        ['Answers', cardinalityDetail(entity.raw.cardinality)],
      ]),
    );
    if (entity.raw.gate) {
      const block = section('Applies when', [conditions(context, entity.raw.gate)]);
      if (block) body.append(block);
    }
    const advice = guidanceDisclosure(context, guidanceFor(model, entity.id));
    if (advice) body.append(advice);
    const usedIn: CompositionMember[] = composition
      .filter((c) => c.to === entity.id)
      .map((c) => ({ target: c.from, answer: c.to, strength: c.strength, mode: c.mode, when: c.when }));
    const block = section(
      'Used in',
      compositionGroups(usedIn, context.owners).map((group) => compositionGroupBlock(context, group)),
    );
    if (block) body.append(block);
  } else if (entity?.kind === 'artifact') {
    const enablement = entity.raw.enablement ?? {};
    const helps = section('Helps you', [paragraph(String(enablement.action ?? ''), 'detail-question')]);
    if (helps) body.append(helps);
    body.append(
      facts([
        ['Who uses it', String(enablement.actor ?? '')],
        ...(enablement.timing ? ([['When to use it', String(enablement.timing)]] as [string, string][]) : []),
      ] as [string, string][]),
    );
    if (entity.raw.disabled_when) {
      const block = section('Do not use when', [conditions(context, entity.raw.disabled_when)]);
      if (block) body.append(block);
    }
    const advice = guidanceDisclosure(context, guidanceFor(model, entity.id));
    if (advice) body.append(advice);
    const members: CompositionMember[] = composition
      .filter((c) => c.from === entity.id)
      .map((c) => ({ target: c.to, from: c.from, strength: c.strength, mode: c.mode, when: c.when }))
      .sort((left, right) => (left.strength === 'core' ? 0 : 1) - (right.strength === 'core' ? 0 : 1));
    const groups = compositionGroups(members, context.owners);
    const contents = section(
      'Contents',
      groups.map((group) => compositionGroupBlock(context, group)),
    );
    if (contents) body.append(contents);
    if (entity.raw.alias?.form) {
      const block = section(entity.raw.alias.kind === 'normative' ? 'Externally defined format' : 'Related format', [
        paragraph(String(entity.raw.alias.form)),
      ]);
      if (block) body.append(block);
    }
  } else if (entity?.kind === 'option') {
    const frame = model.entities.find((e) => e.id === entity.frameId);
    const values = model.entities.filter((e) => e.kind === 'element' && (e.frameValues[ordering] ?? e.raw[ordering]) === entity.sourceId);
    const ids = new Set(values.map((e) => e.id));
    const owners = model.entities.filter((e) => e.kind === 'artifact' && composition.some((c) => c.from === e.id && ids.has(c.to)));
    body.prepend(paragraph(frame ? `${frame.label} option` : 'Option', 'detail-kind'));
    body.append(
      facts([
        ['Artifacts', String(owners.length)],
        ['Elements', String(values.length)],
      ]),
    );
    const block = section(
      'Elements here',
      values.length
        ? [
            semanticGroup(
              context,
              values.map((element) => element.id),
              2,
            ),
          ]
        : [],
    );
    if (block) body.append(block);
  } else if (entity) {
    if (entity.raw.role) {
      const block = section('Role', [paragraph(roleCopy(entity.raw.role))]);
      if (block) body.append(block);
    }
    const options = model.entities.filter((e) => e.kind === 'option' && e.id.startsWith(`option:${entity.sourceId}:`));
    if (options.length) {
      const block = section('Options', [
        semanticGroup(
          context,
          options.map((option) => option.id),
        ),
      ]);
      if (block) body.append(block);
    }
    for (const [facet, values] of Object.entries((entity.raw.facets ?? {}) as Record<string, string[]>)) {
      const block = section(human(facet), [listedGroup(countOf(values.length, 'option'), values.map(human))]);
      if (block) body.append(block);
    }
  } else if (rule) {
    const block = section('No artifact needed when', [conditions(context, rule.raw.when)]);
    if (block) body.append(block);
  }

  const relations = model.connections.filter((c) => c.kind !== 'composition' && (c.from === subject || c.to === subject));
  if (relations.length) {
    const rows = relations.map((c: Connection) => relationRow(context, c, subject));
    const others = relations.map((c: Connection) => (c.from === subject ? c.to : c.from));
    const block = section('Related knowledge', [rowsGroup(context, others, rows)]);
    if (block) body.append(block);
  }
  body.append(sourceDisclosure(entity?.raw ?? rule?.raw ?? {}));

  const blocks = [...body.querySelectorAll<HTMLElement>(':scope > .section')];
  const find = (titles: string[]) => blocks.find((block) => titles.includes(block.querySelector('h3')?.textContent ?? ''));
  const contents = find(SECTION_TITLES.contents);
  const related = find(SECTION_TITLES.related);
  if (contents || related) {
    const choices = [
      { value: 'overview', label: 'Overview' },
      ...(contents ? [{ value: 'contents', label: 'Contents' }] : []),
      ...(related ? [{ value: 'related', label: 'Related' }] : []),
    ];
    const nav = segmented(
      'Detail sections',
      choices,
      'overview',
      (value) => {
        const target = value === 'contents' ? contents : value === 'related' ? related : null;
        body.scrollTop = target ? target.offsetTop - body.offsetTop : 0;
        for (const button of nav.querySelectorAll('button')) button.setAttribute('aria-pressed', String(button.dataset.value === value));
      },
      'sections',
    );
    surface.head.after(nav);
  }
  return { root: surface.root, subject };
}
