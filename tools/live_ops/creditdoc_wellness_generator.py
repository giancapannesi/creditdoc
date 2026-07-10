#!/usr/bin/env python3
"""
CreditDoc — Wellness Guide Generator

Generates financial wellness guides using OpenAI.
Appends to wellness-guides.json — NEVER overwrites existing entries.

Usage:
    python3 tools/creditdoc_wellness_generator.py                    # Generate next 2 from queue
    python3 tools/creditdoc_wellness_generator.py --count 5          # Generate 5
    python3 tools/creditdoc_wellness_generator.py --dry-run          # Show what would be generated
    python3 tools/creditdoc_wellness_generator.py --list-queue       # Show remaining queue
    python3 tools/creditdoc_wellness_generator.py --build            # Build + push after generating

Cron:
    0 15 * * * /srv/BusinessOps/.venv/bin/python3 /srv/BusinessOps/tools/creditdoc_wellness_generator.py --count 2 --build
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from creditdoc_oauth import call_ai
from creditdoc_content_guardrails import reject_if_unsafe
from creditdoc_content_repair import repair_unsafe_json

# === CONFIG ===
PROJECT_DIR = "/srv/BusinessOps/creditdoc"
GUIDES_FILE = os.path.join(PROJECT_DIR, "src/content/wellness-guides.json")
SITE_URL = "https://creditdoc.co"
INDEXNOW_KEY = "1efee5eebbd54ea4812e2e77a9b73fcc"
TODAY = datetime.now().strftime("%Y-%m-%d")
YEAR = datetime.now().strftime("%Y")

# === CreditDoc DB API (Phase 3 dual-write — 2026-04-09) ===
sys.path.insert(0, os.path.join(PROJECT_DIR, "tools"))
try:
    from creditdoc_db import CreditDocDB
    HAS_PERSISTENCE_DB = True
except Exception:
    HAS_PERSISTENCE_DB = False

TELEGRAM_TOKEN = "8552358080:AAFC8FjKxQdj_NJyqwMbgUZrxKzUrn83tGY"
TELEGRAM_CHAT_ID = "1351661181"

# === GUIDE QUEUE ===
# Ordered by cluster priority (highest affiliate revenue first).
# Script skips any slug already in wellness-guides.json.
GUIDE_QUEUE = [
    # --- Fix My Credit cluster (highest revenue: $65-200/sale) ---
    {"slug": "how-credit-repair-works", "title": "How Credit Repair Actually Works (Step by Step)", "category": "credit-repair", "category_label": "Credit Repair"},
    {"slug": "diy-vs-credit-repair-company", "title": "DIY Credit Repair vs Hiring a Company: Which Is Right for You?", "category": "credit-repair", "category_label": "Credit Repair"},
    {"slug": "dispute-credit-report-errors", "title": "How to Dispute Errors on Your Credit Report (2026 Guide)", "category": "credit-repair", "category_label": "Credit Repair"},
    {"slug": "what-credit-repair-companies-do", "title": "What Credit Repair Companies Can and Can't Legally Do", "category": "credit-repair", "category_label": "Credit Repair"},
    {"slug": "credit-repair-scams", "title": "Credit Repair Scams: 8 Red Flags to Watch For", "category": "credit-repair", "category_label": "Credit Repair"},
    {"slug": "how-long-credit-repair-takes", "title": "How Long Does Credit Repair Take? Realistic Timelines", "category": "credit-repair", "category_label": "Credit Repair"},
    {"slug": "credit-repair-after-bankruptcy", "title": "Credit Repair After Bankruptcy: A Complete Recovery Plan", "category": "credit-repair", "category_label": "Credit Repair"},
    {"slug": "credit-repair-for-veterans", "title": "Credit Repair for Veterans: Programs and Resources", "category": "credit-repair", "category_label": "Credit Repair"},
    {"slug": "credit-repair-rights-fcra-croa", "title": "Your Legal Rights: FCRA and CROA Explained in Plain English", "category": "credit-repair", "category_label": "Credit Repair"},
    {"slug": "choosing-credit-repair-company", "title": "How to Choose a Credit Repair Company (Without Getting Ripped Off)", "category": "credit-repair", "category_label": "Credit Repair"},

    # --- Financial Recovery / Debt cluster ($27-1,000/referral) ---
    {"slug": "debt-settlement-explained", "title": "Debt Settlement Explained: How It Works, Costs, and Risks", "category": "financial-recovery", "category_label": "Financial Recovery"},
    {"slug": "debt-consolidation-guide", "title": "Debt Consolidation: Pros, Cons, and How to Qualify", "category": "financial-recovery", "category_label": "Financial Recovery"},
    {"slug": "bankruptcy-alternatives", "title": "5 Alternatives to Bankruptcy You Should Try First", "category": "financial-recovery", "category_label": "Financial Recovery"},
    {"slug": "dealing-with-debt-collectors", "title": "How to Deal with Debt Collectors: Your Rights and Scripts", "category": "financial-recovery", "category_label": "Financial Recovery"},
    {"slug": "medical-debt-guide", "title": "Medical Debt: New Rules, Negotiation Tactics, and Your Rights", "category": "financial-recovery", "category_label": "Financial Recovery"},
    {"slug": "student-loan-repayment", "title": "Student Loan Repayment Options: IDR, PSLF, and When to Refinance", "category": "financial-recovery", "category_label": "Financial Recovery"},
    {"slug": "credit-after-foreclosure", "title": "Rebuilding Credit After Foreclosure: Year-by-Year Timeline", "category": "financial-recovery", "category_label": "Financial Recovery"},

    # --- Loans & Interest cluster ($110-350/lead) ---
    {"slug": "personal-loans-bad-credit", "title": "Personal Loans for Bad Credit: Where to Apply and What to Expect", "category": "loans-and-interest", "category_label": "Loans & Interest"},
    {"slug": "secured-vs-unsecured-loans", "title": "Secured vs Unsecured Loans: Which Should You Choose?", "category": "loans-and-interest", "category_label": "Loans & Interest"},
    {"slug": "payday-loan-alternatives", "title": "Payday Loan Alternatives That Won't Trap You in Debt", "category": "loans-and-interest", "category_label": "Loans & Interest"},
    {"slug": "auto-loans-bad-credit", "title": "Auto Loans with Bad Credit: How to Get Approved Without Overpaying", "category": "loans-and-interest", "category_label": "Loans & Interest"},
    {"slug": "understanding-loan-terms", "title": "Understanding Loan Terms: APR, Origination Fees, and Fine Print", "category": "loans-and-interest", "category_label": "Loans & Interest"},
    {"slug": "refinancing-guide", "title": "When and How to Refinance: Auto Loans, Personal Loans, and Mortgages", "category": "loans-and-interest", "category_label": "Loans & Interest"},

    # --- Understanding Credit cluster (trust builder) ---
    {"slug": "credit-utilization-guide", "title": "Credit Utilization: The Factor That Can Change Your Score Fastest", "category": "understanding-credit", "category_label": "Understanding Credit"},
    {"slug": "authorized-user-strategy", "title": "Authorized User Strategy: Piggyback on Someone Else's Credit", "category": "understanding-credit", "category_label": "Understanding Credit"},
    {"slug": "hard-vs-soft-inquiries", "title": "Hard vs Soft Credit Inquiries: What Hurts Your Score?", "category": "understanding-credit", "category_label": "Understanding Credit"},
    {"slug": "credit-freeze-vs-lock", "title": "Credit Freeze vs Credit Lock: Which Protects You Better?", "category": "understanding-credit", "category_label": "Understanding Credit"},
    {"slug": "credit-for-immigrants", "title": "Building Credit as an Immigrant: A Step-by-Step Guide", "category": "understanding-credit", "category_label": "Understanding Credit"},

    # --- Build Credit cluster ---
    {"slug": "secured-credit-cards-guide", "title": "Best Secured Credit Cards for Building Credit (2026)", "category": "building-credit", "category_label": "Building Credit"},
    {"slug": "credit-builder-loans", "title": "Credit Builder Loans: How They Work and Who They're For", "category": "building-credit", "category_label": "Building Credit"},
    {"slug": "building-credit-from-zero", "title": "Building Credit from Scratch: The Complete Beginner's Guide", "category": "building-credit", "category_label": "Building Credit"},
    {"slug": "credit-for-young-adults", "title": "Credit for Young Adults: What to Do in Your 18-25 Years", "category": "building-credit", "category_label": "Building Credit"},

    # --- Everyday Finance cluster ---
    {"slug": "checking-savings-guide", "title": "Checking vs Savings Accounts: What You Actually Need", "category": "everyday-finance", "category_label": "Everyday Finance"},
    {"slug": "credit-card-vs-debit", "title": "Credit Card vs Debit Card: When to Use Each", "category": "everyday-finance", "category_label": "Everyday Finance"},
    {"slug": "understanding-your-paycheck", "title": "Understanding Your Paycheck: Taxes, Deductions, and Take-Home Pay", "category": "everyday-finance", "category_label": "Everyday Finance"},
    {"slug": "financial-literacy-basics", "title": "Financial Literacy 101: The 10 Things Nobody Taught You About Money", "category": "everyday-finance", "category_label": "Everyday Finance"},

    # === WAVE 2 (added Mar 26) — 30 more high-intent topics ===

    # --- Credit Repair (revenue driver) ---
    {"slug": "goodwill-letter-template", "title": "Goodwill Letters: How to Get Late Payments Removed (With Templates)", "category": "credit-repair", "category_label": "Credit Repair"},
    {"slug": "pay-for-delete-guide", "title": "Pay for Delete: Does It Still Work in 2026?", "category": "credit-repair", "category_label": "Credit Repair"},
    {"slug": "credit-repair-after-divorce", "title": "Credit Repair After Divorce: Protecting Your Score During a Split", "category": "credit-repair", "category_label": "Credit Repair"},
    {"slug": "remove-collections-from-credit", "title": "How to Remove Collections From Your Credit Report", "category": "credit-repair", "category_label": "Credit Repair"},
    {"slug": "609-dispute-letter-truth", "title": "Section 609 Dispute Letters: What They Actually Do (and Don't Do)", "category": "credit-repair", "category_label": "Credit Repair"},

    # --- Financial Recovery ---
    {"slug": "wage-garnishment-guide", "title": "Wage Garnishment: How to Stop It and Protect Your Paycheck", "category": "financial-recovery", "category_label": "Financial Recovery"},
    {"slug": "debt-snowball-vs-avalanche", "title": "Debt Snowball vs Avalanche: Which Payoff Method Works Faster?", "category": "financial-recovery", "category_label": "Financial Recovery"},
    {"slug": "statute-of-limitations-debt", "title": "Statute of Limitations on Debt: When Collectors Can't Sue You", "category": "financial-recovery", "category_label": "Financial Recovery"},
    {"slug": "credit-counseling-guide", "title": "Nonprofit Credit Counseling: What to Expect and How to Find One", "category": "financial-recovery", "category_label": "Financial Recovery"},
    {"slug": "irs-tax-debt-options", "title": "IRS Tax Debt: Payment Plans, Offers in Compromise, and Fresh Start", "category": "financial-recovery", "category_label": "Financial Recovery"},

    # --- Loans & Interest ---
    {"slug": "cosigner-guide", "title": "Should You Get a Cosigner? Risks, Benefits, and Alternatives", "category": "loans-and-interest", "category_label": "Loans & Interest"},
    {"slug": "debt-to-income-ratio", "title": "Debt-to-Income Ratio: Why Lenders Care and How to Improve Yours", "category": "loans-and-interest", "category_label": "Loans & Interest"},
    {"slug": "loan-prequalification-guide", "title": "Prequalification vs Preapproval: What's the Difference?", "category": "loans-and-interest", "category_label": "Loans & Interest"},
    {"slug": "title-loans-dangers", "title": "Car Title Loans: Why They're Dangerous and What to Do Instead", "category": "loans-and-interest", "category_label": "Loans & Interest"},
    {"slug": "small-business-loans-bad-credit", "title": "Small Business Loans with Bad Credit: Your Realistic Options", "category": "loans-and-interest", "category_label": "Loans & Interest"},

    # --- Understanding Credit ---
    {"slug": "credit-score-ranges-explained", "title": "Credit Score Ranges: What's Good, Fair, and Bad in 2026", "category": "understanding-credit", "category_label": "Understanding Credit"},
    {"slug": "vantagescore-vs-fico", "title": "VantageScore vs FICO: Why You Have Multiple Credit Scores", "category": "understanding-credit", "category_label": "Understanding Credit"},
    {"slug": "credit-report-reading-guide", "title": "How to Read Your Credit Report Line by Line", "category": "understanding-credit", "category_label": "Understanding Credit"},
    {"slug": "how-credit-scores-calculated", "title": "How Credit Scores Are Calculated: The 5 Factors Explained", "category": "understanding-credit", "category_label": "Understanding Credit"},
    {"slug": "credit-myths-debunked", "title": "12 Credit Myths That Are Costing You Money", "category": "understanding-credit", "category_label": "Understanding Credit"},

    # --- Building Credit ---
    {"slug": "rent-reporting-services", "title": "Rent Reporting Services: Build Credit by Paying Rent", "category": "building-credit", "category_label": "Building Credit"},
    {"slug": "credit-building-after-prison", "title": "Building Credit After Incarceration: A Fresh Start Guide", "category": "building-credit", "category_label": "Building Credit"},
    {"slug": "joint-accounts-credit", "title": "Joint Accounts and Credit: How Shared Finances Affect Your Score", "category": "building-credit", "category_label": "Building Credit"},

    # --- Budgeting & Saving ---
    {"slug": "emergency-fund-guide", "title": "Emergency Fund: How Much You Need and Where to Keep It", "category": "budgeting-and-saving", "category_label": "Budgeting & Saving"},
    {"slug": "50-30-20-budget-rule", "title": "The 50/30/20 Budget Rule: A Simple System That Works", "category": "budgeting-and-saving", "category_label": "Budgeting & Saving"},
    {"slug": "living-paycheck-to-paycheck", "title": "Breaking the Paycheck-to-Paycheck Cycle: Practical Steps", "category": "budgeting-and-saving", "category_label": "Budgeting & Saving"},
    {"slug": "saving-on-low-income", "title": "How to Save Money on a Low Income: 15 Strategies That Work", "category": "budgeting-and-saving", "category_label": "Budgeting & Saving"},
    {"slug": "bank-fees-avoid", "title": "Bank Fees You're Probably Paying (and How to Stop)", "category": "budgeting-and-saving", "category_label": "Budgeting & Saving"},

    # --- Everyday Finance ---
    {"slug": "identity-theft-recovery", "title": "Identity Theft Recovery: Step-by-Step Action Plan", "category": "everyday-finance", "category_label": "Everyday Finance"},
    {"slug": "financial-planning-single-parents", "title": "Financial Planning for Single Parents: Making Every Dollar Count", "category": "everyday-finance", "category_label": "Everyday Finance"},

    # === WAVE 3 (added May 12) — 40 topics filling coverage gaps ===

    # --- Protection & Identity (only 1 guide existed) ---
    {"slug": "identity-theft-prevention", "title": "How to Prevent Identity Theft: 10 Steps That Actually Work", "category": "everyday-finance", "category_label": "Everyday Finance"},
    {"slug": "credit-monitoring-explained", "title": "Credit Monitoring: Free vs Paid Services and Which You Need", "category": "everyday-finance", "category_label": "Everyday Finance"},
    {"slug": "fraud-alerts-explained", "title": "Fraud Alerts vs Credit Freezes: Which Protection Is Right for You?", "category": "everyday-finance", "category_label": "Everyday Finance"},
    {"slug": "phishing-scam-protection", "title": "Financial Phishing Scams: How to Spot and Avoid Them in 2026", "category": "everyday-finance", "category_label": "Everyday Finance"},
    {"slug": "dark-web-monitoring-guide", "title": "Dark Web Monitoring: Is It Worth It for Your Financial Safety?", "category": "everyday-finance", "category_label": "Everyday Finance"},

    # --- Budgeting & Saving (only 6 existed) ---
    {"slug": "side-hustle-income-guide", "title": "Side Hustles to Pay Off Debt Faster: What Actually Works in 2026", "category": "budgeting-and-saving", "category_label": "Budgeting & Saving"},
    {"slug": "automating-your-finances", "title": "How to Automate Your Finances: Bills, Savings, and Debt Payments", "category": "budgeting-and-saving", "category_label": "Budgeting & Saving"},
    {"slug": "grocery-budget-tips", "title": "How to Cut Your Grocery Bill in Half Without Couponing", "category": "budgeting-and-saving", "category_label": "Budgeting & Saving"},
    {"slug": "high-yield-savings-guide", "title": "High-Yield Savings Accounts: Where to Park Your Emergency Fund", "category": "budgeting-and-saving", "category_label": "Budgeting & Saving"},
    {"slug": "financial-goals-setting", "title": "Setting Financial Goals You'll Actually Achieve: A Realistic Framework", "category": "budgeting-and-saving", "category_label": "Budgeting & Saving"},
    {"slug": "no-spend-challenge", "title": "The No-Spend Challenge: Reset Your Spending Habits in 30 Days", "category": "budgeting-and-saving", "category_label": "Budgeting & Saving"},
    {"slug": "subscription-audit-guide", "title": "Subscription Audit: Find and Cancel Hidden Recurring Charges", "category": "budgeting-and-saving", "category_label": "Budgeting & Saving"},

    # --- Loans & Borrowing (only 8 existed) ---
    {"slug": "home-equity-loans-guide", "title": "Home Equity Loans and HELOCs: When They Make Sense", "category": "loans-and-interest", "category_label": "Loans & Interest"},
    {"slug": "peer-to-peer-lending", "title": "Peer-to-Peer Lending: An Alternative to Traditional Bank Loans", "category": "loans-and-interest", "category_label": "Loans & Interest"},
    {"slug": "buy-here-pay-here-risks", "title": "Buy Here Pay Here Dealerships: The Real Cost of Easy Approval", "category": "loans-and-interest", "category_label": "Loans & Interest"},
    {"slug": "loan-modification-guide", "title": "Loan Modification: How to Renegotiate When You Can't Pay", "category": "loans-and-interest", "category_label": "Loans & Interest"},
    {"slug": "consolidation-loan-qualify", "title": "How to Qualify for a Debt Consolidation Loan with Bad Credit", "category": "loans-and-interest", "category_label": "Loans & Interest"},
    {"slug": "credit-union-vs-bank-loans", "title": "Credit Unions vs Banks: Where to Get a Better Loan Deal", "category": "loans-and-interest", "category_label": "Loans & Interest"},
    {"slug": "predatory-lending-signs", "title": "Predatory Lending: Warning Signs and How to Protect Yourself", "category": "loans-and-interest", "category_label": "Loans & Interest"},

    # --- Credit Building (expanding) ---
    {"slug": "credit-after-50", "title": "Rebuilding Credit After 50: It's Never Too Late", "category": "building-credit", "category_label": "Building Credit"},
    {"slug": "first-credit-card-guide", "title": "Your First Credit Card: How to Choose and Use It Responsibly", "category": "building-credit", "category_label": "Building Credit"},
    {"slug": "credit-limit-increase-guide", "title": "How to Get a Credit Limit Increase (and Why It Helps Your Score)", "category": "building-credit", "category_label": "Building Credit"},
    {"slug": "store-credit-cards-worth-it", "title": "Store Credit Cards: Are They Worth It for Building Credit?", "category": "building-credit", "category_label": "Building Credit"},
    {"slug": "credit-building-apps", "title": "Credit Building Apps: Chime, Self, and Grow Credit Compared", "category": "building-credit", "category_label": "Building Credit"},

    # --- Financial Recovery (expanding) ---
    {"slug": "negotiating-medical-bills", "title": "How to Negotiate Medical Bills: Scripts and Strategies That Work", "category": "financial-recovery", "category_label": "Financial Recovery"},
    {"slug": "debt-validation-letters", "title": "Debt Validation Letters: Your First Defense Against Collectors", "category": "financial-recovery", "category_label": "Financial Recovery"},
    {"slug": "credit-card-debt-payoff", "title": "How to Pay Off Credit Card Debt: The Fastest Methods Ranked", "category": "financial-recovery", "category_label": "Financial Recovery"},
    {"slug": "debt-management-plan-guide", "title": "Debt Management Plans: How They Work and Who They Help", "category": "financial-recovery", "category_label": "Financial Recovery"},
    {"slug": "financial-fresh-start", "title": "Financial Fresh Start: A 90-Day Reset Plan for Any Situation", "category": "financial-recovery", "category_label": "Financial Recovery"},

    # --- Understanding Credit (expanding) ---
    {"slug": "credit-age-explained", "title": "Average Age of Credit: Why Old Accounts Matter", "category": "understanding-credit", "category_label": "Understanding Credit"},
    {"slug": "credit-mix-explained", "title": "Credit Mix: Does Having Different Types of Credit Really Help?", "category": "understanding-credit", "category_label": "Understanding Credit"},
    {"slug": "late-payment-impact", "title": "How One Late Payment Affects Your Credit Score (and Recovery Timeline)", "category": "understanding-credit", "category_label": "Understanding Credit"},
    {"slug": "credit-score-after-paying-debt", "title": "Why Your Credit Score Drops After Paying Off Debt (and What to Do)", "category": "understanding-credit", "category_label": "Understanding Credit"},
    {"slug": "credit-report-errors-common", "title": "The 5 Most Common Credit Report Errors and How to Fix Them", "category": "understanding-credit", "category_label": "Understanding Credit"},

    # --- Everyday Finance (expanding) ---
    {"slug": "balance-transfer-guide", "title": "Balance Transfer Credit Cards: How to Use Them Without Getting Burned", "category": "everyday-finance", "category_label": "Everyday Finance"},
    {"slug": "cash-advance-alternatives", "title": "Cash Advance Alternatives: Better Ways to Get Money Fast", "category": "everyday-finance", "category_label": "Everyday Finance"},
    {"slug": "financial-literacy-for-teens", "title": "Financial Literacy for Teens: What to Teach Before They Turn 18", "category": "everyday-finance", "category_label": "Everyday Finance"},
    {"slug": "couples-money-management", "title": "Managing Money as a Couple: Joint, Separate, or Hybrid Accounts", "category": "everyday-finance", "category_label": "Everyday Finance"},
    {"slug": "apr-explained-simply", "title": "APR Explained: What It Really Costs You in Dollars", "category": "everyday-finance", "category_label": "Everyday Finance"},
]

QUALITY_QUARANTINE_SLUGS = {
    # 2026-06-02: Opus CLI timed out at 240s and 420s; fallback output was
    # rejected twice at ~1,200 words against the 1,500-word quality floor.
    "credit-score-after-paying-debt",
}


def load_existing_guides():
    """Load existing guides from JSON file."""
    with open(GUIDES_FILE) as f:
        return json.load(f)


def get_queue(existing_slugs):
    """Return guides that haven't been generated yet.
    Auto-generates new topics when queue drops below 10 (never runs dry)."""
    remaining = [
        g for g in GUIDE_QUEUE
        if g["slug"] not in existing_slugs and g["slug"] not in QUALITY_QUARANTINE_SLUGS
    ]
    if len(remaining) >= 10:
        return remaining
    # Queue is low or empty — auto-generate new topics from answer pages
    new_topics = _generate_new_topics(existing_slugs, count=20)
    if new_topics:
        return remaining + new_topics
    return remaining


def _fetch_answer_titles():
    """Pull answer page titles from Supabase to inform topic generation."""
    try:
        import urllib.request as ur
        import urllib.parse
        env = {}
        for line in open("/srv/BusinessOps/tools/.supabase-creditdoc.env"):
            if '=' in line and not line.startswith('#'):
                k, v = line.strip().split('=', 1)
                env[k] = v.strip('"').strip("'")
        hdr = {
            'apikey': env['SUPABASE_SERVICE_ROLE_KEY'],
            'Authorization': f"Bearer {env['SUPABASE_SERVICE_ROLE_KEY']}",
            'Accept': 'application/json',
        }
        url = f"{env['SUPABASE_URL'].rstrip('/')}/rest/v1/answers?select=slug,title&limit=200"
        req = ur.Request(url, headers=hdr)
        with ur.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception:
        return []


def _generate_new_topics(existing_slugs, count=20):
    """Use OpenAI to generate new wellness topic ideas based on coverage gaps.

    Pulls from the answers table to ensure new guides are coherent with
    the questions people are actually asking on the site.
    """
    categories = {
        "understanding-credit": "Understanding Credit",
        "building-credit": "Building Credit",
        "credit-repair": "Credit Repair",
        "financial-recovery": "Financial Recovery",
        "loans-and-interest": "Loans & Interest",
        "everyday-finance": "Everyday Finance",
        "budgeting-and-saving": "Budgeting & Saving",
        "protection-identity": "Protection & Identity",
    }
    existing_list = ", ".join(sorted(existing_slugs)[:80])

    # Pull real questions from the answers table
    answers = _fetch_answer_titles()
    answer_titles = [a['title'].replace(' | CreditDoc', '') for a in answers]
    answers_section = ""
    if answer_titles:
        answers_section = f"""
