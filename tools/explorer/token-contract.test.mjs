import test from 'node:test';
import assert from 'node:assert/strict';
import {
  auditCSS,
  auditLadders,
  auditPartReach,
  auditRoleReach,
  auditRoles,
  auditTokenOwnership,
  auditRuntime,
  auditThemeNumbers,
  auditZoomGrowth,
  valueNamedTokens,
  validateAuthority,
  validateExceptions,
} from './token-contract.mjs';
import { selectorsByToken } from './tokens-report.mjs';
import { closedSelectors } from './generate-tokens.mjs';
const tokens = { '--kb-control-height': { kind: 'length', value: '28px', role: 'Control height' } };
test('rejects hardcoded close size and state mixtures', () => {
  assert.ok(auditCSS('.close{height:28px}', tokens).length);
  assert.ok(auditCSS('.close:hover{background:color-mix(in srgb,var(--kb-control-height) 7%,transparent)}', tokens).length);
});
test('accepts token consumption, rejects missing tokens and redeclarations', () => {
  assert.equal(auditCSS('.close{height:var(--kb-control-height)}', tokens).length, 0);
  assert.ok(auditCSS('.close{height:var(--kb-missing)}', tokens).length);
  assert.ok(auditCSS(':root{--kb-control-height:32px}', tokens).length);
});
test('a fallback on a var the authority does not own cannot smuggle a literal past the gate', () => {
  assert.ok(auditCSS('.x{color:var(--rogue, #ff00ff)}', tokens).length);
  assert.ok(auditCSS('.x{height:var(--rogue, 28px)}', tokens).length);
  assert.ok(auditCSS('.x{opacity:var(--rogue, 0.5)}', tokens).length);
  assert.ok(auditCSS('.x{color:var(--rogue, red)}', tokens).length);
  assert.ok(auditCSS('.x{background:var(--rogue, rgba(0, 0, 0, 0.5))}', tokens).length);
  assert.ok(auditCSS('.x{transform:scale(var(--outer, var(--inner, 2)))}', tokens).length);
});
test('a fallback inside a token var is judged by the same rule, so the prefix buys no exemption', () => {
  const owned = { '--kb-space-8': { kind: 'length', value: '8px', role: 'Gap' } };
  assert.equal(auditCSS('.x{padding:var(--kb-space-8)}', owned).length, 0);
  assert.ok(auditCSS('.x{padding:var(--kb-space-8, 12px)}', owned).length);
  assert.equal(auditCSS('.x{transform:scale(var(--kb-space-8, 1))}', owned).length, 0);
});
test('an identity fallback carries no visual quantity, so it stays legal', () => {
  assert.equal(auditCSS('.x{transform:scale(var(--zoom-scale, 1))}', tokens).length, 0);
  assert.equal(auditCSS('.x{stroke-width:calc(var(--kb-control-height) * var(--zoom-scale, 1))}', tokens).length, 0);
  assert.equal(auditCSS('.x{margin-left:var(--part-offset, 0)}', tokens).length, 0);
  assert.equal(auditCSS('.x{background:var(--card-accent)}', tokens).length, 0);
  assert.equal(auditCSS('.x{height:var(--rogue, var(--kb-control-height))}', tokens).length, 0);
  assert.equal(auditCSS('.x{display:var(--rogue, block)}', tokens).length, 0);
});
test('a border is floored to whole device pixels, so its width never follows the camera by calc', () => {
  const followsTheCamera = (css) => auditCSS(css, tokens).filter((finding) => finding.reason === 'Border width follows the camera');
  for (const property of ['border-width', 'border-top-width', 'border-inline-start-width'])
    assert.equal(followsTheCamera(`.x{${property}:calc(var(--kb-control-height) * var(--zoom-scale, 1))}`).length, 1, property);
  for (const property of ['border', 'border-left', 'border-block-end'])
    assert.equal(
      followsTheCamera(`.x{${property}:calc(var(--kb-control-height) * var(--zoom-scale, 1)) solid var(--card-accent)}`).length,
      1,
      property,
    );
  assert.equal(followsTheCamera('.x{border-width:calc(var(--zoom-scale) * var(--kb-control-height))}').length, 1);
  assert.deepEqual(followsTheCamera('.x{border:var(--kb-control-height) solid var(--card-accent)}'), []);
  for (const property of ['stroke-width', 'border-radius', 'font-size'])
    assert.deepEqual(followsTheCamera(`.x{${property}:calc(var(--kb-control-height) * var(--zoom-scale, 1))}`), [], property);
  assert.deepEqual(followsTheCamera('.x{transform:scale(var(--zoom-scale, 1))}'), []);
  const excepted = followsTheCamera('.x{border-width:calc(var(--kb-control-height) * var(--zoom-scale, 1))}').map((finding) => ({
    ...finding,
    file: 'a.css',
  }));
  assert.ok(
    validateExceptions(
      excepted,
      excepted.map((finding) => ({ ...finding, reason: 'It looked like the pattern' })),
    ).some((error) => error.startsWith('Non-exemptible authority violation')),
  );
});
test('runtime visual literals are audited, including SVG and style objects', () => {
  for (const source of [
    "b.style.height='28px';",
    "b.setAttribute('font-size','12');",
    "Object.assign(b.style,{width:'30px'});",
    'b.innerHTML=`<span style="padding:6px">x</span>`;',
  ])
    assert.ok(auditRuntime(source, tokens).length, source);
  assert.equal(auditRuntime("b.style.height='var(--kb-control-height)';", tokens).length, 0);
});
test('a literal smuggled through a var fallback is caught in runtime styling, as it is in a stylesheet', () => {
  const owned = { '--kb-space-8': { kind: 'length', value: '8px', role: 'Gap' } };
  assert.ok(auditCSS('.x{height:var(--kb-space-8, 12px)}', owned).length);
  assert.ok(auditRuntime('b.innerHTML=`<span style="height:var(--kb-space-8, 12px)">x</span>`;', owned).length);
  assert.ok(auditRuntime("b.style.height='var(--kb-space-8, 12px)';", owned).length);
  assert.ok(auditRuntime("b.style['height']='var(--kb-space-8, 12px)';", owned).length);
  assert.ok(auditRuntime("b.style.setProperty('height','var(--kb-space-8, 12px)');", owned).length);
  assert.ok(auditRuntime("Object.assign(b.style,{height:'var(--kb-space-8, 12px)'});", owned).length);
  assert.ok(auditRuntime("b.setAttribute('width','var(--kb-space-8, 12px)');", owned).length);
  assert.equal(auditRuntime("b.style.transform='scale(var(--kb-space-8, 1))';", owned).length, 0);
  assert.equal(auditRuntime("b.style.height='var(--kb-space-8)';", owned).length, 0);
});
test('a named colour is caught in runtime styling, as it is in a stylesheet', () => {
  assert.ok(auditCSS('.x{color:red}', tokens).length);
  for (const source of [
    "b.style.color='red';",
    "b.style.backgroundColor='red';",
    "b.style['color']='red';",
    "b.style.setProperty('color','red');",
    "Object.assign(b.style,{color:'red'});",
    "b.setAttribute('fill','red');",
    "b.setAttribute('style','color:red');",
    'b.innerHTML=`<circle fill="red"/>`;',
  ])
    assert.ok(auditRuntime(source, tokens).length, source);
  for (const source of [
    "b.style.color='var(--kb-control-height)';",
    "b.style.fill='none';",
    "b.style.color='transparent';",
    "b.setAttribute('fill','currentColor');",
    "b.style.display='block';",
    "b.style.pointerEvents='stroke';",
  ])
    assert.equal(auditRuntime(source, tokens).length, 0, source);
});
test('indirect and multiline styling cannot silently bypass the gate', () => {
  for (const source of [
    "const size=29; b.style.height=size+'px';",
    "b.style['height']='29px';",
    "Object.assign(b.style, {\nheight:'29px'\n});",
    "b.setAttribute('style','height:29px');",
  ])
    assert.ok(auditRuntime(source, tokens).length, source);
  assert.ok(auditCSS('.close{color:red}', tokens).length);
});
test('fixed styling cannot be relabeled as a structural exception', () => {
  const f = { file: 'a.css', property: 'height', value: '29px', reason: 'Unclassified visual literal' };
  assert.ok(validateExceptions([f], [{ ...f, reason: 'Pretend this is geometry' }]).length);
  const smuggled = { file: 'a.css', property: 'color', value: 'var(--rogue, #ff00ff)', reason: 'Literal in a var fallback' };
  assert.ok(validateExceptions([smuggled], [{ ...smuggled, reason: 'Pretend the rogue property always resolves' }]).length);
});
test('authority rejects cycles and unresolved aliases', () => {
  assert.ok(
    validateAuthority({
      '--kb-a': { kind: 'color', value: 'var(--kb-b)', role: 'A' },
      '--kb-b': { kind: 'color', value: 'var(--kb-a)', role: 'B' },
    }).length,
  );
  assert.ok(validateAuthority({ '--kb-a': { kind: 'color', value: 'var(--kb-missing)', role: 'A' } }).length);
});
test('a token value may only reference other tokens, so every token finishes at build time', () => {
  assert.equal(
    validateAuthority({
      '--kb-a': { kind: 'color', value: 'var(--kb-b)', role: 'A' },
      '--kb-b': { kind: 'color', value: '#000', role: 'B' },
    }).length,
    0,
  );
  const contextual = { '--kb-a': { kind: 'color', value: 'color-mix(in srgb,var(--supplied) 15%,#000)', role: 'A' } };
  assert.ok(validateAuthority(contextual).length);
});
test('a kind that does not describe its own value is refused', () => {
  assert.ok(validateAuthority({ '--kb-stroke-1': { kind: 'color', value: '1px', role: 'Hairline' } }).length);
  assert.ok(validateAuthority({ '--kb-space-8': { kind: 'length', value: '8', role: 'Gap' } }).length);
  assert.ok(validateAuthority({ '--kb-leading-1-5': { kind: 'number', value: '1.5px', role: 'Leading' } }).length);
  assert.ok(validateAuthority({ '--kb-motion-camera': { kind: 'duration', value: '420', role: 'Camera glide' } }).length);
  assert.ok(validateAuthority({ '--kb-font-sans': { kind: 'font', value: '13px', role: 'Interface face' } }).length);
  assert.ok(validateAuthority({ '--kb-view-tabs-box-shadow': { kind: 'shadow', value: '#0001', role: 'Detail lift' } }).length);
  assert.ok(validateAuthority({ '--kb-canvas': { kind: 'color', value: 'light-dark(#f5f5f1,12px)', role: 'Canvas' } }).length);
});
const shorthands = {
  gradient: { value: 'radial-gradient(#d7dddf .7px,transparent .7px) 0 0/24px 24px', role: 'Board field' },
  transition: { value: 'background-color .12s,border-color .12s', role: 'Control ease' },
  filter: { value: 'brightness(1.04)', role: 'Hover lift' },
};
test('color, duration and number describe one value each, so a shorthand is refused', () => {
  assert.ok(validateAuthority({ '--kb-viewport-background': { kind: 'color', ...shorthands.gradient } }).length);
  assert.ok(validateAuthority({ '--kb-control-transition': { kind: 'duration', ...shorthands.transition } }).length);
  assert.ok(validateAuthority({ '--kb-card-hover-filter': { kind: 'number', ...shorthands.filter } }).length);
});
test('paint, transition and filter describe the shapes color, duration and number refuse', () => {
  assert.equal(validateAuthority({ '--kb-viewport-background': { kind: 'paint', ...shorthands.gradient } }).length, 0);
  assert.equal(validateAuthority({ '--kb-control-transition': { kind: 'transition', ...shorthands.transition } }).length, 0);
  assert.equal(validateAuthority({ '--kb-card-hover-filter': { kind: 'filter', ...shorthands.filter } }).length, 0);
});
test('the three new kinds are not a second home for any value at all', () => {
  assert.ok(validateAuthority({ '--kb-space-8': { kind: 'paint', value: '8px', role: 'Gap' } }).length);
  assert.ok(validateAuthority({ '--kb-motion-camera': { kind: 'transition', value: '420ms', role: 'Camera glide' } }).length);
  assert.ok(validateAuthority({ '--kb-leading-1-5': { kind: 'filter', value: '1.5', role: 'Leading' } }).length);
});
test('a kind is judged at the end of the alias chain, not at the alias', () => {
  assert.equal(
    validateAuthority({
      '--kb-count-border': { kind: 'length', value: 'var(--kb-stroke-1)', role: 'Count border' },
      '--kb-stroke-1': { kind: 'length', value: '1px', role: 'Hairline' },
    }).length,
    0,
  );
  assert.ok(
    validateAuthority({
      '--kb-count-border': { kind: 'length', value: 'var(--kb-accent)', role: 'Count border' },
      '--kb-accent': { kind: 'color', value: 'light-dark(#f5f5f1,#171e22)', role: 'Accent' },
    }).length,
  );
});
test('every shape the authority already ships satisfies its own kind', () => {
  assert.equal(
    validateAuthority({
      '--kb-border': { kind: 'color', value: 'light-dark(#d7dddf,#3b454c)', role: 'Border' },
      '--kb-shadow-faint': { kind: 'color', value: '#0001', role: 'Faint shadow' },
      '--kb-element': { kind: 'color', value: 'light-dark(#347773,#93c5bf)', role: 'Element' },
      '--kb-boundary-scope-background': {
        kind: 'color',
        value: 'color-mix(in srgb,var(--kb-border) 3%,var(--kb-element))',
        role: 'Scope wash',
      },
      '--kb-viewport-background': {
        kind: 'paint',
        value: 'radial-gradient(var(--kb-border) .7px,transparent .7px) 0 0/24px 24px',
        role: 'Board field',
      },
      '--kb-space--8': { kind: 'length', value: '-8px', role: 'Negative gap' },
      '--kb-card-hover-filter': { kind: 'filter', value: 'brightness(1.04)', role: 'Hover lift' },
      '--kb-connection-dash-mixed': { kind: 'number', value: '12 3 3 3', role: 'Mixed dash' },
      '--kb-motion-camera': { kind: 'duration', value: '420ms', role: 'Camera glide' },
      '--kb-control-transition': { kind: 'transition', value: 'background-color .12s,border-color .12s', role: 'Control ease' },
      '--kb-font-sans': { kind: 'font', value: '-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif', role: 'Interface face' },
      '--kb-view-tabs-box-shadow': { kind: 'shadow', value: '0 2px 8px var(--kb-shadow-faint)', role: 'Detail lift' },
      '--kb-chip-pressed-box-shadow': { kind: 'shadow', value: 'inset 0 0 0 1px var(--kb-element)', role: 'Options ring' },
      '--kb-card-selected-ring-frame': {
        kind: 'shadow',
        value: '0 0 0 5px color-mix(in srgb,var(--kb-element) 12%,transparent)',
        role: 'Selected ring',
      },
    }).length,
    0,
  );
});
const themed = {
  '--kb-hairline': { kind: 'length', value: 'light-dark(1px,2px)', role: 'Theme-split hairline' },
  '--kb-count-border': { kind: 'length', value: 'var(--kb-hairline)', role: 'Count border' },
  '--kb-space-8': { kind: 'length', value: '8px', role: 'Gap' },
};
test('a token that changes with the theme may never be read as a number', () => {
  assert.ok(auditThemeNumbers("const edge = tokenNumber('--kb-hairline');", themed).length);
  assert.ok(auditThemeNumbers("const edge = tokenNumber('--kb-count-border');", themed).length);
  assert.ok(auditThemeNumbers('const edge = round(tokenNumber("--kb-count-border") * 2);', themed).length);
});
test('a theme-independent token stays readable as a number, and reading a value is never a number read', () => {
  assert.equal(auditThemeNumbers("const gap = tokenNumber('--kb-space-8');", themed).length, 0);
  assert.equal(auditThemeNumbers("const edge = tokenValue('--kb-hairline');", themed).length, 0);
  assert.equal(auditThemeNumbers("const edge = paint('--kb-hairline');", themed).length, 0);
  assert.equal(auditThemeNumbers('export function tokenNumber(name: TokenName): number {', themed).length, 0);
});
const selfNaming = {
  '--kb-radius-10': { kind: 'length', value: '10px', role: 'Radius' },
  '--kb-stroke-1-5': { kind: 'length', value: '1.5px', role: 'Hairline' },
  '--kb-radius-5-6': { kind: 'length', value: '5.6px', role: 'Nub radius' },
  '--kb-opacity--4': { kind: 'number', value: '.4', role: 'Dimmed' },
  '--kb-space--8': { kind: 'length', value: '-8px', role: 'Negative gap' },
  '--kb-count-radius': { kind: 'length', value: 'var(--kb-radius-10)', role: 'Count radius' },
  '--kb-control-height': { kind: 'length', value: '28px', role: 'Control height' },
  '--kb-dock-box-shadow-2': { kind: 'shadow', value: '0 8px 24px var(--kb-radius-10)', role: 'Dock lift' },
};
test('a token whose name ends in its own value cannot change value without a rename', () => {
  assert.deepEqual(valueNamedTokens(selfNaming).sort(), [
    '--kb-opacity--4',
    '--kb-radius-10',
    '--kb-radius-5-6',
    '--kb-space--8',
    '--kb-stroke-1-5',
  ]);
});
const ladders = {
  space: {
    base: 4,
    fineWork: [1, 2, 3, 6, 10],
    '0-25': { kind: 'length', value: '1px', role: 'Hairline gap' },
    1: { kind: 'length', value: '4px', role: 'Small control padding' },
    5: { kind: 'length', value: '20px', role: 'Boundary inset' },
  },
  radius: { md: { kind: 'length', value: '6px', role: 'The one button and card corner' } },
};
test('a ladder step is a multiple of its base, or the ladder says it is fine work', () => {
  assert.deepEqual(auditLadders(ladders), []);
  const strayed = { ...ladders, space: { ...ladders.space, '2-75': { kind: 'length', value: '11px', role: 'Stray step' } } };
  const findings = auditLadders(strayed);
  assert.equal(findings.length, 1);
  assert.match(findings[0], /--kb-space-2-75/);
  assert.match(findings[0], /11px/);
  assert.match(findings[0], /space ladder/);
  assert.match(findings[0], /\b4\b/);
  const finer = { ...strayed, space: { ...strayed.space, fineWork: [...ladders.space.fineWork, 11] } };
  assert.deepEqual(auditLadders(finer), []);
  const unladdered = { ...strayed, space: Object.fromEntries(Object.entries(strayed.space).filter(([leaf]) => leaf !== 'base')) };
  assert.deepEqual(auditLadders(unladdered), []);
});
const zoomGrowths = {
  '--kb-zoom-growth-sm': { kind: 'number', value: '1', role: 'One dock zoom step of compensation' },
  '--kb-zoom-growth-lg': { kind: 'number', value: '2', role: 'Two dock zoom steps of compensation' },
  '--kb-count-zoom-growth': { kind: 'number', value: 'var(--kb-zoom-growth-sm)', role: 'Count badge — zoom growth' },
  '--kb-label-zoom-growth': { kind: 'number', value: 'var(--kb-zoom-growth-lg)', role: 'Connection label — zoom growth' },
  '--kb-heading-zoom-growth': { kind: 'number', value: '0', role: 'Boundary heading — zoom growth' },
};
test("a zoom growth is a whole number of dock steps, so the ladder is the dock's own scale", () => {
  assert.deepEqual(auditZoomGrowth(zoomGrowths), []);
  const offRung = { ...zoomGrowths, '--kb-zoom-growth-lg': { ...zoomGrowths['--kb-zoom-growth-lg'], value: '1.54' } };
  const findings = auditZoomGrowth(offRung);
  assert.equal(findings.length, 1);
  assert.match(findings[0], /--kb-label-zoom-growth/);
  assert.match(findings[0], /1\.54/);
  const shrinking = { ...zoomGrowths, '--kb-heading-zoom-growth': { ...zoomGrowths['--kb-heading-zoom-growth'], value: '-1' } };
  assert.equal(auditZoomGrowth(shrinking).length, 1);
  const factor = { ...zoomGrowths, '--kb-count-zoom-growth': { ...zoomGrowths['--kb-count-zoom-growth'], value: '1.25' } };
  assert.equal(auditZoomGrowth(factor).length, 1);
  assert.deepEqual(auditZoomGrowth({ '--kb-zoom-step': { kind: 'number', value: '1.25', role: 'One dock click' } }), []);
});
test('exceptions match exact findings; unused, duplicated, and unexplained exceptions fail', () => {
  const finding = { file: 'layout.js', property: 'width', value: 'bounds.width', line: 2 };
  const exception = { ...finding, reason: 'Measured world-space width; not an authored visual size.' };
  assert.equal(validateExceptions([finding], [exception]).length, 0);
  assert.ok(validateExceptions([], [exception]).length);
  assert.ok(validateExceptions([finding], [{ ...exception, value: 'other.width' }]).length);
  assert.ok(validateExceptions([finding], [{ ...exception, reason: '' }]).length);
  assert.ok(validateExceptions([finding], [exception, exception]).length);
});
test("a part's rules use only that part's tokens", () => {
  const owners = { count: ['.count'] };
  assert.equal(
    auditCSS('.count{border-radius:var(--kb-count-radius)}', {
      '--kb-count-radius': { kind: 'length', value: '10px', role: 'Count radius' },
    }).length,
    0,
  );
  assert.equal(auditTokenOwnership('.count{border-radius:var(--kb-count-radius)}', owners).length, 0);
  assert.equal(auditTokenOwnership('.count{border-radius:var(--kb-radius-10)}', owners)[0].token, '--kb-radius-10');
  assert.equal(auditTokenOwnership('.dock{border-radius:var(--kb-radius-10)}', owners).length, 0);
});
const reachable = {
  count: {
    selectors: ['.count', '.nub-line'],
    closed: true,
    radius: { kind: 'length', value: '10px', role: 'Count badge — corner radius' },
    stroke: { kind: 'length', value: '1.5px', role: 'Count badge — leader stroke' },
  },
  legend: { selectors: ['.legend'], bottom: { kind: 'length', value: '84px', role: 'Legend — floor clearance' } },
  scene: { selectors: ['.world'], margin: { kind: 'length', value: '24px', role: 'Scene — margin around the map' } },
};
const drawn = (css) =>
  Object.fromEntries(
    [...selectorsByToken(css, ['--kb-count-radius', '--kb-count-stroke', '--kb-legend-bottom'])].map(([n, s]) => [n, [...s]]),
  );
