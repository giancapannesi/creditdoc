#!/usr/bin/env python3
"""
Revalidate stale hard website_status warnings on CreditDoc lender records.

This job is intentionally guarded for multi-agent work:
- skips while build/deploy/git processes are active
- skips while the repo has had recent file activity
- only changes known false/misleading warning records
- does not build or deploy
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path("/srv/BusinessOps/creditdoc")
LENDERS = ROOT / "src/content/lenders"
REPORT_DIR = ROOT / "reports/website-status"
LOCK = Path("/tmp/creditdoc_website_status_revalidator.lock")

FALSE_WARNING_SLUGS = {
    "morgan-cash": "live verified; stale parked flag",
    "cnic-employees-credit-union": "live verified; stale dead flag",
    "credit-done-right": "live verified; stale dead flag",
    "jcb-international-credit-card": "live verified; stale parked flag",
    "my-credit-repair-in-columbus-oh": "live verified; stale dead flag",
    "securcommunity-federal-credit-union": "live verified; stale parked flag",
    "plan-b-credit-repair-texas": "HTTP site reachable; SSL warning too strong for public inactive warning",
    "optimal-debt-relief-debt-consolidation-settlement": "under construction, not parked/for-sale",
}

ACTIVE_PROCESS_PATTERNS = (
    "astro build",
    "npm run build",
    "wrangler deploy",
    "deploy.sh",
    "git commit",
    "git rebase",
    "git merge",
)


def run(cmd: list[str], cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False)


def log(message: str) -> None:
    print(f"[website-status] {message}")


def acquire_lock() -> object:
    import fcntl

    LOCK.parent.mkdir(parents=True, exist_ok=True)
    lock_f = LOCK.open("w")
    try:
        fcntl.flock(lock_f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        log("skip: another website-status revalidator is running")
        sys.exit(0)
    return lock_f


def active_processes() -> list[str]:
    proc = run(["ps", "-eo", "pid=,args="], cwd=ROOT)
    if proc.returncode != 0:
        return ["ps check failed"]
    matches: list[str] = []
    own_pid = os.getpid()
    for line in proc.stdout.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split(maxsplit=1)
        try:
            pid = int(parts[0])
        except (ValueError, IndexError):
            continue
        if pid == own_pid:
            continue
        args = parts[1] if len(parts) > 1 else ""
        if any(pattern in args for pattern in ACTIVE_PROCESS_PATTERNS):
            matches.append(stripped)
    return matches


def repo_recently_touched(seconds: int) -> bool:
    now = time.time()
    paths = [ROOT / "src", ROOT / "scripts", ROOT / "tools", ROOT / "package.json", ROOT / "astro.config.mjs"]
    newest = 0.0
    for base in paths:
        if not base.exists():
            continue
        if base.is_file():
            newest = max(newest, base.stat().st_mtime)
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in {".git", "node_modules", "dist", "__pycache__"}]
            for filename in filenames:
                try:
                    newest = max(newest, (Path(dirpath) / filename).stat().st_mtime)
                except OSError:
                    continue
    return newest > 0 and (now - newest) < seconds


def current_hard_warnings() -> dict[str, dict]:
    warnings: dict[str, dict] = {}
    for path in sorted(LENDERS.glob("*.json")):
        try:
            data = json.loads(path.read_text())
        except Exception:
            continue
        if data.get("website_status"):
            warnings[data.get("slug") or path.stem] = {
                "path": path,
                "name": data.get("name", ""),
                "status": data.get("website_status", ""),
                "checked": data.get("website_status_checked", ""),
                "url": data.get("website_url") or data.get("website") or "",
            }
    return warnings


def fetch_summary(url: str) -> tuple[str, str, str]:
    if not url:
        return "missing-url", "", ""
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 CreditDoc website-status revalidator"})
    try:
        with urlopen(req, timeout=15) as response:
            body = response.read(256_000).decode("utf-8", "ignore")
            final_url = response.geturl()
            code = str(response.status)
    except HTTPError as exc:
        body = exc.read(128_000).decode("utf-8", "ignore")
        final_url = exc.geturl()
        code = str(exc.code)
    except URLError as exc:
        return "error", "", str(exc.reason)
    except Exception as exc:
        return "error", "", str(exc)

    title = ""
    match = re.search(r"<title[^>]*>(.*?)</title>", body, flags=re.I | re.S)
    if match:
        title = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", match.group(1))).strip()[:120]
    return code, final_url, title


def clear_status_in_db(slug: str, checked_date: str, reason: str) -> bool:
    """Wipe website_status in the DB (source of truth) so the guardian
    DB→JSON sync can't re-corrupt the file. Writing JSON directly here was
    the 2026-07-18 bug: revalidator stripped JSON, guardian restored it
    from the still-bad DB row within 5 min.
    """
    sys.path.insert(0, str(ROOT))
    from tools.creditdoc_db import CreditDocDB
    with CreditDocDB() as db:
        res = db.update_lender(
            slug,
            {"website_status": None, "website_status_checked": checked_date},
            updated_by="founder",
            reason=f"revalidator: {reason}",
        )
        return res["changed"] > 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Apply known stale warning corrections.")
    parser.add_argument("--quiet-seconds", type=int, default=1800)
    parser.add_argument("--force", action="store_true", help="Bypass quiet/process guards for manual use.")
    args = parser.parse_args()

    acquire_lock()
    os.chdir(ROOT)

    if not args.force:
        active = active_processes()
        if active:
            log("skip: active build/deploy/git process detected")
            for line in active[:8]:
                log(f"  {line}")
            return 0
        if repo_recently_touched(args.quiet_seconds):
            log(f"skip: repo files touched inside quiet window ({args.quiet_seconds}s)")
            return 0

    warnings = current_hard_warnings()
    today = date.today().isoformat()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / f"website_status_revalidation_{datetime.now(timezone.utc).strftime('%Y-%m-%d_%H%M%S')}.json"

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "apply": args.apply,
        "known_false_warning_slugs": sorted(FALSE_WARNING_SLUGS),
        "before_warning_count": len(warnings),
        "checked": [],
        "changed": [],
        "remaining_warning_count": None,
    }

    for slug in sorted(FALSE_WARNING_SLUGS):
        info = warnings.get(slug)
        if not info:
            report["checked"].append({"slug": slug, "present": False, "reason": "no current hard website_status"})
            continue
        code, final_url, title = fetch_summary(info["url"])
        row = {
            "slug": slug,
            "name": info["name"],
            "old_status": info["status"],
            "old_checked": info["checked"],
            "url": info["url"],
            "http_code": code,
            "final_url": final_url,
            "title": title,
            "correction_reason": FALSE_WARNING_SLUGS[slug],
        }
        report["checked"].append(row)
        if args.apply:
            changed = clear_status_in_db(slug, today, FALSE_WARNING_SLUGS[slug])
            if changed:
                report["changed"].append({"slug": slug, "checked": today, "layer": "db"})

    report["remaining_warning_count"] = len(current_hard_warnings())
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    log(f"report: {report_path}")
    log(f"changed: {len(report['changed'])}")
    log(f"remaining hard warning count: {report['remaining_warning_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
