#!/usr/bin/env python3
"""
CreditDoc Incremental Sync — JSON files → SQLite database.

Scans src/content/lenders/*.json for files modified since last sync.
Only updates the DB for files that actually changed (mtime + checksum check).

This is the BRIDGE script while Phase 3 rewires scripts to use the DB directly.
Once all scripts use the DB API, this script becomes unnecessary.

Max drift: 24 hours (runs daily at 07:00 UTC / 2 AM EST).
Manual triggers: safe to run anytime, idempotent.

Protection handling: If a protected profile's JSON file differs from the DB,
the DB is NOT overwritten. The drift is logged and reported as a warning
(possibly indicating a rogue script touched a protected profile).

Usage:
    python3 tools/creditdoc_db_sync.py              # Incremental sync (default)
    python3 tools/creditdoc_db_sync.py --dry-run    # Show what would change
    python3 tools/creditdoc_db_sync.py --full       # Force check ALL files (slow)
    python3 tools/creditdoc_db_sync.py --status     # Show last sync time + stats
    python3 tools/creditdoc_db_sync.py --since <ts> # Force sync files newer than ts

Output:
    Logs to /srv/BusinessOps/logs/creditdoc_db_sync.log
    Records sync in builds table
"""

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from creditdoc_db import CreditDocDB, ProtectedProfileError

PROJECT_DIR = Path(__file__).parent.parent
LENDERS_DIR = PROJECT_DIR / "src" / "content" / "lenders"
CONTENT_DIR = PROJECT_DIR / "src" / "content"
LOG_PATH = Path("/srv/BusinessOps/logs/creditdoc_db_sync.log")

# Telegram alerts for drift warnings
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


def log(msg, to_file=True):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{ts}] {msg}"
    print(line)
    if to_file:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "a") as f:
            f.write(line + "\n")


def checksum_json(data):
    """Canonical JSON hash — sorted keys, compact separators."""
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def get_last_sync_time(db):
    """Get the last successful sync timestamp from metadata table."""
    row = db.conn.execute(
        "SELECT value FROM metadata WHERE key = 'last_sync_at'"
    ).fetchone()
    return row["value"] if row else None


def set_last_sync_time(db, ts):
    """Record the successful sync timestamp."""
    db.conn.execute(
        "INSERT OR REPLACE INTO metadata (key, value, updated_at) VALUES (?, ?, ?)",
        ("last_sync_at", ts, ts),
    )
    db.conn.commit()


def find_changed_files(since_mtime=None):
    """
    Find lender JSON files with mtime > since_mtime.
    Returns list of (path, slug, mtime) tuples.
    """
    candidates = []
    for fpath in LENDERS_DIR.glob("*.json"):
        mtime = fpath.stat().st_mtime
        if since_mtime is None or mtime > since_mtime:
            candidates.append((fpath, fpath.stem, mtime))
    return candidates


def find_changed_content_files(since_mtime=None):
    """Find content JSON files with mtime > since_mtime."""
    files_to_check = [
        ("blog-posts.json", "blog_posts"),
        ("comparisons.json", "comparisons"),
        ("wellness-guides.json", "wellness_guides"),
        ("listicles.json", "listicles"),
        ("categories.json", "categories"),
    ]
    changed = []
    for filename, table in files_to_check:
        fpath = CONTENT_DIR / filename
        if not fpath.exists():
            continue
        mtime = fpath.stat().st_mtime
        if since_mtime is None or mtime > since_mtime:
            changed.append((fpath, filename, table, mtime))
    return changed


