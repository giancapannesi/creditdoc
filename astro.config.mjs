// @ts-check
import { defineConfig } from 'astro/config';
import { execSync } from 'node:child_process';
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';
import tailwindcss from '@tailwindcss/vite';
import sitemap from '@astrojs/sitemap';
import cloudflare from '@astrojs/cloudflare';

// CDM-REV iter 36 (Task #41): SSR routes without getStaticPaths cannot be
// discovered by @astrojs/sitemap.
// Pull per-slug URLs from the local SQLite source-of-truth at build time and
// inject via customPages. Sync execSync is fine — runs once at build, ~50ms.
const SITE = 'https://www.creditdoc.co';

function normalizeDate(value) {
  if (!value) return null;
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return null;
  return parsed.toISOString().slice(0, 10);
}

function fileDate(relativePath) {
  try {
    return statSync(join(process.cwd(), relativePath)).mtime.toISOString().slice(0, 10);
  } catch {
    return null;
  }
}

function addLastmod(map, path, date) {
  const normalized = normalizeDate(date);
  if (!normalized) return;
  const cleanPath = path.endsWith('/') ? path : `${path}/`;
  map.set(`${SITE}${cleanPath}`, normalized);
}

function latestDate(current, candidate) {
  const normalized = normalizeDate(candidate);
  if (!normalized) return current;
  if (!current) return normalized;
  return new Date(normalized).getTime() > new Date(current).getTime() ? normalized : current;
}

function loadJson(relativePath) {
  return JSON.parse(readFileSync(join(process.cwd(), relativePath), 'utf8'));
}

