#!/usr/bin/env node
// Post-build guard: RSS/feed endpoints are crawl and distribution surfaces.
// If these disappear, the build should fail before production does.

import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(fileURLToPath(import.meta.url), '..', '..');
const DIST = join(ROOT, 'dist');
const FEED_FILES = ['rss.xml', 'feed.xml'];
const MIN_ITEMS = 10;

function fail(message) {
  console.error(`Feed contract FAILED: ${message}`);
  process.exit(1);
}

function itemCount(xml) {
  return [...xml.matchAll(/<item\b/g)].length;
}

function main() {
  if (!existsSync(DIST)) {
    fail('dist/ does not exist. Run this after astro build.');
  }

  for (const name of FEED_FILES) {
    const path = join(DIST, name);
    if (!existsSync(path)) {
      fail(`missing dist/${name}`);
    }

    const xml = readFileSync(path, 'utf8');
    if (!/<rss\b[^>]*version="2\.0"/.test(xml)) {
      fail(`dist/${name} is not RSS 2.0`);
    }
    if (!xml.includes('<channel>') || !xml.includes('<title>CreditDoc Blog</title>')) {
      fail(`dist/${name} has the wrong channel metadata`);
    }
    if (!xml.includes('<link>https://www.creditdoc.co/blog/</link>')) {
      fail(`dist/${name} is missing the CreditDoc blog channel link`);
    }
    const count = itemCount(xml);
    if (count < MIN_ITEMS) {
      fail(`dist/${name} has only ${count} item(s), expected at least ${MIN_ITEMS}`);
    }
  }

  const index = readFileSync(join(DIST, 'index.html'), 'utf8');
  if (!/<link\b[^>]+rel="alternate"[^>]+type="application\/rss\+xml"[^>]+href="https:\/\/www\.creditdoc\.co\/rss\.xml"/.test(index)) {
    fail('homepage is missing RSS autodiscovery link');
  }

  console.log(`[feed-contract] OK — ${FEED_FILES.length} feed endpoint(s), RSS autodiscovery, and item counts verified.`);
}

main();
