import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { composeHtml, embedJson } from './render.mjs';
import { checkHtml, checkSvg } from './check-artifacts.mjs';
import { auditCSS, auditRuntime, validateAuthority, validateExceptions } from './token-contract.mjs';
import { closedSelectors, flattenAuthority, tokenCss, themeValues } from './generate-tokens.mjs';
import { CAPTURE_NOISE_LIMITS, cameraResponsiveMetrics, frozenCameraMetrics, geometryComparison, shotVerdict } from './shots.mjs';

const model = { schema: 'knowledge-bus/explorer-model/1', wiring: [], universe: { label: 'Test <b>&</b>', id: 'test' }, entities: [] };

test('composed HTML embeds an inert model and refuses a script terminator', () => {
  const html = composeHtml({ model, script: 'console.log(1)' });
  assert.match(html, /<title>Test &lt;b&gt;&amp;&lt;\/b&gt;/);
  assert.match(html, /id="explorer-model">\{"schema"/);
  assert.doesNotMatch(html.split('id="explorer-model">')[1].split('</script>')[0], /[<>&]/);
  assert.throws(() => composeHtml({ model, script: 'a="</script>"' }));
  assert.equal(embedJson(' '), '"\\u2028"');
  assert.deepEqual(checkHtml('good.html', html), []);
});

test('artifact checks refuse external, unsafe or incomplete output', () => {
  const good = composeHtml({ model, script: 'var x=1' });
  assert.ok(checkHtml('bad.html', good.replace('<script>', '<script src="https://cdn.example/x.js"></script><script>')).length);
  assert.ok(checkHtml('bad.html', good.replace('var x=1', 'fetch("https://example.com")')).length);
  assert.ok(checkHtml('bad.html', good.replace('var x=1', 'var p="/Users/someone/x"')).length);
  assert.ok(checkHtml('bad.html', good.replace('<noscript>', '<span>')).length);
  assert.ok(checkHtml('bad.html', good.replace('"wiring":[]', '"w":[]')).length);
});

test('a mark a universe declares must travel inside the artifact, never as a reference out of it', () => {
  const marked = {
    ...model,
    marks: { id: 'test-marks', label: 'Test', version: '1', marksFor: 'test', declared: { 'frame:one': { glyph: 'M4 4h16v16H4Z' } } },
  };
  const inlined = composeHtml({ model: marked, script: 'var x=1' });
  assert.deepEqual(checkHtml('good.html', inlined), []);
  const referencedInstead = ['url(#one)', '#one', 'https://example.com/one.svg', '//example.com/one.svg', 'one.svg', 'frame'];
  for (const reference of referencedInstead)
    assert.ok(
      checkHtml('bad.html', inlined.replace('M4 4h16v16H4Z', reference)).length,
      `a declared mark reading ${reference} reached the artifact unrefused`,
    );
  assert.ok(checkHtml('bad.html', inlined.replace('"glyph"', '"href"')).length);
});

test('SVG checks require both themes, resolved variables, cards and no scripts', () => {
  const svg =
    '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 10 10" role="img"><title>T</title><desc>D</desc>' +
    '<style>svg{--kb-canvas:#000000;--kb-text:#ffffff}@media(prefers-color-scheme:light){svg{--kb-canvas:#ffffff;--kb-text:#000000}}</style>' +
    '<rect fill="var(--kb-canvas)"/><g data-entity="e"><text x="1" y="1" fill="var(--kb-text)">e</text></g></svg>';
  assert.deepEqual(checkSvg('good.svg', svg), []);
  assert.ok(checkSvg('bad.svg', svg.replace('<rect', '<foreignObject></foreignObject><rect')).length);
  assert.ok(checkSvg('bad.svg', svg.replace('var(--kb-canvas)', 'var(--kb-missing)')).length);
  assert.ok(checkSvg('bad.svg', svg.replace(/@media[^}]+\}\}/, '')).length);
  assert.ok(checkSvg('bad.svg', svg.replace('<g data-entity="e">', '<g data-entity="e"><script>1</script>')).length);
  assert.ok(checkSvg('bad.svg', svg.replace('--kb-canvas:#ffffff;--kb-text:#000000', '--kb-canvas:#000000;--kb-text:#ffffff')).length);
  assert.ok(checkSvg('bad.svg', svg.replace('#000000', 'light-dark(#fff,#000)')).length);
  assert.ok(checkSvg('bad.svg', svg.replace('<text x="1"', '<text x="NaN"')).length);
});

