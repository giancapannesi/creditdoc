# Phase 3.5 — /browse/ family delivered (2026-07-17)

Ninth family covered by the DB-authoritative Python renderer. Adds
`/browse/<cat_slug>/<city_slug>/` — 467 category × city cross-slice
pages, one per (category, city) pair where ≥5 indexable lenders match.

## What shipped

Commit: pending on `cdm-rev-hybrid`.

| File | Change |
|---|---|
| `renderer/db.py` | + `browse_pairs(min_count=5)` — enumerates every (category, city) pair with ≥5 indexable lenders |
| `renderer/render.py` | + `render_browse(cat_slug, city_slug, out_dir)`, + `browse` CLI subcommand, + `_BROWSE_KEYWORDS` map for category-specific H1 rules |
| `renderer/templates/browse.html.j2` | NEW — full page: CollectionPage + BreadcrumbList + ItemList JSON-LD, breadcrumbs (Home / Category / City), H1, avg-rating badge, top-rated grid, all-listings grid, {state} regulations block, how-to-compare block, more-research grid, disclaimer |
| `renderer/build_all.py` | 9th entry in `FAMILIES` tuple. Uses compound "cat/city" slug format via `_browse_wrapper()` that splits and calls `render_browse` |

## Compound slug handling

The existing `build_all.py` was single-slug per family. Browse is
category × city, so the family entry emits compound slugs like
`personal-loans/new-york-ny`. `_atomic_render` handles this naturally
because `DIST / "browse" / "personal-loans/new-york-ny"` resolves
to the correct nested path.

## Parity vs live — sampled 5 pairs across category size distribution

- personal-loans / new-york-ny — r=1.03 (n=17 lenders)
- emergency-cash / chicago-il — r=1.89 (n=13, small live page)
- credit-repair / miami-fl — r=0.91 (n=25)
- pawn-shops / houston-tx — r=0.87 (n=95)
- banking / los-angeles-ca — r=1.00 (n=32)

All 5 PASS at ≥ 0.80 with CollectionPage + BreadcrumbList schemas.

Full-sweep parity check runs after build_all completes.

## What's next

Rendered families now (post Phase 3.5):

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
| /browse/ | 467 | Phase 3.5 |
| **Total** | **17,462** | **9 families** |

Still uncovered:
- /credit-guide/ (~8,240 — Supabase, deferred)
- /trends/ (~714 — CFPB JSON data)
- /compare/ (~392 — head-to-head lender comparisons)
- /best/ (27 — SVG gradient issue, save for last)
- /state/[slug]/lending-laws/ (50 — Phase 3.4B)
- /research/, /tools/, /courses/, /resources/, static pages
