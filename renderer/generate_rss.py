#!/usr/bin/env python3
"""
Regenerate /rss.xml, /feed.xml, /blog/rss.xml from data/creditdoc.db blog_posts.

The Astro-era src/pages/rss.xml.ts + feed.xml.ts were deleted during my
AstroKill sweep 2026-07-18 (commit e0c1be3041) without a Python
replacement. Dist files froze at 2026-07-16 as a result. This is that
replacement.

Reads: data/creditdoc.db blog_posts (status='published' OR status IS NULL)
Writes:
  dist/rss.xml
  dist/feed.xml       (identical content, historical alias)
  dist/blog/rss.xml   (was 404 — first-time creation)

Run: python3 renderer/generate_rss.py
Called by: nightly cron (to be added) and manual invocation.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

REPO = Path(__file__).resolve().parent.parent
DB = REPO / "data" / "creditdoc.db"
DIST = REPO / "dist"
SITE = "https://www.creditdoc.co"

RSS_HEADER = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>CreditDoc Blog</title>
    <link>{site}/blog/</link>
    <description>CreditDoc articles on credit, lending, debt, and consumer finance.</description>
    <language>en-us</language>
    <lastBuildDate>{last_build}</lastBuildDate>
    <atom:link href="{self_href}" rel="self" type="application/rss+xml" />
"""

RSS_ITEM = """    <item>
      <title>{title}</title>
      <link>{url}</link>
      <guid isPermaLink="true">{url}</guid>
      <description>{description}</description>
      <pubDate>{pub_date}</pubDate>
      <category>{category}</category>
    </item>
"""

RSS_FOOTER = """  </channel>
</rss>
"""


def rfc822(iso: str) -> str:
    """Convert ISO date/datetime to RFC-822 for RSS pubDate."""
    if not iso:
        return datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    try:
        # Handle YYYY-MM-DD or full ISO
        if "T" in iso:
            dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(iso).replace(tzinfo=timezone.utc)
    except ValueError:
        return datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")


def load_posts() -> list[dict]:
    conn = sqlite3.connect(str(DB))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT slug, data, updated_at
        FROM blog_posts
        WHERE status = 'published' OR status IS NULL OR status = ''
        """
    ).fetchall()
    conn.close()
    posts = []
    for row in rows:
        try:
            data = json.loads(row["data"])
        except (json.JSONDecodeError, TypeError):
            continue
        # Prefer publish_date from data; fall back to row updated_at
        pub_iso = data.get("publish_date") or data.get("published_at") or row["updated_at"]
        posts.append(
            {
                "slug": row["slug"],
                "title": data.get("title") or row["slug"].replace("-", " ").title(),
                "description": (
                    data.get("seo_description")
                    or data.get("description")
                    or data.get("excerpt")
                    or ""
                ),
                "category": data.get("category_label") or data.get("category") or "Credit",
                "pub_iso": pub_iso,
                "updated_at": row["updated_at"],
            }
        )
    # Sort by pub_iso DESC (newest first)
    posts.sort(key=lambda p: p["pub_iso"] or "", reverse=True)
    return posts


def render_rss(self_href: str, posts: list[dict]) -> str:
    last_build = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    out = [RSS_HEADER.format(site=SITE, last_build=last_build, self_href=self_href)]
    for p in posts:
        out.append(
            RSS_ITEM.format(
                title=escape(p["title"]),
                url=f"{SITE}/blog/{p['slug']}/",
                description=escape(p["description"]),
                pub_date=rfc822(p["pub_iso"]),
                category=escape(p["category"]),
            )
        )
    out.append(RSS_FOOTER)
    return "".join(out)


def main() -> None:
    posts = load_posts()
    if not posts:
        raise SystemExit("No published blog_posts found — refusing to write empty RSS.")

    # 3 output paths — all serve identical feed except for atom:link self-href
    targets = [
        (DIST / "rss.xml", f"{SITE}/rss.xml"),
        (DIST / "feed.xml", f"{SITE}/feed.xml"),
        (DIST / "blog" / "rss.xml", f"{SITE}/blog/rss.xml"),
    ]
    for path, self_href in targets:
        path.parent.mkdir(parents=True, exist_ok=True)
        xml = render_rss(self_href, posts)
        path.write_text(xml, encoding="utf-8")
        print(f"  wrote {path.relative_to(REPO)} ({len(posts)} items, {len(xml):,} bytes)")


if __name__ == "__main__":
    main()
