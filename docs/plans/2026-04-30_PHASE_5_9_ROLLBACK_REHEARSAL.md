# CDM-REV Phase 5.9 — Rollback Rehearsal Playbook

**Status:** DRAFTED 2026-04-30 (iter 9). Awaits dress-rehearsal once CF Pages deploy unblocks.
**Owner:** Claude (with Jammi greenlight per step).
**Target:** ≤ 5 min revert from "broken cutover" → "last known-good production".
**Why this exists:** Phase 6 cutover (DNS flip) is gated on a rehearsed rollback. If a regression appears T+0 to T+24h post-cutover, every minute we're rolling back blind is a minute users see broken pages or stale data. This doc removes the "what now" from rollback and reduces it to copy-paste.

---

## What CAN be rolled back (and how fast)

| Layer | Failure mode | Rollback action | Wall-time | Risk |
|---|---|---|---|---|
| CF Pages adapter | Worker JS bug, 5xx loop, OOM | Revert commit on `cdm-rev-hybrid` → push → wait for deploy | 2-4 min once deploy works | Low — rollback commit is a known-good build |
| Astro SSR routes | One route regresses (e.g. /answers/[slug] returns 500) | Per-route `prerender = true` revert + redeploy | 2-4 min | Low — prior-static HTML is in git |
| Middleware cacheWrap | Cache poisoning, version-key broken, every miss | Single-line `return next()` early-return at top of `onRequest` | 2-4 min | Low — bypasses cache, doesn't break renders |
| Supabase migration A.5 | MV refresh CPU pegging DB, anon SELECT exposing wrong rows | Documented rollback SQL block in migration header | < 1 min | Medium — DROP MV is instant; DROP COLUMN on `lenders` rewrites all rows |
| DNS flip (Phase 6) | Cert mismatch, edge cache stuck, propagation gap | Revert DNS record → wait propagation | 5-30 min | High — depends on TTL set at flip time |
| Supabase data | Bad bulk write (N rows mutated in error) | Point-in-time recovery via Supabase dashboard | 10-30 min | High — coarse-grained, restores entire DB to a timestamp |

---

## Pre-cutover snapshot (capture once, just before Phase 6)

Run BEFORE any DNS flip. These are the targets a rollback returns to.

```bash
# Tag the last known-good commit
git tag -a cdm-rev-pre-cutover-$(date -u +%Y%m%d-%H%M) -m "CDM-REV Phase 6 pre-cutover anchor"
git push origin --tags

# Record CF Pages production deploy ID (needed for CF API rollback)
# (requires CF token populated)
echo "Production deploy ID: <PASTE FROM DASHBOARD>" >> backups/cdm_rev_pre_cutover_anchors.txt

# Record Supabase project version + last-applied migration
psql "$SUPABASE_DB_URL" -c "SELECT name, applied_at FROM supabase_migrations.schema_migrations ORDER BY applied_at DESC LIMIT 5"

# Snapshot lenders + answers + listicles row counts (rollback-detection baseline)
python3 tools/cdm_rev_snapshot_counts.py > backups/cdm_rev_pre_cutover_counts.json
```

---

## Drill 1 — CF Pages worker rollback (most likely scenario)

**Trigger:** any one of:
- `/answers/[slug]` or `/best/[slug]` returns 5xx for > 30 sec
- p99 latency on a route exceeds 2 sec for > 5 min
- middleware `x-cdm-cache: BYPASS-*` appears on > 5% of requests (indicates version-probe broken)

**Rollback (target: 4 min):**
```bash
cd /srv/BusinessOps/creditdoc

# 1. Identify the bad commit (HEAD at time of cutover-rollback decision)
BAD_HEAD=$(git rev-parse HEAD)
GOOD_TAG="cdm-rev-pre-cutover-<TS>"

# 2. Revert the bad commit chain back to the anchor
git revert --no-edit $GOOD_TAG..HEAD
git push origin cdm-rev-hybrid  # OR main, depending on cutover branch

# 3. Wait for CF Pages to build the revert commit
# Monitor via:
while true; do
  curl -sI -L https://creditdoc.co/answers/are-small-business-loans-worth-it/ | grep -E "(HTTP|x-cdm-version|cf-cache)"
  sleep 10
done
# Stop when x-cdm-version disappears AND HTTP 200

# 4. Verify last-known-good
python3 tools/cdm_rev_phase24_e2e_probe.py --route all --trials 3 --no-apply
```

**If CF Pages build fails on the revert:** drop to Drill 2 (per-route disable).

---

## Drill 2 — Per-route prerender revert (single-route regression)

If only one SSR route is broken (e.g. /answers/[slug] but /best/[slug] is fine), revert that route to prerendered HTML.

```astro
---
// Revert: change `export const prerender = false` → `export const prerender = true`
// at top of src/pages/answers/[slug].astro
// Astro will rebuild the static page from src/content/answers/<slug>.json
// (which is still synced from DB by the daily cron).
export const prerender = true;
// ... rest of frontmatter must read from local JSON, NOT runtime fetch ...
---
```

Then `npm run build && git commit -am "EMERGENCY: revert /answers/[slug] to prerender" && git push`.

**Caveat:** edits to that route's content go back to needing a `git push` until re-fixed (OBJ-1 forfeit for that route only).

---

## Drill 3 — Middleware cacheWrap kill-switch

If cacheWrap is the failure mode (poisoned cache, version-probe broken, every request misses), bypass without removing.

