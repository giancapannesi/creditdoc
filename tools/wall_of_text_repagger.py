#!/usr/bin/env python3
"""
Wall-of-text repagger.

Scans description_long for profiles that render as one big block because:
  - No explicit \n\n breaks
  - <= 3 sentences (autoParagraphs guard bypasses split)
  - >= 200 chars (short enough to be one block, long enough to look bad)

Splits into paragraphs at sentence boundaries:
  - 2 sentences  -> s1 / s2
  - 3 sentences  -> s1 / s2 s3
  (Profiles with 1 sentence are skipped — not a wall, just a short blurb.)

Uses the NUL-sentinel abbreviation splitter from ebay_tier3_scrub for accuracy.
Dry-run by default. --apply writes via CreditDocDB(force=True).
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

ABBREVIATIONS = [
    "U.S.A.", "U.S.", "U.K.", "e.g.", "i.e.", "etc.", "vs.", "Mr.", "Mrs.", "Ms.",
    "Dr.", "Jr.", "Sr.", "Inc.", "Ltd.", "Co.", "Corp.", "St.", "Ave.", "Blvd.",
    "Rd.", "No.", "a.m.", "p.m.", "A.M.", "P.M.",
]
NUL = "\x00"

SENT_COUNT_RE = re.compile(r"[^.!?]+[.!?]+(?:\s+|$)")  # mirrors inline-linker.ts

MIN_CHARS = 200
MAX_SENTENCES_FOR_WALL = 3


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


def repage(text: str) -> str | None:
    """Return repaginated text, or None if not applicable."""
    if not text or "\n\n" in text:
        return None
    if len(text.strip()) < MIN_CHARS:
        return None

    # Mirror the runtime guard: count sentences the same way inline-linker does.
    runtime_sents = SENT_COUNT_RE.findall(text)
    if not runtime_sents or len(runtime_sents) > MAX_SENTENCES_FOR_WALL:
        return None

    # Now split properly (abbrev-safe) for the rewrite.
    sents = split_sentences(text)
    if len(sents) < 2:
        return None
    if len(sents) == 2:
        return f"{sents[0]}\n\n{sents[1]}"
    # 3 sentences -> s1 / s2+s3 (keeps balance, breaks the wall)
    return f"{sents[0]}\n\n{' '.join(sents[1:])}"


def scan(conn: sqlite3.Connection) -> list[dict]:
    cur = conn.cursor()
    cur.execute(
        "SELECT slug, is_protected, data FROM lenders WHERE processing_status != 'archived'"
    )
    results: list[dict] = []
    for slug, protected, data_json in cur.fetchall():
        data = json.loads(data_json)
        desc = data.get("description_long") or ""
        new = repage(desc)
        if new is None:
            continue
        results.append({
            "slug": slug,
            "is_protected": bool(protected),
            "orig_len": len(desc),
            "new_len": len(new),
            "orig": desc,
            "new": new,
        })
    return results


def render_diff(results: list[dict], show_samples: int = 5) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Wall-of-Text Repagger — Diff",
        "",
        f"Generated: {now}",
        f"Rows: {len(results)}",
        f"Protected (will skip): {sum(1 for r in results if r['is_protected'])}",
        "",
        "## Samples",
        "",
    ]
    for r in results[:show_samples]:
        lines.append(f"### `{r['slug']}`  ({r['orig_len']} → {r['new_len']}c)")
        lines.append("")
        lines.append("**Before:**")
        lines.append("```")
        lines.append(r["orig"])
        lines.append("```")
        lines.append("")
        lines.append("**After:**")
        lines.append("```")
        lines.append(r["new"])
        lines.append("```")
        lines.append("")
    lines.append("## All Affected Slugs")
    lines.append("")
    for r in results:
        mark = " (PROTECTED — will skip)" if r["is_protected"] else ""
        lines.append(f"- `{r['slug']}`{mark}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--samples", type=int, default=5)
    args = ap.parse_args()
    if not (args.dry_run or args.apply):
        ap.error("pass --dry-run or --apply")

    conn = sqlite3.connect(DB_PATH)
    results = scan(conn)
    conn.close()

    now = datetime.now(timezone.utc)
    tag = "apply" if args.apply else "dry"
    report = render_diff(results, show_samples=args.samples)
    out = ROOT / "reports" / f"wall_of_text_repagger_{tag}_{now:%Y-%m-%dT%H-%M-%SZ}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report)
    print(f"Report: {out}")
    print(f"  rows: {len(results)} | protected: {sum(1 for r in results if r['is_protected'])}")

    if not args.apply:
        return 0

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from creditdoc_db import CreditDocDB  # type: ignore

    db = CreditDocDB()
    written = 0
    skipped_protected = 0
    for r in results:
        if r["is_protected"]:
            skipped_protected += 1
            continue
        db.update_lender(
            r["slug"],
            {"description_long": r["new"]},
            updated_by="wall_of_text_repagger",
            reason="split 3-sentence block into paragraphs (runtime autoParagraphs bypassed)",
            force=True,
        )
        written += 1
    db.close()
    print(f"Written: {written} | skipped_protected: {skipped_protected}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
