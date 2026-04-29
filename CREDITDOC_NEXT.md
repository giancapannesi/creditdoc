# CreditDoc — NEXT (RULE 10 handoff, written 2026-04-29 09:40 UTC)

## Decision waiting on Jammi (BLOCKS Phase 1.3.B → 1.7)

**The question:** how does the SSR `/review/[slug]` route get its data on Cloudflare Workers?

`src/pages/review/[slug].astro` (1087 LOC) currently uses `getStaticPaths()` and imports
from `src/utils/data.ts`, which uses `fs.readdirSync('src/content/lenders/')` to load
20,814 JSON files at build. None of that runs on Workers — `fs` is a Node API and `src/`
is not in the worker bundle.

So Phase 1.3.B (convert `/review/[slug]` to SSR) cannot ship until we pick a data path.

### Three options (only Option C is fully inside the loop authority)

#### Option A — DB columns + bodies inline (correct long-term, off-limits this loop)

**Updated 2026-04-29 10:15 UTC — sized the data, A.1 (all inline) is viable.**

Body-content size distribution measured against `src/content/lenders/*.json`:
- 20,813 files, 133.2 MB raw
- avg 6.6 KB / p50 6.9 KB / p95 8.7 KB / p99 11.8 KB / max 17.3 KB
- After Postgres TOAST + zstd → estimated ~40–60 MB stored, well within Supabase free-tier 500 MB cap
- No file >50 KB → R2 split is unnecessary for body content

**Recommended A.1 — all inline, no R2 split:**
```sql
-- ALTER (one-shot, ~5s for 20K rows on Supabase free):
ALTER TABLE public.lenders
  ADD COLUMN body_inline jsonb;

-- Backfill (run from a server with the JSON files; CSV-streamed to keep tx small):
-- pseudocode:
--   for each src/content/lenders/<slug>.json:
--     write CSV row: <slug>,<json_compact>
--   then: \copy lenders_body_staging(slug,body_inline) FROM '...' CSV
--   then: UPDATE lenders l SET body_inline = s.body_inline
--         FROM lenders_body_staging s WHERE l.slug = s.slug;

-- Optional R2 fallback column (kept null for now; future-proof):
ALTER TABLE public.lenders
  ADD COLUMN body_r2_key text;
```

After ALTER:
1. Update `src/lib/db.ts` `CATALOG_COLUMNS` to also SELECT `body_inline,body_r2_key`
2. Update `RuntimeLender` interface to add the two fields back
3. Convert `/review/[slug]` to use `getLenderBySlugRuntime` instead of build-time `fs.readdirSync`
4. Keep `/r/[slug]` pilot for one cycle as a smoke check, then delete (Phase 4.4)

**Tradeoffs:**
- ✅ True OBJ-1: row update → cache evict → next request rebuilds in <50ms
- ✅ Single round-trip per page (no R2 GET hop)
- ✅ Simplest db.ts code path
- ✅ Backfill is a one-shot ~5 minute job (`tools/creditdoc_db_backfill_body_inline.py` to be written when approved)
- ❌ Requires Supabase ALTER TABLE + 20K-row UPDATE (LIVE WRITE — off-limits this loop)
- ❌ Adds ~50 MB to Postgres footprint (acceptable: free tier is 500 MB, lenders rows + body still <100 MB after compression)
- ⚠ Future-proofing: add `body_r2_key` even though A.1 leaves it null, so the schema doesn't need a second migration when (if) we move to R2.

**To unblock:** Jammi runs the SQL above (or greenlights us to run it), THEN greenlights the backfill script run, THEN we ship the `/review/[slug]` SSR cutover.

**Rollback plan:** `ALTER TABLE public.lenders DROP COLUMN body_inline, DROP COLUMN body_r2_key;` — non-destructive to existing data; static `/review/[slug]` keeps working from JSON files. ~5 min revert.

#### Option B — Bundle JSONs into the worker (cheap but defeats OBJ-1)
At build, copy a pruned set of lender JSONs into `dist/_lenders/<slug>.json`. Worker fetches
its own static asset for the body, fetches the catalog row from Supabase only for cache-key
versioning.

