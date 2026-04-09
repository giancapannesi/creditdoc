#!/usr/bin/env python3
"""
CreditDoc Incremental Build — exports changed data from DB, builds, commits.

This replaces the old pattern of:
    git add -A src/content/lenders/ && git commit && git push

New pattern:
    python3 tools/creditdoc_build.py --export-and-commit
    python3 tools/creditdoc_build.py --export-only          # just export, no git
    python3 tools/creditdoc_build.py --export-content        # just content tables
    python3 tools/creditdoc_build.py --full-export           # export ALL (for rebuilds)
    python3 tools/creditdoc_build.py --status                # show what would be exported

How it works:
    1. Reads DB for lenders where updated_at > exported_at (or never exported)
    2. Writes only those lenders to JSON files
    3. Exports content tables (blog, comparisons, wellness, listicles) if changed
    4. Optionally: git add changed files → commit → push
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent dir so we can import creditdoc_db
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from creditdoc_db import CreditDocDB

PROJECT_DIR = Path(__file__).parent.parent
LENDERS_DIR = PROJECT_DIR / "src" / "content" / "lenders"
CONTENT_DIR = PROJECT_DIR / "src" / "content"
LOGOS_DIR = PROJECT_DIR / "public" / "logos"


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def export_changed_lenders(db):
    """Export only lenders that changed since last export."""
    rows = db.conn.execute(
        """SELECT slug FROM lenders
           WHERE exported_at IS NULL OR updated_at > exported_at"""
    ).fetchall()
    slugs = [r["slug"] for r in rows]

    if not slugs:
        print("No lender changes to export.")
        return []

    print(f"Exporting {len(slugs)} changed lenders...")
    exported = []
    for slug in slugs:
        if db.export_lender_to_json(slug):
            exported.append(slug)

    print(f"  Exported {len(exported)} lenders to JSON.")
    return exported


def export_changed_content(db):
    """Export content tables that have changes since last export."""
    content_map = {
        "blog_posts": "blog-posts.json",
        "comparisons": "comparisons.json",
        "wellness_guides": "wellness-guides.json",
        "listicles": "listicles.json",
        "categories": "categories.json",
    }

    exported = {}
    for table, filename in content_map.items():
        # Check if any rows changed since last export
        if table == "categories":
            # Categories don't have exported_at, always export
            count = db.export_content_file(table, filename)
            exported[table] = count
        else:
            changed = db.conn.execute(
                f"SELECT COUNT(*) FROM {table} WHERE exported_at IS NULL OR updated_at > exported_at"
            ).fetchone()[0]
            if changed > 0:
                count = db.export_content_file(table, filename)
                exported[table] = count
                print(f"  Exported {table}: {count} rows ({changed} changed)")

    if not exported:
        print("No content changes to export.")
    return exported


def get_status(db):
    """Show what would be exported without doing it."""
    # Changed lenders
    lender_count = db.conn.execute(
        "SELECT COUNT(*) FROM lenders WHERE exported_at IS NULL OR updated_at > exported_at"
    ).fetchone()[0]

    # Changed content
    content_changes = {}
    for table in ["blog_posts", "comparisons", "wellness_guides", "listicles"]:
        changed = db.conn.execute(
            f"SELECT COUNT(*) FROM {table} WHERE exported_at IS NULL OR updated_at > exported_at"
        ).fetchone()[0]
        if changed > 0:
            content_changes[table] = changed

    # Last build
    last_build = db.conn.execute(
        "SELECT * FROM builds ORDER BY id DESC LIMIT 1"
    ).fetchone()

    print(f"\n{'='*50}")
    print("CreditDoc Build Status")
    print(f"{'='*50}")
    print(f"Lenders needing export:  {lender_count:,}")
    if content_changes:
        print(f"Content changes:")
        for table, count in content_changes.items():
            print(f"  {table}: {count}")
    else:
        print(f"Content changes:         none")

    if last_build:
        print(f"\nLast build:")
        print(f"  Time:     {last_build['completed_at']}")
        print(f"  Exported: {last_build['lenders_exported']} lenders")
        print(f"  Status:   {last_build['status']}")
    else:
        print(f"\nNo previous builds recorded.")

    print(f"{'='*50}")
    return lender_count, content_changes


def git_commit_changes(exported_slugs, content_exported, push=False):
    """Stage DB-exported files AND any other modified files under src/content/.
    Commits and optionally pushes. This is backward-compatible with the old
    git add -A pattern — dual-write scripts that modified JSON without going
    through the DB API still get picked up.
    """
    os.chdir(str(PROJECT_DIR))

    # Step 1: Stage DB-exported lender JSON files (explicit)
    if exported_slugs:
        batch_size = 500
        for i in range(0, len(exported_slugs), batch_size):
            batch = exported_slugs[i:i+batch_size]
            files = [f"src/content/lenders/{slug}.json" for slug in batch]
            subprocess.run(["git", "add"] + files, check=True, capture_output=True)

    # Step 2: Stage DB-exported content files (explicit)
    if content_exported:
        file_map = {
            "blog_posts": "src/content/blog-posts.json",
            "comparisons": "src/content/comparisons.json",
            "wellness_guides": "src/content/wellness-guides.json",
            "listicles": "src/content/listicles.json",
            "categories": "src/content/categories.json",
        }
        content_files = [file_map[t] for t in content_exported if t in file_map]
        if content_files:
            subprocess.run(["git", "add"] + content_files, check=True, capture_output=True)

    # Step 3: CATCH-UP — stage any other modified/untracked files under src/content/lenders/
    # Uses -z (null-separated) to handle paths with special chars / unicode
    result = subprocess.run(
        ["git", "status", "--porcelain", "-z", "src/content/lenders/"],
        capture_output=True, text=True
    )
    if result.stdout:
        catchup_files = []
        # Null-separated: "XY path\0XY path\0..."
        for entry in result.stdout.split("\0"):
            if len(entry) < 4:
                continue
            status = entry[:2]
            path = entry[3:]
            # Stage modified (M), added (A), untracked (??), deleted (D)
            if status.strip() in ("M", "A", "??", "AM", "MM"):
                catchup_files.append(path)
        if catchup_files:
            # Batch in groups of 500
            for i in range(0, len(catchup_files), 500):
                batch = catchup_files[i:i+500]
                # Use -- to separate flags from paths (safety)
                subprocess.run(["git", "add", "--"] + batch, check=True, capture_output=True)
            print(f"  Catch-up: staged {len(catchup_files)} additional modified lender files")

    # Step 4: Stage any other modified content files (catch-up)
    result = subprocess.run(
        ["git", "status", "--porcelain", "-z", "src/content/"],
        capture_output=True, text=True
    )
    if result.stdout:
        catchup_content = []
        for entry in result.stdout.split("\0"):
            if len(entry) < 4:
                continue
            status = entry[:2]
            path = entry[3:]
            # Only content JSON files at the src/content/ root (not lenders subdir)
            if (path.endswith(".json") and "/lenders/" not in path
                and status.strip() in ("M", "A", "??", "AM", "MM")):
                catchup_content.append(path)
        if catchup_content:
            subprocess.run(["git", "add", "--"] + catchup_content, check=True, capture_output=True)
            print(f"  Catch-up: staged {len(catchup_content)} additional content files")

    # Step 5: Stage any new logos
    result = subprocess.run(
        ["git", "status", "--porcelain", "-z", "public/logos/"],
        capture_output=True, text=True
    )
    if result.stdout:
        new_logos = []
        for entry in result.stdout.split("\0"):
            if len(entry) < 4:
                continue
            status = entry[:2]
            path = entry[3:]
            if status.strip() in ("??", "A", "M", "MM", "AM"):
                new_logos.append(path)
        if new_logos:
            # Batch in groups of 500
            for i in range(0, len(new_logos), 500):
                batch = new_logos[i:i+500]
                subprocess.run(["git", "add", "--"] + batch, check=True, capture_output=True)
            print(f"  Staged {len(new_logos)} new logos")

    # Check if there's anything to commit
    result = subprocess.run(
        ["git", "diff", "--cached", "--stat"],
        capture_output=True, text=True
    )
    if not result.stdout.strip():
        print("Nothing to commit (no changes after export).")
        return False

    # Build commit message
    parts = []
    if exported_slugs:
        parts.append(f"{len(exported_slugs)} lenders")
    if content_exported:
        for table, count in content_exported.items():
            parts.append(f"{count} {table.replace('_', ' ')}")

    msg = f"DB export: {', '.join(parts)} ({datetime.now().strftime('%Y-%m-%d')})"
    print(f"  Committing: {msg}")

    # Verify any protected profile changes match the DB first (safety check)
    # The build script is DB-authoritative, so legitimate protected profile
    # updates from the DB (via force=True) should pass the pre-commit hook.
    # We bypass the hook via CREDITDOC_SKIP_PROTECTION=1 — but only after
    # verifying that protected profile file content matches DB.
    _verify_protected_match_db()

    env = os.environ.copy()
    env["CREDITDOC_SKIP_PROTECTION"] = "1"

    subprocess.run(["git", "commit", "-m", msg], check=True, capture_output=True, env=env)

    if push:
        print("  Pushing to remote...")
        subprocess.run(["git", "push", "origin", "main"], check=True, capture_output=True)
        print("  Pushed.")

    return True


def _verify_protected_match_db():
    """Safety check: before committing, verify any modified protected profiles
    match the DB exactly. If they don't, something is wrong — abort.
    """
    import hashlib
    from creditdoc_db import CreditDocDB

    # Get list of staged protected profile files
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "src/content/lenders/"],
        capture_output=True, text=True
    )
    staged_lender_files = [
        line.strip() for line in result.stdout.strip().split("\n")
        if line.strip().endswith(".json")
    ]

    if not staged_lender_files:
        return

    protected_path = PROJECT_DIR / "data" / "protected_profiles.json"
    if not protected_path.exists():
        return
    with open(protected_path) as f:
        protected = set(json.load(f).get("profiles", []))

    def canon(d):
        return json.dumps(d, sort_keys=True, separators=(",", ":"))

    with CreditDocDB() as db:
        for fpath in staged_lender_files:
            slug = fpath.replace("src/content/lenders/", "").replace(".json", "")
            if slug not in protected:
                continue

            db_data = db.get_lender_data(slug)
            if not db_data:
                print(f"  ⚠ Protected {slug}: not in DB — aborting commit")
                raise RuntimeError(f"Protected profile {slug} staged but not in DB")

            full_path = PROJECT_DIR / fpath
            if not full_path.exists():
                print(f"  ⚠ Protected {slug}: file missing — aborting commit")
                raise RuntimeError(f"Protected profile {slug} file missing")

            with open(full_path) as f:
                file_data = json.load(f)

            if canon(db_data) != canon(file_data):
                print(f"  ⚠ Protected {slug}: file DIFFERS from DB — aborting commit")
                print(f"    Run: python3 tools/creditdoc_guardian.py --protected-only")
                raise RuntimeError(f"Protected profile {slug} drift detected")

    print(f"  ✓ All staged protected profiles match DB")


def main():
    parser = argparse.ArgumentParser(description="CreditDoc Incremental Build")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--export-and-commit", action="store_true",
                       help="Export changes from DB → JSON, git commit changed files")
    group.add_argument("--export-and-push", action="store_true",
                       help="Export, commit, AND push to remote")
    group.add_argument("--export-only", action="store_true",
                       help="Export changes from DB → JSON, no git operations")
    group.add_argument("--export-content", action="store_true",
                       help="Export only content tables (blog, comparisons, etc.)")
    group.add_argument("--full-export", action="store_true",
                       help="Export ALL lenders from DB (full rebuild)")
    group.add_argument("--status", action="store_true",
                       help="Show what would be exported")

    args = parser.parse_args()
    db = CreditDocDB()

    if args.status:
        get_status(db)
        db.close()
        return

    # Record build start
    ts = now_iso()
    db.conn.execute(
        "INSERT INTO builds (started_at, status) VALUES (?, 'running')",
        (ts,)
    )
    build_id = db.conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.conn.commit()

    try:
        if args.full_export:
            print("Full export: ALL lenders from DB...")
            count = db.export_all_lenders()
            content = export_changed_content(db)
            print(f"Exported {count} lenders + content.")
            db.conn.execute(
                "UPDATE builds SET completed_at=?, lenders_exported=?, status='completed' WHERE id=?",
                (now_iso(), count, build_id)
            )
            db.conn.commit()

        elif args.export_content:
            content = export_changed_content(db)
            db.conn.execute(
                "UPDATE builds SET completed_at=?, content_exported=?, status='completed' WHERE id=?",
                (now_iso(), sum(content.values()) if content else 0, build_id)
            )
            db.conn.commit()

        elif args.export_only:
            exported_slugs = export_changed_lenders(db)
            content = export_changed_content(db)
            db.conn.execute(
                "UPDATE builds SET completed_at=?, lenders_exported=?, lenders_changed=?, status='completed' WHERE id=?",
                (now_iso(), len(exported_slugs), len(exported_slugs), build_id)
            )
            db.conn.commit()

        elif args.export_and_commit or args.export_and_push:
            exported_slugs = export_changed_lenders(db)
            content = export_changed_content(db)

            if exported_slugs or content:
                committed = git_commit_changes(
                    exported_slugs, content,
                    push=args.export_and_push
                )
            else:
                committed = False

            db.conn.execute(
                "UPDATE builds SET completed_at=?, lenders_exported=?, lenders_changed=?, status='completed' WHERE id=?",
                (now_iso(), len(exported_slugs), len(exported_slugs), build_id)
            )
            db.conn.commit()

    except Exception as e:
        db.conn.execute(
            "UPDATE builds SET completed_at=?, status='failed' WHERE id=?",
            (now_iso(), build_id)
        )
        db.conn.commit()
        print(f"ERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
