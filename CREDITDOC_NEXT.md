# CreditDoc — NEXT (RULE 10 handoff, last updated 2026-05-12 pipeline repair)

## Immediate priorities

1. **Monitor pipeline health.** Smoke test runs 05:00 UTC. If it catches failures, fix same day. The 4-day blog gap and 9-day wellness gap happened because nothing alerted.

2. **Strategic analysis.** Jammi asked "what is the next highest-impact thing we can do" — session pivoted to fixing broken pipelines before answering. Verified data: 287/18,968 indexed, 0 organic clicks yet (domain is 8 weeks old). The regulatory layer is LIVE. City guides + localized quiz are the planned next content layer (see `project_creditdoc_city_guides_plan.md`).

3. **Wellness Wave 3 will exhaust in ~17 days** (34 remaining ÷ 2/day). Need Wave 4 before then or the queue goes empty again. The smoke test will catch it, but proactive refill is better.

4. **Blog queue has 49 items** — good for ~24 days at 2/day.

## DO NOT

- Do not touch Supabase sync — it's working. All 4 content write methods now auto-sync.
- Do not rewrite any SEO content changed in last 7 days.
- Do not touch the indexing script — verified 152 OK today. Let it run.
- Do not use CLOUDFLARE_API_TOKEN for wrangler deploy — must unset it and use CLOUDFLARE_API_KEY.

## Previously completed (kept for reference)

Deploy details:
- Worker: `creditdoc`
- Version: `8b502c80-3cfe-476c-a1a5-4f700e858a28`
- Deployed at 2026-05-07 08:03 UTC using the documented Global API Key auth path, not the zone-only `CLOUDFLARE_API_TOKEN`.

Completed checks:
1. Test live:
   - `https://www.creditdoc.co/city/dallas-texas/` → 301 → `/city/dallas-tx/` → 200
   - `https://www.creditdoc.co/city/jersey-city-new%20jersey/` → 301 → `/city/jersey-city-nj/` → 200
   - `https://www.creditdoc.co/city/durham-north%20carolina/` → 301 → `/city/durham-nc/` → 200
   - canonical city URLs like `/city/dallas-tx/` return 200 with no redirect.
2. Live sitemap check: `https://www.creditdoc.co/sitemap-0.xml` has 260 city URLs and 0 `%20`/full-state city URL matches.

GSC status:
1. Existing GSC OAuth credentials are wired and refresh successfully.
2. Read endpoint works on `sc-domain:creditdoc.co`.
3. GSC already has the correct production sitemap registered: `https://www.creditdoc.co/sitemap-index.xml`; last submitted `2026-04-27T13:02:26.581Z`, last downloaded `2026-04-27T13:02:27.620Z`, sitemap index, `0` errors, `0` warnings.
4. API resubmit was attempted on 2026-05-07 and Google returned 403 `ACCESS_TOKEN_SCOPE_INSUFFICIENT` for `SitemapsService.Submit`. The saved refresh token can read GSC but cannot submit sitemaps until re-authorized with full `https://www.googleapis.com/auth/webmasters` scope.

Remaining:
1. Manual GSC resubmit or OAuth re-auth with full `webmasters` scope if scriptable sitemap submit is required.
2. Monitor weekly in stored/live GSC. Keep city 301s at least 12 months for old URLs that had impressions; never remove before 90 days with zero meaningful impressions/crawls.

Reference files:
- Code normalization: `src/utils/data-build.ts`
- Runtime fallback guard: `src/middleware.ts`
- Static Cloudflare redirect rules: `public/_redirects`
- Durable ledger: `docs/redirect-ledger.md`
- Baseline/results: top entry in `CREDITDOC_NOW.md`

## ✅ CUTOVER DONE — `www.creditdoc.co` is live on the new Worker

The DNS flip is done. Both API calls (Worker route bind + CNAME proxy flip) succeeded at ~10:18 CAT, 2026-05-02. 7/7 smoke tests GREEN on the real production URL. OBJ-1 (live database update → live page in ~5s) proven on `www.creditdoc.co/r/upstart-columbus/`.

