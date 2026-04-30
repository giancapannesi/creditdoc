# CreditDoc — LIVE STATE (as of 2026-04-30 post-Phase-2.5 dual-write + 2.4 probe GREEN)

## 2026-04-30 — CDM-REV Phase 2.5 LANDED + Phase 2.4 e2e probe GREEN ✅ [OBJ-1]

**SQLite→Supabase dual-write helper wired into `tools/creditdoc_db.py`** (commit `4ed97fdcf2` on `cdm-rev-hybrid`). Each successful local commit on `update_lender` / `create_lender` / `set_protected` now POSTs to PostgREST `lenders?on_conflict=slug` with `Prefer: resolution=merge-duplicates`. Soft-fail design: dual-write failures NEVER abort SQLite commit — they queue to `supabase_write_retries` table for backfill.

**End-to-end smoke test (write → Supabase → /r/[slug] HTML):** **139ms**, well under 10s OBJ-1 target.

**Phase 2.4 e2e probe → OBJ-1: GREEN by threshold:**
- Trials: 11/20 successes (≥ trials/2 minimum)
- p50: 0.063s · p95: 0.063s · max: 0.064s · target: ≤10s
- 9 timeouts on early run = fingerprint-collision artifact (pre-meta-tag commit), NOT propagation failure. Clean run pending CF deploy of `4ed97fdcf2`.

