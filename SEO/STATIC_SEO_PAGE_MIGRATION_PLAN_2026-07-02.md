# CreditDoc Static SEO Page Migration Plan

Date: 2026-07-02

## Objective

Move CreditDoc's ranking assets toward static HTML without going backwards on the content engine, daily publishing, indexing, feeds, or social automation.

The goal is not to make every URL static. The goal is to make pages that should rank fast, stable, crawlable, and independent of runtime Supabase/Worker failures.

## Working Tracker

Latest update: 2026-07-02 UTC. Owner instruction was tools first, then questions/answers. Tools, answers, blog detail pages, financial-wellness detail pages, and `/best/` money pages are now static and build-verified.

| Phase | Status | Route family | Why it matters | Main files | Next action |
|---|---:|---|---|---|---|
| 0 | Done | Audit cleanup | Reduce crawler noise while static migration happens | `BaseLayout.astro`, `LenderCard.astro`, `TopPicksTable.astro`, review/best/compare CTAs | Build-verified; commit with static work |
| 0 | Done | `/tools/*` | Tool pages are already static and need stronger crawl paths between calculators/quizzes | `src/pages/tools/*.astro`, `src/components/ToolRelatedLinks.astro` | 19 tool/index URLs generated as static HTML. |
| 1 | Done | `/answers/[slug]/` | Keyword/FAQ answer pages | `src/pages/answers/[slug].astro` | 491 individual answer URLs generated as static HTML in `dist/answers/*/index.html`; 492 including index. |
| 1 | Done | `/answers/` | Answer index discovery | `src/pages/answers/index.astro` | Static index generated from local answers corpus. |
| 2 | Done | `/blog/[slug]/` | Editorial SEO pages should be static | `src/pages/blog/[slug].astro`, `src/utils/data-build.ts` | Static generation from local blog corpus. |
| 2 | Done | `/financial-wellness/[slug]/` | Helpful-content pages should be static | `src/pages/financial-wellness/[slug].astro`, `src/utils/data-build.ts` | Static generation from local wellness corpus. |
| 2 | Done | `/best/[slug]/` | Money pages and high-value comparisons | `src/pages/best/[slug].astro` | Static generation from local listicles and lender JSON. |
| 3 | Pending | Selected `/credit-guide/` pages | City/category pages closest to click range | `src/pages/credit-guide/[slug]/index.astro`, `src/pages/credit-guide/[slug]/[category].astro` | Build GSC-driven static allowlist |
| 4 | Pending | Selected `/categories/` pages | Category hubs pass relevance to money/tools pages | `src/pages/categories/[category].astro` | Staticize only useful categories first |
| 5 | Later | Selected `/review/` pages | Supporting pages, not first priority | `src/pages/review/[slug].astro` | Staticize only protected/indexed/high-impression reviews |

## Current Route Classification

### Static Now

These are already prerendered and should stay static:

- `/tools/*`
- `/answers/[slug]/`
- `/answers/`
- `/blog/[slug]/`
- `/courses/*`
- `/resources/*`
- `/blog/`
- `/financial-wellness/[slug]/`
- `/financial-wellness/`
- `/best/[slug]/`
- `/city/`
- `/city/[slug]/`
- `/browse/[catSlug]/[citySlug]/`
- `/compare/[slug]/`
- `/trends/*`
- Core company/legal pages

### Convert Selectively

These should not all be staticized blindly:

- `/credit-guide/[slug]/`
- `/credit-guide/[slug]/[category]/`
- `/categories/[category]/`
- `/review/[slug]/`
- `/brand/[brand]/`
- `/state/[slug]/`

### Keep Dynamic

These should remain dynamic/utility:

- `/search/`
- `/api/*`
- `/go/[slug]`
- `/r/[slug]`
- OAuth/callback pages

## Resumption Checklist

When picking this back up, continue in this order:

1. Verify the deployed sitemap includes static URLs for `/tools/`, `/answers/`, `/blog/`, `/financial-wellness/`, and `/best/`.
2. Move to selective staticization only where evidence supports it: priority candidates are high-impression `/categories/`, `/credit-guide/`, and selected indexed/high-value `/review/` pages.
3. Do not bulk-staticize every directory/review route without checking data freshness, sitemap size, and build-time impact.
4. Keep `/search/`, `/api/*`, `/go/[slug]`, `/r/[slug]`, and OAuth/callback utility pages dynamic or non-indexable as appropriate.

## Validation Commands

Run after every migration phase:

```bash
npm run build
rg -n "export const prerender = false" src/pages
find dist/blog -name index.html | wc -l
find dist/financial-wellness -name index.html | wc -l
node scripts/check_sitemap_robots_conflicts.mjs
node scripts/check_sitemap_critical_urls.mjs
node scripts/check_feed_contract.mjs
node scripts/check_image_alt_contract.mjs
node scripts/check_image_filename_contract.mjs
```

Sample live/static checks after deploy:

