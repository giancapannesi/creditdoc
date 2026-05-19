#!/usr/bin/env python3
"""Sync regulator.db enrichment data → Supabase for SSR Worker access.

Reads from local regulator.db + regulator_entities, pushes to:
  - regulator_company_stats
  - regulator_enforcement
  - regulator_sba_rankings

Run after entity_resolver.py and after ingest crons complete.
Usage: python3 sync_to_supabase.py [--dry-run]
"""

import sys
import os
import json
import logging
import argparse
import requests
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from tools.regulator_data.utils import get_db
from tools.regulator_data.config import LOG_DIR

os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'regulator_sync.log')),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

ENV_FILE = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'tools', '.supabase-creditdoc.env')


def _load_supabase_env():
    env = {}
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                k, v = line.split('=', 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def _supabase_headers(env):
    key = env['SUPABASE_SERVICE_ROLE_KEY']
    return {
        'apikey': key,
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates',
    }


def _supabase_upsert(url, headers, table, rows, batch_size=500):
    """Upsert rows to Supabase table in batches."""
    endpoint = f'{url}/rest/v1/{table}'
    total = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        resp = requests.post(endpoint, headers=headers, json=batch, timeout=30)
        if resp.status_code not in (200, 201):
            log.error(f'  Upsert {table} batch {i//batch_size}: HTTP {resp.status_code} — {resp.text[:200]}')
            continue
        total += len(batch)
    return total


def _supabase_delete_all(url, headers, table):
    """Delete all rows from a table (for full refresh)."""
    endpoint = f'{url}/rest/v1/{table}?id=gt.0'
    resp = requests.delete(endpoint, headers=headers, timeout=30)
    if resp.status_code not in (200, 204):
        endpoint2 = f'{url}/rest/v1/{table}?creditdoc_slug=neq.'
        resp = requests.delete(endpoint2, headers=headers, timeout=30)
    return resp.status_code


def sync_company_stats(reg, url, headers, dry_run=False):
    """Push regulator_entities + cfpb_company_stats → regulator_company_stats."""
    log.info('Syncing company stats...')

    entities = reg.execute('''
        SELECT e.creditdoc_slug, e.canonical_name, e.normalized_name,
               e.match_confidence, e.fdic_cert
        FROM regulator_entities e
        WHERE e.creditdoc_slug IS NOT NULL
          AND e.match_confidence >= 0.85
    ''').fetchall()

    log.info(f'  {len(entities)} entities with confidence >= 0.85')

    rows = []
    for ent in entities:
        slug = ent['creditdoc_slug']
        norm = ent['normalized_name']

        stats = reg.execute(
            'SELECT * FROM cfpb_company_stats WHERE company_normalized = ?', (norm,)
        ).fetchone()
        if not stats:
            stats = reg.execute(
                'SELECT * FROM cfpb_company_stats WHERE REPLACE(company_normalized, " ", "") = REPLACE(?, " ", "")', (norm,)
            ).fetchone()

        branch_count = 0
        if ent['fdic_cert']:
            bc = reg.execute(
                'SELECT COUNT(*) FROM fdic_locations WHERE cert = ?', (ent['fdic_cert'],)
            ).fetchone()
            branch_count = bc[0] if bc else 0

        row = {
            'creditdoc_slug': slug,
            'company_name': ent['canonical_name'],
            'match_confidence': ent['match_confidence'],
            'total_complaints_alltime': stats['total_complaints_alltime'] if stats else 0,
            'total_complaints_12mo': stats['total_complaints_12mo'] if stats else 0,
            'total_complaints_3mo': stats['total_complaints_3mo'] if stats else 0,
            'timely_response_rate': stats['timely_response_rate'] if stats else None,
            'resolved_with_relief_rate': stats['resolved_with_relief_rate'] if stats else None,
            'top_issue_1': stats['top_issue_1'] if stats else None,
            'top_issue_1_pct': stats['top_issue_1_pct'] if stats else None,
            'top_issue_2': stats['top_issue_2'] if stats else None,
            'top_issue_2_pct': stats['top_issue_2_pct'] if stats else None,
            'top_issue_3': stats['top_issue_3'] if stats else None,
            'top_issue_3_pct': stats['top_issue_3_pct'] if stats else None,
            'complaint_trend': stats['complaint_trend'] if stats else None,
            'fdic_branch_count': branch_count,
            'updated_at': datetime.now(timezone.utc).isoformat(),
        }
        rows.append(row)

    log.info(f'  {len(rows)} rows ready for upsert')

    if dry_run:
        for r in rows[:5]:
            log.info(f'    [DRY] {r["creditdoc_slug"]}: {r["total_complaints_12mo"]} complaints 12mo, '
                     f'{r["fdic_branch_count"]} branches')
        return len(rows)

    count = _supabase_upsert(url, headers, 'regulator_company_stats', rows)
    log.info(f'  Upserted {count} company stats rows')
    return count


def sync_enforcement(reg, url, headers, dry_run=False):
    """Push enforcement actions for matched entities → regulator_enforcement."""
    log.info('Syncing enforcement actions...')

    actions = reg.execute('''
        SELECT e.creditdoc_slug, ea.title, ea.action_date, ea.penalty_amount,
               ea.description, ea.case_url
        FROM cfpb_enforcement_actions ea
        JOIN regulator_entities e
          ON ea.company_normalized = e.normalized_name
          OR REPLACE(ea.company_normalized, ' ', '') = REPLACE(e.normalized_name, ' ', '')
        WHERE e.creditdoc_slug IS NOT NULL
          AND e.match_confidence >= 0.85
        ORDER BY ea.action_date DESC
    ''').fetchall()

    log.info(f'  {len(actions)} enforcement actions matched to entities')

    rows = []
    for a in actions:
        rows.append({
            'creditdoc_slug': a['creditdoc_slug'],
            'action_date': a['action_date'],
            'penalty_amount': a['penalty_amount'],
            'title': a['title'],
            'description': a['description'],
            'case_url': a['case_url'],
            'updated_at': datetime.now(timezone.utc).isoformat(),
        })

    if dry_run:
        for r in rows[:5]:
            log.info(f'    [DRY] {r["creditdoc_slug"]}: {r["action_date"]} — ${r["penalty_amount"]}')
        return len(rows)

    # Full refresh — delete old, insert new
    _supabase_delete_all(url, headers, 'regulator_enforcement')
    count = _supabase_upsert(url, headers, 'regulator_enforcement', rows)
    log.info(f'  Inserted {count} enforcement rows')
    return count


def sync_sba_rankings(reg, url, headers, dry_run=False):
    """Push SBA rankings for matched entities → regulator_sba_rankings."""
    log.info('Syncing SBA rankings...')

    # State rankings
    state_ranks = reg.execute('''
        SELECT e.creditdoc_slug, sr.fiscal_year, sr.program, sr.state,
               sr.loan_count, sr.total_approval, sr.rank_state
        FROM sba_lender_state_year sr
        JOIN regulator_entities e
          ON sr.lender_name_normalized = e.normalized_name
        WHERE e.creditdoc_slug IS NOT NULL
          AND e.match_confidence >= 0.85
          AND sr.rank_state <= 25
    ''').fetchall()

    # National rankings
    nat_ranks = reg.execute('''
        SELECT e.creditdoc_slug, nr.fiscal_year, nr.program,
               nr.loan_count, nr.total_approval, nr.rank_national
        FROM sba_lender_national_year nr
        JOIN regulator_entities e
          ON nr.lender_name_normalized = e.normalized_name
        WHERE e.creditdoc_slug IS NOT NULL
          AND e.match_confidence >= 0.85
          AND nr.rank_national <= 50
    ''').fetchall()

    log.info(f'  {len(state_ranks)} state rankings, {len(nat_ranks)} national rankings')

    rows = []
    seen = set()
    for sr in state_ranks:
        key = (sr['creditdoc_slug'], sr['fiscal_year'], sr['program'], sr['state'])
        if key in seen:
            continue
        seen.add(key)
        rows.append({
            'creditdoc_slug': sr['creditdoc_slug'],
            'fiscal_year': sr['fiscal_year'],
            'program': sr['program'],
            'state': sr['state'],
            'loan_count': sr['loan_count'],
            'total_approval': sr['total_approval'],
            'rank_state': sr['rank_state'],
            'rank_national': None,
            'updated_at': datetime.now(timezone.utc).isoformat(),
        })

    for nr in nat_ranks:
        existing = [r for r in rows
                    if r['creditdoc_slug'] == nr['creditdoc_slug']
                    and r['fiscal_year'] == nr['fiscal_year']
                    and r['program'] == nr['program']
                    and r['state'] is None]
        if not existing:
            rows.append({
                'creditdoc_slug': nr['creditdoc_slug'],
                'fiscal_year': nr['fiscal_year'],
                'program': nr['program'],
                'state': None,
                'loan_count': nr['loan_count'],
                'total_approval': nr['total_approval'],
                'rank_state': None,
                'rank_national': nr['rank_national'],
                'updated_at': datetime.now(timezone.utc).isoformat(),
            })

    if dry_run:
        for r in rows[:5]:
            log.info(f'    [DRY] {r["creditdoc_slug"]}: FY{r["fiscal_year"]} {r["program"]} '
                     f'state={r["state"]} rank_s={r["rank_state"]} rank_n={r["rank_national"]}')
        return len(rows)

    _supabase_delete_all(url, headers, 'regulator_sba_rankings')
    count = _supabase_upsert(url, headers, 'regulator_sba_rankings', rows)
    log.info(f'  Inserted {count} SBA ranking rows')
    return count


def sync(dry_run=False):
    log.info('=== Regulator → Supabase Sync ===')

    sb_env = _load_supabase_env()
    url = sb_env['SUPABASE_URL'].rstrip('/')
    headers = _supabase_headers(sb_env)

    reg = get_db(readonly=True)

    entity_count = reg.execute('SELECT COUNT(*) FROM regulator_entities').fetchone()[0]
    stats_count = reg.execute('SELECT COUNT(*) FROM cfpb_company_stats').fetchone()[0]
    log.info(f'Local state: {entity_count} entities, {stats_count} company stats')

    if entity_count == 0:
        log.error('No entities resolved — run entity_resolver.py first')
        reg.close()
        return

    stats_pushed = sync_company_stats(reg, url, headers, dry_run)
    enf_pushed = sync_enforcement(reg, url, headers, dry_run)
    sba_pushed = sync_sba_rankings(reg, url, headers, dry_run)

    log.info(f'\n=== Sync Complete ===')
    log.info(f'Company stats: {stats_pushed}')
    log.info(f'Enforcement actions: {enf_pushed}')
    log.info(f'SBA rankings: {sba_pushed}')

    reg.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Sync regulator.db → Supabase')
    parser.add_argument('--dry-run', action='store_true', help='Preview without pushing')
    args = parser.parse_args()
    sync(dry_run=args.dry_run)
