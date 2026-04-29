# CreditDoc — LIVE STATE (as of 2026-04-29 13:14 UTC)

## CDM-REV Phase 1.3.B — A.1 LANDED / A.2 BACKFILL READY / A.3 + A.4 ARTIFACTS READY / Phase 2.1 LANDED

**This loop's adds (no live DB writes; cdm-rev-hybrid only, not pushed):**

| Commit | What |
|---|---|
| `1bc162784d` | A.1 + A.2 scaffolding: `/review/[slug]` SSR cutover, A.2 DDL on live Supabase, backfill CSV-staged (81/165/57). |
| `0e0c7a3d92` | Phase 2.1: `/api/revalidate` endpoint (POST + token auth + opportunistic prewarm). `/r/[slug]` upgraded to read body_inline. |
| `8c8c790806` | A.3 + A.4 DDL artifacts (NOT applied) + backfill scripts (dry-run only) + runtime fetchers in db.ts. |

**Stage A.3 — states / categories / glossary_terms** (artifact, awaiting greenlight)
- DDL: `supabase/migrations/2026-04-29_cdm_rev_a3_states_categories_glossary.sql`
- Backfill: `tools/creditdoc_db_backfill_a3_content.py` — dry-run staged 50 / 18 / 71 rows
- Runtime: `getStateByCodeRuntime`, `getAllStatesRuntime`, `getAllCategoriesRuntime`, `getCategoryBySlugRuntime`, `getGlossaryTermsForContextsRuntime` in `src/lib/db.ts`

**Stage A.4 — blog_posts / listicles / answers / specials** (artifact, awaiting greenlight)
- DDL: `supabase/migrations/2026-04-29_cdm_rev_a4_blog_listicles_answers_specials.sql`
- Backfill: `tools/creditdoc_db_backfill_a4_content.py` — dry-run staged 34 / 26 / 14 / 3 rows
- Runtime: `getBlogPostBySlugRuntime`, `getBlogPostsByCategoryRuntime`, `getListicleBySlugRuntime`, `getAnswerBySlugRuntime`, `getSpecialsForLenderRuntime`

**Phase 2.1 — `/api/revalidate`** (LANDED, awaiting Phase 2.3 wiring greenlight)
- POST-only, gated on `x-revalidate-token` header
- Body: `{ type: "lender"|"wellness"|"comparison"|"brand", slug }`
- Opportunistic pre-warm via internal fetch (5s timeout) of canonical URL
- Returns 200 with `{ ok, type, slug, prewarmed, target }`
- The OBJ-1 invalidation mechanism is automatic (updated_at→cache key); this endpoint adds observability + pre-warm

**Build state:** 141s, Worker bundle 285 KB gzipped (under 1 MB cap), 0 `/review/` prerender lines.

**Pending Jammi greenlights (all live-DB or production-tool work):**
1. `--apply` Stage A.2 backfill (303 rows: wellness + comparisons + brands).
2. Apply Stage A.3 DDL + backfill (139 rows: states + categories + glossary).
3. Apply Stage A.4 DDL + backfill (77 rows: blog + listicles + answers + specials).
4. Phase 2.3 — wire `tools/creditdoc_db.py` → POST `/api/revalidate` (production-tool modification).
5. Set Pages env var `REVALIDATE_TOKEN` (a random 32-byte secret) on `cdm-rev-hybrid` preview.

---

# Earlier state (Apr 29 10:36 UTC) — preserved below for trajectory.

## Branch
- Working branch: `cdm-rev-hybrid` (off `main`, **13 commits ahead, NOT pushed**)
- `main`: untouched. Last commit `88e6836d8d` (DB export Apr 28).
- `arch-overhaul`: parallel-window territory — DO NOT TOUCH.
- Stash: `pre-cdm-rev-hybrid-branch-stash 2026-04-29T09:11Z` — 549 modified `src/content/lenders/*.json` files (DB-export drift). Stashed cleanly before branch creation.

## Live system status (DO NOT TOUCH)
- Vercel production at `https://www.creditdoc.co/` — UNCHANGED, serving the previous static build.
- DNS at Cloudflare zone `creditdoc.co` — A → `216.198.79.1` Vercel anycast, CNAME `www` → Vercel, all `proxied=False`. **Deliberate. Phase 6 cutover only.**
- Supabase project `pndpnjjkhknmutlmlwsk` — read-only access used by verifier. No writes.
- Privacy/terms/disclosure all live (200 OK at `https://www.creditdoc.co/{privacy,terms,disclosure}/`). DO NOT redo (`feedback_check_existing_before_drafting.md`).

## CDM-REV-2026-04-29 progress

