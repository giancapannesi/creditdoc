#!/usr/bin/env python3
"""
CreditDoc Enrichment Prioritizer

Scores unenriched lender profiles to find the next 100 best candidates
for Level 2 deep enrichment, aligned with SEO and business strategy.

Scoring dimensions:
  1. Category Priority (0-30) — money keyword categories rank highest
  2. Google Signal (0-20) — high ratings/reviews = authority boost
  3. Website Quality (0-15) — has website = can scrape, logo, verify
  4. Brand Recognition (0-15) — known brands drive clicks and trust
  5. Affiliate Potential (0-10) — categories with affiliate programs
  6. Content Readiness (0-10) — already has some enrichment signals

Usage:
  python3 scripts/enrichment_prioritizer.py                  # show top 100
  python3 scripts/enrichment_prioritizer.py --top 50         # show top 50
  python3 scripts/enrichment_prioritizer.py --category fix-my-credit  # filter
  python3 scripts/enrichment_prioritizer.py --csv /tmp/out.csv        # export
  python3 scripts/enrichment_prioritizer.py --explain slug-name       # explain score
"""

import json
import glob
import argparse
import os
import sys
import csv
import re

LENDERS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "src", "content", "lenders")
PROTECTED_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              "data", "protected_profiles.json")

# === STRATEGY WEIGHTS ===

# Categories ranked by SEO + monetization value
# Higher = more valuable for money keywords and affiliate revenue
CATEGORY_PRIORITY = {
    'fix-my-credit': 30,       # #1 money keyword: "credit repair companies" — highest affiliate CPA
    'debt-relief': 28,         # #2 money keyword: "debt relief companies" — high volume
    'personal-loans': 26,      # #3 money keyword: "personal loans for bad credit" — high intent
    'build-credit': 24,        # #4 money keyword: "credit builder loans", "secured credit cards" — card affiliates $35-200
    'credit-monitoring': 22,   # #5 money keyword: "credit monitoring services" — recurring revenue
    'credit-cards': 22,        # Credit card affiliates pay $35-200/approval (TPG model)
    'free-help': 18,           # "credit counseling" — traffic driver, trust builder
    'payday-alternatives': 16, # "payday loan alternatives" — underserved, low competition
    'banking': 12,             # Banks/CUs — stable but low affiliate $
    'bankruptcy': 10,          # Niche but needed for content completeness
    'business-loans': 8,       # Not core consumer focus
    'mortgages': 6,            # Competitive, dominated by LendingTree/Bankrate
    'emergency-cash': 4,       # Already well-covered (44 Level 2). Predatory risk.
    'pawn-shops': 2,           # Low value, low affiliate potential
    'check-cashing': 2,       # Low value
    'atm': 1,                 # Minimal SEO value
    'insurance': 4,           # Niche
    'credit-repair': 20,      # Legacy category — map to fix-my-credit
    'credit-counseling': 18,  # Legacy — map to free-help
    'credit-building': 24,    # Legacy — map to build-credit
    'loan-marketplace': 14,   # Moderate value
}

# Money keywords from inline-linker.ts — profiles mentioning these get a boost
MONEY_KEYWORDS = [
    'credit repair companies', 'credit repair services', 'debt relief companies',
    'debt relief programs', 'personal loans for bad credit', 'personal loan lenders',
    'debt consolidation loans', 'debt consolidation', 'credit builder loans',
    'secured credit cards', 'credit monitoring services', 'credit monitoring',
    'cash advance apps', 'payday loan alternatives', 'credit counseling',
    'identity theft protection', 'rent reporting', 'credit score simulator',
    'borrowing power', 'debt payoff calculator', 'credit repair', 'debt relief',
    'personal loans',
]

