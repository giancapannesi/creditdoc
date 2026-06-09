#!/usr/bin/env python3
"""
CreditDoc — Comparison Page Generator

Generates comparison pages between lenders using Claude CLI.
Appends to comparisons.json — NEVER overwrites existing entries.

Usage:
    python3 tools/creditdoc_comparison_generator.py                    # Generate next 5 from queue
    python3 tools/creditdoc_comparison_generator.py --count 10         # Generate 10
    python3 tools/creditdoc_comparison_generator.py --dry-run          # Show what would be generated
    python3 tools/creditdoc_comparison_generator.py --stats            # Show queue stats
    python3 tools/creditdoc_comparison_generator.py --build            # Build + push after generating

Cron:
    30 15 * * * /usr/bin/python3 /srv/BusinessOps/tools/creditdoc_comparison_generator.py --count 5 --build
"""

import argparse
import json
import glob
import os
import subprocess
import sys
import time
from itertools import combinations
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from creditdoc_oauth import call_claude
from creditdoc_content_guardrails import reject_if_unsafe, supplied_fact_values
from creditdoc_content_repair import repair_unsafe_json

# === CONFIG ===
PROJECT_DIR = "/srv/BusinessOps/creditdoc"
COMPARISONS_FILE = os.path.join(PROJECT_DIR, "src/content/comparisons.json")
LENDERS_DIR = os.path.join(PROJECT_DIR, "src/content/lenders")
SITE_URL = "https://creditdoc.co"
INDEXNOW_KEY = "f2018aa106044007bf54b7cde9067a1e"
TODAY = datetime.now().strftime("%Y-%m-%d")
YEAR = datetime.now().strftime("%Y")

# === CreditDoc DB API (Phase 3 dual-write — 2026-04-09) ===
sys.path.insert(0, os.path.join(PROJECT_DIR, "tools"))
try:
    from creditdoc_db import CreditDocDB
    HAS_PERSISTENCE_DB = True
except Exception:
    HAS_PERSISTENCE_DB = False

TELEGRAM_TOKEN = ""  # removed — all alerts via Harvey email (cron_alert.py)
TELEGRAM_CHAT_ID = ""


def load_lenders():
    """Load all lender JSONs."""
    lenders = {}
    for f in glob.glob(os.path.join(LENDERS_DIR, "*.json")):
        d = json.load(open(f))
        lenders[d['slug']] = d
    return lenders


def load_comparisons():
    """Load existing comparisons."""
    with open(COMPARISONS_FILE) as f:
        return json.load(f)


def comp_score(l):
    """Score a lender's comparison readiness."""
    s = 0
    if l.get('pricing', {}).get('monthly_price', 0) > 0: s += 3
    if len(l.get('pricing', {}).get('tiers', [])) > 0: s += 2
    if len(l.get('pros', [])) >= 3: s += 2
    if len(l.get('cons', [])) >= 2: s += 2
    if len(l.get('description_long', '') or '') > 200: s += 2
    if l.get('company_info', {}).get('bbb_rating', '') not in ('', 'N/A', 'NR'): s += 1
    if l.get('website_url', '').strip(): s += 1
    if l.get('pricing', {}).get('money_back_guarantee'): s += 1
    return s


def is_comparison_ready(l):
    """Check if a lender has enough data for a meaningful comparison."""
    return (
        (l.get('has_been_enriched') or l.get('data_source') == 'editorial')
        and len(l.get('pros', [])) >= 2
        and l.get('rating', 0) > 0
    )


