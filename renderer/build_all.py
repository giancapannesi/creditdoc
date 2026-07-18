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
import json
import sqlite3
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "creditdoc.db"
DIST = REPO_ROOT / "dist"
LOCK_PATH = Path("/tmp/creditdoc_db_writer.lock")
LOCK_TIMEOUT_SEC = 600
KNOWN_FALSE_WEBSITE_STATUS_SLUGS = {
    "morgan-cash": "live verified; stale parked flag",
    "cnic-employees-credit-union": "live verified; stale dead flag",
    "credit-done-right": "live verified; stale dead flag",
    "jcb-international-credit-card": "live verified; stale dead flag",
    "my-credit-repair-in-columbus-oh": "live verified; stale dead flag",
    "optimal-debt-relief-debt-consolidation-settlement": "under construction, not parked/for-sale",
    "plan-b-credit-repair-texas": "live verified; stale dead flag",
    "securcommunity-federal-credit-union": "live verified; stale parked flag",
}

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render import (  # noqa: E402
    render_answer,
    render_best,
    render_blog,
    render_brand,
    render_browse,
    render_category,
    render_city,
    render_compare,
    render_credit_guide_category,
    render_credit_guide_hub,
    render_review,
    render_state,
    render_state_lending_laws,
    render_trends,
    render_wellness,
)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from db import (  # noqa: E402
    all_brands,
    all_comparisons,
    all_listicles,
    all_states_info,
    all_states_with_lending_laws,
    all_trends_entries,
    browse_pairs,
    cities_with_lenders,
    lenders_by_brand,
)


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


def _assert_no_known_false_website_status() -> None:
    """Block builds if known false-positive website warnings reappear.

    These pages were manually verified on 2026-07-18. The stale flags came from
    old website-status data and showed misleading public warnings.
    """
    failures = []
    for slug, reason in KNOWN_FALSE_WEBSITE_STATUS_SLUGS.items():
        json_path = REPO_ROOT / "src" / "content" / "lenders" / f"{slug}.json"
        db_status = None
        json_status = None

        if json_path.exists():
            with open(json_path) as f:
                json_status = json.load(f).get("website_status")

        with sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True) as conn:
            row = conn.execute("SELECT data FROM lenders WHERE slug = ?", (slug,)).fetchone()
            if row:
                db_status = json.loads(row[0]).get("website_status")

        if db_status or json_status:
            failures.append(
                f"{slug}: db={db_status!r} json={json_status!r} ({reason})"
            )

    if failures:
        print("[build_all] BLOCKED: known false website_status warning(s) reappeared:")
        for failure in failures:
            print(f"  - {failure}")
        print("[build_all] Fix: clear website_status in DB/source before publishing.")
        raise RuntimeError("known false website_status warning reappeared")


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


def _browse_wrapper(compound_slug: str, out_dir: Path):
    """Bridge single-slug build_all interface to render_browse's (cat, city) signature.

    The 'slug' passed by build_all is "cat_slug/city_slug"; the atomic-write path
    matches the URL structure.
    """
    cat, city = compound_slug.split("/", 1)
    return render_browse(cat, city, out_dir)


FAMILIES = [
    # (label, family_dir, render_fn, slug_query)
    ("review",    "review",              render_review,   lambda: _slugs("lenders",          "processing_status", ("ready_for_index", "approved", "pending_approval"))),
    ("answer",    "answers",             render_answer,   lambda: _slugs("cluster_answers",  "status",            ("published", "approved"))),
    ("blog",      "blog",                render_blog,     lambda: _slugs("blog_posts",       "status",            ("published",))),
    ("wellness",  "financial-wellness",  render_wellness, lambda: _slugs("wellness_guides",  "",                  ())),  # no status column — all rows are considered published
    ("category",  "categories",          render_category, lambda: _slugs("categories",       "",                  ())),  # all rows published
    ("city",      "city",                render_city,     lambda: [c["slug"] for c in cities_with_lenders(5)]),  # aggregated from lenders table (city+state), ≥5 lenders
    ("brand",     "brand",               render_brand,    lambda: [b["slug"] for b in all_brands() if lenders_by_brand(b["slug"])]),  # brand JSON files with ≥1 indexable lender
    ("state",     "state",               render_state,    lambda: [s["slug"] for s in all_states_info()]),  # 50 US states from data.ts STATE_ABBREVIATIONS
    ("browse",    "browse",              _browse_wrapper, lambda: [f"{cat}/{city}" for cat, city in browse_pairs(5)]),  # category × city cross-slices ≥5 lenders each
    ("trends",    "trends",              render_trends,   lambda: [e["slug"] for e in all_trends_entries()]),  # CFPB Consumer Response profiles (filtered against lenders.processing_status/no_index)
    ("compare",   "compare",             render_compare,  lambda: [c["slug"] for c in all_comparisons()]),  # head-to-head lender comparisons (JSON + 2 lender rows)
    ("state-laws","state",               render_state_lending_laws, lambda: [f"{s['slug']}/lending-laws" for s in all_states_with_lending_laws()]),  # /state/<slug>/lending-laws/
    ("best",      "best",                render_best,     lambda: [l["slug"] for l in all_listicles()]),  # 27 money-page listicles from src/content/listicles.json
    ("credit-guide-hub", "credit-guide", render_credit_guide_hub,
        lambda: _credit_guide_slugs()),  # 412 /credit-guide/<slug>/index.html hubs (Supabase city_guides)
    ("credit-guide-cat", "credit-guide", render_credit_guide_category,
        lambda: _credit_guide_category_slugs()),  # 7,828 /credit-guide/<slug>/<cat>/index.html pages
]


