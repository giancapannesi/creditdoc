#!/usr/bin/env python3
# UNPAUSED 2026-05-08 — founder directive: blog must publish daily alongside answers pipeline.
"""
CreditDoc — Blog Content Generator

Generates SEO-optimized blog articles targeting money keywords in the
consumer finance space. Articles funnel readers to listicles, lender
reviews, and wellness guides.

Usage:
    python3 tools/creditdoc_blog.py                       # Generate next article
    python3 tools/creditdoc_blog.py --count 2             # Generate 2 articles
    python3 tools/creditdoc_blog.py --dry-run             # Preview without writing
    python3 tools/creditdoc_blog.py --list-queue          # Show pending articles
    python3 tools/creditdoc_blog.py --seed-queue          # Populate queue from SEED_ARTICLES

Cron: Daily 06:30 UTC (before indexing at 08:00)
"""

import argparse
import json
import os
import subprocess
import sys
import re
import time
from datetime import datetime
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────

PROJECT_DIR = "/srv/BusinessOps/creditdoc"
BLOG_FILE = os.path.join(PROJECT_DIR, "src/content/blog-posts.json")
QUEUE_FILE = "/srv/BusinessOps/CreditDoc_SEO/blog_queue.json"
LOG_FILE = "/srv/BusinessOps/CreditDoc_SEO/blog_log.json"

TELEGRAM_TOKEN = "8552358080:AAFC8FjKxQdj_NJyqwMbgUZrxKzUrn83tGY"
TELEGRAM_CHAT_ID = "1351661181"

