#!/usr/bin/env bash
# CDM-REV Phase 5.9.2 — single-route prerender revert.
#
# Flips `export const prerender = false;` → `export const prerender = true;`
# in a single Astro page, commits, and pushes. Idempotent (no-op if already
# reverted). Used during Drill 2 of the rollback rehearsal.
#
# Usage:
#   tools/cdm_rev_revert_route.sh src/pages/answers/[slug].astro
#   tools/cdm_rev_revert_route.sh --dry-run src/pages/best/[slug].astro
#
# WARNING: this forfeits OBJ-1 ≤10s for the reverted route. Edits to its
# content go back to needing a `git push`. Use only during emergency rollback.
#
# Exit codes:
#   0 = reverted (or already reverted) and pushed
#   1 = file not found / not an Astro page
#   2 = no `prerender = false` line found (already reverted or never SSR)
#   3 = git operation failed

set -euo pipefail

DRY_RUN=0
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
  shift
fi

ROUTE="${1:-}"
if [[ -z "$ROUTE" ]]; then
  echo "usage: $0 [--dry-run] <path-to-astro-file>" >&2
  exit 1
fi

# Anchor on creditdoc repo root.
cd "$(dirname "$0")/.." || exit 1

if [[ ! -f "$ROUTE" ]]; then
  echo "ERROR: $ROUTE not found" >&2
  exit 1
fi

if ! head -50 "$ROUTE" | grep -q "^export const prerender"; then
  echo "ERROR: no \`export const prerender\` line in first 50 lines of $ROUTE" >&2
  echo "       (this script is for Astro pages with explicit prerender opt-out)" >&2
  exit 2
fi

if grep -q "^export const prerender = true;" "$ROUTE"; then
  echo "no-op: $ROUTE already has prerender = true (already reverted)"
  exit 0
fi

if ! grep -q "^export const prerender = false;" "$ROUTE"; then
  echo "ERROR: $ROUTE has prerender directive but not exactly \`export const prerender = false;\`" >&2
  echo "       Manual review required — bailing out." >&2
  exit 2
fi

echo "INFO: reverting $ROUTE to prerender = true"
if [[ "$DRY_RUN" == "1" ]]; then
  echo "DRY RUN — would patch:"
  grep -n "^export const prerender" "$ROUTE"
  echo "DRY RUN — would commit + push to current branch"
  exit 0
fi

# Patch in-place. sed is fine here — the line is a one-liner, no escaping concerns.
sed -i 's/^export const prerender = false;$/export const prerender = true;/' "$ROUTE"

# Verify the patch landed.
if ! grep -q "^export const prerender = true;" "$ROUTE"; then
  echo "ERROR: sed patch failed — line not changed" >&2
  exit 3
fi

git add "$ROUTE" || { echo "git add failed" >&2; exit 3; }

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
COMMIT_MSG="EMERGENCY ROLLBACK: revert $(basename "$ROUTE" .astro) to prerender [OBJ-1 forfeit for this route]"
git commit -m "$COMMIT_MSG" || { echo "git commit failed" >&2; exit 3; }

git push origin "$CURRENT_BRANCH" || { echo "git push failed — commit is local only" >&2; exit 3; }

echo "DONE: $ROUTE reverted on branch $CURRENT_BRANCH and pushed."
echo "Wait ~3 min for CF Pages to build, then verify the route is static again:"
echo "  curl -sI https://<host>$(echo "$ROUTE" | sed 's|src/pages||;s|\[slug\]|<slug>|;s|\.astro$|/|') | head -3"
