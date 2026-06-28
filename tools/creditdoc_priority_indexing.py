#!/usr/bin/env python3
"""
CreditDoc Priority Indexing — pushes publishable content pages only.

FOUNDER RULE 2026-04-24: Never submit /review/<slug>/ lender profiles
(FA or otherwise) to search engines. Only submit the pages that earn clicks
and move users toward money: money pages, drip, blog, education.

Push tiers (founder focus refreshed 2026-06-16):
    1. Tools/quizzes/questionnaires  /tools/<slug>/
    2. Courses/learn                /courses/<slug>/, /learn/
    3. Questions/answers            /answers/<slug>/
    4. Money pages                  /best/, /categories/, /browse/, /compare/
    5. Research/trust               /research/<slug>/ + methodology/disclosure/about
    6. Resources                    /resources/<slug>/
    7. Wellness                     /financial-wellness/<slug>/
    8. Blog                         /blog/<slug>/
    9. Brand hubs                   /brand/<slug>/
   10. State pages                  /state/<slug>/
   99. City guides                  /credit-guide/<slug>/ last

Quota: 200/day Google Indexing API, unlimited IndexNow (Bing/AI search).

Usage:
    python3 creditdoc_priority_indexing.py              # Full run: GSC + IndexNow
    python3 creditdoc_priority_indexing.py --indexnow-only
    python3 creditdoc_priority_indexing.py --tier money --indexnow-only
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
FORCE_GOOGLE_QUEUE_FILE = Path("/srv/BusinessOps/data/creditdoc_force_google_indexing_urls.json")

# Re-push window: re-submit a confirmed-indexed URL only if it hasn't been
# pushed to the Indexing API in the last RESUBMIT_DAYS, AND its content
# probably changed. For now: never re-push PASS rows (Google has them).
RESUBMIT_DAYS = 30


VALID_TIERS = (
    "tools",
    "courses",
    "research",
    "regulatory",
    "resources",
    "wellness",
    "money",
    "answers",
    "city",
    "blog",
    "brand",
    "compare",
    "state",
)


def load_force_google_urls():
    """One-shot Google priority queue.

    These URLs bypass the normal cooldown and are prepended to the next Google
    Indexing API run. Accepted URLs are removed after push, so this file is a
    durable retry mechanism rather than a permanent daily quota drain.
    """
    if not FORCE_GOOGLE_QUEUE_FILE.exists():
        return []
    try:
        payload = json.loads(FORCE_GOOGLE_QUEUE_FILE.read_text())
    except Exception as e:
        print(f"  Force queue unreadable: {FORCE_GOOGLE_QUEUE_FILE}: {e}")
        return []

    urls = payload.get("urls", payload if isinstance(payload, list) else [])
    if not isinstance(urls, list):
        return []

    seen = set()
    normalized = []
    for url in urls:
        if not isinstance(url, str):
            continue
        url = url.strip()
        if not url:
            continue
        if url.startswith("https://creditdoc.co/"):
            url = url.replace("https://creditdoc.co/", f"{SITE}/", 1)
        if not url.startswith(f"{SITE}/"):
            continue
        if not url.endswith("/"):
            url = url + "/"
        if url not in seen:
            seen.add(url)
            normalized.append(url)
    return normalized


def save_force_google_urls(urls):
    FORCE_GOOGLE_QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "site": "creditdoc",
        "purpose": "One-shot forced Google Indexing API priority queue. Accepted URLs are removed by creditdoc_priority_indexing.py.",
        "updated": datetime.now(timezone.utc).isoformat(),
        "urls": urls,
    }
    FORCE_GOOGLE_QUEUE_FILE.write_text(json.dumps(payload, indent=2) + "\n")


def remove_force_google_urls(accepted_urls):
    if not accepted_urls or not FORCE_GOOGLE_QUEUE_FILE.exists():
        return 0
    remaining = [u for u in load_force_google_urls() if u not in set(accepted_urls)]
    before = len(load_force_google_urls())
    save_force_google_urls(remaining)
    return before - len(remaining)


def fetch_priority_urls(db, limit, force_all=False, tier_filter=None, ignore_cooldown=False):
    """Publishable URLs only: tools, courses, research/trust, resources,
    wellness, money pages, answers, city, blog, brand, compare, and state pages.
    /review/* lender profiles are NEVER pushed (founder rule 2026-04-24).

    Quota-conserving filter (2026-05-03, hardened):
      - PUSH ONLY urls with indexation_status.verdict='NEUTRAL' (verified not-indexed)
      - SKIP 'PASS' (Google has them) — quota waste
      - SKIP unchecked / unknown (no row, NULL verdict) — pushing blind is idiotic.
        These get inspected by creditdoc_daily_gsc_queue (06:15 UTC) and become
        eligible the next day once their verdict comes back NEUTRAL.
      - SKIP urls submitted via Indexing API in last RESUBMIT_DAYS (cooldown) —
        Google has the request; nagging it again wastes quota.
        IndexNow-only tier pings may set ignore_cooldown=True because they do
        not spend Google quota.
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

    # Founder focus refreshed 2026-06-16: tools/quizzes/questionnaires,
    # courses, answers, and money pages are the acquisition path. City guides
    # remain useful, but they must not consume priority-indexing quota first.
    publishable_cte = f"""
    publishable AS (
      SELECT DISTINCT 'tools' AS tier,
             TRIM(REPLACE(page_url, '{SITE}/', ''), '/') AS path,
             TRIM(REPLACE(page_url, '{SITE}/', ''), '/') AS sort_key
        FROM indexation_status
        WHERE page_url LIKE '{SITE}/tools/%'
      UNION ALL
      SELECT DISTINCT 'courses' AS tier,
             TRIM(REPLACE(page_url, '{SITE}/', ''), '/') AS path,
             TRIM(REPLACE(page_url, '{SITE}/', ''), '/') AS sort_key
        FROM indexation_status
        WHERE page_url LIKE '{SITE}/courses/%'
           OR page_url = '{SITE}/learn/'
           OR page_url LIKE '{SITE}/learn/%'
      UNION ALL
      SELECT 'answers' AS tier, 'answers/' || slug AS path,
             COALESCE(published_at, updated_at, slug) AS sort_key
        FROM cluster_answers
        WHERE status='published'
      UNION ALL
      SELECT 'money' AS tier, 'best/' || slug AS path, slug AS sort_key
        FROM listicles
      UNION ALL
      SELECT DISTINCT 'money' AS tier,
             TRIM(REPLACE(page_url, '{SITE}/', ''), '/') AS path,
             TRIM(REPLACE(page_url, '{SITE}/', ''), '/') AS sort_key
        FROM indexation_status
        WHERE page_url LIKE '{SITE}/categories/%'
           OR page_url LIKE '{SITE}/browse/%'
           OR page_url LIKE '{SITE}/compare/%'
      UNION ALL
      SELECT DISTINCT 'research' AS tier,
             TRIM(REPLACE(page_url, '{SITE}/', ''), '/') AS path,
             TRIM(REPLACE(page_url, '{SITE}/', ''), '/') AS sort_key
        FROM indexation_status
        WHERE page_url LIKE '{SITE}/research/%'
      UNION ALL
      SELECT 'regulatory' AS tier, 'about' AS path, 'about' AS sort_key
      UNION ALL SELECT 'regulatory' AS tier, 'about/creditdoc-data' AS path, 'about/creditdoc-data' AS sort_key
      UNION ALL SELECT 'regulatory' AS tier, 'about/harvey-brooks' AS path, 'about/harvey-brooks' AS sort_key
      UNION ALL SELECT 'regulatory' AS tier, 'disclosure' AS path, 'disclosure' AS sort_key
      UNION ALL SELECT 'regulatory' AS tier, 'editorial-policy' AS path, 'editorial-policy' AS sort_key
      UNION ALL SELECT 'regulatory' AS tier, 'methodology' AS path, 'methodology' AS sort_key
      UNION ALL SELECT 'regulatory' AS tier, 'privacy' AS path, 'privacy' AS sort_key
      UNION ALL SELECT 'regulatory' AS tier, 'terms' AS path, 'terms' AS sort_key
      UNION ALL
      SELECT DISTINCT 'resources' AS tier,
             TRIM(REPLACE(page_url, '{SITE}/', ''), '/') AS path,
             TRIM(REPLACE(page_url, '{SITE}/', ''), '/') AS sort_key
        FROM indexation_status
        WHERE page_url LIKE '{SITE}/resources/%'
      UNION ALL
      SELECT DISTINCT 'wellness' AS tier,
             TRIM(REPLACE(page_url, '{SITE}/', ''), '/') AS path,
             TRIM(REPLACE(page_url, '{SITE}/', ''), '/') AS sort_key
        FROM indexation_status
        WHERE page_url LIKE '{SITE}/financial-wellness/%'
      UNION ALL
      SELECT DISTINCT 'city' AS tier,
             TRIM(REPLACE(page_url, '{SITE}/', ''), '/') AS path,
             TRIM(REPLACE(page_url, '{SITE}/', ''), '/') AS sort_key
        FROM indexation_status
        WHERE page_url LIKE '{SITE}/credit-guide/%'
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
      -- /compare/ pages are treated as money pages above so they share the
      -- same priority as other conversion-adjacent pages and are not duplicated.
      UNION ALL
      SELECT DISTINCT 'state' AS tier,
             TRIM(REPLACE(page_url, '{SITE}/', ''), '/') AS path,
             TRIM(REPLACE(page_url, '{SITE}/', ''), '/') AS sort_key
        FROM indexation_status
        WHERE page_url LIKE '{SITE}/state/%'
    )"""

    tier_where = ""
    if tier_filter:
        if tier_filter not in VALID_TIERS:
            raise ValueError(f"invalid tier: {tier_filter}")
        tier_where = f"p.tier = '{tier_filter}'"

    if force_all:
        # Emergency re-index: bypass all filters, push everything.
        status_cte = ""
        join_clause = "LEFT JOIN indexation_status i"
        conditions = ["COALESCE(i.coverage_state, '') != 'Alternate page with proper canonical tag'"]
        if tier_where:
            conditions.append(tier_where)
        where_filter = "WHERE " + " AND ".join(conditions)
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
        conditions = []
        if not ignore_cooldown:
            conditions.append(
                f"(i.last_request_indexing_submitted IS NULL "
                f" OR i.last_request_indexing_submitted < datetime('now', '-{RESUBMIT_DAYS} days'))"
            )
        if tier_where:
            conditions.append(tier_where)
        where_filter = "WHERE " + " AND ".join(conditions) if conditions else ""

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
        WHEN 'tools' THEN 1
        WHEN 'courses' THEN 2
        WHEN 'answers' THEN 3
        WHEN 'money' THEN 4
        WHEN 'research' THEN 5
        WHEN 'regulatory' THEN 6
        WHEN 'resources' THEN 7
        WHEN 'wellness' THEN 8
        WHEN 'blog' THEN 9
        WHEN 'brand' THEN 10
        WHEN 'compare' THEN 11
        WHEN 'state' THEN 12
        WHEN 'city' THEN 99
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
        breakdown_where = f"WHERE {tier_where}" if tier_where else ""
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
            {breakdown_where}
        """).fetchone()
        skipped["indexed"] = breakdown[0] or 0
        skipped["unchecked"] = breakdown[1] or 0
        skipped["cooldown"] = breakdown[2] or 0

    by_tier = {t: sum(1 for u in urls if u["tier"] == t) for t in VALID_TIERS}
    print(f"  Tools:    {by_tier['tools']}")
    print(f"  Courses:  {by_tier['courses']}")
    print(f"  Research: {by_tier['research']}")
    print(f"  Reg/trust:{by_tier['regulatory']}")
    print(f"  Resources:{by_tier['resources']}")
    print(f"  Wellness: {by_tier['wellness']}")
    print(f"  Money:    {by_tier['money']}")
    print(f"  Answers:  {by_tier['answers']}")
    print(f"  City:     {by_tier['city']}")
    print(f"  Blog:     {by_tier['blog']}")
    print(f"  Brand:    {by_tier['brand']}")
    print(f"  Compare:  {by_tier['compare']}")
    print(f"  State:    {by_tier['state']}")
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
    parser.add_argument("--tier", choices=VALID_TIERS,
                        help="Only submit one tier, e.g. tools, resources, wellness, money, or answers")
    parser.add_argument("--limit", type=int, default=GOOGLE_DAILY_QUOTA,
                        help=f"Max URLs to push (default {GOOGLE_DAILY_QUOTA})")
    args = parser.parse_args()

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"CreditDoc Priority Indexing — {ts}")
    print(f"{'='*60}")

    db = CreditDocDB()
    indexnow_tier_reping = args.indexnow_only and args.tier in ("money", "answers", "blog")
    url_list = fetch_priority_urls(
        db,
        args.limit,
        tier_filter=args.tier,
        force_all=indexnow_tier_reping,
        ignore_cooldown=indexnow_tier_reping,
    )
    force_urls = []
    if not args.indexnow_only and not args.tier:
        force_urls = load_force_google_urls()
        if force_urls:
            forced_items = [
                {"url": url, "slug": url.rstrip("/").split("/")[-1], "tier": "forced", "verdict": "FORCE"}
                for url in force_urls
            ]
            url_list = forced_items + [u for u in url_list if u["url"] not in set(force_urls)]
            print(f"  Force Google queue: {len(force_urls)} URLs prepended ahead of normal cooldown")
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
                removed = remove_force_google_urls(www_urls)
                if removed:
                    print(f"  Force queue cleared: {removed} accepted URLs removed")
        else:
            print("  Skipped: no service account token")

    # Telegram report. send_telegram is currently disabled, but keep this
    # summary accurate for the day alerts are re-enabled.
    tier_counts = {
        tier: sum(1 for u in url_list if u["tier"] == tier)
        for tier in VALID_TIERS
    }
    tier_summary = ", ".join(
        f"{tier}: {count}" for tier, count in tier_counts.items() if count
    )
    msg = (
        f"<b>📊 CreditDoc Priority Indexing</b>\n"
        f"{ts}\n\n"
        f"<b>Queue:</b> {len(url_list)} URLs ({tier_summary})\n\n"
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
