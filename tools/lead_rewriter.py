#!/usr/bin/env python3
"""
lead_rewriter.py — Rewrite chain location page lead paragraphs to be location-first.

Reads DB rows where brand_slug IS NOT NULL. For each row:
  - Skip if is_protected=1
  - Skip if description_short already leads with address/location pattern
  - Build a prompt for Claude Haiku via CLI, validate output, write to DB
  - Cache responses to avoid re-spending on re-runs

Usage:
  python3 tools/lead_rewriter.py --list-chains
  python3 tools/lead_rewriter.py --chain "western union" --dry-run
  python3 tools/lead_rewriter.py --chain "western union" --dry-run --live
  python3 tools/lead_rewriter.py --chain "western union" --apply
  python3 tools/lead_rewriter.py --chain "western union" --limit 5
"""

import argparse
import hashlib
import json
import random
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ─── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
CACHE_FILE = PROJECT_DIR / "data" / "lead_rewriter_cache.json"

# Add tools dir so we can import creditdoc_db
sys.path.insert(0, str(SCRIPT_DIR))
from creditdoc_db import CreditDocDB

# ─── Constants ─────────────────────────────────────────────────────────────────
HYPE_WORDS = [
    "best", "trusted", "top-rated", "leading", "premier",
    "convenient location", "excellent", "satisfied customers",
    "top rated", "reliable", "number one", "#1",
]

ALREADY_LOCATION_LED_PATTERNS = [
    r"^\d",                         # starts with digit (street address)
    r"^At ",                        # "At 123 Main St"
    r"^Located at ",                # "Located at ..."
    r"^The [A-Z][a-z]+ ",          # "The Albuquerque ..."
]

# The prompt template from the plan — used verbatim
PROMPT_TEMPLATE = """You're rewriting the first paragraph of a business directory page so it leads with location-specific information instead of brand boilerplate. This is for a US consumer-finance directory page.

LOCATION DATA:
- Brand: {name}
- Address: {address}
- City: {city}, {state_abbr}
- Phone: {phone}
(Service category hint — do NOT quote or reference in output: {category_label})

CURRENT FIRST PARAGRAPH (to be replaced):
{description_short}

RULES:
1. Lead with the address or city — e.g. "At {address}, {city}..." or "The {city}, {state_abbr} location of..."
2. Include the phone number once, written naturally.
3. Mention the brand name ({name}) once — but NOT in the first five words.
4. Keep 2-3 sentences, maximum 280 characters total.
5. Use specific, verifiable facts only. Do NOT invent hours, ratings, staff names, review counts, or local details not present in the location data above.
6. Do NOT use marketing hype: no "best", "trusted", "top", "leading", "premier", "reliable", "convenient" (it's implied).
7. Do NOT make any factual claim about WHAT the business is (do not say "operates as", "provides X services", "is a credit union/bank/pawn shop"). Describe only concrete location attributes — address, city, phone, hours if provided. If you have no concrete local facts beyond address + phone, output: NO_CHANGE
8. If the only facts you have are address + phone, write a factual sentence using only those. Do not invent.
9. If the current description is already location-led, output exactly: NO_CHANGE

Output format: just the new paragraph. No preamble. No quotes. No "Here is the new version:" wrapper."""

RETRY_SUFFIX = "\n\nYour previous output failed validation: {reason}. Retry following the rules exactly."


# ─── Address Parsing ──────────────────────────────────────────────────────────

def parse_address(address_str):
    """
    Parse city and state from a US address string.
    Expected format: "123 Main St, CityName, ST 12345"
    Returns (street, city, state_abbr) or best effort.
    """
    if not address_str:
        return "", "", ""

    parts = [p.strip() for p in address_str.split(",")]

    if len(parts) >= 3:
        street = ", ".join(parts[:-2]).strip()
        city = parts[-2].strip()
        # Last part: "ST 12345" or "ST"
        last = parts[-1].strip()
        state_match = re.match(r'^([A-Z]{2})\s*\d*$', last)
        state_abbr = state_match.group(1) if state_match else last[:2]
        return street, city, state_abbr
    elif len(parts) == 2:
        street = parts[0].strip()
        last = parts[1].strip()
        state_match = re.match(r'^([A-Z]{2})\s*\d*$', last)
        state_abbr = state_match.group(1) if state_match else ""
        return street, "", state_abbr
    else:
        return address_str, "", ""


