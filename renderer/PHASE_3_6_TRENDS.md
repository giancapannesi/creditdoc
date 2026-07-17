# Phase 3.6 — /trends/ family delivered (2026-07-17)

Tenth family covered by the DB-authoritative Python renderer. Adds
`/trends/[slug]/` — CFPB Consumer Response profile pages, sourced from
`src/content/cfpb-trends.json` filtered against the local lenders
table to exclude archived / no-index profiles (matching Astro).

## What shipped

Commit: `9827e6231b` on `cdm-rev-hybrid`.

| File | Change |
|---|---|
| `renderer/db.py` | + `all_trends_entries()` (reads cfpb-trends.json, filters against lenders.processing_status + json_extract($.no_index) in one SQL round-trip), + `load_trends_entry(slug)` |
| `renderer/render.py` | + `render_trends(slug, out_dir)`, + `trends` CLI subcommand, + `_trends_slug_context()` helper (port of Astro's `slugContext()` — extracts non-name context words for title disambiguation) |
| `renderer/templates/trends.html.j2` | NEW — full page: WebPage + BreadcrumbList JSON-LD, breadcrumbs, H1, 3 metric cards (recorded response outcome %, timely %, total complaints), top-products progress bars, top-issues progress bars, response breakdown, transparency-context block, data-source footer |
| `renderer/build_all.py` | 10th entry in `FAMILIES` tuple; `--only trends` works |

## Count reconciliation

Raw entries in cfpb-trends.json: **775**.
After filter (exclude archived / no_index lenders): **713**.
Astro dist directory count: **714** (713 slug dirs + the `/trends/index.html` hub file).

Renderer output matches Astro's slug count exactly. The earlier
closeout draft said "1-page delta, unicode edge case" — that was
wrong; Phase 3.6 audit confirmed 713 = 713.

## Parity 20/20 pass (initial sample) + 25/25 pass (audit re-run)

Ratios ~1.4× — the renderer template is richer than Astro's because
of the "how to read this" paragraphs added after each dynamic block
(products, issues, breakdown). This is a deliberate content-budget
choice so sparse-data entries still pass parity.

Every page has WebPage + BreadcrumbList JSON-LD present and canonical
exact-match `https://www.creditdoc.co/trends/<slug>/`.

## Deploy status

**Not deployed.** Local `dist/trends/<slug>/index.html` contains
renderer output; live production still serves Astro's Jul 16 build.
Rollback: `dist.trashed_r1_1784269927/trends/`.

## Speed

713 pages in 13.0s (~0.02s/page — second fastest family after /brand/).

## Rolling total after Phase 3.6

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
| /trends/ | 713 | Phase 3.6 |
| **Total** | **18,175** | **10 families** |

## Deploy blocker fix included in this commit range

Phase 3.6 audit (agentId `aea1d3d59fd013063`) additionally caught a
stale status filter in `renderer/watch_and_rebuild.py:64` that was
using `('ready_for_index','approved')` — the same bug Phase 3.2
audit found in `db.py`. Fixed in a follow-up commit so the auto-
rebuild cron won't silently drop `pending_approval`-promoted lenders.

## What's next

Phase 3.7 → `/compare/` (~392 head-to-head lender comparisons).
Debugger flagged that `slugContext` from /trends/ is reused in
`compare/[slug].astro:391` — factor it into a shared util.
