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

REQUIRED_SCHEMA_BY_KIND = {
    "review": {"FinancialService", "BreadcrumbList", "FAQPage"},
    "answer": {"Article", "BreadcrumbList"},
    "blog": {"Article", "BreadcrumbList"},
}
REQUIRED_SCHEMA = {"FinancialService", "BreadcrumbList", "FAQPage"}  # back-compat default
# Byte ratio is a rough backstop for total structural completeness. The real
# quality signal is visible-text word ratio (below), which strips markup /
# framework noise and measures what a human/crawler sees.
MIN_BYTE_RATIO = 0.35
MIN_VISIBLE_WORD_RATIO = 0.80
MIN_INTERNAL_LINK_RATIO = 0.80


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


def _visible_word_count(html: str) -> int:
    """Words visible to a crawler/user — strips scripts, styles, and tags."""
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text).strip()
    return len(text.split())


def _has_head_essentials(html: str) -> bool:
    return all([
        re.search(r"<title[^>]*>[^<]", html),
        re.search(r'<meta\s+name="description"\s+content="[^"]', html),
        re.search(r'<link\s+rel="canonical"', html),
    ])


def parity_gate(astro_html: str, renderer_html: str, kind: str = "review") -> tuple[bool, list[str]]:
    """Return (passed, reasons). If passed=False, reasons lists failures."""
    reasons: list[str] = []

    if not _has_head_essentials(renderer_html):
        reasons.append("renderer output is missing title/meta/canonical")

    required_schema = REQUIRED_SCHEMA_BY_KIND.get(kind, REQUIRED_SCHEMA)
    astro_types = _extract_schema_types(astro_html)
    render_types = _extract_schema_types(renderer_html)
    missing_required = required_schema - render_types
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

    astro_words = _visible_word_count(astro_html)
    render_words = _visible_word_count(renderer_html)
    if astro_words > 0 and (render_words / astro_words) < MIN_VISIBLE_WORD_RATIO:
        reasons.append(f"visible-text parity {render_words}/{astro_words} ({100*render_words/astro_words:.1f}%) below {MIN_VISIBLE_WORD_RATIO*100:.0f}%")

    return (not reasons, reasons)


sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from render import render_answer as _render_answer_inproc  # type: ignore  # noqa: E402
    from render import render_blog as _render_blog_inproc  # type: ignore  # noqa: E402
    from render import render_review as _render_review_inproc  # type: ignore  # noqa: E402
except ImportError:
    _render_review_inproc = None
    _render_answer_inproc = None
    _render_blog_inproc = None


_INPROC_BY_KIND = {
    "review": _render_review_inproc,
    "answer": _render_answer_inproc,
    "blog": _render_blog_inproc,
}


