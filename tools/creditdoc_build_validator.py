#!/usr/bin/env python3
"""
creditdoc_build_validator.py — Post-build validator for CreditDoc.

Runs after `npm run build`, before `git push`. Catches problems before deploy.

Checks:
  1. Broken local logos — logo_url starts with /logos/ but file missing
  2. Unresolved template literals — ${...} in built HTML (build-time failure)
  3. Page count sanity — visible lenders vs built review pages
  4. Sample page health — random pages have <h1>, schema, logo element

Exit codes:
  0 = all pass
  1 = warnings only
  2 = critical failures (block push)

Usage:
    python3 tools/creditdoc_build_validator.py          # run all checks
    python3 tools/creditdoc_build_validator.py --verbose # detailed output
"""

import argparse
import json
import os
import random
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LENDER_DIR = PROJECT_ROOT / "src" / "content" / "lenders"
LOGO_DIR = PROJECT_ROOT / "public" / "logos"
DIST_DIR = PROJECT_ROOT / "dist"
DIST_REVIEW = DIST_DIR / "review"

# Telegram alert (optional)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT = os.environ.get("TELEGRAM_CHAT_ID", "")


def send_telegram(msg):
    """Send critical alert via Telegram."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT:
        return
    try:
        import requests
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT, "text": msg, "parse_mode": "HTML"},
            timeout=10,
        )
    except Exception:
        pass


class Validator:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.warnings = []
        self.criticals = []

    def warn(self, msg):
        self.warnings.append(msg)
        if self.verbose:
            print(f"  WARN: {msg}")

    def critical(self, msg):
        self.criticals.append(msg)
        print(f"  CRITICAL: {msg}")

    def check_broken_logos(self):
        """For every lender with logo_url=/logos/*, verify file exists."""
        print("\n[1/4] Checking local logo references...")
        broken = 0
        checked = 0

        for f in LENDER_DIR.glob("*.json"):
            try:
                data = json.loads(f.read_text())
            except Exception:
                continue

            logo = data.get("logo_url", "")
            if not logo.startswith("/logos/"):
                continue

            checked += 1
            logo_file = PROJECT_ROOT / "public" / logo.lstrip("/")
            if not logo_file.exists():
                broken += 1
                self.warn(f"Missing logo: {logo} (lender: {f.stem})")

        print(f"  Checked {checked} local logo refs, {broken} broken")
        if broken > 10:
            self.critical(f"{broken} broken local logo references")

    def check_unresolved_templates(self):
        """Grep built HTML for unresolved ${...} template literals."""
        print("\n[2/4] Checking for unresolved template literals...")

        if not DIST_REVIEW.exists():
            self.warn("dist/review/ not found — run `npm run build` first")
            return

        patterns = [
            r'\$\{new URL\(',
            r'\$\{lender\.',
            r'\$\{entry\.',
        ]

        found = 0
        sample_files = list(DIST_REVIEW.rglob("index.html"))

        # Check all or sample if too many
        check_files = sample_files if len(sample_files) < 500 else random.sample(sample_files, 500)

        for html_file in check_files:
            try:
                content = html_file.read_text(errors="ignore")
                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        found += len(matches)
                        rel = html_file.relative_to(DIST_DIR)
                        self.warn(f"Unresolved template in {rel}: {matches[0]}")
            except Exception:
                continue

        print(f"  Checked {len(check_files)} pages, {found} unresolved templates")
        if found > 0:
            self.critical(f"{found} unresolved template literals in built HTML")

    def check_page_count(self):
        """Compare visible lenders vs built review pages."""
        print("\n[3/4] Checking page count sanity...")

        # Count all lenders (Astro builds both visible and no_index pages)
        total_lenders = len(list(LENDER_DIR.glob("*.json")))
        visible = 0
        for f in LENDER_DIR.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                if not data.get("no_index"):
                    visible += 1
            except Exception:
                continue

        # Count built pages
        if not DIST_REVIEW.exists():
            self.warn("dist/review/ not found — run `npm run build` first")
            return

        built = len(list(DIST_REVIEW.iterdir()))

        # Compare built vs total lenders (Astro builds all, including no_index)
        diff_pct = abs(total_lenders - built) / max(total_lenders, 1) * 100
        print(f"  Total lenders:   {total_lenders}")
        print(f"  Visible:         {visible}")
        print(f"  Built pages:     {built}")
        print(f"  Diff (total):    {diff_pct:.1f}%")

        if diff_pct > 10:
            self.critical(f"Page count mismatch: {total_lenders} lenders vs {built} built ({diff_pct:.1f}% diff)")
        elif diff_pct > 5:
            self.warn(f"Page count drift: {total_lenders} lenders vs {built} built ({diff_pct:.1f}% diff)")

    def check_sample_health(self):
        """Spot-check 10 random review pages for basic health."""
        print("\n[4/4] Sample page health check...")

        if not DIST_REVIEW.exists():
            self.warn("dist/review/ not found — run `npm run build` first")
            return

        pages = list(DIST_REVIEW.rglob("index.html"))
        if not pages:
            self.critical("No review pages found in dist/")
            return

        samples = random.sample(pages, min(10, len(pages)))
        issues = 0

        for page in samples:
            slug = page.parent.name
            try:
                html = page.read_text(errors="ignore")
            except Exception:
                self.warn(f"Can't read {slug}")
                issues += 1
                continue

            checks = {
                "non-empty": len(html) > 1000,
                "has <h1>": "<h1" in html,
                "has schema": "application/ld+json" in html,
                "has logo/img": 'class="w-14 h-14' in html or "<img" in html[:5000],
            }

            failed = [k for k, v in checks.items() if not v]
            if failed:
                issues += 1
                self.warn(f"{slug}: missing {', '.join(failed)}")
            elif self.verbose:
                print(f"  OK: {slug}")

        print(f"  Checked {len(samples)} pages, {issues} with issues")
        if issues > len(samples) // 2:
            self.critical(f"Majority of sample pages have issues ({issues}/{len(samples)})")

    def run(self):
        """Run all checks and return exit code."""
        print("CreditDoc Post-Build Validator")
        print("=" * 50)

        self.check_broken_logos()
        self.check_unresolved_templates()
        self.check_page_count()
        self.check_sample_health()

        print("\n" + "=" * 50)
        print(f"Warnings:  {len(self.warnings)}")
        print(f"Criticals: {len(self.criticals)}")

        if self.criticals:
            print("\nRESULT: FAIL — do NOT push")
            msg = f"🚨 CreditDoc build validator FAILED\n\n"
            msg += "\n".join(f"• {c}" for c in self.criticals[:5])
            send_telegram(msg)
            return 2
        elif self.warnings:
            print("\nRESULT: PASS with warnings")
            return 1
        else:
            print("\nRESULT: PASS")
            return 0


def main():
    parser = argparse.ArgumentParser(description="CreditDoc post-build validator")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    validator = Validator(verbose=args.verbose)
    sys.exit(validator.run())


if __name__ == "__main__":
    main()
