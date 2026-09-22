import { expect, test, type Browser, type Page } from '@playwright/test';
import { build } from 'esbuild';
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { paths } from '@/src/lib/icons';
import type { ExplorerModel } from '@/src/lib/model';

const root = path.resolve(import.meta.dirname, '../../..');
const artifact = path.join(root, 'dist/explorer/product-development.html');
type Leaf = { value: string };
const authority = JSON.parse(readFileSync(path.join(root, 'explorer/styles/visual-tokens.json'), 'utf8')) as {
  roles: Record<string, Record<string, Leaf>>;
  parts: Record<string, Record<string, Leaf | string[]>>;
};
const tokens: Record<string, Leaf> = {};
for (const [group, entries] of Object.entries(authority.roles))
  for (const [leaf, token] of Object.entries(entries)) tokens[group === 'color' ? `--kb-${leaf}` : `--kb-${group}-${leaf}`] = token;
for (const [part, entries] of Object.entries(authority.parts))
  for (const [leaf, token] of Object.entries(entries)) if (leaf !== 'selectors') tokens[`--kb-${part}-${leaf}`] = token as Leaf;
const partSelectors: Record<string, string[]> = Object.fromEntries(
  Object.entries(authority.parts)
    .filter(([, entries]) => Array.isArray(entries.selectors))
    .map(([part, entries]) => [part, entries.selectors as string[]]),
);

const aliased = (name: string) => {
  let value = tokens[name].value;
  for (let hop = 0; hop < 20; hop += 1) {
    const alias = value.match(/^var\(\s*(--[\w-]+)\s*\)$/);
    if (!alias) break;
    value = tokens[alias[1]].value;
  }
  return value;
};
const themed = (name: string, theme: 'light' | 'dark') => {
  const value = aliased(name);
  const pair = value.match(/^light-dark\(([^,]+),([^)]+)\)$/);
  const hex = (pair ? pair[theme === 'light' ? 1 : 2] : value).trim();
  const full = hex.length === 4 ? `#${hex[1]}${hex[1]}${hex[2]}${hex[2]}${hex[3]}${hex[3]}` : hex;
  return `rgb(${parseInt(full.slice(1, 3), 16)}, ${parseInt(full.slice(3, 5), 16)}, ${parseInt(full.slice(5, 7), 16)})`;
};
const light = (name: string) => themed(name, 'light');
const metric = (name: string) => parseFloat(aliased(name));
const iconPath = (name: string) => paths[name];

interface State {
  options: {
    view: string;
    connections: string;
    display: string;
    lineStyle: string;
    group: boolean;
    emphasis: string[];
    frames: string[];
    theme: string;
  };
  selection: { entity: string; connection: string; option: string };
  camera: { x: number; y: number; z: number };
}

test.beforeAll(() => {
  if (!existsSync(artifact)) throw new Error('Generated artifact missing: run build:explorer and render:explorer first.');
});

async function open(page: Page) {
  const requests: string[] = [];
  const errors: string[] = [];
  await page.route(/^(?!file:)/, (route) => {
    requests.push(route.request().url());
    void route.abort();
  });
  page.on('pageerror', (error) => errors.push(error.message));
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(message.text());
  });
  await page.goto(pathToFileURL(artifact).href);
  await page.waitForFunction(() => !!(document.getElementById('explorer') as { explorerViewer?: unknown } | null)?.explorerViewer);
  await settle(page);
  return { requests, errors };
}

const explorer = (page: Page, selector: string) => page.locator('#explorer').locator(selector);
const embeddedModel = (page: Page): Promise<ExplorerModel> =>
  page.evaluate(() => JSON.parse(document.getElementById('explorer-model')!.textContent!));
const state = (page: Page): Promise<State> =>
  page.evaluate(() =>
    (document.getElementById('explorer') as unknown as { explorerViewer: { getState(): State } }).explorerViewer.getState(),
  );

async function settle(page: Page) {
  let previous = '';
  for (let attempt = 0; attempt < 40; attempt += 1) {
    await page.waitForTimeout(70);
    const current = JSON.stringify((await state(page)).camera);
    if (current === previous) return;
    previous = current;
  }
}

async function selectDetail(page: Page, subject: string) {
  await page.evaluate((id) => {
    (document.getElementById('explorer') as unknown as { explorerViewer: { select(value: string): void } }).explorerViewer.select(id);
  }, subject);
  await page.waitForFunction(
    (id) =>
      (document.getElementById('explorer') as unknown as { explorerViewer: { getState(): State } }).explorerViewer.getState().selection
        .entity === id,
    subject,
  );
  await settle(page);
  return explorer(page, '.detail');
}

const overlaps = (a: { x: number; y: number; width: number; height: number }, b: typeof a) =>
  a.x < b.x + b.width && b.x < a.x + a.width && a.y < b.y + b.height && b.y < a.y + a.height;

async function openMenu(page: Page) {
  if (!(await explorer(page, '.settings').isVisible())) await explorer(page, '.menu-trigger').click();
  await expect(explorer(page, '.settings')).toBeVisible();
}

async function showLines(page: Page) {
  await openMenu(page);
  await explorer(page, '.settings [data-value="lines"]').click();
  await page.keyboard.press('Escape');
  await expect.poll(async () => (await state(page)).options.display).toBe('lines');
  await settle(page);
}

test('opens offline on composition counts, and the lines that tell required from optional are one menu step away', async ({ page }) => {
  const { requests, errors } = await open(page);
  const current = await state(page);
  expect(current.options.connections).toBe('composition');
  expect(current.options.display).toBe('counts');
  expect(current.options.lineStyle).toBe('distinct');
  expect(current.options.view).toBe('elements');
  expect(current.options.group).toBe(true);
  expect(current.selection.entity).toBe('');
  const model = await embeddedModel(page);
  expect(new Set(await explorer(page, '.card').evaluateAll((cards) => cards.map((card) => card.getAttribute('data-id'))))).toEqual(
    new Set(model.entities.filter((entity) => entity.kind === 'artifact' || entity.kind === 'element').map((entity) => entity.id)),
  );
  const connected = new Set(
    model.connections.filter((connection) => connection.kind === 'composition').flatMap((connection) => [connection.from, connection.to]),
  );
  expect(
    new Set(await explorer(page, '[data-nub]').evaluateAll((badges) => badges.map((badge) => badge.getAttribute('data-nub')))),
  ).toEqual(connected);
  expect(await explorer(page, '.wire').count()).toBe(0);
  await expect(explorer(page, '.legend')).toHaveCount(0);
  await showLines(page);
  expect(await explorer(page, '.wire').count()).toBeGreaterThan(0);
  expect(await explorer(page, '.count').count()).toBe(0);
  await expect(explorer(page, '.legend')).toHaveCount(1);
  expect(requests).toEqual([]);
  expect(errors).toEqual([]);
});

test('the universe overview opens from the title and reports its counts', async ({ page }) => {
  await open(page);
  await explorer(page, '.identity-title').click();
  const overview = explorer(page, '.overview');
  await expect(overview).toBeVisible();
  await expect(overview).toContainText('About');
  await expect(overview).toContainText('Who it is for');
  await expect(overview).toContainText('Outside its scope');
  const model = await embeddedModel(page);
  await expect(overview.locator('.stats > span')).toHaveText([
    ...(['artifact', 'element', 'frame', 'factor'] as const).map(
      (kind) => `${model.entities.filter((entity) => entity.kind === kind).length} ${kind[0].toUpperCase() + kind.slice(1)}s`,
    ),
    `${model.connections.filter((connection) => connection.kind !== 'composition').length} Relations`,
  ]);
  await expect(explorer(page, '.scrim')).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(overview).toHaveCount(0);
});

test('cards carry ordering icons, cardinality and referenced-frame icons', async ({ page }) => {
  await open(page);
  const vision = explorer(page, '.card[data-id="element:product-vision"]');
  await expect(vision.locator('.card-order-icon')).toHaveCount(1);
  await expect(vision).toContainText('One answer');
  const gated = explorer(page, '.card[data-id="element:positioning-statement"]');
  await expect(gated.locator('.card-frames')).toHaveAttribute('aria-label', /Uptake/);
  await expect(explorer(page, '.card[data-kind="artifact"]').first()).toHaveCSS('border-top-width', `${metric('--kb-stroke-lg')}px`);
});

test('selection frames the subject beside the overlay and dismissal returns to the overview', async ({ page }) => {
  await open(page);
  await explorer(page, '.card[data-kind="artifact"]').first().click();
  await settle(page);
  expect((await state(page)).selection.entity).toBe('artifact:product-strategy-canvas');
  const detail = explorer(page, '.detail');
  await expect(detail).toBeVisible();
  await expect(detail).toContainText('commit to a direction');
  await expect(detail).toContainText('Who uses it');
  await expect(detail).toContainText('Do not use when');
  await expect(detail.locator('.section > h3').filter({ hasText: 'Contents' })).toHaveCount(1);
  const card = await explorer(page, '.card[data-state="selected"]').boundingBox();
  const overlay = await detail.boundingBox();
  const viewport = await explorer(page, '.viewport').boundingBox();
  expect(overlaps(card!, overlay!)).toBe(false);
  expect(overlay!.height).toBeLessThan(viewport!.height);
  expect(await explorer(page, '.card[data-state="dimmed"]').count()).toBeGreaterThan(0);
  await detail.locator('.close').click();
  await settle(page);
  const dismissed = await state(page);
  expect(dismissed.selection.entity).toBe('artifact:product-strategy-canvas');
  await expect(explorer(page, '.detail')).toHaveCount(0);
  expect(await explorer(page, '.card[data-state="dimmed"]').count()).toBeGreaterThan(0);
  await expect(explorer(page, '.card[data-state="selected"]')).toHaveCount(1);
});

test('dismissing the detail returns the camera to the same overview the map fits to', async ({ page }) => {
  await open(page);
  await explorer(page, '.dock button[aria-label="Fit map to view"]').click();
  await settle(page);
  const fitted = (await state(page)).camera;
  await explorer(page, '.card[data-id="element:rollout-and-phasing"]').click();
  await settle(page);
  expect((await state(page)).camera.z).not.toBeCloseTo(fitted.z, 3);
  await explorer(page, '.detail .close').click();
  await settle(page);
  const after = (await state(page)).camera;
  expect(after.z).toBeCloseTo(fitted.z, 3);
  expect(after.x).toBeCloseTo(fitted.x, 0);
  expect(after.y).toBeCloseTo(fitted.y, 0);
});

test('previewing a card while another is selected keeps it dimmed and only recolours its border', async ({ page }) => {
  await open(page);
  await explorer(page, '.card[data-id="element:product-vision"]').click();
  await settle(page);
  const other = explorer(page, '.card[data-id="element:trade-offs"]');
  await expect(other).toHaveAttribute('data-state', 'dimmed');
  const dimmed = await other.evaluate((card) => {
    const style = getComputedStyle(card);
    return { background: style.backgroundColor, title: getComputedStyle(card.querySelector('.card-title')!).opacity };
  });
  await other.hover({ force: true });
  await expect(other).toHaveAttribute('data-preview', 'true');
  await page.waitForTimeout(400);
  const previewed = await other.evaluate((card) => {
    const style = getComputedStyle(card);
    return {
      background: style.backgroundColor,
      border: style.borderLeftColor,
      title: getComputedStyle(card.querySelector('.card-title')!).opacity,
    };
  });
  expect(previewed.background).toBe(dimmed.background);
  expect(previewed.title).toBe(dimmed.title);
  expect(previewed.border).toBe(light('--kb-element'));
  await expect(other).toHaveAttribute('data-state', 'dimmed');
});

test('detail sections navigate, lists disclose after three, and inline references move the selection', async ({ page }) => {
  await open(page);
  await explorer(page, '.card[data-id="artifact:design-doc"]').click();
  await settle(page);
  const detail = explorer(page, '.detail');
  await expect(detail.locator('.sections button')).toHaveCount(3);
  const showAll = detail.locator('.show-all').first();
  await expect(showAll).toContainText('Show all');
  await showAll.click();
  await expect(showAll).toContainText('Show fewer');
  await detail.locator('.sections button', { hasText: 'Related' }).click();
  await detail.locator('.reference').first().click();
  await settle(page);
  expect((await state(page)).selection.entity).not.toBe('artifact:design-doc');
});

test('composition copy states each requirement once over its group, with its conditions', async ({ page }) => {
  await open(page);
  await explorer(page, '.card[data-id="artifact:opportunity-assessment"]').click();
  await settle(page);
  const detail = explorer(page, '.detail');
  const groups = detail.locator('.group');
  expect(await groups.count()).toBeGreaterThan(1);
  await expect(detail.locator('.group h4').filter({ hasText: 'Required when applicable' })).toHaveCount(1);
  await expect(detail).toContainText('Required when');
  await expect(detail).toContainText('Otherwise optional, if the element applies.');
  await expect(detail.locator('.conditions .frame-name').first()).toContainText('Authority');
  expect(await detail.locator('.entry[data-holding]').count()).toBeGreaterThan(0);
});

test('the connection panel carries the same gating condition as the entity panel', async ({ page }) => {
  await open(page);
  await explorer(page, '.count[aria-label^="Opportunity assessment:"]').click();
  await settle(page);
  const detail = explorer(page, '.detail');
  await expect(detail).toBeVisible();
  const showAll = detail.locator('.show-all').first();
  if (await showAll.count()) await showAll.click();
  const gated = detail.locator('.group').filter({ hasText: 'Consent and authority' }).first();
  await expect(gated).toContainText('Required when applicable');
  const block = gated.locator('.section').filter({ hasText: 'Required when' });
  await expect(block).toHaveCount(1);
  await expect(block.locator('.conditions .frame-name').first()).toContainText('Authority');
  await expect(block).toContainText('Otherwise optional, if the element applies.');
});

test('relations read with their authored phrasing, never a raw kind', async ({ page }) => {
  await open(page);
  await explorer(page, '.card[data-id="element:value-proposition"]').click();
  await settle(page);
  const detail = explorer(page, '.detail');
  await expect(detail).toContainText('Related knowledge');
  const text = (await detail.textContent()) ?? '';
  expect(text).not.toMatch(/distinct-from|presupposes|counterweight-to|split-signal/);
  expect(text).toMatch(/Not interchangeable with|Context from|Context for|Balances/);
});

test('view options are persistent, independent of selection, and reset keeps the selection', async ({ page }) => {
  await open(page);
  await explorer(page, '.card[data-kind="artifact"]').first().click();
  await settle(page);
  await openMenu(page);
  await explorer(page, '.settings [data-value=""]').click();
  expect((await state(page)).options.connections).toBe('');
  expect(await explorer(page, '.count').count()).toBe(0);
  expect((await state(page)).selection.entity).toBe('artifact:product-strategy-canvas');
  await openMenu(page);
  await explorer(page, '.settings [data-value="relations"]').click();
  await openMenu(page);
  await explorer(page, '.settings [data-value="lines"]').click();
  expect(await explorer(page, '.wire').count()).toBeGreaterThan(0);
  await openMenu(page);
  await explorer(page, '.settings [data-page="emphasis"]').click();
  await explorer(page, '.settings .chip').nth(0).click();
  await explorer(page, '.settings .chip').nth(1).click();
  expect((await state(page)).options.emphasis).toHaveLength(2);
  await explorer(page, '.settings .back').click();
  await expect(explorer(page, '.settings')).toContainText('View options');
  await explorer(page, '.settings [data-action="reset"]').click();
  const reset = await state(page);
  expect(reset.options).toMatchObject({
    connections: 'composition',
    display: 'counts',
    lineStyle: 'distinct',
    emphasis: [],
    frames: [],
    group: true,
  });
  expect(reset.selection.entity).toBe('artifact:product-strategy-canvas');
});

test('frame filters narrow the map and the active dot reflects them', async ({ page }) => {
  await open(page);
  const before = await explorer(page, '.card[data-kind="element"]').count();
  await openMenu(page);
  await explorer(page, '.settings [data-page="frames"]').click();
  await explorer(page, '.settings .chip').first().click();
  const after = await explorer(page, '.card[data-kind="element"]').count();
  expect(after).toBeLessThan(before);
  expect(after).toBeGreaterThan(0);
  await expect(explorer(page, '.menu-trigger .active-dot')).toBeVisible();
});

test('composition line style marks required and situational memberships', async ({ page }) => {
  await open(page);
  await openMenu(page);
  await explorer(page, '.settings [data-value="lines"]').click();
  await openMenu(page);
  await explorer(page, '.settings [data-value="distinct"]').click();
  expect((await state(page)).options.lineStyle).toBe('distinct');
  expect(await explorer(page, '.wire[data-dash="situational"]').count()).toBeGreaterThan(0);
  await expect(explorer(page, '.legend span[data-key="situational"]')).toHaveText('When applicable');
  await expect(explorer(page, '.legend span[data-key="required"]')).toHaveText('Required');
});

test('every view lays out, and the artifact view rolls connections up', async ({ page }) => {
  await open(page);
  const model = await embeddedModel(page);
  await explorer(page, '.view-tabs [data-value="frames"]').click();
  await settle(page);
  expect((await state(page)).options.view).toBe('frames');
  await expect(explorer(page, '.card[data-kind="rule"]')).toHaveCount(model.rules.length);
  await expect(explorer(page, '.card[data-kind="option"]')).toHaveCount(
    model.entities.filter((entity) => entity.kind === 'option' && entity.id.startsWith(`option:${model.universe.ordering_frame}:`)).length,
  );
  await explorer(page, '.view-tabs [data-value="artifacts"]').click();
  await settle(page);
  expect(await explorer(page, '.card[data-kind="element"]').count()).toBe(0);
  await expect(explorer(page, '.card[data-kind="artifact"]')).toHaveCount(
    model.entities.filter((entity) => entity.kind === 'artifact').length,
  );
  await openMenu(page);
  await explorer(page, '.settings [data-value="relations"]').click();
  await openMenu(page);
  await explorer(page, '.settings [data-value="lines"]').click();
  await settle(page);
  expect(await explorer(page, '.wire[data-paint="rolled"]').count()).toBeGreaterThan(0);
});

test('a connection opens its own details listing every source', async ({ page }) => {
  await open(page);
  await explorer(page, '.count').first().click();
  await settle(page);
  expect((await state(page)).selection.connection).not.toBe('');
  const detail = explorer(page, '.detail');
  await expect(detail).toBeVisible();
  await expect(detail).toContainText('connection');
  await expect(detail.locator('.source')).toHaveCount(1);
});

test('search reveals an element, switching view when it is not on the map', async ({ page }) => {
  await open(page);
  await explorer(page, '.view-tabs [data-value="artifacts"]').click();
  await settle(page);
  await explorer(page, '.dock button[aria-label="Find an artifact or element"]').click();
  await explorer(page, '.search input').fill('north star');
  await expect(explorer(page, '.result').first()).toBeVisible();
  await explorer(page, '.result').filter({ hasText: 'North star metric' }).first().click();
  await settle(page);
  const current = await state(page);
  expect(current.selection.entity).toBe('element:north-star-metric');
  expect(current.options.view).toBe('elements');
  await expect(explorer(page, '.search')).toHaveCount(0);
});

test('blank canvas clears the selection and Escape only dismisses the detail', async ({ page }) => {
  await open(page);
  await explorer(page, '.card[data-kind="artifact"]').first().click();
  await settle(page);
  const viewport = (await explorer(page, '.viewport').boundingBox())!;
  const empty = await page.evaluate(() => {
    const shell = document.getElementById('explorer')!.shadowRoot!;
    const box = shell.querySelector('.viewport')!.getBoundingClientRect();
    for (let y = box.bottom - 90; y > box.top + 20; y -= 12)
      for (let x = box.right - 30; x > box.left + 20; x -= 12) {
        const hit = shell.elementFromPoint(x, y);
        if (hit && !hit.closest('.card,.count,.panel,.dock,.legend,.boundary-title,.wire-hit')) return { x, y };
      }
    return null;
  });
  expect(empty).not.toBeNull();
  await page.mouse.click(empty!.x, empty!.y);
  await settle(page);
  expect((await state(page)).selection.entity).toBe('');
  await explorer(page, '.card[data-kind="artifact"]').nth(1).click();
  await settle(page);
  expect((await state(page)).selection.entity).toBe('artifact:business-model-canvas');
  await page.keyboard.press('Escape');
  await settle(page);
  expect((await state(page)).selection.entity).not.toBe('');
  await expect(explorer(page, '.detail')).toHaveCount(0);
  expect(await explorer(page, '.card[data-state="dimmed"]').count()).toBeGreaterThan(0);
  await page.keyboard.press('Escape');
  await settle(page);
  expect((await state(page)).selection.entity).not.toBe('');
});

