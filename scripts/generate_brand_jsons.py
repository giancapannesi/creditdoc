#!/usr/bin/env python3
"""
Generate per-brand copy JSONs for all 57 approved chains.
Uses claude CLI (claude-haiku-4-5) for summary_long + FAQs.
Run sequentially with 2s sleep between calls.

Usage:
    python3 scripts/generate_brand_jsons.py
    python3 scripts/generate_brand_jsons.py --brand western-union  # single brand
"""
import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "creditdoc.db"
BRANDS_DIR = Path(__file__).parent.parent / "src" / "content" / "brands"

# Known brand data (display names, websites, parent companies)
# Factual, no marketing hype. No guessing on websites.
BRAND_META = {
    "moneygram": {
        "display_name": "MoneyGram",
        "official_website": "https://www.moneygram.com",
        "parent_company": "Madison Dearborn Partners (private, as of 2023)",
    },
    "western-union": {
        "display_name": "Western Union",
        "official_website": "https://www.westernunion.com",
        "parent_company": None,
    },
    "ace-cash-express": {
        "display_name": "ACE Cash Express",
        "official_website": "https://www.acecashexpress.com",
        "parent_company": "Populus Financial Group",
    },
    "advance-america": {
        "display_name": "Advance America",
        "official_website": "https://www.advanceamerica.net",
        "parent_company": "Grupo Elektra",
    },
    "cash-america-pawn": {
        "display_name": "Cash America Pawn",
        "official_website": "https://www.cashamerica.com",
        "parent_company": "FirstCash Holdings",
    },
    "titlemax-title-loans": {
        "display_name": "TitleMax Title Loans",
        "official_website": "https://www.titlemax.com",
        "parent_company": "TMX Finance",
    },
    "pls-check-cashers": {
        "display_name": "PLS Check Cashers",
        "official_website": "https://www.plsfinancial.com",
        "parent_company": "PLS Financial Services",
    },
    "montana-capital-car-title-loans": {
        "display_name": "Montana Capital Car Title Loans",
        "official_website": "https://www.montanacapital.com",
        "parent_company": None,
    },
    "western-union-money-order-only": {
        "display_name": "Western Union Money Order Only",
        "official_website": "https://www.westernunion.com",
        "parent_company": "Western Union",
    },
    "5-star-car-title-loans": {
        "display_name": "5 Star Car Title Loans",
        "official_website": "https://www.5starcartitleloans.com",
        "parent_company": None,
    },
    "ezpawn": {
        "display_name": "EZPawn",
        "official_website": "https://www.ezpawn.com",
        "parent_company": "EZCORP",
    },
    "speedy-cash": {
        "display_name": "Speedy Cash",
        "official_website": "https://www.speedycash.com",
        "parent_company": "Curo Financial Technologies",
    },
    "us-cash-advance": {
        "display_name": "US Cash Advance",
        "official_website": None,
        "parent_company": None,
    },
    "loan-for-any-purpose": {
        "display_name": "Loan For Any Purpose",
        "official_website": None,
        "parent_company": None,
    },
    "check-into-cash": {
        "display_name": "Check Into Cash",
        "official_website": "https://www.checkintocash.com",
        "parent_company": None,
    },
    "checksmart": {
        "display_name": "Checksmart",
        "official_website": "https://www.checksmart.com",
        "parent_company": "Community Choice Financial",
    },
    "superb-cash-advance": {
        "display_name": "Superb Cash Advance",
        "official_website": None,
        "parent_company": None,
    },
    "first-state-bank": {
        "display_name": "First State Bank",
        "official_website": None,
        "parent_company": None,
    },
    "first-cash-pawn": {
        "display_name": "First Cash Pawn",
        "official_website": "https://www.firstcash.com",
        "parent_company": "FirstCash Holdings",
    },
    "check-n-go": {
        "display_name": "Check 'n Go",
        "official_website": "https://www.checkngo.com",
        "parent_company": None,
    },
    "value-pawn-jewelry": {
        "display_name": "Value Pawn & Jewelry",
        "official_website": None,
        "parent_company": None,
    },
    "loanmax-title-loans": {
        "display_name": "LoanMax Title Loans",
        "official_website": "https://www.loanmax.com",
        "parent_company": "Community Loans of America",
    },
    "titlemax-title-pawns": {
        "display_name": "TitleMax Title Pawns",
        "official_website": "https://www.titlemax.com",
        "parent_company": "TMX Finance",
    },
    "swift-title-loans": {
        "display_name": "Swift Title Loans",
        "official_website": None,
        "parent_company": None,
    },
    "primo-personal-loans": {
        "display_name": "Primo Personal Loans",
        "official_website": None,
        "parent_company": None,
    },
    "lendnation": {
        "display_name": "LendNation",
        "official_website": "https://www.lendnation.com",
        "parent_company": None,
    },
    "california-check-cashing-stores": {
        "display_name": "California Check Cashing Stores",
        "official_website": None,
        "parent_company": "Community Choice Financial",
    },
    "farmers-state-bank": {
        "display_name": "Farmers State Bank",
        "official_website": None,
        "parent_company": None,
    },
    "dolex-dollar-express": {
        "display_name": "Dolex Dollar Express",
        "official_website": "https://www.dolex.com",
        "parent_company": None,
    },
    "loanstar-title-loans": {
        "display_name": "LoanStar Title Loans",
        "official_website": "https://www.loanstartitleloans.com",
        "parent_company": None,
    },
    "sam-check-cashing-machine": {
        "display_name": "Sam Check Cashing Machine",
        "official_website": None,
        "parent_company": None,
    },
    "peoples-bank": {
        "display_name": "Peoples Bank",
        "official_website": None,
        "parent_company": None,
    },
    "payday-loans-cash": {
        "display_name": "Payday Loans Cash",
        "official_website": None,
        "parent_company": None,
    },
    "pawn1st": {
        "display_name": "Pawn1st",
        "official_website": None,
        "parent_company": None,
    },
    "la-familia-pawn-and-jewelry": {
        "display_name": "La Familia Pawn and Jewelry",
        "official_website": None,
        "parent_company": None,
    },
    "instaloan": {
        "display_name": "InstaLoan",
        "official_website": "https://www.instaloan.com",
        "parent_company": "TMX Finance",
    },
    "citizens-state-bank": {
        "display_name": "Citizens State Bank",
        "official_website": None,
        "parent_company": None,
    },
    "superpawn": {
        "display_name": "SuperPawn",
        "official_website": "https://www.superpawn.com",
        "parent_company": "EZCORP",
    },
    "onemain-financial": {
        "display_name": "OneMain Financial",
        "official_website": "https://www.onemainfinancial.com",
        "parent_company": None,
    },
    "nccl-no-credit-check-loans": {
        "display_name": "NCCL No Credit Check Loans",
        "official_website": None,
        "parent_company": None,
    },
    "allied-cash-advance": {
        "display_name": "Allied Cash Advance",
        "official_website": "https://www.alliedcashadvance.com",
        "parent_company": "Community Choice Financial",
    },
    "ria-money-transfer": {
        "display_name": "Ria Money Transfer",
        "official_website": "https://www.riamoneytransfer.com",
        "parent_company": "Euronet Worldwide",
    },
    "farmers-and-merchants-bank": {
        "display_name": "Farmers and Merchants Bank",
        "official_website": None,
        "parent_company": None,
    },
    "community-state-bank": {
        "display_name": "Community State Bank",
        "official_website": None,
        "parent_company": None,
    },
    "texas-car-title-and-payday-loan-services-inc": {
        "display_name": "Texas Car Title and Payday Loan Services",
        "official_website": None,
        "parent_company": None,
    },
    "easy-payday-loans": {
        "display_name": "Easy Payday Loans",
        "official_website": None,
        "parent_company": None,
    },
    "chase-bank": {
        "display_name": "Chase Bank",
        "official_website": "https://www.chase.com",
        "parent_company": "JPMorgan Chase & Co.",
    },
    "bank-of-america-financial-center": {
        "display_name": "Bank of America Financial Center",
        "official_website": "https://www.bankofamerica.com",
        "parent_company": "Bank of America Corporation",
    },
    "security-state-bank": {
        "display_name": "Security State Bank",
        "official_website": None,
        "parent_company": None,
    },
    "orlandi-valuta": {
        "display_name": "Orlandi Valuta",
        "official_website": None,
        "parent_company": "Western Union",
    },
    "first-community-bank": {
        "display_name": "First Community Bank",
        "official_website": None,
        "parent_company": None,
    },
    "first-bank": {
        "display_name": "First Bank",
        "official_website": None,
        "parent_company": None,
    },
    "consumer-credit-counseling-services": {
        "display_name": "Consumer Credit Counseling Services",
        "official_website": None,
        "parent_company": None,
    },
    "community-bank": {
        "display_name": "Community Bank",
        "official_website": None,
        "parent_company": None,
    },
    "cash-store": {
        "display_name": "Cash Store",
        "official_website": "https://www.cashstore.com",
        "parent_company": None,
    },
    "world-finance": {
        "display_name": "World Finance",
        "official_website": "https://www.loansbyworld.com",
        "parent_company": "World Acceptance Corporation",
    },
    "oportun": {
        "display_name": "Oportun",
        "official_website": "https://oportun.com",
        "parent_company": None,
    },
}


