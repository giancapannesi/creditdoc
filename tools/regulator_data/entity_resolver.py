#!/usr/bin/env python3
"""Entity resolver: link creditdoc lenders → regulator.db federal records.

Three tiers:
  1. FDIC cert / NCUA charter (hard key, 100% accurate)
  2. Exact normalized name match
  3. Token-weighted fuzzy (min 3 tokens, no single-word matches)

Run: python3 entity_resolver.py [--dry-run]
"""

import sys
import os
import json
import sqlite3
import logging
import argparse
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from tools.regulator_data.utils import normalize_company_name, get_db
from tools.regulator_data.config import LOG_DIR

os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'entity_resolver.log')),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

CREDITDOC_DB = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'creditdoc.db')

STRIP_WORDS = {'bank', 'credit', 'union', 'national', 'association', 'federal',
               'savings', 'company', 'corporation', 'financial', 'group',
               'services', 'holdings', 'the', 'of', 'and', 'inc', 'llc',
               'corp', 'ltd', 'na', 'fsb', 'ssb', 'fa'}


def _tokenize(name):
    """Split name into meaningful tokens, removing noise words."""
    tokens = name.lower().replace(',', '').replace('.', '').split()
    return [t for t in tokens if t not in STRIP_WORDS and len(t) > 1]


def _token_similarity(name_a, name_b):
    """Token overlap ratio — 1.0 = perfect match, 0.0 = no overlap."""
    tokens_a = set(_tokenize(name_a))
    tokens_b = set(_tokenize(name_b))
    if not tokens_a or not tokens_b:
        return 0.0
    overlap = tokens_a & tokens_b
    return len(overlap) / max(len(tokens_a), len(tokens_b))


