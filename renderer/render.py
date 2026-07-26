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
import re
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
    all_states_with_lending_laws,
    all_trends_entries,
    browse_pairs,
    load_comparison,
    category_count,
    category_to_pillar,
    all_listicles,
    cities_with_lenders,
    glossary_for_context,
    glossary_for_review,
    glossary_grouped_for_context,
    load_listicle,
    lenders_by_brand,
    lenders_by_city_state,
    lenders_in_state,
    load_blog_post,
    load_brand,
    load_category,
    load_cluster_answer,
    load_lender,
    load_state_lending_laws,
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
    states_with_lenders,
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


_SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")
_MD_BOLD_RE = re.compile(r'\*\*([^\n]+?)\*\*')
_MD_ITALIC_RE = re.compile(r'(?<![*\w])\*([^*\n]+?)\*(?!\w)')


def _apply_inline_md(s: str) -> str:
    """Convert **bold** and *italic* to HTML. Idempotent — safe to run on already-linked text.

    Italic runs before bold so a **bold clause containing *italic*** still resolves.
    """
    s = _MD_ITALIC_RE.sub(r'<em>\1</em>', s)
    s = _MD_BOLD_RE.sub(r'<strong class="font-semibold text-text">\1</strong>', s)
    return s


def _strip_inline_md(s: str) -> str:
    """Drop markdown asterisks so JSON-LD text and other plain-text contexts are clean."""
    if not s:
        return s
    s = _MD_BOLD_RE.sub(r'\1', s)
    s = _MD_ITALIC_RE.sub(r'\1', s)
    return s


def _preprocess_faqs(faqs: list) -> list:
    """Attach `answer_html` (markdown → HTML) and clean `answer` (markdown asterisks stripped).

    Templates render FAQ answers in two places: JSON-LD schema (plain text) and
    the visible FAQ card (HTML). Storing both variants prevents leaked ``**bold**``
    markdown from surfacing in either context.
    """
    out = []
    for f in faqs or []:
        raw = f.get("answer", "") or ""
        new = dict(f)
        new["answer_html"] = _apply_inline_md(raw)
        new["answer"] = _strip_inline_md(raw)
        out.append(new)
    return out


def _split_paragraphs(text: str, target_sentences: int = 3) -> list[str]:
    """Return a list of paragraph strings from a description blob.

    Handles three storage patterns: (a) `\\n\\n` separated (already paragraphed),
    (b) single `\\n` separated (one break per paragraph), and (c) one continuous
    blob with no breaks — falls back to grouping sentences.

    Also applies inline markdown (**bold**, *italic*) so hand-authored review
    descriptions like Chime's "**Checking Account:**" render as HTML rather
    than leaking asterisks to the user.
    """
    if not text:
        return []
    text = text.replace("\r\n", "\n").strip()
    if "\n\n" in text:
        parts = [p.strip() for p in text.split("\n\n") if p.strip()]
    elif "\n" in text:
        parts = [p.strip() for p in text.split("\n") if p.strip()]
    else:
        parts = [text]
    out: list[str] = []
    for part in parts:
        if len(part) <= 600:
            out.append(_apply_inline_md(part))
            continue
        sentences = _SENT_SPLIT_RE.split(part)
        for i in range(0, len(sentences), target_sentences):
            chunk = " ".join(sentences[i : i + target_sentences]).strip()
            if chunk:
                out.append(_apply_inline_md(chunk))
    return out


def _seo_meta(text: str, max_len: int = 155) -> str:
    """Keep rendered meta descriptions under crawler limits without mid-word cuts."""
    clean = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(clean) <= max_len:
        return clean
    return clean[:max_len].rsplit(" ", 1)[0].rstrip(" ,.;:")


def render_review(slug: str, output_dir: Path) -> Path:
    """Render one /review/<slug>/index.html from DB. Returns the output path."""
    lender = load_lender(slug)
    if lender is None:
        raise SystemExit(f"error: no lender with slug '{slug}' in DB")

    similar = similar_lenders(lender["category"], slug, limit=8)
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

    lender["faqs"] = [
        {**f, "a_html": _apply_inline_md(f.get("a", "") or ""), "a": _strip_inline_md(f.get("a", "") or "")}
        for f in (lender.get("faqs") or [])
    ]

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

    lender["description_long_paragraphs"] = _split_paragraphs(lender["description_long_linked"])

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    is_pending = lender.get("processing_status") == "pending_approval"

    # Regulatory consolidation (2026-07-19): surface CFPB profile as a
    # structured card on review, replacing the dark /trends/ family as
    # the primary display surface. Compute here so template stays simple.
    cfpb_profile = load_trends_entry(slug)
    cfpb_ctx: dict[str, Any] | None = None
    if cfpb_profile and cfpb_profile.get("found_in_cfpb"):
        breakdown = cfpb_profile.get("response_breakdown") or {}
        total_complaints = sum(breakdown.values()) if breakdown else 0
        if total_complaints > 0:
            def _fmt(v):
                try:
                    return f"{float(v):.0f}"
                except (TypeError, ValueError):
                    return None
            top_issues = [i.get("name") for i in (cfpb_profile.get("top_issues") or [])[:3] if i.get("name")]
            cfpb_ctx = {
                "resolution_pct": _fmt(cfpb_profile.get("resolution_rate")),
                "timely_pct": _fmt(cfpb_profile.get("timely_rate")),
                "total_complaints": total_complaints,
                "top_issues": top_issues,
                "data_period": cfpb_profile.get("data_period"),
                "checked_at": cfpb_profile.get("checked_at"),
            }

    template = env.get_template("review.html.j2")
    html = template.render(
        lender=lender,
        similar_lenders=similar,
        related_answers=answers,
        wellness_guides=wellness,
        state_ctx=state_ctx,
        glossary=glossary,
        is_pending=is_pending,
        cfpb=cfpb_ctx,
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
        # Italic first so **bold containing *italic*** still resolves cleanly.
        s = _re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)', r'<em>\1</em>', s)
        s = _re.sub(r'\*\*([^\n]+?)\*\*', r'<strong class="font-semibold text-text">\1</strong>', s)
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
            head = _re.sub(r'^H[1-6]:\s*', '', line[4:])
            out.append(f'<h4 class="text-lg font-semibold text-text mt-6 mb-2">{inline(head)}</h4>')
        elif line.startswith("## "):
            flush_list()
            head = _re.sub(r'^H[1-6]:\s*', '', line[3:])
            out.append(f'<h4 class="text-lg font-semibold text-text mt-6 mb-2">{inline(head)}</h4>')
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
    faqs = _preprocess_faqs([f for f in (answer.get("faq_schema") or []) if isinstance(f, dict) and f.get("question") and f.get("answer")])
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
    key_takeaways = [_apply_inline_md(t) for t in key_takeaways if t]

    # Direct-answer paragraph: ≤300 chars, no leading Yes./No., first section's opening.
    # Per SEO Master Class Rec #1 (pp.80/151/152/154) — the snippet-capture pattern.
    def _direct_answer(section_content: str) -> str:
        if not section_content:
            return ""
        plain = _re.sub(r"\*\*(.+?)\*\*", r"\1", section_content)
        plain = _re.sub(r"[\*_`|#>]+", " ", plain)
        plain = _re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", plain)
        plain = _re.sub(r"\s+", " ", plain).strip()
        plain = _re.sub(r"^(Yes|No|Yes\.|No\.|Yes,|No,)\s+", "", plain, flags=_re.IGNORECASE)
        if len(plain) <= 300:
            return plain
        cut = plain[:300]
        last_sentence_end = max(cut.rfind("."), cut.rfind("!"), cut.rfind("?"))
        if last_sentence_end > 150:
            return cut[:last_sentence_end + 1]
        last_space = cut.rfind(" ")
        return cut[:last_space] + "…" if last_space > 200 else cut + "…"
    direct_answer = _direct_answer(sections_raw[0].get("content", "") if sections_raw else "")

    # Visible-date string. Prefer dateModified > published_at.
    from datetime import datetime as _dt
    def _fmt_date(iso: str) -> str:
        if not iso:
            return ""
        try:
            d = _dt.fromisoformat(iso.replace("Z", "+00:00"))
            return d.strftime("%B %d, %Y")
        except Exception:
            return iso[:10]
    last_updated_iso = answer.get("last_updated") or answer.get("updated_at") or answer.get("published_at") or ""
    published_iso = answer.get("published_at") or answer.get("last_updated") or ""
    last_updated_display = _fmt_date(last_updated_iso)

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
        direct_answer=direct_answer,
        last_updated_display=last_updated_display,
        last_updated_iso=last_updated_iso,
        published_iso=published_iso,
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
    faqs = _preprocess_faqs([f for f in (post.get("faq") or []) if isinstance(f, dict) and f.get("question") and f.get("answer")])

    # Blog uses key_takeaways as a top-level list already
    key_takeaways = post.get("key_takeaways") or []
    if not isinstance(key_takeaways, list):
        key_takeaways = []
    key_takeaways = [_apply_inline_md(t) if isinstance(t, str) else t for t in key_takeaways]

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
    faqs = _preprocess_faqs([f for f in (post.get("faq") or []) if isinstance(f, dict) and f.get("question") and f.get("answer")])
    key_takeaways = post.get("key_takeaways") or []
    if not isinstance(key_takeaways, list):
        key_takeaways = []
    key_takeaways = [_apply_inline_md(t) if isinstance(t, str) else t for t in key_takeaways]
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
        "seo_description": _seo_meta(cat.get("seo_description") or cat.get("description") or ""),
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


