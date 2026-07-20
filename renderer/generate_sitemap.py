#!/usr/bin/env python3
"""
generate_sitemap.py — regenerate dist/sitemap-*.xml and dist/sitemap-index.xml.

Replaces the @astrojs/sitemap plugin. Reads URLs from the same sources the
Astro build did (verified against astro.config.mjs.DISABLED_2026-07-17):
    1. dist/ walk: every existing <family>/<slug>/index.html
    2. Categories from DB (categories table)
    3. Brands: DB DISTINCT lenders.brand_slug, cross-checked against
       src/content/brands/<slug>.json
    4. State roots from src/content/states.json
    5. City guides from Supabase (city_guides table where status=ready_for_index)

Exclusions:
    * Three CSV files of URLs pulled from GSC / crawler audits
    * /search/, /specials/, /linkedin-oauth-callback/, anything ending /print/
    * Rendered HTML pages with meta robots noindex

Per-family priority + changefreq: matches Astro's serialize() logic.
Chunking: 5,000 URLs per sitemap file. Emits sitemap-N.xml + sitemap-index.xml.

Standalone runner:
    python3 renderer/generate_sitemap.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DIST = REPO_ROOT / "dist"
DB_PATH = REPO_ROOT / "data" / "creditdoc.db"
SUPABASE_ENV_FILE = REPO_ROOT.parent / "tools" / ".supabase-creditdoc.env"
SITE = "https://www.creditdoc.co"
ENTRY_LIMIT = 5000

# The 3 CSV files Astro reads for exclusions (astro.config.mjs.DISABLED:34-36)
EXCLUSION_CSV_FILES = [
    REPO_ROOT / "SEO/Table 404 Missing Pages.csv",
    REPO_ROOT / "SEO/Table - Duplicates.csv",
    Path("/srv/BusinessOps/CreditDoc_SEO/gsc_reports/creditdoc.co-Coverage-Drilldown-2026-07-14 - Table.csv"),
]

# Static-page exclusions from Astro's filter() (config lines 456-462)
STATIC_EXCLUSIONS = {"/search/", "/specials/", "/linkedin-oauth-callback/"}

# Family-prefix exclusions (2026-07-19): /trends/ family retired — CFPB data
# now lives on /review/{slug}#cfpb-profile. All /trends/* URLs 301 redirect
# via public/_redirects, so they must NOT appear in the sitemap.
EXCLUDED_PREFIXES = ("/trends/",)


def _normalize_url(raw: str) -> str | None:
    """Match Astro's normalizeSitemapUrl(): canonical https://www.creditdoc.co/<path>/ .

    Percent-encodes non-ASCII path segments to match Astro's output. Astro uses
    the URL constructor which auto-percent-encodes, so `国宝银行` → `%E5%9B%BD...`.
    """
    from urllib.parse import quote, urlparse
    try:
        u = urlparse(raw if raw.startswith("http") else SITE + raw)
        path = u.path.rstrip("/")
        if not path:
            path = "/"
        else:
            path = path + "/"
        # Percent-encode segments; keep / literal
        path = "/".join(quote(seg, safe="") for seg in path.split("/"))
        return f"https://www.creditdoc.co{path}"
    except Exception:
        return None


def load_exclusions() -> set[str]:
    """Grep URLs from 3 CSV files, normalize them."""
    excl: set[str] = set()
    for csv_path in EXCLUSION_CSV_FILES:
        if not csv_path.exists():
            continue
        try:
            text = csv_path.read_text(encoding="utf-8", errors="replace")
            # Astro strips BOM
            if text.startswith("\ufeff"):
                text = text[1:]
            for m in re.finditer(r"https?://(?:www\.)?creditdoc\.co/[^\"',\s]+", text):
                n = _normalize_url(m.group(0))
                if n:
                    excl.add(n)
        except Exception as e:
            print(f"  warn: exclusion file {csv_path} skipped: {e}", file=sys.stderr)
    return excl


def _keep_static(path: str) -> bool:
    """Match Astro's filter(): drop search/specials/linkedin-oauth-callback/print.
    Also drops retired family prefixes (EXCLUDED_PREFIXES)."""
    if path in STATIC_EXCLUSIONS:
        return False
    if path.endswith("/print/"):
        return False
    for prefix in EXCLUDED_PREFIXES:
        if path.startswith(prefix):
            return False
    return True


def _html_has_noindex(html_path: Path) -> bool:
    try:
        html = html_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return False
    for tag in re.findall(r"<meta\b[^>]*>", html, flags=re.IGNORECASE):
        if not re.search(r'\bname=["\']robots["\']', tag, flags=re.IGNORECASE):
            continue
        if re.search(r'\bcontent=["\'][^"\']*\bnoindex\b', tag, flags=re.IGNORECASE):
            return True
    return False


def walk_dist_urls() -> dict[str, float]:
    """Every dist/<...>/index.html → path + file mtime.

    Returns mapping url_path → mtime_epoch.
    """
    out: dict[str, float] = {}
    for root, _dirs, files in os.walk(DIST):
        if "index.html" not in files:
            continue
        rel = Path(root).relative_to(DIST)
        # Skip build chrome
        parts = rel.parts
        if parts and parts[0] in {"_astro", "_worker.js", "_server-islands"}:
            continue
        # Normalize path
        if str(rel) == ".":
            path = "/"
        else:
            path = "/" + str(rel).replace(os.sep, "/") + "/"
        html_path = Path(root) / "index.html"
        if not _keep_static(path):
            continue
        if _html_has_noindex(html_path):
            continue
        mtime = html_path.stat().st_mtime
        out[path] = mtime
    return out


def _load_supabase_anon_key() -> str | None:
    if not SUPABASE_ENV_FILE.exists():
        return None
    for line in SUPABASE_ENV_FILE.read_text().splitlines():
        m = re.match(r'^SUPABASE_ANON_KEY=["\']?([^"\'\s]+)', line)
        if m:
            return m.group(1)
    return None


def load_supabase_city_guides() -> list[dict[str, Any]]:
    """Fetch published city guide slugs from Supabase."""
    key = _load_supabase_anon_key()
    if not key:
        print("  warn: SUPABASE_ANON_KEY missing — city guides skipped", file=sys.stderr)
        return []
    url = (
        "https://pndpnjjkhknmutlmlwsk.supabase.co/rest/v1/city_guides"
        "?status=eq.ready_for_index&select=slug,updated_at"
    )
    req = urllib.request.Request(
        url,
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  warn: Supabase city_guides fetch failed: {e}", file=sys.stderr)
        return []


def db_urls() -> tuple[list[str], list[str]]:
    """Category paths + brand paths (brand filtered by profile file existence).

    Matches astro.config.mjs.DISABLED:310-334.
    """
    cats: list[str] = []
    brands: list[str] = []
    if not DB_PATH.exists():
        return cats, brands

    # Build the brandFiles set from src/content/brands/*.json
    brand_files_dir = REPO_ROOT / "src" / "content" / "brands"
    brand_slugs_with_profile: set[str] = set()
    if brand_files_dir.exists():
        for p in brand_files_dir.glob("*.json"):
            brand_slugs_with_profile.add(p.stem)

    with sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True) as conn:
        for r in conn.execute("SELECT slug FROM categories ORDER BY slug").fetchall():
            cats.append(f"/categories/{r[0]}/")
        for r in conn.execute(
            "SELECT DISTINCT brand_slug FROM lenders "
            "WHERE brand_slug IS NOT NULL AND brand_slug <> '' "
            "AND processing_status = 'ready_for_index' "
            "ORDER BY brand_slug"
        ).fetchall():
            slug = r[0]
            if slug in brand_slugs_with_profile:
                brands.append(f"/brand/{slug}/")
    return cats, brands


def load_state_roots() -> list[str]:
    """From src/content/states.json — matches astro.config lines 285-303."""
    states_json = REPO_ROOT / "src/content/states.json"
    if not states_json.exists():
        return []
    try:
        data = json.loads(states_json.read_text())
    except Exception:
        return []
    urls: list[str] = []
    for st in data.values() if isinstance(data, dict) else []:
        slug = None
        if isinstance(st, dict):
            slug = st.get("slug") or (st.get("name", "").lower().replace(" ", "-") if st.get("name") else None)
        if slug:
            urls.append(f"/state/{slug}/")
    return urls


def _priority_and_freq(url_path: str) -> tuple[float, str]:
    """Match Astro serialize() rules (astro.config lines 465-500)."""
    if "/best/" in url_path:
        return 0.9, "weekly"
    if "/answers/" in url_path:
        return 0.85, "weekly"
    if "/financial-wellness/" in url_path:
        return 0.8, "monthly"
    if "/brand/" in url_path:
        return 0.75, "weekly"
    if "/blog/" in url_path or "/categories/" in url_path:
        return 0.7, "weekly" if "/categories/" in url_path else "monthly"
    if "/review/" in url_path:
        return 0.6, "monthly"
    if "/compare/" in url_path or "/city/" in url_path or "/state/" in url_path:
        return 0.5, "monthly"
    return 0.5, "monthly"  # default


def _to_iso(mtime_epoch: float | str | None) -> str | None:
    if mtime_epoch is None:
        return None
    if isinstance(mtime_epoch, str):
        return mtime_epoch.split("T")[0]  # crude, keeps existing ISO date
    try:
        dt = datetime.fromtimestamp(mtime_epoch, tz=timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    except Exception:
        return None


def build_sitemap_entries() -> list[dict[str, Any]]:
    """Return a list of dicts: {url, lastmod, priority, changefreq}."""
    exclusions = load_exclusions()

    # 1. Walk dist/
    dist_urls = walk_dist_urls()

    # 2. DB categories + brands
    cat_paths, brand_paths = db_urls()

    # 3. State roots
    state_paths = load_state_roots()

    # 4. City guides (Supabase)
    city_guides = load_supabase_city_guides()

    # Deduplicate. Path → (lastmod_iso_or_None)
    path_to_lastmod: dict[str, str | None] = {}

    for path, mtime in dist_urls.items():
        path_to_lastmod[path] = _to_iso(mtime)

    for path in cat_paths + brand_paths + state_paths:
        if not _keep_static(path):
            continue
        # If we already have the file in dist/, its mtime wins.
        path_to_lastmod.setdefault(path, None)

    for cg in city_guides:
        slug = cg.get("slug") if isinstance(cg, dict) else None
        if not slug:
            continue
        path = f"/credit-guide/{slug}/"
        if not _keep_static(path):
            continue
        upd = cg.get("updated_at")
        lastmod = _to_iso(upd) if upd else None
        path_to_lastmod.setdefault(path, lastmod)

    # Filter exclusions
    entries: list[dict[str, Any]] = []
    for path, lastmod in path_to_lastmod.items():
        full_url = f"{SITE}{path}"
        normalized = _normalize_url(full_url)
        if normalized is None:
            continue
        if normalized in exclusions:
            continue
        priority, changefreq = _priority_and_freq(path)
        entries.append({
            "loc": normalized,  # Percent-encoded canonical form (matches Astro)
            "lastmod": lastmod,
            "priority": priority,
            "changefreq": changefreq,
        })

    entries.sort(key=lambda e: e["loc"])
    return entries


def write_sitemaps(entries: list[dict[str, Any]], dry_run: bool = False) -> None:
    chunks = [entries[i:i + ENTRY_LIMIT] for i in range(0, len(entries), ENTRY_LIMIT)]
    print(f"[sitemap] {len(entries)} URL(s) across {len(chunks)} chunk(s)")

    if dry_run:
        for i, chunk in enumerate(chunks):
            print(f"  chunk {i}: {len(chunk)} URLs (would write dist/sitemap-{i}.xml)")
        return

    for stale in DIST.glob("sitemap-*.xml"):
        if stale.name == "sitemap-index.xml":
            continue
        m = re.fullmatch(r"sitemap-(\d+)\.xml", stale.name)
        if m and int(m.group(1)) >= len(chunks):
            stale.unlink()

    for i, chunk in enumerate(chunks):
        out = DIST / f"sitemap-{i}.xml"
        # Atomic write
        tmp = out.with_suffix(".xml.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>')
            f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
            for e in chunk:
                f.write("<url>")
                f.write(f"<loc>{e['loc']}</loc>")
                if e.get("lastmod"):
                    f.write(f"<lastmod>{e['lastmod']}</lastmod>")
                f.write(f"<changefreq>{e['changefreq']}</changefreq>")
                f.write(f"<priority>{e['priority']}</priority>")
                f.write("</url>")
            f.write("</urlset>")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, out)

    # sitemap-index.xml
    idx = DIST / "sitemap-index.xml"
    tmp = idx.with_suffix(".xml.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>')
        f.write('<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
        for i in range(len(chunks)):
            f.write(f"<sitemap><loc>{SITE}/sitemap-{i}.xml</loc></sitemap>")
        f.write("</sitemapindex>")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, idx)
    print(f"[sitemap] wrote {len(chunks)} sitemap-N.xml + sitemap-index.xml → {DIST}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Regenerate dist/sitemap-*.xml from DB + dist walk.")
    parser.add_argument("--dry-run", action="store_true", help="Enumerate + count, do not write.")
    args = parser.parse_args()

    entries = build_sitemap_entries()
    write_sitemaps(entries, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
