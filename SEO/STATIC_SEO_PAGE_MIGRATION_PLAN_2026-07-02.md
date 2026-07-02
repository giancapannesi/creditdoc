# CreditDoc Static SEO Page Migration Plan

Date: 2026-07-02

## Objective

Move CreditDoc's ranking assets toward static HTML without going backwards on the content engine, daily publishing, indexing, feeds, or social automation.

The goal is not to make every URL static. The goal is to make pages that should rank fast, stable, crawlable, and independent of runtime Supabase/Worker failures.

## Working Tracker

Latest update: 2026-07-02 UTC. Owner instruction is tools first, then questions/answers. Both are now implemented and build-verified.

| Phase | Status | Route family | Why it matters | Main files | Next action |
|---|---:|---|---|---|---|
| 0 | In progress | Audit cleanup | Reduce crawler noise while static migration happens | `BaseLayout.astro`, `LenderCard.astro`, `TopPicksTable.astro`, review/best/compare CTAs | Commit after validation |
| 0 | Done | `/tools/*` | Tool pages are already static and need stronger crawl paths between calculators/quizzes | `src/pages/tools/*.astro`, `src/components/ToolRelatedLinks.astro` | Validate generated HTML and include in commit |
| 1 | Done | `/answers/[slug]/` | Keyword/FAQ answer pages | `src/pages/answers/[slug].astro` | 491 individual answer URLs generated as static HTML in `dist/answers/*/index.html`; 492 including index. |
| 1 | Done | `/answers/` | Answer index discovery | `src/pages/answers/index.astro` | Static index generated from local answers corpus. |
| 2 | Next | `/blog/[slug]/` | Editorial SEO pages should be static | `src/pages/blog/[slug].astro`, `src/utils/data-build.ts` | Convert to `getStaticPaths()` |
| 2 | Next | `/financial-wellness/[slug]/` | Helpful-content pages should be static | `src/pages/financial-wellness/[slug].astro`, `src/utils/data-build.ts` | Convert to `getStaticPaths()` |
| 2 | Pending | `/best/[slug]/` | Money pages and high-value comparisons | `src/pages/best/[slug].astro` | Replace runtime data with build-time listicles |
| 3 | Pending | Selected `/credit-guide/` pages | City/category pages closest to click range | `src/pages/credit-guide/[slug]/index.astro`, `src/pages/credit-guide/[slug]/[category].astro` | Build GSC-driven static allowlist |
| 4 | Pending | Selected `/categories/` pages | Category hubs pass relevance to money/tools pages | `src/pages/categories/[category].astro` | Staticize only useful categories first |
| 5 | Later | Selected `/review/` pages | Supporting pages, not first priority | `src/pages/review/[slug].astro` | Staticize only protected/indexed/high-impression reviews |

## Current Route Classification

### Static Now

These are already prerendered and should stay static:

- `/tools/*`
- `/courses/*`
- `/resources/*`
- `/blog/`
- `/financial-wellness/`
- `/city/`
- `/city/[slug]/`
- `/browse/[catSlug]/[citySlug]/`
- `/compare/[slug]/`
- `/trends/*`
- Core company/legal pages

### Convert To Static First

These should be the first migration batch:

- `/blog/[slug]/`
- `/financial-wellness/[slug]/`

### Convert To Static Second

These are the second migration batch:

- `/best/[slug]/`
- `/answers/[slug]/`
- `/answers/`

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

1. Commit current audit-noise cleanup after validation.
2. Convert `/blog/[slug]/` to static.
3. Build and confirm generated blog HTML exists.
4. Convert `/financial-wellness/[slug]/` to static.
5. Build and confirm generated wellness HTML exists.
6. Confirm blog/wellness URLs remain in XML sitemap.
7. Curl 5 sample blog URLs and 5 sample wellness URLs.
8. Commit Phase 1.
9. Move to `/best/[slug]/`.

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

## Current State

Already static/prerendered:

- Tools
- Course pages
- Resource pages
- Blog index
- Financial wellness index
- City index and `/city/[slug]/`
- Browse pages
- Compare pages
- Trend pages
- Core company/legal pages

Still dynamic/SSR:

- `/blog/[slug]/`
- `/financial-wellness/[slug]/`
- `/best/[slug]/`
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

## Phase 1: Static Editorial Pages

Priority: highest.

Convert these first:

- `/blog/[slug]/`
- `/financial-wellness/[slug]/`

Reason:

- They are controlled editorial SEO assets.
- They should not depend on runtime Supabase availability.
- The local build data already contains the records.
- Index pages are already static, so this is a natural next move.

Implementation:

- Remove `export const prerender = false`.
- Add `getStaticPaths()` using `getBlogPosts()` and `getWellnessGuides()`.
- Replace runtime DB helpers with `data-build` helpers:
  - `getBlogPostBySlug`
  - `getBlogPostsByCategory`
  - `getWellnessGuideBySlug`
  - `getWellnessGuides`
  - `getCategories`
  - `getGlossaryTermsForContext`
  - `getListicles`
  - `getClusterAnswers`
- Remove runtime-only Supabase related-answer fetch from blog pages and replace with local answer matching by `cluster_pillar`.
- Remove SSR cache headers from these pages because static HTML does not need them.

Validation:

- `npm run build`
- Confirm generated files exist:
  - `dist/blog/<slug>/index.html`
  - `dist/financial-wellness/<slug>/index.html`
- Confirm no route entries remain for these in `rg "prerender = false" src/pages`.
- Confirm sitemap still includes all blog and wellness URLs.
- Curl 5 sample URLs and confirm 200, canonical, no robots noindex.

## Phase 2: Static Money Pages

Priority: very high.

Convert next:

- `/best/[slug]/`
- `/answers/[slug]/`
- `/answers/`

Reason:

- These are the main keyword-targeting pages.
- GSC shows business/credit/loan impressions, but weak positions.
- Static rendering makes them faster and more reliable for crawl/index checks.
- These pages are more valuable than generic review inventory.

Implementation:

- Use `getListicles()` for `/best/[slug]/`.
- Use `getClusterAnswers()` for `/answers/[slug]/`.
- Keep data relationships local where possible.
- If live Supabase-only fields are needed, export them into the local build artifact before build instead of fetching during page render.

Validation:

- Check priority money URLs in generated sitemap.
- Curl:
  - `/best/best-sba-loans/`
  - `/best/best-business-lines-of-credit/`
  - `/tools/commercial-loan-calculator/`
  - `/answers/business-line-of-credit-guide-new-llc-bad-credit/`
- Confirm no static route produces 404/500 during build.

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
