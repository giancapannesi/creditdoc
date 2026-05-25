#!/usr/bin/env node
// Post-build guard: URLs protected by public/robots.txt must not be submitted
// in generated XML sitemaps. Otherwise Search Console reports
// "Blocked by robots.txt" for pages we handed to Google ourselves.

import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(fileURLToPath(import.meta.url), '..', '..');
const ROBOTS = join(ROOT, 'public/robots.txt');
const DIST = join(ROOT, 'dist');

function robotsDisallows() {
  const src = readFileSync(ROBOTS, 'utf8');
  const rules = [];
  let appliesToAll = false;

  for (const rawLine of src.split('\n')) {
    const line = rawLine.replace(/#.*/, '').trim();
    if (!line) continue;

    const match = line.match(/^([^:]+):\s*(.*)$/);
    if (!match) continue;

    const key = match[1].toLowerCase();
    const value = match[2].trim();

    if (key === 'user-agent') {
      appliesToAll = value === '*';
      continue;
    }

    if (appliesToAll && key === 'disallow' && value && value !== '/') {
      rules.push(value.endsWith('*') ? value.slice(0, -1) : value);
    }
  }

  return rules;
}

function sitemapUrls() {
  if (!existsSync(DIST)) {
    throw new Error('dist/ does not exist. Run this after astro build.');
  }

  const files = readdirSync(DIST).filter((name) => /^sitemap.*\.xml$/.test(name));
  const urls = [];

  for (const name of files) {
    const xml = readFileSync(join(DIST, name), 'utf8');
    for (const match of xml.matchAll(/<loc>([^<]+)<\/loc>/g)) {
      urls.push(match[1]);
    }
  }

  return urls;
}

function pathnameFor(url) {
  try {
    return new URL(url).pathname;
  } catch {
    return null;
  }
}

function main() {
  const rules = robotsDisallows();
  if (!rules.length) {
    console.log('[sitemap-robots] OK — no User-agent:* Disallow rules to compare.');
    return;
  }

  const conflicts = [];
  for (const url of sitemapUrls()) {
    const pathname = pathnameFor(url);
    if (!pathname) continue;
    const rule = rules.find((disallow) => pathname === disallow || pathname.startsWith(disallow));
    if (rule) conflicts.push({ url, rule });
  }

  if (conflicts.length) {
    console.error('');
    console.error('Sitemap/robots conflict FAILED:');
    for (const { url, rule } of conflicts.slice(0, 25)) {
      console.error(`  - ${url} matches robots Disallow: ${rule}`);
    }
    if (conflicts.length > 25) {
      console.error(`  ... and ${conflicts.length - 25} more`);
    }
    console.error('');
    console.error('Fix: keep the robots protection, and exclude protected URLs from the sitemap generator.');
    process.exit(1);
  }

  console.log(`[sitemap-robots] OK — checked generated sitemaps against ${rules.length} robots disallow rule(s).`);
}

main();