def build_queue(lenders, existing_comps):
    """Build prioritized queue of comparisons to generate."""
    existing_pairs = set()
    for c in existing_comps:
        pair = tuple(sorted([c['lender_a'], c['lender_b']]))
        existing_pairs.add(pair)

    ready = [l for l in lenders.values() if is_comparison_ready(l)]

    # Group by category
    by_cat = {}
    for l in ready:
        cat = l['category']
        if cat not in by_cat:
            by_cat[cat] = []
        by_cat[cat].append(l)

    # Priority order for categories (highest affiliate revenue first)
    cat_priority = [
        'fix-my-credit', 'debt-relief', 'personal-loans',
        'credit-monitoring', 'build-credit', 'free-help',
        'emergency-cash', 'pawn-shops', 'payday-alternatives',
    ]

    queue = []
    for cat in cat_priority:
        if cat not in by_cat:
            continue
        top = sorted(by_cat[cat], key=lambda l: -comp_score(l))[:12]
        for a, b in combinations(top, 2):
            pair = tuple(sorted([a['slug'], b['slug']]))
            if pair in existing_pairs:
                continue
            queue.append({
                'lender_a': a['slug'],
                'lender_b': b['slug'],
                'category': cat,
                'priority': comp_score(a) + comp_score(b),
            })
            existing_pairs.add(pair)

    # Sort by combined score (best data first)
    queue.sort(key=lambda x: -x['priority'])
    return queue


def format_price(price):
    """Format price for display."""
    if price == 0:
        return "Contact for pricing"
    if price == int(price):
        return f"${int(price)}"
    return f"${price:.2f}"


