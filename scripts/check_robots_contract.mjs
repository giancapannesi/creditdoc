#!/usr/bin/env node
// Build-time guard for robots.txt rules that are intentional protections.
// This prevents accidental removal of internal route blocks during SEO fixes.

import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(fileURLToPath(import.meta.url), '..', '..');
const ROBOTS = join(ROOT, 'public/robots.txt');

const REQUIRED_LINES = [
  'User-agent: *',
  'Allow: /',
  'Disallow: /search/',
  'Sitemap: https://www.creditdoc.co/sitemap-index.xml',
];

function main() {
  const src = readFileSync(ROBOTS, 'utf8');
  const lines = new Set(
    src
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean)
  );

  const missing = REQUIRED_LINES.filter((line) => !lines.has(line));
  if (missing.length) {
    console.error('');
    console.error('robots.txt contract FAILED:');
    for (const line of missing) {
      console.error(`  - missing required line: ${line}`);
    }
    console.error('');
    console.error('Do not remove protected robots rules without founder approval.');
    process.exit(1);
  }

  console.log(`[robots-contract] OK — protected robots rules present.`);
}

main();
