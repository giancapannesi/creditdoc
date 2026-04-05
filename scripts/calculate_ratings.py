#!/usr/bin/env python3
"""
CreditDoc Star Rating Calculator

5-dimension scoring formula:
  Value (20%) + Effectiveness (25%) + Customer Service (20%)
  + Transparency (15%) + Ease of Use (20%)

Each dimension: base score + signal bonuses, clamped 1.0–5.0.
Overall: weighted average, rounded to 1 decimal.

Usage:
  python3 scripts/calculate_ratings.py --dry-run              # all enriched profiles
  python3 scripts/calculate_ratings.py --slug ace-cash-express # single profile
  python3 scripts/calculate_ratings.py --apply                 # write changes
  python3 scripts/calculate_ratings.py --indexed-only          # only no_index=false
"""

import json
import glob
import argparse
import os
import sys

LENDERS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "src", "content", "lenders")

WEIGHTS = {
    "value": 0.20,
    "effectiveness": 0.25,
    "customer_service": 0.20,
    "transparency": 0.15,
    "ease_of_use": 0.20,
}


PREDATORY_CATEGORIES = {
    "payday-loans", "title-loans", "check-cashing", "cash-advance",
    "emergency-cash", "pawn-shop",
}
HIGH_APR_SUBCATEGORIES = {
    "payday-loans", "title-loans", "cash-advance", "bad-credit-loans",
    "subprime-lending", "check-cashing", "emergency-cash",
}

import re

def clamp(val, lo=1.0, hi=5.0):
    return max(lo, min(hi, val))


def detect_cfpb_penalties(d):
    """Scan certifications for CFPB penalty/fine mentions. Returns penalty magnitude."""
    certs = d.get("company_info", {}).get("certifications", [])
    penalty = 0.0
    for cert in certs:
        cert_lower = cert.lower()
        if "cfpb" in cert_lower and ("penalty" in cert_lower or "settlement" in cert_lower
                                      or "redress" in cert_lower or "fine" in cert_lower
                                      or "consent order" in cert_lower or "$" in cert):
            # Extract dollar amounts
            amounts = re.findall(r'\$(\d+(?:\.\d+)?)\s*[MB]', cert, re.IGNORECASE)
            for amt_str in amounts:
                amt = float(amt_str)
                if 'B' in cert[cert.index(amt_str):cert.index(amt_str)+10].upper():
                    amt *= 1000  # billions
                if amt >= 100:  # $100M+
                    penalty = max(penalty, 2.0)
                elif amt >= 10:  # $10M+
                    penalty = max(penalty, 1.5)
                else:
                    penalty = max(penalty, 1.0)
            if not amounts and ("penalty" in cert_lower or "settlement" in cert_lower):
                penalty = max(penalty, 1.0)
    return penalty


def is_predatory_category(d):
    """Check if lender is in a predatory lending category."""
    cat = d.get("category", "")
    subcats = set(d.get("subcategories", []))
    if cat in PREDATORY_CATEGORIES:
        return True
    if subcats & (HIGH_APR_SUBCATEGORIES | PREDATORY_CATEGORIES):
        return True
    return False


def get_google_rating(d):
    """Get Google rating, treating 0 as missing data."""
    g = d.get("google_rating")
    if g is not None and g > 0:
        return g
    return None


def calc_value(d):
    """Dimension 1: Value — How much do you get for what you pay?
    Philosophy: Most legitimate services are reasonably priced. Only penalize
    genuinely expensive or predatory products.
    """
    score = 3.5  # Generous base — most companies are decent value
    pricing = d.get("pricing", {})

    monthly = pricing.get("monthly_price")
    if monthly is not None:
        if monthly == 0:
            score += 1.0
        elif monthly < 50:
            score += 0.3
        elif monthly > 150:
            score -= 1.0  # Only penalize truly expensive
        elif monthly > 100:
            score -= 0.5

    if pricing.get("setup_fee", 0) == 0:
        score += 0.3

    if pricing.get("free_consultation"):
        score += 0.2

    if pricing.get("money_back_guarantee"):
        score += 0.3

    tiers = pricing.get("tiers", [])
    if tiers and len(tiers) > 0:
        score += 0.2

    # Predatory category penalty: "free" payday loans aren't really free (high APR)
    if is_predatory_category(d):
        score -= 3.0

    return clamp(score)


