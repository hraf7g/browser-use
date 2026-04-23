import { rm } from 'node:fs/promises';
import { resolve } from 'node:path';

const targets = ['.next/cache', '.next/dev', '.next/trace'];

for (const target of targets) {
  const path = resolve(process.cwd(), target);
  await rm(path, { recursive: true, force: true });
}

console.log('Cleared stale Next dev cache.');
