#!/usr/bin/env python3
"""
CreditDoc: Migrate JSON flat files to SQLite database.

This is Phase 1 of the persistence architecture. Creates the database
as the single source of truth for all CreditDoc data.

Usage:
    python3 tools/creditdoc_migrate_to_db.py --create-schema
    python3 tools/creditdoc_migrate_to_db.py --migrate-lenders
    python3 tools/creditdoc_migrate_to_db.py --migrate-content
    python3 tools/creditdoc_migrate_to_db.py --migrate-logos
    python3 tools/creditdoc_migrate_to_db.py --migrate-all
    python3 tools/creditdoc_migrate_to_db.py --verify
"""

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
DB_PATH = PROJECT_DIR / "data" / "creditdoc.db"
LENDERS_DIR = PROJECT_DIR / "src" / "content" / "lenders"
CONTENT_DIR = PROJECT_DIR / "src" / "content"
LOGOS_DIR = PROJECT_DIR / "public" / "logos"
PROTECTED_PATH = PROJECT_DIR / "data" / "protected_profiles.json"

SCHEMA_SQL = """
-- CreditDoc Persistent Database
-- Created: 2026-04-08
-- Purpose: Single source of truth for all CreditDoc data.
--          JSON files in src/content/ become exports from this DB.

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- =============================================================
-- LENDERS — replaces 26,698 individual JSON files
-- =============================================================
CREATE TABLE IF NOT EXISTS lenders (
    slug TEXT PRIMARY KEY,
    data JSON NOT NULL,
    category TEXT NOT NULL DEFAULT 'unknown',
    processing_status TEXT NOT NULL DEFAULT 'raw',
    is_protected INTEGER NOT NULL DEFAULT 0,
    is_enriched INTEGER NOT NULL DEFAULT 0,
    quality_score INTEGER NOT NULL DEFAULT 0,
    logo_path TEXT,
    website_url TEXT,
    checksum TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    updated_by TEXT NOT NULL DEFAULT 'migration',
    exported_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_lenders_category ON lenders(category);
CREATE INDEX IF NOT EXISTS idx_lenders_status ON lenders(processing_status);
CREATE INDEX IF NOT EXISTS idx_lenders_protected ON lenders(is_protected);
CREATE INDEX IF NOT EXISTS idx_lenders_updated ON lenders(updated_at);
CREATE INDEX IF NOT EXISTS idx_lenders_exported ON lenders(exported_at);

-- =============================================================
-- AUDIT LOG — every change tracked with before/after
-- =============================================================
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL,
    table_name TEXT NOT NULL DEFAULT 'lenders',
    field_changed TEXT,
    old_value TEXT,
    new_value TEXT,
    changed_by TEXT NOT NULL,
    changed_at TEXT NOT NULL,
    reason TEXT
);

CREATE INDEX IF NOT EXISTS idx_audit_slug ON audit_log(slug);
CREATE INDEX IF NOT EXISTS idx_audit_changed_at ON audit_log(changed_at);

-- =============================================================
-- CONTENT TABLES — replace individual JSON files
-- =============================================================
CREATE TABLE IF NOT EXISTS blog_posts (
    slug TEXT PRIMARY KEY,
    data JSON NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    checksum TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    updated_by TEXT NOT NULL DEFAULT 'migration',
    exported_at TEXT
);

CREATE TABLE IF NOT EXISTS comparisons (
    slug TEXT PRIMARY KEY,
    data JSON NOT NULL,
    checksum TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    updated_by TEXT NOT NULL DEFAULT 'migration',
    exported_at TEXT
);

CREATE TABLE IF NOT EXISTS wellness_guides (
    slug TEXT PRIMARY KEY,
    data JSON NOT NULL,
    checksum TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    updated_by TEXT NOT NULL DEFAULT 'migration',
    exported_at TEXT
);

CREATE TABLE IF NOT EXISTS listicles (
    slug TEXT PRIMARY KEY,
    data JSON NOT NULL,
    checksum TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    updated_by TEXT NOT NULL DEFAULT 'migration',
    exported_at TEXT
);

CREATE TABLE IF NOT EXISTS categories (
    slug TEXT PRIMARY KEY,
    data JSON NOT NULL,
    checksum TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    updated_by TEXT NOT NULL DEFAULT 'migration'
);

-- =============================================================
-- LOGOS — track every logo file with hash
-- =============================================================
CREATE TABLE IF NOT EXISTS logos (
    slug TEXT PRIMARY KEY,
    file_path TEXT,
    file_hash TEXT,
    source_url TEXT,
    fetched_at TEXT,
    status TEXT NOT NULL DEFAULT 'missing'
);

CREATE INDEX IF NOT EXISTS idx_logos_status ON logos(status);

-- =============================================================
-- BUILDS — track every export/build
-- =============================================================
CREATE TABLE IF NOT EXISTS builds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    lenders_exported INTEGER DEFAULT 0,
    lenders_changed INTEGER DEFAULT 0,
    content_exported INTEGER DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'running'
);

-- =============================================================
-- METADATA — key-value store for DB-level state
-- =============================================================
CREATE TABLE IF NOT EXISTS metadata (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT
);
"""


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_json(data):
    """Stable JSON hash — sorted keys, no whitespace variance."""
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def sha256_file(path):
    """Hash a binary file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def create_schema(db_path=DB_PATH):
    """Create all tables. Safe to run multiple times (IF NOT EXISTS)."""
    print(f"Creating schema at {db_path}...")
    os.makedirs(db_path.parent, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.executescript(SCHEMA_SQL)
    conn.execute(
        "INSERT OR REPLACE INTO metadata (key, value, updated_at) VALUES (?, ?, ?)",
        ("schema_version", "1.0", now_iso()),
    )
    conn.execute(
        "INSERT OR REPLACE INTO metadata (key, value, updated_at) VALUES (?, ?, ?)",
        ("created_at", now_iso(), now_iso()),
    )
    conn.commit()
    conn.close()
    print("  Schema created successfully.")
    return True


def migrate_lenders(db_path=DB_PATH):
    """Import all lender JSON files into the lenders table."""
    print(f"Migrating lenders from {LENDERS_DIR}...")

    # Load protected profiles list
    protected_slugs = set()
    if PROTECTED_PATH.exists():
        with open(PROTECTED_PATH) as f:
            pp = json.load(f)
            protected_slugs = set(pp.get("profiles", []))
        print(f"  Loaded {len(protected_slugs)} protected profiles.")

    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")

    json_files = sorted(LENDERS_DIR.glob("*.json"))
    total = len(json_files)
    print(f"  Found {total} JSON files.")

    inserted = 0
    skipped = 0
    errors = 0
    ts = now_iso()

    # Batch insert for performance
    conn.execute("BEGIN")
    for i, fpath in enumerate(json_files):
        slug = fpath.stem
        try:
            with open(fpath) as f:
                data = json.load(f)

            category = data.get("category", "unknown")
            processing_status = data.get("processing_status", "raw")
            is_enriched = 1 if data.get("has_been_enriched") else 0
            quality_score = data.get("quality_score", 0) or 0
            logo_path = data.get("logo_url", "")
            website_url = data.get("website_url", "") or data.get("website", "")
            checksum = sha256_json(data)

            conn.execute(
                """INSERT OR REPLACE INTO lenders
                   (slug, data, category, processing_status, is_protected,
                    is_enriched, quality_score, logo_path, website_url,
                    checksum, created_at, updated_at, updated_by)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    slug,
                    json.dumps(data, separators=(",", ":")),
                    category,
                    processing_status,
                    1 if slug in protected_slugs else 0,
                    is_enriched,
                    quality_score,
                    logo_path,
                    website_url,
                    checksum,
                    ts,
                    ts,
                    "migration",
                ),
            )
            inserted += 1

        except json.JSONDecodeError as e:
            print(f"  ERROR: {slug} — invalid JSON: {e}")
            errors += 1
        except Exception as e:
            print(f"  ERROR: {slug} — {e}")
            errors += 1

        if (i + 1) % 5000 == 0:
            conn.commit()
            conn.execute("BEGIN")
            print(f"  Progress: {i+1}/{total} ({inserted} inserted, {errors} errors)")

    conn.commit()

    # Record migration in metadata
    conn.execute(
        "INSERT OR REPLACE INTO metadata (key, value, updated_at) VALUES (?, ?, ?)",
        ("lenders_migrated_at", now_iso(), now_iso()),
    )
    conn.execute(
        "INSERT OR REPLACE INTO metadata (key, value, updated_at) VALUES (?, ?, ?)",
        ("lenders_migrated_count", str(inserted), now_iso()),
    )
    conn.commit()
    conn.close()

    print(f"\n  Migration complete:")
    print(f"    Inserted: {inserted}")
    print(f"    Errors:   {errors}")
    print(f"    Protected: {len(protected_slugs)}")
    return inserted, errors


