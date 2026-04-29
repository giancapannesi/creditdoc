#!/usr/bin/env bash
# CDM-REV-2026-04-29 Phase 1.7 — TTFB acceptance gate.
#
# Hits the SSR pilot route + JSON probe on a target base URL (preview deploy
# from Phase 1.6, or http://127.0.0.1:8788 for wrangler pages dev). Cold + warm
# pass per slug, p50/p95 reported.
#
# Acceptance bar (per CREDITDOC_NEXT.md):
#   warm  TTFB < 100ms p95
#   cold  TTFB < 600ms p95
#
# Usage:
#   ./tools/cdm_rev_phase17_ttfb.sh                  # local wrangler dev
#   ./tools/cdm_rev_phase17_ttfb.sh https://<preview>.pages.dev
#
# Output: per-slug timing CSV → stdout, summary stats at end.

set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:8788}"
SLUGS=(
  affirm
  axos-bank
  brigit
  credit-glory
  credit-saint
  earnin
  klarna
  lendingclub
  lexington-law
  oportun
  ovation-credit
  prosper
  rocket-loans
  sky-blue-credit
  sofi
  the-credit-people
  upgrade
  upstart
  wallethub
)

WARM_RUNS=3

echo "BASE_URL=$BASE_URL"
echo "WARM_RUNS=$WARM_RUNS  SLUGS=${#SLUGS[@]}"
echo ""
echo "slug,route,phase,run,http,ttfb_ms,total_ms,bytes"

cold_ttfbs=()
warm_ttfbs=()

curl_metric() {
  # %{time_starttransfer} = TTFB seconds (float). Multiply ×1000.
  local url="$1"
  local h_var="$2"
  local out
  out=$(curl -sS -o /dev/null -L --max-time 30 \
    -w '%{http_code}|%{time_starttransfer}|%{time_total}|%{size_download}' \
    -H "Cache-Control: no-store" \
    "$url" 2>&1) || out="000|0|0|0"
  echo "$out"
}

for slug in "${SLUGS[@]}"; do
  for route in "/r/$slug" "/api/lender/$slug"; do
    url="$BASE_URL$route"
    # Cold: include a unique query string to bypass cache
    cold_url="${url}?_cdm_cold=$(date +%s%N)"
    cold=$(curl_metric "$cold_url" "cold")
    cold_http=$(echo "$cold" | cut -d'|' -f1)
    cold_ttfb_s=$(echo "$cold" | cut -d'|' -f2)
    cold_total_s=$(echo "$cold" | cut -d'|' -f3)
    cold_bytes=$(echo "$cold" | cut -d'|' -f4)
    cold_ttfb_ms=$(awk "BEGIN{printf \"%.1f\", $cold_ttfb_s * 1000}")
    cold_total_ms=$(awk "BEGIN{printf \"%.1f\", $cold_total_s * 1000}")
    echo "$slug,$route,cold,1,$cold_http,$cold_ttfb_ms,$cold_total_ms,$cold_bytes"
    cold_ttfbs+=("$cold_ttfb_ms")

    for i in $(seq 1 $WARM_RUNS); do
      warm=$(curl_metric "$url" "warm")
      warm_http=$(echo "$warm" | cut -d'|' -f1)
      warm_ttfb_s=$(echo "$warm" | cut -d'|' -f2)
      warm_total_s=$(echo "$warm" | cut -d'|' -f3)
      warm_bytes=$(echo "$warm" | cut -d'|' -f4)
      warm_ttfb_ms=$(awk "BEGIN{printf \"%.1f\", $warm_ttfb_s * 1000}")
      warm_total_ms=$(awk "BEGIN{printf \"%.1f\", $warm_total_s * 1000}")
      echo "$slug,$route,warm,$i,$warm_http,$warm_ttfb_ms,$warm_total_ms,$warm_bytes"
      warm_ttfbs+=("$warm_ttfb_ms")
    done
  done
done

stats() {
  local label="$1"; shift
  local arr=("$@")
  local n=${#arr[@]}
  if [ "$n" = "0" ]; then echo "$label: NO DATA"; return; fi
  printf '%s\n' "${arr[@]}" | sort -n > /tmp/_cdm_ttfb.tmp
  local p50_idx p95_idx
  p50_idx=$(( (n - 1) / 2 ))
  p95_idx=$(( n * 95 / 100 ))
  [ "$p95_idx" -ge "$n" ] && p95_idx=$((n-1))
  local p50 p95 max
  p50=$(sed -n "$((p50_idx+1))p" /tmp/_cdm_ttfb.tmp)
  p95=$(sed -n "$((p95_idx+1))p" /tmp/_cdm_ttfb.tmp)
  max=$(tail -1 /tmp/_cdm_ttfb.tmp)
  echo "$label  n=$n  p50=${p50}ms  p95=${p95}ms  max=${max}ms"
}

echo ""
echo "=== summary ==="
stats "cold" "${cold_ttfbs[@]}"
stats "warm" "${warm_ttfbs[@]}"
echo ""
echo "Acceptance bar: warm<100ms p95, cold<600ms p95"
