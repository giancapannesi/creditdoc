#!/usr/bin/env python3
"""Pre-push validation: catch null array fields before they crash the Astro build.

Usage:
    python3 tools/validate_build_data.py          # check all lender JSONs
    python3 tools/validate_build_data.py --fix     # auto-fix nulls to empty arrays

This catches the exact class of error that crashed 3 consecutive Vercel builds
on Apr 17 2026: "Cannot read properties of undefined (reading 'includes')"
at getLendersByCategory -> subcategories was null.
"""

import json
import os
import sys
from pathlib import Path

LENDERS_DIR = Path(__file__).parent.parent / "src" / "content" / "lenders"
ANSWERS_DIR = Path(__file__).parent.parent / "src" / "content" / "answers"

# Fields that MUST be arrays (not null, not undefined, not string)
REQUIRED_ARRAYS = [
    "subcategories", "states_served", "cities_served",
    "best_for", "services", "similar_lenders", "pros", "cons",
]

def validate_lenders(fix=False):
    errors = []
    fixed = 0
    files = sorted(LENDERS_DIR.glob("*.json"))
    for f in files:
        try:
            data = json.loads(f.read_text())
        except json.JSONDecodeError as e:
            errors.append(f"{f.name}: INVALID JSON: {e}")
            continue

        needs_write = False
        for field in REQUIRED_ARRAYS:
            val = data.get(field)
            if not isinstance(val, list):
                if fix:
                    data[field] = [] if val is None else [val] if isinstance(val, str) else []
                    needs_write = True
                    fixed += 1
                else:
                    errors.append(f"{f.name}: {field} is {type(val).__name__} ({val!r}), expected array")

        # Pricing tiers: price must be numeric
        pricing = data.get("pricing")
        if isinstance(pricing, dict):
            for tier_name, tier in pricing.get("tiers", {}).items():
                if isinstance(tier, dict):
                    price = tier.get("price")
                    if price is not None and not isinstance(price, (int, float)):
                        if fix:
                            tier["price"] = 0
                            needs_write = True
                            fixed += 1
                        else:
                            errors.append(f"{f.name}: pricing.tiers.{tier_name}.price is {type(price).__name__} ({price!r}), expected number")

        if needs_write:
            f.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")

    return errors, fixed, len(files)

def validate_answers():
    errors = []
    files = sorted(ANSWERS_DIR.glob("*.json"))
    for f in files:
        try:
            data = json.loads(f.read_text())
        except json.JSONDecodeError as e:
            errors.append(f"answers/{f.name}: INVALID JSON: {e}")
            continue

        if not data.get("slug"):
            errors.append(f"answers/{f.name}: missing slug")
        if not isinstance(data.get("sections"), list):
            errors.append(f"answers/{f.name}: sections is not an array")

    return errors, len(files)

if __name__ == "__main__":
    fix = "--fix" in sys.argv

    print("Validating lender JSONs...")
    l_errors, l_fixed, l_total = validate_lenders(fix=fix)

    print("Validating answer JSONs...")
    a_errors, a_total = validate_answers()

    all_errors = l_errors + a_errors

    print(f"\nLenders: {l_total} files checked")
    print(f"Answers: {a_total} files checked")

    if fix and l_fixed:
        print(f"Fixed: {l_fixed} field(s) across lender files")

    if all_errors:
        print(f"\nERRORS ({len(all_errors)}):")
        for e in all_errors[:50]:
            print(f"  - {e}")
        if len(all_errors) > 50:
            print(f"  ... and {len(all_errors) - 50} more")
        sys.exit(1)
    else:
        print("\nAll clear - build should succeed.")
        sys.exit(0)
