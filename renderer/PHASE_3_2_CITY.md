# Phase 3.2 — /city/ family delivered (2026-07-17)

Sixth family now covered by the DB-authoritative Python renderer.
Extends Phase 3.1 (/categories/) by adding `/city/*` — 320 hub pages.
Second-largest SEO bet after /credit-guide/, per the debugger's
Phase 3 ordering.

## What shipped

Commit: `9d4482db00` on `cdm-rev-hybrid`.

| File | Change |
|---|---|
| `renderer/db.py` | + `cities_with_lenders(min_count=5)`, `lenders_by_city_state(city_lower, state_abbr)`, `all_categories()`, `normalize_state_abbr(state)`, `slugify_city(city)`, plus `STATE_ABBREVIATIONS` map |
| `renderer/render.py` | + `render_city(slug, out_dir)`, `city` CLI subcommand, `_CATEGORY_ALIASES` (fix-my-credit → credit-repair), `_safe_jsonld_str()` shared helper (moved out of render_category, now used by both) |
| `renderer/templates/city.html.j2` | NEW — full page: CollectionPage + BreadcrumbList + ItemList (with about.City containment) JSON-LD, category jump chips, featured 6, per-category sections × 6, federal + state rights block, local checklist CTA, FAQ block, other-cities carousel, disclaimer |
| `renderer/build_all.py` | 6th entry in `FAMILIES` tuple; `--only city` works |

## Why /city/ was picked ahead of /credit-guide/

Debugger recommendation carried forward from Phase 3.1:

1. **SEO #1 bet** — city hubs anchor the local-directory strategy and get
   ranked separately from state pages
2. **No Supabase dependency** — data is all in local SQLite (initial worry
   about Supabase turned out to be misplaced; city data comes from the
   lenders table's `company_info.city` + `company_info.state` fields)
3. **Already static-served** — `dist/_routes.json` has `/city/*` in the
   `exclude` list; safe to swap in without touching routing
4. **330-page batch** is 4x smaller than /credit-guide/'s ~8,200 —
   easier to spot-check parity on

Left for Phase 3.3+:
- `/credit-guide/` (~8,240) — biggest single family, Supabase-backed
- `/trends/` (~714) — company-level enforcement/complaint aggregates
- `/browse/` (~467) — category × city cross-slices
- `/brand/` (57), `/state/` (101), `/compare/` (392)
- `/best/` (27) — last, most revenue at stake

## How to use

```bash
# Render one city:
python3 renderer/render.py city --slug new-york-ny --output-dir /tmp/x

# Rebuild all 320 (idempotent, atomic per-file, flock-guarded):
python3 renderer/build_all.py --only city

# Dry-run to count:
python3 renderer/build_all.py --dry-run --only city
```

## Parity verified — 20/20 sampled cities across the distribution

Sample chosen: top 5 by count, mid 5, bottom 5, plus 5 random from the
middle. Every one passed:

- Visible-word ratio ≥ **0.80** vs live
- CollectionPage + BreadcrumbList JSON-LD present
- ItemList JSON-LD added when featured providers exist
- Canonical exact-match

```
  PASS new-york-ny        r=0.80  n=409  (top)
  PASS chicago-il         r=0.81  n=347
  PASS houston-tx         r=0.83  n=343
  PASS miami-fl           r=0.81  n=262
  PASS dallas-tx          r=0.80  n=246
  PASS brooklyn-ny        r=0.87  n=105
  PASS irvine-ca          r=1.13  n=18
  PASS santa-ana-ca       r=1.17  n=8   (mid)
  ... 12 more ...
  PASS wilmington-ca      r=1.30  n=5   (small)
```

**Pattern:** big cities land at floor because Astro's LocalLeadCapture +
CityLandingEnhancement contribute ~1500 visible words per page that the
renderer doesn't reproduce; small cities land above 1.0× because the
checklist/rights/FAQ blocks are a fixed ~2000-word floor regardless of
lender count.

## Deploy status

**Not deployed.** Local `dist/city/*/index.html` contains renderer output:
~120KB per top-tier city (vs Astro's ~470KB), ~50KB per small city (vs
Astro's ~120KB). Live production still serves Astro's Jul 16 build via
the worker.

Deploy path: `wrangler deploy dist` (needs `CLOUDFLARE_GLOBAL_API_KEY` +
`CLOUDFLARE_EMAIL` env, per lies_caught #2) — but only after founder
review of a spot-check render.

Rollback: `dist.trashed_r1_1784269927/city/` retains all 332 Astro-built
pages.

## Coverage gap

**12 Astro-built /city/ pages are not renderer-covered** (Astro's
`company_info`-based grouping saw ≥5 lenders per city; my SQLite counting
disagreed by 1–2 lenders because of state-abbreviation normalization edge
cases). Those directories keep their Astro Jul 16 index.html unchanged.
If a founder review flags any of them as still-needed, the fix is a
one-line adjustment to `normalize_state_abbr` or the ≥5 threshold.

## Simplifications vs Astro

Astro renders three components the Phase 3.2 template does NOT reproduce:

- `LocalLeadCapture` (331 lines) — category-specific signup blocks with
  state consumer rights context. Replaced by a static "Get the {city}
  Credit & Borrowing Checklist" block.
- `CityLandingEnhancement` (121 lines) — per-city curated content read
  from `content/local-city-landing-enhancements.json`. Skipped entirely
  (only ~30 cities have curated entries).
- State economic context strip (avg credit score, median income, poverty
  rate, payday-loan status) — needs `states.json` reader. Skipped for
  now; the state rights block below already carries similar signal.

## What's next

**Phase 3.3 → /credit-guide/ (~8,240 pages)** — biggest single family
and Supabase-backed (per debugger's earlier note about
`local-city-landing-enhancements.json` being Supabase-hydrated for
credit-guide, not city). The Phase 3.2 pattern gives us a shared
JSON-LD helper + `_safe_jsonld_str` + template chrome reuse that
should carry directly.
