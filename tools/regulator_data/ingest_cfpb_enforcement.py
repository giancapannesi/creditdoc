#!/usr/bin/env python3
"""Phase 1: Ingest CFPB Enforcement Actions into regulator.db

Strategy: scrape paginated listing at /enforcement/actions/?page=N to collect all
action slugs (~385), then fetch each detail page to extract company, date, penalty.
"""

import sys
import os
import re
import time
import logging
import argparse
import requests
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from tools.regulator_data.utils import get_db, normalize_company_name, log_ingest_start, log_ingest_end
from tools.regulator_data.config import USER_AGENT, LOG_DIR

os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'regulator_enf.log')),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

HEADERS = {'User-Agent': USER_AGENT}
BASE_URL = 'https://www.consumerfinance.gov'


def collect_action_slugs():
    """Paginate through the enforcement actions listing to collect all unique slugs."""
    all_slugs = []
    seen = set()

    for page in range(1, 50):
        url = f'{BASE_URL}/enforcement/actions/?page={page}'
        log.info(f'Listing page {page}...')
        resp = requests.get(url, headers=HEADERS, timeout=20)
        if resp.status_code != 200:
            break

        slugs = set(re.findall(r'/enforcement/actions/([a-z0-9-]+)/', resp.text))
        slugs.discard('enforcement-action-definitions')

        new_slugs = slugs - seen
        if not new_slugs:
            log.info(f'  No new slugs on page {page}, done collecting')
            break

        for s in new_slugs:
            all_slugs.append(s)
            seen.add(s)

        log.info(f'  +{len(new_slugs)} new slugs (total: {len(all_slugs)})')
        time.sleep(0.5)

    return all_slugs


def parse_detail_page(slug):
    """Fetch and parse a single enforcement action detail page."""
    url = f'{BASE_URL}/enforcement/actions/{slug}/'
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        if resp.status_code != 200:
            log.warning(f'  {slug}: HTTP {resp.status_code}')
            return None
    except Exception as e:
        log.warning(f'  {slug}: {e}')
        return None

    html = resp.text

    title_m = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
    title = re.sub(r'<[^>]+>', '', title_m.group(1)).strip() if title_m else slug.replace('-', ' ').title()

    date_m = re.search(r'(\w+ \d{1,2}, \d{4})', html[:5000])
    action_date = None
    if date_m:
        try:
            action_date = datetime.strptime(date_m.group(1), '%B %d, %Y').strftime('%Y-%m-%d')
        except ValueError:
            pass

    penalty_amount = None
    penalty_patterns = re.findall(r'\$\s*([\d,.]+)\s*(billion|million|thousand)?', html, re.IGNORECASE)
    if penalty_patterns:
        best_val = 0
        for num_str, multiplier in penalty_patterns:
            try:
                num = float(num_str.replace(',', ''))
                if 'billion' in multiplier.lower():
                    num *= 1_000_000_000
                elif 'million' in multiplier.lower():
                    num *= 1_000_000
                elif 'thousand' in multiplier.lower():
                    num *= 1_000
                if num > best_val:
                    best_val = num
            except ValueError:
                continue
        if best_val > 0:
            penalty_amount = best_val

    company = title
    for pattern in [
        r'(?:against|with)\s+(.+?)(?:\s+for\b|\s+to\b|\s+and\s+its\b)',
        r'(?:orders?|action)\s+(?:against\s+)?(.+?)(?:\s+for\b|\s+to\b)',
    ]:
        m = re.search(pattern, title, re.IGNORECASE)
        if m:
            company = m.group(1).strip().rstrip(',.')
            break

    desc_m = re.search(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']', html, re.IGNORECASE)
    description = desc_m.group(1).strip() if desc_m else ''

    return {
        'company': company,
        'title': title,
        'action_date': action_date,
        'penalty_amount': penalty_amount,
        'description': description,
        'case_url': url,
        'status': 'consent_order'
    }


def ingest(dry_run=False):
    log.info('=== CFPB Enforcement Actions Ingest ===')

    # Clear old log for fresh run
    conn = get_db()
    run_id = log_ingest_start(conn, 'cfpb_enforcement')

    try:
        slugs = collect_action_slugs()
        log.info(f'Collected {len(slugs)} enforcement action slugs')

        if dry_run:
            log.info(f'[DRY RUN] Would parse {len(slugs)} detail pages')
            for s in slugs[:5]:
                action = parse_detail_page(s)
                if action:
                    log.info(f'  [DRY RUN] {action["company"]}: ${action.get("penalty_amount", "N/A")} ({action["action_date"]})')
            log_ingest_end(conn, run_id, len(slugs), 0, status='dry_run')
            return

        actions = []
        for i, slug in enumerate(slugs):
            action = parse_detail_page(slug)
            if action:
                actions.append(action)
            if (i + 1) % 25 == 0:
                log.info(f'  Parsed {i+1}/{len(slugs)} ({len(actions)} valid)...')
            time.sleep(0.3)

        log.info(f'Parsed {len(actions)} valid actions from {len(slugs)} pages')

        conn.execute('DELETE FROM cfpb_enforcement_actions')
        inserted = 0
        for a in actions:
            norm = normalize_company_name(a['company'])
            conn.execute(
                'INSERT INTO cfpb_enforcement_actions '
                '(company, company_normalized, title, action_date, penalty_amount, '
                'description, case_url, status) VALUES (?,?,?,?,?,?,?,?)',
                (a['company'], norm, a['title'], a['action_date'],
                 a.get('penalty_amount'), a.get('description', ''),
                 a.get('case_url', ''), a.get('status', ''))
            )
            inserted += 1

        conn.commit()
        total = conn.execute('SELECT COUNT(*) FROM cfpb_enforcement_actions').fetchone()[0]
        distinct = conn.execute('SELECT COUNT(DISTINCT company_normalized) FROM cfpb_enforcement_actions').fetchone()[0]
        log.info(f'Done. {inserted} inserted. Total: {total} actions, {distinct} distinct companies.')

        top5 = conn.execute(
            'SELECT company, penalty_amount, action_date FROM cfpb_enforcement_actions '
            'WHERE penalty_amount IS NOT NULL ORDER BY penalty_amount DESC LIMIT 5'
        ).fetchall()
        log.info('Top 5 by penalty:')
        for r in top5:
            log.info(f'  {r[0]}: ${r[1]:,.0f} ({r[2]})')

        log_ingest_end(conn, run_id, len(slugs), inserted)

    except Exception as e:
        log.error(f'Ingest failed: {e}', exc_info=True)
        log_ingest_end(conn, run_id, 0, 0, status='failed', error_message=str(e))
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Ingest CFPB Enforcement Actions')
    parser.add_argument('--dry-run', action='store_true', help='Preview without inserting')
    args = parser.parse_args()
    ingest(dry_run=args.dry_run)
