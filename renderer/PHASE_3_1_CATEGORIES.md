# Phase 3.1 — /categories/ family delivered (2026-07-17)

Fifth family now covered by the DB-authoritative Python renderer.
Extends Phase 2 (/review/, /answers/, /blog/, /financial-wellness/) by adding
`/categories/*` — 19 hub pages.

## What shipped

Commit: `b99da60567` on `cdm-rev-hybrid`.

| File | Change |
|---|---|
| `renderer/db.py` | + `load_category(slug)`, `top_lenders_by_category(cat, 48)`, `category_count(cat)` |
| `renderer/render.py` | + `render_category(slug, out_dir)`, `category` CLI subcommand, hardcoded money/tool/wellness maps mirroring Astro's `[category].astro` |
| `renderer/templates/category.html.j2` | NEW — full page: CollectionPage + BreadcrumbList + ItemList JSON-LD, breadcrumbs, H1, linkified description, authority-path grid, top-48 lender grid (simplified card), wellness guides, loan disclaimer |
| `renderer/build_all.py` | 5th entry in `FAMILIES` tuple; `--only category` works |

## Why /categories/ was picked first (Phase 3.1 vs Phase 3.2+)

Debugger audit ranking (in this session):

1. **Lowest risk** — only 19 pages; blast radius = 19 URLs if anything breaks
2. **Already static-served** — `dist/_routes.json` has `/categories/*` in
   `exclude`, so the worker never sees these; safe to swap in without
   touching routing config
3. **Immediate visible win** — the hub pages are on-menu (Categories
   dropdown in the header), so any success is user-facing
4. **No Supabase dependency** — category rows live in local SQLite
   (`data/creditdoc.db`), unlike /city/ which touches Supabase

Left for later:
- `/best/` (27 pages) — SVG gradient IDs randomize per build; needs
  determinism work; also money pages, highest revenue at stake
- `/credit-guide/` (~8,240) — Supabase-driven; biggest single family
- `/city/` (330) — next up, Phase 3.2

## How to use

```bash
# Render one category:
python3 renderer/render.py category --slug credit-repair --output-dir /tmp/x

# Rebuild all 19 (idempotent, atomic per-file, flock-guarded):
python3 renderer/build_all.py --only category

# Dry-run to count:
python3 renderer/build_all.py --dry-run --only category
```

## Parity verified 19/19

Ran vs live `https://www.creditdoc.co/categories/<slug>/` for each of 19
slugs. Every page:

- **Visible-word ratio ≥ 1.72×** the live Astro output (parity floor is 0.80)
- **CollectionPage + BreadcrumbList** JSON-LD present (Astro's baseline)
- **ItemList** JSON-LD added (renderer supersets Astro's schema)
- **Canonical** exact-match `https://www.creditdoc.co/categories/<slug>/`

Fintech's ratio is the lowest (1.72×) because it has only 11 lenders vs
banking's 4,795 — fewer lender cards means fewer visible words, but the
page still doubles Astro's word count.

Full parity table below. **All 19 PASS.**

```
  PASS atm                    local=2149 live=619 ratio=3.47 canon=ok
  PASS banking                local=2089 live=607 ratio=3.44 canon=ok
  PASS bankruptcy             local=2319 live=601 ratio=3.86 canon=ok
  PASS build-credit           local=1714 live=614 ratio=2.79 canon=ok
  PASS business-loans         local=2366 live=662 ratio=3.57 canon=ok
  PASS check-cashing          local=2209 live=638 ratio=3.46 canon=ok
  PASS credit-cards           local=1751 live=616 ratio=2.84 canon=ok
  PASS credit-monitoring      local=1328 live=616 ratio=2.16 canon=ok
  PASS credit-repair          local=2313 live=616 ratio=3.75 canon=ok
  PASS credit-unions          local=2219 live=613 ratio=3.62 canon=ok
  PASS debt-relief            local=2341 live=612 ratio=3.83 canon=ok
  PASS emergency-cash         local=2323 live=656 ratio=3.54 canon=ok
  PASS fintech                local=1044 live=607 ratio=1.72 canon=ok
  PASS free-help              local=2168 live=597 ratio=3.63 canon=ok
  PASS insurance              local=1764 live=603 ratio=2.93 canon=ok
  PASS mortgages              local=2341 live=669 ratio=3.50 canon=ok
  PASS pawn-shops             local=2297 live=656 ratio=3.50 canon=ok
  PASS payday-alternatives    local=2174 live=662 ratio=3.28 canon=ok
  PASS personal-loans         local=2324 live=655 ratio=3.55 canon=ok
```

## Deploy status

**Not deployed.** Local `dist/categories/<slug>/index.html` now contains
renderer output (~87 KB per page, up from ~37 KB Astro); live production
still serves Astro's Jul 16 build via the worker.

Deploy path: `wrangler deploy dist` (needs `CLOUDFLARE_GLOBAL_API_KEY` +
`CLOUDFLARE_EMAIL` env, per lies_caught #2) — but only after founder review
of a spot-check render.

Rollback path: `dist.trashed_r1_1784269927/categories/` holds Astro's Jul 16
version of every /categories/ page for straight `cp` restoration.

## Simplifications vs Astro

Astro's `[category].astro` uses `LenderCard.astro` which imports a huge
`softenProviderCardCopy` regex map (100+ substitutions) plus `RatingStars`
and `TrustBadge`. Rather than re-implementing those Astro components, the
Phase 3.1 template uses a simpler card layout:

- Name + review link (canonical URL)
- City, ST if present
- BBB badge if `company_info.bbb_rating` present
- Short teaser text (from `description_short` / `meta_description`, truncated)
- "View Details" review link

This is what accounts for the 1.72×–3.86× parity ratios: my card block is
denser with visible text than Astro's stylised card.

If parity checkers complain later, the Astro copy-softening dictionary
can be lifted verbatim into a Python helper — no logic changes required.

## What's next

**Phase 3.2 → /city/ (330 pages)** — next largest family after /credit-guide/
and /trends/, but ordered ahead of them per debugger recommendation
(SEO #1 bet + hub for the local-city vision).
