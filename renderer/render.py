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
    category_to_pillar,
    glossary_for_review,
    load_blog_post,
    load_cluster_answer,
    load_lender,
    related_answers,
    sibling_blog_posts,
    sibling_cluster_answers,
    similar_lenders,
    state_context,
    wellness_guides_by_category,
)
from linker import linkify_description  # noqa: E402
from _faqs import category_faqs, lender_specific_faqs  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


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
    else:
        parser.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
