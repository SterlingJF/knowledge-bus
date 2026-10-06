import assert from 'node:assert/strict';
import { copyFileSync, existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import test from 'node:test';
import {
  GALLERY_MAP,
  checkGalleryMap,
  cropPath,
  galleryCrop,
  galleryCropRegion,
  galleryFingerprint,
  galleryInputs,
  galleryMapStatus,
  galleryRoot,
  canonicalSources,
  readFingerprint,
  renderGalleryMap,
  writeGalleryMap,
} from './gallery-map.mjs';
import { build } from 'esbuild';
import { shared } from './build.mjs';
import { root } from './generate-tokens.mjs';
import { renderSvg } from './render.mjs';

const exported =
  '<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" style="display:block;width:100vw;height:100vh" viewBox="-24 36 3663 1830" preserveAspectRatio="xMidYMid meet" role="img"><title>Product development</title><text x="10" y="20">Rollout and phasing</text></svg>\n';
const FINGERPRINT = 'sha256:' + 'a'.repeat(64);
const OTHER = 'sha256:' + 'b'.repeat(64);

const card = (id, x, y) =>
  `<g data-entity="element:${id}"><rect x="${x}" y="${y}" width="230" height="104" rx="6" fill="var(--kb-surface)" stroke="var(--kb-border)"/><text x="${x + 36}" y="${y + 27}" font-size="15">${id}</text><text x="${x + 36}" y="${y + 43}" font-size="12">One answer</text></g>`;
const band = (x, y, width, height, label) =>
  `<rect x="${x}" y="${y}" width="${width}" height="${height}" rx="14" fill="none" stroke="var(--kb-border)"/><text x="${x + 20}" y="${y + 6}" font-size="22" fill="var(--kb-text)" font-weight="500">${label}</text>`;
const banded =
  '<svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" style="display:block;width:100vw;height:100vh" viewBox="-24 36 3663 1830" preserveAspectRatio="xMidYMid meet" role="img"><title>Product development</title>' +
  band(40, 60, 2409, 459, 'Artifacts') +
  band(0, 560, 3615, 1282, 'Elements') +
  band(40, 600, 1130, 720, 'Strategy') +
  band(1240, 600, 1130, 476, 'Discovery') +
  [
    card('a', 70, 690),
    card('b', 895, 690),
    card('c', 70, 812),
    card('d', 345, 812),
    card('e', 70, 934),
    card('f', 1270, 690),
    card('g', 1270, 990),
  ].join('') +
  '</svg>\n';
const viewBox = (svg) =>
  rootTag(svg)
    .match(/ viewBox="([^"]+)"/)[1]
    .split(/\s+/)
    .map(Number);

const rootTag = (svg) => svg.match(/^<svg\b[^>]*>/)[0];
const scratch = (prefix = 'knowledge-bus-gallery-') => mkdtempSync(path.join(tmpdir(), prefix));

test('the gallery map is rendered from the bundled universe, its guidance and its marks', () => {
  assert.deepEqual(GALLERY_MAP, {
    input: 'universes/product-development/universe.kbp.yaml',
    guidance: 'universes/product-development/type-guidance.kbp.yaml',
    marks: 'universes/product-development/marks.explorer.yaml',
    svg: 'docs/assets/product-development-map.svg',
    crop: 'docs/assets/product-development-map-crop.svg',
  });
  assert.equal(cropPath(GALLERY_MAP.svg), GALLERY_MAP.crop, 'the crop sits beside the full map');
  for (const file of Object.values(GALLERY_MAP)) assert.ok(existsSync(path.join(root, file)), `${file} is missing`);
});

test('the gallery copy takes its width and height from its viewBox and drops the full-viewport sizing', () => {
  const sized = galleryRoot(exported, FINGERPRINT);
  const tag = rootTag(sized);
  assert.match(tag, / width="3663"/);
  assert.match(tag, / height="1830"/);
  assert.doesNotMatch(tag, /100%|100vw|100vh/);
  assert.match(tag, / style="display:block"/);
  assert.match(tag, / viewBox="-24 36 3663 1830"/);
  assert.match(tag, / preserveAspectRatio="xMidYMid meet"/);
  assert.match(tag, / role="img"/);
  assert.equal(sized.slice(tag.length), exported.slice(rootTag(exported).length), 'only the root element changes');
  assert.throws(() => galleryRoot('<svg xmlns="http://www.w3.org/2000/svg"></svg>', FINGERPRINT), /viewBox/);
});