QUESTIONS PEOPLE ARE ASKING ON OUR SITE (generate guides that go deeper on these topics):
{chr(10).join(f'- {t}' for t in answer_titles[:40])}

Each wellness guide should expand on or complement one of these questions — providing the
in-depth, step-by-step guide that someone asking that question actually needs.
"""

    prompt = f"""Generate {count} NEW financial wellness guide topics for CreditDoc.co.

EXISTING GUIDES (do NOT repeat these or anything similar):
{existing_list}
{answers_section}
CATEGORIES (pick from these, distribute evenly):
{json.dumps(categories, indent=2)}

TARGET AUDIENCE: People with bad/fair credit, financial struggles, looking for practical help.

OUTPUT FORMAT — respond with ONLY a JSON array, no markdown, no explanation:
[
  {{"slug": "topic-slug-here", "title": "Clear Actionable Title (Year)", "category": "category-key", "category_label": "Category Label"}},
  ...
]

RULES:
- Slugs must be unique, lowercase, hyphenated, 3-6 words
- Titles must be specific and actionable, not generic
- Include the year (2026) where it helps SEO
- Focus on high-intent topics people actually search for
- Each topic should be a DEEPER guide that complements an existing answer page
- Mix evergreen fundamentals with timely topics
- Think about what someone would search AFTER reading one of the answer pages above
"""
    try:
        result = call_ai(prompt, model="gpt-4.1")
        text = result.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        topics = json.loads(text)
        topics = [t for t in topics if t.get("slug") not in existing_slugs]
        if topics:
            print(f"  Auto-generated {len(topics)} new topics from answer-page analysis")
        return topics
    except Exception as e:
        print(f"  Auto-topic generation failed: {e}")
        return []


def generate_guide(topic):
    """Generate a wellness guide using OpenAI."""
    slug = topic["slug"]
    title = topic["title"]
    category = topic["category"]
    category_label = topic["category_label"]

    # Load existing guide slugs for cross-linking
    existing = load_existing_guides()
    same_cat = [g["slug"] for g in existing if g["category"] == category and g["slug"] != slug]
    other_cats = [g["slug"] for g in existing if g["category"] != category]

    # Pick related guides (2 same category + 1 different)
    import random
    related = same_cat[:2]
    if other_cats:
        related.append(random.choice(other_cats))

    # Map category to related lender categories
    cat_to_lender = {
        "credit-repair": ["fix-my-credit", "credit-monitoring", "build-credit"],
        "financial-recovery": ["debt-relief", "free-help", "fix-my-credit"],
        "loans-and-interest": ["personal-loans", "emergency-cash", "payday-alternatives"],
        "understanding-credit": ["fix-my-credit", "build-credit", "credit-monitoring"],
        "building-credit": ["build-credit", "credit-monitoring", "personal-loans"],
        "everyday-finance": ["personal-loans", "build-credit", "free-help"],
        "budgeting-and-saving": ["free-help", "debt-relief", "build-credit"],
    }
    related_categories = cat_to_lender.get(category, ["fix-my-credit", "build-credit"])

    prompt = f"""Generate a comprehensive financial wellness guide for CreditDoc.co.

