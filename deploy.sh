#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
source /srv/BusinessOps/.env 2>/dev/null

echo "=== CreditDoc Deploy ==="
echo "$(date -u '+%Y-%m-%d %H:%M:%S UTC')"

# 0. Pre-build: export CFPB data for trend pages
python3 scripts/export_cfpb_trends.py 2>/dev/null || true

# 1. Build
echo ""
echo "[1/4] Building..."
if [ "${SKIP_BUILD:-0}" = "1" ]; then
  echo "  SKIP_BUILD=1 — using existing dist/ from targeted renderer output"
else
  BUILD_LOG="/tmp/creditdoc_build_$(date +%s).log"
  if ! npm run build > "$BUILD_LOG" 2>&1; then
    echo "!!! BUILD FAILED — last 40 lines of $BUILD_LOG !!!"
    tail -40 "$BUILD_LOG"
    exit 1
  fi
  tail -3 "$BUILD_LOG"
fi

# Post-build sanity: dist must have thousands of files, not zero.
DIST_COUNT=$(find dist -name '*.html' 2>/dev/null | wc -l)
if [ "$DIST_COUNT" -lt 10000 ]; then
  echo "!!! DIST HAS ONLY $DIST_COUNT HTML FILES — EXPECTED >10000 — ABORTING !!!"
  echo "Build log: $BUILD_LOG"
  exit 1
fi
echo "  dist has $DIST_COUNT HTML files"

# 2. Deploy to Cloudflare Workers
echo ""
echo "[2/4] Deploying to Cloudflare Workers..."
DEPLOY_LOG="/tmp/creditdoc_deploy_$(date +%s).log"
if ! CLOUDFLARE_API_TOKEN="" \
     CLOUDFLARE_EMAIL="$CLOUDFLARE_EMAIL" \
     CLOUDFLARE_API_KEY="$CLOUDFLARE_GLOBAL_API_KEY" \
     npx wrangler deploy > "$DEPLOY_LOG" 2>&1; then
  echo "!!! WRANGLER DEPLOY FAILED — last 40 lines of $DEPLOY_LOG !!!"
  tail -40 "$DEPLOY_LOG"
  exit 1
fi
tail -5 "$DEPLOY_LOG"

# 3. Purge Cloudflare cache.
#
# Do not purge the whole zone by default. CreditDoc has thousands of SSR pages
# behind versioned edge cache; a full purge makes every crawler request a cold
# Worker render and can trigger Cloudflare 1102 CPU failures. Use
# FULL_CACHE_PURGE=1 only for emergencies or planned low-traffic maintenance.
echo ""
echo "[3/4] Purging Cloudflare cache..."
ZONE_ID="b644afdfb731703f578f6885ca1774b4"
if [ "${FULL_CACHE_PURGE:-0}" = "1" ]; then
  purge_payload='{"purge_everything":true}'
else
  purge_payload=$(python3 - <<'PY'
import json

paths = [
    "/",
    "/robots.txt",
    "/sitemap-index.xml",
    "/feed.xml",
    "/rss.xml",
    "/best/",
    "/linkedin-oauth-callback/",
    "/review/lexington-law/",
    "/state/wyoming/",
    "/state/wisconsin/",
    "/credit-guide/austin-tx/",
    "/credit-guide/austin-tx/credit-repair/",
    "/credit-guide/charlotte-nc/atm/",
    "/answers/",
    "/answers/best-debt-consolidation-loans-bad-credit/",
    "/best/best-credit-repair-companies/",
    "/categories/credit-repair/",
    "/blog/how-to-get-a-personal-loan-with-bad-credit-in-2026/",
    "/financial-wellness/credit-score-basics/",
    "/brand/advance-america/",
]
print(json.dumps({
    "files": [f"https://www.creditdoc.co{path}" for path in paths]
}))
PY
)
fi
purge_result=$(curl -s -X POST "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/purge_cache" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  --data "$purge_payload")
if echo "$purge_result" | python3 -c "import sys,json; sys.exit(0 if json.load(sys.stdin).get('success') else 1)" 2>/dev/null; then
  if [ "${FULL_CACHE_PURGE:-0}" = "1" ]; then
    echo "Full cache purge completed."
  else
    echo "Targeted cache purge completed."
  fi
else
  echo "WARNING: Cache purge failed!"
  echo "$purge_result"
fi

# 4. Verify site loads — homepage, CSS, and SSR route families.
# These SSR checks also warm Cloudflare's versioned cache after purge/deploy so
# users and crawlers are less likely to be the first expensive render.
echo ""
echo "[4/4] Verifying site..."
sleep 2

FAIL=0

# Homepage
status=$(curl -s -o /dev/null -w "%{http_code}" "https://www.creditdoc.co/")
css_url=$(curl -s "https://www.creditdoc.co/" | grep -oP 'href="(/[^"]*\.css[^"]*)"' | head -1 | sed 's/href="//;s/"//')
css_status=$(curl -s -o /dev/null -w "%{http_code}" "https://www.creditdoc.co${css_url}")
echo "Homepage: $status | CSS ($css_url): $css_status"
# Note: previous form `[ A ] || [ B ] && FAIL=1` silently missed A-failures due to
# && binding tighter than the [] || [] sequence. Use explicit if to catch both.
if [ "$status" != "200" ] || [ "$css_status" != "200" ]; then
  FAIL=1
