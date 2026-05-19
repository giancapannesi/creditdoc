#!/usr/bin/env python3
"""Phase 2: Ingest CFPB Consumer Complaints into regulator.db"""

import sys
import os
import time
import logging
import argparse
import requests
from datetime import datetime, timedelta, timezone
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from tools.regulator_data.utils import get_db, normalize_company_name, log_ingest_start, log_ingest_end
from tools.regulator_data.config import (
    USER_AGENT, LOG_DIR, CFPB_COMPLAINTS_API,
    CFPB_COMPLAINTS_PAGE_SIZE, CFPB_COMPLAINTS_RATE_LIMIT
)

os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'regulator_cfpb.log')),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

HEADERS = {'User-Agent': USER_AGENT}


def _api_get(params, timeout=(10, 60), retries=5):
    """GET with retry on timeout/5xx. 400 errors raise immediately (no retry)."""
    for attempt in range(retries):
        try:
            resp = requests.get(CFPB_COMPLAINTS_API, params=params, headers=HEADERS, timeout=timeout)
            if resp.status_code == 400:
                resp.raise_for_status()
            if resp.status_code >= 500 and attempt < retries - 1:
                wait = 30 * (attempt + 1)
                log.warning(f'  HTTP {resp.status_code}, retry {attempt+1}/{retries} in {wait}s...')
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
            if attempt < retries - 1:
                wait = 30 * (attempt + 1)
                log.warning(f'  {type(e).__name__}, retry {attempt+1}/{retries} in {wait}s...')
                time.sleep(wait)
            else:
                raise
    return resp


def get_last_complaint_date(conn):
    """Get the most recent complaint date in DB for incremental mode."""
    row = conn.execute('SELECT MAX(date_received) FROM cfpb_complaints').fetchone()
    return row[0] if row and row[0] else None


def _parse_hit(hit):
    """Extract complaint record from an API hit."""
    src = hit.get('_source', {})
    return {
        'complaint_id': src.get('complaint_id'),
        'date_received': src.get('date_received'),
        'product': src.get('product'),
        'sub_product': src.get('sub_product'),
        'issue': src.get('issue'),
        'sub_issue': src.get('sub_issue'),
        'company': src.get('company'),
        'state': src.get('state'),
        'consumer_consent_provided': src.get('consumer_consent_provided'),
        'submitted_via': src.get('submitted_via'),
        'date_sent_to_company': src.get('date_sent_to_company'),
        'company_response': src.get('company_response'),
        'timely_response': src.get('timely'),
        'consumer_disputed': src.get('consumer_disputed'),
    }


US_STATES = [
    'AL','AK','AZ','AR','CA','CO','CT','DE','DC','FL','GA','HI','ID','IL','IN',
    'IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH',
    'NJ','NM','NY','NC','ND','OH','OK','OR','PA','PR','RI','SC','SD','TN','TX',
    'UT','VT','VA','WA','WV','WI','WY','GU','VI','AS','MP','AA','AE','AP',
]


def _paginate(base_params, page_size=CFPB_COMPLAINTS_PAGE_SIZE):
    """Paginate within ES 10K limit for a given set of filter params."""
    offset = 0
    while True:
        remaining = min(page_size, 10000 - offset)
        if remaining <= 0:
            break
        params = {**base_params, 'size': remaining, 'sort': 'created_date_desc',
                  'no_aggs': 'true', 'frm': offset}
        resp = _api_get(params)
        hits = resp.json().get('hits', {}).get('hits', [])
        if not hits:
            break
        for hit in hits:
            yield _parse_hit(hit)
        if len(hits) < remaining:
            break
        offset += len(hits)
        time.sleep(CFPB_COMPLAINTS_RATE_LIMIT)


