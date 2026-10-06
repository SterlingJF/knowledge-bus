import { transform } from 'esbuild';
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { parseArgs } from 'node:util';
import { buildStandaloneSource, shared } from './build.mjs';
import { root } from './generate-tokens.mjs';
import { composeHtml, prepareModel, renderSvg } from './render.mjs';

export const GALLERY_MAP = {
  input: 'universes/product-development/universe.kbp.yaml',
  guidance: 'universes/product-development/type-guidance.kbp.yaml',
  marks: 'universes/product-development/marks.explorer.yaml',
  svg: 'docs/assets/product-development-map.svg',
  crop: 'docs/assets/product-development-map-crop.svg',
};

const SCHEME = 'knowledge-bus/gallery-map-inputs/1';
const FINGERPRINT = /^sha256:[0-9a-f]{64}$/;
const ROOT_TAG = /^<svg\b[^>]*>/;
const REGENERATE = 'run render:explorer:gallery or just explorer-gallery';

export const cropPath = (svgPath) => svgPath.replace(/\.svg$/, '') + '-crop.svg';

const shown = (file) => (path.relative(root, file).startsWith('..') ? file : path.relative(root, file));
const lf = (text) => text.replace(/\r\n?/g, '\n');
const attribute = (name) => new RegExp(`\\s${name}="([^"]*)"`);

function setAttribute(tag, name, value) {
  const pattern = attribute(name);
  return pattern.test(tag) ? tag.replace(pattern, ` ${name}="${value}"`) : tag.replace(/\/?>$/, (end) => ` ${name}="${value}"${end}`);
}

export function galleryRoot(svg, fingerprint) {
  if (!FINGERPRINT.test(fingerprint)) throw new Error('Gallery map fingerprint must be sha256:<64 hex digits>.');
  const tag = svg.match(ROOT_TAG)?.[0];
  if (!tag) throw new Error('Gallery map has no root <svg> element.');
  const box = tag
    .match(attribute('viewBox'))?.[1]
    .trim()
    .split(/[\s,]+/);
  if (box?.length !== 4) throw new Error('Gallery map root has no viewBox to take its size from.');
  let sized = setAttribute(setAttribute(tag, 'width', box[2]), 'height', box[3]);
  const style = sized.match(attribute('style'))?.[1];
  if (style !== undefined) {
    const kept = style
      .split(';')
      .filter((declaration) => declaration.trim() && !/^\s*(width|height)\s*:/i.test(declaration))
      .join(';');
    sized = kept ? setAttribute(sized, 'style', kept) : sized.replace(attribute('style'), '');
  }
  return setAttribute(sized, 'data-kb-inputs', fingerprint) + svg.slice(tag.length);
}

const viewBoxOf = (tag) =>
  tag
    .match(attribute('viewBox'))?.[1]
    .trim()
    .split(/[\s,]+/)
    .map(Number);

const CROP_PAD = 6;
const BAND = /<rect x="([^"]+)" y="([^"]+)" width="([^"]+)" height="([^"]+)" rx="14"[^>]*\/><text x="([^"]+)"[^>]*>([^<]+)<\/text>/g;
const CARD = /<g data-entity="element:[^"]+"><rect x="([^"]+)" y="([^"]+)" width="([^"]+)" height="([^"]+)"/g;

export function galleryCropRegion(svg) {
  const view = viewBoxOf(svg.match(ROOT_TAG)?.[0] ?? '');
  const bands = [...svg.matchAll(BAND)].map(([, x, y, width, height, labelX, label]) => ({
    x: +x,
    y: +y,
    width: +width,
    height: +height,
    labelX: +labelX,
    label,
  }));
  const artifacts = bands.find((found) => found.label === 'Artifacts');
  const elements = bands.find((found) => found.label === 'Elements');
  const inside = (outer, x, y) => x >= outer.x && y >= outer.y && x <= outer.x + outer.width && y <= outer.y + outer.height;
  const group = bands
    .filter((found) => found !== elements && elements && inside(elements, found.x, found.y))
    .sort((a, b) => a.y - b.y || a.x - b.x)[0];
  if (view?.length !== 4 || !artifacts || !group)
    throw new Error('Gallery map crop: the render has no viewBox, Artifacts band, or Elements group to take the crop region from.');
  const cards = [...svg.matchAll(CARD)]
    .map(([, x, y, width, height]) => ({ x: +x, y: +y, bottom: +y + +height }))
    .filter((found) => inside(group, found.x, found.y));
  const rows = [...new Set(cards.map((found) => found.y))].sort((a, b) => a - b);
  if (!rows.length) throw new Error('Gallery map crop: the first Elements group has no element cards to take the crop region from.');
  const shownRow = rows[Math.min(1, rows.length - 1)];
  const rowBottom = Math.max(...cards.filter((found) => found.y === shownRow).map((found) => found.bottom));
  const next = rows[rows.indexOf(shownRow) + 1];
  const left = Math.min(artifacts.labelX, elements.labelX) - CROP_PAD;
  const right = group.x + group.width + CROP_PAD;
  const top = view[1];
  const bottom = next === undefined ? rowBottom + CROP_PAD : (rowBottom + next) / 2;
  const round = (value) => Math.round(value * 10) / 10;
  return [round(left), round(top), round(right - left), round(bottom - top)];
}