def migrate_content(db_path=DB_PATH):
    """Import blog posts, comparisons, wellness guides, listicles, categories."""
    print("Migrating content files...")
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    ts = now_iso()

    content_map = {
        "blog-posts.json": ("blog_posts", "slug"),
        "comparisons.json": ("comparisons", "slug"),
        "wellness-guides.json": ("wellness_guides", "slug"),
        "listicles.json": ("listicles", "slug"),
        "categories.json": ("categories", "slug"),
    }

    for filename, (table, slug_field) in content_map.items():
        fpath = CONTENT_DIR / filename
        if not fpath.exists():
            print(f"  SKIP: {filename} not found")
            continue

        with open(fpath) as f:
            items = json.load(f)

        if not isinstance(items, list):
            print(f"  SKIP: {filename} is not a JSON array")
            continue

        count = 0
        conn.execute("BEGIN")
        for item in items:
            slug = item.get(slug_field, "")
            if not slug:
                continue

            checksum = sha256_json(item)
            status = item.get("status", "") if table == "blog_posts" else None

            if table == "blog_posts":
                conn.execute(
                    """INSERT OR REPLACE INTO blog_posts
                       (slug, data, status, checksum, updated_at, updated_by)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (slug, json.dumps(item, separators=(",", ":")), status or "draft", checksum, ts, "migration"),
                )
            elif table == "categories":
                conn.execute(
                    """INSERT OR REPLACE INTO categories
                       (slug, data, checksum, updated_at, updated_by)
                       VALUES (?, ?, ?, ?, ?)""",
                    (slug, json.dumps(item, separators=(",", ":")), checksum, ts, "migration"),
                )
            else:
                conn.execute(
                    f"""INSERT OR REPLACE INTO {table}
                        (slug, data, checksum, updated_at, updated_by)
                        VALUES (?, ?, ?, ?, ?)""",
                    (slug, json.dumps(item, separators=(",", ":")), checksum, ts, "migration"),
                )
            count += 1

        conn.commit()
        print(f"  ✓ {filename} → {table}: {count} rows")

    conn.execute(
        "INSERT OR REPLACE INTO metadata (key, value, updated_at) VALUES (?, ?, ?)",
        ("content_migrated_at", now_iso(), now_iso()),
    )
    conn.commit()
    conn.close()
    print("  Content migration complete.")


def migrate_logos(db_path=DB_PATH):
    """Scan public/logos/ and populate the logos table with hashes."""
    print(f"Migrating logos from {LOGOS_DIR}...")
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")

    if not LOGOS_DIR.exists():
        print("  SKIP: logos directory not found")
        return

    logo_files = sorted(LOGOS_DIR.iterdir())
    total = len(logo_files)
    print(f"  Found {total} logo files.")

    count = 0
    conn.execute("BEGIN")
    for i, fpath in enumerate(logo_files):
        if fpath.is_dir():
            continue

        slug = fpath.stem
        file_hash = sha256_file(fpath)
        rel_path = f"/logos/{fpath.name}"

        # Try to get source URL from lender data
        row = conn.execute(
            "SELECT json_extract(data, '$.logo_url') FROM lenders WHERE slug = ?",
            (slug,),
        ).fetchone()
        source_url = row[0] if row and row[0] else ""

        conn.execute(
            """INSERT OR REPLACE INTO logos
               (slug, file_path, file_hash, source_url, fetched_at, status)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (slug, rel_path, file_hash, source_url, now_iso(), "fetched"),
        )
        count += 1

        if (i + 1) % 2000 == 0:
            conn.commit()
            conn.execute("BEGIN")
            print(f"  Progress: {i+1}/{total}")

    conn.commit()
    conn.execute(
        "INSERT OR REPLACE INTO metadata (key, value, updated_at) VALUES (?, ?, ?)",
        ("logos_migrated_at", now_iso(), now_iso()),
    )
    conn.commit()
    conn.close()
    print(f"  ✓ Logos migrated: {count}")


