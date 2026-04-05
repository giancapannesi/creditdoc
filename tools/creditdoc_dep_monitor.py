#!/usr/bin/env python3
"""
creditdoc_dep_monitor.py — External dependency health check.

Pings fallback APIs and key services. Sends Telegram alert if any fail.
Not critical-path (logos are local), but early warning for fallback chain.

Cron: 0 6 * * * /srv/BusinessOps/.venv/bin/python3 /srv/BusinessOps/creditdoc/tools/creditdoc_dep_monitor.py

Usage:
    python3 tools/creditdoc_dep_monitor.py           # check all
    python3 tools/creditdoc_dep_monitor.py --verbose  # detailed output
"""

import argparse
import os
import sys
import time

try:
    import requests
except ImportError:
    os.system(f"{sys.executable} -m pip install requests -q")
    import requests

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT = os.environ.get("TELEGRAM_CHAT_ID", "")

# Endpoints to check
CHECKS = [
    {
        "name": "Google Favicon API (faviconV2)",
        "url": "https://t1.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://google.com&size=128",
        "expect_status": 200,
        "critical": False,
    },
    {
        "name": "icon.horse (fallback favicon)",
        "url": "https://icon.horse/icon/google.com",
        "expect_status": 200,
        "critical": False,
    },
    {
        "name": "CreditDoc site",
        "url": "https://creditdoc.co/",
        "expect_status": 200,
        "critical": True,
    },
    {
        "name": "Vercel Geo API",
        "url": "https://creditdoc.co/api/geo",
        "expect_status": 200,
        "critical": False,
    },
]


def send_telegram(msg):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT, "text": msg, "parse_mode": "HTML"},
            timeout=10,
        )
    except Exception:
        pass


def check_endpoint(check, verbose=False):
    """Check a single endpoint. Returns (ok, message)."""
    name = check["name"]
    try:
        start = time.time()
        r = requests.get(check["url"], timeout=15, allow_redirects=True)
        elapsed = time.time() - start

        if r.status_code == check["expect_status"]:
            msg = f"OK ({r.status_code}, {elapsed:.1f}s)"
            if verbose:
                print(f"  ✓ {name}: {msg}")
            return True, msg
        else:
            msg = f"BAD STATUS {r.status_code} (expected {check['expect_status']}, {elapsed:.1f}s)"
            print(f"  ✗ {name}: {msg}")
            return False, msg
    except requests.exceptions.Timeout:
        msg = "TIMEOUT (>15s)"
        print(f"  ✗ {name}: {msg}")
        return False, msg
    except requests.exceptions.ConnectionError as e:
        msg = f"CONNECTION ERROR: {str(e)[:80]}"
        print(f"  ✗ {name}: {msg}")
        return False, msg
    except Exception as e:
        msg = f"ERROR: {str(e)[:80]}"
        print(f"  ✗ {name}: {msg}")
        return False, msg


def main():
    parser = argparse.ArgumentParser(description="CreditDoc dependency health check")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    print("CreditDoc Dependency Monitor")
    print("=" * 40)

    failures = []
    for check in CHECKS:
        ok, msg = check_endpoint(check, verbose=args.verbose)
        if not ok:
            failures.append((check, msg))

    print(f"\n{'=' * 40}")
    if failures:
        critical = [f for f in failures if f[0]["critical"]]
        print(f"FAILURES: {len(failures)} ({len(critical)} critical)")
        alert = "⚠️ <b>CreditDoc Dep Monitor</b>\n\n"
        for check, msg in failures:
            prefix = "🔴" if check["critical"] else "🟡"
            alert += f"{prefix} {check['name']}: {msg}\n"
        send_telegram(alert)
        sys.exit(2 if critical else 1)
    else:
        print("All endpoints healthy")
        sys.exit(0)


if __name__ == "__main__":
    main()