def _credit_guide_slugs() -> list[str]:
    """Fetch city_guide slugs from Supabase (via renderer.db_remote).

    Isolated in a helper so import-time failure to reach Supabase doesn't
    break the whole FAMILIES tuple — only the credit-guide family fails.
    """
    try:
        import db_remote
        return [g["slug"] for g in db_remote.all_city_guides() if g.get("slug")]
    except Exception as exc:
        print(f"[build_all] credit-guide-hub: cannot fetch slugs from Supabase — {exc}")
        return []


def _credit_guide_category_slugs() -> list[str]:
    """City × category compound slugs for the 7,828 /credit-guide/<city>/<cat>/ pages."""
    try:
        import db_remote
        from db import all_categories as _cats
        cities = [g["slug"] for g in db_remote.all_city_guides() if g.get("slug")]
        cats = [c["slug"] for c in _cats() if c.get("slug")]
        return [f"{city}/{cat}" for city in cities for cat in cats]
    except Exception as exc:
        print(f"[build_all] credit-guide-cat: cannot fetch pairs — {exc}")
        return []


def _purge_stale(family_dir: str, keep_slugs: set[str]) -> tuple[int, list[str]]:
    """Delete dist/<family_dir>/<slug>/ subdirs not in keep_slugs.

    Handles compound slugs like "cat/city" for /browse/ — walks two levels
    when any keep_slug contains '/'.

    Preserves top-level files like dist/<family_dir>/index.html (family
    landing page). Returns (n_deleted, sample_names).
    """
    root = DIST / family_dir
    if not root.exists():
        return (0, [])
    compound = any("/" in s for s in keep_slugs)
    keep = set(keep_slugs)
    stale: list[Path] = []
    if compound:
        # Two levels: dist/<family>/<a>/<b>/index.html
        for a in root.iterdir():
            if not a.is_dir():
                continue
            for b in a.iterdir():
                if not b.is_dir():
                    continue
                slug = f"{a.name}/{b.name}"
                if slug not in keep:
                    stale.append(b)
    else:
        for entry in root.iterdir():
            if not entry.is_dir():
                continue
            if entry.name not in keep:
                stale.append(entry)
    for p in stale:
        idx = p / "index.html"
        try:
            if idx.exists():
                idx.unlink()
            # remove now-empty dir; ignore if it has other files
            try:
                p.rmdir()
            except OSError:
                pass
        except Exception:
            pass
    return (len(stale), [str(p.relative_to(root)) for p in stale[:5]])


def main() -> int:
    parser = argparse.ArgumentParser(description="DB-authoritative rebuild of renderer-covered families.")
    parser.add_argument("--dry-run", action="store_true", help="Count slugs per family; render nothing.")
    parser.add_argument("--only", choices=[f[0] for f in FAMILIES], help="Rebuild one family only.")
    parser.add_argument("--no-purge", action="store_true", help="Skip pre-build stale-slug purge.")
    args = parser.parse_args()

    print(f"[build_all] acquiring {LOCK_PATH} (wait up to {LOCK_TIMEOUT_SEC}s)...")
    lock_fd = _acquire_lock()
    print("[build_all] lock acquired.")

    try:
        _assert_no_known_false_website_status()
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

            if not args.no_purge:
                n_purged, sample = _purge_stale(family_dir, set(slugs))
                if n_purged:
                    ex = ", ".join(sample) + (" ..." if n_purged > len(sample) else "")
                    print(f"[build_all] {label}: purged {n_purged} stale slug dir(s): {ex}")

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