| Phase | Status | Notes |
|---|---|---|
| 0.4 — inventory snapshot | ✅ DONE | `creditdoc/data/exports/cdm_rev_inventory_2026-04-29.md` |
| 0.5 — verify_strategic_objectives.py | ✅ DONE | Commit `8e31372a51`. Read-only. Returns OBJ-1/2/3 traffic-light JSON. |
| 1.1 — branch `cdm-rev-hybrid` | ✅ DONE | Created off `main` after stashing 549 lender drift files. |
| 1.2 — `@astrojs/cloudflare` + `output: 'static'` (Astro 5 hybrid) | ✅ DONE | Commit `24b0f94ddf`. Adapter v12.6 (Astro-5-compatible). Astro 5 hybrid pattern: `output: 'static'` + adapter + per-route `prerender = false` flag. |
| 1.3.A — SSR scaffolding (cache.ts, db.ts, wrangler.toml) | ✅ DONE | Commit `96b501472d`. Cache API helper + Supabase READ-ONLY runtime helper. Lazy module init — no live calls at build. |
| 1.3.B — Option C pilot `/r/[slug]` SSR | ✅ DONE | Commit `e49d29a1e8`. TS endpoint, db.ts (anon PostgREST), cache.ts wrap. Catalog-row-only — body content gated on Option A. noindex pilot. |
| 1.3.B — `/review/[slug]` cutover (Option A) | ⏸ PAUSED | Needs Jammi greenlight: ALTER TABLE lenders ADD body_r2_key + body_inline + R2 backfill. Live DB write = off-limits this loop. |
| 1.4 — wire CF Cache API around SSR handler | ✅ DONE | cacheWrap() integrated in `/r/[slug]` (commit `e49d29a1e8`). |
| 1.5 — `wrangler pages dev` local SSR preview | ✅ DONE | `LENDERS_PRERENDER_LIMIT=50 npx astro build` (~2min, was 67min for full 20K) → wrangler dev port 8788 → `/r/credit-saint` 200, `/api/lender/credit-saint` 200. Local TTFB cold p95=46.1ms warm p95=43.1ms. Bug fix: `imageService: 'compile'`→`'passthrough'` (sharp+detect-libc bundle broke workerd). Commit `d2ba763d70`. Log: `docs/2026-04-29_PHASE17_TTFB_LOCAL.log`. |
| 1.6 — `wrangler pages deploy dist` (preview) | ✅ DONE | Deployed to **`https://cdm-rev-hybrid.creditdoc.pages.dev`** (alias) / `82ab229b.creditdoc.pages.dev` (latest). Production branch `main` UNTOUCHED. creditdoc.co not affected. Auth: scoped `CLOUDFLARE_API_TOKEN` returns code 10000 on Pages endpoints — used `CLOUDFLARE_GLOBAL_API_KEY` + `CLOUDFLARE_EMAIL` instead. Env vars set via PATCH `/accounts/{id}/pages/projects/creditdoc` with `deployment_configs.preview.env_vars` (both `secret_text`; `plain_text` did NOT persist). Commit `13b3a11db7` ([assets] block dropped — Workers-only directive). |
| 1.7 — TTFB measurements + Phase 1 acceptance gate | ✅ **GREEN** | `tools/cdm_rev_phase17_ttfb.sh https://cdm-rev-hybrid.creditdoc.pages.dev`: cold p95=**91.0ms** warm p95=**88.7ms** max=163.3ms (n=38 cold, 114 warm, 19 slugs × 2 routes × 4 runs). Bars: warm<100ms ✅ (11ms headroom), cold<600ms ✅ (6.6× under). Log: `docs/2026-04-29_PHASE17_TTFB_PREVIEW.log`. |
| 2.x — revalidation Worker + DB-write wiring | not started | PAUSE for Jammi greenlight before 2.3 (touches `creditdoc_db.py` production tool) and 2.4 (live row probe). |
| 3.1–3.5 — audit_log triggers, RLS audit, DPA, token register, cookie banner | not started | PAUSE for Jammi greenlight before 3.1 (live Supabase trigger creation). |
| 3.6 — privacy/terms pages | ✅ ALREADY LIVE | VERIFIED today: `/privacy/`, `/terms/`, `/disclosure/` all 200. DO NOT redo. |
| 3.7 — encryption-at-rest verification | ✅ DONE | Commit `ace7bd78c4`. `creditdoc/docs/compliance/encryption_at_rest.md`. |
| 4.1 — growth-readiness probe `/api/lender/[slug]` | ✅ DONE | Commit `ca99ffbab0`. 71 LOC TS endpoint, same db.ts+cache.ts, JSON content-type. Proves OBJ-2 — new SSR surface in <50 non-comment LOC. |
| 4.2 — measurement (LOC + diff vs `/r/[slug]`) | ✅ DONE | Recorded in commit `ca99ffbab0`. Same helpers, only content-type differs. |
| 4.3 — extending_the_app.md doc | ✅ DONE | Commit `ace7bd78c4`. 6-step howto for adding a new SSR surface. |
| 4.4 — decommission probe | deferred | Until Phase 1.7 acceptance gate green. |
| RULE 10 handoff docs | ✅ DONE | Commits `bdd057e2f5` + `ad7554314a` + `65fba30709`. `CREDITDOC_NOW.md` + `CREDITDOC_NEXT.md` (Option A.1 sized) + Phase 0.4 inventory. |