test('the minimap toggles, drags by its header, and navigates by its plot', async ({ page }) => {
  await open(page);
  const toggle = explorer(page, '.dock button:has-text("Map")');
  await toggle.click();
  await expect(toggle).toHaveAttribute('aria-expanded', 'true');
  const minimap = explorer(page, '.minimap');
  const before = (await minimap.boundingBox())!;
  const head = (await minimap.locator('.minimap-head').boundingBox())!;
  await page.mouse.move(head.x + 20, head.y + head.height / 2);
  await page.mouse.down();
  await page.mouse.move(head.x - 150, head.y - 60, { steps: 6 });
  await page.mouse.up();
  const after = (await minimap.boundingBox())!;
  expect(after.x).toBeLessThan(before.x - 50);
  await explorer(page, '.dock button[aria-label="Zoom in"]').click();
  await explorer(page, '.dock button[aria-label="Zoom in"]').click();
  await settle(page);
  const cameraBefore = (await state(page)).camera;
  const plot = (await minimap.locator('.plot').boundingBox())!;
  await page.mouse.click(plot.x + plot.width * 0.85, plot.y + plot.height * 0.85);
  await settle(page);
  const cameraAfter = (await state(page)).camera;
  expect(cameraAfter.x !== cameraBefore.x || cameraAfter.y !== cameraBefore.y).toBe(true);
  await minimap.locator('.close').click();
  await expect(toggle).toHaveAttribute('aria-expanded', 'false');
});

test('the dock zooms, fits, and reports the zoom level', async ({ page }) => {
  await open(page);
  const readout = explorer(page, '.zoom-readout');
  const start = (await state(page)).camera.z;
  await explorer(page, '.dock button[aria-label="Zoom in"]').click();
  await settle(page);
  expect((await state(page)).camera.z).toBeGreaterThan(start);
  await expect(readout).toContainText('%');
  await explorer(page, '.dock button[aria-label="Reset zoom to 100%"]').click();
  await settle(page);
  expect(Math.round((await state(page)).camera.z * 100)).toBe(100);
  await explorer(page, '.dock button[aria-label="Fit map to view"]').click();
  await settle(page);
  expect((await state(page)).camera.z).toBeLessThan(1);
});

test('theme switching drives the whole surface', async ({ page }) => {
  await open(page);
  await expect(explorer(page, '.shell')).toHaveCSS('background-color', light('--kb-canvas'));
  await explorer(page, '.utilities button[aria-label="Use dark theme"]').click();
  expect((await state(page)).options.theme).toBe('dark');
  await expect(explorer(page, '.shell')).not.toHaveCSS('background-color', light('--kb-canvas'));
  await explorer(page, '.utilities button[aria-label="Use light theme"]').click();
  await expect(explorer(page, '.shell')).toHaveCSS('background-color', light('--kb-canvas'));
});

test('the export menu offers SVG and downloads a complete dual-theme file', async ({ page }) => {
  await open(page);
  await explorer(page, '.utilities button[aria-label="Export map"]').click();
  const menu = explorer(page, '.share-menu');
  await expect(menu).toBeVisible();
  await expect(menu.locator('button', { hasText: 'Copy image' })).toBeDisabled();
  await expect(menu.locator('button', { hasText: 'PNG' })).toBeDisabled();
  const download = page.waitForEvent('download');
  await menu.locator('button', { hasText: 'SVG' }).click();
  const file = await download;
  expect(file.suggestedFilename()).toBe('product-development-map.svg');
});

test('the export is deterministic, complete and free of chrome', async ({ page }) => {
  await open(page);
  const cards = await explorer(page, '.card').count();
  const [first, second] = await page.evaluate(async () => {
    const viewer = (document.getElementById('explorer') as unknown as { explorerViewer: { exportSvg(o?: object): Promise<string> } })
      .explorerViewer;
    return [await viewer.exportSvg({ theme: 'auto' }), await viewer.exportSvg({ theme: 'auto' })];
  });
  expect(first).toBe(second);
  expect(first.match(/<g data-entity=/g)?.length).toBe(cards);
  expect(first).not.toMatch(/<script|foreignObject/);
  expect(first).not.toContain('View options');
  expect(first).not.toContain('Find an artifact');
  const dir = mkdtempSync(path.join(tmpdir(), 'explorer-svg-'));
  const file = path.join(dir, 'map.svg');
  writeFileSync(file, first);
  try {
    for (const scheme of ['light', 'dark'] as const) {
      await page.emulateMedia({ colorScheme: scheme });
      await page.goto(pathToFileURL(file).href);
      const fill = await page.evaluate(() => getComputedStyle(document.querySelector('rect')!).fill);
      expect(fill).toBe(scheme === 'light' ? light('--kb-canvas') : 'rgb(23, 30, 34)');
      const bounds = await page.evaluate(() => {
        const svg = document.documentElement as unknown as SVGSVGElement;
        const view = svg.viewBox.baseVal;
        const items = [...svg.querySelectorAll('text, rect, path, polygon')].map((node) => {
          const b = (node as SVGGraphicsElement).getBBox();
          return { x: b.x, y: b.y, width: b.width, height: b.height };
        });
        return { view: { x: view.x, y: view.y, w: view.width, h: view.height }, items };
      });
      for (const item of bounds.items) {
        expect(item.x).toBeGreaterThanOrEqual(bounds.view.x - 1);
        expect(item.x + item.width).toBeLessThanOrEqual(bounds.view.x + bounds.view.w + 1);
        expect(item.y + item.height).toBeLessThanOrEqual(bounds.view.y + bounds.view.h + 1);
      }
    }
    const viewports = [
      { width: 1366, height: 768 },
      { width: 390, height: 844 },
    ];
    for (const viewport of viewports) {
      await page.setViewportSize(viewport);
      await page.goto('about:blank');
      await page.goto(pathToFileURL(file).href);
      await page.evaluate(() => new Promise(requestAnimationFrame));
      const fit = await page.evaluate(() => {
        const svg = document.documentElement as unknown as SVGSVGElement;
        const view = svg.viewBox.baseVal;
        const matrix = svg.getScreenCTM()!;
        const start = new DOMPoint(view.x, view.y).matrixTransform(matrix);
        const end = new DOMPoint(view.x + view.width, view.y + view.height).matrixTransform(matrix);
        return { start, end, preserve: svg.preserveAspectRatio.baseVal.align };
      });
      expect(fit.start.x).toBeGreaterThanOrEqual(-1);
      expect(fit.start.y).toBeGreaterThanOrEqual(-1);
      expect(fit.end.x).toBeLessThanOrEqual(viewport.width + 1);
      expect(fit.end.y).toBeLessThanOrEqual(viewport.height + 1);
      expect(fit.preserve).not.toBe(1);
    }
    const embedded = path.join(dir, 'embedded.html');
    writeFileSync(embedded, '<img src="./map.svg" style="display:block;width:320px;height:auto">');
    await page.goto(pathToFileURL(embedded).href);
    const renderedRatio = await page.evaluate(() => {
      const image = document.querySelector('img')!;
      const box = image.getBoundingClientRect();
      return box.width / box.height;
    });
    const viewBox = first
      .match(/viewBox="[^"]*\s([\d.]+)\s([\d.]+)"/)!
      .slice(1)
      .map(Number);
    expect(renderedRatio).toBeCloseTo(viewBox[0] / viewBox[1], 3);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test('tokens reach live consumers including an open overlay', async ({ page }) => {
  await open(page);
  await explorer(page, '.card[data-kind="artifact"]').first().click();
  await settle(page);
  const tab = explorer(page, '.view-tabs button[aria-pressed="true"]');
  await expect(tab).toHaveCSS('box-shadow', /.+/);
  await page.evaluate(() => {
    const style = document.createElement('style');
    style.textContent = '.shell{--kb-accent:#ff0000;--kb-panel-height-max:180px;--kb-icon-base:40px;--kb-canvas:#00ff00}';
    document.getElementById('explorer')!.shadowRoot!.append(style);
  });
  await expect(explorer(page, '.shell')).toHaveCSS('background-color', 'rgb(0, 255, 0)');
  const overlay = (await explorer(page, '.detail').boundingBox())!;
  expect(overlay.height).toBeLessThanOrEqual(180);
  await expect(explorer(page, '.dock .icon').first()).toHaveCSS('width', '40px');
});

test('narrow viewports stack the overlay and keep every control reachable', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await open(page);
  await page.evaluate(() =>
    (document.getElementById('explorer') as unknown as { explorerViewer: { select(id: string): void } }).explorerViewer.select(
      'artifact:product-strategy-canvas',
    ),
  );
  await settle(page);
  const detail = (await explorer(page, '.detail').boundingBox())!;
  expect(detail.x + detail.width).toBeLessThanOrEqual(390);
  expect(detail.height).toBeLessThanOrEqual(844 * metric('--kb-panel-height-narrow-fraction') + 1);
  await expect(explorer(page, '.dock')).toBeInViewport();
  await expect(explorer(page, '.menu-trigger')).toBeInViewport();
  await openMenu(page);
  const menu = (await explorer(page, '.settings').boundingBox())!;
  expect(menu.x + menu.width).toBeLessThanOrEqual(390);
  expect(menu.x).toBeGreaterThanOrEqual(0);
});

test('reduced motion makes camera changes immediate', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await open(page);
  await explorer(page, '.card[data-kind="artifact"]').first().click();
  const immediate = (await state(page)).camera;
  await page.waitForTimeout(metric('--kb-motion-camera') + 60);
  expect((await state(page)).camera).toEqual(immediate);
});

test('library: two viewers stay independent, destroy cleans up, and bad input refuses', async ({ page }) => {
  await open(page);
  const bundle = await build({
    tsconfig: path.join(root, 'explorer/tsconfig.test.json'),
    entryPoints: [path.join(root, 'explorer/src/index.ts')],
    bundle: true,
    format: 'iife',
    globalName: 'ExplorerLib',
    loader: { '.css': 'text' },
    write: false,
    logLevel: 'silent',
  });
  await page.addScriptTag({ content: bundle.outputFiles[0].text });
  const result = await page.evaluate(() => {
    type Handle = { getState(): State; select(id: string | null): void; destroy(): void };
    const lib = (globalThis as unknown as { ExplorerLib: { mountUniverseViewer(host: HTMLElement, model: unknown): Handle } }).ExplorerLib;
    const model = JSON.parse(document.getElementById('explorer-model')!.textContent!);
    const make = () => {
      const host = document.createElement('div');
      host.style.cssText = 'width:900px;height:700px';
      document.body.append(host);
      return host;
    };
    const a = make();
    const b = make();
    const first = lib.mountUniverseViewer(a, model);
    const second = lib.mountUniverseViewer(b, model);
    first.select('artifact:product-strategy-canvas');
    const independent =
      second.getState().selection.entity === '' && first.getState().selection.entity === 'artifact:product-strategy-canvas';
    first.destroy();
    const cleaned = a.shadowRoot!.childNodes.length === 0;
    second.select('artifact:lean-canvas');
    const stillWorking = second.getState().selection.entity === 'artifact:lean-canvas' && !!b.shadowRoot!.querySelector('.detail');
    const hostile = structuredClone(model);
    hostile.entities[0].label = '<img src=x onerror="document.title=\'pwned\'">';
    hostile.universe.label = '</script><script>document.title="pwned"</script>';
    const c = make();
    lib.mountUniverseViewer(c, hostile);
    const inert = !c.shadowRoot!.querySelector('img') && document.title !== 'pwned';
    const refused: string[] = [];
    for (const [name, broken] of [
      ['schema', { ...model, schema: 'knowledge-bus/explorer-model/99' }],
      ['connection', { ...model, connections: [{ ...model.connections[0], to: 'element:missing' }] }],
      ['wiring', { ...model, wiring: [{ ...model.wiring[0], from: 'frame:missing' }] }],
    ] as const) {
      try {
        lib.mountUniverseViewer(make(), broken);
      } catch {
        refused.push(name);
      }
    }
    return { independent, cleaned, stillWorking, inert, refused };
  });
  expect(result).toEqual({
    independent: true,
    cleaned: true,
    stillWorking: true,
    inert: true,
    refused: ['schema', 'connection', 'wiring'],
  });
});

test('P19 two model concepts draw two marks, in a universe whose vocabulary the curated glyphs have never seen', async ({ page }) => {
  await open(page);
  const bundle = await build({
    tsconfig: path.join(root, 'explorer/tsconfig.test.json'),
    entryPoints: [path.join(root, 'explorer/src/index.ts')],
    bundle: true,
    format: 'iife',
    globalName: 'ExplorerLib',
    loader: { '.css': 'text' },
    write: false,
    logLevel: 'silent',
  });
  await page.addScriptTag({ content: bundle.outputFiles[0].text });
  const measured = await page.evaluate(async (curated: string[]) => {
    const UNSEEN = 'unseen-';
    const model = JSON.parse(document.getElementById('explorer-model')!.textContent!);
    const vocabulary = new Set<string>(
      model.entities
        .filter((entity: { kind: string }) => ['frame', 'factor', 'option'].includes(entity.kind))
        .map((entity: { sourceId: string }) => entity.sourceId),
    );
    const renamed = (value: string) =>
      value
        .split(':')
        .map((segment) => (vocabulary.has(segment) ? UNSEEN + segment : segment))
        .join(':');
    const renamedDeeply = (value: unknown): unknown => {
      if (typeof value === 'string') return renamed(value);
      if (Array.isArray(value)) return value.map(renamedDeeply);
      if (value && typeof value === 'object')
        return Object.fromEntries(Object.entries(value).map(([key, inner]) => [renamed(key), renamedDeeply(inner)]));
      return value;
    };

    const synthetic = structuredClone(model);
    synthetic.guidance = null;
    synthetic.orderingFrameId = renamed(synthetic.orderingFrameId);
    synthetic.universe.ordering_frame = renamed(synthetic.universe.ordering_frame);
    for (const entity of synthetic.entities) {
      entity.id = renamed(entity.id);
      entity.sourceId = renamed(entity.sourceId);
      if (entity.frameId) entity.frameId = renamed(entity.frameId);
      entity.frameValues = renamedDeeply(entity.frameValues);
      entity.raw = renamedDeeply(entity.raw);
    }
    for (const wire of synthetic.wiring) {
      wire.id = renamed(wire.id);
      wire.from = renamed(wire.from);
      wire.to = renamed(wire.to);
      wire.sourceFrameId = renamed(wire.sourceFrameId);
      wire.value = renamedDeeply(wire.value);
      if (wire.targetPair) wire.targetPair = renamedDeeply(wire.targetPair);
    }
    for (const connection of synthetic.connections) {
      connection.from = renamed(connection.from);
      connection.to = renamed(connection.to);
      if (connection.when) connection.when = renamedDeeply(connection.when);
    }
    for (const rule of synthetic.rules) rule.raw = renamedDeeply(rule.raw);
    const syntheticNamesTheCuratedTableKnows = [...vocabulary].map((name) => UNSEEN + name).filter((name) => curated.includes(name));

    const host = document.createElement('div');
    host.style.cssText = 'width:1400px;height:900px';
    document.body.append(host);
    const handle = (
      globalThis as unknown as {
        ExplorerLib: { mountUniverseViewer(host: HTMLElement, model: unknown): { select(id: string): void } };
      }
    ).ExplorerLib.mountUniverseViewer(host, synthetic);
    const shadow = host.shadowRoot!;
    const settled = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));
    await settled(700);

    const markDrawnBy = (svg: Element) => svg.querySelector('text')?.textContent ?? svg.querySelector('path')?.getAttribute('d') ?? '';
    const spelled = (node: Element | null | undefined) => node?.querySelector('span')?.textContent?.trim() ?? '';
    const readable = (value: string) => (value ? value.replaceAll('-', ' ').replace(/^./, (c) => c.toUpperCase()) : '');
    const ordering = synthetic.orderingFrameId.split(':').slice(1).join(':');
    const entityById = new Map<string, any>(synthetic.entities.map((entity: any) => [entity.id, entity]));
    const frameIdSpelled = new Map<string, string>(
      synthetic.entities
        .filter((entity: any) => entity.kind === 'frame' || entity.kind === 'factor')
        .map((entity: any) => [readable(entity.sourceId), entity.id]),
    );
    const frameIdLabelled = new Map<string, string>(
      synthetic.entities
        .filter((entity: any) => entity.kind === 'frame' || entity.kind === 'factor')
        .map((entity: any) => [entity.label, entity.id]),
    );
    const frameNamed = (name: string) => frameIdSpelled.get(name) ?? frameIdLabelled.get(name);
    const optionIdOfValue = new Map<string, string>(
      synthetic.entities
        .filter((entity: any) => entity.kind === 'option')
        .map((entity: any) => [`${entity.frameId} ${entity.sourceId}`, entity.id]),
    );

    const seen: { site: string; concept: string; mark: string }[] = [];
    const record = (site: string, concept: string, mark: string) => seen.push({ site, concept, mark });

    for (const card of shadow.querySelectorAll('.card[data-kind="element"]')) {
      const svg = card.querySelector('.card-order-icon .icon');
      const entity = entityById.get(card.getAttribute('data-id') ?? '');
      const value = String(entity?.frameValues?.[ordering] ?? entity?.raw?.[ordering] ?? '');
      const concept = optionIdOfValue.get(`${synthetic.orderingFrameId} ${value}`);
      if (svg && concept) record('card ordering icon', concept, markDrawnBy(svg));
    }
    for (const slot of shadow.querySelectorAll('.card-frames > span[title]')) {
      const svg = slot.querySelector('.icon');
      const concept = frameNamed((slot as HTMLElement).title);
      if (svg && concept) record('card frame row', concept, markDrawnBy(svg));
    }
    const recordBoundaryHeadings = () => {
      for (const head of shadow.querySelectorAll('.boundary-title[data-boundary]')) {
        const svg = head.querySelector('.icon');
        const concept = entityById.get((head as HTMLElement).dataset.boundary ?? '');
        if (svg && concept) record('boundary heading', concept.id, markDrawnBy(svg));
      }
    };
    recordBoundaryHeadings();

    (shadow.querySelector('.view-tabs button[data-value="frames"]') as HTMLElement | null)?.click();
    await settled(700);
    for (const card of shadow.querySelectorAll('.card')) {
      const svg = card.querySelector('.icon');
      const concept = entityById.get(card.getAttribute('data-id') ?? '');
      if (svg && concept) record('frames view card', concept.id, markDrawnBy(svg));
    }
    recordBoundaryHeadings();

    (shadow.querySelector('.view-tabs button[data-value="elements"]') as HTMLElement | null)?.click();
    await settled(400);
    (shadow.querySelector('.menu-trigger') as HTMLElement | null)?.click();
    await settled(200);
    (shadow.querySelector('.disclosure[data-page="frames"]') as HTMLElement | null)?.click();
    await settled(200);
    for (const chip of shadow.querySelectorAll('.chip')) {
      const svg = chip.querySelector('.icon');
      if (svg) record('view options chips', (chip as HTMLElement).dataset.value ?? '', markDrawnBy(svg));
    }
    for (const label of shadow.querySelectorAll('.field-label')) {
      const svg = label.querySelector('.icon');
      const concept = frameNamed(spelled(label));
      if (svg && concept) record('view options chips', concept, markDrawnBy(svg));
    }

    handle.select(renamed('element:positioning-statement'));
    await settled(800);
    for (const name of shadow.querySelectorAll('.frame-name')) {
      const svg = name.querySelector('.icon');
      const concept = frameNamed(spelled(name));
      if (svg && concept) record('detail frame name', concept, markDrawnBy(svg));
    }

    const sitesMeasured = [...new Set(seen.map((entry) => entry.site))];
    const sitesDrawingFewerMarksThanConcepts = sitesMeasured.filter((site) => {
      const here = seen.filter((entry) => entry.site === site);
      return new Set(here.map((entry) => entry.mark)).size !== new Set(here.map((entry) => entry.concept)).size;
    });
    const markOfConcept = new Map<string, Set<string>>();
    const conceptOfMark = new Map<string, Set<string>>();
    for (const entry of seen) {
      (markOfConcept.get(entry.concept) ?? markOfConcept.set(entry.concept, new Set()).get(entry.concept)!).add(entry.mark);
      (conceptOfMark.get(entry.mark) ?? conceptOfMark.set(entry.mark, new Set()).get(entry.mark)!).add(entry.concept);
    }
    return {
      syntheticNamesTheCuratedTableKnows,
      sitesMeasured,
      sitesDrawingFewerMarksThanConcepts,
      conceptsDrawnWithMoreThanOneMark: [...markOfConcept].filter(([, marks]) => marks.size > 1).map(([concept]) => concept),
      marksDrawnForMoreThanOneConcept: [...conceptOfMark].filter(([, concepts]) => concepts.size > 1).map(([mark]) => mark),
      distinctConcepts: markOfConcept.size,
      distinctMarks: conceptOfMark.size,
      markableButNeverDrawn: synthetic.entities
        .filter(
          (entity: any) =>
            entity.kind === 'frame' ||
            entity.kind === 'factor' ||
            (entity.kind === 'option' && entity.frameId === synthetic.orderingFrameId),
        )
        .map((entity: any) => entity.id)
        .filter((id: string) => !markOfConcept.has(id)),
      conceptsTheSyntheticModelCanMark: synthetic.entities.filter(
        (entity: any) =>
          entity.kind === 'frame' || entity.kind === 'factor' || (entity.kind === 'option' && entity.frameId === synthetic.orderingFrameId),
      ).length,
    };
  }, Object.keys(paths));
  expect(measured.syntheticNamesTheCuratedTableKnows).toEqual([]);
  expect(measured.sitesMeasured.sort()).toEqual([
    'boundary heading',
    'card frame row',
    'card ordering icon',
    'detail frame name',
    'frames view card',
    'view options chips',
  ]);
  expect(measured.sitesDrawingFewerMarksThanConcepts).toEqual([]);
  expect(measured.conceptsDrawnWithMoreThanOneMark).toEqual([]);
  expect(measured.marksDrawnForMoreThanOneConcept).toEqual([]);
  expect(measured.markableButNeverDrawn).toEqual([]);
  expect(measured.distinctConcepts).toBe(measured.conceptsTheSyntheticModelCanMark);
  expect(measured.distinctMarks).toBe(measured.distinctConcepts);
});

