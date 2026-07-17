#!/usr/bin/env node
// Guard for AI crawler discovery surfaces. This keeps llms.txt aligned with
// the public SEO assets we want Google, OpenAI, Perplexity, and other crawlers
// to understand: static hubs, tools, course pages, answers, feeds, and sitemaps.

import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(fileURLToPath(import.meta.url), '..', '..');
const ROBOTS = join(ROOT, 'public/robots.txt');
const LLMS = join(ROOT, 'public/llms.txt');
const DIST = join(ROOT, 'dist');

// robots.txt must contain zero non-standard directives (Bing parse error
// history) — no `LLMs:` line, not even as a comment. llms.txt is still
// discoverable directly at /llms.txt (which LLM crawlers auto-check).
const REQUIRED_ROBOTS_LINES = [
  'User-agent: GPTBot',
  'User-agent: ChatGPT-User',
  'User-agent: OAI-SearchBot',
  'User-agent: PerplexityBot',
];

const REQUIRED_LLMS_URLS = [
  'https://www.creditdoc.co/sitemap-index.xml',
  'https://www.creditdoc.co/rss.xml',
  'https://www.creditdoc.co/feed.xml',
  'https://www.creditdoc.co/answers/',
  'https://www.creditdoc.co/tools/',
  'https://www.creditdoc.co/financial-wellness/',
  'https://www.creditdoc.co/courses/credit-fundamentals/',
  'https://www.creditdoc.co/tools/business-loan-calculator/',
  'https://www.creditdoc.co/tools/business-line-of-credit-calculator/',
  'https://www.creditdoc.co/tools/commercial-loan-calculator/',
  'https://www.creditdoc.co/tools/sba-loan-calculator/',
  'https://www.creditdoc.co/tools/credit-score-simulator/',
  'https://www.creditdoc.co/best/best-small-business-loans/',
  'https://www.creditdoc.co/best/best-business-lines-of-credit/',
  'https://www.creditdoc.co/best/best-sba-loans/',
  'https://www.creditdoc.co/best/best-personal-loan-lenders/',
  'https://www.creditdoc.co/best/best-credit-repair-companies/',
];

const FORBIDDEN_LLMS_PATTERNS = [
  /https:\/\/www\.creditdoc\.co\/go\//,
  /https:\/\/www\.creditdoc\.co\/api\//,
  /https:\/\/www\.creditdoc\.co\/search\//,
  /https:\/\/www\.creditdoc\.co\/specials\//,
];

const FORBIDDEN_LLMS_URLS = [
  'https://www.creditdoc.co/sitemap.xml',
];

function lineSet(src) {
  return new Set(src.split('\n').map((line) => line.trim()).filter(Boolean));
}

function extractCreditDocUrls(src) {
  const urls = [];
  const pattern = /https:\/\/www\.creditdoc\.co\/[^\s)\]]+/g;
  for (const match of src.matchAll(pattern)) {
    urls.push(match[0].replace(/[.,;]+$/g, ''));
  }
  return [...new Set(urls)];
}

function urlPath(url) {
  return new URL(url).pathname;
}

function distCandidates(pathname) {
  const clean = pathname.replace(/^\/+/, '');
  if (!clean) return [join(DIST, 'index.html')];
  if (clean.endsWith('/')) return [join(DIST, clean, 'index.html')];
  return [join(DIST, clean), join(DIST, clean, 'index.html')];
}

function hasDistArtifact(url) {
  return distCandidates(urlPath(url)).some((file) => existsSync(file));
}

function main() {
  const robots = readFileSync(ROBOTS, 'utf8');
  const llms = readFileSync(LLMS, 'utf8');
  const robotsLines = lineSet(robots);
  const llmsUrls = extractCreditDocUrls(llms);

  const missingRobots = REQUIRED_ROBOTS_LINES.filter((line) => !robotsLines.has(line));
  const missingLlms = REQUIRED_LLMS_URLS.filter((url) => !llms.includes(url));
  const forbiddenLlms = FORBIDDEN_LLMS_PATTERNS.filter((pattern) => pattern.test(llms)).map((pattern) => pattern.toString());
  const forbiddenUrls = FORBIDDEN_LLMS_URLS.filter((url) => llms.includes(url));
  const missingArtifacts = existsSync(DIST)
    ? llmsUrls.filter((url) => !hasDistArtifact(url)).slice(0, 25)
    : [];

  if (missingRobots.length || missingLlms.length || forbiddenLlms.length || forbiddenUrls.length || missingArtifacts.length) {
    console.error('');
    console.error('AI ingestion contract FAILED:');
    for (const line of missingRobots) console.error(`  - robots.txt missing: ${line}`);
    for (const url of missingLlms) console.error(`  - llms.txt missing: ${url}`);
    for (const pattern of forbiddenLlms) console.error(`  - llms.txt contains forbidden pattern: ${pattern}`);
    for (const url of forbiddenUrls) console.error(`  - llms.txt advertises forbidden URL: ${url}`);
    for (const url of missingArtifacts) console.error(`  - llms.txt URL has no built dist artifact: ${url}`);
    console.error('');
    console.error('Fix: keep llms.txt focused on static, indexable, high-value CreditDoc surfaces.');
    process.exit(1);
  }

  console.log(`[ai-ingestion] OK — robots advertises llms.txt; llms.txt covers ${REQUIRED_LLMS_URLS.length} high-value URLs and ${llmsUrls.length} built artifacts.`);
}

main();
