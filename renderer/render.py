#!/usr/bin/env python3
"""
CreditDoc Renderer — replaces Astro for the /review/ page family.

Phase 1 (2026-07-17): Skeleton. Renders one lender from the DB using a
Jinja2 template and writes it to a target dist directory. This is the
minimum-viable proof that we can produce static HTML from DB rows without
Astro's build pipeline.

Design principles (from the plan the founder was originally overridden on):
- DB is source of truth. Read `data/creditdoc.db` directly. No JSON layer.
- One page = one function call. No batch requirement.
- Same URL, same HTML shape as Astro output (parity harness enforces).
- Zero framework runtime. Just Python + Jinja2 → static file.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

# renderer/ is on sys.path when invoked as `python3 renderer/render.py`, so a
# relative import works. We use the module for DB helpers to avoid duplicating
# lender-loading logic here.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from db import (  # noqa: E402
    all_brands,
    all_categories,
    all_comparisons,
    all_states_info,
    all_trends_entries,
    browse_pairs,
    load_comparison,
    category_count,
    category_to_pillar,
    cities_with_lenders,
    glossary_for_review,
    lenders_by_brand,
    lenders_by_city_state,
    lenders_in_state,
    load_blog_post,
    load_brand,
    load_category,
    load_cluster_answer,
    load_lender,
    load_trends_entry,
    load_wellness_guide,
    normalize_state_abbr,
    related_answers,
    sibling_blog_posts,
    sibling_cluster_answers,
    sibling_wellness_guides,
    similar_lenders,
    slugify_city,
    state_context,
    state_lender_and_city_counts,
    top_lenders_by_category,
    wellness_guides_by_category,
)
from linker import linkify_description  # noqa: E402
from _faqs import category_faqs, lender_specific_faqs  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


def _safe_jsonld_str(obj: Any) -> str:
    """Serialize obj to a JSON-LD-safe string.

    Escapes `</` so a hostile lender name containing `</script>` can't break
    out of the enclosing <script> tag. Preserves non-ASCII (ensure_ascii=False)
    so city/lender names render correctly.
    """
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


def render_review(slug: str, output_dir: Path) -> Path:
    """Render one /review/<slug>/index.html from DB. Returns the output path."""
    lender = load_lender(slug)
    if lender is None:
        raise SystemExit(f"error: no lender with slug '{slug}' in DB")

    similar = similar_lenders(lender["category"], slug, limit=4)
    pillar = category_to_pillar(lender["category"])
    answers = related_answers(pillar, limit=6)
    wellness = wellness_guides_by_category(lender["category"], limit=4)
    # State resolution: prefer explicit state column, fall back to company_info.state
    # or company_info.headquarters (matches Astro's derivation).
    lender_state = lender.get("state")
    if not lender_state:
        ci = lender.get("company_info") or {}
        lender_state = ci.get("state")
        if not lender_state:
            hq = (ci.get("headquarters") or "")
            # "North Salt Lake, UT" → "UT"
            if "," in hq:
                lender_state = hq.rsplit(",", 1)[-1].strip()
    if lender_state:
        lender["state"] = lender_state
    state_ctx = state_context(lender_state)
    glossary = glossary_for_review(lender["category"] or "", limit=15)

    # FAQ: prefer data-driven lender-specific questions, then merge in category template.
    # Matches Astro's behavior where the FAQ is populated from the lender's own fields.
    if not lender.get("faqs"):
        specific = lender_specific_faqs(lender, list(similar))
        lender["faqs"] = specific if specific else category_faqs(lender["category"] or "", lender.get("name") or "")

    # Pre-linkify description_long so inline money links appear (parity with Astro's
    # linkifyDescription helper). Template renders result with |safe.
    if lender.get("description_long"):
        lender["description_long_linked"] = linkify_description(
            lender["description_long"],
            current_slug=slug,
            current_category=lender["category"] or "",
            money_budget=4,
        )
    else:
        lender["description_long_linked"] = ""

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("review.html.j2")
    html = template.render(
        lender=lender,
        similar_lenders=similar,
        related_answers=answers,
        wellness_guides=wellness,
        state_ctx=state_ctx,
        glossary=glossary,
    )

    out_path = output_dir / "review" / slug / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path


def _md_to_html(src: str) -> str:
    """Minimal markdown → HTML for answer sections.

    Handles headings (## / ###), bullet lists (- ), pipe tables, bold, italic,
    paragraph breaks. Mirrors the surface set used by Astro's mdToHtml. Not a
    full markdown implementation — the DB content sticks to this subset.
    """
    import re as _re
    lines = src.split("\n")
    out: list[str] = []
    table_rows: list[list[str]] = []
    in_table = False
    in_list = False

    def inline(s: str) -> str:
        s = _re.sub(r'\*\*([^*]+)\*\*', r'<strong class="font-semibold text-text">\1</strong>', s)
        s = _re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', s)
        # Bare markdown links [text](url)
        s = _re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" class="text-primary hover:underline">\1</a>', s)
        return s

    def flush_table() -> None:
        nonlocal in_table, table_rows
        if not table_rows:
            return
        header = table_rows[0]
        body = table_rows[2:] if len(table_rows) >= 2 else []
        out.append('<div class="my-6 overflow-x-auto rounded-lg border border-border"><table class="w-full text-sm">')
        out.append('<thead class="bg-bg-alt"><tr>' + "".join(
            f'<th class="px-4 py-2.5 text-left font-semibold text-text">{inline(c)}</th>' for c in header
        ) + '</tr></thead><tbody>')
        for row in body:
            out.append('<tr class="border-t border-border">' + "".join(
                f'<td class="px-4 py-2.5 text-text">{inline(c)}</td>' for c in row
            ) + '</tr>')
        out.append('</tbody></table></div>')
        table_rows = []
        in_table = False

    def flush_list() -> None:
        nonlocal in_list
        if in_list:
            out.append('</ul>')
            in_list = False

    for raw in lines:
        line = raw.rstrip()
        if line.startswith("|") and line.endswith("|"):
            cells = [c.strip() for c in line[1:-1].split("|")]
            table_rows.append(cells)
            in_table = True
            continue
        if in_table:
            flush_table()
        if line.startswith("### "):
            flush_list()
            out.append(f'<h4 class="text-lg font-semibold text-text mt-6 mb-2">{inline(line[4:])}</h4>')
        elif line.startswith("## "):
            flush_list()
            out.append(f'<h4 class="text-lg font-semibold text-text mt-6 mb-2">{inline(line[3:])}</h4>')
        elif line.startswith("- "):
            if not in_list:
                out.append('<ul class="list-disc pl-6 my-3 space-y-1.5 text-text">')
                in_list = True
            out.append(f'<li class="leading-relaxed">{inline(line[2:])}</li>')
        elif line == "":
            flush_list()
            out.append("")
        else:
            flush_list()
            out.append(f'<p class="text-text leading-relaxed my-3">{inline(line)}</p>')
    flush_table()
    flush_list()
    return "\n".join(out)


def render_answer(slug: str, output_dir: Path) -> Path:
    """Render one /answers/<slug>/index.html from DB. Returns the output path."""
    answer = load_cluster_answer(slug)
    if answer is None:
        raise SystemExit(f"error: no cluster_answer with slug '{slug}' in DB")

    sections_raw = [s for s in (answer.get("sections") or []) if isinstance(s, dict) and s.get("heading") and s.get("content")]
    sections = [
        {"heading": s.get("heading", ""), "content_html": _md_to_html(s.get("content", ""))}
        for s in sections_raw
    ]
    faqs = [f for f in (answer.get("faq_schema") or []) if isinstance(f, dict) and f.get("question") and f.get("answer")]
    primary_sources = [s for s in (answer.get("primary_sources") or []) if isinstance(s, dict) and s.get("url") and s.get("name")]

    # Key takeaways = first sentence of first 4 sections
    import re as _re
    def _first_sentence(md: str) -> str:
        plain = _re.sub(r"[\*_`|#>-]+", " ", md)
        plain = _re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", plain)
        plain = _re.sub(r"\s+", " ", plain).strip()
        m = _re.match(r"(.*?[.!?])(\s|$)", plain)
        return (m.group(1) if m else plain[:160]).strip()
    key_takeaways = [_first_sentence(s.get("content", "")) for s in sections_raw[:4] if s.get("content")]
    key_takeaways = [t for t in key_takeaways if t]

    related = list(sibling_cluster_answers(slug, answer.get("cluster_pillar") or "", limit=4))

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("answer.html.j2")
    html = template.render(
        answer=answer,
        sections=sections,
        faqs=faqs,
        primary_sources=primary_sources,
        key_takeaways=key_takeaways,
        related_siblings=related,
    )

    out_path = output_dir / "answers" / slug / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path


def render_blog(slug: str, output_dir: Path) -> Path:
    """Render one /blog/<slug>/index.html from DB. Returns the output path."""
    post = load_blog_post(slug)
    if post is None:
        raise SystemExit(f"error: no blog_post with slug '{slug}' in DB")

    sections_raw = [s for s in (post.get("sections") or []) if isinstance(s, dict) and s.get("heading") and s.get("content")]
    sections = [
        {"heading": s.get("heading", ""), "content_html": _md_to_html(s.get("content", ""))}
        for s in sections_raw
    ]
    faqs = [f for f in (post.get("faq") or []) if isinstance(f, dict) and f.get("question") and f.get("answer")]

    # Blog uses key_takeaways as a top-level list already
    key_takeaways = post.get("key_takeaways") or []
    if not isinstance(key_takeaways, list):
        key_takeaways = []

    related = list(sibling_blog_posts(slug, post.get("category") or "", limit=4))

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("blog.html.j2")
    html = template.render(
        post=post,
        sections=sections,
        faqs=faqs,
        primary_sources=[],
        key_takeaways=key_takeaways,
        related_siblings=related,
    )

    out_path = output_dir / "blog" / slug / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path


def render_wellness(slug: str, output_dir: Path) -> Path:
    """Render one /financial-wellness/<slug>/index.html from DB."""
    post = load_wellness_guide(slug)
    if post is None:
        raise SystemExit(f"error: no wellness_guide with slug '{slug}' in DB")

    sections_raw = [s for s in (post.get("sections") or []) if isinstance(s, dict) and s.get("heading") and s.get("content")]
    sections = [
        {"heading": s.get("heading", ""), "content_html": _md_to_html(s.get("content", ""))}
        for s in sections_raw
    ]
    faqs = [f for f in (post.get("faq") or []) if isinstance(f, dict) and f.get("question") and f.get("answer")]
    key_takeaways = post.get("key_takeaways") or []
    if not isinstance(key_takeaways, list):
        key_takeaways = []
    related = list(sibling_wellness_guides(slug, post.get("category") or "", limit=4))

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("wellness.html.j2")
    html = template.render(
        post=post,
        sections=sections,
        faqs=faqs,
        primary_sources=[],
        key_takeaways=key_takeaways,
        related_siblings=related,
    )

    out_path = output_dir / "financial-wellness" / slug / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path


_CATEGORY_MONEY_MAP: dict[str, dict[str, str]] = {
    "business-loans": {"href": "/best/best-small-business-loans/", "label": "Small business loan options", "body": "Compare business funding routes, then use calculators to estimate payment pressure."},
    "personal-loans": {"href": "/best/best-personal-loans-bad-credit/", "label": "Personal loan options", "body": "Compare loan options and qualification context before contacting providers."},
    "emergency-cash": {"href": "/best/best-payday-loan-alternatives/", "label": "Payday loan alternatives", "body": "Review safer emergency-cash routes before using short-term products."},
    "payday-alternatives": {"href": "/best/best-payday-loan-alternatives/", "label": "Payday loan alternatives", "body": "Compare lower-risk alternatives and repayment pressure before borrowing."},
    "credit-repair": {"href": "/best/best-credit-repair-companies/", "label": "Credit repair companies", "body": "Compare credit-repair providers with educational context and report-review steps."},
    "debt-relief": {"href": "/best/best-debt-relief-companies/", "label": "Debt relief companies", "body": "Compare debt-relief routes and understand settlement, counseling, and payoff trade-offs."},
    "credit-counseling": {"href": "/best/best-credit-counseling-agencies/", "label": "Credit counseling agencies", "body": "Review counseling options and debt-management context before choosing help."},
    "build-credit": {"href": "/best/best-credit-builder-loans/", "label": "Credit builder loans", "body": "Compare credit-building routes and understand payment-history trade-offs."},
    "credit-cards": {"href": "/best/best-secured-credit-cards/", "label": "Secured credit cards", "body": "Compare secured-card deposits, fees, bureau reporting, and graduation context."},
    "credit-monitoring": {"href": "/best/best-credit-monitoring-services/", "label": "Credit monitoring services", "body": "Compare monitoring tools with identity-theft and report-review context."},
    "credit-unions": {"href": "/best/best-personal-loan-lenders/", "label": "Personal loan lenders", "body": "Compare borrowing options alongside credit-union and bank profiles."},
    "banking": {"href": "/best/best-personal-loan-lenders/", "label": "Personal loan lenders", "body": "Compare borrowing options after reviewing banking and credit-union profiles."},
    "mortgages": {"href": "/tools/borrowing-power-quiz/", "label": "Borrowing power quiz", "body": "Review income, debt, and credit context before comparing mortgage profiles."},
    "pawn-shops": {"href": "/best/best-payday-loan-alternatives/", "label": "Cash alternatives", "body": "Compare short-term cash alternatives before using collateral or pawn options."},
    "check-cashing": {"href": "/best/best-payday-loan-alternatives/", "label": "Cash alternatives", "body": "Compare lower-risk alternatives before relying on check-cashing or short-term cash products."},
}
_CATEGORY_TOOL_MAP: dict[str, dict[str, str]] = {
    "business-loans": {"href": "/tools/business-loan-calculator/", "label": "Business loan calculator", "body": "Estimate payment, term, and cost scenarios before comparing lenders."},
    "credit-repair": {"href": "/resources/credit-report-checklist/", "label": "Credit report checklist", "body": "Organize reports and dispute notes before paying for credit help."},
    "debt-relief": {"href": "/tools/debt-payoff-calculator/", "label": "Debt payoff calculator", "body": "Estimate payoff paths before comparing relief or counseling options."},
    "credit-counseling": {"href": "/tools/debt-payoff-calculator/", "label": "Debt payoff calculator", "body": "Frame balances and repayment options before speaking with a counselor."},
    "credit-cards": {"href": "/tools/credit-score-simulator/", "label": "Credit score simulator", "body": "Model credit-factor scenarios before comparing card options."},
    "build-credit": {"href": "/tools/credit-score-simulator/", "label": "Credit score simulator", "body": "Model common score-factor scenarios before choosing a credit-building path."},
    "credit-monitoring": {"href": "/tools/credit-score-simulator/", "label": "Credit score simulator", "body": "Review score-factor context before choosing monitoring products."},
}
_WELLNESS_GUIDE_MAP: dict[str, str] = {
    "credit-repair": "credit-repair",
    "debt-relief": "financial-recovery",
    "personal-loans": "loans-and-interest",
    "check-cashing": "everyday-finance",
    "credit-counseling": "financial-recovery",
    "pawn-lenders": "everyday-finance",
    "buy-here-pay-here": "loans-and-interest",
}
_LOCAL_CITY_LINKS = [
    {"label": "Amarillo, TX", "slug": "amarillo-tx"},
    {"label": "Austin, TX", "slug": "austin-tx"},
    {"label": "Charlotte, NC", "slug": "charlotte-nc"},
]


def _soften_category_title(title: str) -> str:
    """Minimal port of softenCategoryTitle from Astro (word-level cleanup)."""
    import re as _re
    t = title
    t = _re.sub(r'^Best\b', 'Compare', t)
    t = _re.sub(r'\bBest\b', 'Compare', t)
    t = _re.sub(r'\btop\b', 'listed', t, flags=_re.IGNORECASE)
    t = _re.sub(r'\bRight\b', 'Relevant', t)
    t = _re.sub(r'\bright\b', 'relevant', t)
    return t


def render_category(slug: str, output_dir: Path) -> Path:
    """Render one /categories/<slug>/index.html from DB. Returns the output path."""
    cat = load_category(slug)
    if cat is None:
        raise SystemExit(f"error: no category with slug '{slug}' in DB")

    top = top_lenders_by_category(slug, limit=48)
    total = category_count(slug)
    if total <= 0:
        total = max(int(cat.get("count") or 0), len(top))

    # Wellness guides use a mapped category label distinct from the lender category.
    guide_cat = _WELLNESS_GUIDE_MAP.get(slug, "understanding-credit")
    wellness = wellness_guides_by_category(guide_cat, limit=4)

    # City links reuse /city/ except credit-cards (per Astro behaviour).
    city_links = []
    for city in _LOCAL_CITY_LINKS:
        city_links.append({
            "label": city["label"],
            "href": "/categories/credit-cards/" if slug == "credit-cards" else f"/city/{city['slug']}/",
        })

    # Action links: money (if mapped) + tool (or fallback quiz) + fixed 3
    money = _CATEGORY_MONEY_MAP.get(slug)
    tool = _CATEGORY_TOOL_MAP.get(slug) or {
        "href": "/tools/borrowing-power-quiz/",
        "label": "Borrowing power quiz",
        "body": "Frame your borrowing and credit context before comparing providers.",
    }
    action_links = []
    if money:
        action_links.append(money)
    action_links.append(tool)
    action_links.extend([
        {"href": "/answers/", "label": "Borrower questions", "body": "Read CreditDoc answers that explain common finance terms, risks, and next steps."},
        {"href": "/state/", "label": "State lending rules", "body": "Check state-level lending-law pages before relying on a general category page."},
        {"href": "/research/consumer-complaints/", "label": "Complaint data context", "body": "Understand how public CFPB complaint data can support provider research."},
    ])

    # Prepare category display fields (soften title, provide safe defaults)
    category_ctx = {
        "slug": cat.get("slug") or slug,
        "name": cat.get("name") or slug.replace("-", " ").title(),
        "description": cat.get("description") or "",
        "seo_title": _soften_category_title(cat.get("seo_title") or f"{cat.get('name') or slug} | CreditDoc"),
        "seo_description": cat.get("seo_description") or cat.get("description") or "",
    }

    # Inline-link the description via the shared linker (matches Astro linker output style).
    linked_description = linkify_description(
        category_ctx["description"],
        current_slug=slug,
        current_category=slug,
        money_budget=4,
    ) if category_ctx["description"] else ""

    is_loan_category = (cat.get("filter_type") == "loan")

    # Pre-build ItemList JSON-LD via the shared _safe_jsonld_str helper.
    item_list_jsonld = ""
    if top:
        item_list_jsonld = _safe_jsonld_str({
            "@context": "https://schema.org",
            "@type": "ItemList",
            "name": f"{category_ctx['name']} Company Profiles",
            "itemListOrder": "https://schema.org/ItemListOrderDescending",
            "numberOfItems": len(top),
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": i,
                    "name": l.get("name") or l.get("slug"),
                    "url": f"https://www.creditdoc.co/review/{l['slug']}/",
                }
                for i, l in enumerate(top, start=1)
            ],
        })

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("category.html.j2")
    html = template.render(
        category=category_ctx,
        top_lenders=list(top),
        total_count=total,
        wellness_guides=list(wellness),
        local_city_links=city_links,
        action_links=action_links,
        is_loan_category=is_loan_category,
        linked_description=linked_description,
        item_list_jsonld=item_list_jsonld,
    )

    out_path = output_dir / "categories" / slug / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path


_CATEGORY_ALIASES: dict[str, str] = {"fix-my-credit": "credit-repair"}


def render_city(slug: str, output_dir: Path) -> Path:
    """Render one /city/<slug>/index.html from DB. Returns the output path."""
    # Locate the city by slug (single scan of the aggregated cities list).
    match = None
    for c in cities_with_lenders(5):
        if c["slug"] == slug:
            match = c
            break
    if match is None:
        raise SystemExit(f"error: no city with slug '{slug}' (need ≥5 indexable lenders)")

    lenders = list(lenders_by_city_state(match["city"].lower(), match["state_abbr"]))
    lender_total = len(lenders)

    # Group by category (with alias collapse, matches Astro).
    groups: dict[str, list[dict[str, Any]]] = {}
    for l in lenders:
        cat = _CATEGORY_ALIASES.get(l.get("category") or "", l.get("category") or "unknown")
        groups.setdefault(cat, []).append(l)
    sorted_groups = sorted(groups.items(), key=lambda kv: -len(kv[1]))

    # Category display-name map (from categories table).
    cat_names: dict[str, str] = {}
    for cat in all_categories():
        s = cat.get("slug")
        if s:
            cat_names[s] = cat.get("name") or s

    # Featured providers: order by stored google_rating (0-5 only, ≥1 reviews).
    def _grate(l: dict[str, Any]) -> float:
        gr = l.get("google_rating") or 0
        gc = l.get("google_reviews_count") or 0
        try:
            gr_f = float(gr); gc_i = int(gc)
        except (TypeError, ValueError):
            return 0.0
        if 0 < gr_f <= 5 and gc_i >= 1:
            return gr_f
        return 0.0
    featured = sorted(lenders, key=lambda l: -_grate(l))[:6]

    # Sort inside each group for the by-category grid (matches Astro).
    for cat, items in sorted_groups:
        items.sort(key=lambda l: -_grate(l))

    other_cities = [c for c in cities_with_lenders(30) if c["slug"] != slug][:24]

    # SEO copy.
    local_kw = f"loan companies in {match['city']}"
    credit_repair_kw = f"{match['city']} credit repair"
    personal_loans_kw = f"personal loans {match['city']}"
    business_loans_kw = f"business loans {match['city']}"
    seo_title = f"Loan Companies in {match['city']}, {match['state_abbr']} | CreditDoc"
    seo_description = (
        f"Compare {local_kw}, {credit_repair_kw}, {personal_loans_kw}, and "
        f"financial service profiles in {match['city']}, {match['state_abbr']}. "
        f"Review {lender_total} local listings."
    )

    # JSON-LD, pre-serialised via the safe helper.
    collection_jsonld = _safe_jsonld_str({
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": f"Loan Companies in {match['city']}, {match['state_abbr']}",
        "description": seo_description,
        "url": f"https://www.creditdoc.co/city/{slug}/",
        "about": {
            "@type": "City",
            "name": match["city"],
            "containedInPlace": {"@type": "State", "name": match["state"]},
        },
    })
    item_list_jsonld = ""
    if featured:
        item_list_jsonld = _safe_jsonld_str({
            "@context": "https://schema.org",
            "@type": "ItemList",
            "name": f"Financial Service Profiles in {match['city']}, {match['state_abbr']}",
            "itemListOrder": "https://schema.org/ItemListOrderDescending",
            "numberOfItems": len(featured),
            "itemListElement": [
                {"@type": "ListItem", "position": i, "name": l.get("name"), "url": f"https://www.creditdoc.co/review/{l['slug']}/"}
                for i, l in enumerate(featured, start=1)
            ],
        })
    breadcrumb_jsonld = _safe_jsonld_str({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://www.creditdoc.co/"},
            {"@type": "ListItem", "position": 2, "name": "Cities", "item": "https://www.creditdoc.co/city/"},
            {"@type": "ListItem", "position": 3, "name": f"{match['city']}, {match['state_abbr']}", "item": f"https://www.creditdoc.co/city/{slug}/"},
        ],
    })

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("city.html.j2")
    html = template.render(
        city=match,
        lender_total=lender_total,
        featured=featured,
        sorted_groups=sorted_groups,
        cat_names=cat_names,
        other_cities=other_cities,
        seo_title=seo_title,
        seo_description=seo_description,
        local_kw=local_kw,
        credit_repair_kw=credit_repair_kw,
        personal_loans_kw=personal_loans_kw,
        business_loans_kw=business_loans_kw,
        map_query=f"{match['city']}, {match['state_abbr']} credit repair financial services",
        collection_jsonld=collection_jsonld,
        item_list_jsonld=item_list_jsonld,
        breadcrumb_jsonld=breadcrumb_jsonld,
    )

    out_path = output_dir / "city" / slug / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path


def render_brand(slug: str, output_dir: Path) -> Path:
    """Render one /brand/<slug>/index.html from src/content/brands/<slug>.json + lenders."""
    brand = load_brand(slug)
    if brand is None:
        raise SystemExit(f"error: no brand with slug '{slug}' in src/content/brands/")

    lenders = list(lenders_by_brand(slug))
    if not lenders:
        raise SystemExit(f"error: brand '{slug}' has no indexable lenders")

    # Group by state (company_info.state fallback).
    by_state: dict[str, list[dict[str, Any]]] = {}
    for l in lenders:
        ci = l.get("company_info") or {}
        st = ci.get("state") or "Unknown"
        by_state.setdefault(st, []).append(l)
    states_grouped = sorted(by_state.items(), key=lambda kv: kv[0])
    states_count = len(states_grouped)

    # Aggregate google ratings.
    google_ratings = []
    for l in lenders:
        gr = l.get("google_rating") or 0
        gc = l.get("google_reviews_count") or 0
        try:
            gr_f = float(gr); gc_i = int(gc)
        except (TypeError, ValueError):
            continue
        if 0 < gr_f <= 5 and gc_i >= 1:
            google_ratings.append(gr_f)
    avg_google_rating = sum(google_ratings) / len(google_ratings) if google_ratings else 0.0

    # Aggregate services / pros / cons / company info.
    services: set[str] = set()
    pros_ct: dict[str, int] = {}
    cons_ct: dict[str, int] = {}
    company_hq = ""
    company_founded = 0
    bbb_rating = ""
    phone_number = ""
    for l in lenders:
        for s in (l.get("services") or []): services.add(s)
        for p in (l.get("pros") or []): pros_ct[p] = pros_ct.get(p, 0) + 1
        for c in (l.get("cons") or []): cons_ct[c] = cons_ct.get(c, 0) + 1
        ci = l.get("company_info") or {}
        if not company_hq and ci.get("headquarters"): company_hq = ci["headquarters"]
        if not company_founded and ci.get("founded_year"):
            try: company_founded = int(ci["founded_year"])
            except (TypeError, ValueError): pass
        if not bbb_rating and ci.get("bbb_rating") and ci["bbb_rating"] != "NR":
            bbb_rating = ci["bbb_rating"]
        if not phone_number and l.get("phone"):
            phone_number = l["phone"]

    top_pros = [p for p, _ in sorted(pros_ct.items(), key=lambda kv: -kv[1])[:5]]
    top_cons = [c for c, _ in sorted(cons_ct.items(), key=lambda kv: -kv[1])[:4]]
    services_list = sorted(services)

    location_count = len(lenders)
    display_name = brand.get("display_name") or slug

    # linker for summary paragraphs (fallback: unmodified)
    linked_summary: list[str] = []
    for para in (brand.get("summary_long") or "").split("\n\n"):
        if para.strip():
            linked_summary.append(linkify_description(para, current_slug=slug, current_category=brand.get("category") or "", money_budget=5))

    linked_faq = [{"q": item.get("q") or "", "a": linkify_description(item.get("a") or "", current_slug=slug, current_category=brand.get("category") or "", money_budget=3)} for item in (brand.get("faq") or [])]

    title = f"{display_name} Locations — Find Your Nearest Branch | CreditDoc"
    description = f"Browse all {location_count} {display_name} locations across {states_count} states. Find hours, addresses, and contact info for each branch."

    org_jsonld = _safe_jsonld_str({
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": display_name,
        "url": brand.get("official_website") or None,
        "description": brand.get("summary_short") or "",
    })
    collection_jsonld = _safe_jsonld_str({
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": f"{display_name} Locations",
        "description": description,
        "url": f"https://www.creditdoc.co/brand/{slug}/",
        "numberOfItems": location_count,
        "provider": {"@type": "Organization", "name": "CreditDoc", "url": "https://www.creditdoc.co"},
    })
    breadcrumb_jsonld = _safe_jsonld_str({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://www.creditdoc.co/"},
            {"@type": "ListItem", "position": 2, "name": "Brands", "item": "https://www.creditdoc.co/"},
            {"@type": "ListItem", "position": 3, "name": display_name, "item": f"https://www.creditdoc.co/brand/{slug}/"},
        ],
    })
    faq_jsonld = ""
    if brand.get("faq"):
        faq_jsonld = _safe_jsonld_str({
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": item.get("q"), "acceptedAnswer": {"@type": "Answer", "text": item.get("a")}}
                for item in brand["faq"]
            ],
        })

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("brand.html.j2")
    html = template.render(
        brand=brand,
        title=title,
        description=description,
        location_count=location_count,
        states_count=states_count,
        avg_google_rating=avg_google_rating,
        google_rating_count=len(google_ratings),
        services_list=services_list,
        top_pros=top_pros,
        top_cons=top_cons,
        company_hq=company_hq,
        company_founded=company_founded,
        bbb_rating=bbb_rating,
        phone_number=phone_number,
        states_grouped=states_grouped,
        linked_summary=linked_summary,
        linked_faq=linked_faq,
        org_jsonld=org_jsonld,
        collection_jsonld=collection_jsonld,
        breadcrumb_jsonld=breadcrumb_jsonld,
        faq_jsonld=faq_jsonld,
    )

    out_path = output_dir / "brand" / slug / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path


def render_state(slug: str, output_dir: Path) -> Path:
    """Render one /state/<slug>/index.html from states.json + lenders."""
    # Find state by slug (name lowercased-with-hyphens).
    state = None
    for s in all_states_info():
        if s["slug"] == slug:
            state = s
            break
    if state is None:
        raise SystemExit(f"error: no state with slug '{slug}'")

    lenders = list(lenders_in_state(state["abbr"], limit=60))
    counts = state_lender_and_city_counts(state["abbr"])
    lender_count = counts["lender_count"]
    city_count = counts["city_count"]

    state_data = state_context(state["abbr"])

    # Category groups from top-60 lenders.
    groups: dict[str, list[dict[str, Any]]] = {}
    for l in lenders:
        cat = l.get("category") or "unknown"
        groups.setdefault(cat, []).append(l)
    sorted_groups = sorted(groups.items(), key=lambda kv: -len(kv[1]))

    cat_names: dict[str, str] = {}
    for cat in all_categories():
        s = cat.get("slug")
        if s:
            cat_names[s] = cat.get("name") or s

    # Top lenders — filter by google rating like Astro.
    def _has_google(l):
        gr = l.get("google_rating") or 0
        gc = l.get("google_reviews_count") or 0
        try:
            gr_f = float(gr); gc_i = int(gc)
        except (TypeError, ValueError):
            return False
        return 0 < gr_f <= 5 and gc_i >= 1 and len((l.get("description_short") or "")) > 20
    top_lenders = sorted([l for l in lenders if _has_google(l)], key=lambda l: -float(l.get("google_rating") or 0))[:10]

    # Cities in this state, top 30 by count.
    state_cities = [c for c in cities_with_lenders(5) if c["state_abbr"] == state["abbr"]][:30]

    # Other states (12 alphabetically-first, excluding self).
    other_states = [s for s in all_states_info() if s["abbr"] != state["abbr"]][:12]

    has_lenders = lender_count > 0

    if has_lenders:
        title = f"Credit Repair & Financial Services in {state['name']} ({state['abbr']}) | CreditDoc"
    else:
        title = f"{state['name']} Credit & Lending Laws | CreditDoc"

    if has_lenders and state_data and state_data.get("consumer_rights_summary"):
        summary_first = (state_data["consumer_rights_summary"] or "").split(".")[0]
        description = f"Find {lender_count} credit repair companies and lenders in {state['name']}. {summary_first}."
    elif has_lenders:
        description = f"Compare {lender_count} credit repair companies, personal lenders, and financial services in {state['name']}. BBB ratings, pricing, and reviews."
    else:
        crs = (state_data.get("consumer_rights_summary") if state_data else "") or ""
        first = crs.split(".")[0] if crs else ""
        description = f"{state['name']} lending regulations, credit repair laws, consumer protections, and financial resources. {first}"

    collection_jsonld = _safe_jsonld_str({
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": f"Credit Repair & Financial Services in {state['name']}",
        "description": description,
        "url": f"https://www.creditdoc.co/state/{slug}/",
        "about": {"@type": "State", "name": state["name"], "containedInPlace": {"@type": "Country", "name": "United States"}},
        "publisher": {"@type": "Organization", "name": "CreditDoc", "url": "https://www.creditdoc.co"},
    })
    breadcrumb_jsonld = _safe_jsonld_str({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://www.creditdoc.co/"},
            {"@type": "ListItem", "position": 2, "name": "States", "item": "https://www.creditdoc.co/state/"},
            {"@type": "ListItem", "position": 3, "name": state["name"], "item": f"https://www.creditdoc.co/state/{slug}/"},
        ],
    })
    item_list_jsonld = ""
    if top_lenders:
        item_list_jsonld = _safe_jsonld_str({
            "@context": "https://schema.org",
            "@type": "ItemList",
            "name": f"Financial Service Profiles in {state['name']}",
            "itemListElement": [
                {
                    "@type": "ListItem", "position": i,
                    "item": {
                        "@type": "FinancialService",
                        "name": l.get("name"),
                        "url": f"https://www.creditdoc.co/review/{l['slug']}/",
                        **({"aggregateRating": {"@type": "AggregateRating", "ratingValue": l.get("google_rating"), "bestRating": 5, "worstRating": 1, "ratingCount": l.get("google_reviews_count")}} if l.get("google_rating") and l.get("google_reviews_count") else {}),
                    }
                }
                for i, l in enumerate(top_lenders[:6], start=1)
            ],
        })

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("state.html.j2")
    html = template.render(
        state=state,
        state_data=state_data,
        title=title,
        description=description,
        lender_count=lender_count,
        city_count=city_count,
        category_group_count=len(sorted_groups),
        sorted_groups=sorted_groups,
        cat_names=cat_names,
        state_cities=state_cities,
        top_lenders=top_lenders,
        other_states=other_states,
        has_lenders=has_lenders,
        collection_jsonld=collection_jsonld,
        breadcrumb_jsonld=breadcrumb_jsonld,
        item_list_jsonld=item_list_jsonld,
    )

    out_path = output_dir / "state" / slug / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path


_BROWSE_KEYWORDS: dict[str, dict[str, str]] = {
    "personal-loans": {"h1": "Personal Loans {city}, {abbr}"},
    "business-loans": {"h1": "Business Loans {city}, {abbr}"},
    "credit-repair": {"h1": "{city} Credit Repair Companies"},
}


def render_browse(cat_slug: str, city_slug: str, output_dir: Path) -> Path:
    """Render one /browse/<cat>/<city>/index.html from lenders in (cat, city, state)."""
    # Find city.
    city = None
    for c in cities_with_lenders(5):
        if c["slug"] == city_slug:
            city = c
            break
    if city is None:
        raise SystemExit(f"error: unknown city slug '{city_slug}'")

    # Find category.
    cat = None
    for cc in all_categories():
        if cc.get("slug") == cat_slug:
            cat = cc
            break
    if cat is None:
        raise SystemExit(f"error: unknown category slug '{cat_slug}'")

    lenders_all = list(lenders_by_city_state(city["city"].lower(), city["state_abbr"]))
    lenders = [l for l in lenders_all if (l.get("category") or "") == cat_slug]
    # Filter to usable copy (skips 403/scrape failures).
    def _usable(l):
        d = (l.get("description_short") or "")
        if any(bad in d for bad in ("403 Forbidden", "Unable to verify", "Unable to generate")):
            return False
        return len(d) >= 30
    display_lenders = [l for l in lenders if _usable(l)]

    # Sort: google-rated first (by rating desc), then by name.
    def _grate(l):
        gr = l.get("google_rating") or 0
        gc = l.get("google_reviews_count") or 0
        try:
            gr_f = float(gr); gc_i = int(gc)
        except (TypeError, ValueError):
            return 0.0
        return gr_f if 0 < gr_f <= 5 and gc_i >= 1 else 0.0
    display_lenders.sort(key=lambda l: (-_grate(l), (l.get("name") or "").lower()))

    google_rated = [l for l in display_lenders if _grate(l) > 0]
    top_rated = [l for l in google_rated if len(l.get("description_short") or "") > 20][:6]
    total_rated = len(google_rated)
    avg_rating = None
    if total_rated > 0:
        avg_rating = f"{sum(_grate(l) for l in google_rated) / total_rated:.1f}"

    cat_name = cat.get("name") or cat_slug.replace("-", " ").title()
    state_slug = city["state"].lower().replace(" ", "-")

    kw = _BROWSE_KEYWORDS.get(cat_slug) or {}
    h1 = kw.get("h1", "{cat_name} in {city}, {abbr}").format(
        cat_name=cat_name, city=city["city"], abbr=city["state_abbr"]
    )
    provider_h2 = f"{cat_name} Companies in {city['city']}"
    all_h2 = f"Listed {cat_name} Profiles in {city['city']}"
    regulation_h2 = f"{city['state']} Rules for {cat_name} in {city['city']}"

    display_count = len(display_lenders)
    title = f"{h1} | CreditDoc"
    description = (
        f"Compare {cat_name.lower()} providers in {city['city']}, {city['state_abbr']} — "
        f"{display_count} listed profiles with pricing, licensing, and CFPB complaint context. "
        f"Review {display_count} listed profiles."
    )

    collection_jsonld = _safe_jsonld_str({
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": h1,
        "description": description,
        "url": f"https://www.creditdoc.co/browse/{cat_slug}/{city_slug}/",
        "about": {
            "@type": "Service",
            "name": cat_name,
            "areaServed": {"@type": "City", "name": city["city"], "containedInPlace": {"@type": "State", "name": city["state"]}},
        },
        "provider": {"@type": "Organization", "name": "CreditDoc", "url": "https://www.creditdoc.co"},
    })
    breadcrumb_jsonld = _safe_jsonld_str({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://www.creditdoc.co/"},
            {"@type": "ListItem", "position": 2, "name": cat_name, "item": f"https://www.creditdoc.co/categories/{cat_slug}/"},
            {"@type": "ListItem", "position": 3, "name": f"{city['city']}, {city['state_abbr']}", "item": f"https://www.creditdoc.co/browse/{cat_slug}/{city_slug}/"},
        ],
    })
    item_list_jsonld = ""
    if top_rated:
        item_list_jsonld = _safe_jsonld_str({
            "@context": "https://schema.org",
            "@type": "ItemList",
            "name": f"Top {cat_name} Providers in {city['city']}",
            "numberOfItems": len(top_rated),
            "itemListElement": [
                {"@type": "ListItem", "position": i, "name": l.get("name"), "url": f"https://www.creditdoc.co/review/{l['slug']}/"}
                for i, l in enumerate(top_rated, start=1)
            ],
        })

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("browse.html.j2")
    html = template.render(
        cat_slug=cat_slug,
        cat_name=cat_name,
        city=city,
        state_slug=state_slug,
        title=title,
        description=description,
        h1=h1,
        provider_h2=provider_h2,
        all_h2=all_h2,
        regulation_h2=regulation_h2,
        avg_rating=avg_rating,
        total_rated=total_rated,
        top_rated=top_rated,
        display_lenders=display_lenders,
        display_count=display_count,
        collection_jsonld=collection_jsonld,
        breadcrumb_jsonld=breadcrumb_jsonld,
        item_list_jsonld=item_list_jsonld,
    )

    out_path = output_dir / "browse" / cat_slug / city_slug / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path


_LEGAL_SUFFIXES = {"inc", "llc", "ltd", "co", "corp", "corporation", "company", "pllc", "lp"}


def _trends_slug_context(slug: str, company_name: str) -> str:
    """Port of Astro's slugContext helper — extract non-name context words from
    slug, title-cased. Used to disambiguate branch/location profiles from
    company-name-only profiles.
    """
    import re as _re
    def _s(s):
        return _re.sub(r"[^a-z0-9]+", "-", _re.sub(r"&", " and ", s.lower())).strip("-")
    slug_parts = [p for p in slug.split("-") if p]
    company_parts = [p for p in _s(company_name).split("-") if p and p not in _LEGAL_SUFFIXES]
    i = 0
    for cp in company_parts:
        if i < len(slug_parts) and slug_parts[i] == cp:
            i += 1
    ctx = slug_parts[i:]
    if not ctx or len(ctx) == len(slug_parts):
        return ""
    return " ".join(p.upper() if len(p) == 2 else p.capitalize() for p in ctx)


def render_trends(slug: str, output_dir: Path) -> Path:
    """Render one /trends/<slug>/index.html from cfpb-trends.json entry."""
    cfpb = load_trends_entry(slug)
    if cfpb is None:
        raise SystemExit(f"error: no cfpb-trends entry for slug '{slug}'")

    def _fmt_pct(v):
        if v is None: return None
        try: return f"{float(v):.1f}"
        except (TypeError, ValueError): return None
    resolution_pct = _fmt_pct(cfpb.get("resolution_rate"))
    timely_pct = _fmt_pct(cfpb.get("timely_rate"))
    breakdown = cfpb.get("response_breakdown") or {}
    breakdown_total = sum(breakdown.values()) if breakdown else 0
    response_breakdown_items = []
    if breakdown_total > 0:
        for k, v in sorted(breakdown.items(), key=lambda kv: -kv[1]):
            response_breakdown_items.append((k, v, 100.0 * v / breakdown_total))

    context_label = _trends_slug_context(cfpb["slug"], cfpb.get("company_name") or "")
    max_len = max(18, 48 - len(context_label)) if context_label else 42
    company_name = cfpb.get("company_name") or ""
    title_company = " ".join(company_name.split())
    if len(title_company) > max_len:
        title_company = title_company[: max_len - 1].rstrip()
    seo_title = (
        f"{title_company} {context_label} CFPB | CreditDoc"
        if context_label
        else f"{title_company} CFPB Data | CreditDoc"
    )
    seo_desc = (
        f"{company_name}{' (' + context_label + ')' if context_label else ''} "
        f"CFPB response data: {resolution_pct or '-'}% recorded response-outcome rate, "
        f"{timely_pct or '-'}% timely responses. Use as transparency context, not a rating."
    )

    webpage_jsonld = _safe_jsonld_str({
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": seo_title,
        "description": seo_desc,
        "url": f"https://www.creditdoc.co/trends/{cfpb['slug']}/",
        "isPartOf": {"@type": "WebSite", "name": "CreditDoc", "url": "https://www.creditdoc.co"},
        "author": {"@type": "Organization", "name": "CreditDoc", "url": "https://www.creditdoc.co"},
        "publisher": {"@type": "Organization", "name": "CreditDoc", "url": "https://www.creditdoc.co",
                       "logo": {"@type": "ImageObject", "url": "https://www.creditdoc.co/favicon.svg"}},
        **({"dateModified": cfpb["checked_at"]} if cfpb.get("checked_at") else {}),
    })
    breadcrumb_jsonld = _safe_jsonld_str({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://www.creditdoc.co/"},
            {"@type": "ListItem", "position": 2, "name": "Consumer Response Data", "item": "https://www.creditdoc.co/research/consumer-complaints/"},
            {"@type": "ListItem", "position": 3, "name": company_name, "item": f"https://www.creditdoc.co/trends/{cfpb['slug']}/"},
        ],
    })

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("trends.html.j2")
    html = template.render(
        cfpb=cfpb,
        seo_title=seo_title,
        seo_desc=seo_desc,
        resolution_pct=resolution_pct,
        timely_pct=timely_pct,
        breakdown_total=breakdown_total,
        response_breakdown_items=response_breakdown_items,
        webpage_jsonld=webpage_jsonld,
        breadcrumb_jsonld=breadcrumb_jsonld,
    )

    out_path = output_dir / "trends" / slug / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path


def render_compare(slug: str, output_dir: Path) -> Path:
    """Render one /compare/<slug>/index.html from comparisons.json + 2 lender rows."""
    comp = load_comparison(slug)
    if comp is None:
        raise SystemExit(f"error: no comparison entry for slug '{slug}'")
    lender_a = load_lender(comp["lender_a"])
    lender_b = load_lender(comp["lender_b"])
    if lender_a is None or lender_b is None:
        raise SystemExit(f"error: comparison '{slug}' missing lender rows")

    winner_slug = comp.get("winner")
    winner_lender = lender_a if winner_slug == lender_a["slug"] else lender_b

    title = (comp.get("seo_title") or comp.get("title") or f"{lender_a['name']} vs {lender_b['name']}")
    if "|" not in title:
        title = f"{title} | CreditDoc"
    description = (
        comp.get("seo_description")
        or comp.get("summary")
        or f"Compare {lender_a['name']} vs {lender_b['name']} — pricing, ratings, licensing, and refund policy side by side."
    )

    webpage_jsonld = _safe_jsonld_str({
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": title,
        "description": description,
        "url": f"https://www.creditdoc.co/compare/{slug}/",
        "isPartOf": {"@type": "WebSite", "name": "CreditDoc", "url": "https://www.creditdoc.co"},
        "publisher": {"@type": "Organization", "name": "CreditDoc", "url": "https://www.creditdoc.co"},
    })
    breadcrumb_jsonld = _safe_jsonld_str({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://www.creditdoc.co/"},
            {"@type": "ListItem", "position": 2, "name": "Compare", "item": "https://www.creditdoc.co/best/"},
            {"@type": "ListItem", "position": 3, "name": f"{lender_a['name']} vs {lender_b['name']}", "item": f"https://www.creditdoc.co/compare/{slug}/"},
        ],
    })

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("compare.html.j2")
    html = template.render(
        comparison=comp,
        lender_a=lender_a,
        lender_b=lender_b,
        winner_lender=winner_lender,
        title=title,
        description=description,
        webpage_jsonld=webpage_jsonld,
        breadcrumb_jsonld=breadcrumb_jsonld,
    )

    out_path = output_dir / "compare" / slug / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CreditDoc renderer — Astro-free HTML from DB.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    review = subparsers.add_parser("review", help="Render /review/[slug]/ page(s)")
    review.add_argument("--slug", required=True, help="Lender slug to render")
    review.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "renderer_dist"),
        help="Output directory (default: renderer_dist/)",
    )

    answer = subparsers.add_parser("answer", help="Render /answers/[slug]/ page(s)")
    answer.add_argument("--slug", required=True, help="Cluster answer slug to render")
    answer.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "renderer_dist"),
        help="Output directory (default: renderer_dist/)",
    )

    blog = subparsers.add_parser("blog", help="Render /blog/[slug]/ page(s)")
    blog.add_argument("--slug", required=True, help="Blog post slug to render")
    blog.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "renderer_dist"),
        help="Output directory (default: renderer_dist/)",
    )

    wellness = subparsers.add_parser("wellness", help="Render /financial-wellness/[slug]/ page(s)")
    wellness.add_argument("--slug", required=True, help="Wellness guide slug to render")
    wellness.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "renderer_dist"),
        help="Output directory (default: renderer_dist/)",
    )

    category = subparsers.add_parser("category", help="Render /categories/[slug]/ page(s)")
    category.add_argument("--slug", required=True, help="Category slug to render")
    category.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "renderer_dist"),
        help="Output directory (default: renderer_dist/)",
    )

    city = subparsers.add_parser("city", help="Render /city/[slug]/ page(s)")
    city.add_argument("--slug", required=True, help="City slug (e.g. new-york-ny) to render")
    city.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "renderer_dist"),
        help="Output directory (default: renderer_dist/)",
    )

    brand = subparsers.add_parser("brand", help="Render /brand/[slug]/ page(s)")
    brand.add_argument("--slug", required=True, help="Brand slug to render")
    brand.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "renderer_dist"),
        help="Output directory (default: renderer_dist/)",
    )

    state_p = subparsers.add_parser("state", help="Render /state/[slug]/ page(s)")
    state_p.add_argument("--slug", required=True, help="State slug (e.g. california) to render")
    state_p.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "renderer_dist"),
        help="Output directory (default: renderer_dist/)",
    )

    browse = subparsers.add_parser("browse", help="Render /browse/[cat]/[city]/ page(s)")
    browse.add_argument("--cat", required=True, help="Category slug (e.g. personal-loans)")
    browse.add_argument("--city", required=True, help="City slug (e.g. new-york-ny)")
    browse.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "renderer_dist"),
        help="Output directory (default: renderer_dist/)",
    )

    trends = subparsers.add_parser("trends", help="Render /trends/[slug]/ page(s)")
    trends.add_argument("--slug", required=True, help="CFPB entry slug")
    trends.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "renderer_dist"),
        help="Output directory (default: renderer_dist/)",
    )

    compare = subparsers.add_parser("compare", help="Render /compare/[slug]/ page(s)")
    compare.add_argument("--slug", required=True, help="Comparison slug (e.g. credit-saint-vs-sky-blue-credit)")
    compare.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "renderer_dist"),
        help="Output directory (default: renderer_dist/)",
    )

    args = parser.parse_args()

    if args.command == "review":
        out = render_review(args.slug, Path(args.output_dir))
        print(f"rendered: {out} ({out.stat().st_size} bytes)")
    elif args.command == "answer":
        out = render_answer(args.slug, Path(args.output_dir))
        print(f"rendered: {out} ({out.stat().st_size} bytes)")
    elif args.command == "blog":
        out = render_blog(args.slug, Path(args.output_dir))
        print(f"rendered: {out} ({out.stat().st_size} bytes)")
    elif args.command == "wellness":
        out = render_wellness(args.slug, Path(args.output_dir))
        print(f"rendered: {out} ({out.stat().st_size} bytes)")
    elif args.command == "category":
        out = render_category(args.slug, Path(args.output_dir))
        print(f"rendered: {out} ({out.stat().st_size} bytes)")
    elif args.command == "city":
        out = render_city(args.slug, Path(args.output_dir))
        print(f"rendered: {out} ({out.stat().st_size} bytes)")
    elif args.command == "brand":
        out = render_brand(args.slug, Path(args.output_dir))
        print(f"rendered: {out} ({out.stat().st_size} bytes)")
    elif args.command == "state":
        out = render_state(args.slug, Path(args.output_dir))
        print(f"rendered: {out} ({out.stat().st_size} bytes)")
    elif args.command == "browse":
        out = render_browse(args.cat, args.city, Path(args.output_dir))
        print(f"rendered: {out} ({out.stat().st_size} bytes)")
    elif args.command == "trends":
        out = render_trends(args.slug, Path(args.output_dir))
        print(f"rendered: {out} ({out.stat().st_size} bytes)")
    elif args.command == "compare":
        out = render_compare(args.slug, Path(args.output_dir))
        print(f"rendered: {out} ({out.stat().st_size} bytes)")
    else:
        parser.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