def verify(db_path=DB_PATH):
    """Verify migration integrity."""
    print(f"\n{'='*60}")
    print("MIGRATION VERIFICATION")
    print(f"{'='*60}\n")

    conn = sqlite3.connect(str(db_path))

    # 1. Lender counts
    db_lenders = conn.execute("SELECT COUNT(*) FROM lenders").fetchone()[0]
    json_files = len(list(LENDERS_DIR.glob("*.json")))
    match = "✓" if db_lenders == json_files else "✗ MISMATCH"
    print(f"Lenders:     DB={db_lenders}  JSON={json_files}  {match}")

    # 2. Category breakdown
    print("\nCategory breakdown:")
    rows = conn.execute(
        "SELECT category, COUNT(*) as cnt FROM lenders GROUP BY category ORDER BY cnt DESC"
    ).fetchall()
    for cat, cnt in rows[:10]:
        print(f"  {cat}: {cnt}")
    if len(rows) > 10:
        print(f"  ... and {len(rows) - 10} more categories")

    # 3. Status breakdown
    print("\nProcessing status:")
    rows = conn.execute(
        "SELECT processing_status, COUNT(*) FROM lenders GROUP BY processing_status ORDER BY COUNT(*) DESC"
    ).fetchall()
    for status, cnt in rows:
        print(f"  {status}: {cnt}")

    # 4. Protected profiles
    protected = conn.execute("SELECT COUNT(*) FROM lenders WHERE is_protected = 1").fetchone()[0]
    print(f"\nProtected profiles: {protected}")

    # 5. Enriched profiles
    enriched = conn.execute("SELECT COUNT(*) FROM lenders WHERE is_enriched = 1").fetchone()[0]
    print(f"Enriched profiles:  {enriched}")

    # 6. Content tables
    print("\nContent tables:")
    for table in ["blog_posts", "comparisons", "wellness_guides", "listicles", "categories"]:
        cnt = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {cnt}")

    # 7. Logos
    logo_count = conn.execute("SELECT COUNT(*) FROM logos").fetchone()[0]
    logo_files = len(list(LOGOS_DIR.glob("*"))) if LOGOS_DIR.exists() else 0
    match = "✓" if logo_count == logo_files else "✗ MISMATCH"
    print(f"\nLogos:       DB={logo_count}  Files={logo_files}  {match}")

    # 8. Spot-check 5 random protected profiles
    print("\nSpot-check 5 random protected profiles:")
    rows = conn.execute(
        "SELECT slug, category, processing_status, is_enriched, quality_score FROM lenders WHERE is_protected = 1 ORDER BY RANDOM() LIMIT 5"
    ).fetchall()
    for slug, cat, status, enriched, qs in rows:
        # Verify JSON file still matches
        json_path = LENDERS_DIR / f"{slug}.json"
        if json_path.exists():
            with open(json_path) as f:
                file_data = json.load(f)
            file_checksum = sha256_json(file_data)
            db_checksum = conn.execute(
                "SELECT checksum FROM lenders WHERE slug = ?", (slug,)
            ).fetchone()[0]
            cs_match = "✓ checksum match" if file_checksum == db_checksum else "✗ CHECKSUM MISMATCH"
        else:
            cs_match = "✗ JSON FILE MISSING"
        print(f"  {slug}: {cat} | {status} | enriched={enriched} | qs={qs} | {cs_match}")

    # 9. Spot-check 5 random non-protected profiles
    print("\nSpot-check 5 random non-protected profiles:")
    rows = conn.execute(
        "SELECT slug, category, processing_status, is_enriched FROM lenders WHERE is_protected = 0 ORDER BY RANDOM() LIMIT 5"
    ).fetchall()
    for slug, cat, status, enriched in rows:
        json_path = LENDERS_DIR / f"{slug}.json"
        if json_path.exists():
            with open(json_path) as f:
                file_data = json.load(f)
            file_checksum = sha256_json(file_data)
            db_checksum = conn.execute(
                "SELECT checksum FROM lenders WHERE slug = ?", (slug,)
            ).fetchone()[0]
            cs_match = "✓" if file_checksum == db_checksum else "✗ MISMATCH"
        else:
            cs_match = "✗ MISSING"
        print(f"  {slug}: {cat} | {status} | enriched={enriched} | {cs_match}")

    # 10. DB file size
    db_size = os.path.getsize(db_path) / (1024 * 1024)
    print(f"\nDatabase size: {db_size:.1f} MB")

    # 11. Metadata
    print("\nMetadata:")
    rows = conn.execute("SELECT key, value, updated_at FROM metadata").fetchall()
    for key, value, updated_at in rows:
        print(f"  {key}: {value} ({updated_at})")

    conn.close()
    print(f"\n{'='*60}")
    print("VERIFICATION COMPLETE")
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(description="CreditDoc JSON → SQLite migration")
    parser.add_argument("--create-schema", action="store_true", help="Create database schema")
    parser.add_argument("--migrate-lenders", action="store_true", help="Migrate lender profiles")
    parser.add_argument("--migrate-content", action="store_true", help="Migrate content files")
    parser.add_argument("--migrate-logos", action="store_true", help="Migrate logo inventory")
    parser.add_argument("--migrate-all", action="store_true", help="Run all migrations")
    parser.add_argument("--verify", action="store_true", help="Verify migration")
    parser.add_argument("--db", type=str, default=str(DB_PATH), help="Database path")

    args = parser.parse_args()
    db_path = Path(args.db)

    if not any([args.create_schema, args.migrate_lenders, args.migrate_content,
                args.migrate_logos, args.migrate_all, args.verify]):
        parser.print_help()
        return

    start = time.time()

    if args.create_schema or args.migrate_all:
        create_schema(db_path)

    if args.migrate_lenders or args.migrate_all:
        migrate_lenders(db_path)

    if args.migrate_content or args.migrate_all:
        migrate_content(db_path)

    if args.migrate_logos or args.migrate_all:
        migrate_logos(db_path)

    if args.verify or args.migrate_all:
        verify(db_path)

    elapsed = time.time() - start
    print(f"\nTotal time: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
