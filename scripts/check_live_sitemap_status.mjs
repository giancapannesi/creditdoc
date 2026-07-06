#!/usr/bin/env node
// Live sitemap validator for production crawl health.
//
// This intentionally runs outside postbuild because it depends on the live site.
// It fetches the live sitemap index, samples URLs by route family, and fails on
// crawler-visible problems: redirects, 4XX, 5XX, noindex, or timeouts.

import { mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const SITE_ORIGIN = 'https://www.creditdoc.co';
const DEFAULT_SITEMAP_INDEX = `${SITE_ORIGIN}/sitemap-index.xml`;
const DEFAULT_LIMIT_PER_FAMILY = 25;
const DEFAULT_CONCURRENCY = 8;
const DEFAULT_TIMEOUT_MS = 15000;
const REPORT_PATH = join(process.cwd(), 'reports', 'live-sitemap-status.json');
const USER_AGENT = 'CreditDoc-LiveSitemapValidator/1.0 (+https://www.creditdoc.co/)';

const PRIORITY_PATHS = [
  '/',
  '/best/best-sba-loans/',
  '/best/best-small-business-loans/',
  '/best/best-business-lines-of-credit/',
  '/tools/sba-loan-calculator/',
  '/tools/sba-guarantee-fee-calculator/',
  '/tools/business-line-of-credit-calculator/',
  '/tools/commercial-loan-calculator/',
  '/courses/credit-fundamentals/',
  '/answers/',
  '/financial-wellness/',
  '/resources/',
  '/rss.xml',
  '/feed.xml',
];

function args() {
  const parsed = {
    sitemap: DEFAULT_SITEMAP_INDEX,
    limitPerFamily: DEFAULT_LIMIT_PER_FAMILY,
    concurrency: DEFAULT_CONCURRENCY,
    timeoutMs: DEFAULT_TIMEOUT_MS,
    all: false,
    family: '',
  };

  for (const arg of process.argv.slice(2)) {
    if (arg === '--all') parsed.all = true;
    else if (arg.startsWith('--sitemap=')) parsed.sitemap = arg.slice('--sitemap='.length);
    else if (arg.startsWith('--limit-per-family=')) parsed.limitPerFamily = Number(arg.slice('--limit-per-family='.length));
    else if (arg.startsWith('--concurrency=')) parsed.concurrency = Number(arg.slice('--concurrency='.length));
    else if (arg.startsWith('--timeout-ms=')) parsed.timeoutMs = Number(arg.slice('--timeout-ms='.length));
    else if (arg.startsWith('--family=')) parsed.family = arg.slice('--family='.length).replace(/^\/|\/$/g, '');
    else if (arg === '--help') {
      console.log(`Usage:
  node scripts/check_live_sitemap_status.mjs [options]

Options:
  --all                         Check every live sitemap URL.
  --limit-per-family=25          Sample count per first-path route family.
  --family=review                Only check one route family.
  --concurrency=8                Concurrent URL checks.
  --timeout-ms=15000             Per-request timeout.
  --sitemap=https://...          Sitemap index or sitemap URL.
`);
      process.exit(0);
    }
  }

  if (!Number.isFinite(parsed.limitPerFamily) || parsed.limitPerFamily < 1) {
    throw new Error('--limit-per-family must be a positive number');
  }
  if (!Number.isFinite(parsed.concurrency) || parsed.concurrency < 1) {
    throw new Error('--concurrency must be a positive number');
  }
  if (!Number.isFinite(parsed.timeoutMs) || parsed.timeoutMs < 1000) {
    throw new Error('--timeout-ms must be at least 1000');
  }

  return parsed;
}

function decodeXml(value) {
  return value
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>');
}

function locs(xml) {
  return [...xml.matchAll(/<loc>([\s\S]*?)<\/loc>/gi)].map((match) => decodeXml(match[1].trim()));
}

async function fetchText(url, timeoutMs, redirect = 'follow') {
  const response = await fetch(url, {
    headers: { 'user-agent': USER_AGENT, accept: 'text/html,application/xml,text/xml,*/*' },
    redirect,
    signal: AbortSignal.timeout(timeoutMs),
  });
  return { response, text: await response.text() };
}

async function liveSitemapUrls(sitemapUrl, timeoutMs) {
  const { text } = await fetchText(sitemapUrl, timeoutMs);
  const found = locs(text);
  const isIndex = /<sitemapindex\b/i.test(text);

  if (!isIndex) return found;

  const urls = [];
  for (const child of found) {
    const { text: childXml } = await fetchText(child, timeoutMs);
    urls.push(...locs(childXml));
  }
  return [...new Set(urls)].sort();
}

function familyFor(url) {
  const { pathname } = new URL(url);
  const first = pathname.split('/').filter(Boolean)[0];
  return first || 'home';
}

function stratifiedSample(urls, limitPerFamily, onlyFamily) {
  const byFamily = new Map();

  for (const url of urls) {
    const family = familyFor(url);
    if (onlyFamily && family !== onlyFamily) continue;
    byFamily.set(family, [...(byFamily.get(family) || []), url]);
  }

  const selected = new Set();
  for (const [family, familyUrls] of byFamily.entries()) {
    const sorted = [...familyUrls].sort();
    const limit = Math.min(limitPerFamily, sorted.length);
    if (limit === sorted.length) {
      sorted.forEach((url) => selected.add(url));
      continue;
    }

    for (let index = 0; index < limit; index += 1) {
      const sampleIndex = Math.floor((index * (sorted.length - 1)) / (limit - 1));
      selected.add(sorted[sampleIndex]);
    }
  }

  for (const pathname of PRIORITY_PATHS) {
    const priorityUrl = new URL(pathname, SITE_ORIGIN).href;
    if (!onlyFamily || familyFor(priorityUrl) === onlyFamily) selected.add(priorityUrl);
  }

  return [...selected].sort();
}

function hasNoindex(headers, body) {
  const xRobots = headers.get('x-robots-tag') || '';
  if (/\bnoindex\b/i.test(xRobots)) return true;
  return /<meta\b[^>]*name=["']robots["'][^>]*content=["'][^"']*\bnoindex\b/i.test(body);
}

async function checkUrl(url, timeoutMs) {
  const startedAt = Date.now();
  try {
    const response = await fetch(url, {
      headers: { 'user-agent': USER_AGENT, accept: 'text/html,application/xml,text/xml,*/*' },
      redirect: 'manual',
      signal: AbortSignal.timeout(timeoutMs),
    });
    const body = await response.text();
    const elapsedMs = Date.now() - startedAt;
    const location = response.headers.get('location') || '';
    const noindex = hasNoindex(response.headers, body);
    const issues = [];

    if (response.status >= 300 && response.status < 400) issues.push('redirect_in_sitemap');
    if (response.status >= 400 && response.status < 500) issues.push('client_error');
    if (response.status >= 500) issues.push('server_error');
    if (noindex) issues.push('noindex_in_sitemap');

    return {
      url,
      family: familyFor(url),
      status: response.status,
      ok: issues.length === 0,
      issues,
      location,
      elapsedMs,
      contentType: response.headers.get('content-type') || '',
      xRobotsTag: response.headers.get('x-robots-tag') || '',
    };
  } catch (error) {
    return {
      url,
      family: familyFor(url),
      status: 0,
      ok: false,
      issues: ['fetch_failed'],
      error: error?.message || String(error),
      elapsedMs: Date.now() - startedAt,
    };
  }
}

async function mapConcurrent(items, concurrency, mapper) {
  const results = new Array(items.length);
  let next = 0;

  async function worker() {
    while (next < items.length) {
      const index = next;
      next += 1;
      results[index] = await mapper(items[index], index);
    }
  }

  await Promise.all(Array.from({ length: Math.min(concurrency, items.length) }, worker));
  return results;
}

function summarize(results) {
  const byFamily = {};
  const issueCounts = {};
  for (const result of results) {
    byFamily[result.family] ||= { checked: 0, ok: 0, failed: 0 };
    byFamily[result.family].checked += 1;
    if (result.ok) byFamily[result.family].ok += 1;
    else byFamily[result.family].failed += 1;
    for (const issue of result.issues || []) issueCounts[issue] = (issueCounts[issue] || 0) + 1;
  }
  return { byFamily, issueCounts };
}

async function main() {
  const options = args();
  const sitemapUrls = await liveSitemapUrls(options.sitemap, options.timeoutMs);
  const urlsToCheck = options.all
    ? sitemapUrls.filter((url) => !options.family || familyFor(url) === options.family)
    : stratifiedSample(sitemapUrls, options.limitPerFamily, options.family);

  const startedAt = new Date();
  const results = await mapConcurrent(urlsToCheck, options.concurrency, (url) => checkUrl(url, options.timeoutMs));
  const failed = results.filter((result) => !result.ok);
  const summary = summarize(results);

  const report = {
    generatedAt: new Date().toISOString(),
    sitemap: options.sitemap,
    mode: options.all ? 'all' : 'stratified-sample',
    limitPerFamily: options.all ? null : options.limitPerFamily,
    family: options.family || null,
    timeoutMs: options.timeoutMs,
    concurrency: options.concurrency,
    liveSitemapUrlCount: sitemapUrls.length,
    checkedUrlCount: results.length,
    failedUrlCount: failed.length,
    elapsedMs: Date.now() - startedAt.getTime(),
    summary,
    failures: failed,
  };

  mkdirSync(join(process.cwd(), 'reports'), { recursive: true });
  writeFileSync(REPORT_PATH, `${JSON.stringify(report, null, 2)}\n`);

  if (failed.length) {
    console.error(`[live-sitemap] FAILED — ${failed.length}/${results.length} checked URL(s) have crawler-visible issues.`);
    for (const result of failed.slice(0, 25)) {
      const location = result.location ? ` -> ${result.location}` : '';
      const error = result.error ? ` (${result.error})` : '';
      console.error(`  - ${result.status} ${result.url}${location} [${result.issues.join(', ')}]${error}`);
    }
    if (failed.length > 25) console.error(`  ... and ${failed.length - 25} more`);
    console.error(`[live-sitemap] report: ${REPORT_PATH}`);
    process.exit(1);
  }

  console.log(`[live-sitemap] OK — checked ${results.length}/${sitemapUrls.length} live sitemap URL(s), failures=0.`);
  console.log(`[live-sitemap] report: ${REPORT_PATH}`);
}

main().catch((error) => {
  console.error(`[live-sitemap] FAILED — ${error?.message || error}`);
  process.exit(1);
});
