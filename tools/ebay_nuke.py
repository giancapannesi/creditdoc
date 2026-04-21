#!/usr/bin/env python3
"""
eBay nuke — Tier 0 + Tier 1 from reports/ebay_cleanup_2026-04-21.md.

For each slug:
  1. Set processing_status='archived' via DB API (transient field, safe).
  2. Delete src/content/lenders/{slug}.json (build excludes archived from getAllLenders).
  3. Delete public/logos/{slug}.{png,jpg,webp,svg} if present.
  4. Emit list of 301 redirect entries for vercel.json (both with and without trailing slash).

Dry-run by default. --apply to execute.
"""
import argparse
import json
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))
from creditdoc_db import CreditDocDB

LENDERS_DIR = PROJECT_DIR / "src" / "content" / "lenders"
LOGOS_DIR = PROJECT_DIR / "public" / "logos"

NUKE_SLUGS = [
    # Tier 0
    "ebay-new-york-office",
    # Tier 1 — website_url = eBay
    "alamo-pawn-jewelry-san-antonio",
    "alamo-pawn-jewelry",
    "aztec-palace-jewelry-loan",
    "darby-pawn-shop",
    "family-jewelry-loan",
    "indy-pawn",
    "la-cienega-jewelry-loan",
    "liberty-pawn-the-jewelry-buyers",
    "lone-star-pawn-shop",
    "mr-bills-collectibles",
    "pawn-shop-watches-etc",
]

REDIRECT_TARGET = "/categories/pawn-shops/"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Actually execute (default: dry-run)")
    args = ap.parse_args()

    db = CreditDocDB()
    report = {"archived": [], "jsons_deleted": [], "logos_deleted": [], "skipped": []}

    for slug in NUKE_SLUGS:
        lender = db.get_lender(slug)
        if not lender:
            report["skipped"].append({"slug": slug, "reason": "not_in_db"})
            continue
        if lender["is_protected"]:
            report["skipped"].append({"slug": slug, "reason": "PROTECTED — refusing"})
            continue

        print(f"\n=== {slug} ===")
        print(f"  current status: {lender['processing_status']}")

        # 1. DB status
        if args.apply:
            db.update_lender_status(slug, "archived", updated_by="ebay_nuke",
                                    reason="website_url or profile is eBay — delisted per founder directive")
            report["archived"].append(slug)
            print(f"  [APPLY] DB status → archived")
        else:
            print(f"  [DRY]   DB status → archived")

        # 2. JSON file
        json_path = LENDERS_DIR / f"{slug}.json"
        if json_path.exists():
            if args.apply:
                json_path.unlink()
                report["jsons_deleted"].append(str(json_path.relative_to(PROJECT_DIR)))
                print(f"  [APPLY] deleted {json_path.relative_to(PROJECT_DIR)}")
            else:
                print(f"  [DRY]   delete {json_path.relative_to(PROJECT_DIR)}")
        else:
            print(f"  (no JSON file)")

        # 3. Logo file (local only — skip if logo_url is external)
        data = lender.get("data", {})
        logo_url = data.get("logo_url", "") or ""
        if logo_url.startswith("/logos/"):
            for ext in ("png", "jpg", "jpeg", "webp", "svg"):
                logo_path = LOGOS_DIR / f"{slug}.{ext}"
                if logo_path.exists():
                    if args.apply:
                        logo_path.unlink()
                        report["logos_deleted"].append(str(logo_path.relative_to(PROJECT_DIR)))
                        print(f"  [APPLY] deleted {logo_path.relative_to(PROJECT_DIR)}")
                    else:
                        print(f"  [DRY]   delete {logo_path.relative_to(PROJECT_DIR)}")
                    break
            else:
                print(f"  (logo_url={logo_url} but no file found)")
        else:
            print(f"  (logo_url is external: {logo_url[:60]})")

    print("\n\n=== REDIRECT ENTRIES TO ADD TO vercel.json ===")
    redirects = []
    for slug in NUKE_SLUGS:
        redirects.append({
            "source": f"/review/{slug}/",
            "destination": REDIRECT_TARGET,
            "permanent": True,
        })
        redirects.append({
            "source": f"/review/{slug}",
            "destination": REDIRECT_TARGET,
            "permanent": True,
        })
    print(json.dumps(redirects, indent=2))

    print("\n\n=== SUMMARY ===")
    print(json.dumps(report, indent=2))

    if not args.apply:
        print("\n(dry-run — nothing changed. Re-run with --apply to execute.)")


if __name__ == "__main__":
    main()
