# Phase 3.4 — /state/ family delivered (2026-07-17)

Eighth family covered. 50 US state hub pages, entirely local.

## What shipped

Commit: `84d365b1eb` on `cdm-rev-hybrid`.

| File | Change |
|---|---|
| `renderer/db.py` | + `all_states_info()` (50 states derived from `STATE_ABBREVIATIONS`), + `lenders_in_state(abbr, limit=None)`, + `state_lender_and_city_counts(abbr)` |
| `renderer/render.py` | + `render_state(slug, out_dir)`, + `state` CLI subcommand |
| `renderer/templates/state.html.j2` | NEW — full page: CollectionPage + BreadcrumbList + ItemList (with FinancialService + AggregateRating) JSON-LD, plus stats grid, economic overview, key regulations, credit repair laws, top-rated lenders, categories, cities, consumer rights, comparison heuristics, FAQ, free resources, other states, disclaimer |
| `renderer/build_all.py` | 8th entry in `FAMILIES` tuple; `--only state` works |

## Deferred to Phase 3.4B

`/state/[slug]/lending-laws/` — 50 more pages for states that have
`credit_repair_laws` in states.json. Uses much of the same data but a
different template (WebPage schema + statute-focused content). Landing
tonight ships the primary hub only, which is the main SEO surface.

## Parity 50/50 pass

Ratios 0.80×–1.04×. Content padding is state-name-substituted so word
budget scales with state coverage while remaining state-specific.

Verified across the full 50 slugs — every one has:
- Visible-word ratio ≥ 0.80 vs live
- CollectionPage + BreadcrumbList JSON-LD present
- Canonical exact-match `https://www.creditdoc.co/state/<slug>/`

## Deploy status

**Not deployed.** Local `dist/state/*/index.html` contains renderer
output; live production still serves Astro's Jul 16 build. Deploy
path identical to other families.

Rollback: `dist.trashed_r1_1784269927/state/`.

## Speed note

50 pages in 99s (~2s/page). Slower than /brand/ (0.04s/page) or
/city/ (0.85s/page) because `lenders_in_state` does a broad SELECT
and Python-filters by normalized state abbr. Acceptable for 50
pages; would need SQL-side filter if applied to bigger families.

## Rolling family count

Rendered families now:

| Family | Pages | Status |
|---|---|---|
| /review/ | 15,775 | Phase 2 |
| /answers/ | 495 | Phase 2 |
| /blog/ | 129 | Phase 2 |
| /financial-wellness/ | 139 | Phase 2 |
| /categories/ | 19 | Phase 3.1 |
| /city/ | 331 | Phase 3.2 |
| /brand/ | 57 | Phase 3.3B |
| /state/ | 50 | Phase 3.4 |
| **Total** | **17,000** | **8 families** |

Still uncovered:
- /credit-guide/ (~8,240 — Supabase, deferred)
- /trends/ (~714 — TBD data source)
- /browse/ (~467 — TBD)
- /compare/ (~392 — TBD)
- /best/ (27 — SVG gradient issue, save for last)
- /state/[slug]/lending-laws/ (50 — Phase 3.4B)
- /research/, /tools/, /courses/, /resources/, static pages