def generate_comparison(lenders, comp_item):
    """Generate a comparison using Claude CLI."""
    a = lenders[comp_item['lender_a']]
    b = lenders[comp_item['lender_b']]

    slug = f"{a['slug']}-vs-{b['slug']}"
    if len(slug) > 80:
        slug = f"{a['slug'][:35]}-vs-{b['slug'][:35]}"

    # Build context for Claude
    def lender_summary(l):
        price = l.get('pricing', {}).get('monthly_price', 0)
        setup = l.get('pricing', {}).get('setup_fee', 0)
        tiers = l.get('pricing', {}).get('tiers', [])
        bbb = l.get('company_info', {}).get('bbb_rating', 'N/A')
        accred = l.get('company_info', {}).get('bbb_accredited', False)
        mbg = l.get('pricing', {}).get('money_back_guarantee', False)
        mbg_detail = l.get('pricing', {}).get('guarantee_details', '')
        google_rating = l.get('google_rating')
        google_reviews_count = l.get('google_reviews_count', 0)

        lines = [
            f"Name: {l['name']}",
            f"Slug: {l['slug']}",
            f"Category: {l['category']}",
            f"CreditDoc Rating: {l.get('rating', 0)}/5",
            f"Google Rating: {google_rating}/5 ({google_reviews_count} reviews)" if google_rating and google_reviews_count else "Google Rating: Not supplied",
            f"Monthly Price: {format_price(price)}",
            f"Setup Fee: {format_price(setup)}",
            f"BBB Rating: {bbb} {'(Accredited)' if accred else ''}",
            f"Money-Back Guarantee: {'Yes — ' + mbg_detail if mbg else 'No'}",
            f"Headquarters: {l.get('company_info', {}).get('headquarters', 'Unknown')}",
            f"Founded: {l.get('company_info', {}).get('founded_year', 'Unknown')}",
        ]
        if tiers:
            lines.append("Tiers: " + " | ".join(f"{t['name']}: {format_price(t['price'])}/mo" for t in tiers))
        if l.get('pros'):
            lines.append("Pros: " + " | ".join(l['pros'][:5]))
        if l.get('cons'):
            lines.append("Cons: " + " | ".join(l['cons'][:5]))
        if l.get('description_short'):
            lines.append(f"Description: {l['description_short']}")
        return "\n".join(lines)

    prompt = f"""Generate a comparison analysis for CreditDoc.co.

COMPANY A:
{lender_summary(a)}

COMPANY B:
{lender_summary(b)}

Write a comparison analysis. Output ONLY strict JSON (no markdown, no code fences):

{{
  "slug": "{slug}",
  "lender_a": "{a['slug']}",
  "lender_b": "{b['slug']}",
  "title": "{a['name']} vs {b['name']} ({YEAR})",
  "target_keyword": "{a['name'].lower()} vs {b['name'].lower()}",
  "summary": "3-5 sentence comparison summary. Be specific about pricing, BBB ratings, features, and clear recommendation only where source data is supplied.",
  "winner": "slug-of-the-better-option",
  "winner_reason": "1-2 sentences explaining why the winner is better. Use specific data points."
}}

RULES:
- Be objective. Use only real data from both companies as supplied above.
- Do NOT invent prices, fees, APRs, BBB ratings, Google ratings, star ratings, guarantees, founded years, locations, or feature claims.
- Dollar amounts, ratings, and guarantees may appear ONLY if the exact value appears in COMPANY A or COMPANY B above.
- If pricing is "Contact for pricing", say pricing is not listed in the current CreditDoc source data; do not estimate it.
- The winner should be the company with the better overall value proposition.
- Consider: price, BBB rating, money-back guarantee, features, reputation.
- Summary should be 80-120 words, specific and useful.
- Output ONLY the JSON object."""

    try:
        output = call_claude(prompt, model='opus', max_tokens=2048)

        # Clean markdown fences
        if "```json" in output:
            output = output.split("```json")[1].split("```")[0].strip()
        elif "```" in output:
            output = output.split("```")[1].split("```")[0].strip()

        comp = json.loads(output)

        # Validate
        required = ["slug", "lender_a", "lender_b", "title", "summary", "winner", "winner_reason"]
        for field in required:
            if field not in comp:
                print(f"  ERROR: Missing field '{field}'")
                return None

        # Ensure correct slugs
        comp["slug"] = slug
        comp["lender_a"] = a['slug']
        comp["lender_b"] = b['slug']

        # Validate winner is one of the two lenders
        if comp["winner"] not in (a['slug'], b['slug']):
            comp["winner"] = a['slug']  # Default to A

        a_summary = lender_summary(a)
        b_summary = lender_summary(b)
        allowed_values = supplied_fact_values([a_summary, b_summary])
        entity_allowed_values = {
            a["name"]: supplied_fact_values([a_summary]),
            b["name"]: supplied_fact_values([b_summary]),
        }
        guardrail_failures = reject_if_unsafe(
            comp,
            allowed_values=allowed_values,
            entity_allowed_values=entity_allowed_values,
        )
        if guardrail_failures:
            print("  REPAIR: CreditDoc guardrails failed; attempting content repair")
            comp, guardrail_failures = repair_unsafe_json(
                comp,
                guardrail_failures,
                content_type="comparison page",
                source_context=f"COMPANY A:\n{a_summary}\n\nCOMPANY B:\n{b_summary}",
                allowed_values=allowed_values,
                entity_allowed_values=entity_allowed_values,
                max_tokens=2048,
            )
        if guardrail_failures:
            print("  REJECT: CreditDoc guardrails failed")
            for failure in guardrail_failures[:8]:
                print(f"    - {failure}")
            return None

        print(f"  OK: {a['name']} vs {b['name']} → winner: {comp['winner']}")
        return comp

    except json.JSONDecodeError as e:
        print(f"  ERROR: Invalid JSON: {e}")
        return None
    except Exception as e:
        print(f"  ERROR: {e}")
        return None


