import { spawnSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';
import { changedFiles, copyOnly } from './snapshot.mjs';

export function lane(root, base, head) {
  const usable = base && !/^0+$/.test(base) ? base : null;
  return copyOnly(changedFiles(root, usable, head) ?? []) ? 'copy' : 'code';
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const [base, head = 'HEAD'] = process.argv.slice(2);
  const top = spawnSync('git', ['rev-parse', '--show-toplevel'], { encoding: 'utf8' });
  if (top.status !== 0) {
    console.error('lane: run inside the repository.');
    process.exit(1);
  }
  console.log(`lane=${lane(top.stdout.trim(), base, head)}`);
}