def render_credit_guide_hub(slug: str, output_dir: Path) -> Path:
    """Render one /credit-guide/<slug>/index.html.

    Reads the city_guide row from Supabase (via db_remote), joins with local
    SQLite data (state row, lenders, categories), and writes the hub page.
    Phase 3.3a — replaces the Astro-authored index.astro (713 lines).
    """
    import db_remote  # noqa: E402

    guide = db_remote.get_city_guide(slug)
    if guide is None:
        raise SystemExit(f"error: no city_guide with slug '{slug}' in Supabase (need status=ready_for_index)")

    city = guide["city"]
    state_abbr = guide.get("state_abbr", "")
    state_name = guide.get("state_name", "")
    body = guide.get("body_inline") or {}

    state_slug = state_name.lower().replace(" ", "-")
    state_rows = [s for s in all_states_with_lending_laws() if s.get("slug") == state_slug]
    state_row = state_rows[0] if state_rows else None
    state_data = state_row.get("body_inline") if state_row else None
    state_hub_exists = bool(state_row)

    # Credit repair laws — either JSON dict or plain string on the state row.
    crl = state_data.get("credit_repair_laws") if isinstance(state_data, dict) else None
    if isinstance(crl, dict):
        parts = []
        parts.append(crl.get("state_statute") or "State credit repair law")
        if crl.get("statute_code"):
            parts[-1] += f" ({crl['statute_code']})"
        parts[-1] += "."
        if crl.get("upfront_fees_prohibited"):
            parts.append("Upfront fees prohibited.")
        if crl.get("cancellation_period_days"):
            parts.append(f"{crl['cancellation_period_days']}-day cancellation period.")
        if crl.get("bond_required"):
            parts.append(f"${crl.get('bond_amount') or '25,000'} bond required.")
        credit_repair_summary = " ".join(parts)
    elif isinstance(crl, str):
        credit_repair_summary = crl
    else:
        credit_repair_summary = None

    # Lenders in state + city (from SQLite).
    state_lenders_all = list(lenders_in_state(state_abbr)) if state_abbr else []

    def _valid(l: dict[str, Any]) -> bool:
        desc = (l.get("description_short") or "")
        if any(bad in desc for bad in ("403 Forbidden", "Unable to verify", "Unable to generate")):
            return False
        return bool(desc) and len(desc) >= 30

    valid_lenders = [l for l in state_lenders_all[:30] if _valid(l)]
    city_lower = city.lower().replace(" ", "-")
    city_lenders = [
        l for l in valid_lenders
        if (l.get("city") or "").lower() == city.lower()
        or (l.get("slug") and city_lower in l["slug"])
    ]
    nearby_lenders = city_lenders if city_lenders else valid_lenders[:12]
    listed_count = len(state_lenders_all)

    # Category display names.
    cat_names: dict[str, str] = {}
    for c in all_categories():
        s = c.get("slug")
        if s:
            cat_names[s] = c.get("name") or s

    # Local category href map (Astro's localCategoryHref).
    aliases = {"debt-consolidation": "debt-relief", "fix-my-credit": "credit-repair", "payday-loans": "payday-alternatives"}
    def _local_href(cat_slug: str) -> str:
        canonical = aliases.get(cat_slug, cat_slug)
        if canonical == "credit-cards":
            return "/categories/credit-cards/"
        return f"/credit-guide/{slug}/{canonical}/"

    # Sibling city guides in same state (excluding self).
    sibling_guides = [g for g in db_remote.city_guides_by_state(state_abbr) if g.get("slug") != slug][:12]

    # Body content — editorial paragraphs + FAQ + tips + local resources.
    editorial_raw = body.get("editorial") or ""
    editorial_paras = [p for p in re.split(r"</p>\s*<p>", editorial_raw, flags=re.IGNORECASE) if p.strip()]
    editorial_paras = [re.sub(r"</?p[^>]*>", "", p, flags=re.IGNORECASE).strip() for p in editorial_paras]
    editorial_paras = [linkify_description(p, money_budget=2) for p in editorial_paras if p]

    local_questions = body.get("local_questions") or []
    def _linkify_answer(a: str) -> str:
        if re.search(r"<[a-z][\s\S]*>", a, flags=re.IGNORECASE):
            return a  # already HTML
        return linkify_description(a, money_budget=2)
    faqs = [{"q": faq.get("q", ""), "a": _linkify_answer(faq.get("a", ""))} for faq in local_questions]

    credit_tips_raw = body.get("credit_tips") or []
    def _strip_inline(v: str) -> str:
        v = re.sub(r"<a\b[^>]*>(.*?)</a>", r"\1", v, flags=re.IGNORECASE | re.DOTALL)
        v = re.sub(r"<[^>]+>", "", v)
        return v.strip()
    credit_tips = [linkify_description(_strip_inline(t), money_budget=2) for t in credit_tips_raw]

    sba_info = body.get("sba_info") or {}
    consumer_protection = body.get("consumer_protection") or {}
    local_resources = body.get("local_resources") or []

    # SEO.
    seo_title = guide.get("seo_title") or f"Credit Repair & Financial Services in {city}, {state_abbr} | CreditDoc"
    seo_description = guide.get("meta_description") or (
        f"Find credit repair companies, personal lenders, SBA resources, and financial services in "
        f"{city}, {state_name}. Local credit guide with {state_name} lending laws and consumer protections."
    )

    # JSON-LD (WebPage + BreadcrumbList + FAQPage if any).
    webpage_jsonld = _safe_jsonld_str({
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": f"Credit Guide for {city}, {state_abbr}",
        "description": seo_description,
        "url": f"https://www.creditdoc.co/credit-guide/{slug}/",
        "about": {"@type": "City", "name": city, "containedInPlace": {"@type": "State", "name": state_name}},
        "publisher": {"@type": "Organization", "name": "CreditDoc", "url": "https://www.creditdoc.co"},
    })
    breadcrumb_items = [{"@type": "ListItem", "position": 1, "name": "Home", "item": "https://www.creditdoc.co/"}]
    if state_hub_exists:
        breadcrumb_items.append({"@type": "ListItem", "position": 2, "name": state_name, "item": f"https://www.creditdoc.co/state/{state_slug}/"})
        breadcrumb_items.append({"@type": "ListItem", "position": 3, "name": f"{city} Credit Guide", "item": f"https://www.creditdoc.co/credit-guide/{slug}/"})
    else:
        breadcrumb_items.append({"@type": "ListItem", "position": 2, "name": f"{city} Credit Guide", "item": f"https://www.creditdoc.co/credit-guide/{slug}/"})
    breadcrumb_jsonld = _safe_jsonld_str({
        "@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": breadcrumb_items,
    })
    faq_jsonld = ""
    if faqs:
        faq_jsonld = _safe_jsonld_str({
            "@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}}
                for f in faqs[:10]
            ],
        })

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("credit_guide_hub.html.j2")
    html = template.render(
        slug=slug,
        guide=guide,
        city=city,
        state_abbr=state_abbr,
        state_name=state_name,
        state_slug=state_slug,
        state_hub_exists=state_hub_exists,
        state_data=state_data,
        credit_repair_summary=credit_repair_summary,
        listed_count=listed_count,
        nearby_lenders=nearby_lenders,
        cat_names=cat_names,
        local_href=_local_href,
        sibling_guides=sibling_guides,
        editorial_paras=editorial_paras,
        faqs=faqs,
        credit_tips=credit_tips,
        sba_info=sba_info,
        consumer_protection=consumer_protection,
        local_resources=local_resources,
        seo_title=seo_title,
        seo_description=seo_description,
        webpage_jsonld=webpage_jsonld,
        breadcrumb_jsonld=breadcrumb_jsonld,
        faq_jsonld=faq_jsonld,
    )

    out_path = output_dir / "credit-guide" / slug / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path


