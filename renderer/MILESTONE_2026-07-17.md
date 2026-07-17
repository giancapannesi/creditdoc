# Milestone: rebuild-necessity eliminated (2026-07-17)

**Status:** the mechanism to update one page without rebuilding the whole site is functional, proven end-to-end, and live on production.

## The proof

```bash
# 1. Rendered from DB via Python + Jinja2 in ~100ms:
$ python3 renderer/render.py review --slug lexington-law
rendered: renderer_dist/review/lexington-law/index.html (76,003 bytes)

# 2. Copied to dist/ and deployed via wrangler:
$ npx wrangler deploy
Current Version ID: a536b3d6-43fc-448d-a2f5-b9c104d4e71e

# 3. Live on production, verified by Bingbot User-Agent:
$ curl -A "Bingbot" https://www.creditdoc.co/renderer-preview/lexington-law/index.html
HTTP/2 200
<title>Lexington Law Review — Credit-Repair | CreditDoc</title>
```

**Astro never ran during that update.** No 45-minute rebuild. No 27,000-page regeneration.

## The scoreboard

| Metric | Astro (before) | Renderer (now) |
|---|---|---|
| Per-page update time | 45–60 min (full rebuild) | 106 ms |
| Data source | JSON cache exported from DB | DB read directly |
| Content pipeline runtime | Astro adapter (SSR risk) | none (static file) |
| Framework fingerprint | `/_astro/*` bundles | none |
| Cutover risk to Bing | LOW (parallel-run pattern) | LOW |

## Coverage against Astro (byte parity)

- Family-wide `/review/` (16 lender sample): **64.8%**
- Lexington-law single page: **44%** (75.9 KB vs 171 KB)
- Structural parity: **100%** — every H2, every JSON-LD schema type, every critical meta/OG tag matches

The remaining 36% byte gap is **content depth** (Astro's longer descriptions,
more detailed section prose), not missing features or missing schema.

## What's committed today

Renderer core:
- `renderer/render.py` — CLI (renders one review to HTML)
- `renderer/db.py` — DB helpers (lender, similar, related answers, wellness, state, glossary)
- `renderer/linker.py` — inline money-link auto-linker (172 phrases)
- `renderer/_faqs.py` — lender-specific + category-fallback FAQs
- `renderer/_money_links.py` — auto-extracted link map
- `renderer/templates/review.html.j2` — Jinja2 review template
- `renderer/templates/_header.html` + `_footer.html` — extracted chrome

Pipeline:
- `renderer/rebuild_one.py` — single-page rebuild + optional wrangler deploy
- `renderer/watch_and_rebuild.py` — DB watermark → cron sweep → per-page rebuild
- `renderer/tests/parity_check.py` — quantitative gap vs Astro output

## What still needs to happen for full Astro replacement

1. **Continue closing parity on /review/** — from 64.8% toward 95%+ (~2-3 days).
2. **Cover other page families** — /credit-guide/, /answers/, /best/, /blog/,
   /state/, /city/, /brand/, /financial-wellness/, /categories/, tools, research (~4-6 days).
3. **Flip `--deploy` on** — replace Astro's output for the /review/ family
   with renderer output. Parity gate: >95% + zero broken links.
4. **Wire the cron** — `* * * * * ... watch_and_rebuild.py --deploy` runs
   every 60 seconds. Each DB row update goes live within a minute.
5. **Delete Astro** — remove `@astrojs/*` packages, `src/pages/`,
   `astro.config.mjs`, middleware, adapter, ~40 SSR-era guard scripts.

## Rollback path (at every stage)

- Renderer writes to `renderer_dist/` or `shadow_dist/` by default.
- Only `--deploy` mode touches `dist/`.
- The next Astro build overwrites `dist/`, restoring the Astro version.
- No irreversible action before the final Phase 6 delete.
