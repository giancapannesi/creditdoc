# CreditDoc — LIVE STATE (as of 2026-04-29 10:30 UTC)

## Branch
- Working branch: `cdm-rev-hybrid` (off `main`, **9 commits ahead, NOT pushed**)
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
| 1.5 — `wrangler pages dev` local SSR preview | not run | Needs full `astro build` first (>10min today — that IS the OBJ-1 problem we're fixing). Defer until 1.3.B-Option-A or Jammi ok's a long build. |
| 1.6 — `wrangler pages deploy dist` (preview) | not run | Preview environment — does not touch live `creditdoc.co`. Same precondition as 1.5. |
| 1.7 — TTFB measurements + Phase 1 acceptance gate | not run | Acceptance bar: TTFB warm <100ms p95, OBJ-1=GREEN. Needs preview deploy first. |
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

OBJ-2 and final OBJ-1 GREEN both gated on off-limits live-system work.

Re-run any time: `python3 tools/verify_strategic_objectives.py`

## Known issues / open questions
- Full `astro build` still slow (>10 min on the 17K+ static prerender). This is the OBJ-1 problem we're fixing — `/review/[slug]` cutover (Option A) will move ~20K pages off prerender. Pilot at `/r/[slug]` proves the architecture without depending on the long build finishing.
- Live `lenders` table is a 12-column catalog index ONLY: `slug, name, category, state, brand_slug, has_logo, seo_tier, processing_status, checksum, id, created_at, updated_at`. NO `brand_name`, `city`, `rating`, `body_r2_key`, `body_inline`. Body content (description, services, hours) is in `src/content/lenders/*.json` and not runtime-readable from the Worker. Option A would add `body_r2_key` + `body_inline` columns + backfill.
- Stashed 549 `src/content/lenders/*.json` drift on main — need a separate "DB export sync to main" commit at some point (not on `cdm-rev-hybrid`).
- `wrangler pages dev` not yet run because it needs a build to complete first (>10min). Pilot route compiles clean (tsc has no errors in `src/lib/db.ts`, `src/lib/cache.ts`, `src/pages/r/[slug].ts`).

## Loop authority
Currently in `/loop` mode with directive: "until you finish all the work that doesnt involve touching the live database or system". Off-limits this loop:
- Live Supabase writes (Phase 2.4, 3.1)
- Wiring `tools/creditdoc_db.py` to revalidate (Phase 2.3 — production tool)
- DNS changes (Phase 6 cutover only)
- Vercel production changes (Phase 6 only)
- CF Pages production deploy (preview is OK)