_CATEGORY_INTROS: dict[str, Any] = {
    "credit-repair": lambda c, s, d: (
        f"Looking for credit repair help in {c}, {s}? Federal law (CROA) protects your right to dispute "
        f"inaccurate items on your credit report, and {s} adds additional consumer protections. "
        + ("State law prohibits credit repair companies from charging upfront fees before services are delivered. "
           if isinstance(d, dict) and (d.get("credit_repair_laws") or {}).get("upfront_fees_prohibited") else "")
        + ((f"Companies must maintain a {(d.get('credit_repair_laws') or {}).get('bond_amount') or '$25,000'} surety bond. ")
           if isinstance(d, dict) and (d.get("credit_repair_laws") or {}).get("bond_required") else "")
        + ((f"You have {(d.get('credit_repair_laws') or {}).get('cancellation_period_days')} days to cancel any credit repair contract without penalty. ")
           if isinstance(d, dict) and (d.get("credit_repair_laws") or {}).get("cancellation_period_days") else "")
        + f"Below are credit repair companies serving {c} residents — compare their services, check their CFPB complaint record, and verify they follow {s} regulations before signing any contract."
    ),
    "personal-loans": lambda c, s, d: (
        f"Need a personal loan in {c}, {s}? "
        + (f"{s} caps interest rates at {d.get('usury_cap')}. " if isinstance(d, dict) and d.get("usury_cap") else "")
        + f"Whether you're consolidating debt, covering an emergency expense, or funding a major purchase, review the listed lender profiles below for APR fields, loan amounts, and eligibility context. {s} residents should verify lender licensing or registration with the state Department of Banking before borrowing."
    ),
    "emergency-cash": lambda c, s, d: (
        f"Need emergency cash in {c}, {s}? "
        + (f"{s} has banned payday lending, limiting payday-loan availability in the state. "
           if isinstance(d, dict) and d.get("payday_loan_status") == "Banned"
           else f"{s} restricts payday lending with rate caps and loan limits. "
           if isinstance(d, dict) and d.get("payday_loan_status") == "Restricted"
           else f"Payday lending may be available in {s}, and listed APRs can be very high. ")
        + f"The profiles below include short-term cash, title-loan, pawn-service, and emergency personal-loan contexts associated with {c}. Compare terms carefully and verify fees before borrowing."
    ),
    "debt-relief": lambda c, s, d: (
        f"Struggling with debt in {c}, {s}? Debt relief companies may advertise creditor negotiation, "
        f"consolidated payments, or structured repayment programs. {s} has specific statutes of limitation "
        f"on debt collection that affect your rights. Review the listed debt relief profiles associated with "
        f"{c}, and consider consulting a HUD-approved credit counselor before committing to any program."
    ),
    "build-credit": lambda c, s, d: (
        f"Building credit in {c}, {s}? Whether you're starting from scratch or rebuilding after financial "
        f"hardship, the profiles below may be relevant to secured cards, credit-builder loans, and "
        f"reporting services. Verify terms, fees, and bureau-reporting details before applying."
    ),
    "free-help": lambda c, s, d: (
        f"Looking for free financial help in {c}, {s}? Nonprofit credit counseling agencies, legal aid "
        f"organizations, and government-funded programs may offer no-cost assistance for debt, foreclosure, "
        f"or credit issues. HUD-approved counselors are required to provide free initial consultations. "
        f"Below are free-help resources listed for this area."
    ),
    "business-loans": lambda c, s, d: (
        f"Need business financing in {c}, {s}? From SBA-backed loans to microloans and lines of credit, "
        f"{c} entrepreneurs can compare several research paths. The SBA {s} District Office can point "
        f"business owners toward participating lender programs and free mentoring through SCORE. Review "
        f"the listed business-lender profiles below for loan size, rate, and eligibility context."
    ),
    "pawn-shops": lambda c, s, d: (
        f"Looking for pawn shops in {c}, {s}? Pawn loans are collateral-based products tied to personal "
        f"property, with fees, redemption periods, and item-recovery rules to verify before signing. "
        f"{s} regulates pawn transactions including maximum interest rates and minimum redemption "
        f"periods. Review the pawn-shop profiles associated with {c} below."
    ),
    "payday-alternatives": lambda c, s, d: (
        f"Looking for payday loan alternatives in {c}, {s}? "
        + (f"Since {s} bans payday lending, these alternatives may be relevant for {c} residents "
           f"researching short-term cash options. "
           if isinstance(d, dict) and d.get("payday_loan_status") == "Banned"
           else f"Compare listed costs, eligibility rules, and repayment terms against any payday loan "
                f"option available in {s}. ")
        + f"Credit union payday alternative loans (PALs), employer advances, and emergency assistance "
        f"programs can provide lower-cost context for short-term borrowing research."
    ),
}

_CATEGORY_QUESTION_TERMS: dict[str, list[str]] = {
    "credit-repair": ["credit repair", "repair company", "dispute"],
    "personal-loans": ["personal loan", "loan", "borrow"],
    "emergency-cash": ["emergency", "cash", "payday", "alternative"],
    "debt-relief": ["debt", "consolidation", "relief"],
    "build-credit": ["improve my credit", "build credit", "credit score", "secured"],
    "free-help": ["free", "counselor", "help", "legal aid"],
    "business-loans": ["sba", "business loan", "small business"],
    "pawn-shops": ["pawn"],
    "credit-monitoring": ["identity theft", "monitoring", "credit score"],
    "payday-alternatives": ["payday", "alternative", "cash"],
    "credit-cards": ["secured", "credit card", "build credit"],
    "banking": ["bank", "credit union"],
    "credit-unions": ["credit union"],
}

_CATEGORY_ANSWER_KEYWORDS: dict[str, list[str]] = {
    "credit-repair": ["build-credit-score-fast", "build-credit-with-no", "does-credit-score-affect"],
    "personal-loans": ["best-personal-loans-bad-credit", "how-to-get-a-personal-loan", "personal-loan-interest-rates", "how-to-find-best-personal-loan", "how-much-can-you-borrow"],
    "emergency-cash": ["best-personal-loans-bad-credit", "how-much-can-you-borrow", "how-to-get-a-personal-loan"],
    "debt-relief": ["debt-consolidation-loans-bad-credit", "debt-consolidation-vs-personal", "can-i-do-debt-consolidation", "can-you-do-debt-consolidation"],
    "build-credit": ["build-credit-with-no", "build-credit-score-fast", "secured-credit-card", "top-secured-credit-cards"],
    "free-help": ["can-i-do-debt-consolidation-myself", "can-you-do-debt-consolidation-yourself", "build-credit-with-no"],
    "business-loans": ["small-business-loans", "how-to-apply-for-a-business-loan", "how-to-get-an-sba-loan", "business-loan-rates-fees", "business-line-of-credit"],
    "pawn-shops": ["how-much-can-you-borrow", "best-personal-loans-bad-credit"],
    "credit-monitoring": ["does-credit-score-affect", "build-credit-score-fast"],
    "payday-alternatives": ["best-personal-loans-bad-credit", "how-much-can-you-borrow", "how-to-get-a-personal-loan"],
    "credit-cards": ["easy-approval-credit-cards", "how-credit-card-interest-works", "no-credit-check-cards", "secured-credit-card"],
    "banking": ["how-much-can-you-borrow", "how-to-get-a-personal-loan"],
    "credit-unions": ["how-much-can-you-borrow", "build-credit-with-no"],
}


def _soften_ymyl(text: str) -> str:
    """Minimal port of src/utils/safe-copy.ts softenYmylCopy. Covers highest-frequency
    YMYL patterns; extend as parity issues surface."""
    if not text:
        return text
    replacements = [
        (r"\bmoney-back guarantees\b", "listed refund terms"),
        (r"\bmoney-back guarantee\b", "listed refund term"),
        (r"\bfull money-back refund\b", "published refund term"),
        (r"\bperformance guarantee\b", "provider-stated performance term"),
        (r"\bcredit score guarantee\b", "score-increase refund term"),
        (r"\bscore-increase guarantee\b", "score-increase refund term"),
        (r"\bguarantee terms\b", "listed refund terms"),
        (r"\bstronger guarantee\b", "more detailed listed refund term"),
        (r"\bbacked by a guarantee\b", "with a published refund term"),
        (r"\bassurance of results\b", "published-term context"),
        (r"\bguaranteed results\b", "published-term context"),
        (r"\bguaranteed removal\b", "listed dispute context"),
        (r"\bguaranteed approval\b", "listed approval context"),
        (r"\bwe guarantee\b", "the provider states"),
        (r"\byou will\b", "you may"),
        (r"\bwill increase\b", "may increase"),
        (r"\bwill improve\b", "may improve"),
        (r"\bwill remove\b", "may dispute for removal of"),
    ]
    for pat, repl in replacements:
        text = re.sub(pat, repl, text, flags=re.IGNORECASE)
    return text