# === CreditDoc DB API (Phase 3 dual-write — 2026-04-09) ===
# Blog posts are append-only in the DB. The JSON file write keeps the
# legacy Astro build working; the DB mirror provides audit + protection.
sys.path.insert(0, os.path.join(PROJECT_DIR, "tools"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from creditdoc_content_guardrails import reject_if_unsafe
from creditdoc_content_repair import repair_unsafe_json

try:
    from creditdoc_db import CreditDocDB
    HAS_PERSISTENCE_DB = True
except Exception:
    HAS_PERSISTENCE_DB = False

TODAY = datetime.now().strftime("%Y-%m-%d")
YEAR = "2026"

# ── Seed Articles ───────────────────────────────────────────────

SEED_ARTICLES = [
    # Personal Loans — highest search volume
    {"topic": "how to get a personal loan with bad credit in 2026", "category": "personal-loans",
     "keyword": "personal loan bad credit", "related_listicles": ["best-personal-loans-bad-credit"],
     "related_categories": ["personal-loans"], "tags": ["personal-loans", "bad-credit"], "priority": 1},
    {"topic": "personal loan vs credit card: which is cheaper for debt consolidation", "category": "personal-loans",
     "keyword": "personal loan vs credit card", "related_listicles": ["best-debt-consolidation-loans"],
     "related_categories": ["personal-loans", "debt-relief"], "tags": ["personal-loans", "debt-consolidation"], "priority": 1},
    {"topic": "how to lower your personal loan interest rate", "category": "personal-loans",
     "keyword": "lower personal loan interest rate", "related_listicles": ["cheapest-personal-loans"],
     "related_categories": ["personal-loans"], "tags": ["personal-loans", "interest-rates"], "priority": 2},
    {"topic": "best ways to use a personal loan responsibly", "category": "personal-loans",
     "keyword": "personal loan tips", "related_listicles": ["best-personal-loan-lenders"],
     "related_categories": ["personal-loans"], "tags": ["personal-loans", "financial-planning"], "priority": 2},

    # Credit Repair — high conversion
    {"topic": "how to dispute errors on your credit report step by step", "category": "credit-repair",
     "keyword": "dispute credit report errors", "related_listicles": ["best-credit-repair-companies"],
     "related_categories": ["fix-my-credit"], "tags": ["credit-repair", "credit-report"], "priority": 1},
    {"topic": "how long does credit repair take: realistic timelines", "category": "credit-repair",
     "keyword": "how long does credit repair take", "related_listicles": ["best-credit-repair-companies"],
     "related_categories": ["fix-my-credit"], "tags": ["credit-repair", "credit-score"], "priority": 1},
    {"topic": "credit repair scams: how to spot them and what to do instead", "category": "credit-repair",
     "keyword": "credit repair scams", "related_listicles": ["best-credit-repair-companies", "best-credit-repair-money-back-guarantee"],
     "related_categories": ["fix-my-credit"], "tags": ["credit-repair", "scam-protection"], "priority": 1},
    {"topic": "rebuilding credit after bankruptcy: a complete timeline", "category": "credit-repair",
     "keyword": "rebuild credit after bankruptcy", "related_listicles": ["best-credit-repair-after-bankruptcy"],
     "related_categories": ["fix-my-credit", "bankruptcy"], "tags": ["bankruptcy", "credit-repair"], "priority": 1},

    # Debt Relief — high affiliate value
    {"topic": "debt consolidation vs debt settlement: which is right for you", "category": "debt-relief",
     "keyword": "debt consolidation vs settlement", "related_listicles": ["best-debt-consolidation-loans", "best-debt-relief-companies"],
     "related_categories": ["debt-relief"], "tags": ["debt-consolidation", "debt-settlement"], "priority": 1},
    {"topic": "how to get out of $10,000 in credit card debt", "category": "debt-relief",
     "keyword": "get out of credit card debt", "related_listicles": ["best-debt-consolidation-loans", "best-credit-counseling-agencies"],
     "related_categories": ["debt-relief"], "tags": ["credit-card-debt", "debt-relief"], "priority": 1},
    {"topic": "do you really need a debt relief company or can you negotiate yourself", "category": "debt-relief",
     "keyword": "negotiate debt yourself", "related_listicles": ["best-debt-relief-companies"],
     "related_categories": ["debt-relief"], "tags": ["debt-settlement", "diy"], "priority": 2},

    # Build Credit — common search
    {"topic": "how to build credit from scratch with no credit history", "category": "build-credit",
     "keyword": "build credit from scratch", "related_listicles": ["best-credit-builder-loans", "best-secured-credit-cards"],
     "related_categories": ["build-credit"], "tags": ["build-credit", "first-credit"], "priority": 1},
    {"topic": "secured credit card vs credit builder loan: which builds credit faster", "category": "build-credit",
     "keyword": "secured card vs credit builder loan", "related_listicles": ["best-secured-credit-cards", "best-credit-builder-loans"],
     "related_categories": ["build-credit"], "tags": ["secured-cards", "credit-builder-loans"], "priority": 1},
    {"topic": "does paying rent build credit: how rent reporting works", "category": "build-credit",
     "keyword": "does paying rent build credit", "related_listicles": ["best-rent-reporting-services"],
     "related_categories": ["build-credit"], "tags": ["rent-reporting", "build-credit"], "priority": 1},

    # Identity Theft & Monitoring
    {"topic": "identity theft warning signs: how to know if your identity was stolen", "category": "identity-theft",
     "keyword": "identity theft signs", "related_listicles": ["best-identity-theft-protection", "best-credit-monitoring-services"],
     "related_categories": ["credit-monitoring"], "tags": ["identity-theft", "fraud-protection"], "priority": 2},
    {"topic": "credit monitoring: free vs paid services compared", "category": "credit-monitoring",
     "keyword": "free vs paid credit monitoring", "related_listicles": ["best-credit-monitoring-services"],
     "related_categories": ["credit-monitoring"], "tags": ["credit-monitoring", "credit-score"], "priority": 2},

    # Cash Advance / Payday Alternatives
    {"topic": "cash advance apps vs payday loans: the real cost comparison", "category": "payday-alternatives",
     "keyword": "cash advance apps vs payday loans", "related_listicles": ["best-cash-advance-apps", "best-payday-loan-alternatives"],
     "related_categories": ["payday-alternatives"], "tags": ["cash-advance", "payday-loans"], "priority": 1},
    {"topic": "how to break the payday loan cycle permanently", "category": "payday-alternatives",
     "keyword": "break payday loan cycle", "related_listicles": ["best-payday-loan-alternatives", "best-credit-counseling-agencies"],
     "related_categories": ["payday-alternatives", "free-help"], "tags": ["payday-loans", "debt-cycle"], "priority": 1},

    # Credit Counseling / Free Help
    {"topic": "what does a credit counselor actually do and is it worth it", "category": "credit-counseling",
     "keyword": "what does credit counselor do", "related_listicles": ["best-credit-counseling-agencies"],
     "related_categories": ["free-help"], "tags": ["credit-counseling", "financial-planning"], "priority": 2},
    {"topic": "free credit repair resources you probably didn't know existed", "category": "credit-repair",
     "keyword": "free credit repair resources", "related_listicles": ["best-credit-repair-companies", "best-credit-counseling-agencies"],
     "related_categories": ["free-help", "fix-my-credit"], "tags": ["free-resources", "credit-repair"], "priority": 2},

    # Veterans
    {"topic": "va loan credit score requirements: what veterans need to know", "category": "veterans",
     "keyword": "va loan credit score", "related_listicles": ["best-credit-repair-veterans"],
     "related_categories": ["fix-my-credit", "personal-loans"], "tags": ["veterans", "va-loans", "credit-score"], "priority": 2},
]

# ── Category Labels ─────────────────────────────────────────────

CATEGORY_LABELS = {
    "personal-loans": "Personal Loans",
    "credit-repair": "Credit Repair",
    "debt-relief": "Debt Relief",
    "build-credit": "Build Credit",
    "identity-theft": "Identity Theft",
    "credit-monitoring": "Credit Monitoring",
    "payday-alternatives": "Payday Alternatives",
    "credit-counseling": "Credit Counseling",
    "veterans": "Veterans",
}


# ── Helpers ─────────────────────────────────────────────────────

def send_telegram(msg):
    # Telegram removed 2026-05-14 — alerts go through cron_alert.py / Harvey email
    pass



def load_queue():
    os.makedirs(os.path.dirname(QUEUE_FILE), exist_ok=True)
    if os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE) as f:
            return json.load(f)
    return []


def save_queue(queue):
    os.makedirs(os.path.dirname(QUEUE_FILE), exist_ok=True)
    with open(QUEUE_FILE, "w") as f:
        json.dump(queue, f, indent=2)


QUESTIONS_CSV = "/srv/BusinessOps/CreditDoc Project Improvement/output/credit_questions_20260409_161324.csv"
QUESTIONS_CSV_BIZ = "/srv/BusinessOps/CreditDoc Project Improvement/output/business_loan_questions_vpn_20260417_083147.csv"

CSV_CATEGORY_MAP = {
    "Credit Building": "build-credit",
    "Credit Cards": "build-credit",
    "Credit Report": "credit-repair",
    "Credit Score": "credit-repair",
    "Credit Repair": "credit-repair",
    "Debt Management": "debt-relief",
    "Debt Collection": "debt-relief",
    "Personal Loans": "personal-loans",
    "Mortgages": "personal-loans",
    "Auto Loans": "personal-loans",
    "Student Loans": "debt-relief",
    "Payday Loans": "payday-alternatives",
    "Identity Theft": "identity-theft",
    "Business Loans": "business-loans",
    "SBA Loans": "business-loans",
}

CATEGORY_LISTICLES = {
    "build-credit": ["best-credit-builder-loans", "best-secured-credit-cards"],
    "credit-repair": ["best-credit-repair-companies"],
    "debt-relief": ["best-debt-consolidation-loans", "best-debt-relief-companies"],
    "personal-loans": ["best-personal-loans-bad-credit", "best-personal-loan-lenders"],
    "payday-alternatives": ["best-payday-loan-alternatives", "best-cash-advance-apps"],
    "identity-theft": ["best-identity-theft-protection", "best-credit-monitoring-services"],
    "credit-monitoring": ["best-credit-monitoring-services"],
    "credit-counseling": ["best-credit-counseling-agencies"],
    "business-loans": ["best-small-business-loans"],
    "veterans": ["best-credit-repair-veterans"],
}


def auto_refill_queue(queue, target=20):
    """Pull blog-worthy questions from scraped CSVs to keep the queue full."""
    import csv

    existing_topics = set()
    for a in queue:
        existing_topics.add(a.get("topic", "").lower())

    existing_posts = load_blog_posts()
    existing_slugs = {p["slug"] for p in existing_posts}

    candidates = []
    for csv_path in [QUESTIONS_CSV, QUESTIONS_CSV_BIZ]:
        if not os.path.exists(csv_path):
            continue
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                q = row.get("question", "").strip()
                if not q or len(q) < 20 or len(q) > 120:
                    continue
                if not row.get("is_question", "").lower().startswith("t"):
                    continue
                src_count = int(row.get("source_count", "1") or "1")
                candidates.append((src_count, q, row.get("category", "")))

    candidates.sort(key=lambda x: -x[0])

    added = 0
    pending_count = len([a for a in queue if a.get("status") in ("pending", "queued")])

    for src_count, question, raw_cat in candidates:
        if pending_count >= target:
            break
        topic = question.lower().rstrip("?").strip()
        if topic in existing_topics:
            continue
        slug_check = topic.replace(" ", "-").replace("'", "")[:80]
        if slug_check in existing_slugs:
            continue

        cat = CSV_CATEGORY_MAP.get(raw_cat, "credit-repair")
        listicles = CATEGORY_LISTICLES.get(cat, ["best-credit-repair-companies"])

        queue.append({
            "topic": topic,
            "category": cat,
            "keyword": " ".join(topic.split()[:5]),
            "related_listicles": listicles,
            "related_categories": [cat],
            "tags": [cat],
            "priority": 2,
            "status": "pending",
            "added_date": TODAY,
            "completed_date": None,
            "word_count": 0,
        })
        existing_topics.add(topic)
        added += 1
        pending_count += 1

    return queue, added


def load_blog_posts():
    if os.path.exists(BLOG_FILE):
        with open(BLOG_FILE) as f:
            return json.load(f)
    return []


def save_blog_posts(posts):
    # Write to JSON file (legacy, for Astro build)
    with open(BLOG_FILE, "w") as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)

    # Dual-write: mirror to persistence DB (Phase 3)
    # add_blog_post uses INSERT OR REPLACE — append-only at the list level,
    # upsert at the row level (same slug updates, new slug adds).
    if HAS_PERSISTENCE_DB:
        try:
            with CreditDocDB() as db:
                added = 0
                for post in posts:
                    if not isinstance(post, dict) or 'slug' not in post:
                        continue
                    try:
                        db.add_blog_post(post, updated_by='blog_generator')
                        added += 1
                    except Exception as e:
                        print(f"    DB add failed for {post.get('slug', '?')}: {e}")
                print(f"    DB mirror: {added}/{len(posts)} blog posts upserted")
        except Exception as e:
            print(f"    DB mirror write failed: {type(e).__name__}: {e}")