function loadSitemapLastmodMap() {
  const lastmods = new Map();

  const staticPages = [
    ['/', 'src/pages/index.astro'],
    ['/about/', 'src/pages/about.astro'],
    ['/about/harvey-brooks/', 'src/pages/about/harvey-brooks.astro'],
    ['/about/creditdoc-data/', 'src/pages/about/creditdoc-data.astro'],
    ['/answers/', 'src/pages/answers/index.astro'],
    ['/blog/', 'src/pages/blog/index.astro'],
    ['/financial-wellness/', 'src/pages/financial-wellness/index.astro'],
    ['/tools/', 'src/pages/tools/index.astro'],
    ['/courses/', 'src/pages/courses/index.astro'],
    ['/state/', 'src/pages/state/index.astro'],
    ['/research/', 'src/pages/research/index.astro'],
    ['/research/consumer-complaints/', 'src/pages/research/consumer-complaints.astro'],
    ['/research/lending-transparency/', 'src/pages/research/lending-transparency.astro'],
    ['/research/most-responsive-consumer-finance-providers-2026/', 'src/pages/research/most-responsive-consumer-finance-providers-2026.astro'],
    ['/research/state-of-subprime-lending-2026/', 'src/pages/research/state-of-subprime-lending-2026.astro'],
    ['/methodology/', 'src/pages/methodology.astro'],
    ['/editorial-policy/', 'src/pages/editorial-policy.astro'],
    ['/disclaimer/', 'src/pages/disclaimer.astro'],
    ['/disclosure/', 'src/pages/disclosure.astro'],
    ['/privacy/', 'src/pages/privacy.astro'],
    ['/terms/', 'src/pages/terms.astro'],
    ['/contact/', 'src/pages/contact.astro'],
    ['/faq/', 'src/pages/faq.astro'],
    ['/press/', 'src/pages/press.astro'],
    ['/deals/', 'src/pages/deals.astro'],
    ['/resources/loan-approval-readiness-toolkit/', 'src/pages/resources/loan-approval-readiness-toolkit/index.astro'],
    ['/resources/credit-report-checklist/', 'src/pages/resources/credit-report-checklist/index.astro'],
  ];
  for (const [path, source] of staticPages) {
    addLastmod(lastmods, path, fileDate(source));
  }

  try {
    const answersDir = join(process.cwd(), 'src/content/answers');
    for (const file of readdirSync(answersDir).filter((name) => name.endsWith('.json'))) {
      const path = join('src/content/answers', file);
      const data = loadJson(path);
      const slug = data.slug || file.replace(/\.json$/, '');
      addLastmod(
        lastmods,
        `/answers/${slug}/`,
        data.seo_meta_reviewed_at || data.last_updated || data.published_at || fileDate(path)
      );
    }
  } catch (err) {
    console.warn('[sitemap] answer lastmod index skipped:', err.message);
  }

  try {
    const brandsDir = join(process.cwd(), 'src/content/brands');
    for (const file of readdirSync(brandsDir).filter((name) => name.endsWith('.json'))) {
      const path = join('src/content/brands', file);
      const data = loadJson(path);
      const slug = data.slug || file.replace(/\.json$/, '');
      addLastmod(lastmods, `/brand/${slug}/`, data.last_updated || data.updated_at || fileDate(path));
    }
  } catch (err) {
    console.warn('[sitemap] brand lastmod index skipped:', err.message);
  }

  try {
    const states = loadJson('src/content/states.json');
    const statesDate = fileDate('src/content/states.json');
    for (const state of Object.values(states)) {
      const slug = state?.slug || state?.name?.toLowerCase().replace(/\s+/g, '-');
      if (slug) {
        addLastmod(lastmods, `/state/${slug}/`, state.last_updated || statesDate);
        addLastmod(lastmods, `/state/${slug}/lending-laws/`, state.last_updated || statesDate);
      }
    }
  } catch (err) {
    console.warn('[sitemap] state lastmod index skipped:', err.message);
  }

  try {
    const course = loadJson('src/content/course-credit-fundamentals.json');
    const courseDate = course.last_updated || fileDate('src/content/course-credit-fundamentals.json');
    addLastmod(lastmods, '/courses/credit-fundamentals/', courseDate);
    for (const module of course.modules || []) {
      if (module.slug) {
        addLastmod(lastmods, `/courses/credit-fundamentals/${module.slug}/`, module.last_updated || courseDate);
      }
    }
  } catch (err) {
    console.warn('[sitemap] course lastmod index skipped:', err.message);
  }

  try {
    const listiclesDate = fileDate('src/content/listicles.json');
    const listicles = loadJson('src/content/listicles.json');
    for (const item of Array.isArray(listicles) ? listicles : Object.values(listicles)) {
      if (item?.slug) {
        addLastmod(lastmods, `/best/${item.slug}/`, item.last_updated || item.updated_at || listiclesDate);
      }
    }
  } catch (err) {
    console.warn('[sitemap] listicle file lastmod index skipped:', err.message);
  }

  try {
    const toolDir = join(process.cwd(), 'src/pages/tools');
    for (const file of readdirSync(toolDir).filter((name) => name.endsWith('.astro') && name !== 'index.astro')) {
      addLastmod(lastmods, `/tools/${file.replace(/\.astro$/, '')}/`, fileDate(join('src/pages/tools', file)));
    }
  } catch (err) {
    console.warn('[sitemap] tool lastmod index skipped:', err.message);
  }

  try {
    const sql = `
      SELECT '/review/' || slug || '/' AS path, updated_at AS lastmod FROM lenders WHERE processing_status='ready_for_index'
      UNION ALL SELECT '/categories/' || slug || '/' AS path, updated_at AS lastmod FROM categories
      UNION ALL SELECT '/blog/' || slug || '/' AS path, updated_at AS lastmod FROM blog_posts WHERE status='published'
      UNION ALL SELECT '/financial-wellness/' || slug || '/' AS path, updated_at AS lastmod FROM wellness_guides
      UNION ALL SELECT '/answers/' || slug || '/' AS path, COALESCE(last_updated, published_at, updated_at) AS lastmod FROM cluster_answers WHERE status='published'
      UNION ALL SELECT '/best/' || slug || '/' AS path, updated_at AS lastmod FROM listicles
      UNION ALL SELECT '/compare/' || slug || '/' AS path, updated_at AS lastmod FROM comparisons;
    `;
    const out = execSync(`sqlite3 -json data/creditdoc.db "${sql.replace(/\n\s+/g, ' ').replace(/"/g, '\\"')}"`, {
      encoding: 'utf8',
      cwd: process.cwd(),
      maxBuffer: 32 * 1024 * 1024,
    });
    const rows = JSON.parse(out || '[]');
    let latestAnswer = null;
    let latestBlog = null;
    let latestWellness = null;
    let latestReview = null;
    for (const row of rows) {
      const path = row.path;
      const date = row.lastmod;
      if (path && date) {
        addLastmod(lastmods, path, date);
        if (path.startsWith('/answers/')) latestAnswer = latestDate(latestAnswer, date);
        if (path.startsWith('/blog/')) latestBlog = latestDate(latestBlog, date);
        if (path.startsWith('/financial-wellness/')) latestWellness = latestDate(latestWellness, date);
        if (path.startsWith('/review/')) latestReview = latestDate(latestReview, date);
      }
    }
    addLastmod(lastmods, '/answers/', latestAnswer);
    addLastmod(lastmods, '/blog/', latestBlog);
    addLastmod(lastmods, '/financial-wellness/', latestWellness);
    addLastmod(lastmods, '/review/', latestReview);
    addLastmod(lastmods, '/', [latestAnswer, latestBlog, latestWellness].reduce(latestDate, null));
  } catch (err) {
    console.warn('[sitemap] DB lastmod index skipped:', err.message);
  }

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
        `curl -s "https://pndpnjjkhknmutlmlwsk.supabase.co/rest/v1/city_guides?status=eq.ready_for_index&select=slug,updated_at" -H "apikey: ${anonKey}" -H "Authorization: Bearer ${anonKey}"`,
        { encoding: 'utf8', timeout: 120000 }
      );
      const cityGuides = JSON.parse(cgOut);
      if (Array.isArray(cityGuides)) {
        for (const cg of cityGuides) {
          if (cg.slug) {
            addLastmod(lastmods, `/credit-guide/${cg.slug}/`, cg.updated_at);
          }
        }
      }
    }
  } catch (err) {
    console.warn('[sitemap] city guide lastmod index skipped:', err.message);
  }

  console.log(`[sitemap] loaded ${lastmods.size} truthful lastmod URL(s)`);
  return lastmods;
}