def _all_answer_refs() -> list[dict[str, Any]]:
    """Return {slug,title} for all published/approved cluster answers.

    Mirrors getAllAnswerRefsBuildTime() from Astro (which hit Supabase 'answers').
    We use local SQLite cluster_answers which has the same shape.
    """
    conn = sqlite3.connect("data/creditdoc.db")
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT slug, title FROM cluster_answers WHERE status IN ('published', 'approved')"
        ).fetchall()
        return [{"slug": r["slug"], "title": r["title"]} for r in rows]
    finally:
        conn.close()


def _filter_answer_refs(patterns: list[str], limit: int = 6) -> list[dict[str, Any]]:
    if not patterns:
        return []
    lower = [p.lower() for p in patterns]
    out: list[dict[str, Any]] = []
    for ref in _all_answer_refs():
        s = (ref.get("slug") or "").lower()
        if any(p in s for p in lower):
            out.append(ref)
            if len(out) >= limit:
                break
    return out


def render_credit_guide_category(compound_slug: str, output_dir: Path) -> Path:
    """Render one /credit-guide/<city_slug>/<category>/index.html.

    compound_slug shape: "<city_slug>/<category>" (e.g. "dallas-tx/personal-loans").
    Ports src/pages/credit-guide/[slug]/[category].astro (585 LoC).
    """
    import db_remote  # noqa: E402

    if "/" not in compound_slug:
        raise SystemExit(f"error: credit-guide category slug must be '<city>/<category>', got '{compound_slug}'")
    city_slug, category = compound_slug.split("/", 1)

    guide = db_remote.get_city_guide(city_slug)
    if guide is None:
        raise SystemExit(f"error: no city_guide with slug '{city_slug}' in Supabase")

    cat_row = next((c for c in all_categories() if c.get("slug") == category), None)
    if cat_row is None:
        raise SystemExit(f"error: no category with slug '{category}'")
    cat_name = cat_row.get("name") or category

    city = guide["city"]
    state_abbr = guide.get("state_abbr", "")
    state_name = guide.get("state_name", "")
    guide_data = guide.get("body_inline") or {}

    state_slug = state_name.lower().replace(" ", "-")
    state_rows = [s for s in all_states_with_lending_laws() if s.get("slug") == state_slug]
    state_row = state_rows[0] if state_rows else None
    state_data = state_row.get("body_inline") if state_row else None
    state_hub_exists = bool(state_row)

    is_atm = category == "atm"

    # Localized intro (category × state).
    intro_fn = _CATEGORY_INTROS.get(category)
    if is_atm:
        local_intro = (
            f"Use this page to browse selected ATM and cash access profiles associated with {state_name}. "
            f"CreditDoc does not maintain a complete, real-time inventory of every ATM in {city}; for the "
            f"nearest machine, verify availability directly with your bank, credit union, or ATM network before you go."
        )
    elif intro_fn:
        local_intro = intro_fn(city, state_name, state_data)
    else:
        local_intro = (
            f"Review {cat_name.lower()} provider profiles associated with {city}, {state_name}. "
            f"Compare local and statewide profile context, and check stored Google ratings where available."
        )

    # Lenders in state × category (SQLite).
    all_state_lenders = list(lenders_in_state(state_abbr)) if state_abbr else []
    def _valid(l: dict[str, Any]) -> bool:
        desc = (l.get("description_short") or "")
        if any(bad in desc for bad in ("403 Forbidden", "Unable to verify", "Unable to generate")):
            return False
        return bool(desc) and len(desc) >= 30
    cat_lenders = [l for l in all_state_lenders if l.get("category") == category and _valid(l)][:100]

    city_lower = city.lower().replace(" ", "-")
    city_lenders = [l for l in cat_lenders if l.get("slug") and city_lower in l["slug"]]
    state_only_lenders = [l for l in cat_lenders if l not in city_lenders]
    sorted_lenders = city_lenders + state_only_lenders

    # Soften descriptions once for template consumption.
    def _prep_lender(l: dict[str, Any]) -> dict[str, Any]:
        return {
            **l,
            "description_short_soft": _soften_ymyl(l.get("description_short") or ""),
        }
    city_lenders = [_prep_lender(l) for l in city_lenders]
    state_only_lenders = [_prep_lender(l) for l in state_only_lenders]

    # Local FAQ filtered by category terms.
    local_qs = guide_data.get("local_questions") or []
    if not isinstance(local_qs, list):
        local_qs = []
    terms = _CATEGORY_QUESTION_TERMS.get(category, [cat_name.lower()])
    def _hay(faq: dict) -> str:
        a = re.sub(r"<[^>]+>", " ", faq.get("a") or "")
        return f"{faq.get('q','')} {a}".lower()
    matched = [f for f in local_qs if any(t in _hay(f) for t in terms)][:4]
    faqs_raw = matched if matched else local_qs[:3]
    def _prep_faq(f: dict) -> dict:
        a = f.get("a", "")
        has_html = bool(re.search(r"<[a-z][\s\S]*>", a, flags=re.IGNORECASE))
        return {"q": f.get("q", ""), "a": a if has_html else f"<p>{a}</p>"}
    faqs = [_prep_faq(f) for f in faqs_raw if f.get("q") and f.get("a")]

    # Related answers.
    answer_keywords = _CATEGORY_ANSWER_KEYWORDS.get(category, ["personal-loan", "credit-score"])
    related_answers_list = _filter_answer_refs(answer_keywords, 6)

    # Sibling city guides + related categories.
    sibling_guides = [g for g in db_remote.city_guides_by_state(state_abbr) if g.get("slug") != city_slug][:8]
    related_cats = [c for c in all_categories() if c.get("slug") != category][:10]

    def _local_related_href(cat_slug: str) -> str:
        if cat_slug == "credit-cards":
            return "/categories/credit-cards/"
        return f"/credit-guide/{city_slug}/{cat_slug}/"

    # SEO.
    if is_atm:
        seo_description = _seo_meta(
            f"Browse selected ATM and cash access profiles for {city}, {state_name}. "
            f"Verify current ATM availability directly with your bank, credit union, or ATM network."
        )
    else:
        seo_description = _seo_meta(
            f"Review {len(sorted_lenders)} listed {cat_name.lower()} profiles associated with "
            f"{city}, {state_name}. Compare local context, ratings, reviews, and contact details."
        )
    seo_title = f"{cat_name} in {city}, {state_abbr} — Local Directory | CreditDoc"

    from datetime import date
    today = date.today().isoformat()

    list_name = (f"Selected {state_name} {cat_name} Profiles"
                 if is_atm and not city_lenders
                 else f"{cat_name} Serving {city}, {state_abbr}")

    # JSON-LD.
    breadcrumb_items = [{"@type": "ListItem", "position": 1, "name": "Home", "item": "https://www.creditdoc.co/"}]
    pos = 2
    if state_hub_exists:
        breadcrumb_items.append({"@type": "ListItem", "position": pos, "name": state_name, "item": f"https://www.creditdoc.co/state/{state_slug}/"})
        pos += 1
    breadcrumb_items.append({"@type": "ListItem", "position": pos, "name": f"{city} Credit Guide", "item": f"https://www.creditdoc.co/credit-guide/{city_slug}/"})
    pos += 1
    breadcrumb_items.append({"@type": "ListItem", "position": pos, "name": f"{cat_name} in {city}", "item": f"https://www.creditdoc.co/credit-guide/{city_slug}/{category}/"})

    breadcrumb_jsonld = _safe_jsonld_str({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": breadcrumb_items})
    collection_jsonld = _safe_jsonld_str({
        "@context": "https://schema.org", "@type": "CollectionPage",
        "name": seo_title, "description": seo_description,
        "url": f"https://www.creditdoc.co/credit-guide/{city_slug}/{category}/",
        "inLanguage": "en-US", "dateModified": today,
        "about": {"@type": "FinancialService", "serviceType": cat_name,
                  "areaServed": {"@type": "City", "name": city,
                                 "containedInPlace": {"@type": "State", "name": state_name}}},
        "publisher": {"@type": "Organization", "name": "CreditDoc", "url": "https://www.creditdoc.co"},
    })
    item_list_jsonld = _safe_jsonld_str({
        "@context": "https://schema.org", "@type": "ItemList", "name": list_name,
        "url": f"https://www.creditdoc.co/credit-guide/{city_slug}/{category}/",
        "numberOfItems": len(sorted_lenders),
        "itemListElement": [
            {"@type": "ListItem", "position": i+1, "item": {
                "@type": "FinancialService", "name": l.get("name"),
                "url": f"https://www.creditdoc.co/review/{l['slug']}/",
                "serviceType": cat_name,
                "areaServed": {"@type": "City" if l in [x for x in city_lenders] else "State",
                               "name": city if l in [x for x in city_lenders] else state_name}}}
            for i, l in enumerate(sorted_lenders[:12])
        ],
    }) if sorted_lenders else ""
    faq_jsonld = ""
    if faqs:
        faq_jsonld = _safe_jsonld_str({
            "@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": f["q"],
                 "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", " ", f["a"]).strip()}}
                for f in faqs
            ],
        })

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("credit_guide_category.html.j2")
    html = template.render(
        city_slug=city_slug, category=category,
        city=city, state_abbr=state_abbr, state_name=state_name, state_slug=state_slug,
        state_hub_exists=state_hub_exists,
        cat_name=cat_name, is_atm=is_atm,
        local_intro=local_intro, list_name=list_name,
        city_lenders=city_lenders, state_only_lenders=state_only_lenders,
        n_sorted=len(sorted_lenders),
        faqs=faqs, related_answers=related_answers_list,
        sibling_guides=sibling_guides, related_cats=related_cats,
        local_related_href=_local_related_href,
        seo_title=seo_title, seo_description=seo_description,
        breadcrumb_jsonld=breadcrumb_jsonld,
        collection_jsonld=collection_jsonld,
        item_list_jsonld=item_list_jsonld,
        faq_jsonld=faq_jsonld,
    )

    out_path = output_dir / "credit-guide" / city_slug / category / "index.html"
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
    description = _seo_meta(
        f"Browse {location_count} {display_name} locations across {states_count} states. "
        "Find branch addresses, phone numbers, and profile research."
    )

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
        description = _seo_meta(f"Find {lender_count} credit repair companies and lenders in {state['name']}. {summary_first}.")
    elif has_lenders:
        description = _seo_meta(f"Compare {lender_count} credit repair companies, personal lenders, and financial services in {state['name']}. BBB ratings, pricing, and reviews.")
    else:
        crs = (state_data.get("consumer_rights_summary") if state_data else "") or ""
        first = crs.split(".")[0] if crs else ""
        description = _seo_meta(f"{state['name']} lending regulations, credit repair laws, consumer protections, and financial resources. {first}")

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


