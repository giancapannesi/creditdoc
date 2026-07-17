#!/usr/bin/env python3
"""
cutover.py — SAFELY replace Astro's production output with renderer output
for one lender OR a batch, with parity checks gating the swap.

This is the mechanism that makes "no full Astro rebuild" real for live URLs.

Usage:
    # Preview mode (default): renders + shows parity delta, does NOT write dist/
    python3 renderer/cutover.py --slug lexington-law

    # Actual cutover: writes dist/review/<slug>/index.html + deploys via wrangler
    python3 renderer/cutover.py --slug lexington-law --commit

    # Batch: cutover many slugs, only those passing parity gate
    python3 renderer/cutover.py --batch-file slugs.txt --commit

Gate conditions (all must pass or the swap is skipped for that slug):
    - Renderer output must have ALL required schema types
      (FinancialService/LocalBusiness, BreadcrumbList, FAQPage)
    - Renderer output must have ≥ 90% of Astro's internal link count
    - Renderer output must have title, meta description, canonical
    - Renderer bytes must be ≥ 50% of Astro bytes (structural completeness)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
ASTRO_DIST = REPO_ROOT / "dist"
RENDER_SCRIPT = REPO_ROOT / "renderer" / "render.py"
SHADOW_DIST = REPO_ROOT / "shadow_dist"

REQUIRED_SCHEMA = {"FinancialService", "BreadcrumbList", "FAQPage"}
MIN_BYTE_RATIO = 0.50
MIN_INTERNAL_LINK_RATIO = 0.90


def _extract_schema_types(html: str) -> set[str]:
    types: set[str] = set()
    for m in re.finditer(r'<script\s+type="application/ld\+json">\s*(.*?)\s*</script>', html, flags=re.DOTALL):
        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        stack: list[Any] = [data]
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


def _internal_link_count(html: str) -> int:
    return len(set(re.findall(r'href="/[^"#?]*"', html)))


def _has_head_essentials(html: str) -> bool:
    return all([
        re.search(r"<title[^>]*>[^<]", html),
        re.search(r'<meta\s+name="description"\s+content="[^"]', html),
        re.search(r'<link\s+rel="canonical"', html),
    ])


def parity_gate(astro_html: str, renderer_html: str) -> tuple[bool, list[str]]:
    """Return (passed, reasons). If passed=False, reasons lists failures."""
    reasons: list[str] = []

    if not _has_head_essentials(renderer_html):
        reasons.append("renderer output is missing title/meta/canonical")

    astro_types = _extract_schema_types(astro_html)
    render_types = _extract_schema_types(renderer_html)
    missing_required = REQUIRED_SCHEMA - render_types
    if missing_required:
        reasons.append(f"renderer missing required schema types: {sorted(missing_required)}")

    astro_links = _internal_link_count(astro_html)
    render_links = _internal_link_count(renderer_html)
    if astro_links > 0 and (render_links / astro_links) < MIN_INTERNAL_LINK_RATIO:
        reasons.append(f"internal-link parity {render_links}/{astro_links} ({100*render_links/astro_links:.1f}%) below {MIN_INTERNAL_LINK_RATIO*100:.0f}%")

    astro_bytes = len(astro_html)
    render_bytes = len(renderer_html)
    if astro_bytes > 0 and (render_bytes / astro_bytes) < MIN_BYTE_RATIO:
        reasons.append(f"byte ratio {render_bytes}/{astro_bytes} ({100*render_bytes/astro_bytes:.1f}%) below {MIN_BYTE_RATIO*100:.0f}%")

    return (not reasons, reasons)


def render(slug: str) -> Path:
    """Invoke renderer/render.py for one slug, output to shadow_dist/."""
    proc = subprocess.run(
        [sys.executable, str(RENDER_SCRIPT), "review", "--slug", slug, "--output-dir", str(SHADOW_DIST)],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        print(f"  render FAIL for {slug}: {proc.stderr.strip()[:300]}", file=sys.stderr)
        raise RuntimeError("render failure")
    return SHADOW_DIST / "review" / slug / "index.html"


def wrangler_deploy() -> bool:
    """Push dist/ to Cloudflare. Wrangler uploads only changed files."""
    env = {**os.environ,
           "CLOUDFLARE_API_TOKEN": "",
           "CLOUDFLARE_EMAIL": os.environ.get("CLOUDFLARE_EMAIL", ""),
           "CLOUDFLARE_API_KEY": os.environ.get("CLOUDFLARE_GLOBAL_API_KEY", "")}
    proc = subprocess.run(
        ["npx", "wrangler", "deploy"],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        print(f"wrangler deploy FAILED: {proc.stderr.strip()[-500:]}")
        return False
    for line in proc.stdout.splitlines()[-5:]:
        print(f"  {line}")
    return True


def cutover_one(slug: str, commit: bool) -> tuple[str, bool]:
    """Render + gate + optionally swap. Returns (status, deployed_bool)."""
    astro_path = ASTRO_DIST / "review" / slug / "index.html"
    if not astro_path.exists():
        return (f"skip: no astro page at {astro_path}", False)

    try:
        renderer_path = render(slug)
    except RuntimeError:
        return ("skip: render failed", False)

    astro_html = astro_path.read_text(encoding="utf-8", errors="replace")
    renderer_html = renderer_path.read_text(encoding="utf-8", errors="replace")
    passed, reasons = parity_gate(astro_html, renderer_html)

    astro_bytes = len(astro_html)
    render_bytes = len(renderer_html)
    ratio = f"{100*render_bytes/astro_bytes:.1f}%"

    if not passed:
        return (f"BLOCK ({ratio} bytes) — {'; '.join(reasons)}", False)

    if not commit:
        return (f"OK ({ratio} bytes) — would swap, no --commit", False)

    # Actual cutover: overwrite Astro's dist file with renderer output.
    shutil.copy2(renderer_path, astro_path)
    return (f"OK ({ratio} bytes) — cut over", True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Safely cut over /review/ pages from Astro to renderer output.",
    )
    parser.add_argument("--slug", help="Single lender slug")
    parser.add_argument("--batch-file", help="File with one slug per line")
    parser.add_argument("--commit", action="store_true", help="Actually swap + deploy. Without this, preview only.")
    args = parser.parse_args()

    if not args.slug and not args.batch_file:
        parser.error("--slug or --batch-file is required")

    slugs: list[str] = []
    if args.slug:
        slugs.append(args.slug)
    if args.batch_file:
        slugs.extend(l.strip() for l in Path(args.batch_file).read_text().splitlines() if l.strip() and not l.startswith("#"))

    deployed_any = False
    for slug in slugs:
        status, deployed = cutover_one(slug, args.commit)
        marker = "✓" if deployed else "·" if status.startswith("OK") else "✗"
        print(f"  {marker}  {slug:60s}  {status}")
        deployed_any = deployed_any or deployed

    if deployed_any and args.commit:
        print()
        print("running wrangler deploy (only changed files upload) ...")
        if wrangler_deploy():
            print("  deploy succeeded")


if __name__ == "__main__":
    main()
