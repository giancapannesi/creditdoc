#!/usr/bin/env python3
"""
Sync local /answers/ JSON files into Supabase public.answers via UPSERT.

Why this exists:
  - creditdoc_cluster_executor.py writes SQLite cluster_answers + JSON files only.
  - On the new architecture (CDM-REV-2026-04-29), /answers/[slug] reads from
    Supabase. So new answers got stranded post-cutover.
  - A.4 backfill is one-shot (refuses on non-empty table). This script is the
    repeatable UPSERT path.

Usage:
  python3 tools/sync_cluster_answers_to_supabase.py            # dry-run
  python3 tools/sync_cluster_answers_to_supabase.py --apply    # write
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ANSWERS_DIR = REPO_ROOT / "src" / "content" / "answers"
SUPABASE_ENV = Path("/srv/BusinessOps/tools/.supabase-creditdoc.env")
ENV_PATH = REPO_ROOT / ".env"


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
    env = _load_env(SUPABASE_ENV) or _load_env(ENV_PATH)
    host = env.get("SUPABASE_DB_HOST", "")
    pw = env.get("SUPABASE_DB_PASSWORD", "")
    if not host or not pw:
        sys.stderr.write("ERROR: SUPABASE_DB_HOST / SUPABASE_DB_PASSWORD missing\n")
        sys.exit(2)
    return f"postgresql://postgres:{pw}@{host}:5432/postgres?sslmode=require"


def strip_nulls(obj):
    if isinstance(obj, str):
        return obj.replace("\u0000", "")
    if isinstance(obj, dict):
        return {k: strip_nulls(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [strip_nulls(v) for v in obj]
    return obj


def scan_local_answers() -> list[dict]:
    rows = []
    for p in sorted(ANSWERS_DIR.glob("*.json")):
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            sys.stderr.write(f"WARN: skip {p.name}: {e}\n")
            continue
        slug = obj.get("slug") or p.stem
        body = strip_nulls(obj)
        body_compact = json.dumps(body, separators=(",", ":"), ensure_ascii=False)
        rows.append({
            "slug": slug,
            "title": (obj.get("title") or obj.get("h1") or "").strip(),
            "cluster_id": obj.get("cluster_id") or "",
            "cluster_pillar": obj.get("cluster_pillar") or "",
            "banner_category": obj.get("banner_category") or "",
            "target_money_page": obj.get("target_money_page") or "",
            "compliance_score": obj.get("compliance_score"),
            "compliance_passed": bool(obj.get("compliance_passed")),
            "body_inline": body_compact,
        })
    return rows


def fetch_supabase_slugs(conn: str) -> set[str]:
    proc = subprocess.run(
        ["psql", conn, "-tA", "-c", "SELECT slug FROM public.answers ORDER BY slug;"],
        capture_output=True, text=True, timeout=30,
    )
    if proc.returncode != 0:
        sys.stderr.write(f"ERROR: psql select failed: {proc.stderr.strip()}\n")
        sys.exit(2)
    return {s.strip() for s in proc.stdout.splitlines() if s.strip()}


def upsert(conn: str, row: dict) -> tuple[bool, str]:
    sql = """
INSERT INTO public.answers
  (slug, title, cluster_id, cluster_pillar, banner_category, target_money_page,
   compliance_score, compliance_passed, body_inline)
VALUES (:slug, :title, :cluster_id, :cluster_pillar, :banner_category, :target_money_page,
        NULLIF(:compliance_score, '')::numeric, :compliance_passed::boolean, :body_inline::jsonb)
ON CONFLICT (slug) DO UPDATE SET
  title = EXCLUDED.title,
  cluster_id = EXCLUDED.cluster_id,
  cluster_pillar = EXCLUDED.cluster_pillar,
  banner_category = EXCLUDED.banner_category,
  target_money_page = EXCLUDED.target_money_page,
  compliance_score = EXCLUDED.compliance_score,
  compliance_passed = EXCLUDED.compliance_passed,
  body_inline = EXCLUDED.body_inline,
  updated_at = now();
"""
    params = [
        ("slug", row["slug"]),
        ("title", row["title"]),
        ("cluster_id", row["cluster_id"]),
        ("cluster_pillar", row["cluster_pillar"]),
        ("banner_category", row["banner_category"]),
        ("target_money_page", row["target_money_page"]),
        ("compliance_score", "" if row["compliance_score"] is None else str(row["compliance_score"])),
        ("compliance_passed", "true" if row["compliance_passed"] else "false"),
        ("body_inline", row["body_inline"]),
    ]
    cmd = ["psql", conn, "-v", "ON_ERROR_STOP=1"]
    for k, v in params:
        cmd += ["-v", f"{k}={v}"]
    bound = sql
    for k, v in params:
        bound = bound.replace(f":{k}", _quote_literal(v))
    proc = subprocess.run(
        ["psql", conn, "-v", "ON_ERROR_STOP=1", "-c", bound],
        capture_output=True, text=True, timeout=60,
    )
    if proc.returncode != 0:
        return False, proc.stderr.strip()
    return True, proc.stdout.strip()


def _quote_literal(v: str) -> str:
    if v == "":
        return "''"
    return "'" + v.replace("'", "''") + "'"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="actually write (default dry-run)")
    args = ap.parse_args()

    conn = _psql_conn()
    local = scan_local_answers()
    sb_slugs = fetch_supabase_slugs(conn)
    local_slugs = {r["slug"] for r in local}

    missing = sorted(local_slugs - sb_slugs)
    extra = sorted(sb_slugs - local_slugs)

    print(f"Local JSON answers: {len(local)}")
    print(f"Supabase answers:   {len(sb_slugs)}")
    print(f"Missing from Supabase: {len(missing)}")
    for s in missing:
        print(f"  + {s}")
    if extra:
        print(f"In Supabase but no local JSON: {len(extra)}")
        for s in extra:
            print(f"  - {s}")

    if not args.apply:
        print("\nDRY RUN — no writes. Re-run with --apply to UPSERT missing rows.")
        return 0

    if not missing:
        print("\nNothing to do.")
        return 0

    print(f"\nApplying UPSERT for {len(missing)} slug(s)...")
    by_slug = {r["slug"]: r for r in local}
    failed = []
    for slug in missing:
        ok, msg = upsert(conn, by_slug[slug])
        status = "OK" if ok else "FAIL"
        print(f"  {status}  {slug}  {msg if not ok else ''}")
        if not ok:
            failed.append(slug)

    if failed:
        sys.stderr.write(f"\n{len(failed)} failure(s).\n")
        return 1
    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
