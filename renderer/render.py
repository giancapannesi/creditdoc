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

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "creditdoc.db"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


def load_lender(slug: str) -> dict[str, Any] | None:
    """Read one lender row from the DB, merging column fields into the JSON blob."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT slug, category, processing_status, is_protected, is_enriched, "
            "quality_score, logo_path, website_url, brand_slug, state, seo_tier, "
            "created_at, updated_at, data "
            "FROM lenders WHERE slug = ?",
            (slug,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return None

    # `data` blob is the JSON payload with 40+ fields. Merge column fields on top
    # so they always win (columns are the transient/system fields; blob is content).
    blob = json.loads(row["data"] or "{}")
    merged: dict[str, Any] = dict(blob)
    merged.update({
        "slug": row["slug"],
        "category": row["category"],
        "processing_status": row["processing_status"],
        "is_protected": bool(row["is_protected"]),
        "is_enriched": bool(row["is_enriched"]),
        "quality_score": row["quality_score"],
        "logo_path": row["logo_path"],
        "website_url": row["website_url"] or merged.get("website_url"),
        "brand_slug": row["brand_slug"],
        "state": row["state"] or merged.get("state"),
        "seo_tier": row["seo_tier"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    })
    return merged


def render_review(slug: str, output_dir: Path) -> Path:
    """Render one /review/<slug>/index.html from DB. Returns the output path."""
    lender = load_lender(slug)
    if lender is None:
        raise SystemExit(f"error: no lender with slug '{slug}' in {DB_PATH}")

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("review.html.j2")
    html = template.render(lender=lender)

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