def build_and_push(new_slugs):
    """Build Astro site, commit, push, and ping IndexNow."""
    os.chdir(PROJECT_DIR)

    print("Building site...")
    result = subprocess.run(["npx", "astro", "build"], capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        print(f"BUILD FAILED: {result.stderr[-500:]}")
        return False

    print("Committing...")
    subprocess.run(["git", "add", "src/content/comparisons.json"], check=True)
    msg = f"Add {len(new_slugs)} comparison pages"
    subprocess.run(["git", "commit", "-m", msg], check=True)

    print("Pushing...")
    subprocess.run(["git", "push", "origin", "HEAD"], check=True)

    # IndexNow
    urls = [f"{SITE_URL}/compare/{s}/" for s in new_slugs]
    payload = json.dumps({
        "host": "creditdoc.co",
        "key": INDEXNOW_KEY,
        "urlList": urls
    })
    import urllib.request
    req = urllib.request.Request(
        "https://api.indexnow.org/indexnow",
        data=payload.encode(),
        headers={"Content-Type": "application/json"}
    )
    try:
        urllib.request.urlopen(req, timeout=10)
        print(f"IndexNow: {len(urls)} URLs submitted")
    except:
        print("IndexNow: failed (non-critical)")

    return True


def send_telegram(message):
    """Send notification to Telegram. DISABLED — use daily summary only."""
    # Telegram removed 2026-05-14 — alerts go through cron_alert.py / Harvey email
    pass



def main():
    parser = argparse.ArgumentParser(description="CreditDoc Comparison Generator")
    parser.add_argument("--count", type=int, default=5, help="Number of comparisons to generate")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be generated")
    parser.add_argument("--stats", action="store_true", help="Show queue statistics")
    parser.add_argument("--build", action="store_true", help="Build + push after generating")
    args = parser.parse_args()

    os.chdir(PROJECT_DIR)

    lenders = load_lenders()
    existing = load_comparisons()
    queue = build_queue(lenders, existing)

    if args.stats:
        print(f"Existing comparisons: {len(existing)}")
        print(f"Queue remaining: {len(queue)}")
        from collections import Counter
        cats = Counter(c['category'] for c in queue)
        for cat, count in cats.most_common():
            print(f"  {cat}: {count}")
        return

    if not queue:
        print("ERROR: Queue empty — all comparison pairs generated.")
        sys.exit(1)

    batch = queue[:args.count]

    if args.dry_run:
        print(f"Would generate {len(batch)} comparisons:")
        for c in batch:
            a_name = lenders[c['lender_a']]['name']
            b_name = lenders[c['lender_b']]['name']
            print(f"  [{c['category']}] {a_name} vs {b_name} (score: {c['priority']})")
        print(f"\nTotal queue: {len(queue)} remaining")
        return

    print(f"Generating {len(batch)} comparisons...")
    print(f"Existing: {len(existing)} | Queue remaining: {len(queue)}\n")

    new_comps = []
    for item in batch:
        a_name = lenders[item['lender_a']]['name']
        b_name = lenders[item['lender_b']]['name']
        print(f"  Generating: {a_name} vs {b_name}...")
        comp = generate_comparison(lenders, item)
        if comp:
            new_comps.append(comp)
        time.sleep(2)

    if not new_comps:
        print("No comparisons generated successfully.")
        sys.exit(1)

    # Save — write to JSON file (legacy, for Astro build)
    combined = existing + new_comps
    with open(COMPARISONS_FILE, 'w') as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)
    print(f"\nSaved {len(combined)} total comparisons ({len(new_comps)} new)")

    # Dual-write: mirror new comparisons to persistence DB (Phase 3)
    if HAS_PERSISTENCE_DB and new_comps:
        try:
            with CreditDocDB() as db:
                added = 0
                for comp in new_comps:
                    if not isinstance(comp, dict) or 'slug' not in comp:
                        continue
                    try:
                        db.add_comparison(comp, updated_by='comparison_generator')
                        added += 1
                    except Exception as e:
                        print(f"    DB add failed for {comp.get('slug', '?')}: {e}")
                print(f"    DB mirror: {added}/{len(new_comps)} new comparisons added")
        except Exception as e:
            print(f"    DB mirror write failed: {type(e).__name__}: {e}")

    new_slugs = [c["slug"] for c in new_comps]

    if args.build:
        if build_and_push(new_slugs):
            remaining = len(queue) - len(new_comps)
            send_telegram(
                f"📊 *CreditDoc Comparisons*\n"
                f"Generated {len(new_comps)} new comparisons\n"
                f"Total: {len(combined)} | Remaining: {remaining}"
            )

    print("Done.")


if __name__ == "__main__":
    main()