def calc_effectiveness(d):
    """Dimension 2: Effectiveness — Does this company deliver results?
    Philosophy: Assume competent unless proven otherwise. Google reviews and
    CFPB data are the main differentiators.
    """
    score = 3.0  # Decent base — most companies do what they say

    g_rating = get_google_rating(d)
    if g_rating is not None:
        if g_rating >= 4.5:
            score += 1.0
        elif g_rating >= 4.0:
            score += 0.5
        elif g_rating >= 3.5:
            score += 0.2
        elif g_rating < 2.0:
            score -= 1.5  # Truly terrible reviews = real signal
        elif g_rating < 2.5:
            score -= 0.8

    g_reviews = d.get("google_reviews_count")
    if g_reviews is not None:
        if g_reviews >= 500:
            score += 0.3
        elif g_reviews >= 100:
            score += 0.2

    services = d.get("services", [])
    if len(services) >= 5:
        score += 0.3

    if d.get("typical_results_timeline"):
        score += 0.2

    if d.get("diagnosis"):
        score += 0.2

    # CFPB penalty reduces effectiveness score
    cfpb_pen = detect_cfpb_penalties(d)
    if cfpb_pen > 0:
        score -= cfpb_pen * 0.5  # Half the penalty magnitude

    # Predatory lending: high-APR products don't "effectively" help consumers
    if is_predatory_category(d):
        score -= 2.0

    return clamp(score)


def calc_customer_service(d):
    """Dimension 3: Customer Service — Are they responsive and helpful?
    Philosophy: Most companies have acceptable service. BBB/CFPB data
    differentiates the great from the bad.
    """
    score = 3.5  # Most companies provide OK service
    ci = d.get("company_info", {})

    bbb = ci.get("bbb_rating", "").upper().strip()
    if bbb == "A+":
        score += 0.8
    elif bbb == "A":
        score += 0.5
    elif bbb in ("B+", "B"):
        score += 0.2
    elif bbb in ("D+", "D", "D-", "F"):
        score -= 1.0  # Only penalize truly bad BBB
    elif bbb in ("C+", "C", "C-"):
        score -= 0.3

    if ci.get("bbb_accredited"):
        score += 0.3

    cfpb = d.get("cfpb_data", {})
    timely = cfpb.get("timely_response_rate")
    if timely is not None:
        if timely >= 95:
            score += 0.3
        elif timely < 80:
            score -= 0.5

    contact = d.get("contact", {})
    if contact.get("phone") or d.get("phone"):
        score += 0.2

    features = d.get("features", {})
    if features.get("online_portal"):
        score += 0.2

    if features.get("mobile_app"):
        score += 0.1

    # Predatory lenders: service model designed around debt cycle
    if is_predatory_category(d):
        score -= 1.5

    return clamp(score)


def calc_transparency(d):
    """Dimension 4: Transparency — Are they honest about what they do and charge?
    Philosophy: Assume reasonable transparency. CFPB penalties and predatory
    categories are the main red flags.
    """
    score = 3.5  # Most companies are reasonably transparent
    ci = d.get("company_info", {})

    if ci.get("bbb_accredited"):
        score += 0.3

    pricing = d.get("pricing", {})
    tiers = pricing.get("tiers", [])
    if tiers and len(tiers) > 0:
        has_details = any(t.get("features") for t in tiers)
        if has_details:
            score += 0.3

    cfpb = d.get("cfpb_data", {})
    res_rate = cfpb.get("resolution_rate")
    if res_rate is not None:
        if res_rate >= 80:
            score += 0.3
        elif res_rate < 50:
            score -= 1.5  # Terrible resolution = real transparency problem

    # Founded year — check company_info first, fall back to top-level
    founded = ci.get("founded_year") or d.get("founded_year")
    if founded is not None and isinstance(founded, (int, float)):
        if founded <= 2000:
            score += 0.5
        elif founded <= 2010:
            score += 0.3

    certs = ci.get("certifications", [])
    if len(certs) >= 3:
        score += 0.3

    ds = d.get("data_source", "")
    if ds in ("fdic", "ncua", "hud"):
        score += 0.2

    # Major CFPB penalties heavily impact transparency
    cfpb_pen = detect_cfpb_penalties(d)
    if cfpb_pen > 0:
        score -= cfpb_pen  # Full penalty magnitude

    # Predatory categories inherently less transparent
    if is_predatory_category(d):
        score -= 1.5

    return clamp(score)


def calc_ease_of_use(d):
    """Dimension 5: Ease of Use — How easy is it to sign up, use, and manage?
    Philosophy: Most modern companies have decent UX. Bonus for mobile/portal,
    penalty only for truly limited access.
    """
    score = 3.5  # Most companies are reasonably easy to use
    features = d.get("features", {})

    if features.get("online_portal"):
        score += 0.3

    if features.get("mobile_app"):
        score += 0.3

    pricing = d.get("pricing", {})
    if pricing.get("free_consultation"):
        score += 0.2

    states = d.get("states_served", [])
    if len(states) >= 40:
        score += 0.3
    elif len(states) >= 20:
        score += 0.2

    if d.get("website_url") or d.get("website"):
        score += 0.2

    g_rating = get_google_rating(d)
    if g_rating is not None and g_rating >= 4.0:
        score += 0.3

    if features.get("score_tracking"):
        score += 0.1

    return clamp(score)


