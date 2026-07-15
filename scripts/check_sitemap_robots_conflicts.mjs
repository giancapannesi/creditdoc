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
const FORBIDDEN_SUBMISSION_URLS = [
  'https://www.creditdoc.co/sitemap.xml',
];
const SUBMISSION_SURFACES = [
  'tools/creditdoc_sitemap_resubmit.py',
  'scripts/submit-indexnow.sh',
];

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

function robotsSitemaps() {
  const src = readFileSync(ROBOTS, 'utf8');
  const urls = [];
  for (const rawLine of src.split('\n')) {
    const line = rawLine.replace(/#.*/, '').trim();
    const match = line.match(/^sitemap:\s*(\S+)/i);
    if (match) urls.push(match[1]);
  }
  return urls;
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
  const staleSubmissions = [];
  for (const relativePath of SUBMISSION_SURFACES) {
    const file = join(ROOT, relativePath);
    if (!existsSync(file)) continue;
    const src = readFileSync(file, 'utf8');
    for (const forbiddenUrl of FORBIDDEN_SUBMISSION_URLS) {
      if (src.includes(forbiddenUrl)) {
        staleSubmissions.push({ relativePath, forbiddenUrl });
      }
    }
  }

  if (staleSubmissions.length) {
    console.error('');
    console.error('Sitemap submission contract FAILED:');
    for (const { relativePath, forbiddenUrl } of staleSubmissions) {
      console.error(`  - ${relativePath} submits stale sitemap URL: ${forbiddenUrl}`);
    }
    console.error('');
    console.error('Fix: submit only https://www.creditdoc.co/sitemap-index.xml to search engines.');
    process.exit(1);
  }

  const missingSitemaps = [];
  for (const sitemapUrl of robotsSitemaps()) {
    const pathname = pathnameFor(sitemapUrl);
    if (!pathname) continue;
    const localFile = join(DIST, pathname.replace(/^\/+/, ''));
    if (!existsSync(localFile)) missingSitemaps.push(sitemapUrl);
  }

  if (missingSitemaps.length) {
    console.error('');
    console.error('Robots sitemap advertisement FAILED:');
    for (const sitemapUrl of missingSitemaps) console.error(`  - ${sitemapUrl} is advertised in robots.txt but missing from dist/`);
    console.error('');
    console.error('Fix: advertise only generated sitemap files in public/robots.txt.');
    process.exit(1);
  }

  const rules = robotsDisallows();
  if (!rules.length) {
    console.log('[sitemap-robots] OK — advertised sitemap files exist; no User-agent:* Disallow rules to compare.');
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