def sync_lender_file(db, fpath, slug, dry_run=False):
    """
    Sync a single lender JSON file to the DB.
    Returns: 'updated', 'unchanged', 'drift_blocked', 'new', 'error'
    """
    try:
        with open(fpath) as f:
            file_data = json.load(f)
    except json.JSONDecodeError as e:
        log(f"  ERROR {slug}: invalid JSON: {e}")
        return "error"
    except Exception as e:
        log(f"  ERROR {slug}: {e}")
        return "error"

    file_checksum = checksum_json(file_data)

    # Check if lender exists in DB
    existing = db.get_lender(slug)

    if not existing:
        # New lender — insert it
        if dry_run:
            log(f"  [DRY RUN] NEW: {slug}")
            return "new"
        try:
            db.create_lender(slug, file_data, updated_by="json_sync")
            log(f"  NEW: {slug}")
            return "new"
        except Exception as e:
            log(f"  ERROR creating {slug}: {e}")
            return "error"

    # Compare checksums
    if existing["checksum"] == file_checksum:
        return "unchanged"

    # Checksums differ — file has been modified
    if existing["is_protected"]:
        # DO NOT overwrite protected profiles from JSON
        # Log it as drift for manual review
        log(f"  DRIFT DETECTED (protected): {slug} — JSON differs from DB, not syncing")
        log(f"    DB checksum:   {existing['checksum'][:16]}...")
        log(f"    File checksum: {file_checksum[:16]}...")
        return "drift_blocked"

    # Non-protected profile — update DB to match JSON
    if dry_run:
        log(f"  [DRY RUN] UPDATE: {slug}")
        return "updated"

    # Diff which fields changed (for better audit logs)
    changed_fields = {}
    for key, new_val in file_data.items():
        old_val = existing["data"].get(key)
        if json.dumps(old_val, sort_keys=True) != json.dumps(new_val, sort_keys=True):
            changed_fields[key] = new_val

    # Also catch removed fields
    for key in existing["data"]:
        if key not in file_data:
            changed_fields[key] = None  # Marking for removal

    if not changed_fields:
        # Checksums differ but no field-level diff — shouldn't happen, but log it
        log(f"  WARN {slug}: checksum mismatch but no field diff")
        return "unchanged"

    try:
        # Use update_lender to log individual field changes to audit_log
        # Filter out None values (field removal requires direct SQL)
        fields_to_update = {k: v for k, v in changed_fields.items() if v is not None}
        if fields_to_update:
            # Sync runs as 'json_sync' — not founder, so persistent field
            # wipes and replaces are blocked by the API. This is correct:
            # if a script wiped a persistent field in JSON, we do NOT want
            # to propagate that to the DB. The Guardian will heal the JSON.
            result = db.update_lender(
                slug,
                fields_to_update,
                updated_by="json_sync",
                reason=f"Synced from JSON file (mtime drift)",
            )
            # Log any blocked attempts — Guardian will handle healing
            if result.get("blocked_wipe") or result.get("blocked_replace"):
                log(f"  PROTECTED fields in {slug}:")
                if result["blocked_wipe"]:
                    log(f"    blocked wipe: {result['blocked_wipe']}")
                if result["blocked_replace"]:
                    log(f"    blocked replace: {result['blocked_replace']}")
        return "updated"
    except ProtectedProfileError:
        # Should not hit this since we checked is_protected above, but safety net
        log(f"  DRIFT BLOCKED (protected): {slug}")
        return "drift_blocked"
    except Exception as e:
        log(f"  ERROR updating {slug}: {e}")
        return "error"