def load_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE) as f:
            return json.load(f)
    return []


def save_log(log):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)


def slug_from_topic(topic):
    slug = re.sub(r'[^a-z0-9]+', '-', topic.lower().strip())
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug[:80]


def trim_meta(value, max_len):
    """Trim generated metadata at a word boundary without exceeding max_len."""
    value = re.sub(r"\s+", " ", (value or "").strip())
    if len(value) <= max_len:
        return value

    suffix = "..."
    limit = max_len - len(suffix)
    trimmed = value[:limit].rstrip()
    if " " in trimmed:
        trimmed = trimmed.rsplit(" ", 1)[0].rstrip()
    return trimmed + suffix


def normalize_blog_metadata(post):
    post["title"] = trim_meta(post.get("title", ""), 55)
    post["description"] = trim_meta(post.get("description", ""), 140)
    post["seo_title"] = trim_meta(post.get("seo_title", f"{post.get('title', '')} | CreditDoc"), 58)
    post["seo_description"] = trim_meta(
        post.get("seo_description") or post.get("description", ""),
        155,
    )
    return post


# ── Article Generation ──────────────────────────────────────────

def openai_call(prompt, timeout_secs=240):
    """Compatibility wrapper around the shared CreditDoc OpenAI text provider."""
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from creditdoc_oauth import call_ai
        return call_ai(prompt, model="gpt-4.1", max_tokens=8192, timeout_secs=timeout_secs)
    except Exception as e:
        print(f"  OpenAI generation failed: {e}")
    return None


