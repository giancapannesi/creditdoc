#!/usr/bin/env python3
"""
CDM-REV — prune dangling slug refs from `body_inline.similar_lenders`.

Discovered 2026-04-30 while investigating Upstart parity drift:
upstart.similar_lenders contained `chacon-autos` (auto-dealer purged
months ago) plus 2 raw-status rows that the SSR adapter filters out.
Runtime fallback then filled with category top-rated, breaking
parity with prod.

DB-wide: 129 dangling refs across the lenders table.

This is a BULK DATA OPERATION. Per RULE 4 / Cardinal Sin #3: requires
explicit Jammi greenlight. Default: --dry-run.

Plan when applied:
  - Walk every row whose body_inline.similar_lenders is a non-empty array.
  - For each entry, check it exists in `lenders` AND has
    processing_status='ready_for_index'. (Adapter filters by both, so
    keeping refs to raw rows is dead weight too.)
  - Strip dead/raw refs. If the row's similar_lenders becomes empty,
    keep the field as `[]` (do not null it — UI fallback expects array).
  - Update body_inline + bump updated_at via the dual-write path
    (creditdoc_db.update_lender). This triggers the audit_log capture
    AND propagates to /api/revalidate.

DRY-RUN OUTPUT:
  - Prints summary (rows touched, refs removed, top 10 dead ref slugs).
  - Writes /srv/BusinessOps/creditdoc/data/dangling_similar_lenders.csv
    for Drive upload review.

APPLY:
  python3 tools/cdm_rev_prune_dangling_similar.py --apply

Per-row write rate: rate-limited to 5 req/s to avoid hammering
PostgREST. Expected runtime: ~30s for ~120 rows.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ENV_FILE = "/srv/BusinessOps/tools/.supabase-creditdoc.env"
OUT_DIR = Path(__file__).parent.parent / "data"
OUT_CSV = OUT_DIR / "dangling_similar_lenders.csv"


def _psql(sql: str, timeout: int = 60) -> tuple[bool, str]:
    """Run a SQL statement via psql, piping the SQL on stdin so embedded
    newlines / single quotes don't get mangled by the shell."""
    cmd = (
        f"set -a && . {ENV_FILE} && set +a && "
        f"psql \"$SUPABASE_DB_URL\" -X -A -t -F '|' -f -"
    )
    proc = subprocess.run(
        ["bash", "-c", cmd], input=sql,
        capture_output=True, text=True, timeout=timeout,
    )
    if proc.returncode != 0:
        return False, (proc.stderr or proc.stdout or "psql failed").strip()
    return True, (proc.stdout or "").strip()


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Perform writes (needs Jammi greenlight).")
    args = ap.parse_args(argv)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Find all (row_slug, dead_ref_slug, reason) triples.
    sql = """
WITH refs AS (
  SELECT slug AS row_slug,
         jsonb_array_elements_text(body_inline->'similar_lenders') AS ref_slug
  FROM lenders
  WHERE jsonb_typeof(body_inline->'similar_lenders') = 'array'
)
SELECT r.row_slug, r.ref_slug,
  CASE
    WHEN e.slug IS NULL THEN 'missing'
    WHEN e.processing_status <> 'ready_for_index' THEN
      'status:' || COALESCE(e.processing_status, 'null')
    ELSE 'ok'
  END AS reason
FROM refs r
LEFT JOIN lenders e ON r.ref_slug = e.slug;
"""
    ok, out = _psql(sql)
    if not ok:
        print(f"ERROR: psql failed — {out}", file=sys.stderr)
        return 2

    rows = [line.split("|") for line in out.splitlines() if line.strip()]
    dead = [(r[0], r[1], r[2]) for r in rows if len(r) == 3 and r[2] != "ok"]
    rows_affected = sorted({r[0] for r in dead})

    # Top-N dead-ref slugs.
    from collections import Counter
    counter = Counter(r[1] for r in dead)
    top = counter.most_common(10)

    print(f"# CDM-REV dangling similar_lenders prune — DRY-RUN" if not args.apply
          else "# CDM-REV dangling similar_lenders prune — APPLY")
    print(f"# refs scanned: {len(rows)}")
    print(f"# dead refs:    {len(dead)}")
    print(f"# rows touched: {len(rows_affected)}")
    print(f"# top dead-ref slugs (by count):")
    for slug, n in top:
        print(f"    {slug:50s}  {n}")

    with open(OUT_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["row_slug", "dead_ref_slug", "reason"])
        for r in dead:
            w.writerow(r)
    print(f"\n# CSV: {OUT_CSV}")

    if not args.apply:
        print("\n# DRY-RUN — no DB writes. Pass --apply to prune (needs Jammi greenlight).")
        return 0

    # Step 2: Apply pruning per row, one UPDATE each.
    print("\n# APPLY mode — pruning...")
    by_row: dict[str, set[str]] = {}
    for (row_slug, ref_slug, _reason) in dead:
        by_row.setdefault(row_slug, set()).add(ref_slug)

    success = 0
    failed = 0
    for i, (row_slug, dead_set) in enumerate(by_row.items(), 1):
        # Filter the array in-place via SQL — preserves remaining order.
        # Use array constructor to avoid jsonb_set on path-into-array quirks.
        dead_list = json.dumps(sorted(dead_set))
        prune_sql = (
            "UPDATE lenders "
            "SET body_inline = jsonb_set("
            "  body_inline, '{similar_lenders}', "
            "  COALESCE(("
            "    SELECT jsonb_agg(elem) "
            "    FROM jsonb_array_elements_text(body_inline->'similar_lenders') AS elem "
            f"   WHERE elem NOT IN (SELECT jsonb_array_elements_text('{dead_list}'::jsonb))"
            "  ), '[]'::jsonb)"
            "), updated_at = clock_timestamp() "
            f"WHERE slug = '{row_slug}' RETURNING slug;"
        )
        ok, out = _psql(prune_sql, timeout=15)
        if ok and out:
            success += 1
        else:
            failed += 1
            print(f"  FAIL {row_slug}: {out[:120]}", file=sys.stderr)
        # Pace at 5 req/s.
        if i % 5 == 0:
            time.sleep(1)

    print(f"\n# done — success={success} failed={failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
