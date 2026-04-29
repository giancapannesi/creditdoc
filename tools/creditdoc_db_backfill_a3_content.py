#!/usr/bin/env python3
"""
CDM-REV-2026-04-29 — Stage A.3 backfill (states + categories + glossary_terms).

DRY-RUN BY DEFAULT. Requires --apply --i-have-jammi-greenlight to write.

Reads:
  src/content/states.json          (dict of 50 — keyed by state code 'AL'/'AK'/...)
  src/content/categories.json      (list of 18)
  src/content/glossary-terms.json  (list of 71)

Writes to (already-created empty) Postgres tables:
  public.states           PK = code (uppercase, 'AL')
  public.categories       PK = slug
  public.glossary_terms   PK = slug

Strip-nulls policy: all `\u0000` bytes recursively removed before COPY (jsonb
rejects them — same fix used for A.1/A.2).

Pre-flight refuses to load if target table is non-empty (defends against
double-loading after partial apply).

Usage:
  python3 tools/creditdoc_db_backfill_a3_content.py
  python3 tools/creditdoc_db_backfill_a3_content.py --apply --i-have-jammi-greenlight
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


# ---------- States ----------

def scan_states() -> list[dict]:
    src = REPO_ROOT / "src" / "content" / "states.json"
    data = json.loads(src.read_text(encoding="utf-8"))
    rows = []
    # states.json is keyed by uppercase state code → dict of facts
    for code, obj in data.items():
        if not isinstance(obj, dict):
            continue
        code_norm = code.strip().upper()
        if not code_norm:
            continue
        body = strip_nulls(obj)
        body_compact = json.dumps(body, separators=(",", ":"), ensure_ascii=False)
        rows.append({
            "code": code_norm,
            "name": obj.get("name", ""),
            "abbr": obj.get("abbr", code_norm),
            "body_inline": body_compact,
        })
    rows.sort(key=lambda r: r["code"])
    return rows


# ---------- Categories ----------

def scan_categories() -> list[dict]:
    src = REPO_ROOT / "src" / "content" / "categories.json"
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
            "name": obj.get("name", ""),
            "body_inline": body_compact,
        })
    return rows


# ---------- Glossary terms ----------

def scan_glossary() -> list[dict]:
    src = REPO_ROOT / "src" / "content" / "glossary-terms.json"
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
            "term": obj.get("term", ""),
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
    print("CDM-REV Stage A.3 backfill — states + categories + glossary_terms")
    print("=" * 60)

    states = scan_states()
    categories = scan_categories()
    glossary = scan_glossary()
    print(f"States:          {len(states)}")
    print(f"Categories:      {len(categories)}")
    print(f"Glossary terms:  {len(glossary)}")

    csv_dir = REPO_ROOT / "tmp_a3_csv"
    csv_dir.mkdir(exist_ok=True)
    states_csv = csv_dir / "states.csv"
    categories_csv = csv_dir / "categories.csv"
    glossary_csv = csv_dir / "glossary.csv"

    write_csv(states, ["code", "name", "abbr", "body_inline"], states_csv)
    write_csv(categories, ["slug", "name", "body_inline"], categories_csv)
    write_csv(glossary, ["slug", "term", "category", "body_inline"], glossary_csv)
    print(f"Wrote: {states_csv} / {categories_csv} / {glossary_csv}")

    if not args.apply:
        print("DRY-RUN. Re-run with --apply --i-have-jammi-greenlight to write to DB.")
        return
    if not args.i_have_jammi_greenlight:
        sys.exit("REFUSED: --apply requires --i-have-jammi-greenlight")

    conn = _psql_conn()
    plan = [
        ("public.states", ["code", "name", "abbr", "body_inline"], states_csv, len(states)),
        ("public.categories", ["slug", "name", "body_inline"], categories_csv, len(categories)),
        ("public.glossary_terms", ["slug", "term", "category", "body_inline"], glossary_csv, len(glossary)),
    ]
    for table, cols, path, expected in plan:
        print(f"\nApplying → {table}")
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
    print("\nA.3 backfill complete.")


if __name__ == "__main__":
    main()