def generate_article(article_meta):
    """Generate a full blog post using OpenAI."""
    topic = article_meta["topic"]
    keyword = article_meta.get("keyword", topic)
    category = article_meta.get("category", "general")
    category_label = CATEGORY_LABELS.get(category, category.replace("-", " ").title())
    related_listicles = article_meta.get("related_listicles", [])
    related_categories = article_meta.get("related_categories", [])
    tags = article_meta.get("tags", [])
    slug = slug_from_topic(topic)

    # Build internal link suggestions
    link_suggestions = []
    for ls in related_listicles:
        link_suggestions.append(f"/best/{ls}/")
    for rc in related_categories:
        link_suggestions.append(f"/categories/{rc}/")

    prompt = f"""Write a comprehensive, SEO-optimized blog article for CreditDoc.co about: "{topic}"

TARGET KEYWORD: "{keyword}"
CATEGORY: {category_label}
YEAR: {YEAR}

REQUIREMENTS:
1. Write 1,800-2,500 words of genuinely useful content
2. Use the target keyword naturally 3-5 times (not forced)
3. Write in second person ("you") — direct, helpful, no fluff
4. Include specific numbers and percentages where they are stable, sourced, and useful
5. Reference actual laws/regulations (FCRA, FDCPA, SCRA, etc.) when applicable
6. Be honest about limitations and downsides — never oversell

STRUCTURE — Return ONLY valid JSON in this exact format:
{{
  "title": "Title under 55 characters — include keyword naturally",
  "description": "One-sentence summary under 140 characters",
  "seo_title": "SEO title under 58 characters with keyword | CreditDoc",
  "seo_description": "Meta description 130-155 characters with keyword and CTA",
  "read_time": "X min",
  "sections": [
    {{"heading": "H2 heading", "content": "Full section content with paragraphs separated by double newlines. Use **bold** for emphasis. Use bullet lists with - prefix. Minimum 4-6 sections, each 200-400 words."}}
  ],
  "key_takeaways": ["3-5 practical takeaways the reader can act on immediately"],
  "faq": [
    {{"question": "Common question about this topic?", "answer": "Clear, concise answer in 2-3 sentences."}}
  ]
}}

INTERNAL LINKS to mention naturally in the content:
{json.dumps(link_suggestions)}

RULES:
- Every claim should be verifiable
- Do NOT invent current prices, fees, APRs, BBB ratings, Google ratings, star ratings, or guarantees for any company, lender, app, card, or service.
- If a current provider-specific price/rate/rating/guarantee is not supplied in this prompt, omit it or say readers should verify current terms directly with the provider.
- Generic educational ranges are allowed only when they are clearly general context, not a claim about a named provider.
- Don't recommend specific companies — that's what our listicle pages are for
- Link readers to our comparison pages for product recommendations
- Include a section on common mistakes or things to avoid
- End with clear next steps
- No disclaimers in the content (template handles that)
- FAQs should be 3-5 questions people actually search for
- Return ONLY the JSON object, nothing else
"""

    try:
        output = openai_call(prompt)
        if not output:
            print(f"  ERROR: No response from OpenAI for '{topic}'")
            return None

        # Extract JSON from response — robust parsing
        # Try direct parse first
        article_data = None
        try:
            article_data = json.loads(output)
        except json.JSONDecodeError:
            pass

        if not article_data:
            # Try extracting JSON block
            json_match = re.search(r'```json\s*([\s\S]*?)```', output)
            if json_match:
                try:
                    article_data = json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass

        if not article_data:
            # Try finding outermost braces with balanced bracket counting
            depth = 0
            start = None
            for i, c in enumerate(output):
                if c == '{':
                    if depth == 0:
                        start = i
                    depth += 1
                elif c == '}':
                    depth -= 1
                    if depth == 0 and start is not None:
                        try:
                            candidate = output[start:i+1]
                            # Fix common JSON issues: trailing commas
                            candidate = re.sub(r',\s*}', '}', candidate)
                            candidate = re.sub(r',\s*]', ']', candidate)
                            article_data = json.loads(candidate)
                            break
                        except json.JSONDecodeError:
                            start = None
                            continue

        if not article_data:
            print(f"  ERROR: Could not parse JSON for '{topic}'")
            # Save raw output for debugging
            debug_file = f"/tmp/creditdoc_blog_debug_{slug}.txt"
            with open(debug_file, "w") as df:
                df.write(output)
            print(f"  Raw output saved to {debug_file}")
            return None

        # Validate required fields
        required = ["title", "sections", "key_takeaways", "faq"]
        for field in required:
            if field not in article_data:
                print(f"  ERROR: Missing field '{field}' in response")
                return None

        if len(article_data["sections"]) < 3:
            print(f"  WARNING: Only {len(article_data['sections'])} sections (expected 4+)")

        guardrail_failures = reject_if_unsafe(article_data)
        if guardrail_failures:
            print("  REPAIR: CreditDoc guardrails failed; attempting content repair")
            article_data, guardrail_failures = repair_unsafe_json(
                article_data,
                guardrail_failures,
                content_type="blog article",
                source_context=(
                    f"Topic: {topic}\n"
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

        # Build full blog post
        post = {
            "slug": slug,
            "title": article_data.get("title", topic.title()),
            "category": category,
            "category_label": category_label,
            "description": article_data.get("description", ""),
            "seo_title": article_data.get("seo_title", f"{article_data.get('title', topic)} | CreditDoc"),
            "seo_description": article_data.get("seo_description", article_data.get("description", "")),
            "read_time": article_data.get("read_time", "8 min"),
            "publish_date": TODAY,
            "status": "published",
            "last_updated": TODAY,
            "sections": article_data["sections"],
            "key_takeaways": article_data["key_takeaways"],
            "related_guides": [],  # Will be linked to wellness guides if relevant
            "related_categories": related_categories,
            "faq": article_data["faq"],
            "tags": tags,
        }

        post = normalize_blog_metadata(post)

        return post

    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT generating article for '{topic}'")
        return None
    except json.JSONDecodeError as e:
        print(f"  JSON PARSE ERROR for '{topic}': {e}")
        return None
    except Exception as e:
        print(f"  ERROR generating article for '{topic}': {e}")
        return None


def expand_short_article(post, article_meta, target_words=1700):
    """Expand a valid but short article once, preserving the JSON shape."""
    current_words = sum(len(s.get("content", "").split()) for s in post.get("sections", []))
    prompt = f"""Expand this CreditDoc blog article to at least {target_words} words while preserving the same JSON structure.

Topic: {article_meta.get("topic", post.get("title", ""))}
Category: {article_meta.get("category", post.get("category", ""))}
Current word count: {current_words}

Rules:
- Return ONLY valid JSON for the full article object.
- Keep the existing title, slug, category, metadata, key_takeaways, tags, and FAQ unless they need minor clarity edits.
- Expand section content with useful, specific explanation, examples, mistakes to avoid, and next steps.
- Do NOT invent current provider prices, APRs, ratings, review counts, guarantees, or approval odds.
- Keep anti-scam warnings, but do not claim guaranteed results or guaranteed approval.
- Use evergreen financial education and federal law context only.

Article JSON:
{json.dumps(post)}
"""
    output = openai_call(prompt)
    if not output:
        return post

    try:
        expanded = json.loads(output)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", output)
        if not match:
            return post
        try:
            expanded = json.loads(match.group(0))
        except json.JSONDecodeError:
            return post

    if not isinstance(expanded, dict) or not expanded.get("sections"):
        return post

    expanded.setdefault("slug", post.get("slug"))
    expanded.setdefault("category", post.get("category"))
    expanded.setdefault("category_label", post.get("category_label"))
    expanded.setdefault("publish_date", post.get("publish_date"))
    expanded.setdefault("status", post.get("status"))
    expanded.setdefault("last_updated", post.get("last_updated"))
    expanded.setdefault("related_guides", post.get("related_guides", []))
    expanded.setdefault("related_categories", post.get("related_categories", []))
    expanded.setdefault("tags", post.get("tags", []))
    expanded = normalize_blog_metadata(expanded)

    guardrail_failures = reject_if_unsafe(expanded)
    if guardrail_failures:
        print("  EXPAND REPAIR: CreditDoc guardrails failed; attempting content repair")
        expanded, guardrail_failures = repair_unsafe_json(
            expanded,
            guardrail_failures,
            content_type="expanded blog article",
            source_context=(
                f"Topic: {article_meta.get('topic', post.get('title', ''))}\n"
                f"Category: {article_meta.get('category', post.get('category', ''))}\n"
                "Use evergreen education only. Do not add current company prices, APRs, ratings, review counts, guarantees, or approval odds."
            ),
            max_tokens=8192,
        )
    if guardrail_failures:
        print("  EXPAND REJECT: CreditDoc guardrails failed")
        for failure in guardrail_failures[:5]:
            print(f"    - {failure}")
        return post

    return expanded


# ── Main ────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="CreditDoc Blog Generator")
    parser.add_argument("--count", type=int, default=1, help="Number of articles to generate")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument("--list-queue", action="store_true", help="Show pending articles")
    parser.add_argument("--seed-queue", action="store_true", help="Populate queue from seeds")
    parser.add_argument("--no-deploy", action="store_true", help="Skip git push")
    args = parser.parse_args()

    # Seed queue
    if args.seed_queue:
        queue = load_queue()
        existing_topics = {a.get("topic", a.get("title", "")) for a in queue}
        existing_posts = load_blog_posts()
        existing_slugs = {p["slug"] for p in existing_posts}

        added = 0
        for seed in SEED_ARTICLES:
            if seed["topic"] not in existing_topics and slug_from_topic(seed["topic"]) not in existing_slugs:
                queue.append({**seed, "status": "pending", "added_date": TODAY})
                added += 1

        save_queue(queue)
        print(f"Queue seeded: {added} new articles added (total: {len(queue)})")
        return

    # List queue
    if args.list_queue:
        queue = load_queue()
        pending = [a for a in queue if a.get("status") == "pending"]
        completed = [a for a in queue if a.get("status") == "completed"]
        print(f"Queue: {len(pending)} pending, {len(completed)} completed")
        for a in sorted(pending, key=lambda x: x.get("priority", 99)):
            print(f"  [P{a.get('priority', '?')}] {a.get('topic', a.get('title', 'unknown'))}")
        return

    # Generate articles
    queue = load_queue()
    if not queue:
        # Auto-seed if empty
        for seed in SEED_ARTICLES:
            queue.append({**seed, "status": "pending", "added_date": TODAY})
        save_queue(queue)

    pending = sorted(
        [a for a in queue if a.get("status") in ("pending", "queued")],
        key=lambda x: x.get("priority", 99)
    )

    if not pending or len(pending) <= 10:
        print(f"Queue low ({len(pending)} pending) — auto-refilling from scraped questions...")
        queue, added = auto_refill_queue(queue, target=20)
        save_queue(queue)
        print(f"  Added {added} topics from question bank.")
        pending = sorted(
            [a for a in queue if a.get("status") in ("pending", "queued")],
            key=lambda x: x.get("priority", 99)
        )

    if not pending:
        print("ERROR: No pending articles in queue and question bank exhausted.")
        sys.exit(1)

    existing_posts = load_blog_posts()
    existing_slugs = {p["slug"] for p in existing_posts}
    generated = 0
    log = load_log()

    max_attempts = min(len(pending), max(args.count * 4, args.count + 5))
    for article_meta in pending[:max_attempts]:
        if generated >= args.count:
            break
        if "topic" not in article_meta and "title" in article_meta:
            article_meta["topic"] = article_meta["title"]
        slug = article_meta.get("slug") or slug_from_topic(article_meta["topic"])

        if slug in existing_slugs:
            print(f"SKIP: {slug} already exists")
            article_meta["status"] = "completed"
            continue

        print(f"\nGenerating: {article_meta['topic']}")
        if args.dry_run:
            print(f"  Would generate: {slug}")
            continue

        post = generate_article(article_meta)
        if not post:
            article_meta["status"] = "failed"
            article_meta["failed_date"] = TODAY
            continue

        # Word count check
        total_words = sum(len(s.get("content", "").split()) for s in post["sections"])
        print(f"  Generated: {post['title']} ({total_words} words, {len(post['sections'])} sections)")

        if total_words < 1500:
            print(f"  EXPAND: Only {total_words} words — requesting one expansion pass")
            post = expand_short_article(post, article_meta)
            total_words = sum(len(s.get("content", "").split()) for s in post["sections"])
            print(f"  Expanded: {post['title']} ({total_words} words, {len(post['sections'])} sections)")
            if total_words < 1500:
                print(f"  REJECT: Only {total_words} words — below CreditDoc blog quality floor")
                article_meta["status"] = "failed_quality"
                article_meta["failed_date"] = TODAY
                article_meta["failure_reason"] = f"word_count_below_1500:{total_words}"
                continue

        # Add to blog posts
        existing_posts.append(post)
        existing_slugs.add(slug)

        # Update queue
        article_meta["status"] = "completed"
        article_meta["completed_date"] = TODAY
        article_meta["word_count"] = total_words

        # Log
        log.append({
            "slug": slug,
            "topic": article_meta["topic"],
            "word_count": total_words,
            "sections": len(post["sections"]),
            "generated_at": datetime.now().isoformat(),
        })

        generated += 1
        time.sleep(2)  # Rate limit between articles

    # Save everything
    if not args.dry_run and generated > 0:
        save_blog_posts(existing_posts)
        save_queue(queue)
        save_log(log)

        # Git commit + push
        try:
            subprocess.run(
                ["git", "add", "src/content/blog-posts.json"],
                cwd=PROJECT_DIR, capture_output=True, timeout=30
            )
            subprocess.run(
                ["git", "commit", "-m", f"blog: add {generated} article(s) — {TODAY}"],
                cwd=PROJECT_DIR, capture_output=True, timeout=30
            )
            if not args.no_deploy:
                push = subprocess.run(
                    ["git", "push", "origin", "HEAD"],
                    cwd=PROJECT_DIR, capture_output=True, text=True, timeout=120
                )
                if push.returncode != 0:
                    raise RuntimeError(f"git push failed: {(push.stderr or push.stdout)[-500:]}")
                print("Pushed to deploy.")

                # IndexNow
                new_slugs = [log_entry["slug"] for log_entry in log[-generated:]]
                _submit_indexnow(new_slugs)
        except Exception as e:
            print(f"Git/deploy error: {e}")

        # Telegram
        topics = [log_entry["topic"] for log_entry in log[-generated:]]
        msg = f"<b>CreditDoc Blog</b>\n{generated} article(s) published:\n" + "\n".join(f"• {t}" for t in topics)
        send_telegram(msg)
    elif not args.dry_run:
        save_queue(queue)
        print("ERROR: No blog articles generated successfully.")
        sys.exit(1)

    print(f"\nDone. Generated: {generated}, Remaining in queue: {len([a for a in queue if a.get('status') == 'pending'])}")


def _submit_indexnow(slugs):
    """Submit new blog URLs to IndexNow."""
    import requests
    key = "1efee5eebbd54ea4812e2e77a9b73fcc"
    host = "www.creditdoc.co"
    urls = [f"https://{host}/blog/{s}/" for s in slugs]
    payload = {
        "host": host, "key": key,
        "keyLocation": f"https://{host}/{key}.txt",
        "urlList": urls
    }
    for engine in ["www.bing.com", "api.indexnow.org"]:
        try:
            requests.post(f"https://{engine}/indexnow", json=payload, timeout=15)
        except Exception:
            pass


if __name__ == "__main__":
    main()
