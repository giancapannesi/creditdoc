#!/usr/bin/env python3
"""Export CFPB data from SQLite to JSON for Astro build-time static paths.

Reads: /srv/BusinessOps/data/creditdoc_cfpb.db
Writes: /srv/BusinessOps/creditdoc/src/content/cfpb-trends.json

Run before `npm run build` or add to prebuild script.
"""
import json
import sqlite3
import os
import tempfile

DB_PATH = '/srv/BusinessOps/data/creditdoc_cfpb.db'
OUT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src', 'content', 'cfpb-trends.json')


def export():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    rows = cur.execute(
        'SELECT slug, company_name, cfpb_company_name, checked_at, found_in_cfpb, '
        'resolution_rate, timely_rate, top_products, top_issues, response_breakdown, '
        'data_period, applied_to_profile '
        'FROM cfpb_data WHERE found_in_cfpb=1'
    ).fetchall()

    data = []
    for row in rows:
        entry = dict(row)
        # Parse JSON fields
        for field in ('top_products', 'top_issues', 'response_breakdown'):
            if entry.get(field):
                try:
                    entry[field] = json.loads(entry[field])
                except (json.JSONDecodeError, TypeError):
                    entry[field] = None
        data.append(entry)

    conn.close()

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    payload = json.dumps(data, indent=None, separators=(',', ':'))
    if os.path.exists(OUT_PATH):
        with open(OUT_PATH) as f:
            if f.read() == payload:
                print(f"CFPB export unchanged: {OUT_PATH}")
                return

    fd, tmp_path = tempfile.mkstemp(prefix='.cfpb-trends.', suffix='.json', dir=os.path.dirname(OUT_PATH))
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(payload)
        os.replace(tmp_path, OUT_PATH)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    print(f"Exported {len(data)} CFPB profiles to {OUT_PATH}")


if __name__ == '__main__':
    export()