test('a selected connection keeps every card count on the map', async ({ page }) => {
  await open(page);
  const before = await explorer(page, '.count').count();
  expect(before, 'a badge must exist to select').toBeGreaterThan(0);
  await explorer(page, '.count').first().click({ force: true });
  await settle(page);
  expect((await state(page)).selection.connection).not.toBe('');
  await expect(explorer(page, '.detail')).toHaveAttribute('aria-label', 'Connection details');
  expect(await explorer(page, '.count').count()).toBe(before);
});

test('edge labels appear only for the selected set, read as authored phrasing, and name both ends', async ({ page }) => {
  await open(page);
  await openMenu(page);
  await explorer(page, '.settings [data-value="relations"]').click();
  await openMenu(page);
  await explorer(page, '.settings [data-value="lines"]').click();
  await page.keyboard.press('Escape');
  await settle(page);
  expect(await explorer(page, '.count').count()).toBe(0);
  await explorer(page, '.card[data-id="element:value-proposition"]').click();
  await settle(page);
  const labels = await explorer(page, '.label').allTextContents();
  expect(labels.length).toBeGreaterThan(0);
  for (const label of labels) expect(label).not.toMatch(/^[a-z]+(-[a-z]+)*$/);
  expect(labels).toContain('Not interchangeable with');
  const cardNames = await explorer(page, '.card .card-title').allTextContents();
  const named = new Set(cardNames.map((name) => name.trim()));
  const titles = await explorer(page, '.label').evaluateAll((nodes) => nodes.map((node) => (node as HTMLElement).title));
  expect(titles.length).toBe(labels.length);
  const unnamed = titles.filter((title) => title.split(' \u00b7 ').filter((end) => named.has(end.trim())).length < 2);
  expect(unnamed, 'labels whose tooltip names both ends of its edge').toEqual([]);
});

test('the detail overlay is named for definitions and never repeats the entity kind', async ({ page }) => {
  await open(page);
  await explorer(page, '.card[data-id="artifact:design-doc"]').click();
  await settle(page);
  const detail = explorer(page, '.detail');
  await expect(detail).toHaveAttribute('aria-label', 'Definition details');
  await expect(detail.locator('.detail-kind')).toHaveCount(0);
  const text = (await detail.textContent()) ?? '';
  expect(text.startsWith('Design docOverviewContentsRelatedHelps you')).toBe(true);
});

test('the map control names the action its next press performs', async ({ page }) => {
  await open(page);
  const map = explorer(page, '.dock button[aria-expanded]');
  await expect(map).toHaveAttribute('title', 'Open Map');
  await map.click();
  await expect(explorer(page, '.minimap')).toBeVisible();
  await expect(map).toHaveAttribute('title', 'Close Map');
  await map.click();
  await expect(explorer(page, '.minimap')).toHaveCount(0);
  await expect(map).toHaveAttribute('title', 'Open Map');
});

test('view options carry no theme control and the theme button shows the current theme', async ({ page }) => {
  await open(page);
  await openMenu(page);
  await expect(explorer(page, '.settings')).not.toContainText('Theme');
  await expect(explorer(page, '.settings [data-value="auto"]')).toHaveCount(0);
  await page.keyboard.press('Escape');
  const theme = explorer(page, '.utilities button[aria-label="Use dark theme"]');
  await expect(theme.locator('path')).toHaveAttribute('d', iconPath('sun'));
  await theme.click();
  const dark = explorer(page, '.utilities button[aria-label="Use light theme"]');
  await expect(dark.locator('path')).toHaveAttribute('d', iconPath('moon'));
});

test('the chrome uses the board glyphs for its menu and its title', async ({ page }) => {
  await open(page);
  await expect(explorer(page, '.menu-trigger path')).toHaveAttribute('d', iconPath('menu'));
  await expect(explorer(page, '.identity-title path')).toHaveAttribute('d', iconPath('chevron-down'));
});

test('a part draws its token value at and above 100% and grows to its limit as you zoom out', async ({ page }) => {
  await open(page);
  const owners = partSelectors;
  const drawnAs: Record<string, string> = {
    size: 'height',
    border: 'borderTopWidth',
    radius: 'borderTopLeftRadius',
    text: 'fontSize',
  };
  const dimensions: Record<string, [string, string][]> = Object.fromEntries(
    Object.entries(authority.parts).map(([part, entries]) => [
      part,
      Object.keys(entries)
        .filter((leaf) => leaf in drawnAs)
        .map((leaf) => [leaf, drawnAs[leaf]] as [string, string]),
    ]),
  );
  const growers = Object.entries(authority.parts)
    .filter(([, entries]) => 'zoom-growth' in entries)
    .map(([part]) => part);
  const declared = (part: string, dimension: string) => metric(`--kb-${part}-${dimension}`);
  const growthCeiling = (part: string) => metric('--kb-zoom-step') ** metric(`--kb-${part}-zoom-growth`);
  const grownOnlyWithItsWholePart = ['border'];
  const growthOf = (leaf: string, node: Record<string, string | number>, factor: number) =>
    grownOnlyWithItsWholePart.includes(leaf) ? (node.grown as number) : factor;
  const shownGrowth = (part: string, node: Record<string, string | number>) =>
    (node.grown as number) * (dimensions[part].some(([leaf]) => leaf === 'text') ? (node.typeSize as number) / declared(part, 'text') : 1);

  const sample = async () => {
    const z = (await state(page)).camera.z;
    const drawn = await page.evaluate(() => {
      const shell = document.getElementById('explorer')!.shadowRoot!;
      const board = new DOMMatrixReadOnly(getComputedStyle(shell.querySelector('.world')!).transform).a;
      const grownBy = (transform: string) => (transform === 'none' ? 1 : new DOMMatrixReadOnly(transform).a);
      return [...shell.querySelectorAll<HTMLElement>('[data-part]')].map((node) => {
        const style = getComputedStyle(node);
        const drawnBox = node.getBoundingClientRect();
        const grown = grownBy(style.transform);
        return {
          part: node.dataset.part!,
          height: drawnBox.height / board,
          grown,
          untransformed: node.offsetHeight,
          borderTopLeftRadius: parseFloat(style.borderTopLeftRadius) * grown,
          borderTopWidth: parseFloat(style.borderTopWidth) * grown,
          fontSize: parseFloat(style.fontSize) * grown,
          typeSize: parseFloat(style.fontSize),
        } as Record<string, string | number>;
      });
    });
    return { z, drawn };
  };

  const measured = new Set<string>();
  const check = async (where: string) => {
    const { z, drawn } = await sample();
    expect(drawn.length, `${where}: nothing declares a part`).toBeGreaterThan(0);
    for (const node of drawn) {
      const part = node.part as string;
      if (!(part in owners)) continue;
      const factor = Math.min(growthCeiling(part), Math.max(1, 1 / z));
      if (growers.includes(part)) {
        measured.add(part);
        expect(shownGrowth(part, node), `${where} z=${z.toFixed(3)} ${part} is drawn growing by its declared bound`).toBeCloseTo(factor, 2);
      }
      expect(
        Math.abs((node.height as number) - (node.untransformed as number) * (node.grown as number)),
        `${where} z=${z.toFixed(3)} ${part} is drawn ${node.height} from a ${node.untransformed} box grown by ${node.grown}`,
      ).toBeLessThanOrEqual(1);
      for (const [dimension, property] of dimensions[part] ?? [])
        expect(node[property] as number, `${where} z=${z.toFixed(3)} ${part}.${dimension}`).toBeCloseTo(
          declared(part, dimension) * growthOf(dimension, node, factor),
          1,
        );
    }
  };

  await explorer(page, '.dock button[aria-label="Zoom in"]').click();
  await explorer(page, '.dock button[aria-label="Zoom in"]').click();
  await settle(page);
  expect((await state(page)).camera.z).toBeGreaterThan(1);
  await check('above 100%');

  await explorer(page, '.dock button[aria-label="Reset zoom to 100%"]').click();
  await settle(page);
  expect((await state(page)).camera.z).toBeCloseTo(1, 2);
  await check('at 100%');

  await explorer(page, '.dock button[aria-label="Fit map to view"]').click();
  await settle(page);
  expect((await state(page)).camera.z).toBeLessThan(1 / growthCeiling('count'));
  await check('below the limit');

  await showConnectionLabels(page);
  await explorer(page, '.dock button[aria-label="Fit map to view"]').click();
  await settle(page);
  await check('below the limit with connection labels');

  expect(
    growers.filter((part) => !measured.has(part)),
    'parts that declare a zoom-growth bound and are drawn nowhere this test looks',
  ).toEqual([]);
});

const DOCK_LADDER = [
  { zoom: 0.15, control: 'Zoom out', clicks: 12 },
  { zoom: 0.4096, control: 'Zoom out', clicks: 4 },
  { zoom: 0.512, control: 'Zoom out', clicks: 3 },
  { zoom: 0.64, control: 'Zoom out', clicks: 2 },
  { zoom: 0.8, control: 'Zoom out', clicks: 1 },
  { zoom: 1, control: 'Zoom in', clicks: 0 },
  { zoom: 1.25, control: 'Zoom in', clicks: 1 },
  { zoom: 1.5625, control: 'Zoom in', clicks: 2 },
  { zoom: 1.8, control: 'Zoom in', clicks: 12 },
];

const worldScale = (page: Page) =>
  page.evaluate(
    () => new DOMMatrixReadOnly(getComputedStyle(document.getElementById('explorer')!.shadowRoot!.querySelector('.world')!).transform).a,
  );

async function clickDockTo(page: Page, rung: (typeof DOCK_LADDER)[number]) {
  await explorer(page, '.dock button[aria-label="Reset zoom to 100%"]').click();
  await settle(page);
  for (let click = 0; click < rung.clicks; click += 1) {
    await explorer(page, `.dock button[aria-label="${rung.control}"]`).click();
    await settle(page);
  }
  expect(await worldScale(page), `${rung.clicks} clicks of ${rung.control}`).toBeCloseTo(rung.zoom, 2);
}

const LABELLED_CARD = 'element:key-activities';

async function showConnectionLabels(page: Page) {
  await open(page);
  await explorer(page, '.dock button[aria-label="Reset zoom to 100%"]').click();
  await settle(page);
  await explorer(page, `.card[data-id="${LABELLED_CARD}"]`).click({ position: { x: 8, y: 5 } });
  await settle(page);
  expect((await state(page)).selection.entity).toBe(LABELLED_CARD);
  expect(await explorer(page, '.label').count()).toBeGreaterThan(0);
}

const drawnLabelText = (page: Page) =>
  page.evaluate(() =>
    [...document.getElementById('explorer')!.shadowRoot!.querySelectorAll<HTMLElement>('.label')].map((node) => {
      const contents = document.createRange();
      contents.selectNodeContents(node);
      const ink = contents.getBoundingClientRect();
      const box = node.getBoundingClientRect();
      return {
        text: node.textContent ?? '',
        fontSize: parseFloat(getComputedStyle(node).fontSize),
        textWidth: ink.width,
        boxWidth: box.width,
        textHeight: ink.height,
        boxHeight: box.height,
      };
    }),
  );

test("a connection label's box is never smaller than the text it draws, at any zoom", async ({ page }) => {
  await showConnectionLabels(page);
  for (const rung of DOCK_LADDER) {
    await clickDockTo(page, rung);
    const drawn = await drawnLabelText(page);
    expect(drawn.length, `z=${rung.zoom}: nothing draws a label`).toBeGreaterThan(0);
    expect(
      drawn.filter((label) => label.textWidth > label.boxWidth + 1 || label.textHeight > label.boxHeight + 1),
      `z=${rung.zoom}`,
    ).toEqual([]);
  }
});

test('a connection label is a plate edged by its declared border, in both themes', async ({ page }) => {
  await showConnectionLabels(page);
  expect(themed('--kb-label-edge', 'light')).not.toBe(themed('--kb-label-edge', 'dark'));
  expect(metric('--kb-label-border')).toBeGreaterThan(0);
  const use = { light: 'Use light theme', dark: 'Use dark theme' };
  for (const theme of ['dark', 'light'] as const) {
    await explorer(page, `.utilities button[aria-label="${use[theme]}"]`).click();
    expect((await state(page)).options.theme).toBe(theme);
    const labels = explorer(page, '.label');
    const drawn = await labels.count();
    expect(drawn, `${theme}: nothing draws a label`).toBeGreaterThan(0);
    for (let index = 0; index < drawn; index += 1) {
      await expect(labels.nth(index)).toHaveCSS('border-top-width', `${metric('--kb-label-border')}px`);
      await expect(labels.nth(index)).toHaveCSS('border-top-style', 'solid');
      await expect(labels.nth(index)).toHaveCSS('border-top-color', themed('--kb-label-edge', theme));
    }
  }
});

const drawnLabelShape = (page: Page) =>
  page.evaluate(() => {
    const shell = document.getElementById('explorer')!.shadowRoot!;
    const board = new DOMMatrixReadOnly(getComputedStyle(shell.querySelector('.world')!).transform).a;
    return [...shell.querySelectorAll<HTMLElement>('.label')].map((node) => ({
      text: node.textContent ?? '',
      widthPerPoint: node.getBoundingClientRect().width / board / parseFloat(getComputedStyle(node).fontSize),
    }));
  });

const SHAPE_DRIFT = 0.01;

test('a connection label keeps its shape as the camera zooms', async ({ page }) => {
  await showConnectionLabels(page);
  const byText = new Map<string, { zoom: number; widthPerPoint: number }[]>();
  for (const rung of DOCK_LADDER) {
    await clickDockTo(page, rung);
    for (const label of await drawnLabelShape(page))
      byText.set(label.text, [...(byText.get(label.text) ?? []), { zoom: rung.zoom, widthPerPoint: label.widthPerPoint }]);
  }
  expect(byText.size, 'no rung of the ladder drew a label').toBeGreaterThan(0);
  for (const [text, seen] of byText) {
    expect(seen.length, `${text} was not drawn at every rung`).toBe(DOCK_LADDER.length);
    const atHundred = seen.find((sample) => sample.zoom === 1)!.widthPerPoint;
    for (const sample of seen)
      expect(
        Math.abs(sample.widthPerPoint / atHundred - 1),
        `${text} at z=${sample.zoom} is ${sample.widthPerPoint} wide per point against ${atHundred} at 100%`,
      ).toBeLessThanOrEqual(SHAPE_DRIFT);
  }
});

const emphasisCounts = (page: Page) =>
  page.evaluate(() => {
    const shell = document.getElementById('explorer')!.shadowRoot!;
    const tally = (values: string[]) =>
      values.reduce<Record<string, number>>((counted, value) => ({ ...counted, [value]: (counted[value] ?? 0) + 1 }), {});
    return {
      cards: tally([...shell.querySelectorAll('.card')].map((c) => (c as HTMLElement).dataset.state ?? '')),
      edges: tally([...shell.querySelectorAll('.wires g[data-emphasis]')].map((g) => (g as SVGElement).dataset.emphasis ?? '')),
    };
  });

async function linesOnArtifacts(page: Page) {
  await open(page);
  await explorer(page, '.view-tabs button').nth(1).click();
  await settle(page);
  await openMenu(page);
  await explorer(page, '.settings [data-value="lines"]').click();
  await page.keyboard.press('Escape');
  await explorer(page, '.dock button[aria-label="Fit map to view"]').click();
  await settle(page);
}

const nubEmphasis = (page: Page) =>
  page.evaluate(() => {
    const shell = document.getElementById('explorer')!.shadowRoot!;
    return [...shell.querySelectorAll('[data-nub]')].reduce<Record<string, number>>(
      (counted, node) => ({
        ...counted,
        [(node as HTMLElement).dataset.emphasis ?? '']: (counted[(node as HTMLElement).dataset.emphasis ?? ''] ?? 0) + 1,
      }),
      {},
    );
  });

test('counts follow the emphasis model: a hover hides none of them, and a count a selection hides is unreachable', async ({ page }) => {
  await countsOnArtifacts(page);
  expect(await nubEmphasis(page)).toEqual({ active: (await nubEmphasis(page)).active });

  await explorer(page, '.card').filter({ hasText: 'Decision brief' }).first().hover({ force: true });
  await expect.poll(async () => (await nubEmphasis(page)).rest ?? 0, 'counts the hover rests').toBeGreaterThan(0);
  const hovered = await nubEmphasis(page);
  expect(hovered.active).toBe(1);
  expect(hovered.hidden ?? 0, 'counts a hover hides').toBe(0);

  await explorer(page, '[data-nub="artifact:decision-brief"] button, button[data-nub="artifact:decision-brief"]')
    .first()
    .click({ force: true });
  await settle(page);
  expect((await state(page)).selection.connection).toBe('nub:artifact:decision-brief');
  const selected = await nubEmphasis(page);
  expect(selected.active).toBe(1);
  expect(selected.rest).toBeGreaterThan(0);
  expect(selected.hidden).toBeGreaterThan(0);
  await expect(explorer(page, '[data-nub][data-emphasis="hidden"]').first()).toHaveCSS('opacity', '0');
  await expect(explorer(page, '[data-nub][data-emphasis="hidden"]').first()).toHaveCSS('pointer-events', 'none');
});

test('an idle board draws every card at rest and every connection at idle strength', async ({ page }) => {
  await linesOnArtifacts(page);
  const rest = light('--kb-connection-opacity-idle');
  const idleBoard = await emphasisCounts(page);
  expect(idleBoard.cards).toEqual({ idle: idleBoard.cards.idle });
  expect(idleBoard.edges).toEqual({ rest: idleBoard.edges.rest });
  await expect(explorer(page, '.wires g[data-emphasis="rest"]').first()).toHaveCSS(
    'opacity',
    String(metric('--kb-connection-opacity-idle')),
  );
  expect(rest).toBeTruthy();
});