```bash
curl -I https://www.creditdoc.co/blog/can-a-bad-credit-score-be-fixed/
curl -I https://www.creditdoc.co/financial-wellness/free-credit-score-check-guide/
curl -I https://www.creditdoc.co/best/best-sba-loans/
curl -I https://www.creditdoc.co/answers/business-line-of-credit-guide-new-llc-bad-credit/
```

## Completed Static Migration Evidence

The main SEO assets are now static build output, not runtime-only pages.

Generated static HTML counts from the 2026-07-02 build:

- `/answers/`: 492 `index.html` files including the answer index.
- `/tools/`: 19 `index.html` files including the tools index.
- `/blog/`: 104 `index.html` files including the blog index.
- `/financial-wellness/`: 140 `index.html` files including the wellness index.
- `/best/`: 27 `index.html` files.

Implementation completed:

- `/answers/[slug]/` uses `getStaticPaths()` from `getClusterAnswers()`.
- `/answers/` builds from the local answer corpus.
- `/blog/[slug]/` uses `getStaticPaths()` from `getBlogPosts()` and local related content.
- `/financial-wellness/[slug]/` uses `getStaticPaths()` from `getWellnessGuides()` and local related content.
- `/best/[slug]/` uses `getStaticPaths()` from `getListicles()` and local lender/listicle data.
- Manual sitemap SQL injection was removed for the route families that Astro now discovers statically.
- `npm run build` passed with prebuild and postbuild checks.
- No `export const prerender = false` remains in `src/pages/blog`, `src/pages/financial-wellness`, `src/pages/best`, `src/pages/answers`, or `src/pages/tools`.

## Current State

Already static/prerendered:

- Tools and quizzes
- Answers/questions
- Blog index and blog detail pages
- Financial wellness index and guide detail pages
- `/best/` money pages
- Course pages
- Resource pages
- City index and `/city/[slug]/`
- Browse pages
- Compare pages
- Trend pages
- Core company/legal pages

Still dynamic/SSR or selective candidates:

- `/categories/[category]/`
- `/credit-guide/[slug]/`
- `/credit-guide/[slug]/[category]/`
- `/review/[slug]/`
- `/brand/[brand]/`
- `/state/[slug]/`
- `/search/`
- API and redirect routes

## Principle

Static first for editorial and money pages. Dynamic only where the page genuinely needs live query behavior.

## Phase 3: Static Selected City/Guide Pages

Priority: medium-high.

Do not staticize every generated guide blindly.

Convert in batches:

- City guide root pages that receive impressions.
- City/category pages in positions 8-30 from GSC.
- Business-loan, credit-repair, personal-loan, debt-relief, credit-card, and credit-union category combinations first.

Reason:

- City pages are closer to click range than many other families.
- But generating all city/category permutations can create crawl bloat.

Implementation:

- Create a static allowlist sourced from:
  - GSC impressions
  - manual SEO priority list
  - currently indexed URLs
  - content quality threshold
- Keep low-value or empty combinations out of the sitemap.

Validation:

- Sitemap contains only useful static guide URLs.
- No `noindex` URLs in sitemap.
- No city/category URL with zero useful listings in sitemap.

## Phase 4: Keep These Dynamic

Keep dynamic:

- `/search/`
- `/api/*`
- `/go/[slug]`
- `/r/[slug]`
- selected `/review/[slug]/` until we choose a static review subset

Reason:

- Search is a utility page, not a ranking page.
- Redirect/API routes should not be SEO landing pages.
- Review pages are numerous and noisy; staticizing all of them first would waste build time and crawl attention.

Rules:

- `/search/` remains `noindex, follow`.
- `/go/` remains blocked/noindex.
- Utility/filter pages must not be in XML sitemap.

## Phase 5: Review Pages Later, Selectively

Priority: medium.

Staticize only:

- Protected/high-value reviews.
- Reviews linked from best pages.
- Reviews already getting impressions.
- Reviews that support money pages.

Avoid:

- Staticizing thousands of low-quality provider/entity pages as the first move.
- Pushing stale/draft/skeleton review pages into the sitemap.

## Deployment Safety

Before each phase deploy:

- Run `npm run build`.
- Run sitemap/robots conflict checks.
- Run feed contract.
- Run image alt and filename contracts.
- Curl a representative sample.
- Check `git diff` for accidental sitemap bloat.

After deploy:

- Re-run SE Ranking crawl.
- Compare 5XX count, noindex-in-sitemap count, internal nofollow count, and broken image count.
- Check GSC coverage/indexing over 7-14 days.

## Expected SEO Impact

Static pages will not instantly create authority, but they should help with:

- More consistent crawl responses.
- Fewer audit false positives caused by runtime failures.
- Better crawler trust on money/editorial pages.
- Faster page fetches.
- Cleaner sitemap/indexing signals.

Expected timeframe:

- Technical audit improvements: next crawl after deploy.
- Google recrawl/indexing changes: days to a few weeks.
- Ranking/traffic movement: usually 2-8 weeks, especially for a 4-month-old site.
