#!/usr/bin/env python3
"""CreditDoc sitemap footprint audit.

Reports URL-family counts from the built XML sitemaps so Bing/Google footprint
changes are measured rather than guessed.
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path("/srv/BusinessOps/creditdoc")
DIST = ROOT / "dist"
REPORT_DIR = ROOT / "reports" / "sitemap-footprint"


def collect_urls() -> list[str]:
    urls: list[str] = []
    for path in sorted(DIST.glob("sitemap-*.xml")):
        if path.name == "sitemap-index.xml":
            continue
        urls.extend(re.findall(r"<loc>(.*?)</loc>", path.read_text(errors="ignore")))
    return urls


def family_for(url: str) -> str:
    parts = [part for part in urlparse(url).path.split("/") if part]
    if not parts:
        return "/"
    if parts[0].startswith("sitemap-") and parts[0].endswith(".xml"):
        return "/sitemap-file/"
    return f"/{parts[0]}/"


def write_report(urls: list[str]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    counts = Counter(family_for(url) for url in urls)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    path = REPORT_DIR / f"sitemap_footprint_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.md"
    lines = [
        f"# CreditDoc Sitemap Footprint - {stamp}",
        "",
        f"Total sitemap URLs: {len(urls):,}",
        "",
        "| Family | URLs |",
        "|---|---:|",
    ]
    for family, count in counts.most_common():
        lines.append(f"| `{family}` | {count:,} |")
    lines.extend([
        "",
        "Notes:",
        "- This is a crawl-footprint audit only; it does not mutate pages.",
        "- Important SEO assets should stay visible: `/best/`, `/tools/`, `/answers/`, `/financial-wellness/`, `/courses/`, `/research/`, and `/resources/`.",
        "- Large programmatic families should be reviewed for quality density before being submitted to Bing/Google.",
    ])
    path.write_text("\n".join(lines) + "\n")
    return path


def main() -> None:
    urls = collect_urls()
    report = write_report(urls)
    print(f"Total sitemap URLs: {len(urls):,}")
    for family, count in Counter(family_for(url) for url in urls).most_common(25):
        print(f"{family:25} {count:8,}")
    print(f"Report: {report}")


if __name__ == "__main__":
    main()