def resolve_entities(dry_run=False):
    log.info('=== Entity Resolution ===')
    reg = get_db()
    cd = sqlite3.connect(CREDITDOC_DB)

    # Load all creditdoc lenders
    lenders = cd.execute(
        'SELECT slug, data, category, state FROM lenders WHERE processing_status = "ready_for_index"'
    ).fetchall()
    log.info(f'Loaded {len(lenders)} creditdoc lenders')

    # Build FDIC cert → institution lookup
    fdic_certs = {}
    for row in reg.execute('SELECT cert, institution_name FROM fdic_institutions').fetchall():
        fdic_certs[row[0]] = row[1]

    # Build CFPB company lookup (companies with >= 5 complaints)
    cfpb_companies = {}
    for row in reg.execute(
        'SELECT company_normalized, COUNT(*) FROM cfpb_complaints '
        'WHERE company_normalized != "" GROUP BY company_normalized HAVING COUNT(*) >= 5'
    ).fetchall():
        cfpb_companies[row[0]] = row[1]

    # Build CFPB enforcement lookup
    enforcement_companies = set(
        r[0] for r in reg.execute(
            'SELECT DISTINCT company_normalized FROM cfpb_enforcement_actions WHERE company_normalized != ""'
        ).fetchall()
    )

    # Build SBA lender lookup
    sba_lenders = set(
        r[0] for r in reg.execute(
            'SELECT DISTINCT lender_name_normalized FROM sba_loans WHERE lender_name_normalized != ""'
        ).fetchall()
    )

    log.info(f'Federal data: {len(fdic_certs)} FDIC certs, {len(cfpb_companies)} CFPB companies, '
             f'{len(enforcement_companies)} enforcement targets, {len(sba_lenders)} SBA lenders')

    # Pre-build indexes for fast matching
    cfpb_token_index = {}
    for cfpb_name in cfpb_companies:
        for tok in _tokenize(cfpb_name):
            cfpb_token_index.setdefault(tok, []).append(cfpb_name)

    fdic_name_index = {}
    for cert_id, inst_name in fdic_certs.items():
        norm = normalize_company_name(inst_name)
        if norm and len(norm) > 3:
            fdic_name_index[norm] = (cert_id, inst_name)

    log.info(f'Built indexes: {len(cfpb_token_index)} CFPB tokens, {len(fdic_name_index)} FDIC names')

    if not dry_run:
        reg.execute('DELETE FROM regulator_entities')
        reg.execute('DELETE FROM entity_aliases')
        reg.commit()

    stats = Counter()
    entities = []

    for slug, data_str, category, state in lenders:
        d = json.loads(data_str) if data_str else {}
        lender_name = d.get('name', '')
        norm_name = normalize_company_name(lender_name)
        if not norm_name:
            stats['skip_no_name'] += 1
            continue

        match_method = None
        match_confidence = 0.0
        canonical_name = lender_name
        fdic_cert = None
        ncua_cu = None

        # TIER 1: FDIC cert number (100% accurate)
        cert = d.get('fdic_cert')
        if cert:
            cert_int = int(cert) if isinstance(cert, (int, float, str)) and str(cert).isdigit() else None
            if cert_int and cert_int in fdic_certs:
                canonical_name = fdic_certs[cert_int]
                fdic_cert = cert_int
                match_method = 'fdic_cert'
                match_confidence = 1.0
                stats['tier1_fdic'] += 1

        # TIER 1b: NCUA charter
        if not match_method:
            charter = d.get('ncua_charter')
            if charter:
                ncua_cu = int(charter) if str(charter).isdigit() else None
                if ncua_cu:
                    match_method = 'ncua_charter'
                    match_confidence = 0.95
                    stats['tier1_ncua'] += 1

        # TIER 2: Exact normalized name match against CFPB
        if not match_method and norm_name in cfpb_companies:
            match_method = 'exact_name_cfpb'
            match_confidence = 0.90
            stats['tier2_exact'] += 1

        # TIER 2b: Exact match against FDIC institution names (pre-built index)
        if not match_method and len(norm_name) > 3:
            fdic_match = fdic_name_index.get(norm_name)
            if fdic_match:
                match_method = 'exact_name_fdic'
                match_confidence = 0.90
                fdic_cert = fdic_match[0]
                canonical_name = fdic_match[1]
                stats['tier2_fdic_name'] += 1

        # TIER 3: Token-indexed fuzzy against CFPB (min 2 meaningful tokens)
        if not match_method:
            name_tokens = set(_tokenize(norm_name))
            if len(name_tokens) >= 2:
                candidates = set()
                for tok in name_tokens:
                    candidates.update(cfpb_token_index.get(tok, []))
                best_score = 0.0
                best_match = None
                for cfpb_name in candidates:
                    score = _token_similarity(norm_name, cfpb_name)
                    if score > best_score and score >= 0.7:
                        best_score = score
                        best_match = cfpb_name
                if best_match:
                    match_method = 'fuzzy_cfpb'
                    match_confidence = round(best_score * 0.85, 2)
                    canonical_name = best_match
                    stats['tier3_fuzzy'] += 1

        if not match_method:
            stats['unmatched'] += 1
            continue

        # Check which federal datasets this entity appears in
        norm_canonical = normalize_company_name(canonical_name)
        has_cfpb = norm_canonical in cfpb_companies or norm_name in cfpb_companies
        has_enforcement = norm_canonical in enforcement_companies or norm_name in enforcement_companies
        has_sba = norm_canonical in sba_lenders or norm_name in sba_lenders
        has_fdic = fdic_cert is not None

        entities.append({
            'canonical_name': canonical_name,
            'normalized_name': norm_name,
            'slug': slug,
            'fdic_cert': fdic_cert,
            'ncua_cu': ncua_cu,
            'confidence': match_confidence,
            'method': match_method,
            'has_cfpb': has_cfpb,
            'has_enforcement': has_enforcement,
            'has_sba': has_sba,
            'has_fdic': has_fdic,
        })

    log.info(f'\n=== RESOLUTION RESULTS ===')
    log.info(f'Total lenders: {len(lenders)}')
    for k, v in sorted(stats.items(), key=lambda x: -x[1]):
        log.info(f'  {k}: {v}')
    log.info(f'Total matched: {len(entities)} ({len(entities)/len(lenders)*100:.1f}%)')

    # Count data coverage
    with_cfpb = sum(1 for e in entities if e['has_cfpb'])
    with_enf = sum(1 for e in entities if e['has_enforcement'])
    with_sba = sum(1 for e in entities if e['has_sba'])
    with_fdic = sum(1 for e in entities if e['has_fdic'])
    log.info(f'\nData coverage among matched:')
    log.info(f'  CFPB complaints: {with_cfpb}')
    log.info(f'  Enforcement actions: {with_enf}')
    log.info(f'  SBA loans: {with_sba}')
    log.info(f'  FDIC branches: {with_fdic}')

    if dry_run:
        log.info('\n[DRY RUN] Would insert {} entities'.format(len(entities)))
        # Show 10 examples from each tier
        for tier in ['tier1_fdic', 'tier1_ncua', 'tier2_exact', 'tier3_fuzzy']:
            examples = [e for e in entities if tier.split('_', 1)[1] in (e['method'] or '')][:5]
            if examples:
                log.info(f'\n  Examples ({tier}):')
                for e in examples:
                    log.info(f'    {e["slug"][:40]:40s} → {e["canonical_name"][:40]:40s} [{e["method"]}] conf={e["confidence"]}')
        return entities

    # Insert
    for e in entities:
        reg.execute(
            'INSERT INTO regulator_entities '
            '(canonical_name, normalized_name, creditdoc_slug, fdic_cert, ncua_cu_number, match_confidence) '
            'VALUES (?, ?, ?, ?, ?, ?)',
            (e['canonical_name'], e['normalized_name'], e['slug'],
             e['fdic_cert'], e['ncua_cu'], e['confidence'])
        )
    reg.commit()
    final = reg.execute('SELECT COUNT(*) FROM regulator_entities').fetchone()[0]
    log.info(f'\nInserted {final} entities into regulator_entities')

    cd.close()
    reg.close()
    return entities


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Resolve creditdoc lenders → federal entities')
    parser.add_argument('--dry-run', action='store_true', help='Preview without inserting')
    args = parser.parse_args()
    resolve_entities(dry_run=args.dry_run)
