# Phase 3.4B — /state/[slug]/lending-laws/ delivered (2026-07-17)

Twelfth family covered. 50 subroute pages, one per US state.

## What shipped

Commit: `d90f81b8c3` on `cdm-rev-hybrid`.

| File | Change |
|---|---|
| `renderer/db.py` | + `all_states_with_lending_laws()`, + `load_state_lending_laws(abbr)`, + `states_with_lenders(min_count=10)` for the sidebar carousel, + `glossary_grouped_for_context()` grouping the 37 lending-laws terms by canonical category (interest-and-rates → how-loans-work → credit-and-scoring → fees-and-costs → legal-terms → debt-and-recovery → mortgages → credit-cards), + `glossary_for_context()` upgraded to accept `limit=None` |
| `renderer/render.py` | + `render_state_lending_laws(compound_slug, out_dir)` parsing `"<state_slug>/lending-laws"`, + `_LOAN_TYPES` constant (personal / payday / title / installment / mortgage with icons), + inline payday-status color map |
| `renderer/templates/state_lending_laws.html.j2` | NEW — WebPage + BreadcrumbList JSON-LD, breadcrumbs, hero + "law summary checked" chip, 4 quick-reference cards, per-loan-type regulation cards, credit-repair regulations block, MLA/SCRA + state-specific veteran block, complaint ladder, official-resources sidebar, credit-repair-providers CTA, know-your-rights link block, other-state cross-links (12), expandable glossary appendix (37 grouped terms), full disclaimer |
| `renderer/build_all.py` | 12th entry in `FAMILIES` using compound slugs `"<state_slug>/lending-laws"` against family_dir="state"; `_purge_stale()` handles the compound path natively |

## Compound slug pattern

This is the first family that lives at a subroute (`/state/<state>/lending-laws/`)
rather than a flat family-name-slugged URL. The renderer handles this
by using compound slugs like `"alabama/lending-laws"` with `family_dir="state"`,
so `_atomic_render` writes to `dist/state/alabama/lending-laws/index.html`.

`_purge_stale()` from the Phase C fixup already handled compound
correctly — it detects `/` in the slug set and walks two dir levels.
State primary (`/state/<slug>/`, non-compound) and state-laws
(`/state/<slug>/lending-laws/`, compound) coexist cleanly because the
level-1 purge for the primary family only looks at the top level and
leaves `dist/state/alabama/lending-laws/` alone.

## Parity 50/50 pass

Ratios **1.12–1.13×** across every state. Full-DefinedTerm glossary
appendix is the reason we cleared the 0.80 floor by so much: initial
build with only term-name shortlist hit r=0.44 (2100 words vs Astro's
4780). Rendering all 37 lending-laws-tagged terms with
`plain_definition + why_it_matters + example` added ~3200 words per
page and got us to full parity.

Every page has:
- `WebPage` + `BreadcrumbList` JSON-LD
- Canonical exact-match `https://www.creditdoc.co/state/<slug>/lending-laws/`
- Payday status color-coded (green Banned / amber Restricted / red Legal)
- 4 quick-reference stats
- Full regulation stack for the 5 loan types
- Credit-repair statute block with bond/registration/cancellation grid
- MLA/SCRA + state-specific veteran protections
- Complaint escalation ladder (compliance → state → CFPB → small claims → military legal aid)
- Sidebar: statute links + consumer protection agency link + credit-repair CTA + wellness cross-links + 12 other states

## Speed

50 pages in 45.9s (~0.9s/page). Slower than `/brand/` (0.04s/page)
because of the glossary rendering + `lenders_in_state()` broad-select
+ per-page normalize; acceptable at 50 pages.

## Deploy status

**Not deployed.** Local `dist/state/*/lending-laws/index.html` contains
renderer output; live production still serves Astro's Jul 16 build.
Rollback: `dist.trashed_r1_1784269927/state/*/lending-laws/`.

## Rolling total after Phase 3.4B

| Family | Pages | Phase |
|---|---:|---|
| /review/ | 15,775 | Phase 2 |
| /trends/ | 713 | Phase 3.6 |
| /answers/ | 495 | Phase 2 |
| /compare/ | 394 | Phase 3.7 |
| /city/ | 331 | Phase 3.2 |
| /financial-wellness/ | 139 | Phase 2 |
| /blog/ | 129 | Phase 2 |
| /brand/ | 57 | Phase 3.3B |
| /state/ | 50 | Phase 3.4 |
| /state/*/lending-laws/ | 50 | Phase 3.4B |
| /browse/ | 467 | Phase 3.5 |
| /categories/ | 19 | Phase 3.1 |
| **Total** | **18,619** | **12 families** |

## What's next

- Phase 3.8 — `/best/` (27 pages, money pages). Blocker: Astro's
  SVG gradient IDs randomize per build; renderer must
  `random.seed(slug)` before ID generation for byte-deterministic
  output.
- Phase 3.9 — static content pages (/research/, /tools/, /courses/,
  /resources/, /about/, /methodology/, /disclosure/, etc.)
- Phase 3.3 — `/credit-guide/` (~412 pages). Blocker: Supabase ETL for
  `city_guides` table.
- Rock 1 (Phase 3.10) — kill `@astrojs/cloudflare` adapter; hand-roll
  worker/index.ts for the 6 remaining SSR routes.
- Rock 3 (Phase 3.11) — per-file wrangler push in `watch_and_rebuild.py`.
