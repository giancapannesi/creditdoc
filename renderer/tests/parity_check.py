#!/usr/bin/env python3
"""
Parity harness — compare Astro output to renderer output.

Goal: give a quantitative gap number so we know when the renderer is
ready to replace Astro for a given page family. Empty diff = safe to
cut over that family.

Usage:
    python3 renderer/tests/parity_check.py --astro dist/ --renderer renderer_dist/
    python3 renderer/tests/parity_check.py --slug lexington-law
    python3 renderer/tests/parity_check.py --family review --sample 20

Metrics emitted:
    - Byte size delta
    - Line count delta
    - Structural element counts (title, meta, h1, h2, links, scripts, ld+json)
    - Set of URLs present in Astro but missing from renderer (link parity)
    - Set of JSON-LD @type values present in Astro but missing from renderer
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ASTRO_DIST = REPO_ROOT / "dist"
RENDERER_DIST = REPO_ROOT / "renderer_dist"

# Structural checks: count instances of each pattern.
STRUCTURAL_PATTERNS: dict[str, str] = {
    "title": r"<title[^>]*>",
    "meta_description": r'<meta\s+name="description"',
    "canonical": r'<link\s+rel="canonical"',
    "og_tags": r'<meta\s+property="og:',
    "h1": r"<h1[^>]*>",
    "h2": r"<h2[^>]*>",
    "internal_link": r'href="/[^"]*"',
    "external_link": r'href="https?://(?!www\.creditdoc\.co)[^"]*"',
    "script_json_ld": r'<script\s+type="application/ld\+json">',
    "img": r"<img\s",
}


def extract_urls(html: str) -> set[str]:
    return set(re.findall(r'href="(/[^"#]*)"', html))


def extract_jsonld_types(html: str) -> set[str]:
    types: set[str] = set()
    for match in re.finditer(
        r'<script\s+type="application/ld\+json">\s*(.*?)\s*</script>',
        html,
        flags=re.DOTALL,
    ):
        try:
            payload = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        stack: list[Any] = [payload]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                t = node.get("@type")
                if isinstance(t, str):
                    types.add(t)
                elif isinstance(t, list):
                    types.update(x for x in t if isinstance(x, str))
                stack.extend(node.values())
            elif isinstance(node, list):
                stack.extend(node)
    return types


def structural_counts(html: str) -> dict[str, int]:
    return {name: len(re.findall(pat, html)) for name, pat in STRUCTURAL_PATTERNS.items()}


def compare_files(astro_path: Path, renderer_path: Path) -> dict[str, Any]:
    astro_html = astro_path.read_text(encoding="utf-8", errors="replace")
    renderer_html = renderer_path.read_text(encoding="utf-8", errors="replace")

    astro_counts = structural_counts(astro_html)
    renderer_counts = structural_counts(renderer_html)

    astro_urls = extract_urls(astro_html)
    renderer_urls = extract_urls(renderer_html)

    astro_ld_types = extract_jsonld_types(astro_html)
    renderer_ld_types = extract_jsonld_types(renderer_html)

    return {
        "astro_bytes": len(astro_html),
        "renderer_bytes": len(renderer_html),
        "byte_delta": len(renderer_html) - len(astro_html),
        "astro_lines": astro_html.count("\n"),
        "renderer_lines": renderer_html.count("\n"),
        "structural": {
            name: {
                "astro": astro_counts[name],
                "renderer": renderer_counts[name],
                "delta": renderer_counts[name] - astro_counts[name],
            }
            for name in STRUCTURAL_PATTERNS
        },
        "urls_missing_from_renderer": sorted(astro_urls - renderer_urls)[:20],
        "urls_extra_in_renderer": sorted(renderer_urls - astro_urls)[:20],
        "urls_astro_total": len(astro_urls),
        "urls_renderer_total": len(renderer_urls),
        "jsonld_types_missing": sorted(astro_ld_types - renderer_ld_types),
        "jsonld_types_extra": sorted(renderer_ld_types - astro_ld_types),
    }


def format_report(slug: str, result: dict[str, Any]) -> str:
    out: list[str] = []
    out.append(f"=== PARITY: /review/{slug}/ ===")
    out.append(
        f"bytes:  astro={result['astro_bytes']:>7,}  "
        f"renderer={result['renderer_bytes']:>7,}  "
        f"gap={-result['byte_delta']:>+7,} to close"
    )
    out.append(
        f"lines:  astro={result['astro_lines']:>7,}  "
        f"renderer={result['renderer_lines']:>7,}"
    )
    out.append("structural elements (astro | renderer | delta):")
    for name, s in result["structural"].items():
        out.append(f"  {name:20s} {s['astro']:>4} | {s['renderer']:>4} | {s['delta']:+d}")
    out.append(f"internal URLs: astro={result['urls_astro_total']}  renderer={result['urls_renderer_total']}")
    if result["urls_missing_from_renderer"]:
        out.append(f"  first {len(result['urls_missing_from_renderer'])} missing from renderer:")
        for u in result["urls_missing_from_renderer"]:
            out.append(f"    - {u}")
    if result["jsonld_types_missing"]:
        out.append(f"JSON-LD @types missing: {result['jsonld_types_missing']}")
    if result["jsonld_types_extra"]:
        out.append(f"JSON-LD @types extra (unexpected): {result['jsonld_types_extra']}")
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser(description="Renderer↔Astro parity check.")
    parser.add_argument("--slug", help="Single lender slug to check")
    parser.add_argument("--family", default="review", help="Page family (default: review)")
    parser.add_argument("--astro-dist", default=str(ASTRO_DIST))
    parser.add_argument("--renderer-dist", default=str(RENDERER_DIST))
    args = parser.parse_args()

    astro_root = Path(args.astro_dist)
    renderer_root = Path(args.renderer_dist)

    if args.slug:
        astro_path = astro_root / args.family / args.slug / "index.html"
        renderer_path = renderer_root / args.family / args.slug / "index.html"
        if not astro_path.exists():
            print(f"error: {astro_path} missing", file=sys.stderr)
            sys.exit(2)
        if not renderer_path.exists():
            print(f"error: {renderer_path} missing — run `render.py {args.family} --slug {args.slug}` first", file=sys.stderr)
            sys.exit(2)
        result = compare_files(astro_path, renderer_path)
        print(format_report(args.slug, result))
    elif args.family:
        # Family-wide: for every renderer-emitted page in that family, compare vs Astro.
        family_root = renderer_root / args.family
        if not family_root.exists():
            print(f"error: {family_root} missing — render some pages first", file=sys.stderr)
            sys.exit(2)
        slugs = sorted(p.name for p in family_root.iterdir() if p.is_dir() and (p / "index.html").exists())
        if not slugs:
            print(f"error: no rendered pages in {family_root}", file=sys.stderr)
            sys.exit(2)

        totals = {"pages": 0, "astro_bytes": 0, "renderer_bytes": 0, "byte_gap": 0}
        largest_gaps: list[tuple[int, str]] = []
        for slug in slugs:
            astro_path = astro_root / args.family / slug / "index.html"
            renderer_path = family_root / slug / "index.html"
            if not astro_path.exists():
                continue
            r = compare_files(astro_path, renderer_path)
            totals["pages"] += 1
            totals["astro_bytes"] += r["astro_bytes"]
            totals["renderer_bytes"] += r["renderer_bytes"]
            totals["byte_gap"] += (r["astro_bytes"] - r["renderer_bytes"])
            largest_gaps.append((r["astro_bytes"] - r["renderer_bytes"], slug))

        print(f"=== FAMILY-WIDE PARITY: /{args.family}/ ({totals['pages']} pages) ===")
        print(f"total astro bytes:    {totals['astro_bytes']:>12,}")
        print(f"total renderer bytes: {totals['renderer_bytes']:>12,}")
        print(f"total gap to close:   {totals['byte_gap']:>12,}")
        if totals["astro_bytes"]:
            pct = 100 * totals["renderer_bytes"] / totals["astro_bytes"]
            print(f"parity coverage:      {pct:>11.1f}%")
        largest_gaps.sort(reverse=True)
        print("\nlargest per-page gaps:")
        for gap, slug in largest_gaps[:10]:
            print(f"  {gap:>+8,} bytes  /{args.family}/{slug}/")


if __name__ == "__main__":
    main()
