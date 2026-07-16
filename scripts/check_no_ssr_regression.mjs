#!/usr/bin/env node
/**
 * check_no_ssr_regression.mjs
 *
 * Fails the build if any content page has `export const prerender = false`
 * (i.e. is server-rendered on each request instead of prerendered as static HTML).
 *
 * Why this exists:
 *   On 2026-04-29/30 the "CDM-REV Phase 5.1" commits flipped /answers/[slug],
 *   /best/[slug], /categories, /brand, /blog, /wellness from prerendered static
 *   HTML → runtime SSR. Bing's crawler responded by dropping the site from
 *   2,200+ citations to zero overnight. Traffic has not recovered.
 *
 *   This guard makes that class of change impossible to ship again without
 *   an explicit allowlist edit + founder acknowledgement.
 *
 * How to legitimately add a new SSR route:
 *   1. Get founder approval (Bing is watching).
 *   2. Add the file path to ALLOWLIST below with a comment.
 *   3. Commit the allowlist edit in the same PR as the SSR page.
 *
 * Manual run: `npm run check:no-ssr`
 * Build integration: prebuild in package.json.
 */

import { readFileSync } from 'node:fs';
import { globSync } from 'node:fs';
import { relative } from 'node:path';
import { execSync } from 'node:child_process';

const REPO_ROOT = new URL('..', import.meta.url).pathname;

// PERMANENT allowlist — pages that MUST be SSR by design.
// Adding to this = shipping a page that Astro renders on every request.
// Only add with founder approval (Bing is watching).
const PERMANENT_SSR_ALLOWLIST = new Set([
  // API endpoints — must be dynamic (accept POST, read runtime env)
  'src/pages/api/email-signup.ts',
  'src/pages/api/geo.ts',
  'src/pages/api/origination-intake.ts',
  'src/pages/api/revalidate.ts',
  'src/pages/api/search.ts',
  // Affiliate + referrer redirects — need runtime for click tracking
  'src/pages/go/[slug].ts',
  'src/pages/r/[slug].ts',
  // Feed generators — currently SSR (should be prerendered eventually but low priority)
  'src/pages/sitemap.xml.ts',
  'src/pages/feed.xml.ts',
  'src/pages/rss.xml.ts',
]);

// TEMPORARY allowlist — SSR regressions from the 2026-04-29 CDM-REV project
// that killed Bing traffic. Each of these MUST be converted to prerendered.
// This list should shrink to empty. When it does, delete it.
// Emits a WARNING per file at build time so the founder can see progress.
const TEMPORARY_SSR_ALLOWLIST = new Set([
  'src/pages/brand/[brand].astro',            // TODO: prerender all 57 brands from Supabase
  'src/pages/credit-guide/[slug]/index.astro', // TODO: prerender all 412 city guides
  'src/pages/credit-guide/[slug]/[category].astro', // TODO: prerender all guide×category pages
  'src/pages/search.astro',                    // TODO: convert to static (no async data)
]);

const ALLOWLIST = new Set([...PERMANENT_SSR_ALLOWLIST, ...TEMPORARY_SSR_ALLOWLIST]);

// Find all page files via shell — Node's built-in glob syntax varies by version
let pageFiles;
try {
  const out = execSync(
    'find src/pages -type f \\( -name "*.astro" -o -name "*.ts" -o -name "*.tsx" \\) -not -name "*.d.ts"',
    { cwd: REPO_ROOT, encoding: 'utf8' }
  );
  pageFiles = out.trim().split('\n').filter(Boolean);
} catch (err) {
  console.error('check_no_ssr_regression: failed to enumerate pages:', err.message);
  process.exit(2);
}

const violations = [];

for (const relPath of pageFiles) {
  if (ALLOWLIST.has(relPath)) continue;
  const abs = `${REPO_ROOT}${relPath}`;
  let content;
  try {
    content = readFileSync(abs, 'utf8');
  } catch {
    continue;
  }
  // Look at the frontmatter / top of file only — declarations after 120 lines
  // are almost certainly not the prerender flag.
  const head = content.split('\n').slice(0, 120).join('\n');
  // Match: export const prerender = false | export const prerender=false
  const ssrMatch = head.match(
    /^\s*export\s+const\s+prerender\s*=\s*false\s*;?/m
  );
  if (ssrMatch) {
    violations.push(relPath);
  }
}

// Also warn about pages in TEMPORARY allowlist — they're expected SSR regressions
// that still need to be converted to prerendered.
const tempSsrPresent = [];
for (const relPath of pageFiles) {
  if (!TEMPORARY_SSR_ALLOWLIST.has(relPath)) continue;
  const abs = `${REPO_ROOT}${relPath}`;
  try {
    const content = readFileSync(abs, 'utf8');
    const head = content.split('\n').slice(0, 120).join('\n');
    if (/^\s*export\s+const\s+prerender\s*=\s*false\s*;?/m.test(head)) {
      tempSsrPresent.push(relPath);
    }
  } catch { /* skip */ }
}

if (violations.length === 0) {
  console.log(
    `[check-no-ssr] OK — no new SSR regressions. ${pageFiles.length} pages checked.`
  );
  console.log(
    `[check-no-ssr]   permanent SSR (dynamic by design): ${PERMANENT_SSR_ALLOWLIST.size}`
  );
  if (tempSsrPresent.length > 0) {
    console.log(
      `[check-no-ssr]   TEMPORARY SSR (still to convert to prerendered): ${tempSsrPresent.length}`
    );
    for (const p of tempSsrPresent) console.log(`[check-no-ssr]     • ${p}`);
  } else {
    console.log(`[check-no-ssr]   temporary SSR: 0 — all reversed! delete TEMPORARY_SSR_ALLOWLIST.`);
  }
  process.exit(0);
}

console.error('');
console.error('╔════════════════════════════════════════════════════════════════════╗');
console.error('║ SSR REGRESSION DETECTED — BUILD BLOCKED                            ║');
console.error('╚════════════════════════════════════════════════════════════════════╝');
console.error('');
console.error(`Found ${violations.length} content page(s) marked SSR (prerender=false):`);
for (const v of violations) console.error(`  • ${v}`);
console.error('');
console.error('History: 2026-04-29/30 SSR conversion dropped Bing from 2,200+');
console.error('citations to zero. This guard prevents that class of regression.');
console.error('');
console.error('To fix:');
console.error('  1. Convert the page to prerendered (remove `prerender = false`,');
console.error('     add getStaticPaths() if it takes a slug param).');
console.error('  2. Or (with founder approval) add the path to ALLOWLIST in');
console.error('     scripts/check_no_ssr_regression.mjs.');
console.error('');
process.exit(1);