def sync_content_file(db, fpath, filename, table, dry_run=False):
    """Sync a content file (blog-posts.json, etc.) to its DB table."""
    try:
        with open(fpath) as f:
            items = json.load(f)
    except Exception as e:
        log(f"  ERROR reading {filename}: {e}")
        return 0

    if not isinstance(items, list):
        log(f"  ERROR {filename}: not a JSON array")
        return 0

    updated = 0
    for item in items:
        slug = item.get("slug", "")
        if not slug:
            continue

        # Get existing row
        existing = db.conn.execute(
            f"SELECT checksum FROM {table} WHERE slug = ?", (slug,)
        ).fetchone()

        item_checksum = checksum_json(item)
        if existing and existing["checksum"] == item_checksum:
            continue  # Unchanged

        if dry_run:
            updated += 1
            continue

        # Upsert via appropriate method
        if table == "blog_posts":
            db.add_blog_post(item, updated_by="json_sync")
        elif table == "comparisons":
            db.add_comparison(item, updated_by="json_sync")
        elif table == "wellness_guides":
            db.add_wellness_guide(item, updated_by="json_sync")
        elif table == "listicles":
            db.add_listicle(item, updated_by="json_sync")
        elif table == "categories":
            # Direct insert for categories (no dedicated method)
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            db.conn.execute(
                """INSERT OR REPLACE INTO categories (slug, data, checksum, updated_at, updated_by)
                   VALUES (?, ?, ?, ?, ?)""",
                (slug, json.dumps(item, separators=(",", ":")), item_checksum, ts, "json_sync"),
            )
            db.conn.commit()
        updated += 1

    return updated


