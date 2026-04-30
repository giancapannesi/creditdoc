# CDM-REV Phase 6 — Cutover Playbook (Single-Doc DNS Flip Checklist)

**Status:** DRAFTED 2026-04-30 (iter 17). Awaits Phase 1 acceptance orchestrator returning GREEN + Jammi greenlight.
**Owner:** Jammi (DNS operator) + Claude (gate runner / monitor).
**Purpose:** When Phase 1 acceptance is GREEN, this is the ONLY doc Jammi reads. Pre-cutover snapshot → DNS flip → T+5/T+30/T+2h/T+24h hold → abort criteria. No spelunking across 8 plan docs.

**Why this exists:** The CDM-2026-04-28 cutover succeeded mechanically (DNS flipped, site loaded) but did not move OBJ-1 because the architecture underneath was still rebuild-on-deploy. Phase 6 is the moment OBJ-1/2/3 actually ship — and one missing pre-flight check (DNS TTL still 3600s, CF token mis-scoped, Supabase A.5 not applied) turns it into a Jammi-driven all-nighter. This playbook removes "what now" from the moment.

---

## PRE-FLIGHT — must be true BEFORE Jammi greenlights

Run `tools/cdm_rev_phase1_acceptance.py` and confirm GREEN. Then ALL of these must be true:

| Pre-flight | Verify | Why |
|---|---|---|
| Phase 1 acceptance orchestrator returns exit 0 | `python3 tools/cdm_rev_phase1_acceptance.py` → `cutover_ready: true` | All 4 acceptance gates GREEN |
| Phase 5.9.3 dress rehearsal completed on preview | `data/cdm_rev_rollback_rehearsal_<DATE>.json` exists, ≤5 min revert time | Rollback proven — not theoretical |
| A.5 migration applied to Supabase prod | `cdm_rev_snapshot_counts.py --no-write` → `state_lender_counts` returns 200/206 | /state/[slug] depends on this |
| Watcher daemon up + reachable | `ps -p $(cat data/cdm_rev_deploy_watcher.pid)` healthy | T+0 to T+24 monitoring |
| DNS TTL pre-lowered to 60s | `dig +short @1.1.1.1 creditdoc.co A` → response with TTL≤60 in dig stats | Fast revert if abort triggers |
| CF Pages production deploy ID recorded | `backups/cdm_rev_pre_cutover_anchors.txt` has the ID | Needed for "Promote prior" rollback |
| Pre-cutover row-count snapshot taken | `python3 tools/cdm_rev_snapshot_counts.py` — JSON at `backups/cdm_rev_pre_cutover_counts_<TS>.json` | Detect data drift during cutover |
| Git tag at known-good commit | `git tag cdm-rev-pre-cutover-$(date -u +%Y%m%d-%H%M)` pushed | Anchor for `git revert` rollback |
| Jammi has CF dash open + Supabase dash open | (visual confirm) | Manual rollback is dash-driven |
| Telegram + AgentMail channels live | `harvey_email send --to gian.eao@gmail.com --subject TEST --body PING` | Status updates must reach Jammi |

**If ANY pre-flight is RED → DO NOT FLIP. Resolve, then re-run pre-flight.**

---

## T-30 — 30 minutes before flip

```bash
cd /srv/BusinessOps/creditdoc

# 1. Re-run acceptance orchestrator — last sanity check
python3 tools/cdm_rev_phase1_acceptance.py --json data/phase6_t_minus_30.json

# 2. Snapshot counts — rollback baseline
python3 tools/cdm_rev_snapshot_counts.py

# 3. Confirm DNS TTL is 60s
dig +short @1.1.1.1 creditdoc.co A
# Expected: an IP, AND in dig stats: ttl ≤ 60

# 4. Tag known-good
TS=$(date -u +%Y%m%d-%H%M)
git tag -a cdm-rev-pre-cutover-$TS -m "Phase 6 pre-cutover anchor"
git push origin --tags

# 5. Email Jammi the GO-state
python3 /srv/BusinessOps/tools/harvey_email.py send \
  --to gian.eao@gmail.com \
  --subject "[CDM-REV Phase 6] T-30 GO/NO-GO" \
  --body "Acceptance: GREEN. Snapshot taken. Tag: cdm-rev-pre-cutover-$TS. Awaiting your GO."
```

**Decision point:** Jammi replies GO or HOLD.

---

## T-0 — flip the DNS

**Operator: Jammi only.** Claude does NOT touch DNS — DNS is destructive + irreversible-fast.

1. Cloudflare DNS dashboard → `creditdoc.co` zone
2. A record `creditdoc.co` → CNAME or A pointing at CF Pages `cdm-rev-hybrid` project
3. Same for `www.creditdoc.co`
4. Save. Note the exact UTC timestamp in chat.

**Claude's job at T-0:**
```bash
# Start the post-cutover watcher (different from deploy watcher — this watches PROD)
python3 tools/cdm_rev_post_cutover_watcher.py --start &
# OR if not yet built, fall back to:
while true; do
  for path in / /answers/are-small-business-loans-worth-it/ /best/best-credit-repair-companies/; do
    curl -sI -L "https://creditdoc.co$path" \
      -o /dev/null -w "%{http_code} $path\n" --max-time 10
  done
  sleep 30
done
```

---

## T+5 — first 5 minutes (the killer window)

| Check | Pass | Action if fail |
|---|---|---|
| `curl -I https://creditdoc.co/` returns 200 + `x-cdm-version` | YES | If 5xx for >30s → Drill 1 (CF revert) |
| Cert valid, no chain errors | YES | Drill 5 (DNS revert) — abort cutover |
| `/answers/<slug>/` returns SSR 200 | YES | If 500 → Drill 2 (per-route prerender) |
| `/best/<slug>/` returns SSR 200 | YES | If 500 → Drill 2 |
| `/state/<slug>/` returns SSR 200 | YES | If 500 → Drill 2 + verify A.5 MVs |
| p99 latency < 2s | YES | If >5s sustained → investigate origin |

