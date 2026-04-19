#!/usr/bin/env python3
"""
Populate brand_slug for approved chains.
Run only for chains flagged HERO_ONLY or DIFFERENTIATE_LEADS in FINAL_ACTION CSV.

Usage:
    python3 scripts/populate_brand_slug.py reports/chain_analysis_2026-04-19.csv --dry-run
    python3 scripts/populate_brand_slug.py reports/chain_analysis_2026-04-19.csv
"""
import argparse
import csv
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "creditdoc.db"
APPROVED_ACTIONS = ("HERO_ONLY", "DIFFERENTIATE_LEADS")


def normalize(name: str) -> str:
    return name.lower().strip()


def slugify(name: str) -> str:
    import re
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s


def main():
    ap = argparse.ArgumentParser(description="Populate brand_slug for approved chains")
    ap.add_argument("csv_path", help="Path to chain_analysis CSV with FINAL_ACTION column")
    ap.add_argument("--dry-run", action="store_true", help="Print what would happen, no writes")
    ap.add_argument("--db", default=str(DB_PATH), help="Path to creditdoc.db")
    args = ap.parse_args()

    csv_path = Path(args.csv_path)
    if not csv_path.exists():
        print(f"ERROR: CSV not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    # Load approved chains from CSV
    approved = {}  # norm_name -> (brand_slug, display_name, action)
    skipped_keep = []
    with open(csv_path) as f:
        for row in csv.DictReader(f):
            action = (row.get("FINAL_ACTION") or row.get("suggested_action") or "").strip()
            if action in APPROVED_ACTIONS:
                norm = normalize(row["chain_name"])
                brand_slug = slugify(row["chain_name"])
                approved[norm] = (brand_slug, row["chain_name"], action)
            else:
                skipped_keep.append(row["chain_name"])

    print(f"Approved chains: {len(approved)}")
    print(f"Skipped (KEEP_AS_IS or unknown): {skipped_keep}")
    print()

    db = sqlite3.connect(args.db)
    db.row_factory = sqlite3.Row

    updates = []  # (brand_slug, slug, display_name, action)
    skipped_protected = []

    for norm, (brand_slug, display_name, action) in approved.items():
        rows = db.execute(
            """SELECT slug, is_protected,
                      json_extract(data, '$.name') AS name,
                      json_extract(data, '$.is_protected') AS data_protected
               FROM lenders
               WHERE LOWER(TRIM(json_extract(data, '$.name'))) = ?
                 AND json_extract(data, '$.processing_status') = 'ready_for_index'""",
            (norm,)
        ).fetchall()

        for r in rows:
            # Skip FA-protected profiles
            is_prot = bool(r["is_protected"]) or r["data_protected"] in (1, "1", True, "true", "True")
            if is_prot:
                skipped_protected.append(r["slug"])
                continue
            updates.append((brand_slug, r["slug"], display_name, action))

    print(f"Would update: {len(updates)} rows across {len(approved)} chains")
    if skipped_protected:
        print(f"Skipped (FA-protected): {len(skipped_protected)} profiles")
    print()

    if args.dry_run:
        print("--- DRY RUN (first 20 rows) ---")
        for brand_slug, slug, display_name, action in updates[:20]:
            print(f"  {slug} <- brand_slug={brand_slug!r}  ({display_name}, {action})")
        if len(updates) > 20:
            print(f"  ... and {len(updates) - 20} more")
        print("\nDry run complete. No changes made.")
        db.close()
        return

    # Apply updates
    count = 0
    for brand_slug, slug, display_name, action in updates:
        db.execute("UPDATE lenders SET brand_slug = ? WHERE slug = ?", (brand_slug, slug))
        count += 1

    db.commit()
    print(f"Committed {count} brand_slug updates.")

    # Verify
    summary = db.execute(
        "SELECT brand_slug, COUNT(*) AS cnt FROM lenders WHERE brand_slug IS NOT NULL "
        "GROUP BY brand_slug ORDER BY cnt DESC LIMIT 10"
    ).fetchall()
    print("\nTop 10 brand_slug populations:")
    for row in summary:
        print(f"  {row['brand_slug']}: {row['cnt']}")

    db.close()


if __name__ == "__main__":
    main()
