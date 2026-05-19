#!/usr/bin/env python3
"""
CreditDoc Priority Indexing — pushes publishable content pages only.

FOUNDER RULE 2026-04-24: Never submit /review/<slug>/ lender profiles
(FA or otherwise) to search engines. Only submit the pages that earn clicks
and move users toward money: money pages, drip, blog, education.

Push tiers (in order — per AI Council 2026-05-13, reordered 2026-05-14):
    1. City guides         /credit-guide/<slug>/      (fastest-ranking, council #1)
    2. Money pages         /best/<slug>/              (listicles)
    3. Blog                /blog/<slug>/              (blog_posts)
    4. Brand hubs          /brand/<slug>/             (brand JSON exists)
    5. Compare pages       /compare/<slug>/           (comparisons)
    6. State pages         /state/<slug>/             (already tracked in GSC)

EXCLUDED (Jammi submits these manually via GSC Request Indexing, 10/day):
    - Drip                /answers/<slug>/
    - Education           /financial-wellness/<slug>/

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
from pathlib import Path

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from creditdoc_db import CreditDocDB

# Import proven functions from gsc_indexing.py
sys.path.insert(0, "/srv/BusinessOps/tools")
from gsc_indexing import get_indexing_api_token, push_indexing_api  # push_indexing_api now stamps shared cooldown

TELEGRAM_TOKEN = ""  # removed — all alerts via Harvey email (cron_alert.py)
TELEGRAM_CHAT_ID = ""

INDEXNOW_KEY = "f2018aa106044007bf54b7cde9067a1e"  # verified: /f2018...txt live
INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"

SITE = "https://www.creditdoc.co"  # canonical (matches indexation_status + GSC property)
SITE_INDEXING_API = "https://creditdoc.co"  # GSC property is non-www; Indexing API rejects www
GOOGLE_DAILY_QUOTA = 200
BRANDS_DIR = Path(__file__).resolve().parents[1] / "src" / "content" / "brands"

# Re-push window: re-submit a confirmed-indexed URL only if it hasn't been
# pushed to the Indexing API in the last RESUBMIT_DAYS, AND its content
# probably changed. For now: never re-push PASS rows (Google has them).
RESUBMIT_DAYS = 30


def fetch_priority_urls(db, limit, force_all=False):
    """Publishable URLs only: money pages, drip, education, blog, brand,
    compare, and state pages.
    /review/* lender profiles are NEVER pushed (founder rule 2026-04-24).

    Quota-conserving filter (2026-05-03, hardened):
      - PUSH ONLY urls with indexation_status.verdict='NEUTRAL' (verified not-indexed)
      - SKIP 'PASS' (Google has them) — quota waste
      - SKIP unchecked / unknown (no row, NULL verdict) — pushing blind is idiotic.
        These get inspected by creditdoc_daily_gsc_queue (06:15 UTC) and become
        eligible the next day once their verdict comes back NEUTRAL.
      - SKIP urls submitted via Indexing API in last RESUBMIT_DAYS (cooldown) —
        Google has the request; nagging it again wastes quota.
    Pass force_all=True to bypass the filter (catastrophic re-index only).
    """
    urls = []

    brand_slugs = [
        p.stem for p in sorted(BRANDS_DIR.glob("*.json"))
        if p.stem and "/" not in p.stem
    ]
    db.conn.execute("DROP TABLE IF EXISTS temp_publishable_brand_slugs")
    db.conn.execute("CREATE TEMP TABLE temp_publishable_brand_slugs (slug TEXT PRIMARY KEY)")
    db.conn.executemany(
        "INSERT OR IGNORE INTO temp_publishable_brand_slugs (slug) VALUES (?)",
        [(s,) for s in brand_slugs],
    )

    # Answers + wellness are excluded: Jammi submits those manually via GSC
    # Request Indexing (10/day). Automated API handles everything else.
    # City guides added + promoted to tier 1 per AI Council (2026-05-14).
    publishable_cte = f"""
    publishable AS (
      SELECT DISTINCT 'city' AS tier,
             TRIM(REPLACE(page_url, '{SITE}/', ''), '/') AS path,
             TRIM(REPLACE(page_url, '{SITE}/', ''), '/') AS sort_key
        FROM indexation_status
        WHERE page_url LIKE '{SITE}/credit-guide/%'
      UNION ALL
      SELECT 'money' AS tier, 'best/' || slug AS path, slug AS sort_key
        FROM listicles
      UNION ALL
      SELECT 'blog' AS tier, 'blog/' || slug AS path, COALESCE(updated_at, slug) AS sort_key
        FROM blog_posts
        WHERE status='published'
      UNION ALL
      SELECT 'brand' AS tier, 'brand/' || b.slug AS path, b.slug AS sort_key
        FROM temp_publishable_brand_slugs b
        JOIN (
          SELECT DISTINCT brand_slug
          FROM lenders
          WHERE brand_slug IS NOT NULL
            AND brand_slug <> ''
            AND processing_status='ready_for_index'
        ) l ON l.brand_slug = b.slug
      UNION ALL
      SELECT 'compare' AS tier, 'compare/' || slug AS path, COALESCE(updated_at, slug) AS sort_key
        FROM comparisons
      UNION ALL
      SELECT DISTINCT 'state' AS tier,
             TRIM(REPLACE(page_url, '{SITE}/', ''), '/') AS path,
             TRIM(REPLACE(page_url, '{SITE}/', ''), '/') AS sort_key
        FROM indexation_status
        WHERE page_url LIKE '{SITE}/state/%'
    )"""

    if force_all:
        # Emergency re-index: bypass all filters, push everything.
        status_cte = ""
        join_clause = "LEFT JOIN indexation_status i"
        where_filter = ""
    else:
        # Normal mode: INNER JOIN forces an indexation_status row to exist,
        # verdict must be NEUTRAL, and cooldown must be expired.
        status_cte = """,
    eligible_status AS (
      SELECT
        page_url,
        MIN(last_request_indexing_submitted) AS last_request_indexing_submitted
      FROM indexation_status
      WHERE verdict = 'NEUTRAL'
        AND COALESCE(coverage_state, '') != 'Alternate page with proper canonical tag'
      GROUP BY page_url
    )"""
        join_clause = "JOIN eligible_status i"
        where_filter = (
            f"WHERE (i.last_request_indexing_submitted IS NULL "
            f"     OR i.last_request_indexing_submitted < datetime('now', '-{RESUBMIT_DAYS} days'))"
        )

    sql = f"""
    WITH {publishable_cte}
    {status_cte}
    SELECT p.tier, p.path,
           CASE WHEN i.page_url IS NULL THEN 'UNCHECKED' ELSE 'NEUTRAL' END AS verdict,
           i.last_request_indexing_submitted AS last_pushed
    FROM publishable p
    {join_clause} ON i.page_url = '{SITE}/' || p.path || '/'
    {where_filter}
    ORDER BY
      CASE p.tier
        WHEN 'city' THEN 1
        WHEN 'money' THEN 2
        WHEN 'blog' THEN 3
        WHEN 'brand' THEN 4
        WHEN 'compare' THEN 5
        WHEN 'state' THEN 6
        ELSE 99
      END,
      p.sort_key DESC
    """
    for r in db.conn.execute(sql).fetchall():
        urls.append({
            "url": f"{SITE}/{r['path']}/",
            "slug": r["path"].split("/")[-1],
            "tier": r["tier"],
            "verdict": r["verdict"],
        })

    skipped = {"indexed": 0, "unchecked": 0, "cooldown": 0}
    if not force_all:
        # Show why URLs were filtered out so quota savings are visible.
        breakdown = db.conn.execute(f"""
            WITH {publishable_cte}
            SELECT
              SUM(CASE WHEN i.verdict='PASS' THEN 1 ELSE 0 END) AS indexed,
              SUM(CASE WHEN i.verdict IS NULL OR i.verdict NOT IN ('NEUTRAL','PASS') THEN 1 ELSE 0 END) AS unchecked,
              SUM(CASE WHEN i.verdict='NEUTRAL'
                       AND i.last_request_indexing_submitted IS NOT NULL
                       AND i.last_request_indexing_submitted >= datetime('now', '-{RESUBMIT_DAYS} days')
                       THEN 1 ELSE 0 END) AS cooldown
            FROM publishable p
            LEFT JOIN indexation_status i ON i.page_url = '{SITE}/' || p.path || '/'
        """).fetchone()
        skipped["indexed"] = breakdown[0] or 0
        skipped["unchecked"] = breakdown[1] or 0
        skipped["cooldown"] = breakdown[2] or 0

    by_tier = {t: sum(1 for u in urls if u["tier"] == t) for t in ("city", "money", "blog", "brand", "compare", "state")}
    print(f"  City:     {by_tier['city']}")
    print(f"  Money:    {by_tier['money']}")
    print(f"  Blog:     {by_tier['blog']}")
    print(f"  Brand:    {by_tier['brand']}")
    print(f"  Compare:  {by_tier['compare']}")
    print(f"  State:    {by_tier['state']}")
    print(f"  (Answers + wellness excluded — Jammi submits manually)")
    if not force_all:
        print(f"  (Skipped {skipped['indexed']} already indexed (PASS), "
              f"{skipped['unchecked']} unverified, "
              f"{skipped['cooldown']} in {RESUBMIT_DAYS}-day cooldown)")
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


def stamp_submitted(db, urls):
    """Mark URLs as just-pushed-to-Indexing-API in indexation_status.
    Without this, the daily email queue will re-suggest the same URLs tomorrow,
    and the cooldown filter on the priority indexer never engages."""
    if not urls:
        return 0
    placeholders = ",".join("?" * len(urls))
    db.conn.execute(
        f"""UPDATE indexation_status
            SET last_request_indexing_submitted = datetime('now'),
                request_indexing_count = COALESCE(request_indexing_count, 0) + 1
            WHERE page_url IN ({placeholders})""",
        urls,
    )
    db.conn.commit()
    return db.conn.total_changes


def send_telegram(message):
    return  # DISABLED — all CreditDoc alerts via Harvey email (cron_alert.py)


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
            urls_only = [u["url"].replace(SITE, SITE_INDEXING_API) for u in url_list[:GOOGLE_DAILY_QUOTA]]
            g_ok, g_fail = push_indexing_api(sa_token, urls_only)
            print(f"  Google: {g_ok} OK, {g_fail} failed")
            # Stamp the URLs that were actually accepted (push_indexing_api
            # returns ok-count and stops early on 429 — first g_ok URLs are the
            # ones Google has now seen). Without this stamp, tomorrow's daily
            # email queue and the cooldown filter both miss the submission.
            if g_ok:
                www_urls = [u.replace(SITE_INDEXING_API, SITE) for u in urls_only[:g_ok]]
                n = stamp_submitted(db, www_urls)
                print(f"  DB stamped: {n} rows (cooldown applies for {RESUBMIT_DAYS}d)")
        else:
            print("  Skipped: no service account token")

    # Telegram report
    money_count = sum(1 for u in url_list if u['tier'] == 'money')
    drip_count = sum(1 for u in url_list if u['tier'] == 'drip')
    blog_count = sum(1 for u in url_list if u['tier'] == 'blog')
    brand_count = sum(1 for u in url_list if u['tier'] == 'brand')
    compare_count = sum(1 for u in url_list if u['tier'] == 'compare')
    msg = (
        f"<b>📊 CreditDoc Priority Indexing</b>\n"
        f"{ts}\n\n"
        f"<b>Queue:</b> {len(url_list)} URLs "
        f"(money: {money_count}, blog: {blog_count}, "
        f"brand: {brand_count}, compare: {compare_count})\n\n"
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
