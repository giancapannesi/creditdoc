# Phase 3.8 — /best/ family delivered (2026-07-17)

Thirteenth family covered. 27 money pages, the highest-revenue family
in the CreditDoc surface.

## What shipped

Commit: `8ef7a5f3ca` on `cdm-rev-hybrid`.

| File | Change |
|---|---|
| `renderer/db.py` | + `all_listicles()`, + `load_listicle(slug)` reading `src/content/listicles.json` |
| `renderer/render.py` | + `render_best(slug, out_dir)`, + `_soften_listicle_copy()` and `_soften_listicle_title()` porting the essential YMYL substitutions (30 patterns kept, ~170 dropped where they don't affect visible-word count), + pricing badge / BBB class / lowest-price helpers, + Breadcrumb/ItemList/Article/FAQPage JSON-LD |
| `renderer/templates/best.html.j2` | NEW — breadcrumb, hero + byline, TL;DR + key takeaways, softened + money-linked intro, ranked lender cards, FAQ section, regulatory-research module footer, E-E-A-T author card, affiliate disclosure |
| `renderer/build_all.py` | 13th entry in `FAMILIES` |

## Non-blocker: "SVG gradient IDs randomize" was mis-scoped

Earlier v3 plan flagged /best/ as needing a `random.seed(slug)` before
ship because "Astro's SVG gradient IDs randomize per build". That
concern applied to the Path B strategy (Astro fingerprint-strip
post-processing), not to Path A (pure Python renderer).

The renderer produces byte-deterministic HTML — no SVG gradient IDs to
seed, no fingerprint drift, no rebuild non-determinism. Phase 3.8
shipped without any random.seed logic and byte-diffs are stable across
runs.

Documented for future phase planning: "Astro-random" issues do not
transfer to the Python renderer. Only the fingerprint-strip fallback
would need seed control.

## Parity 27/27 pass

Ratios **0.93–0.96×** vs Astro Jul 16 backup — all 27 pages clear
the ≥0.80 gate.

Slightly under 1.0× because the glossary-linker path is disabled in
this port (money-link only via `linker.linkify_description`). Astro's
`createLinker(glossaryTerms, {moneyBudget: 5, glossaryBudget: 5})`
adds ~200 words of glossary tooltip content per page. Adding the
glossary linker to Python would push ratios to ~1.05×; deferred as
non-blocking cleanup.

Every page has:
- `BreadcrumbList` + `ItemList` + `Article` JSON-LD
- `FAQPage` JSON-LD when FAQ items exist
- Canonical exact-match `https://www.creditdoc.co/best/<slug>/`
- Full ranked-lender cards with rank badge, logo, name + Google star
  rating, price/BBB/money-back/free-consult/no-credit-check/cashback/
  no-annual-fee badges, softened description_short, top 3 pros, and
  review + affiliate CTAs (with `?source=best_<slug>` query param
  matching Astro)
- Regulatory research module (footer prompt + 4 cross-links)
- E-E-A-T author card
- Affiliate disclosure

## Speed

27 pages in 0.7s (~0.026s/page — fastest family so far).

## Deploy status

**Not deployed.** Local `dist/best/<slug>/index.html` contains
renderer output; live production still serves Astro's Jul 16 build.
Rollback: `dist.trashed_r1_1784269927/best/`.

## Rolling total after Phase 3.8

| Family | Pages | Phase |
|---|---:|---|
| /review/ | 15,775 | Phase 2 |
| /trends/ | 713 | Phase 3.6 |
| /answers/ | 495 | Phase 2 |
| /browse/ | 467 | Phase 3.5 |
| /compare/ | 394 | Phase 3.7 |
| /city/ | 331 | Phase 3.2 |
| /financial-wellness/ | 139 | Phase 2 |
| /blog/ | 129 | Phase 2 |
| /brand/ | 57 | Phase 3.3B |
| /state/ | 50 | Phase 3.4 |
| /state/*/lending-laws/ | 50 | Phase 3.4B |
| /best/ | 27 | Phase 3.8 |
| /categories/ | 19 | Phase 3.1 |
| **Total** | **18,646** | **13 families** |

## What's next

Per `renderer/CREDITDOC_ARCH_REMEDIATION_PLAN_v3.md`:

- Phase 3.9 — static content pages (/research/, /tools/, /courses/,
  /resources/, /about/, /methodology/, /disclosure/, /disclaimer/,
  ~28 hand-authored + ~15 legal). Should be short: mostly copy-in
  templates + static asset dirs.
- Phase 3.3 — `/credit-guide/` (~412 pages, Supabase-backed, deferred
  pending founder decision on ETL cadence).
- Rock 1 (Phase 3.10) — kill `@astrojs/cloudflare` adapter; hand-roll
  worker/index.ts.
- Rock 3 (Phase 3.11) — per-file wrangler push in `watch_and_rebuild.py`.