# Known brands that drive clicks (from GSC data + industry knowledge)
KNOWN_BRANDS = {
    # Tier 1: Major brands people search for
    'experian', 'equifax', 'transunion', 'credit-karma', 'nerdwallet',
    'lending-tree', 'sofi', 'discover', 'capital-one', 'chase',
    'bank-of-america', 'wells-fargo', 'citi', 'ally-bank', 'marcus',
    'american-express', 'synchrony-bank', 'navy-federal-credit-union',
    'usaa', 'pnc', 'td-bank', 'us-bank',
    # Tier 2: Known credit repair / debt relief brands
    'lexington-law', 'credit-saint', 'the-credit-pros', 'sky-blue-credit',
    'the-credit-people', 'national-debt-relief', 'freedom-debt-relief',
    'clearone-advantage', 'americor', 'curadebt', 'greenpath-financial-wellness',
    'money-management-international', 'cambridge-credit-counseling',
    'incharge-debt-solutions', 'take-charge-america', 'navicore-solutions',
    # Tier 3: Growing fintech brands
    'chime', 'varo', 'dave', 'brigit', 'earnin', 'moneylion', 'upgrade',
    'upstart', 'avant', 'oportun', 'lendingclub', 'prosper', 'best-egg',
    'marcus-by-goldman-sachs', 'lightstream', 'payoff', 'happy-money',
    'self', 'kikoff', 'credit-strong', 'grow-credit',
}

# Categories with active or pending affiliate programs
AFFILIATE_CATEGORIES = {
    'fix-my-credit': 10,      # The Credit People ($125), CJ programs
    'debt-relief': 8,         # CuraDebt ($55-75/lead)
    'personal-loans': 8,      # Lead Stack Media, SoFi
    'build-credit': 8,        # OpenSky, First Progress, Self
    'credit-cards': 10,       # Card affiliates $35-200/approval
    'credit-monitoring': 6,   # Experian, Credit Karma
    'banking': 4,             # BMO, Axos Bank, Valley National
    'free-help': 2,           # Low direct monetization
}


def load_protected():
    """Load protected profile slugs."""
    if os.path.exists(PROTECTED_FILE):
        try:
            with open(PROTECTED_FILE) as f:
                return set(json.load(f).get('profiles', []))
        except:
            pass
    return set()


def count_money_keywords(text):
    """Count money keyword phrases in text."""
    if not text:
        return 0
    text_lower = text.lower()
    count = 0
    for kw in MONEY_KEYWORDS:
        if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
            count += 1
    return count


def score_profile(data):
    """Score a profile for enrichment priority. Returns (total_score, breakdown)."""
    slug = data.get('slug', '')
    cat = data.get('category', '')
    breakdown = {}

    # 1. Category Priority (0-30)
    cat_score = CATEGORY_PRIORITY.get(cat, 5)
    breakdown['category'] = cat_score

    # 2. Google Signal (0-20)
    google_score = 0
    g_rating = data.get('google_rating', 0) or 0
    g_reviews = data.get('google_reviews_count', 0) or 0

    if g_rating >= 4.5 and g_reviews >= 100:
        google_score = 20
    elif g_rating >= 4.0 and g_reviews >= 50:
        google_score = 15
    elif g_rating >= 4.0:
        google_score = 10
    elif g_rating >= 3.5:
        google_score = 7
    elif g_rating > 0:
        google_score = 3

    # Review volume bonus
    if g_reviews >= 1000:
        google_score = min(20, google_score + 5)
    elif g_reviews >= 500:
        google_score = min(20, google_score + 3)
    breakdown['google_signal'] = google_score

    # 3. Website Quality (0-15)
    web_score = 0
    if data.get('website_url'):
        web_score += 10
    if data.get('logo_url'):
        web_score += 5
    breakdown['website'] = web_score

    # 4. Brand Recognition (0-15)
    brand_score = 0
    if slug in KNOWN_BRANDS:
        brand_score = 15
    elif data.get('company_info', {}).get('bbb_accredited'):
        brand_score = 8
    elif data.get('company_info', {}).get('bbb_rating', '') in ('A+', 'A'):
        brand_score = 5
    breakdown['brand'] = brand_score

    # 5. Affiliate Potential (0-10)
    aff_score = AFFILIATE_CATEGORIES.get(cat, 0)
    breakdown['affiliate'] = aff_score

    # 6. Content Readiness (0-10)
    content_score = 0
    desc_long = data.get('description_long', '') or ''
    if len(desc_long) >= 500:
        content_score += 3
    if len(data.get('services', []) or []) >= 3:
        content_score += 2
    if data.get('diagnosis'):
        content_score += 2
    # Money keyword presence in existing content
    kw_count = count_money_keywords(desc_long + ' ' + (data.get('diagnosis', '') or ''))
    if kw_count >= 3:
        content_score += 3
    elif kw_count >= 1:
        content_score += 1
    content_score = min(10, content_score)
    breakdown['content_readiness'] = content_score

    total = sum(breakdown.values())
    return total, breakdown


