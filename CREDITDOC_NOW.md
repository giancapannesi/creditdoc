# CreditDoc — NOW (Architecture Overhaul)

**Status:** Architecture migration code-complete on branch `arch-overhaul`. Local build green. Bundle under Vercel limit. NOT pushed.

## What's done
- **Astro hybrid → static + per-route SSR.** Astro 5.17 dropped `output: 'hybrid'`; the project now uses `output: 'static'` and the 12 dynamic routes (`/review/[slug]`, `/answers/[slug]`, `/best/[slug]`, `/blog/[slug]`, `/brand/[slug]`, `/categories/[slug]`, `/city/[slug]`, `/compare/[slug]`, `/financial-wellness/[slug]`, `/state/[slug]`, `/browse/[cat]/[loc]`, etc.) export `prerender = false`. Vercel ISR handles them with 24h expiration.
- **Build time: 372s+ → 45s locally**, 13.75s server bundle on the green run. Vercel 45-min ceiling no longer relevant.
- **Adaptive DB client at `src/utils/db.ts`.** Three-tier resolution:
  1. `CREDITDOC_LOCAL_DB` env (build time)
  2. `data/creditdoc-slim.db` bundled into the function (runtime)
  3. Turso/libsql fallback if neither exists
  - `createRequire(import.meta.url)` solves ESM-cannot-`require()` for the CJS native module.
- **Slim DB at `data/creditdoc-slim.db` (149M)** — copy of `creditdoc.db` minus `audit_log` (53M); contains lenders + categories + comparisons + listicles + wellness_guides + blog_posts + cluster_answers; includes `idx_lenders_slug` and `idx_lenders_status`.
- **`src/utils/data.ts`** refactored: `getLendersByCategory/State/City` now use SQL `json_each` filters instead of pulling all 20K rows then filtering in Node. `getCategories` uses GROUP BY count queries instead of `getAllLenders().filter()`.
- **Bundle size: 353M → 192M** (Vercel limit 250M).
  - `src/content/lenders/` (164M of 26K JSON files) moved to `.archived-content/lenders/` — unreferenced after the DB migration.
  - `astro.config.mjs` adapter `includeFiles` explicitly bundles `data/creditdoc-slim.db` + the better-sqlite3 native binary + its lib files + `bindings` + `file-uri-to-path` (nft can't follow `createRequire`).
- **Smoke-tested locally** against the actual function bundle by booting `dist/server/entry.mjs` and hitting each dynamic route. Caught + fixed:
  - `/state/[slug]`, `/city/[slug]`, `/browse/[cat]/[city]` were still using `Astro.props` (left over from getStaticPaths). Rewrote to read `Astro.params` and resolve via data helpers.
  - `/review/[slug]`, `/blog/[slug]`, `/best/[slug]`, `/compare/[slug]`, `/financial-wellness/[slug]`, `/answers/[slug]` were non-null-asserting (`getXBySlug(s)!`) and 500'd on missing slugs. Added `if (!obj) return new Response('Not found', { status: 404 });` guards.
  - All 12 dynamic patterns now PASS (200 with valid slug, proper 404 with garbage slug).
  - Cold-start latencies (in-bundle node test): `/review` 1340ms, `/compare` 675ms, all others 9–75ms. Warm requests sub-50ms. ISR masks cold-start from end users.
- **Phase 5 wired:** `scripts/build_slim_db.sh` regenerates `data/creditdoc-slim.db` from `/srv/BusinessOps/creditdoc/data/creditdoc.db`. Atomic swap, sanity check on row count. Exposed as `npm run rebuild-slim-db` and `npm run build:full` (rebuild + astro build).

## What's open
- **Not pushed.** Per founder directive, no push until explicit approval.
- **Vercel env vars:** `TURSO_DATABASE_URL` + `TURSO_AUTH_TOKEN` should remain set as runtime fallback only (the bundled DB will win every time `data/creditdoc-slim.db` exists in the function).
- **Phase 5 cron not wired yet.** `scripts/build_slim_db.sh` exists and works, but no cron pulls the latest creditdoc.db into a slim rebuild + commit + push automatically. Until that's added, slim DB drifts from creditdoc.db until someone runs `npm run rebuild-slim-db` and pushes.
- **Brands directory** still reads from `src/content/brands/*.json` (232K, 57 files) — kept as-is, fine for now.
- **Content collections** under `src/content/` (answers/, brands/, blog-posts.json, etc.) bundled into the function. ~3.6M total — fine.

## Key files (this branch only)
| File | Change |
|------|--------|
| `astro.config.mjs` | static + ISR adapter, includeFiles for DB + better-sqlite3 |
| `package.json` | `better-sqlite3` moved deps→runtime |
| `src/utils/db.ts` | NEW: adaptive client (better-sqlite3 / Turso) |
| `src/utils/data.ts` | refactored: SQL json_each filters, removed getAllLenders fan-out |
| `data/creditdoc-slim.db` | NEW: 149M slim copy |
| `.archived-content/lenders/` | NEW: 164M of unused JSONs (out of bundle) |
| `scripts/sync_to_turso.mjs` | drafted Phase 5 helper, may not be needed |

## How to verify before pushing
```bash
cd /srv/BusinessOps/creditdoc-arch
npm run build   # ~45s, must end "Complete!"
du -sh .vercel/output/functions/_isr.func/   # must be < 250M
ls .vercel/output/functions/_isr.func/node_modules/better-sqlite3/build/Release/better_sqlite3.node
```
