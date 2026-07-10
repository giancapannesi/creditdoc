#!/usr/bin/env python3
"""CreditDoc Bing recovery lane.

Uses Bing Webmaster Tools direct URL submission for the highest-value static
SEO pages. IndexNow remains useful, but this gives us a measurable 100/day Bing
API path after the April canonical/SSR transition coincided with lost Bing
impressions.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path("/srv/BusinessOps/creditdoc")
DIST = ROOT / "dist"
STATE_FILE = Path("/srv/BusinessOps/data/creditdoc_bing_direct_submission_state.json")
REPORT_DIR = ROOT / "reports" / "bing-recovery"
SITE = "https://www.creditdoc.co"
BING_SITE = "https://creditdoc.co/"
DEFAULT_LIMIT = 100
COOLDOWN_DAYS = 14

sys.path.insert(0, "/srv/BusinessOps/tools")
from bing_webmaster import api_post  # noqa: E402


PRIORITY_PREFIXES = (
    ("tools", 10),
    ("courses", 20),
    ("answers", 30),
    ("financial-wellness", 40),
    ("best", 50),
    ("research", 60),
    ("resources", 70),
    ("blog", 80),
    ("state", 90),
)


PINNED_PATHS = (
    "/answers/how-to-check-if-a-lender-is-licensed/",
    "/answers/where-to-complain-about-a-lender/",
    "/answers/how-to-file-a-cfpb-complaint/",
    "/answers/what-does-a-cfpb-complaint-mean/",
    "/answers/how-to-check-a-credit-repair-company/",
    "/about/creditdoc-data/",
    "/editorial-policy/",
    "/methodology/",
    "/research/consumer-complaints/",
    "/research/lending-transparency/",
    "/tools/sba-guarantee-fee-calculator/",
    "/tools/commercial-loan-calculator/",
    "/tools/business-line-of-credit-calculator/",
    "/tools/equipment-financing-calculator/",
    "/tools/loan-denial-reason-checker/",
    "/tools/credit-score-simulator/",
    "/courses/credit-fundamentals/",
    "/financial-wellness/credit-repair-rights-fcra-croa/",
    "/financial-wellness/debt-validation-letters/",
    "/financial-wellness/how-credit-repair-works/",
)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {"submitted": {}}
    try:
        data = json.loads(STATE_FILE.read_text())
    except Exception:
        return {"submitted": {}}
    if not isinstance(data, dict):
        return {"submitted": {}}
    data.setdefault("submitted", {})
    return data


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    state["updated"] = now_utc().isoformat()
    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")


def route_from_html(path: Path) -> str | None:
    rel = path.relative_to(DIST)
    if rel.name != "index.html":
        return None
    parent = rel.parent.as_posix()
    if parent == ".":
        return "/"
    return "/" + parent.strip("/") + "/"


def priority_for(route: str) -> tuple[int, str]:
    if route in PINNED_PATHS:
        return (0, route)
    first = route.strip("/").split("/", 1)[0]
    for prefix, score in PRIORITY_PREFIXES:
        if first == prefix:
            return (score, route)
    return (999, route)


def collect_candidate_routes() -> list[str]:
    routes = set(PINNED_PATHS)
    for html in DIST.glob("**/index.html"):
        route = route_from_html(html)
        if not route:
            continue
        first = route.strip("/").split("/", 1)[0]
        if first in {prefix for prefix, _ in PRIORITY_PREFIXES}:
            routes.add(route)
    return sorted(routes, key=priority_for)


def is_recently_submitted(route: str, state: dict, cooldown_days: int) -> bool:
    raw = state.get("submitted", {}).get(route)
    if not raw:
        return False
    try:
        submitted_at = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return False
    return submitted_at >= now_utc() - timedelta(days=cooldown_days)


def live_ok(url: str) -> tuple[bool, str]:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "CreditDoc-Bing-Recovery/1.0"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read(4096).decode("utf-8", errors="ignore").lower()
            status = getattr(resp, "status", resp.getcode())
            final_url = resp.geturl()
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}"
    except Exception as e:
        return False, str(e)[:120]
    if status != 200:
        return False, f"HTTP {status}"
    if "page not found" in body or "<title>not found" in body or "404" in body[:1000]:
        return False, "body looks like 404"
    if not final_url.startswith(SITE):
        return False, f"unexpected final URL {final_url}"
    return True, "200"


def select_urls(limit: int, cooldown_days: int) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    state = load_state()
    selected = []
    skipped = []
    for route in collect_candidate_routes():
        if len(selected) >= limit:
            break
        if is_recently_submitted(route, state, cooldown_days):
            skipped.append((route, "cooldown"))
            continue
        url = f"{SITE}{route}"
        ok, note = live_ok(url)
        if ok:
            selected.append((route, url))
        else:
            skipped.append((route, note))
        time.sleep(0.05)
    return selected, skipped


def submit_to_bing(urls: list[str]) -> bool:
    result = api_post("SubmitUrlBatch", {"siteUrl": BING_SITE, "urlList": urls})
    return result is not None


def write_report(selected: list[tuple[str, str]], skipped: list[tuple[str, str]], submitted: bool) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORT_DIR / f"bing_recovery_{now_utc().strftime('%Y-%m-%d')}.md"
    lines = [
        f"# CreditDoc Bing Recovery - {now_utc().strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        f"Submitted: {'yes' if submitted else 'no'}",
        f"Selected URLs: {len(selected)}",
        f"Skipped during selection: {len(skipped)}",
        "",
        "## Selected",
    ]
    lines.extend(f"- {url}" for _, url in selected)
    lines.extend(["", "## Skipped Sample"])
    lines.extend(f"- {route}: {note}" for route, note in skipped[:50])
    path.write_text("\n".join(lines) + "\n")
    return path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Submit selected URLs to Bing")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--cooldown-days", type=int, default=COOLDOWN_DAYS)
    args = parser.parse_args()

    selected, skipped = select_urls(args.limit, args.cooldown_days)
    urls = [url for _, url in selected]

    print(f"CreditDoc Bing recovery - selected {len(urls)} URLs")
    for _, url in selected[:20]:
        print(f"  + {url}")
    if len(selected) > 20:
        print(f"  ... and {len(selected) - 20} more")

    submitted = False
    if args.apply and urls:
        submitted = submit_to_bing(urls)
        if submitted:
            state = load_state()
            stamp = now_utc().isoformat()
            for route, _ in selected:
                state["submitted"][route] = stamp
            save_state(state)
            print(f"Bing submitted: {len(urls)} URLs")
        else:
            print("Bing submission failed")
            sys.exit(1)
    else:
        print("Dry run only; pass --apply to submit")

    report = write_report(selected, skipped, submitted)
    print(f"Report: {report}")


if __name__ == "__main__":
    main()
