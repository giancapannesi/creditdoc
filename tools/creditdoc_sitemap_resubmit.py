#!/usr/bin/env python3
"""Resubmit CreditDoc sitemap surfaces where API access allows it.

Bing supports sitemap/feed submission through SubmitFeed. Google Search Console
requires a write-scoped OAuth token; if the stored token is read-only, this
script records that clearly instead of pretending submission happened.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

ROOT = Path("/srv/BusinessOps/creditdoc")
REPORT_DIR = ROOT / "reports" / "sitemap-resubmissions"
GSC_CREDS = Path("/srv/BusinessOps/tools/.gsc-credentials.json")
GSC_PROPERTY = "sc-domain:creditdoc.co"
BING_SITE = "https://creditdoc.co/"
SITEMAPS = [
    "https://www.creditdoc.co/sitemap-index.xml",
    "https://www.creditdoc.co/sitemap.xml",
]

sys.path.insert(0, "/srv/BusinessOps/tools")
from bing_webmaster import api_post  # noqa: E402


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def submit_bing() -> list[dict]:
    results = []
    for sitemap in SITEMAPS:
        data = api_post("SubmitFeed", {"siteUrl": BING_SITE, "feedUrl": sitemap})
        results.append({
            "engine": "bing",
            "sitemap": sitemap,
            "submitted": data is not None,
            "response": data,
        })
    return results


def gsc_credentials() -> Credentials:
    raw = json.loads(GSC_CREDS.read_text())
    return Credentials(
        token=raw.get("token") or raw.get("access_token"),
        refresh_token=raw.get("refresh_token"),
        token_uri=raw.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=raw.get("client_id"),
        client_secret=raw.get("client_secret"),
        scopes=raw.get("scopes") or raw.get("scope", "").split(),
    )


def gsc_has_write_scope(creds: Credentials) -> bool:
    scopes = set(creds.scopes or [])
    return "https://www.googleapis.com/auth/webmasters" in scopes


def inspect_or_submit_gsc(apply: bool) -> list[dict]:
    if not GSC_CREDS.exists():
        return [{"engine": "google", "submitted": False, "note": "missing GSC credentials"}]

    creds = gsc_credentials()
    service = build("webmasters", "v3", credentials=creds, cache_discovery=False)
    results = []

    if apply and gsc_has_write_scope(creds):
        for sitemap in SITEMAPS:
            service.sitemaps().submit(siteUrl=GSC_PROPERTY, feedpath=sitemap).execute()
            results.append({
                "engine": "google",
                "sitemap": sitemap,
                "submitted": True,
                "note": "submitted via GSC sitemap API",
            })
        return results

    try:
        listed = service.sitemaps().list(siteUrl=GSC_PROPERTY).execute().get("sitemap", [])
    except Exception as e:
        return [{"engine": "google", "submitted": False, "note": f"GSC list failed: {e}"}]

    known = {row.get("path"): row for row in listed}
    for sitemap in SITEMAPS:
        row = known.get(sitemap, {})
        results.append({
            "engine": "google",
            "sitemap": sitemap,
            "submitted": False,
            "note": "GSC token is read-only; refresh OAuth with webmasters write scope to submit",
            "lastSubmitted": row.get("lastSubmitted"),
            "lastDownloaded": row.get("lastDownloaded"),
            "errors": row.get("errors"),
            "warnings": row.get("warnings"),
        })
    return results


def write_report(results: list[dict]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORT_DIR / f"sitemap_resubmit_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.md"
    lines = [f"# CreditDoc Sitemap Resubmission - {now()}", ""]
    for row in results:
        lines.append(f"## {row.get('engine', 'unknown').title()}")
        lines.append(f"- Sitemap: {row.get('sitemap', 'n/a')}")
        lines.append(f"- Submitted: {row.get('submitted')}")
        for key in ("note", "lastSubmitted", "lastDownloaded", "errors", "warnings", "response"):
            if key in row and row[key] is not None:
                lines.append(f"- {key}: {row[key]}")
        lines.append("")
    path.write_text("\n".join(lines))
    return path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    results = []
    if args.apply:
        results.extend(submit_bing())
    else:
        results.extend({
            "engine": "bing",
            "sitemap": sitemap,
            "submitted": False,
            "note": "dry run",
        } for sitemap in SITEMAPS)
    results.extend(inspect_or_submit_gsc(args.apply))
    report = write_report(results)

    for row in results:
        print(f"{row.get('engine')} {row.get('sitemap', '')}: submitted={row.get('submitted')} {row.get('note', '')}")
    print(f"Report: {report}")


if __name__ == "__main__":
    main()
