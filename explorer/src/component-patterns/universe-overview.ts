import { panel } from '../component-elements/panel';
import { type ExplorerModel, human } from '../lib/model';
import { countOf, listedGroup, paragraph, section } from './detail-copy';

export interface OverviewParts {
  scrim: HTMLElement;
  root: HTMLElement;
}

export function universeStats(model: ExplorerModel): HTMLElement {
  const stats = document.createElement('div');
  stats.className = 'stats';
  stats.setAttribute('aria-label', 'Universe summary');
  const counts: [string, number][] = [
    ['Artifacts', model.entities.filter((e) => e.kind === 'artifact').length],
    ['Elements', model.entities.filter((e) => e.kind === 'element').length],
    ['Frames', model.entities.filter((e) => e.kind === 'frame').length],
    ['Factors', model.entities.filter((e) => e.kind === 'factor').length],
    ['Relations', model.connections.filter((c) => c.kind !== 'composition').length],
  ];
  for (const [label, count] of counts) {
    const item = document.createElement('span');
    const value = document.createElement('b');
    value.textContent = String(count);
    item.append(value, document.createTextNode(` ${label}`));
    stats.append(item);
  }
  return stats;
}

export function universeOverview(model: ExplorerModel, close: () => void): OverviewParts {
  const scrim = document.createElement('div');
  scrim.className = 'scrim';
  scrim.addEventListener('click', (event) => {
    event.stopPropagation();
    close();
  });
  const surface = panel('overview', 'Universe overview', close);
  surface.root.querySelector('.panel-head')?.classList.add('overview-head');
  surface.title.textContent = model.universe.label;
  surface.head.append(universeStats(model));

  const overview = (model.universe.overview ?? {}) as Record<string, string>;
  for (const [title, key] of [
    ['About', 'covers'],
    ['Who it is for', 'for'],
    ['Outside its scope', 'excludes'],
  ] as const) {
    const block = section(title, overview[key] ? [paragraph(overview[key])] : []);
    if (block) surface.body.append(block);
  }

  const details = document.createElement('details');
  details.className = 'source';
  const summary = document.createElement('summary');
  summary.textContent = 'Definition information';
  const facts = document.createElement('dl');
  facts.className = 'facts';
  for (const [term, value] of [
    ['Version', String(model.universe.version)],
    ['Protocol', String(model.universe.conforms_to ?? model.protocolVersion)],
  ] as const) {
    const row = document.createElement('div');
    const dt = document.createElement('dt');
    dt.textContent = term;
    const dd = document.createElement('dd');
    dd.textContent = value;
    row.append(dt, dd);
    facts.append(row);
  }
  details.append(summary, facts);
  const statuses = (model.source.statuses ?? []) as string[];
  const block = section(
    'Declared statuses',
    statuses.length ? [listedGroup(countOf(statuses.length, 'status', 'statuses'), statuses.map(human))] : [],
  );
  if (block) details.append(block);
  surface.body.append(details);
  return { scrim, root: surface.root };
}
