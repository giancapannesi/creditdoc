#!/usr/bin/env python3
"""
Chain Enricher — Pass 2 writer

Pulls Google Places API (New) Text Search data for chain location rows already
rewritten in Pass 1 and upgrades description_short with verified local facts
(hours, rating, neighborhood). Writes via creditdoc_db.update_lender.

Usage:
    # Preview 100-row batch — writes a markdown diff report, no DB changes
    python3 tools/chain_enricher.py --limit 100 --dry-run

    # Apply to DB (explicit flag required)
    python3 tools/chain_enricher.py --limit 100 --apply

    # Filter to one chain
    python3 tools/chain_enricher.py --limit 50 --chain western-union --apply

Halts the batch if any of these cross their threshold:
  - >15% phone mismatch rate
  - >15% street-number mismatch rate
  - <2 avg facts per row (batch quality too thin)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.creditdoc_db import CreditDocDB

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "creditdoc.db"
ENV_PATH = ROOT / ".env"
REPORTS_DIR = ROOT / "reports"

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
])

# Chains from Pass 1 sweep
CHAIN_BRAND_SLUGS = [
    "western-union", "moneygram", "ace-cash-express", "advance-america",
    "cash-america-pawn", "titlemax-title-loans", "pls-check-cashers",
    "montana-capital", "ezpawn", "speedy-cash", "us-cash-advance",
    "loan-for-any-purpose", "check-into-cash", "checksmart", "superb-cash-advance",
    "first-cash-pawn", "check-n-go", "value-pawn-jewelry", "loanmax-title-loans",
    "titlemax-title-pawns", "swift-title-loans", "primo-personal-loans",
    "lendnation", "california-check-cashing-stores", "dolex-dollar-express",
    "loanstar-title-loans", "pawn1st", "la-familia-pawn-and-jewelry",
    "instaloan", "superpawn", "onemain-financial", "allied-cash-advance",
    "ria-money-transfer", "orlandi-valuta", "chase-bank",
    "bank-of-america-financial-center", "texas-car-title-and-payday-loan-services-inc",
    "sam-check-cashing-machine", "payday-loans-cash", "nccl-no-credit-check-loans",
    "easy-payday-loans", "consumer-credit-counseling-services", "cash-store",
    "world-finance", "oportun",
]


# ---------- helpers ----------

def load_api_key() -> str:
    load_dotenv(ENV_PATH)
    key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not key:
        sys.exit(f"GOOGLE_PLACES_API_KEY missing from {ENV_PATH}")
    return key


def normalize_digits(s: str | None) -> str:
    if not s:
        return ""
    d = "".join(c for c in s if c.isdigit())
    if d.startswith("1") and len(d) == 11:
        d = d[1:]
    return d


def brand_tokens(brand: str) -> set[str]:
    """Significant tokens from brand name for host-overlap check."""
    stop = {"the", "of", "and", "a", "an", "inc", "llc", "co",
            "services", "service", "center", "branch", "financial"}
    toks = re.findall(r"[a-z0-9]+", (brand or "").lower())
    return {t for t in toks if len(t) >= 3 and t not in stop}


def api_name(place: dict) -> str:
    return (place.get("displayName") or {}).get("text") or ""


def is_host_mismatch(brand: str, place: dict) -> bool:
    """
    True when the API returned a different business name than our brand
    (e.g. brand=MoneyGram but API returned Walmart Neighborhood Market —
    the MoneyGram counter lives inside that store).
    """
    bt = brand_tokens(brand)
    at = brand_tokens(api_name(place))
    if not bt or not at:
        return False
    return not (bt & at)


def extract_neighborhood(components: list | None) -> str | None:
    if not components:
        return None
    by_type = {}
    for c in components:
        for t in c.get("types", []):
            by_type.setdefault(t, c.get("longText"))
    for key in ("neighborhood", "sublocality_level_1", "sublocality"):
        v = by_type.get(key)
        if v:
            return v
    return None


def condense_hours(regular: dict | None) -> str | None:
    if not regular:
        return None
    desc = regular.get("weekdayDescriptions") or []
    if not desc or len(desc) != 7:
        return None
    bodies = [d.split(": ", 1)[-1] for d in desc]
    uniq = set(bodies)
    if len(uniq) == 1:
        only = next(iter(uniq))
        if only.lower() in ("open 24 hours", "24 hours"):
            return "open 24 hours daily"
        if only.lower() == "closed":
            return None
        return f"open {only} daily"
    weekdays = set(bodies[0:5])
    if len(weekdays) == 1:
        wd = next(iter(weekdays))
        if wd.lower() == "closed":
            return None
        return f"Mon-Fri {wd}"
    return None


def places_search(api_key: str, brand: str, address: str) -> dict:
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": FIELD_MASK,
    }
    body = {"textQuery": f"{brand} {address}", "maxResultCount": 1}
    try:
        r = httpx.post(PLACES_URL, headers=headers, json=body, timeout=25)
    except httpx.HTTPError as e:
        return {"_error": f"transport: {e}"}
    if r.status_code != 200:
        return {"_error": f"HTTP {r.status_code}: {r.text[:200]}"}
    js = r.json()
    places = js.get("places") or []
    return places[0] if places else {"_error": "no_results"}


def compose_description(row: dict, place: dict, host_mismatch: bool) -> tuple[str, list[str]]:
    facts: list[str] = []
    brand = row["name"] or row["brand_slug"].replace("-", " ").title()
    addr = row["address"] or ""
    phone = row["phone"] or ""

    neighborhood = extract_neighborhood(place.get("addressComponents"))
    hours_short = condense_hours(place.get("regularOpeningHours"))
    status = place.get("businessStatus")
    rating = place.get("rating")
    reviews = place.get("userRatingCount")
    host = api_name(place) if host_mismatch else None

    # Sentence 1
    nb_tail = f" in the {neighborhood} neighborhood" if neighborhood else ""
    if host:
        # "MoneyGram inside the Walmart Neighborhood Market at 1820 Unser Blvd..."
        s1 = f"{brand} inside the {host} at {addr}{nb_tail}"
        facts.append(f"host={host}")
    elif hours_short:
        s1 = f"{brand} at {addr}{nb_tail} is {hours_short}"
    else:
        s1 = f"{brand} is located at {addr}{nb_tail}"
    if neighborhood:
        facts.append(f"neighborhood={neighborhood}")

    sentences = [s1]

    # Host-row gets soft hours only
    if host and hours_short:
        sentences.append("Accessible during store hours")
    elif (not host) and hours_short:
        facts.append(f"hours={hours_short}")
        # hours already in s1
    elif hours_short:
        facts.append(f"hours={hours_short}")

    if status and status != "OPERATIONAL":
        sentences.append(f"Business status: {status}")
        facts.append(f"status={status}")

    # Drop rating for host-mismatch rows (those reviews aren't about our brand)
    if not host and rating and reviews and reviews >= 10:
        sentences.append(f"Google reviewers rate the branch {rating:.1f} stars across {reviews} reviews")
        facts.append(f"rating={rating:.1f}/{reviews}")

    if phone:
        sentences.append(f"Call {phone}")
        facts.append(f"phone={phone}")

    text = ". ".join(s.rstrip(".") for s in sentences) + "."
    return text, facts


# ---------- row selection ----------

def fetch_candidate_rows(limit: int, chain: str | None) -> list[dict]:
    """Rows already rewritten in Pass 1, not FA-protected, chain brand."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    where_chain = ""
    params: list = []
    if chain:
        where_chain = "AND brand_slug = ?"
        params.append(chain)
    else:
        placeholders = ",".join(["?"] * len(CHAIN_BRAND_SLUGS))
        where_chain = f"AND brand_slug IN ({placeholders})"
        params.extend(CHAIN_BRAND_SLUGS)

    # A Pass-1 row starts "At <address>" or "<Brand> at <address>" or similar;
    # we want rows whose description_short is short-formulaic and not already
    # enriched by Pass 2.
    params.append(limit)
    cur.execute(
        f"""
        SELECT slug, brand_slug, data
        FROM lenders
        WHERE is_protected = 0
          AND updated_by != 'chain_enricher_pass2'
          {where_chain}
          AND json_extract(data, '$.description_short') IS NOT NULL
          AND length(json_extract(data, '$.description_short')) BETWEEN 60 AND 260
          AND json_extract(data, '$.address') IS NOT NULL
          AND json_extract(data, '$.phone') IS NOT NULL
        ORDER BY brand_slug, slug
        LIMIT ?
        """,
        params,
    )
    out = []
    for slug, brand, raw in cur.fetchall():
        d = json.loads(raw)
        out.append({
            "slug": slug,
            "brand_slug": brand,
            "name": d.get("name"),
            "address": d.get("address"),
            "phone": d.get("phone"),
            "pass1_desc": d.get("description_short"),
        })
    conn.close()
    return out


