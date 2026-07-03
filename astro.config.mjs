// @ts-check
import { defineConfig } from 'astro/config';
import { execSync } from 'node:child_process';
import { readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import tailwindcss from '@tailwindcss/vite';
import sitemap from '@astrojs/sitemap';
import cloudflare from '@astrojs/cloudflare';

// CDM-REV iter 36 (Task #41): SSR routes without getStaticPaths cannot be
// discovered by @astrojs/sitemap.
// Pull per-slug URLs from the local SQLite source-of-truth at build time and
// inject via customPages. Sync execSync is fine — runs once at build, ~50ms.
const SITE = 'https://www.creditdoc.co';
function ssrSitemapPages() {
  try {
    // iter 37 fix: brand sitemap entries must cross-check against an actual
    // brand record file in src/content/brands/, otherwise crawlers hit a 404
    // (DB has lenders with brand_slug, but no matching brand profile exists).
    const brandFiles = new Set(
      readdirSync(join(process.cwd(), 'src/content/brands'))
        .filter((f) => f.endsWith('.json'))
        .map((f) => f.replace(/\.json$/, ''))
    );
    const stateData = JSON.parse(readFileSync(join(process.cwd(), 'src/content/states.json'), 'utf8'));
    const stateRows = Object.values(stateData);
    const sql = `
      SELECT 'categories/' || slug FROM categories;
      SELECT 'review/' || slug FROM lenders WHERE processing_status='ready_for_index';
      SELECT DISTINCT brand_slug FROM lenders
        WHERE brand_slug IS NOT NULL AND brand_slug <> ''
          AND processing_status='ready_for_index';
    `;
    const out = execSync(`sqlite3 data/creditdoc.db "${sql.replace(/\n\s+/g, ' ').replace(/"/g, '\\"')}"`, {
      encoding: 'utf8',
      cwd: process.cwd(),
    });
    const lines = out.split('\n').map((s) => s.trim()).filter(Boolean);
    let droppedBrands = 0;
    const urls = [];
    for (const line of lines) {
      // Brand slug rows are bare slugs (no '/'); blog/wellness rows already
      // carry their prefix. Differentiate by '/' presence.
      if (!line.includes('/')) {
        // Bare brand slug — keep only if a matching brand file exists.
        if (brandFiles.has(line)) {
          urls.push(`${SITE}/brand/${line}/`);
        } else {
          droppedBrands += 1;
        }
      } else {
        urls.push(`${SITE}/${line}/`);
      }
    }
    if (droppedBrands > 0) {
      console.log(`[sitemap] dropped ${droppedBrands} brand slug(s) with no brand record`);
    }
    if (Array.isArray(stateRows)) {
      let addedStateRoots = 0;
      for (const state of stateRows) {
        const slug = state?.slug || state?.name?.toLowerCase().replace(/\s+/g, '-');
        if (slug) {
          urls.push(`${SITE}/state/${slug}/`);
          addedStateRoots += 1;
        }
      }
      console.log(`[sitemap] added ${addedStateRoots} state root URL(s)`);
    }

    // City guides live in Supabase (not local SQLite). Read anon key from env
    // file and fetch slugs at build time via REST.
    try {
      const envFile = join(process.cwd(), '..', 'tools', '.supabase-creditdoc.env');
      const envLines = readFileSync(envFile, 'utf8').split('\n');
      let anonKey = process.env.SUPABASE_ANON_KEY || '';
      for (const ln of envLines) {
        const m = ln.match(/^SUPABASE_ANON_KEY=["']?([^"'\s]+)/);
        if (m) { anonKey = m[1]; break; }
      }
      if (anonKey) {
        const cgOut = execSync(
          `curl -s "https://pndpnjjkhknmutlmlwsk.supabase.co/rest/v1/city_guides?status=eq.ready_for_index&select=slug" -H "apikey: ${anonKey}" -H "Authorization: Bearer ${anonKey}"`,
          { encoding: 'utf8', timeout: 120000 }
        );
        const cityGuides = JSON.parse(cgOut);
        if (Array.isArray(cityGuides)) {
          const categorySlugs = [
            'credit-repair', 'personal-loans', 'emergency-cash', 'payday-alternatives',
            'debt-relief', 'build-credit', 'credit-monitoring', 'free-help',
            'pawn-shops', 'atm', 'credit-cards', 'business-loans', 'mortgages',
            'bankruptcy', 'check-cashing', 'insurance', 'banking', 'credit-unions',
          ];
          for (const cg of cityGuides) {
            if (cg.slug) {
              urls.push(`${SITE}/credit-guide/${cg.slug}/`);
              for (const cat of categorySlugs) {
                urls.push(`${SITE}/credit-guide/${cg.slug}/${cat}/`);
              }
            }
          }
          if (cityGuides.length > 0) {
            console.log(`[sitemap] added ${cityGuides.length} city guide(s) + ${cityGuides.length * categorySlugs.length} category sub-pages`);
          }
        }
      }
    } catch (cgErr) {
      console.warn('[sitemap] city guides fetch failed (non-fatal):', cgErr.message);
    }

    return urls;
  } catch (err) {
    console.warn('[sitemap] ssrSitemapPages failed:', err.message);
    return [];
  }
}
const ssrPages = ssrSitemapPages();
console.log(`[sitemap] injecting ${ssrPages.length} SSR route URLs`);

// CDM-REV-2026-04-29 Phase 1.2 — Cloudflare adapter for hybrid SSR.
// In Astro 5, `output: 'static'` is the new hybrid: pages prerender by default,
// individual pages opt INTO server-rendering with `export const prerender = false;`.
// Marketing pages stay prerendered; high-churn routes (/review/[slug] etc.) opt-in
// to SSR. Adapter must be present for any SSR route to build.
export default defineConfig({
  site: 'https://www.creditdoc.co',
  output: 'static',
  adapter: cloudflare({
    routes: {
      extend: {
        exclude: [
          { pattern: '/sitemap-index.xml' },
          { pattern: '/sitemap-*.xml' },
        ],
      },
    },
    // 'passthrough' avoids bundling sharp/detect-libc into the worker (which
    // breaks workerd at runtime — bare require('fs')/'child_process'). Static
    // images in dist/_astro/ are still optimized at build time. SSR pages do
    // not currently use Astro's <Image> runtime — if that changes, switch to
    // 'cloudflare' (Workers Image Resizing) rather than 'compile'.
    imageService: 'passthrough',
  }),
  build: {
    format: 'directory',
  },
  vite: {
    plugins: [tailwindcss()],
  },
  integrations: [
    sitemap({
      // Split into multiple sitemaps (~5000 URLs each) for crawl efficiency
      entryLimit: 5000,
      customPages: ssrPages,
      // Exclude utility, print, and redirect-only pages from XML sitemaps.
      // Content pages should have one useful H1; these routes are not search
      // landing pages and create crawler noise in third-party audit tools.
      filter(page) {
        const url = new URL(page);
        if (url.pathname === '/search/') return false;
        if (url.pathname === '/specials/') return false;
        if (url.pathname === '/linkedin-oauth-callback/') return false;
        if (url.pathname.endsWith('/print/')) return false;
        return true;
      },
      // Set priority + changefreq per page type
      serialize(item) {
        const url = item.url;
        if (url.includes('/best/')) {
          item.priority = 0.9;
          item.changefreq = 'weekly';
        } else if (url.includes('/answers/')) {
          item.priority = 0.85;
          item.changefreq = 'weekly';
        } else if (url.includes('/financial-wellness/')) {
          item.priority = 0.8;
          item.changefreq = 'monthly';
        } else if (url.includes('/blog/')) {
          item.priority = 0.7;
          item.changefreq = 'monthly';
        } else if (url.includes('/review/')) {
          item.priority = 0.6;
          item.changefreq = 'monthly';
        } else if (url.includes('/compare/')) {
          item.priority = 0.5;
          item.changefreq = 'monthly';
        } else if (url.includes('/city/') || url.includes('/state/')) {
          item.priority = 0.5;
          item.changefreq = 'monthly';
        } else if (url.includes('/categories/')) {
          item.priority = 0.7;
          item.changefreq = 'weekly';
        } else if (url.includes('/brand/')) {
          item.priority = 0.75;
          item.changefreq = 'weekly';
        }
        return item;
      },
    }),
  ],
});