def _fetch_by_product(win_min, win_max, page_size=CFPB_COMPLAINTS_PAGE_SIZE):
    """Fetch complaints for a single day by product, then by state if still >10K."""
    try:
        probe = _api_get({
            'date_received_min': win_min, 'date_received_max': win_max, 'size': 0,
        })
    except Exception as e:
        log.warning(f'    Product probe failed for {win_min}: {e}')
        return
    buckets = probe.json().get('aggregations', {}).get('product', {}).get('product', {}).get('buckets', [])
    products = [(b['key'], b['doc_count']) for b in buckets]
    log.info(f'    Fetching {win_min} by {len(products)} product categories')

    for prod, count in products:
        base = {'date_received_min': win_min, 'date_received_max': win_max, 'product': prod}
        if count <= 9999:
            try:
                yield from _paginate(base, page_size)
            except Exception as e:
                log.warning(f'    SKIP product "{prod}" on {win_min}: {e}')
        else:
            log.info(f'    Product "{prod}" has {count} — sub-splitting by state')
            for st in US_STATES:
                try:
                    yield from _paginate({**base, 'state': st}, page_size)
                except Exception as e:
                    log.warning(f'    SKIP state {st} product "{prod}" on {win_min}: {e}')
                time.sleep(0.3)


def _fetch_window(win_min, win_max, page_size=CFPB_COMPLAINTS_PAGE_SIZE):
    """Fetch all complaints in one date window. Auto-splits if >9,999 records."""
    try:
        probe = _api_get({
            'date_received_min': win_min, 'date_received_max': win_max,
            'size': 1, 'no_aggs': 'true', 'frm': 0
        })
        total = probe.json().get('hits', {}).get('total', {}).get('value', 0)
    except Exception as e:
        log.warning(f'  Probe failed for {win_min}→{win_max}: {e}')
        return

    if total == 0:
        return

    if total > 9999:
        start = datetime.strptime(win_min, '%Y-%m-%d')
        end = datetime.strptime(win_max, '%Y-%m-%d')
        if (end - start).days < 1:
            log.info(f'  Single day {win_min} has {total} records — splitting by product')
            yield from _fetch_by_product(win_min, win_max, page_size)
            return
        else:
            mid = start + (end - start) / 2
            mid_str = mid.strftime('%Y-%m-%d')
            log.info(f'  Auto-splitting {win_min}→{win_max} ({total} records) at {mid_str}')
            yield from _fetch_window(win_min, mid_str, page_size)
            next_day = (mid + timedelta(days=1)).strftime('%Y-%m-%d')
            if next_day <= win_max:
                yield from _fetch_window(next_day, win_max, page_size)
            return

    offset = 0
    fetched = 0
    while True:
        remaining = min(page_size, 10000 - offset)
        if remaining <= 0:
            log.warning(f'  Hit ES 10K cap on {win_min}→{win_max} (fetched {fetched}/{total})')
            break
        params = {
            'date_received_min': win_min, 'date_received_max': win_max,
            'size': remaining, 'sort': 'created_date_desc',
            'no_aggs': 'true', 'frm': offset
        }
        resp = _api_get(params)
        hits = resp.json().get('hits', {}).get('hits', [])
        if not hits:
            break
        for hit in hits:
            yield _parse_hit(hit)
        fetched += len(hits)
        if fetched >= total or len(hits) < remaining:
            break
        offset += len(hits)
        time.sleep(CFPB_COMPLAINTS_RATE_LIMIT)


def fetch_complaints(date_min, date_max, page_size=CFPB_COMPLAINTS_PAGE_SIZE):
    """Yield complaints using 7-day date windows with auto-splitting for ES 10K limit."""
    start = datetime.strptime(date_min[:10], '%Y-%m-%d')
    end = datetime.strptime(date_max[:10], '%Y-%m-%d')
    windows = []
    cursor = start
    while cursor < end:
        win_end = min(cursor + timedelta(days=7), end)
        windows.append((cursor.strftime('%Y-%m-%d'), win_end.strftime('%Y-%m-%d')))
        cursor = win_end + timedelta(days=1)

    log.info(f'Split {date_min[:10]}→{date_max[:10]} into {len(windows)} windows (7-day, auto-split if >9999)')

    grand_total = 0
    skipped_windows = []
    for i, (win_min, win_max) in enumerate(windows):
        window_count = 0
        try:
            for complaint in _fetch_window(win_min, win_max, page_size):
                yield complaint
                window_count += 1
        except Exception as e:
            log.warning(f'  SKIP window {win_min}→{win_max} after {window_count} records: {e}')
            skipped_windows.append((win_min, win_max, str(e)))
        grand_total += window_count
        if window_count > 0:
            log.info(f'  Window {i+1}/{len(windows)} [{win_min}→{win_max}]: {window_count} (total: {grand_total})')
        time.sleep(CFPB_COMPLAINTS_RATE_LIMIT)
    if skipped_windows:
        log.warning(f'  {len(skipped_windows)} windows skipped due to errors: {skipped_windows}')


