#!/usr/bin/env python3
"""
CDM-REV Phase 5.9.2 — pre-cutover row-count snapshot.

Captures the rollback-detection baseline: row counts + max(updated_at) per
table for the SSR-route-backing tables, plus a few sanity counters. Output
is JSON to backups/cdm_rev_pre_cutover_counts_<TS>.json (and stdout).

Use:
    python3 tools/cdm_rev_snapshot_counts.py
    python3 tools/cdm_rev_snapshot_counts.py --no-write   # stdout-only

Why:
    Phase 6 cutover gate §5.9.2. If a rollback is needed, you compare the
    snapshot taken just before the DNS flip against current state to detect
    "was anything written / lost during the failed cutover?" The MV row
    counts also let you verify state-aggregate refresh is healthy.

Env required:
    SUPABASE_URL, SUPABASE_ANON_KEY  — read-only via PostgREST + RLS

Reads:
    /srv/BusinessOps/tools/.supabase-creditdoc.env
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ENV_PATH = Path("/srv/BusinessOps/tools/.supabase-creditdoc.env")
DEFAULT_OUT_DIR = Path("/srv/BusinessOps/creditdoc/backups")

TABLES_WITH_UPDATED_AT = [
    "lenders",
    "answers",
    "listicles",
    "blog_posts",
    "wellness_guides",
    "states",
    "categories",
    "specials",
]

# Materialized views from migration A.5 — nullable in output if not yet applied.
OPTIONAL_MVS = [
    "state_lender_counts",
    "state_city_lender_counts",
]


def load_env() -> dict[str, str]:
    if not ENV_PATH.exists():
        sys.exit(f"missing {ENV_PATH}")
    out: dict[str, str] = {}
    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def pg_get(env: dict[str, str], path: str, prefer: str | None = None) -> tuple[int, dict | list]:
    """Single PostgREST GET. Returns (status, parsed_json_or_text)."""
    url = f"{env['SUPABASE_URL']}/rest/v1/{path}"
    req = Request(url)
    req.add_header("apikey", env["SUPABASE_ANON_KEY"])
    req.add_header("authorization", f"Bearer {env['SUPABASE_ANON_KEY']}")
    req.add_header("accept", "application/json")
    if prefer:
        req.add_header("prefer", prefer)
    try:
        with urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else None
    except HTTPError as e:
        return e.code, {"error": e.read().decode("utf-8", errors="replace")}
    except URLError as e:
        return 0, {"error": str(e.reason)}


def count_table(env: dict[str, str], table: str) -> dict[str, Any]:
    """Exact row count via PostgREST `count=exact` Range header.

    `table` can include filters: e.g. "lenders?processing_status=eq.ready_for_index".
    We append &select=*&limit=0 with the right separator.
    """
    sep = "&" if "?" in table else "?"
    url = f"{env['SUPABASE_URL']}/rest/v1/{table}{sep}select=*&limit=0"
    req = Request(url)
    req.add_header("apikey", env["SUPABASE_ANON_KEY"])
    req.add_header("authorization", f"Bearer {env['SUPABASE_ANON_KEY']}")
    req.add_header("prefer", "count=exact")
    req.add_header("range", "0-0")
    try:
        with urlopen(req, timeout=15) as resp:
            cr = resp.headers.get("content-range", "")
            # content-range: 0-0/N or */N
            total = None
            if "/" in cr:
                tail = cr.split("/", 1)[1]
                if tail.isdigit():
                    total = int(tail)
            return {"status": resp.status, "row_count": total}
    except HTTPError as e:
        return {"status": e.code, "row_count": None, "error": e.read().decode("utf-8", errors="replace")[:200]}
    except URLError as e:
        return {"status": 0, "row_count": None, "error": str(e.reason)}


def max_updated_at(env: dict[str, str], table: str) -> str | None:
    """Most recent updated_at on a table (for staleness detection)."""
    status, body = pg_get(
        env,
        f"{table}?select=updated_at&order=updated_at.desc&limit=1",
    )
    if status != 200 or not isinstance(body, list) or not body:
        return None
    return body[0].get("updated_at")


def snapshot(env: dict[str, str]) -> dict[str, Any]:
    out: dict[str, Any] = {
        "snapshot_ts_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "supabase_url": env["SUPABASE_URL"],
        "tables": {},
        "mvs": {},
        "lenders_by_state_top10": [],
        "ready_for_index_count": None,
    }

    for t in TABLES_WITH_UPDATED_AT:
        c = count_table(env, t)
        # PostgREST returns 206 for ranged count requests — both are success.
        if c.get("status") in (200, 206):
            c["max_updated_at"] = max_updated_at(env, t)
        out["tables"][t] = c

    # ready_for_index — the publish gate for /r/[slug] + state pages.
    c = count_table(env, "lenders?processing_status=eq.ready_for_index")
    out["ready_for_index_count"] = c.get("row_count")

    for mv in OPTIONAL_MVS:
        c = count_table(env, mv)
        out["mvs"][mv] = c

    # If state_lender_counts exists, capture top-10 (early signal of state-page health).
    if out["mvs"].get("state_lender_counts", {}).get("status") in (200, 206):
        status, body = pg_get(
            env,
            "state_lender_counts?select=state_abbr,lender_count,city_count&order=lender_count.desc&limit=10",
        )
        if status == 200 and isinstance(body, list):
            out["lenders_by_state_top10"] = body

    return out


def main() -> int:
    write = "--no-write" not in sys.argv
    env = load_env()
    if not env.get("SUPABASE_URL") or not env.get("SUPABASE_ANON_KEY"):
        sys.exit("SUPABASE_URL or SUPABASE_ANON_KEY missing in .supabase-creditdoc.env")

    t0 = time.monotonic()
    snap = snapshot(env)
    snap["wall_seconds"] = round(time.monotonic() - t0, 2)

    if write:
        DEFAULT_OUT_DIR.mkdir(parents=True, exist_ok=True)
        ts = snap["snapshot_ts_utc"].replace(":", "").replace("-", "")[:15]
        out_path = DEFAULT_OUT_DIR / f"cdm_rev_pre_cutover_counts_{ts}.json"
        out_path.write_text(json.dumps(snap, indent=2, sort_keys=True) + "\n")
        snap["written_to"] = str(out_path)

    print(json.dumps(snap, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
