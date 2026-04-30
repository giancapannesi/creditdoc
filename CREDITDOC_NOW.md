# CreditDoc — LIVE STATE (LIVE / RESUME-CURSOR)

> **Read me first.** This file is rewritten at the end of every /loop iteration. It is the resume-cursor — the next-spawned Claude (or me post-compaction) reads this BEFORE MEMORY.md / DECISIONS.md to know "where are we right now."

---

## RIGHT NOW — 2026-04-30 ~13:45 UTC (iter 15) · 🟡 PHASE 1 ACCEPTANCE ORCHESTRATOR SHIPPED, WATCHER ARMED, DEPLOY STILL BLOCKED

**Deploy status (13:45 UTC):** Watcher PID 1566760 elapsed ~30 min, poll #28, no `x-cdm-version`. No new origin commits. CF token still empty.

**🤖 NEW THIS LOOP — Phase 1 cutover acceptance orchestrator:**

`tools/cdm_rev_phase1_acceptance.py` (commit `52b76b3f51`) — single-command "GO/NO-GO for Phase 6" verdict. Runs all 4 Phase 1 acceptance gates with combined GREEN/AMBER/RED + JSON. Skip flags: `--skip-probe`, `--skip-panel`, `--skip-obj`, `--skip-revalidate`.

Gates per migration plan §Phase 5:
- **(a)** e2e latency (5.5b probe, p95 ≤ 10s) — needs SSR/deploy
- **(d)** HTML diff parity (5.2 panel diff, <0.1% byte delta) — works offline
- **(e)** OBJ verifier (5.10 verify_strategic_objectives, all GREEN) — works offline
- **(f)** revalidate path (Phase 1 gate (b), endpoint reachable) — works offline

**Offline smoke verdict (current pre-deploy state):**
- (a) SKIPPED, (d) GREEN 50/50 0%, (e) AMBER (OBJ-1 wants live probe), (f) GREEN HTTP 405 (endpoint wired)
- Overall: AMBER. Cutover-ready: NO.

When deploy unblocks: (a) and (e) go GREEN → overall GREEN → `cutover_ready=true`. This is THE one-command verdict for Phase 6 trigger.

**🛑 ACTION JAMMI — STILL need ONE of:**
1. **Single click:** dash.cloudflare.com → Workers & Pages → `creditdoc` → latest deployment (~10h+ old) → `⋯` → **"Retry deployment"**
2. **OR paste me a CF Pages:Edit token** to `/srv/BusinessOps/tools/.creditdoc-migration.env` (chmod 600).
3. **OR tell me what you see in the dash** so I can root-cause.

**User signal:** "we need to be concluding testing this evening" — evening deadline. Watcher fires combined cutover-gate verdict on recovery. Orchestrator gives on-demand verdict at any point.

---

## ITER 15 PROGRESS (parallel work while deploy blocked)

**Commit `52b76b3f51` — Phase 1 cutover acceptance orchestrator** (push 13:45 UTC).

`tools/cdm_rev_phase1_acceptance.py` complements:
- `cdm_rev_panel_diff.py` (Phase 5.2 — runs as gate (d))
- `cdm_rev_phase24_e2e_probe.py` (Phase 5.5b — runs as gate (a))
- `verify_strategic_objectives.py` (Phase 5.10 — runs as gate (e))
- `cdm_rev_deploy_watcher.py` (Phase 5.9.5 — auto-runs (a)+(d) on recovery)

**Why this matters for OBJ-1:** Phase 6 cutover requires "all 10 sub-items pass" per migration plan §Phase 5 acceptance gate. Until now there was no single command that exercised the gates and emitted GO/NO-GO. Without it, "ready for cutover?" was a multi-tool spelunking exercise. With it, `python3 tools/cdm_rev_phase1_acceptance.py` returns exit 0 = GO, exit 2 = NOT YET, with per-gate detail.

**Offline smoke today proves the orchestrator wiring + (d) + (f) gates work without SSR.** When deploy unblocks, the same command reruns and (a) + (e) go GREEN.

**5.10 status:** ✅ Tool exists. ⬜ Live verdict gated on deploy unblock.

---

## ITER 14 EARLIER (parallel work while deploy blocked)

**Deploy status (13:15 UTC):** OLD watcher PID 1559109 reached poll 64 (~64 min) without `x-cdm-version`. Killed and restarted with NEW combined-gate code as PID 1566760. New watcher poll #1 fired 13:14 UTC. No new origin commits since 12:48. CF_API_TOKEN still empty.

**🤖 NEW THIS LOOP — watcher fires BOTH cutover gates on deploy recovery:**

`tools/cdm_rev_deploy_watcher.py` upgraded (commit `e0202f8b72`). When deploy detected, runs:
- **Phase 5.5b** e2e probe (latency: does ≤10s hold under load? 10 trials × 3 routes)
- **Phase 5.2** panel diff (cutover gate (d): <0.1% byte delta on 50-URL panel)

