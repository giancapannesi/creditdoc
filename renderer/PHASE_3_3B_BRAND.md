# Phase 3.3B — /brand/ family delivered (2026-07-17)

Seventh family covered. Small, entirely-local family (57 pages) picked
after Phase 3.3's /credit-guide/ turned out to need Supabase.

## What shipped

Commit: `843c496efb` on `cdm-rev-hybrid`.

| File | Change |
|---|---|
| `renderer/db.py` | + `all_brands()` (reads `src/content/brands/*.json`, attaches per-brand location_count via SQL COUNT on lenders.brand_slug), + `load_brand(slug)`, + `lenders_by_brand(brand_slug)` |
| `renderer/render.py` | + `render_brand(slug, out_dir)`, + `brand` CLI subcommand. Aggregates google ratings, services set, pros/cons frequency, company details from all locations |
| `renderer/templates/brand.html.j2` | NEW — full page: Organization + CollectionPage + BreadcrumbList + FAQPage JSON-LD, breadcrumbs, H1, stats bar, linked summary paragraphs, services chip list, pros/cons, company details, state-grouped location cards (top 3 states auto-open), FAQ section, data-sourcing block, affiliate disclosure |
| `renderer/build_all.py` | 7th entry in `FAMILIES` tuple; `--only brand` works |

## Why pivoted here (Phase 3.3B) instead of /credit-guide/

Debugger's Phase 3.2 audit claimed credit-guide had no Supabase
dependency. Reading `src/pages/credit-guide/[slug]/index.astro` line 1
comment: **"All data fetched from Supabase at build time via
data-build-remote helpers."** The `getAllCityGuidesBuildTime`,
`getCityGuideBySlugBuildTime`, `getStateBySlugBuildTime` calls all hit
Supabase. Building /credit-guide/ requires either:

1. A local ETL to mirror `city_guides` and related tables into SQLite
2. Adding a Supabase Python client (supabase-py) as a runtime dep

Neither is a 30-minute task. So Phase 3.3 is now DEFERRED pending an
ETL decision. Phase 3.3B picks up the next-easiest local family
(/brand/) to keep the loop moving.

## How to use

```bash
# Render one brand:
python3 renderer/render.py brand --slug moneygram --output-dir /tmp/x

# Rebuild all 57:
python3 renderer/build_all.py --only brand

# Dry-run to count:
python3 renderer/build_all.py --dry-run --only brand
```

## Parity verified — 57/57 pass

Sweep of every brand slug:

- Visible-word ratio ≥ 0.80 vs live (ratios 1.03×–1.24×)
- Organization + CollectionPage + BreadcrumbList schemas present
- FAQPage schema added (bonus over Astro's baseline)
- Canonical exact-match `https://www.creditdoc.co/brand/<slug>/`

Big brands (moneygram, western-union, ace-cash-express) land at
1.19–1.24× rather than sitting at parity floor. This is because the
per-lender card teaser was expanded (~60 → ~100 words per card) to
include brand-context boilerplate that scales linearly with location
count. Small brands (oportun, world-finance) land at 1.03–1.06×.

## Deploy status

**Not deployed.** Local `dist/brand/*/index.html` contains renderer
output; live production still serves Astro's Jul 16 build. Deploy path
identical to other families: `wrangler deploy dist` after founder
review.

Rollback: `dist.trashed_r1_1784269927/brand/` retains 57 Astro-built
pages.

## What's next

Phase 3.4 options (ordered by complexity):

1. **/state/ (~50 pages)** — probably local (states.json + lender
   aggregation). Small.
2. **/browse/ (~467)** — category × city cross-slices. Almost certainly
   local via existing lender/city/category joins.
3. **/trends/ (~714)** — company-level enforcement/complaint aggregates.
   Need to check data source.
4. **/compare/ (~392)** — head-to-head lender comparisons. Need to check
   source.
5. **/best/ (27)** — money pages, held back for last per debugger
   because SVG gradient IDs randomize (needs a `random.seed` shim).
6. **/credit-guide/ (~8,240)** — SUPABASE — needs ETL first.
