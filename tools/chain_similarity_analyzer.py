#!/usr/bin/env python3
import argparse
import csv
import random
import re
import sqlite3
import sys
from datetime import date
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "creditdoc.db"
REPORTS_DIR = Path(__file__).parent.parent / "reports"

US_STATES = {
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
    "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho",
    "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana",
    "maine", "maryland", "massachusetts", "michigan", "minnesota",
    "mississippi", "missouri", "montana", "nebraska", "nevada",
    "new hampshire", "new jersey", "new mexico", "new york",
    "north carolina", "north dakota", "ohio", "oklahoma", "oregon",
    "pennsylvania", "rhode island", "south carolina", "south dakota",
    "tennessee", "texas", "utah", "vermont", "virginia", "washington",
    "west virginia", "wisconsin", "wyoming",
}

STATE_ABBREVS = {
    "al", "ak", "az", "ar", "ca", "co", "ct", "de", "fl", "ga",
    "hi", "id", "il", "in", "ia", "ks", "ky", "la", "me", "md",
    "ma", "mi", "mn", "ms", "mo", "mt", "ne", "nv", "nh", "nj",
    "nm", "ny", "nc", "nd", "oh", "ok", "or", "pa", "ri", "sc",
    "sd", "tn", "tx", "ut", "vt", "va", "wa", "wv", "wi", "wy",
}

PHONE_RE = re.compile(r'\b\d[\d\s\-().+]{6,}\d\b')
ADDR_LEAD_RE = re.compile(r'^(\d|at |located at |the )', re.IGNORECASE)
CITY_IN_FIRST_RE = re.compile(r'^(\d|at |located at )', re.IGNORECASE)


def _jaro_winkler(s1, s2):
    if not s1 or not s2:
        return 0.0
    s1, s2 = s1.lower(), s2.lower()
    if s1 == s2:
        return 1.0
    len1, len2 = len(s1), len(s2)
    match_distance = max(len1, len2) // 2 - 1
    if match_distance < 0:
        match_distance = 0
    s1_matches = [False] * len1
    s2_matches = [False] * len2
    matches = 0
    for i in range(len1):
        start = max(0, i - match_distance)
        end = min(i + match_distance + 1, len2)
        for j in range(start, end):
            if s2_matches[j] or s1[i] != s2[j]:
                continue
            s1_matches[i] = True
            s2_matches[j] = True
            matches += 1
            break
    if matches == 0:
        return 0.0
    k = 0
    transpositions = 0
    for i in range(len1):
        if not s1_matches[i]:
            continue
        while not s2_matches[k]:
            k += 1
        if s1[i] != s2[k]:
            transpositions += 1
        k += 1
    transpositions //= 2
    jaro = (matches / len1 + matches / len2 + (matches - transpositions) / matches) / 3
    prefix = 0
    for i in range(min(4, len1, len2)):
        if s1[i] == s2[i]:
            prefix += 1
        else:
            break
    return jaro + prefix * 0.1 * (1 - jaro)


def normalize_name(name):
    return re.sub(r'\s+', ' ', (name or '').lower().strip())


def tokenize_for_removal(chain_name, city, state):
    tokens = []
    tokens.append(re.escape(chain_name.lower()))
    if city:
        tokens.append(re.escape(city.lower()))
    for s in US_STATES:
        tokens.append(re.escape(s))
    for s in STATE_ABBREVS:
        tokens.append(r'\b' + re.escape(s) + r'\b')
    if state:
        tokens.append(re.escape(state.lower()))
    return tokens


def anonymize(text, chain_name, cities):
    if not text:
        return ''
    t = text[:120].lower()
    t = PHONE_RE.sub('<PHONE>', t)
    t = re.sub(re.escape(chain_name.lower()), '<NAME>', t)
    for city in cities:
        if city:
            t = re.sub(re.escape(city.lower()), '<CITY>', t, flags=re.IGNORECASE)
    for state in US_STATES:
        t = re.sub(r'\b' + re.escape(state) + r'\b', '<STATE>', t, flags=re.IGNORECASE)
    for abbr in STATE_ABBREVS:
        t = re.sub(r'\b' + re.escape(abbr) + r'\b', '<STATE>', t)
    return t


