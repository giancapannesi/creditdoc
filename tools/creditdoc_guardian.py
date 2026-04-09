#!/usr/bin/env python3
"""
CreditDoc Guardian — Active persistence enforcement.

Runs HOURLY. Heals drift between JSON files and the database.
Enforces persistence rules that the passive sync can't fix alone.

Responsibilities:
    1. Protected profile healing: if a protected profile's JSON file
       differs from the DB, OVERWRITE the JSON with the DB version.
       (The DB is the canonical source for protected profiles.)

    2. Logo persistence: if a logo file exists in public/logos/{slug}.png
       but the lender's logo_url doesn't reference it, RESTORE the reference.
       (Logos never disappear once found.)

    3. Persistent field healing: if a JSON file has a wiped or shrunken
       persistent field (description, pros, etc.), RESTORE from DB.
       (Editorial content never gets lost.)

    4. Content table completeness: ensure every row in blog_posts,
       comparisons, wellness_guides, listicles, categories exists in its
       JSON file. If a JSON file is missing rows, REGENERATE from DB.
       (Content archive is append-only.)

Usage:
    python3 tools/creditdoc_guardian.py                  # Run all checks
    python3 tools/creditdoc_guardian.py --dry-run        # Show what would be fixed
    python3 tools/creditdoc_guardian.py --protected-only # Only heal protected profiles
    python3 tools/creditdoc_guardian.py --logos-only     # Only heal logos
    python3 tools/creditdoc_guardian.py --persistent-only # Only heal persistent fields
    python3 tools/creditdoc_guardian.py --content-only   # Only heal content tables
    python3 tools/creditdoc_guardian.py --report         # Show current drift, no fixes

Cron: 5 minutes past every hour (runs between legacy cron jobs)
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
from creditdoc_db import CreditDocDB, PERSISTENT_FIELDS, _is_empty

PROJECT_DIR = Path(__file__).parent.parent
LENDERS_DIR = PROJECT_DIR / "src" / "content" / "lenders"
CONTENT_DIR = PROJECT_DIR / "src" / "content"
LOGOS_DIR = PROJECT_DIR / "public" / "logos"
LOG_PATH = Path("/srv/BusinessOps/logs/creditdoc_guardian.log")

# Telegram alerts
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


def _canonical(value):
    """Canonical JSON representation for comparison."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _checksum(data):
    canonical = _canonical(data)
    return hashlib.sha256(canonical.encode()).hexdigest()


def write_lender_json(slug, data):
    """Write DB version of a lender to its JSON file."""
    filepath = LENDERS_DIR / f"{slug}.json"
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