test('hovering a card lights its connections and hushes the rest of the board, without claiming to be selected', async ({ page }) => {
  await linesOnArtifacts(page);
  const card = explorer(page, '.card').filter({ hasText: 'Decision brief' }).first();
  await card.hover({ force: true });
  await expect.poll(async () => (await emphasisCounts(page)).edges.active ?? 0, 'connections the hovered card lights').toBeGreaterThan(0);
  const hovered = await emphasisCounts(page);
  expect(hovered.cards.selected ?? 0, 'cards a hover stamps selected').toBe(0);
  expect(hovered.cards.dimmed ?? 0, 'cards a hover dims as a selection would').toBe(0);
  expect(hovered.cards.hushed).toBeGreaterThan(0);
  expect(hovered.edges.rest).toBeGreaterThan(0);
  expect(hovered.edges.hidden ?? 0).toBe(0);
  await expect(card).toHaveAttribute('data-preview', 'true');
  await expect(card).toHaveAttribute('aria-pressed', 'false');
  await expect(explorer(page, '.card[aria-pressed="true"]')).toHaveCount(0);

  const hushed = metric('--kb-opacity-hushed');
  expect(hushed).toBeLessThan(1);
  expect(hushed).toBeGreaterThan(metric('--kb-opacity-dimmed'));
  await expect(explorer(page, '.card[data-state="hushed"] .card-title').first()).toHaveCSS('opacity', String(hushed));
  const surface = (selector: string) =>
    explorer(page, selector)
      .first()
      .evaluate((node) => {
        const style = getComputedStyle(node);
        return { background: style.backgroundColor, border: style.borderBottomColor };
      });
  await expect
    .poll(() => surface('.card[data-kind="artifact"][data-state="hushed"]'), 'a hushed card keeps the surface of a card at rest')
    .toEqual(await surface('.card[data-kind="artifact"][data-state="idle"][data-preview="false"]'));
});

const WHAT_THE_EMPHASIS_TOUCHES: Record<string, string> = {
  card: '.card',
  'card contents': '.card > *',
  connection: 'g[data-connection]',
  wire: 'g[data-connection] .wire',
  label: 'g[data-label]',
  count: '[data-nub]',
};

interface EmphasisBoard {
  board: string;
  arrive: (page: Page) => Promise<void>;
  hover: (page: Page) => Promise<void>;
  kindsAHoverMoves: string[];
}

async function countsOnArtifacts(page: Page) {
  await open(page);
  await explorer(page, '.view-tabs button').nth(1).click();
  await settle(page);
}

const hoverDecisionBrief = (page: Page) => explorer(page, '.card').filter({ hasText: 'Decision brief' }).first().hover({ force: true });

async function hoverAConnectionOfTheSelectedCard(page: Page) {
  const wire = await pointAtAConnectionThePointerCanReach(page, '.wires g[data-emphasis="active"]');
  expect(wire, 'a connection of the selected card must be reachable by the pointer').not.toBeNull();
  await page.mouse.move(wire!.x, wire!.y);
}

const EMPHASIS_BOARDS: EmphasisBoard[] = [
  {
    board: 'a card hovered over lines',
    arrive: linesOnArtifacts,
    hover: hoverDecisionBrief,
    kindsAHoverMoves: ['card', 'card contents', 'connection', 'wire'],
  },
  {
    board: 'a card hovered over counts',
    arrive: countsOnArtifacts,
    hover: hoverDecisionBrief,
    kindsAHoverMoves: ['card', 'card contents', 'count'],
  },
  {
    board: 'a labelled connection of the selected card hovered',
    arrive: connectionHandles,
    hover: hoverAConnectionOfTheSelectedCard,
    kindsAHoverMoves: ['connection', 'wire', 'label'],
  },
];

const rememberEveryComputedStyle = (page: Page) =>
  page.evaluate((kinds) => {
    const shell = document.getElementById('explorer')!.shadowRoot!;
    const remembered = new Map<Element, { kind: string; style: Record<string, string> }>();
    for (const [kind, selector] of Object.entries(kinds))
      for (const node of shell.querySelectorAll(selector)) {
        const computed = getComputedStyle(node);
        const style: Record<string, string> = {};
        for (const property of computed) style[property] = computed.getPropertyValue(property);
        remembered.set(node, { kind, style });
      }
    (window as unknown as { styleAtRest: typeof remembered }).styleAtRest = remembered;
    return remembered.size;
  }, WHAT_THE_EMPHASIS_TOUCHES);

interface MovedByTheHover {
  kind: string;
  elements: number;
  moved: string[];
  snapped: string[];
}

const whatMovedSinceRest = (page: Page): Promise<MovedByTheHover[]> =>
  page.evaluate(() => {
    const remembered = (window as unknown as { styleAtRest: Map<Element, { kind: string; style: Record<string, string> }> }).styleAtRest;
    const seconds = (time: string) => (time.endsWith('ms') ? parseFloat(time) / 1000 : parseFloat(time));
    const longhandsOf = (property: string) => {
      const probe = document.createElement('div');
      probe.style.setProperty(property, 'inherit');
      return [...probe.style];
    };
    const NOT_A_VALUE_OF_ITS_OWN = /^transition-|^animation-|-(?:block|inline)(?:-|$)/;
    const byKind = new Map<string, { elements: number; moved: Set<string>; snapped: Set<string> }>();
    for (const [node, { kind, style }] of remembered) {
      const tally = byKind.get(kind) ?? { elements: 0, moved: new Set<string>(), snapped: new Set<string>() };
      byKind.set(kind, tally);
      tally.elements += 1;
      const computed = getComputedStyle(node);
      const eased = new Set<string>();
      const properties = computed.transitionProperty.split(',').map((name) => name.trim());
      const durations = computed.transitionDuration.split(',').map((time) => seconds(time.trim()));
      properties.forEach((property, index) => {
        if (!(durations[index % durations.length] > 0)) return;
        eased.add(property);
        for (const longhand of longhandsOf(property)) eased.add(longhand);
      });
      for (const property of computed) {
        if (NOT_A_VALUE_OF_ITS_OWN.test(property) || computed.getPropertyValue(property) === style[property]) continue;
        tally.moved.add(property);
        if (!eased.has('all') && !eased.has(property)) tally.snapped.add(property);
      }
    }
    return [...byKind].map(([kind, tally]) => ({
      kind,
      elements: tally.elements,
      moved: [...tally.moved].sort(),
      snapped: [...tally.snapped].sort(),
    }));
  });

const transitionsStillRunning = (page: Page) =>
  page.evaluate(() => document.getElementById('explorer')!.shadowRoot!.getAnimations().length);

for (const { board, arrive, hover, kindsAHoverMoves } of EMPHASIS_BOARDS)
  test(`P17 every property a hover moves, on everything the emphasis touches, is one that element eases: ${board}`, async ({ page }) => {
    await arrive(page);
    await page.mouse.move(OFF_EVERY_CONNECTION.x, OFF_EVERY_CONNECTION.y);
    await expect.poll(() => transitionsStillRunning(page)).toBe(0);
    const atRest = await emphasisCounts(page);
    expect(await rememberEveryComputedStyle(page)).toBeGreaterThan(0);

    await hover(page);
    await expect
      .poll(() => transitionsStillRunning(page), {
        message: 'transitions the hover starts, or the wait below waits for nothing',
        intervals: [10],
      })
      .toBeGreaterThan(0);
    await expect.poll(() => emphasisCounts(page), 'the board answers the hover').not.toEqual(atRest);
    await expect.poll(() => transitionsStillRunning(page), 'transitions still running').toBe(0);

    const moved = await whatMovedSinceRest(page);
    expect
      .soft(
        moved.filter((row) => row.moved.length > 0).map((row) => row.kind),
        `kinds the hover moved: ${JSON.stringify(moved)}`,
      )
      .toEqual(kindsAHoverMoves);
    expect(
      moved.filter((row) => row.snapped.length > 0).map((row) => `${row.kind} snaps ${row.snapped.join(', ')}`),
      'properties a hover moves with no transition of their own',
    ).toEqual([]);
  });

for (const { board, arrive, hover, kindsAHoverMoves } of EMPHASIS_BOARDS)
  test(`with reduced motion nothing the emphasis touches takes any time to change: ${board}`, async ({ page }) => {
    const slowest = () =>
      page.evaluate((kinds) => {
        const shell = document.getElementById('explorer')!.shadowRoot!;
        const seconds = (time: string) => (time.endsWith('ms') ? parseFloat(time) / 1000 : parseFloat(time));
        return Object.entries(kinds).map(([kind, selector]) => {
          const nodes = [...shell.querySelectorAll(selector)];
          const times = nodes.flatMap((node) =>
            getComputedStyle(node)
              .transitionDuration.split(',')
              .map((time) => seconds(time.trim())),
          );
          return { kind, elements: nodes.length, slowest: Math.max(0, ...times) };
        });
      }, WHAT_THE_EMPHASIS_TOUCHES);
    await arrive(page);
    const moving = (await slowest()).filter((row) => row.elements > 0);
    const drawn = moving.map((row) => row.kind);
    expect(
      kindsAHoverMoves.filter((kind) => !drawn.includes(kind)),
      'kinds this hover moves that the board does not draw',
    ).toEqual([]);
    expect(
      moving.filter((row) => !(row.slowest > 0)).map((row) => row.kind),
      `kinds that take no time even when motion is allowed, so stillness would prove nothing: ${JSON.stringify(moving)}`,
    ).toEqual([]);
    await page.emulateMedia({ reducedMotion: 'reduce' });
    const still = (await slowest()).filter((row) => row.elements > 0);
    expect(still.map((row) => `${row.kind}:${row.elements}`)).toEqual(moving.map((row) => `${row.kind}:${row.elements}`));
    expect(
      still.filter((row) => row.slowest > 0).map((row) => `${row.kind} still takes ${row.slowest}s`),
      'kinds that still take time under reduced motion',
    ).toEqual([]);
    const atRest = await emphasisCounts(page);
    await page.mouse.move(OFF_EVERY_CONNECTION.x, OFF_EVERY_CONNECTION.y);
    await hover(page);
    await expect.poll(() => emphasisCounts(page), 'the dwell is intent, not animation, so the hover still lands').not.toEqual(atRest);
  });

test('selecting a card hides the connections that are not its own', async ({ page }) => {
  await linesOnArtifacts(page);
  const card = explorer(page, '.card').filter({ hasText: 'Decision brief' }).first();
  await card.click({ force: true, position: { x: 12, y: 8 } });
  await settle(page);
  const selected = await emphasisCounts(page);
  expect(selected.cards.selected).toBe(1);
  expect(selected.edges.hidden).toBeGreaterThan(0);
  expect(selected.edges.rest ?? 0).toBe(0);
  await expect(explorer(page, '.wires g[data-emphasis="active"]').first()).toHaveCSS('opacity', '1');
  await expect(explorer(page, '.wires g[data-emphasis="hidden"]').first()).toHaveCSS('opacity', '0');
});

const CENTRELINE_FRACTIONS = [0.25, 0.5, 0.75];

test('a hidden connection takes no pointer, and a centreline click lands on whatever is visible there', async ({ page }) => {
  await linesOnArtifacts(page);
  await explorer(page, '.card')
    .filter({ hasText: 'Decision brief' })
    .first()
    .click({ force: true, position: { x: 12, y: 8 } });
  await settle(page);
  const hidden = explorer(page, '.wires g[data-emphasis="hidden"]').first();
  await expect(hidden).toHaveCSS('pointer-events', 'none');
  const hiddenHitPaths = await page.evaluate((fractions) => {
    const shell = document.getElementById('explorer')!.shadowRoot!;
    const measured = { groups: 0, hitPathsTakingPointerEvents: 0, centrelinePointsOnScreen: 0, centrelinePointsThatMetTheirOwnGroup: 0 };
    for (const group of shell.querySelectorAll<SVGGElement>('.wires g[data-emphasis="hidden"]')) {
      const hit = group.querySelector<SVGPathElement>('.wire-hit')!;
      measured.groups += 1;
      if (getComputedStyle(hit).pointerEvents !== 'none') measured.hitPathsTakingPointerEvents += 1;
      for (const fraction of fractions) {
        const point = hit.getPointAtLength(hit.getTotalLength() * fraction).matrixTransform(hit.getScreenCTM()!);
        if (point.x <= 0 || point.y <= 0 || point.x >= window.innerWidth || point.y >= window.innerHeight) continue;
        measured.centrelinePointsOnScreen += 1;
        if (shell.elementFromPoint(point.x, point.y)?.closest('g[data-connection]') === group)
          measured.centrelinePointsThatMetTheirOwnGroup += 1;
      }
    }
    return measured;
  }, CENTRELINE_FRACTIONS);
  expect(hiddenHitPaths.groups).toBeGreaterThan(0);
  expect(hiddenHitPaths.centrelinePointsOnScreen).toBe(hiddenHitPaths.groups * CENTRELINE_FRACTIONS.length);
  expect(hiddenHitPaths).toMatchObject({ hitPathsTakingPointerEvents: 0, centrelinePointsThatMetTheirOwnGroup: 0 });
  const hiddenPath = await hidden.getAttribute('data-connection');
  expect(hiddenPath).toBeTruthy();
  const spot = await hidden.locator('.wire-hit').evaluate((path) => {
    const svgPath = path as SVGPathElement;
    const point = svgPath.getPointAtLength(svgPath.getTotalLength() / 2);
    const screen = point.matrixTransform(svgPath.getScreenCTM()!);
    const onScreen = screen.x > 0 && screen.y > 0 && screen.x < window.innerWidth && screen.y < window.innerHeight;
    const shell = document.getElementById('explorer')!.shadowRoot!;
    const topmost = shell.elementFromPoint(screen.x, screen.y)?.closest('g[data-connection]') as SVGGElement | null;
    return { x: screen.x, y: screen.y, onScreen, topmostConnection: topmost?.dataset.connection ?? null };
  });
  expect(spot.onScreen).toBe(true);
  await page.mouse.move(spot.x, spot.y);
  await page.waitForTimeout(300);
  expect(await explorer(page, '.wires g[data-emphasis="active"]').count()).toBeGreaterThan(0);
  await expect(hidden).toHaveAttribute('data-emphasis', 'hidden');
  await page.mouse.click(spot.x, spot.y);
  await settle(page);
  const clickedConnection = (await state(page)).selection.connection;
  expect(clickedConnection).not.toBe(hiddenPath);
  if (spot.topmostConnection === null) expect(clickedConnection).toBe('');
  else expect(clickedConnection).toBe(spot.topmostConnection);
});

const POINTER_SAMPLES = 60;

async function pointAtAConnectionThePointerCanReach(page: Page, selector: string) {
  return page.evaluate(
    ({ selector, samples }) => {
      const shell = document.getElementById('explorer')!.shadowRoot!;
      for (const group of shell.querySelectorAll<SVGGElement>(selector)) {
        const hit = group.querySelector<SVGPathElement>('.wire-hit')!;
        const length = hit.getTotalLength();
        const matrix = hit.getScreenCTM()!;
        for (let sample = 1; sample < samples; sample += 1) {
          const onCentreline = hit.getPointAtLength((length * sample) / samples).matrixTransform(matrix);
          if (shell.elementFromPoint(onCentreline.x, onCentreline.y) === hit)
            return { connection: group.dataset.connection ?? '', x: onCentreline.x, y: onCentreline.y };
        }
      }
      return null;
    },
    { selector, samples: POINTER_SAMPLES },
  );
}

const connectionStrengths = (page: Page) =>
  page.evaluate(() => {
    const shell = document.getElementById('explorer')!.shadowRoot!;
    return [...shell.querySelectorAll<SVGGElement>('.wires g[data-emphasis]')].map((group) => ({
      connection: group.dataset.connection ?? '',
      emphasis: group.dataset.emphasis ?? '',
      opacity: group.style.opacity,
      stroke: group.querySelector<SVGPathElement>('.wire')!.style.strokeWidth,
    }));
  });

const labelStrengths = (page: Page) =>
  page.evaluate(() => {
    const shell = document.getElementById('explorer')!.shadowRoot!;
    return [...shell.querySelectorAll<SVGGElement>('[data-label]')].map((group) => ({
      label: group.dataset.label ?? '',
      opacity: group.style.opacity,
    }));
  });

const cardStates = (page: Page) =>
  page.evaluate(() => {
    const shell = document.getElementById('explorer')!.shadowRoot!;
    return [...shell.querySelectorAll<HTMLElement>('.card')].map((card) => `${card.dataset.id ?? ''}=${card.dataset.state ?? ''}`);
  });

async function emphasisedRelationLines(page: Page) {
  await open(page);
  await explorer(page, '.view-tabs button').nth(1).click();
  await settle(page);
  await openMenu(page);
  await explorer(page, '.settings [data-value="relations"]').click();
  await openMenu(page);
  await explorer(page, '.settings [data-value="lines"]').click();
  await openMenu(page);
  await explorer(page, '.settings [data-page="emphasis"]').click();
  await explorer(page, '.settings .chip').nth(1).click();
  await page.keyboard.press('Escape');
  await explorer(page, '.dock button[aria-label="Fit map to view"]').click();
  await settle(page);
  expect((await state(page)).options.emphasis).toHaveLength(1);
}

const selectDecisionBrief = async (page: Page) => {
  await explorer(page, '.card')
    .filter({ hasText: 'Decision brief' })
    .first()
    .click({ force: true, position: { x: 12, y: 8 } });
  await settle(page);
};

test('hovering one connection of the selected card lights it and rests its siblings', async ({ page }) => {
  await linesOnArtifacts(page);
  await selectDecisionBrief(page);
  const selected = await emphasisCounts(page);
  const selectedCards = await cardStates(page);
  const camera = (await state(page)).camera;
  expect(selected.edges.active).toBeGreaterThan(1);

  const wire = await pointAtAConnectionThePointerCanReach(page, '.wires g[data-emphasis="active"]');
  expect(wire, 'a connection of the selected card must be reachable by the pointer').not.toBeNull();
  await page.mouse.move(wire!.x, wire!.y);
  await page.waitForTimeout(300);

  expect(await cardStates(page)).toEqual(selectedCards);
  const hovered = await emphasisCounts(page);
  expect(hovered.edges.active).toBe(1);
  expect(hovered.edges.rest).toBe(selected.edges.active - 1);
  expect(hovered.edges.hidden).toBe(selected.edges.hidden);
  await expect(explorer(page, '.wires g[data-emphasis="active"]')).toHaveAttribute('data-connection', wire!.connection);
  expect((await state(page)).selection.entity).toBe('artifact:decision-brief');
  expect((await state(page)).camera).toEqual(camera);

  const legible = (await labelStrengths(page)).filter((label) => label.opacity === '1');
  expect(legible.map((label) => label.label)).toEqual([wire!.connection]);

  const sibling = await pointAtAConnectionThePointerCanReach(page, '.wires g[data-emphasis="rest"]');
  expect(sibling, 'a rested sibling must still be reachable, or the selection is a trap').not.toBeNull();
  await page.mouse.move(sibling!.x, sibling!.y);
  await page.waitForTimeout(300);
  await expect(explorer(page, '.wires g[data-emphasis="active"]')).toHaveAttribute('data-connection', sibling!.connection);
});

test('an emphasised connection holds full strength on an idle board and gives it up inside a selection', async ({ page }) => {
  await emphasisedRelationLines(page);
  const preview = String(metric('--kb-connection-stroke-preview'));
  const idle = String(metric('--kb-connection-opacity-idle'));

  const idleBoard = (await connectionStrengths(page)).filter((row) => row.stroke === preview);
  expect(idleBoard.length).toBeGreaterThan(0);
  expect([...new Set(idleBoard.map((row) => row.opacity))]).toEqual(['1']);

  await selectDecisionBrief(page);
  const wire = await pointAtAConnectionThePointerCanReach(page, '.wires g[data-emphasis="active"]');
  expect(wire, 'an emphasised connection of the selected card must be reachable by the pointer').not.toBeNull();
  await page.mouse.move(wire!.x, wire!.y);
  await page.waitForTimeout(300);

  const rows = await connectionStrengths(page);
  expect(rows.find((row) => row.connection === wire!.connection)).toMatchObject({ emphasis: 'active', opacity: '1' });
  const emphasisedSiblings = rows.filter((row) => row.emphasis === 'rest' && row.stroke === preview);
  expect(emphasisedSiblings.length).toBeGreaterThan(0);
  expect([...new Set(emphasisedSiblings.map((row) => row.opacity))]).toEqual([idle]);
});

