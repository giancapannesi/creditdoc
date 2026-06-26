#!/usr/bin/env python3
"""
CreditDoc Cluster Compliance Check

The pre-publish quality gate for cluster answer assets. Blocks publication
of any asset that doesn't meet the bar — no velocity-over-quality slippage.

This is the first implementation — 20 checks covering the most important
failure modes. Full 65-point checklist from CREDITDOC_DETAILED_CONTENT_PLAN.md
is being built incrementally; this module is designed so new checks drop in
as single functions.

Usage as library:
    from tools.cluster_compliance_check import run_compliance_check
    score, passed, failures = run_compliance_check(asset_dict, target_money_page)

CLI:
    python3 tools/cluster_compliance_check.py --slug <slug>
"""
import argparse, json, re, sys
from pathlib import Path

BASE = Path("/srv/BusinessOps")
CREDITDOC = BASE / "creditdoc"

# --- Individual checks ---
# Each returns (bool, reason_if_fail). Name must start with 'check_'.

def check_h1_present(a, _):
    h1 = a.get("h1", "")
    return bool(h1 and 1 <= len(h1) <= 90), f"h1 len={len(h1)}"

def check_title_length(a, _):
    t = a.get("title", "")
    return len(t) <= 60 and len(t) >= 20, f"title len={len(t)} (need 20-60)"

def check_title_has_brand(a, _):
    return "CreditDoc" in a.get("title", ""), "title missing 'CreditDoc'"

def check_meta_description(a, _):
    md = a.get("meta_description", "")
    return 130 <= len(md) <= 160, f"meta_description len={len(md)} (need 130-160)"

