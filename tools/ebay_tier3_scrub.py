#!/usr/bin/env python3
"""
eBay Tier 3 body-text scrubber.

Input: 92 slugs from reports/ebay_cleanup_2026-04-21.md Tier 3 section.
For each slug:
  1. Load description_long + pros + cons from DB.
  2. Drop any sentence (or list item) containing 'eBay' (word-boundary, any case).
  3. If resulting description_long < 200 chars, flag for manual review — skip DB write.
  4. Otherwise DB write via update_lender(force=True, updated_by='ebay_tier3_scrub').

Dry-run by default. --pilot for diff on first 10. --apply to execute.
Never touches protected profiles. Report written to reports/.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "creditdoc.db"

EBAY_RE = re.compile(r"\bebay\b", re.IGNORECASE)

ABBREVIATIONS = [
    "U.S.A.", "U.S.", "U.K.", "e.g.", "i.e.", "etc.", "vs.", "Mr.", "Mrs.", "Ms.",
    "Dr.", "Jr.", "Sr.", "Inc.", "Ltd.", "Co.", "Corp.", "St.", "Ave.", "Blvd.",
    "Rd.", "No.", "a.m.", "p.m.", "A.M.", "P.M.",
]
NUL = "\x00"

TIER3_SLUGS = [
    "14k-gold-coin", "14k-pawn-exchange", "14k-pawn-gun", "1st-pacific-pawn",
    "am-pawn-and-gold-buyers", "arizona-ez-pawn", "atlantic-jewelry-loan",
    "best-deal-gun-and-pawn", "best-pawn-shop-euclid", "best-pawn-shop-north-randall",
    "beverly-hills-jewelry-watch-loan", "big-money-pawn", "bishop-pawn",
    "bronx-pawn-shop", "buy-sell-trade-it-all", "cal-coin-and-jewelry",
    "cash-express-jewelry-pawn", "cash-inn-south-jewelry-pawn", "casino-pawn",
    "cbj-jewelry-and-pawn", "cc-coins-jewelry-loan", "coast-to-coast-pawn",
    "county-line-pawn-shop", "crazy-pawn-jewelry", "dash-2-cash-pawn-shop",
    "dave-tipp-jewelry-loan", "diamonds-beyond", "dynasty-jewelry-and-pawn",
    "elliott-salter-pawnshop", "excel-pawn-and-jewelry", "famous-pawn-jewelry",
    "fresno-hock-shoppe", "gem-loan-of-beverly-hills", "georges-pawn-shop",
    "globe-loan-jewelry", "gold-n-stones-ii-pawn-shop", "great-lakes-pawn",
    "irving-super-pawn-gun", "jewelry-loan", "kaybee-jewelry-and-loan",
    "la-habra-loan-jewelry", "lincoln-square-pawnbrokers", "lous-jewelry-pawn",
    "loyalty-pawn-1", "loyalty-pawn-2", "loyalty-pawn", "metro-pawn-and-gun",
    "mo-money-pawn-shop", "money-mizer-pawns-and-jewelers-of-jacksonville-fl-acme",
    "mr-pawn-nyc", "north-city-pawn", "once-a-pawn-a-time", "one-stop-pawn-shop",
    "paradise-pawnbrokers", "pawn-into-cash", "pawn-now-mesa-az", "pawn-now-mesa",
    "pawn-now", "pawn-phoenix", "peoples-pawn-and-jewelry", "poplar-jewelry-loan",
    "poplar-jewelry-pawn", "queen-of-pawns-kissimmee", "queen-of-pawns-orlando-fl",
    "queen-of-pawns-orlando", "queen-of-pawns-tampa-fl", "queen-of-pawns-tampa",
    "queen-of-pawns", "r-j-jewelry-loan", "southern-ohio-gold-and-silver-exchange",
    "sunbelt-pawn-jewelry-loan-1", "sunbelt-pawn-jewelry-loan-10",
    "sunbelt-pawn-jewelry-loan-11", "sunbelt-pawn-jewelry-loan-12",
    "sunbelt-pawn-jewelry-loan-17", "sunbelt-pawn-jewelry-loan-2",
    "sunbelt-pawn-jewelry-loan-3", "sunbelt-pawn-jewelry-loan-6",
    "sunbelt-pawn-jewelry-loan-7", "sunbelt-pawn-jewelry-loan-9",
    "tempe-pawn-gold", "the-kings-pawn", "top-cash-pawn-1", "top-cash-pawn-9",
    "top-cash-pawn-austin-tx", "top-cash-pawn-austin", "top-cash-pawn-pflugerville",
    "top-cash-pawn-plano", "top-cash-pawn", "trading-post-northwest",
    "warminster-cash-exchange-pawn-shop", "wimpeys-pawn-shop",
]

PILOT_SLUGS = TIER3_SLUGS[:10]
MIN_DESC_CHARS = 200


def split_sentences(text: str) -> list[str]:
    if not text or not text.strip():
        return []
    protected = text
    for abbr in ABBREVIATIONS:
        protected = protected.replace(abbr, abbr.replace(".", NUL))
    protected = re.sub(r"(\d)\.(\d)", lambda m: m.group(1) + NUL + m.group(2), protected)
    protected = re.sub(r"\.(?=[a-z]{2,4}\b)", NUL, protected)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])", protected)
    return [p.replace(NUL, ".").strip() for p in parts if p.strip()]


def scrub_text(text: str) -> tuple[str, list[str]]:
    """Drop any sentence containing 'eBay'. Preserves paragraph breaks.
    Returns (cleaned, dropped_sentences)."""
    if not text:
        return text, []
    dropped: list[str] = []
    cleaned_paragraphs: list[str] = []
    for para in re.split(r"\n\s*\n", text):
        kept_sents: list[str] = []
        for s in split_sentences(para):
            if EBAY_RE.search(s):
                dropped.append(s)
            else:
                kept_sents.append(s)
        joined = " ".join(kept_sents).strip()
        if joined:
            cleaned_paragraphs.append(joined)
    return "\n\n".join(cleaned_paragraphs).strip(), dropped


def scrub_list(items) -> tuple[list, list]:
    """Drop any list item (string) mentioning 'eBay'. Returns (kept, dropped)."""
    if not items or not isinstance(items, list):
        return items, []
    kept, dropped = [], []
    for it in items:
        if isinstance(it, str) and EBAY_RE.search(it):
            dropped.append(it)
        else:
            kept.append(it)
    return kept, dropped


def load_row(conn: sqlite3.Connection, slug: str) -> dict | None:
    cur = conn.cursor()
    cur.execute("SELECT slug, is_protected, data FROM lenders WHERE slug = ?", (slug,))
    row = cur.fetchone()
    if not row:
        return None
    slug_, protected, data_json = row
    return {"slug": slug_, "is_protected": bool(protected), "data": json.loads(data_json)}


def process_row(row: dict) -> dict:
    """Compute scrub result without writing."""
    data = row["data"]
    desc = data.get("description_long") or ""
    pros = data.get("pros") or []
    cons = data.get("cons") or []

    new_desc, dropped_desc = scrub_text(desc)
    new_pros, dropped_pros = scrub_list(pros)
    new_cons, dropped_cons = scrub_list(cons)

    updates = {}
    flags: list[str] = []

    has_desc_change = bool(dropped_desc)
    has_pros_change = bool(dropped_pros)
    has_cons_change = bool(dropped_cons)

    if has_desc_change:
        if len(new_desc) < MIN_DESC_CHARS:
            flags.append(f"desc_too_short:{len(new_desc)}")
        else:
            updates["description_long"] = new_desc

    if has_pros_change:
        updates["pros"] = new_pros
    if has_cons_change:
        updates["cons"] = new_cons

    return {
        "slug": row["slug"],
        "is_protected": row["is_protected"],
        "orig_desc_len": len(desc),
        "new_desc_len": len(new_desc),
        "dropped_desc": dropped_desc,
        "dropped_pros": dropped_pros,
        "dropped_cons": dropped_cons,
        "updates": updates,
        "flags": flags,
    }


def render_diff(results: list[dict]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# eBay Tier 3 Scrub — Diff",
        "",
        f"Generated: {now}",
        f"Rows: {len(results)}",
        f"Would write: {sum(1 for r in results if r['updates'] and not r['flags'])}",
        f"Flagged manual: {sum(1 for r in results if r['flags'])}",
        f"No change: {sum(1 for r in results if not r['updates'] and not r['flags'])}",
        "",
    ]
    for r in results:
        lines.append(f"## `{r['slug']}`")
        lines.append(f"- desc: {r['orig_desc_len']} → {r['new_desc_len']} chars")
        lines.append(f"- dropped: {len(r['dropped_desc'])} desc / {len(r['dropped_pros'])} pros / {len(r['dropped_cons'])} cons")
        if r["flags"]:
            lines.append(f"- **FLAGS:** {', '.join(r['flags'])}")
        for s in r["dropped_desc"]:
            lines.append(f"  - ~~desc: {s}~~")
        for s in r["dropped_pros"]:
            lines.append(f"  - ~~pros: {s}~~")
        for s in r["dropped_cons"]:
            lines.append(f"  - ~~cons: {s}~~")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true", help="10-row preview diff, no writes")
    ap.add_argument("--dry-run", action="store_true", help="All 92 rows, diff only")
    ap.add_argument("--apply", action="store_true", help="Apply DB writes")
    args = ap.parse_args()

    if not (args.pilot or args.dry_run or args.apply):
        ap.error("pass --pilot, --dry-run, or --apply")

    conn = sqlite3.connect(DB_PATH)
    slugs = PILOT_SLUGS if args.pilot else TIER3_SLUGS

    results = []
    missing = []
    protected_skipped = []
    for slug in slugs:
        row = load_row(conn, slug)
        if not row:
            missing.append(slug)
            continue
        if row["is_protected"]:
            protected_skipped.append(slug)
            continue
        results.append(process_row(row))
    conn.close()

    now = datetime.now(timezone.utc)
    report = render_diff(results)
    tag = "pilot" if args.pilot else ("apply" if args.apply else "dry")
    out = ROOT / "reports" / f"ebay_tier3_scrub_{tag}_{now:%Y-%m-%dT%H-%M-%SZ}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report)
    print(f"Report: {out}")
    print(f"  rows: {len(results)} | missing: {len(missing)} | protected_skipped: {len(protected_skipped)}")
    print(f"  would_write: {sum(1 for r in results if r['updates'] and not r['flags'])}")
    print(f"  flagged: {sum(1 for r in results if r['flags'])}")
    print(f"  no_change: {sum(1 for r in results if not r['updates'] and not r['flags'])}")
    if missing:
        print(f"  MISSING slugs: {missing}")
    if protected_skipped:
        print(f"  PROTECTED (skipped): {protected_skipped}")

    if not args.apply:
        return 0

    # APPLY path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from creditdoc_db import CreditDocDB  # type: ignore

    db = CreditDocDB()
    written = 0
    for r in results:
        if not r["updates"] or r["flags"]:
            continue
        dropped = len(r["dropped_desc"]) + len(r["dropped_pros"]) + len(r["dropped_cons"])
        db.update_lender(
            r["slug"],
            r["updates"],
            updated_by="ebay_tier3_scrub",
            reason=f"removed {dropped} eBay mention(s) per founder directive",
            force=True,
        )
        written += 1
        print(f"  [WRITE] {r['slug']}: {dropped} mention(s) scrubbed")
    db.close()
    print(f"\nWritten: {written}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