fi

# SSR smoke tests — one URL per dynamic route family
SSR_URLS=(
  "/review/lexington-law/"
  "/state/wyoming/"
  "/credit-guide/austin-tx/"
  "/credit-guide/austin-tx/credit-repair/"
  "/answers/"
  "/answers/best-debt-consolidation-loans-bad-credit/"
  "/best/best-credit-repair-companies/"
  "/categories/credit-repair/"
  "/blog/how-to-get-a-personal-loan-with-bad-credit-in-2026/"
  "/financial-wellness/credit-score-basics/"
  "/brand/advance-america/"
)
for url in "${SSR_URLS[@]}"; do
  headers=$(mktemp)
  s=$(curl -sL -D "$headers" -o /dev/null -w "%{http_code}" --max-time 10 "https://www.creditdoc.co${url}")
  cache=$(grep -i '^x-cdm-cache:' "$headers" | tail -1 | tr -d '\r' | sed 's/^x-cdm-cache: //I' || true)
  rm -f "$headers"
  echo "  $url → $s${cache:+ | cache=$cache}"
  [ "$s" != "200" ] && FAIL=1
done

# Worker API + affiliate smoke tests. Added 2026-07-27 after the run_worker_first
# regression I introduced silently 404'd /api/* + /go/* for ~2 hours. Deploy
# declared "successful" three times while the site was actually broken because
# the SSR_URLS list only contained static pages.
echo ""
echo "[4b/5] Worker API + affiliate smoke tests..."
# /api/search MUST be tested with trailing slash — that's what the client JS calls
API_TESTS=(
  "GET|/api/search/?limit=3|200"
  "GET|/api/search?limit=3|200"
  "GET|/api/geo|200"
  "GET|/go/lexington-law?source=deploy-smoke|302"
)
for entry in "${API_TESTS[@]}"; do
  IFS='|' read -r method url expect <<< "$entry"
  s=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" --max-time 10 "https://www.creditdoc.co${url}")
  echo "  $method $url → $s (want $expect)"
  [ "$s" != "$expect" ] && FAIL=1
done

# Redirect contract tests. Any of these breaking = regression on today's fixes.
echo ""
echo "[4c/5] Redirect contract tests..."
REDIRECT_TESTS=(
  "/search/?state=Utah|301|/state/utah/"
  "/browse/credit-repair/austin-texas/|301|/browse/credit-repair/austin-tx/"
  "/sitemap-4.xml|301|/sitemap-index.xml"
  "/trends/|301|/research/consumer-complaints/"
)
for entry in "${REDIRECT_TESTS[@]}"; do
  IFS='|' read -r url expect_code expect_loc <<< "$entry"
  s=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "https://www.creditdoc.co${url}")
  loc=$(curl -sI --max-time 10 "https://www.creditdoc.co${url}" | grep -i '^location:' | tr -d '\r' | sed 's/location: //i' | sed 's|https://www.creditdoc.co||')
  echo "  $url → $s → $loc (want $expect_code → $expect_loc)"
  if [ "$s" != "$expect_code" ] || [ "$loc" != "$expect_loc" ]; then FAIL=1; fi
done

# Canonical rewrite test — /search/?category=X must rewrite to /categories/X/
echo ""
echo "[4d/5] Canonical rewrite tests..."
can=$(curl -sL --max-time 10 "https://www.creditdoc.co/search/?category=credit-repair" | grep -oE '<link rel="canonical" href="[^"]+"' | head -1)
if echo "$can" | grep -q 'categories/credit-repair/'; then
  echo "  /search/?category=credit-repair canonical → /categories/credit-repair/ ✓"
else
  echo "  /search/?category=credit-repair canonical WRONG: $can"
  FAIL=1
fi

# Form JS guard — dist/search/index.html must retain the categoryOnlyMap + stateOnlyMap
# added 2026-07-27. If /search/ page is ever regenerated, these get wiped.
echo ""
echo "[4e/5] Form JS orphan-prevention guard..."
formjs=$(curl -sL --max-time 10 "https://www.creditdoc.co/search/")
for marker in stateOnlyMap categoryOnlyMap; do
  n=$(echo "$formjs" | grep -c "$marker" || true)
  echo "  $marker in /search/: $n hits (want ≥1)"
  [ "$n" = "0" ] && FAIL=1
done
homejs=$(curl -sL --max-time 10 "https://www.creditdoc.co/")
n=$(echo "$homejs" | grep -c "HP_CATEGORY_MAP" || true)
echo "  HP_CATEGORY_MAP in homepage: $n hits (want ≥1)"
[ "$n" = "0" ] && FAIL=1

if [ "$FAIL" = "0" ]; then
  echo ""
  echo "=== Deploy successful ==="
else
  echo ""
  echo "!!! DEPLOY VERIFICATION FAILED — CHECK ROUTES ABOVE !!!"
  exit 1
fi
