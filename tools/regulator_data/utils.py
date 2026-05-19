import re
import sqlite3
import os
from datetime import datetime, timezone
from . import config


def get_db(readonly=False):
    mode = '?mode=ro' if readonly else ''
    uri = f'file:{config.DB_PATH}{mode}'
    conn = sqlite3.connect(uri, uri=True)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA foreign_keys=ON')
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    with open(schema_path) as f:
        schema_sql = f.read()
    conn = sqlite3.connect(config.DB_PATH)
    conn.executescript(schema_sql)
    conn.close()


_LEGAL_SUFFIXES = re.compile(
    r',?\s*\b(inc\.?|llc\.?|l\.l\.c\.?|corp\.?|corporation|co\.?|company|'
    r'ltd\.?|limited|n\.?a\.?|national\s+association|'
    r'bancorp|bancshares|holdings|the)\b\.?\s*$',
    re.IGNORECASE
)

_INSTITUTION_SUFFIXES = re.compile(
    r',?\s*\b(f\.?s\.?b\.?|federal\s+savings\s+bank|'
    r's\.?b\.?|savings\s+bank|'
    r'f\.?c\.?u\.?|federal\s+credit\s+union|'
    r'c\.?u\.?|credit\s+union|'
    r'bank|financial|services|group)\b\.?\s*$',
    re.IGNORECASE
)

_NON_ALNUM = re.compile(r'[^a-z0-9\s]')
_MULTI_SPACE = re.compile(r'\s+')


def normalize_company_name(name: str) -> str:
    if not name:
        return ''
    n = name.strip()
    for _ in range(3):
        n = _LEGAL_SUFFIXES.sub('', n).strip()
    for _ in range(2):
        candidate = _INSTITUTION_SUFFIXES.sub('', n).strip()
        if len(candidate.split()) >= 2:
            n = candidate
        else:
            break
    n = _NON_ALNUM.sub('', n.lower())
    n = _MULTI_SPACE.sub(' ', n).strip()
    return n


def log_ingest_start(conn, source: str) -> int:
    cur = conn.execute(
        'INSERT INTO ingest_runs (source, started_at, status) VALUES (?, ?, ?)',
        (source, datetime.now(timezone.utc).isoformat(), 'running')
    )
    conn.commit()
    return cur.lastrowid


def log_ingest_end(conn, run_id: int, records_fetched: int, records_inserted: int,
                   records_updated: int = 0, status: str = 'completed', error_message: str = None):
    conn.execute(
        'UPDATE ingest_runs SET completed_at=?, records_fetched=?, records_inserted=?, '
        'records_updated=?, status=?, error_message=? WHERE id=?',
        (datetime.now(timezone.utc).isoformat(), records_fetched, records_inserted,
         records_updated, status, error_message, run_id)
    )
    conn.commit()
