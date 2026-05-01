#!/usr/bin/env python3
"""Site-wide route smoke against Worker URL.

Probes every route CLASS (not just panel URLs) — root, search, lenders index,
state index, /best/, /answers/, /r/, /state/, /city/, /trust, /privacy, etc.
Reports HTTP status + size + timing per route. Used as a pre-DNS-flip gate.
"""
import argparse
import json
import sys
import time
import urllib.request
from urllib.error import HTTPError, URLError

UA = "Mozilla/5.0 (X11; Linux x86_64) cdm-rev-site-smoke/1.0"
TIMEOUT_S = 15

# Route classes — one or two representative slugs each so we cover the SSR
# surface area without drowning the smoke in lender-detail pages.
ROUTES = [
    # static index pages
    ("/",                                   "static"),
    ("/about/",                             "static"),
    ("/contact/",                           "static"),
    ("/privacy/",                           "static"),
    ("/terms/",                             "static"),
    ("/state/",                             "static-or-ssr"),
    ("/answers/",                           "ssr"),
    ("/blog/",                              "static-or-ssr"),
    ("/glossary/",                          "static-or-ssr"),

    # SSR row pages — /r/ (lender), /state/, /best/, /answers/
    ("/r/credit-karma/",                    "ssr-r"),
    ("/r/wallethub/",                       "ssr-r"),
    ("/state/california/",                  "ssr-state"),
    ("/state/texas/",                       "ssr-state"),
    ("/state/wyoming/",                     "ssr-state"),
    ("/state/new-york/",                    "ssr-state"),
    ("/best/best-credit-repair-companies/", "ssr-best"),
    ("/best/best-personal-loans-bad-credit/", "ssr-best"),
    ("/best/best-debt-consolidation-loans/", "ssr-best"),
    ("/answers/are-small-business-loans-worth-it/",        "ssr-answer"),
    ("/answers/build-credit-with-no-credit-history/",      "ssr-answer"),
    ("/answers/personal-loans-bad-credit-how-to-qualify/", "ssr-answer"),

    # state lending-laws subroute (per-state static)
    ("/state/wyoming/lending-laws/",        "static-state-laws"),

    # not-found expectation: bogus slugs MUST 404, not 500
    ("/r/__nonexistent_lender_for_smoke__/",  "404-expected"),
    ("/state/__nonexistent_state__/",         "404-expected"),
    ("/best/__nonexistent_best__/",           "404-expected"),
    ("/answers/__nonexistent_answer__/",      "404-expected"),

    # parity-with-prod 404s — these don't exist on Vercel prod either,
    # so Worker must also 404 (proves no accidental new route handler)
    ("/lenders/",                            "404-parity"),
    ("/best/",                               "404-parity"),
    ("/state/california/los-angeles/",       "404-parity"),
]

def fetch(base: str, path: str) -> dict:
    url = base.rstrip("/") + path
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml",
    })
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
            body = r.read()
            wall = time.monotonic() - t0
            return {
                "url": url,
                "status": r.status,
                "bytes": len(body),
                "ms": round(wall * 1000, 1),
                "ok": True,
            }
    except HTTPError as e:
        wall = time.monotonic() - t0
        return {
            "url": url,
            "status": e.code,
            "bytes": 0,
            "ms": round(wall * 1000, 1),
            "ok": False,
            "error": f"HTTP {e.code}",
        }
    except (URLError, TimeoutError, Exception) as e:
        wall = time.monotonic() - t0
        return {
            "url": url,
            "status": None,
            "bytes": 0,
            "ms": round(wall * 1000, 1),
            "ok": False,
            "error": str(e),
        }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="https://creditdoc.fancy-glitter-38f7.workers.dev")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    print(f"# CDM-REV site smoke — base={args.base}")
    print(f"# routes={len(ROUTES)}\n")

    results = []
    for path, kind in ROUTES:
        r = fetch(args.base, path)
        r["kind"] = kind
        # 404-expected and 404-parity routes pass if they 404, fail if 200 or 500.
        if kind in ("404-expected", "404-parity"):
            r["pass"] = (r["status"] == 404)
        else:
            r["pass"] = (r["ok"] and r["status"] == 200 and r["bytes"] > 500)
        results.append(r)
        sym = "✓" if r["pass"] else "✗"
        print(f"  {sym} {r.get('status','---'):>4}  {r['ms']:>7.1f}ms  {r['bytes']:>8}B  {kind:<20}  {path}")

    passes = sum(1 for r in results if r["pass"])
    fails = len(results) - passes
    print(f"\n  pass {passes}/{len(results)}, fail {fails}")
    overall = "GREEN" if fails == 0 else "RED"
    print(f"  VERDICT: {overall}")

    if args.json:
        with open(args.json, "w") as f:
            json.dump({"base": args.base, "results": results,
                       "pass": passes, "fail": fails,
                       "verdict": overall, "ts": int(time.time())}, f, indent=2)
        print(f"  JSON: {args.json}")

    return 0 if fails == 0 else 2

if __name__ == "__main__":
    sys.exit(main())