type CentrelineMeeting =
  | 'own-hit'
  | 'other-hit'
  | 'painted-wire'
  | 'painted-arrowhead'
  | 'painted-leader'
  | 'hidden-connection'
  | 'not-a-connection'
  | 'off-viewport';

interface CentrelineSample {
  connection: string;
  on: 'route' | 'arrowhead' | 'label-anchor';
  x: number;
  y: number;
  meets: CentrelineMeeting;
  met: string;
  own: boolean;
  leaderLength: number;
}

const OFF_EVERY_CONNECTION = { x: 1, y: 1 };

const centrelineSamples = (page: Page): Promise<CentrelineSample[]> =>
  page.evaluate((fractions) => {
    const shell = document.getElementById('explorer')!.shadowRoot!;
    const out: CentrelineSample[] = [];
    const meet = (group: SVGGElement, on: CentrelineSample['on'], x: number, y: number, leaderLength = 0) => {
      const inView = x > 0 && y > 0 && x < window.innerWidth && y < window.innerHeight;
      const top = inView ? shell.elementFromPoint(x, y) : null;
      const owner = top?.closest<SVGGElement>('g[data-connection]') ?? null;
      const leaderOf = top?.classList.contains('leader') ? (top.closest<SVGGElement>('g[data-label]')?.dataset.label ?? '') : null;
      const meets: CentrelineMeeting = !inView
        ? 'off-viewport'
        : leaderOf !== null
          ? 'painted-leader'
          : !top || !owner
            ? 'not-a-connection'
            : owner.dataset.emphasis === 'hidden'
              ? 'hidden-connection'
              : top.classList.contains('wire')
                ? 'painted-wire'
                : top.classList.contains('arrowhead')
                  ? 'painted-arrowhead'
                  : owner === group
                    ? 'own-hit'
                    : 'other-hit';
      out.push({
        connection: group.dataset.connection ?? '',
        on,
        x,
        y,
        meets,
        met: top ? (top.getAttribute('class') ?? top.tagName) : '',
        own: owner === group || leaderOf === group.dataset.connection,
        leaderLength,
      });
    };
    const leaders = new Map(
      [...shell.querySelectorAll<SVGGElement>('.labels-layer g[data-label]')].map((label) => [
        label.dataset.label ?? '',
        label.querySelector<SVGPathElement>('.leader')!,
      ]),
    );
    for (const group of shell.querySelectorAll<SVGGElement>('.wires g[data-connection]')) {
      if (group.dataset.emphasis === 'hidden') continue;
      const hit = group.querySelector<SVGPathElement>('.wire-hit')!;
      const length = hit.getTotalLength();
      const matrix = hit.getScreenCTM()!;
      for (const fraction of fractions) {
        const point = hit.getPointAtLength(length * fraction).matrixTransform(matrix);
        meet(group, 'route', point.x, point.y);
      }
      const head = group.querySelector<SVGPolygonElement>('.arrowhead');
      if (head) {
        const box = head.getBoundingClientRect();
        meet(group, 'arrowhead', box.x + box.width / 2, box.y + box.height / 2);
      }
      const leader = leaders.get(group.dataset.connection ?? '');
      if (leader) {
        const anchor = leader.getPointAtLength(0).matrixTransform(leader.getScreenCTM()!);
        meet(group, 'label-anchor', anchor.x, anchor.y, leader.getTotalLength());
      }
    }
    return out;
  }, CENTRELINE_FRACTIONS);

const aFreshHoverPoll = () => [metric('--kb-motion-dwell'), 20];

const activeConnections = (page: Page) =>
  page.evaluate(() =>
    [...document.getElementById('explorer')!.shadowRoot!.querySelectorAll<SVGGElement>('.wires g[data-emphasis="active"]')].map(
      (group) => group.dataset.connection ?? '',
    ),
  );

async function relationLinesOnArtifacts(page: Page) {
  await open(page);
  await explorer(page, '.view-tabs button').nth(1).click();
  await settle(page);
  await openMenu(page);
  await explorer(page, '.settings [data-value="relations"]').click();
  await openMenu(page);
  await explorer(page, '.settings [data-value="lines"]').click();
  await page.keyboard.press('Escape');
  await explorer(page, '.dock button[aria-label="Fit map to view"]').click();
  await settle(page);
}

async function connectionHandles(page: Page) {
  const bundle = await build({
    tsconfig: path.join(root, 'explorer/tsconfig.test.json'),
    entryPoints: [path.join(root, 'explorer/test/browser/connection-handles.ts')],
    bundle: true,
    format: 'iife',
    loader: { '.css': 'text' },
    write: false,
    logLevel: 'silent',
  });
  await page.setContent('<style>html,body,#explorer{margin:0;width:100%;height:100%}</style><div id="explorer"></div>');
  await page.addScriptTag({ content: bundle.outputFiles[0].text });
}

interface CentrelineBoard {
  board: string;
  arrive: (page: Page) => Promise<void>;
  drawsArrowheads: boolean;
  drawsLeaders: boolean;
}

const CENTRELINE_BOARDS: CentrelineBoard[] = [
  { board: 'composition lines, idle', arrive: linesOnArtifacts, drawsArrowheads: false, drawsLeaders: false },
  {
    board: 'composition lines, Decision brief selected',
    arrive: async (page) => {
      await linesOnArtifacts(page);
      await selectDecisionBrief(page);
    },
    drawsArrowheads: false,
    drawsLeaders: false,
  },
  { board: 'relation lines, idle', arrive: relationLinesOnArtifacts, drawsArrowheads: true, drawsLeaders: false },
  {
    board: 'component: offset and inline connection handles',
    arrive: connectionHandles,
    drawsArrowheads: true,
    drawsLeaders: true,
  },
];

for (const { board, arrive, drawsArrowheads, drawsLeaders } of CENTRELINE_BOARDS)
  test(`P14 the pointer on a drawn centreline meets a hit path, never a painted mark: ${board}`, async ({ page }) => {
    test.slow();
    await arrive(page);
    await page.mouse.move(OFF_EVERY_CONNECTION.x, OFF_EVERY_CONNECTION.y);
    const samples = await centrelineSamples(page);
    const measured = samples.filter((sample) => sample.meets !== 'off-viewport' && sample.meets !== 'not-a-connection');
    const tally = samples.reduce<Record<string, number>>((counted, sample) => {
      const key = `${sample.on}:${sample.meets}${sample.meets.startsWith('painted') ? (sample.own ? ':own' : ':other') : ''}`;
      return { ...counted, [key]: (counted[key] ?? 0) + 1 };
    }, {});
    const on = (kind: CentrelineSample['on'], rows: CentrelineSample[]) => rows.filter((sample) => sample.on === kind);
    expect.soft(on('route', samples).length, `route samples drawn: ${JSON.stringify(tally)}`).toBeGreaterThan(0);
    expect.soft(on('arrowhead', samples).length > 0, `arrowhead samples drawn: ${JSON.stringify(tally)}`).toBe(drawsArrowheads);
    const drawnLeaderAnchors = on('label-anchor', measured).filter((sample) => sample.leaderLength > 0);
    expect
      .soft(drawnLeaderAnchors.length > 0, `label anchors measured at the wire end of a leader that has length: ${JSON.stringify(tally)}`)
      .toBe(drawsLeaders);
    if (drawsLeaders) expect(drawnLeaderAnchors.map((sample) => sample.meets)).toEqual(['own-hit']);
    expect
      .soft(
        samples.filter((sample) => sample.meets === 'off-viewport').length,
        `samples the fitted camera left off the viewport: ${JSON.stringify(tally)}`,
      )
      .toBe(0);

    const painted = measured.filter(
      (sample) => sample.meets === 'painted-wire' || sample.meets === 'painted-arrowhead' || sample.meets === 'painted-leader',
    );
    expect
      .soft(
        painted.length,
        `painted marks took the pointer, first ${painted
          .slice(0, 3)
          .map((sample) => `${sample.on} of ${sample.connection} met .${sample.met}`)
          .join('; ')} in ${JSON.stringify(tally)}`,
      )
      .toBe(0);
    expect.soft(measured.filter((sample) => sample.meets === 'hidden-connection')).toEqual([]);

    const own = measured.filter((sample) => sample.meets === 'own-hit');
    expect.soft(on('route', own).length, `route samples that met their own hit path: ${JSON.stringify(tally)}`).toBeGreaterThan(0);
    expect
      .soft(on('arrowhead', own).length > 0, `arrowhead samples that met their own hit path: ${JSON.stringify(tally)}`)
      .toBe(drawsArrowheads);
    expect(
      await page.evaluate(
        ({ x, y }) => !!document.getElementById('explorer')!.shadowRoot!.elementFromPoint(x, y)?.closest('g[data-connection]'),
        OFF_EVERY_CONNECTION,
      ),
    ).toBe(false);
    const parked = await activeConnections(page);
    const oneProbePerHandleShape = new Map<CentrelineSample['on'], CentrelineSample>();
    for (const sample of own) if (!oneProbePerHandleShape.has(sample.on)) oneProbePerHandleShape.set(sample.on, sample);
    for (const sample of oneProbePerHandleShape.values()) {
      await parkThePointerOffEveryConnection(page, parked);
      await page.mouse.move(sample.x, sample.y);
      await expect
        .poll(() => activeConnections(page), { message: `${sample.on} of ${sample.connection}`, intervals: aFreshHoverPoll() })
        .toEqual([sample.connection]);
    }
  });

test("a click on the drawn centreline of a selected card's own connection selects that connection", async ({ page }) => {
  await linesOnArtifacts(page);
  await selectDecisionBrief(page);
  expect((await state(page)).selection).toEqual({ entity: 'artifact:decision-brief', connection: '', option: '' });
  await page.mouse.move(OFF_EVERY_CONNECTION.x, OFF_EVERY_CONNECTION.y);
  const aimed = (await centrelineSamples(page)).find(
    (sample) => sample.on === 'route' && sample.own && (sample.meets === 'own-hit' || sample.meets === 'painted-wire'),
  );
  expect(aimed, "a centreline point where the selected card's own connection is topmost").toBeDefined();
  await page.mouse.click(aimed!.x, aimed!.y);
  await settle(page);
  expect((await state(page)).selection).toEqual({ entity: '', connection: aimed!.connection, option: '' });
});

interface BrowserRect {
  x: number;
  y: number;
  width: number;
  height: number;
}

const drawnCardAndLabelBoxes = (page: Page): Promise<{ cards: BrowserRect[]; labels: BrowserRect[] }> =>
  page.evaluate(() => {
    const shell = document.getElementById('explorer')!.shadowRoot!;
    const rect = (r: DOMRect): { x: number; y: number; width: number; height: number } => ({
      x: r.x,
      y: r.y,
      width: r.width,
      height: r.height,
    });
    const cards = [...shell.querySelectorAll<HTMLElement>('.card')].map((card) => rect(card.getBoundingClientRect()));
    const labels = [...shell.querySelectorAll<SVGGElement>('.labels-layer g[data-label]')]
      .filter((group) => group.style.opacity !== '0')
      .map((group) => rect(group.querySelector<HTMLButtonElement>('button.label')!.getBoundingClientRect()));
    return { cards, labels };
  });

test('P18 canonical product-development: selected composition labels avoid cards and each other through dock steps', async ({ page }) => {
  test.slow();
  await open(page);
  await page.evaluate(() => {
    const viewer = (
      document.getElementById('explorer') as unknown as {
        explorerViewer: { setViewOptions(patch: Partial<State['options']>): void; select(id: string): void };
      }
    ).explorerViewer;
    viewer.setViewOptions({ view: 'elements', group: false, display: 'lines' });
    viewer.select('artifact:decision-brief');
  });
  await settle(page);
  const checkNoOverlap = async (moment: string) => {
    const { cards, labels } = await drawnCardAndLabelBoxes(page);
    expect(labels.length, `${moment}: nothing draws a label`).toBeGreaterThan(0);
    const onCard = labels.filter((label) => cards.some((card) => overlaps(label, card)));
    expect(onCard, `${moment}: labels overlapping a card`).toEqual([]);
    const onAnother: [number, number][] = [];
    for (let i = 0; i < labels.length; i += 1)
      for (let j = i + 1; j < labels.length; j += 1) if (overlaps(labels[i], labels[j])) onAnother.push([i, j]);
    expect(onAnother, `${moment}: labels overlapping another label`).toEqual([]);
  };
  await checkNoOverlap('framed on the selection');
  await explorer(page, '.dock button[aria-label="Fit map to view"]').click();
  await settle(page);
  await checkNoOverlap('after fit');
  await explorer(page, '.dock button[aria-label="Reset zoom to 100%"]').click();
  await settle(page);
  await checkNoOverlap('back to 100%');
});

interface ReachableLabel {
  connection: string;
  x: number;
  y: number;
  leaderLength: number;
  topmostAtItsCentre: 'own-label' | 'other-label' | 'something-else' | 'off-viewport';
  onItsOwnWire: { x: number; y: number } | null;
}

const LABEL_WIRE_SAMPLES = 200;
const SWEEP_STEPS = 16;

const drawnLabels = (page: Page): Promise<ReachableLabel[]> =>
  page.evaluate((samples) => {
    const shell = document.getElementById('explorer')!.shadowRoot!;
    const inView = (x: number, y: number) => x > 0 && y > 0 && x < window.innerWidth && y < window.innerHeight;
    return [...shell.querySelectorAll<SVGGElement>('.labels-layer g[data-label]')]
      .filter((group) => group.style.opacity !== '0')
      .map((group) => {
        const button = group.querySelector<HTMLButtonElement>('button.label')!;
        const box = button.getBoundingClientRect();
        const x = box.x + box.width / 2;
        const y = box.y + box.height / 2;
        const top = inView(x, y) ? shell.elementFromPoint(x, y) : null;
        const hit = shell.querySelector<SVGPathElement>(`.wires g[data-connection="${CSS.escape(group.dataset.label ?? '')}"] .wire-hit`);
        let onItsOwnWire: { x: number; y: number; away: number } | null = null;
        if (hit) {
          const length = hit.getTotalLength();
          const matrix = hit.getScreenCTM()!;
          for (let sample = 1; sample < samples; sample += 1) {
            const point = hit.getPointAtLength((length * sample) / samples).matrixTransform(matrix);
            if (!inView(point.x, point.y) || shell.elementFromPoint(point.x, point.y) !== hit) continue;
            const away = Math.hypot(point.x - x, point.y - y);
            if (!onItsOwnWire || away < onItsOwnWire.away) onItsOwnWire = { x: point.x, y: point.y, away };
          }
        }
        return {
          connection: group.dataset.label ?? '',
          x,
          y,
          leaderLength: group.querySelector<SVGPathElement>('.leader')!.getTotalLength(),
          topmostAtItsCentre: !top
            ? ('off-viewport' as const)
            : top === button
              ? ('own-label' as const)
              : top.classList.contains('label')
                ? ('other-label' as const)
                : ('something-else' as const),
          onItsOwnWire: onItsOwnWire && { x: onItsOwnWire.x, y: onItsOwnWire.y },
        };
      });
  }, LABEL_WIRE_SAMPLES);

const pointerMeets = (page: Page, connection: string, x: number, y: number) =>
  page.evaluate(
    ({ connection, x, y }) => {
      const shell = document.getElementById('explorer')!.shadowRoot!;
      const top = shell.elementFromPoint(x, y);
      const handle = top?.classList.contains('label')
        ? top.closest<SVGGElement>('g[data-label]')?.dataset.label
        : top?.classList.contains('wire-hit')
          ? top.closest<SVGGElement>('g[data-connection]')?.dataset.connection
          : undefined;
      return {
        aHandleOfTheConnection: handle === connection,
        active: [...shell.querySelectorAll<SVGGElement>('.wires g[data-emphasis="active"]')].map((group) => group.dataset.connection ?? ''),
      };
    },
    { connection, x, y },
  );

async function parkThePointerOffEveryConnection(page: Page, parked: string[]) {
  await page.mouse.move(OFF_EVERY_CONNECTION.x, OFF_EVERY_CONNECTION.y);
  await expect
    .poll(() => activeConnections(page), { message: 'the parked pointer lights nothing of its own', intervals: aFreshHoverPoll() })
    .toEqual(parked);
}

const startWatchingEveryConnectionsEmphasis = (page: Page) =>
  page.evaluate(() => {
    const shell = document.getElementById('explorer')!.shadowRoot!;
    const seen: string[] = [];
    const watcher = new MutationObserver((changes) => {
      for (const change of changes) {
        const group = change.target as SVGGElement;
        if (group.dataset.emphasis !== change.oldValue)
          seen.push(`${group.dataset.connection}: ${change.oldValue} to ${group.dataset.emphasis}`);
      }
    });
    for (const group of shell.querySelectorAll('g[data-connection]'))
      watcher.observe(group, { attributes: true, attributeFilter: ['data-emphasis'], attributeOldValue: true });
    (window as unknown as { emphasisChanges: string[] }).emphasisChanges = seen;
  });

const emphasisChangesOnceThePointerHasRested = async (page: Page) => {
  const movedAt = await page.evaluate(() => performance.now());
  await expect
    .poll(() => page.evaluate((since) => performance.now() - since, movedAt), { intervals: aFreshHoverPoll() })
    .toBeGreaterThan(metric('--kb-motion-dwell') * 2);
  return page.evaluate(() => (window as unknown as { emphasisChanges: string[] }).emphasisChanges.splice(0));
};

test("P16 the pointer on a connection's label lights that connection and only that one", async ({ page }) => {
  await connectionHandles(page);
  await page.mouse.move(OFF_EVERY_CONNECTION.x, OFF_EVERY_CONNECTION.y);
  const parked = await activeConnections(page);
  const parkedCounts = await emphasisCounts(page);
  expect(parked).toEqual(['offset', 'inline']);

  const labels = await drawnLabels(page);
  const reachable = labels.filter((label) => label.topmostAtItsCentre === 'own-label');
  expect(reachable.map((label) => label.connection)).toEqual(['offset', 'inline']);

  for (const label of reachable) {
    await parkThePointerOffEveryConnection(page, parked);
    await page.mouse.move(label.x, label.y);
    const met = await pointerMeets(page, label.connection, label.x, label.y);
    expect.soft(met.aHandleOfTheConnection, `the pointer is on the label of ${label.connection}`).toBe(true);
    await expect.poll(() => activeConnections(page), { intervals: aFreshHoverPoll() }).toEqual([label.connection]);
    const counts = await emphasisCounts(page);
    expect
      .soft(counts.edges.hidden ?? 0, `hidden connections while on the label of ${label.connection}`)
      .toBe(parkedCounts.edges.hidden ?? 0);
    expect.soft(counts.edges.rest, `rested siblings of ${label.connection}`).toBe(parked.length - 1);
    const legible = (await labelStrengths(page)).filter((row) => row.opacity === '1').map((row) => row.label);
    expect.soft(legible, `labels at full strength while on the label of ${label.connection}`).toEqual([label.connection]);
  }
  await parkThePointerOffEveryConnection(page, parked);
  await page.mouse.click(reachable[0].x, reachable[0].y);
  await expect(page.locator('#explorer')).toHaveAttribute('data-selected-connection', reachable[0].connection);
});

test('the hover holds while the pointer moves from a lit wire onto its own label, and back', async ({ page }) => {
  await connectionHandles(page);
  await page.mouse.move(OFF_EVERY_CONNECTION.x, OFF_EVERY_CONNECTION.y);
  const parked = await activeConnections(page);
  const label = (await drawnLabels(page)).find((label) => label.connection === 'inline')!;
  expect([label.topmostAtItsCentre, label.leaderLength, !!label.onItsOwnWire]).toEqual(['own-label', 0, true]);
  const wire = label.onItsOwnWire!;
  await parkThePointerOffEveryConnection(page, parked);
  await page.mouse.move(wire.x, wire.y);
  await expect.poll(() => activeConnections(page)).toEqual([label.connection]);
  await startWatchingEveryConnectionsEmphasis(page);
  for (const { from, to, name } of [
    { from: wire, to: label, name: 'wire to label' },
    { from: label, to: wire, name: 'label to wire' },
  ]) {
    for (let step = 1; step <= SWEEP_STEPS; step += 1) {
      const x = from.x + ((to.x - from.x) * step) / SWEEP_STEPS;
      const y = from.y + ((to.y - from.y) * step) / SWEEP_STEPS;
      await page.mouse.move(x, y);
      expect(await pointerMeets(page, label.connection, x, y), `${name} step ${step}`).toEqual({
        aHandleOfTheConnection: true,
        active: [label.connection],
      });
    }
    expect(await emphasisChangesOnceThePointerHasRested(page), `${name} must never change emphasis`).toEqual([]);
  }
});

