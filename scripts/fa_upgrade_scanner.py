#!/usr/bin/env python3
"""
CreditDoc Profile Quality Checker

Validates lender profiles against the Credit Saint deep enrichment template.
Checks 6 quality dimensions:

  1. Internal Linking (money keywords in description_long that trigger auto-linker)
  2. Scoring System (5-dimension rating_breakdown present)
  3. Website URL (website_url populated)
  4. Logo (logo_url populated or website_url for fallback)
  5. Content Quality (description, pros, cons, diagnosis, services)
  6. Pricing Detail (tiers with feature lists)

Usage:
  python3 scripts/profile_quality_check.py                     # all Level 2 profiles
  python3 scripts/profile_quality_check.py --slug credit-saint # single profile
  python3 scripts/profile_quality_check.py --all               # all enriched profiles
  python3 scripts/profile_quality_check.py --csv /tmp/out.csv  # export results
  python3 scripts/profile_quality_check.py --fail-only         # show only failures
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

# Money keywords from inline-linker.ts — profiles must contain these for auto-linking
MONEY_KEYWORDS = [
    'credit repair companies', 'credit repair services', 'debt relief companies',
    'debt relief programs', 'personal loans for bad credit', 'personal loan lenders',
    'debt consolidation loans', 'debt consolidation', 'credit builder loans',
    'secured credit cards', 'credit monitoring services', 'credit monitoring',
    'cash advance apps', 'payday loan alternatives', 'credit counseling',
    'identity theft protection', 'rent reporting', 'credit score simulator',
    'borrowing power', 'debt payoff calculator', 'credit repair', 'debt relief',
    'best instalment loans', 'personal installment loans', 'installment lenders',
    'instalment loan', 'installment loans',
    'personal loans',
]

# Protected profiles list — founder-approved, do not overwrite
PROTECTED_PROFILES_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "protected_profiles.json"
)


def load_profile(slug):
    path = os.path.join(LENDERS_DIR, f"{slug}.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def count_money_keywords(text):
    """Count how many money keyword phrases appear in the text."""
    if not text:
        return 0, []
    text_lower = text.lower()
    found = []
    # Sort by length (longest first) to match inline-linker behavior
    sorted_kw = sorted(MONEY_KEYWORDS, key=len, reverse=True)
    for kw in sorted_kw:
        if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
            found.append(kw)
    return len(found), found


def check_profile(data):
    """Run all 6 quality checks on a profile. Returns dict of results."""
    results = {}

    # 1. Internal Linking — money keywords in description_long
    desc_long = data.get('description_long', '') or ''
    kw_count, kw_found = count_money_keywords(desc_long)
    # Also check diagnosis
    diagnosis = data.get('diagnosis', '') or ''
    diag_count, diag_found = count_money_keywords(diagnosis)
    total_kw = len(set(kw_found + diag_found))
    results['internal_links'] = {
        'pass': total_kw >= 2,
        'score': min(total_kw, 5),
        'max': 5,
        'keywords_found': list(set(kw_found + diag_found))[:5],
        'detail': f"{total_kw} money keywords found" if total_kw >= 2 else f"FAIL: only {total_kw} money keywords (need 2+)"
    }

    # 2. Scoring System — 5-dimension rating_breakdown
    breakdown = data.get('rating_breakdown', {})
    has_all_5 = (isinstance(breakdown, dict) and
                 all(k in breakdown for k in ['value', 'effectiveness', 'customer_service', 'transparency', 'ease_of_use']))
    results['scoring'] = {
        'pass': has_all_5,
        'score': 5 if has_all_5 else 0,
        'max': 5,
        'detail': "5-dimension rating present" if has_all_5 else "FAIL: missing rating_breakdown dimensions"
    }

    # 3. Website URL
    has_website = bool(data.get('website_url'))
    results['website'] = {
        'pass': has_website,
        'score': 5 if has_website else 0,
        'max': 5,
        'detail': data.get('website_url', 'FAIL: no website_url')
    }

    # 4. Logo — local logo OR DDG/Icon Horse fallback chain (needs website_url)
    has_logo = bool(data.get('logo_url'))
    has_fallback = has_website  # DDG → Icon Horse → initial letter chain works if website_url exists
    results['logo'] = {
        'pass': has_logo or has_fallback,
        'fallback': has_fallback,
        'score': 5 if has_logo else (3 if has_fallback else 0),
        'max': 5,
        'detail': data.get('logo_url', 'DDG/Icon Horse fallback' if has_fallback else 'FAIL: no logo and no website for fallback')
    }

    # 5. Content Quality
    desc_short = data.get('description_short', '') or ''
    pros = data.get('pros', []) or []
    cons = data.get('cons', []) or []
    best_for = data.get('best_for', []) or []
    services = data.get('services', []) or []
    diag = data.get('diagnosis', '') or ''
    timeline = data.get('typical_results_timeline', '') or ''

    content_checks = {
        'description_short': len(desc_short) >= 50,
        'description_long': len(desc_long) >= 500,
        'pros_4+': len(pros) >= 4,
        'cons_3+': len(cons) >= 3,
        'best_for_2+': len(best_for) >= 2,
        'services_5+': len(services) >= 5,
        'diagnosis': len(diag) >= 50,
        'timeline': len(timeline) >= 20,
    }
    passed = sum(content_checks.values())
    failed_items = [k for k, v in content_checks.items() if not v]
    results['content'] = {
        'pass': passed >= 6,  # 6 of 8 required
        'score': passed,
        'max': 8,
        'checks': content_checks,
        'detail': f"{passed}/8 content checks" + (f" — missing: {', '.join(failed_items)}" if failed_items else "")
    }

    # 6. Pricing Detail — tiers with features
    tiers = data.get('pricing', {}).get('tiers', []) or []
    tiers_with_features = [t for t in tiers if t.get('features') and len(t.get('features', [])) > 0]
    has_guarantee = bool(data.get('pricing', {}).get('guarantee_details'))
    results['pricing'] = {
        'pass': len(tiers_with_features) >= 1,
        'score': min(len(tiers_with_features), 3) + (2 if has_guarantee else 0),
        'max': 5,
        'tiers_total': len(tiers),
        'tiers_with_features': len(tiers_with_features),
        'has_guarantee_details': has_guarantee,
        'detail': f"{len(tiers_with_features)} tiers with features" + (", guarantee details" if has_guarantee else ", no guarantee details")
    }

    # Overall
    total_score = sum(r['score'] for r in results.values())
    total_max = sum(r['max'] for r in results.values())
    all_pass = all(r['pass'] for r in results.values())
    results['_overall'] = {
        'score': total_score,
        'max': total_max,
        'pct': round(total_score / total_max * 100, 1) if total_max > 0 else 0,
        'pass': all_pass,
        'grade': 'A' if total_score >= 28 else 'B' if total_score >= 22 else 'C' if total_score >= 16 else 'F'
    }

    return results


def format_result(slug, results, verbose=False):
    """Format check results for display."""
    o = results['_overall']
    grade = o['grade']
    status = 'PASS' if o['pass'] else 'FAIL'
    dims = ['internal_links', 'scoring', 'website', 'logo', 'content', 'pricing']
    checks = ''.join(['.' if results[d]['pass'] else 'X' for d in dims])

    line = f"  {status:4} [{checks}] {slug:<50} {o['score']:>2}/{o['max']} ({o['pct']:>5.1f}%) Grade:{grade}"

    if verbose:
        for dim in dims:
            r = results[dim]
            mark = 'OK' if r['pass'] else 'XX'
            line += f"\n       {mark} {dim:<18} {r['score']}/{r['max']}  {r['detail']}"

    return line


def main():
    parser = argparse.ArgumentParser(description="CreditDoc Profile Quality Checker")
    parser.add_argument("--slug", help="Check a single profile")
    parser.add_argument("--all", action="store_true", help="Check ALL enriched profiles (not just Level 2)")
    parser.add_argument("--level2", action="store_true", default=True, help="Check profiles with tier features (default)")
    parser.add_argument("--indexed-only", action="store_true", help="Only check indexed profiles")
    parser.add_argument("--fail-only", action="store_true", help="Show only profiles that fail checks")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show dimension details")
    parser.add_argument("--csv", help="Export results to CSV file")
    parser.add_argument("--min-grade", default="F", choices=['A', 'B', 'C', 'F'], help="Minimum grade to show")
    args = parser.parse_args()

    if args.slug:
        data = load_profile(args.slug)
        if data is None:
            print(f"Profile not found: {args.slug}")
            sys.exit(1)
        profiles = [(data, args.slug)]
    else:
        profiles = []
        for fpath in sorted(glob.glob(os.path.join(LENDERS_DIR, "*.json"))):
            try:
                with open(fpath) as f:
                    d = json.load(f)
            except (json.JSONDecodeError, IOError):
                continue

            slug = d.get('slug', os.path.basename(fpath).replace('.json', ''))

            if not d.get('has_been_enriched'):
                continue

            if args.indexed_only and d.get('no_index', True):
                continue

            if not args.all:
                # Level 2 filter: must have pricing tiers with features
                tiers = d.get('pricing', {}).get('tiers', []) or []
                if not any(t.get('features') for t in tiers):
                    continue

            profiles.append((d, slug))

    # Run checks
    all_results = []
    for data, slug in profiles:
        results = check_profile(data)
        all_results.append((slug, data, results))

    # Filter
    grade_order = {'A': 4, 'B': 3, 'C': 2, 'F': 1}
    min_g = grade_order.get(args.min_grade, 1)

    filtered = []
    for slug, data, results in all_results:
        o = results['_overall']
        if args.fail_only and o['pass']:
            continue
        if grade_order.get(o['grade'], 1) < min_g:
            continue
        filtered.append((slug, data, results))

    # Print
    print(f"CreditDoc Profile Quality Check — Credit Saint Template")
    print(f"Checked: {len(all_results)} profiles | Showing: {len(filtered)}")
    print(f"Legend: [ILSWCP] = Internal Links, Scoring, Website, Logo, Content, Pricing")
    print("=" * 100)

    grade_counts = {'A': 0, 'B': 0, 'C': 0, 'F': 0}
    pass_count = 0
    fail_count = 0
    dim_fails = {d: 0 for d in ['internal_links', 'scoring', 'website', 'logo', 'content', 'pricing']}

    for slug, data, results in all_results:
        o = results['_overall']
        grade_counts[o['grade']] = grade_counts.get(o['grade'], 0) + 1
        if o['pass']:
            pass_count += 1
        else:
            fail_count += 1
        for dim in dim_fails:
            if not results[dim]['pass']:
                dim_fails[dim] += 1

    for slug, data, results in filtered:
        print(format_result(slug, results, verbose=args.verbose))

    print()
    print("=" * 100)
    print(f"SUMMARY: {pass_count} PASS, {fail_count} FAIL out of {len(all_results)} checked")
    print(f"Grades: A={grade_counts['A']}  B={grade_counts['B']}  C={grade_counts['C']}  F={grade_counts['F']}")
    print(f"\nFailure by dimension:")
    for dim, count in sorted(dim_fails.items(), key=lambda x: -x[1]):
        pct = round(count / len(all_results) * 100, 1) if all_results else 0
        print(f"  {dim:<20} {count:>4} fails ({pct}%)")

    # CSV export
    if args.csv:
        with open(args.csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'slug', 'category', 'rating', 'grade', 'score', 'max', 'pct',
                'pass', 'internal_links', 'scoring', 'website', 'logo', 'content', 'pricing',
                'money_keywords_found', 'content_gaps', 'url'
            ])
            for slug, data, results in all_results:
                o = results['_overall']
                kw = ', '.join(results['internal_links'].get('keywords_found', []))
                gaps = ', '.join([k for k, v in results.get('content', {}).get('checks', {}).items() if not v])
                writer.writerow([
                    slug, data.get('category', ''), data.get('rating', ''),
                    o['grade'], o['score'], o['max'], o['pct'],
                    'PASS' if o['pass'] else 'FAIL',
                    'PASS' if results['internal_links']['pass'] else 'FAIL',
                    'PASS' if results['scoring']['pass'] else 'FAIL',
                    'PASS' if results['website']['pass'] else 'FAIL',
                    'PASS' if results['logo']['pass'] else 'FAIL',
                    'PASS' if results['content']['pass'] else 'FAIL',
                    'PASS' if results['pricing']['pass'] else 'FAIL',
                    kw, gaps,
                    f"https://www.creditdoc.co/review/{slug}/"
                ])
        print(f"\nCSV exported to: {args.csv}")


if __name__ == "__main__":
    main()
