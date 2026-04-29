#!/usr/bin/env bash
# CDM-REV-2026-04-29 — HTML parity smoke test.
#
# Fetches /review/<slug>/ from BOTH the Vercel production site (creditdoc.co)
# and the Cloudflare Pages preview (cdm-rev-hybrid.creditdoc.pages.dev) for
# each slug in a list, normalizes whitespace + dynamic content, and reports a
# byte-level diff percentage per slug.
#
# Phase 1 acceptance gate (d): HTML diff <0.1% over 20 sample slugs.
#
# This is READ-ONLY (HTTP GET). Safe to run in /loop "no live DB" mode.
#
# Usage:
#   tools/cdm_rev_html_diff.sh                       # uses default slug list
#   tools/cdm_rev_html_diff.sh slugs.txt             # one slug per line
#   tools/cdm_rev_html_diff.sh --slugs a,b,c         # comma-separated

set -euo pipefail

PROD_HOST="${PROD_HOST:-https://www.creditdoc.co}"
PREVIEW_HOST="${PREVIEW_HOST:-https://cdm-rev-hybrid.creditdoc.pages.dev}"

# Default 20 slugs — top-rated lenders from each major category.
DEFAULT_SLUGS=(
  credit-saint
  the-credit-pros
  sky-blue-credit
  the-credit-people
  lexington-law
  experian-boost
  credit-strong
  self-credit-builder
  bbva-secured-credit-card
  capital-one-platinum-secured
  upstart-personal-loan
  lightstream-personal-loan
  sofi-personal-loan
  marcus-personal-loan
  best-egg-personal-loan
  upgrade-personal-loan
  prosper-personal-loan
  lendingclub-personal-loan
  rocket-loans
  discover-personal-loan
)

SLUGS=()
if [[ $# -gt 0 ]]; then
  if [[ "$1" == "--slugs" ]]; then
    IFS=',' read -ra SLUGS <<< "$2"
  elif [[ -f "$1" ]]; then
    while IFS= read -r line; do
      [[ -n "$line" && "$line" != \#* ]] && SLUGS+=("$line")
    done < "$1"
  else
    echo "ERROR: $1 is not a file and not --slugs"; exit 2
  fi
else
  SLUGS=("${DEFAULT_SLUGS[@]}")
fi

echo "============================================================"
echo "CDM-REV HTML parity smoke test"
echo "============================================================"
echo "PROD     : $PROD_HOST"
echo "PREVIEW  : $PREVIEW_HOST"
echo "Slugs    : ${#SLUGS[@]}"
echo

mkdir -p tmp_html_diff
LOG="tmp_html_diff/diff_$(date -u +%Y%m%dT%H%M%SZ).log"
: > "$LOG"

normalize() {
  # Strip:
  #  - timestamp-like content (e.g. "Updated: April 29, 2026")
  #  - cache-busted asset hashes  /_astro/*.HASH.{js,css}
  #  - prerender-vs-SSR comments
  #  - whitespace runs
  # then output to stdout.
  sed -E '
    s|/_astro/[^"]+\.[a-zA-Z0-9_-]{8,}\.(js|css|woff2)|/_astro/HASH.&|g;
    s|<!--.*-->||g;
    s|>[[:space:]]+<|><|g;
    s|[[:space:]]+| |g;
    s|("|content="|description="|content_url="|"\?_v=)[0-9TZ:.\-]{8,}|\1NORM|g;
  '
}

total_pct=0
count_ok=0
count_fail=0

printf "%-50s %12s %12s %10s %s\n" "slug" "prod_bytes" "prev_bytes" "diff_pct" "status"
printf '%.0s-' {1..100}; echo

for slug in "${SLUGS[@]}"; do
  prod_url="$PROD_HOST/review/$slug/"
  prev_url="$PREVIEW_HOST/review/$slug/"

  prod_file="tmp_html_diff/${slug}.prod.html"
  prev_file="tmp_html_diff/${slug}.prev.html"
  prod_norm="tmp_html_diff/${slug}.prod.norm.html"
  prev_norm="tmp_html_diff/${slug}.prev.norm.html"

  prod_status=$(curl -sL -o "$prod_file" -w "%{http_code}" --max-time 20 "$prod_url" || echo "000")
  prev_status=$(curl -sL -o "$prev_file" -w "%{http_code}" --max-time 20 "$prev_url" || echo "000")

  if [[ "$prod_status" != "200" ]] || [[ "$prev_status" != "200" ]]; then
    printf "%-50s %12s %12s %10s %s\n" \
      "$slug" "${prod_status}" "${prev_status}" "n/a" "FAIL_HTTP"
    echo "[$slug] HTTP failure: prod=$prod_status preview=$prev_status" >> "$LOG"
    count_fail=$((count_fail + 1))
    continue
  fi

  normalize < "$prod_file" > "$prod_norm"
  normalize < "$prev_file" > "$prev_norm"

  prod_bytes=$(wc -c < "$prod_norm")
  prev_bytes=$(wc -c < "$prev_norm")

  # Bytes-different (rough): wc -l of diff -u
  diff_lines=$(diff -u "$prod_norm" "$prev_norm" | grep -cE "^[+-]" || true)
  # Approximate percent: char-level Levenshtein is too slow for full pages,
  # so we use line-diff count / total lines as a coarse proxy.
  total_lines=$(wc -l < "$prod_norm")
  if [[ "$total_lines" -eq 0 ]]; then total_lines=1; fi
  pct=$(awk -v d="$diff_lines" -v t="$total_lines" 'BEGIN { printf "%.3f", (d/t)*100 }')

  status="OK"
  if (( $(awk -v p="$pct" 'BEGIN { print (p > 0.1) }') )); then
    status="OVER_THRESHOLD"
    count_fail=$((count_fail + 1))
  else
    count_ok=$((count_ok + 1))
  fi

  printf "%-50s %12s %12s %10s %s\n" \
    "$slug" "$prod_bytes" "$prev_bytes" "$pct%" "$status"
  echo "[$slug] prod=${prod_bytes}B prev=${prev_bytes}B diff=${pct}% status=${status}" >> "$LOG"

  total_pct=$(awk -v t="$total_pct" -v p="$pct" 'BEGIN { printf "%.4f", t+p }')
done

echo
echo "============================================================"
avg_pct=$(awk -v t="$total_pct" -v n="${#SLUGS[@]}" 'BEGIN { if (n>0) printf "%.4f", t/n; else print "0.0000" }')
echo "Slugs OK         : $count_ok"
echo "Slugs over 0.1%  : $count_fail"
echo "Mean diff %      : ${avg_pct}%"
echo "Log              : $LOG"

# Acceptance gate: 0 over-threshold AND mean < 0.1%
if [[ "$count_fail" -eq 0 ]] && (( $(awk -v p="$avg_pct" 'BEGIN { print (p < 0.1) }') )); then
  echo "RESULT: ACCEPTANCE GATE GREEN"
  exit 0
else
  echo "RESULT: ACCEPTANCE GATE RED"
  exit 1
fi
