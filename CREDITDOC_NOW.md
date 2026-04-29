# CreditDoc — LIVE STATE (as of 2026-04-29 09:35 UTC)

## Branch
- Working branch: `cdm-rev-hybrid` (off `main`, 3 commits ahead, NOT pushed)
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
| 1.3.B — convert `/review/[slug]` to SSR | ⏸ PAUSED | Blocked on data-layer decision (see `CREDITDOC_NEXT.md` §1). |
| 1.4 — wire CF Cache API around SSR handler | partial — helper ready | Will plug in once 1.3.B ships. |
| 1.5 — `wrangler pages dev` local SSR preview | not started | Local dev only — safe to do once 1.3.B ships. |
| 1.6 — `wrangler pages deploy dist` (preview) | not started | Preview environment — does not touch live `creditdoc.co`. |
| 1.7 — TTFB measurements + Phase 1 acceptance gate | not started | Acceptance bar: build /review/* prerender=0s, TTFB warm <100ms p95, OBJ-1=GREEN. |
| 2.x — revalidation Worker + DB-write wiring | not started | PAUSE for Jammi greenlight before 2.3 (touches `creditdoc_db.py` production tool) and 2.4 (live row probe). |
| 3.1–3.5 — audit_log triggers, RLS audit, DPA, token register, cookie banner | not started | PAUSE for Jammi greenlight before 3.1 (live Supabase trigger creation). |
| 3.6 — privacy/terms pages | ✅ ALREADY LIVE | VERIFIED today: `/privacy/`, `/terms/`, `/disclosure/` all 200. DO NOT redo. |
| 3.7 — encryption-at-rest verification | not started | Doc-only, safe to do. |

## Verifier baseline (Apr 29 09:30 UTC, branch cdm-rev-hybrid)

```
OBJ-1: RED   — hybrid mode active (output: 'static' + CF adapter), but no SSR pilot route yet (Phase 1.3.B not shipped).
OBJ-2: RED   — audit_log table exists, fn_audit_row() missing, 0/4 trigger coverage on lenders|cluster_answers|lead_captures|user_quiz_responses.
OBJ-3: RED   — no SSR pilot route → ~105 LOC to add a parallel SSR JSON route. Drops to GREEN once helpers (cache.ts + db.ts) are wired into a working SSR pilot.
```

Re-run any time: `python3 tools/verify_strategic_objectives.py`

## Known issues / open questions
- Full `astro build` still slow (>10 min on the 17K+ static prerender). This is the OBJ-1 problem we're fixing — Phase 1.3.B will move `/review/[slug]` (~20K pages) off prerender, dropping bulk of build time.
- `body_r2_key` and `body_inline` columns DO NOT exist on Supabase `lenders` yet. Phase 1.3.B needs them (or an alternative data path) before SSR can serve lender bodies.
- Stashed 549 `src/content/lenders/*.json` drift on main — need a separate "DB export sync to main" commit at some point (not on `cdm-rev-hybrid`).

## Loop authority
Currently in `/loop` mode with directive: "until you finish all the work that doesnt involve touching the live database or system". Off-limits this loop:
- Live Supabase writes (Phase 2.4, 3.1)
- Wiring `tools/creditdoc_db.py` to revalidate (Phase 2.3 — production tool)
- DNS changes (Phase 6 cutover only)
- Vercel production changes (Phase 6 only)
- CF Pages production deploy (preview is OK)
