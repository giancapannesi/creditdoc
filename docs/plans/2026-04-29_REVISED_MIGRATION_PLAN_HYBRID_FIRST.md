# 🎯 STRATEGIC OBJECTIVES — READ FIRST, RE-READ BEFORE EVERY DECISION

**Jammi's verbatim brief, 2026-04-29:** *"the entire point was to build something that can be updated on the fly - something that can fit regulatory scrutiny with security and something that can grow."*

| # | Objective | Concrete success criterion | Status (2026-04-29) |
|---|---|---|:---:|
| **OBJ-1** | **Update on the fly** — a single content edit goes live in seconds without rebuilding 17K+ pages | DB-row update at T+0 → URL serves new HTML at T+≤10s globally. No `git push`. No full rebuild. | 🔴 RED |
| **OBJ-2** | **Regulatory scrutiny / security** — GLBA-roadmap-ready, GDPR/CCPA-defensible | RLS on every Supabase table; `audit_log` of every write (who/when/what/old/new); DPAs signed (CF + Supabase); scoped tokens only; encryption at rest; cookie consent; Privacy + Terms pages | 🟡 AMBER |
| **OBJ-3** | **Grow** — scales beyond 21K rows, supports new product surfaces, no single-vendor lock-in | New surface (e.g. `/api/lender/{id}` JSON, `/applications/[id]` user-state route) ships in <1 day, <50 LOC, no infra rewrite | 🟡 AMBER |

## 🛑 RULE OF FORFEIT (NON-NEGOTIABLE)

If any plan revision, scope cut, or "let's just ship it" proposal would ship with one of OBJ-1/2/3 still red, **the plan is wrong, not the objective**. Cut scope from elsewhere. Never from these.

This rule exists because **CDM-2026-04-28 was executed end-to-end without addressing OBJ-1**. It shipped `output: 'static'` to a new host (Cloudflare instead of Vercel) — same rebuild-on-every-deploy problem. Two days of Jammi's personal work — credit card, account creation, DNS prep, R2 bucket provisioning, 14,384 logo uploads — did not move OBJ-1 one millimetre. **This plan exists so that doesn't recur.**

## ✅ ENFORCEMENT (BUILT INTO THIS PLAN)

1. **Section A.6 gate** — before each phase ships, run `creditdoc/tools/verify_strategic_objectives.py` (built in Phase 0.5). Three checks: OBJ-1 update-latency probe, OBJ-2 audit_log row coverage, OBJ-3 surface-add probe. Phase blocked if any objective regressed. JSON output posted to chat.
2. **Section D.4 gate** — Memory Palace per-step drawer count must equal step count for the phase. Verifier blocks the next phase if drawers are missing. CDM-2026-04-28 promised this and shipped 1 of ~30 step drawers. This plan enforces it via tool, not just instruction.
3. **North-star pin** — `/root/.claude/projects/-srv-BusinessOps/memory/creditdoc_north_star.md` is pinned to the top of `MEMORY.md`, which loads into every session. Every CreditDoc agent reads OBJ-1/2/3 before any other context.

---

# CreditDoc — REVISED MIGRATION PLAN (Hybrid-First)

**Plan ID:** CDM-REV-2026-04-29
**Supersedes:** `CreditDoc Project Improvement/2026-04-28_PROJECT_PLAN_CLOUDFLARE_MIGRATION.md` (CDM-2026-04-28) for everything from Phase 5 (Cutover) onwards. Phases 1, 2, 4, 4.6 of CDM-2026-04-28 stay valid as **foundation** and are folded into Phase 0 of this plan.
**Created:** 2026-04-29 cutover morning (post-mortem of CDM-2026-04-28 + recovery)
**Owner:** Jammi (decisions) + main Claude session (execution under loop authority)
**Branch:** new branch `cdm-rev-hybrid` off `main` (NOT `arch-overhaul`, that is owned by parallel window).
**Mirror:** `creditdoc/docs/plans/2026-04-29_REVISED_MIGRATION_PLAN_HYBRID_FIRST.md`. The two files are kept identical. This project-folder copy is the primary reference for Jammi's strategy library; the creditdoc-repo copy is the in-tree reference for the engineering work.

---

## SECTION A — APPROVAL GATES (Jammi must say YES to each before execution)

