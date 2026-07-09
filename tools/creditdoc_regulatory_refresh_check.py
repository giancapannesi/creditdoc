#!/usr/bin/env python3
"""CreditDoc regulatory link drift and refresh scheduler report."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
STATES_PATH = ROOT / "src" / "content" / "states.json"
REPORT_DIR = ROOT / "reports" / "regulatory-refresh"
STATIC_URLS = [
    "https://www.creditdoc.co/tools/state-consumer-credit-regulator-directory/",
    "https://www.creditdoc.co/state/",
    "https://www.creditdoc.co/research/consumer-complaints/",
    "https://www.creditdoc.co/about/creditdoc-data/",
    "https://www.consumerfinance.gov/complaint/",
    "https://reportfraud.ftc.gov/",
    "https://www.annualcreditreport.com/",
]


def collect_urls() -> list[tuple[str, str]]:
    urls: list[tuple[str, str]] = [(url, "static") for url in STATIC_URLS]
    if not STATES_PATH.exists():
      return urls

    data = json.loads(STATES_PATH.read_text())
    records = data if isinstance(data, list) else list(data.values())
    for state in records:
        label = state.get("name") or state.get("slug") or "state"
        fields = [
            state.get("consumer_protection_url"),
            state.get("licensing_board_url"),
            state.get("attorney_general_url"),
        ]
        for field in fields:
            if isinstance(field, str) and field.startswith("http"):
                urls.append((field, label))
        for key in ("complaint_resources", "statute_links"):
            items = state.get(key)
            if isinstance(items, list):
                for item in items:
                    url = item.get("url") if isinstance(item, dict) else None
                    if isinstance(url, str) and url.startswith("http"):
                        urls.append((url, f"{label}:{key}"))

    deduped: dict[str, str] = {}
    for url, source in urls:
        deduped.setdefault(url, source)
    return sorted(deduped.items())


def check_url(url: str, timeout: int) -> tuple[str, int | None, str]:
    req = Request(url, method="HEAD", headers={"User-Agent": "CreditDocRegulatoryRefresh/1.0"})
    try:
        with urlopen(req, timeout=timeout) as res:
            return ("ok", res.status, "")
    except HTTPError as exc:
        if exc.code in {403, 405, 429}:
            try:
                req_get = Request(url, method="GET", headers={"User-Agent": "CreditDocRegulatoryRefresh/1.0"})
                with urlopen(req_get, timeout=timeout) as res:
                    return ("ok", res.status, "GET fallback")
            except Exception as inner:
                return ("warn", exc.code, f"HEAD {exc.code}; GET fallback failed: {inner}")
        return ("fail", exc.code, str(exc))
    except (URLError, TimeoutError) as exc:
        return ("fail", None, str(exc))


def write_report(rows: list[dict], full: bool) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = REPORT_DIR / f"regulatory_refresh_{stamp}.md"
    failed = [row for row in rows if row["status"] == "fail"]
    warned = [row for row in rows if row["status"] == "warn"]
    mode = "six-month full refresh checklist" if full else "monthly link drift check"
    lines = [
        f"# CreditDoc Regulatory Refresh - {stamp}",
        "",
        f"- Mode: {mode}",
        f"- URLs checked: {len(rows)}",
        f"- Failed: {len(failed)}",
        f"- Warnings: {len(warned)}",
        "",
    ]
    if full:
        lines.extend([
            "## Manual Full-Refresh Checklist",
            "",
            "- Verify state regulator names and official URLs.",
            "- Verify attorney general / consumer protection complaint URLs.",
            "- Verify statute and lending-law references.",
            "- Verify CFPB/FTC complaint-routing links.",
            "- Review rate-cap and fee-context wording for stale claims.",
            "- Update page `dateModified` / schema where substantive changes are made.",
            "- Keep all copy educational and avoid unverified licensing claims.",
            "",
        ])
    if failed or warned:
        lines.append("## Issues")
        lines.append("")
        for row in failed + warned:
            lines.append(f"- `{row['status']}` {row['code'] or ''} {row['url']} ({row['source']}) {row['note']}".strip())
        lines.append("")
    lines.append("## Checked URLs")
    lines.append("")
    for row in rows:
        lines.append(f"- `{row['status']}` {row['code'] or ''} {row['url']} ({row['source']})".strip())
    path.write_text("\n".join(lines) + "\n")
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="include six-month manual refresh checklist")
    parser.add_argument("--timeout", type=int, default=12)
    parser.add_argument("--max-urls", type=int, default=0, help="debug cap; 0 checks all URLs")
    args = parser.parse_args()

    urls = collect_urls()
    if args.max_urls:
        urls = urls[: args.max_urls]

    rows = []
    for url, source in urls:
        status, code, note = check_url(url, args.timeout)
        rows.append({"url": url, "source": source, "status": status, "code": code, "note": note})

    report = write_report(rows, args.full)
    failed = [row for row in rows if row["status"] == "fail"]
    warned = [row for row in rows if row["status"] == "warn"]
    print(f"CreditDoc regulatory refresh check: checked={len(rows)} failed={len(failed)} warnings={len(warned)} report={report}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
