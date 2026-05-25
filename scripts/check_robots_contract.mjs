#!/usr/bin/env node
// Build-time guard for robots.txt rules that must stay aligned with indexation
// policy. Crawlable noindex pages must not be robots-blocked, otherwise Google
// cannot see the noindex directive and Search Console reports blocked URLs.

import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(fileURLToPath(import.meta.url), '..', '..');
const ROBOTS = join(ROOT, 'public/robots.txt');

const REQUIRED_LINES = [
  'User-agent: *',
  'Allow: /',
  'Sitemap: https://www.creditdoc.co/sitemap-index.xml',
];

const FORBIDDEN_LINES = [
  'Disallow: /search/',
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
  const forbidden = FORBIDDEN_LINES.filter((line) => lines.has(line));
  if (missing.length || forbidden.length) {
    console.error('');
    console.error('robots.txt contract FAILED:');
    for (const line of missing) {
      console.error(`  - missing required line: ${line}`);
    }
    for (const line of forbidden) {
      console.error(`  - forbidden line present: ${line}`);
    }
    console.error('');
    console.error('Keep /search/ crawlable so Google can see its page-level noindex directive.');
    process.exit(1);
  }

  console.log(`[robots-contract] OK — robots.txt allows crawlable noindex handling.`);
}

main();
