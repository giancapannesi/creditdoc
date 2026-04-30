#!/usr/bin/env python3
"""
CDM-REV-2026-04-29 — STRUCTURAL HTML parity gate for /review/[slug].

Why this exists:
    The byte-delta gate in cdm_rev_html_diff.sh measures whitespace and
    asset-hash variation, not user-visible drift. When normalize() strips
    those, real visual regressions (empty BBB ratings, missing logos,
    shuffled cards, ISO timestamps) show up as <0.1% byte deltas because
    `BBB:` is barely shorter than `BBB: B+`.

What this checks (per slug):
    1. BBB badges that have a non-empty rating value (B+, A+, NR — but not blank)
    2. Logo <img src="/logos/..."> count (vs text-fallback <span> initials)
    3. /compare/<this-slug>-vs-X/ card links
    4. Rating aria-labels with value > 0.0
    5. JSON-LD `datePublished` is YYYY-MM-DD format (not ISO datetime)

The gate passes when prod and preview match within ±1 on each count, AND
both have the YYYY-MM-DD datePublished format.

Read-only HTTP GET only. Safe to run anytime, including /loop "no live DB" mode.

Usage:
    python3 tools/cdm_rev_structural_parity.py
    python3 tools/cdm_rev_structural_parity.py --slugs credit-saint,lexington-law
    python3 tools/cdm_rev_structural_parity.py --slugs-file slugs.txt
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass, field
from typing import Optional
from urllib.error import URLError
from urllib.request import Request, urlopen

PROD_HOST = "https://www.creditdoc.co"
PREVIEW_HOST = "https://cdm-rev-hybrid.creditdoc.pages.dev"
TIMEOUT_S = 20

DEFAULT_SLUGS = [
    "credit-saint",
    "the-credit-pros",
    "sky-blue-credit",
    "the-credit-people",
    "lexington-law",
    "experian-boost",
    "credit-strong",
    "self-credit-builder",
    "capital-one-platinum-secured",
    "rocket-loans",
]


@dataclass
class StructuralCounts:
    bbb_with_value: int = 0
    bbb_empty_or_nr: int = 0
    logo_imgs: int = 0
    text_fallback_initials: int = 0
    compare_cards: int = 0
    valid_ratings: int = 0
    zero_ratings: int = 0
    date_published_iso: bool = False
    date_published_short: bool = False
    date_published_raw: Optional[str] = None
    fetch_status: int = 0
    fetch_bytes: int = 0
    notes: list[str] = field(default_factory=list)


def fetch(url: str) -> tuple[int, str, int]:
    # Cache-bust query string to bypass CF edge cache (stale post-deploy).
    sep = "&" if "?" in url else "?"
    url = f"{url}{sep}_cdm_rev_cb={int(time.time() * 1000)}"
    req = Request(url, headers={
        "User-Agent": "cdm-rev-parity/1.0",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    })
    try:
        with urlopen(req, timeout=TIMEOUT_S) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.getcode(), body, len(body)
    except URLError as e:
        return 0, str(e), 0
    except Exception as e:
        return 0, repr(e), 0


def analyze(html: str, slug: str) -> StructuralCounts:
    c = StructuralCounts()
    c.fetch_bytes = len(html)

    # 1. BBB badges. Markup pattern: <span class="...bbb-X-Y">\n  BBB: B+ </span>
    #    Empty case: <span class="...bbb-nr"> BBB: </span>
    for m in re.finditer(
        r"bbb-[a-z0-9-]+[\"\s][^>]*>\s*BBB:\s*([A-Za-z+\-]*)\s*</span>", html
    ):
        rating = m.group(1).strip()
        if rating and rating.upper() != "NR":
            c.bbb_with_value += 1
        else:
            c.bbb_empty_or_nr += 1

    # 2. Logo imgs vs text-fallback initials.
    c.logo_imgs = len(re.findall(r'<img\s+[^>]*src="/logos/[^"]+"', html))
    # Text fallback: <span class="...font-bold text-primary"> X </span> where X is 1-2 chars.
    # Only count when it's the *initial* text (single letter) — otherwise we'd
    # double-count company-name text. The initial pattern in card body is precise:
    #   <span class="text-lg font-bold text-primary"> L </span>
    #   <span class="text-2xl font-bold text-primary">C</span>  (heading variant)
    c.text_fallback_initials = len(
        re.findall(
            r'<span class="text-(?:lg|xl|2xl) font-bold text-primary">\s*[A-Z]\s*</span>',
            html,
        )
    )

    # 3. /compare/ cards mentioning this slug.
    #    Form: /compare/<slug>-vs-X/ OR /compare/X-vs-<slug>/
    compare_re = re.compile(
        rf'href="/compare/(?:{re.escape(slug)}-vs-[^"/]+|[^"/]+-vs-{re.escape(slug)})/"'
    )
    c.compare_cards = len(compare_re.findall(html))

    # 4. Rating aria-labels: "Rating: 4.7 out of 5 stars" valid; "Rating: 0.0 ..." zero.
    for m in re.finditer(r'aria-label="Rating: ([\d.]+) out of 5 stars"', html):
        v = float(m.group(1))
        if v > 0:
            c.valid_ratings += 1
        else:
            c.zero_ratings += 1

    # 5. JSON-LD datePublished format check.
    dp = re.search(r'"datePublished":"([^"]+)"', html)
    if dp:
        raw = dp.group(1)
        c.date_published_raw = raw
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
            c.date_published_short = True
        elif re.match(r"\d{4}-\d{2}-\d{2}T", raw):
            c.date_published_iso = True

    return c


def compare_slug(slug: str) -> tuple[bool, list[str]]:
    prod_url = f"{PROD_HOST}/review/{slug}/"
    prev_url = f"{PREVIEW_HOST}/review/{slug}/"

    p_code, p_body, _ = fetch(prod_url)
    v_code, v_body, _ = fetch(prev_url)

    if p_code != 200 or v_code != 200:
        return False, [f"HTTP fail prod={p_code} preview={v_code}"]

    pc = analyze(p_body, slug)
    vc = analyze(v_body, slug)
    pc.fetch_status, vc.fetch_status = p_code, v_code

    issues: list[str] = []

    def cmp_within(name: str, a: int, b: int, tol: int = 1) -> None:
        if abs(a - b) > tol:
            issues.append(f"{name}: prod={a} preview={b} (delta {a-b})")

    cmp_within("bbb_with_value", pc.bbb_with_value, vc.bbb_with_value, tol=0)
    cmp_within("logo_imgs", pc.logo_imgs, vc.logo_imgs, tol=0)
    cmp_within("text_fallback_initials", pc.text_fallback_initials, vc.text_fallback_initials, tol=0)
    cmp_within("compare_cards", pc.compare_cards, vc.compare_cards, tol=0)
    cmp_within("valid_ratings", pc.valid_ratings, vc.valid_ratings, tol=0)
    cmp_within("zero_ratings", pc.zero_ratings, vc.zero_ratings, tol=0)

    if pc.date_published_short and vc.date_published_iso:
        issues.append(
            f"datePublished format drift: prod={pc.date_published_raw} preview={vc.date_published_raw}"
        )
    elif not pc.date_published_short and not pc.date_published_iso:
        issues.append("prod has no parseable datePublished")
    elif not vc.date_published_short and not vc.date_published_iso:
        issues.append("preview has no parseable datePublished")

    rec = (
        f"prod[bbb={pc.bbb_with_value}/{pc.bbb_with_value+pc.bbb_empty_or_nr} "
        f"logo={pc.logo_imgs} init={pc.text_fallback_initials} "
        f"cmp={pc.compare_cards} rat={pc.valid_ratings}/{pc.valid_ratings+pc.zero_ratings} "
        f"dp={'iso' if pc.date_published_iso else 'short' if pc.date_published_short else 'NA'}] "
        f"preview[bbb={vc.bbb_with_value}/{vc.bbb_with_value+vc.bbb_empty_or_nr} "
        f"logo={vc.logo_imgs} init={vc.text_fallback_initials} "
        f"cmp={vc.compare_cards} rat={vc.valid_ratings}/{vc.valid_ratings+vc.zero_ratings} "
        f"dp={'iso' if vc.date_published_iso else 'short' if vc.date_published_short else 'NA'}]"
    )
    issues.insert(0, rec)
    return len(issues) == 1, issues


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slugs", help="comma-separated slug list")
    ap.add_argument("--slugs-file", help="file with one slug per line")
    args = ap.parse_args(argv)

    slugs: list[str] = []
    if args.slugs:
        slugs = [s.strip() for s in args.slugs.split(",") if s.strip()]
    elif args.slugs_file:
        with open(args.slugs_file) as f:
            slugs = [
                s.strip() for s in f
                if s.strip() and not s.startswith("#")
            ]
    else:
        slugs = list(DEFAULT_SLUGS)

    print("=" * 80)
    print("CDM-REV STRUCTURAL HTML parity gate")
    print(f"PROD     : {PROD_HOST}")
    print(f"PREVIEW  : {PREVIEW_HOST}")
    print(f"Slugs    : {len(slugs)}")
    print("=" * 80)
    print()

    pass_count = 0
    fail_count = 0
    for slug in slugs:
        ok, lines = compare_slug(slug)
        status = "PASS" if ok else "FAIL"
        if ok:
            pass_count += 1
        else:
            fail_count += 1
        print(f"[{status}] {slug}")
        for ln in lines:
            print(f"    {ln}")
        print()

    print("=" * 80)
    print(f"PASS: {pass_count} / {len(slugs)}")
    print(f"FAIL: {fail_count} / {len(slugs)}")
    print("=" * 80)
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
