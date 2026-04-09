#!/usr/bin/env python3
"""
CreditDoc Database Backup — Rotating SQLite backups.

Uses SQLite's native .backup API (atomic, non-blocking, works while DB is in use).
Compresses with gzip and rotates according to retention policy.

Retention:
  - Daily:    keep 7 most recent
  - Weekly:   keep 4 most recent (from Sunday backups)
  - Monthly:  keep 12 most recent (from 1st-of-month backups)

Usage:
    python3 tools/creditdoc_db_backup.py                 # Run backup (auto-rotate)
    python3 tools/creditdoc_db_backup.py --list          # List existing backups
    python3 tools/creditdoc_db_backup.py --verify <file> # Verify a backup is valid
    python3 tools/creditdoc_db_backup.py --stats         # Show backup stats

Cron: Runs at 06:50 UTC daily (10 min before the sync cron at 07:00 UTC / 2 AM EST)
      so we have a snapshot of pre-sync state.
"""

import argparse
import gzip
import os
import shutil
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
DB_PATH = PROJECT_DIR / "data" / "creditdoc.db"
BACKUP_DIR = Path("/srv/BusinessOps/backups/creditdoc_db")
LOG_PATH = Path("/srv/BusinessOps/logs/creditdoc_db_backup.log")

# Retention policy
KEEP_DAILY = 7
KEEP_WEEKLY = 4
KEEP_MONTHLY = 12


def log(msg, to_file=True):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{ts}] {msg}"
    print(line)
    if to_file:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "a") as f:
            f.write(line + "\n")


def backup_database(db_path=DB_PATH, backup_dir=BACKUP_DIR):
    """Create a compressed backup using SQLite .backup API (atomic)."""
    backup_dir.mkdir(parents=True, exist_ok=True)

    if not db_path.exists():
        log(f"ERROR: Database not found at {db_path}")
        return None

    # Determine backup type (daily/weekly/monthly)
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    is_sunday = now.weekday() == 6
    is_first = now.day == 1

    # Build filename
    if is_first:
        prefix = "monthly"
    elif is_sunday:
        prefix = "weekly"
    else:
        prefix = "daily"

    backup_name = f"creditdoc_{prefix}_{date_str}.db"
    backup_path = backup_dir / backup_name
    gz_path = backup_dir / f"{backup_name}.gz"

    log(f"Starting backup: {gz_path.name}")
    start = time.time()

    # Step 1: Live SQLite backup (atomic, doesn't block other connections)
    try:
        source = sqlite3.connect(str(db_path))
        dest = sqlite3.connect(str(backup_path))
        source.backup(dest)
        dest.close()
        source.close()
        src_size = os.path.getsize(db_path) / (1024 * 1024)
        log(f"  SQLite backup complete: {src_size:.1f} MB")
    except Exception as e:
        log(f"  ERROR during SQLite backup: {e}")
        if backup_path.exists():
            backup_path.unlink()
        return None

    # Step 2: Compress with gzip
    try:
        with open(backup_path, "rb") as f_in:
            with gzip.open(gz_path, "wb", compresslevel=6) as f_out:
                shutil.copyfileobj(f_in, f_out)
        backup_path.unlink()  # Remove uncompressed version
        gz_size = os.path.getsize(gz_path) / (1024 * 1024)
        ratio = (1 - gz_size / src_size) * 100 if src_size > 0 else 0
        log(f"  Compressed: {gz_size:.1f} MB ({ratio:.0f}% reduction)")
    except Exception as e:
        log(f"  ERROR during compression: {e}")
        if backup_path.exists():
            backup_path.unlink()
        if gz_path.exists():
            gz_path.unlink()
        return None

    # Step 3: Verify the compressed backup is readable and valid
    if not verify_backup(gz_path):
        log(f"  ERROR: Backup verification failed, removing {gz_path}")
        gz_path.unlink()
        return None

    elapsed = time.time() - start
    log(f"  Backup complete: {gz_path} ({elapsed:.1f}s)")

    # Step 4: Rotate old backups
    rotate_backups(backup_dir)

    return gz_path