| Gate | What | Status |
|---|---|---|
| A.1 | Pause CDM-2026-04-28 cutover scheduled this morning. Vercel stays live as production for ~7-14 calendar days while hybrid layer is built and tested. | ☐ |
| A.2 | Architecture change: switch from `output: 'static'` to `output: 'hybrid'` with `@astrojs/cloudflare` adapter. Per-route prerender flag. CF KV + Cache API for revalidation. | ☐ |
| A.3 | Cost: $0 incremental over CDM-2026-04-28. CF Pages free tier covers Workers invocations until ≥100K req/day. Supabase Free covers reads. KV is free up to 100K reads/day. | ☐ |
| A.4 | Loop authority: I work autonomously between wakes (30-90 min cadence active phases). I commit to the new branch only — no merges to `main`, no DNS changes, no Vercel changes without Jammi explicit "go". | ☐ |
| A.5 | Memory protocol: per-step Memory Palace write is **mandatory**, not optional. CDM-2026-04-28 promised this and shipped 1 of ~30 step drawers. This plan enforces it via Section D + a verifier script (D.4). | ☐ |
| A.6 | Goal-verification gate (NEW): before each phase ships, run `tools/verify_strategic_objectives.py` and post the OBJ-1/2/3 deltas to chat. Phase blocked if any objective regressed. | ☐ |
| A.7 | Cutover prerequisites: (1) hybrid SSR works on preview, (2) revalidation API < 10s end-to-end measured, (3) audit_log captures 100% of writes verified, (4) HTML diff < 0.1% on 50-URL panel vs Vercel current, (5) Jammi explicit greenlight + 24h notice + dress rehearsal. | ☐ |

---

## SECTION B — PHASES

### Phase 0 — STABILIZE (today, 2026-04-29)
**Goal:** stop digging. Convert CDM-2026-04-28 outputs into a foundation we can build on.
**OBJ moved:** none directly. Buys time without losing what's already provisioned.

- 0.1 PAUSE cutover. Edit `CREDITDOC_NOW.md` and `2026-04-29_CUTOVER_MORNING_CHECKLIST.md` to PAUSED state. Neither A nor B SSL handover initiated until hybrid layer ready.
- 0.2 Confirm Vercel production untouched: `curl -sL -o /dev/null -w "%{http_code}\n" https://creditdoc.co/` → 200; deploy `766629ddb1` still READY.
- 0.3 Lock CDM-2026-04-28 phases that stay valid: Phase 1 (CF/Supabase/R2 accounts), Phase 2 (data migration to Postgres + R2), Phase 4 cache headers, Phase 4.6 health-check poller + CWV baseline. Mark Phase 3 (build pipeline) and Phase 5 (cutover) as superseded.
- 0.4 Inventory snapshot: write `creditdoc/data/exports/cdm_rev_inventory_2026-04-29.md` listing what's built, what's wired, what's wasted.
- 0.5 Build `creditdoc/tools/verify_strategic_objectives.py`. Three checks: (a) update-on-fly latency end-to-end probe (preview only), (b) audit_log row-coverage check, (c) growth-readiness probe (does the data layer support a new route added in <50 LOC). Returns OBJ-1/2/3 traffic-light JSON. Used as goal-verification gate before each phase ship.

**Acceptance gate:** OBJ inventory committed; Vercel production verified untouched; `verify_strategic_objectives.py` runnable.
**Memory write (mandatory):** `mempalace_add_drawer wing=creditdoc room=migration` with verbatim phase result.

### Phase 1 — HYBRID CONVERSION (Days 1-3)
**Goal:** make a single live route serve from Cloudflare Workers SSR with sub-second TTFB and instant content updates.
**OBJ moved:** OBJ-1 (proves on-the-fly is achievable on this stack).