_LOAN_TYPES = [
    {"key": "personal_loans",     "name": "Personal Loans",     "icon": "💰"},
    {"key": "payday_loans",       "name": "Payday Loans",       "icon": "⚡"},
    {"key": "title_loans",        "name": "Title Loans",        "icon": "🚗"},
    {"key": "installment_loans",  "name": "Installment Loans",  "icon": "📅"},
    {"key": "mortgage",           "name": "Mortgage",           "icon": "🏠"},
]


def render_state_lending_laws(compound_slug: str, output_dir: Path) -> Path:
    """Render one /state/<state_slug>/lending-laws/index.html.

    compound_slug is `<state_slug>/lending-laws` — the atomic_render helper
    passes it through so the disk path matches the URL structure.
    """
    if "/" not in compound_slug:
        raise SystemExit(f"error: expected 'state_slug/lending-laws', got '{compound_slug}'")
    state_slug, tail = compound_slug.split("/", 1)
    if tail != "lending-laws":
        raise SystemExit(f"error: unexpected subroute '{tail}' for state-lending-laws")

    state = None
    for s in all_states_info():
        if s["slug"] == state_slug:
            state = s
            break
    if state is None:
        raise SystemExit(f"error: no state with slug '{state_slug}'")

    data = load_state_lending_laws(state["abbr"])
    if data is None or not data.get("credit_repair_laws"):
        raise SystemExit(f"error: state '{state['abbr']}' has no credit_repair_laws in states.json")

    lenders = list(lenders_in_state(state["abbr"]))
    cr_lenders = [
        l for l in lenders
        if l.get("category") in ("credit-repair", "credit-counseling")
    ]
    cr_count = len(cr_lenders)
    if cr_count > 0:
        cr_summary = (
            f"Review {cr_count} listed credit repair "
            f"{'provider profile' if cr_count == 1 else 'provider profiles'} in {state['name']}."
        )
    else:
        cr_summary = f"Review local provider listings and state-rule context for {state['name']}."

    cr = data.get("credit_repair_laws") or {}
    lt = data.get("lending_types") or {}
    vp = data.get("veteran_protections") or {}
    complaints = data.get("complaint_resources") or []
    statutes = data.get("statute_links") or []
    glossary = glossary_for_context("lending-laws")
    glossary_groups = glossary_grouped_for_context("lending-laws")

    from datetime import datetime, timezone
    year = datetime.now(timezone.utc).year
    title = f"{state['name']} Lending & Credit Laws ({year}) | CreditDoc"
    description = _seo_meta(
        f"{state['name']} lending regulations, credit repair laws, "
        "payday loan rules, veteran protections (MLA/SCRA), and consumer "
        "rights. Official statute references and complaint resources."
    )

    # Format the "law summary checked" date if present.
    check_iso = data.get("legislation_last_updated") or ""
    check_pretty = ""
    if check_iso:
        try:
            dt = datetime.fromisoformat(check_iso.replace("Z", "+00:00"))
            check_pretty = dt.strftime("%B %-d, %Y")
        except ValueError:
            check_pretty = check_iso

    url = f"https://www.creditdoc.co/state/{state_slug}/lending-laws/"
    webpage_jsonld = _safe_jsonld_str({
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": f"{state['name']} Lending & Credit Laws",
        "description": description,
        "url": url,
        "dateModified": check_iso or datetime.now(timezone.utc).date().isoformat(),
        "publisher": {"@type": "Organization", "name": "CreditDoc", "url": "https://www.creditdoc.co"},
        "about": [
            {"@type": "Thing", "name": f"{state['name']} consumer lending regulations"},
            {"@type": "Thing", "name": "Credit repair laws"},
            {"@type": "Thing", "name": "Military Lending Act"},
        ],
    })
    breadcrumb_jsonld = _safe_jsonld_str({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://www.creditdoc.co/"},
            {"@type": "ListItem", "position": 2, "name": "States", "item": "https://www.creditdoc.co/state/"},
            {"@type": "ListItem", "position": 3, "name": state["name"], "item": f"https://www.creditdoc.co/state/{state_slug}/"},
            {"@type": "ListItem", "position": 4, "name": "Lending Laws", "item": url},
        ],
    })

    other_states = [s for s in states_with_lenders(10) if s["abbr"] != state["abbr"]][:12]

    # Materialize the (key, name, icon, loan) list for the template, skipping absent loan types.
    loan_rows = []
    for lt_row in _LOAN_TYPES:
        loan = lt.get(lt_row["key"])
        if not loan:
            continue
        loan_rows.append({**lt_row, "loan": loan})

    # Interest rate cap short form for the top-right stat card.
    usury_short = ""
    if data.get("usury_cap"):
        usury_short = (data["usury_cap"] or "").split(";")[0].strip()

    # Payday status color mapping (positive/warning/negative).
    payday_status = (data.get("payday_loan_status") or "").strip() or "Unknown"
    if payday_status == "Banned":
        payday_bg, payday_text = "bg-positive-light", "text-positive"
    elif payday_status == "Restricted":
        payday_bg, payday_text = "bg-warning-light", "text-warning"
    else:
        payday_bg, payday_text = "bg-negative-light", "text-negative"

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("state_lending_laws.html.j2")
    html = template.render(
        state=state,
        state_slug=state_slug,
        data=data,
        cr=cr,
        vp=vp,
        complaints=complaints,
        statutes=statutes,
        glossary=glossary,
        glossary_groups=glossary_groups,
        glossary_total=len(glossary),
        title=title,
        description=description,
        year=year,
        url=url,
        check_iso=check_iso,
        check_pretty=check_pretty,
        cr_summary=cr_summary,
        usury_short=usury_short,
        payday_status=payday_status,
        payday_bg=payday_bg,
        payday_text=payday_text,
        loan_rows=loan_rows,
        other_states=other_states,
        webpage_jsonld=webpage_jsonld,
        breadcrumb_jsonld=breadcrumb_jsonld,
    )

    out_path = output_dir / "state" / state_slug / "lending-laws" / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path


