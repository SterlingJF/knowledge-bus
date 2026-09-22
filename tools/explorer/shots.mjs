import { chromium } from '@playwright/test';
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { parseArgs } from 'node:util';
import { readAuthority, root, SELECTORS, tokenLeaves } from './generate-tokens.mjs';

export const artifactPath = path.join(root, 'dist/explorer/product-development.html');

const VIEWPORT = { width: 1600, height: 1000 };
const DEVICE_SCALE_FACTOR = 2;
const ZOOM_TOLERANCE = 0.005;
const CLICKS_PAST_CLAMP = 12;
const SETTLE_POLLS = 80;
const SETTLE_INTERVAL = 40;
const PARK_COLUMNS = 48;
const PARK_ROWS = 30;
const SELECTED_CARD = 'element:key-activities';
const SELECTED_CARD_POSITION = { x: 8, y: 5 };
const ROUNDING = 1e4;

export const ZOOM_LADDER = [
  { zoom: 0.15, control: 'Zoom out', clicks: CLICKS_PAST_CLAMP },
  { zoom: 0.4096, control: 'Zoom out', clicks: 4 },
  { zoom: 0.512, control: 'Zoom out', clicks: 3 },
  { zoom: 0.64, control: 'Zoom out', clicks: 2 },
  { zoom: 0.8, control: 'Zoom out', clicks: 1 },
  { zoom: 1, control: 'Zoom in', clicks: 0 },
  { zoom: 1.25, control: 'Zoom in', clicks: 1 },
  { zoom: 1.5625, control: 'Zoom in', clicks: 2 },
  { zoom: 1.8, control: 'Zoom in', clicks: CLICKS_PAST_CLAMP },
];

export const VIEW_TABS = { frames: 0, artifacts: 1, elements: 2 };

export const TIERS = {
  step: {
    views: ['elements'],
    states: ['idle', 'card-selected'],
    themes: ['dark', 'light'],
    zooms: [0.4096, 1, 1.8],
  },
  stage: {
    views: ['frames', 'artifacts', 'elements'],
    states: ['idle', 'card-selected', 'connection-selected'],
    themes: ['dark', 'light'],
    zooms: [0.15, 0.4096, 0.8, 1, 1.25, 1.8],
  },
};

export const MEASUREMENTS = [
  { key: 'card-box', selector: '.card', metric: 'box' },
  { key: 'card-border', selector: '.card', metric: 'borderTopWidth' },
  { key: 'card-radius', selector: '.card', metric: 'borderTopLeftRadius' },
  { key: 'card-title-font', selector: '.card-title', metric: 'fontSize' },
  { key: 'card-subtitle-font', selector: '.card-subtitle', metric: 'fontSize' },
  { key: 'boundary-heading-font', selector: '.boundary-title', metric: 'fontSize' },
  { key: 'boundary-caption-font', selector: '.boundary-caption', metric: 'fontSize' },
  { key: 'count-badge-box', selector: '.count', metric: 'box' },
  { key: 'count-badge-radius', selector: '.count', metric: 'borderTopLeftRadius' },
  { key: 'count-badge-border', selector: '.count', metric: 'borderTopWidth' },
  { key: 'count-badge-font', selector: '.count', metric: 'fontSize' },
  { key: 'nub-line-stroke', selector: '.nub-line', metric: 'strokeWidth' },
  { key: 'connection-label-box', selector: '.label', metric: 'box' },
  { key: 'connection-label-radius', selector: '.label', metric: 'borderTopLeftRadius' },
  { key: 'connection-label-font', selector: '.label', metric: 'fontSize' },
  { key: 'label-leader-stroke', selector: '.leader', metric: 'strokeWidth' },
  { key: 'connection-wire-stroke', selector: '.wire', metric: 'strokeWidth' },
];

export const POPULATIONS = [{ key: 'count-badges-inset', selector: '.count.count-inset' }];

const ZOOM_GROWTH = 'zoom-growth';

const selectorClasses = (selector) => selector.split('.').filter(Boolean);

const wornBy = (selector, worn) => selectorClasses(worn).every((className) => selectorClasses(selector).includes(className));

