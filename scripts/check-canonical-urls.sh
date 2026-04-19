#!/usr/bin/env bash
# Blocks commits that re-introduce hardcoded apex URLs (must use www).
# Allows https://creditdoc.com (different TLD, unlikely but safe).
set -e
BAD=$(grep -rln 'https://creditdoc\.co[^m]' src/ 2>/dev/null || true)
if [ -n "$BAD" ]; then
  echo "ERROR: Found hardcoded apex URLs (https://creditdoc.co/...) in:"
  echo "$BAD"
  echo ""
  echo "Replace with https://www.creditdoc.co to preserve canonical consistency."
  echo "Apex is only for CDN redirects — templates must emit the www form."
  exit 1
fi
echo "OK: No hardcoded apex URLs in src/"
