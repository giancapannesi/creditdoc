#!/usr/bin/env python3
"""
watch_and_rebuild.py — polls the DB for recently-updated rows and rebuilds
one page per changed row.

This is the mechanism that removes the necessity to rebuild the entire site.

Run as a cron every 60 seconds:
    * * * * * cd /srv/BusinessOps/creditdoc && \
              /srv/BusinessOps/.venv/bin/python3 renderer/watch_and_rebuild.py

State: stores `last_seen_ts` in `data/renderer_watermark.txt`. On each run:
    1. SELECT slug FROM lenders WHERE updated_at > last_seen_ts
    2. For each returned slug, invoke render.py to rewrite that one page
       into shadow_dist/ (or dist/ + wrangler once parity gate is open)
    3. Update watermark

Bounded batch: max 50 rebuilds per invocation (safety cap against
sync-mass-update scenarios that would blast wrangler).

Currently writes to shadow_dist/ ONLY — --deploy flag switches to
dist/ + wrangler once parity coverage is production-ready.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "creditdoc.db"
WATERMARK = REPO_ROOT / "data" / "renderer_watermark.txt"
WATERMARK_ANSWERS = REPO_ROOT / "data" / "renderer_watermark_answers.txt"
WATERMARK_BLOG = REPO_ROOT / "data" / "renderer_watermark_blog.txt"
RENDER_SCRIPT = REPO_ROOT / "renderer" / "render.py"
SHADOW_DIST = REPO_ROOT / "shadow_dist"
ASTRO_DIST = REPO_ROOT / "dist"

BATCH_CAP = 50


def read_watermark(path: Path = WATERMARK) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return "1970-01-01T00:00:00Z"


def write_watermark(ts: str, path: Path = WATERMARK) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(ts, encoding="utf-8")


def changed_slugs_since(last_seen: str, limit: int) -> list[tuple[str, str]]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT slug, updated_at FROM lenders "
            "WHERE updated_at > ? AND processing_status IN ('ready_for_index','approved') "
            "ORDER BY updated_at ASC LIMIT ?",
            (last_seen, limit + 1),
        ).fetchall()
    return [(r["slug"], r["updated_at"]) for r in rows]


def changed_answers_since(last_seen: str, limit: int) -> list[tuple[str, str]]:
    """Changed cluster_answers rows since watermark (published+approved only)."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT slug, updated_at FROM cluster_answers "
            "WHERE updated_at > ? AND status IN ('published','approved') "
            "ORDER BY updated_at ASC LIMIT ?",
            (last_seen, limit + 1),
        ).fetchall()
    return [(r["slug"], r["updated_at"]) for r in rows]