export function cameraResponsiveMetrics(authority = readAuthority()) {
  const grown = Object.values(authority.parts ?? {})
    .filter((part) => tokenLeaves(part).includes(ZOOM_GROWTH))
    .flatMap((part) => part[SELECTORS] ?? []);
  return [...MEASUREMENTS, ...POPULATIONS]
    .filter((spec) => grown.some((selector) => wornBy(spec.selector, selector)))
    .map((spec) => spec.key);
}

const measuredValue = (entry) =>
  Object.entries(entry)
    .filter(([field]) => field !== 'sample')
    .map(([, value]) => value)
    .join('x');

export function frozenCameraMetrics(manifest, keys = cameraResponsiveMetrics()) {
  const captured = manifest.shots.filter((shot) => shot.captured);
  if (new Set(captured.map((shot) => shot.zoom)).size < 2) return [];
  const findings = [];
  for (const key of keys) {
    const zooms = new Set();
    const values = new Set();
    for (const shot of captured) {
      const entry = shot.geometry?.[key];
      if (!entry) continue;
      zooms.add(shot.zoom);
      values.add(measuredValue(entry));
    }
    if (!values.size) findings.push({ key, held: null, zooms: [] });
    else if (zooms.size > 1 && values.size === 1) findings.push({ key, held: [...values][0], zooms: [...zooms].sort((a, b) => a - b) });
  }
  return findings;
}

export const describeFrozenMetric = (finding) =>
  finding.held === null
    ? `${finding.key} was measured in no captured shot`
    : `${finding.key} held ${finding.held} at every zoom of ${finding.zooms.join(', ')}`;

const shell = (page, selector) => page.locator('#explorer').locator(selector);

const viewerState = (page) => page.evaluate(() => document.getElementById('explorer').explorerViewer.getState());

const liveScale = (page) =>
  page.evaluate(
    () => new DOMMatrixReadOnly(getComputedStyle(document.getElementById('explorer').shadowRoot.querySelector('.world')).transform).a,
  );

export const shotName = ({ view, state, theme, zoom }) => `${view}-${state}-${theme}-z${zoom.toFixed(4)}`;

export function plan(tier) {
  const recipe = TIERS[tier];
  if (!recipe) throw new Error(`Unknown tier ${tier}; expected step or stage.`);
  return recipe.views.flatMap((view) =>
    recipe.states.flatMap((state) => recipe.themes.flatMap((theme) => recipe.zooms.map((zoom) => ({ view, state, theme, zoom })))),
  );
}

async function settle(page) {
  let previous = '';
  for (let poll = 0; poll < SETTLE_POLLS; poll += 1) {
    await page.waitForTimeout(SETTLE_INTERVAL);
    const current = await page.evaluate(() => {
      const host = document.getElementById('explorer');
      const world = host.shadowRoot.querySelector('.world');
      return JSON.stringify([host.explorerViewer.getState().camera, getComputedStyle(world).transform]);
    });
    if (current === previous) return;
    previous = current;
  }
  throw new Error('The camera never settled.');
}

async function openFresh(context) {
  const page = await context.newPage();
  const pageErrors = [];
  page.on('pageerror', (error) => pageErrors.push(error.message));
  page.on('console', (message) => {
    if (message.type() === 'error') pageErrors.push(message.text());
  });
  await page.route(/^(?!file:)/, (route) => route.abort());
  await page.goto(pathToFileURL(artifactPath).href);
  await page.waitForFunction(() => !!document.getElementById('explorer')?.explorerViewer);
  await page.waitForFunction(() => document.fonts.status === 'loaded');
  await page.evaluate(async () => {
    await document.fonts.ready;
  });
  await settle(page);
  return { page, pageErrors };
}

async function showView(page, view) {
  await shell(page, '.view-tabs button').nth(VIEW_TABS[view]).click();
  await settle(page);
  const shown = (await viewerState(page)).options.view;
  if (shown !== view) throw new Error(`The ${view} tab left the viewer showing ${shown}.`);
}