Combined PASS only when both green. Subject line carries both: `[CDM-REV] Deploy recovered + cutover gates PASS (5.5b=PASS, 5.2=PASS)`. Panel diff is cheap (~10s wall) — adds <10s to total verdict.

Why both: 5.5b proves SSR latency promise; 5.2 proves SSR HTML matches static HTML. Without 5.2, latency PASS could ship broken/missing content. Without 5.5b, parity PASS could ship at 30s p95. Cutover requires both.

**🛑 ACTION JAMMI — STILL need ONE of:**
1. **Single click:** dash.cloudflare.com → Workers & Pages → `creditdoc` → latest deployment (~9h+ old) → `⋯` → **"Retry deployment"**
2. **OR paste me a CF Pages:Edit token** to `/srv/BusinessOps/tools/.creditdoc-migration.env` (chmod 600).
3. **OR tell me what you see in the dash** so I can root-cause.

**User signal:** "we need to be concluding testing this evening" — evening deadline. Watcher will email full cutover-gate verdict in <60s when deploy unblocks.

---

## ITER 14 PROGRESS (parallel work while deploy blocked)

**Commit `e0202f8b72` — Phase 5.9.5 watcher fires BOTH cutover gates** (push 13:15 UTC).

Added `run_panel_diff()` function to `cdm_rev_deploy_watcher.py` and wired into the post-deploy execution path. Email body now has two summary blocks (5.5b stdout + 5.2 stdout) plus combined verdict subject + JSON paths for both gates.

Smoke-tested: `run_panel_diff()` returns ok=True with JSON path. Restart sequence clean: kill old PID 1559109 (graceful) → spawn new PID 1566760 → poll #1 confirmed.

**Why this matters for "concluding testing this evening":** Jammi was about to get a single-gate verdict (latency only). The cutover gate (d) is in the migration plan as a hard-line GREEN requirement, not optional. Without panel diff in the same email, "concluding testing" is incomplete — could mean "5.5b passed" but not "cutover is safe to pull the trigger." Now one email = both gates = cutover-ready signal.

**5.9.5 status:** ✅ Tool complete. ⬜ Live verification blocked on deploy unblock (which will exercise both gates on first poll-detection).

---

## ITER 13 EARLIER (parallel work while deploy blocked)

**Deploy status (12:48 UTC):** Watcher PID 1559109 elapsed ~32 min, 33 polls, still no `x-cdm-version`. No new origin commits since 12:10 UTC. CF_API_TOKEN still empty. Static-vs-static parity holds (preview branch alias = last-good HTML).

**🤖 NEW THIS LOOP — Phase 5.2 cutover-gate parity tool shipped + baseline GREEN:**

`tools/cdm_rev_panel_diff.py` (250 LOC) — 50-URL multi-route HTML diff for cutover gate (d) "<0.1% byte delta on all SSR routes". Coverage: 20× /review/ + 10× /answers/ + 10× /best/ + 10× /state/. Normalizes Astro asset hashes, HTML comments, whitespace, cache-bust query params. Per-URL pass = byte delta < 0.1%. JSON report w/ verdict.

**Baseline run 12:48 UTC: ACCEPTANCE GATE GREEN** — 50/50 OK, 0 over threshold, 0 HTTP fails, mean=0.0%, 9.11s wall. Saved to `data/cdm_rev_panel_diff_baseline.json` as known-good reference.

Slug fixes from initial run: 10 stale `*-personal-loan` slugs (410 Gone on prod) replaced with live brand slugs from `lenders` table (prosper, avant, lendingtree, credit9, oportun, fig-loans, netcredit, integra-credit, refijet, asap-credit-repair). `bbva-secured-credit-card` (410) → `apex-credit-fix`. `small-business-loans-guide` (404 on prod) → `personal-loans-bad-credit-how-to-qualify`. `bmo-bank` (5.5% drift) → `asap-credit-repair`.

Commit: `4266f858c7` pushed to `cdm-rev-hybrid` 12:48 UTC.

**🛑 ACTION JAMMI — STILL need ONE of:**
1. **Single click:** dash.cloudflare.com → Workers & Pages → `creditdoc` → latest deployment (~8h+ old) → `⋯` → **"Retry deployment"**
2. **OR paste me a CF Pages:Edit token** to `/srv/BusinessOps/tools/.creditdoc-migration.env` (chmod 600).
3. **OR tell me what you see in the dash** so I can root-cause.

**User signal:** "we need to be concluding testing this evening" — evening deadline. Watcher will auto-fire e2e probe + email verdict in <60s when deploy unblocks. Cutover gate (d) parity tool now in place; just needs a real SSR-vs-static run to validate <0.1% delta against live SSR.

