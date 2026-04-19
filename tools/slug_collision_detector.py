#!/usr/bin/env python3
import argparse
import csv
import json
import sqlite3
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent if SCRIPT_DIR.name == "tools" else SCRIPT_DIR
DB_PATH = PROJECT_DIR / "data" / "creditdoc.db"
REPORTS_DIR = PROJECT_DIR / "reports"


def _jaro(s1, s2):
    if s1 == s2:
        return 1.0
    l1, l2 = len(s1), len(s2)
    if l1 == 0 or l2 == 0:
        return 0.0
    match_dist = max(l1, l2) // 2 - 1
    match_dist = max(0, match_dist)
    s1_matches = [False] * l1
    s2_matches = [False] * l2
    matches = 0
    transpositions = 0
    for i in range(l1):
        lo = max(0, i - match_dist)
        hi = min(i + match_dist + 1, l2)
        for j in range(lo, hi):
            if s2_matches[j] or s1[i] != s2[j]:
                continue
            s1_matches[i] = True
            s2_matches[j] = True
            matches += 1
            break
    if matches == 0:
        return 0.0
    k = 0
    for i in range(l1):
        if not s1_matches[i]:
            continue
        while not s2_matches[k]:
            k += 1
        if s1[i] != s2[k]:
            transpositions += 1
        k += 1
    return (matches / l1 + matches / l2 + (matches - transpositions / 2) / matches) / 3


def _jaro_winkler(s1, s2, p=0.1):
    j = _jaro(s1, s2)
    prefix = 0
    for c1, c2 in zip(s1[:4], s2[:4]):
        if c1 == c2:
            prefix += 1
        else:
            break
    return j + prefix * p * (1 - j)


def load_lenders(db_path, limit=None):
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    sql = (
        "SELECT slug, category, processing_status, data "
        "FROM lenders WHERE processing_status = 'ready_for_index'"
    )
    if limit:
        sql += f" LIMIT {int(limit)}"
    rows = conn.execute(sql).fetchall()
    conn.close()
    lenders = []
    for r in rows:
        try:
            d = json.loads(r["data"])
        except Exception:
            continue
        lenders.append({
            "slug": r["slug"],
            "category": r["category"] or "",
            "name": (d.get("name") or "").strip(),
            "city": (d.get("city") or "").strip(),
            "state": (d.get("state") or "").strip(),
        })
    return lenders


def detect_collisions(lenders):
    name_dup_slug_diff = []
    slug_prefix = []
    chain_dup_pairs = []

    by_category = defaultdict(list)
    for L in lenders:
        by_category[L["category"]].append(L)

    for cat, group in by_category.items():
        by_prefix = defaultdict(list)
        for L in group:
            key = L["name"].lower()[:3]
            by_prefix[key].append(L)

        for key, bucket in by_prefix.items():
            n = len(bucket)
            for i in range(n):
                for j in range(i + 1, n):
                    a, b = bucket[i], bucket[j]
                    sim_name = _jaro_winkler(a["name"].lower(), b["name"].lower())
                    sim_slug = _jaro_winkler(a["slug"], b["slug"])
                    if sim_name >= 0.85 and sim_slug <= 0.60:
                        name_dup_slug_diff.append((a, b, sim_name, sim_slug))

        n = len(group)
        for i in range(n):
            for j in range(i + 1, n):
                a, b = group[i], group[j]
                if b["slug"].startswith(a["slug"] + "-") or a["slug"].startswith(b["slug"] + "-"):
                    slug_prefix.append((a, b))

    by_name = defaultdict(list)
    for L in lenders:
        key = L["name"].lower().strip()
        if key:
            by_name[key].append(L)

    for name_key, members in by_name.items():
        if len(members) < 2:
            continue
        cities = {m["city"] for m in members}
        if len(cities) < 2:
            continue
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                a, b = members[i], members[j]
                if a["city"] != b["city"]:
                    chain_dup_pairs.append((a, b))

    return name_dup_slug_diff, slug_prefix, chain_dup_pairs, by_name