def changed_blog_since(last_seen: str, limit: int) -> list[tuple[str, str]]:
    """Changed blog_posts rows since watermark (published only)."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT slug, updated_at FROM blog_posts "
            "WHERE updated_at > ? AND status = 'published' "
            "ORDER BY updated_at ASC LIMIT ?",
            (last_seen, limit + 1),
        ).fetchall()
    return [(r["slug"], r["updated_at"]) for r in rows]


def rebuild_one(slug: str, output_dir: Path, kind: str = "review") -> tuple[bool, int, int]:
    """Invoke render.py for one slug. Returns (ok, elapsed_ms, bytes)."""
    start = time.time()
    proc = subprocess.run(
        [sys.executable, str(RENDER_SCRIPT), kind, "--slug", slug, "--output-dir", str(output_dir)],
        capture_output=True,
        text=True,
        check=False,
    )
    elapsed_ms = int((time.time() - start) * 1000)
    if proc.returncode != 0:
        print(f"  FAIL {slug}: {proc.stderr.strip()[:200]}")
        return (False, elapsed_ms, 0)
    family_dir = {"review": "review", "answer": "answers", "blog": "blog"}.get(kind, kind + "s")
    out_file = output_dir / family_dir / slug / "index.html"
    size = out_file.stat().st_size if out_file.exists() else 0
    return (True, elapsed_ms, size)


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


def deploy_changed(changed_files: list[Path]) -> bool:
    """Copy changed files to dist/ and run wrangler deploy (uploads changed only).

    Uses Global API Key path (per lies_caught #2).
    """
    if not changed_files:
        return True
    for src in changed_files:
        rel = src.relative_to(SHADOW_DIST)
        dst = ASTRO_DIST / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    dotenv = {**_load_env_file(REPO_ROOT.parent / ".env"),
              **_load_env_file(REPO_ROOT / ".env")}
    global_key = os.environ.get("CLOUDFLARE_GLOBAL_API_KEY") or dotenv.get("CLOUDFLARE_GLOBAL_API_KEY", "")
    email = os.environ.get("CLOUDFLARE_EMAIL") or dotenv.get("CLOUDFLARE_EMAIL", "contact@creditdoc.co")
    if not global_key:
        print("  wrangler deploy FAILED: no CLOUDFLARE_GLOBAL_API_KEY")
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
        print(f"  wrangler deploy FAILED: {proc.stderr.strip()[-500:]}")
        return False
    print(f"  wrangler deploy OK ({len(changed_files)} files uploaded)")
    return True


def parity_ok(slug: str, renderer_path: Path, kind: str = "review") -> tuple[bool, str]:
    """Check renderer output passes parity gate vs current dist/. Skip swap if not."""
    family_dir = {"review": "review", "answer": "answers", "blog": "blog"}.get(kind, kind + "s")
    astro_path = ASTRO_DIST / family_dir / slug / "index.html"
    if not astro_path.exists():
        # No Astro baseline — safe to write renderer output directly.
        return (True, "no-baseline")
    try:
        from cutover import parity_gate  # local import — cutover.py sits alongside
    except ImportError:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from cutover import parity_gate  # type: ignore
    astro_html = astro_path.read_text(encoding="utf-8", errors="replace")
    render_html = renderer_path.read_text(encoding="utf-8", errors="replace")
    passed, reasons = parity_gate(astro_html, render_html, kind=kind)
    return (passed, "; ".join(reasons) if not passed else "ok")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="DB → per-page renderer trigger. Poll-driven; runs as cron.",
    )
    parser.add_argument(
        "--deploy",
        action="store_true",
        help="Copy renders to dist/ and run wrangler deploy. Off by default (shadow only).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=BATCH_CAP,
        help=f"Max rebuilds per invocation (default: {BATCH_CAP})",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show what would run; don't render")
    args = parser.parse_args()

    lender_last = read_watermark(WATERMARK)
    answer_last = read_watermark(WATERMARK_ANSWERS)
    blog_last = read_watermark(WATERMARK_BLOG)
    lender_rows = changed_slugs_since(lender_last, args.limit)
    answer_rows = changed_answers_since(answer_last, args.limit)
    blog_rows = changed_blog_since(blog_last, args.limit)

    if not lender_rows and not answer_rows and not blog_rows:
        # Silent success — this runs every minute, no need to spam logs
        return

    print(f"[watch_and_rebuild] {len(lender_rows)} lender + {len(answer_rows)} answer + {len(blog_rows)} blog changed")

    if args.dry_run:
        for slug, ts in lender_rows[:20]:
            print(f"  would rebuild lender: {slug}  ({ts})")
        for slug, ts in answer_rows[:20]:
            print(f"  would rebuild answer: {slug}  ({ts})")
        for slug, ts in blog_rows[:20]:
            print(f"  would rebuild blog: {slug}  ({ts})")
        return

    output_dir = SHADOW_DIST
    changed_files: list[Path] = []
    total_ms = 0
    ok_count = 0
    fail_count = 0
    skipped_count = 0

    def _process(rows: list[tuple[str, str]], kind: str, wm_path: Path, last: str) -> str:
        nonlocal ok_count, fail_count, skipped_count, total_ms
        max_ts = last
        family_dir = {"review": "review", "answer": "answers", "blog": "blog"}.get(kind, kind + "s")
        for slug, ts in rows[: args.limit]:
            ok, elapsed_ms, size = rebuild_one(slug, output_dir, kind)
            total_ms += elapsed_ms
            if not ok:
                fail_count += 1
                continue
            if args.deploy:
                rendered = output_dir / family_dir / slug / "index.html"
                gate_ok, reason = parity_ok(slug, rendered, kind)
                if not gate_ok:
                    skipped_count += 1
                    print(f"  SKIP {kind}:{slug}: parity gate — {reason}")
                    if ts > max_ts:
                        max_ts = ts
                    continue
            ok_count += 1
            changed_files.append(output_dir / family_dir / slug / "index.html")
            if ts > max_ts:
                max_ts = ts
        return max_ts

    new_lender_last = _process(lender_rows, "review", WATERMARK, lender_last) if lender_rows else lender_last
    new_answer_last = _process(answer_rows, "answer", WATERMARK_ANSWERS, answer_last) if answer_rows else answer_last
    new_blog_last = _process(blog_rows, "blog", WATERMARK_BLOG, blog_last) if blog_rows else blog_last

    print(f"[watch_and_rebuild] rendered {ok_count} ok, {fail_count} fail, {skipped_count} skipped(gate) in {total_ms} ms")

    if args.deploy and changed_files:
        deploy_changed(changed_files)

    # Advance watermarks only if at least one page was successfully rendered for each type.
    if new_lender_last != lender_last:
        write_watermark(new_lender_last, WATERMARK)
        print(f"[watch_and_rebuild] lender watermark → {new_lender_last}")
    if new_answer_last != answer_last:
        write_watermark(new_answer_last, WATERMARK_ANSWERS)
        print(f"[watch_and_rebuild] answer watermark → {new_answer_last}")
    if new_blog_last != blog_last:
        write_watermark(new_blog_last, WATERMARK_BLOG)
        print(f"[watch_and_rebuild] blog watermark → {new_blog_last}")


if __name__ == "__main__":
    main()
