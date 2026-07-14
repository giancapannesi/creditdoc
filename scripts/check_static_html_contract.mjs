#!/usr/bin/env node
// Post-build guard: high-value SEO routes must exist as static HTML files.
// This catches Astro/adapter regressions where routes silently fall back to
// Worker runtime and crawlers see intermittent 404/5xx/slow responses.

import { existsSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(fileURLToPath(import.meta.url), '..', '..');
const DIST = join(ROOT, 'dist');

const REQUIRED_HTML = [
  ['state index', 'state/index.html'],
  ['Texas state page', 'state/texas/index.html'],
  ['Utah state page', 'state/utah/index.html'],
  ['Texas lending laws', 'state/texas/lending-laws/index.html'],
  ['Utah lending laws', 'state/utah/lending-laws/index.html'],
  ['city index', 'city/index.html'],
  ['tools index', 'tools/index.html'],
  ['MCA repayment calculator', 'tools/mca-repayment-calculator/index.html'],
  ['answers index', 'answers/index.html'],
  ['wellness index', 'financial-wellness/index.html'],
  ['course index', 'courses/index.html'],
];

const missing = REQUIRED_HTML.filter(([, rel]) => !existsSync(join(DIST, rel)));

if (missing.length) {
  console.error('');
  console.error('[static-html-contract] FAILED — required static HTML files are missing:');
  for (const [label, rel] of missing) {
    console.error(`  - ${label}: dist/${rel}`);
  }
  console.error('');
  console.error('Fix: add explicit `export const prerender = true` or repair getStaticPaths/output config.');
  process.exit(1);
}

console.log(`[static-html-contract] OK — ${REQUIRED_HTML.length} required static HTML file(s) exist.`);