def main():
    parser = argparse.ArgumentParser(description="CreditDoc Enrichment Prioritizer")
    parser.add_argument("--top", type=int, default=100, help="Number of top candidates to show")
    parser.add_argument("--category", help="Filter by category")
    parser.add_argument("--csv", help="Export to CSV file")
    parser.add_argument("--explain", help="Explain scoring for a specific slug")
    parser.add_argument("--min-score", type=int, default=0, help="Minimum score to include")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show score breakdown")
    args = parser.parse_args()

    protected = load_protected()

    # Load all profiles
    candidates = []
    already_l2 = 0
    no_website = 0
    is_protected = 0
    no_index_count = 0

    for fpath in sorted(glob.glob(os.path.join(LENDERS_DIR, "*.json"))):
        try:
            with open(fpath) as f:
                d = json.load(f)
        except (json.JSONDecodeError, IOError):
            continue

        slug = d.get('slug', os.path.basename(fpath).replace('.json', ''))

        # Skip protected (already Level 2 approved)
        if slug in protected:
            is_protected += 1
            continue

        # Skip already Level 2 (has pricing tiers with features)
        tiers = d.get('pricing', {}).get('tiers', []) or []
        if any(t.get('features') for t in tiers):
            already_l2 += 1
            continue

        # Must have been through Level 1 enrichment
        if not d.get('has_been_enriched'):
            continue

        # Must have a website URL (needed for scraping, logo, verification)
        if not d.get('website_url'):
            no_website += 1
            continue

        # Prefer indexed profiles (but don't require it)
        if d.get('no_index', True):
            no_index_count += 1
            # Don't skip — just note it. Some may be worth indexing after enrichment.

        # Category filter
        if args.category and d.get('category') != args.category:
            continue

        total, breakdown = score_profile(d)
        candidates.append({
            'slug': slug,
            'name': d.get('name', slug),
            'category': d.get('category', ''),
            'rating': d.get('rating', 0),
            'google_rating': d.get('google_rating', 0) or 0,
            'google_reviews': d.get('google_reviews_count', 0) or 0,
            'bbb_rating': d.get('company_info', {}).get('bbb_rating', ''),
            'website_url': d.get('website_url', ''),
            'no_index': d.get('no_index', True),
            'score': total,
            'breakdown': breakdown,
            'data': d,
        })

    # Handle --explain mode
    if args.explain:
        found = [c for c in candidates if c['slug'] == args.explain]
        if not found:
            # Try loading directly
            fpath = os.path.join(LENDERS_DIR, f"{args.explain}.json")
            if os.path.exists(fpath):
                with open(fpath) as f:
                    d = json.load(f)
                total, breakdown = score_profile(d)
                print(f"\n  {d.get('name', args.explain)} ({args.explain})")
                print(f"  Category: {d.get('category', '?')}")
                print(f"  Total Score: {total}/100")
                for dim, val in sorted(breakdown.items(), key=lambda x: -x[1]):
                    print(f"    {dim:<22} {val:>3}")
                if args.explain in protected:
                    print(f"\n  STATUS: PROTECTED (founder-approved Level 2)")
                tiers = d.get('pricing', {}).get('tiers', []) or []
                if any(t.get('features') for t in tiers):
                    print(f"  STATUS: Already Level 2 enriched")
            else:
                print(f"Profile not found: {args.explain}")
            return

        c = found[0]
        print(f"\n  {c['name']} ({c['slug']})")
        print(f"  Category: {c['category']}")
        print(f"  Google: {c['google_rating']} stars, {c['google_reviews']} reviews")
        print(f"  BBB: {c['bbb_rating']}")
        print(f"  Total Score: {c['score']}/100")
        for dim, val in sorted(c['breakdown'].items(), key=lambda x: -x[1]):
            print(f"    {dim:<22} {val:>3}")
        return

    # Sort by score descending
    candidates.sort(key=lambda x: -x['score'])

    # Filter by minimum score
    if args.min_score > 0:
        candidates = [c for c in candidates if c['score'] >= args.min_score]

    top = candidates[:args.top]

    # Print header
    print(f"CreditDoc Enrichment Prioritizer — Next {args.top} Candidates")
    print(f"Pool: {len(candidates)} candidates | Protected: {is_protected} | Already L2: {already_l2} | No website: {no_website}")
    if args.category:
        print(f"Filter: category={args.category}")
    print("=" * 110)
    print(f"  {'#':>3}  {'Score':>5}  {'Slug':<45} {'Category':<20} {'Google':>8} {'BBB':>4}  {'Indexed':>7}")
    print("=" * 110)

    # Category distribution in top N
    cat_counts = {}

    for i, c in enumerate(top):
        cat_counts[c['category']] = cat_counts.get(c['category'], 0) + 1
        indexed = "YES" if not c['no_index'] else "no"
        g_str = f"{c['google_rating']:.1f}" if c['google_rating'] > 0 else "-"
        print(f"  {i+1:>3}  {c['score']:>5}  {c['slug']:<45} {c['category']:<20} {g_str:>8} {c['bbb_rating']:>4}  {indexed:>7}")

        if args.verbose:
            bd = c['breakdown']
            print(f"       cat:{bd['category']} goog:{bd['google_signal']} web:{bd['website']} brand:{bd['brand']} aff:{bd['affiliate']} content:{bd['content_readiness']}")

    # Summary
    print()
    print("=" * 110)
    print(f"Category distribution in top {len(top)}:")
    for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
        print(f"  {cat:<25} {count:>4}")

    # Money keyword coverage
    print(f"\nMoney keyword alignment:")
    money_cats = {'fix-my-credit', 'debt-relief', 'personal-loans', 'build-credit',
                  'credit-monitoring', 'credit-cards', 'free-help', 'payday-alternatives',
                  'credit-repair', 'credit-counseling', 'credit-building'}
    money_count = sum(1 for c in top if c['category'] in money_cats)
    print(f"  {money_count}/{len(top)} candidates in money keyword categories ({round(money_count/len(top)*100)}%)")

    # CSV export
    if args.csv:
        with open(args.csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'rank', 'slug', 'name', 'category', 'score',
                'cat_score', 'google_score', 'website_score', 'brand_score',
                'affiliate_score', 'content_score',
                'google_rating', 'google_reviews', 'bbb_rating',
                'website_url', 'indexed', 'review_url'
            ])
            for i, c in enumerate(top):
                bd = c['breakdown']
                writer.writerow([
                    i + 1, c['slug'], c['name'], c['category'], c['score'],
                    bd['category'], bd['google_signal'], bd['website'],
                    bd['brand'], bd['affiliate'], bd['content_readiness'],
                    c['google_rating'], c['google_reviews'], c['bbb_rating'],
                    c['website_url'], 'YES' if not c['no_index'] else 'NO',
                    f"https://www.creditdoc.co/review/{c['slug']}/"
                ])
        print(f"\nCSV exported to: {args.csv}")


if __name__ == "__main__":
    main()