async function useTheme(page, theme) {
  for (let attempt = 0; attempt <= 2; attempt += 1) {
    const resolved = await page.evaluate(() => {
      const board = document.getElementById('explorer').shadowRoot.querySelector('.shell');
      return { marked: board.dataset.theme, scheme: getComputedStyle(board).colorScheme };
    });
    if (resolved.marked === theme && resolved.scheme === theme) return;
    await shell(page, '.utilities button[aria-label^="Use "]').click();
    await settle(page);
  }
  throw new Error(`The theme control never resolved the shell to ${theme}.`);
}

async function enterState(page, state) {
  if (state === 'idle') return { reached: true };
  if (state === 'card-selected') {
    const card = shell(page, `.card[data-id="${SELECTED_CARD}"]`);
    if ((await card.count()) === 0) return { reached: false, reason: `This view draws no card for ${SELECTED_CARD}.` };
    await card.click({ position: SELECTED_CARD_POSITION });
    await settle(page);
    const selected = (await viewerState(page)).selection.entity;
    if (selected !== SELECTED_CARD) return { reached: false, reason: `Clicking the card selected ${selected || 'nothing'}.` };
    return { reached: true, subject: selected };
  }
  const badge = shell(page, 'button.count').first();
  if ((await badge.count()) === 0) return { reached: false, reason: 'This view draws no count badges.' };
  await badge.click();
  await settle(page);
  const selected = (await viewerState(page)).selection.connection;
  if (!selected) return { reached: false, reason: 'Clicking the first count badge selected no connection.' };
  return { reached: true, subject: selected };
}

async function reachZoom(page, zoom) {
  const rung = ZOOM_LADDER.find((step) => step.zoom === zoom);
  if (!rung) throw new Error(`No dock route reaches zoom ${zoom}.`);
  const dock = (label) => shell(page, `.dock button[aria-label="${label}"]`);
  await dock('Reset zoom to 100%').click();
  for (let click = 0; click < rung.clicks; click += 1) await dock(rung.control).click();
  await settle(page);
  const scale = await liveScale(page);
  if (Math.abs(scale - zoom) > ZOOM_TOLERANCE) throw new Error(`Dock clicks reached a scale of ${scale} rather than ${zoom}.`);
  return scale;
}

async function parkPointer(page) {
  const clear = await page.evaluate(
    ([columns, rows]) => {
      const board = document.getElementById('explorer').shadowRoot;
      const frame = board.querySelector('.viewport').getBoundingClientRect();
      const reactive =
        '.card, .count, .label, .boundary, button, a, summary, input, .detail, .legend, .topbar, .dock, .minimap, .settings, .overview, .scrim';
      for (let row = 0; row < rows; row += 1)
        for (let column = 0; column < columns; column += 1) {
          const x = Math.round(frame.left + (frame.width * (column + 0.5)) / columns);
          const y = Math.round(frame.top + (frame.height * (row + 0.5)) / rows);
          const node = board.elementFromPoint(x, y);
          if (node && !node.closest(reactive)) return { x, y };
        }
      return null;
    },
    [PARK_COLUMNS, PARK_ROWS],
  );
  if (!clear) throw new Error('No point in the viewport is clear of cards and controls.');
  await page.mouse.move(clear.x, clear.y);
  await page.waitForFunction(() => !document.getElementById('explorer').shadowRoot.querySelector('[data-preview="true"]'));
  return clear;
}

