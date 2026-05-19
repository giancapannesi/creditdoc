#!/usr/bin/env python3
"""Phase 3: Ingest FDIC Institutions + Locations from local CSV into regulator.db"""

import sys
import os
import csv
import logging
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from tools.regulator_data.utils import get_db, log_ingest_start, log_ingest_end
from tools.regulator_data.config import FDIC_INSTITUTIONS_CSV, FDIC_LOCATIONS_CSV, LOG_DIR

os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'regulator_fdic.log')),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)


def ingest_institutions(conn, csv_path, dry_run=False):
    """Load FDIC institutions from CSV."""
    log.info(f'Loading institutions from {csv_path}')

    with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            cert = row.get('CERT', '').strip()
            if not cert or not cert.isdigit():
                continue
            active = 1 if row.get('ACTIVE', '').strip() == '1' else 0
            rows.append((
                int(cert),
                row.get('REPDTE', row.get('NAME', row.get('INSTNAME', ''))).strip() if 'REPDTE' not in row else row.get('NAME', row.get('INSTNAME', '')).strip(),
                row.get('CITY', '').strip(),
                row.get('STALP', row.get('STATE', '')).strip(),
                active,
                row.get('WEBADDR', '').strip(),
                row.get('INSTCAT', row.get('CLASS', '')).strip(),
            ))

    log.info(f'Parsed {len(rows)} institutions')

    if dry_run:
        for r in rows[:5]:
            log.info(f'  [DRY RUN] CERT={r[0]} {r[1]} ({r[2]}, {r[3]}) active={r[4]}')
        return len(rows), 0

    conn.execute('DELETE FROM fdic_institutions')
    conn.executemany(
        'INSERT OR REPLACE INTO fdic_institutions '
        '(cert, institution_name, city, state, active, website, class) '
        'VALUES (?,?,?,?,?,?,?)', rows
    )
    conn.commit()
    total = conn.execute('SELECT COUNT(*) FROM fdic_institutions').fetchone()[0]
    log.info(f'Institutions loaded: {total}')
    return len(rows), total


def ingest_locations(conn, csv_path, dry_run=False):
    """Load FDIC branch locations from CSV."""
    log.info(f'Loading locations from {csv_path}')

    with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            cert = row.get('CERT', '').strip()
            if not cert or not cert.isdigit():
                continue

            main_office = 1 if row.get('MAINOFF', '').strip() in ('1', 'Yes', 'Y') else 0

            lat = row.get('LATITUDE', row.get('Y', '')).strip()
            lon = row.get('LONGITUDE', row.get('X', '')).strip()

            rows.append((
                int(cert),
                row.get('BRANCHNAME', row.get('OFFNAME', row.get('NAME', ''))).strip(),
                row.get('CITY', '').strip(),
                row.get('STALP', row.get('STATE', '')).strip(),
                row.get('COUNTY', row.get('STCNTY', '')).strip(),
                row.get('ADDRESS', row.get('ADDRESBR', '')).strip(),
                row.get('ZIP', row.get('ZIPBR', '')).strip(),
                float(lat) if lat else None,
                float(lon) if lon else None,
                main_office,
            ))

    log.info(f'Parsed {len(rows)} locations')

    if dry_run:
        for r in rows[:5]:
            log.info(f'  [DRY RUN] CERT={r[0]} {r[1]} ({r[2]}, {r[3]}) main={r[9]}')
        return len(rows), 0

    conn.execute('DELETE FROM fdic_locations')

    batch_size = 10000
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i+batch_size]
        conn.executemany(
            'INSERT INTO fdic_locations '
            '(cert, branch_name, city, state, county, address, zip, latitude, longitude, main_office) '
            'VALUES (?,?,?,?,?,?,?,?,?,?)', batch
        )
        log.info(f'  Batch {i//batch_size + 1}: inserted {len(batch)} locations')

    conn.commit()
    total = conn.execute('SELECT COUNT(*) FROM fdic_locations').fetchone()[0]
    log.info(f'Locations loaded: {total}')
    return len(rows), total


def ingest(dry_run=False):
    log.info('=== FDIC Institutions + Locations Ingest ===')

    if not os.path.exists(FDIC_INSTITUTIONS_CSV):
        log.error(f'Institutions CSV not found: {FDIC_INSTITUTIONS_CSV}')
        return
    if not os.path.exists(FDIC_LOCATIONS_CSV):
        log.error(f'Locations CSV not found: {FDIC_LOCATIONS_CSV}')
        return

    conn = get_db()
    run_id = log_ingest_start(conn, 'fdic')

    try:
        inst_parsed, inst_loaded = ingest_institutions(conn, FDIC_INSTITUTIONS_CSV, dry_run)
        loc_parsed, loc_loaded = ingest_locations(conn, FDIC_LOCATIONS_CSV, dry_run)

        total_fetched = inst_parsed + loc_parsed
        total_inserted = inst_loaded + loc_loaded

        if not dry_run:
            states = conn.execute(
                'SELECT state, COUNT(*) FROM fdic_locations GROUP BY state ORDER BY 2 DESC LIMIT 5'
            ).fetchall()
            log.info('Top 5 states by branch count:')
            for s in states:
                log.info(f'  {s[0]}: {s[1]}')

        status = 'dry_run' if dry_run else 'completed'
        log_ingest_end(conn, run_id, total_fetched, total_inserted, status=status)
        log.info(f'Done. Institutions: {inst_loaded}, Locations: {loc_loaded}')

    except Exception as e:
        log.error(f'Ingest failed: {e}', exc_info=True)
        log_ingest_end(conn, run_id, 0, 0, status='failed', error_message=str(e))
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Ingest FDIC data from local CSV')
    parser.add_argument('--dry-run', action='store_true', help='Preview without inserting')
    args = parser.parse_args()
    ingest(dry_run=args.dry_run)