def similarity_sample(texts, max_pairs):
    n = len(texts)
    if n < 2:
        return 0.0
    all_pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    if len(all_pairs) > max_pairs:
        all_pairs = random.sample(all_pairs, max_pairs)
    scores = [_jaro_winkler(texts[i], texts[j]) for i, j in all_pairs]
    return sum(scores) / len(scores) if scores else 0.0


def load_chains(db_path, min_size):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """SELECT slug,
                  json_extract(data, '$.name') AS name,
                  json_extract(data, '$.description_short') AS desc_short,
                  json_extract(data, '$.city') AS city,
                  json_extract(data, '$.state') AS state,
                  json_extract(data, '$.phone') AS phone,
                  json_extract(data, '$.address') AS address,
                  json_extract(data, '$.google_rating') AS google_rating
           FROM lenders
           WHERE processing_status = 'ready_for_index'
             AND json_extract(data, '$.name') IS NOT NULL
        """
    ).fetchall()
    conn.close()

    chains = {}
    for r in rows:
        norm = normalize_name(r['name'])
        chains.setdefault(norm, []).append(dict(r))

    return {k: v for k, v in chains.items() if len(v) >= min_size}


def analyze_chain(norm_name, members, max_pairs):
    display_name = members[0]['name'] or norm_name
    location_count = len(members)
    cities = {(m.get('city') or '').strip() for m in members}

    anon_texts = [
        anonymize(m.get('desc_short', '') or '', norm_name, cities)
        for m in members
    ]
    desc_sim = round(similarity_sample(anon_texts, max_pairs), 4)

    phones = [m.get('phone') or '' for m in members]
    unique_phone_pct = round(len(set(p for p in phones if p)) / location_count * 100, 1)

    addresses = [m.get('address') or '' for m in members]
    unique_address_pct = round(len(set(a for a in addresses if a)) / location_count * 100, 1)

    rated = sum(1 for m in members if m.get('google_rating') not in (None, '', '0', 0))
    rating_present_pct = round(rated / location_count * 100, 1)

    brand_lead = 0
    city_lead = 0
    for m in members:
        first50 = (m.get('desc_short') or '')[:50].lower()
        is_addr = bool(ADDR_LEAD_RE.match(first50))
        has_brand = norm_name in first50
        if has_brand and not is_addr:
            brand_lead += 1
        if is_addr:
            city_lead += 1
        else:
            city = (m.get('city') or '').lower()
            if city and city in first50:
                city_lead += 1

    brand_lead_pct = round(brand_lead / location_count * 100, 1)
    city_lead_pct = round(city_lead / location_count * 100, 1)

    if desc_sim > 0.85 and brand_lead_pct > 80:
        thin_risk = 'HIGH'
    elif desc_sim > 0.70 and brand_lead_pct > 50:
        thin_risk = 'MEDIUM'
    else:
        thin_risk = 'LOW'

    if desc_sim > 0.95 and unique_phone_pct < 30 and unique_address_pct < 50:
        action = 'CONSOLIDATE'
    elif thin_risk == 'LOW':
        if location_count < 20:
            action = 'KEEP_AS_IS'
        else:
            action = 'HERO_ONLY'
    elif thin_risk in ('HIGH', 'MEDIUM') and unique_phone_pct > 50:
        action = 'DIFFERENTIATE_LEADS'
    elif thin_risk == 'LOW':
        action = 'HERO_ONLY'
    else:
        action = 'DIFFERENTIATE_LEADS'

    slugs = [m['slug'] for m in members if m.get('slug')][:3]
    while len(slugs) < 3:
        slugs.append('')

    return {
        'chain_name': display_name,
        'location_count': location_count,
        'desc_similarity_avg': desc_sim,
        'unique_phone_pct': unique_phone_pct,
        'unique_address_pct': unique_address_pct,
        'rating_present_pct': rating_present_pct,
        'brand_lead_pct': brand_lead_pct,
        'city_lead_pct': city_lead_pct,
        'thin_risk': thin_risk,
        'suggested_action': action,
        'sample_slug_1': slugs[0],
        'sample_slug_2': slugs[1],
        'sample_slug_3': slugs[2],
        'FINAL_ACTION': '',
    }