test('the token contract refuses literals, unknown tokens and relabelled sizes', () => {
  const tokens = { '--kb-control-height': { kind: 'length', value: '28px', role: 'Control height' } };
  assert.equal(auditCSS('.close{height:var(--kb-control-height)}', tokens).length, 0);
  assert.ok(auditCSS('.close{height:28px}', tokens).length);
  assert.ok(auditCSS('.close{color:red}', tokens).length);
  assert.ok(auditCSS('.close{height:var(--kb-missing)}', tokens).length);
  assert.ok(auditCSS(':root{--kb-control-height:32px}', tokens).length);
  for (const source of [
    "el.style.height='28px';",
    "el.setAttribute('font-size','12');",
    "Object.assign(el.style,{width:'30px'});",
    "const size=29; el.style.height=size+'px';",
  ])
    assert.ok(auditRuntime(source, tokens).length, source);
  assert.equal(auditRuntime("el.style.height=tokenValue('--kb-control-height');", tokens).length, 0);
  assert.equal(auditRuntime('el.style.left = `${card.x}px`;', tokens).length, 0);
  assert.ok(
    validateAuthority({
      '--kb-a': { kind: 'color', value: 'var(--kb-b)', role: 'A' },
      '--kb-b': { kind: 'color', value: 'var(--kb-a)', role: 'B' },
    }).length,
  );
  assert.ok(validateAuthority({ '--kb-a': { kind: 'color', value: 'var(--kb-missing)', role: 'A' } }).length);
  const finding = { file: 'a.css', property: 'height', value: '29px', reason: 'Unclassified visual literal' };
  assert.ok(validateExceptions([finding], [{ ...finding, reason: 'Pretend this is geometry' }]).length);
});

test('exceptions must match a real finding exactly, once, with a reason', () => {
  const finding = { file: 'layout.ts', property: 'width', value: 'bounds.width', line: 2 };
  const exception = { ...finding, reason: 'Measured world-space width; not an authored visual size.' };
  assert.equal(validateExceptions([finding], [exception]).length, 0);
  assert.ok(validateExceptions([], [exception]).length);
  assert.ok(validateExceptions([finding], [{ ...exception, value: 'other.width' }]).length);
  assert.ok(validateExceptions([finding], [{ ...exception, reason: '' }]).length);
  assert.ok(validateExceptions([finding], [exception, exception]).length);
});

test('generated token CSS and export themes come from the authority alone', () => {
  const manifest = {
    scope: '.shell',
    roles: { color: { canvas: { kind: 'color', value: 'light-dark(#fff,#000)', role: 'Canvas' } } },
    parts: {},
  };
  assert.equal(
    tokenCss(manifest),
    '/* Generated from visual-tokens.json. Do not edit. */\n.shell{\n  --kb-canvas: light-dark(#fff,#000);\n}\n',
  );
  assert.equal(themeValues(manifest, 'light')['--kb-canvas'], '#fff');
  assert.equal(themeValues(manifest, 'dark')['--kb-canvas'], '#000');
});

test('a tier is a naming rule: the palette is bare, another role carries its group, and a part carries its own name', () => {
  const manifest = {
    scope: '.shell',
    roles: {
      color: { canvas: { kind: 'color', value: '#fff', role: 'Canvas' } },
      radius: { 10: { kind: 'length', value: '10px', role: 'Badge corner' } },
    },
    parts: { count: { selectors: ['.count'], radius: { kind: 'length', value: 'var(--kb-radius-10)', role: 'Count — corner' } } },
  };
  assert.deepEqual(Object.keys(flattenAuthority(manifest)), ['--kb-canvas', '--kb-radius-10', '--kb-count-radius']);
  const owned = { ...manifest, parts: { count: { ...manifest.parts.count, closed: true } } };
  assert.deepEqual(Object.keys(flattenAuthority(owned)), ['--kb-canvas', '--kb-radius-10', '--kb-count-radius']);
  assert.deepEqual(closedSelectors(manifest), {});
  assert.deepEqual(closedSelectors(owned), { count: ['.count'] });
  assert.throws(
    () => flattenAuthority({ roles: { radius: { 10: { value: '10px' } } }, parts: { radius: { 10: { value: '9px' } } } }),
    /--kb-radius-10/,
  );
});

