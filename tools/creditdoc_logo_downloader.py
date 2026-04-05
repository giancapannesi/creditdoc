#!/usr/bin/env python3
"""
creditdoc_logo_localizer.py — Download logos to local storage.

Phase 2 of logo pipeline:
  1. Other agent (creditdoc_logo_fetcher.py) scrapes websites for high-quality logo URLs
  2. THIS script downloads those URLs to public/logos/{slug}.png and updates logo_url

For lenders with no logo_url set yet (or Google Photos URLs), falls back to
Google faviconV2 → icon.horse.

Saves to public/logos/{slug}.png and sets logo_url = "/logos/{slug}.png"

Usage:
    python3 tools/creditdoc_logo_downloader.py --count 100   # localize first 100
    python3 tools/creditdoc_logo_downloader.py --all          # all visible lenders
    python3 tools/creditdoc_logo_downloader.py --missing       # only those without local logo
    python3 tools/creditdoc_logo_downloader.py --slug arbor-financial  # single lender
    python3 tools/creditdoc_logo_downloader.py --stats         # coverage report
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

try:
    import requests
except ImportError:
    os.system(f"{sys.executable} -m pip install requests -q")
    import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LENDER_DIR = PROJECT_ROOT / "src" / "content" / "lenders"
LOGO_DIR = PROJECT_ROOT / "public" / "logos"

# Favicon fallback APIs (for lenders with no logo_url)
GOOGLE_FAVICON = "https://t1.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://{host}&size=128"
ICON_HORSE = "https://icon.horse/icon/{host}"

RATE_LIMIT = 10
MIN_INTERVAL = 1.0 / RATE_LIMIT

# URLs that are junk / not real logos
JUNK_PATTERNS = [
    "googleusercontent.com",  # Google Maps photos, filtered by template
    "google.com/s2/favicons",  # Old Google favicon API (low quality, external)
]


def is_external_logo(url):
    """Check if logo_url is an external URL that should be localized."""
    if not url:
        return False
    if url.startswith("/logos/"):
        return False  # Already local
    if url.startswith("http"):
        return True
    return False


def is_junk_logo(url):
    """Check if logo_url is a known junk/unusable URL."""
    if not url:
        return True
    lower = url.lower()
    return any(p in lower for p in JUNK_PATTERNS)


def get_extension(url, content_type=""):
    """Guess file extension from URL or content type."""
    lower = url.lower()
    if ".svg" in lower:
        return ".svg"
    if ".png" in lower:
        return ".png"
    if ".jpg" in lower or ".jpeg" in lower:
        return ".jpg"
    if ".webp" in lower:
        return ".webp"
    if ".avif" in lower:
        return ".avif"
    if "svg" in content_type:
        return ".svg"
    if "jpeg" in content_type or "jpg" in content_type:
        return ".jpg"
    if "webp" in content_type:
        return ".webp"
    return ".png"  # default


def get_lenders(count=None, missing_only=False, slug=None):
    """Scan lender JSONs and return list of dicts needing localization."""
    results = []
    for f in sorted(LENDER_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        if data.get("no_index"):
            continue
        if not data.get("website_url"):
            continue

        lender_slug = f.stem
        if slug and lender_slug != slug:
            continue

        logo_url = data.get("logo_url", "")

        # Skip if already has local logo file
        if missing_only and logo_url.startswith("/logos/"):
            local_file = LOGO_DIR / logo_url.split("/")[-1]
            if local_file.exists() and local_file.stat().st_size > 100:
                continue

        results.append({
            "slug": lender_slug,
            "website_url": data["website_url"],
            "logo_url": logo_url,
            "json_path": f,
        })

    if count and not slug:
        results = results[:count]
    return results


def download_url(url, timeout=15):
    """Download a URL, return (bytes, content_type) or (None, None)."""
    try:
        r = requests.get(url, timeout=timeout, allow_redirects=True,
                         headers={"User-Agent": "Mozilla/5.0 CreditDoc/1.0"})
        if r.status_code == 200 and len(r.content) > 100:
            return r.content, r.headers.get("content-type", "")
    except Exception:
        pass
    return None, None


def download_favicon(host):
    """Fallback: try faviconV2 then icon.horse."""
    content, ct = download_url(GOOGLE_FAVICON.format(host=host))
    if content:
        return content, ct, "faviconV2"

    content, ct = download_url(ICON_HORSE.format(host=host))
    if content:
        return content, ct, "icon.horse"

    return None, None, None


def update_json(json_path, logo_path):
    """Set logo_url in lender JSON."""
    data = json.loads(json_path.read_text())
    data["logo_url"] = logo_path
    json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def print_stats():
    """Print logo coverage report."""
    total = empty = google_photos = external = local = favicon_ext = 0
    for f in LENDER_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text())
        except Exception:
            continue
        if data.get("no_index"):
            continue
        total += 1
        logo = data.get("logo_url", "")
        if not logo:
            empty += 1
        elif logo.startswith("/logos/"):
            local += 1
        elif "googleusercontent.com" in logo:
            google_photos += 1
        elif "google.com/s2/favicons" in logo:
            favicon_ext += 1
        elif logo.startswith("http"):
            external += 1

    print(f"\nCreditDoc Logo Coverage")
    print(f"{'='*45}")
    print(f"Visible lenders:        {total:>7}")
    print(f"Local (/logos/):        {local:>7}  ← goal")
    print(f"External URLs:          {external:>7}  ← need download")
    print(f"Google Photos (junk):   {google_photos:>7}  ← need favicon")
    print(f"External favicon URLs:  {favicon_ext:>7}  ← need download")
    print(f"Empty (no logo):        {empty:>7}  ← need favicon")
    print(f"{'='*45}")
    print(f"Need localization:      {external + google_photos + favicon_ext + empty:>7}")

    # Local files
    if LOGO_DIR.exists():
        files = list(LOGO_DIR.iterdir())
        size = sum(f.stat().st_size for f in files if f.is_file())
        print(f"\nLocal logo files: {len(files)} ({size / (1024*1024):.1f}MB)")


def main():
    parser = argparse.ArgumentParser(description="Download & localize logos for CreditDoc lenders")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--count", type=int, help="Process first N lenders")
    group.add_argument("--all", action="store_true", help="All visible lenders")
    group.add_argument("--missing", action="store_true", help="Only those without local logo")
    group.add_argument("--slug", type=str, help="Single lender by slug")
    group.add_argument("--stats", action="store_true", help="Coverage report only")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without downloading")
    args = parser.parse_args()

    LOGO_DIR.mkdir(parents=True, exist_ok=True)

    if args.stats:
        print_stats()
        return

    missing_only = args.missing or args.all
    lenders = get_lenders(count=args.count, missing_only=missing_only, slug=args.slug)
    print(f"Lenders to process: {len(lenders)}")

    if args.dry_run:
        external = sum(1 for l in lenders if is_external_logo(l["logo_url"]) and not is_junk_logo(l["logo_url"]))
        needs_favicon = sum(1 for l in lenders if not l["logo_url"] or is_junk_logo(l["logo_url"]))
        already_local = sum(1 for l in lenders if l["logo_url"].startswith("/logos/"))
        print(f"  External URLs to download:  {external}")
        print(f"  Need favicon fallback:      {needs_favicon}")
        print(f"  Already local:              {already_local}")
        return

    success = failed = skipped = 0
    localized = favicon_dl = 0
    last_request = 0

    for i, lender in enumerate(lenders, 1):
        slug = lender["slug"]
        logo_url = lender["logo_url"]
        json_path = lender["json_path"]
        website_url = lender["website_url"]

        # Already local and file exists?
        if logo_url.startswith("/logos/"):
            local_file = LOGO_DIR / logo_url.split("/")[-1]
            if local_file.exists() and local_file.stat().st_size > 100:
                skipped += 1
                continue

        # Rate limit
        elapsed = time.time() - last_request
        if elapsed < MIN_INTERVAL:
            time.sleep(MIN_INTERVAL - elapsed)
        last_request = time.time()

        content = None
        source = ""

        # Strategy 1: Download the external logo URL (set by scraper agent)
        if is_external_logo(logo_url) and not is_junk_logo(logo_url):
            content, ct = download_url(logo_url)
            if content:
                ext = get_extension(logo_url, ct)
                source = "localized"
                localized += 1

        # Strategy 2: Favicon fallback (no logo_url, or junk, or download failed)
        if not content:
            try:
                host = urlparse(website_url).hostname
            except Exception:
                host = None

            if host:
                content, ct, src = download_favicon(host)
                if content:
                    ext = ".png"
                    source = src
                    favicon_dl += 1

        if content:
            filename = f"{slug}{ext}" if 'ext' in dir() and ext != ".png" else f"{slug}.png"
            logo_file = LOGO_DIR / filename
            logo_file.write_bytes(content)
            local_path = f"/logos/{filename}"
            update_json(json_path, local_path)
            size_kb = len(content) / 1024
            print(f"  [{i}/{len(lenders)}] OK    {slug} — {source} ({size_kb:.1f}KB)")
            success += 1
        else:
            print(f"  [{i}/{len(lenders)}] FAIL  {slug}")
            failed += 1

        if i % 500 == 0:
            print(f"\n--- Progress: {i}/{len(lenders)} | OK: {success} | FAIL: {failed} | SKIP: {skipped} ---\n")

    print(f"\n{'='*60}")
    print(f"Done. Processed {len(lenders)} lenders.")
    print(f"  Localized (from scraper URLs): {localized}")
    print(f"  Favicon fallback:              {favicon_dl}")
    print(f"  Failed:                        {failed}")
    print(f"  Skipped (already local):       {skipped}")
    if LOGO_DIR.exists():
        files = list(LOGO_DIR.iterdir())
        size = sum(f.stat().st_size for f in files if f.is_file())
        print(f"  Logo dir: {size / (1024*1024):.1f}MB ({len(files)} files)")


if __name__ == "__main__":
    main()