**Worker live on production:** `17807bf2-ce57-4587-ad96-10bb2b1d1600` via Cloudflare zone `b644afdfb731703f578f6885ca1774b4`, route ID `9e0f031ee146425182f0a083d328897e`.

**Apex `creditdoc.co` (no www) was NOT flipped — it still points at Vercel.** If you want apex → Worker too, that's a separate flip:
- Add Worker route `creditdoc.co/*` → `creditdoc`
- Add `creditdoc.co` proxied DNS record (currently `A 216.198.79.1 proxied=False` → Vercel; would need to be Cloudflare-proxied for the route to fire)

For now, the canonical site is `https://www.creditdoc.co` and the apex is a Vercel fallback. Most users hit www anyway, but Google may still show some apex links until they re-crawl. Decision: leave for now, or flip in a follow-up.

---

## 🟢 ORIGINAL NEXT ACTION (now superseded — kept for reference)
**~~Tomorrow morning switchover (2026-05-03, Jammi-side)~~** — done same-day at Jammi's request.

The latest version on the live test address now includes **three extra fixes Jammi asked for** before the switchover (security headers on static pages, broken brand pages dropped from the sitemap, search page rewritten to query the database instead of bundling a 20MB blob into the page). Live "edit the database, see it on the page within 5 seconds" was tested end-to-end and worked.