def get_category_label(category_slug):
    """Convert category slug to human-readable label."""
    labels = {
        "check-cashing": "check cashing and money transfer",
        "credit-repair": "credit repair",
        "personal-loans": "personal loans",
        "auto-loans": "auto loans",
        "mortgage": "mortgage",
        "payday-loans": "payday loans",
        "title-loans": "title loans",
        "pawn-shops": "pawn services",
        "credit-unions": "credit union",
        "banks": "banking",
        "debt-consolidation": "debt consolidation",
        "student-loans": "student loans",
        "business-loans": "business loans",
    }
    return labels.get(category_slug, category_slug.replace("-", " "))


# ─── Already-Location-Led Check ───────────────────────────────────────────────

def is_already_location_led(description_short, city=""):
    """Return True if description_short already leads with location."""
    if not description_short:
        return False

    text = description_short.strip()

    for pattern in ALREADY_LOCATION_LED_PATTERNS:
        if re.match(pattern, text):
            return True

    # Also catch "The {city}" pattern
    if city and text.startswith(f"The {city}"):
        return True

    return False


# ─── Cache ─────────────────────────────────────────────────────────────────────

def load_cache():
    """Load the response cache from disk."""
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_cache(cache):
    """Write cache to disk."""
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


def cache_key(slug, description_short):
    """Generate a stable cache key from slug + input hash."""
    content = f"{slug}:{description_short}"
    return hashlib.sha256(content.encode()).hexdigest()[:24]


# ─── Validation ───────────────────────────────────────────────────────────────

def validate_output(text, name, phone, city, address):
    """
    Validate the Claude output against quality rules.
    Returns (ok: bool, reason: str).
    """
    if not text or not text.strip():
        return False, "output is empty"

    text = text.strip()

    # NO_CHANGE handling
    if text == "NO_CHANGE":
        return True, "NO_CHANGE"

    # If NO_CHANGE appears mixed with other text
    if "NO_CHANGE" in text:
        return False, "NO_CHANGE mixed into output text"

    # Length check
    if len(text) > 280:
        return False, f"too long ({len(text)} chars, max 280)"
    if len(text) < 80:
        return False, f"too short ({len(text)} chars, min 80)"

    # Must start with location pattern
    starts_with_location = any([
        re.match(r"^\d", text),          # digit = address number
        text.startswith("At "),
        text.startswith("Located at "),
        city and text.startswith(f"The {city}"),
        city and text.startswith(city),
    ])
    if not starts_with_location:
        return False, f"does not start with location pattern (starts with: '{text[:40]}')"

    # Must contain phone number (normalize both to digits for comparison)
    if phone:
        phone_digits = re.sub(r'\D', '', phone)
        output_digits = re.sub(r'\D', '', text)
        if phone_digits and phone_digits not in output_digits:
            return False, f"phone number missing (expected digits: {phone_digits})"

    # Must contain brand name exactly once
    if name:
        count = text.lower().count(name.lower())
        if count == 0:
            return False, f"brand name '{name}' not present"
        if count > 1:
            return False, f"brand name '{name}' appears {count} times (must be exactly once)"

    # Hype word check
    text_lower = text.lower()
    for hype in HYPE_WORDS:
        if hype in text_lower:
            return False, f"hype word detected: '{hype}'"

    return True, "ok"


# ─── Claude CLI Call ──────────────────────────────────────────────────────────

