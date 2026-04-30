# CreditDoc — LIVE STATE (LIVE / RESUME-CURSOR)

> **Read me first.** This file is rewritten at the end of every /loop iteration. It is the resume-cursor — the next-spawned Claude (or me post-compaction) reads this BEFORE MEMORY.md / DECISIONS.md to know "where are we right now."

---

## RIGHT NOW — 2026-04-30 ~11:38 UTC (iter 11) · 🟡 ALL ROLLBACK TOOLING SHIPPED, DEPLOY STILL BLOCKED

**Deploy status:** Last successful CF Pages build was ~04:00 UTC. 7 commits now pushed to `cdm-rev-hybrid` since — none built. Verified at 11:37 UTC: 5 commit-prefixed deploy URLs (`c76f12a1` → `44db458c2a`) ALL return 404. Branch alias `cdm-rev-hybrid.creditdoc.pages.dev` returns HTTP 200 but serves the LAST KNOWN GOOD HTML (no `x-cdm-version`, `cache-control: max-age=0, must-revalidate`). Webhook-kick FAILED.

**Auth state UNCHANGED:** CF API token empty. `wrangler whoami` not authenticated. Cannot drive deploys autonomously.

**🛑 ACTION JAMMI — pick ONE:**
1. **Single click:** dash.cloudflare.com → Workers & Pages → `creditdoc` → latest deployment (~7h old) → `⋯` → **"Retry deployment"**
2. **OR paste me a CF Pages:Edit token** and I'll drive every redeploy via `wrangler` for the rest of the migration. Token goes in `/srv/BusinessOps/tools/.creditdoc-migration.env` (chmod 600).
3. **OR tell me what you see in the dash** — building? red error? auth-disconnected banner? — so I can root-cause instead of guess.

**User signal:** "we need to be concluding testing this evening" — evening deadline. Live e2e testing is impossible until deploy unblocks. Offline work continues.

---

## ITER 11 PROGRESS (parallel work while deploy blocked)

**Commit `44db458c2a` — Phase 5.9.2 rollback drill tool (3 of 3)** (push 11:38 UTC).

`tools/cdm_rev_rollback_drill.sh` (175 LOC) — automated wrapper around Drill 1 (CF Pages worker rollback). Captures pre-revert state of probe URL (status + `x-cdm-version` + body sha256), marks decision-to-revert timestamp, runs `git revert --no-edit anchor..HEAD`, pushes, polls every 5s with 8min timeout, writes JSON report to `data/cdm_rev_rollback_drill_<TS>.json`. Pass criterion: `total_seconds <= 300`. Distinct exit codes 0/1/2/3/4 for pass/bad-args/git-failed/never-recovered/exceeded. Has `--dry-run`.

**Task #21 (3 rollback rehearsal scripts) NOW COMPLETE in commits.** Dress rehearsal still gated on CF Pages deploy unblock — needs a working preview URL to time `git revert → 200` wall clock against.

**5.9 status overall:**
- 5.9.1 Playbook (`docs/plans/2026-04-30_PHASE_5_9_ROLLBACK_REHEARSAL.md`) ✅ DONE iter 9
- 5.9.2 Tooling (3 scripts) ✅ DONE iter 10+11
- 5.9.3 Dress rehearsal ⬜ BLOCKED on deploy
- 5.9.4 Open Qs to Jammi (DNS TTL, dash access, PITR window, notify channel, auto-revert daemon) ⬜ ASKED iter 9, awaiting answers

This unblocks **§5.9 Rollback wrapper rehearsed and timed** for the Phase 6 cutover gate ONCE CF Pages deploy unblock + dress rehearsal completes.

---

## ITER 10 PROGRESS (parallel work while deploy blocked)

**Commit `208bcb5dc9` — Phase 5.9.2 rollback tooling (2 of 3)** (push 11:33 UTC).

