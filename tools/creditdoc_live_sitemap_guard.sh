#!/usr/bin/env bash
set -euo pipefail

cd /srv/BusinessOps/creditdoc

MODE="${1:-sample}"
case "$MODE" in
  sample)
    exec /usr/bin/node scripts/check_live_sitemap_status.mjs --limit-per-family=25 --timeout-ms=15000
    ;;
  full)
    exec /usr/bin/node scripts/check_live_sitemap_status.mjs --all --concurrency=12 --timeout-ms=15000
    ;;
  *)
    echo "Usage: $0 [sample|full]" >&2
    exit 2
    ;;
esac