def call_claude(prompt, model="claude-haiku-4-5"):
    """
    Call Claude CLI with the given prompt.
    Returns (output_text, error_str).
    """
    try:
        result = subprocess.run(
            ["claude", "--model", model, "--print", prompt],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            return None, f"CLI error (rc={result.returncode}): {result.stderr[:200]}"
        return result.stdout.strip(), None
    except subprocess.TimeoutExpired:
        return None, "CLI timeout after 60s"
    except Exception as e:
        return None, f"CLI exception: {e}"


# ─── Row Processor ────────────────────────────────────────────────────────────

def build_prompt(row_data, name, address, city, state_abbr, phone, category_label):
    """Build the prompt for a single row."""
    return PROMPT_TEMPLATE.format(
        name=name,
        address=address,
        city=city,
        state_abbr=state_abbr,
        phone=phone,
        category_label=category_label,
        description_short=row_data.get("description_short", ""),
    )


def process_row(slug, row_data, is_protected, cache, live=False, verbose=True):
    """
    Process a single lender row.

    Returns dict with keys:
      action: "write" | "skip" | "already_led" | "no_change" | "protected" | "failed" | "cached"
      new_text: str or None
      reason: str
      old_text: str
    """
    old_text = row_data.get("description_short", "")

    # Skip protected
    if is_protected:
        return {"action": "protected", "new_text": None, "reason": "FA-protected profile", "old_text": old_text}

    # Parse location from address
    address = row_data.get("address", "")
    name = row_data.get("name", "")
    phone = row_data.get("phone", "")
    category = row_data.get("category", "")
    category_label = get_category_label(category)

    street, city, state_abbr = parse_address(address)

    # Skip if already location-led
    if is_already_location_led(old_text, city):
        return {"action": "already_led", "new_text": None, "reason": "description already location-led", "old_text": old_text}

    # Skip if no description to rewrite
    if not old_text or len(old_text.strip()) < 20:
        return {"action": "skip", "new_text": None, "reason": "description too short or empty", "old_text": old_text}

    # Check cache
    ck = cache_key(slug, old_text)
    if ck in cache:
        cached = cache[ck]
        if cached.get("validation") == "ok" and cached.get("output"):
            return {
                "action": "cached",
                "new_text": cached["output"],
                "reason": "cache hit",
                "old_text": old_text,
            }
        elif cached.get("validation") == "skip":
            return {
                "action": "skip",
                "new_text": None,
                "reason": f"cached skip: {cached.get('skip_reason', 'unknown')}",
                "old_text": old_text,
            }

    # Name/description mismatch detection — catches corrupt rows like WU/Western Sun
    # If the brand name doesn't appear anywhere in description_short, the row likely has
    # pre-existing data corruption and needs manual curation, not an automated rewrite.
    if name and old_text and name.lower() not in old_text.lower():
        print(f"  [WARN] name/desc mismatch: '{name}' not found in description_short. Skipping (needs manual curation).")
        return {"action": "skip", "new_text": None, "reason": f"name/desc mismatch: '{name}' not in description_short", "old_text": old_text}

    # If not live mode, can't call Claude
    if not live:
        return {"action": "skip", "new_text": None, "reason": "dry-run (no --live)", "old_text": old_text}

    # Build and send prompt
    prompt = build_prompt(row_data, name, address, city, state_abbr, phone, category_label)

    output, err = call_claude(prompt)
    if err:
        cache[ck] = {"output": None, "validation": "failed", "timestamp": _now(), "skip_reason": err}
        return {"action": "failed", "new_text": None, "reason": f"CLI error: {err}", "old_text": old_text}

    valid, reason = validate_output(output, name, phone, city, address)

    # Retry once on failure
    if not valid:
        retry_prompt = prompt + RETRY_SUFFIX.format(reason=reason)
        if verbose:
            print(f"  [retry] validation failed: {reason}")
        output2, err2 = call_claude(retry_prompt)
        if not err2:
            valid2, reason2 = validate_output(output2, name, phone, city, address)
            if valid2:
                output = output2
                valid = True
                reason = reason2
            else:
                reason = f"retry also failed: {reason2}"
        else:
            reason = f"retry CLI error: {err2}"

    if not valid:
        cache[ck] = {
            "output": output,
            "validation": "failed",
            "timestamp": _now(),
            "skip_reason": reason,
        }
        return {"action": "failed", "new_text": None, "reason": reason, "old_text": old_text}

    if output == "NO_CHANGE":
        cache[ck] = {
            "output": None,
            "validation": "skip",
            "timestamp": _now(),
            "skip_reason": "model returned NO_CHANGE",
        }
        return {"action": "no_change", "new_text": None, "reason": "model returned NO_CHANGE", "old_text": old_text}

    # Success
    cache[ck] = {
        "output": output,
        "validation": "ok",
        "timestamp": _now(),
    }
    return {"action": "write", "new_text": output, "reason": "ok", "old_text": old_text}


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ─── Main Commands ─────────────────────────────────────────────────────────────

def cmd_list_chains(db):
    """List all brand_slug values and their row counts."""
    rows = db.conn.execute(
        "SELECT brand_slug, COUNT(*) as cnt FROM lenders WHERE brand_slug IS NOT NULL GROUP BY brand_slug ORDER BY cnt DESC"
    ).fetchall()
    print(f"{'CHAIN SLUG':<40} {'COUNT':>6}")
    print("-" * 50)
    for r in rows:
        print(f"{r['brand_slug']:<40} {r['cnt']:>6}")
    print(f"\nTotal chains: {len(rows)}")


def get_chain_rows(db, chain_slug, limit=None):
    """Fetch all lender rows for a given brand_slug (normalized)."""
    # Normalize the chain name to slug
    chain_slug_norm = chain_slug.lower().strip().replace(" ", "-").replace("/", "-")

    sql = """
        SELECT slug, data, is_protected, brand_slug
        FROM lenders
        WHERE brand_slug = ?
        ORDER BY slug
    """
    params = [chain_slug_norm]
    if limit:
        sql += " LIMIT ?"
        params.append(limit)

    rows = db.conn.execute(sql, params).fetchall()
    return rows


def cmd_dry_run(db, chain, limit, live):
    """Dry run: print plan (and optionally call Claude), no DB writes."""
    rows = get_chain_rows(db, chain, limit)

    if not rows:
        print(f"ERROR: No rows found for chain '{chain}' (tried slug: {chain.lower().strip().replace(' ','-')})")
        return

    print(f"\n{'='*60}")
    print(f"DRY RUN: chain='{chain}' | rows={len(rows)} | live={live}")
    print(f"{'='*60}\n")

    cache = load_cache()
    start = time.time()

    # Counters
    counts = {"write": 0, "skip": 0, "already_led": 0, "no_change": 0,
               "protected": 0, "failed": 0, "cached": 0}

    for i, row in enumerate(rows, 1):
        slug = row["slug"]
        data = json.loads(row["data"])
        is_prot = bool(row["is_protected"])

        result = process_row(slug, data, is_prot, cache, live=live, verbose=True)
        counts[result["action"]] = counts.get(result["action"], 0) + 1

        if live:
            # Print before/after
            print(f"[{i}/{len(rows)}] {slug}")
            print(f"  action   : {result['action']}")
            print(f"  BEFORE   : {result['old_text'][:120]}...")
            if result["new_text"]:
                print(f"  AFTER    : {result['new_text']}")
            print(f"  reason   : {result['reason']}")
            print()
            if result["action"] in ("write", "failed"):
                time.sleep(2)  # rate limit buffer
        else:
            print(f"  [{i}/{len(rows)}] {slug} -> would {result['action']}: {result['reason']}")

        # Save cache every 25 rows
        if i % 25 == 0:
            save_cache(cache)

    save_cache(cache)
    elapsed = time.time() - start

    print(f"\n{'='*60}")
    print(f"DRY RUN SUMMARY (no DB writes)")
    print(f"  Total rows     : {len(rows)}")
    print(f"  Would write    : {counts.get('write',0) + counts.get('cached',0)}")
    print(f"  Already led    : {counts.get('already_led',0)}")
    print(f"  No change      : {counts.get('no_change',0)}")
    print(f"  Skip (other)   : {counts.get('skip',0)}")
    print(f"  Protected      : {counts.get('protected',0)}")
    print(f"  Failed valid.  : {counts.get('failed',0)}")
    print(f"  Runtime        : {elapsed:.1f}s")
    print(f"{'='*60}")


def cmd_apply(db, chain, limit, today_str):
    """Apply mode: call Claude, validate, write to DB."""
    rows = get_chain_rows(db, chain, limit)

    if not rows:
        print(f"ERROR: No rows found for chain '{chain}'")
        return

    chain_slug_norm = chain.lower().strip().replace(" ", "-").replace("/", "-")
    batch_tag = f"{chain_slug_norm}_{today_str}"

    print(f"\n{'='*60}")
    print(f"APPLY: chain='{chain}' | rows={len(rows)} | batch_tag={batch_tag}")
    print(f"{'='*60}\n")

    cache = load_cache()
    start = time.time()

    # Counters + tracking
    counts = {"write": 0, "skip": 0, "already_led": 0, "no_change": 0,
              "protected": 0, "failed": 0, "cached": 0}
    written_rows = []  # list of (slug, old_text, new_text)
    failed_rows = []   # list of (slug, reason)

    for i, row in enumerate(rows, 1):
        slug = row["slug"]
        data = json.loads(row["data"])
        is_prot = bool(row["is_protected"])

        result = process_row(slug, data, is_prot, cache, live=True, verbose=True)
        action = result["action"]
        counts[action] = counts.get(action, 0) + 1

        print(f"Processing {i}/{len(rows)}: {slug} — validation: {action}")

        if action in ("write", "cached") and result["new_text"]:
            # Write to DB
            try:
                db_result = db.update_lender(
                    slug,
                    {"description_short": result["new_text"]},
                    updated_by="lead_rewriter",
                    reason=f"batch_tag:{batch_tag} | location-first rewrite",
                    force=True,  # description_short is a persistent field — needs force=True
                )
                written_rows.append((slug, result["old_text"], result["new_text"]))
                counts["write"] = counts.get("write", 0) + (1 if action == "cached" else 0)
                if action == "cached":
                    counts["cached"] -= 1  # don't double count
            except Exception as e:
                print(f"  ERROR writing {slug}: {e}")
                failed_rows.append((slug, f"DB write error: {e}"))
                counts["failed"] = counts.get("failed", 0) + 1
                counts[action] -= 1
        elif action == "failed":
            failed_rows.append((slug, result["reason"]))

        # Rate limit buffer for live calls
        if action not in ("already_led", "protected", "skip", "cached"):
            time.sleep(2)

        # Save cache every 25 rows
        if i % 25 == 0:
            save_cache(cache)

    save_cache(cache)
    elapsed = time.time() - start

    # Compute total written
    total_written = len(written_rows)
    total_failed = len(failed_rows)
    fail_rate = total_failed / len(rows) if rows else 0

    # Final summary
    print(f"\n{'='*60}")
    print(f"APPLY SUMMARY")
    print(f"  Total rows     : {len(rows)}")
    print(f"  Written to DB  : {total_written}")
    print(f"  Already led    : {counts.get('already_led',0)}")
    print(f"  No change      : {counts.get('no_change',0)}")
    print(f"  Skip (other)   : {counts.get('skip',0)}")
    print(f"  Protected      : {counts.get('protected',0)}")
    print(f"  Validation fail: {total_failed}")
    print(f"  Fail rate      : {fail_rate:.1%}")
    print(f"  Batch tag      : {batch_tag}")
    print(f"  Runtime        : {elapsed:.1f}s")

    if total_failed > 0:
        print(f"\nFailed rows:")
        for slug, reason in failed_rows:
            print(f"  {slug}: {reason}")

    if fail_rate > 0.15:
        print(f"\nWARNING: Failure rate {fail_rate:.1%} exceeds 15% threshold.")
        print("Do NOT commit. Investigate prompt quality and retry.")
        return None

    if not written_rows:
        print("\nNo rows were written. Nothing to commit.")
        return None

    # Print 3 random before/after samples
    sample_rows = random.sample(written_rows, min(3, len(written_rows)))
    print(f"\n{'='*60}")
    print("RANDOM SAMPLES (for quality review):")
    print(f"{'='*60}")
    for j, (slug, old, new) in enumerate(sample_rows, 1):
        print(f"\nSample {j}: {slug}")
        print(f"  BEFORE: {old}")
        print(f"  AFTER : {new}")

    return written_rows, batch_tag


# ─── Entry Point ──────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="Rewrite chain location page lead paragraphs to be location-first."
    )
    ap.add_argument("--chain", help="Chain name (e.g. 'western union')")
    ap.add_argument("--dry-run", action="store_true", help="Print plan only, no DB writes")
    ap.add_argument("--live", action="store_true", help="Make actual CLI calls (use with --dry-run for preview)")
    ap.add_argument("--apply", action="store_true", help="Call Claude + write to DB")
    ap.add_argument("--limit", type=int, help="Process only first N rows (test mode)")
    ap.add_argument("--list-chains", action="store_true", help="List all brand_slug values + counts")
    args = ap.parse_args()

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    with CreditDocDB(PROJECT_DIR / "data" / "creditdoc.db") as db:
        if args.list_chains:
            cmd_list_chains(db)
            return

        if not args.chain:
            ap.print_help()
            sys.exit(1)

        if args.dry_run:
            cmd_dry_run(db, args.chain, args.limit, live=args.live)
        elif args.apply:
            result = cmd_apply(db, args.chain, args.limit, today_str)
            if result is None:
                sys.exit(1)
        else:
            print("Specify --dry-run or --apply.")
            ap.print_help()
            sys.exit(1)


if __name__ == "__main__":
    main()