interface SampledBox {
  key: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

const GROUND = '--kb-ground-frame';
const WIRE_SAMPLE_SPAN = 5;
const WIRE_SAMPLES_PER_ROUTE = 7;

const countBadgeBoxes = (page: Page): Promise<SampledBox[]> =>
  page.evaluate(() =>
    [...document.getElementById('explorer')!.shadowRoot!.querySelectorAll<HTMLElement>('.count')].map((badge, index) => {
      const box = badge.getBoundingClientRect();
      return { key: badge.getAttribute('aria-label') ?? `count ${index}`, x: box.x, y: box.y, width: box.width, height: box.height };
    }),
  );

const wireSampleBoxes = (page: Page, span: number, samples: number): Promise<SampledBox[]> =>
  page.evaluate(
    ([side, steps]) => {
      const boxes: SampledBox[] = [];
      for (const wire of document.getElementById('explorer')!.shadowRoot!.querySelectorAll<SVGPathElement>('.wire')) {
        const length = wire.getTotalLength();
        const matrix = wire.getScreenCTM();
        if (!matrix || !length) continue;
        const connection = (wire.parentNode as SVGGElement).dataset.connection ?? '';
        for (let step = 1; step < steps; step += 1) {
          const at = wire.getPointAtLength((length * step) / steps);
          const screen = new DOMPoint(at.x, at.y).matrixTransform(matrix);
          boxes.push({
            key: `${connection} at ${step}/${steps}`,
            x: screen.x - side / 2,
            y: screen.y - side / 2,
            width: side,
            height: side,
          });
        }
      }
      return boxes;
    },
    [span, samples] as const,
  );

async function boxesPaintedFlat(page: Page, sampled: SampledBox[]): Promise<{ measured: string[]; flat: string[] }> {
  const shot = `data:image/png;base64,${(await page.screenshot()).toString('base64')}`;
  return page.evaluate(
    async ([source, boxes]) => {
      const image = await new Promise<HTMLImageElement>((resolve, reject) => {
        const loading = new Image();
        loading.onload = () => resolve(loading);
        loading.onerror = () => reject(new Error('the browser could not decode the shot of its own page'));
        loading.src = source as string;
      });
      const canvas = document.createElement('canvas');
      canvas.width = image.naturalWidth;
      canvas.height = image.naturalHeight;
      const surface = canvas.getContext('2d', { willReadFrequently: true })!;
      surface.drawImage(image, 0, 0);
      const measured: string[] = [];
      const flat: string[] = [];
      for (const box of boxes as SampledBox[]) {
        const x = Math.round(box.x);
        const y = Math.round(box.y);
        const width = Math.round(box.width);
        const height = Math.round(box.height);
        if (width < 1 || height < 1 || x < 0 || y < 0 || x + width > canvas.width || y + height > canvas.height) continue;
        measured.push(box.key);
        const pixels = surface.getImageData(x, y, width, height).data;
        const shades = new Set<string>();
        for (let offset = 0; offset < pixels.length; offset += 4)
          shades.add(`${pixels[offset]},${pixels[offset + 1]},${pixels[offset + 2]}`);
        if (shades.size < 2) flat.push(box.key);
      }
      return { measured, flat };
    },
    [shot, sampled] as const,
  );
}

const restyle = (page: Page, css: string) =>
  page.evaluate((rules) => {
    const style = document.createElement('style');
    style.textContent = rules;
    document.getElementById('explorer')!.shadowRoot!.append(style);
  }, css);

const withoutTheGround = (page: Page) => restyle(page, `.shell{${GROUND}:transparent}`);

const naiveGroundOverTheMap = (page: Page) => restyle(page, `.boundary[data-role='group']{background:var(${GROUND})}`);

const swallowedBy = (withGround: string[], withoutGround: string[]) => withGround.filter((key) => !withoutGround.includes(key));

const MEASURED_FLOOR = 20;

async function badgesOnTheWholeMap(page: Page) {
  await open(page);
  await explorer(page, '.dock button[aria-label="Fit map to view"]').click();
  await settle(page);
  const badges = await countBadgeBoxes(page);
  expect(badges.length).toBeGreaterThan(MEASURED_FLOOR);
  return badges;
}

async function wiresOnTheWholeMap(page: Page) {
  await open(page);
  await openMenu(page);
  await explorer(page, '.settings [data-value="lines"]').click();
  await explorer(page, '.dock button[aria-label="Fit map to view"]').click();
  await settle(page);
  expect(await explorer(page, '.wire').count()).toBeGreaterThan(0);
  const wires = await wireSampleBoxes(page, WIRE_SAMPLE_SPAN, WIRE_SAMPLES_PER_ROUTE);
  expect(wires.length).toBeGreaterThan(MEASURED_FLOOR);
  return wires;
}

async function swallowedWhenTheGroundIsRemoved(page: Page, what: string, sampled: SampledBox[]) {
  const withGround = await boxesPaintedFlat(page, sampled);
  await withoutTheGround(page);
  const withoutGround = await boxesPaintedFlat(page, sampled);
  expect(withGround.measured.length, `only ${withGround.measured.length} of ${sampled.length} ${what} were in frame`).toBeGreaterThan(
    MEASURED_FLOOR,
  );
  const gone = swallowedBy(withGround.flat, withoutGround.flat);
  return { gone, note: `the ground swallowed ${gone.length} of ${withGround.measured.length} ${what}, first ${gone[0] ?? 'none'}` };
}

test('P13 the boundary ground swallows no count badge and no drawn wire that is painted without it', async ({ page }) => {
  const badges = await swallowedWhenTheGroundIsRemoved(page, 'count badges', await badgesOnTheWholeMap(page));
  expect(badges.gone.length, badges.note).toBe(0);
  const wires = await swallowedWhenTheGroundIsRemoved(page, 'wire samples', await wiresOnTheWholeMap(page));
  expect(wires.gone.length, wires.note).toBe(0);
});

test('a ground painted on the boundary itself is reported swallowing the badges and wires beneath it', async ({ page }) => {
  const badges = await badgesOnTheWholeMap(page);
  const badgesAsShipped = await boxesPaintedFlat(page, badges);
  await naiveGroundOverTheMap(page);
  const badgesUnderTheNaiveGround = await boxesPaintedFlat(page, badges);
  expect(swallowedBy(badgesUnderTheNaiveGround.flat, badgesAsShipped.flat).length).toBeGreaterThan(0);

  const wires = await wiresOnTheWholeMap(page);
  const wiresAsShipped = await boxesPaintedFlat(page, wires);
  await naiveGroundOverTheMap(page);
  const wiresUnderTheNaiveGround = await boxesPaintedFlat(page, wires);
  expect(swallowedBy(wiresUnderTheNaiveGround.flat, wiresAsShipped.flat).length).toBeGreaterThan(0);
});

const BOARD_DOT_PITCH = parseFloat(tokens['--kb-viewport-background'].value.match(/\/\s*([\d.]+)px/)![1]);
const SCREEN_THAT_RESOLVES_A_BOARD_DOT = { viewport: { width: 1600, height: 1000 }, deviceScaleFactor: 2 };

interface DimmedCardReading {
  id: string;
  ownerRole: string;
  background: string;
  measured: boolean;
  pixelsOffItsOwnShade: number;
  shade: string;
  shadeAroundIt: string;
}

interface DimmedBoardReading {
  cards: DimmedCardReading[];
  boardShade: string;
  barePatches: number;
  barePatchesShowingADot: number;
}

async function dimmedCardsReadOffThePixels(page: Page): Promise<DimmedBoardReading> {
  await page.mouse.move(0, 0);
  await restyle(page, '.card > *{visibility:hidden!important}.shell > :not(.viewport):not(.topbar){visibility:hidden!important}');
  const geometry = await page.evaluate((pitch) => {
    const shell = document.getElementById('explorer')!.shadowRoot!;
    const frame = shell.querySelector('.viewport')!.getBoundingClientRect();
    const world = shell.querySelector('.world')!;
    const inFrame = (x: number, y: number) => x > frame.x && y > frame.y && x < frame.right && y < frame.bottom;
    const cards = [...shell.querySelectorAll<HTMLElement>('.card[data-state="dimmed"]')].map((card) => {
      const box = card.getBoundingClientRect();
      const inset = 5;
      const probes = [
        [box.x + inset, box.y + inset],
        [box.right - inset, box.y + inset],
        [box.x + inset, box.bottom - inset],
        [box.right - inset, box.bottom - inset],
        [box.x + box.width / 2, box.y + box.height / 2],
      ];
      return {
        id: card.dataset.id ?? '',
        ownerRole: card.dataset.ownerRole ?? '',
        background: getComputedStyle(card).backgroundColor,
        measured: probes.every(([x, y]) => inFrame(x, y) && shell.elementFromPoint(x, y) === card),
        x: box.x,
        y: box.y,
        width: box.width,
        height: box.height,
      };
    });
    const boundaries = [...world.querySelectorAll<HTMLElement>('.boundary')].map((boundary) => ({
      box: boundary.getBoundingClientRect(),
      grounded: !/^rgba\(.*, 0\)$|^transparent$/.test(getComputedStyle(boundary, '::before').backgroundColor),
    }));
    const obstacles = [...world.querySelectorAll('*')]
      .filter((node) => !node.classList.contains('boundary') && !node.classList.contains('wires'))
      .map((node) => node.getBoundingClientRect())
      .filter((box) => box.width > 0 && box.height > 0);
    const margin = 3;
    const meets = (box: DOMRect, x: number, y: number) =>
      x < box.right + margin && box.x - margin < x + pitch && y < box.bottom + margin && box.y - margin < y + pitch;
    const wellInside = (box: DOMRect, x: number, y: number) =>
      x > box.x + margin && x + pitch < box.right - margin && y > box.y + margin && y + pitch < box.bottom - margin;
    const patches: { x: number; y: number }[] = [];
    for (let y = frame.y + margin; y + pitch < frame.bottom - margin; y += pitch)
      for (let x = frame.x + margin; x + pitch < frame.right - margin; x += pitch) {
        if (boundaries.some(({ box, grounded }) => meets(box, x, y) && (grounded || !wellInside(box, x, y)))) continue;
        if (obstacles.some((box) => meets(box, x, y))) continue;
        patches.push({ x, y });
      }
    return { cards, patches, pitch };
  }, BOARD_DOT_PITCH);
  const shot = `data:image/png;base64,${(await page.screenshot({ animations: 'disabled', caret: 'hide', scale: 'device' })).toString('base64')}`;
  return page.evaluate(
    async ([source, { cards, patches, pitch }]) => {
      const image = await new Promise<HTMLImageElement>((resolve, reject) => {
        const loading = new Image();
        loading.onload = () => resolve(loading);
        loading.onerror = () => reject(new Error('the browser could not decode the shot of its own page'));
        loading.src = source;
      });
      const canvas = document.createElement('canvas');
      canvas.width = image.naturalWidth;
      canvas.height = image.naturalHeight;
      const surface = canvas.getContext('2d', { willReadFrequently: true })!;
      surface.drawImage(image, 0, 0);
      const density = image.naturalWidth / window.innerWidth;
      const shadesIn = (strips: { x: number; y: number; width: number; height: number }[]) => {
        const tally = new Map<string, number>();
        let pixelsRead = 0;
        for (const strip of strips) {
          const x = Math.round(strip.x * density);
          const y = Math.round(strip.y * density);
          const width = Math.round(strip.width * density);
          const height = Math.round(strip.height * density);
          if (width < 1 || height < 1 || x < 0 || y < 0 || x + width > canvas.width || y + height > canvas.height) continue;
          const pixels = surface.getImageData(x, y, width, height).data;
          for (let offset = 0; offset < pixels.length; offset += 4) {
            const shade = `${pixels[offset]},${pixels[offset + 1]},${pixels[offset + 2]}`;
            tally.set(shade, (tally.get(shade) ?? 0) + 1);
            pixelsRead += 1;
          }
        }
        const [modal, modalCount] = [...tally.entries()].sort((a, b) => b[1] - a[1])[0] ?? ['', 0];
        return { modal, offModal: pixelsRead - modalCount, pixelsRead };
      };
      const inside = 6;
      const near = 1;
      const far = 3;
      const read = cards.map((card) => {
        const interior = shadesIn([
          { x: card.x + inside, y: card.y + inside, width: card.width - 2 * inside, height: card.height - 2 * inside },
        ]);
        const around = shadesIn([
          { x: card.x, y: card.y - far, width: card.width, height: far - near },
          { x: card.x, y: card.y + card.height + near, width: card.width, height: far - near },
          { x: card.x - far, y: card.y, width: far - near, height: card.height },
          { x: card.x + card.width + near, y: card.y, width: far - near, height: card.height },
        ]);
        return {
          id: card.id,
          ownerRole: card.ownerRole,
          background: card.background,
          measured: card.measured && interior.pixelsRead > 0 && around.pixelsRead > 0,
          pixelsOffItsOwnShade: interior.offModal,
          shade: interior.modal,
          shadeAroundIt: around.modal,
        };
      });
      const bare = patches.map((patch) => shadesIn([{ x: patch.x, y: patch.y, width: pitch, height: pitch }]));
      const boardShades = new Map<string, number>();
      for (const patch of bare) boardShades.set(patch.modal, (boardShades.get(patch.modal) ?? 0) + 1);
      return {
        cards: read,
        boardShade: [...boardShades.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] ?? '',
        barePatches: bare.length,
        barePatchesShowingADot: bare.filter((patch) => patch.offModal > 0).length,
      };
    },
    [shot, geometry] as const,
  );
}

const showingTheBoardsDots = (reading: DimmedBoardReading) =>
  reading.cards.filter((card) => card.measured && card.pixelsOffItsOwnShade > 0).map((card) => card.id);

const standingOutOfTheirGround = (reading: DimmedBoardReading) =>
  reading.cards.filter((card) => card.measured && card.shade !== card.shadeAroundIt).map((card) => card.id);

interface DimmingBoard {
  board: string;
  arrive: (page: Page) => Promise<void>;
  select: string;
}

const viewTab = (view: string) => async (page: Page) => {
  await explorer(page, `.view-tabs [data-value="${view}"]`).click();
  await settle(page);
};

const BOARDS_THAT_DIM_CARDS: DimmingBoard[] = [
  { board: 'grouped elements', arrive: async () => {}, select: '.card[data-kind="artifact"]' },
  {
    board: 'flat elements',
    arrive: async (page) => {
      await openMenu(page);
      await explorer(page, '.settings [data-value="none"]').click();
      await page.keyboard.press('Escape');
      await settle(page);
    },
    select: '.card[data-kind="artifact"]',
  },
  { board: 'artifacts', arrive: viewTab('artifacts'), select: '.card[data-kind="artifact"]' },
  { board: 'frames', arrive: viewTab('frames'), select: '.card[data-kind="frame"]' },
];

async function aCardSelectedOnTheFittedMap(page: Page, { arrive, select }: DimmingBoard) {
  await open(page);
  await arrive(page);
  await explorer(page, select)
    .first()
    .click({ force: true, position: { x: 12, y: 8 } });
  await settle(page);
  await explorer(page, '.detail .close').click();
  await explorer(page, '.dock button[aria-label="Fit map to view"]').click();
  await settle(page);
  expect(await explorer(page, '.card[data-state="selected"]').count()).toBe(1);
}

async function onAScreenThatResolvesABoardDot(browser: Browser, run: (page: Page) => Promise<void>) {
  const context = await browser.newContext(SCREEN_THAT_RESOLVES_A_BOARD_DOT);
  try {
    await run(await context.newPage());
  } finally {
    await context.close();
  }
}

const BOARD_THEMES = ['light', 'dark'] as const;

async function showTheBoardIn(page: Page, theme: (typeof BOARD_THEMES)[number]) {
  const switchToIt = explorer(page, `.utilities button[aria-label="Use ${theme} theme"]`);
  if (await switchToIt.count()) await switchToIt.click();
  await expect(explorer(page, `.utilities button[aria-label="Use ${theme === 'light' ? 'dark' : 'light'} theme"]`)).toHaveCount(1);
}

for (const dimming of BOARDS_THAT_DIM_CARDS)
  test(`P15 a dimmed card paints the ground it stands on, so no board dot shows through it and it is no hole in a grounded boundary: ${dimming.board}`, async ({
    browser,
  }) => {
    await onAScreenThatResolvesABoardDot(browser, async (page) => {
      await aCardSelectedOnTheFittedMap(page, dimming);
      for (const theme of BOARD_THEMES) {
        await showTheBoardIn(page, theme);
        const reading = await dimmedCardsReadOffThePixels(page);
        const measured = reading.cards.filter((card) => card.measured);
        const where = `${dimming.board}, ${theme}`;
        expect(measured.length, `${where}: no dimmed card was in frame to be measured`).toBeGreaterThan(0);
        expect(reading.barePatches, `${where}: no bare patch of board was found to prove the instrument on`).toBeGreaterThan(0);
        expect(
          reading.barePatchesShowingADot,
          `${where}: the instrument saw a dot on ${reading.barePatchesShowingADot} of ${reading.barePatches} bare patches of board, so it cannot say a card hides them`,
        ).toBe(reading.barePatches);
        expect(
          measured.filter((card) => card.shadeAroundIt === reading.boardShade).length,
          `${where}: no measured dimmed card stood on the bare board, where the dots are`,
        ).toBeGreaterThan(0);
        const dotted = showingTheBoardsDots(reading);
        expect(dotted, `${where}: ${dotted.length} of ${measured.length} measured dimmed cards show the board's dots`).toEqual([]);
        const holes = standingOutOfTheirGround(reading);
        expect(
          holes,
          `${where}: ${holes.length} of ${measured.length} measured dimmed cards are not the shade of the ground around them`,
        ).toEqual([]);
        const rolesMeasured = new Set(measured.map((card) => card.ownerRole));
        const backgroundsByRole = new Map<string, Set<string>>();
        for (const card of reading.cards)
          backgroundsByRole.set(card.ownerRole, (backgroundsByRole.get(card.ownerRole) ?? new Set()).add(card.background));
        for (const [role, backgrounds] of backgroundsByRole) {
          expect(role, `${where}: a dimmed card does not say what kind of boundary it stands in`).not.toBe('');
          expect(rolesMeasured.has(role), `${where}: no dimmed card standing in a ${role} was measured on the pixels`).toBe(true);
          expect([...backgrounds], `${where}: dimmed cards standing in a ${role} do not all paint one background`).toHaveLength(1);
        }
      }
    });
  });

test('a transparent dimmed card is reported showing the dots, and one painted the canvas is reported a hole in its ground', async ({
  browser,
}) => {
  await onAScreenThatResolvesABoardDot(browser, async (page) => {
    await aCardSelectedOnTheFittedMap(page, BOARDS_THAT_DIM_CARDS[0]);
    for (const theme of BOARD_THEMES) {
      await showTheBoardIn(page, theme);
      await restyle(page, `.card[data-state='dimmed']{background:transparent!important}`);
      const transparent = await dimmedCardsReadOffThePixels(page);
      expect(showingTheBoardsDots(transparent).length, `${theme}: transparent cards showing dots`).toBeGreaterThan(0);
      expect(standingOutOfTheirGround(transparent), `${theme}: transparent cards out of their ground`).toEqual([]);
      await restyle(page, `.card[data-state='dimmed']{background:var(--kb-canvas)!important}`);
      const canvas = await dimmedCardsReadOffThePixels(page);
      expect(showingTheBoardsDots(canvas), `${theme}: canvas cards showing dots`).toEqual([]);
      expect(standingOutOfTheirGround(canvas).length, `${theme}: canvas cards out of their ground`).toBeGreaterThan(0);
    }
  });
});

const surfaceOf = (page: Page, selector: string) =>
  explorer(page, selector)
    .first()
    .evaluate((node) => {
      const style = getComputedStyle(node);
      return { background: style.backgroundColor, lift: style.boxShadow, radius: parseFloat(style.borderTopLeftRadius) };
    });

async function theMapWithItsFloatingChromeOnScreen(page: Page) {
  await open(page);
  const resting = await surfaceOf(page, '.card');
  await explorer(page, '.dock button[aria-expanded]').click();
  await expect(explorer(page, '.minimap')).toBeVisible();
  await explorer(page, '.card[data-id="element:product-vision"]').click();
  await settle(page);
  await expect(explorer(page, '.legend')).toBeVisible();
  return resting;
}

test('chrome that floats over the map is a lifted surface; a card at rest is not', async ({ page }) => {
  const resting = await theMapWithItsFloatingChromeOnScreen(page);
  const minimap = await surfaceOf(page, '.minimap');
  const legend = await surfaceOf(page, '.legend');

  expect(minimap.lift, 'the minimap is the lift the legend peers with, so it cannot itself be flat').not.toBe('none');
  expect(legend.lift).toBe(minimap.lift);
  expect(legend.background).toBe(light('--kb-surface'));
  expect(legend.radius).toBe(metric('--kb-radius-lg'));
  expect(minimap.radius).toBe(metric('--kb-radius-lg'));

  expect(resting.lift).toBe('none');
  expect(resting.radius).toBe(metric('--kb-radius-md'));
  expect(legend.radius).toBeGreaterThan(resting.radius);
});

const P21 =
  'P21 every claim the guidance document makes reaches its own subject verbatim, and the copy explorer writes around it is never a guidance kind id';

test(P21, async ({ page }) => {
  await open(page);
  const panels = await build({
    tsconfig: path.join(root, 'explorer/tsconfig.test.json'),
    stdin: {
      contents: "export { detailOverlay } from './component-patterns/detail-overlay';",
      resolveDir: path.join(root, 'explorer/src'),
      loader: 'ts',
    },
    bundle: true,
    format: 'iife',
    globalName: 'ExplorerPanels',
    loader: { '.css': 'text' },
    write: false,
    logLevel: 'silent',
  });
  await page.addScriptTag({ content: panels.outputFiles[0].text });

  const measured = await page.evaluate(async () => {
    interface Entry {
      subject: string;
      kind: string;
      claim: string;
    }
    interface Model {
      entities: { id: string; kind: string; label: string; description: string }[];
      guidance: { kinds: { id: string }[]; entries: Entry[] };
    }
    type Panels = { detailOverlay(model: Model, subject: string, close: () => void, select: (id: string) => void): { root: HTMLElement } };
    const lib = (globalThis as unknown as { ExplorerPanels: Panels }).ExplorerPanels;
    const model = JSON.parse(document.getElementById('explorer-model')!.textContent!) as Model;
    const kindIds = model.guidance.kinds.map((kind) => kind.id);
    const attachable = model.entities.filter((entity) => ['element', 'artifact'].includes(entity.kind)).map((entity) => entity.id);
    const claimsOf = (subject: string, source: Model = model) => source.guidance.entries.filter((entry) => entry.subject === subject);
    const kindIdsIn = (text: string) => kindIds.filter((kind) => new RegExp(`\\b${kind}\\b`, 'i').test(text));

    const stage = document.createElement('div');
    document.body.append(stage);
    const panelFor = (subject: string, source: Model) => {
      stage.replaceChildren();
      stage.append(
        lib.detailOverlay(
          source,
          subject,
          () => {},
          () => {},
        ).root,
      );
      const body = stage.querySelector<HTMLElement>('.panel-body')!;
      const block = body.querySelector<HTMLDetailsElement>(':scope > details.guidance');
      if (block) block.open = true;
      return { body, block };
    };

    const sweep = (source: Model) => {
      const blocksWhereTheDocumentHasNone: string[] = [];
      const subjectsMissingTheirBlock: string[] = [];
      const claimsNotDrawnVerbatim: string[] = [];
      const claimsDrawnMoreThanOnce: string[] = [];
      const claimsDrawnInsideARelationRow: string[] = [];
      const kindIdsReachingTheReader = new Set<string>();
      let claimsExpected = 0;
      let claimsDrawn = 0;
      for (const subject of attachable) {
        const entries = claimsOf(subject, source);
        claimsExpected += entries.length;
        const { body, block } = panelFor(subject, source);
        if (!entries.length) {
          if (block) blocksWhereTheDocumentHasNone.push(subject);
          continue;
        }
        if (!block) {
          subjectsMissingTheirBlock.push(subject);
          continue;
        }
        const text = body.innerText;
        const relationText = [...body.querySelectorAll<HTMLElement>('.relation')].map((row) => row.innerText);
        for (const entry of entries) {
          const occurrences = text.split(entry.claim).length - 1;
          if (occurrences === 0) claimsNotDrawnVerbatim.push(`${subject}: ${entry.claim}`);
          else claimsDrawn += 1;
          if (occurrences > 1) claimsDrawnMoreThanOnce.push(`${subject}: ${entry.claim}`);
          if (relationText.some((row) => row.includes(entry.claim))) claimsDrawnInsideARelationRow.push(`${subject}: ${entry.claim}`);
        }
        for (const kind of kindIdsIn(text)) kindIdsReachingTheReader.add(kind);
      }
      return {
        claimsExpected,
        claimsDrawn,
        blocksWhereTheDocumentHasNone,
        subjectsMissingTheirBlock,
        claimsNotDrawnVerbatim,
        claimsDrawnMoreThanOnce,
        claimsDrawnInsideARelationRow,
        kindIdsReachingTheReader: [...kindIdsReachingTheReader].sort(),
      };
    };

    const RENAMED = 'Renamedword';
    const PROSE_A_DOCUMENT_AUTHORS = [
      'label',
      'description',
      'question',
      'claim',
      'action',
      'actor',
      'timing',
      'form',
      'cite',
      'forward',
      'reverse',
    ];
    let counter = 0;
    const renameProse = (value: unknown): unknown =>
      Array.isArray(value)
        ? value.map(renameProse)
        : value && typeof value === 'object'
          ? Object.fromEntries(
              Object.entries(value as Record<string, unknown>).map(([key, held]) => [
                key,
                PROSE_A_DOCUMENT_AUTHORS.includes(key) && typeof held === 'string' && held
                  ? `${RENAMED}${(counter += 1)}`
                  : renameProse(held),
              ]),
            )
          : value;
    const renamed = renameProse(structuredClone(model)) as Model;
    const asAuthored = sweep(model);
    const withTheDocumentsOwnWordsRenamed = sweep(renamed);
    stage.remove();

    const viewer = (document.getElementById('explorer') as unknown as { explorerViewer: { select(id: string | null): void } })
      .explorerViewer;
    const frame = () => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    const onScreen: { subject: string; claims: number; drawn: number; blockPresent: boolean }[] = [];
    const firstOfEachKindCarryingGuidance = ['element', 'artifact'].flatMap((kind) => [
      model.entities.find((entity) => entity.kind === kind && claimsOf(entity.id).length)?.id,
      model.entities.find((entity) => entity.kind === kind && !claimsOf(entity.id).length)?.id,
    ]);
    for (const subject of firstOfEachKindCarryingGuidance) {
      if (!subject) continue;
      viewer.select(subject);
      await frame();
      const body = document.getElementById('explorer')!.shadowRoot!.querySelector<HTMLElement>('.panel.detail .panel-body')!;
      const block = body.querySelector<HTMLDetailsElement>(':scope > details.guidance');
      if (block) block.open = true;
      const text = body.innerText;
      onScreen.push({
        subject,
        claims: claimsOf(subject).length,
        drawn: claimsOf(subject).filter((entry) => text.includes(entry.claim)).length,
        blockPresent: !!block,
      });
    }

    return {
      kindIds,
      subjectsCarryingGuidance: attachable.filter((subject) => claimsOf(subject).length).length,
      subjectsCarryingNone: attachable.filter((subject) => !claimsOf(subject).length).length,
      subjectsCarryingABoundaryClaim: attachable.filter((subject) => claimsOf(subject).some((entry) => entry.kind === 'boundary')).length,
      asAuthored,
      withTheDocumentsOwnWordsRenamed,
      onScreen,
    };
  });

  expect(
    measured.kindIds.length,
    'the document must declare kinds for the deny-list half of this property to mean anything',
  ).toBeGreaterThan(0);
  expect(measured.subjectsCarryingGuidance, 'a probe that visits no guided subject cannot fail').toBeGreaterThan(0);
  expect(measured.subjectsCarryingNone, 'the unguided case must exist, or the empty half of this property never runs').toBeGreaterThan(0);
  expect(measured.subjectsCarryingABoundaryClaim, 'boundary guidance must be on screen for its placement to be under test').toBeGreaterThan(
    0,
  );

  expect(measured.asAuthored.subjectsMissingTheirBlock).toEqual([]);
  expect(measured.asAuthored.blocksWhereTheDocumentHasNone).toEqual([]);
  expect(measured.asAuthored.claimsNotDrawnVerbatim).toEqual([]);
  expect(measured.asAuthored.claimsDrawnMoreThanOnce).toEqual([]);
  expect(measured.asAuthored.claimsDrawnInsideARelationRow).toEqual([]);
  expect(measured.asAuthored.claimsDrawn).toBe(measured.asAuthored.claimsExpected);

  expect(
    measured.asAuthored.kindIdsReachingTheReader.length,
    'a check that does not separate the two reports the document for the ordinary English in its own claims',
  ).toBeGreaterThan(0);
  expect(measured.withTheDocumentsOwnWordsRenamed.claimsDrawn).toBe(measured.withTheDocumentsOwnWordsRenamed.claimsExpected);
  expect(measured.withTheDocumentsOwnWordsRenamed.kindIdsReachingTheReader).toEqual([]);

  expect(measured.onScreen.length, 'the mounted viewer must be visited with and without guidance, on both kinds it attaches to').toBe(4);
  for (const panel of measured.onScreen) {
    expect(panel.blockPresent, `${panel.subject} draws a guidance block only where the document has claims`).toBe(panel.claims > 0);
    expect(panel.drawn, `${panel.subject} draws every claim the document gives it`).toBe(panel.claims);
  }
});

test('the connection panel states its reading in the panel, not only in a tooltip', async ({ page }) => {
  await open(page);
  await explorer(page, '.count').first().click();
  await settle(page);
  const detail = explorer(page, '.detail');
  await expect(detail).toBeVisible();
  for (const showAll of await detail.locator('.show-all').all()) await showAll.click();
  const rows = await detail.evaluate((panel) =>
    [...panel.querySelectorAll('.relation-glyph')].map((glyph) => ({
      reading: glyph.querySelector('title')?.textContent ?? '',
      atRest: glyph.closest('.group')?.querySelector('h4')?.textContent ?? '',
    })),
  );
  const computed = rows.filter((row) => row.reading);
  expect(computed.length, 'rows whose glyph computes a reading').toBeGreaterThan(0);
  expect(
    computed.filter((row) => row.atRest !== row.reading),
    'rows whose reading reaches only the tooltip',
  ).toEqual([]);
});

test('the source definition is a code block with a control that copies it', async ({ page }) => {
  await open(page);
  await explorer(page, '.card[data-id="artifact:design-doc"]').click();
  await settle(page);
  const source = explorer(page, '.detail .source');
  await source.locator('summary').click();
  const code = source.locator('.code-block pre code');
  await expect(code).toHaveCount(1);
  const definition = (await code.textContent()) ?? '';
  expect(definition.length).toBeGreaterThan(0);
  expect(await code.locator('*').count(), 'the payload carries no syntax highlighting').toBe(0);
  const copy = source.locator('button[aria-label="Copy definition"]');
  await expect(copy).toHaveAttribute('title', 'Copy definition');
  await page.evaluate(() => {
    const held = window as unknown as { written: string[] };
    held.written = [];
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: {
        writeText: (text: string) => {
          held.written.push(text);
          return Promise.resolve();
        },
      },
    });
  });
  await copy.click();
  expect(await page.evaluate(() => (window as unknown as { written: string[] }).written)).toEqual([definition]);
});