def compute_company_stats(conn):
    """Recompute cfpb_company_stats from raw complaints."""
    log.info('Computing company stats...')
    now = datetime.now(timezone.utc)
    date_12mo = (now - timedelta(days=365)).strftime('%Y-%m-%d')
    date_3mo = (now - timedelta(days=90)).strftime('%Y-%m-%d')

    conn.execute('DELETE FROM cfpb_company_stats')

    companies = [r[0] for r in conn.execute(
        'SELECT DISTINCT company_normalized FROM cfpb_complaints WHERE company_normalized != ""'
    ).fetchall()]

    log.info(f'Computing stats for {len(companies)} companies...')
    batch = []

    for i, comp in enumerate(companies):
        total_all = conn.execute(
            'SELECT COUNT(*) FROM cfpb_complaints WHERE company_normalized=?', (comp,)
        ).fetchone()[0]

        if total_all < 5:
            continue

        total_12 = conn.execute(
            'SELECT COUNT(*) FROM cfpb_complaints WHERE company_normalized=? AND date_received>=?',
            (comp, date_12mo)
        ).fetchone()[0]

        total_3 = conn.execute(
            'SELECT COUNT(*) FROM cfpb_complaints WHERE company_normalized=? AND date_received>=?',
            (comp, date_3mo)
        ).fetchone()[0]

        timely_count = conn.execute(
            'SELECT COUNT(*) FROM cfpb_complaints WHERE company_normalized=? AND timely_response="Yes"',
            (comp,)
        ).fetchone()[0]
        timely_rate = timely_count / total_all if total_all > 0 else 0

        relief_count = conn.execute(
            'SELECT COUNT(*) FROM cfpb_complaints WHERE company_normalized=? AND '
            '(company_response LIKE "%monetary relief%" OR company_response LIKE "%non-monetary relief%")',
            (comp,)
        ).fetchone()[0]
        relief_rate = relief_count / total_all if total_all > 0 else 0

        issues = conn.execute(
            'SELECT issue, COUNT(*) as cnt FROM cfpb_complaints '
            'WHERE company_normalized=? AND issue IS NOT NULL '
            'GROUP BY issue ORDER BY cnt DESC LIMIT 3', (comp,)
        ).fetchall()

        issue_data = []
        for issue_row in issues:
            pct = issue_row[1] / total_all * 100 if total_all > 0 else 0
            issue_data.append((issue_row[0], round(pct, 1)))
        while len(issue_data) < 3:
            issue_data.append((None, None))

        if total_12 > 0 and total_3 > 0:
            monthly_12 = total_12 / 12
            monthly_3 = total_3 / 3
            if monthly_3 > monthly_12 * 1.2:
                trend = 'growing'
            elif monthly_3 < monthly_12 * 0.8:
                trend = 'declining'
            else:
                trend = 'stable'
        else:
            trend = 'stable'

        batch.append((
            comp, total_all, total_12, total_3,
            round(timely_rate, 4), round(relief_rate, 4),
            issue_data[0][0], issue_data[0][1],
            issue_data[1][0], issue_data[1][1],
            issue_data[2][0], issue_data[2][1],
            trend, now.isoformat()
        ))

        if (i + 1) % 500 == 0:
            log.info(f'  Computed {i+1}/{len(companies)}...')

    conn.executemany(
        'INSERT INTO cfpb_company_stats VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
        batch
    )
    conn.commit()
    log.info(f'Stats computed for {len(batch)} companies (≥5 complaints)')