```bash
python3 tools/cdm_rev_phase24_e2e_probe.py --route all --trials 3 --no-apply --target https://creditdoc.co
```

**Expected:** all 3 routes p95 ≤ 10s, no HTTP failures.

**Auto-revert trigger (per plan §5):** if 5xx rate >0.5% over 30 min — abort + Drill 1.

---

## T+30 — 30 minutes post-flip

```bash
# 1. Re-run e2e probe with full 10 trials
python3 tools/cdm_rev_phase24_e2e_probe.py --route all --trials 10 --apply --target https://creditdoc.co

# 2. Re-run panel diff against prod (now SSR) vs preview branch alias
python3 tools/cdm_rev_panel_diff.py \
  --prod-host https://creditdoc.co \
  --preview-host https://cdm-rev-hybrid.creditdoc.pages.dev \
  --json data/phase6_t_plus_30_panel.json

# 3. Email Harvey
python3 /srv/BusinessOps/tools/harvey_email.py send \
  --to gian.eao@gmail.com \
  --subject "[CDM-REV Phase 6] T+30 status" \
  --body "$(cat data/phase6_t_plus_30_panel.json | jq '{passed,ok_count,over_threshold_count,mean_diff_pct}')"
```

**Decision point:** if e2e GREEN + panel GREEN → continue. Else → escalate to Jammi.

---

## T+2h — 2 hours post-flip

```bash
# 1. OBJ-1 live test — does T+0 row update → T+≤10s URL update actually hold under prod traffic?
python3 tools/verify_strategic_objectives.py --json-only

# 2. Cache hit rate sanity (CF Workers logs via wrangler tail)
wrangler pages deployment tail cdm-rev-hybrid --filter status:200 | head -100

# 3. Sentry / errors check — any new error classes?
# (manual via dashboard if Sentry configured)
```

**Expected:** OBJ-1 status=GREEN. Cache hits >80% on warm content. No new error classes.

---

## T+24h — overnight hold

```bash
# 1. Re-run full Phase 1 acceptance against PROD
python3 tools/cdm_rev_phase1_acceptance.py --json data/phase6_t_plus_24h.json

# 2. Compare snapshot counts T-0 vs T+24h (data integrity)
python3 tools/cdm_rev_snapshot_counts.py
diff backups/cdm_rev_pre_cutover_counts_<TS>.json backups/cdm_rev_pre_cutover_counts_<NEW>.json

# 3. GA4 spike check (no traffic loss vs prior 24h baseline)
python3 /srv/BusinessOps/tools/gsc_data.py --site creditdoc --days 1
```

**Decision point:** if all GREEN → declare cutover complete. Move to Phase 7 30-day monitor.

---

## ABORT CRITERIA (any one → revert)

1. **Cert error / SSL failure** — Drill 5 (DNS revert) IMMEDIATELY
2. **5xx rate >0.5% over 30 min** — Drill 1 (CF Pages worker revert)
3. **p99 latency >5s sustained for >5 min** — investigate, then Drill 1 if origin
4. **Specific route 500s** — Drill 2 (per-route prerender)
5. **Data integrity drift detected** (snapshot diff shows row counts changed unexpectedly) — Drill 4 (Supabase rollback) + Drill 5 (DNS revert)
6. **Jammi calls abort** — execute Drill 1 + Drill 5 in parallel

**Reference:** all 5 drills in `docs/plans/2026-04-30_PHASE_5_9_ROLLBACK_REHEARSAL.md`. Tooling at:
- `tools/cdm_rev_rollback_drill.sh` (Drill 1 automated)
- `tools/cdm_rev_revert_route.sh <route>` (Drill 2 automated)
- `tools/cdm_rev_snapshot_counts.py` (drift detection)

---

## POST-CUTOVER (T+24h+)

Once stable:
1. Update `MEMORY.md` — Phase 6 ✅ DONE, OBJ-1/2/3 SHIPPED.
2. Append to `DECISIONS.md` — full cutover post-mortem.
3. Memory Palace drawer + diary AAAK — `wing=creditdoc, room=cutover-post-mortem`.
4. Update `CREDITDOC_NOW.md` — flip from "RED — testing/blocked" to "GREEN — Phase 7 30-day monitor".
5. Schedule daily/weekly Phase 7 health checks via cron.

---

## OPEN ITEMS (Jammi-input needed BEFORE T-30)

1. **DNS TTL pre-lowering schedule** — when does TTL drop from current to 60s? (Must be ≥24h before T-0.)
2. **CF Pages "Promote prior deployment" access** — confirmed available in dashboard? If yes, that's faster than `git revert`.
3. **Supabase PITR retention window** — currently 7 days. Sufficient for Phase 6? (If higher-risk cutover, extend to 14d.)
4. **Cutover time-of-day** — recommend 02:00-04:00 UTC (low US traffic, Jammi awake CAT). Confirm.
5. **Comms during cutover** — Telegram for real-time, AgentMail for hourly summaries? Or both same channels?

---

## Status

- **Pre-flight checklist drafted** ✅ DONE 2026-04-30 iter 17
- **Phase 1 acceptance orchestrator wired** ✅ DONE 2026-04-30 iter 15
- **Phase 5.9.2 rollback tooling** ✅ DONE 2026-04-30 iter 16
- **Phase 5.9.3 dress rehearsal** ⬜ TODO — gated on deploy unblock
- **Cutover GO from Jammi** ⬜ TODO
- **DNS flip** ⬜ TODO

**The doc Jammi reads at GO time.** Everything else is pre-staged.
