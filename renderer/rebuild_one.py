#!/usr/bin/env python3
"""
rebuild_one.py — per-page rebuild pipeline (the thing that kills full rebuilds).

This is the mechanism that removes the necessity to rebuild the entire site
for every change. Called with a slug and family, it:

  1. Renders that one page from the DB (using renderer/render.py)
  2. Writes to `shadow_dist/<family>/<slug>/index.html`
  3. Reports timing and byte count

Once parity is production-ready, `--deploy` will:
  4. Copy the file into `dist/<family>/<slug>/index.html`
  5. Run `wrangler deploy` (which only uploads changed files)
  6. Verify the live URL responds

Called by:
  - Manual: `python3 renderer/rebuild_one.py review --slug X`
  - DB trigger webhook: on row UPDATE, POST to /internal/rebuild
  - Cron sweep: every 5 min, check `updated_at > last_seen`, rebuild changed

Design constraint: end-to-end (DB change → live HTML) must be < 30 seconds.
Astro's alternative is a 45-minute full rebuild — a 90x improvement floor.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SHADOW_DIST = REPO_ROOT / "shadow_dist"
ASTRO_DIST = REPO_ROOT / "dist"
RENDER_SCRIPT = REPO_ROOT / "renderer" / "render.py"


def render(family: str, slug: str, output_dir: Path) -> Path:
    """Invoke render.py for one page. Returns the emitted file path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [sys.executable, str(RENDER_SCRIPT), family, "--slug", slug, "--output-dir", str(output_dir)],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        print(f"render failed for {family}/{slug}:", file=sys.stderr)
        print(proc.stderr, file=sys.stderr)
        raise SystemExit(proc.returncode)
    return output_dir / family / slug / "index.html"


def deploy_one(source: Path, family: str, slug: str) -> None:
    """Copy to Astro's dist/ and run wrangler deploy (uploads only changed files)."""
    target = ASTRO_DIST / family / slug / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    print(f"copied {source} → {target}")

    env_extra = {
        "CLOUDFLARE_API_TOKEN": "",
        "CLOUDFLARE_EMAIL": os.environ.get("CLOUDFLARE_EMAIL", ""),
        "CLOUDFLARE_API_KEY": os.environ.get("CLOUDFLARE_GLOBAL_API_KEY", ""),
    }
    env = {**os.environ, **env_extra}
    print("wrangler deploy (uploads only changed files) ...")
    proc = subprocess.run(
        ["npx", "wrangler", "deploy"],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        print("wrangler deploy failed:", file=sys.stderr)
        print(proc.stderr[-2000:], file=sys.stderr)
        raise SystemExit(proc.returncode)
    for line in proc.stdout.splitlines()[-8:]:
        print(f"  {line}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rebuild one page from DB — replaces full-site Astro rebuild for that page.",
    )
    parser.add_argument("family", choices=["review"], help="Page family (currently: review only)")
    parser.add_argument("--slug", required=True, help="Page slug to rebuild")
    parser.add_argument(
        "--deploy",
        action="store_true",
        help="Actually deploy to production. Without this, writes to shadow_dist/ only (safe).",
    )
    args = parser.parse_args()

    start = time.time()
    output_dir = ASTRO_DIST.parent / "dist" if args.deploy else SHADOW_DIST
    print(f"rebuilding /{args.family}/{args.slug}/  (mode: {'DEPLOY' if args.deploy else 'shadow'})")

    render_start = time.time()
    output_path = render(args.family, args.slug, output_dir if not args.deploy else SHADOW_DIST)
    render_ms = int((time.time() - render_start) * 1000)
    size = output_path.stat().st_size
    print(f"  render: {render_ms} ms, {size:,} bytes → {output_path}")

    if args.deploy:
        deploy_start = time.time()
        deploy_one(output_path, args.family, args.slug)
        deploy_ms = int((time.time() - deploy_start) * 1000)
        print(f"  deploy: {deploy_ms} ms")

    total_ms = int((time.time() - start) * 1000)
    print(f"total elapsed: {total_ms} ms")

    if not args.deploy:
        print()
        print("(shadow mode — did NOT touch dist/ or wrangler)")
        print("Once parity is production-ready, rerun with --deploy.")


if __name__ == "__main__":
    main()
