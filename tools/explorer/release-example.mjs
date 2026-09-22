import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, renameSync, rmSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { parseArgs } from 'node:util';
import { renderSvg } from './render.mjs';
import { root } from './generate-tokens.mjs';

const identity = (data, mimeType) => ({
  mimeType,
  bytes: data.length,
  digest: `sha256:${createHash('sha256').update(data).digest('hex')}`,
});

export function addSvgToReceipt(directory, svg) {
  const receiptPath = path.join(directory, 'receipt.json');
  const receipt = JSON.parse(readFileSync(receiptPath, 'utf8'));
  const data = Buffer.from(svg.endsWith('\n') ? svg : svg + '\n');
  writeFileSync(path.join(directory, 'map.svg'), data);
  receipt.outputs['map.svg'] = identity(data, 'image/svg+xml');
  writeFileSync(receiptPath, JSON.stringify(receipt, null, 2) + '\n');
  return receipt;
}

export async function buildReleaseExample({ input, output, universe, theme = 'auto' }) {
  const destination = path.resolve(output);
  if (existsSync(destination)) throw new Error(`Refusing to overwrite ${destination}`);
  mkdirSync(path.dirname(destination), { recursive: true });
  const stageRoot = mkdtempSync(path.join(path.dirname(destination), `.${path.basename(destination)}.stage-`));
  const stage = path.join(stageRoot, 'artifact');
  try {
    const result = spawnSync(
      'uv',
      ['run', '--locked', 'kbp', '--explore', '--output', stage, ...(universe ? ['--universe', universe] : []), path.resolve(input)],
      { cwd: root, encoding: 'utf8' },
    );
    if (result.status !== 0) throw new Error((result.stderr || result.stdout).trim() || 'Static generation failed.');
    const svg = await renderSvg(path.join(stage, 'index.html'), theme);
    addSvgToReceipt(stage, svg);
    const files = new Set(['index.html', 'model.json', 'map.svg', 'receipt.json']);
    const actual = new Set(readdirSync(stage));
    if (actual.size !== files.size || [...files].some((file) => !actual.has(file)))
      throw new Error('Release example inventory is incomplete.');
    renameSync(stage, destination);
    return destination;
  } finally {
    rmSync(stageRoot, { recursive: true, force: true });
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const { values } = parseArgs({
    options: {
      input: { type: 'string' },
      output: { type: 'string' },
      universe: { type: 'string' },
      theme: { type: 'string', default: 'auto' },
    },
  });
  if (!values.input || !values.output) {
    console.error('Usage: node tools/explorer/release-example.mjs --input <universe.yaml> --output <fresh-directory> [--universe <id>]');
    process.exitCode = 2;
  } else {
    buildReleaseExample(values).then(
      (output) => console.log(`explorer release example: wrote ${output}`),
      (error) => {
        console.error(error.message);
        process.exitCode = 1;
      },
    );
  }
}