export function galleryCrop(svg, fingerprint) {
  const tag = svg.match(ROOT_TAG)?.[0];
  if (!tag) throw new Error('Gallery map has no root <svg> element.');
  return galleryRoot(setAttribute(tag, 'viewBox', galleryCropRegion(svg).join(' ')) + svg.slice(tag.length), fingerprint);
}

const SOURCE_LOADERS = { '.ts': 'ts', '.json': 'json', ...shared.loader };
const CANONICAL = {
  '.ts': async (text) => text,
  '.css': async (text) => (await transform(text, { loader: 'css', minifyWhitespace: true, legalComments: 'none' })).code,
  '.json': async (text) => JSON.stringify(JSON.parse(text)),
};
export const canonicalSources = {
  name: 'canonical-sources',
  setup(builder) {
    builder.onLoad({ filter: /\.(ts|css|json)$/ }, async (args) => ({
      contents: await CANONICAL[path.extname(args.path)](lf(readFileSync(args.path, 'utf8'))),
      loader: SOURCE_LOADERS[path.extname(args.path)],
    }));
  },
};

export const readFingerprint = (svg) => svg.match(ROOT_TAG)?.[0].match(attribute('data-kb-inputs'))?.[1];

export async function galleryInputs({ files = GALLERY_MAP, scratch } = {}) {
  const directory = scratch ?? mkdtempSync(path.join(tmpdir(), 'knowledge-bus-gallery-'));
  try {
    const model = prepareModel(
      path.resolve(root, files.input),
      path.join(directory, 'map.model.json'),
      path.resolve(root, files.guidance),
      path.resolve(root, files.marks),
    );
    const script = lf(await buildStandaloneSource({ plugins: [canonicalSources] }));
    const renderPath = lf(
      [
        renderSvg,
        renderGalleryMap,
        writeGalleryMap,
        galleryRoot,
        galleryCrop,
        galleryCropRegion,
        viewBoxOf,
        cropPath,
        setAttribute,
        attribute,
        shown,
        ROOT_TAG,
        FINGERPRINT,
        CROP_PAD,
        BAND,
        CARD,
      ]
        .map(String)
        .join('\n'),
    );
    return { model, script, renderPath };
  } finally {
    if (!scratch) rmSync(directory, { recursive: true, force: true });
  }
}

export function galleryFingerprint({ model, script, renderPath }) {
  const html = composeHtml({ model, script: lf(script) });
  return (
    'sha256:' +
    createHash('sha256')
      .update(JSON.stringify([SCHEME, html, lf(renderPath)]))
      .digest('hex')
  );
}

export async function renderGalleryMap() {
  const scratch = mkdtempSync(path.join(tmpdir(), 'knowledge-bus-gallery-'));
  try {
    const inputs = await galleryInputs({ scratch });
    const htmlPath = path.join(scratch, 'map.html');
    writeFileSync(htmlPath, composeHtml(inputs));
    return { svg: (await renderSvg(htmlPath)) + '\n', fingerprint: galleryFingerprint(inputs) };
  } finally {
    rmSync(scratch, { recursive: true, force: true });
  }
}