test('the input fingerprint sits on the root element and reads back; a map without one has none', () => {
  const sized = galleryRoot(exported, FINGERPRINT);
  assert.match(rootTag(sized), new RegExp(` data-kb-inputs="${FINGERPRINT}"`));
  assert.equal(readFingerprint(sized), FINGERPRINT);
  assert.equal(readFingerprint(exported), undefined);
  assert.equal(readFingerprint(exported.replace('</svg>', `<g data-kb-inputs="${FINGERPRINT}"></g></svg>`)), undefined);
  assert.throws(() => galleryRoot(exported, 'md5:abc'), /sha256/);
});

test('a committed map whose fingerprint matches passes even when its bytes differ, as with other fonts', () => {
  const here = galleryRoot(exported, FINGERPRINT);
  const elsewhere = galleryRoot(exported.replace('x="10" y="20"', 'x="12" y="24"'), FINGERPRINT);
  assert.notEqual(here, elsewhere);
  assert.deepEqual(galleryMapStatus('map.svg', here, FINGERPRINT), []);
  assert.deepEqual(galleryMapStatus('map.svg', elsewhere, FINGERPRINT), []);
});

test('a committed map with a different fingerprint, or none, is stale and names the regenerate command', () => {
  const [stale] = galleryMapStatus('map.svg', galleryRoot(exported, OTHER), FINGERPRINT);
  assert.match(stale, /^map\.svg: stale; /);
  assert.match(stale, /render:explorer:gallery/);
  assert.match(stale, /just explorer-gallery/);
  const [unmarked] = galleryMapStatus('map.svg', exported, FINGERPRINT);
  assert.match(unmarked, /^map\.svg: stale; no input fingerprint/);
  assert.match(unmarked, /render:explorer:gallery/);
  const [missing] = galleryMapStatus('map.svg', undefined, FINGERPRINT);
  assert.match(missing, /^map\.svg: missing; /);
  assert.match(missing, /render:explorer:gallery/);
});

test('a committed map that is cut short, sized off its viewBox, or carries the fingerprint twice is damaged even when the fingerprint matches', () => {
  const good = galleryRoot(exported, FINGERPRINT);
  assert.deepEqual(galleryMapStatus('map.svg', good, FINGERPRINT), []);
  for (const [why, damaged] of [
    ['cut short', good.slice(0, good.indexOf('</text>'))],
    ['sized off its viewBox', good.replace(' width="3663"', ' width="300"')],
    ['no size', good.replace(' height="1830"', '')],
    ['fingerprint twice', good.replace(` data-kb-inputs="${FINGERPRINT}"`, ` data-kb-inputs="${FINGERPRINT}" data-kb-inputs="${OTHER}"`)],
  ]) {
    const failures = galleryMapStatus('map.svg', damaged, FINGERPRINT);
    assert.equal(failures.length, 1, why);
    assert.match(failures[0], /^map\.svg: damaged; /, why);
    assert.match(failures[0], /render:explorer:gallery/, why);
  }
});

