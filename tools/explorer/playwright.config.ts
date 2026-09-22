import { defineConfig, devices } from '@playwright/test';
import { tmpdir } from 'node:os';
import { resolve } from 'node:path';
import { laneNamed, laneOptions } from './lanes';

export default defineConfig({
  tsconfig: resolve(import.meta.dirname, '../../explorer/tsconfig.test.json'),
  testDir: resolve(import.meta.dirname, '../../explorer/test/browser'),
  testMatch: '*.spec.ts',
  outputDir: resolve(tmpdir(), 'knowledge-bus-explorer-results'),
  ...laneOptions(laneNamed(process.env.KB_EXPLORER_LANE)),
  reporter: 'list',
  use: { locale: 'en-US', timezoneId: 'UTC', trace: 'retain-on-failure' },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'], browserName: 'chromium' } }],
});