function damage(committed) {
  const tag = committed.match(ROOT_TAG)[0];
  const box = tag
    .match(attribute('viewBox'))?.[1]
    .trim()
    .split(/[\s,]+/);
  const found = [];
  const marks = tag.match(new RegExp(attribute('data-kb-inputs').source, 'g')).length;
  if (marks !== 1) found.push(`its root carries the input fingerprint ${marks} times`);
  if (box?.length !== 4 || tag.match(attribute('width'))?.[1] !== box[2] || tag.match(attribute('height'))?.[1] !== box[3])
    found.push('its root width and height do not match its viewBox');
  if (!/<\/svg>\s*$/.test(committed)) found.push('it does not end with </svg>');
  return found;
}

export function galleryMapStatus(name, committed, fingerprint) {
  if (committed === undefined) return [`${name}: missing; ${REGENERATE}`];
  const recorded = readFingerprint(committed);
  if (recorded === undefined) return [`${name}: stale; no input fingerprint on its root element; ${REGENERATE}`];
  const found = damage(committed);
  if (found.length) return [`${name}: damaged; ${found.join('; ')}; ${REGENERATE}`];
  if (recorded === fingerprint) return [];
  return [`${name}: stale; the definitions or explorer code changed since it was rendered (${recorded} now ${fingerprint}); ${REGENERATE}`];
}

const currentFingerprint = async () => galleryFingerprint(await galleryInputs());
const readIfThere = (file) => (existsSync(file) ? readFileSync(file, 'utf8') : undefined);

function cropOutside(crop, full) {
  const [x, y, width, height] = viewBoxOf(crop.match(ROOT_TAG)[0]);
  const [fx, fy, fw, fh] = viewBoxOf(full.match(ROOT_TAG)[0]);
  return !(x >= fx && y >= fy && x + width <= fx + fw && y + height <= fy + fh);
}

const sameBox = (found, expected) => found?.length === expected.length && found.every((value, index) => value === expected[index]);

function derivedRegion(full) {
  try {
    return galleryCropRegion(full);
  } catch {
    return undefined;
  }
}

export async function checkGalleryMap(committedPath, fingerprintOf = currentFingerprint, committedCropPath = cropPath(committedPath)) {
  const full = readIfThere(committedPath);
  const crop = readIfThere(committedCropPath);
  const fingerprint = await fingerprintOf();
  const failures = [
    ...galleryMapStatus(shown(committedPath), full, fingerprint),
    ...galleryMapStatus(shown(committedCropPath), crop, fingerprint),
  ];
  if (failures.length) return failures;
  const region = derivedRegion(full);
  if (region === undefined) failures.push(`${shown(committedPath)}: damaged; no crop region can be derived from it; ${REGENERATE}`);
  else if (cropOutside(crop, full))
    failures.push(`${shown(committedCropPath)}: damaged; its viewBox lies outside the full map's viewBox; ${REGENERATE}`);
  else if (!sameBox(viewBoxOf(crop.match(ROOT_TAG)[0]), region))
    failures.push(`${shown(committedCropPath)}: damaged; its viewBox is not the crop region of the full map; ${REGENERATE}`);
  return failures;
}

export async function writeGalleryMap(targetPath, renderMap = renderGalleryMap, cropTarget = cropPath(targetPath)) {
  const { svg, fingerprint } = await renderMap();
  const full = galleryRoot(svg, fingerprint);
  const crop = galleryCrop(svg, fingerprint);
  for (const [file, text] of [
    [targetPath, full],
    [cropTarget, crop],
  ]) {
    mkdirSync(path.dirname(file), { recursive: true });
    writeFileSync(file, text);
  }
  return [shown(targetPath), shown(cropTarget)].join(', ');
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const { values } = parseArgs({ options: { write: { type: 'boolean' }, check: { type: 'boolean' }, svg: { type: 'string' } } });
  const target = path.resolve(root, values.svg ?? GALLERY_MAP.svg);
  if (values.write === values.check) {
    console.error('Usage: node tools/explorer/gallery-map.mjs --write|--check [--svg <committed.svg>]');
    process.exitCode = 2;
  } else if (values.write)
    writeGalleryMap(target).then(
      (written) => console.log('gallery map: wrote ' + written),
      (error) => {
        console.error(error.message);
        process.exitCode = 1;
      },
    );
  else
    checkGalleryMap(target).then(
      (failures) => {
        for (const failure of failures) console.error(failure);
        console.log(failures.length ? 'gallery map: stale' : 'gallery map: matches its inputs');
        process.exitCode = failures.length ? 1 : 0;
      },
      (error) => {
        console.error(error.message);
        process.exitCode = 1;
      },
    );
}
