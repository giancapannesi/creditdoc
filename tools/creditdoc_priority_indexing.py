#!/usr/bin/env python3
"""
CreditDoc Priority Indexing — pushes publishable content pages only.

FOUNDER RULE 2026-04-24: Never submit /review/<slug>/ lender profiles
(FA or otherwise) to search engines. Only submit the pages that earn clicks
and move users toward money: money pages, drip, blog, education.

Push tiers (in order):
    1. Money pages         /best/<slug>/              (listicles)
    2. Drip                /answers/<slug>/           (cluster_answers, published)
    3. Blog                /blog/<slug>/              (blog_posts)
    4. Education           /financial-wellness/<slug>/ (wellness_guides)

Quota: 200/day Google Indexing API, unlimited IndexNow (Bing/AI search).

Usage:
    python3 creditdoc_priority_indexing.py              # Full run: GSC + IndexNow
    python3 creditdoc_priority_indexing.py --indexnow-only
    python3 creditdoc_priority_indexing.py --dry-run
    python3 creditdoc_priority_indexing.py --limit 200  # override cap
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from creditdoc_db import CreditDocDB

# Import proven functions from gsc_indexing.py
sys.path.insert(0, "/srv/BusinessOps/tools")
from gsc_indexing import get_indexing_api_token, push_indexing_api

TELEGRAM_TOKEN = "8552358080:AAFC8FjKxQdj_NJyqwMbgUZrxKzUrn83tGY"
TELEGRAM_CHAT_ID = "1351661181"

INDEXNOW_KEY = "f2018aa106044007bf54b7cde9067a1e"  # verified: /f2018...txt live
INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"

SITE = "https://creditdoc.co"
GOOGLE_DAILY_QUOTA = 200


def fetch_priority_urls(db, limit):
    """Publishable URLs only: money pages, drip, blog, education.
    /review/* lender profiles are NEVER pushed (founder rule 2026-04-24).
    """
    urls = []

    # 1. Money pages — highest commercial intent
    for r in db.conn.execute(
        "SELECT slug FROM listicles ORDER BY slug"
    ).fetchall():
        urls.append({"url": f"{SITE}/best/{r['slug']}/",
                     "slug": r["slug"], "tier": "money"})

    # 2. Drip (/answers/) — published cluster answers only
    for r in db.conn.execute(
        "SELECT slug FROM cluster_answers "
        "WHERE status='published' AND published_at IS NOT NULL "
        "ORDER BY published_at DESC"
    ).fetchall():
        urls.append({"url": f"{SITE}/answers/{r['slug']}/",
                     "slug": r["slug"], "tier": "drip"})

    # 3. Blog posts
    for r in db.conn.execute(
        "SELECT slug FROM blog_posts ORDER BY updated_at DESC"
    ).fetchall():
        urls.append({"url": f"{SITE}/blog/{r['slug']}/",
                     "slug": r["slug"], "tier": "blog"})

    # 4. Wellness guides (education)
    for r in db.conn.execute(
        "SELECT slug FROM wellness_guides ORDER BY updated_at DESC"
    ).fetchall():
        urls.append({"url": f"{SITE}/financial-wellness/{r['slug']}/",
                     "slug": r["slug"], "tier": "wellness"})

    print(f"  Money:    {sum(1 for u in urls if u['tier']=='money')}")
    print(f"  Drip:     {sum(1 for u in urls if u['tier']=='drip')}")
    print(f"  Blog:     {sum(1 for u in urls if u['tier']=='blog')}")
    print(f"  Wellness: {sum(1 for u in urls if u['tier']=='wellness')}")
    return urls[:limit]


def push_indexnow(url_list):
    """IndexNow: single bulk POST, unlimited quota. Returns (ok, fail)."""
    if not url_list:
        return 0, 0

    payload = {
        "host": "creditdoc.co",
        "key": INDEXNOW_KEY,
        "keyLocation": f"https://creditdoc.co/{INDEXNOW_KEY}.txt",
        "urlList": [u["url"] for u in url_list],
    }
    try:
        resp = requests.post(INDEXNOW_ENDPOINT, json=payload, timeout=30)
        if resp.status_code in (200, 202):
            return len(url_list), 0
        print(f"  IndexNow failed: HTTP {resp.status_code} — {resp.text[:200]}")
        return 0, len(url_list)
    except Exception as e:
        print(f"  IndexNow exception: {e}")
        return 0, len(url_list)


def send_telegram(message):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message[:4000],
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=10,
        )
    except Exception as e:
        print(f"Telegram failed: {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--indexnow-only", action="store_true",
                        help="Skip Google Indexing API (already quota-exhausted)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=GOOGLE_DAILY_QUOTA,
                        help=f"Max URLs to push (default {GOOGLE_DAILY_QUOTA})")
    args = parser.parse_args()

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"CreditDoc Priority Indexing — {ts}")
    print(f"{'='*60}")

    db = CreditDocDB()
    url_list = fetch_priority_urls(db, args.limit)
    print(f"\nTotal priority queue: {len(url_list)} URLs")

    if not url_list:
        print("Nothing to push.")
        db.close()
        return

    if args.dry_run:
        print("\n--- DRY RUN — top 10 ---")
        for u in url_list[:10]:
            print(f"  [{u['tier']:8s}] {u['url']}")
        db.close()
        return

    # Step 1: IndexNow (unlimited)
    print(f"\n[1/2] IndexNow push ({len(url_list)} URLs)...")
    in_ok, in_fail = push_indexnow(url_list)
    print(f"  IndexNow: {in_ok} OK, {in_fail} failed")

    # Step 2: Google Indexing API
    g_ok, g_fail = 0, 0
    if not args.indexnow_only:
        print(f"\n[2/2] Google Indexing API push (quota: {GOOGLE_DAILY_QUOTA}/day)...")
        sa_token = get_indexing_api_token()
        if sa_token:
            urls_only = [u["url"] for u in url_list[:GOOGLE_DAILY_QUOTA]]
            g_ok, g_fail = push_indexing_api(sa_token, urls_only)
            print(f"  Google: {g_ok} OK, {g_fail} failed")
        else:
            print("  Skipped: no service account token")

    # Telegram report
    money_count = sum(1 for u in url_list if u['tier'] == 'money')
    drip_count = sum(1 for u in url_list if u['tier'] == 'drip')
    blog_count = sum(1 for u in url_list if u['tier'] == 'blog')
    well_count = sum(1 for u in url_list if u['tier'] == 'wellness')
    msg = (
        f"<b>📊 CreditDoc Priority Indexing</b>\n"
        f"{ts}\n\n"
        f"<b>Queue:</b> {len(url_list)} URLs "
        f"(money: {money_count}, drip: {drip_count}, "
        f"blog: {blog_count}, wellness: {well_count})\n\n"
        f"<b>IndexNow:</b> {in_ok} OK / {in_fail} fail\n"
    )
    if not args.indexnow_only:
        msg += f"<b>Google Indexing:</b> {g_ok} OK / {g_fail} fail\n"
        if g_fail > g_ok:
            msg += f"\n⚠ Google quota likely exhausted — retry tomorrow"
    send_telegram(msg)

    db.close()
    print(f"\n✓ Done.")


if __name__ == "__main__":
    main()
