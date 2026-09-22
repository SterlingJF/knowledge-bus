import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { addSvgToReceipt } from './release-example.mjs';

test('release example receipt records the exact contributor-only SVG output', () => {
  const directory = mkdtempSync(path.join(tmpdir(), 'knowledge-bus-example-'));
  try {
    writeFileSync(path.join(directory, 'receipt.json'), JSON.stringify({ schema: 'knowledge-bus/explorer-artifact/1', outputs: {} }));
    const receipt = addSvgToReceipt(directory, '<svg xmlns="http://www.w3.org/2000/svg"></svg>');
    const data = readFileSync(path.join(directory, 'map.svg'));
    assert.deepEqual(receipt.outputs['map.svg'], {
      mimeType: 'image/svg+xml',
      bytes: data.length,
      digest: `sha256:${createHash('sha256').update(data).digest('hex')}`,
    });
    assert.deepEqual(JSON.parse(readFileSync(path.join(directory, 'receipt.json'))), receipt);
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});