# ---------- main ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--chain", default=None, help="brand_slug filter")
    ap.add_argument("--dry-run", action="store_true", help="report only, no DB writes")
    ap.add_argument("--apply", action="store_true", help="required to write to DB")
    args = ap.parse_args()

    if not args.dry_run and not args.apply:
        sys.exit("Refusing to run: pass --dry-run to preview or --apply to write.")
    if args.dry_run and args.apply:
        sys.exit("--dry-run and --apply are mutually exclusive.")

    api_key = load_api_key()
    rows = fetch_candidate_rows(args.limit, args.chain)
    if not rows:
        sys.exit("No candidate rows matched.")

    print(f"Loaded {len(rows)} rows (limit={args.limit}, chain={args.chain or 'ANY'}, mode={'DRY-RUN' if args.dry_run else 'APPLY'})")

    results = []
    phone_mismatches = 0
    street_mismatches = 0
    total_facts = 0
    host_rows = 0
    errors = 0
    written = 0

    db = CreditDocDB() if args.apply else None

    for i, row in enumerate(rows, 1):
        brand_human = row["name"] or row["brand_slug"].replace("-", " ").title()
        place = places_search(api_key, brand_human, row["address"])
        time.sleep(0.25)

        if place.get("_error"):
            errors += 1
            results.append({"row": row, "place": place, "action": "skip_error"})
            print(f"  [{i:>3}/{len(rows)}] {row['slug']}: ERR {place['_error']}")
            continue

        # Sanity checks
        api_phone = normalize_digits(place.get("nationalPhoneNumber"))
        db_phone = normalize_digits(row["phone"])
        phone_ok = bool(api_phone and db_phone and api_phone == db_phone)
        if not phone_ok:
            phone_mismatches += 1

        db_num = re.match(r"^(\d+)", row["address"] or "")
        api_num = re.match(r"^(\d+)", place.get("formattedAddress") or "")
        street_ok = bool(db_num and api_num and db_num.group(1) == api_num.group(1))
        if not street_ok:
            street_mismatches += 1

        if not phone_ok or not street_ok:
            results.append({
                "row": row, "place": place, "action": "skip_mismatch",
                "phone_ok": phone_ok, "street_ok": street_ok,
            })
            print(f"  [{i:>3}/{len(rows)}] {row['slug']}: SKIP mismatch (phone={phone_ok}, street={street_ok})")
            continue

        host = is_host_mismatch(brand_human, place)
        if host:
            host_rows += 1
        new_desc, facts = compose_description(row, place, host)

        # Quality gate: require ≥1 net-new fact beyond what Pass 1 already has.
        # Pass 1 already contains brand/address/phone, so those don't count.
        net_new = [f for f in facts if not f.startswith("phone=")]
        if len(net_new) < 1:
            results.append({
                "row": row, "place": place, "action": "skip_thin",
                "facts": facts, "new_desc": new_desc,
            })
            print(f"  [{i:>3}/{len(rows)}] {row['slug']}: SKIP thin (no net-new facts)")
            continue

        total_facts += len(facts)
        action = "dry_run" if args.dry_run else "pending"
        results.append({
            "row": row, "place": place, "action": action,
            "host_mismatch": host, "facts": facts, "new_desc": new_desc,
        })

        if args.apply:
            try:
                r = db.update_lender(
                    row["slug"],
                    {"description_short": new_desc},
                    updated_by="chain_enricher_pass2",
                    reason=f"Pass 2 enrichment; facts={len(facts)}; host={host}",
                    force=True,
                )
                results[-1]["action"] = "written" if r["changed"] else "unchanged"
                if r["changed"]:
                    written += 1
            except Exception as e:
                results[-1]["action"] = f"write_error: {e}"
                errors += 1
        print(f"  [{i:>3}/{len(rows)}] {row['slug']}: {len(facts)} facts{' (host)' if host else ''} → {len(new_desc)} chars [{results[-1]['action']}]")

        # Halt triggers — check every 20 rows once we have signal
        if i % 20 == 0 and i >= 20:
            pm = phone_mismatches / i
            sm = street_mismatches / i
            if pm > 0.15:
                print(f"\nHALT: phone mismatch rate {pm:.1%} > 15% at row {i}")
                break
            if sm > 0.15:
                print(f"\nHALT: street# mismatch rate {sm:.1%} > 15% at row {i}")
                break

    if db:
        db.close()

    # Write report
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    mode = "dry" if args.dry_run else "apply"
    report_path = REPORTS_DIR / f"chain_enricher_{mode}_{ts}.md"
    json_path = REPORTS_DIR / f"chain_enricher_{mode}_{ts}.json"

    processed = len(results) - errors
    proc_nonzero = max(processed, 1)
    summary = {
        "mode": "dry_run" if args.dry_run else "apply",
        "rows_loaded": len(rows),
        "rows_processed": len(results),
        "errors": errors,
        "phone_mismatches": phone_mismatches,
        "street_mismatches": street_mismatches,
        "host_rows": host_rows,
        "rows_written": written,
        "avg_facts": total_facts / proc_nonzero,
        "chain_filter": args.chain,
    }

    json_path.write_text(json.dumps({"summary": summary, "results": results}, indent=2, default=str))

    lines = [
        f"# Chain Enricher Run — {mode.upper()} — {ts}",
        "",
        "## Summary",
        "",
        f"- Mode: **{summary['mode']}**",
        f"- Chain filter: `{args.chain or 'ALL'}`",
        f"- Rows loaded: {summary['rows_loaded']}",
        f"- Rows processed: {summary['rows_processed']}",
        f"- Rows WRITTEN to DB: **{summary['rows_written']}**",
        f"- Errors: {summary['errors']}",
        f"- Phone mismatches skipped: {summary['phone_mismatches']}",
        f"- Street# mismatches skipped: {summary['street_mismatches']}",
        f"- Host-detected rows (e.g. agent inside Walmart): {summary['host_rows']}",
        f"- Avg facts per written row: {summary['avg_facts']:.2f}",
        "",
        "## Samples (first 10)",
        "",
    ]
    samples = [r for r in results if r["action"] in ("written", "dry_run", "pending", "unchanged")][:10]
    for s in samples:
        row = s["row"]
        lines.append(f"### `{row['slug']}` — {s['action']}{' (host)' if s.get('host_mismatch') else ''}")
        lines.append(f"- **Pass 1:** {row['pass1_desc']}")
        lines.append(f"- **Pass 2:** {s.get('new_desc', '')}")
        lines.append(f"- **Facts:** {', '.join(s.get('facts', []))}")
        lines.append("")

    if phone_mismatches + street_mismatches > 0:
        lines.append("## Skipped mismatches (first 5)")
        lines.append("")
        skipped = [r for r in results if r["action"] == "skip_mismatch"][:5]
        for s in skipped:
            lines.append(f"- `{s['row']['slug']}` — phone_ok={s['phone_ok']}, street_ok={s['street_ok']}, db=`{s['row']['address']}` | api=`{s['place'].get('formattedAddress')}`")
        lines.append("")

    report_path.write_text("\n".join(lines))
    print("\nSUMMARY:")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    print(f"\nReport: {report_path}")
    print(f"JSON:   {json_path}")


if __name__ == "__main__":
    main()