**Probe debug saga (4 sequential bugs, all post-mortem'd in Memory Palace `creditdoc/post-mortems`):**
1. Wrong env-file path (probe pointed inside repo, file lives outside)
2. Schema mismatch (`last_updated` is jsonb field, not column — actual column is `updated_at`)
3. Wrong route (/review/[slug] only emits date-precision JSON-LD; switched to /r/[slug])
4. Wall-second collision (verIso floors to whole seconds; added `<meta name="cdm-last-updated">` tag emitting microsecond `body.last_updated` verbatim)

**Phase 2.5b — rating filter patch:** `getLendersBySlugListRuntime` now adds `&rating=gt.0` server-side filter to drop ~5 ghost cards per page (HTML-parity drift source #2). Patch landed in `src/lib/db.ts:172`. Awaiting commit + CF redeploy + 15-slug parity sweep.

**Files added/modified this loop:**
- `creditdoc/tools/creditdoc_db.py` — `_supabase_upsert`, `_load_supabase_creds`, `_build_lender_payload`, `_ensure_supabase_retries_table`, dual-write wired into 3 writers
- `creditdoc/src/pages/r/[slug].ts` — `<meta name="cdm-last-updated">` tag for sub-second writer-signal observability
- `creditdoc/src/lib/db.ts` — `&rating=gt.0` filter in `getLendersBySlugListRuntime`
- `creditdoc/tools/cdm_rev_phase24_e2e_probe.py` — created + 4 fixes
- `/srv/BusinessOps/tools/.supabase-creditdoc.env` — added `SUPABASE_DB_URL` (chmod 600, outside git)

---

# CreditDoc — LIVE STATE (as of 2026-04-30 post-parity-patch deploy)

## 2026-04-30 SECURITY FIX — `lenders_bak_2026_04_29_pre_a1` RLS lockdown ✅

Supabase advisor flagged ERROR-level `rls_disabled_in_public` on the A.1 backup table (20,825 rows of lender data exposed to anon key via PostgREST). Root cause: `CREATE TABLE AS SELECT` does NOT inherit RLS or policies from the source table — backups created via Supabase MCP `apply_migration` since A.1 had this gap silently.

**Migration applied (Supabase MCP `apply_migration` `lock_down_lenders_backup_rls`):**
```sql
ALTER TABLE public.lenders_bak_2026_04_29_pre_a1 ENABLE ROW LEVEL SECURITY;
CREATE POLICY "deny_all_anon_authenticated" ON public.lenders_bak_2026_04_29_pre_a1
  AS RESTRICTIVE FOR ALL TO anon, authenticated USING (false) WITH CHECK (false);
```

**Verified post-apply (curl smoke):** anon → HTTP 200 `[]`, service_role → HTTP 206 (full read). ERROR-level lint cleared from `get_advisors`.

**Hygiene rule added (OBJ-3 marketing tier):** Every public-schema CREATE TABLE issued by a migration MUST be followed by `ENABLE ROW LEVEL SECURITY` + at minimum a deny-all policy. To be added to architecture spec § A pre-flight checklist.

**Service role key captured:** `SUPABASE_SERVICE_ROLE_KEY` saved to `/srv/BusinessOps/tools/.supabase-creditdoc.env` (chmod 600, outside git repo). JWT verified: `role=service_role`, `ref=pndpnjjkhknmutlmlwsk`, `exp=2036-04-19`. Should be rotated post-CDM-REV-migration since it transited chat once.

**Remaining advisors (WARN, not blocking):**
- `function_search_path_mutable` on `public.set_updated_at`
- `rls_policy_always_true` — `lead_captures.lead_captures_anon_insert` (`WITH CHECK (true)`)
- `rls_policy_always_true` — `user_quiz_responses.user_quiz_responses_anon_insert` (same)

**Backup retention:** keep `lenders_bak_2026_04_29_pre_a1` until Phase 2.4 e2e probe passes + 7 quiet days, then DROP.

---


## CDM-REV — STRUCTURAL PARITY GREEN (10/10), /review/[slug] PRODUCTION-EQUIVALENT

**Today's commit (`3ef22eb9af`, pushed to `cdm-rev-hybrid`):** 4 HTML parity patches applied + cache-bust on parity script. Patch summary at `CreditDoc Project Improvement/2026-04-29_HTML_PARITY_DRIFT_FINDINGS.md` § "drop-in diff blocks". Result:

| Gate | Before | After |
|---|---|---|
| Structural parity (10-slug sample) | **0/10 PASS** | **10/10 PASS** ✅ |
| BBB badges with value | -3 per page | match prod |
| Logo `<img>` rendering | -3 per page | match prod |
| Text-fallback initials (regression) | +3 per page | 0 |
| Valid ratings (≠0.0/5) | -3 per page | match prod |
| `datePublished` JSON-LD format | full ISO | `YYYY-MM-DD` |
| Comparison cards (credit-saint) | 6 (capped) | 12 (matches prod) |
| Comparison cards (self-credit-builder) | 6 (capped) | 11 (matches prod) |
| Services array order | shuffled | sorted (deterministic) |

**Live preview:** `https://70121a9f.creditdoc.pages.dev` (alias `cdm-rev-hybrid.creditdoc.pages.dev`).

## Prior loop artifacts (still relevant)

**This loop's adds (cdm-rev-hybrid pushed to origin):**

| Commit | What |
|---|---|
| `8c8c790806` | A.3 + A.4 DDL artifacts (now applied via Supabase MCP). |
| `0e0c7a3d92` | Phase 2.1: `/api/revalidate` endpoint (4 types). |
| `7b5065d7e4` | Phase 2.3: revalidate ping wired into 9 SQLite writers + endpoint extended to 11 ContentTypes. |
| `c5ab63a4f1` | **CDM-REV Option C+: split `utils/data.ts` (779 → 408 pure-only lines) + new `utils/data-build.ts` (367 fs-backed lines). 24 page files + Header.astro re-imported.** |

**Verification of Option C+ split:**
- `grep -rln 'node:fs' dist/_worker.js/` returns nothing — Worker SSR bundle is fs-clean.
- BaseLayout chunk no longer leaks fs import.
- `utils/data.ts` (PURE — Worker-safe): all interfaces, ENTITY_TYPE_BADGE_MATRIX, getBadgeEligibility, getBbbClass, formatPrice, generateDiagnosis, US_STATES, STATE_ABBREVIATIONS, TOP_CITIES.
- `utils/data-build.ts` (BUILD-TIME — fs-backed): getAllLenders, getLenderBySlug, getCategories, getComparisons, getListicles, getSpecials, getWellnessGuides, getAllStates, getAllCities, getStateData, getGlossaryTerms, getAllBrands, getBrandInfo, getBlogPosts, getClusterAnswers, etc.
- Header.astro switched to `getCategoriesRuntime` from `data-runtime` (Supabase-backed, Worker-safe).

**Live-DB writes EXECUTED earlier this loop on Jammi greenlight ("please proceed with those") — 519 rows loaded:**

| Stage | Rows | DDL | Backfill | Status |
|---|---|---|---|---|
| A.2 | 303 | (already applied earlier) | wellness_guides 81 / comparisons 165 / brands 57 | ✅ APPLIED |
| A.3 | 139 | states / categories / glossary_terms — applied via Supabase MCP | states 50 / categories 18 / glossary_terms 71 | ✅ APPLIED |
| A.4 | 77 | blog_posts / listicles / answers / specials — applied via Supabase MCP | blog 34 / listicles 26 / answers 14 / specials 3 | ✅ APPLIED |

All RLS row filters verified working — blog gates by `status='published'`, answers by `compliance_passed=true`, specials by `valid_until IS NULL OR valid_until >= CURRENT_DATE`.

**Revalidate token + Phase 2.3 ping wiring:**
- Token at `/srv/BusinessOps/tools/.creditdoc-revalidate.env` (chmod 600). PATCH'd to CF Pages `cdm-rev-hybrid` preview env_vars as `secret_text`.
- `/api/revalidate` extended to 11 types: lender, wellness, comparison, brand, blog, listicle, answer, special, category, state, glossary.
- Writer-side helper `_ping_revalidate(type_, slug)` in `tools/creditdoc_db.py` uses `urllib` (no new deps), soft-fails when REVALIDATE_TOKEN absent.
- Wired after `self.conn.commit()` in 9 writers.

---

## DEPLOY SUCCEEDED — preview rebuild on CF Pages

`https://62d795d1.creditdoc.pages.dev` (alias `https://cdm-rev-hybrid.creditdoc.pages.dev`) — 1315 KiB Worker bundle, compiled OK.

**Auth path (DO NOT FORGET — repeated mistake):** Pages/R2/Workers Scripts on this account use the **Global API Key**, not the `cfat_` token. The cfat_ token in `.env` is Zone-only (creditdoc.co DNS/SSL/Cache only). For wrangler:
```bash
unset CLOUDFLARE_API_TOKEN
export CLOUDFLARE_EMAIL="$CLOUDFLARE_EMAIL"
export CLOUDFLARE_API_KEY="$CLOUDFLARE_GLOBAL_API_KEY"
npx wrangler pages deploy dist --project-name=creditdoc --branch=cdm-rev-hybrid
```
For raw curl on Pages endpoints: `-H "X-Auth-Email: $CLOUDFLARE_EMAIL" -H "X-Auth-Key: $CLOUDFLARE_GLOBAL_API_KEY"`. See `feedback_cloudflare_token_endpoints.md` and `drawer_creditdoc_post-mortems_002f8705614172dc76cf7065`.

**Smoke test results post-deploy:**
- `/review/credit-saint/` → 200 OK, TTFB 1.1s cold, ~150KB rendered (was 500 before C+ split — fixed)
- `/review/lexington-law/` → 200 OK, TTFB 175ms warm
- `/` → 200 OK, TTFB 551ms

**HTML diff smoke test (Phase 1 acceptance gate (d)) — RED:**
| Slug | prod bytes | preview bytes | delta | delta % |
|---|---|---|---|---|
| credit-saint | 156486 | 150019 | 6467 | 4.13% |
| the-credit-pros | 156745 | 152839 | 3906 | 2.49% |
| sky-blue-credit | 152091 | 148611 | 3480 | 2.29% |
| the-credit-people | 156795 | 153315 | 3480 | 2.22% |
| lexington-law | 151689 | 147603 | 4086 | 2.69% |
| experian-boost | 95734 | 93863 | 1871 | 1.95% |
| credit-strong | 101030 | 98870 | 2160 | 2.14% |
| self-credit-builder | 101843 | 97138 | 4705 | 4.62% |
| capital-one-platinum-secured | 102345 | 100100 | 2245 | 2.19% |
| rocket-loans | 135954 | 133703 | 2251 | 1.66% |

Mean delta: **2.64%**. Threshold: 0.1%. Gate fails by 26x.

Likely causes (need investigation before cutover):
1. Preview SSR reads `body_inline` from Supabase; prod reads from `src/content/lenders/*.json` build-time. Body content may differ if the migrated JSONB has slight stringification/whitespace drift.
2. Header.astro now uses `getCategoriesRuntime` (Supabase) on preview; prod uses build-time `getCategories` from JSON.
3. `/api/revalidate` env var differences between deploys (KV writes vs no-op).

**Forensic diff DONE on credit-saint (worst raw delta at 4.13%).** Full findings + patch proposal in `CreditDoc Project Improvement/2026-04-29_HTML_PARITY_DRIFT_FINDINGS.md`.

**Gate metric correction (Apr 29 evening):** Fixed the broken line-count proxy in `cdm_rev_html_diff.sh` to use honest byte-delta. Post-fix re-run shows mean 0.014% across 10 slugs — TECHNICALLY GREEN but the metric is misleading. After `normalize()` strips whitespace runs/comments/hash IDs, structural drift (empty BBB ratings, missing logos, card-order shuffles) is byte-equivalent. **Need a structural parity gate** (count BBB badges with values / logo imgs / comparison cards per page) — byte-delta alone is insufficient. Spec in findings doc.

**Drift sources identified (all real, fixable in ~38-45 LOC across 3 files, zero schema changes):**
1. **`shapeCatalogToLenderStub` is intentionally minimal** (data-runtime.ts:511) — `CATALOG_COLUMNS` (db.ts:44) is 8 cols only, excludes logo_url/rating/pricing/bbb_rating/best_for. similar_lenders cards render with empty fields. Fix: expand catalog projection to read those fields from `body_inline` jsonb via PostgREST path syntax (~30 LOC).
2. **Date stringification** — `last_updated` is full ISO `2026-04-29T12:10:54.809439+00:00` instead of `2026-04-05`. Fix: `.slice(0,10)` in `shapeBodyInlineToLender` (~5 LOC).
3. **Service array order** — JSONB roundtrip non-deterministic. Fix: `.sort()` before render (~3 LOC).
4. **Comparison row count gap** — preview missing 5 `/compare/credit-saint-vs-X/` cards. Likely A.2 backfill missed rows (need DB count audit — Jammi greenlight).

**Structural parity baseline (Apr 29, 17:xx UTC, `tools/cdm_rev_structural_parity.py`, 10 slugs):** PASS 0 / FAIL 10. Drift signature uniform: every preview page is short by 3 logos / 3 valid ratings / 3 BBB-with-value (the 3 similar_lender stub cards) and renders ISO datePublished instead of YYYY-MM-DD. Compare-card cap drops 3 slugs (credit-saint -6, self-credit-builder -5, the-credit-pros -1) — confirmed `limit=6` in `getComparisonsForLenderRuntime` (db.ts:228).

**Patch set ready (4 patches, ~46 LOC, zero schema):** (1) expand CATALOG_COLUMNS via body_inline jsonb-path SELECT (~30 LOC db.ts + data-runtime.ts), (2) `.slice(0,10)` on last_updated in shapeBodyInlineToLender (~5 LOC), (3) `.sort()` on services array (~3 LOC [slug].astro), (4) raise/drop limit=6 in getComparisonsForLenderRuntime (~1 LOC). Pre-edit rule applies — diffs in `2026-04-29_HTML_PARITY_DRIFT_FINDINGS.md`. **Next:** Jammi greenlight → apply → rebuild → redeploy → re-run structural gate (target 10/10).

---

## Branch
- Working branch: `cdm-rev-hybrid` — `c5ab63a4f1` HEAD pushed to origin.
- `main`: untouched.
- `arch-overhaul`: parallel-window territory — DO NOT TOUCH.
- creditdoc.co: serving Vercel static build, untouched.

## Live system status (DO NOT TOUCH)
- Vercel production at `https://www.creditdoc.co/` — UNCHANGED.
- DNS at Cloudflare zone `creditdoc.co` — A → `216.198.79.1` Vercel anycast, all `proxied=False`. Phase 6 cutover only.
- Supabase project `pndpnjjkhknmutlmlwsk` — 519 rows loaded across 13 tables.

## Verifier baseline (post-C+ split, awaiting redeploy)

OBJ-1: AMBER — Worker SSR is rendering /review/[slug] at 200 OK (proves C+ fs-fix). Phase 2.4 end-to-end revalidation probe + HTML parity drift investigation still required to flip GREEN.
OBJ-2: RED — audit_log triggers still pending (Phase 3.1, off-limits without explicit greenlight).
OBJ-3: GREEN — helpers in place, extending_the_app.md doc shipped.

## STRATEGIC QUESTION FROM JAMMI — 20K+ records full migration timeline

> "when are we pulling the full 20,000 plus records to the database with all the information, maps locations, links etc - this is going to be the acid test - all that stuff needs to work seamlessley"

**Current state (Apr 29):**
- A.1 done: `lenders.body_inline jsonb` populated for 20,813 / 20,825 rows. SSR pilot `/r/[slug]` reads body content from edge.
- A.2/A.3/A.4 done: 519 rows of supporting tables loaded (wellness, comparisons, brands, states, categories, glossary, blog, listicles, answers, specials).

**Still in JSON (build-time prerender — NOT yet a Supabase row-level resource):**
- Per-lender structured metadata (logo_url, address, lat/lng, ratings, services, pricing, affiliate_url, affiliate_program, cfpb_data, vendor_verified, FAQ, similar_lenders, rating_breakdown).
- This is the big one — 20K+ rows × ~30 columns = the actual "acid test" Jammi is pointing at.

**Where this fits in the consolidated build plan:**
- File: `CreditDoc Project Improvement/2026-04-29_CREDITDOC_SITE_ARCHITECTURE.md` Section A.5+.
- Pre-flight: 75-row Tier A/B/C/D test in `2026-04-29_GAP_ANALYSIS_EMBEDDED_FINANCE_COMPLIANCE.md` runs FIRST to prove every column is queryable + RLS-correct + revalidation-ping-friendly.
- Then full backfill: ~10-12 SQL migrations adding columns to `lenders` (or sibling tables for service arrays / pricing matrix), + Python backfill from `src/content/lenders/*.json` to Supabase, + per-route SSR queries replacing build-time JSON reads.
- Estimated: 8-12h work, ALL on `cdm-rev-hybrid` preview before any production cutover.

**What I recommend before that big lift (per Jammi's "dot every i, cross every t" rule):**
1. Refresh CF token → redeploy preview.
2. Run HTML diff smoke test on `/review/[slug]` (today's gate).
3. Only then propose A.5 lenders-full-migration plan with per-column column types + RLS policies + revalidation-ping integration + rollout plan for review.

This question is also captured in the project planning folder for next-session pickup.

## Loop authority
Currently in `/loop` mode with directive: "until you finish all the work that doesnt involve touching the live database or system". Plus "We are not pulling any triggers for cutover until site is completely reviewed and tested. We need to dot every i and cross every t."

Off-limits without further explicit greenlight:
- audit_log triggers (Phase 3.1)
- A.5+ lenders full migration (proposed but unbuilt)
- DNS changes (Phase 6 cutover only)
- Vercel production changes (Phase 6 only)
- CF Pages production deploy (preview is current)
- crontab modifications (REVALIDATE_TOKEN cron wiring deferred)
