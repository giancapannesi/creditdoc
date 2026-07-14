#!/usr/bin/env node

import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { dirname, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const DIST = join(ROOT, 'dist');
const REDIRECTS_FILE = join(ROOT, 'public', '_redirects');
const REPORT_DIR = join(ROOT, 'reports', 'seo-debug');
const TODAY = new Date().toISOString().slice(0, 10);
const REPORT_PATH = join(REPORT_DIR, `internal_static_links_${TODAY}.json`);

const STATIC_PREFIXES = [
  '/answers/',
  '/best/',
  '/blog/',
  '/browse/',
  '/city/',
  '/courses/',
  '/financial-wellness/',
  '/research/',
  '/resources/',
  '/state/',
  '/tools/',
];

const ALLOWED_DYNAMIC_PREFIXES = [
  '/api/',
  '/go/',
  '/r/',
  '/search/',
  '/linkedin-oauth-callback/',
];

function readText(path) {
  return readFileSync(path, 'utf8');
}

function walkHtml(dir, files = []) {
  if (!existsSync(dir)) return files;
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) walkHtml(full, files);
    else if (entry.isFile() && entry.name.endsWith('.html')) files.push(full);
  }
  return files;
}

function routeToDistFile(pathname) {
  const clean = normalizePathname(pathname);
  if (clean === '/') return join(DIST, 'index.html');
  return join(DIST, clean.replace(/^\/+/, ''), 'index.html');
}

function normalizePathname(pathname) {
  if (!pathname || pathname === '/') return '/';
  const clean = pathname.split('#')[0].split('?')[0].replace(/\/+$/, '');
  return clean ? `${clean}/` : '/';
}

function routeFromDistFile(file) {
  let rel = `/${relative(DIST, file).replaceAll('\\', '/')}`;
  if (rel === '/index.html') return '/';
  return rel.replace(/\/index\.html$/, '/');
}

function loadRedirectSources() {
  const sources = new Set();
  if (!existsSync(REDIRECTS_FILE)) return sources;
  for (const rawLine of readText(REDIRECTS_FILE).split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith('#')) continue;
    const [from, to, status] = line.split(/\s+/);
    if (!from || !to) continue;
    if (status && !/^30[1278]$/.test(status)) continue;
    sources.add(normalizePathname(from));
  }
  return sources;
}

function extractInternalLinks(html) {
  const links = [];
  const attrPattern = /\b(?:href|src)=["']([^"']+)["']/gi;
  for (const match of html.matchAll(attrPattern)) {
    const raw = match[1].trim();
    if (!raw || raw.startsWith('#')) continue;
    if (/^(mailto:|tel:|javascript:|data:|blob:)/i.test(raw)) continue;
    if (/^https?:\/\//i.test(raw) && !/^https:\/\/www\.creditdoc\.co\//i.test(raw)) continue;
    const local = raw.replace(/^https:\/\/www\.creditdoc\.co/i, '');
    if (!local.startsWith('/')) continue;
    links.push(local);
  }
  return links;
}

function shouldCheck(pathname) {
  if (ALLOWED_DYNAMIC_PREFIXES.some((prefix) => pathname.startsWith(prefix))) return false;
  return pathname === '/' || STATIC_PREFIXES.some((prefix) => pathname.startsWith(prefix));
}

const redirectSources = loadRedirectSources();
const issues = [];
const issueTargets = new Map();
const checkedLinks = new Set();
const files = walkHtml(DIST);

for (const file of files) {
  const sourceRoute = routeFromDistFile(file);
  const html = readText(file);
  for (const rawLink of extractInternalLinks(html)) {
    const pathname = normalizePathname(rawLink);
    if (!shouldCheck(pathname)) continue;
    const key = `${sourceRoute} -> ${pathname}`;
    if (checkedLinks.has(key)) continue;
    checkedLinks.add(key);
    if (existsSync(routeToDistFile(pathname)) || redirectSources.has(pathname)) continue;
    const issue = {
      source_route: sourceRoute,
      target: pathname,
      source_file: relative(ROOT, file),
      expected_static_file: relative(ROOT, routeToDistFile(pathname)),
    };
    issues.push(issue);

    const grouped = issueTargets.get(pathname) || {
      target: pathname,
      count: 0,
      sample_source_routes: [],
      expected_static_file: issue.expected_static_file,
    };
    grouped.count += 1;
    if (grouped.sample_source_routes.length < 10) grouped.sample_source_routes.push(sourceRoute);
    issueTargets.set(pathname, grouped);
  }
}

const missingTargets = [...issueTargets.values()].sort((a, b) => b.count - a.count || a.target.localeCompare(b.target));

const result = {
  generated_at: new Date().toISOString(),
  status: issues.length ? 'FAIL' : 'PASS',
  checked_html_files: files.length,
  checked_internal_links: checkedLinks.size,
  issue_count: issues.length,
  unique_missing_target_count: missingTargets.length,
  missing_targets: missingTargets,
  issues: issues.slice(0, 500),
};

mkdirSync(REPORT_DIR, { recursive: true });
writeFileSync(REPORT_PATH, `${JSON.stringify(result, null, 2)}\n`);

if (missingTargets.length) {
  console.error(`[internal-static-links] FAILED — ${missingTargets.length} unique missing static target(s), ${issues.length} source link(s); report: ${relative(ROOT, REPORT_PATH)}`);
  for (const issue of missingTargets.slice(0, 40)) {
    console.error(`[internal-static-links] ${issue.target} (${issue.count} source link(s)); examples: ${issue.sample_source_routes.join(', ')}`);
  }
  if (missingTargets.length > 40) console.error(`[internal-static-links] ...and ${missingTargets.length - 40} more target(s).`);
  process.exit(1);
}

console.log(`[internal-static-links] OK — ${checkedLinks.size} internal static links checked; report: ${relative(ROOT, REPORT_PATH)}`);
