#!/usr/bin/env python3
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from tools.creditdoc_pinterest_ui.app import post_queue_row

ROOT = Path("/srv/BusinessOps/creditdoc")
DB_PATH = ROOT / "data" / "creditdoc.db"


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> int:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT id
            FROM pinterest_pin_queue
            WHERE status='scheduled'
              AND scheduled_for IS NOT NULL
              AND scheduled_for <= ?
            ORDER BY scheduled_for ASC
            LIMIT 10
            """,
            (now_utc(),),
        ).fetchall()
    finally:
        conn.close()
    for row in rows:
        try:
            post_queue_row(int(row["id"]))
            print(f"posted {row['id']}")
        except Exception as exc:
            print(f"failed {row['id']}: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