const CARD_HEADING_RUNGS = DOCK_LADDER.filter((rung) => [1.25, 1, 0.8, 0.4096].includes(rung.zoom));

const headingInkOutsideItsCard = (page: Page) =>
  page.evaluate(() => {
    const TOLERANCE = 1;
    const shell = document.getElementById('explorer')!.shadowRoot!;
    const board = new DOMMatrixReadOnly(getComputedStyle(shell.querySelector('.world')!).transform).a;
    const escapes: string[] = [];
    for (const card of shell.querySelectorAll<HTMLElement>('.card')) {
      const box = card.getBoundingClientRect();
      const style = getComputedStyle(card);
      const content = {
        left: box.left + parseFloat(style.paddingLeft) * board,
        top: box.top + parseFloat(style.paddingTop) * board,
        right: box.right - parseFloat(style.paddingRight) * board,
        bottom: box.bottom - parseFloat(style.paddingBottom) * board,
      };
      const row = card.querySelector('.card-frames')?.getBoundingClientRect() ?? null;
      for (const node of card.querySelectorAll<HTMLElement>('.card-title, .card-subtitle')) {
        const contents = document.createRange();
        contents.selectNodeContents(node);
        const ink = contents.getBoundingClientRect();
        if (!ink.width || !ink.height) continue;
        const over = (
          [
            ['left', content.left - ink.left],
            ['top', content.top - ink.top],
            ['right', ink.right - content.right],
            ['bottom', ink.bottom - content.bottom],
          ] as [string, number][]
        ).filter(([, past]) => past / board > TOLERANCE);
        for (const [edge, past] of over)
          escapes.push(`${card.dataset.id} ${node.className} ink leaves its card ${(past / board).toFixed(1)}px past the ${edge} edge`);
        if (row && ink.bottom > row.top + TOLERANCE * board && ink.top < row.bottom && ink.left < row.right && ink.right > row.left)
          escapes.push(`${card.dataset.id} ${node.className} ink reaches the frame-icon row`);
      }
    }
    return escapes;
  });

test('card titles and subtitles grow toward true size without their ink leaving the card or reaching the frame-icon row', async ({
  page,
}) => {
  await open(page);
  for (const view of ['elements', 'artifacts', 'frames'] as const) {
    await explorer(page, `.view-tabs button[data-value="${view}"]`).click();
    await settle(page);
    for (const rung of CARD_HEADING_RUNGS) {
      await clickDockTo(page, rung);
      expect(await explorer(page, '.card-title').count(), `${view} z=${rung.zoom} draws no card heading`).toBeGreaterThan(0);
      expect(await headingInkOutsideItsCard(page), `${view} z=${rung.zoom}`).toEqual([]);
    }
  }
});

const markToTitleGaps = (page: Page) =>
  page.evaluate(() => {
    const shell = document.getElementById('explorer')!.shadowRoot!;
    const rows: { card: string; gap: number }[] = [];
    for (const title of shell.querySelectorAll<HTMLElement>('.card-title')) {
      const mark = title.querySelector('svg');
      const words = title.querySelector('span');
      if (!mark || !words) continue;
      const line = document.createRange();
      line.selectNodeContents(words);
      const first = line.getClientRects()[0];
      if (!first) continue;
      rows.push({ card: (title.closest('.card') as HTMLElement).dataset.id ?? '', gap: first.left - mark.getBoundingClientRect().right });
    }
    return rows;
  });

test('a card mark stands clear of the title it introduces', async ({ page }) => {
  await open(page);
  await explorer(page, '.view-tabs button[data-value="frames"]').click();
  await settle(page);
  const gaps = await markToTitleGaps(page);
  expect(gaps.length, 'no card draws a mark inside its title, so this asserts nothing').toBeGreaterThan(0);
  expect(
    gaps.filter((row) => !(row.gap > 0)).map((row) => `${row.card} leaves ${row.gap.toFixed(1)}px between its mark and its title`),
  ).toEqual([]);
});

const DESCRIPTION_LINES_ALLOWED: Record<string, number> = { frame: 2, factor: 2, option: 3 };

const describedCards = (page: Page, allowed: Record<string, number>) =>
  page.evaluate((limits) => {
    const shell = document.getElementById('explorer')!.shadowRoot!;
    const linesEndingAbove = (node: HTMLElement, bottom: number) => {
      const run = document.createRange();
      run.selectNodeContents(node);
      const tops = new Set<number>();
      for (const rect of run.getClientRects()) if (rect.height && rect.bottom <= bottom + 1) tops.add(Math.round(rect.top));
      return tops.size;
    };
    const rows: { card: string; limit: number; drawn: number; whole: number; tooltip: string }[] = [];
    for (const card of shell.querySelectorAll<HTMLElement>('.card')) {
      const limit = limits[card.dataset.kind ?? ''];
      const said = card.querySelector<HTMLElement>('.card-subtitle');
      if (limit === undefined || !said) continue;
      const twin = said.cloneNode(true) as HTMLElement;
      twin.removeAttribute('title');
      twin.style.position = 'absolute';
      twin.style.visibility = 'hidden';
      twin.style.display = 'block';
      twin.style.overflow = 'visible';
      twin.style.width = `${said.clientWidth}px`;
      said.parentElement!.append(twin);
      const whole = linesEndingAbove(twin, Number.POSITIVE_INFINITY);
      twin.remove();
      rows.push({
        card: card.dataset.id ?? '',
        limit,
        drawn: linesEndingAbove(said, said.getBoundingClientRect().bottom),
        whole,
        tooltip: said.getAttribute('title') ?? '',
      });
    }
    return rows;
  }, allowed);

test('a frame or frame-option description is drawn within its line allowance, and carries its full text exactly where it is clipped', async ({
  page,
}) => {
  await open(page);
  await explorer(page, '.view-tabs button[data-value="frames"]').click();
  await settle(page);
  for (const rung of DOCK_LADDER) {
    await clickDockTo(page, rung);
    const described = await describedCards(page, DESCRIPTION_LINES_ALLOWED);
    expect(described.length, `z=${rung.zoom} draws no described card`).toBeGreaterThan(0);
    expect(
      described.filter((row) => row.drawn > row.limit).map((row) => `${row.card} draws ${row.drawn} lines where ${row.limit} are allowed`),
      `z=${rung.zoom}`,
    ).toEqual([]);
    expect(
      described
        .filter((row) => (row.tooltip !== '') !== row.whole > row.drawn)
        .map((row) => `${row.card} draws ${row.drawn} of ${row.whole} lines with ${row.tooltip ? 'a' : 'no'} tooltip`),
      `z=${rung.zoom}`,
    ).toEqual([]);
  }
});