_LISTICLE_SOFTEN_PAIRS = [
    # (regex, replacement) — case-insensitive on all
    (re.compile(r"\bexpert analysis\b", re.I), "editorial comparison"),
    (re.compile(r"\bexpert reviews\b", re.I), "editorial reviews"),
    (re.compile(r"\breal results\b", re.I), "documented outcomes"),
    (re.compile(r"\btop picks\b", re.I), "notable profiles"),
    (re.compile(r"\btop pick\b", re.I), "notable profile"),
    (re.compile(r"\bhighest approval rate\b", re.I), "highest stored approval-context claim"),
    (re.compile(r"\bapproval rate\b", re.I), "approval-context claim"),
    (re.compile(r"\bapproval speed\b", re.I), "approval-timing context"),
    (re.compile(r"\bsettlement success rates\b", re.I), "settlement-outcome context"),
    (re.compile(r"\bsuccess rates\b", re.I), "outcome context"),
    (re.compile(r"\bthe best rates\b", re.I), "lower listed rates"),
    (re.compile(r"\bbest rates\b", re.I), "lower listed rates"),
    (re.compile(r"\bbest options\b", re.I), "options to compare"),
    (re.compile(r"\bbest option\b", re.I), "option to compare"),
    (re.compile(r"\bbest choice\b", re.I), "profile to compare"),
    (re.compile(r"\bbest combination\b", re.I), "listed combination"),
    (re.compile(r"\bbest for\b", re.I), "profile signals for"),
    (re.compile(r"\bbest if\b", re.I), "profiled if"),
    (re.compile(r"\bcheapest personal loans\b", re.I), "lower-cost personal loan profiles"),
    (re.compile(r"\bcheapest personal loan\b", re.I), "lower-cost personal loan profile"),
    (re.compile(r"\bcheapest\b", re.I), "lower-cost"),
    (re.compile(r"\blowest APR\b", re.I), "lower listed APR"),
    (re.compile(r"\blowest interest rates\b", re.I), "lower listed interest rates"),
    (re.compile(r"\bTop 10 SBA lender\b", re.I), "listed SBA lending-volume context"),
    (re.compile(r"\btop SBA\b", re.I), "notable SBA"),
    (re.compile(r"\btop-rated\b"), "profiled"),
    (re.compile(r"\bTop-rated\b"), "Profiled"),
    # YMYL soften subset borrowed from safe-copy
    (re.compile(r"\bpredatory\b", re.I), "high-cost"),
    (re.compile(r"\bguaranteed\b", re.I), "listed"),
]

_LISTICLE_TITLE_EXTRA = [
    (re.compile(r"^Cheapest\b", re.I), "Lower-Cost"),
    (re.compile(r"\bTop\b"), "Notable"),
    (re.compile(r"\btop\b"), "notable"),
    (re.compile(r"\bWith Money-Back Guarantee\b", re.I), "With Listed Refund Terms"),
    (re.compile(r"\bMoney-Back Guarantee\b", re.I), "Listed Refund Terms"),
    (re.compile(r"\bLowest Interest Rates\b", re.I), "Lower Listed Interest Rates"),
    (re.compile(r"\bLowest APR Lenders\b", re.I), "Lower Listed APR Lenders"),
    (re.compile(r"\bLow Credit Score Options\b", re.I), "Lower Credit Score Profiles"),
]


def _soften_listicle_copy(text: str) -> str:
    if not text:
        return text or ""
    for pat, rep in _LISTICLE_SOFTEN_PAIRS:
        text = pat.sub(rep, text)
    return text


def _soften_listicle_title(title: str) -> str:
    t = _soften_listicle_copy(title)
    for pat, rep in _LISTICLE_TITLE_EXTRA:
        t = pat.sub(rep, t)
    return t


_LOAN_CATEGORIES_FOR_BEST = {
    "personal-loans", "business-loans", "mortgages",
    "emergency-cash", "payday-alternatives", "pawn-shops",
}


def _pricing_badge_label(lender: dict[str, Any], lowest_price: Any) -> str:
    cat = lender.get("category")
    if cat in _LOAN_CATEGORIES_FOR_BEST:
        return "Rates and terms vary"
    if cat == "credit-cards":
        return "Fees vary by card"
    if cat in ("credit-repair", "debt-relief"):
        if isinstance(lowest_price, (int, float)) and lowest_price > 0:
            return f"From ${lowest_price:.2f}/mo".rstrip("0").rstrip(".") + "/mo" if "." in f"{lowest_price}" else f"From ${lowest_price:.0f}/mo"
        return "Details vary by provider"
    return "Details vary by provider"


def _bbb_class(rating: str | None) -> str:
    r = (rating or "").strip().upper()
    if r in ("A+", "A", "A-"):
        return "bg-positive-light text-positive"
    if r in ("B+", "B", "B-"):
        return "bg-warning-light text-warning"
    return "bg-bg-alt text-muted"


def _best_lowest_price(lender: dict[str, Any]) -> float | int | None:
    pricing = lender.get("pricing") or {}
    tiers = pricing.get("tiers") or []
    prices = [t.get("price") for t in tiers if isinstance(t.get("price"), (int, float))]
    if prices:
        return min(prices)
    return pricing.get("monthly_price")