async function measure(page) {
  const measured = await page.evaluate(
    ({ specs, populations }) => {
      const board = document.getElementById('explorer').shadowRoot;
      const scale = new DOMMatrixReadOnly(getComputedStyle(board.querySelector('.world')).transform).a;
      const grownBy = (transform) => (transform === 'none' ? 1 : new DOMMatrixReadOnly(transform).a);
      const geometry = {};
      for (const spec of specs) {
        const node = board.querySelector(spec.selector);
        if (!node) continue;
        const sample = node.closest('[data-id]')?.dataset.id || node.textContent.trim().slice(0, 48) || spec.selector;
        if (spec.metric === 'box') {
          const box = node.getBoundingClientRect();
          geometry[spec.key] = { sample, width: box.width / scale, height: box.height / scale };
        } else {
          const style = getComputedStyle(node);
          geometry[spec.key] = { sample, value: parseFloat(style[spec.metric]) * grownBy(style.transform) };
        }
      }
      for (const spec of populations)
        geometry[spec.key] = { sample: spec.selector, population: board.querySelectorAll(spec.selector).length };
      return { scale, geometry };
    },
    { specs: MEASUREMENTS, populations: POPULATIONS },
  );
  const round = (value) => Math.round(value * ROUNDING) / ROUNDING;
  for (const entry of Object.values(measured.geometry))
    for (const field of ['width', 'height', 'value']) if (field in entry) entry[field] = round(entry[field]);
  return measured.geometry;
}

export async function capture({ out, tier, onShot = () => {} }) {
  if (!existsSync(artifactPath))
    throw new Error('dist/explorer/product-development.html is missing; run build:explorer and render:explorer first.');
  mkdirSync(out, { recursive: true });
  const shots = plan(tier);
  const browser = await chromium.launch();
  const records = [];
  try {
    const context = await browser.newContext({
      viewport: VIEWPORT,
      deviceScaleFactor: DEVICE_SCALE_FACTOR,
      reducedMotion: 'reduce',
      forcedColors: 'none',
      colorScheme: 'light',
      locale: 'en-US',
      timezoneId: 'UTC',
    });
    for (const shot of shots) {
      const name = shotName(shot);
      const { page, pageErrors } = await openFresh(context);
      try {
        await showView(page, shot.view);
        await useTheme(page, shot.theme);
        const state = await enterState(page, shot.state);
        if (!state.reached) {
          records.push({ ...shot, name, captured: false, reason: state.reason });
          onShot(records.at(-1));
          continue;
        }
        const achievedScale = await reachZoom(page, shot.zoom);
        const pointer = await parkPointer(page);
        const geometry = await measure(page);
        await page.screenshot({ path: path.join(out, `${name}.png`), animations: 'disabled', caret: 'hide', scale: 'device' });
        records.push({
          ...shot,
          name,
          file: `${name}.png`,
          captured: true,
          subject: state.subject ?? null,
          achievedScale,
          pointer,
          geometry,
          ...(pageErrors.length ? { pageErrors: [...pageErrors] } : {}),
        });
        onShot(records.at(-1));
      } finally {
        await page.close();
      }
    }
  } finally {
    await browser.close();
  }
  const manifest = {
    tier,
    artifact: path.relative(root, artifactPath),
    artifactSha256: createHash('sha256').update(readFileSync(artifactPath)).digest('hex'),
    viewport: { ...VIEWPORT, deviceScaleFactor: DEVICE_SCALE_FACTOR },
    geometryUnit: 'board',
    planned: shots.length,
    captured: records.filter((record) => record.captured).length,
    shots: records,
  };
  const frozen = frozenCameraMetrics(manifest);
  if (frozen.length)
    throw new Error(
      ['This capture measured the camera without following it, so no manifest was written:', ...frozen.map(describeFrozenMetric)].join(
        '\n  ',
      ),
    );
  writeFileSync(path.join(out, 'manifest.json'), JSON.stringify(manifest, null, 2) + '\n');
  return manifest;
}

export const CAPTURE_NOISE_LIMITS = { maxChannelDelta: 8, differingFraction: 0.00002 };

const shotNames = (directory) =>
  new Set(
    existsSync(directory)
      ? readdirSync(directory)
          .filter((entry) => entry.endsWith('.png'))
          .map((entry) => entry.slice(0, -'.png'.length))
      : [],
  );

const shotDataUrl = (directory, name) => 'data:image/png;base64,' + readFileSync(path.join(directory, `${name}.png`)).toString('base64');

export function geometryByShot(directory) {
  const manifestFile = path.join(directory, 'manifest.json');
  if (!existsSync(manifestFile)) throw new Error(`${manifestFile} is missing, so the geometry cannot be compared.`);
  const manifest = JSON.parse(readFileSync(manifestFile, 'utf8'));
  return new Map(manifest.shots.filter((record) => record.captured).map((record) => [record.name, record.geometry]));
}

