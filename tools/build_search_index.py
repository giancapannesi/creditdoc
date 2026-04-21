#!/usr/bin/env python3
"""
Build a slim client-side search index of all published lenders.

Output: creditdoc/public/search/lender-name-index.json
Schema: [{"s": slug, "n": name, "c": city, "st": state}, ...]

Used by src/components/LenderNameSearch.astro (hero + post-categories widget).
Size target: ~1.3 MB raw, ~260 KB gzipped over the wire.

Safe to run any time. Idempotent. Reads from src/content/lenders/*.json (what
actually ships to the site) so the index always matches what users see.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LENDERS_DIR = ROOT / "src" / "content" / "lenders"
OUT_DIR = ROOT / "public" / "search"
OUT_FILE = OUT_DIR / "lender-name-index.json"


def main() -> int:
    if not LENDERS_DIR.exists():
        print(f"ERROR: {LENDERS_DIR} does not exist", file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    entries: list[dict] = []
    skipped = 0
    for jf in sorted(LENDERS_DIR.glob("*.json")):
        try:
            d = json.loads(jf.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  [skip] {jf.name}: {e}")
            skipped += 1
            continue
        slug = d.get("slug") or jf.stem
        name = d.get("name")
        if not name:
            skipped += 1
            continue
        # no_index profiles shouldn't show up in name search either
        if d.get("no_index") is True:
            skipped += 1
            continue

        addr = (d.get("address") or "").strip()
        city = ""
        state = ""
        # Prefer structured fields when present
        ci = d.get("company_info") or {}
        city = (ci.get("city") or "").strip()
        state = (ci.get("state") or "").strip()
        # Fall back to parsing "123 Main St, City, ST 12345"
        if (not city or not state) and addr:
            parts = [p.strip() for p in addr.split(",")]
            if len(parts) >= 2:
                if not city:
                    city = parts[-2][:40]
                if not state:
                    tail = parts[-1].strip().split()
                    if tail and len(tail[0]) == 2 and tail[0].isupper():
                        state = tail[0]

        entries.append({
            "s": slug,
            "n": name,
            "c": city,
            "st": state,
        })

    # Stable sort by name for deterministic diffs
    entries.sort(key=lambda e: (e["n"].lower(), e["s"]))

    OUT_FILE.write_text(json.dumps(entries, separators=(",", ":"), ensure_ascii=False))
    size_kb = OUT_FILE.stat().st_size / 1024
    print(f"[ok] wrote {OUT_FILE.relative_to(ROOT)} — {len(entries)} entries, {size_kb:,.1f} KB (skipped {skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
