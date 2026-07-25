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

# Sitemap URL-count guardrail — self-healing.
#
# Prior version used a fixed baseline (27,304 set 2026-07-18) and screamed for 5
# days when commit d5c1eafad6 correctly dropped noindex pages on 2026-07-20.
# Fixed baselines rot the moment content genuinely changes.
#
# New model:
#   - Record last-good count in SITEMAP_STATE_PATH.
#   - Compare today's count to that recorded value.
#   - Only fail if the DROP exceeds both SITEMAP_MIN_DROP_URLS and SITEMAP_MIN_DROP_PCT
#     (both must be true → real regression, not slow enrichment churn).
#   - Growth or gentle shrinkage silently updates the state, no alert.
#   - First-ever run seeds the state and exits green.
SITEMAP_STATE_PATH = Path("/srv/BusinessOps/data/creditdoc_sitemap_state.json")
SITEMAP_MIN_DROP_URLS = 500  # ignore drops smaller than this
SITEMAP_MIN_DROP_PCT = 3.0   # AND smaller than this % of last-good
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


def _load_last_good_sitemap() -> int:
    """Return the last-known-good sitemap URL count, or 0 if state file missing/invalid."""
    try:
        data = json.loads(SITEMAP_STATE_PATH.read_text())
        return int(data.get("last_good_count", 0))
    except Exception:
        return 0


def _save_last_good_sitemap(count: int) -> None:
    """Persist the current healthy sitemap count as the new last-good baseline."""
    try:
        SITEMAP_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        SITEMAP_STATE_PATH.write_text(json.dumps({
            "last_good_count": count,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }, indent=2) + "\n")
    except Exception as exc:
        print(f"[health] failed to save sitemap state: {exc}", file=sys.stderr)


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

    # Sitemap URL-count guardrail — self-healing (see SITEMAP_STATE_PATH block).
    sitemap_count, sitemap_err = count_sitemap_urls()
    prev_count = _load_last_good_sitemap()
    sitemap_delta = sitemap_count - prev_count if prev_count else 0
    real_regression = False
    if sitemap_err is None and sitemap_count > 0 and prev_count:
        drop_urls = prev_count - sitemap_count
        drop_pct = (drop_urls / prev_count) * 100.0 if prev_count else 0.0
        if drop_urls >= SITEMAP_MIN_DROP_URLS and drop_pct >= SITEMAP_MIN_DROP_PCT:
            real_regression = True
            failures.append({
                "url": "sitemap-count",
                "status": sitemap_count,
                "elapsed_s": 0.0,
                "error": f"drop {drop_urls} URLs ({drop_pct:.1f}%) from last-good {prev_count} exceeds thresholds ({SITEMAP_MIN_DROP_URLS} URLs AND {SITEMAP_MIN_DROP_PCT:.1f}%)",
            })
    # Only persist last-good when the fetch itself succeeded and it isn't a real
    # regression (otherwise the alert would silence itself on the next run).
    if sitemap_err is None and sitemap_count > 0 and not real_regression:
        _save_last_good_sitemap(sitemap_count)

    all_green = not failures
    now = datetime.now(timezone.utc).isoformat()
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a") as fh:
        fh.write(json.dumps({
            "ts": now, "results": results, "all_green": all_green,
            "sitemap": {"count": sitemap_count, "last_good": prev_count,
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
