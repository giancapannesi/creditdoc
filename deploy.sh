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
npm run build 2>&1 | tail -3

# 2. Deploy to Cloudflare Workers
echo ""
echo "[2/4] Deploying to Cloudflare Workers..."
CLOUDFLARE_API_TOKEN="" \
CLOUDFLARE_EMAIL="$CLOUDFLARE_EMAIL" \
CLOUDFLARE_API_KEY="$CLOUDFLARE_GLOBAL_API_KEY" \
npx wrangler deploy 2>&1 | tail -5

# 3. Purge Cloudflare cache
echo ""
echo "[3/4] Purging Cloudflare cache..."
ZONE_ID="b644afdfb731703f578f6885ca1774b4"
purge_result=$(curl -s -X POST "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/purge_cache" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  --data '{"purge_everything":true}')
if echo "$purge_result" | python3 -c "import sys,json; sys.exit(0 if json.load(sys.stdin).get('success') else 1)" 2>/dev/null; then
  echo "Cache purged."
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
[ "$status" != "200" ] || [ "$css_status" != "200" ] && FAIL=1

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

if [ "$FAIL" = "0" ]; then
  echo ""
  echo "=== Deploy successful ==="
else
  echo ""
  echo "!!! DEPLOY VERIFICATION FAILED — CHECK ROUTES ABOVE !!!"
  exit 1
fi
