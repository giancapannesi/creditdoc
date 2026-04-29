#!/usr/bin/env python3
"""
CDM-REV-2026-04-29 — Stage A.4 backfill (blog_posts + listicles + answers + specials).

DRY-RUN BY DEFAULT. Requires --apply --i-have-jammi-greenlight to write.

Reads:
  src/content/blog-posts.json         (list of 34)
  src/content/listicles.json          (list of 26)
  src/content/answers/*.json          (14 files)
  src/content/specials.json           (list of 3)

Writes to (already-created empty) Postgres tables:
  public.blog_posts        PK = slug
  public.listicles         PK = slug
  public.answers           PK = slug
  public.specials          PK = uuid (auto), unique (lender_slug, deal_title)

Strip-nulls policy: all `\u0000` bytes recursively removed before COPY (jsonb
rejects them — same fix used for A.1/A.2/A.3).

Pre-flight refuses to load if target table is non-empty.

Usage:
  python3 tools/creditdoc_db_backfill_a4_content.py
  python3 tools/creditdoc_db_backfill_a4_content.py --apply --i-have-jammi-greenlight
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


# ---------- Blog posts ----------

def scan_blog_posts() -> list[dict]:
    src = REPO_ROOT / "src" / "content" / "blog-posts.json"
    data = json.loads(src.read_text(encoding="utf-8"))
    rows = []
    for obj in data:
        slug = obj.get("slug")
        if not slug:
            continue
        body = strip_nulls(obj)
        body_compact = json.dumps(body, separators=(",", ":"), ensure_ascii=False)
        publish_date = obj.get("publish_date") or ""
        # Normalize to YYYY-MM-DD or empty (Postgres date column accepts NULL via empty)
        rows.append({
            "slug": slug,
            "title": obj.get("title", ""),
            "category": obj.get("category", ""),
            "status": obj.get("status", "published") or "published",
            "publish_date": publish_date,
            "body_inline": body_compact,
        })
    return rows


# ---------- Listicles ----------

def scan_listicles() -> list[dict]:
    src = REPO_ROOT / "src" / "content" / "listicles.json"
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
            "title": obj.get("title", ""),
            "target_keyword": obj.get("target_keyword", ""),
            "category": obj.get("category", ""),
            "body_inline": body_compact,
        })
    return rows


# ---------- Answers ----------

def scan_answers() -> list[dict]:
    src_dir = REPO_ROOT / "src" / "content" / "answers"
    rows = []
    for p in sorted(src_dir.glob("*.json")):
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  WARN: skip {p.name}: {e}", file=sys.stderr)
            continue
        slug = obj.get("slug") or p.stem
        body = strip_nulls(obj)
        body_compact = json.dumps(body, separators=(",", ":"), ensure_ascii=False)
        rows.append({
            "slug": slug,
            "title": obj.get("title", "") or obj.get("h1", ""),
            "cluster_id": obj.get("cluster_id", ""),
            "cluster_pillar": obj.get("cluster_pillar", ""),
            "banner_category": obj.get("banner_category", ""),
            "target_money_page": obj.get("target_money_page", ""),
            "compliance_score": obj.get("compliance_score", "") if obj.get("compliance_score") is not None else "",
            "compliance_passed": "t" if obj.get("compliance_passed") else "f",
            "body_inline": body_compact,
        })
    return rows


# ---------- Specials ----------

def scan_specials() -> list[dict]:
    src = REPO_ROOT / "src" / "content" / "specials.json"
    data = json.loads(src.read_text(encoding="utf-8"))
    rows = []
    for obj in data:
        lender_slug = obj.get("lender_slug")
        deal_title = obj.get("deal_title")
        if not lender_slug or not deal_title:
            continue
        body = strip_nulls(obj)
        body_compact = json.dumps(body, separators=(",", ":"), ensure_ascii=False)
        rows.append({
            "lender_slug": lender_slug,
            "deal_title": deal_title,
            "valid_until": obj.get("valid_until", "") or "",
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
    print("CDM-REV Stage A.4 backfill — blog + listicles + answers + specials")
    print("=" * 60)

    blog = scan_blog_posts()
    listicles = scan_listicles()
    answers = scan_answers()
    specials = scan_specials()
    print(f"Blog posts:      {len(blog)}")
    print(f"Listicles:       {len(listicles)}")
    print(f"Answers:         {len(answers)}")
    print(f"Specials:        {len(specials)}")

    csv_dir = REPO_ROOT / "tmp_a4_csv"
    csv_dir.mkdir(exist_ok=True)
    blog_csv = csv_dir / "blog.csv"
    listicles_csv = csv_dir / "listicles.csv"
    answers_csv = csv_dir / "answers.csv"
    specials_csv = csv_dir / "specials.csv"

    write_csv(blog,
              ["slug", "title", "category", "status", "publish_date", "body_inline"],
              blog_csv)
    write_csv(listicles,
              ["slug", "title", "target_keyword", "category", "body_inline"],
              listicles_csv)
    write_csv(answers,
              ["slug", "title", "cluster_id", "cluster_pillar", "banner_category",
               "target_money_page", "compliance_score", "compliance_passed", "body_inline"],
              answers_csv)
    write_csv(specials,
              ["lender_slug", "deal_title", "valid_until", "body_inline"],
              specials_csv)
    print(f"Wrote: {blog_csv} / {listicles_csv} / {answers_csv} / {specials_csv}")

    if not args.apply:
        print("DRY-RUN. Re-run with --apply --i-have-jammi-greenlight to write to DB.")
        return
    if not args.i_have_jammi_greenlight:
        sys.exit("REFUSED: --apply requires --i-have-jammi-greenlight")

    conn = _psql_conn()
    plan = [
        ("public.blog_posts",
         ["slug", "title", "category", "status", "publish_date", "body_inline"],
         blog_csv, len(blog)),
        ("public.listicles",
         ["slug", "title", "target_keyword", "category", "body_inline"],
         listicles_csv, len(listicles)),
        ("public.answers",
         ["slug", "title", "cluster_id", "cluster_pillar", "banner_category",
          "target_money_page", "compliance_score", "compliance_passed", "body_inline"],
         answers_csv, len(answers)),
        ("public.specials",
         ["lender_slug", "deal_title", "valid_until", "body_inline"],
         specials_csv, len(specials)),
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
    print("\nA.4 backfill complete.")


if __name__ == "__main__":
    main()