TOPIC: {title}
CATEGORY: {category_label}
SLUG: {slug}

REQUIREMENTS:
- Write for people with bad/fair credit or financial struggles. Plain language, no jargon.
- Voice: direct, specific, actionable. Not "consider consulting an advisor" but "here's what to do."
- 6-8 sections, each 200-400 words. Total: 1,500-2,500 words.
- Include specific numbers, percentages, and real examples only where they are stable, sourced, and useful.
- Reference relevant laws (FCRA, CROA, FDCPA, TCPA) where applicable.
- 3-5 key takeaways (one sentence each, actionable).
- 3 FAQ questions with 2-3 sentence answers.
- SEO title under 60 chars, meta description under 155 chars.
- Estimated read time (e.g., "8 min").
- Do NOT invent current prices, fees, APRs, BBB ratings, Google ratings, star ratings, or guarantees for any company, lender, app, card, or service.
- If a current provider-specific price/rate/rating/guarantee is not supplied in this prompt, omit it or say readers should verify current terms directly with the provider.
- Generic educational ranges are allowed only when clearly framed as general context, not as a claim about a named provider.

OUTPUT FORMAT (strict JSON, no markdown):
{{
  "slug": "{slug}",
  "title": "{title}",
  "category": "{category}",
  "category_label": "{category_label}",
  "description": "1-2 sentence description for cards/previews",
  "seo_title": "SEO title under 60 chars with (2026) and | CreditDoc",
  "seo_description": "Meta description under 155 chars",
  "read_time": "X min",
  "last_updated": "{TODAY}",
  "sections": [
    {{"heading": "Section Title", "content": "Full section text with **bold** for emphasis. Use \\n\\n between paragraphs."}},
    ...
  ],
  "key_takeaways": ["takeaway 1", "takeaway 2", ...],
  "related_guides": {json.dumps(related)},
  "related_categories": {json.dumps(related_categories)},
  "faq": [
    {{"question": "Question?", "answer": "Answer text."}},
    ...
  ]
}}