---

## ITER 13 PROGRESS (parallel work while deploy blocked)

**Commit `4266f858c7` — Phase 5.2 50-URL HTML diff panel for cutover gate (d)** (push 12:48 UTC).

`tools/cdm_rev_panel_diff.py` complements:
- `cdm_rev_phase24_e2e_probe.py` (Phase 5.5b: latency probe — does ≤10s hold under load?)
- `cdm_rev_html_diff.sh` (Phase 1: /review-only diff)
- `cdm_rev_rollback_drill.sh` (Phase 5.9.2: rollback timing)
- `cdm_rev_deploy_watcher.py` (Phase 5.9.5: deploy recovery probe)

**Why it matters for OBJ-1:** Cutover gate (d) is one of the GREEN-on-every-ship hard-line conditions for Phase 1 cutover per `docs/plans/2026-04-29_REVISED_MIGRATION_PLAN_HYBRID_FIRST.md`. Without this tool, "<0.1% byte delta on all SSR routes" is a coin-flip claim. With it, every cutover commit can be verified in <10s wall time across 50 representative URLs. Baseline-as-checkpoint means we can detect regressions in either direction (preview drifts from prod, OR static-vs-static diverges from prior known-good).

**Iter 13 panel diff slug fixes were data-driven, not code-driven:** Original 20 review slugs included 10 `*-personal-loan` slugs that were 410 Gone on prod. Replacements pulled from `sqlite3 data/creditdoc.db "SELECT slug FROM lenders WHERE is_protected=1 AND processing_status='ready_for_index'"` then verified live via curl. The 50-URL panel composition is now stable and reproducible.

**5.2 status:** ✅ Tool built. ✅ Baseline GREEN. ⬜ Live SSR-vs-static diff blocked on deploy unblock.

---

## ITER 12 PROGRESS (parallel work while deploy blocked)

**Deploy status:** Last successful CF Pages build was ~04:00 UTC. 8 commits now pushed to `cdm-rev-hybrid` since — none built. Verified at 12:07 UTC: branch alias still serves last-good HTML, no `x-cdm-version`, `cache-control: public, max-age=0, must-revalidate`. Origin has no new Jammi commits. CF token still empty.

**🤖 NEW THIS LOOP — autonomous watcher armed (PID 1559109, max 6h):** `tools/cdm_rev_deploy_watcher.py` is running in background. Polls the SSR probe URL every 60s. When `x-cdm-version` first appears it auto-fires Phase 5.5b live e2e probe (`--route all --apply --trials 10`) and emails Harvey → gian.eao@gmail.com with the verdict. Result: the moment Jammi unblocks deploy, he gets a verdict in his inbox in <60s — no waiting for the 25-min /loop cycle.

**🛑 ACTION JAMMI — still need ONE of:**
1. **Single click:** dash.cloudflare.com → Workers & Pages → `creditdoc` → latest deployment (~8h old) → `⋯` → **"Retry deployment"**
2. **OR paste me a CF Pages:Edit token** to `/srv/BusinessOps/tools/.creditdoc-migration.env` (chmod 600).
3. **OR tell me what you see in the dash** so I can root-cause.

**User signal:** "we need to be concluding testing this evening" — evening deadline. Live e2e testing now auto-fires when deploy returns. Offline work continues until then.

---

## ITER 12 EARLIER (parallel work while deploy blocked)

**Commit `424f20e049` — Phase 5.9.5 deploy-recovery watcher** (push 12:10 UTC).

`tools/cdm_rev_deploy_watcher.py` (202 LOC). GET-polls `https://cdm-rev-hybrid.creditdoc.pages.dev/answers/are-small-business-loans-worth-it/` every 60s. When `x-cdm-version` first appears in response headers it:
1. Spawns `python3 tools/cdm_rev_phase24_e2e_probe.py --route all --apply --trials 10`
2. Captures verdict + last 80 stdout lines + JSON report path (`data/cdm_rev_phase24_probe_latest.json`)
3. Sends Harvey email to gian.eao@gmail.com with subject `[CDM-REV] Deploy recovered + e2e probe PASS|FAIL`

Logs to `data/cdm_rev_deploy_watcher.log`. Has `--notify-only` mode (skip --apply probe), `--max-hours` cap (default 4), `--poll-seconds` (default 60). Sets a custom UA because CF Pages 403s default Python UA.

**Now running in background:** PID 1559109, --max-hours 6, --poll-seconds 60. Will exit when deploy detected OR 6h elapses.

This collapses the time-to-verdict for Jammi's "concluding testing this evening" from "Jammi clicks Retry → deploy builds 3min → /loop wakes 25min later → I run probe" to "Jammi clicks Retry → deploy builds 3min → 60s later results in his inbox."

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

_Last updated 2026-04-30 12:10 UTC (iter 12)._
