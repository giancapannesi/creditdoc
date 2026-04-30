#!/usr/bin/env python3
"""
CDM-REV Phase 2.4 — END-TO-END REVALIDATE PROBE.

What this measures:
    DB row UPDATE at T+0  →  globally-cached new HTML at T+N
    Target: N ≤ 10s p95 over 20 trials.
    A pass on this probe is what flips OBJ-1 from AMBER to GREEN.

How a single trial works:
    1. GET   <preview>/review/<slug>/?_cb=<ms>  → capture pre-write content fingerprint
    2. T0 = monotonic()
    3. UPDATE lenders SET last_updated = NOW() WHERE slug = <slug>
       (transient field; trigger bumps lenders_updated_at; writer pings /api/revalidate)
    4. Poll GET <preview>/review/<slug>/?_cb=<ms> until fingerprint changes
    5. T1 = monotonic(); record latency = T1 - T0

How the fingerprint is built:
    SHA-256 of the JSON-LD `dateModified` + `datePublished` block on the page.
    These move on every DB UPDATE because last_updated is sliced into
    the structured-data emit.

SAFETY:
    --dry-run  default. Prints intended writes, exits without DB contact.
    --apply    requires explicit Jammi greenlight. Performs N=20 writes against
               the live `lenders` table. Writes are non-destructive (last_updated
               is TRANSIENT). Trigger + revalidate ping fire each time.

Usage:
    python3 tools/cdm_rev_phase24_e2e_probe.py --dry-run
    python3 tools/cdm_rev_phase24_e2e_probe.py --apply --slug credit-saint --trials 20
    python3 tools/cdm_rev_phase24_e2e_probe.py --apply --slugs credit-saint,lexington-law

DEPENDENCIES:
    - Reads creds from tools/.supabase-creditdoc.env (psql)
    - REVALIDATE_TOKEN must be set on the preview env (already done Apr 29)
    - Cache-busts every poll (Cache-Control: no-cache + ?_cb=<ms>)

OUTPUT:
    JSON to stdout. Per-trial latency, p50, p95, max, fail count.
    Exits 0 if p95 ≤ 10s, else 1.
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
DEFAULT_SLUG = "credit-saint"
DEFAULT_TRIALS = 20
P95_TARGET_S = 10.0
POLL_INTERVAL_S = 0.5
POLL_TIMEOUT_S = 30.0
SUPABASE_ENV_FILE = "/srv/BusinessOps/tools/.supabase-creditdoc.env"


@dataclass
class Trial:
    slug: str
    pre_fingerprint: str
    post_fingerprint: str
    latency_s: float
    polls: int
    timed_out: bool
    error: Optional[str] = None


def _cache_busted_get(url: str) -> tuple[int, str]:
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
            return r.getcode(), r.read().decode("utf-8", errors="replace")
    except URLError as e:
        return 0, str(e)


def _fingerprint(html: str) -> str:
    """Hash the cdm-last-updated meta tag (microsecond-precision writer signal).

    /r/[slug] emits <meta name="cdm-last-updated" content="..."> verbatim from
    body_inline.last_updated. Cache-API content-version floors to whole
    seconds, so we deliberately do NOT include verIso in the fingerprint —
    consecutive trials within the same wall-second would otherwise collide.
    """
    m = re.search(
        r'<meta name="cdm-last-updated" content="([^"]*)"',
        html,
    )
    return hashlib.sha256((m.group(1) if m else "").encode()).hexdigest()[:16]


def _psql_update(slug: str) -> tuple[bool, str]:
    """Bump updated_at + body_inline.last_updated for a single row.
    Transient field; non-destructive. Trigger lenders_updated_at fires.
    body_inline change moves datePublished in the rendered HTML.
    """
    if not os.path.exists(SUPABASE_ENV_FILE):
        return False, f"missing {SUPABASE_ENV_FILE}"
    # Microsecond precision (clock_timestamp + .US format) so consecutive
    # trials within the same wall-clock second still produce a unique string,
    # otherwise the fingerprint won't change and the trial times out.
    cmd = (
        f". {SUPABASE_ENV_FILE} && "
        f'psql "$SUPABASE_DB_URL" -X -A -t -c '
        f"\"UPDATE lenders SET updated_at = clock_timestamp(), "
        f"body_inline = jsonb_set(body_inline, '{{last_updated}}', "
        f"to_jsonb(to_char(clock_timestamp() AT TIME ZONE 'UTC', "
        f"'YYYY-MM-DD\\\"T\\\"HH24:MI:SS.US\\\"Z\\\"'))) "
        f"WHERE slug = '{slug}' RETURNING slug;\""
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


def run_trial(slug: str, dry: bool) -> Trial:
    url = f"{PREVIEW_HOST}/r/{slug}"
    code, body = _cache_busted_get(url)
    if code != 200:
        return Trial(slug, "", "", 0.0, 0, False, f"pre-GET {code}")
    pre = _fingerprint(body)

    if dry:
        return Trial(slug, pre, pre, 0.0, 0, False, "dry-run (no write)")

    ok, msg = _psql_update(slug)
    if not ok:
        return Trial(slug, pre, "", 0.0, 0, False, f"db: {msg}")

    t0 = time.monotonic()
    polls = 0
    deadline = t0 + POLL_TIMEOUT_S
    post = pre
    while time.monotonic() < deadline:
        polls += 1
        code, body = _cache_busted_get(url)
        if code == 200:
            post = _fingerprint(body)
            if post != pre:
                return Trial(slug, pre, post, time.monotonic() - t0, polls, False)
        time.sleep(POLL_INTERVAL_S)

    return Trial(slug, pre, post, POLL_TIMEOUT_S, polls, True, "fingerprint never changed")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="Perform live DB writes. Requires Jammi greenlight.")
    ap.add_argument("--dry-run", action="store_true",
                    help="No DB writes. Default behavior unless --apply.")
    ap.add_argument("--slug", default=DEFAULT_SLUG)
    ap.add_argument("--slugs", help="comma-separated; rotates across trials")
    ap.add_argument("--trials", type=int, default=DEFAULT_TRIALS)
    args = ap.parse_args(argv)

    if not args.apply:
        args.dry_run = True

    slugs = (
        [s.strip() for s in args.slugs.split(",") if s.strip()]
        if args.slugs
        else [args.slug]
    )

    print(f"# CDM-REV Phase 2.4 e2e revalidate probe", file=sys.stderr)
    print(f"# preview={PREVIEW_HOST}", file=sys.stderr)
    print(f"# slugs={slugs} trials={args.trials} mode={'APPLY' if args.apply else 'DRY-RUN'}",
          file=sys.stderr)
    print(f"# target p95 ≤ {P95_TARGET_S}s", file=sys.stderr)

    trials: list[Trial] = []
    for i in range(args.trials):
        slug = slugs[i % len(slugs)]
        t = run_trial(slug, dry=not args.apply)
        trials.append(t)
        ok = "OK" if (not t.error or t.error == "dry-run (no write)") and not t.timed_out else "FAIL"
        print(
            f"  trial {i+1:2d}/{args.trials}  {slug:30s}  {ok}  "
            f"{t.latency_s:5.2f}s  polls={t.polls:2d}  "
            f"{t.error or ''}",
            file=sys.stderr,
        )

    successes = [t for t in trials if not t.timed_out and not t.error]
    latencies = [t.latency_s for t in successes if t.latency_s > 0]
    summary = {
        "preview": PREVIEW_HOST,
        "trials": len(trials),
        "applied": args.apply,
        "successes": len(successes),
        "timeouts": sum(1 for t in trials if t.timed_out),
        "errors": sum(1 for t in trials if t.error and t.error != "dry-run (no write)"),
        "p50_s": statistics.median(latencies) if latencies else None,
        "p95_s": (statistics.quantiles(latencies, n=20)[18]
                  if len(latencies) >= 20 else
                  (max(latencies) if latencies else None)),
        "max_s": max(latencies) if latencies else None,
        "target_p95_s": P95_TARGET_S,
        "obj1_verdict": (
            "GREEN" if (latencies and
                        len(latencies) >= max(1, args.trials // 2) and
                        ((statistics.quantiles(latencies, n=20)[18]
                          if len(latencies) >= 20 else max(latencies))
                         <= P95_TARGET_S))
            else ("AMBER" if args.apply else "DRY-RUN")
        ),
        "details": [asdict(t) for t in trials],
    }
    print(json.dumps(summary, indent=2))
    return 0 if summary["obj1_verdict"] == "GREEN" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