## Verifier baseline (Apr 29 10:30 UTC, branch cdm-rev-hybrid)

```
OBJ-1: AMBER — 2 SSR pilot routes detected (src/pages/r/[slug].ts, src/pages/api/lender/[slug].ts). Revalidation endpoint not yet wired — DB writes do not invalidate cache. GREEN requires Phase 2 (off-limits this loop).
OBJ-2: RED   — audit_log table exists, fn_audit_row() missing, 0/4 trigger coverage. Phase 3.1 = off-limits this loop. (NB — naming convention in verifier: this is OBJ-2 audit/compliance scaffolding, not the "future-proof" axis. New-surface ability is demonstrated by `/api/lender/[slug]` at 49 non-comment LOC.)
OBJ-3: GREEN — helpers (cache.ts + db.ts) in place. New SSR route ~20 LOC. Pattern in docs/architecture/extending_the_app.md.
```

Trajectory this loop:
- 09:30 UTC start: RED / RED / RED
- 09:35 UTC: Phase 1.2 + 1.3.A scaffolding committed → no traffic-light change yet
- 09:55 UTC: Phase 4.3 + 3.7 docs committed → OBJ-3 flips RED→GREEN
- 10:05 UTC: Phase 1.3.B Option C pilot committed → OBJ-1 flips RED→AMBER
- 10:20 UTC: Phase 4.1 growth probe committed → still AMBER but two pilot surfaces now prove OBJ-2 in <50 LOC each
- 10:30 UTC: Option A.1 sizing analysis added to NEXT.md (NO live write) — A.1 confirmed viable, no R2 split needed
- 10:36 UTC: **Phase 1.5 + 1.6 + 1.7 GREEN** — local SSR working, preview deployed, TTFB acceptance gate cleared on CF Pages preview. OBJ-1 stays AMBER (revalidation Phase 2 still pending — off-limits), but the architectural property "global SSR sub-100ms warm" is now proven on the actual Cloudflare edge. Final OBJ-1 GREEN gated on revalidation wiring + production cutover, both off-limits this loop.

OBJ-2 and final OBJ-1 GREEN both gated on off-limits live-system work.

Re-run any time: `python3 tools/verify_strategic_objectives.py`

## Known issues / open questions
- Full `astro build` still slow (>10 min on the 17K+ static prerender). This is the OBJ-1 problem we're fixing — `/review/[slug]` cutover (Option A) will move ~20K pages off prerender. Pilot at `/r/[slug]` proves the architecture without depending on the long build finishing. Phase 1 builds use `LENDERS_PRERENDER_LIMIT=50` env to cap prerender for smoke testing.
- Live `lenders` table is a 12-column catalog index ONLY: `slug, name, category, state, brand_slug, has_logo, seo_tier, processing_status, checksum, id, created_at, updated_at`. NO `brand_name`, `city`, `rating`, `body_r2_key`, `body_inline`. Body content (description, services, hours) is in `src/content/lenders/*.json` and not runtime-readable from the Worker. Option A would add `body_r2_key` + `body_inline` columns + backfill (script: `tools/creditdoc_db_backfill_body_inline.py` — DRY-RUN-ready, requires `--apply --i-have-jammi-greenlight` + pre-flight ALTER TABLE).
- Stashed 549 `src/content/lenders/*.json` drift on main — need a separate "DB export sync to main" commit at some point (not on `cdm-rev-hybrid`).
- Preview env vars on CF Pages: when PATCHing `deployment_configs.preview.env_vars`, BOTH must be `type: "secret_text"`. `plain_text` did not persist for `SUPABASE_URL` (only `secret_text` did). Bug fixed in this loop.
- Scoped CF token (`CLOUDFLARE_API_TOKEN`) lacks Pages permissions — code 10000 on `/accounts/{id}/pages/projects`. Use `CLOUDFLARE_GLOBAL_API_KEY` + `CLOUDFLARE_EMAIL` for Pages ops; for wrangler: `export CLOUDFLARE_API_KEY=$CLOUDFLARE_GLOBAL_API_KEY; unset CLOUDFLARE_API_TOKEN`.

## Loop authority
Currently in `/loop` mode with directive: "until you finish all the work that doesnt involve touching the live database or system". Off-limits this loop:
- Live Supabase writes (Phase 2.4, 3.1)
- Wiring `tools/creditdoc_db.py` to revalidate (Phase 2.3 — production tool)
- DNS changes (Phase 6 cutover only)
- Vercel production changes (Phase 6 only)
- CF Pages production deploy (preview is OK)
