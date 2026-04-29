#!/usr/bin/env python3
"""
verify_strategic_objectives.py — CDM-REV-2026-04-29 goal-verification gate.

Read-only checks against the local repo + Supabase Postgres + Cloudflare Pages preview.
NEVER writes to live DB or live system. Safe to run from CI or hand.

Three checks:
  OBJ-1 — update-on-fly latency end-to-end probe (preview only). Measures the time
          from a probe row update on a preview-only side-table to globally-cached
          new HTML at preview URL. RED until Phase 1 ships /review/[slug] SSR;
          AMBER once SSR live but no revalidation; GREEN once Phase 2 ships.
  OBJ-2 — audit_log row-coverage check. Reads table size + trigger inventory via
          information_schema (read-only). RED if no triggers, AMBER if some,
          GREEN once every write-target table has the trigger attached.
  OBJ-3 — growth-readiness probe. Static-analysis: counts LOC required to add a
          parallel SSR JSON route given existing patterns. <50 LOC = GREEN.

Output: JSON to stdout. Posted to chat per Section A.6.

Usage:
  python3 tools/verify_strategic_objectives.py             # all checks
  python3 tools/verify_strategic_objectives.py --obj 1     # just OBJ-1
  python3 tools/verify_strategic_objectives.py --json-only # no human text

Exit codes:
  0 = all GREEN
  1 = any AMBER
  2 = any RED
  3 = check error
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = Path("/srv/BusinessOps/tools/.supabase-creditdoc.env")


@dataclass
class CheckResult:
    obj: str
    status: str  # GREEN | AMBER | RED | ERROR | NA
    summary: str
    detail: dict = field(default_factory=dict)


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


def _psql(env: dict, sql: str, timeout: int = 30) -> tuple[int, str, str]:
    """Read-only psql call via Supabase direct connection. Returns (rc, stdout, stderr)."""
    db_host = env.get("SUPABASE_DB_HOST", "")
    db_password = env.get("SUPABASE_DB_PASSWORD", "")
    if not db_host or not db_password:
        return 1, "", "missing SUPABASE_DB_HOST or SUPABASE_DB_PASSWORD"
    conn = f"postgresql://postgres:{db_password}@{db_host}:5432/postgres?sslmode=require"
    try:
        proc = subprocess.run(
            ["psql", conn, "-tA", "-c", sql],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except FileNotFoundError:
        return 1, "", "psql not installed"
    except subprocess.TimeoutExpired:
        return 1, "", f"timeout after {timeout}s"


# ---------------------------------------------------------------------------
# OBJ-1 — Update-on-fly latency
# ---------------------------------------------------------------------------
def check_obj1(env: dict) -> CheckResult:
    """
    Detects mode + reports without performing any live edits.
    Phase gates:
      - astro.config.mjs `output: 'static'` AND no @astrojs/cloudflare → RED
      - hybrid+CF adapter present AND /review/[slug] has prerender=false → AMBER
      - revalidation Worker (/api/revalidate) reachable AND probe round-trip < 10s → GREEN
    """
    detail = {}
    astro_cfg = REPO_ROOT / "astro.config.mjs"
    pkg_json = REPO_ROOT / "package.json"
    review_page = REPO_ROOT / "src" / "pages" / "review" / "[slug].astro"
    revalidate_route = REPO_ROOT / "src" / "pages" / "api" / "revalidate.ts"

    cfg_text = astro_cfg.read_text() if astro_cfg.exists() else ""
    pkg_text = pkg_json.read_text() if pkg_json.exists() else ""
    review_text = review_page.read_text() if review_page.exists() else ""

    is_static = "output: 'static'" in cfg_text or 'output: "static"' in cfg_text
    is_hybrid = "output: 'hybrid'" in cfg_text or 'output: "hybrid"' in cfg_text
    has_cf_adapter_dep = "@astrojs/cloudflare" in pkg_text
    review_is_ssr = "prerender = false" in review_text or "prerender=false" in review_text
    has_revalidate_route = revalidate_route.exists()

    detail.update(
        astro_output="hybrid" if is_hybrid else ("static" if is_static else "unknown"),
        cf_adapter_installed=has_cf_adapter_dep,
        review_slug_ssr=review_is_ssr,
        revalidate_endpoint_present=has_revalidate_route,
    )

    if is_static and not has_cf_adapter_dep:
        return CheckResult(
            obj="OBJ-1",
            status="RED",
            summary="Static output. Every change requires full rebuild + git push. No on-the-fly updates.",
            detail=detail,
        )

    if is_hybrid and has_cf_adapter_dep and review_is_ssr and not has_revalidate_route:
        return CheckResult(
            obj="OBJ-1",
            status="AMBER",
            summary="Hybrid + SSR pilot route shipped. Revalidation endpoint not yet wired — DB writes do not invalidate cache.",
            detail=detail,
        )

    if is_hybrid and has_cf_adapter_dep and review_is_ssr and has_revalidate_route:
        # Phase 2 ship — could probe an end-to-end edit but that touches live DB.
        # Verifier remains read-only; mark AMBER until Phase 2 acceptance probe documented.
        # Acceptance gate must show p95 ≤ 10s in a phase-2 commit-tagged run.
        return CheckResult(
            obj="OBJ-1",
            status="AMBER",
            summary="Hybrid + SSR + revalidate endpoint present. Run Phase 2 acceptance probe to upgrade to GREEN.",
            detail=detail,
        )

    return CheckResult(
        obj="OBJ-1",
        status="RED",
        summary="Mixed/incomplete state — re-check astro.config.mjs and /review/[slug].astro.",
        detail=detail,
    )


# ---------------------------------------------------------------------------
# OBJ-2 — audit_log row-coverage
# ---------------------------------------------------------------------------
def check_obj2(env: dict) -> CheckResult:
    """
    Read-only inventory:
      - audit_log table exists?
      - fn_audit_row() function exists?
      - which write-target tables have audit trigger attached?
    """
    detail = {}
    rc, out, err = _psql(
        env,
        """SELECT to_regclass('public.audit_log') IS NOT NULL,
                  EXISTS (
                    SELECT 1 FROM pg_proc p
                    JOIN pg_namespace n ON n.oid = p.pronamespace
                    WHERE n.nspname='public' AND p.proname='fn_audit_row'
                  );""",
    )
    if rc != 0:
        return CheckResult(
            obj="OBJ-2",
            status="ERROR",
            summary=f"psql failed: {err or 'unknown'}",
            detail={"rc": rc, "stderr": err},
        )
    parts = out.split("|") if "|" in out else out.split()
    table_present = parts[0].strip().lower() in ("t", "true") if parts else False
    fn_present = parts[1].strip().lower() in ("t", "true") if len(parts) > 1 else False
    detail["audit_log_table"] = table_present
    detail["fn_audit_row_function"] = fn_present

    # Which write-target tables have audit trigger?
    write_targets = ("lenders", "cluster_answers", "lead_captures", "user_quiz_responses")
    rc, out, err = _psql(
        env,
        f"""SELECT event_object_table
            FROM information_schema.triggers
            WHERE trigger_schema='public'
              AND action_statement ILIKE '%fn_audit_row%'
              AND event_object_table IN ({", ".join("'"+t+"'" for t in write_targets)});""",
    )
    triggered = set()
    if rc == 0 and out:
        triggered = {line.strip() for line in out.splitlines() if line.strip()}
    detail["write_target_tables"] = list(write_targets)
    detail["triggered_tables"] = sorted(triggered)
    detail["coverage"] = f"{len(triggered)}/{len(write_targets)}"

    # row count
    rc, out, _ = _psql(env, "SELECT COUNT(*) FROM public.audit_log;")
    if rc == 0 and out.isdigit():
        detail["audit_log_rows"] = int(out)

    if not table_present:
        return CheckResult(
            obj="OBJ-2",
            status="RED",
            summary="audit_log table missing.",
            detail=detail,
        )
    if not fn_present or not triggered:
        return CheckResult(
            obj="OBJ-2",
            status="RED",
            summary="audit_log table exists but fn_audit_row missing or no triggers attached. Phase 3.1 not yet executed.",
            detail=detail,
        )
    if len(triggered) < len(write_targets):
        return CheckResult(
            obj="OBJ-2",
            status="AMBER",
            summary=f"Partial trigger coverage: {len(triggered)}/{len(write_targets)} write-target tables.",
            detail=detail,
        )
    return CheckResult(
        obj="OBJ-2",
        status="GREEN",
        summary=f"Full trigger coverage: {len(triggered)}/{len(write_targets)} write-target tables.",
        detail=detail,
    )


# ---------------------------------------------------------------------------
# OBJ-3 — Growth-readiness LOC probe
# ---------------------------------------------------------------------------
def check_obj3(env: dict) -> CheckResult:
    """
    Static analysis. How many LOC to add a parallel SSR JSON route?
    Reference pattern: /api/lender/[slug].json mirroring /review/[slug].astro.
    Counts:
      - SSR helper: 1 file ~25 LOC if shared db helper exists, ~80 LOC if not
      - new route file: ~20 LOC
      - cache+revalidate wiring: 0 LOC if shared with existing handler
    """
    detail = {}
    review_page = REPO_ROOT / "src" / "pages" / "review" / "[slug].astro"
    db_helper = REPO_ROOT / "src" / "lib" / "db.ts"
    revalidate_route = REPO_ROOT / "src" / "pages" / "api" / "revalidate.ts"
    cache_helper = REPO_ROOT / "src" / "lib" / "cache.ts"

    has_review = review_page.exists()
    has_db_helper = db_helper.exists()
    has_revalidate = revalidate_route.exists()
    has_cache = cache_helper.exists()

    detail["review_page"] = has_review
    detail["db_helper"] = has_db_helper
    detail["revalidate_route"] = has_revalidate
    detail["cache_helper"] = has_cache

    estimated_loc = 0
    if has_review:
        estimated_loc += 20  # new page file
    else:
        estimated_loc += 60
    if not has_db_helper:
        estimated_loc += 60
    if not has_cache:
        estimated_loc += 25

    detail["estimated_loc_for_new_ssr_route"] = estimated_loc

    if estimated_loc <= 50 and has_review and has_db_helper and has_cache:
        return CheckResult(
            obj="OBJ-3",
            status="GREEN",
            summary=f"New SSR route can be added in ~{estimated_loc} LOC. Patterns + helpers in place.",
            detail=detail,
        )
    if has_review and (has_db_helper or has_cache):
        return CheckResult(
            obj="OBJ-3",
            status="AMBER",
            summary=f"New SSR route ~{estimated_loc} LOC — over the 50 LOC bar. Helpers partial.",
            detail=detail,
        )
    return CheckResult(
        obj="OBJ-3",
        status="RED",
        summary=f"No SSR pilot route yet — add-route cost ~{estimated_loc} LOC. Phase 1 not shipped.",
        detail=detail,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--obj", type=int, choices=[1, 2, 3])
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args(argv)

    env = _load_env(ENV_FILE)
    results: list[CheckResult] = []

    try:
        if args.obj in (None, 1):
            results.append(check_obj1(env))
        if args.obj in (None, 2):
            results.append(check_obj2(env))
        if args.obj in (None, 3):
            results.append(check_obj3(env))
    except Exception as exc:  # pragma: no cover
        print(json.dumps({"error": str(exc)}))
        return 3

    payload = {
        "plan": "CDM-REV-2026-04-29",
        "ts": int(time.time()),
        "results": [asdict(r) for r in results],
    }
    print(json.dumps(payload, indent=2))

    if not args.json_only:
        print("\n--- summary ---", file=sys.stderr)
        for r in results:
            print(f"  {r.obj}: {r.status} — {r.summary}", file=sys.stderr)

    statuses = {r.status for r in results}
    if "ERROR" in statuses:
        return 3
    if "RED" in statuses:
        return 2
    if "AMBER" in statuses:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
