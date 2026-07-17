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
    load_lender,
    related_answers,
    similar_lenders,
    wellness_guides_by_category,
)

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
    )

    out_path = output_dir / "review" / slug / "index.html"
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

    args = parser.parse_args()

    if args.command == "review":
        out = render_review(args.slug, Path(args.output_dir))
        print(f"rendered: {out} ({out.stat().st_size} bytes)")
    else:
        parser.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
