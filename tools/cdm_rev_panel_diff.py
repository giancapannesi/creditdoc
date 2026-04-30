#!/usr/bin/env python3
"""
CDM-REV Phase 5.2 — 50-URL HTML diff panel (multi-route).

Phase 1 cutover gate (d) per docs/plans/2026-04-29_REVISED_MIGRATION_PLAN_HYBRID_FIRST.md:
    HTML diff < 0.1% byte delta on a 50-URL panel covering all SSR routes,
    comparing PRODUCTION (https://www.creditdoc.co) against PREVIEW
    (https://cdm-rev-hybrid.creditdoc.pages.dev).

Why a separate tool:
    `tools/cdm_rev_html_diff.sh` covers /review/<slug>/ only. The cutover
    gate is "every SSR route" so the panel needs /answers, /best, /state
    coverage too.

Panel composition (50 URLs):
     20 × /review/<slug>/    — top-rated lenders, mix of categories
     10 × /answers/<slug>/   — published pillars (the 14 we have, top 10)
     10 × /best/<slug>/      — money pages (top 10 listicles by category)
     10 × /state/<slug>/     — top states by lender count (CA, TX, FL, NY...)

Per-URL contract:
    1. HTTP 200 from BOTH prod + preview
    2. Normalize: strip Astro asset hashes, HTML comments, run-of-whitespace,
       known-dynamic content tokens.
    3. Pass = |bytes_prod - bytes_preview| / max(...) < 0.1%

Usage:
    python3 tools/cdm_rev_panel_diff.py
    python3 tools/cdm_rev_panel_diff.py --json data/cdm_rev_panel_diff.json
    python3 tools/cdm_rev_panel_diff.py --prod-host https://www.creditdoc.co \\
        --preview-host https://cdm-rev-hybrid.creditdoc.pages.dev

Exit codes:
    0 — gate GREEN (0 over-threshold, mean < 0.1%)
    1 — bad args
    2 — gate RED (any URL > 0.1% OR HTTP failure)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

UA = "cdm-rev-panel-diff/1.0 (curl-compat)"
DEFAULT_PROD = "https://www.creditdoc.co"
DEFAULT_PREVIEW = "https://cdm-rev-hybrid.creditdoc.pages.dev"
THRESHOLD_PCT = 0.1
REPO_ROOT = Path(__file__).resolve().parent.parent

# 50-URL panel.
PANEL_REVIEW = [
    # Verified live on prod 2026-04-30 (HTTP 200 against www.creditdoc.co).
    # The original 10 *-personal-loan slugs were 410 Gone — replaced with
    # live brand slugs from `lenders` table where is_protected=1.
    "credit-saint", "the-credit-pros", "sky-blue-credit", "the-credit-people",
    "lexington-law", "experian-boost", "credit-strong", "self-credit-builder",
    "apex-credit-fix", "capital-one-platinum-secured",
    "prosper", "avant", "lendingtree", "credit9", "oportun",
    "fig-loans", "netcredit", "integra-credit", "refijet", "asap-credit-repair",
]
PANEL_ANSWERS = [
    # Verified live on prod 2026-04-30 (HTTP 200). `small-business-loans-guide`
    # was 404 on prod — replaced with `personal-loans-bad-credit-how-to-qualify`.
    "are-small-business-loans-worth-it",
    "build-credit-with-no-credit-history",
    "can-i-do-debt-consolidation-myself",
    "can-i-get-a-car-loan-with-my-credit-score",
    "does-credit-score-affect-car-insurance",
    "how-credit-card-interest-works",
    "how-to-build-credit-score-fast",
    "how-to-get-a-personal-loan",
    "personal-loan-interest-rates-explained",
    "personal-loans-bad-credit-how-to-qualify",
]
PANEL_BEST = [
    "best-credit-repair-companies",
    "best-credit-repair-money-back-guarantee",
    "best-personal-loans-bad-credit",
    "best-debt-consolidation-loans",
    "best-credit-builder-loans",
    "best-secured-credit-cards",
    "best-no-credit-check-cards",
    "best-debt-relief-companies",
    "best-cash-advance-apps",
    "best-payday-loan-alternatives",
]
PANEL_STATE = [
    # Top 10 by population/lender count — drift OK, real list resolves at runtime.
    "california", "texas", "florida", "new-york", "pennsylvania",
    "illinois", "ohio", "georgia", "north-carolina", "michigan",
]

PANEL: list[tuple[str, str]] = (
    [("/review", s) for s in PANEL_REVIEW]
    + [("/answers", s) for s in PANEL_ANSWERS]
    + [("/best", s) for s in PANEL_BEST]
    + [("/state", s) for s in PANEL_STATE]
)


# Normalization patterns — strip dynamic content that would inflate byte deltas.
NORM_PATTERNS = [
    # Astro asset hashes: /_astro/foo.aBc123Xy.{js,css,woff2}
    (re.compile(r"/_astro/([^\"\s]+?)\.[a-zA-Z0-9_-]{8,}\.(js|css|woff2)"),
     r"/_astro/\1.HASH.\2"),
    # HTML comments
    (re.compile(r"<!--.*?-->", re.DOTALL), ""),
    # Cache-bust query params: ?_v=2026-04-30T...
    (re.compile(r"(\?|&)_v=[0-9TZ:.\-]{8,}"), r"\1_v=NORM"),
    # Run-of-whitespace between tags
    (re.compile(r">\s+<"), "><"),
    # Run-of-whitespace
    (re.compile(r"\s+"), " "),
    # x-cdm-version-style timestamp tokens in body (defensive)
    (re.compile(r'(content="|description=")[0-9TZ:.\-]{15,}'), r"\1NORM"),
]


def normalize(html: str) -> str:
    out = html
    for pat, repl in NORM_PATTERNS:
        out = pat.sub(repl, out)
    return out


def fetch(url: str, timeout: int = 20) -> tuple[int, str]:
    req = Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
    try:
        with urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except HTTPError as e:
        return e.code, ""
    except (URLError, TimeoutError, OSError) as e:
        return 0, ""


def diff_pct(a_bytes: int, b_bytes: int) -> float:
    if a_bytes == 0 and b_bytes == 0:
        return 0.0
    delta = abs(a_bytes - b_bytes)
    return (delta / max(a_bytes, b_bytes)) * 100


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prod-host", default=DEFAULT_PROD)
    ap.add_argument("--preview-host", default=DEFAULT_PREVIEW)
    ap.add_argument("--threshold", type=float, default=THRESHOLD_PCT,
                    help="Pass threshold per-URL byte delta percentage (default 0.1)")
    ap.add_argument("--json", default=None,
                    help="Write JSON report to this path (default: stdout summary only)")
    ap.add_argument("--limit", type=int, default=None,
                    help="Limit panel to first N URLs (for smoke testing)")
    args = ap.parse_args()

    panel = PANEL[: args.limit] if args.limit else PANEL
    print(f"CDM-REV Phase 5.2 panel diff — {len(panel)} URLs")
    print(f"PROD     : {args.prod_host}")
    print(f"PREVIEW  : {args.preview_host}")
    print(f"Threshold: {args.threshold}% byte delta\n")

    print(f"{'route':<10} {'slug':<40} {'prod':>9} {'prev':>9} {'pct':>7}  status")
    print("-" * 90)

    results: list[dict] = []
    t0 = time.monotonic()

    for route, slug in panel:
        prod_url = f"{args.prod_host}{route}/{slug}/"
        prev_url = f"{args.preview_host}{route}/{slug}/"
        prod_status, prod_html = fetch(prod_url)
        prev_status, prev_html = fetch(prev_url)

        if prod_status != 200 or prev_status != 200:
            row = {
                "route": route, "slug": slug,
                "prod_status": prod_status, "preview_status": prev_status,
                "prod_bytes": None, "preview_bytes": None,
                "diff_pct": None, "status": "FAIL_HTTP",
            }
            print(f"{route:<10} {slug:<40} {prod_status:>9} {prev_status:>9} {'n/a':>7}  FAIL_HTTP")
            results.append(row)
            continue

        prod_norm = normalize(prod_html)
        prev_norm = normalize(prev_html)
        pb = len(prod_norm.encode("utf-8"))
        vb = len(prev_norm.encode("utf-8"))
        pct = diff_pct(pb, vb)
        ok = pct < args.threshold
        status = "OK" if ok else "OVER"
        row = {
            "route": route, "slug": slug,
            "prod_status": prod_status, "preview_status": prev_status,
            "prod_bytes": pb, "preview_bytes": vb,
            "diff_pct": round(pct, 4), "status": status,
        }
        print(f"{route:<10} {slug:<40} {pb:>9} {vb:>9} {pct:>6.3f}%  {status}")
        results.append(row)

    wall = round(time.monotonic() - t0, 2)
    over = [r for r in results if r["status"] == "OVER"]
    fail = [r for r in results if r["status"] == "FAIL_HTTP"]
    ok_pcts = [r["diff_pct"] for r in results if isinstance(r["diff_pct"], (int, float))]
    mean_pct = round(sum(ok_pcts) / len(ok_pcts), 4) if ok_pcts else None

    summary = {
        "ts_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "prod_host": args.prod_host,
        "preview_host": args.preview_host,
        "threshold_pct": args.threshold,
        "panel_size": len(panel),
        "ok_count": len(results) - len(over) - len(fail),
        "over_threshold_count": len(over),
        "http_fail_count": len(fail),
        "mean_diff_pct": mean_pct,
        "wall_seconds": wall,
        "passed": len(over) == 0 and len(fail) == 0
                  and mean_pct is not None and mean_pct < args.threshold,
        "results": results,
    }

    print()
    print("=" * 90)
    print(f"OK              : {summary['ok_count']}")
    print(f"Over threshold  : {summary['over_threshold_count']}")
    print(f"HTTP failures   : {summary['http_fail_count']}")
    print(f"Mean diff %     : {mean_pct}")
    print(f"Wall            : {wall}s")
    verdict = "GREEN" if summary["passed"] else "RED"
    print(f"VERDICT         : ACCEPTANCE GATE {verdict}")

    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(summary, indent=2) + "\n")
        print(f"JSON            : {out}")

    return 0 if summary["passed"] else 2


if __name__ == "__main__":
    sys.exit(main())