def get_brand_db_data(db, brand_slug):
    """Fetch brand stats from DB."""
    rows = db.execute(
        """SELECT COUNT(*) as cnt,
                  json_extract(data, '$.category') as category,
                  GROUP_CONCAT(DISTINCT json_extract(data, '$.company_info.state')) as states
           FROM lenders
           WHERE brand_slug = ?
             AND json_extract(data, '$.processing_status') = 'ready_for_index'""",
        (brand_slug,)
    ).fetchone()
    return rows


def call_claude(prompt):
    """Call claude CLI with a prompt. Returns text output."""
    try:
        result = subprocess.run(
            ["claude", "--model", "claude-haiku-4-5", "--print", prompt],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            print(f"  WARNING: claude returned code {result.returncode}: {result.stderr[:200]}")
            return None
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        print("  WARNING: claude call timed out")
        return None
    except FileNotFoundError:
        print("  ERROR: claude CLI not found in PATH")
        return None


def generate_brand_json(brand_slug, db_row, meta):
    """Generate brand JSON using Claude CLI for summary_long + FAQs."""
    location_count = db_row["cnt"]
    category = db_row["category"] or "financial-services"
    states_raw = db_row["states"] or ""
    # Top 3 states by frequency (states_raw is comma-separated, may have dupes)
    state_list = [s.strip() for s in states_raw.split(",") if s.strip()]
    state_counts = {}
    for s in state_list:
        state_counts[s] = state_counts.get(s, 0) + 1
    top_states = sorted(state_counts, key=lambda x: -state_counts[x])[:3]

    display_name = meta["display_name"]
    parent_company = meta.get("parent_company")
    official_website = meta.get("official_website")

    parent_str = f"owned by {parent_company}" if parent_company else "an independent company"
    top_states_str = ", ".join(top_states) if top_states else "multiple US states"

    prompt = f"""You are writing factual, Wikipedia-tone content for a financial directory.
Write a 3-paragraph brand overview for {display_name}.

Context:
- Brand: {display_name}
- Category: {category.replace('-', ' ')}
- US locations: {location_count}
- Top states: {top_states_str}
- Corporate: {parent_str}
- Official website: {official_website or 'not verified'}

Rules:
1. Wikipedia tone — factual, neutral, no marketing language.
2. No words: best, trusted, premier, leading, top, excellent, exceptional, outstanding, superior, amazing.
3. Do not invent facts. If you don't know something, omit it.
4. Paragraph 1: What this company does and who it serves.
5. Paragraph 2: Geographic footprint and any notable products/services.
6. Paragraph 3: Consumer considerations — what to know before using (fees, regulations, alternatives).
7. Each paragraph is 2-3 sentences. Total: ~150 words.
8. Then write 3 FAQs in this exact format:
   Q: [question about {display_name}]
   A: [factual answer, 1-2 sentences]
   Q: [question about finding a location]
   A: [factual answer]
   Q: [question about safety, fees, or regulations]
   A: [factual answer]

Output format:
SUMMARY:
[3 paragraphs]

FAQs:
Q: ...
A: ...
Q: ...
A: ...
Q: ...
A: ...
"""

    output = call_claude(prompt)
    if not output:
        # Fallback: minimal content
        summary_long = f"{display_name} is a {category.replace('-', ' ')} provider with {location_count} locations across the US. The company operates in {len(state_list)} states including {top_states_str}. Consumers should review terms and fees before using this service."
        faqs = [
            {"q": f"How do I find a nearby {display_name} location?", "a": f"Use the location finder on this page to browse all {location_count} {display_name} branches by state."},
            {"q": f"What does {display_name} offer?", "a": f"{display_name} provides {category.replace('-', ' ')} services at branch locations."},
            {"q": f"Is {display_name} regulated?", "a": "Financial service providers are regulated at the state level. Check your state regulator for specific licensing information."},
        ]
        return summary_long, faqs

    # Parse output
    summary_long = ""
    faqs = []

    # Split on SUMMARY: and FAQs:
    summary_match = re.search(r"SUMMARY:\s*(.*?)(?=FAQs:|$)", output, re.DOTALL | re.IGNORECASE)
    faq_match = re.search(r"FAQs:\s*(.*?)$", output, re.DOTALL | re.IGNORECASE)

    if summary_match:
        summary_long = summary_match.group(1).strip()
    else:
        # Try to grab first 3 paragraphs
        lines = output.split("\n\n")
        non_faq = [l for l in lines if not l.strip().startswith("Q:") and not l.strip().startswith("FAQs")]
        summary_long = "\n\n".join(non_faq[:3]).strip()

    if faq_match:
        faq_text = faq_match.group(1).strip()
        q_pattern = re.findall(r"Q:\s*(.+?)\nA:\s*(.+?)(?=\nQ:|\Z)", faq_text, re.DOTALL)
        for q, a in q_pattern:
            faqs.append({"q": q.strip(), "a": a.strip()})

    # Fallback FAQs if parsing failed
    if not faqs:
        faqs = [
            {"q": f"How do I find a nearby {display_name} location?", "a": f"Use the location finder on this page to browse all {location_count} {display_name} branches by state."},
            {"q": f"What does {display_name} offer?", "a": f"{display_name} provides {category.replace('-', ' ')} services at branch locations."},
            {"q": f"Is {display_name} regulated?", "a": "Financial service providers are regulated at the state level. Check your state regulator for specific licensing information."},
        ]

    if not summary_long:
        summary_long = f"{display_name} is a {category.replace('-', ' ')} provider with {location_count} locations across the US, operating primarily in {top_states_str}. The company provides services at physical branch locations. Consumers should review terms and fees before using this service."

    return summary_long, faqs


def get_summary_short(display_name, category, location_count):
    cat_label = category.replace("-", " ")
    return f"{display_name} is a {cat_label} provider with {location_count} locations across the US."


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brand", help="Generate for a single brand slug only")
    args = ap.parse_args()

    BRANDS_DIR.mkdir(parents=True, exist_ok=True)

    db = sqlite3.connect(str(DB_PATH))
    db.row_factory = sqlite3.Row

    # Get all brand slugs from DB
    rows = db.execute(
        """SELECT DISTINCT brand_slug FROM lenders WHERE brand_slug IS NOT NULL ORDER BY brand_slug"""
    ).fetchall()
    all_slugs = [r["brand_slug"] for r in rows]

    if args.brand:
        if args.brand not in all_slugs:
            print(f"Brand slug not found in DB: {args.brand}")
            sys.exit(1)
        all_slugs = [args.brand]

    print(f"Generating JSONs for {len(all_slugs)} brands...")
    generated = 0
    skipped = 0

    for i, brand_slug in enumerate(all_slugs, 1):
        out_path = BRANDS_DIR / f"{brand_slug}.json"

        # Skip if already exists (re-run safety)
        if out_path.exists() and not args.brand:
            skipped += 1
            continue

        meta = BRAND_META.get(brand_slug, {
            "display_name": brand_slug.replace("-", " ").title(),
            "official_website": None,
            "parent_company": None,
        })

        db_row = get_brand_db_data(db, brand_slug)
        if not db_row or db_row["cnt"] == 0:
            print(f"  [{i}/{len(all_slugs)}] SKIP (no DB rows): {brand_slug}")
            skipped += 1
            continue

        location_count = db_row["cnt"]
        category = db_row["category"] or "financial-services"
        display_name = meta["display_name"]

        print(f"  [{i}/{len(all_slugs)}] Generating: {brand_slug} ({location_count} locations)...")

        summary_short = get_summary_short(display_name, category, location_count)
        summary_long, faqs = generate_brand_json(brand_slug, db_row, meta)

        brand_data = {
            "slug": brand_slug,
            "display_name": display_name,
            "summary_short": summary_short,
            "summary_long": summary_long,
            "faq": faqs,
            "official_website": meta.get("official_website"),
            "parent_company": meta.get("parent_company"),
            "category": category,
            "last_reviewed": "2026-04-20",
        }

        out_path.write_text(json.dumps(brand_data, indent=2, ensure_ascii=False))
        print(f"    Written: {out_path.name}")
        generated += 1

        # Rate limit: 2s sleep between claude calls
        if i < len(all_slugs):
            time.sleep(2)

    db.close()
    print(f"\nDone: {generated} generated, {skipped} skipped.")
    print(f"Brand JSONs at: {BRANDS_DIR}")


if __name__ == "__main__":
    main()
