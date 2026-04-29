#!/usr/bin/env python3
"""
CDM-REV-2026-04-29 — body_inline backfill (Option A.1).

DOC-READY, DRY-RUN BY DEFAULT. DOES NOT WRITE WITHOUT --apply AND --i-have-jammi-greenlight.

Reads src/content/lenders/*.json, stages into lenders_body_staging via COPY,
then UPDATEs lenders.body_inline by slug. ~5 min for 20K rows.

Pre-requisite (run by Jammi or with explicit greenlight):
    ALTER TABLE public.lenders ADD COLUMN IF NOT EXISTS body_inline jsonb;
    ALTER TABLE public.lenders ADD COLUMN IF NOT EXISTS body_r2_key text;

Usage:
    # Dry-run (default, safe — counts + sample, no writes):
    python3 tools/creditdoc_db_backfill_body_inline.py

    # Generate CSV only (still no DB write):
    python3 tools/creditdoc_db_backfill_body_inline.py --build-csv

    # Apply (REQUIRES BOTH FLAGS, REQUIRES PRE-FLIGHT ALTER TABLE):
    python3 tools/creditdoc_db_backfill_body_inline.py --apply --i-have-jammi-greenlight

Rollback:
    ALTER TABLE public.lenders DROP COLUMN body_inline;
    ALTER TABLE public.lenders DROP COLUMN body_r2_key;

Verifier impact: writing body_inline does NOT flip OBJ-1 GREEN by itself —
the revalidation Worker (Phase 2.x) still needs to be wired so DB writes
invalidate the cache. This script is the data-layer prerequisite for the
/review/[slug] SSR cutover, not the latency mechanism.
"""

import argparse
import csv
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LENDERS_DIR = REPO_ROOT / "src" / "content" / "lenders"
ENV_PATH = REPO_ROOT / ".env"
STAGING_TABLE = "lenders_body_staging_cdm_rev"


def _load_env(path: Path) -> dict:
    env = {}
    if not path.exists():
        return env
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def _psql_conn(env: dict) -> str:
    host = env.get("SUPABASE_DB_HOST", "")
    pw = env.get("SUPABASE_DB_PASSWORD", "")
    if not host or not pw:
        sys.stderr.write("ERROR: SUPABASE_DB_HOST or SUPABASE_DB_PASSWORD missing in .env\n")
        sys.exit(2)
    return f"postgresql://postgres:{pw}@{host}:5432/postgres?sslmode=require"


def _run_psql(conn: str, sql: str, timeout: int = 60) -> tuple[int, str, str]:
    proc = subprocess.run(
        ["psql", conn, "-tA", "-c", sql],
        capture_output=True, text=True, timeout=timeout,
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


@dataclass
class ScanResult:
    files_total: int
    files_skipped: int
    files_ready: int
    bytes_total: int
    bytes_max: int
    largest_slug: str
    skipped_reasons: dict


def scan_lender_jsons() -> tuple[ScanResult, list[tuple[str, str]]]:
    """Scan src/content/lenders/*.json and return (stats, [(slug, json_compact_str), ...])."""
    if not LENDERS_DIR.is_dir():
        sys.stderr.write(f"ERROR: {LENDERS_DIR} not found\n")
        sys.exit(2)

    rows: list[tuple[str, str]] = []
    skipped_reasons: dict = {}
    files_total = files_skipped = files_ready = 0
    bytes_total = bytes_max = 0
    largest_slug = ""

    for p in sorted(LENDERS_DIR.glob("*.json")):
        files_total += 1
        slug = p.stem
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            files_skipped += 1
            reason = f"json_parse_error: {type(e).__name__}"
            skipped_reasons[reason] = skipped_reasons.get(reason, 0) + 1
            continue

        if not isinstance(obj, dict):
            files_skipped += 1
            skipped_reasons["not_object"] = skipped_reasons.get("not_object", 0) + 1
            continue

        compact = json.dumps(obj, separators=(",", ":"), ensure_ascii=False)
        size = len(compact.encode("utf-8"))
        rows.append((slug, compact))
        files_ready += 1
        bytes_total += size
        if size > bytes_max:
            bytes_max = size
            largest_slug = slug

    return ScanResult(
        files_total=files_total,
        files_skipped=files_skipped,
        files_ready=files_ready,
        bytes_total=bytes_total,
        bytes_max=bytes_max,
        largest_slug=largest_slug,
        skipped_reasons=skipped_reasons,
    ), rows


def build_csv(rows: list[tuple[str, str]], out_path: Path) -> int:
    """Write slug,json_compact CSV. Returns row count written."""
    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL)
        w.writerow(["slug", "body_inline"])
        for slug, body in rows:
            w.writerow([slug, body])
    return len(rows)


def precheck_columns(conn: str) -> tuple[bool, str]:
    """Verify body_inline column exists. Returns (ok, message)."""
    rc, out, err = _run_psql(
        conn,
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema='public' AND table_name='lenders' "
        "AND column_name IN ('body_inline','body_r2_key') ORDER BY column_name;",
    )
    if rc != 0:
        return False, f"psql error: {err}"
    cols = [c.strip() for c in out.split("\n") if c.strip()]
    if "body_inline" not in cols:
        return False, "body_inline column missing — run pre-flight ALTER TABLE first"
    return True, f"columns present: {cols}"


