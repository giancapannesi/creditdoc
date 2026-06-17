#!/usr/bin/env node
// Build-time guard: every SSR route (`export const prerender = false`)
// under src/pages/ that produces user-facing URLs must have a matching
// SELECT in `ssrSitemapPages()` in astro.config.mjs. Otherwise the
// route flips to SSR but its per-slug URLs silently disappear from the
// sitemap (no `getStaticPaths` for the plugin to walk). Pattern hit
// 3× already (Apr 29, May 2 ×2). This catches it pre-merge.

import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(fileURLToPath(import.meta.url), '..', '..');
const PAGES = join(ROOT, 'src/pages');
const CONFIG = join(ROOT, 'astro.config.mjs');

// SSR pages that are intentionally NOT in the sitemap. Keep this list
// small and document the reason — every entry is a deliberate carve-out.
const EXEMPT = new Set([
  // API endpoints — JSON / handlers, never indexed
  'api/lender/[slug].ts',
  'api/search.ts',
  'api/revalidate.ts',
  // Pilot route with intentional noindex (CDM-REV-2026-04-29 §1.3)
  'r/[slug].ts',
  // Redirect-only outbound CTA route; robot-blocked and intentionally omitted from sitemap.
  'go/[slug].ts',
  // Single fixed routes — no per-slug fan-out, plugin auto-discovers
  'search.astro',
  'answers/index.astro',
  // /credit-guide/[slug] — data lives in Supabase city_guides table (not
  // local SQLite). Sitemap injection handled separately via Supabase REST
  // query in ssrSitemapPages(). Exempt from SQLite parity check.
  'credit-guide/[slug]/index.astro',
  // /credit-guide/[slug]/[category] — city×category sub-pages, dynamic SSR.
  // Sitemap injection via same Supabase REST path + categories cross-product.
  'credit-guide/[slug]/[category].astro',
]);

function walk(dir, out = []) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    const s = statSync(p);
    if (s.isDirectory()) walk(p, out);
    else if (/\.(astro|ts|js)$/.test(name)) out.push(p);
  }
  return out;
}

function isSSR(file) {
  const src = readFileSync(file, 'utf8');
  return /export\s+const\s+prerender\s*=\s*false/.test(src);
}

// Derive the route prefix the sitemap injector must cover. For
// `src/pages/blog/[slug].astro` -> `blog/`. For
// `src/pages/financial-wellness/[slug].astro` -> `financial-wellness/`.
// For `src/pages/brand/[brand].astro` -> `brand/`.
function routePrefix(rel) {
  const segments = rel.split('/');
  // Drop the last segment if it's `[slug].astro` / `[brand].astro` etc.
  const last = segments[segments.length - 1];
  if (/^\[[^\]]+\]\.(astro|ts|js)$/.test(last)) {
    return segments.slice(0, -1).join('/') + '/';
  }
  return null; // not a per-slug pattern
}

function main() {
  const config = readFileSync(CONFIG, 'utf8');
  const files = walk(PAGES);
  const ssrFiles = files.filter(isSSR);

  const failures = [];
  for (const f of ssrFiles) {
    const rel = relative(PAGES, f);
    if (EXEMPT.has(rel)) continue;
    const prefix = routePrefix(rel);
    if (!prefix) continue; // single fixed route — Astro auto-discovers
    // Two valid patterns in the injector:
    //   (a) SQL prefix literal:   'blog/' || slug
    //   (b) JS template literal:  `${SITE}/brand/${line}/` (when slugs come bare)
    // Either form must reference the prefix. Search both.
    const trimmed = prefix.replace(/\/$/, ''); // 'blog' / 'brand' / 'financial-wellness'
    const sqlPattern = new RegExp(`'${trimmed}/'\\s*\\|\\|`);
    const jsPattern = new RegExp(`/${trimmed.replace(/[-]/g, '\\-')}/\\$\\{`);
    if (!sqlPattern.test(config) && !jsPattern.test(config)) {
      failures.push({ rel, prefix });
    }
  }

  if (failures.length) {
    console.error('');
    console.error('SSR sitemap parity FAILED:');
    for (const { rel, prefix } of failures) {
      console.error(`  - src/pages/${rel} is SSR (prerender=false) but no SELECT for '${prefix}' in astro.config.mjs ssrSitemapPages()`);
    }
    console.error('');
    console.error('Fix: add a SELECT in ssrSitemapPages(), OR add the file path to EXEMPT in scripts/check_ssr_sitemap_parity.mjs with a one-line reason.');
    console.error('Why this guard exists: 3× the same regression — SSR flip drops per-slug URLs from sitemap because the plugin has no getStaticPaths to walk.');
    process.exit(1);
  }

  console.log(`[ssr-sitemap-parity] OK — checked ${ssrFiles.length} SSR routes, all per-slug prefixes covered.`);
}

main();