test('a shot comparison separates capture noise from a real change', () => {
  const pixels = 6400000;
  const noisy = { sized: true, pixels, differing: 11, maxDelta: 5 };
  assert.equal(shotVerdict(noisy, CAPTURE_NOISE_LIMITS), 'noise');
  assert.equal(shotVerdict({ ...noisy, maxDelta: 9 }, CAPTURE_NOISE_LIMITS), 'changed');
  assert.equal(shotVerdict({ ...noisy, differing: 128 }, CAPTURE_NOISE_LIMITS), 'changed');
  assert.equal(shotVerdict({ ...noisy, differing: 127 }, CAPTURE_NOISE_LIMITS), 'noise');
  assert.equal(shotVerdict({ sized: false }, CAPTURE_NOISE_LIMITS), 'resized');
  assert.equal(shotVerdict(noisy, { maxChannelDelta: 4, differingFraction: 1 }), 'changed');
});

test('a geometry comparison judges only the shots both captures measured', () => {
  const left = new Map([
    ['a', { 'card-box': { width: 1 } }],
    ['b', { 'card-box': { width: 2 } }],
  ]);
  const right = new Map([
    ['a', { 'card-box': { width: 1 } }],
    ['c', { 'card-box': { width: 9 } }],
  ]);
  assert.deepEqual(geometryComparison(left, right), { compared: 1, differing: [] });
  assert.deepEqual(geometryComparison(left, new Map([['a', { 'card-box': { width: 3 } }]])), { compared: 1, differing: ['a'] });
});

test('a captured metric follows the camera exactly when its part declares a growth bound, and then never holds still across zooms', () => {
  const cardHeading = (leaves) => ({ parts: { 'card-heading': { selectors: ['.card'], ...leaves } } });
  const text = { text: { kind: 'color', value: 'var(--kb-ink)', role: 'Card heading — text' } };
  const growth = { 'zoom-growth': { kind: 'number', value: 'var(--kb-zoom-growth-sm)', role: 'Card heading — zoom growth limit' } };
  assert.deepEqual(cameraResponsiveMetrics(cardHeading({ ...text, ...growth })), ['card-box', 'card-border', 'card-radius']);
  assert.deepEqual(cameraResponsiveMetrics(cardHeading(text)), []);
  const responsive = cameraResponsiveMetrics();
  assert.ok(responsive.includes('count-badges-inset'));
  const shot = (zoom, patch = {}) => ({
    view: 'elements',
    state: 'idle',
    theme: 'dark',
    zoom,
    captured: true,
    geometry: {
      ...Object.fromEntries(responsive.map((key) => [key, { sample: key, value: zoom }])),
      'card-border': { sample: '.card', value: 3 },
      ...patch,
    },
  });
  const pinned = { 'count-badge-font': { sample: '8', value: 12 } };
  const frozen = frozenCameraMetrics({ shots: [shot(0.4096, pinned), shot(1, pinned), shot(1.8, pinned)] });
  assert.deepEqual(
    frozen.map((finding) => finding.key),
    ['count-badge-font'],
  );
  assert.equal(frozen[0].held, '12');
  assert.deepEqual(frozen[0].zooms, [0.4096, 1, 1.8]);
  assert.deepEqual(frozenCameraMetrics({ shots: [shot(0.4096), shot(1), shot(1.8)] }), []);
  assert.deepEqual(frozenCameraMetrics({ shots: [shot(1), shot(1)] }), []);
  const dropped = (zoom) => {
    const record = shot(zoom);
    delete record.geometry['count-badge-radius'];
    return record;
  };
  assert.deepEqual(
    frozenCameraMetrics({ shots: [dropped(0.4096), dropped(1), dropped(1.8)] }).map((finding) => finding.key),
    ['count-badge-radius'],
  );
  const uncaptured = { view: 'frames', state: 'idle', theme: 'dark', zoom: 1, captured: false, reason: 'no cards' };
  assert.deepEqual(frozenCameraMetrics({ shots: [shot(0.4096), shot(1), shot(1.8), uncaptured] }), []);
});

test('a new literal stops the token gate', () => {
  const dir = mkdtempSync(path.join(tmpdir(), 'explorer-token-'));
  try {
    const file = path.join(dir, 'a.css');
    writeFileSync(file, '.a{height:43px}');
    assert.ok(auditCSS('.a{height:43px}', {}).some((f) => f.value.includes('43px')));
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});