```typescript
// src/middleware.ts — add at top of onRequest, FIRST line:
export const onRequest = defineMiddleware(async (context, next) => {
  // EMERGENCY: bypass cacheWrap. Renders are still fine.
  return next();
  // ... existing body ...
});
```

Commit + push. Pages still SSR but every request renders fresh — slower but correct. OBJ-1 ≤ 10s remains green via Astro response `cache-control` headers (max-age=86400) — just no content-version invalidation, so a row update takes up to 24h to propagate (same as pre-cacheWrap behavior). Acceptable degradation.

---

## Drill 4 — Supabase migration A.5 rollback

Rollback SQL is in `supabase/migrations/2026-04-30_cdm_rev_a5_state_aggregates.sql` header, copy-paste-ready:

```sql
BEGIN;
DROP MATERIALIZED VIEW IF EXISTS state_city_lender_counts;
DROP MATERIALIZED VIEW IF EXISTS state_lender_counts;
DROP FUNCTION IF EXISTS refresh_state_aggregates();
ALTER TABLE lenders DROP COLUMN IF EXISTS state_abbr;
ALTER TABLE lenders DROP COLUMN IF EXISTS city_norm;
NOTIFY pgrst, 'reload schema';
COMMIT;
```

**Risk note:** `ALTER TABLE lenders DROP COLUMN` on 26K rows IS instant in Postgres (it's a metadata-only op when the column has no triggers/indexes), but the index drop cascades. Wall time observed in dev: < 2 sec for both columns + 2 indexes. PostgREST schema reload picks up within 5 sec.

**Pre-rollback:** if /state/[slug].astro is converted to use these helpers, ALSO revert that route first via Drill 2 — otherwise it 500s the moment the columns disappear.

---

## Drill 5 — Full DNS revert (worst case, Phase 6 only)

```bash
# 1. Cloudflare DNS dashboard → creditdoc.co A record
#    Change CNAME target back to the prior provider (Vercel? CF Pages production project?)
# 2. Wait for propagation (TTL was set short pre-cutover — should be 60s)
# 3. Verify
dig +short creditdoc.co
curl -sI https://creditdoc.co/ | head -5
# 4. Notify Jammi via Telegram + AgentMail
```

**Hard truth:** if DNS revert is needed, the migration is dead for at least 30 days (Google takes ~25 days to flush CrUX field data per `creditdoc_site_age_and_seo_timeline.md`). Plan post-mortem the same hour.

---

## Rehearsal procedure (DRESS REHEARSAL — schedule before Phase 6)

1. Greenlight from Jammi for a 30-min window where preview URL is the rehearsal target (NOT production).
2. On `cdm-rev-hybrid`, intentionally introduce a known-bad commit (e.g. throw in middleware.ts).
3. Confirm preview URL returns 5xx.
4. Run Drill 1 against the preview URL. Time wall-clock from `git revert` to first 200.
5. **Pass criterion:** ≤ 5 min from decision-to-revert → first known-good response.
6. Repeat Drills 2 and 3 once each on preview.
7. Drill 4 (Supabase rollback): apply A.5 to preview Supabase branch, then run rollback. Time both directions.
8. Drill 5 (DNS): NOT rehearsed live. Instead: verify TTL is set ≤ 60s in cutover commit and verify dashboard access. Document the operator (Jammi only).
9. Write rehearsal results to `data/cdm_rev_rollback_rehearsal_$(date +%Y%m%d).json`.
10. Sign off: `verify_strategic_objectives.py` after rehearsal — should still be GREEN.

---

## Tooling needed (to be built before rehearsal)

- [ ] `tools/cdm_rev_snapshot_counts.py` — capture pre-cutover row counts for lenders/answers/listicles + last updated_at per table. Output JSON.
- [ ] `tools/cdm_rev_rollback_drill.sh` — automated wrapper around Drills 1+3 with timing capture. Wraps `git revert`, `git push`, polling loop, and writes JSON.
- [ ] `tools/cdm_rev_revert_route.sh <route_name>` — flips `prerender = false` → `true` in a single Astro page, commits, pushes. Idempotent (no-op if already reverted).

These are NOT critical-path for daily operation — just for the rehearsal. Estimate: 90 min total to write all three.

---

## Open questions for Jammi

1. **DNS TTL pre-cutover:** confirm we set it to 60s (or 300s) at least 24h before Phase 6 so propagation on revert is fast. Currently unknown.
2. **CF Pages account-level rollback access:** is there a "Promote prior deployment to production" button? If yes, that's faster than `git revert + push`. (I can't see the dashboard.)
3. **Supabase point-in-time recovery window:** what's the project's PITR retention? 7 days standard. Confirm or upgrade before Phase 6.
4. **Notification channel during a rollback:** Telegram + AgentMail to Jammi only? Or also a status-page update if/when one exists?
5. **Auto-revert wiring:** plan §5 mentions "auto-revert on >0.5% 5xx in 30 min" — that needs a watcher daemon. Do we want one, or human-driven revert only?

---

## Status

- **5.9.1** — Playbook drafted (this doc) ✅ DONE 2026-04-30
- **5.9.2** — Tooling built (3 scripts above) ⬜ TODO
- **5.9.3** — Dress rehearsal on preview ⬜ TODO (gated on CF deploy unblock + tooling)
- **5.9.4** — Open-questions answered with Jammi ⬜ TODO

**Acceptance gate:** all 4 sub-items DONE before Phase 6 cutover greenlight is requested.