def verify_backup(gz_path):
    """Verify a gzipped SQLite backup by decompressing to temp and running integrity_check."""
    try:
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            tmp_path = tmp.name

        with gzip.open(gz_path, "rb") as f_in:
            with open(tmp_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

        conn = sqlite3.connect(tmp_path)
        result = conn.execute("PRAGMA integrity_check").fetchone()
        lender_count = conn.execute("SELECT COUNT(*) FROM lenders").fetchone()[0]
        audit_count = conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
        conn.close()

        os.unlink(tmp_path)

        if result[0] != "ok":
            log(f"  Integrity check FAILED: {result[0]}")
            return False

        log(f"  Verified: integrity=ok, lenders={lender_count}, audit={audit_count}")
        return True
    except Exception as e:
        log(f"  Verification error: {e}")
        return False


def rotate_backups(backup_dir=BACKUP_DIR):
    """Apply retention policy — keep N daily/weekly/monthly."""
    if not backup_dir.exists():
        return

    # Group backups by type
    daily = sorted(backup_dir.glob("creditdoc_daily_*.db.gz"), reverse=True)
    weekly = sorted(backup_dir.glob("creditdoc_weekly_*.db.gz"), reverse=True)
    monthly = sorted(backup_dir.glob("creditdoc_monthly_*.db.gz"), reverse=True)

    removed = 0

    # Delete oldest daily beyond KEEP_DAILY
    for old in daily[KEEP_DAILY:]:
        log(f"  Rotating (daily): {old.name}")
        old.unlink()
        removed += 1

    # Delete oldest weekly beyond KEEP_WEEKLY
    for old in weekly[KEEP_WEEKLY:]:
        log(f"  Rotating (weekly): {old.name}")
        old.unlink()
        removed += 1

    # Delete oldest monthly beyond KEEP_MONTHLY
    for old in monthly[KEEP_MONTHLY:]:
        log(f"  Rotating (monthly): {old.name}")
        old.unlink()
        removed += 1

    if removed > 0:
        log(f"  Removed {removed} old backup(s)")


def list_backups(backup_dir=BACKUP_DIR):
    """List all existing backups with size + date."""
    if not backup_dir.exists():
        print(f"Backup directory does not exist: {backup_dir}")
        return

    all_backups = sorted(backup_dir.glob("creditdoc_*.db.gz"), reverse=True)

    if not all_backups:
        print(f"No backups found in {backup_dir}")
        return

    print(f"\n{'='*65}")
    print(f"CreditDoc DB Backups ({len(all_backups)} total)")
    print(f"{'='*65}")

    total_size = 0
    for backup in all_backups:
        size_mb = os.path.getsize(backup) / (1024 * 1024)
        total_size += size_mb
        mtime = datetime.fromtimestamp(backup.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        backup_type = backup.name.split("_")[1]
        marker = {"daily": "D", "weekly": "W", "monthly": "M"}.get(backup_type, "?")
        print(f"  [{marker}] {backup.name}  {size_mb:6.1f} MB  {mtime}")

    print(f"{'='*65}")
    print(f"Total size: {total_size:.1f} MB")
    print(f"{'='*65}")


def stats(backup_dir=BACKUP_DIR):
    """Show backup statistics."""
    if not backup_dir.exists():
        print(f"No backup directory yet: {backup_dir}")
        return

    daily = sorted(backup_dir.glob("creditdoc_daily_*.db.gz"), reverse=True)
    weekly = sorted(backup_dir.glob("creditdoc_weekly_*.db.gz"), reverse=True)
    monthly = sorted(backup_dir.glob("creditdoc_monthly_*.db.gz"), reverse=True)

    total_size = sum(os.path.getsize(f) for f in daily + weekly + monthly) / (1024 * 1024)

    print(f"\n=== Backup Stats ===")
    print(f"Location: {backup_dir}")
    print(f"Daily:    {len(daily)}/{KEEP_DAILY}")
    print(f"Weekly:   {len(weekly)}/{KEEP_WEEKLY}")
    print(f"Monthly:  {len(monthly)}/{KEEP_MONTHLY}")
    print(f"Total:    {len(daily)+len(weekly)+len(monthly)} backups, {total_size:.1f} MB")

    if daily:
        latest = daily[0]
        age_hours = (time.time() - latest.stat().st_mtime) / 3600
        print(f"\nLatest daily: {latest.name} ({age_hours:.1f}h ago)")


def main():
    parser = argparse.ArgumentParser(description="CreditDoc DB Backup")
    parser.add_argument("--list", action="store_true", help="List existing backups")
    parser.add_argument("--verify", type=str, help="Verify a specific backup file")
    parser.add_argument("--stats", action="store_true", help="Show backup stats")
    args = parser.parse_args()

    if args.list:
        list_backups()
        return

    if args.verify:
        path = Path(args.verify)
        if not path.exists():
            print(f"File not found: {path}")
            sys.exit(1)
        log(f"Verifying {path}...")
        ok = verify_backup(path)
        sys.exit(0 if ok else 1)

    if args.stats:
        stats()
        return

    # Default: run backup
    result = backup_database()
    if result is None:
        log("BACKUP FAILED")
        sys.exit(1)

    log("BACKUP SUCCESS")


if __name__ == "__main__":
    main()
