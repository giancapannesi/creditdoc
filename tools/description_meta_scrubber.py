#!/usr/bin/env python3
"""
Description Meta-Commentary Scrubber

Removes AI scraping-analysis leakage from description_long fields. A previous
enrichment run saved its own scratchpad commentary (e.g. "the website content
provided contains multiple 404 errors") as real lender bios. No one reading
a lender review cares about 404s or that 'the website explicitly states...'.

Approach: sentence-level scrub. Any sentence containing a flagged phrase is
dropped. The rest of the description stays intact. If scrubbing leaves <200
chars, the row is flagged for manual review instead of auto-updated.

MODES:
    --pilot             Pilot on 10 known-polluted rows, write markdown diff, NO DB writes
    --dry-run --limit N Scan N candidate rows, write report, NO DB writes
    --apply --limit N   Scrub N rows and WRITE TO DB (force=True, updated_by='meta_scrub')
    --slug SLUG         Target a specific slug (works with --dry-run or --apply)

Run: source /srv/BusinessOps/.venv/bin/activate && python3 tools/description_meta_scrubber.py --pilot
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

# Hard-signal phrases — if a sentence contains any of these, it's meta-commentary
# or scraping artifact and should be removed. Case-insensitive.
SCRUB_PHRASES = [
    r"\b404\s+error",
    r"\bwebsite content provided",
    r"\bthe website provided",
    r"\bbased on the (?:website|provided)",
    r"\bthe provided content",
    r"\bSorry,?\s*this type of loan",
    r"\bsuggesting either outdated",
    r"\bwebsite content indicates",
    r"\boutdated links",
    r"\bthe website explicitly states",
    r"\bwebsite explicitly states",
    r"\bmultiple 404",
    r"\bappears to vary by state",
    r"\bthis is not available in this state",
    r"\blimited availability in certain geographic",
    r"\bthe content (?:provided|suggests)",
    r"\bthe scraped",
    r"\bweb scraping",
]

SCRUB_PATTERN = re.compile("|".join(SCRUB_PHRASES), re.IGNORECASE)

# Abbreviations and patterns whose "." must NOT be treated as sentence end
ABBREVIATIONS = [
    "U.S.A.", "U.S.", "U.K.", "e.g.", "i.e.", "etc.", "vs.", "Mr.", "Mrs.", "Ms.",
    "Dr.", "Jr.", "Sr.", "Inc.", "Ltd.", "Co.", "Corp.", "St.", "Ave.", "Blvd.",
    "Rd.", "No.", "a.m.", "p.m.", "A.M.", "P.M.",
]

NUL = "\x00"


def split_sentences(text: str) -> list[str]:
    """
    Split on sentence boundaries without breaking abbreviations, decimals,
    or URLs. Protect known abbrevs + decimal numbers + domain TLDs by
    swapping their '.' with a sentinel, split on '. ' (punct + whitespace +
    capital), then restore.
    """
    if not text or not text.strip():
        return []
    protected = text
    for abbr in ABBREVIATIONS:
        protected = protected.replace(abbr, abbr.replace(".", NUL))
    # Decimal numbers like 3.5, 4.99
    protected = re.sub(r"(\d)\.(\d)", lambda m: m.group(1) + NUL + m.group(2), protected)
    # Domain-style dots (WU.com, bank.org) — '.' followed by 2-4 lowercase letters
    protected = re.sub(r"\.(?=[a-z]{2,4}\b)", NUL, protected)
    # Split on end-punct + whitespace + capital/digit/quote (start of next sentence)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])", protected)
    return [p.replace(NUL, ".").strip() for p in parts if p.strip()]

PILOT_SLUGS = [
    "ace-cash-express-alhambra",
    "ace-cash-express-bakersfield",
    "ace-cash-express-denver",
    "moneygram-albuquerque",
    "western-union-atlanta-ga",
    "consumer-credit-counseling-services-seattle",
    "superb-cash-advance-tulsa",
    "ria-money-transfer-houston",
    "orlandi-valuta-los-angeles",
    "texas-car-title-and-payday-loan-services-inc-austin",
]


def scrub_description(text: str) -> tuple[str, list[str]]:
    """
    Returns (cleaned_text, dropped_sentences).
    Preserves sentences that don't match any flagged phrase.
    """
    if not text:
        return text, []
    sentences = split_sentences(text)
    kept, dropped = [], []
    for s in sentences:
        if SCRUB_PATTERN.search(s):
            dropped.append(s)
        else:
            kept.append(s)
    cleaned = " ".join(kept).strip()
    return cleaned, dropped


def load_candidates(conn: sqlite3.Connection, limit: int, slug: str | None) -> list[dict]:
    cur = conn.cursor()
    if slug:
        cur.execute("SELECT slug, brand_slug, is_protected, data FROM lenders WHERE slug = ?", (slug,))
    else:
        # Only rows where description_long contains a hard signal
        like_clauses = " OR ".join(
            [
                "json_extract(data,'$.description_long') LIKE '%404 error%'",
                "json_extract(data,'$.description_long') LIKE '%multiple 404%'",
                "json_extract(data,'$.description_long') LIKE '%website content provided%'",
                "json_extract(data,'$.description_long') LIKE '%the website provided%'",
                "json_extract(data,'$.description_long') LIKE '%based on the website%'",
                "json_extract(data,'$.description_long') LIKE '%based on the provided%'",
                "json_extract(data,'$.description_long') LIKE '%the provided content%'",
                "json_extract(data,'$.description_long') LIKE '%the content provided%'",
                "json_extract(data,'$.description_long') LIKE '%the content suggests%'",
                "json_extract(data,'$.description_long') LIKE '%the scraped%'",
                "json_extract(data,'$.description_long') LIKE '%web scraping%'",
                "json_extract(data,'$.description_long') LIKE '%Sorry, this type of loan%'",
                "json_extract(data,'$.description_long') LIKE '%suggesting either outdated%'",
                "json_extract(data,'$.description_long') LIKE '%website content indicates%'",
                "json_extract(data,'$.description_long') LIKE '%website explicitly states%'",
                "json_extract(data,'$.description_long') LIKE '%outdated links%'",
                "json_extract(data,'$.description_long') LIKE '%appears to vary by state%'",
                "json_extract(data,'$.description_long') LIKE '%this is not available in this state%'",
                "json_extract(data,'$.description_long') LIKE '%limited availability in certain geographic%'",
            ]
        )
        q = f"""
            SELECT slug, brand_slug, is_protected, data
            FROM lenders
            WHERE ({like_clauses})
            ORDER BY brand_slug, slug
            LIMIT ?
        """
        cur.execute(q, (limit,))
    rows = []
    for slug_, brand, protected, data_json in cur.fetchall():
        data = json.loads(data_json)
        rows.append(
            {
                "slug": slug_,
                "brand_slug": brand,
                "is_protected": bool(protected),
                "desc_long": data.get("description_long") or "",
            }
        )
    return rows


def render_pilot_report(entries: list[dict]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Description Meta-Commentary Scrubber — Pilot Diff",
        "",
        f"**Generated:** {now}",
        f"**DB writes:** NONE — review-only",
        f"**Rows:** {len(entries)}",
        "",
        "## What this scrubber does",
        "",
        "Removes individual sentences that contain scraping-analysis leakage",
        "(phrases like '404 errors', 'website content provided', 'outdated links',",
        "'Sorry, this type of loan is not available'). Keeps every other sentence",
        "verbatim. If the cleaned result is shorter than 200 chars, the row is",
        "flagged for manual review instead of auto-applied.",
        "",
        "## Diffs",
        "",
    ]
    for i, e in enumerate(entries, 1):
        orig = e["desc_long"]
        cleaned, dropped = scrub_description(orig)
        lines.append(f"### {i}. `{e['slug']}`")
        lines.append("")
        lines.append(f"- brand: `{e['brand_slug']}` | protected: {e['is_protected']}")
        lines.append(f"- orig length: {len(orig)}  →  cleaned length: {len(cleaned)}")
        lines.append(f"- sentences dropped: **{len(dropped)}**")
        if len(cleaned) < 200:
            lines.append(f"- ⚠️  **TOO SHORT after scrub ({len(cleaned)} chars) — would flag for manual review**")
        lines.append("")
        lines.append("**BEFORE:**")
        lines.append(f"> {orig}")
        lines.append("")
        lines.append("**AFTER:**")
        lines.append(f"> {cleaned}")
        lines.append("")
        if dropped:
            lines.append("**Sentences removed:**")
            for s in dropped:
                lines.append(f"- ~~{s}~~")
            lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true", help="Pilot 10 hard-coded rows, markdown diff, no DB writes")
    ap.add_argument("--dry-run", action="store_true", help="Scan candidates, write report, no DB writes")
    ap.add_argument("--apply", action="store_true", help="Scrub + WRITE TO DB")
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--slug", type=str)
    args = ap.parse_args()

    conn = sqlite3.connect(DB_PATH)

    if args.pilot:
        entries = []
        for slug in PILOT_SLUGS:
            rows = load_candidates(conn, 1, slug)
            if rows:
                entries.append(rows[0])
            else:
                print(f"SKIP {slug}: not in DB", file=sys.stderr)
        if not entries:
            print("No pilot rows found.", file=sys.stderr)
            return 2
        out = ROOT / "reports" / f"description_scrub_pilot_{datetime.now(timezone.utc):%Y-%m-%dT%H-%M-%SZ}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_pilot_report(entries))
        print(f"Pilot report: {out}")
        # Quick summary
        total_drop = sum(len(scrub_description(e['desc_long'])[1]) for e in entries)
        too_short = sum(1 for e in entries if len(scrub_description(e['desc_long'])[0]) < 200)
        print(f"  {len(entries)} rows | {total_drop} sentences dropped | {too_short} flagged as too-short")
        return 0

    # dry-run or apply over all candidate polluted rows
    if not (args.dry_run or args.apply):
        print("pass --pilot, --dry-run, or --apply", file=sys.stderr)
        return 1

    rows = load_candidates(conn, args.limit, args.slug)
    if not rows:
        print("No polluted rows found.")
        return 0

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from creditdoc_db import CreditDocDB  # type: ignore

    now = datetime.now(timezone.utc)
    report_lines = [
        f"# Description Scrub — {'APPLY' if args.apply else 'DRY-RUN'}",
        f"Generated: {now.strftime('%Y-%m-%d %H:%M UTC')}",
        f"Rows scanned: {len(rows)}",
        "",
    ]
    skipped_too_short = 0
    skipped_no_drops = 0
    written = 0
    db = CreditDocDB() if args.apply else None
    for i, e in enumerate(rows, 1):
        if e["is_protected"]:
            report_lines.append(f"- `{e['slug']}`: SKIP (protected)")
            continue
        cleaned, dropped = scrub_description(e["desc_long"])
        if not dropped:
            skipped_no_drops += 1
            continue
        if len(cleaned) < 200:
            skipped_too_short += 1
            report_lines.append(f"- `{e['slug']}`: SKIP (cleaned={len(cleaned)} chars < 200)")
            continue
        action = "DRY-RUN" if args.dry_run else "WRITE"
        print(f"  [{i:>4}/{len(rows)}] {e['slug']}: dropped {len(dropped)} sentence(s) ({action})")
        if args.apply:
            db.update_lender(
                e["slug"],
                {"description_long": cleaned},
                updated_by="meta_commentary_scrub",
                reason=f"scrubbed {len(dropped)} meta-commentary sentence(s)",
                force=True,
            )
            written += 1
    if db:
        db.close()

    out = ROOT / "reports" / f"description_scrub_{('apply' if args.apply else 'dry')}_{now:%Y-%m-%dT%H-%M-%SZ}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    report_lines.append("")
    report_lines.append(f"Written to DB: {written}")
    report_lines.append(f"Skipped (no drops): {skipped_no_drops}")
    report_lines.append(f"Skipped (too short after scrub): {skipped_too_short}")
    out.write_text("\n".join(report_lines))
    print(f"\nReport: {out}")
    print(f"  written: {written} | skipped_no_drops: {skipped_no_drops} | skipped_too_short: {skipped_too_short}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