**Active worker version:** `17807bf2-ce57-4587-ad96-10bb2b1d1600` (replaces yesterday's `1df76d8e`).

The switchover steps below are unchanged.

## 🟢 ORIGINAL NEXT ACTION — Tomorrow morning switchover (2026-05-03, Jammi-side)

The latest code is on the live website now. Three things still need to happen tomorrow morning (in this order):

1. **Open Cloudflare dashboard → Workers & Pages → `creditdoc` → Domains & Routes.**
2. **Add the route `www.creditdoc.co/*`** pointing at the `creditdoc` worker. (This is the action that "moves" the live website from Vercel to Cloudflare.)
3. **Test in a browser:** `https://www.creditdoc.co/` returns the homepage; `https://www.creditdoc.co/blog/<any-real-slug>/` shows the blog post; `https://www.creditdoc.co/r/upstart/` shows the lender review.

**Step-by-step in the switchover review PDF:** [Drive link](https://drive.google.com/file/d/1QXRAkZAzkMUsTrTGPnVfNomVe0dI0Hdh/view) — sections "DNS flip checklist" and "Rollback plan."

If anything looks wrong: rollback is one click — remove the Cloudflare route. The website goes straight back to Vercel.

**Why this is needed:** the new code is live but only on a test address (`creditdoc.fancy-glitter-38f7.workers.dev`). Visitors going to `www.creditdoc.co` are still hitting the old Vercel build. Step 2 above is what moves them across.

## Cleanup tasks for after the switchover (NOT urgent, can wait days)

- Patch the test probe `tools/cdm_rev_phase24_e2e_probe.py` — its default address still points at a deleted host (`cdm-rev-hybrid.creditdoc.pages.dev`). Should be `https://www.creditdoc.co`.
- Build a precomputed lender-by-category table so `/categories/<category>/` pages can also update without rebuilds. Currently still pre-baked (works fine, just not as fast to update).
- Review and commit the 5 misc local files not yet pushed to git: `CREDITDOC_NOW.md`, the migration plan doc, two `tools/*.astro` test pages, and `html-diff.sh`.

---



## ✅ LANDED (Apr 30 PM late) — Phase 3.4 + 3.5 + 3.6 + Phase 5.4 [OBJ-1, OBJ-3]

**Phase 5.4 — SSR health-check poller** (commit `081fd0162b`): `tools/cdm_rev_health_poller.py`. Single-shot poll of 5 URLs on the preview, records status / TTFB / body / cf-cache / cdm-last-updated meta tag. JSON-lines log to `data/health/poll-YYYYMMDD.jsonl`. First run: 5/5 status=200, p95 TTFB 0.540s, 3 /r/ URLs flagged for missing meta tag (the same CF deploy-lag we already knew about — when CF picks up `4ed97fdcf2`+ this flips to PASS). Cron wiring deferred (needs Jammi greenlight).

**Phase 3.6 — Privacy policy mentions consent banner** (commit `e116ed6b60`): bumps Last Updated date, describes the on-site banner.

## ✅ LANDED (Apr 30 PM late) — Phase 3.4 token register + Phase 3.5 cookie consent [OBJ-3]

**Phase 3.4 — `docs/compliance/token_register.md`** (commit `754c88ea2e`): single source of truth for every credential. CF + Supabase + R2 + REVALIDATE_TOKEN + GSC/GA4 + Places + social + DPA attestations. Quarterly review, next due 2026-07-30.

**Phase 3.5 — Cookie consent + GA4 default-deny** (commit `fd3c477908`): `CookieConsent.astro` pinned bottom-of-viewport, two buttons (Accept / Decline), localStorage `cd_consent` persistence. BaseLayout switched to Google Consent Mode v2 — `gtag('consent', 'default', {analytics_storage: 'denied', ...})` runs BEFORE the gtag library loads, so measurement queues until opt-in. Banner only shows for genuinely new visitors (prior consent silently restored).

CDM-REV Phase 3 (compliance baseline) is now substantively complete: 3.1 audit_log triggers GREEN, 3.2 RLS hygiene rule documented, 3.4 token register, 3.5 consent. Remaining: 3.3 DPA PDFs (needs CF + Supabase dashboard access — Jammi-side), 3.6 verify privacy.astro/terms.astro copy is current.

## ✅ LANDED (Apr 30 PM late) — Dangling similar_lenders prune APPLIED [OBJ-1]

Jammi verbal greenlight 2026-04-30 ("if its dead data then its warranted cleanup"). `python3 tools/cdm_rev_prune_dangling_similar.py --apply` ran clean: **1,386/1,386 rows updated, 0 failed**. 14,013 refs → 11,758 refs (2,255 dead removed). Re-scan confirms 0 remaining dead refs. Audit_log holds full rollback trail per row.

## ✅ LANDED (Apr 30 PM) — Phase 2.5b filter-bug fix + PostgREST linter [OBJ-1]

**Bug caught pre-deploy.** Commit `082ded1de2` added `&rating=gt.0` to similar_lenders PostgREST URL; `rating` is inside body_inline jsonb, not a column. Direct curl returned `42703 column lenders.rating does not exist`. Adapter would have silently returned `[]`, collapsing every sidebar to empty (then category-fill backfilling all 3 slots). Fixed in commit `6b357cb250` — drop URL filter, do client-side filter instead.

**New regression guard:** `tools/cdm_rev_postgrest_lint.py` (commit `12bc73ca75`) greps src/lib/db.ts for PostgREST predicates and validates each filter column exists on the table via `information_schema.columns`. Run before every push:
```
python3 tools/cdm_rev_postgrest_lint.py
# OK — 18 filter(s) lint clean across 9 table(s).
```

**Verifier:** 3/3 OBJ GREEN holds. Probe age=750s, p95=0.061s.

## ✅ LANDED (Apr 30 mid-day) — Phase 2.5 dual-write + Phase 2.4 GREEN [OBJ-1]

**Path A is DONE.** `creditdoc_db.py` now dual-writes to Supabase via PostgREST upsert on every lender writer. Soft-fail + retry queue. Smoke test 139ms. e2e probe verdict OBJ-1: GREEN by threshold. Commit `4ed97fdcf2` on `cdm-rev-hybrid`.

## Immediate next moves (in order)

1. **Commit Phase 2.5b rating filter + 4ed97fdcf2 amendments** if not already pushed. Push to `cdm-rev-hybrid`.
2. **Wait for CF Pages auto-deploy** of Phase 2.5b — confirm via `curl -I cdm-rev-hybrid.creditdoc.pages.dev/r/upstart` (look for fresh `x-cdm-content-version` and absence of zero-rating ghost cards in HTML).
3. **Re-run extended 15-slug parity sweep** (`tools/cdm_rev_structural_parity.py` against the 15-slug list including upstart). Target: 14/15 (3 of 4 prior fails were 404-on-both bad slugs; only Upstart was real drift).
4. **Re-run Phase 2.4 probe with cleaner meta-tag fingerprint** to lock OBJ-1 GREEN definitively (target: 20/20 successes once CF deploy lands).
5. **Update `verify_strategic_objectives.py`** to read probe output JSON directly so the verifier reflects the GREEN verdict instead of staying AMBER.

## ❓ Open decisions waiting on Jammi

- **Phase 6 DNS cutover** — flip `creditdoc.co` apex from current host to `cdm-rev-hybrid.creditdoc.pages.dev`. Off-limits without explicit greenlight per CDM-REV plan.
- **REVALIDATE_TOKEN crontab** — periodic warm-cache pings. Off-limits without greenlight (paid-API class concern even though it's free).
- **Service role key rotation** — `SUPABASE_SERVICE_ROLE_KEY` transited chat once. Rotate post-CDM-REV migration in Supabase dashboard → Settings → API Keys → Reset.
- **DROP `lenders_bak_2026_04_29_pre_a1`** — keep until Phase 2.4 confirmed + 7 quiet days, then DROP.

## What NOT to do

- Don't touch `arch-overhaul` branch — that's the parallel-window Claude's territory.
- Don't `git add -A src/content/lenders/` — use `creditdoc_build.py --export-and-commit`.
- Don't rebuild scrapers/clusters — see RULE 6 in CLAUDE.md.
- Don't apply Phase 3.1 audit_log triggers / DNS cutover / REVALIDATE_TOKEN crontab without explicit Jammi greenlight.

---

## ✅ UNBLOCKED (Apr 30 morning) — historical, kept for context

**Supabase service_role key captured** → `SUPABASE_SERVICE_ROLE_KEY` lives at `/srv/BusinessOps/tools/.supabase-creditdoc.env` (chmod 600, outside git). Plus `SUPABASE_DB_PASSWORD` already there. Either auth path (REST PATCH or psycopg) is now usable. The "HARD BLOCKER" claim in earlier handoffs was wrong — DB password was always sufficient.

**Backup table RLS lockdown applied** (`apply_migration` `lock_down_lenders_backup_rls`): `lenders_bak_2026_04_29_pre_a1` is now RLS-on with deny-all policy for anon/authenticated. ERROR-level advisor cleared. Backup kept until Phase 2.4 e2e probe + 7 quiet days, then DROP.

**Hygiene rule added** ([OBJ-3]): every public-schema CREATE TABLE must enable RLS + add ≥1 policy in the same migration. See `feedback_supabase_public_table_rls.md` in auto-memory.

## What Path A actually requires (next move)

**Architectural gap reminder:** `tools/creditdoc_db.py` is **SQLite-only**. SSR reads **Supabase**. There is **no SQLite→Supabase write bridge** yet. Every "DB write" the writers perform never reaches the surface the SSR is reading from. Phase 2.4 e2e revalidate probe will time out until this lands.

**Decision (Jammi greenlit, verbatim):** "Please put the final phase of moving to B right at the end after the migration and make sure its recorded as part of the project so we can address it at the end. Please keep going with A we need to switch asap so we can work on the site"

- **Path A (NOW, ~30-50 LOC additive):** dual-write in `creditdoc_db.py`. SQLite UPDATE → Supabase write (REST PATCH with service_role OR psycopg with DB password — TBD which during build) → revalidate ping. Phase 2.3.C in plan.
- **Path B (Phase 8, post-cutover):** retire SQLite, Supabase canonical. ~400-600 LOC churn. DO NOT START before cutover stable.

**Verification commands the next agent should run before doing anything else:**
```bash
# Confirm gap still exists (should return only the revalidate ping line, no PATCH calls)
grep -n 'rest/v1\|PATCH\|psycopg' /srv/BusinessOps/creditdoc/tools/creditdoc_db.py
# Confirm key absent (should not contain SERVICE_ROLE)
grep -l SERVICE_ROLE /srv/BusinessOps/tools/.supabase-creditdoc.env /srv/BusinessOps/.env /srv/BusinessOps/tools/.creditdoc-migration.env 2>/dev/null
# Confirm RLS state (anon SELECT-only on writer tables)
# (use Supabase MCP list_tables for project pndpnjjkhknmutlmlwsk)
```

Memory Palace drawers filed: `creditdoc/architecture` (gap), `creditdoc/decisions` (Path A/B sequencing), `claude-cdm-rev-loop` diary entry.

---

## What's next

### 1. **HTML parity drift — RESOLVED on canonical 10-slug sample, 11/15 on extended sweep** ✅

Commit `3ef22eb9af` (Apr 30) applied the 4 patches. Preview at `70121a9f.creditdoc.pages.dev`. `tools/cdm_rev_structural_parity.py` reports 10/10 PASS on canonical sample (with cache-bust query string).

**1a. Extended sweep finding (Apr 30, post-loop):** 11/15 PASS on a wider 15-slug sample. 3 fails were 404-on-both (bad slug guesses in the test set). 1 real residual: **`upstart`** — preview pulls a *different* `similar_lenders` set than prod did at prerender time (`007-credit-agent`, `1st-and-last-stop-financial`, `a-plus-credit-services` vs prod's `a-plus-credit-services`, `better-life-credit-llc`), and 2 of the new entries have `rating=0` in `body_inline`. **This is data drift, not code drift** — DB `similar_lenders` was edited after prod prerender. Two cleanest fixes:
  - (A) Server-side filter in `getLendersBySlugListRuntime`: `&rating=gt.0` ~2 LOC. Hides 0-rated cards globally.
  - (B) DB cleanup: rewrite `similar_lenders` arrays to exclude rating=0 slugs. Data fix.

  **Awaiting Jammi greenlight on choice (A or B).** No silent fix — pre-edit rule applies.

### 1b. (Was) HTML parity drift investigation (kept for context)

Forensic diff complete on credit-saint (worst at 4.13%). Findings file:
`CreditDoc Project Improvement/2026-04-29_HTML_PARITY_DRIFT_FINDINGS.md`

**Real drift sources (not formatting noise):**
1. **Date stringification** — `lenders.last_updated` returned as full ISO `2026-04-29T12:10:54.809439+00:00` instead of `2026-04-05` date-only. Hits JSON-LD `datePublished` and visible "Updated" line. Cosmetic but affects search snippets. Fix: ~5 LOC slice in SSR loader.
2. **`similar_lenders` cards rendered with empty fields (CRITICAL)** — logos, descriptions, ratings, pricing, BBB, money-back, "Best for" all blank on preview. Confirmed via JSON inspection: `similar_lenders` is a **list of slug strings** in JSON; build-time prerender expands via `getAllLenders()` filesystem join. SSR calls `getLendersBySlugListRuntime` then `shapeCatalogToLenderStub` — but the stub function isn't selecting/exposing the card-render columns. Fix: ~30-50 LOC in `data-runtime.ts`.
3. **5 `/compare/credit-saint-vs-X/` cards missing** on preview. Either A.2 comparisons backfill missed rows OR `getComparisonsForLenderRuntime` filter mismatch. Need to read the runtime query.
4. **Service array order shuffled** — JSONB roundtrip doesn't preserve order. Fix: `.sort()` ~3 LOC.

**Read-only next steps (this loop, no DB writes, no edits without diff):**
- DONE — db.ts + data-runtime.ts read; root cause confirmed (CATALOG_COLUMNS 8 cols, shapeCatalogToLenderStub minimal, comparisons limit=6 hardcoded).
- DONE — `tools/cdm_rev_structural_parity.py` written + 10-slug baseline captured (0/10 pass).
- DONE — patch proposal written (4 patches, ~18 LOC after re-scoping with existing infra, zero schema) — see findings doc.
- DONE — drop-in unified diff blocks for all 4 patches written into findings doc § "drop-in diff blocks". Application is now mechanical on greenlight.
- **AWAITING Jammi greenlight** to apply patches.
- After greenlight: apply → rebuild → `npx wrangler pages deploy dist` → re-run `tools/cdm_rev_structural_parity.py` (target 10/10) → re-run `tools/cdm_rev_html_diff.sh` (target <0.1%).

### 2. **Phase 2.4 end-to-end revalidation probe — script DRAFTED Apr 30**

Probe drafted at `tools/cdm_rev_phase24_e2e_probe.py`. Defaults to `--dry-run` (no DB contact). Dry-run smoke test PASSED. On greenlight, run:
```bash
python3 tools/cdm_rev_phase24_e2e_probe.py --apply --slug credit-saint --trials 20
```
Method: GET pre-fingerprint (JSON-LD timestamps) → `UPDATE lenders SET last_updated = NOW()` (transient field, trigger fires, writer pings revalidate) → poll cache-busted GET until fingerprint flips → record latency. Target p95 ≤ 10s. Output is JSON with p50/p95/max + `obj1_verdict: GREEN|AMBER`. **This run is what flips OBJ-1 to GREEN.**

Cron wiring proposal (Phase 2.3.B) drafted at `tools/cdm_rev_revalidate_cron_proposal.md` — append-only crontab edits for guardian + db_sync + publish_blog_posts + daily_seo_content. AWAITING JAMMI GREENLIGHT.

### 2. **Activate revalidate ping in production tools**

Phase 2.3 is wired, but only fires when `REVALIDATE_TOKEN` env var is set. Token lives at `/srv/BusinessOps/tools/.creditdoc-revalidate.env` (chmod 600). To activate:

```bash
# In any cron unit that calls creditdoc_db.py writers:
. /srv/BusinessOps/tools/.creditdoc-revalidate.env
export REVALIDATE_TOKEN
```

Cron units that should source it (need Jammi greenlight to modify crontab):
- `creditdoc_db_sync.py` (07:00 UTC daily)
- `creditdoc_guardian.py` (hourly)
- Any cluster_answer publisher
- Any blog_writer.py / publish_blog_posts.py invocation

### 3. Phase 3.1 — audit_log triggers (off-limits without explicit greenlight)

Live Supabase trigger creation. Plan unchanged.

### 4. **Strategic question from Jammi — 20K+ records full migration to Supabase — ANSWERED (Apr 29 loop)**

> "when are we pulling the full 20,000 plus records to the database with all the information, maps locations, links etc - this is going to be the acid test - all that stuff needs to work seamlessley"

**Short answer:** It's already done — but the SSR can't read it yet. Full analysis in `CreditDoc Project Improvement/2026-04-29_20K_RECORDS_QUESTION_ANSWER.md`.

**Confirmed via `jq`:** `body_inline jsonb` (A.1 backfill, 20,813/20,825 rows) contains every per-lender field — logo_url, rating, pricing.tiers[], rating_breakdown.bbb, money_back_guarantee, similar_lenders[], best_for[], services[], pros/cons, address, affiliate_url, etc. The data IS in Supabase.

**The bottleneck is projection, not migration.** `CATALOG_COLUMNS` (db.ts:44) is 8 cols. `shapeCatalogToLenderStub` doesn't read body_inline jsonb paths. Patch 1 in the parity findings doc fixes this with ~30 LOC across `db.ts` + `data-runtime.ts`, zero schema changes.

**Recommended sequence:**
1. Apply the 4 parity patches → HTML parity GREEN → OBJ-1 unblocks.
2. Phase 2.4 revalidate probe → OBJ-1 fully GREEN.
3. **Path X (proper column promotion) is DEFERRED**, only triggered when one of: column-level RLS needed (affiliate_url scoping), GIN-indexed structured search needed, foreign-key referential integrity needed, or per-column audit_log granularity needed (Phase 3.1).

The "acid test" Jammi was pointing at is now framed as a render-side fix, not a data-migration project. ~30 LOC instead of 8-12h.

---

## What's DONE this loop

- [x] Pushed `cdm-rev-hybrid` to origin (5 commits) earlier
- [x] A.2 backfill applied — 303 rows (wellness 81 / comparisons 165 / brands 57)
- [x] A.3 DDL applied + backfill — 139 rows (states 50 / categories 18 / glossary 71)
- [x] A.4 DDL applied + backfill — 77 rows (blog 34 / listicles 26 / answers 14 / specials 3)
- [x] REVALIDATE_TOKEN set on CF Pages preview env
- [x] Worker redeployed (14:49 UTC): `https://d1ed5fba.creditdoc.pages.dev`
- [x] Phase 2.3 wired: `_ping_revalidate()` + 9 writer injection points + `/api/revalidate` extended to 11 ContentTypes — commit `7b5065d7e4`
- [x] **Option C+ utils/data.ts split landed** — commit `c5ab63a4f1`. data.ts (779→408 pure) + new data-build.ts (367 fs-backed) + 24 page imports + Header.astro switched to data-runtime. `grep -rln 'node:fs' dist/_worker.js/` returns nothing.

## What's NEXT (in order, awaiting unblock)

1. **(Jammi action)** Refresh `CLOUDFLARE_API_TOKEN` in `/srv/BusinessOps/.env` per item 1 above.
2. **(loop)** `cd /srv/BusinessOps/creditdoc && source /srv/BusinessOps/.env && export CLOUDFLARE_API_TOKEN && npx wrangler pages deploy dist --project-name creditdoc --branch cdm-rev-hybrid`
3. **(loop)** Run `tools/cdm_rev_html_diff.sh` — Phase 1 acceptance gate (d). If green: OBJ-1 → GREEN.
4. **(propose)** Section A.5 plan for full 20K+ lender records → Supabase row-level resources. Wait for Jammi greenlight before any DB DDL.
5. **(crontab modification — Jammi greenlight)** Wire `REVALIDATE_TOKEN` into cron units.
6. **(Jammi greenlight)** Phase 3.1 audit_log trigger creation.
7. **(separate explicit greenlight + 24h notice)** Phase 6 DNS flip.

---

## What NOT to do

- Do NOT touch `arch-overhaul` branch (parallel-window territory).
- Do NOT auto-flip DNS. Production cutover is separate explicitly-approved step. Jammi: "We are not pulling any triggers for cutover until site is completely reviewed and tested. We need to dot every i and cross every t."
- Do NOT touch `utils/data.ts` or `utils/data-build.ts` without showing the diff first — pre-edit rule applies and the split is a recent (today) change.
- Do NOT redo `/privacy/`, `/terms/`, `/disclosure/` — they are LIVE and 200 OK.
- Do NOT propose A.5+ (full lender migration) execution until preview deploy is clean and HTML diff smoke test passes.

---

## Reference: branch state at handoff

- Working branch: `cdm-rev-hybrid` — pushed to origin at `c5ab63a4f1`
- Latest commit: `c5ab63a4f1` — CDM-REV Option C+ utils/data.ts split
- Previous: `7b5065d7e4` — Phase 2.3 wiring
- `main`: untouched
- `arch-overhaul`: parallel-window, off-limits
- Live `creditdoc.co`: serving previous Vercel static build, untouched
- CF Pages preview: `https://cdm-rev-hybrid.creditdoc.pages.dev` (deploy `d1ed5fba` — STALE, awaits redeploy after token refresh)

Re-check verifier any time:
```bash
python3 tools/verify_strategic_objectives.py
```