def ingest(backfill_days=730, dry_run=False, date_min_override=None, date_max_override=None, skip_stats=False):
    log.info(f'=== CFPB Consumer Complaints Ingest ===')
    conn = get_db()
    run_id = log_ingest_start(conn, 'cfpb_complaints')

    try:
        now = datetime.now(timezone.utc)

        if date_min_override:
            date_min = date_min_override
            log.info(f'Explicit date range: from {date_min}')
        else:
            last_date = get_last_complaint_date(conn)
            if last_date:
                date_min = last_date[:10]
                log.info(f'Incremental mode: fetching from {date_min}')
            else:
                date_min = (now - timedelta(days=backfill_days)).strftime('%Y-%m-%d')
                log.info(f'Backfill mode: fetching from {date_min}')

        date_max = date_max_override or now.strftime('%Y-%m-%d')
        log.info(f'Date range: {date_min} → {date_max}')

        if dry_run:
            log.info('[DRY RUN] Would fetch complaints from {} to {}'.format(date_min, date_max))
            count = 0
            for complaint in fetch_complaints(date_min, date_max, page_size=10):
                log.info(f'  [DRY RUN] {complaint["company"]}: {complaint["product"]} - {complaint["issue"]}')
                count += 1
                if count >= 10:
                    break
            log_ingest_end(conn, run_id, count, 0, status='dry_run')
            return

        fetched = 0
        inserted = 0
        batch = []
        batch_size = 5000

        for complaint in fetch_complaints(date_min, date_max):
            fetched += 1
            norm = normalize_company_name(complaint['company'] or '')

            batch.append((
                complaint['complaint_id'],
                complaint['date_received'],
                complaint['product'],
                complaint['sub_product'],
                complaint['issue'],
                complaint['sub_issue'],
                complaint['company'],
                norm,
                complaint['state'],
                complaint['consumer_consent_provided'],
                complaint['submitted_via'],
                complaint['date_sent_to_company'],
                complaint['company_response'],
                complaint['timely_response'],
                complaint['consumer_disputed'],
            ))

            if len(batch) >= batch_size:
                conn.executemany(
                    'INSERT OR IGNORE INTO cfpb_complaints '
                    '(complaint_id, date_received, product, sub_product, issue, sub_issue, '
                    'company, company_normalized, state, consumer_consent_provided, '
                    'submitted_via, date_sent_to_company, company_response, '
                    'timely_response, consumer_disputed) '
                    'VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                    batch
                )
                inserted += conn.total_changes
                conn.commit()
                log.info(f'  Batch committed. Fetched: {fetched}, DB total changes: {inserted}')
                batch = []

        if batch:
            conn.executemany(
                'INSERT OR IGNORE INTO cfpb_complaints '
                '(complaint_id, date_received, product, sub_product, issue, sub_issue, '
                'company, company_normalized, state, consumer_consent_provided, '
                'submitted_via, date_sent_to_company, company_response, '
                'timely_response, consumer_disputed) '
                'VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                batch
            )
            conn.commit()

        total_in_db = conn.execute('SELECT COUNT(*) FROM cfpb_complaints').fetchone()[0]
        log.info(f'Complaints loaded. Fetched: {fetched}, Total in DB: {total_in_db}')

        if not skip_stats:
            compute_company_stats(conn)
            stats_count = conn.execute('SELECT COUNT(*) FROM cfpb_company_stats').fetchone()[0]
            log.info(f'Final: {total_in_db} complaints, {stats_count} company stats rows')
        else:
            log.info(f'Final: {total_in_db} complaints (stats skipped for batch mode)')

        log_ingest_end(conn, run_id, fetched, total_in_db)

    except Exception as e:
        log.error(f'Ingest failed: {e}', exc_info=True)
        log_ingest_end(conn, run_id, 0, 0, status='failed', error_message=str(e))
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Ingest CFPB Consumer Complaints')
    parser.add_argument('--backfill-days', type=int, default=730, help='Days to backfill (default 730)')
    parser.add_argument('--date-min', type=str, help='Explicit start date (YYYY-MM-DD)')
    parser.add_argument('--date-max', type=str, help='Explicit end date (YYYY-MM-DD)')
    parser.add_argument('--skip-stats', action='store_true', help='Skip company stats (for batch mode)')
    parser.add_argument('--dry-run', action='store_true', help='Preview without inserting')
    args = parser.parse_args()
    ingest(backfill_days=args.backfill_days, dry_run=args.dry_run,
           date_min_override=args.date_min, date_max_override=args.date_max,
           skip_stats=args.skip_stats)
