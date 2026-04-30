#!/usr/bin/env python3
"""
CDM-REV deploy-recovery watcher.

Polls the SSR probe URL every 60s. When `x-cdm-version` first appears in
the response headers (= CF Pages has built one of the queued commits and
SSR is live), fires the Phase 5.5b live e2e probe and emails Harvey the
verdict so Jammi gets results in his inbox without waiting for the next
/loop wakeup.

Use:
    # Foreground, 4h max:
    python3 tools/cdm_rev_deploy_watcher.py
    # Custom probe URL + max runtime:
    python3 tools/cdm_rev_deploy_watcher.py --probe-url https://... --max-hours 2
    # Don't run --apply probe, just notify (safer):
    python3 tools/cdm_rev_deploy_watcher.py --notify-only

Why this exists:
    Jammi said "we need to be concluding testing this evening" but deploy
    is gated on Jammi clicking Retry in CF dash. When he clicks, deploy
    builds for ~3 min, then I want results in his inbox in <60s — not
    25min later when /loop next wakes.

Exit codes:
    0 — deploy detected, e2e probe ran, email sent
    1 — bad args
    2 — max runtime elapsed without deploy recovery
    3 — deploy detected but e2e probe failed (still emails the failure)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROBE_URL = (
    "https://cdm-rev-hybrid.creditdoc.pages.dev/"
    "answers/are-small-business-loans-worth-it/"
)
HARVEY_EMAIL_TOOL = "/srv/BusinessOps/tools/harvey_email.py"
NOTIFY_TO = "gian.eao@gmail.com"
LOG_FILE = REPO_ROOT / "data" / "cdm_rev_deploy_watcher.log"


def log(msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a") as f:
        f.write(line + "\n")


UA = "cdm-rev-deploy-watcher/1.0 (curl-compat)"


def probe_headers(url: str, timeout: int = 10) -> dict[str, str]:
    """GET the URL (don't read body), return lowercase-key headers dict.
    CF Pages 403s the default Python UA so we set a custom one. Returns
    empty dict on error — caller checks for x-cdm-version presence."""
    req = Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urlopen(req, timeout=timeout) as resp:
            return {k.lower(): v for k, v in resp.headers.items()}
    except HTTPError as e:
        # 403 / 404 still tell us deploy state — capture x-cdm-version if any.
        return {k.lower(): v for k, v in (e.headers.items() if e.headers else [])}
    except (URLError, TimeoutError, OSError):
        return {}


def is_deploy_live(headers: dict[str, str]) -> bool:
    """Deploy is live when x-cdm-version header appears (set by middleware
    or lib/cache.ts cacheWrap on SSR-served routes)."""
    return bool(headers.get("x-cdm-version"))


def run_e2e_probe(notify_only: bool) -> tuple[bool, str, str | None]:
    """Run Phase 5.5b probe. Returns (success, summary_text, json_path)."""
    if notify_only:
        return True, "Notify-only mode — e2e probe NOT run.", None

    cmd = [
        "python3",
        str(REPO_ROOT / "tools" / "cdm_rev_phase24_e2e_probe.py"),
        "--route", "all",
        "--apply",
        "--trials", "10",
    ]
    log(f"running probe: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd, cwd=REPO_ROOT, timeout=900, capture_output=True, text=True
        )
        ok = result.returncode == 0
        # Probe writes JSON to data/cdm_rev_phase24_probe_latest.json by convention.
        json_path = REPO_ROOT / "data" / "cdm_rev_phase24_probe_latest.json"
        json_existed = json_path.exists()
        summary = (
            f"exit={result.returncode}\n\n"
            f"--- stdout (last 80 lines) ---\n"
            + "\n".join(result.stdout.splitlines()[-80:])
            + "\n\n--- stderr ---\n"
            + result.stderr[-2000:]
        )
        return ok, summary, str(json_path) if json_existed else None
    except subprocess.TimeoutExpired:
        return False, "e2e probe timed out (>15min)", None
    except Exception as e:
        return False, f"e2e probe crashed: {e!r}", None


def send_harvey_email(subject: str, body: str) -> bool:
    """Send via harvey_email.py CLI. Returns True on send."""
    cmd = [
        "python3", HARVEY_EMAIL_TOOL,
        "send",
        "--to", NOTIFY_TO,
        "--subject", subject,
        "--body", body,
    ]
    try:
        result = subprocess.run(cmd, timeout=60, capture_output=True, text=True)
        if result.returncode == 0:
            log(f"harvey email sent: {subject!r}")
            return True
        log(f"harvey email FAILED rc={result.returncode}: {result.stderr[:300]}")
        return False
    except Exception as e:
        log(f"harvey email crashed: {e!r}")
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe-url", default=DEFAULT_PROBE_URL)
    ap.add_argument("--poll-seconds", type=int, default=60)
    ap.add_argument("--max-hours", type=float, default=4.0)
    ap.add_argument("--notify-only", action="store_true",
                    help="Don't run --apply e2e probe; only email that deploy is back.")
    args = ap.parse_args()

    deadline = time.time() + args.max_hours * 3600
    poll_count = 0
    log(
        f"watcher start url={args.probe_url} poll={args.poll_seconds}s "
        f"max_hours={args.max_hours} notify_only={args.notify_only}"
    )

    while time.time() < deadline:
        poll_count += 1
        headers = probe_headers(args.probe_url)
        version = headers.get("x-cdm-version", "")
        status_line = headers.get("status", "?")
        log(
            f"poll #{poll_count}: x-cdm-version={version!r} "
            f"cache-control={headers.get('cache-control', '?')[:60]}"
        )
        if is_deploy_live(headers):
            log(f"DEPLOY RECOVERED — x-cdm-version={version!r}")
            ok, summary, json_path = run_e2e_probe(args.notify_only)
            verdict = "PASS" if ok else "FAIL"
            subject = f"[CDM-REV] Deploy recovered + e2e probe {verdict}"
            body_lines = [
                f"CF Pages deploy is BACK as of {datetime.now(timezone.utc).isoformat(timespec='seconds')}.",
                f"x-cdm-version: {version}",
                f"Probe URL: {args.probe_url}",
                "",
                "Phase 5.5b e2e probe result (10 trials × 3 routes):",
                f"  Verdict: {verdict}",
                "",
                "Probe output summary:",
                summary,
            ]
            if json_path:
                body_lines.append(f"\nFull JSON report: {json_path}")
            send_harvey_email(subject, "\n".join(body_lines))
            return 0 if ok else 3
        time.sleep(args.poll_seconds)

    log(f"watcher TIMEOUT after {args.max_hours}h — deploy never recovered")
    send_harvey_email(
        "[CDM-REV] Deploy watcher timed out — still broken",
        f"Polled {args.probe_url} every {args.poll_seconds}s for "
        f"{args.max_hours}h. Never saw x-cdm-version header. "
        "Deploy is still broken. Check CF dash.",
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