def detail_mode(chain_key, chains, max_pairs):
    matches = [(k, v) for k, v in chains.items() if chain_key in k]
    if not matches:
        print(f"Chain not found: {chain_key}")
        sys.exit(1)
    norm_name, members = matches[0]
    r = analyze_chain(norm_name, members, max_pairs)
    print(f"\n=== Chain Detail: {r['chain_name']} ===")
    print(f"  Locations      : {r['location_count']}")
    print(f"  Desc Similarity: {r['desc_similarity_avg']}")
    print(f"  Unique Phone%  : {r['unique_phone_pct']}")
    print(f"  Unique Addr%   : {r['unique_address_pct']}")
    print(f"  Rating Present : {r['rating_present_pct']}")
    print(f"  Brand Lead%    : {r['brand_lead_pct']}")
    print(f"  City Lead%     : {r['city_lead_pct']}")
    print(f"  Thin Risk      : {r['thin_risk']}")
    print(f"  Suggested Act  : {r['suggested_action']}")
    print(f"  Slugs          : {r['sample_slug_1']} | {r['sample_slug_2']} | {r['sample_slug_3']}")
    print()
    print("  Sample descriptions (raw):")
    for m in members[:5]:
        desc = (m.get('desc_short') or '')[:120]
        print(f"    [{m['slug']}] {desc}")


def main():
    ap = argparse.ArgumentParser(description='Score chain locations for thin-content risk.')
    ap.add_argument('--min', type=int, default=10, help='Min chain size (default 10)')
    ap.add_argument('--chain', type=str, default='', help='Detail mode for one chain')
    ap.add_argument('--output', type=str, default='', help='Custom CSV output path')
    ap.add_argument('--sample-pairs', type=int, default=50, help='Max pairs per chain (default 50)')
    args = ap.parse_args()

    random.seed(42)
    chains = load_chains(str(DB_PATH), args.min)

    if args.chain:
        random.seed(42)
        detail_mode(normalize_name(args.chain), chains, args.sample_pairs)
        return

    results = []
    for norm_name, members in chains.items():
        row = analyze_chain(norm_name, members, args.sample_pairs)
        results.append(row)

    results.sort(key=lambda x: x['location_count'], reverse=True)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = args.output or str(REPORTS_DIR / f"chain_analysis_{date.today()}.csv")

    fieldnames = [
        'chain_name', 'location_count', 'desc_similarity_avg',
        'unique_phone_pct', 'unique_address_pct', 'rating_present_pct',
        'brand_lead_pct', 'city_lead_pct', 'thin_risk', 'suggested_action',
        'sample_slug_1', 'sample_slug_2', 'sample_slug_3', 'FINAL_ACTION',
    ]
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(results)

    high = sum(1 for r in results if r['thin_risk'] == 'HIGH')
    med = sum(1 for r in results if r['thin_risk'] == 'MEDIUM')
    low = sum(1 for r in results if r['thin_risk'] == 'LOW')
    print(f"Chains analyzed : {len(results)}")
    print(f"HIGH            : {high}")
    print(f"MEDIUM          : {med}")
    print(f"LOW             : {low}")
    print(f"CSV             : {out_path}")


if __name__ == '__main__':
    main()