export function geometryComparison(left, right) {
  const shared = [...left.keys()].filter((name) => right.has(name)).sort();
  return {
    compared: shared.length,
    differing: shared.filter((name) => JSON.stringify(left.get(name)) !== JSON.stringify(right.get(name))),
  };
}

export function shotVerdict(measured, limits) {
  if (!measured.sized) return 'resized';
  if (measured.maxDelta > limits.maxChannelDelta) return 'changed';
  return measured.differing < measured.pixels * limits.differingFraction ? 'noise' : 'changed';
}

const differenceRank = (measured) => (measured.sized ? measured.maxDelta * 1e10 + measured.differing : Number.MAX_SAFE_INTEGER);

async function measureDifference(page, leftUrl, rightUrl) {
  return page.evaluate(
    async ([leftSource, rightSource]) => {
      const decode = (source) =>
        new Promise((resolve, reject) => {
          const image = new Image();
          image.onload = () => resolve(image);
          image.onerror = () => reject(new Error('The browser could not decode a shot.'));
          image.src = source;
        });
      const [before, after] = await Promise.all([decode(leftSource), decode(rightSource)]);
      if (before.naturalWidth !== after.naturalWidth || before.naturalHeight !== after.naturalHeight)
        return {
          sized: false,
          leftSize: { width: before.naturalWidth, height: before.naturalHeight },
          rightSize: { width: after.naturalWidth, height: after.naturalHeight },
        };
      const width = before.naturalWidth;
      const height = before.naturalHeight;
      const samples = (image) => {
        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        const surface = canvas.getContext('2d', { willReadFrequently: true });
        surface.drawImage(image, 0, 0);
        return surface.getImageData(0, 0, width, height).data;
      };
      const left = samples(before);
      const right = samples(after);
      let differing = 0;
      let maxDelta = 0;
      let leastColumn = width;
      let mostColumn = -1;
      let leastRow = height;
      let mostRow = -1;
      for (let offset = 0; offset < left.length; offset += 4) {
        let delta = 0;
        for (let channel = 0; channel < 4; channel += 1) {
          const gap = Math.abs(left[offset + channel] - right[offset + channel]);
          if (gap > delta) delta = gap;
        }
        if (delta === 0) continue;
        differing += 1;
        if (delta > maxDelta) maxDelta = delta;
        const pixel = offset / 4;
        const column = pixel % width;
        const row = (pixel - column) / width;
        if (column < leastColumn) leastColumn = column;
        if (column > mostColumn) mostColumn = column;
        if (row < leastRow) leastRow = row;
        if (row > mostRow) mostRow = row;
      }
      return {
        sized: true,
        pixels: width * height,
        differing,
        maxDelta,
        box: mostColumn < 0 ? null : { x: leastColumn, y: leastRow, width: mostColumn - leastColumn + 1, height: mostRow - leastRow + 1 },
      };
    },
    [leftUrl, rightUrl],
  );
}

export async function compare({ left, right, limits = CAPTURE_NOISE_LIMITS, onShot = () => {} }) {
  const leftShots = shotNames(left);
  const rightShots = shotNames(right);
  const shared = [...leftShots].filter((name) => rightShots.has(name)).sort();
  if (!shared.length) throw new Error(`${left} and ${right} share no shot.`);
  const geometry = geometryComparison(geometryByShot(left), geometryByShot(right));
  const browser = await chromium.launch();
  const shots = [];
  try {
    const page = await browser.newPage();
    await page.setContent('<!doctype html><title>explorer compare</title>');
    for (const name of shared) {
      const measured = await measureDifference(page, shotDataUrl(left, name), shotDataUrl(right, name));
      shots.push({ name, ...measured, verdict: shotVerdict(measured, limits) });
      onShot(shots.at(-1));
    }
  } finally {
    await browser.close();
  }
  const worst = [...shots].sort((a, b) => differenceRank(b) - differenceRank(a))[0] ?? null;
  return {
    left,
    right,
    limits,
    geometry,
    onlyLeft: [...leftShots].filter((name) => !rightShots.has(name)).sort(),
    onlyRight: [...rightShots].filter((name) => !leftShots.has(name)).sort(),
    shots,
    worst,
    passed: geometry.differing.length === 0 && shots.every((shot) => shot.verdict === 'noise'),
  };
}