- ✅ Zero schema change
- ✅ No live DB write
- ❌ Defeats OBJ-1 — body still needs a build to update. Same problem as today.
- ❌ Worker bundle bloats by ~100MB if we don't aggressively prune

**Verdict:** doesn't solve the problem we set out to solve. Skip.

#### Option C — `/r/[slug]` pilot route (recommended for this loop) ⭐
Create a NEW SSR route `/r/[slug]` that uses ONLY `db.ts`. It reads `lenders` row
via PostgREST, renders a minimal HTML body (brand name, category, rating, description,
website, phone — what we already have on the `lenders` row today, no `body_*` needed yet).

Existing `/review/[slug]` stays static + prerendered. `/r/[slug]` is the SSR pilot that
proves the architecture and unblocks Phase 1.4 (cache wiring) + 1.5 (wrangler dev) + 1.6
(preview deploy) + 1.7 (TTFB measurements + acceptance gate).

When Jammi greenlights Option A, we cut over `/review/[slug]` to the same pattern and
delete `/r/[slug]`.

- ✅ Inside loop authority — no live DB write, no production traffic touched
- ✅ Lets us ship Phase 1.4–1.7 + measure OBJ-1
- ✅ ~80–100 LOC for the route + already-built helpers
- ❌ Body content limited to columns that exist on `lenders` today (no rich body until Option A lands)

**Recommend:** ship Option C this loop. Phase 1.3.B becomes "pilot SSR on `/r/[slug]`".
Final cutover stays gated on Jammi's Option A approval.

## What is safe to ship in this loop after Option C is greenlit

1. **Phase 1.3.B (rev'd)** — `/r/[slug]` SSR pilot using `db.ts` (~80 LOC).
2. **Phase 1.4** — wire `cache.ts` around the `/r/[slug]` handler. Cache key = pathname + `contentVersionOf(lender)`.
3. **Phase 1.5** — `wrangler pages dev` local SSR preview. Verify `/r/<known-slug>` renders.
4. **Phase 1.6** — `wrangler pages deploy dist --project=creditdoc` (PREVIEW environment only — does NOT touch live `creditdoc.co`).
5. **Phase 1.7** — TTFB measurements on the preview URL: cold/warm p50/p95. Acceptance bar: warm <100ms p95, cold <600ms p95. Re-run verifier — OBJ-1 should flip GREEN.
6. **Phase 4.3 doc** — `creditdoc/docs/architecture/extending_the_app.md` "How to add a new SSR route in 6 steps". Doc-only, safe.
7. **Phase 3.7 doc** — encryption-at-rest verification (doc-only — Supabase-managed, just record what's already true).

## What is OFF-LIMITS this loop (do not start)

- Phase 2.3 — wiring `/api/revalidate` to `tools/creditdoc_db.py` (production tool — needs Jammi greenlight)
- Phase 2.4 — live row probe to verify update→evict→serve (live DB write)
- Phase 3.1 — creating `audit_log` triggers (live Supabase DDL)
- Phase 3.2 — RLS audit policy changes (live Supabase DDL)
- DNS changes (Phase 6 cutover only)
- Vercel production changes (Phase 6 only)
- CF Pages **production** deploy (preview is OK)

## When to ping Jammi

- Before Phase 1.6 (preview deploy) — confirm token / CF account access is set
- Before any of the off-limits items above is unblocked
- If full `astro build` keeps timing out at >10min on `cdm-rev-hybrid` and we need to short-circuit prerender for the build to finish

## Files to read before continuing

- `creditdoc/CREDITDOC_NOW.md` — live state (commits, branch, verifier baseline)
- `creditdoc/docs/plans/2026-04-29_REVISED_MIGRATION_PLAN_HYBRID_FIRST.md` — full plan rev 4
- `CreditDoc Project Improvement/2026-04-29_CREDITDOC_SITE_ARCHITECTURE.md` — A.1–A.14 build plan
- Memory: `creditdoc_north_star.md` — three OBJs, rule of forfeit
- Memory: `project_creditdoc_cloudflare_migration.md` — original CDM plan
- Memory: `project_creditdoc_arch_overhaul_parallel.md` — `arch-overhaul` is OWNED BY ANOTHER WINDOW