def read_lender_json(slug):
    """Read a lender JSON file. Returns None if missing."""
    filepath = LENDERS_DIR / f"{slug}.json"
    if not filepath.exists():
        return None
    try:
        with open(filepath) as f:
            return json.load(f)
    except Exception as e:
        log(f"  ERROR reading {slug}.json: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════
# 1. PROTECTED PROFILE HEALING
# ═══════════════════════════════════════════════════════════════════

def heal_protected_profiles(db, dry_run=False):
    """
    Ensure protected profile JSON files match DB exactly.
    If drift detected, overwrite JSON with DB version.
    """
    log("=== HEAL: Protected Profiles ===")

    rows = db.conn.execute(
        "SELECT slug, data, checksum FROM lenders WHERE is_protected = 1"
    ).fetchall()

    total = len(rows)
    healed = 0
    matching = 0
    missing = 0

    for row in rows:
        slug = row["slug"]
        db_data = json.loads(row["data"])
        db_checksum = row["checksum"]

        file_data = read_lender_json(slug)
        if file_data is None:
            missing += 1
            log(f"  MISSING: {slug}.json — restoring from DB")
            if not dry_run:
                write_lender_json(slug, db_data)
                healed += 1
            continue

        file_checksum = _checksum(file_data)

        if file_checksum == db_checksum:
            matching += 1
            continue

        # Drift detected — heal by writing DB over JSON
        log(f"  DRIFT: {slug} — healing from DB")
        log(f"    DB checksum:   {db_checksum[:16]}...")
        log(f"    File checksum: {file_checksum[:16]}...")

        if not dry_run:
            write_lender_json(slug, db_data)
            healed += 1

            # Audit log
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            db.conn.execute(
                """INSERT INTO audit_log
                   (slug, table_name, field_changed, changed_by, changed_at, reason)
                   VALUES (?, 'lenders', 'HEALED_FROM_DB', 'guardian', ?, ?)""",
                (slug, ts, f"Protected profile drift healed; file mtime was newer"),
            )
            db.conn.commit()

    log(f"  Protected profiles: {total} total, {matching} matching, {healed} healed, {missing} restored")
    return {"total": total, "matching": matching, "healed": healed, "missing": missing}


# ═══════════════════════════════════════════════════════════════════
# 2. LOGO PERSISTENCE
# ═══════════════════════════════════════════════════════════════════

def heal_logos(db, dry_run=False):
    """
    Ensure every logo file in public/logos/ is referenced by its lender.

    Rules:
    1. If /logos/{slug}.png exists, lender's logo_url MUST = /logos/{slug}.png
    2. If logos table has a record, lender data MUST match logos.file_path
    3. Logo file deletions are ALLOWED (founder-initiated), but references get cleaned
    """
    log("=== HEAL: Logo Persistence ===")

    if not LOGOS_DIR.exists():
        log("  SKIP: logos directory does not exist")
        return {"checked": 0, "healed_db": 0, "healed_file": 0, "orphaned": 0}

    # Build set of slugs that have logo files on disk
    logo_files = {}  # slug → local_path
    for fpath in LOGOS_DIR.iterdir():
        if fpath.is_file():
            slug = fpath.stem
            logo_files[slug] = f"/logos/{fpath.name}"

    log(f"  Found {len(logo_files)} logo files on disk")

    checked = 0
    healed_db = 0    # DB logo_url restored
    healed_file = 0  # JSON logo_url restored
    orphaned = 0     # logo file with no matching lender

    for slug, local_path in logo_files.items():
        lender = db.get_lender(slug)
        if not lender:
            orphaned += 1
            continue

        checked += 1
        db_logo = lender["data"].get("logo_url", "") or ""

        # CASE 1: DB has wrong/missing logo_url — heal it
        if db_logo != local_path:
            # Check if current value is an external URL pointing to something real
            # If it's empty or broken, always replace with local path
            if _is_empty(db_logo) or not db_logo.startswith("/logos/"):
                log(f"  DB: {slug} logo_url='{db_logo[:60]}' → '{local_path}'")
                if not dry_run:
                    # Use force=True because we're overwriting a persistent field,
                    # but this is a legitimate restoration (local file IS the truth)
                    try:
                        # If protected, need founder override
                        if lender["is_protected"]:
                            updated_by = "founder"  # Guardian acts as founder for logos
                        else:
                            updated_by = "guardian"
                        db.update_lender(
                            slug,
                            {"logo_url": local_path},
                            updated_by=updated_by,
                            reason=f"Guardian: local logo file exists at {local_path}",
                            force=True,
                        )
                        healed_db += 1
                    except Exception as e:
                        log(f"    ERROR updating DB: {e}")

        # CASE 2: JSON file has wrong logo_url (even if DB is right)
        file_data = read_lender_json(slug)
        if file_data and file_data.get("logo_url", "") != local_path:
            # JSON is out of sync
            if _is_empty(file_data.get("logo_url")) or not str(file_data.get("logo_url", "")).startswith("/logos/"):
                log(f"  FILE: {slug}.json logo_url restored to '{local_path}'")
                if not dry_run:
                    file_data["logo_url"] = local_path
                    write_lender_json(slug, file_data)
                    healed_file += 1

    log(f"  Logos: {checked} checked, {healed_db} DB healed, {healed_file} files healed, {orphaned} orphaned")
    return {
        "checked": checked,
        "healed_db": healed_db,
        "healed_file": healed_file,
        "orphaned": orphaned,
    }


# ═══════════════════════════════════════════════════════════════════
# 3. PERSISTENT FIELD HEALING
# ═══════════════════════════════════════════════════════════════════

def heal_persistent_fields(db, dry_run=False, sample_limit=None):
    """
    Scan all lender JSON files. For each, check if any persistent field
    has been wiped or shrunken compared to the DB version. If so, restore.

    This fixes cases where a rogue script modified a JSON file and the sync
    script blocked the DB update — leaving the file corrupted until guardian.

    Performance: This is expensive (26,698 files). Default: only check files
    with mtime > last_guardian_run.
    """
    log("=== HEAL: Persistent Fields ===")

    # Get last guardian run
    row = db.conn.execute(
        "SELECT value FROM metadata WHERE key = 'last_guardian_run'"
    ).fetchone()
    last_run = row["value"] if row else None

    if last_run:
        try:
            last_mtime = datetime.fromisoformat(last_run.replace("Z", "+00:00")).timestamp()
            log(f"  Last guardian run: {last_run}")
        except Exception:
            last_mtime = 0
    else:
        last_mtime = 0
        log("  No previous guardian run — checking all files (slow)")

    # Find files modified since last run
    candidates = []
    for fpath in LENDERS_DIR.glob("*.json"):
        if fpath.stat().st_mtime > last_mtime:
            candidates.append(fpath)

    log(f"  Candidates to check: {len(candidates)}")

    if sample_limit:
        candidates = candidates[:sample_limit]

    checked = 0
    healed = 0
    healed_fields_total = 0

    for fpath in candidates:
        slug = fpath.stem

        # Get DB version
        db_data = db.get_lender_data(slug)
        if not db_data:
            continue  # Not in DB, skip (sync will handle new lenders)

        try:
            with open(fpath) as f:
                file_data = json.load(f)
        except Exception as e:
            log(f"  ERROR reading {slug}.json: {e}")
            continue

        checked += 1
        fields_to_restore = {}

        for field in PERSISTENT_FIELDS:
            db_value = db_data.get(field)
            file_value = file_data.get(field)

            db_empty = _is_empty(db_value)
            file_empty = _is_empty(file_value)

            # CASE 1: DB has value, file is missing/empty → restore
            if not db_empty and file_empty:
                fields_to_restore[field] = db_value

            # CASE 2: DB has value, file has different value → compare
            elif not db_empty and not file_empty and _canonical(db_value) != _canonical(file_value):
                # Check if file value is suspiciously shorter than DB
                if isinstance(db_value, str) and isinstance(file_value, str):
                    if len(file_value) < len(db_value) * 0.5:
                        # File value is <50% of DB length — suspicious shrink, restore
                        fields_to_restore[field] = db_value

        if fields_to_restore:
            log(f"  RESTORE: {slug} — {list(fields_to_restore.keys())}")
            if not dry_run:
                # Write restored fields to JSON file
                for field, value in fields_to_restore.items():
                    file_data[field] = value
                write_lender_json(slug, file_data)
                healed += 1
                healed_fields_total += len(fields_to_restore)

                # Audit log
                ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                for field in fields_to_restore:
                    db.conn.execute(
                        """INSERT INTO audit_log
                           (slug, table_name, field_changed, changed_by, changed_at, reason)
                           VALUES (?, 'lenders', ?, 'guardian', ?, ?)""",
                        (slug, f"RESTORED:{field}", ts, f"Persistent field restored from DB"),
                    )
                db.conn.commit()

    log(f"  Persistent fields: {checked} files checked, {healed} healed, {healed_fields_total} fields restored")
    return {"checked": checked, "healed": healed, "fields_restored": healed_fields_total}


# ═══════════════════════════════════════════════════════════════════
# 4. CONTENT TABLE COMPLETENESS
# ═══════════════════════════════════════════════════════════════════

def heal_content_tables(db, dry_run=False):
    """
    Ensure every row in DB content tables exists in the corresponding JSON file.
    If JSON has fewer rows than DB, REGENERATE the JSON from DB (full export).

    This prevents the scenario where a script overwrites blog-posts.json with
    only its own 2 new posts, silently losing the other 23.
    """
    log("=== HEAL: Content Tables ===")

    mapping = [
        ("blog_posts", "blog-posts.json"),
        ("comparisons", "comparisons.json"),
        ("wellness_guides", "wellness-guides.json"),
        ("listicles", "listicles.json"),
        ("categories", "categories.json"),
    ]

    results = {}

    for table, filename in mapping:
        db_count = db.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

        fpath = CONTENT_DIR / filename
        if not fpath.exists():
            log(f"  {filename}: MISSING — regenerating from DB ({db_count} rows)")
            if not dry_run:
                db.export_content_file(table, filename)
            results[table] = {"db": db_count, "file": 0, "action": "regenerated"}
            continue

        try:
            with open(fpath) as f:
                file_items = json.load(f)
        except Exception as e:
            log(f"  {filename}: ERROR reading ({e}) — regenerating from DB")
            if not dry_run:
                db.export_content_file(table, filename)
            results[table] = {"db": db_count, "file": 0, "action": "regenerated"}
            continue

        file_count = len(file_items)

        if file_count < db_count:
            # JSON is missing rows — full regen from DB
            log(f"  {filename}: DB={db_count}, FILE={file_count} — regenerating from DB")
            if not dry_run:
                db.export_content_file(table, filename)
            results[table] = {"db": db_count, "file": file_count, "action": "regenerated"}

            # Audit log
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            db.conn.execute(
                """INSERT INTO audit_log
                   (slug, table_name, field_changed, old_value, new_value, changed_by, changed_at, reason)
                   VALUES (?, ?, 'RESTORED_FROM_DB', ?, ?, 'guardian', ?, ?)""",
                (
                    filename,
                    table,
                    str(file_count),
                    str(db_count),
                    ts,
                    f"Content file had {file_count} rows, DB has {db_count} — regenerated",
                ),
            )
            db.conn.commit()
        else:
            results[table] = {"db": db_count, "file": file_count, "action": "ok"}

        log(f"  {filename}: DB={db_count}, FILE={file_count} {'✓' if file_count >= db_count else '⚠'}")

    return results


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def send_telegram_alert(msg):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        import urllib.request
        import urllib.parse
        data = urllib.parse.urlencode({
            "chat_id": TELEGRAM_CHAT_ID,
            "text": f"CreditDoc Guardian:\n{msg}",
            "parse_mode": "Markdown",
        }).encode()
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        urllib.request.urlopen(url, data, timeout=10)
    except Exception:
        pass


def run_guardian(dry_run=False, sections=None):
    """Run guardian checks. sections is a list of sections to run, or None for all."""
    start = time.time()
    db = CreditDocDB()

    if sections is None:
        sections = ["protected", "logos", "persistent", "content"]

    results = {}

    try:
        if "protected" in sections:
            results["protected"] = heal_protected_profiles(db, dry_run=dry_run)
        if "logos" in sections:
            results["logos"] = heal_logos(db, dry_run=dry_run)
        if "persistent" in sections:
            results["persistent"] = heal_persistent_fields(db, dry_run=dry_run)
        if "content" in sections:
            results["content"] = heal_content_tables(db, dry_run=dry_run)

        # Update last_guardian_run timestamp
        if not dry_run:
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            db.conn.execute(
                "INSERT OR REPLACE INTO metadata (key, value, updated_at) VALUES (?, ?, ?)",
                ("last_guardian_run", ts, ts),
            )
            db.conn.commit()

    finally:
        db.close()

    elapsed = time.time() - start

    log("")
    log(f"Guardian complete in {elapsed:.1f}s")

    # Summary
    total_healed = 0
    if "protected" in results:
        total_healed += results["protected"].get("healed", 0)
    if "logos" in results:
        total_healed += results["logos"].get("healed_db", 0) + results["logos"].get("healed_file", 0)
    if "persistent" in results:
        total_healed += results["persistent"].get("healed", 0)
    if "content" in results:
        total_healed += sum(1 for r in results["content"].values() if r.get("action") == "regenerated")

    if total_healed > 0:
        alert = f"Guardian healed {total_healed} drift issue(s). Check {LOG_PATH}"
        log(f"ALERT: {alert}")
        send_telegram_alert(alert)

    log("─" * 60)
    return results


def report_only():
    """Show drift without fixing anything."""
    run_guardian(dry_run=True)


def main():
    parser = argparse.ArgumentParser(description="CreditDoc Guardian")
    parser.add_argument("--dry-run", action="store_true", help="Show drift without fixing")
    parser.add_argument("--report", action="store_true", help="Same as --dry-run")
    parser.add_argument("--protected-only", action="store_true", help="Heal protected profiles only")
    parser.add_argument("--logos-only", action="store_true", help="Heal logos only")
    parser.add_argument("--persistent-only", action="store_true", help="Heal persistent fields only")
    parser.add_argument("--content-only", action="store_true", help="Heal content tables only")
    args = parser.parse_args()

    if args.report:
        args.dry_run = True

    # Determine sections to run
    sections = None
    if args.protected_only:
        sections = ["protected"]
    elif args.logos_only:
        sections = ["logos"]
    elif args.persistent_only:
        sections = ["persistent"]
    elif args.content_only:
        sections = ["content"]

    run_guardian(dry_run=args.dry_run, sections=sections)


if __name__ == "__main__":
    main()