export function describeShotDifference(shot) {
  if (!shot.sized)
    return `${shot.name} ${shot.verdict} ${shot.leftSize.width}x${shot.leftSize.height} against ${shot.rightSize.width}x${shot.rightSize.height}`;
  const share = ((shot.differing / shot.pixels) * 100).toFixed(5);
  const box = shot.box ? `box ${shot.box.width}x${shot.box.height} at ${shot.box.x},${shot.box.y}` : 'box none';
  return `${shot.name} ${shot.verdict} ${shot.differing} px ${share}% delta ${shot.maxDelta} ${box}`;
}

export function formatComparison(report) {
  const geometry = report.geometry.differing.length
    ? `geometry differs on ${report.geometry.differing.length} of ${report.geometry.compared}: ${report.geometry.differing.join(', ')}`
    : `geometry identical across ${report.geometry.compared} shots`;
  const unmatched = [
    report.onlyLeft.length ? `${report.onlyLeft.length} only in ${report.left}` : '',
    report.onlyRight.length ? `${report.onlyRight.length} only in ${report.right}` : '',
  ].filter(Boolean);
  const held = report.shots.filter((shot) => shot.verdict === 'noise').length;
  return [
    `explorer compare: ${report.left} against ${report.right}`,
    `explorer compare: ${geometry}`,
    ...(unmatched.length ? [`explorer compare: ${unmatched.join('; ')}`] : []),
    `explorer compare: worst shot ${report.worst ? describeShotDifference(report.worst) : 'none'}`,
    `explorer compare: limits max channel delta ${report.limits.maxChannelDelta}, differing under ${report.limits.differingFraction * 100}%`,
    `explorer compare: ${held} of ${report.shots.length} shots within capture noise`,
  ].join('\n');
}

function runComparison(values, positionals) {
  const limits = {
    maxChannelDelta: values['max-delta'] === undefined ? CAPTURE_NOISE_LIMITS.maxChannelDelta : Number(values['max-delta']),
    differingFraction: values['max-fraction'] === undefined ? CAPTURE_NOISE_LIMITS.differingFraction : Number(values['max-fraction']),
  };
  return compare({
    left: path.resolve(positionals[0]),
    right: path.resolve(positionals[1]),
    limits,
    onShot: (shot) => console.log(`explorer compare: ${describeShotDifference(shot)}`),
  }).then((report) => {
    console.log(formatComparison(report));
    process.exitCode = report.passed ? 0 : 1;
  });
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const { values, positionals } = parseArgs({
    options: {
      out: { type: 'string' },
      tier: { type: 'string' },
      compare: { type: 'boolean', default: false },
      'max-delta': { type: 'string' },
      'max-fraction': { type: 'string' },
    },
    allowPositionals: true,
  });
  const fail = (error) => {
    console.error(error.message);
    process.exitCode = 1;
  };
  if (values.compare && positionals.length !== 2) {
    console.error('Usage: node tools/explorer/shots.mjs --compare <dirA> <dirB> [--max-delta n] [--max-fraction f]');
    process.exitCode = 2;
  } else if (values.compare) runComparison(values, positionals).catch(fail);
  else if (!values.out || !TIERS[values.tier ?? '']) {
    console.error('Usage: node tools/explorer/shots.mjs --out <dir> --tier step|stage');
    process.exitCode = 2;
  } else
    capture({
      out: path.resolve(values.out),
      tier: values.tier,
      onShot: (record) =>
        console.log(record.captured ? `explorer shots: ${record.file}` : `explorer shots: skipped ${record.name} — ${record.reason}`),
    }).then((manifest) => console.log(`explorer shots: ${manifest.captured} of ${manifest.planned} ${manifest.tier} shots written`), fail);
}