def send_telegram_alert(msg):
    """Send a Telegram alert if configured."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        import urllib.request
        import urllib.parse
        data = urllib.parse.urlencode({
            "chat_id": TELEGRAM_CHAT_ID,
            "text": f"CreditDoc DB Sync:\n{msg}",
            "parse_mode": "Markdown",
        }).encode()
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        urllib.request.urlopen(url, data, timeout=10)
    except Exception as e:
        log(f"  Telegram alert failed: {e}")


def run_sync(dry_run=False, full=False, since=None):
    """Run the incremental sync."""
    db = CreditDocDB()
    start = time.time()

    # Determine sync cutoff
    if since:
        try:
            since_mtime = datetime.fromisoformat(since.replace("Z", "+00:00")).timestamp()
            log(f"Forced sync since: {since}")
        except Exception as e:
            log(f"Invalid --since value: {e}")
            db.close()
            sys.exit(1)
    elif full:
        since_mtime = None
        log("FULL sync — checking all files (slow)")
    else:
        last_sync = get_last_sync_time(db)
        if last_sync:
            try:
                since_mtime = datetime.fromisoformat(last_sync.replace("Z", "+00:00")).timestamp()
                log(f"Last sync: {last_sync}")
            except Exception:
                since_mtime = None
                log(f"Could not parse last_sync_at={last_sync}, running full scan")
        else:
            since_mtime = None
            log("No previous sync recorded, running full scan")

    # Record build start
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if not dry_run:
        db.conn.execute(
            "INSERT INTO builds (started_at, status) VALUES (?, 'running')",
            (now_iso,),
        )
        build_id = db.conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        db.conn.commit()
    else:
        build_id = None

    # ═══ LENDER SYNC ═══
    log("Scanning lender JSON files...")
    candidates = find_changed_files(since_mtime)
    log(f"  Found {len(candidates)} candidate files (mtime > last sync)")

    results = {
        "updated": 0,
        "unchanged": 0,
        "drift_blocked": 0,
        "new": 0,
        "error": 0,
    }
    drift_slugs = []

    for i, (fpath, slug, mtime) in enumerate(candidates):
        result = sync_lender_file(db, fpath, slug, dry_run=dry_run)
        results[result] += 1

        if result == "drift_blocked":
            drift_slugs.append(slug)

        if (i + 1) % 500 == 0:
            log(f"  Progress: {i+1}/{len(candidates)} "
                f"(updated={results['updated']}, unchanged={results['unchanged']}, "
                f"new={results['new']}, drift={results['drift_blocked']}, error={results['error']})")

    log("")
    log("Lender sync results:")
    log(f"  Updated:       {results['updated']}")
    log(f"  New:           {results['new']}")
    log(f"  Unchanged:     {results['unchanged']}")
    log(f"  Drift blocked: {results['drift_blocked']}")
    log(f"  Errors:        {results['error']}")

    # ═══ CONTENT SYNC ═══
    log("")
    log("Scanning content files...")
    content_changed = find_changed_content_files(since_mtime)
    log(f"  Found {len(content_changed)} content files to check")

    content_updates = 0
    for fpath, filename, table, mtime in content_changed:
        count = sync_content_file(db, fpath, filename, table, dry_run=dry_run)
        if count > 0:
            log(f"  {filename} → {table}: {count} rows updated")
            content_updates += count

    log("")
    log("Content sync results:")
    log(f"  Rows updated: {content_updates}")

    # ═══ FINALIZE ═══
    elapsed = time.time() - start

    if not dry_run:
        # Update last_sync_at
        set_last_sync_time(db, now_iso)

        # Update builds table
        db.conn.execute(
            """UPDATE builds
               SET completed_at = ?, lenders_changed = ?, content_exported = ?, status = 'completed'
               WHERE id = ?""",
            (now_iso, results["updated"] + results["new"], content_updates, build_id),
        )
        db.conn.commit()

    log("")
    log(f"Sync complete in {elapsed:.1f}s")
    log(f"{'─'*60}")

    # Alert on drift
    if drift_slugs:
        alert = (
            f"DRIFT DETECTED on {len(drift_slugs)} protected profile(s):\n"
            f"{', '.join(drift_slugs[:10])}"
            f"{f' and {len(drift_slugs)-10} more' if len(drift_slugs) > 10 else ''}\n\n"
            f"These protected profiles' JSON files differ from the DB. "
            f"Review with: python3 tools/creditdoc_db.py get <slug>"
        )
        log(f"ALERT: {alert}")
        send_telegram_alert(alert)

    # Alert on errors
    if results["error"] > 0:
        alert = f"Sync had {results['error']} errors — check {LOG_PATH}"
        log(f"ALERT: {alert}")
        send_telegram_alert(alert)

    db.close()
    return results, content_updates, drift_slugs


def show_status():
    """Show sync status without running anything."""
    db = CreditDocDB()

    last_sync = get_last_sync_time(db)
    if last_sync:
        try:
            last_mtime = datetime.fromisoformat(last_sync.replace("Z", "+00:00")).timestamp()
            age_hours = (time.time() - last_mtime) / 3600
            print(f"Last sync: {last_sync} ({age_hours:.1f}h ago)")
        except Exception:
            print(f"Last sync: {last_sync} (could not parse)")
            last_mtime = None
    else:
        print("Last sync: NEVER")
        last_mtime = None

    if last_mtime is not None:
        candidates = find_changed_files(last_mtime)
        print(f"Files changed since last sync: {len(candidates)}")

        content_changed = find_changed_content_files(last_mtime)
        if content_changed:
            print(f"Content files changed: {len(content_changed)}")
            for _, filename, _, mtime in content_changed:
                age = (time.time() - mtime) / 3600
                print(f"  {filename} ({age:.1f}h ago)")

    # Recent builds
    recent = db.conn.execute(
        "SELECT * FROM builds ORDER BY id DESC LIMIT 5"
    ).fetchall()
    if recent:
        print(f"\nRecent sync/build history:")
        for b in recent:
            print(f"  #{b['id']} {b['started_at']} → {b['status']} "
                  f"(lenders_changed={b['lenders_changed']}, content={b['content_exported']})")

    db.close()


def main():
    parser = argparse.ArgumentParser(description="CreditDoc Incremental DB Sync")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change without applying")
    parser.add_argument("--full", action="store_true", help="Check ALL files regardless of mtime")
    parser.add_argument("--since", type=str, help="Force sync files newer than this ISO timestamp")
    parser.add_argument("--status", action="store_true", help="Show sync status without running")
    args = parser.parse_args()

    if args.status:
        show_status()
        return

    try:
        results, content, drift = run_sync(
            dry_run=args.dry_run,
            full=args.full,
            since=args.since,
        )
    except Exception as e:
        log(f"FATAL: {e}")
        import traceback
        log(traceback.format_exc())
        sys.exit(1)

    # Exit code: 1 if any errors, 2 if any drift blocked, 0 otherwise
    if results["error"] > 0:
        sys.exit(1)
    if drift:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
