#!/usr/bin/env python3
"""
CDM-REV Phase 5.4 — health-check poller for the SSR pilot surface.

Polls a fixed list of URLs on `cdm-rev-hybrid.creditdoc.pages.dev` and
records: HTTP status, TTFB, response size, presence of the
`<meta name="cdm-last-updated">` SSR fingerprint, and the cf-cache-status
header. Output goes to a JSON-lines log so the next CWV / cutover audit
can replay history.

Designed to be cron-wireable (every 5 min) BUT not yet wired. Wiring to
cron needs Jammi greenlight per CLAUDE.md RULE 4 / safety.md crontab
discipline.

Usage:
  python3 tools/cdm_rev_health_poller.py             # one-shot poll, exit 0/1
  python3 tools/cdm_rev_health_poller.py --json      # machine-readable summary
  python3 tools/cdm_rev_health_poller.py --urls-file ...

Exit codes:
  0 — all URLs returned 200 within thresholds
  1 — one or more URLs failed status / TTFB threshold
  2 — config / IO error

Thresholds (defaults, tunable via flags):
  status:   200 only
  TTFB:     ≤ 2.0s P95 across the URL set (single sample per URL per run)
  body:     ≥ 1024 bytes
  meta tag: `<meta name="cdm-last-updated"` MUST be present on /r/* URLs
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_URLS = [
    "https://cdm-rev-hybrid.creditdoc.pages.dev/r/upstart",
    "https://cdm-rev-hybrid.creditdoc.pages.dev/r/lendingclub",
    "https://cdm-rev-hybrid.creditdoc.pages.dev/r/sofi",
    "https://cdm-rev-hybrid.creditdoc.pages.dev/review/upstart",
    "https://cdm-rev-hybrid.creditdoc.pages.dev/",
]
LOG_DIR = Path(__file__).parent.parent / "data" / "health"
META_RE = re.compile(rb'<meta\s+name="cdm-last-updated"\s+content="(\d+)"')


def poll(url: str, timeout: float = 5.0) -> dict:
    t0 = time.perf_counter()
    rec = {"url": url, "status": None, "ttfb_s": None, "bytes": 0,
           "cf_cache": None, "meta_ts": None, "error": None}
    try:
        req = urllib.request.Request(url, headers={"user-agent": "cdm-rev-health/1"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            rec["status"] = resp.status
            rec["cf_cache"] = resp.headers.get("cf-cache-status")
            body = resp.read()
            rec["ttfb_s"] = round(time.perf_counter() - t0, 4)
            rec["bytes"] = len(body)
            m = META_RE.search(body)
            if m:
                try:
                    rec["meta_ts"] = int(m.group(1))
                except ValueError:
                    pass
    except Exception as exc:
        rec["error"] = f"{type(exc).__name__}: {exc}"
        rec["ttfb_s"] = round(time.perf_counter() - t0, 4)
    return rec


def evaluate(records: list[dict], ttfb_p95: float = 2.0,
             min_bytes: int = 1024) -> tuple[bool, list[str]]:
    fails: list[str] = []
    for r in records:
        if r["status"] != 200:
            fails.append(f"{r['url']} status={r['status']} err={r['error']}")
            continue
        if r["bytes"] < min_bytes:
            fails.append(f"{r['url']} body={r['bytes']}B (<{min_bytes})")
        # meta tag check is a soft gate — only required on /r/ routes
        if "/r/" in r["url"] and r["meta_ts"] is None:
            fails.append(f"{r['url']} missing cdm-last-updated meta tag")
    ok_records = [r for r in records if r["status"] == 200 and r["ttfb_s"] is not None]
    if ok_records:
        ttfbs = sorted(r["ttfb_s"] for r in ok_records)
        # one sample per URL per run, so P95 = max for small N
        p95 = ttfbs[-1]
        if p95 > ttfb_p95:
            fails.append(f"P95 TTFB {p95:.3f}s > {ttfb_p95:.3f}s threshold")
    return (not fails), fails


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="emit machine-readable summary")
    ap.add_argument("--urls-file", type=Path, help="newline-separated URLs (overrides default list)")
    ap.add_argument("--log-dir", type=Path, default=LOG_DIR)
    ap.add_argument("--ttfb-p95", type=float, default=2.0)
    args = ap.parse_args(argv)

    if args.urls_file:
        if not args.urls_file.exists():
            print(f"ERROR: {args.urls_file} not found", file=sys.stderr)
            return 2
        urls = [u.strip() for u in args.urls_file.read_text().splitlines() if u.strip()]
    else:
        urls = list(DEFAULT_URLS)

    args.log_dir.mkdir(parents=True, exist_ok=True)
    records = [poll(u) for u in urls]
    ok, fails = evaluate(records, ttfb_p95=args.ttfb_p95)

    now = datetime.now(timezone.utc)
    line = {
        "ts": now.isoformat(),
        "ok": ok,
        "n_urls": len(urls),
        "failures": fails,
        "records": records,
    }
    log_file = args.log_dir / f"poll-{now.strftime('%Y%m%d')}.jsonl"
    with log_file.open("a") as f:
        f.write(json.dumps(line) + "\n")

    if args.json:
        print(json.dumps(line, indent=2))
    else:
        print(f"# CDM-REV health poll @ {now.isoformat()}")
        print(f"#   urls:   {len(urls)}")
        print(f"#   ok:     {sum(1 for r in records if r['status'] == 200)}/{len(urls)}")
        ok_records = [r for r in records if r["ttfb_s"] is not None]
        if ok_records:
            ttfbs = [r["ttfb_s"] for r in ok_records]
            print(f"#   ttfb:   min={min(ttfbs):.3f}s  p50={statistics.median(ttfbs):.3f}s  p95={max(ttfbs):.3f}s")
        print(f"#   verdict: {'PASS' if ok else 'FAIL'}")
        for fail in fails:
            print(f"   FAIL  {fail}")
        print(f"# log:    {log_file}")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
