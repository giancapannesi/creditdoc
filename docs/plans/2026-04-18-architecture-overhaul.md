# CreditDoc Architecture Overhaul — Kill the Full Rebuild

> **Problem:** Every content change rebuilds 16,666 pages (372 seconds). Builds fail frequently. Pages go stale. The "incremental" DB export doesn't help because Astro static mode rebuilds EVERYTHING.

> **Goal:** Deploy content changes in seconds, not minutes. Pages persist. No more build failures killing content.

---

## Current Architecture (Broken)

```
SQLite DB → creditdoc_build.py → 20K JSON files → git push → Vercel full Astro build (372s) → atomic deploy
```

**Root cause:** `data.ts` reads ALL 20,826 JSON files via `fs.readdirSync()` into memory. Every `getStaticPaths()` triggers this. Astro static mode must render ALL 16,666 pages even if only one JSON changed. There is no incremental static build in Astro.

---

## Recommendation: Astro Hybrid Mode + ISR on Vercel

**Why this wins:**
- Same framework, same templates, same components — no rewrite
- Only ~100 truly static pages build at deploy time (~30s)
- 16K+ dynamic pages served via SSR with ISR caching
- Content changes go live in seconds via revalidation API
- $0/month incremental cost (all included in Vercel Team plan)
- SEO preserved — SSR produces identical HTML to static

**Options evaluated and rejected:**
- Next.js rewrite — too risky, full rewrite for 6-10 weeks, SEO disruption
- Cloudflare Pages — violates Vercel constraint
- Static shell + API content — SEO disaster, Google sees empty pages
- Smarter static pipeline — Astro doesn't support partial static builds

---

## Migration Plan

### Phase 0: Data Layer Refactor (Week 1)

**Problem:** `data.ts` reads 20K JSON files from disk. In Vercel SSR, those files don't exist on the function filesystem.

**Solution:** Two options, start simple:

**Step 1 (Bundled SQLite — do first):**
- Copy `creditdoc.db` into the Vercel function bundle at deploy time
- Use `better-sqlite3` in SSR to query directly
- Content updates still need a deploy, BUT deploy is 30s not 372s
- This is "good enough" for Phase 1

**Step 2 (Turso — add later if needed):**
- Migrate to Turso (edge SQLite, free tier: 9GB, unlimited reads)
- Content goes live WITHOUT any deploy — just sync DB to Turso
- Python tools write locally, sync script pushes to Turso

**Files:**
- Refactor: `src/utils/data.ts` — replace `fs.readdirSync` with DB queries
- Create: `src/utils/db.ts` — database access layer
- Create: `tools/creditdoc_turso_sync.py` (Phase 2)

### Phase 1: Hybrid Mode Conversion (Week 2)

**Changes to `astro.config.mjs`:**
```javascript
import vercel from '@astrojs/vercel';
export default defineConfig({
  output: 'hybrid',        // was 'static'
  adapter: vercel({ isr: true }),  // new
  // ... rest stays the same
});
```

**Static pages** (add `export const prerender = true`):
- `about.astro`, `terms.astro`, `privacy.astro`, `404.astro`, `faq.astro`
- `methodology.astro`, `deals.astro`, `tools/*.astro`, `index.astro`
- ~100 pages, build in ~30s

**SSR pages** (remove `getStaticPaths`, use direct params):
- `review/[slug].astro` — 15K+ pages (the big win)
- `city/[slug].astro` — 261 pages
- `state/[slug].astro` — 51 pages
- `best/[slug].astro` — 18+ pages
- `compare/[slug].astro` — 134 pages
- `financial-wellness/[slug].astro` — 81 pages
- `blog/[slug].astro` — 23 pages
- `answers/[slug].astro` — 7+ growing pages
- `categories/[category].astro` — 17 pages
- `state/[slug]/lending-laws.astro` — 51 pages
- `browse/[catSlug]/[citySlug].astro` — 462 pages

**Conversion pattern for each SSR page:**

Before:
```javascript
export function getStaticPaths() {
  const lenders = getAllLenders();
  return lenders.map(l => ({ params: { slug: l.slug } }));
}
const { slug } = Astro.params;
const lender = getLenderBySlug(slug!)!;
```

After:
```javascript
// No getStaticPaths — SSR renders on demand
const { slug } = Astro.params;
const lender = await getLenderBySlug(slug!);
if (!lender) return new Response(null, { status: 404 });
```

### Phase 2: ISR + Revalidation API (Week 2-3)

