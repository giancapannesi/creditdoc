#!/usr/bin/env python3
"""Weekly execution check for CreditDoc regulatory SEO plan."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports" / "regulatory-refresh"
PRIORITY_TOOLS = [
    "business-line-of-credit-calculator",
    "sba-loan-calculator",
    "business-loan-calculator",
    "commercial-loan-calculator",
    "credit-score-simulator",
    "debt-payoff-calculator",
]
REGULATORY_ANSWER_SLUGS = [
    "how-to-check-if-a-lender-is-licensed",
    "where-to-complain-about-a-lender",
    "how-to-file-a-cfpb-complaint",
    "what-does-a-cfpb-complaint-mean",
    "how-to-check-a-credit-repair-company",
]


def has_text(path: Path, needle: str) -> bool:
    return path.exists() and needle in path.read_text(errors="ignore")


def crontab_text() -> str:
    proc = subprocess.run(["crontab", "-l"], text=True, capture_output=True, check=False)
    return proc.stdout


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    rows: list[str] = []
    failures: list[str] = []

    component = ROOT / "src" / "components" / "RegulatoryResearchModule.astro"
    if component.exists():
        rows.append("- OK reusable regulatory module exists.")
    else:
        failures.append("Reusable regulatory module is missing.")

    best_template = ROOT / "src" / "pages" / "best" / "[slug].astro"
    if has_text(best_template, "RegulatoryResearchModule"):
        rows.append("- OK `/best/` template includes regulatory module.")
    else:
        failures.append("`/best/` template does not include regulatory module.")

    for slug in PRIORITY_TOOLS:
        page = ROOT / "src" / "pages" / "tools" / f"{slug}.astro"
        if has_text(page, "RegulatoryResearchModule"):
            rows.append(f"- OK `/tools/{slug}/` includes regulatory module.")
        else:
            failures.append(f"`/tools/{slug}/` missing regulatory module.")

    dist_best = ROOT / "dist" / "best" / "best-business-lines-of-credit" / "index.html"
    dist_tool = ROOT / "dist" / "tools" / "business-line-of-credit-calculator" / "index.html"
    if has_text(dist_best, "Check The Regulatory Context") or has_text(dist_best, "Use This Guide With Regulatory Research"):
        rows.append("- OK built `/best/` sample includes regulatory copy.")
    else:
        rows.append("- WARN built `/best/` sample does not yet show regulatory copy; rebuild may be needed.")
    if has_text(dist_tool, "Check The Regulatory Context"):
        rows.append("- OK built priority tool sample includes regulatory copy.")
    else:
        rows.append("- WARN built priority tool sample does not yet show regulatory copy; rebuild may be needed.")

    answers_dir = ROOT / "src" / "content" / "answers"
    existing_answers = [slug for slug in REGULATORY_ANSWER_SLUGS if (answers_dir / f"{slug}.json").exists()]
    rows.append(f"- Regulatory answer cluster present: {len(existing_answers)}/{len(REGULATORY_ANSWER_SLUGS)}.")
    if len(existing_answers) < len(REGULATORY_ANSWER_SLUGS):
        rows.append("- NEXT: create remaining regulatory-intent answer pages and add them to indexing priority.")

    cron = crontab_text()
    for marker in [
        "creditdoc-regulatory-link-drift",
        "creditdoc-regulatory-full-refresh",
        "creditdoc-regulatory-seo-execution",
        "creditdoc-regulatory-next-phase",
    ]:
        if marker in cron:
            rows.append(f"- OK cron marker present: `{marker}`.")
        else:
            failures.append(f"Cron marker missing: `{marker}`.")

    status = "PASS" if not failures else "WARN"
    out = REPORT_DIR / f"regulatory_seo_execution_{now.strftime('%Y-%m-%d')}.md"
    lines = [
        f"# CreditDoc Regulatory SEO Execution Check - {now.strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        f"- Status: {status}",
        f"- Failures: {len(failures)}",
        "",
        "## Checks",
        "",
        *rows,
    ]
    if failures:
        lines.extend(["", "## Missing", ""])
        lines.extend(f"- {failure}" for failure in failures)
    out.write_text("\n".join(lines) + "\n")
    print(f"CreditDoc regulatory SEO execution check: status={status} report={out}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