def render_best(slug: str, output_dir: Path) -> Path:
    """Render one /best/<slug>/index.html from listicles.json + lenders."""
    listicle = load_listicle(slug)
    if listicle is None:
        raise SystemExit(f"error: no listicle with slug '{slug}'")

    # Fill defaults; DON'T soften raw fields yet — Astro renders soften on display copies only.
    raw_title = listicle.get("title") or listicle.get("slug")
    raw_seo_title = listicle.get("seo_title") or raw_title
    raw_description = listicle.get("description") or ""
    raw_seo_description = listicle.get("seo_description") or raw_description
    raw_intro = listicle.get("intro") or ""
    raw_tldr = listicle.get("tldr") or ""
    raw_takeaways = listicle.get("key_takeaways") or []
    raw_faq = listicle.get("faq") or []
    raw_lender_slugs = listicle.get("lenders") or []

    # Display copies (softened).
    title = _soften_listicle_title(raw_title)
    seo_title = _soften_listicle_title(raw_seo_title)
    description = _soften_listicle_copy(raw_description)
    seo_description = _soften_listicle_copy(raw_seo_description)
    # Prepend short title to SEO description if "best" is in title but not in description.
    if re.search(r"\bbest\b", raw_seo_title, re.I) and not re.search(r"\bbest\b", seo_description, re.I):
        short = re.sub(r"\s*\([^)]*\)", "", raw_seo_title)
        short = re.sub(r"\s*[—-].*$", "", short)
        short = re.sub(r"\s*\|\s*CreditDoc.*$", "", short, flags=re.I).strip()
        seo_description = f"{short}: {seo_description}"
    intro = _soften_listicle_copy(raw_intro)
    tldr = _soften_listicle_copy(raw_tldr) if raw_tldr else ""
    takeaways = [_soften_listicle_copy(t) for t in raw_takeaways]
    faq = [{"q": _soften_listicle_copy(f.get("q", "")), "a": _soften_listicle_copy(f.get("a", ""))} for f in raw_faq]

    # Ranked lenders — resolve each slug, skip missing.
    ranked = []
    for lslug in raw_lender_slugs:
        l = load_lender(lslug)
        if l is None:
            continue
        ranked.append(l)

    # Per-lender computed props.
    from urllib.parse import quote_plus  # noqa: F401
    lender_ctx = []
    for i, lender in enumerate(ranked, start=1):
        ci = lender.get("company_info") or {}
        pricing = lender.get("pricing") or {}
        lowest = _best_lowest_price(lender)
        bbb_r = ci.get("bbb_rating") or ""
        bbb_cls = _bbb_class(bbb_r)
        gr = lender.get("google_rating") or 0
        gc = lender.get("google_reviews_count") or 0
        try:
            gr_f = float(gr); gc_i = int(gc)
            show_google = (0 < gr_f <= 5) and gc_i >= 1
        except (TypeError, ValueError):
            gr_f = 0.0; gc_i = 0; show_google = False
        pros = lender.get("pros") or []
        subcats = lender.get("subcategories") or []
        tiers = pricing.get("tiers") or []
        no_annual_fee = any(
            (t.get("price") == 0 and t.get("price_type") == "annual_fee") for t in tiers
        )
        go_href = lender.get("affiliate_url") or ""
        lender_ctx.append({
            "index": i,
            "l": lender,
            "logo_url": lender.get("logo_url") or "",
            "name": lender.get("name") or lender.get("slug"),
            "first_char": (lender.get("name") or "?")[:1].upper(),
            "google_rating": gr_f,
            "google_reviews_count": gc_i,
            "show_google": show_google,
            "bbb_rating": bbb_r or "n/a",
            "bbb_class": bbb_cls,
            "badge_label": _pricing_badge_label(lender, lowest or 0),
            "money_back": bool(pricing.get("money_back_guarantee")),
            "free_consult": bool(pricing.get("free_consultation")),
            "no_credit_check": "no-credit-check" in subcats,
            "cashback": "cashback-rewards" in subcats,
            "no_annual_fee": no_annual_fee,
            "description_short": lender.get("description_short") or "",
            "pros_top3": pros[:3],
            "go_href": go_href,
        })

    # Money-link the intro + FAQ answers (glossary linking skipped — parity will
    # still land because word count dominates over hyperlink density).
    linked_intro = linkify_description(intro, current_slug=slug, current_category=listicle.get("category") or "", money_budget=5)
    linked_faq = [
        {"q": item["q"], "a": linkify_description(item["a"], current_slug=slug, current_category=listicle.get("category") or "", money_budget=3)}
        for item in faq
    ]

    # Related content — grow the internal link graph so this money page acts as
    # a topical hub. Aim: 10+ /review/, 5+ /answers/, 3+ /financial-wellness/, 2+ sibling /best/.
    listicle_category = listicle.get("category") or ""
    ranked_slugs = {l["slug"] for l in ranked}
    related_lenders_ctx = []
    if listicle_category:
        peers = top_lenders_by_category(listicle_category, limit=30)
        for p in peers:
            if p["slug"] in ranked_slugs:
                continue
            related_lenders_ctx.append({
                "slug": p["slug"],
                "name": p.get("name") or p["slug"],
                "logo_url": p.get("logo_url") or "",
                "google_rating": p.get("google_rating") or 0,
                "google_reviews_count": p.get("google_reviews_count") or 0,
                "city": (p.get("company_info") or {}).get("city") or "",
                "state_abbr": (p.get("company_info") or {}).get("state") or "",
            })
            if len(related_lenders_ctx) >= 12:
                break

    related_answers_ctx = []
    wellness_ctx = []
    if listicle_category:
        pillar = category_to_pillar(listicle_category)
        for a in related_answers(pillar, limit=6):
            related_answers_ctx.append({
                "slug": a["slug"],
                "title": a.get("h1") or a.get("title") or a["slug"],
            })
        for w in wellness_guides_by_category(listicle_category, limit=4):
            wellness_ctx.append({
                "slug": w["slug"],
                "title": w.get("title") or w["slug"],
            })

    # Wellness fallback — every /best/ page should surface at least 3 evergreen
    # wellness guides so that topical link density stays strong even for
    # business-loan / niche categories that don't map to a wellness cluster.
    _EVERGREEN_WELLNESS = [
        ("credit-score-basics", "Credit Score Basics"),
        ("credit-utilization-guide", "Credit Utilization Guide"),
        ("credit-report-reading-guide", "How to Read a Credit Report"),
        ("dispute-credit-report-errors", "Dispute Credit Report Errors"),
        ("debt-payoff-strategies", "Debt Payoff Strategies"),
    ]
    existing_slugs = {w["slug"] for w in wellness_ctx}
    for slug_fb, title_fb in _EVERGREEN_WELLNESS:
        if len(wellness_ctx) >= 4:
            break
        if slug_fb in existing_slugs:
            continue
        wellness_ctx.append({"slug": slug_fb, "title": title_fb})

    # Sibling /best/ pages — same category (excluding self).
    sibling_best_ctx = []
    try:
        for other in all_listicles():
            if other.get("slug") == slug:
                continue
            if (other.get("category") or "") != listicle_category:
                continue
            sibling_best_ctx.append({
                "slug": other["slug"],
                "title": other.get("title") or other["slug"],
            })
            if len(sibling_best_ctx) >= 4:
                break
    except Exception:
        sibling_best_ctx = []

    canonical = f"https://www.creditdoc.co/best/{slug}/"
    breadcrumb_jsonld = _safe_jsonld_str({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://www.creditdoc.co/"},
            {"@type": "ListItem", "position": 2, "name": title, "item": canonical},
        ],
    })
    item_list_jsonld = _safe_jsonld_str({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": title,
        "description": description,
        "numberOfItems": len(ranked),
        "itemListElement": [
            {"@type": "ListItem", "position": i, "name": l.get("name"),
             "url": f"https://www.creditdoc.co/review/{l['slug']}/"}
            for i, l in enumerate(ranked, start=1)
        ],
    })
    article_jsonld = _safe_jsonld_str({
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": description,
        "author": {"@type": "Organization", "name": "CreditDoc Editorial Team",
                   "url": "https://www.creditdoc.co/about/"},
        "publisher": {"@type": "Organization", "name": "CreditDoc", "url": "https://www.creditdoc.co",
                      "logo": {"@type": "ImageObject", "url": "https://www.creditdoc.co/favicon.svg"}},
        "image": "https://www.creditdoc.co/og-default.png",
        "url": canonical,
        "about": [
            {"@type": "Thing", "name": "Consumer finance comparison"},
            {"@type": "Thing", "name": "State lending laws"},
            {"@type": "Thing", "name": "Consumer complaint data"},
        ],
        "mentions": [
            {"@type": "Organization", "name": "Consumer Financial Protection Bureau", "url": "https://www.consumerfinance.gov/"},
            {"@type": "Organization", "name": "Federal Trade Commission", "url": "https://www.ftc.gov/"},
            {"@type": "WebPage", "name": "CreditDoc State Consumer Credit Regulator Directory",
             "url": "https://www.creditdoc.co/tools/state-consumer-credit-regulator-directory/"},
        ],
    })
    faq_jsonld = ""
    faq_schema_items = [
        {"@type": "Question", "name": item["q"].strip(),
         "acceptedAnswer": {"@type": "Answer", "text": item["a"].strip()}}
        for item in faq if item.get("q", "").strip() and item.get("a", "").strip()
    ]
    if faq_schema_items:
        faq_jsonld = _safe_jsonld_str({
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": faq_schema_items,
        })

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("best.html.j2")
    html = template.render(
        listicle=listicle,
        slug=slug,
        title=title,
        seo_title=seo_title,
        seo_description=seo_description,
        description=description,
        intro=intro,
        linked_intro=linked_intro,
        tldr=tldr,
        takeaways=takeaways,
        lender_ctx=lender_ctx,
        related_lenders_ctx=related_lenders_ctx,
        related_answers_ctx=related_answers_ctx,
        wellness_ctx=wellness_ctx,
        sibling_best_ctx=sibling_best_ctx,
        linked_faq=linked_faq,
        has_faq=bool(faq),
        has_ranked=bool(ranked),
        canonical=canonical,
        breadcrumb_jsonld=breadcrumb_jsonld,
        item_list_jsonld=item_list_jsonld,
        article_jsonld=article_jsonld,
        faq_jsonld=faq_jsonld,
    )

    out_path = output_dir / "best" / slug / "index.html"
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
    description = _seo_meta(
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


def render_best_index(output_dir: Path) -> Path:
    """Render /best/ as a hub for all commercial comparison guides."""
    listicles = []
    category_labels = {
        c.get("slug"): c.get("name") or (c.get("slug") or "").replace("-", " ").title()
        for c in all_categories()
    }
    for item in all_listicles():
        raw_title = item.get("seo_title") or item.get("title") or item.get("slug")
        title = _soften_listicle_title(re.sub(r"\s*\|\s*CreditDoc.*$", "", raw_title, flags=re.I).strip())
        description = _seo_meta(_soften_listicle_copy(item.get("seo_description") or item.get("description") or "Compare CreditDoc research guides."))
        category = item.get("category") or ""
        listicles.append({
            "slug": item.get("slug"),
            "title": title,
            "description": description,
            "category_label": category_labels.get(category) or category.replace("-", " ").title() or "Guide",
        })
    listicles = [item for item in listicles if item.get("slug")]
    listicles.sort(key=lambda item: (item["category_label"].lower(), item["title"].lower()))

    url = "https://www.creditdoc.co/best/"
    collection_jsonld = _safe_jsonld_str({
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": "Best Credit and Loan Guides",
        "description": "Browse CreditDoc comparison guides for credit repair, loans, debt relief, credit cards, and business financing.",
        "url": url,
        "numberOfItems": len(listicles),
        "provider": {"@type": "Organization", "name": "CreditDoc", "url": "https://www.creditdoc.co"},
    })
    breadcrumb_jsonld = _safe_jsonld_str({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://www.creditdoc.co/"},
            {"@type": "ListItem", "position": 2, "name": "Best Guides", "item": url},
        ],
    })

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("best_index.html.j2")
    html = template.render(
        listicles=listicles,
        collection_jsonld=collection_jsonld,
        breadcrumb_jsonld=breadcrumb_jsonld,
    )
    out_path = output_dir / "best" / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path


_RESEARCH_NOISE_SUFFIXES = re.compile(
    r",?\s+(Inc\.?|LLC|N\.A\.?|NA|Corp\.?|Corporation|Company|Co\.?|Ltd\.?|LP|LLP|Bank)\.?$",
    re.I,
)
_RESEARCH_LOCATION_TAIL = re.compile(
    r"\s+(ATM|Financial Center|Corporate Center|Branch|Headquarters|HQ|Office)$",
    re.I,
)


def _research_base_name(name: str) -> str:
    """Dedup helper for the CFPB leaderboard: collapse "Bank of America ATM" +
    "Bank of America Corporate Center" into a single "Bank of America" entry.
    Same logic used in the 2026-07-23 matcher-repair tooling.
    """
    s = (name or "").strip()
    s = _RESEARCH_NOISE_SUFFIXES.sub("", s)
    s = _RESEARCH_LOCATION_TAIL.sub("", s)
    return s.strip()


