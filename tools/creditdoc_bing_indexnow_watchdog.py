#!/usr/bin/env python3
"""CreditDoc Bing + IndexNow watchdog.

This catches the silent failure class we just found: Bing can still crawl/index
the site while impressions are zero and IndexNow/key wiring is broken or stale.
"""

from __future__ import annotations

import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/srv/BusinessOps/creditdoc")
REPORT_DIR = ROOT / "reports" / "bing-indexnow-watchdog"
KEY = "1efee5eebbd54ea4812e2e77a9b73fcc"
KEY_URL = f"https://www.creditdoc.co/{KEY}.txt"
BING_SITE = "https://www.creditdoc.co/"

sys.path.insert(0, "/srv/BusinessOps/tools")
from bing_webmaster import api_get, _unwrap, _parse_date  # noqa: E402


def check_key_file() -> dict:
    try:
        req = urllib.request.Request(
            KEY_URL,
            headers={"User-Agent": "CreditDoc-Bing-IndexNow-Watchdog/1.0"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8", errors="replace").strip()
            return {
                "ok": resp.status == 200 and body == KEY,
                "status": resp.status,
                "body_ok": body == KEY,
            }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def bing_traffic() -> dict:
    data = api_get("GetRankAndTrafficStats", {"siteUrl": BING_SITE})
    rows = [r for r in _unwrap(data) if isinstance(r, dict)]
    total_impressions = sum(int(r.get("Impressions", 0) or 0) for r in rows[-30:])
    total_clicks = sum(int(r.get("Clicks", 0) or 0) for r in rows[-30:])
    recent_rows = [
        {
            "date": _parse_date(r.get("Date")),
            "impressions": int(r.get("Impressions", 0) or 0),
            "clicks": int(r.get("Clicks", 0) or 0),
        }
        for r in rows[-30:]
    ]
    return {
        "ok": data is not None,
        "rows": len(rows),
        "impressions_30d": total_impressions,
        "clicks_30d": total_clicks,
        "recent_rows": recent_rows,
    }


def bing_crawl() -> dict:
    data = api_get("GetCrawlStats", {"siteUrl": BING_SITE})
    rows = [r for r in _unwrap(data) if isinstance(r, dict)]
    last = rows[-1] if rows else {}
    return {
        "ok": data is not None and bool(rows),
        "last_date": _parse_date(last.get("Date")) if last else None,
        "last_crawled": last.get("CrawledPages", last.get("PagesCrawled")) if last else None,
        "last_errors": last.get("CrawlErrors", last.get("Errors")) if last else None,
        "last_in_index": last.get("InIndex", last.get("PagesInIndex")) if last else None,
    }


def write_report(payload: dict) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORT_DIR / f"bing_indexnow_watchdog_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return path


def main() -> None:
    payload = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "key_file": check_key_file(),
        "bing_traffic": bing_traffic(),
        "bing_crawl": bing_crawl(),
    }
    report = write_report(payload)

    failures = []
    if not payload["key_file"].get("ok"):
        failures.append("IndexNow key file is not live/valid")
    if not payload["bing_crawl"].get("ok"):
        failures.append("Bing crawl stats unavailable")
    if payload["bing_traffic"].get("ok") and payload["bing_traffic"].get("impressions_30d", 0) == 0:
        failures.append("Bing impressions are still 0 over the API traffic window")
    elif not payload["bing_traffic"].get("ok"):
        failures.append("Bing traffic stats unavailable")

    print(f"CreditDoc Bing/IndexNow watchdog report: {report}")
    print(f"Key file OK: {payload['key_file'].get('ok')}")
    print(
        "Bing crawl: "
        f"date={payload['bing_crawl'].get('last_date')} "
        f"crawled={payload['bing_crawl'].get('last_crawled')} "
        f"in_index={payload['bing_crawl'].get('last_in_index')}"
    )
    print(
        "Bing traffic 30d: "
        f"impressions={payload['bing_traffic'].get('impressions_30d')} "
        f"clicks={payload['bing_traffic'].get('clicks_30d')}"
    )

    if failures:
        print("FAILURES:")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
