#!/usr/bin/env bash
# Regenerate data/creditdoc-slim.db from /srv/BusinessOps/creditdoc/data/creditdoc.db.
# This is the runtime DB that gets bundled into the Vercel function.
#
# What's included: lenders + categories + comparisons + listicles + wellness_guides +
#   blog_posts + cluster_answers (plus idx_lenders_slug, idx_lenders_status).
# What's excluded: audit_log (53M, write-heavy log not needed at runtime), all the
#   tracker / pinterest / index_snapshots / serp_winnability tables, etc.
#
# Usage: ./scripts/build_slim_db.sh
# Exits non-zero on any error.

set -euo pipefail

SOURCE="/srv/BusinessOps/creditdoc/data/creditdoc.db"
DEST="/srv/BusinessOps/creditdoc-arch/data/creditdoc-slim.db"
TMP="${DEST}.tmp.$$"

if [[ ! -f "$SOURCE" ]]; then
  echo "ERROR: source DB not found at $SOURCE" >&2
  exit 1
fi

mkdir -p "$(dirname "$DEST")"
rm -f "$TMP"

echo "Building slim DB from $SOURCE -> $DEST"
sqlite3 "$TMP" <<SQL
ATTACH DATABASE '$SOURCE' AS src;

CREATE TABLE lenders          AS SELECT * FROM src.lenders;
CREATE TABLE categories       AS SELECT * FROM src.categories;
CREATE TABLE comparisons      AS SELECT * FROM src.comparisons;
CREATE TABLE listicles        AS SELECT * FROM src.listicles;
CREATE TABLE wellness_guides  AS SELECT * FROM src.wellness_guides;
CREATE TABLE blog_posts       AS SELECT * FROM src.blog_posts;
CREATE TABLE cluster_answers  AS SELECT * FROM src.cluster_answers;

CREATE INDEX idx_lenders_slug   ON lenders(slug);
CREATE INDEX idx_lenders_status ON lenders(processing_status);

DETACH DATABASE src;
VACUUM;
SQL

# Atomic swap.
mv "$TMP" "$DEST"

# Sanity check.
N=$(sqlite3 "$DEST" "SELECT COUNT(*) FROM lenders")
SIZE=$(du -h "$DEST" | cut -f1)
echo "Slim DB built: $N lenders, $SIZE"

if (( N < 10000 )); then
  echo "ERROR: lender count $N looks too low; aborting" >&2
  exit 2
fi