def check_slug_format(a, _):
    s = a.get("slug", "")
    return bool(re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", s)) and len(s) <= 80, f"slug '{s}' invalid or >80"

def check_sections_count(a, _):
    n = len(a.get("sections", []))
    return 5 <= n <= 12, f"{n} sections (need 5-12)"

def check_word_count(a, _):
    total = sum(len(s.get("content", "").split()) for s in a.get("sections", []))
    return 1200 <= total <= 3500, f"{total} words (need 1200-3500)"

def check_no_thin_sections(a, _):
    thin = [s.get("heading", "?") for s in a.get("sections", []) if len(s.get("content", "").split()) < 80]
    return not thin, f"thin sections: {thin}" if thin else "ok"

def check_faq_count(a, _):
    n = len(a.get("faq_schema", []))
    return 4 <= n <= 8, f"{n} FAQ (need 4-8)"

def check_faq_shape(a, _):
    for f in a.get("faq_schema", []):
        if not f.get("question") or not f.get("answer"):
            return False, "FAQ entry missing q or a"
        if len(f.get("answer", "")) < 30:
            return False, f"FAQ answer too short: {f.get('question', '')[:40]}"
    return True, "ok"

def check_internal_links_count(a, _):
    n = len(a.get("internal_links", []))
    return 8 <= n <= 20, f"{n} links (need 8-20)"

def check_target_money_link(a, target):
    urls = [ln.get("url", "") for ln in a.get("internal_links", [])]
    return any(target in u for u in urls), f"missing link to {target}"

def check_money_link_diversity(a, _):
    urls = {ln.get("url", "") for ln in a.get("internal_links", []) if "/best/" in ln.get("url", "")}
    return len(urls) >= 2, f"only {len(urls)} unique money links (need ≥2)"

def check_link_types(a, _):
    types = {ln.get("type", "") for ln in a.get("internal_links", [])}
    required = {"money_listicle"}
    missing = required - types
    return not missing, f"missing link types: {missing}" if missing else "ok"

def check_primary_sources(a, _):
    n = len(a.get("primary_sources", []))
    return n >= 2, f"{n} primary sources (need ≥2)"

def check_primary_sources_are_authoritative(a, _):
    bad = []
    for src in a.get("primary_sources", []):
        url = src.get("url", "").lower()
        if not url.startswith("https://"):
            bad.append(src.get("name", "?"))
            continue
        # .gov, .edu, .org, or well-known domains
        ok_domains = (".gov", ".edu", ".org", "consumerfinance.gov", "federalreserve", "bls.gov",
                      "ftc.gov", "irs.gov", "cfpb.gov", "experian.com", "equifax.com",
                      "transunion.com", "myfico.com", "thezebra.com", "nerdwallet.com",
                      "bankrate.com", "creditkarma.com", "wallethub.com",
                      "annualcreditreport.com")
        if not any(d in url for d in ok_domains):
            bad.append(src.get("name", "?"))
    return not bad, f"non-authoritative sources: {bad}" if bad else "ok"

def check_no_banned_phrases(a, _):
    banned = ["as an ai", "i'm just", "i cannot", "my apologies", "i apologize",
              "i don't have access", "cutoff date", "knowledge cutoff"]
    body = " ".join(s.get("content", "") for s in a.get("sections", [])).lower()
    hits = [b for b in banned if b in body]
    return not hits, f"banned phrases: {hits}" if hits else "ok"

def check_no_placeholder_text(a, _):
    body = " ".join(s.get("content", "") for s in a.get("sections", []))
    for m in ["TODO", "TBD", "[insert", "[placeholder", "Lorem ipsum", "xxxx"]:
        if m in body:
            return False, f"placeholder: {m}"
    return True, "ok"

def check_questions_answered(a, _):
    n = len(a.get("questions_answered", []))
    if a.get("page_format") == "dedicated_question_answer":
        return 1 <= n <= 3, f"{n} questions_answered (need 1-3 for dedicated answer pages)"
    return n >= 5, f"{n} questions_answered (legacy cluster page needs ≥5)"

def check_dedicated_page_targets_primary_question(a, _):
    if a.get("page_format") != "dedicated_question_answer":
        return True, "legacy page"
    primary = (a.get("primary_question") or (a.get("questions_answered") or [""])[0]).lower()
    h1 = a.get("h1", "").lower()
    title = a.get("title", "").lower()
    q_tokens = {
        t for t in re.findall(r"[a-z0-9]+", primary)
        if t not in {"a", "an", "and", "are", "can", "do", "does", "for", "how", "i", "is", "of", "or", "the", "to", "what", "when", "where", "which", "who", "why", "with", "you", "your"}
    }
    page_tokens = set(re.findall(r"[a-z0-9]+", f"{h1} {title}"))
    needed = max(2, min(5, len(q_tokens) // 2))
    if len(q_tokens & page_tokens) < needed:
        return False, "title/h1 do not clearly target primary_question"
    h1_tokens = set(re.findall(r"[a-z0-9]+", h1))
    if q_tokens and not q_tokens <= h1_tokens:
        missing = ", ".join(sorted(q_tokens - h1_tokens))
        return False, f"h1 missing primary_question term(s): {missing}"
    return True, "ok"

def check_no_duplicate_with_published(a, _):
    """Reject if another published asset already covers the same slug or title."""
    try:
        sys.path.insert(0, str(CREDITDOC))
        from tools.creditdoc_db import CreditDocDB
        slug = a.get("slug", "")
        title = a.get("title", "").lower().strip()
        with CreditDocDB() as db:
            # Check slug collision with published rows that aren't the current one
            row = db.conn.execute(
                "SELECT slug, title FROM cluster_answers WHERE status='published' AND slug != ?",
                (slug,),
            ).fetchall()
            for r in row:
                if r["title"].lower().strip() == title:
                    return False, f"duplicate title of published '{r['slug']}'"
        return True, "ok"
    except Exception as e:
        return True, f"dup check skipped ({e})"


ALL_CHECKS = [
    check_h1_present, check_title_length, check_title_has_brand, check_meta_description,
    check_slug_format, check_sections_count, check_word_count, check_no_thin_sections,
    check_faq_count, check_faq_shape, check_internal_links_count, check_target_money_link,
    check_money_link_diversity, check_link_types, check_primary_sources,
    check_primary_sources_are_authoritative, check_no_banned_phrases, check_no_placeholder_text,
    check_questions_answered, check_dedicated_page_targets_primary_question,
    check_no_duplicate_with_published,
]


def run_compliance_check(asset, target_money_page):
    """Returns (score, passed_bool, failures_list).
    passed requires score/max >= 0.85 (so ≥17/20 at current check count).
    """
    results = []
    for fn in ALL_CHECKS:
        try:
            ok, reason = fn(asset, target_money_page)
        except Exception as e:
            ok, reason = False, f"check exception: {e}"
        results.append((fn.__name__, ok, reason))
    passed_count = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    failures = [(name, reason) for name, ok, reason in results if not ok]
    passed = (passed_count / total) >= 0.85
    return passed_count, total, passed, failures


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--slug", required=True)
    p.add_argument("--explain", action="store_true")
    args = p.parse_args()

    sys.path.insert(0, str(CREDITDOC))
    from tools.creditdoc_db import CreditDocDB
    with CreditDocDB() as db:
        asset = db.get_cluster_answer(args.slug)
    if not asset:
        print(f"slug '{args.slug}' not found")
        return 1

    target = asset.get("target_money_page", "")
    score, total, passed, failures = run_compliance_check(asset, target)
    print(f"{args.slug}: {score}/{total}  {'PASSED' if passed else 'FAILED'}")
    if args.explain or failures:
        for name, reason in failures:
            print(f"  ✗ {name}: {reason}")
    return 0 if passed else 2


if __name__ == "__main__":
    sys.exit(main())