test('the freshness check compares fingerprints without rendering and writes nothing beside the committed copy', async () => {
  const directory = scratch();
  const committed = path.join(directory, 'map.svg');
  const fingerprintOf = async () => FINGERPRINT;
  try {
    writeFileSync(path.join(directory, 'map-crop.svg'), galleryCrop(banded, FINGERPRINT));
    writeFileSync(committed, galleryRoot(banded, OTHER));
    assert.equal((await checkGalleryMap(committed, fingerprintOf)).length, 1);
    writeFileSync(committed, galleryRoot(banded, FINGERPRINT));
    assert.deepEqual(await checkGalleryMap(committed, fingerprintOf), []);
    assert.equal(readFileSync(committed, 'utf8'), galleryRoot(banded, FINGERPRINT));
    rmSync(committed);
    assert.match((await checkGalleryMap(committed, fingerprintOf))[0], /missing/);
    assert.equal(existsSync(committed), false);
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test('writing the gallery map stores the rendered SVG and its crop, each with a sized root and the input fingerprint', async () => {
  const directory = scratch();
  const target = path.join(directory, 'nested/map.svg');
  try {
    await writeGalleryMap(target, async () => ({ svg: banded, fingerprint: FINGERPRINT }));
    const written = readFileSync(target, 'utf8');
    assert.equal(written, galleryRoot(banded, FINGERPRINT));
    assert.deepEqual(galleryMapStatus('map.svg', written, FINGERPRINT), []);
    const crop = readFileSync(path.join(directory, 'nested/map-crop.svg'), 'utf8');
    assert.equal(crop, galleryCrop(banded, FINGERPRINT));
    assert.deepEqual(galleryMapStatus('map-crop.svg', crop, FINGERPRINT), []);
    assert.deepEqual(await checkGalleryMap(target, async () => FINGERPRINT), []);
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test('the crop region spans the first Elements group and the band labels at its left, down to the end of its second card row', () => {
  assert.deepEqual(galleryCropRegion(banded), [14, 36, 1162, 889]);
  assert.throws(() => galleryCropRegion(exported), /crop/i);
});

test('the crop is the same SVG with only its root viewBox, width and height changed, and the same fingerprint', () => {
  const crop = galleryCrop(banded, FINGERPRINT);
  const tag = rootTag(crop);
  assert.match(tag, / viewBox="14 36 1162 889"/);
  assert.match(tag, / width="1162" height="889"/);
  assert.equal(readFingerprint(crop), FINGERPRINT);
  assert.equal(crop.slice(tag.length), banded.slice(rootTag(banded).length));
});

test('the freshness check covers the crop: missing, stale, damaged, or outside the full map fails', async () => {
  const directory = scratch();
  const committed = path.join(directory, 'map.svg');
  const committedCrop = path.join(directory, 'map-crop.svg');
  const fingerprintOf = async () => FINGERPRINT;
  const crop = galleryCrop(banded, FINGERPRINT);
  try {
    writeFileSync(committed, galleryRoot(banded, FINGERPRINT));
    assert.match((await checkGalleryMap(committed, fingerprintOf)).join('\n'), /map-crop\.svg: missing; .*render:explorer:gallery/);
    writeFileSync(committedCrop, galleryCrop(banded, OTHER));
    assert.match((await checkGalleryMap(committed, fingerprintOf)).join('\n'), /map-crop\.svg: stale; /);
    writeFileSync(committedCrop, crop.replace(' width="1162"', ' width="960"'));
    assert.match((await checkGalleryMap(committed, fingerprintOf)).join('\n'), /map-crop\.svg: damaged; /);
    writeFileSync(committedCrop, galleryRoot(crop.replace(' viewBox="14 36 1162 889"', ' viewBox="-100 36 1162 889"'), FINGERPRINT));
    assert.match(
      (await checkGalleryMap(committed, fingerprintOf)).join('\n'),
      /map-crop\.svg: damaged; its viewBox lies outside the full map's viewBox/,
    );
    writeFileSync(committedCrop, crop);
    assert.deepEqual(await checkGalleryMap(committed, fingerprintOf), []);
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test('the freshness check fails a crop whose viewBox is not the region derived from the full map, even inside it with the right fingerprint', async () => {
  const directory = scratch();
  const committed = path.join(directory, 'map.svg');
  const committedCrop = path.join(directory, 'map-crop.svg');
  const fingerprintOf = async () => FINGERPRINT;
  const crop = galleryCrop(banded, FINGERPRINT);
  try {
    writeFileSync(committed, galleryRoot(banded, FINGERPRINT));
    for (const moved of ['40 36 1162 889', '14 36 1100 889', '14 60 1162 889']) {
      writeFileSync(committedCrop, galleryRoot(crop.replace(' viewBox="14 36 1162 889"', ` viewBox="${moved}"`), FINGERPRINT));
      const failures = await checkGalleryMap(committed, fingerprintOf);
      assert.equal(failures.length, 1, moved);
      assert.match(
        failures[0],
        /map-crop\.svg: damaged; its viewBox is not the crop region of the full map; .*render:explorer:gallery/,
        moved,
      );
    }
    writeFileSync(committedCrop, crop);
    assert.deepEqual(await checkGalleryMap(committed, fingerprintOf), []);
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test('the freshness check blames the full map, not the crop, when no crop region can be derived from the full map', async () => {
  const directory = scratch();
  const committed = path.join(directory, 'map.svg');
  const committedCrop = path.join(directory, 'map-crop.svg');
  const fingerprintOf = async () => FINGERPRINT;
  try {
    writeFileSync(committedCrop, galleryCrop(banded, FINGERPRINT));
    for (const [name, full] of [
      ['no bands', exported],
      ['no element cards', banded.replace(/<g data-entity="element:[^"]+">.*?<\/g>/g, '')],
    ]) {
      writeFileSync(committed, galleryRoot(full, FINGERPRINT));
      const failures = await checkGalleryMap(committed, fingerprintOf);
      assert.equal(failures.length, 1, name);
      assert.match(failures[0], /map\.svg: damaged; no crop region can be derived from it; .*render:explorer:gallery/, name);
      assert.doesNotMatch(failures[0], /map-crop\.svg/, name);
    }
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test('the fingerprint covers the prepared model, the standalone bundle and the render-path code', async () => {
  const inputs = await galleryInputs();
  assert.deepEqual(Object.keys(inputs).sort(), ['model', 'renderPath', 'script']);
  assert.equal(inputs.model.universe.id, 'product-development');
  for (const step of [renderSvg, renderGalleryMap, writeGalleryMap, galleryRoot, galleryCrop, galleryCropRegion])
    assert.ok(inputs.renderPath.includes(step.toString().replace(/\r\n?/g, '\n')), `${step.name} is not fingerprinted`);
  const base = galleryFingerprint(inputs);
  assert.match(base, /^sha256:[0-9a-f]{64}$/);
  assert.equal(galleryFingerprint(structuredClone(inputs)), base);
  assert.notEqual(galleryFingerprint({ ...inputs, script: inputs.script + ';' }), base, 'bundle change');
  assert.notEqual(galleryFingerprint({ ...inputs, renderPath: inputs.renderPath + ' ' }), base, 'render-path change');
  const relabelled = structuredClone(inputs);
  relabelled.model.universe.label += '!';
  assert.notEqual(galleryFingerprint(relabelled), base, 'model change');
  assert.equal(galleryFingerprint({ ...inputs, script: inputs.script.replace(/\n/g, '\r\n') }), base, 'line endings are not staleness');
});

const HASHED_BY_OUTPUT = new Set(['galleryInputs', 'galleryFingerprint']);
const DECLARATION = /^(?:export )?(?:async )?(?:function\*? |const |let )([\w$]+)/;

function moduleDeclarations(source) {
  const lines = source.replace(/\r\n?/g, '\n').split('\n');
  const starts = [];
  lines.forEach((line, index) => {
    if (DECLARATION.test(line) || /^(?:if|import) /.test(line)) starts.push(index);
  });
  const declarations = new Map();
  starts.forEach((start, position) => {
    const name = lines[start].match(DECLARATION)?.[1];
    if (name)
      declarations.set(
        name,
        lines
          .slice(start, starts[position + 1] ?? lines.length)
          .join('\n')
          .trim(),
      );
  });
  return declarations;
}

const valueText = (name, declaration) =>
  declaration
    .replace(/^export /, '')
    .replace(new RegExp(`^(?:const|let) ${name.replace(/\$/g, '\\$')} = `), '')
    .replace(/;$/, '');

test('the render-path fingerprint covers every module helper the render and write steps reach', async () => {
  const declarations = moduleDeclarations(readFileSync(path.join(root, 'tools/explorer/gallery-map.mjs'), 'utf8'));
  const reached = new Set();
  const pending = ['renderGalleryMap', 'writeGalleryMap', 'galleryRoot', 'galleryCrop'];
  while (pending.length) {
    const name = pending.pop();
    if (reached.has(name) || HASHED_BY_OUTPUT.has(name)) continue;
    reached.add(name);
    for (const word of declarations.get(name).match(/[A-Za-z_$][\w$]*/g)) if (declarations.has(word) && word !== name) pending.push(word);
  }
  for (const helper of ['setAttribute', 'attribute', 'ROOT_TAG', 'FINGERPRINT', 'galleryCropRegion', 'cropPath'])
    assert.ok(reached.has(helper), `${helper} is not reached`);
  const { renderPath } = await galleryInputs();
  for (const name of reached) assert.ok(renderPath.includes(valueText(name, declarations.get(name))), `${name} is not fingerprinted`);
});

test('formatting and comments in bundled CSS and JSON leave the bundle unchanged; their values do not', async () => {
  const directory = scratch();
  const bundle = async (css, json) => {
    writeFileSync(
      path.join(directory, 'entry.ts'),
      'import css from "./part.css";\nimport data from "./part.json";\nexport const value = [css, data];\n',
    );
    writeFileSync(path.join(directory, 'part.css'), css);
    writeFileSync(path.join(directory, 'part.json'), json);
    const result = await build({
      ...shared,
      absWorkingDir: directory,
      tsconfig: undefined,
      entryPoints: ['entry.ts'],
      write: false,
      plugins: [canonicalSources],
    });
    return result.outputFiles[0].text;
  };
  const css = '/* Generated. */\n.shell {\n  width: 100%;\n  --kb-canvas: light-dark(#f5f5f1, #171e22);\n}\n';
  const json = '{\n  "roles": {\n    "canvas": { "value": "#fff", "role": "page ground" }\n  }\n}\n';
  try {
    const base = await bundle(css, json);
    assert.equal(await bundle(css.replace('Generated.', 'Generated; do not edit.'), json), base, 'css comment');
    assert.equal(await bundle(css.replace('  width: 100%;', 'width:100%;'), json), base, 'css whitespace');
    assert.equal(await bundle(css, JSON.stringify(JSON.parse(json))), base, 'json layout');
    assert.notEqual(await bundle(css.replace('100%', '90%'), json), base, 'css value');
    assert.notEqual(await bundle(css, json.replace('#fff', '#000')), base, 'json value');
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test('comments, formatting and type annotations in explorer TypeScript leave the bundle unchanged; code does not', async () => {
  const directory = scratch();
  const bundle = async (ts) => {
    writeFileSync(path.join(directory, 'entry.ts'), ts);
    const result = await build({
      ...shared,
      absWorkingDir: directory,
      tsconfig: undefined,
      entryPoints: ['entry.ts'],
      write: false,
      plugins: [canonicalSources],
    });
    return result.outputFiles[0].text;
  };
  const ts = 'export const width = (n: number): string => `${n}%`;\n';
  try {
    const base = await bundle(ts);
    assert.equal(await bundle('// Width of a panel.\n' + ts), base, 'ts comment');
    assert.equal(await bundle('export const width = ( n : number ) : string =>\n    `${n}%`;\n'), base, 'ts formatting');
    assert.equal(await bundle(ts.replace('n: number', 'n: unknown')), base, 'ts type annotation');
    assert.notEqual(await bundle(ts.replace('%', 'px')), base, 'ts code');
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test('a CRLF checkout bundles the same text: sources are read with LF line endings', async () => {
  const directory = scratch();
  const bundleWith = async (eol) => {
    writeFileSync(path.join(directory, 'entry.ts'), ['import css from "./part.css";', 'export const value = css;', ''].join(eol));
    writeFileSync(path.join(directory, 'part.css'), ['.shell {', '  width: 100%;', '}', ''].join(eol));
    const result = await build({
      ...shared,
      absWorkingDir: directory,
      tsconfig: undefined,
      entryPoints: ['entry.ts'],
      write: false,
      plugins: [canonicalSources],
    });
    return result.outputFiles[0].text;
  };
  try {
    const unix = await bundleWith('\n');
    assert.ok(unix.includes('width:100%'));
    assert.equal(await bundleWith('\r\n'), unix);
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test('changing the universe, its guidance or its marks changes the fingerprint', async () => {
  const directory = scratch();
  const copy = (name) => path.join(directory, path.basename(GALLERY_MAP[name]));
  const files = { input: copy('input'), guidance: copy('guidance'), marks: copy('marks') };
  for (const name of Object.keys(files)) copyFileSync(path.join(root, GALLERY_MAP[name]), files[name]);
  const edit = (name, from, to) => {
    const text = readFileSync(files[name], 'utf8');
    assert.ok(text.includes(from), `${from} not found in ${name}`);
    writeFileSync(files[name], text.replace(from, to));
  };
  try {
    const base = galleryFingerprint(await galleryInputs({ files }));
    assert.equal(base, galleryFingerprint(await galleryInputs()), 'a copy at another path fingerprints the same');
    const seen = new Set([base]);
    for (const [name, from, to] of [
      ['input', 'label: Product development\n', 'label: Product development, revised\n'],
      ['guidance', 'Roman Pichler — Product Vision Board', 'Roman Pichler — The Product Vision Board'],
      ['marks', "glyph: 'M8 5h13", "glyph: 'M8 6h13"],
    ]) {
      edit(name, from, to);
      const changed = galleryFingerprint(await galleryInputs({ files }));
      assert.ok(!seen.has(changed), `${name} edit left the fingerprint unchanged`);
      seen.add(changed);
    }
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test('the fingerprint is the same from any working directory and scratch directory', async () => {
  const first = scratch('knowledge-bus-gallery-a-');
  const second = scratch('knowledge-bus-gallery-elsewhere-');
  const cwd = process.cwd();
  try {
    process.chdir(first);
    const fromFirst = galleryFingerprint(await galleryInputs({ scratch: first }));
    process.chdir(second);
    const fromSecond = galleryFingerprint(await galleryInputs({ scratch: second }));
    assert.equal(fromFirst, fromSecond);
  } finally {
    process.chdir(cwd);
    rmSync(first, { recursive: true, force: true });
    rmSync(second, { recursive: true, force: true });
  }
});

test('the committed gallery map and its crop declare their own size and carry the same input fingerprint', () => {
  const full = readFileSync(path.join(root, GALLERY_MAP.svg), 'utf8');
  const crop = readFileSync(path.join(root, GALLERY_MAP.crop), 'utf8');
  for (const svg of [full, crop]) {
    const tag = rootTag(svg);
    const [, , width, height] = tag.match(/ viewBox="([^"]+)"/)[1].split(/\s+/);
    assert.match(tag, new RegExp(` width="${width}" height="${height}"`));
    assert.doesNotMatch(tag, /100%|100vw|100vh/);
    assert.match(tag, / data-kb-inputs="sha256:[0-9a-f]{64}"/);
  }
  assert.equal(readFingerprint(crop), readFingerprint(full));
  assert.equal(crop.slice(rootTag(crop).length), full.slice(rootTag(full).length), 'only the root element differs');
});

test('the committed crop lies inside the full map and is narrow enough that its 12-unit text shows near 10 px at 960 px wide', () => {
  const [fx, fy, fw, fh] = viewBox(readFileSync(path.join(root, GALLERY_MAP.svg), 'utf8'));
  const [x, y, w, h] = viewBox(readFileSync(path.join(root, GALLERY_MAP.crop), 'utf8'));
  assert.ok(x >= fx && y >= fy && x + w <= fx + fw && y + h <= fy + fh, `crop ${[x, y, w, h]} is outside ${[fx, fy, fw, fh]}`);
  assert.ok(w <= 1170, `crop is ${w} units wide`);
  assert.ok((12 * 960) / w >= 9.8, `smallest text shows at ${((12 * 960) / w).toFixed(1)} px`);
});

test('the explorer pipeline checks the gallery map beside the generated-artifact check, and a script regenerates it', () => {
  const { scripts } = JSON.parse(readFileSync(path.join(root, 'package.json'), 'utf8'));
  assert.equal(scripts['render:explorer:gallery'], 'node tools/explorer/gallery-map.mjs --write');
  assert.equal(scripts['check:explorer:gallery'], 'node tools/explorer/gallery-map.mjs --check');
  assert.match(scripts['test:explorer'], / check:explorer:artifacts check:explorer:gallery$/);
  assert.match(readFileSync(path.join(root, 'justfile'), 'utf8'), /^explorer-gallery: \(_pnpm_run 'render:explorer:gallery'\)$/m);
});

test('CI checks the gallery map in a job with node and uv but no browser', () => {
  const workflow = readFileSync(path.join(root, '.github/workflows/ci.yml'), 'utf8');
  const job = workflow.match(/\n {2}checks-static:\n([\s\S]*?)(?=\n {2}[\w-]+:\n)/)[1];
  assert.match(job, /- run: pnpm run check:explorer:gallery\n/);
  assert.match(job, /setup-uv/);
  assert.doesNotMatch(job, /playwright install/);
});

test('the README shows the crop at an explicit width, lets it set its height, and links it to the full map', () => {
  const readme = readFileSync(path.join(root, 'README.md'), 'utf8');
  assert.doesNotMatch(readme, /!\[[^\]]*\]\(docs\/assets\/product-development-map/);
  assert.match(readme, new RegExp(`<a href="${GALLERY_MAP.svg}"><img src="${GALLERY_MAP.crop}" alt="[^"]+" width="\\d+" /></a>`));
  assert.doesNotMatch(readme, new RegExp(`<img src="${GALLERY_MAP.crop}"[^>]*\\sheight=`));
  assert.doesNotMatch(readme, new RegExp(`<img src="${GALLERY_MAP.svg}"`), 'the unreadable full-width embed is gone');
});