- 1.1 New branch `cdm-rev-hybrid` off `main`. No work on `arch-overhaul`.
- 1.2 `npm i -D @astrojs/cloudflare`. Update `astro.config.mjs`: replace `output: 'static'` with `output: 'hybrid'`, add `adapter: cloudflare({ mode: 'directory' })`, drop the Vercel adapter import (Vercel stays live via the unchanged production deploy on `main`).
- 1.3 Pick one high-churn route as pilot: `/review/[slug]`. Add `export const prerender = false;` to its page module. Wire it to read from Supabase Postgres at request time using the existing helper. Body JSON read from R2 by R2 key embedded in the catalog row.
- 1.4 Wire CF Cache API in front of the SSR handler. Cache key includes slug + content-version (a monotonic int from `lenders.updated_at`). 24h max-age, immutable per version.
- 1.5 Local dev: `wrangler pages dev` for a working SSR preview on port 8788.
- 1.6 Deploy to CF Pages preview: `wrangler pages deploy dist`. Smoke test 20 lender slugs SSR-rendered + cached.
- 1.7 Measure: TTFB cold, TTFB warm, build time (should drop dramatically since /review/* no longer prerendered).

**Acceptance gate:**
- (a) Build time for /review/* prerender = 0s (route is SSR).
- (b) TTFB warm < 100ms p95 on the 20 sample slugs.
- (c) `verify_strategic_objectives.py` returns OBJ-1 = GREEN on the pilot route.
- (d) HTML diff vs Vercel < 0.1% on 20 sample slugs.

**Memory write (mandatory):** `mempalace_add_drawer wing=creditdoc room=migration` with verbatim Phase 1 result + measurements.

### Phase 2 — REVALIDATION + DB WRITE WIRING (Days 3-4)
**Goal:** writing one DB row makes the cached HTML obsolete in <10s globally.
**OBJ moved:** OBJ-1 (closes the "on-the-fly" loop end-to-end), OBJ-3 (foundation for future product surfaces).

- 2.1 Build `/api/revalidate` Worker endpoint. POST with bearer token. Body: `{type: 'lender', slug: 'foo'}` or `{tag: 'category-personal-loans'}`. Action: bump content-version key in KV; CF Cache API automatically misses on next request because cache key changed.
- 2.2 KV namespace `creditdoc-versions`. Two access patterns: per-slug version int, per-tag version int. Workers binding wired to the SSR handler (1.4) for read, to revalidate handler (2.1) for write.
- 2.3 Wire `tools/creditdoc_db.py update_lender()` to POST `/api/revalidate` after each successful DB write. Token loaded from `tools/.cdm_revalidate_token` chmod 600.
- 2.4 End-to-end probe: edit a lender row via `creditdoc_db.py update_lender(slug, fields)`, time the round-trip from DB write to globally-cached new HTML serving. Target ≤ 10s p95.

**Acceptance gate:** end-to-end revalidation probe ≤ 10s p95 over 20 trials. `verify_strategic_objectives.py` OBJ-1 = GREEN end-to-end.
**Memory write (mandatory):** verbatim probe results + token rotation procedure.

### Phase 3 — COMPLIANCE BASELINE (Days 4-6)
**Goal:** the app is GLBA-roadmap-ready and GDPR/CCPA-defensible TODAY, not at "later."
**OBJ moved:** OBJ-2 (this is the entire phase).

- 3.1 `audit_log` table in Supabase: id, ts, actor, action, table_name, row_pk, old_json, new_json. RLS so only service-role can read/write. Triggers on `lenders`, `cluster_answers`, `affiliate_gates`, every write-target table.
- 3.2 RLS audit: for every public-readable table, RLS policy explicitly enumerates allowed columns. Sensitive columns (internal scores, raw scrape data) get a separate view with no RLS bypass.
- 3.3 DPA confirmation: pull DPA PDF from Cloudflare and Supabase, save to `creditdoc/docs/compliance/`, file a Memory Palace drawer with the SHA256 of each PDF + signing date.
- 3.4 Scoped token register: `creditdoc/docs/compliance/token_register.md` lists every token in use, its scope, where stored, rotation cadence, last rotated. Currently: CF Global API Key, CF account-scoped tokens, Supabase service-role, R2 access keys, GSC service account, GA4 service account, revalidate token. Rotation cadence: 90 days for application tokens, on-demand for CF Global API Key.
- 3.5 Cookie banner. Astro component. Shows once per session for new visitors. Stores consent in localStorage. Blocks GA4 + any future ad pixels until consent given. Privacy policy page links from banner.
- 3.6 `/legal/privacy` and `/legal/terms` pages. Existing copy where present; placeholder + lawyer-review item flagged where missing.
- 3.7 Encryption at rest verified (Supabase Postgres = on by default, R2 = on by default; document the verifications).

**Acceptance gate:** `verify_strategic_objectives.py` OBJ-2 = GREEN. All 7 sub-items have a Memory Palace drawer + a doc in `creditdoc/docs/compliance/`.
**Memory write (mandatory):** per sub-item.

### Phase 4 — GROWTH-READINESS PROBE (Days 6-7)
**Goal:** prove the architecture can absorb a new product surface without rewriting infrastructure.
**OBJ moved:** OBJ-3.

- 4.1 Add a throwaway probe route: `/api/lender/[slug].json` that serves the same data as `/review/[slug]` but as JSON. SSR via the same Cloudflare adapter. Same Cache API + KV revalidation pattern.
- 4.2 Measure: total LOC added, build-time delta, TTFB. Target: < 50 LOC, no build-time regression, TTFB parity.
- 4.3 Document: `creditdoc/docs/architecture/extending_the_app.md` — "how to add a new SSR route" in 6 steps.
- 4.4 Decommission the throwaway probe route (revalidation tag flush + delete).

**Acceptance gate:** `verify_strategic_objectives.py` OBJ-3 = GREEN. Doc committed.

### Phase 5 — NEW CUTOVER GATES (Days 7-8)
**Goal:** cutover prerequisites for the hybrid architecture (different from CDM-2026-04-28's static-cutover gates).
**OBJ moved:** none (gate work). But: cutover blocked unless OBJ-1/2/3 all GREEN.

- 5.1 Convert remaining high-churn routes: `/answers/[slug]`, `/best/[slug]`, `/state/[slug]`. SSR with same Cache API + KV pattern. Marketing pages stay prerendered.
- 5.2 Full preview rebuild on `cdm-rev-hybrid`. Verify: 17K+ static pages still render, dynamic routes serve via Workers. Build time target: < 5 min (vs 36 min for CDM-2026-04-28's full static).
- 5.3 50-URL HTML diff vs current Vercel production. < 0.1% byte delta.
- 5.4 Health-check poller (reused from CDM-2026-04-28).
- 5.5 Indexing API push (reused).
- 5.6 PSI baseline regression: mobile ≥ 0.77, desktop ≥ 0.98.
- 5.7 Revalidation latency test under load (1000 sequential edits). Target p99 ≤ 30s.
- 5.8 Audit log coverage test: forced-write of 100 rows; verify 100/100 have audit_log entries.
- 5.9 Rollback wrapper rehearsed and timed (target ≤ 5 min revert).
- 5.10 Goal-verification gate run. All 3 = GREEN. Posted to chat.

**Acceptance gate:** all 10 sub-items pass. Jammi explicit "go" + 24h notice + dress rehearsal scheduled.

### Phase 6 — CUTOVER (Day 8 or later, Jammi-greenlit only)
**Goal:** flip DNS, watch, hold.
**OBJ moved:** ships OBJ-1/2/3 to production.

(Reuse CDM-2026-04-28 Phase 5 mechanics: SSL Option A or B, T-30/T-0/T+5/T+30/T+2hr/T+24hr sequence, auto-revert on >0.5% 5xx in 30 min, manual rollback on cert errors, etc.)

### Phase 7 — 30-DAY MONITOR + POST-MORTEM (Day 8 to Day 38)
- Daily GSC checks. Weekly comparison vs Apr 22-28 baseline. CrUX field data settles ~Day 25.
- Final post-mortem written to template at `_TEMPLATE_PROJECT_POSTMORTEM.md`.
- Goal-verification gate run weekly during this period.

---

## SECTION C — LOOP PROTOCOL

Same as CDM-2026-04-28. I work autonomously in `/loop`. Wake cadence 30-90 min during active phases, 4-12h during compliance/monitor phases. NEVER commit to `main`, NEVER touch DNS, NEVER spend without Jammi in chat.

Difference from CDM-2026-04-28: each loop iteration ends with a **mandatory** Memory Palace drawer write (Section D) AND a **mandatory** `tools/verify_strategic_objectives.py` run posted to chat.

---

## SECTION D — MEMORY PROTOCOL (HARDENED)

Per CLAUDE.md RULE 0. Per CDM-2026-04-28 Section D.1. **This time it actually happens.**

- D.1 At the end of EVERY step (1.1, 1.2, 2.1, 2.2, etc., not just at end of phase): `mempalace_add_drawer wing=creditdoc room=migration` with verbatim findings (decisions, root causes, working solutions, measurements).
- D.2 At the end of EVERY loop iteration: `mempalace_diary_write` with one-line AAAK summary.
- D.3 At the end of EVERY phase: append to `DECISIONS.md`, update `MEMORY.md` north-star pointer, update `CREDITDOC_NOW.md`.
- D.4 NEW — verifier: `creditdoc/tools/verify_memory_protocol.py` greps Memory Palace via `mempalace_search wing=creditdoc room=migration` and counts drawers by step. If a phase ends without one drawer per sub-step, the next phase is blocked. Run as an explicit gate in the goal-verification script.

If D.1-D.4 are skipped, the next agent will not find this work, and we will rebuild it badly. The CDM-2026-04-28 incident proved this.

---

## SECTION E — COMMIT PROTOCOL

- Branch: `cdm-rev-hybrid` only. Off `main`. NEVER `arch-overhaul`.
- One conceptual change per commit. Reference plan section ID: `[CDM-REV §1.3] enable hybrid mode for /review/[slug]`.
- No force-push. No merge to `main` until Phase 5 gate passes + Jammi explicit go.
- Pre-commit: ruff + tsc + verify_strategic_objectives.py (must not regress).

---

## SECTION F — LOG CHECKS

Every loop iteration:
- `git log --oneline -10` on creditdoc + creditdoc-arch (so I see if parallel window touched something).
- `crontab -l` (no surprise crons).
- `git diff main...cdm-rev-hybrid --stat` (so I see what I've been doing).

---

## SECTION G — RISK REGISTER

| ID | Risk | Mitigation |
|---|---|---|
| R-1 | Hybrid mode breaks SSG fallback for marketing pages | Per-route `prerender` flag explicit; smoke 50 marketing URLs after every Phase 1+ change |
| R-2 | Cache API + KV revalidation gets stuck (stale HTML served) | Probe in Phase 2.4 + load test in 5.7. KV TTL safety net at 24h. |
| R-3 | Workers cold-start adds latency | Measured in 1.7. CF Workers cold start typically <50ms; tolerate. |
| R-4 | Audit log misses writes that go around `creditdoc_db.py` | Postgres triggers, not application-level audit. Trigger fires regardless of caller. |
| R-5 | Goal drift again | OBJ-1/2/3 verifier in 0.5 + Section A.6 gate before every phase. |
| R-6 | Memory protocol drift again | D.4 verifier blocks next phase if drawer count < step count. |
| R-7 | Parallel-window collision (`arch-overhaul`) | Branch isolation `cdm-rev-hybrid`. Memory note `project_creditdoc_arch_overhaul_parallel.md` already in place. |
| R-8 | Vercel ToS / cap re-emerges during 7-14 day overlap | Phase 0.2 verifies Vercel still healthy. If Vercel hard-caps mid-build, plan accelerates Phase 5. |
| R-9 | "Just ship the static cutover, fix it later" pressure | Section 0 forfeit rule (top of this doc). Section A.7 cutover prerequisites. Goal-verification gate is the technical control. |

---

## SECTION H — SOP NOTES

- This plan structure (strategic objectives at top, then Section A approval gates, Sections B-G phases/protocols, Section H SOP notes) becomes the BusinessOps standard for any project where a prior plan failed a goal-verification check.
- Every future plan starts with the **strategic objectives at the very top** stating verbatim founder ask + concrete success criteria. If a phase doesn't move at least one objective, it doesn't ship.
- Every plan has a goal-verification script. Cheap to write, expensive to skip.
- Every plan has a memory verifier. Memory Palace drift is silent until you go looking.

---

## CROSS-REFERENCES

- Original CDM-2026-04-28 plan (foundation, partially superseded): `CreditDoc Project Improvement/2026-04-28_PROJECT_PLAN_CLOUDFLARE_MIGRATION.md`
- Incident report (Apr 28 off-plan merge + token fiasco): `CreditDoc Project Improvement/2026-04-28_INCIDENT_REPORT_OFF_PLAN_MERGE_AND_TOKEN_FIASCO.md`
- Original arch-overhaul plan (parallel window, do not touch): `creditdoc/docs/plans/2026-04-18-architecture-overhaul.md`
- Live state: `creditdoc/CREDITDOC_NOW.md`
- Next concrete actions: `creditdoc/CREDITDOC_NEXT.md`
- North-star memory (pinned to top of MEMORY.md): `/root/.claude/projects/-srv-BusinessOps/memory/creditdoc_north_star.md`
- Memory Palace wing/room: `creditdoc/migration`
- Cutover-morning checklist (now SUPERSEDED): `CreditDoc Project Improvement/2026-04-29_CUTOVER_MORNING_CHECKLIST.md`
- SOP template: `CreditDoc Project Improvement/_TEMPLATE_PROJECT_POSTMORTEM.md`
- In-tree mirror of this plan: `creditdoc/docs/plans/2026-04-29_REVISED_MIGRATION_PLAN_HYBRID_FIRST.md`
