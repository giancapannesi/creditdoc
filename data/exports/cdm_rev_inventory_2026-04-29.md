# CDM-REV-2026-04-29 — Phase 0.4 Inventory Snapshot

**Branch:** `cdm-rev-hybrid` off `main` (commit `88e6836d8d`)
**Date:** 2026-04-29 09:30 UTC

This is the inventory of provisioned-but-not-yet-leveraged infrastructure as of the start of CDM-REV Phase 1. It is the foundation Phase 1+ builds on. Mirrors `creditdoc_cf_supabase_inventory_apr29.md` in MEMORY for cross-session lookup.

## Cloudflare (account `39e709b7…`)

| Resource | State | Phase that leverages it |
|---|---|---|
| Zone `creditdoc.co` (id `b644afdfb731703f578f6885ca1774b4`) | Free Website plan, active. DNS A → Vercel anycast `216.198.79.1`, CNAME `www` → Vercel, all `proxied=False`. **DELIBERATE — staged for Phase 6 cutover. DO NOT TOUCH.** | Phase 6 cutover only |
| Pages project `creditdoc` (`creditdoc.pages.dev`) | Production deployment NONE; latest preview `84925f7c…` on `preview-cdm-2026-04-…` (Apr 28 14:31 UTC). Env vars / KV / R2 / D1 bindings all empty. Compatibility date 2026-04-28. | Phase 1.6 (preview deploy of cdm-rev-hybrid) |
| R2 bucket `creditdoc-assets` (id `4aee4c5d7a2349aaa846f73ecf395fbc`) | 35,214 objects / 274 MB. Public URL: `pub-4aee4c5d7a2349aaa846f73ecf395fbc.r2.dev`. No custom domain, no CORS. | Phase 1.6 (binding `ASSETS`) — body JSON + assets |
| Worker `creditdoc` | Exists, modified Apr 28 07:29 UTC, content empty (HTTP 204), no routes. | Optional — Cache API in Astro SSR is enough for Phase 1 |
| KV namespaces | None | Phase 2 (`creditdoc-versions`) |
| D1 databases | None | Not planned — Supabase Postgres is canonical |

## Supabase (project ref `pndpnjjkhknmutlmlwsk`, TraderTrac org, us-east-1, Postgres 17.6.1.111)

| Table | Rows | Phase 1 status |
|---|---:|---|
| `lenders` | 20,825 | Phase 1.3.B will read via PostgREST + RLS-anon. Missing columns: `body_r2_key`, `body_inline` (need migration). |
| `audit_log` | 0 | Schema only. `fn_audit_row()` trigger NOT created. NOT attached. Phase 3.1 lights this up. |
| `lead_captures` | 0 | INSERT for anon `WITH CHECK (true)` — advisor flagged. Phase 3.2 RLS audit will tighten. |
| `user_quiz_responses` | 0 | Same advisor flag as `lead_captures`. |

**RLS:** all 4 tables RLS-enabled. SELECT on `lenders` gated by `processing_status = 'ready_for_index'` for anon/authenticated.
**Migrations:** `20260428111214 / 0001_initial` (only one).
**Triggers + functions:** `set_updated_at()` (mutable search_path warn), `lenders_updated_at` BEFORE UPDATE.
**Extensions installed:** `pgcrypto`, `uuid-ossp`, `plpgsql`, `pg_stat_statements`, `supabase_vault`. **Not installed (relevant later):** `pg_cron`, `pgaudit`, `vector`, `postgis`.
**Edge functions:** none.
**Security advisor warnings (3 WARN):** `set_updated_at` mutable search_path; `lead_captures_anon_insert` always-true RLS; `user_quiz_responses_anon_insert` always-true RLS.

## Resource × OBJ matrix

| Resource | OBJ served now | OBJ served after Phase 1 plumbing |
|---|---|---|
| CF zone | none (DNS-only, deliberate) | OBJ-1 + OBJ-3 post-cutover |
| CF Pages project | none (preview only) | OBJ-1 (preview smoke), OBJ-1 prod post-cutover |
| R2 `creditdoc-assets` | public-dev URL only | OBJ-1 + OBJ-2 (binding + serving) |
| Worker `creditdoc` (empty) | nothing | optional — Cache API in Astro SSR is enough |
| `lenders` table | nothing in prod (Vercel reads SQLite at build) | OBJ-1 — runtime read source |
| `lead_captures` / `user_quiz_responses` | nothing | OBJ-2 — quiz/lead schema already in place |
| `audit_log` table | nothing (empty) | OBJ-3 tier-1 once trigger added |
| RLS policies | basic correct posture | OBJ-3 tier-1 after 3 free fixes |
| `supabase_vault` | not yet used | OBJ-3 future tiers — encrypted secrets |

## Stage 1 gap (what's missing vs what existed coming in)

- **Repo:** `@astrojs/cloudflare` adapter ✅ INSTALLED (commit `24b0f94ddf`); `output: 'static'` + adapter present (Astro 5 hybrid pattern). `src/lib/cache.ts` + `src/lib/db.ts` ✅ SCAFFOLDED (commit `96b501472d`). `/review/[slug]` SSR conversion DEFERRED (data-layer decision required).
- **Pages provisioning:** env vars (preview), R2 binding `ASSETS = creditdoc-assets`, Supabase secrets — all PLACEHOLDERS in `wrangler.toml`. Filled at Phase 1.6 deploy time.
- **Supabase:** 3 advisor fixes + `audit_log` trigger + `consent_log` + `dsar_request` tables — all SQL-only, no DNS impact, all DEFERRED to Phase 3.

## Source documents

- Inventory review: `CreditDoc Project Improvement/2026-04-29_CLOUDFLARE_SUPABASE_INVENTORY_REVIEW.md`
- Active plan: `creditdoc/docs/plans/2026-04-29_REVISED_MIGRATION_PLAN_HYBRID_FIRST.md`
- Memory snapshot: `/root/.claude/projects/-srv-BusinessOps/memory/creditdoc_cf_supabase_inventory_apr29.md`
- Memory Palace drawer: `wing=creditdoc room=migration` (multiple drawers tagged CDM-REV-2026-04-29)