def apply_backfill(conn: str, csv_path: Path, dry_run_count_only: bool = False) -> dict:
    """
    Stages CSV into a temp table and UPDATEs lenders.body_inline by slug.
    Wraps in a single transaction. Returns counts.
    """
    sql_setup = f"""
DROP TABLE IF EXISTS {STAGING_TABLE};
CREATE TABLE {STAGING_TABLE} (slug text PRIMARY KEY, body_inline jsonb);
"""
    sql_apply = f"""
BEGIN;
  UPDATE public.lenders l
     SET body_inline = s.body_inline
    FROM {STAGING_TABLE} s
   WHERE l.slug = s.slug;
  SELECT COUNT(*) AS staging_rows FROM {STAGING_TABLE};
  SELECT COUNT(*) AS lenders_with_body FROM public.lenders WHERE body_inline IS NOT NULL;
COMMIT;
DROP TABLE {STAGING_TABLE};
"""
    rc, out, err = _run_psql(conn, sql_setup, timeout=30)
    if rc != 0:
        return {"ok": False, "stage": "setup", "error": err}

    # \copy must run via psql -c "\copy ..." or here-doc; use file mode
    copy_cmd = f"\\copy {STAGING_TABLE}(slug, body_inline) FROM '{csv_path}' CSV HEADER"
    proc = subprocess.run(
        ["psql", conn, "-c", copy_cmd],
        capture_output=True, text=True, timeout=600,
    )
    if proc.returncode != 0:
        return {"ok": False, "stage": "copy", "error": proc.stderr.strip()}
    copy_msg = proc.stdout.strip()

    if dry_run_count_only:
        rc, out, err = _run_psql(conn, f"SELECT COUNT(*) FROM {STAGING_TABLE};")
        _run_psql(conn, f"DROP TABLE {STAGING_TABLE};")
        return {"ok": True, "stage": "dry_run", "copied_rows": copy_msg, "staged": out}

    rc, out, err = _run_psql(conn, sql_apply, timeout=300)
    if rc != 0:
        return {"ok": False, "stage": "apply", "error": err}
    return {"ok": True, "stage": "apply", "copied_rows": copy_msg, "psql_out": out}


def main():
    ap = argparse.ArgumentParser(description="Backfill lenders.body_inline from src/content/lenders/*.json")
    ap.add_argument("--build-csv", action="store_true", help="Write CSV to ./tmp_body_inline_backfill.csv (no DB)")
    ap.add_argument("--apply", action="store_true", help="Run COPY + UPDATE (REQUIRES --i-have-jammi-greenlight)")
    ap.add_argument("--i-have-jammi-greenlight", action="store_true", help="Required gate flag for --apply")
    ap.add_argument("--csv", default="", help="Override CSV path")
    args = ap.parse_args()

    print("=" * 60)
    print("CDM-REV body_inline backfill — Option A.1")
    print("=" * 60)
    print(f"REPO_ROOT  = {REPO_ROOT}")
    print(f"LENDERS_DIR = {LENDERS_DIR}")
    print()

    print("[1/4] Scanning JSONs...")
    scan, rows = scan_lender_jsons()
    avg = scan.bytes_total / max(scan.files_ready, 1)
    print(f"  files_total = {scan.files_total}")
    print(f"  files_ready = {scan.files_ready}")
    print(f"  files_skipped = {scan.files_skipped}  reasons={scan.skipped_reasons}")
    print(f"  bytes_total = {scan.bytes_total:,} ({scan.bytes_total/1024/1024:.1f} MB)")
    print(f"  avg = {avg/1024:.1f} KB  max = {scan.bytes_max/1024:.1f} KB ({scan.largest_slug})")
    print()

    if scan.bytes_max > 60 * 1024:
        print(f"  WARNING: largest body {scan.bytes_max/1024:.1f} KB exceeds 60 KB — Option A.2 (R2 split) may be needed")
    if scan.bytes_total > 200 * 1024 * 1024:
        print(f"  WARNING: total {scan.bytes_total/1024/1024:.1f} MB — review Supabase free-tier 500 MB cap")

    csv_path = Path(args.csv) if args.csv else REPO_ROOT / "tmp_body_inline_backfill.csv"
    if args.build_csv or args.apply:
        print(f"[2/4] Writing CSV → {csv_path}")
        wrote = build_csv(rows, csv_path)
        print(f"  wrote {wrote} rows  ({csv_path.stat().st_size:,} bytes)")
        print()

    if not args.apply:
        print("[3/4] DRY RUN — exiting before any DB call.")
        print("To proceed: --apply --i-have-jammi-greenlight (after pre-flight ALTER TABLE)")
        return

    if not args.i_have_jammi_greenlight:
        print("[3/4] REFUSED — --apply requires --i-have-jammi-greenlight")
        sys.exit(3)

    env = _load_env(ENV_PATH)
    conn = _psql_conn(env)

    print("[3/4] Pre-flight column check...")
    ok, msg = precheck_columns(conn)
    print(f"  {msg}")
    if not ok:
        sys.exit(4)

    print("[4/4] Applying backfill...")
    result = apply_backfill(conn, csv_path)
    print(f"  result = {result}")
    if not result.get("ok"):
        sys.exit(5)
    print()
    print("Done. Re-run tools/verify_strategic_objectives.py to confirm.")


if __name__ == "__main__":
    main()