IMPORTANT: Output ONLY the JSON object. No markdown, no code fences, no explanation."""

    print(f"  Generating: {title}...")
    try:
        output = call_ai(prompt, model="gpt-4.1")

        # Clean any markdown fences or short assistant prefaces.
        if "```json" in output:
            output = output.split("```json")[1].split("```")[0].strip()
        elif "```" in output:
            output = output.split("```")[1].split("```")[0].strip()
        else:
            match = re.search(r"\{.*\}", output, re.DOTALL)
            if match:
                output = match.group(0).strip()

        guide = json.loads(output)

        # Validate required fields
        required = ["slug", "title", "category", "sections", "faq", "key_takeaways"]
        for field in required:
            if field not in guide:
                print(f"  ERROR: Missing field '{field}'")
                return None

        if len(guide["sections"]) < 6:
            print(f"  REJECT: Only {len(guide['sections'])} sections (expected 6-8)")
            return None

        guardrail_failures = reject_if_unsafe(guide)
        if guardrail_failures:
            print("  REPAIR: CreditDoc guardrails failed; attempting content repair")
            guide, guardrail_failures = repair_unsafe_json(
                guide,
                guardrail_failures,
                content_type="financial wellness guide",
                source_context=(
                    f"Guide title: {title}\n"
                    f"Category: {category}\n"
                    "Use evergreen education only. Do not add current company prices, APRs, ratings, review counts, guarantees, or approval odds."
                ),
                max_tokens=8192,
            )
        if guardrail_failures:
            print("  REJECT: CreditDoc guardrails failed")
            for failure in guardrail_failures[:8]:
                print(f"    - {failure}")
            return None

        # Ensure correct metadata
        guide["slug"] = slug
        guide["last_updated"] = TODAY
        guide["related_guides"] = related
        guide["related_categories"] = related_categories

        word_count = sum(len(s["content"].split()) for s in guide["sections"])
        if word_count < 1500:
            print(f"  REJECT: Only {word_count} words — below CreditDoc wellness quality floor")
            return None
        print(f"  OK: {len(guide['sections'])} sections, {word_count} words, {len(guide['faq'])} FAQs")
        return guide

    except json.JSONDecodeError as e:
        print(f"  ERROR: Invalid JSON from OpenAI: {e}")
        debug_path = f"/tmp/creditdoc_guide_debug_{slug}.txt"
        with open(debug_path, "w") as f:
            f.write(output)
        print(f"  Raw output saved to {debug_path}")
        return None
    except Exception as e:
        print(f"  ERROR: {e}")
        return None


def save_guides(existing, new_guides):
    """Append new guides to the JSON file AND mirror to DB. NEVER overwrites existing."""
    combined = existing + new_guides
    # Write to JSON file (legacy, for Astro build)
    with open(GUIDES_FILE, "w") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(combined)} total guides ({len(new_guides)} new)")

    # Dual-write: mirror new guides to persistence DB (Phase 3)
    if HAS_PERSISTENCE_DB and new_guides:
        try:
            with CreditDocDB() as db:
                added = 0
                for guide in new_guides:
                    if not isinstance(guide, dict) or 'slug' not in guide:
                        continue
                    try:
                        db.add_wellness_guide(guide, updated_by='wellness_generator')
                        added += 1
                    except Exception as e:
                        print(f"    DB add failed for {guide.get('slug', '?')}: {e}")
                print(f"    DB mirror: {added}/{len(new_guides)} new wellness guides added")
        except Exception as e:
            print(f"    DB mirror write failed: {type(e).__name__}: {e}")


def build_and_push(new_slugs):
    """Build Astro site, commit, push, and ping IndexNow."""
    os.chdir(PROJECT_DIR)

    print("Building site...")
    result = subprocess.run(["npx", "astro", "build"], capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        print(f"BUILD FAILED: {result.stderr[-500:]}")
        return False

    print("Committing...")
    subprocess.run(["git", "add", "src/content/wellness-guides.json"], check=True)
    msg = f"Add {len(new_slugs)} wellness guides: {', '.join(new_slugs[:5])}"
    if len(new_slugs) > 5:
        msg += f" (+{len(new_slugs)-5} more)"
    subprocess.run(["git", "commit", "-m", msg], check=True)

    print("Pushing...")
    subprocess.run(["git", "push", "origin", "HEAD"], check=True)

    # IndexNow
    urls = [f"{SITE_URL}/financial-wellness/{s}/" for s in new_slugs]
    urls.append(f"{SITE_URL}/financial-wellness/")
    payload = json.dumps({
        "host": "www.creditdoc.co",
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
    parser = argparse.ArgumentParser(description="CreditDoc Wellness Guide Generator")
    parser.add_argument("--count", type=int, default=2, help="Number of guides to generate")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be generated")
    parser.add_argument("--list-queue", action="store_true", help="Show remaining queue")
    parser.add_argument("--build", action="store_true", help="Build + push after generating")
    args = parser.parse_args()

    os.chdir(PROJECT_DIR)

    existing = load_existing_guides()
    existing_slugs = {g["slug"] for g in existing}
    queue = get_queue(existing_slugs)

    if args.list_queue:
        print(f"Existing: {len(existing)} guides")
        print(f"Queue: {len(queue)} remaining\n")
        for g in queue:
            print(f"  [{g['category_label']}] {g['title']}")
        return

    if not queue:
        print("ERROR: Queue empty and auto-generation failed. Cannot produce content.")
        sys.exit(1)

    attempt_limit = max(args.count * 3, args.count)
    batch = queue[:attempt_limit]

    if args.dry_run:
        print(f"Would attempt up to {len(batch)} guides to publish {args.count}:")
        for g in batch:
            print(f"  [{g['category_label']}] {g['title']}")
        return

    print(f"Generating {args.count} wellness guides...")
    if len(batch) > args.count:
        print(f"Will attempt up to {len(batch)} queued topics if quality gates reject output.")
    print(f"Existing: {len(existing)} | Queue remaining: {len(queue)}\n")

    new_guides = []
    for topic in batch:
        guide = generate_guide(topic)
        if guide:
            new_guides.append(guide)
            if len(new_guides) >= args.count:
                break
        time.sleep(2)  # Rate limit between generations

    if not new_guides:
        print("No guides generated successfully.")
        sys.exit(1)

    save_guides(existing, new_guides)

    new_slugs = [g["slug"] for g in new_guides]

    if args.build:
        if build_and_push(new_slugs):
            total = len(existing) + len(new_guides)
            remaining = len(queue) - len(new_guides)
            send_telegram(
                f"📚 *CreditDoc Wellness Guides*\n"
                f"Generated {len(new_guides)} new guides\n"
                f"Total: {total} | Remaining: {remaining}\n"
                f"New: {', '.join(new_slugs)}"
            )
    else:
        print(f"\nGenerated {len(new_guides)} guides. Run with --build to deploy.")


if __name__ == "__main__":
    main()
