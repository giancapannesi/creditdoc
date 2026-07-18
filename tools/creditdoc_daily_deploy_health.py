#!/usr/bin/env python3
"""Daily CreditDoc production deploy health check.

Curls the same 12 canary URLs that deploy.sh smoke-tests. On any non-200,
emails a Harvey alert to the founder and exits 1. On all-green, exits 0
(silent). Cron-wired to run every 2 hours.

Rationale (deploy.sh silent-error bug caught 2026-07-18): deploy.sh's
built-in verification only runs at deploy time. If prod later drifts to
5xx from an outside cause (Supabase down, Worker cron misfire, Cloudflare
edge issue), we won't notice until someone reports it. This standalone
poller closes that gap.

Env: reads /srv/BusinessOps/tools/.agentmail-api-key for Harvey.
Log:  /srv/BusinessOps/logs/creditdoc_deploy_health.log (append-only)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

CANARY_URLS = [
    "/",
    "/robots.txt",
    "/sitemap-index.xml",
    "/review/lexington-law/",
    "/state/wyoming/",
    "/credit-guide/austin-tx/",
    "/credit-guide/austin-tx/credit-repair/",
    "/answers/",
    "/answers/best-debt-consolidation-loans-bad-credit/",
    "/best/best-credit-repair-companies/",
    "/categories/credit-repair/",
    "/blog/how-to-get-a-personal-loan-with-bad-credit-in-2026/",
    "/financial-wellness/credit-score-basics/",
    "/brand/advance-america/",
    "/api/geo",
]
BASE = "https://www.creditdoc.co"
USER_AGENT = "creditdoc-deploy-health/1"
TIMEOUT = 8.0
LOG_PATH = Path("/srv/BusinessOps/logs/creditdoc_deploy_health.log")
HARVEY_KEY_PATH = Path("/srv/BusinessOps/tools/.agentmail-api-key")
FOUNDER_EMAIL = "gian.eao@gmail.com"

# Sitemap URL-count guardrail. Baseline = 27,304 (session-end 2026-07-18).
# Alarm if drift exceeds SITEMAP_TOLERANCE either direction. Update baseline
# after any legitimate content-scale change.
SITEMAP_BASELINE = 27_304
SITEMAP_TOLERANCE = 200  # ±200 URLs = ~0.7% drift budget
SITEMAP_INDEX_URL = f"{BASE}/sitemap-index.xml"


def probe(url: str) -> tuple[int, float, str | None]:
    """Return (status, elapsed_seconds, error_message_or_None)."""
    t0 = time.perf_counter()
    req = urllib.request.Request(url, headers={"user-agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            resp.read(1024)  # touch body to force full connect
            return (resp.status, time.perf_counter() - t0, None)
    except urllib.error.HTTPError as exc:
        return (exc.code, time.perf_counter() - t0, None)
    except Exception as exc:
        return (0, time.perf_counter() - t0, f"{type(exc).__name__}: {exc}")


def count_sitemap_urls() -> tuple[int, str | None]:
    """Fetch sitemap-index.xml + each child, return (total_url_count, error_or_None)."""
    import re
    try:
        req = urllib.request.Request(SITEMAP_INDEX_URL, headers={"user-agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            index_xml = resp.read().decode("utf-8", errors="replace")
    except Exception as exc:
        return (0, f"sitemap-index fetch failed: {type(exc).__name__}: {exc}")

    child_urls = re.findall(r"<loc>([^<]+)</loc>", index_xml)
    total = 0
    for child_url in child_urls:
        try:
            req = urllib.request.Request(child_url, headers={"user-agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                child_xml = resp.read().decode("utf-8", errors="replace")
            total += len(re.findall(r"<loc>", child_xml))
        except Exception as exc:
            return (total, f"child sitemap {child_url}: {exc}")
    return (total, None)


def send_alert(failures: list[dict]) -> None:
    """Send a Harvey alert for the failures. Silent if AgentMail key missing."""
    try:
        key = HARVEY_KEY_PATH.read_text().strip()
    except FileNotFoundError:
        print("[health] no AgentMail key — cannot send alert", file=sys.stderr)
        return

    lines = ["CreditDoc production health check FAILED:", ""]
    for f in failures:
        s = f["status"]
        err = f" ({f['error']})" if f.get("error") else ""
        lines.append(f"  {f['url']} → {s}{err} [{f['elapsed_s']:.2f}s]")
    lines += ["", f"Full log: {LOG_PATH}",
              f"Timestamp: {datetime.now(timezone.utc).isoformat()}"]
    body_text = "\n".join(lines)

    payload = {
        "from": "longleader503@agentmail.to",
        "to": [FOUNDER_EMAIL],
        "subject": f"[CreditDoc] Deploy health FAIL — {len(failures)}/{len(CANARY_URLS)} down",
        "text": body_text,
    }
    req = urllib.request.Request(
        "https://api.agentmail.to/v0/inboxes/longleader503@agentmail.to/messages/send",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp.read()
        print("[health] Harvey alert sent", file=sys.stderr)
    except Exception as exc:
        print(f"[health] Harvey send failed: {exc}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quiet", action="store_true", help="Suppress stdout on all-green")
    parser.add_argument("--no-alert", action="store_true", help="Skip Harvey email on fail")
    args = parser.parse_args()

    results = []
    for path in CANARY_URLS:
        code, elapsed, err = probe(BASE + path)
        rec = {"url": path, "status": code, "elapsed_s": elapsed}
        if err:
            rec["error"] = err
        results.append(rec)

    failures = [r for r in results if r["status"] != 200]

    # Sitemap URL-count guardrail (once per run — cheap, catches drift).
    sitemap_count, sitemap_err = count_sitemap_urls()
    sitemap_delta = sitemap_count - SITEMAP_BASELINE
    sitemap_ok = (sitemap_err is None
                  and abs(sitemap_delta) <= SITEMAP_TOLERANCE
                  and sitemap_count > 0)
    if not sitemap_ok:
        failures.append({
            "url": "sitemap-count",
            "status": sitemap_count,
            "elapsed_s": 0.0,
            "error": sitemap_err or f"drift {sitemap_delta:+d} from baseline {SITEMAP_BASELINE} exceeds ±{SITEMAP_TOLERANCE}",
        })

    all_green = not failures
    now = datetime.now(timezone.utc).isoformat()
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a") as fh:
        fh.write(json.dumps({
            "ts": now, "results": results, "all_green": all_green,
            "sitemap": {"count": sitemap_count, "baseline": SITEMAP_BASELINE,
                        "delta": sitemap_delta, "err": sitemap_err},
        }) + "\n")

    if all_green:
        if not args.quiet:
            print(f"[health] {now}  {len(results)}/{len(results)} green")
        return 0

    print(f"[health] {now}  FAIL {len(failures)}/{len(results)}", file=sys.stderr)
    for f in failures:
        print(f"  {f['url']} → {f['status']} ({f.get('error','')})", file=sys.stderr)
    if not args.no_alert:
        send_alert(failures)
    return 1


if __name__ == "__main__":
    sys.exit(main())
