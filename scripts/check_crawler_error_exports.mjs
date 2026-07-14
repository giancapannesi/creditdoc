#!/usr/bin/env node
// Guard for crawler-export regressions.
// Every URL in the current GSC/SE/Bing error CSV exports must either have a
// built static HTML target or an explicit redirect in public/_redirects.

import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(fileURLToPath(import.meta.url), '..', '..');
const DIST = join(ROOT, 'dist');
const REDIRECTS = join(ROOT, 'public', '_redirects');

const EXPORTS = [
  join(ROOT, 'SEO', 'Table 404 Missing Pages.csv'),
  join(ROOT, 'SEO', 'Table - Duplicates.csv'),
];

function parseCsv(text) {
  const rows = [];
  let row = [];
  let value = '';
  let quoted = false;

  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    const next = text[i + 1];

    if (quoted) {
      if (ch === '"' && next === '"') {
        value += '"';
        i += 1;
      } else if (ch === '"') {
        quoted = false;
      } else {
        value += ch;
      }
      continue;
    }

    if (ch === '"') {
      quoted = true;
    } else if (ch === ',') {
      row.push(value);
      value = '';
    } else if (ch === '\n') {
      row.push(value);
      rows.push(row);
      row = [];
      value = '';
    } else if (ch !== '\r') {
      value += ch;
    }
  }

  if (value || row.length) {
    row.push(value);
    rows.push(row);
  }

  return rows;
}

function normalizePath(pathname) {
  let decoded = pathname;
  try {
    decoded = decodeURI(pathname);
  } catch {
    decoded = pathname;
  }
  decoded = decoded.replace(/\/+$/, '') || '/';
  return decoded === '/' ? '/' : `${decoded}/`;
}

function encodedPath(pathname) {
  return encodeURI(normalizePath(pathname)).replace(/\/+$/, '/');
}

function staticHtmlExists(pathname) {
  const normalized = normalizePath(pathname);
  const rel = normalized === '/' ? 'index.html' : join(normalized.replace(/^\/|\/$/g, ''), 'index.html');
  return existsSync(join(DIST, rel));
}

function loadRedirects() {
  const sources = new Set();
  const rules = [];
  if (!existsSync(REDIRECTS)) return { sources, rules };

  for (const rawLine of readFileSync(REDIRECTS, 'utf8').split(/\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith('#')) continue;
    const parts = line.split(/\s+/);
    if (parts.length < 3 || !/^30[1278]$/.test(parts[2])) continue;

    const source = parts[0];
    const target = parts[1];
    sources.add(normalizePath(source));
    sources.add(encodedPath(source));
    rules.push({ source, target });
  }
  return { sources, rules };
}

function loadSitemapUrls() {
  const urls = new Set();
  if (!existsSync(DIST)) return urls;

  for (const file of readdirSync(DIST).filter((name) => /^sitemap.*\.xml$/.test(name))) {
    const xml = readFileSync(join(DIST, file), 'utf8');
    for (const match of xml.matchAll(/<loc>([^<]+)<\/loc>/g)) {
      try {
        const url = new URL(match[1]);
        if (url.hostname !== 'www.creditdoc.co') continue;
        urls.add(normalizePath(url.pathname));
      } catch {
        // The schema/sitemap contract owns invalid sitemap URL formatting.
      }
    }
  }
  return urls;
}

const redirects = loadRedirects();
const sitemapUrls = loadSitemapUrls();
const failures = [];
const sitemapLeaks = new Set();
const badRedirectTargets = [];
let checked = 0;
let staticCount = 0;
let redirectCount = 0;

for (const exportPath of EXPORTS) {
  if (!existsSync(exportPath)) continue;
  const rows = parseCsv(readFileSync(exportPath, 'utf8').replace(/^\uFEFF/, ''));
  const header = rows.shift() ?? [];
  const urlIndex = header.findIndex((h) => h.trim().toLowerCase() === 'url');
  if (urlIndex === -1) {
    failures.push(`${exportPath}: missing URL column`);
    continue;
  }

  for (const row of rows) {
    const rawUrl = row[urlIndex]?.trim();
    if (!rawUrl) continue;
    let pathname;
    try {
      pathname = new URL(rawUrl).pathname;
    } catch {
      failures.push(`${exportPath}: invalid URL ${rawUrl}`);
      continue;
    }

    checked += 1;
    const normalized = normalizePath(pathname);
    const encoded = encodedPath(pathname);
    if (sitemapUrls.has(normalized)) sitemapLeaks.add(normalized);

    if (staticHtmlExists(normalized)) {
      staticCount += 1;
      continue;
    }
    if (redirects.sources.has(normalized) || redirects.sources.has(encoded)) {
      redirectCount += 1;
      continue;
    }
    failures.push(`${rawUrl} -> no static file or explicit redirect`);
  }
}

for (const rule of redirects.rules) {
  if (/^https?:\/\//i.test(rule.target)) continue;
  if (!rule.target.startsWith('/')) continue;
  if (staticHtmlExists(rule.target)) continue;
  badRedirectTargets.push(`${rule.source} -> ${rule.target} target has no static HTML`);
}

if (failures.length || sitemapLeaks.size || badRedirectTargets.length) {
  console.error('');
  console.error(`[crawler-error-exports] FAILED — unresolved=${failures.length}, sitemap_leaks=${sitemapLeaks.size}, bad_redirect_targets=${badRedirectTargets.length}`);
  for (const failure of failures.slice(0, 80)) {
    console.error(`  - ${failure}`);
  }
  if (failures.length > 80) console.error(`  ... ${failures.length - 80} more`);
  for (const leak of [...sitemapLeaks].slice(0, 80)) {
    console.error(`  - sitemap still includes exported crawler URL ${leak}`);
  }
  if (sitemapLeaks.size > 80) console.error(`  ... ${sitemapLeaks.size - 80} more sitemap leak(s)`);
  for (const target of badRedirectTargets.slice(0, 80)) {
    console.error(`  - ${target}`);
  }
  if (badRedirectTargets.length > 80) console.error(`  ... ${badRedirectTargets.length - 80} more bad redirect target(s)`);
  process.exit(1);
}

console.log(`[crawler-error-exports] OK — ${checked} exported URL row(s): ${staticCount} static, ${redirectCount} redirected, sitemap leaks=0, bad redirect targets=0.`);
