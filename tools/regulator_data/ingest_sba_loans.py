#!/usr/bin/env python3
"""Phase 4: Ingest SBA 7(a) + 504 Loans into regulator.db from data.sba.gov bulk CSV"""

import sys
import os
import csv
import io
import logging
import argparse
import requests
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from tools.regulator_data.utils import get_db, normalize_company_name, log_ingest_start, log_ingest_end
from tools.regulator_data.config import USER_AGENT, LOG_DIR

os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'regulator_sba.log')),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

HEADERS = {'User-Agent': USER_AGENT}

SBA_URLS = {
    '7a_recent': 'https://data.sba.gov/en/dataset/0ff8e8e9-b967-4f4e-987c-6ac78c575087/resource/d67d3ccb-2002-4134-a288-481b51cd3479/download/foia-7a-fy2020-present-asof-260331.csv',
    '504_recent': 'https://data.sba.gov/en/dataset/0ff8e8e9-b967-4f4e-987c-6ac78c575087/resource/4ad7f0f1-9da6-4d90-8bdb-89a6f821a1a9/download/foia-504-fy2010-present-asof-260331.csv',
}

DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '..', 'data', 'sba')


def download_csv(name, url):
    """Download SBA CSV to local cache."""
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    local_path = os.path.join(DOWNLOAD_DIR, f'{name}.csv')

    if os.path.exists(local_path):
        size_mb = os.path.getsize(local_path) / 1024 / 1024
        log.info(f'{name}: using cached file ({size_mb:.1f} MB)')
        return local_path

    log.info(f'{name}: downloading from SBA...')
    resp = requests.get(url, headers=HEADERS, stream=True, timeout=120)
    resp.raise_for_status()

    with open(local_path, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)

    size_mb = os.path.getsize(local_path) / 1024 / 1024
    log.info(f'{name}: downloaded ({size_mb:.1f} MB)')
    return local_path


def parse_float(val):
    if not val:
        return 0.0
    try:
        return float(val.strip().replace(',', ''))
    except (ValueError, AttributeError):
        return 0.0


def parse_int(val):
    if not val:
        return None
    try:
        return int(val.strip())
    except (ValueError, AttributeError):
        return None


def load_csv(csv_path, program_label, min_fy=2020):
    """Parse SBA CSV and yield loan records."""
    log.info(f'Parsing {csv_path} (program={program_label}, min_fy={min_fy})...')
    count = 0

    with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        for row in reader:
            fy = parse_int(row.get('approvalfy', row.get('ApprovalFY', '')))
            if not fy or fy < min_fy:
                continue

            bank_name = (row.get('bankname', row.get('BankName', '')) or '').strip()
            if not bank_name:
                continue

            gross = parse_float(row.get('grossapproval', row.get('GrossApproval', '')))
            sba_guar = parse_float(row.get('sbaguaranteedapproval', row.get('SBAGuaranteedApproval', '')))
            borrower_state = (row.get('borrstate', row.get('BorrState', '')) or '').strip()
            bank_city = (row.get('bankcity', row.get('BankCity', '')) or '').strip()
            bank_state = (row.get('bankstate', row.get('BankState', '')) or '').strip()
            approval_date = (row.get('approvaldate', row.get('ApprovalDate', '')) or '').strip()
            naics = (row.get('naicscode', row.get('NaicsCode', '')) or '').strip()

            yield {
                'program': program_label,
                'lender_name': bank_name,
                'lender_city': bank_city,
                'lender_state': bank_state,
                'borrower_state': borrower_state,
                'approval_date': approval_date,
                'gross_approval': gross,
                'sba_guaranteed': sba_guar,
                'fiscal_year': fy,
                'naics_code': naics,
            }
            count += 1

    log.info(f'  Parsed {count} loans from {program_label}')


