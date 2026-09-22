import { icon } from '../component-elements/icon';
import { iconButton, labelledButton } from '../component-elements/icon-button';
import { segmented } from '../component-elements/segmented';
import { holdingGlyph } from '../component-elements/relation-glyph';
import { type ExplorerModel, type View } from '../lib/model';
import { LEGEND_ROW_HOLDING, type LegendRow } from '../lib/scene';
import { tokenNumber } from '../lib/tokens';
import { universeStats } from './universe-overview';

export interface TopBar {
  root: HTMLElement;
  tabs: HTMLElement;
  utilities: HTMLElement;
  themeButton: HTMLButtonElement;
  shareButton: HTMLButtonElement;
  renderTabs(view: View): void;
  syncTheme(effective: 'light' | 'dark'): void;
}

export interface TopBarActions {
  openOverview(): void;
  setView(view: View): void;
  toggleTheme(): void;
  toggleShare(): void;
}

export function topBar(model: ExplorerModel, actions: TopBarActions): TopBar {
  const root = document.createElement('div');
  root.className = 'topbar';
  const identity = document.createElement('div');
  identity.className = 'identity';
  const title = document.createElement('button');
  title.type = 'button';
  title.className = 'identity-title';
  title.title = 'Open universe details';
  const name = document.createElement('strong');
  name.textContent = model.universe.label;
  title.append(name, icon('chevron-down'));
  title.addEventListener('click', (event) => {
    event.stopPropagation();
    actions.openOverview();
  });
  identity.append(title, universeStats(model));

  const tabs = document.createElement('div');
  tabs.className = 'view-tabs';
  const renderTabs = (view: View) => {
    const group = segmented(
      'Map view',
      [
        { value: 'frames', label: 'Dimensions' },
        { value: 'artifacts', label: 'Artifacts' },
        { value: 'elements', label: 'Artifacts & Elements' },
      ],
      view,
      (value) => actions.setView(value as View),
    );
    tabs.replaceChildren(...group.childNodes);
  };

  const utilities = document.createElement('div');
  utilities.className = 'utilities';
  const themeButton = iconButton('sun', 'Use dark theme', actions.toggleTheme);
  themeButton.title = 'Use dark theme';
  const shareButton = iconButton('share', 'Export map', actions.toggleShare);
  shareButton.setAttribute('aria-expanded', 'false');
  utilities.append(themeButton, shareButton);
  root.append(identity, tabs, utilities);

  const syncTheme = (effective: 'light' | 'dark') => {
    const label = effective === 'light' ? 'Use dark theme' : 'Use light theme';
    themeButton.setAttribute('aria-label', label);
    themeButton.title = label;
    themeButton.replaceChildren(icon(effective === 'light' ? 'sun' : 'moon'));
  };

  return { root, tabs, utilities, themeButton, shareButton, renderTabs, syncTheme };
}

export function shareMenu(exportSvg: () => void): HTMLElement {
  const menu = document.createElement('div');
  menu.className = 'share-menu';
  menu.setAttribute('aria-label', 'Export map');
  const copyHeading = document.createElement('div');
  copyHeading.className = 'menu-heading';
  copyHeading.textContent = 'Copy';
  const copy = labelledButton('copy', 'Copy image', () => {});
  copy.disabled = true;
  const downloadHeading = document.createElement('div');
  downloadHeading.className = 'menu-heading';
  downloadHeading.textContent = 'Download';
  const png = labelledButton('image', 'PNG', () => {});
  png.disabled = true;
  png.querySelector('span')?.append(Object.assign(document.createElement('small'), { textContent: 'Image' }));
  const svg = labelledButton('vector', 'SVG', exportSvg);
  svg.querySelector('span')?.append(Object.assign(document.createElement('small'), { textContent: 'Vector image' }));
  menu.append(copyHeading, copy, downloadHeading, png, svg);
  return menu;
}

export interface Dock {
  root: HTMLElement;
  mapToggle: HTMLButtonElement;
  readout: HTMLElement;
  setZoom(zoom: number): void;
  setMinimapOpen(open: boolean): void;
}

export interface DockActions {
  search(): void;
  toggleMinimap(): void;
  fit(): void;
  zoomIn(): void;
  zoomOut(): void;
  actualSize(): void;
}

const PERCENT = 100;

export function dock(actions: DockActions): Dock {
  const root = document.createElement('div');
  root.className = 'dock';
  root.setAttribute('aria-label', 'Map navigation');
  const first = document.createElement('div');
  first.className = 'dock-group';
  first.append(iconButton('search', 'Find an artifact or element', actions.search));
  const second = document.createElement('div');
  second.className = 'dock-group';
  const mapToggle = labelledButton('map', 'Map', actions.toggleMinimap);
  mapToggle.setAttribute('aria-expanded', 'false');
  mapToggle.title = 'Open Map';
  const readout = document.createElement('output');
  readout.className = 'zoom-readout';
  const actual = document.createElement('button');
  actual.type = 'button';
  actual.setAttribute('aria-label', 'Reset zoom to 100%');
  actual.title = 'Reset zoom to 100%';
  actual.append(readout);
  actual.addEventListener('click', actions.actualSize);
  second.append(
    mapToggle,
    iconButton('fit', 'Fit map to view', actions.fit),
    iconButton('minus', 'Zoom out', actions.zoomOut),
    actual,
    iconButton('plus', 'Zoom in', actions.zoomIn),
  );
  root.append(first, second);
  return {
    root,
    mapToggle,
    readout,
    setZoom: (zoom) => (readout.textContent = `${Math.round(zoom * PERCENT)}%`),
    setMinimapOpen: (open: boolean) => {
      mapToggle.setAttribute('aria-expanded', String(open));
      mapToggle.title = open ? 'Close Map' : 'Open Map';
    },
  };
}

export const legendRowCopy: Record<LegendRow, string> = {
  direct: 'Direct',
  rolled: 'Rolled up',
  required: 'Required',
  situational: 'When applicable',
  mixed: 'Both',
  owns: 'Answer',
  links: 'Reference',
};

const SVG = 'http://www.w3.org/2000/svg';

function legendSwatch(): SVGSVGElement {
  const span = tokenNumber('--kb-legend-swatch-width');
  const height = tokenNumber('--kb-icon-base');
  const middle = height / 2;
  const svg = document.createElementNS(SVG, 'svg');
  svg.setAttribute('viewBox', `0 0 ${span} ${height}`);
  svg.setAttribute('class', 'legend-swatch');
  svg.setAttribute('aria-hidden', 'true');
  const mark = document.createElementNS(SVG, 'path');
  mark.setAttribute('d', `M 0 ${middle} L ${span} ${middle}`);
  svg.append(mark);
  return svg;
}

export function legend(rows: readonly LegendRow[]): HTMLElement {
  const root = document.createElement('div');
  root.className = 'legend';
  for (const row of rows) {
    const item = document.createElement('span');
    item.dataset.key = row;
    const holding = LEGEND_ROW_HOLDING[row];
    item.append(holding ? holdingGlyph(holding) : legendSwatch());
    item.append(document.createTextNode(legendRowCopy[row]));
    root.append(item);
  }
  return root;
}
