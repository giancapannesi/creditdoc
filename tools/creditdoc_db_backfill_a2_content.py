#!/usr/bin/env python3
"""
CDM-REV-2026-04-29 — Stage A.2 backfill (wellness_guides + comparisons + brands).

DRY-RUN BY DEFAULT. Requires --apply --i-have-jammi-greenlight to write.

Reads:
  src/content/wellness-guides.json   (list of 81 — wellness_guides)
  src/content/comparisons.json       (list of 165 — comparisons)
  src/content/brands/*.json          (57 files — brands)

Writes to (already-created empty) Postgres tables:
  public.wellness_guides
  public.comparisons
  public.brands

Strip-nulls policy: all `\u0000` bytes recursively removed before COPY (jsonb rejects them — same fix used for A.1).

Usage:
  python3 tools/creditdoc_db_backfill_a2_content.py
  python3 tools/creditdoc_db_backfill_a2_content.py --apply --i-have-jammi-greenlight
"""

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = REPO_ROOT / ".env"
SUPABASE_ENV = Path("/srv/BusinessOps/tools/.supabase-creditdoc.env")


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


def _psql_conn() -> str:
    env = _load_env(SUPABASE_ENV)
    if not env:
        env = _load_env(ENV_PATH)
    host = env.get("SUPABASE_DB_HOST", "")
    pw = env.get("SUPABASE_DB_PASSWORD", "")
    if not host or not pw:
        sys.stderr.write("ERROR: SUPABASE_DB_HOST / SUPABASE_DB_PASSWORD missing\n")
        sys.exit(2)
    return f"postgresql://postgres:{pw}@{host}:5432/postgres?sslmode=require"


def strip_nulls(obj):
    """Recursively strip \u0000 from any string in a JSON-shaped value."""
    if isinstance(obj, str):
        return obj.replace("\u0000", "")
    if isinstance(obj, dict):
        return {k: strip_nulls(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [strip_nulls(v) for v in obj]
    return obj


def _run_psql(conn: str, sql: str, timeout: int = 60) -> tuple[int, str, str]:
    proc = subprocess.run(
        ["psql", conn, "-tA", "-c", sql],
        capture_output=True, text=True, timeout=timeout,
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def _copy_csv(conn: str, table: str, columns: list[str], csv_path: Path) -> tuple[bool, str]:
    cols = ",".join(columns)
    cmd = f"\\copy {table}({cols}) FROM '{csv_path}' CSV HEADER"
    proc = subprocess.run(
        ["psql", conn, "-c", cmd],
        capture_output=True, text=True, timeout=600,
    )
    if proc.returncode != 0:
        return False, proc.stderr.strip()
    return True, proc.stdout.strip()


# ---------- Wellness guides ----------

def scan_wellness() -> list[dict]:
    src = REPO_ROOT / "src" / "content" / "wellness-guides.json"
    data = json.loads(src.read_text(encoding="utf-8"))
    rows = []
    for obj in data:
        slug = obj.get("slug")
        if not slug:
            continue
        title = obj.get("title", "")
        category = obj.get("category", "")
        body = strip_nulls(obj)
        body_compact = json.dumps(body, separators=(",", ":"), ensure_ascii=False)
        rows.append({
            "slug": slug,
            "title": title,
            "category": category,
            "body_inline": body_compact,
        })
    return rows


# ---------- Comparisons ----------

def scan_comparisons() -> list[dict]:
    src = REPO_ROOT / "src" / "content" / "comparisons.json"
    data = json.loads(src.read_text(encoding="utf-8"))
    rows = []
    for obj in data:
        slug = obj.get("slug")
        if not slug:
            continue
        body = strip_nulls(obj)
        body_compact = json.dumps(body, separators=(",", ":"), ensure_ascii=False)
        rows.append({
            "slug": slug,
            "lender_a": obj.get("lender_a", ""),
            "lender_b": obj.get("lender_b", ""),
            "body_inline": body_compact,
        })
    return rows


# ---------- Brands ----------

def scan_brands() -> list[dict]:
    src_dir = REPO_ROOT / "src" / "content" / "brands"
    rows = []
    for p in sorted(src_dir.glob("*.json")):
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        slug = obj.get("slug") or p.stem
        body = strip_nulls(obj)
        body_compact = json.dumps(body, separators=(",", ":"), ensure_ascii=False)
        rows.append({
            "slug": slug,
            "display_name": obj.get("display_name", ""),
            "category": obj.get("category", ""),
            "body_inline": body_compact,
        })
    return rows


# ---------- Common writer ----------

def write_csv(rows: list[dict], cols: list[str], out_path: Path) -> int:
    with out_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, quoting=csv.QUOTE_ALL)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})
    return len(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--i-have-jammi-greenlight", action="store_true")
    args = ap.parse_args()

    print("=" * 60)
    print("CDM-REV Stage A.2 backfill — wellness + comparisons + brands")
    print("=" * 60)

    wellness = scan_wellness()
    comparisons = scan_comparisons()
    brands = scan_brands()
    print(f"Wellness guides: {len(wellness)}")
    print(f"Comparisons:     {len(comparisons)}")
    print(f"Brands:          {len(brands)}")

    csv_dir = REPO_ROOT / "tmp_a2_csv"
    csv_dir.mkdir(exist_ok=True)
    wellness_csv = csv_dir / "wellness.csv"
    comparisons_csv = csv_dir / "comparisons.csv"
    brands_csv = csv_dir / "brands.csv"

    write_csv(wellness, ["slug", "title", "category", "body_inline"], wellness_csv)
    write_csv(comparisons, ["slug", "lender_a", "lender_b", "body_inline"], comparisons_csv)
    write_csv(brands, ["slug", "display_name", "category", "body_inline"], brands_csv)
    print(f"Wrote: {wellness_csv} / {comparisons_csv} / {brands_csv}")

    if not args.apply:
        print("DRY-RUN. Re-run with --apply --i-have-jammi-greenlight to write to DB.")
        return
    if not args.i_have_jammi_greenlight:
        sys.exit("REFUSED: --apply requires --i-have-jammi-greenlight")

    conn = _psql_conn()
    plan = [
        ("public.wellness_guides", ["slug", "title", "category", "body_inline"], wellness_csv, len(wellness)),
        ("public.comparisons", ["slug", "lender_a", "lender_b", "body_inline"], comparisons_csv, len(comparisons)),
        ("public.brands", ["slug", "display_name", "category", "body_inline"], brands_csv, len(brands)),
    ]
    for table, cols, path, expected in plan:
        print(f"\nApplying → {table}")
        # Pre-flight: verify table exists and is empty
        rc, out, err = _run_psql(conn, f"SELECT COUNT(*) FROM {table};")
        if rc != 0:
            sys.exit(f"  pre-check failed: {err}")
        existing = int(out)
        if existing != 0:
            sys.exit(f"  REFUSED: {table} already has {existing} rows — refusing to double-load")
        ok, msg = _copy_csv(conn, table, cols, path)
        if not ok:
            sys.exit(f"  COPY failed: {msg}")
        print(f"  COPY: {msg}")
        rc, out, err = _run_psql(conn, f"SELECT COUNT(*) FROM {table};")
        loaded = int(out) if out else -1
        print(f"  Loaded rows: {loaded} (expected {expected})")
        if loaded != expected:
            sys.exit(f"  ROW COUNT MISMATCH: {loaded} vs {expected}")
    print("\nA.2 backfill complete.")


if __name__ == "__main__":
    main()