def calculate_all(d):
    """Calculate all 5 dimensions and overall rating for a lender dict."""
    dims = {
        "value": round(calc_value(d), 1),
        "effectiveness": round(calc_effectiveness(d), 1),
        "customer_service": round(calc_customer_service(d), 1),
        "transparency": round(calc_transparency(d), 1),
        "ease_of_use": round(calc_ease_of_use(d), 1),
    }

    overall = sum(dims[k] * WEIGHTS[k] for k in dims)
    overall = clamp(round(overall, 1))

    return overall, dims


def load_profile(slug):
    path = os.path.join(LENDERS_DIR, f"{slug}.json")
    if not os.path.exists(path):
        return None, path
    with open(path) as f:
        return json.load(f), path


def save_profile(data, path):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def format_comparison(slug, old_rating, old_breakdown, new_rating, new_breakdown):
    """Format a before/after comparison line."""
    changes = []
    for dim in ["value", "effectiveness", "customer_service", "transparency", "ease_of_use"]:
        old_v = old_breakdown.get(dim, 0) if old_breakdown else 0
        new_v = new_breakdown.get(dim, 0)
        diff = new_v - old_v
        if abs(diff) >= 0.1:
            arrow = "+" if diff > 0 else ""
            changes.append(f"{dim[:5]}:{old_v}->{new_v}({arrow}{diff:.1f})")

    old_r = old_rating or 0
    diff_overall = new_rating - old_r
    arrow = "+" if diff_overall > 0 else ""
    change_str = " | ".join(changes) if changes else "no change"

    return (f"  {slug:<45} {old_r:.1f} -> {new_rating:.1f} ({arrow}{diff_overall:.1f})  "
            f"[{change_str}]")


def main():
    parser = argparse.ArgumentParser(description="CreditDoc Star Rating Calculator")
    parser.add_argument("--slug", help="Calculate for a single profile")
    parser.add_argument("--apply", action="store_true", help="Write ratings back to JSON files")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Show what would change (default)")
    parser.add_argument("--enriched-only", action="store_true", default=True,
                        help="Only process enriched profiles (default)")
    parser.add_argument("--indexed-only", action="store_true",
                        help="Only process indexed (no_index=false) profiles")
    parser.add_argument("--all", action="store_true",
                        help="Process ALL lender profiles")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show dimension details for each profile")
    args = parser.parse_args()

    if args.apply:
        args.dry_run = False

    if args.slug:
        data, path = load_profile(args.slug)
        if data is None:
            print(f"Profile not found: {args.slug}")
            sys.exit(1)
        profiles = [(data, path)]
    else:
        profiles = []
        for fpath in sorted(glob.glob(os.path.join(LENDERS_DIR, "*.json"))):
            try:
                with open(fpath) as f:
                    d = json.load(f)
            except (json.JSONDecodeError, IOError):
                continue

            if not args.all:
                if args.indexed_only:
                    if d.get("no_index", True):
                        continue
                if args.enriched_only and not d.get("has_been_enriched"):
                    continue

            profiles.append((d, fpath))

    print(f"Processing {len(profiles)} profiles...")
    print(f"Mode: {'APPLY (writing changes)' if args.apply else 'DRY RUN (preview only)'}")
    print()

    changed = 0
    unchanged = 0
    results = []

    for data, path in profiles:
        slug = data.get("slug", os.path.basename(path).replace(".json", ""))
        old_rating = data.get("rating")
        old_breakdown = data.get("rating_breakdown")

        new_rating, new_breakdown = calculate_all(data)

        rating_changed = (old_rating != new_rating or old_breakdown != new_breakdown)

        if rating_changed:
            changed += 1
            line = format_comparison(slug, old_rating, old_breakdown, new_rating, new_breakdown)
            results.append(("CHANGE", line))

            if args.verbose:
                results.append(("DETAIL", f"    V:{new_breakdown['value']} E:{new_breakdown['effectiveness']} "
                                          f"CS:{new_breakdown['customer_service']} T:{new_breakdown['transparency']} "
                                          f"EU:{new_breakdown['ease_of_use']}"))

            if args.apply:
                data["rating"] = new_rating
                data["rating_breakdown"] = new_breakdown
                save_profile(data, path)
        else:
            unchanged += 1
            if args.verbose:
                results.append(("SAME", f"  {slug:<45} {new_rating:.1f} (unchanged)"))

    # Print results grouped
    print("=" * 100)
    print(f"{'SLUG':<47} {'OLD':>5} -> {'NEW':>5} {'DIFF':>7}  DIMENSION CHANGES")
    print("=" * 100)

    for kind, line in results:
        if kind in ("CHANGE", "DETAIL"):
            print(line)
        elif kind == "SAME" and args.verbose:
            print(line)

    print()
    print(f"Summary: {changed} changed, {unchanged} unchanged, {len(profiles)} total")

    if not args.apply and changed > 0:
        print(f"\nRun with --apply to write changes to disk.")


if __name__ == "__main__":
    main()