`tools/cdm_rev_snapshot_counts.py` (140 LOC) — pre-cutover row-count snapshot via PostgREST anon. Tested live. ~1.4s wall time. Output covers:
- 8 SSR-backing tables (lenders, answers, listicles, blog_posts, wellness_guides, states, categories, specials) with row_count + max(updated_at)
- ready_for_index_count (publish gate for /r/[slug] + state pages) — currently 15,524
- 2 MV stubs (state_lender_counts, state_city_lender_counts) — return 404 as expected (A.5 not yet applied)
- Top-10 lenders-by-state when MVs exist

Live baseline saved to `backups/cdm_rev_pre_cutover_counts_20260430T113330.json` — usable as the rollback-detection anchor.

`tools/cdm_rev_revert_route.sh` (75 LOC) — single-route prerender flip for emergency Drill 2. Idempotent, refuses if directive isn't exactly the expected form, has `--dry-run`. Tested dry-run on `src/pages/answers/[slug].astro` — correctly identifies line 17 for patch.

**Third tool (`cdm_rev_rollback_drill.sh`) deferred** — it needs a working CF Pages deploy to time against (the polling-loop wall time is the whole point).

Two bugs caught + fixed during snapshot tool build:
1. URL builder collision (`?` vs `&` separator when query already had filters) — hardcoded `?` was breaking `lenders?processing_status=eq.ready_for_index` count
2. Status check `== 200` missed the PostgREST 206 (Partial Content) on ranged count queries — max_updated_at was always null. Now accepts `(200, 206)`.

---

## ITER 9 PROGRESS (parallel work while deploy blocked)

**Commit `88e6a0851a` — Phase 5.9 rollback rehearsal playbook drafted** (push 11:25 UTC).

`docs/plans/2026-04-30_PHASE_5_9_ROLLBACK_REHEARSAL.md` (197 LOC) covers 5 drills with copy-paste commands + ≤5 min target wall-times:
1. CF Pages worker rollback (most likely scenario) — `git revert` chain → push → wait for CF rebuild
2. Per-route prerender revert — flip `prerender = false` → `true` on a single Astro page
3. Middleware cacheWrap kill-switch — early `return next()` at top of onRequest
4. Supabase A.5 migration rollback — DROP MV/FN/COL chain (already in migration header)
5. DNS revert (worst case Phase 6) — change A record, propagate

