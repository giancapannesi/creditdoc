#!/usr/bin/env node
// Post-build guard for high-value sitemap invariants that have regressed before.
// Keep this narrow: it checks generated XML, not source assumptions.

import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(fileURLToPath(import.meta.url), '..', '..');
const DIST = join(ROOT, 'dist');

const REQUIRED_URLS = [
  'https://www.creditdoc.co/state/utah/',
  'https://www.creditdoc.co/state/utah/lending-laws/',
  'https://www.creditdoc.co/financial-wellness/personal-loan-application-checklist/',
  'https://www.creditdoc.co/financial-wellness/personal-loan-interest-how-calculated/',
];

const FORBIDDEN_URLS = [
  'https://www.creditdoc.co/search/',
  'https://www.creditdoc.co/compare/kikoff-vs-a-better-way-auto-brokerage/',
];

function sitemapUrls() {
  if (!existsSync(DIST)) {
    throw new Error('dist/ does not exist. Run this after astro build.');
  }

  const files = readdirSync(DIST).filter((name) => /^sitemap.*\.xml$/.test(name));
  const urls = new Set();

  for (const name of files) {
    const xml = readFileSync(join(DIST, name), 'utf8');
    for (const match of xml.matchAll(/<loc>([^<]+)<\/loc>/g)) {
      urls.add(match[1]);
    }
  }

  return urls;
}

function main() {
  const urls = sitemapUrls();
  const missing = REQUIRED_URLS.filter((url) => !urls.has(url));
  const forbiddenPresent = FORBIDDEN_URLS.filter((url) => urls.has(url));

  if (missing.length || forbiddenPresent.length) {
    console.error('');
    console.error('Critical sitemap URL guard FAILED:');
    for (const url of missing) {
      console.error(`  - missing required URL: ${url}`);
    }
    for (const url of forbiddenPresent) {
      console.error(`  - forbidden URL present: ${url}`);
    }
    console.error('');
    console.error('Fix: update sitemap customPages/filter logic and rebuild.');
    process.exit(1);
  }

  console.log(`[sitemap-critical] OK — ${REQUIRED_URLS.length} required URL(s) present and ${FORBIDDEN_URLS.length} forbidden URL(s) absent.`);
}

main();