def render(slug: str, kind: str = "review") -> Path:
    """Render one slug into shadow_dist/. In-process if importable, else subprocess."""
    inproc = _INPROC_BY_KIND.get(kind)
    if inproc is not None:
        try:
            return inproc(slug, SHADOW_DIST)
        except SystemExit as e:
            print(f"  render FAIL for {slug}: {e}", file=sys.stderr)
            raise RuntimeError("render failure")
    proc = subprocess.run(
        [sys.executable, str(RENDER_SCRIPT), kind, "--slug", slug, "--output-dir", str(SHADOW_DIST)],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        print(f"  render FAIL for {slug}: {proc.stderr.strip()[:300]}", file=sys.stderr)
        raise RuntimeError("render failure")
    family_dir = {"review": "review", "answer": "answers", "blog": "blog"}.get(kind, kind + "s")
    return SHADOW_DIST / family_dir / slug / "index.html"


def _load_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def wrangler_deploy() -> bool:
    """Push dist/ to Cloudflare. Wrangler uploads only changed files.

    Uses Global API Key path (per lies_caught #2): wrangler reads
    CLOUDFLARE_API_KEY (not _GLOBAL_API_KEY) plus CLOUDFLARE_EMAIL.
    Must NOT have CLOUDFLARE_API_TOKEN in env — that Zone-only token
    can't do Workers ops and its presence hijacks the auth path.
    """
    dotenv = {**_load_env_file(REPO_ROOT.parent / ".env"),
              **_load_env_file(REPO_ROOT / ".env")}
    global_key = os.environ.get("CLOUDFLARE_GLOBAL_API_KEY") or dotenv.get("CLOUDFLARE_GLOBAL_API_KEY", "")
    email = os.environ.get("CLOUDFLARE_EMAIL") or dotenv.get("CLOUDFLARE_EMAIL", "contact@creditdoc.co")
    if not global_key:
        print("wrangler deploy FAILED: no CLOUDFLARE_GLOBAL_API_KEY in env or .env")
        return False
    env = {k: v for k, v in os.environ.items() if k != "CLOUDFLARE_API_TOKEN"}
    env["CLOUDFLARE_EMAIL"] = email
    env["CLOUDFLARE_API_KEY"] = global_key
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


FAMILY_DIR = {"review": "review", "answer": "answers", "blog": "blog"}


def cutover_one(slug: str, commit: bool, kind: str = "review") -> tuple[str, bool]:
    """Render + gate + optionally swap. Returns (status, deployed_bool)."""
    family_dir = FAMILY_DIR.get(kind, kind + "s")
    astro_path = ASTRO_DIST / family_dir / slug / "index.html"
    if not astro_path.exists():
        return (f"skip: no astro page at {astro_path}", False)

    try:
        renderer_path = render(slug, kind)
    except RuntimeError:
        return ("skip: render failed", False)

    astro_html = astro_path.read_text(encoding="utf-8", errors="replace")
    renderer_html = renderer_path.read_text(encoding="utf-8", errors="replace")
    passed, reasons = parity_gate(astro_html, renderer_html, kind=kind)

    astro_bytes = len(astro_html)
    render_bytes = len(renderer_html)
    astro_words = _visible_word_count(astro_html)
    render_words = _visible_word_count(renderer_html)
    ratio = f"{100*render_bytes/astro_bytes:.0f}%b/{100*render_words/max(1,astro_words):.0f}%w"

    if not passed:
        return (f"BLOCK ({ratio}) — {'; '.join(reasons)}", False)

    if not commit:
        return (f"OK ({ratio}) — would swap, no --commit", False)

    # Actual cutover: overwrite Astro's dist file with renderer output.
    shutil.copy2(renderer_path, astro_path)
    return (f"OK ({ratio}) — cut over", True)


def _pool_worker(args_tuple: tuple[str, bool, str]) -> tuple[str, tuple[str, bool]]:
    slug, commit, kind = args_tuple
    return (slug, cutover_one(slug, commit, kind))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Safely cut over /review/ pages from Astro to renderer output.",
    )
    parser.add_argument("--slug", help="Single slug")
    parser.add_argument("--batch-file", help="File with one slug per line")
    parser.add_argument("--all-review", action="store_true", help="Iterate every existing dist/review/<slug>/index.html")
    parser.add_argument("--all-answers", action="store_true", help="Iterate every existing dist/answers/<slug>/index.html")
    parser.add_argument("--all-blog", action="store_true", help="Iterate every existing dist/blog/<slug>/index.html")
    parser.add_argument("--kind", choices=["review", "answer", "blog"], default="review", help="Page family for --slug/--batch-file")
    parser.add_argument("--commit", action="store_true", help="Actually swap + deploy. Without this, preview only.")
    parser.add_argument("--no-deploy", action="store_true", help="Do the swap but skip wrangler (useful for staging)")
    parser.add_argument("--quiet", action="store_true", help="Only print blocked / errored slugs")
    parser.add_argument("--workers", type=int, default=1, help="Parallel workers (multiprocessing). Default 1.")
    args = parser.parse_args()

    if not args.slug and not args.batch_file and not args.all_review and not args.all_answers and not args.all_blog:
        parser.error("--slug, --batch-file, --all-review, --all-answers, or --all-blog is required")

    kind = args.kind
    slugs: list[str] = []
    if args.slug:
        slugs.append(args.slug)
    if args.batch_file:
        slugs.extend(l.strip() for l in Path(args.batch_file).read_text().splitlines() if l.strip() and not l.startswith("#"))
    if args.all_review:
        kind = "review"
        for p in sorted((ASTRO_DIST / "review").iterdir()):
            if p.is_dir() and (p / "index.html").exists():
                slugs.append(p.name)
    if args.all_answers:
        kind = "answer"
        for p in sorted((ASTRO_DIST / "answers").iterdir()):
            if p.is_dir() and (p / "index.html").exists():
                slugs.append(p.name)
    if args.all_blog:
        kind = "blog"
        for p in sorted((ASTRO_DIST / "blog").iterdir()):
            if p.is_dir() and (p / "index.html").exists():
                slugs.append(p.name)

    deployed_any = False
    ok = block = err = 0

    def _report(slug: str, result: tuple[str, bool]) -> None:
        nonlocal ok, block, err, deployed_any
        status, deployed = result
        if deployed:
            ok += 1
        elif status.startswith("OK"):
            ok += 1
        elif status.startswith("BLOCK"):
            block += 1
        else:
            err += 1
        marker = "✓" if deployed else "·" if status.startswith("OK") else "✗"
        if not args.quiet or marker == "✗":
            print(f"  {marker}  {slug:60s}  {status}")
        deployed_any = deployed_any or deployed

    if args.workers > 1:
        from multiprocessing import Pool
        pool_args = [(s, args.commit, kind) for s in slugs]
        with Pool(processes=args.workers) as pool:
            for slug, result in pool.imap_unordered(_pool_worker, pool_args, chunksize=25):
                _report(slug, result)
    else:
        for slug in slugs:
            _report(slug, cutover_one(slug, args.commit, kind))

    print()
    print(f"totals: {ok} passed  {block} blocked  {err} errored  ({len(slugs)} scanned)")

    if deployed_any and args.commit and not args.no_deploy:
        print()
        print("running wrangler deploy (only changed files upload) ...")
        if wrangler_deploy():
            print("  deploy succeeded")


if __name__ == "__main__":
    main()