Plus pre-cutover snapshot procedure, dress-rehearsal protocol with pass criteria, 3 helper scripts to build (Task #21), and 5 open questions for Jammi (DNS TTL, CF rollback access, Supabase PITR window, notification channel, auto-revert daemon).

This unblocks the Phase 6 cutover gate ("§5.9 Rollback wrapper rehearsed and timed"). Drafted-but-unrehearsed today; rehearsal blocked on CF deploy unblock.

---

## ITER 8 PROGRESS (parallel work while deploy blocked)

**Commit `c76f12a109` — Phase 5.1.b state-page runtime helpers + middleware listicles fix** (push 11:18 UTC, queued behind broken deploy).

`src/lib/db.ts` — 4 new helpers:
- `getStateAggregateRuntime(abbr)` — single-row state count (lender_count, city_count) from `state_lender_counts` MV
- `getAllStateAggregatesRuntime()` — all 50+ states ordered by lender_count desc (for /state index)
- `getStateCitiesAggregateRuntime(abbr, limit)` — top cities in a state from `state_city_lender_counts` MV
- `getLendersByStateRuntime(abbr, limit)` — uses new generated `state_abbr` column on lenders table (replaces unfilterable `body_inline.company_info.state` jsonb deep-path that returns PostgREST 500s)

`src/middleware.ts` — typo fix: added `'listicles'` to the table-union type. /best/[slug] cacheWrap now type-checks against the correct table for `updated_at` probe (was inferring `'lenders'` by mistake).

**Migration NOT yet applied:** `supabase/migrations/2026-04-30_cdm_rev_a5_state_aggregates.sql` is staged. Adds:
- `lenders.state_abbr` generated stored col (UPPER+TRIM of `body_inline.company_info.state`)
- `lenders.city_norm` generated stored col (lower+TRIM of `body_inline.company_info.city`)
- 2 indexes (state_abbr; state_abbr+city_norm)
- 2 MVs (`state_lender_counts`; `state_city_lender_counts`)
- `refresh_state_aggregates()` function
- GRANT SELECT to anon, authenticated
- NOTIFY pgrst, 'reload schema'

**Awaits Jammi greenlight before I run via Supabase MCP `apply_migration`.** Migration is read-only-shape (adds columns + MVs); zero existing-data mutation. Rollback is 5 lines (DROP MV / DROP FN / ALTER DROP COLUMN). Once applied, /state/[slug].astro becomes a one-shot SSR conversion (Phase 5.1 last route).

---

## OBJECTIVES STATE (verifier output expected unchanged from iter 7)

- **OBJ-1 — ≤10s rebuild-free:** GREEN in static analysis (3 SSR routes done: /r/[slug], /answers/[slug], /best/[slug]; /answers/index added; middleware version-keyed cacheWrap on /answers + /best). UNVERIFIED-LIVE because deploy is blocked. Phase 5.5b probe ready to fire post-deploy.
- **OBJ-2 — <50 LOC new surface:** GREEN. State-aggregate helpers add ~90 LOC to db.ts (one file, follows existing _restGet pattern). /state/[slug] conversion will be ≤50 LOC of frontmatter swap.
- **OBJ-3 — staged compliance:** GREEN at marketing-tier. No FS providers active.

## TASKS

- **#15 [in_progress]** — /state/[slug].astro SSR. Helpers landed. Blocked on Jammi greenlight for migration apply.
- **#19 [pending]** — Phase 5.5b live e2e probe `--route all --apply --trials 10`. Blocked on CF deploy.
- **#20 [pending]** — Unblock CF Pages deploy. Blocked on Jammi action OR CF token. **EVENING DEADLINE per Jammi.**
- **#21 [DONE iter 11]** — 3 rollback rehearsal scripts shipped. Dress rehearsal blocked on deploy.
- Phase 5.2 (50-URL HTML diff sweep) — blocked on deploy.
- Phase 5.3 (indexing API + PSI baseline) — blocked on deploy.
- **Phase 5.9 (rollback rehearsal)** — playbook + 3 tools committed. Dress rehearsal gated on CF deploy unblock + Jammi answers to 5 open Qs.

## DECISIONS THIS LOOP

1. Did NOT halt loop on deploy block. Continued parallel work on /state/[slug] runtime helpers — these are pure read paths that don't depend on deploy.
2. Drafted but did NOT apply A.5 state-aggregates migration. Bulk DDL on `lenders` (26K rows) + 2 MV builds is a 5-Step Protocol candidate per `.claude/rules/safety.md` — needs Jammi greenlight + smoke-test plan even though it's additive-only.
3. Fixed middleware.ts type bug found via `tsc --noEmit`. Was inferring `lenders` table for /best/[slug] — would have hit row-not-found on every cache probe and bypassed cache forever (silent perf loss, not a correctness bug).

## NEXT ACTIONS — IF DEPLOY UNBLOCKS

1. Confirm `x-cdm-version` headers appear on /answers + /best
2. Run `python3 tools/cdm_rev_phase24_e2e_probe.py --route all --apply --trials 10` → Phase 5.5b verdict
3. If green: ship Phase 5.2 50-URL HTML-diff sweep as parity proof
4. If red: investigate first failure before any further work

## NEXT ACTIONS — IF JAMMI GREENLIGHTS A.5 MIGRATION

1. Apply via `mcp__claude_ai_Supabase__apply_migration`
2. Smoke test: PostgREST GET `state_lender_counts?select=*&limit=3` returns rows + 200
3. Convert /state/[slug].astro to SSR using new helpers (≤50 LOC swap)
4. Local `npm run build` → verify static export size drops (no fs aggregate scan)
5. Commit + push — rides whatever deploy mechanism is unblocked

---

_Last updated 2026-04-30 11:38 UTC (iter 11)._
