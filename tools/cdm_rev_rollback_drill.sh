#!/usr/bin/env bash
# CDM-REV Phase 5.9.2 — automated rollback drill (Drill 1).
#
# Times the wall-clock from `git revert` decision → first known-good response
# at the rollback-target URL. Captures JSON to data/cdm_rev_rollback_drill_<TS>.json.
#
# Usage:
#   tools/cdm_rev_rollback_drill.sh --anchor <good-tag-or-sha> --probe-url <url> [--branch BRANCH] [--dry-run]
#
# Example dress rehearsal:
#   tools/cdm_rev_rollback_drill.sh \
#     --anchor cdm-rev-pre-cutover-20260430-1200 \
#     --probe-url https://cdm-rev-hybrid.creditdoc.pages.dev/answers/test-slug/ \
#     --branch cdm-rev-hybrid
#
# Pass criterion: total_seconds <= 300 (5 min from decision-to-revert → 200 OK).
#
# What it does:
#   1. Capture pre-revert state of probe URL (status, x-cdm-version, body hash)
#   2. git revert <anchor>..HEAD with --no-edit (creates revert commits)
#   3. git push to <branch>
#   4. Poll probe URL every 5s with 8min timeout
#   5. Stop polling when state diverges from pre-revert (status changes,
#      x-cdm-version disappears, OR body hash changes)
#   6. Write JSON report
#
# Exit codes:
#   0 = drill complete, pass criterion met
#   1 = bad args
#   2 = git operation failed
#   3 = probe-url never recovered within timeout
#   4 = pass criterion exceeded (>5 min)

set -euo pipefail

DRY_RUN=0
ANCHOR=""
PROBE_URL=""
BRANCH=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --anchor) ANCHOR="$2"; shift 2 ;;
    --probe-url) PROBE_URL="$2"; shift 2 ;;
    --branch) BRANCH="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    *) echo "unknown arg: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$ANCHOR" || -z "$PROBE_URL" ]]; then
  echo "usage: $0 --anchor <tag-or-sha> --probe-url <url> [--branch BRANCH] [--dry-run]" >&2
  exit 1
fi

cd "$(dirname "$0")/.." || exit 2

if [[ -z "$BRANCH" ]]; then
  BRANCH="$(git rev-parse --abbrev-ref HEAD)"
fi

# Verify anchor exists.
if ! git rev-parse --verify "$ANCHOR" >/dev/null 2>&1; then
  echo "ERROR: anchor '$ANCHOR' does not exist as tag or sha" >&2
  exit 2
fi

ANCHOR_SHA="$(git rev-parse "$ANCHOR")"
HEAD_SHA="$(git rev-parse HEAD)"

if [[ "$ANCHOR_SHA" == "$HEAD_SHA" ]]; then
  echo "no-op: HEAD == anchor, nothing to revert"
  exit 0
fi

# 1. Pre-revert probe.
echo "Step 1/5 — capturing pre-revert state of $PROBE_URL"
PRE_HEADERS="$(curl -sI -L --max-time 10 "$PROBE_URL" 2>/dev/null || echo "")"
PRE_STATUS="$(echo "$PRE_HEADERS" | head -1 | awk '{print $2}')"
PRE_VERSION="$(echo "$PRE_HEADERS" | grep -i '^x-cdm-version:' | head -1 | tr -d '\r' | awk '{print $2}')"
PRE_BODY_HASH="$(curl -sL --max-time 10 "$PROBE_URL" 2>/dev/null | sha256sum | awk '{print $1}')"
echo "  pre-status=$PRE_STATUS pre-version=${PRE_VERSION:-none} pre-hash=${PRE_BODY_HASH:0:16}"

# 2. Decision point — start the wall clock NOW.
DECISION_TS="$(date -u +%s)"
echo "Step 2/5 — decision-to-revert at $DECISION_TS ($(date -u -d @$DECISION_TS '+%H:%M:%S UTC'))"

if [[ "$DRY_RUN" == "1" ]]; then
  echo "DRY RUN — would: git revert --no-edit ${ANCHOR}..HEAD ; git push origin ${BRANCH}"
  echo "DRY RUN — would: poll $PROBE_URL every 5s for state divergence (timeout 8min)"
  echo "DRY RUN — would: write report to data/cdm_rev_rollback_drill_<TS>.json"
  exit 0