def compute_rankings(conn):
    """Compute per-state and national lender rankings from raw loan data."""
    log.info('Computing lender rankings...')

    conn.execute('DELETE FROM sba_lender_state_year')
    conn.execute('DELETE FROM sba_lender_national_year')

    conn.execute('''
        INSERT INTO sba_lender_state_year
        (lender_name_normalized, state, fiscal_year, program, loan_count, total_approval, total_sba_guaranteed, rank_state)
        SELECT
            lender_name_normalized,
            borrower_state,
            fiscal_year,
            program,
            COUNT(*) as loan_count,
            SUM(gross_approval) as total_approval,
            SUM(sba_guaranteed) as total_sba_guaranteed,
            0
        FROM sba_loans
        WHERE borrower_state != '' AND lender_name_normalized != ''
        GROUP BY lender_name_normalized, borrower_state, fiscal_year, program
        HAVING loan_count >= 3
    ''')

    for fy_row in conn.execute('SELECT DISTINCT fiscal_year, program FROM sba_lender_state_year').fetchall():
        fy, prog = fy_row
        for state_row in conn.execute(
            'SELECT DISTINCT state FROM sba_lender_state_year WHERE fiscal_year=? AND program=?', (fy, prog)
        ).fetchall():
            st = state_row[0]
            ranked = conn.execute(
                'SELECT lender_name_normalized FROM sba_lender_state_year '
                'WHERE fiscal_year=? AND program=? AND state=? ORDER BY total_approval DESC',
                (fy, prog, st)
            ).fetchall()
            for rank, r in enumerate(ranked, 1):
                conn.execute(
                    'UPDATE sba_lender_state_year SET rank_state=? '
                    'WHERE lender_name_normalized=? AND state=? AND fiscal_year=? AND program=?',
                    (rank, r[0], st, fy, prog)
                )

    conn.execute('''
        INSERT INTO sba_lender_national_year
        (lender_name_normalized, fiscal_year, program, loan_count, total_approval, total_sba_guaranteed, rank_national)
        SELECT
            lender_name_normalized,
            fiscal_year,
            program,
            SUM(loan_count),
            SUM(total_approval),
            SUM(total_sba_guaranteed),
            0
        FROM sba_lender_state_year
        GROUP BY lender_name_normalized, fiscal_year, program
    ''')

    for fy_row in conn.execute('SELECT DISTINCT fiscal_year, program FROM sba_lender_national_year').fetchall():
        fy, prog = fy_row
        ranked = conn.execute(
            'SELECT lender_name_normalized FROM sba_lender_national_year '
            'WHERE fiscal_year=? AND program=? ORDER BY total_approval DESC',
            (fy, prog)
        ).fetchall()
        for rank, r in enumerate(ranked, 1):
            conn.execute(
                'UPDATE sba_lender_national_year SET rank_national=? '
                'WHERE lender_name_normalized=? AND fiscal_year=? AND program=?',
                (rank, r[0], fy, prog)
            )

    conn.commit()

    state_count = conn.execute('SELECT COUNT(*) FROM sba_lender_state_year').fetchone()[0]
    nat_count = conn.execute('SELECT COUNT(*) FROM sba_lender_national_year').fetchone()[0]
    log.info(f'Rankings computed: {state_count} state-level, {nat_count} national-level')


def ingest(min_fy=2020, dry_run=False):
    log.info(f'=== SBA Loans Ingest (min_fy={min_fy}) ===')
    conn = get_db()
    run_id = log_ingest_start(conn, 'sba')

    try:
        all_loans = []

        for name, url in SBA_URLS.items():
            csv_path = download_csv(name, url)
            program = '7a' if '7a' in name else '504'
            for loan in load_csv(csv_path, program, min_fy=min_fy):
                all_loans.append(loan)

        log.info(f'Total loans to ingest: {len(all_loans)}')

        if dry_run:
            log.info(f'[DRY RUN] Would insert {len(all_loans)} loans')
            for l in all_loans[:5]:
                log.info(f'  [DRY RUN] {l["lender_name"]} → {l["borrower_state"]} FY{l["fiscal_year"]} ${l["gross_approval"]:,.0f}')
            log_ingest_end(conn, run_id, len(all_loans), 0, status='dry_run')
            return

        conn.execute('DELETE FROM sba_loans')

        batch_size = 10000
        inserted = 0
        batch = []
        for loan in all_loans:
            norm = normalize_company_name(loan['lender_name'])
            batch.append((
                loan['program'], loan['lender_name'], norm,
                loan['lender_city'], loan['lender_state'],
                loan['borrower_state'], loan['approval_date'],
                loan['gross_approval'], loan['sba_guaranteed'],
                loan['fiscal_year'], loan['naics_code']
            ))
            if len(batch) >= batch_size:
                conn.executemany(
                    'INSERT INTO sba_loans (program, lender_name, lender_name_normalized, '
                    'lender_city, lender_state, borrower_state, approval_date, '
                    'gross_approval, sba_guaranteed, fiscal_year, naics_code) '
                    'VALUES (?,?,?,?,?,?,?,?,?,?,?)', batch
                )
                inserted += len(batch)
                conn.commit()
                log.info(f'  Inserted {inserted} loans...')
                batch = []

        if batch:
            conn.executemany(
                'INSERT INTO sba_loans (program, lender_name, lender_name_normalized, '
                'lender_city, lender_state, borrower_state, approval_date, '
                'gross_approval, sba_guaranteed, fiscal_year, naics_code) '
                'VALUES (?,?,?,?,?,?,?,?,?,?,?)', batch
            )
            inserted += len(batch)
            conn.commit()

        total = conn.execute('SELECT COUNT(*) FROM sba_loans').fetchone()[0]
        log.info(f'Loaded {total} loans')

        compute_rankings(conn)

        top10 = conn.execute(
            'SELECT lender_name_normalized, loan_count, total_approval, rank_national '
            'FROM sba_lender_national_year WHERE fiscal_year=2025 AND program="7a" '
            'ORDER BY rank_national LIMIT 10'
        ).fetchall()
        if top10:
            log.info('Top 10 SBA 7(a) lenders nationally (FY2025):')
            for r in top10:
                log.info(f'  #{r[3]}: {r[0]} — {r[1]} loans, ${r[2]:,.0f}')

        log_ingest_end(conn, run_id, len(all_loans), inserted)

    except Exception as e:
        log.error(f'Ingest failed: {e}', exc_info=True)
        log_ingest_end(conn, run_id, 0, 0, status='failed', error_message=str(e))
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Ingest SBA 7(a) + 504 loans')
    parser.add_argument('--min-fy', type=int, default=2020, help='Minimum fiscal year (default 2020)')
    parser.add_argument('--dry-run', action='store_true', help='Preview without inserting')
    args = parser.parse_args()
    ingest(min_fy=args.min_fy, dry_run=args.dry_run)
