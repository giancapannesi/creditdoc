#!/usr/bin/env python3
"""
Chain Enricher — PILOT (no DB writes)

Pulls Google Places API (New) Text Search data for 10 representative chain rows
already rewritten in Pass 1, composes a proposed Pass 2 description_short, and
writes a markdown diff report for founder review.

READ ONLY: does not touch creditdoc.db. Jammi green-lights before any writer
gets built.

Run: python3 tools/chain_enricher_pilot.py
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "creditdoc.db"
REPORT_PATH = ROOT / "reports" / f"chain_enricher_pilot_{datetime.now(timezone.utc):%Y-%m-%d}.md"
ENV_PATH = ROOT / ".env"

PILOT_SLUGS = [
    "ace-cash-express-alhambra",
    "advance-america-bakersfield-ca",
    "bank-of-america-financial-center-atlanta",
    "cash-america-pawn-apopka",
    "chase-bank-brooklyn-ny",
    "check-into-cash-bullhead-city",
    "ezpawn-austin",
    "moneygram-albuquerque-nm",
    "titlemax-title-loans-arlington-tx",
    "western-union-albuquerque-nm",
]

PLACES_URL = "https://places.googleapis.com/v1/places:searchText"
FIELD_MASK = ",".join([
    "places.displayName",
    "places.formattedAddress",
    "places.nationalPhoneNumber",
    "places.regularOpeningHours",
    "places.rating",
    "places.userRatingCount",
    "places.businessStatus",
    "places.location",
    "places.addressComponents",
    "places.primaryTypeDisplayName",
    "places.types",
])


def load_api_key() -> str:
    load_dotenv(ENV_PATH)
    key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not key:
        sys.exit(f"GOOGLE_PLACES_API_KEY missing from {ENV_PATH}")
    return key


def fetch_row(cur: sqlite3.Cursor, slug: str) -> dict:
    cur.execute(
        "SELECT slug, brand_slug, data FROM lenders WHERE slug = ?",
        (slug,),
    )
    r = cur.fetchone()
    if not r:
        return {}
    data = json.loads(r[2])
    return {
        "slug": r[0],
        "brand_slug": r[1],
        "name": data.get("name"),
        "address": data.get("address"),
        "phone": data.get("phone"),
        "pass1_desc": data.get("description_short"),
    }


def places_search(api_key: str, brand: str, address: str) -> dict:
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": FIELD_MASK,
    }
    body = {"textQuery": f"{brand} {address}", "maxResultCount": 1}
    r = httpx.post(PLACES_URL, headers=headers, json=body, timeout=20)
    if r.status_code != 200:
        return {"_error": f"HTTP {r.status_code}: {r.text[:300]}"}
    js = r.json()
    places = js.get("places") or []
    if not places:
        return {"_error": "no_results"}
    return places[0]


def extract_neighborhood(address_components: list) -> str | None:
    if not address_components:
        return None
    # Prefer neighborhood > sublocality > sublocality_level_1
    by_type = {}
    for comp in address_components:
        for t in comp.get("types", []):
            by_type.setdefault(t, comp.get("longText"))
    for key in ("neighborhood", "sublocality_level_1", "sublocality"):
        if by_type.get(key):
            return by_type[key]
    return None


def format_hours(regular: dict | None) -> str | None:
    if not regular:
        return None
    desc = regular.get("weekdayDescriptions") or []
    if not desc:
        return None
    # collapse identical days: "Mon-Fri 9am-5pm, Sat 10am-2pm, Sun closed"
    return " | ".join(desc)


def condense_hours(regular: dict | None) -> str | None:
    """Short inline hours phrase (e.g. 'Open 24 hours' or 'Mon-Fri 9am-7pm')."""
    if not regular:
        return None
    if regular.get("openNow") is None and not regular.get("periods"):
        return None
    desc = regular.get("weekdayDescriptions") or []
    if not desc:
        return None
    # Check if all 7 days are the same string → collapse
    uniq = {d.split(": ", 1)[-1] for d in desc}
    if len(uniq) == 1:
        only = next(iter(uniq))
        if only.lower() in ("open 24 hours", "24 hours"):
            return "open 24 hours daily"
        return f"open {only} daily"
    # weekday vs weekend grouping
    weekdays = {desc[i].split(": ", 1)[-1] for i in range(5)}
    weekend = {desc[5].split(": ", 1)[-1], desc[6].split(": ", 1)[-1]}
    if len(weekdays) == 1:
        wd = next(iter(weekdays))
        return f"Mon-Fri {wd}" if wd.lower() != "closed" else "weekdays closed"
    return None  # too irregular — omit from short desc, keep in full report


def propose_desc(row: dict, place: dict) -> tuple[str, list[str]]:
    """
    Compose a 300-400 char enriched description_short. Returns (text, facts_used).
    Only uses VERIFIED facts from Places API + the existing DB address/phone.
    """
    facts = []
    brand = row["name"] or row["brand_slug"].replace("-", " ").title()
    addr = row["address"] or ""
    phone = row["phone"] or ""

    # Sentence 1: location + optional neighborhood
    neighborhood = extract_neighborhood(place.get("addressComponents") or [])
    hours_short = condense_hours(place.get("regularOpeningHours"))
    status = place.get("businessStatus")
    rating = place.get("rating")
    reviews = place.get("userRatingCount")

    s1_tail = ""
    if neighborhood:
        s1_tail = f" in the {neighborhood} neighborhood"
        facts.append(f"neighborhood={neighborhood}")
    if hours_short:
        facts.append(f"hours={hours_short}")
        s1 = f"{brand} at {addr}{s1_tail} is {hours_short}"
    else:
        s1 = f"{brand} is located at {addr}{s1_tail}"

    sentences = [s1]

    if status and status != "OPERATIONAL":
        sentences.append(f"Business status: {status}")
        facts.append(f"status={status}")

    if rating and reviews and reviews >= 10:
        sentences.append(
            f"Google reviewers rate the branch {rating:.1f} stars across {reviews} reviews"
        )
        facts.append(f"rating={rating:.1f}/{reviews}")

    if phone:
        sentences.append(f"Call {phone}")
        facts.append(f"phone={phone}")

    text = ". ".join(s.rstrip(".") for s in sentences) + "."
    return text, facts


def render_report(entries: list[dict]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Chain Pass-2 Enrichment — Pilot Diff Report (10 rows)",
        "",
        f"**Generated:** {now}",
        f"**Source:** Google Places API (New) Text Search",
        f"**DB writes:** NONE — review-only pilot",
        "",
        "## Summary",
        "",
        f"- Rows queried: {len(entries)}",
        f"- Places found: {sum(1 for e in entries if not e['place'].get('_error'))}",
        f"- Errors: {sum(1 for e in entries if e['place'].get('_error'))}",
        f"- Avg facts per row: {sum(len(e['facts']) for e in entries) / max(len(entries), 1):.1f}",
        "",
        "## Per-row diff",
        "",
    ]
    for i, e in enumerate(entries, 1):
        row = e["row"]
        place = e["place"]
        facts = e["facts"]
        proposed = e["proposed"]
        lines.append(f"### {i}. `{row['slug']}`")
        lines.append("")
        lines.append(f"- **Brand:** {row['brand_slug']}")
        lines.append(f"- **DB address:** {row['address']}")
        lines.append(f"- **DB phone:** {row['phone']}")
        lines.append("")
        lines.append("**Pass 1 (current on creditdoc.co):**")
        lines.append(f"> {row['pass1_desc']}")
        lines.append("")
        if place.get("_error"):
            lines.append(f"**Places API error:** `{place['_error']}`")
            lines.append("")
            lines.append("**Proposed Pass 2:** (unchanged — no verified facts)")
            lines.append("")
            continue
        lines.append("**Places API raw (compact):**")
        lines.append("```json")
        compact = {
            "displayName": (place.get("displayName") or {}).get("text"),
            "formattedAddress": place.get("formattedAddress"),
            "nationalPhoneNumber": place.get("nationalPhoneNumber"),
            "businessStatus": place.get("businessStatus"),
            "rating": place.get("rating"),
            "userRatingCount": place.get("userRatingCount"),
            "primaryTypeDisplayName": (place.get("primaryTypeDisplayName") or {}).get("text"),
            "regularOpeningHours_weekdayDescriptions":
                (place.get("regularOpeningHours") or {}).get("weekdayDescriptions"),
            "location": place.get("location"),
            "neighborhood": extract_neighborhood(place.get("addressComponents") or []),
        }
        lines.append(json.dumps(compact, indent=2))
        lines.append("```")
        lines.append("")
        lines.append(f"**Facts usable ({len(facts)}):** {', '.join(facts) if facts else '(none)'}")
        lines.append("")
        lines.append(f"**Proposed Pass 2 ({len(proposed)} chars):**")
        lines.append(f"> {proposed}")
        lines.append("")
        # sanity checks
        checks = []
        if row["phone"] and place.get("nationalPhoneNumber"):
            # strip non-digits
            db_digits = "".join(c for c in row["phone"] if c.isdigit())
            api_digits = "".join(c for c in place["nationalPhoneNumber"] if c.isdigit())
            # strip leading 1 from db
            if db_digits.startswith("1") and len(db_digits) == 11:
                db_digits = db_digits[1:]
            checks.append(f"phone match: {'✓' if db_digits == api_digits else '✗ ' + db_digits + ' vs ' + api_digits}")
        if row["address"] and place.get("formattedAddress"):
            # loose check: street number present in both
            import re
            db_num = re.match(r"^(\d+)", row["address"])
            api_num = re.match(r"^(\d+)", place["formattedAddress"])
            if db_num and api_num:
                checks.append(f"street# match: {'✓' if db_num.group(1) == api_num.group(1) else '✗'}")
        if checks:
            lines.append(f"**Sanity checks:** {' | '.join(checks)}")
            lines.append("")
        lines.append("---")
        lines.append("")
    lines.append("## What this pilot does NOT do")
    lines.append("")
    lines.append("- No DB writes")
    lines.append("- No JSON rewrites")
    lines.append("- No commits")
    lines.append("- No deploys")
    lines.append("")
    lines.append("## If Jammi approves")
    lines.append("")
    lines.append("Next step: batch-100 writer with DB update via `creditdoc_db.update_lender(force=True, updated_by='chain_enricher_pass2')`, ")
    lines.append("check-in after every 100, halt on >15% phone mismatch / street# mismatch / <2 facts per row.")
    lines.append("")
    return "\n".join(lines)


def main():
    api_key = load_api_key()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    entries = []
    for slug in PILOT_SLUGS:
        row = fetch_row(cur, slug)
        if not row:
            print(f"SKIP {slug}: not in DB", file=sys.stderr)
            continue
        brand_human = row["name"] or row["brand_slug"].replace("-", " ").title()
        place = places_search(api_key, brand_human, row["address"])
        time.sleep(0.3)  # gentle
        if place.get("_error"):
            proposed = row["pass1_desc"]
            facts = []
        else:
            proposed, facts = propose_desc(row, place)
        entries.append({"row": row, "place": place, "facts": facts, "proposed": proposed})
        print(f"OK  {slug}: {'ERR ' + place['_error'] if place.get('_error') else f'{len(facts)} facts → {len(proposed)} chars'}")

    conn.close()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(render_report(entries))
    print(f"\nReport written: {REPORT_PATH}")


if __name__ == "__main__":
    main()