fi

# 3. git revert chain.
REVERT_COUNT="$(git rev-list --count "${ANCHOR}..HEAD")"
echo "Step 3/5 — reverting $REVERT_COUNT commits ($ANCHOR..HEAD)"
if ! git revert --no-edit "${ANCHOR}..HEAD" 2>&1; then
  echo "ERROR: git revert failed — bailing out (manual cleanup required)" >&2
  exit 2
fi

# 4. Push.
echo "Step 4/5 — pushing $BRANCH"
if ! git push origin "$BRANCH" 2>&1; then
  echo "ERROR: git push failed" >&2
  exit 2
fi

PUSH_TS="$(date -u +%s)"
echo "  push completed at $((PUSH_TS - DECISION_TS))s"

# 5. Poll probe URL until divergence.
echo "Step 5/5 — polling $PROBE_URL every 5s (timeout 480s)"
DEADLINE=$((PUSH_TS + 480))
RECOVERED_TS=""
ATTEMPTS=0
while [[ $(date -u +%s) -lt $DEADLINE ]]; do
  ATTEMPTS=$((ATTEMPTS + 1))
  HEADERS="$(curl -sI -L --max-time 10 "$PROBE_URL" 2>/dev/null || echo "")"
  STATUS="$(echo "$HEADERS" | head -1 | awk '{print $2}')"
  VERSION="$(echo "$HEADERS" | grep -i '^x-cdm-version:' | head -1 | tr -d '\r' | awk '{print $2}')"
  BODY_HASH="$(curl -sL --max-time 10 "$PROBE_URL" 2>/dev/null | sha256sum | awk '{print $1}')"

  if [[ "$STATUS" != "$PRE_STATUS" ]] || [[ "$VERSION" != "$PRE_VERSION" ]] || [[ "$BODY_HASH" != "$PRE_BODY_HASH" ]]; then
    RECOVERED_TS="$(date -u +%s)"
    echo "  divergence detected on attempt $ATTEMPTS — status=$STATUS version=${VERSION:-none} hash=${BODY_HASH:0:16}"
    break
  fi
  sleep 5
done

NOW_TS="$(date -u +%s)"
TOTAL_SEC=$((NOW_TS - DECISION_TS))

# Write JSON report.
mkdir -p data
REPORT="data/cdm_rev_rollback_drill_$(date -u +%Y%m%dT%H%M%S).json"
cat > "$REPORT" <<EOF
{
  "drill": "Drill 1 — CF Pages worker rollback",
  "decision_ts_utc": $DECISION_TS,
  "push_ts_utc": $PUSH_TS,
  "recovered_ts_utc": ${RECOVERED_TS:-null},
  "push_seconds": $((PUSH_TS - DECISION_TS)),
  "recovery_seconds": $([[ -n "$RECOVERED_TS" ]] && echo $((RECOVERED_TS - PUSH_TS)) || echo "null"),
  "total_seconds": $TOTAL_SEC,
  "polling_attempts": $ATTEMPTS,
  "anchor": "$ANCHOR",
  "anchor_sha": "$ANCHOR_SHA",
  "head_sha_pre": "$HEAD_SHA",
  "head_sha_post": "$(git rev-parse HEAD)",
  "branch": "$BRANCH",
  "probe_url": "$PROBE_URL",
  "pre": {"status": "$PRE_STATUS", "version": "${PRE_VERSION:-null}", "body_hash": "$PRE_BODY_HASH"},
  "post": {"status": "${STATUS:-null}", "version": "${VERSION:-null}", "body_hash": "${BODY_HASH:-null}"},
  "pass_criterion_seconds": 300,
  "passed": $([[ -n "$RECOVERED_TS" && $TOTAL_SEC -le 300 ]] && echo "true" || echo "false")
}
EOF
echo "Report: $REPORT"
cat "$REPORT"

if [[ -z "$RECOVERED_TS" ]]; then
  echo "FAIL: probe never diverged within 480s — rollback did NOT take effect" >&2
  exit 3
fi

if [[ $TOTAL_SEC -gt 300 ]]; then
  echo "FAIL: total ${TOTAL_SEC}s exceeded 300s pass criterion" >&2
  exit 4
fi

echo "PASS: rollback completed in ${TOTAL_SEC}s (≤300s)"
exit 0
