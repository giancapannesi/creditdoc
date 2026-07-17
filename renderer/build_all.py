#!/usr/bin/env python3
"""
build_all.py — DB-authoritative full rebuild of the four renderer-covered families.

Iterates every published row in lenders/cluster_answers/blog_posts/wellness_guides
and writes dist/<family>/<slug>/index.html. Does not touch anything else in
dist/ (uncovered families, _worker.js/, _astro/, sitemap files, public/-copied
assets, redirects, headers). Does not call wrangler.

Safety features (per Phase-2 debugger audit):
    * flock on /tmp/creditdoc_db_writer.lock so we can't race the DB guardian
    * atomic per-file write (tmp file → os.replace) so a crash mid-run
      never leaves half-written HTML in dist/
    * skips /best/ (Astro's SVG gradient IDs randomize per build; renderer
      doesn't cover /best/ yet either — Phase 3 territory)
    * standalone: not called from `npm run build`. Runs as
      `python3 renderer/build_all.py [--dry-run]`.

Not a replacement for cutover.py:
    * No parity gate. This is authoritative "renderer wins" mode.
    * Use during controlled rebuilds. cutover.py is still the right tool
      for gated cutovers against Astro's dist output.
"""
from __future__ import annotations

import argparse
import fcntl
import os
import sqlite3
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "creditdoc.db"
DIST = REPO_ROOT / "dist"
LOCK_PATH = Path("/tmp/creditdoc_db_writer.lock")
LOCK_TIMEOUT_SEC = 600

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render import (  # noqa: E402
    render_answer,
    render_blog,
    render_brand,
    render_category,
    render_city,
    render_review,
    render_wellness,
)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from db import all_brands, cities_with_lenders, lenders_by_brand  # noqa: E402


def _acquire_lock():
    """Return an open FD holding an exclusive flock on the DB writer lock.

    Waits up to LOCK_TIMEOUT_SEC. Raises RuntimeError on timeout so we fail
    loud rather than start a build with concurrent DB writes.
    """
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(LOCK_PATH), os.O_CREAT | os.O_RDWR, 0o644)
    deadline = time.time() + LOCK_TIMEOUT_SEC
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return fd
        except BlockingIOError:
            if time.time() > deadline:
                os.close(fd)
                raise RuntimeError(f"could not acquire {LOCK_PATH} within {LOCK_TIMEOUT_SEC}s")
            time.sleep(1)


def _release_lock(fd: int) -> None:
    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


def _slugs(table: str, status_col: str, statuses: tuple[str, ...]) -> list[str]:
    """Return published slugs. status_col='' → no filter (used for wellness_guides
    where status lives inside the data JSON blob, not as a column).
    """
    with sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True) as conn:
        if not status_col:
            q = f"SELECT slug FROM {table} ORDER BY slug"
            return [r[0] for r in conn.execute(q).fetchall()]
        placeholders = ",".join("?" for _ in statuses)
        q = f"SELECT slug FROM {table} WHERE {status_col} IN ({placeholders}) ORDER BY slug"
        return [r[0] for r in conn.execute(q, statuses).fetchall()]


def _atomic_render(slug: str, render_fn, out_family: str) -> tuple[bool, str]:
    """Render into dist/<family>/<slug>/index.html.tmp then os.replace.

    Returns (ok, error_message_or_empty).
    """
    out_dir = DIST / out_family / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    final = out_dir / "index.html"
    tmp = out_dir / "index.html.tmp"
    try:
        # render_fn writes directly to <output_dir>/<family_dir>/<slug>/index.html.
        # We give it a scratch parent, then move the result to `tmp` and
        # os.replace into `final`. Per-file atomic even if we crash.
        scratch = REPO_ROOT / ".build_scratch"
        scratch.mkdir(exist_ok=True)
        rendered = render_fn(slug, scratch)  # returns Path to the written file
        rendered_bytes = rendered.read_bytes()
        with open(tmp, "wb") as f:
            f.write(rendered_bytes)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, final)
        return (True, "")
    except SystemExit as e:
        return (False, str(e))
    except Exception as e:
        return (False, f"{type(e).__name__}: {e}")


FAMILIES = [
    # (label, family_dir, render_fn, slug_query)
    ("review",    "review",              render_review,   lambda: _slugs("lenders",          "processing_status", ("ready_for_index", "approved"))),
    ("answer",    "answers",             render_answer,   lambda: _slugs("cluster_answers",  "status",            ("published", "approved"))),
    ("blog",      "blog",                render_blog,     lambda: _slugs("blog_posts",       "status",            ("published",))),
    ("wellness",  "financial-wellness",  render_wellness, lambda: _slugs("wellness_guides",  "",                  ())),  # no status column — all rows are considered published
    ("category",  "categories",          render_category, lambda: _slugs("categories",       "",                  ())),  # all rows published
    ("city",      "city",                render_city,     lambda: [c["slug"] for c in cities_with_lenders(5)]),  # aggregated from lenders table (city+state), ≥5 lenders
    ("brand",     "brand",               render_brand,    lambda: [b["slug"] for b in all_brands() if lenders_by_brand(b["slug"])]),  # brand JSON files with ≥1 indexable lender
]


def main() -> int:
    parser = argparse.ArgumentParser(description="DB-authoritative rebuild of renderer-covered families.")
    parser.add_argument("--dry-run", action="store_true", help="Count slugs per family; render nothing.")
    parser.add_argument("--only", choices=[f[0] for f in FAMILIES], help="Rebuild one family only.")
    args = parser.parse_args()

    print(f"[build_all] acquiring {LOCK_PATH} (wait up to {LOCK_TIMEOUT_SEC}s)...")
    lock_fd = _acquire_lock()
    print("[build_all] lock acquired.")

    try:
        total_ok = 0
        total_fail = 0
        wall_start = time.time()

        for label, family_dir, render_fn, slug_query in FAMILIES:
            if args.only and args.only != label:
                continue

            slugs = slug_query()
            if args.dry_run:
                print(f"[build_all] {label}: {len(slugs)} slug(s) would be rendered")
                continue

            print(f"[build_all] rendering {label}: {len(slugs)} slug(s)")
            fam_start = time.time()
            fam_ok = 0
            fam_fail = 0
            for slug in slugs:
                ok, err = _atomic_render(slug, render_fn, family_dir)
                if ok:
                    fam_ok += 1
                else:
                    fam_fail += 1
                    print(f"  FAIL {label}/{slug}: {err}")

            elapsed = time.time() - fam_start
            print(f"[build_all] {label}: {fam_ok} ok, {fam_fail} fail in {elapsed:.1f}s")
            total_ok += fam_ok
            total_fail += fam_fail

        wall = time.time() - wall_start
        print(f"[build_all] TOTAL: {total_ok} ok, {total_fail} fail in {wall:.1f}s")
        return 0 if total_fail == 0 else 2
    finally:
        _release_lock(lock_fd)
        # Clean up scratch dir
        scratch = REPO_ROOT / ".build_scratch"
        if scratch.exists():
            import shutil
            shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
