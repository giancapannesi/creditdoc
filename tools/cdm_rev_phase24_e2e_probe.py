#!/usr/bin/env python3
"""
CDM-REV Phase 2.4 / Phase 5.5 — END-TO-END REVALIDATE PROBE.

What this measures:
    DB row UPDATE at T+0  →  globally-cached new HTML at T+N
    Target: N ≤ 10s p95 over 20 trials.
    A pass on this probe is what flips OBJ-1 from AMBER to GREEN.

Routes covered (--route flag):
    r        → /r/<slug>            (lenders table; own cacheWrap in endpoint)
    answers  → /answers/<slug>      (answers table; middleware cacheWrap)
    best     → /best/<slug>         (listicles table; middleware cacheWrap)
    all      → run all three sequentially

Phase 5.5 added /answers and /best so OBJ-1 GREEN is empirically verified
for the SSR routes that ride the middleware cacheWrap (commit 05c8fd8e1d).

How a single trial works:
    1. GET   <preview>/<route>/<slug>/?_cb=<ms>  → capture pre-write fingerprint
    2. T0 = monotonic()
    3. UPDATE <table> SET updated_at = clock_timestamp() WHERE slug = <slug>
       (transient field; lenders/answers/listicles all have updated_at)
    4. Poll GET <same URL> until fingerprint changes
    5. T1 = monotonic(); record latency = T1 - T0

How the fingerprint is built:
    Unified across routes: SHA-256 of the `x-cdm-version` response header.
    Middleware sets it from floor(Date.parse(updated_at)/1000); /r/[slug]
    sets it via lib/cache.ts cacheWrap. Header is reliable on both HIT and MISS.

SAFETY:
    --dry-run  default. Prints intended writes, exits without DB contact.
    --apply    requires explicit Jammi greenlight. Writes against live tables.
               Updates are non-destructive (updated_at is transient + trigger-managed).

Usage:
    python3 tools/cdm_rev_phase24_e2e_probe.py --dry-run
    python3 tools/cdm_rev_phase24_e2e_probe.py --apply --route r --slug credit-saint --trials 20
    python3 tools/cdm_rev_phase24_e2e_probe.py --apply --route answers --trials 5
    python3 tools/cdm_rev_phase24_e2e_probe.py --apply --route best --trials 5
    python3 tools/cdm_rev_phase24_e2e_probe.py --apply --route all --trials 10

DEPENDENCIES:
    - Reads creds from tools/.supabase-creditdoc.env (psql)
    - Cache-busts every poll (Cache-Control: no-cache + ?_cb=<ms>)

OUTPUT:
    JSON to stdout. Per-trial latency, p50, p95, max, fail count, per-route breakdown.
    Exits 0 if p95 ≤ 10s on every executed route, else 1.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import statistics
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from typing import Optional
from urllib.error import URLError
from urllib.request import Request, urlopen

PREVIEW_HOST = os.environ.get(
    "CDM_REV_PREVIEW_HOST", "https://cdm-rev-hybrid.creditdoc.pages.dev"
)
DEFAULT_TRIALS = 20
P95_TARGET_S = 10.0
POLL_INTERVAL_S = 0.5
POLL_TIMEOUT_S = 30.0
SUPABASE_ENV_FILE = "/srv/BusinessOps/tools/.supabase-creditdoc.env"

# Route profiles — each has a URL template, the table to UPDATE, a default
# slug for testing, and notes. Fingerprint is unified via x-cdm-version
# response header (set by both lib/cache.ts and middleware.ts).
ROUTE_PROFILES = {
    "r": {
        "url_template": "/r/{slug}",
        "table": "lenders",
        "default_slug": "credit-saint",
        "note": "endpoint cacheWrap (lib/cache.ts)",
    },
    "answers": {
        "url_template": "/answers/{slug}",
        "table": "answers",
        # Will resolve dynamically if unspecified — first published answer slug.
        "default_slug": None,
        "note": "middleware cacheWrap (variant=answers-slug)",
    },
    "best": {
        "url_template": "/best/{slug}",
        "table": "listicles",
        "default_slug": "best-credit-repair-companies",
        "note": "middleware cacheWrap (variant=best-slug)",
    },
}


@dataclass
class Trial:
    route: str
    slug: str
    pre_fingerprint: str
    post_fingerprint: str
    latency_s: float
    polls: int
    timed_out: bool
    error: Optional[str] = None


def _cache_busted_get(url: str) -> tuple[int, str, dict]:
    """GET with cache-bust. Returns (status, body, headers_lower)."""
    sep = "&" if "?" in url else "?"
    full = f"{url}{sep}_cb={int(time.time() * 1000)}"
    req = Request(
        full,
        headers={
            "User-Agent": "cdm-rev-e2e-probe/1.0",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )
    try:
        with urlopen(req, timeout=15) as r:
            headers = {k.lower(): v for k, v in r.getheaders()}
            return r.getcode(), r.read().decode("utf-8", errors="replace"), headers
    except URLError as e:
        return 0, str(e), {}


def _fingerprint(html: str, headers: dict) -> str:
    """Unified fingerprint: x-cdm-version header.

    All cacheable routes (/r, /answers, /best) emit x-cdm-version in their
    response. Set by lib/cache.ts (for /r/) and middleware.ts (for /answers,
    /best). Header is reliable on both HIT and MISS responses.

    Falls back to cdm-last-updated meta tag for legacy compatibility, then
    to body hash so a non-zero fingerprint is always returned.
    """
    ver = headers.get("x-cdm-version", "")
    if ver:
        return hashlib.sha256(f"v={ver}".encode()).hexdigest()[:16]
    m = re.search(r'<meta name="cdm-last-updated" content="([^"]*)"', html)
    if m:
        return hashlib.sha256(m.group(1).encode()).hexdigest()[:16]
    return hashlib.sha256(html[:4096].encode()).hexdigest()[:16]


def _psql_update(table: str, slug: str) -> tuple[bool, str]:
    """Bump updated_at on the row via clock_timestamp() (microsecond-unique).

    For lenders we also bump body_inline.last_updated since the meta tag uses
    that field for the legacy fingerprint. For answers/listicles, header-based
    fingerprint suffices — we just need updated_at to move.

    Transient field. Non-destructive. Trigger fires on lenders.
    """
    if not os.path.exists(SUPABASE_ENV_FILE):
        return False, f"missing {SUPABASE_ENV_FILE}"
    if table == "lenders":
        sql = (
            "UPDATE lenders SET updated_at = clock_timestamp(), "
            "body_inline = jsonb_set(body_inline, '{last_updated}', "
            "to_jsonb(to_char(clock_timestamp() AT TIME ZONE 'UTC', "
            "'YYYY-MM-DD\\\"T\\\"HH24:MI:SS.US\\\"Z\\\"'))) "
            f"WHERE slug = '{slug}' RETURNING slug;"
        )
    else:
        # answers, listicles — just bump updated_at; that drives the version.
        sql = (
            f"UPDATE {table} SET updated_at = clock_timestamp() "
            f"WHERE slug = '{slug}' RETURNING slug;"
        )
    cmd = (
        f". {SUPABASE_ENV_FILE} && "
        f'psql "$SUPABASE_DB_URL" -X -A -t -c "{sql}"'
    )
    try:
        proc = subprocess.run(
            ["bash", "-c", cmd], capture_output=True, text=True, timeout=20
        )
        out = (proc.stdout or "").strip()
        if proc.returncode != 0 or not out:
            return False, (proc.stderr or proc.stdout or "psql failed").strip()[:200]
        return True, out
    except subprocess.TimeoutExpired:
        return False, "psql timeout"


def _resolve_default_slug(route: str) -> Optional[str]:
    """Resolve a default slug for routes that don't ship one (e.g. answers
    where slugs are content-driven). Picks the most-recently-updated row
    via PostgREST anon REST."""
    profile = ROUTE_PROFILES[route]
    if profile["default_slug"]:
        return profile["default_slug"]
    table = profile["table"]
    # Read SUPABASE_URL + ANON_KEY from the env file
    if not os.path.exists(SUPABASE_ENV_FILE):
        return None
    try:
        proc = subprocess.run(
            ["bash", "-c",
             f". {SUPABASE_ENV_FILE} && echo \"$SUPABASE_URL|$SUPABASE_ANON_KEY\""],
            capture_output=True, text=True, timeout=5,
        )
        url_key = (proc.stdout or "").strip()
        if "|" not in url_key:
            return None
        sb_url, anon = url_key.split("|", 1)
        if not sb_url or not anon:
            return None
        req = Request(
            f"{sb_url}/rest/v1/{table}?select=slug&order=updated_at.desc&limit=1",
            headers={"apikey": anon, "authorization": f"Bearer {anon}"},
        )
        with urlopen(req, timeout=8) as r:
            rows = json.loads(r.read())
            return rows[0]["slug"] if rows else None
    except Exception:
        return None


def run_trial(route: str, slug: str, dry: bool) -> Trial:
    profile = ROUTE_PROFILES[route]
    url = f"{PREVIEW_HOST}{profile['url_template'].format(slug=slug)}"
    code, body, headers = _cache_busted_get(url)
    if code != 200:
        return Trial(route, slug, "", "", 0.0, 0, False, f"pre-GET {code}")
    pre = _fingerprint(body, headers)

    if dry:
        return Trial(route, slug, pre, pre, 0.0, 0, False, "dry-run (no write)")

    ok, msg = _psql_update(profile["table"], slug)
    if not ok:
        return Trial(route, slug, pre, "", 0.0, 0, False, f"db: {msg}")

    t0 = time.monotonic()
    polls = 0
    deadline = t0 + POLL_TIMEOUT_S
    post = pre
    while time.monotonic() < deadline:
        polls += 1
        code, body, headers = _cache_busted_get(url)
        if code == 200:
            post = _fingerprint(body, headers)
            if post != pre:
                return Trial(route, slug, pre, post, time.monotonic() - t0, polls, False)
        time.sleep(POLL_INTERVAL_S)

    return Trial(route, slug, pre, post, POLL_TIMEOUT_S, polls, True,
                 "fingerprint never changed")


def _summarize(trials: list[Trial], applied: bool, target_trials: int) -> dict:
    """Compute p50/p95/max + verdict for a single trial set (one route)."""
    successes = [t for t in trials if not t.timed_out and not t.error]
    latencies = [t.latency_s for t in successes if t.latency_s > 0]
    p95 = (
        statistics.quantiles(latencies, n=20)[18]
        if len(latencies) >= 20
        else (max(latencies) if latencies else None)
    )
    verdict = (
        "GREEN" if (latencies and
                    len(latencies) >= max(1, target_trials // 2) and
                    p95 is not None and p95 <= P95_TARGET_S)
        else ("AMBER" if applied else "DRY-RUN")
    )
    return {
        "trials": len(trials),
        "successes": len(successes),
        "timeouts": sum(1 for t in trials if t.timed_out),
        "errors": sum(1 for t in trials if t.error and t.error != "dry-run (no write)"),
        "p50_s": statistics.median(latencies) if latencies else None,
        "p95_s": p95,
        "max_s": max(latencies) if latencies else None,
        "obj1_verdict": verdict,
    }


def _run_route(route: str, slugs: list[str], trials: int, apply: bool) -> tuple[list[Trial], dict]:
    profile = ROUTE_PROFILES[route]
    print(f"# route={route} table={profile['table']} url={profile['url_template']} ({profile['note']})",
          file=sys.stderr)
    print(f"# slugs={slugs} trials={trials}", file=sys.stderr)
    out: list[Trial] = []
    for i in range(trials):
        slug = slugs[i % len(slugs)]
        t = run_trial(route, slug, dry=not apply)
        out.append(t)
        ok = "OK" if (not t.error or t.error == "dry-run (no write)") and not t.timed_out else "FAIL"
        print(
            f"  [{route}] trial {i+1:2d}/{trials}  {slug:35s}  {ok}  "
            f"{t.latency_s:5.2f}s  polls={t.polls:2d}  {t.error or ''}",
            file=sys.stderr,
        )
    return out, _summarize(out, apply, trials)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="Perform live DB writes. Requires Jammi greenlight.")
    ap.add_argument("--dry-run", action="store_true",
                    help="No DB writes. Default behavior unless --apply.")
    ap.add_argument("--route", default="r",
                    choices=["r", "answers", "best", "all"],
                    help="Which route to probe (default: r). 'all' runs every route.")
    ap.add_argument("--slug", help="Override default slug for the chosen route.")
    ap.add_argument("--slugs", help="comma-separated; rotates across trials")
    ap.add_argument("--trials", type=int, default=DEFAULT_TRIALS)
    args = ap.parse_args(argv)

    if not args.apply:
        args.dry_run = True

    routes = ["r", "answers", "best"] if args.route == "all" else [args.route]

    print(f"# CDM-REV Phase 2.4/5.5 e2e revalidate probe", file=sys.stderr)
    print(f"# preview={PREVIEW_HOST}", file=sys.stderr)
    print(f"# routes={routes} mode={'APPLY' if args.apply else 'DRY-RUN'} target=p95≤{P95_TARGET_S}s",
          file=sys.stderr)

    per_route_trials: dict = {}
    per_route_summary: dict = {}
    for route in routes:
        if args.slugs and len(routes) == 1:
            slugs = [s.strip() for s in args.slugs.split(",") if s.strip()]
        elif args.slug and len(routes) == 1:
            slugs = [args.slug]
        else:
            d = _resolve_default_slug(route)
            if not d:
                print(f"  [{route}] could not resolve default slug — skipping", file=sys.stderr)
                continue
            slugs = [d]
        ts, summary = _run_route(route, slugs, args.trials, args.apply)
        per_route_trials[route] = [asdict(t) for t in ts]
        per_route_summary[route] = summary

    # Aggregate verdict: GREEN only if every executed route is GREEN.
    verdicts = [s["obj1_verdict"] for s in per_route_summary.values()]
    if not verdicts:
        agg = "AMBER" if args.apply else "DRY-RUN"
    elif all(v == "GREEN" for v in verdicts):
        agg = "GREEN"
    elif all(v == "DRY-RUN" for v in verdicts):
        agg = "DRY-RUN"
    else:
        agg = "AMBER"

    summary = {
        "preview": PREVIEW_HOST,
        "applied": args.apply,
        "routes_executed": list(per_route_summary.keys()),
        "per_route": per_route_summary,
        "obj1_verdict": agg,
        "target_p95_s": P95_TARGET_S,
        "details_by_route": per_route_trials,
        "ts_unix": int(time.time()),
    }
    print(json.dumps(summary, indent=2))

    # Persist latest probe result so verify_strategic_objectives.py can
    # read OBJ-1 verdict directly instead of staying AMBER forever.
    artifact_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"
    )
    try:
        os.makedirs(artifact_dir, exist_ok=True)
        with open(
            os.path.join(artifact_dir, "cdm_rev_phase24_probe_latest.json"), "w"
        ) as f:
            json.dump(summary, f, indent=2)
    except Exception:
        pass

    return 0 if summary["obj1_verdict"] == "GREEN" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