test("a part's token is not reachable from another part, so a part can be read on its own", () => {
  const own =
    '.count{border-radius:var(--kb-count-radius)}.nub-line{stroke-width:var(--kb-count-stroke)}.legend{bottom:var(--kb-legend-bottom)}';
  assert.deepEqual(auditPartReach(reachable, drawn(own)), []);
  assert.deepEqual(auditPartReach(reachable, drawn('.count-inset{border-radius:var(--kb-count-radius)}')), []);
  const foreign = auditPartReach(reachable, drawn(own + '.legend{border-radius:var(--kb-count-radius)}'));
  assert.equal(foreign.length, 1);
  assert.match(foreign[0], /--kb-count-radius/);
  assert.match(foreign[0], /\.legend/);
  assert.match(foreign[0], /parts\.count/);
  assert.equal(reachable.legend.closed, undefined);
  const open = auditPartReach(reachable, drawn(own + '.count{bottom:var(--kb-legend-bottom)}'));
  assert.equal(open.length, 1);
  assert.match(open[0], /--kb-legend-bottom/);
  assert.match(open[0], /\.count/);
  assert.match(open[0], /parts\.legend/);
  assert.deepEqual(auditTokenOwnership('.legend{border-radius:var(--kb-radius-10)}', closedSelectors({ parts: reachable })), []);
  const silent = auditPartReach({ ...reachable, heading: { 'zoom-growth': reachable.scene.margin } }, drawn(own));
  assert.equal(silent.length, 1);
  assert.match(silent[0], /parts\.heading/);
  assert.match(silent[0], /declares no selectors/);
});
const roled = {
  '--kb-legend-bottom': { kind: 'length', value: '84px', role: 'Legend — height above the viewport floor that clears the dock' },
  '--kb-minimap-bottom': { kind: 'length', value: '85px', role: 'Minimap — height above the viewport floor that clears the dock' },
};
test('a role names a purpose in this codebase, so no two tokens may claim the same one', () => {
  assert.equal(auditRoles(roled).length, 0);
  const twinned = { ...roled, '--kb-minimap-bottom': { ...roled['--kb-minimap-bottom'], role: roled['--kb-legend-bottom'].role } };
  assert.ok(auditRoles(twinned).length);
});
test('a role that only names a group, a prototype selector or a missing inventory is refused', () => {
  for (const role of [
    'Spacing scale',
    'Corner radius scale',
    'Legacy layout size scale; primary controls and overlays use semantic roles',
    'Existing 12px type scale step; role assignments are listed in the consumer inventory',
    '#kb-board .b-radar — box-shadow; preserved baseline role',
  ])
    assert.ok(auditRoles({ '--kb-x': { kind: 'length', value: '8px', role } }).length, role);
});
const roleOwned = {
  count: { selectors: ['.count', '.nub-line'] },
  connection: { selectors: ['.wire', '.arrowhead'] },
  plot: { selectors: ['.plot'] },
  scrim: { selectors: ['.scrim'] },
  overview: { selectors: ['.overview'] },
  legend: { selectors: ['.legend'] },
};
const roleReached = (role, selectors, token = '--kb-x') =>
  auditRoleReach(roleOwned, { [token]: { kind: 'length', value: '1.5px', role } }, { [token]: selectors });
test("a role naming one part is that part's own, so another part may not reach it", () => {
  assert.deepEqual(roleReached('Count connector stroke', ['.nub-line']), []);
  const borrowed = roleReached('Count connector stroke', ['.plot rect[data-camera]'], '--kb-connection-stroke-nub');
  assert.equal(borrowed.length, 1);
  assert.match(borrowed[0], /--kb-connection-stroke-nub/);
  assert.match(borrowed[0], /\.plot rect\[data-camera\]/);
  assert.match(borrowed[0], /parts\.count/);
  assert.match(borrowed[0], /Count connector stroke/);
  assert.equal(roleReached('Idle connection opacity', ['.plot rect[data-camera]']).length, 1);
  assert.deepEqual(roleReached('Rolled-up connection paint', ['.wire', '.legend span::before']), []);
  assert.deepEqual(roleReached('Corner shared by the legend, the plot and the scrim', ['.plot']), []);
  assert.deepEqual(roleReached('Opacity of a dimmed count', ['.plot']), []);
  assert.deepEqual(roleReached('Universe overview backdrop', ['.scrim'], '--kb-layer-scrim'), []);
  assert.deepEqual(roleReached('Hairline the board draws everywhere', ['.plot', '.legend']), []);
});
