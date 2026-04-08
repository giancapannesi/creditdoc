#!/usr/bin/env python3
"""
logo_gate.py — Build-time logo validator.

Runs BEFORE every build. Ensures every visible lender has a working logo.
If a logo is missing, attempts to fetch it. If fetch fails, generates a
branded text placeholder so the page never shows a broken image.

Usage:
    python3 scripts/logo_gate.py          # Check + fix all visible lenders
    python3 scripts/logo_gate.py --check  # Check only, no fixes (for CI)
    python3 scripts/logo_gate.py --category credit-repair  # Single category
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

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LENDER_DIR = PROJECT_ROOT / "src" / "content" / "lenders"
LOGO_DIR = PROJECT_ROOT / "public" / "logos"

GOOGLE_FAVICON = "https://t1.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://{host}&size=128"
ICON_HORSE = "https://icon.horse/icon/{host}"

# CreditDoc brand colors for placeholders
BRAND_BG = (15, 23, 42)       # slate-900
BRAND_TEXT = (56, 189, 248)    # sky-400
BRAND_BORDER = (30, 41, 59)   # slate-800

MIN_LOGO_BYTES = 500


def get_visible_lenders(category=None):
    """Get all lenders that will appear on the live site."""
    lenders = []
    for f in sorted(LENDER_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        ps = data.get("processing_status", "")
        if ps not in ("ready_for_index", "pending_approval"):
            continue

        if category and data.get("category") != category:
            continue

        slug = f.stem
        lenders.append({
            "slug": slug,
            "name": data.get("name", slug),
            "website_url": data.get("website_url", ""),
            "logo_url": data.get("logo_url", ""),
            "json_path": f,
        })
    return lenders


def logo_exists(slug):
    """Check if a valid local logo file exists."""
    logo_path = LOGO_DIR / f"{slug}.png"
    if logo_path.exists() and logo_path.stat().st_size >= MIN_LOGO_BYTES:
        return True
    # Check other extensions
    for ext in [".jpg", ".svg", ".webp"]:
        alt = LOGO_DIR / f"{slug}{ext}"
        if alt.exists() and alt.stat().st_size >= MIN_LOGO_BYTES:
            return True
    return False


def fetch_favicon(website_url):
    """Try to fetch a favicon for the website."""
    try:
        host = urlparse(website_url).hostname
    except Exception:
        return None

    if not host:
        return None

    for url in [GOOGLE_FAVICON.format(host=host), ICON_HORSE.format(host=host)]:
        try:
            r = requests.get(url, timeout=10, allow_redirects=True,
                           headers={"User-Agent": "Mozilla/5.0 CreditDoc/1.0"})
            if r.status_code == 200 and len(r.content) >= MIN_LOGO_BYTES:
                return r.content
        except Exception:
            continue

    return None


def generate_placeholder(name, slug):
    """Generate a branded text placeholder logo."""
    if not HAS_PIL:
        return None

    # Get initials (up to 2 chars)
    words = name.replace("-", " ").split()
    initials = "".join(w[0].upper() for w in words if w)[:2]
    if not initials:
        initials = slug[0].upper()

    # Create 200x200 image
    size = 200
    img = Image.new("RGB", (size, size), BRAND_BG)
    draw = ImageDraw.Draw(img)

    # Draw border
    draw.rectangle([0, 0, size-1, size-1], outline=BRAND_BORDER, width=2)

    # Draw initials centered
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
    except (OSError, IOError):
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), initials, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (size - text_w) // 2
    y = (size - text_h) // 2 - 5
    draw.text((x, y), initials, fill=BRAND_TEXT, font=font)

    # Save to bytes
    from io import BytesIO
    buf = BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def fix_logo(lender):
    """Attempt to fix a missing logo: fetch favicon, then generate placeholder."""
    slug = lender["slug"]
    website_url = lender["website_url"]
    name = lender["name"]

    # Try favicon
    if website_url:
        content = fetch_favicon(website_url)
        if content:
            logo_path = LOGO_DIR / f"{slug}.png"
            logo_path.write_bytes(content)
            update_json(lender["json_path"], f"/logos/{slug}.png")
            return "favicon"

    # Generate placeholder
    content = generate_placeholder(name, slug)
    if content:
        logo_path = LOGO_DIR / f"{slug}.png"
        logo_path.write_bytes(content)
        update_json(lender["json_path"], f"/logos/{slug}.png")
        return "placeholder"

    return None


def update_json(json_path, logo_path):
    """Set logo_url in lender JSON."""
    data = json.loads(json_path.read_text())
    if data.get("logo_url") != logo_path:
        data["logo_url"] = logo_path
        json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Build-time logo validator")
    parser.add_argument("--check", action="store_true", help="Check only, no fixes")
    parser.add_argument("--category", type=str, help="Single category to check")
    args = parser.parse_args()

    LOGO_DIR.mkdir(parents=True, exist_ok=True)

    lenders = get_visible_lenders(category=args.category)
    print(f"Logo gate: checking {len(lenders)} visible lenders...")

    missing = []
    ok = 0
    for l in lenders:
        if logo_exists(l["slug"]):
            ok += 1
        else:
            missing.append(l)

    print(f"  OK: {ok} | Missing: {len(missing)}")

    if not missing:
        print("All logos present. Gate passed.")
        return

    if args.check:
        print(f"\nFAIL: {len(missing)} lenders have no logo:")
        for m in missing[:20]:
            print(f"  - {m['slug']}")
        if len(missing) > 20:
            print(f"  ... and {len(missing) - 20} more")
        sys.exit(1)

    # Fix mode
    print(f"\nFixing {len(missing)} missing logos...")
    fetched = placeholder = failed = 0

    for i, lender in enumerate(missing, 1):
        result = fix_logo(lender)
        if result == "favicon":
            fetched += 1
            print(f"  [{i}/{len(missing)}] FAVICON  {lender['slug']}")
        elif result == "placeholder":
            placeholder += 1
            print(f"  [{i}/{len(missing)}] PLACEHOLDER  {lender['slug']}")
        else:
            failed += 1
            print(f"  [{i}/{len(missing)}] FAILED  {lender['slug']}")

        # Rate limit favicon fetches
        if i < len(missing):
            time.sleep(0.15)

    print(f"\nLogo gate results:")
    print(f"  Fetched favicon:  {fetched}")
    print(f"  Generated placeholder: {placeholder}")
    print(f"  Failed: {failed}")

    if failed > 0:
        print(f"\nWARNING: {failed} lenders still have no logo")
    else:
        print("\nAll logos resolved. Gate passed.")


if __name__ == "__main__":
    main()
