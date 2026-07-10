#!/usr/bin/env python3
"""Stateful scheduler for CreditDoc regulatory SEO next phases.

This runner is intentionally conservative:
- it does not pause or alter publishing/social crons;
- it does not invent pages;
- it queues the regulatory/moat URLs for the existing priority indexer;
- it writes a daily report so the work continues while the founder is away.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/srv/BusinessOps/creditdoc")
BUSINESSOPS = Path("/srv/BusinessOps")
REPORT_DIR = ROOT / "reports" / "regulatory-refresh"
STATE_FILE = BUSINESSOPS / "data" / "creditdoc_regulatory_next_phase_state.json"
FORCE_GOOGLE_QUEUE_FILE = BUSINESSOPS / "data" / "creditdoc_force_google_indexing_urls.json"
SITE = "https://www.creditdoc.co"

PRIORITY_URLS = [
    "/tools/state-consumer-credit-regulator-directory/",
    "/state/",
    "/about/creditdoc-data/",
    "/research/consumer-complaints/",
    "/best/best-business-lines-of-credit/",
    "/best/best-sba-loans/",
    "/best/best-small-business-loans/",
    "/best/best-personal-loan-lenders/",
    "/best/best-personal-loans-bad-credit/",
    "/best/best-credit-repair-companies/",
    "/best/best-debt-relief-companies/",
    "/best/best-secured-credit-cards/",
    "/tools/business-line-of-credit-calculator/",
    "/tools/sba-loan-calculator/",
    "/tools/business-loan-calculator/",
    "/tools/commercial-loan-calculator/",
    "/tools/credit-score-simulator/",
    "/tools/debt-payoff-calculator/",
    "/answers/how-to-check-if-a-lender-is-licensed/",
    "/answers/where-to-complain-about-a-lender/",
    "/answers/how-to-file-a-cfpb-complaint/",
    "/answers/what-does-a-cfpb-complaint-mean/",
    "/answers/how-to-check-a-credit-repair-company/",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_url(path: str) -> str:
    if path.startswith("https://"):
        url = path
    else:
        url = f"{SITE}{path if path.startswith('/') else '/' + path}"
    return url if url.endswith("/") else f"{url}/"


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def save_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def append_force_google_queue(urls: list[str]) -> tuple[int, int]:
    payload = load_json(
        FORCE_GOOGLE_QUEUE_FILE,
        {
            "site": "creditdoc",
            "purpose": "One-shot forced Google Indexing API priority queue. Accepted URLs are removed by creditdoc_priority_indexing.py.",
            "urls": [],
        },
    )
    existing = payload.get("urls", [])
    if not isinstance(existing, list):
        existing = []
    seen = {canonical_url(url) for url in existing if isinstance(url, str)}
    added = []
    for url in urls:
        clean = canonical_url(url)
        if clean not in seen:
            seen.add(clean)
            added.append(clean)
    payload["updated"] = now_iso()
    payload["urls"] = sorted(seen)
    save_json(FORCE_GOOGLE_QUEUE_FILE, payload)
    return len(added), len(payload["urls"])


def run_check(command: list[str]) -> tuple[int, str]:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=180)
    output = (result.stdout or "") + (result.stderr or "")
    return result.returncode, output.strip()


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc)
    state = load_json(STATE_FILE, {"runs": []})

    urls = [canonical_url(path) for path in PRIORITY_URLS]
    added, queue_size = append_force_google_queue(urls)

    checks = []
    for label, command in [
        ("regulatory execution", ["python3", "tools/creditdoc_regulatory_seo_execution_check.py"]),
        ("priority regulatory dry-run", ["python3", "tools/creditdoc_priority_indexing.py", "--tier", "regulatory", "--dry-run"]),
        ("social duplicate guard", ["node", "scripts/creditdoc_linkedin_manager.mjs", "audit-social-duplicates"]),
    ]:
        code, output = run_check(command)
        checks.append({"label": label, "code": code, "output": output[-4000:]})

    run_record = {
        "ran_at": ts.isoformat(),
        "priority_urls": len(urls),
        "force_google_added": added,
        "force_google_queue_size": queue_size,
        "checks": [{k: v for k, v in check.items() if k != "output"} for check in checks],
    }
    state.setdefault("runs", []).append(run_record)
    state["runs"] = state["runs"][-30:]
    state["last_run"] = run_record
    save_json(STATE_FILE, state)

    report = REPORT_DIR / f"regulatory_next_phase_{ts.strftime('%Y-%m-%d')}.md"
    lines = [
        f"# CreditDoc Regulatory Next Phase Scheduler - {ts.strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "## Indexing Queue",
        f"- Priority regulatory/money/tool URLs tracked: {len(urls)}",
        f"- Newly added to force-Google queue: {added}",
        f"- Force-Google queue size after merge: {queue_size}",
        "",
        "## Checks",
    ]
    failed = False
    for check in checks:
        status = "OK" if check["code"] == 0 else "FAIL"
        failed = failed or check["code"] != 0
        lines.extend([
            f"### {check['label']} - {status}",
            "```",
            check["output"] or "(no output)",
            "```",
            "",
        ])
    lines.extend([
        "## Next Phase Instructions",
        "- Keep regulatory pages and priority tools in the forced indexing queue until the existing priority indexer accepts/removes them.",
        "- Continue weekly regulatory execution checks and monthly link-drift checks.",
        "- Regulatory-intent answer cluster is part of the forced indexing queue and should be checked in the weekly execution report.",
        "- Do not pause feeds, city/blog/answers/wellness publishing, LinkedIn, Pinterest, or existing crons without explicit founder approval.",
        "",
    ])
    report.write_text("\n".join(lines))

    print(
        "CreditDoc regulatory next phase scheduler: "
        f"priority_urls={len(urls)} added={added} queue_size={queue_size} "
        f"status={'FAIL' if failed else 'OK'} report={report}"
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