test('frame and frame-option panels keep every authored row meaning with its own static row', async ({ page }) => {
  await open(page);
  const panels = await build({
    tsconfig: path.join(root, 'explorer/tsconfig.test.json'),
    stdin: {
      contents: "export { detailOverlay } from './component-patterns/detail-overlay';",
      resolveDir: path.join(root, 'explorer/src'),
      loader: 'ts',
    },
    bundle: true,
    format: 'iife',
    globalName: 'ExplorerSemanticRows',
    loader: { '.css': 'text' },
    write: false,
    logLevel: 'silent',
  });
  await page.addScriptTag({ content: panels.outputFiles[0].text });
  const measured = await page.evaluate(() => {
    interface Entity {
      id: string;
      sourceId: string;
      kind: string;
      label: string;
      description: string;
      frameValues: Record<string, unknown>;
    }
    interface Model {
      orderingFrameId: string;
      entities: Entity[];
      connections: unknown[];
      rules: unknown[];
    }
    type Panels = { detailOverlay(model: Model, subject: string, close: () => void, select: (id: string) => void): { root: HTMLElement } };
    const model = JSON.parse(document.getElementById('explorer-model')!.textContent!) as Model;
    const lib = (globalThis as unknown as { ExplorerSemanticRows: Panels }).ExplorerSemanticRows;
    const ordering = model.orderingFrameId.split(':').slice(1).join(':');
    const framesBySource = new Map(model.entities.filter((entity) => entity.kind === 'frame').map((frame) => [frame.sourceId, frame]));
    const optionsByFrame = new Map<string, Entity[]>();
    const elementsByOption = new Map<string, Entity[]>();
    for (const option of model.entities.filter((entity) => entity.kind === 'option')) {
      const frame = framesBySource.get(option.id.split(':')[1] ?? '');
      if (!frame) continue;
      const entries = optionsByFrame.get(frame.id) ?? [];
      entries.push(option);
      optionsByFrame.set(frame.id, entries);
    }
    for (const element of model.entities.filter((entity) => entity.kind === 'element')) {
      const value = element.frameValues[ordering];
      if (typeof value !== 'string') continue;
      const optionId = `option:${ordering}:${value}`;
      const entries = elementsByOption.get(optionId) ?? [];
      entries.push(element);
      elementsByOption.set(optionId, entries);
    }
    const stage = document.createElement('div');
    document.body.append(stage);
    const problems: string[] = [];
    let describedOptions = 0;
    let undescribedOptions = 0;
    let longElementLists = 0;
    const panelFor = (subject: string) => {
      stage.replaceChildren(
        lib.detailOverlay(
          model,
          subject,
          () => {},
          () => {},
        ).root,
      );
      return stage.querySelector<HTMLElement>('.panel-body')!;
    };
    const sectionNamed = (body: HTMLElement, title: string) =>
      [...body.querySelectorAll<HTMLElement>(':scope > .section')].find((section) => section.querySelector('h3')?.textContent === title);
    const checkRows = (subject: string, group: HTMLElement | null | undefined, expected: Entity[]) => {
      if (!group) {
        problems.push(`${subject}: missing group`);
        return;
      }
      const rows = [...group.querySelectorAll<HTMLElement>('.semantic-row')];
      const rowsById = new Map(rows.map((row) => [row.dataset.semanticId, row]));
      if (rows.length !== expected.length) problems.push(`${subject}: expected ${expected.length} rows, found ${rows.length}`);
      for (const entity of expected) {
        const row = rowsById.get(entity.id);
        if (!row) {
          problems.push(`${subject}: ${entity.id} missing its row`);
          continue;
        }
        const names = [...row.querySelectorAll<HTMLElement>('.semantic-name')].filter((node) => node.textContent === entity.label);
        if (names.length !== 1) problems.push(`${subject}: ${entity.id} has ${names.length} matching labels in its row`);
        const descriptions = [...row.querySelectorAll<HTMLElement>('.semantic-description')];
        if (entity.description.trim()) {
          if (descriptions.length !== 1 || descriptions[0]?.textContent !== entity.description)
            problems.push(`${subject}: ${entity.id} does not carry its exact description once`);
        } else if (descriptions.length) problems.push(`${subject}: ${entity.id} reserves supporting copy without an authored description`);
      }
    };

    for (const frame of model.entities.filter((entity) => entity.kind === 'frame')) {
      const options = optionsByFrame.get(frame.id) ?? [];
      if (!options.length) continue;
      describedOptions += options.filter((option) => option.description.trim()).length;
      undescribedOptions += options.filter((option) => !option.description.trim()).length;
      const body = panelFor(frame.id);
      checkRows(frame.id, sectionNamed(body, 'Options')?.querySelector<HTMLElement>('.group'), options);
    }
    for (const option of model.entities.filter((entity) => entity.kind === 'option')) {
      const elements = elementsByOption.get(option.id) ?? [];
      if (!elements.length) continue;
      if (elements.length > 3) longElementLists += 1;
      const body = panelFor(option.id);
      checkRows(option.id, sectionNamed(body, 'Elements here')?.querySelector<HTMLElement>('.group'), elements);
    }
    stage.remove();
    return { problems, describedOptions, undescribedOptions, longElementLists };
  });

  expect(measured.describedOptions, 'the described-option half must have a real model probe').toBeGreaterThan(0);
  expect(measured.undescribedOptions, 'the description-less half must have a real model probe').toBeGreaterThan(0);
  expect(measured.longElementLists, 'the disclosed-element half must have a real model probe').toBeGreaterThan(0);
  expect(measured.problems).toEqual([]);
});

test('frame options are complete static values while long element groups disclose once', async ({ page }) => {
  await open(page);
  const phase = await selectDetail(page, 'frame:phase');
  const phaseOptions = phase.locator('.section').filter({ hasText: /^Options/ });
  const phaseRows = phaseOptions.locator('.semantic-row');
  const expectedPhaseOptions = await page.evaluate(
    () =>
      (
        JSON.parse(document.getElementById('explorer-model')!.textContent!) as {
          entities: { id: string; kind: string; frameId?: string }[];
        }
      ).entities.filter((entity) => entity.kind === 'option' && entity.frameId === 'frame:phase').length,
  );
  await expect(phaseRows).toHaveCount(expectedPhaseOptions);
  expect(await phaseRows.evaluateAll((rows) => rows.every((row) => !(row as HTMLElement).hidden))).toBe(true);
  await expect(phaseOptions.locator('.show-all')).toHaveCount(0);
  expect(
    await phaseRows.evaluateAll((rows) => rows.every((row) => !row.querySelector('button,a,[role="button"],.reference,[data-target],svg'))),
  ).toBe(true);

  const strategy = await selectDetail(page, 'option:phase:strategy');
  const elements = strategy.locator('.section').filter({ hasText: /^Elements here/ });
  const rows = elements.locator('.semantic-row');
  const expectedElements = await page.evaluate(() => {
    const model = JSON.parse(document.getElementById('explorer-model')!.textContent!) as {
      orderingFrameId: string;
      entities: { kind: string; sourceId: string; frameValues: Record<string, unknown> }[];
    };
    const ordering = model.orderingFrameId.split(':').slice(1).join(':');
    return model.entities.filter((entity) => entity.kind === 'element' && entity.frameValues[ordering] === 'strategy').length;
  });
  const disclosure = elements.locator('.show-all');
  await expect(disclosure).toHaveCount(1);
  await expect(disclosure).toHaveText(`Show all ${expectedElements}`);
  await expect(disclosure).toHaveAttribute('aria-expanded', 'false');
  expect(
    await rows.evaluateAll((semanticRows) =>
      semanticRows.every((row) => !row.querySelector('button,a,[role="button"],.reference,[data-target],svg')),
    ),
  ).toBe(true);
  await disclosure.click();
  await expect(disclosure).toHaveText('Show fewer');
  await expect(disclosure).toHaveAttribute('aria-expanded', 'true');
  await expect(disclosure).toBeFocused();
  expect(await rows.evaluateAll((semanticRows) => semanticRows.every((row) => !(row as HTMLElement).hidden))).toBe(true);
  await disclosure.click();
  await expect(disclosure).toHaveAttribute('aria-expanded', 'false');
  await expect(disclosure).toBeFocused();
});

test('semantic rows remain quiet, whole and reachable in capped desktop and narrow panels', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await open(page);
  const phase = await selectDetail(page, 'frame:phase');
  const phaseLayout = await phase.evaluate((panel) => {
    const body = panel.querySelector<HTMLElement>('.panel-body')!;
    const group = [...panel.querySelectorAll<HTMLElement>('.section')]
      .find((section) => section.querySelector('h3')?.textContent === 'Options')!
      .querySelector<HTMLElement>('.group')!;
    const rows = [...group.querySelectorAll<HTMLElement>('.semantic-row')];
    const measureText = (node: HTMLElement) => ({
      clippedX: node.scrollWidth > node.clientWidth + 1,
      clippedY: node.scrollHeight > node.clientHeight + 1,
      lineClamp: getComputedStyle(node).webkitLineClamp,
    });
    return {
      panelHeight: panel.getBoundingClientRect().height,
      bodyOverflowY: getComputedStyle(body).overflowY,
      groupOverflowY: getComputedStyle(group).overflowY,
      groupScrolls: group.scrollHeight > group.clientHeight + 1,
      questions: rows.flatMap((row) => [...row.querySelectorAll<HTMLElement>('.semantic-description')].map(measureText)),
      group: {
        border: parseFloat(getComputedStyle(group).borderTopWidth),
        background: getComputedStyle(group).backgroundColor,
        shadow: getComputedStyle(group).boxShadow,
      },
      rows: rows.map((row) => {
        const name = row.querySelector<HTMLElement>('.semantic-name')!;
        const question = row.querySelector<HTMLElement>('.semantic-description')!;
        return {
          background: getComputedStyle(row).backgroundColor,
          shadow: getComputedStyle(row).boxShadow,
          divider: parseFloat(getComputedStyle(row).borderBottomWidth),
          nameSize: parseFloat(getComputedStyle(name).fontSize),
          questionSize: parseFloat(getComputedStyle(question).fontSize),
          nameWeight: parseFloat(getComputedStyle(name).fontWeight),
          questionWeight: parseFloat(getComputedStyle(question).fontWeight),
          questionOpacity: parseFloat(getComputedStyle(question).opacity),
        };
      }),
    };
  });
  expect(phaseLayout.panelHeight).toBeLessThanOrEqual(480);
  expect(phaseLayout.bodyOverflowY).toBe('auto');
  expect(phaseLayout.groupOverflowY).toBe('visible');
  expect(phaseLayout.groupScrolls).toBe(false);
  expect(phaseLayout.questions.filter((question) => question.clippedX || question.clippedY || question.lineClamp !== 'none')).toEqual([]);
  expect(phaseLayout.group.border).toBeGreaterThan(0);
  expect(phaseLayout.group.background).toBe('rgba(0, 0, 0, 0)');
  expect(phaseLayout.group.shadow).toBe('none');
  expect(phaseLayout.rows.filter((row) => row.background !== 'rgba(0, 0, 0, 0)' || row.shadow !== 'none')).toEqual([]);
  expect(phaseLayout.rows.slice(0, -1).every((row) => row.divider > 0)).toBe(true);
  expect(phaseLayout.rows.at(-1)?.divider).toBe(0);
  expect(
    phaseLayout.rows.every(
      (row) =>
        row.nameSize >= 14 &&
        row.questionSize >= 13 &&
        row.nameSize >= row.questionSize &&
        row.nameWeight > row.questionWeight &&
        row.questionOpacity === 1,
    ),
  ).toBe(true);

  const strategy = await selectDetail(page, 'option:phase:strategy');
  const desktopRest = await strategy.evaluate((panel) => {
    const body = panel.querySelector<HTMLElement>('.panel-body')!;
    const group = [...panel.querySelectorAll<HTMLElement>('.section')]
      .find((section) => section.querySelector('h3')?.textContent === 'Elements here')!
      .querySelector<HTMLElement>('.group')!;
    const box = body.getBoundingClientRect();
    const rows = [...group.querySelectorAll<HTMLElement>('.semantic-row')].filter((row) => !row.hidden);
    const toggle = group.querySelector<HTMLElement>('.show-all')!;
    const whollyInside = (node: HTMLElement) => {
      const rect = node.getBoundingClientRect();
      return rect.top >= box.top - 1 && rect.bottom <= box.bottom + 1 && rect.left >= box.left - 1 && rect.right <= box.right + 1;
    };
    return {
      visibleRows: rows.length,
      wholeRows: rows.every(whollyInside),
      wholeToggle: whollyInside(toggle),
      groupOverflowY: getComputedStyle(group).overflowY,
      groupScrolls: group.scrollHeight > group.clientHeight + 1,
      bodyScrollTop: body.scrollTop,
    };
  });
  expect(desktopRest.visibleRows).toBe(2);
  expect(desktopRest.wholeRows).toBe(true);
  expect(desktopRest.wholeToggle).toBe(true);
  expect(desktopRest.groupOverflowY).toBe('visible');
  expect(desktopRest.groupScrolls).toBe(false);
  const toggle = strategy
    .locator('.section')
    .filter({ hasText: /^Elements here/ })
    .locator('.show-all');
  await toggle.click();
  const expanded = await strategy.evaluate((panel) => {
    const body = panel.querySelector<HTMLElement>('.panel-body')!;
    const group = [...panel.querySelectorAll<HTMLElement>('.section')]
      .find((section) => section.querySelector('h3')?.textContent === 'Elements here')!
      .querySelector<HTMLElement>('.group')!;
    const rows = [...group.querySelectorAll<HTMLElement>('.semantic-row')];
    const questions = rows.flatMap((row) => [...row.querySelectorAll<HTMLElement>('.semantic-description')]);
    return {
      hiddenRows: rows.filter((row) => row.hidden).length,
      groupOverflowY: getComputedStyle(group).overflowY,
      groupScrolls: group.scrollHeight > group.clientHeight + 1,
      questionClips: questions.filter(
        (question) => question.scrollWidth > question.clientWidth + 1 || question.scrollHeight > question.clientHeight + 1,
      ).length,
      bodyScrollTop: body.scrollTop,
    };
  });
  expect(expanded.hiddenRows).toBe(0);
  expect(expanded.groupOverflowY).toBe('visible');
  expect(expanded.groupScrolls).toBe(false);
  expect(expanded.questionClips).toBe(0);
  expect(Math.abs(expanded.bodyScrollTop - desktopRest.bodyScrollTop)).toBeLessThanOrEqual(1);
  await toggle.scrollIntoViewIfNeeded();
  await expect(toggle).toBeVisible();
  await expect(toggle).toBeFocused();

  await page.setViewportSize({ width: 390, height: 844 });
  await settle(page);
  const narrow = await strategy.evaluate((panel) => {
    const body = panel.querySelector<HTMLElement>('.panel-body')!;
    const group = [...panel.querySelectorAll<HTMLElement>('.section')]
      .find((section) => section.querySelector('h3')?.textContent === 'Elements here')!
      .querySelector<HTMLElement>('.group')!;
    const questions = [...group.querySelectorAll<HTMLElement>('.semantic-description')];
    return {
      panelHeight: panel.getBoundingClientRect().height,
      bodyOverflowY: getComputedStyle(body).overflowY,
      groupOverflowY: getComputedStyle(group).overflowY,
      groupScrolls: group.scrollHeight > group.clientHeight + 1,
      questionClips: questions.filter(
        (question) => question.scrollWidth > question.clientWidth + 1 || question.scrollHeight > question.clientHeight + 1,
      ).length,
    };
  });
  expect(narrow.panelHeight).toBeLessThanOrEqual(260);
  expect(narrow.bodyOverflowY).toBe('auto');
  expect(narrow.groupOverflowY).toBe('visible');
  expect(narrow.groupScrolls).toBe(false);
  expect(narrow.questionClips).toBe(0);
  await toggle.scrollIntoViewIfNeeded();
  await expect(toggle).toBeVisible();
});

const panelGroupSurfaces = (page: Page) =>
  page.evaluate(() =>
    [...document.getElementById('explorer')!.shadowRoot!.querySelectorAll<HTMLElement>('.detail .group, .detail .conditions')].map(
      (node) => {
        const style = getComputedStyle(node);
        return {
          kind: node.className,
          border: parseFloat(style.borderTopWidth) + parseFloat(style.borderLeftWidth),
          background: style.backgroundColor,
          image: style.backgroundImage,
        };
      },
    ),
  );

const panelBesideItsSubject = (page: Page) =>
  page.evaluate(() => {
    const shell = document.getElementById('explorer')!.shadowRoot!;
    const panel = shell.querySelector<HTMLElement>('.detail');
    const subject = shell.querySelector<HTMLElement>('.card[data-state="selected"]');
    if (!panel || !subject) return null;
    const box = panel.getBoundingClientRect();
    const seen = subject.getBoundingClientRect();
    const viewport = shell.querySelector('.viewport')!.getBoundingClientRect();
    const dock = shell.querySelector('.dock')!.getBoundingClientRect();
    return {
      subject: subject.dataset.id ?? '',
      panelCentre: (box.top + box.bottom) / 2,
      subjectCentre: (seen.top + seen.bottom) / 2,
      insideViewport: box.top >= viewport.top - 1 && box.bottom <= viewport.bottom + 1,
      clearsDock: box.bottom <= dock.top + 1,
    };
  });

test('the detail panel stands beside the subject it describes, on screen and clear of the dock', async ({ page }) => {
  await open(page);
  await explorer(page, '.view-tabs button[data-value="artifacts"]').click();
  await settle(page);
  const ids = await page.evaluate(() =>
    [...document.getElementById('explorer')!.shadowRoot!.querySelectorAll<HTMLElement>('.card[data-kind="artifact"]')].map(
      (card) => card.dataset.id!,
    ),
  );
  expect(ids.length, 'the board draws no artifact card').toBeGreaterThan(0);
  const placed: NonNullable<Awaited<ReturnType<typeof panelBesideItsSubject>>>[] = [];
  for (const id of ids) {
    await selectDetail(page, id);
    const row = await panelBesideItsSubject(page);
    expect(row, `${id} must open its panel`).not.toBeNull();
    placed.push(row!);
  }
  expect(placed.map((row) => row.subject)).toEqual(ids);
  expect(placed.filter((row) => !row.insideViewport).map((row) => row.subject)).toEqual([]);
  expect(placed.filter((row) => !row.clearsDock).map((row) => row.subject)).toEqual([]);
  const tops = placed.map((row) => row.panelCentre);
  expect(Math.max(...tops) - Math.min(...tops), 'the panel sits at the same height whatever it describes').toBeGreaterThan(0);
  const bySubject = [...placed].sort((left, right) => left.subjectCentre - right.subjectCentre);
  expect(
    bySubject.filter((row, index) => index > 0 && row.panelCentre < bySubject[index - 1].panelCentre - 1).map((row) => row.subject),
    'a lower subject drew a higher panel',
  ).toEqual([]);
  const free = placed.filter((row) => row.panelCentre > Math.min(...tops) && row.panelCentre < Math.max(...tops));
  expect(
    free
      .filter((row) => Math.abs(row.panelCentre - row.subjectCentre) > 1)
      .map((row) => `${row.subject} panel centre ${row.panelCentre.toFixed(1)} against subject ${row.subjectCentre.toFixed(1)}`),
    'a panel free of both clamps is not level with its subject',
  ).toEqual([]);
});

const NO_FILL = ['rgba(0, 0, 0, 0)', 'transparent'];

const PANELS_THAT_GROUP_WHAT_THEY_LIST = [
  { subject: 'artifact card', view: 'artifacts', counted: false, opens: '.card[data-kind="artifact"]' },
  { subject: 'element card', view: 'elements', counted: false, opens: '.card[data-kind="element"]' },
  { subject: 'frame card', view: 'frames', counted: false, opens: '.card[data-kind="frame"]' },
  { subject: 'frame-option card', view: 'frames', counted: false, opens: '.card[data-kind="option"]' },
  { subject: 'element connection', view: 'elements', counted: true, opens: '.count' },
  { subject: 'rolled-up connection', view: 'artifacts', counted: true, opens: '.count' },
] as const;

test('a panel group is drawn by a border and never by a fill, in both themes, with the guidance disclosure above the composition it qualifies', async ({
  page,
}) => {
  await open(page);
  for (const theme of ['light', 'dark'] as const) {
    for (const subject of PANELS_THAT_GROUP_WHAT_THEY_LIST) {
      await explorer(page, `.view-tabs button[data-value="${subject.view}"]`).click();
      await settle(page);
      if (subject.counted) {
        await openMenu(page);
        await explorer(page, '.settings [data-value="counts"]').click();
        await page.keyboard.press('Escape');
        await settle(page);
      }
      await explorer(page, subject.opens).first().click();
      await settle(page);
      const surfaces = await panelGroupSurfaces(page);
      expect(surfaces.length, `${theme} ${subject.subject}: the panel draws no group`).toBeGreaterThan(0);
      expect(
        surfaces.filter((surface) => !(surface.border > 0)),
        `${theme} ${subject.subject}: groups drawn without a border`,
      ).toEqual([]);
      expect(
        surfaces.filter((surface) => !NO_FILL.includes(surface.background) || surface.image !== 'none'),
        `${theme} ${subject.subject}: groups drawn with a fill`,
      ).toEqual([]);
    }
    await explorer(page, '.utilities button[aria-label^="Use "]').click();
    await settle(page);
  }
  await explorer(page, '.view-tabs button[data-value="artifacts"]').click();
  await settle(page);
  await explorer(page, '.card[data-id="artifact:design-doc"]').click();
  await settle(page);
  const order = await page.evaluate(() => {
    const body = document.getElementById('explorer')!.shadowRoot!.querySelector('.panel-body')!;
    const children = [...body.children];
    const guidance = children.findIndex((node) => node.classList.contains('guidance'));
    const composition = children.findIndex((node) => node.querySelector('.group'));
    return { guidance, composition };
  });
  expect(order.guidance, 'the panel draws a guidance disclosure').toBeGreaterThanOrEqual(0);
  expect(order.composition, 'the panel draws a composition section').toBeGreaterThanOrEqual(0);
  expect(order.guidance).toBeLessThan(order.composition);
});
