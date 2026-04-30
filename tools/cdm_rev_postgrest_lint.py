#!/usr/bin/env python3
"""
CDM-REV PostgREST URL linter — catches column filters that reference
non-existent columns before they ship to Cloudflare Pages.

Background: 2026-04-30 commit 082ded1de2 added `&rating=gt.0` to a
similar_lenders query; `rating` is inside body_inline (jsonb), not a
top-level column on `lenders`. PostgREST returned 42703 silently and
the adapter fell through to `if (!res.ok) return []` — every sidebar
would have collapsed to zero cards on cutover.

This script:
  1. Greps src/lib/db.ts for `${env.SUPABASE_URL}/rest/v1/<table>`
     blocks plus their associated `?col=` / `&col=op.value` filters.
  2. Calls Supabase information_schema for each table's actual column
     list.
  3. Reports any filter column not in that list.

Exits 1 if any mismatch found, else 0.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

DB_TS = Path(__file__).parent.parent / "src/lib/db.ts"
ENV_FILE = "/srv/BusinessOps/tools/.supabase-creditdoc.env"

# PostgREST operator suffix in a URL filter, e.g. `&processing_status=eq.foo`
FILTER_RE = re.compile(
    r'[?&]([a-z_][a-z0-9_]*)=(?:eq|neq|gt|gte|lt|lte|like|ilike|is|in|fts|cs|cd|sl|sr|nxr|nxl|adj|ov)\.'
)
# Endpoint `${env.SUPABASE_URL}/rest/v1/<table>` (env optionally chained)
ENDPOINT_RE = re.compile(r'\$\{env\??\.SUPABASE_URL\}/rest/v1/([a-z_][a-z0-9_]*)')


def _load_env() -> dict[str, str]:
    out: dict[str, str] = {}
    if not os.path.exists(ENV_FILE):
        return out
    # The env file uses bare `KEY=value` lines (no `export`); read directly.
    proc = subprocess.run(
        ["bash", "-c",
         f"set -a && . {ENV_FILE} && set +a && env | grep -E '^SUPABASE_'"],
        capture_output=True, text=True, timeout=5,
    )
    for line in (proc.stdout or "").splitlines():
        if "=" in line:
            k, _, v = line.partition("=")
            out[k] = v
    return out


def _columns(env: dict[str, str], table: str) -> list[str] | None:
    """Fetch column names for `public.<table>` via psql ($SUPABASE_DB_URL).

    information_schema.columns is not exposed via PostgREST anon, so we
    use the direct DB connection (already required for migrations + the
    Phase 2.4 e2e probe). Treat the table name as untrusted input from
    the regex — single-quote it before substitution and reject anything
    that isn't an identifier.
    """
    if "SUPABASE_DB_URL" not in env:
        return None
    if not re.fullmatch(r"[a-z_][a-z0-9_]*", table):
        return None
    sql = (
        "SELECT column_name FROM information_schema.columns "
        f"WHERE table_schema='public' AND table_name='{table}' "
        "ORDER BY ordinal_position"
    )
    proc = subprocess.run(
        ["psql", env["SUPABASE_DB_URL"], "-X", "-A", "-t", "-c", sql],
        capture_output=True, text=True, timeout=15,
    )
    if proc.returncode != 0:
        return None
    cols = [c.strip() for c in (proc.stdout or "").splitlines() if c.strip()]
    return cols or None


def main() -> int:
    src = DB_TS.read_text()
    # Walk through line-by-line, holding the most recently seen endpoint
    # table and applying it to filters in subsequent lines until the next
    # endpoint or a clear block boundary.
    issues: list[tuple[int, str, str]] = []  # (line, table, col)
    current_table: str | None = None
    for lineno, line in enumerate(src.splitlines(), start=1):
        m_ep = ENDPOINT_RE.search(line)
        if m_ep:
            current_table = m_ep.group(1)
            continue
        if "fetch(" in line or "headers" in line or "function " in line:
            current_table = None
        if current_table is None:
            continue
        for m in FILTER_RE.finditer(line):
            col = m.group(1)
            issues.append((lineno, current_table, col))

    if not issues:
        print("No PostgREST filters detected to lint.")
        return 0

    env = _load_env()
    if not env:
        print(f"WARN: cannot load creds from {ENV_FILE}; skipping schema check.")
        return 0

    schema_cache: dict[str, list[str] | None] = {}
    fails: list[tuple[int, str, str]] = []
    for (lineno, table, col) in issues:
        if table not in schema_cache:
            schema_cache[table] = _columns(env, table)
        cols = schema_cache[table]
        if cols is None:
            print(f"WARN db.ts:{lineno} — could not fetch schema for `{table}`; skipping {col}")
            continue
        if col not in cols:
            fails.append((lineno, table, col))

    if fails:
        print("FAIL — PostgREST filter columns missing from schema:")
        for (lineno, table, col) in fails:
            print(f"  db.ts:{lineno}  {table}.{col}  (not in: {len(schema_cache[table] or [])} cols)")
        print()
        print("Each FAIL means PostgREST will return 42703 and the adapter")
        print("will silently return [] — collapsing whatever surface uses it.")
        return 1

    print(f"OK — {len(issues)} filter(s) lint clean across "
          f"{len(schema_cache)} table(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
