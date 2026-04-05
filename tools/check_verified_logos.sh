#!/bin/bash
# Build-time check: all verified providers MUST have valid logo_url
# Run before deploy to catch dropped logos

FAIL=0
cd /srv/BusinessOps/creditdoc

for f in $(grep -rl '"verified_provider": true' src/content/lenders/); do
  name=$(python3 -c "import json; print(json.load(open('$f'))['name'])")
  logo=$(python3 -c "import json; print(json.load(open('$f')).get('logo_url',''))")
  
  if [ -z "$logo" ]; then
    echo "FAIL: $name has no logo_url"
    FAIL=1
  elif [[ "$logo" == /logos/* ]]; then
    # Check local file exists
    if [ ! -f "public${logo}" ]; then
      echo "FAIL: $name logo file missing: public${logo}"
      FAIL=1
    else
      echo "OK: $name -> ${logo}"
    fi
  else
    echo "OK: $name -> ${logo}"
  fi
done

if [ $FAIL -eq 1 ]; then
  echo ""
  echo "BLOCKED: Verified providers must have valid logos. Fix before deploying."
  exit 1
fi

echo ""
echo "All verified provider logos OK."
