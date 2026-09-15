import { spawnSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';

// Run every requested script, retaining any failure instead of stopping early.
export function runScripts(scripts, run = spawnSync) {
  if (!scripts.length) return 1;
  let failed = false;
  for (const script of scripts) {
    const result = run(process.env.npm_execpath, ['run', script], {
      stdio: 'inherit',
    });
    if (result.error) console.error(result.error.message);
    if (result.signal) return 1;
    if (result.error || result.status !== 0) failed = true;
  }
  return failed ? 1 : 0;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  if (!process.env.npm_execpath) {
    console.error('Run this helper through a package script (pnpm run).');
    process.exitCode = 1;
  } else {
    process.exitCode = runScripts(process.argv.slice(2));
  }
}
