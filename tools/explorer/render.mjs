import { spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { parseArgs } from 'node:util';
import { buildExplorer, standaloneBundle } from './build.mjs';
import { root } from './generate-tokens.mjs';

const INERT = { '<': '\\u003c', '>': '\\u003e', '&': '\\u0026', '\u2028': '\\u2028', '\u2029': '\\u2029' };

export function embedJson(value) {
  return JSON.stringify(value).replace(/[<>&\u2028\u2029]/g, (c) => INERT[c]);
}

const escapeHtml = (value) => String(value).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);

const FALLBACK_STYLE =
  'html,body{margin:0;height:100%;background:#171e22;color:#e5eceb;font:14px system-ui,sans-serif}' +
  '@media(prefers-color-scheme:light){html,body{background:#f5f5f1;color:#263638}}' +
  '#explorer{position:fixed;inset:0}noscript{display:block;padding:24px}';

export function composeHtml({ model, script }) {
  if (script.includes('</script')) throw new Error('Bundle contains a script terminator.');
  return [
    '<!doctype html>',
    '<html lang="en">',
    '<head>',
    '<meta charset="utf-8">',
    '<meta name="viewport" content="width=device-width, initial-scale=1">',
    `<title>${escapeHtml(model.universe.label)} \u00b7 Knowledge Bus Explorer</title>`,
    `<style>${FALLBACK_STYLE}</style>`,
    '</head>',
    '<body>',
    '<noscript>This universe map needs JavaScript to be interactive. The file is self-contained and works offline once scripts are allowed.</noscript>',
    '<div id="explorer"></div>',
    `<script type="application/json" id="explorer-model">${embedJson(model)}</script>`,
    `<script>${script}</script>`,
    '</body>',
    '</html>',
    '',
  ].join('\n');
}

export function prepareModel(input, output, guidance, marks) {
  mkdirSync(path.dirname(output), { recursive: true });
  const result = spawnSync(
    'uv',
    [
      'run',
      '--locked',
      'python',
      path.join(root, 'tools/explorer/prepare_model.py'),
      '--input',
      input,
      '--output',
      output,
      ...(guidance ? ['--guidance', guidance] : []),
      ...(marks ? ['--marks', marks] : []),
    ],
    { cwd: root, stdio: 'inherit' },
  );
  if (result.status !== 0) throw new Error('Model preparation failed; see diagnostics above.');
  return JSON.parse(readFileSync(output, 'utf8'));
}

export async function renderSvg(htmlPath, theme = 'auto') {
  const { chromium } = await import('@playwright/test');
  const browser = await chromium.launch();
  try {
    const page = await browser.newPage();
    await page.route(/^(?!file:)/, (route) => route.abort());
    const failures = [];
    page.on('pageerror', (error) => failures.push(error.message));
    await page.goto(pathToFileURL(htmlPath).href);
    await page.waitForFunction(() => !!document.getElementById('explorer')?.explorerViewer);
    await page.waitForFunction(() => document.fonts.status === 'loaded');
    const svg = await page.evaluate((chosen) => document.getElementById('explorer').explorerViewer.exportSvg({ theme: chosen }), theme);
    if (failures.length) throw new Error('Viewer errors while rendering: ' + failures.join('; '));
    return svg;
  } finally {
    await browser.close();
  }
}

export async function render({ input, guidance, marks, html, svg, model: modelPath, theme = 'auto' }) {
  const target = html ?? svg;
  const modelOutput = modelPath ?? path.join(path.dirname(target), path.basename(target).replace(/\.[^.]+$/, '') + '.model.json');
  const model = prepareModel(
    path.resolve(root, input),
    path.resolve(root, modelOutput),
    guidance ? path.resolve(root, guidance) : undefined,
    marks ? path.resolve(root, marks) : undefined,
  );
  if (!existsSync(standaloneBundle)) await buildExplorer();
  const script = readFileSync(standaloneBundle, 'utf8');
  const htmlPath = path.resolve(root, html ?? modelOutput.replace(/\.model\.json$/, '.html'));
  mkdirSync(path.dirname(htmlPath), { recursive: true });
  writeFileSync(htmlPath, composeHtml({ model, script }));
  const written = [modelOutput, path.relative(root, htmlPath)];
  if (svg) {
    const svgPath = path.resolve(root, svg);
    mkdirSync(path.dirname(svgPath), { recursive: true });
    writeFileSync(svgPath, (await renderSvg(htmlPath, theme)) + '\n');
    written.push(path.relative(root, svgPath));
  }
  return written;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const { values } = parseArgs({
    options: {
      input: { type: 'string' },
      guidance: { type: 'string' },
      marks: { type: 'string' },
      html: { type: 'string' },
      svg: { type: 'string' },
      model: { type: 'string' },
      theme: { type: 'string', default: 'auto' },
    },
  });
  if (!values.input || !(values.html || values.svg)) {
    console.error(
      'Usage: node tools/explorer/render.mjs --input <universe.yaml> [--guidance <guidance.yaml>] [--marks <marks.yaml>] [--html <out.html>] [--svg <out.svg>] [--model <out.json>] [--theme auto|light|dark]',
    );
    process.exitCode = 2;
  } else
    render(values).then(
      (written) => console.log('explorer: wrote ' + written.join(', ')),
      (error) => {
        console.error(error.message);
        process.exitCode = 1;
      },
    );
}