const sitemapLastmods = loadSitemapLastmodMap();

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
    const urls = [];

    // State roots are SEO-critical SSR pages. Keep them independent from the
    // optional local SQLite export below so a missing/stale DB cannot remove
    // /state/<slug>/ from clean deploy sitemaps.
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

    const sql = `
      SELECT 'categories/' || slug FROM categories;
      SELECT 'review/' || slug FROM lenders WHERE processing_status='ready_for_index';
      SELECT DISTINCT brand_slug FROM lenders
        WHERE brand_slug IS NOT NULL AND brand_slug <> ''
          AND processing_status='ready_for_index';
    `;
    try {
      const out = execSync(`sqlite3 data/creditdoc.db "${sql.replace(/\n\s+/g, ' ').replace(/"/g, '\\"')}"`, {
        encoding: 'utf8',
        cwd: process.cwd(),
      });
      const lines = out.split('\n').map((s) => s.trim()).filter(Boolean);
      let droppedBrands = 0;
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
    } catch (dbErr) {
      console.warn('[sitemap] local DB-backed SSR URLs skipped (non-fatal):', dbErr.message);
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
            }
          }
          if (cityGuides.length > 0) {
            console.log(`[sitemap] added ${cityGuides.length} city guide root URL(s); category sub-pages are noindex/follow and omitted`);
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
          // SEO content that is prerendered into real HTML should bypass the
          // Worker route table entirely.
          { pattern: '/answers' },
          { pattern: '/answers/*' },
          { pattern: '/blog' },
          { pattern: '/blog/*' },
          { pattern: '/tools' },
          { pattern: '/tools/*' },
          { pattern: '/financial-wellness' },
          { pattern: '/financial-wellness/*' },
          { pattern: '/courses' },
          { pattern: '/courses/*' },
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
        const lastmod = sitemapLastmods.get(url);
        if (lastmod) {
          item.lastmod = lastmod;
        }
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