def render_research_consumer_complaints(output_dir: Path) -> Path:
    """Render /research/consumer-complaints/ — the CFPB Consumer Response Data hub.

    Replaces the frozen Astro static page that shipped 2026-07-16 with "0 companies,
    0 complaints" placeholders. Reads aggregate stats + leaderboard from the same
    cfpb-trends.json used by /review/#cfpb-profile.

    Positive framing enforced per feedback_creditdoc_no_negative_lender_content.md.
    """
    entries = [e for e in all_trends_entries()
               if e.get("found_in_cfpb") and e.get("response_breakdown")]

    # Aggregates
    total_records = sum(sum((e.get("response_breakdown") or {}).values()) for e in entries)
    companies_tracked = len({_research_base_name(e.get("company_name", "")) for e in entries})
    res_rates = [e["resolution_rate"] for e in entries if e.get("resolution_rate") is not None]
    tim_rates = [e["timely_rate"] for e in entries if e.get("timely_rate") is not None]
    avg_resolution_rate = sum(res_rates) / len(res_rates) if res_rates else 0.0
    avg_timely_rate = sum(tim_rates) / len(tim_rates) if tim_rates else 0.0

    # Leaderboard — dedup by CFPB canonical name. Display label is the canonical
    # CFPB name, title-cased and stripped of common corporate-form suffixes so
    # "BANK OF AMERICA, NATIONAL ASSOCIATION" renders as "Bank of America".
    # This avoids pulling in data-quality-broken CreditDoc display names.
    def _clean_canonical_label(canon: str) -> str:
        s = canon
        # Strip DBA/AKA/FKA trails first (before hitting other suffix rules)
        s = re.sub(r",?\s+(D/?B/?A|A/?K/?A|F/?K/?A)\s+.*$", "", s, flags=re.I)
        # Strip legal-form suffixes
        s = re.sub(
            r",?\s+(NATIONAL\s+ASSOCIATION|N\.A\.|NA|INCORPORATED|INC\.?|LLC|LTD|CORP\.?|CORPORATION|COMPANY|CO\.?|LP|LLP)\.?$",
            "", s, flags=re.I,
        )
        # Trim dangling connectors
        s = re.sub(r"[\s,&]+$", "", s)
        # Title-case whole string
        s = s.title()
        # Preserve lowercase connectors
        for w in ("Of", "And", "The", "For"):
            s = re.sub(rf"\b{w}\b", w.lower(), s)
        # Cap length so we don't get 100-char rows
        if len(s) > 40:
            s = s[:37].rstrip() + "..."
        return s.strip()

    # Pick per canonical group: highest volume + link to the most-representative slug
    by_canon: dict[str, dict[str, Any]] = {}
    for e in entries:
        rb = e.get("response_breakdown") or {}
        total = sum(rb.values()) if rb else 0
        if total < 5:
            continue
        canon = (e.get("cfpb_company_name") or "").strip()
        if not canon:
            continue
        display_label = _clean_canonical_label(canon)
        # Score slug quality: prefer slugs whose display name looks well-formed
        # (proper multi-word name, not a bare data-quality artifact like just "Bank")
        display_raw = (e.get("company_name") or "").strip()
        slug_quality = len(display_raw.split()) * 10 + len(display_raw)

        prev = by_canon.get(canon)
        if prev is None:
            by_canon[canon] = {
                "slug": e["slug"],
                "company_name": display_label,
                "canon": canon,
                "total": total,
                "slug_quality": slug_quality,
                "resolution_rate": e.get("resolution_rate") or 0.0,
                "timely_rate": e.get("timely_rate") or 0.0,
            }
        else:
            # Highest-volume slug wins the total; highest-quality display name wins the link
            if total > prev["total"]:
                prev["total"] = total
            if slug_quality > prev["slug_quality"]:
                prev["slug"] = e["slug"]
                prev["slug_quality"] = slug_quality
                prev["resolution_rate"] = e.get("resolution_rate") or 0.0
                prev["timely_rate"] = e.get("timely_rate") or 0.0

    leaderboard = sorted(by_canon.values(), key=lambda r: r["total"], reverse=True)[:25]
    sample_profiles = leaderboard[:12]

    data_checked = max((e.get("checked_at") or "" for e in entries), default="")
    if not data_checked:
        from datetime import datetime as _dt
        data_checked = _dt.utcnow().strftime("%Y-%m-%d")

    site = "https://www.creditdoc.co"
    url = f"{site}/research/consumer-complaints/"

    article_jsonld = _safe_jsonld_str({
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": "Consumer Response Data Transparency",
        "description": "Aggregate CFPB Consumer Response data across every financial company CreditDoc tracks. Federal transparency records used for lender research.",
        "author": {"@type": "Organization", "name": "CreditDoc Editorial Team", "url": f"{site}/about/"},
        "publisher": {"@type": "Organization", "name": "CreditDoc", "url": site,
                      "logo": {"@type": "ImageObject", "url": f"{site}/favicon.svg"}},
        "url": url,
        "datePublished": "2026-05-12",
        "dateModified": data_checked,
    })
    breadcrumb_jsonld = _safe_jsonld_str({
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": site + "/"},
            {"@type": "ListItem", "position": 2, "name": "Research", "item": f"{site}/research/"},
            {"@type": "ListItem", "position": 3, "name": "Consumer Response Data", "item": url},
        ],
    })
    dataset_jsonld = _safe_jsonld_str({
        "@context": "https://schema.org", "@type": "Dataset",
        "name": "CreditDoc Aggregate Consumer Response Dataset",
        "description": f"Aggregate CFPB Consumer Response data across {companies_tracked:,} financial companies. Includes total records, resolution rates, on-time response rates.",
        "creator": {"@type": "Organization", "name": "CreditDoc", "url": site},
        "isBasedOn": "https://www.consumerfinance.gov/data-research/consumer-complaints/",
        "license": "https://www.consumerfinance.gov/foia/",
        "dateModified": data_checked,
        "url": url,
        "keywords": "CFPB, consumer response, financial services, complaints database, transparency",
    })

    title = f"Consumer Response Data — {companies_tracked:,} Companies Tracked | CreditDoc"
    description = f"Aggregate CFPB Consumer Response data across {companies_tracked:,} financial companies. Average resolution rate: {avg_resolution_rate:.1f}%. Average on-time response: {avg_timely_rate:.1f}%. Federal transparency records for lender research."

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=False,
        lstrip_blocks=False,
    )
    template = env.get_template("research_consumer_complaints.html.j2")
    html = template.render(
        title=title,
        description=description,
        data_checked=data_checked,
        total_records=total_records,
        companies_tracked=companies_tracked,
        avg_resolution_rate=avg_resolution_rate,
        avg_timely_rate=avg_timely_rate,
        leaderboard=leaderboard,
        sample_profiles=sample_profiles,
        article_jsonld=article_jsonld,
        breadcrumb_jsonld=breadcrumb_jsonld,
        dataset_jsonld=dataset_jsonld,
    )
    out_path = output_dir / "research" / "consumer-complaints" / "index.html"
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

    best = subparsers.add_parser("best", help="Render /best/[slug]/ page(s)")
    best.add_argument("--slug", required=True, help="Listicle slug (e.g. best-personal-loans)")
    best.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "renderer_dist"),
        help="Output directory (default: renderer_dist/)",
    )

    state_laws = subparsers.add_parser("state-laws", help="Render /state/[slug]/lending-laws/")
    state_laws.add_argument("--slug", required=True, help="State slug (e.g. california) — subroute is appended")
    state_laws.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "renderer_dist"),
        help="Output directory (default: renderer_dist/)",
    )

    guide_hub = subparsers.add_parser("credit-guide-hub", help="Render /credit-guide/[slug]/ city hub")
    guide_hub.add_argument("--slug", required=True, help="city_guide slug (e.g. dallas-tx)")
    guide_hub.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "renderer_dist"),
        help="Output directory (default: renderer_dist/)",
    )

    guide_cat = subparsers.add_parser("credit-guide-cat", help="Render /credit-guide/[slug]/[cat]/ page")
    guide_cat.add_argument("--slug", required=True,
                            help="Compound slug '<city_slug>/<category>' (e.g. dallas-tx/personal-loans)")
    guide_cat.add_argument(
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
    elif args.command == "best":
        out = render_best(args.slug, Path(args.output_dir))
        print(f"rendered: {out} ({out.stat().st_size} bytes)")
    elif args.command == "state-laws":
        # compound_slug shape for render_state_lending_laws is "<slug>/lending-laws"
        out = render_state_lending_laws(f"{args.slug}/lending-laws", Path(args.output_dir))
        print(f"rendered: {out} ({out.stat().st_size} bytes)")
    elif args.command == "credit-guide-hub":
        out = render_credit_guide_hub(args.slug, Path(args.output_dir))
        print(f"rendered: {out} ({out.stat().st_size} bytes)")
    elif args.command == "credit-guide-cat":
        out = render_credit_guide_category(args.slug, Path(args.output_dir))
        print(f"rendered: {out} ({out.stat().st_size} bytes)")
    else:
        parser.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
