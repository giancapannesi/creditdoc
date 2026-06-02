#!/usr/bin/env node
// Build-time guard for robots.txt rules that must stay aligned with indexation
// policy. Crawlable noindex pages must not be robots-blocked, otherwise Google
// cannot see the noindex directive and Search Console reports blocked URLs.

import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(fileURLToPath(import.meta.url), '..', '..');
const ROBOTS = join(ROOT, 'public/robots.txt');
const SEARCH_PAGE = join(ROOT, 'src/pages/search.astro');

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

  const searchPage = readFileSync(SEARCH_PAGE, 'utf8');
  const searchGuards = [
    {
      ok: searchPage.includes("Astro.url.searchParams.get('state')"),
      message: 'src/pages/search.astro must detect state query filters.',
    },
    {
      ok: searchPage.includes('Astro.redirect(`/state/${matchedState.toLowerCase().replace(/\\s+/g, \'-\')}/`, 301)'),
      message: 'src/pages/search.astro must 301 state-only filters to /state/<state>/ pages.',
    },
    {
      ok: searchPage.includes('const hasSearchFilters = Astro.url.searchParams.toString().length > 0;') &&
        searchPage.includes('noindex={hasSearchFilters}'),
      message: 'src/pages/search.astro must keep clean /search/ indexable while noindexing remaining filtered search pages.',
    },
  ];
  const searchFailures = searchGuards.filter((guard) => !guard.ok);
  if (searchFailures.length) {
    console.error('');
    console.error('search route indexation contract FAILED:');
    for (const failure of searchFailures) {
      console.error(`  - ${failure.message}`);
    }
    console.error('');
    console.error('State search URLs must not reappear in GSC as blocked /search/?state=... pages.');
    process.exit(1);
  }

  console.log(`[robots-contract] OK — robots.txt allows crawlable noindex handling.`);
}

main();