def chain_group_sizes(by_name):
    groups = []
    for name_key, members in by_name.items():
        if len(members) < 2:
            continue
        cities = {m["city"] for m in members}
        if len(cities) < 2:
            continue
        groups.append((name_key, len(members)))
    return sorted(groups, key=lambda x: -x[1])


def write_csv(output_path, name_dup_slug_diff, slug_prefix, chain_dup_pairs):
    FIELDS = [
        "reason", "slug_a", "name_a", "category_a", "city_a", "state_a",
        "slug_b", "name_b", "category_b", "city_b", "state_b",
        "similarity_name", "similarity_slug",
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for a, b, sim_name, sim_slug in name_dup_slug_diff:
            w.writerow({
                "reason": "NAME_DUP_SLUG_DIFF",
                "slug_a": a["slug"], "name_a": a["name"],
                "category_a": a["category"], "city_a": a["city"], "state_a": a["state"],
                "slug_b": b["slug"], "name_b": b["name"],
                "category_b": b["category"], "city_b": b["city"], "state_b": b["state"],
                "similarity_name": f"{sim_name:.4f}", "similarity_slug": f"{sim_slug:.4f}",
            })
        for a, b in slug_prefix:
            sim_name = _jaro_winkler(a["name"].lower(), b["name"].lower())
            sim_slug = _jaro_winkler(a["slug"], b["slug"])
            w.writerow({
                "reason": "SLUG_PREFIX",
                "slug_a": a["slug"], "name_a": a["name"],
                "category_a": a["category"], "city_a": a["city"], "state_a": a["state"],
                "slug_b": b["slug"], "name_b": b["name"],
                "category_b": b["category"], "city_b": b["city"], "state_b": b["state"],
                "similarity_name": f"{sim_name:.4f}", "similarity_slug": f"{sim_slug:.4f}",
            })
        for a, b in chain_dup_pairs:
            w.writerow({
                "reason": "CHAIN_DUP",
                "slug_a": a["slug"], "name_a": a["name"],
                "category_a": a["category"], "city_a": a["city"], "state_a": a["state"],
                "slug_b": b["slug"], "name_b": b["name"],
                "category_b": b["category"], "city_b": b["city"], "state_b": b["state"],
                "similarity_name": "1.0000", "similarity_slug": "",
            })


def main():
    parser = argparse.ArgumentParser(description="Detect slug collisions in CreditDoc lender DB.")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    today = date.today().isoformat()
    output_path = Path(args.output) if args.output else REPORTS_DIR / f"slug_collisions_{today}.csv"

    print(f"Loading lenders from {DB_PATH} ...")
    lenders = load_lenders(DB_PATH, limit=args.limit)
    print(f"Loaded {len(lenders)} lenders (ready_for_index).")

    print("Detecting collisions ...")
    name_dup_slug_diff, slug_prefix, chain_dup_pairs, by_name = detect_collisions(lenders)

    chain_pairs_unique = list({
        (min(a["slug"], b["slug"]), max(a["slug"], b["slug"])): (a, b)
        for a, b in chain_dup_pairs
    }.values())

    chain_groups = [
        (name_key, cnt) for name_key, cnt in chain_group_sizes(by_name)
    ]
    n_chain_groups = len(chain_groups)

    write_csv(output_path, name_dup_slug_diff, slug_prefix, chain_pairs_unique)

    csv_size = output_path.stat().st_size if output_path.exists() else 0
    total_pairs = len(name_dup_slug_diff) + len(slug_prefix) + len(chain_pairs_unique)

    print(f"\nTotal lenders scanned: {len(lenders)}")
    print(f"Pairs flagged:")
    print(f"  NAME_DUP_SLUG_DIFF: {len(name_dup_slug_diff)}")
    print(f"  SLUG_PREFIX: {len(slug_prefix)}")
    print(f"  CHAIN_DUP: {len(chain_pairs_unique)} ({n_chain_groups} chain groups)")
    print(f"Report written to: {output_path}  ({csv_size:,} bytes)")
    print(f"Next step: Jammi reviews CSV and decides per-row action.")

    if chain_groups:
        print(f"\nTop chain duplicate groups:")
        for name_key, cnt in chain_groups[:5]:
            print(f"  '{name_key}': {cnt} locations")


if __name__ == "__main__":
    main()
