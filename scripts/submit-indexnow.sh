#!/usr/bin/env bash
set -euo pipefail

host="www.creditdoc.co"
key="8eaf0cb216c85989ac151853f4a3af16cb87803ba170a792f1ceab37234bf23e"
key_location="https://${host}/${key}.txt"

urls=(
  "https://www.creditdoc.co/"
  "https://www.creditdoc.co/sitemap-index.xml"
)

payload="$(node -e '
const host = process.argv[1];
const key = process.argv[2];
const keyLocation = process.argv[3];
const urls = process.argv.slice(4);
process.stdout.write(JSON.stringify({ host, key, keyLocation, urlList: urls }));
' "$host" "$key" "$key_location" "${urls[@]}")"

curl -sS -i \
  -H "Content-Type: application/json; charset=utf-8" \
  -X POST "https://api.indexnow.org/indexnow" \
  --data "$payload"