**ISR expiration per page type:**
| Page Type | ISR Expiration | Rationale |
|-----------|---------------|-----------|
| Reviews | 24 hours | Low change frequency |
| Listicles (/best/) | 1 hour | Money pages, stay fresh |
| Blog/wellness | 24 hours | Rarely change |
| State/city | 24 hours | Rarely change |
| Compare | 24 hours | Rarely change |
| Answers | 24 hours | Daily additions |

**Create `api/revalidate.ts`:**
- POST with `{ slug, type, secret }`
- Validates shared secret
- Purges Vercel ISR cache for that URL
- Returns success/failure

**Update `creditdoc_build.py`:**
- After JSON export: push to Turso (or just deploy if bundled SQLite)
- Call `/api/revalidate` for each changed URL
- No more "git push and pray"

### Phase 3: DB-Driven Sitemaps (Week 3)

**Problem:** `@astrojs/sitemap` auto-discovers pages from `getStaticPaths()`. SSR pages don't have that.

**Solution:** Generate sitemaps from DB:
- `src/pages/sitemap-reviews.xml.ts` — queries DB for all review slugs
- `src/pages/sitemap-listicles.xml.ts` — all /best/ pages
- `src/pages/sitemap-index.xml.ts` — index pointing to all sub-sitemaps
- Always up-to-date with DB, better than build-time discovery

### Phase 4: SEO Testing (Week 3-4)

Before going live:
1. **URL parity:** Fetch every URL from current sitemap, verify 200 on preview
2. **Content parity:** Diff 100 sample pages (title, meta, h1, schema, canonical)
3. **Performance:** TTFB <1s for cached pages, <3s for cold
4. **Schema.org:** Structured data identical
5. **404s:** Non-existent slugs return proper 404

### Phase 5: Python Toolchain Update (Week 4)

Update scripts to work with new architecture:
- `creditdoc_build.py` — add Turso sync + revalidation
- `creditdoc_guardian.py` — add Turso sync to healing
- `creditdoc_db_sync.py` — add Turso push
- New: `creditdoc_revalidate.py` — manual revalidation tool

### Phase 6: Cutover (Week 4-5)

1. Deploy hybrid build to Vercel preview branch
2. Run full URL + content parity tests
3. If pass, merge to main
4. Monitor GSC daily for 2 weeks
5. Keep static branch for 30-day rollback

---

## Build Time Comparison

| Scenario | Now (Static) | After (Hybrid + ISR) |
|----------|:---:|:---:|
| Full deploy | 372s+ (often fails) | ~30s |
| One lender changed | 372s+ | ~2s (revalidate) |
| New lender added | 372s+ | ~2s (first visit) |
| Template change | 372s+ | ~30s + pages refresh on visit |
| 100 lenders enriched | 372s+ | ~15s (100 revalidate calls) |

## Cost

| Item | Cost |
|------|------|
| Turso Free Tier | $0/mo |
| Vercel (already paying) | No change |
| Serverless functions | Included |
| ISR cache | Included |
| **Total** | **$0/mo** |

## Rollback

- **Quick (minutes):** Revert to previous Vercel deployment via dashboard
- **Full (hours):** Revert git to pre-hybrid, push, static build resumes
- **Partial:** Add `prerender = true` to any problem route to force static

---

## Critical Files

| File | Change |
|------|--------|
| `astro.config.mjs` | `output: 'hybrid'`, add Vercel adapter |
| `src/utils/data.ts` | Refactor from filesystem to DB queries |
| `src/utils/db.ts` | New — Turso/SQLite client |
| `src/pages/review/[slug].astro` | Remove `getStaticPaths`, add SSR + 404 |
| All 10 other dynamic routes | Same conversion |
| `tools/creditdoc_build.py` | Add Turso sync + revalidation |
| `package.json` | Add `@astrojs/vercel`, `@libsql/client` |
| `api/revalidate.ts` | New — on-demand ISR purge endpoint |

## Timeline

| Week | Phase | What |
|------|-------|------|
| 1 | Phase 0 | Data layer refactor (bundled SQLite first, Turso later) |
| 2 | Phase 1 | Hybrid mode — convert 11 dynamic routes to SSR |
| 2-3 | Phase 2 | ISR config + revalidation API |
| 3 | Phase 3 | DB-driven sitemaps |
| 3-4 | Phase 4 | SEO parity testing |
| 4 | Phase 5 | Python toolchain update |
| 4-5 | Phase 6 | Cutover + monitoring |

**Total: 4-5 weeks.** Can compress to 3 if aggressive.
