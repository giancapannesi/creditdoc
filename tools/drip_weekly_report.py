#!/usr/bin/env python3
"""Weekly /answers/ drip report — published pages in the last 7 days.

Renders a markdown summary, converts to PDF, uploads to Google Drive folder
"CreditDoc Drip Reports" (ID: 1BeIoGG8fZU-ZpjgiIAS2lhyuX2wTUWh8).

Run: python3 creditdoc/tools/drip_weekly_report.py
Cron: 0 6 * * 6  (Saturday 06:00 UTC = 08:00 CAT)
"""
import os
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

BUSINESSOPS = Path("/srv/BusinessOps")
sys.path.insert(0, str(BUSINESSOPS))
sys.path.insert(0, str(BUSINESSOPS / "tools"))

DB_PATH = BUSINESSOPS / "creditdoc" / "data" / "creditdoc.db"
DRIVE_FOLDER_ID = "1BeIoGG8fZU-ZpjgiIAS2lhyuX2wTUWh8"
SITE_BASE = "https://creditdoc.co/answers"


def fetch_week(cutoff_iso: str) -> list[dict]:
    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        """
        SELECT slug, cluster_pillar, cluster_id, title, h1, meta_description,
               compliance_score, status, published_at, target_money_page
        FROM cluster_answers
        WHERE status = 'published'
          AND published_at IS NOT NULL
          AND published_at >= ?
        ORDER BY published_at DESC
        """,
        (cutoff_iso,),
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def fetch_all_to_date() -> tuple[int, dict]:
    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    total = con.execute(
        "SELECT COUNT(*) FROM cluster_answers WHERE status='published'"
    ).fetchone()[0]
    by_pillar = dict(con.execute(
        "SELECT cluster_pillar, COUNT(*) FROM cluster_answers "
        "WHERE status='published' GROUP BY cluster_pillar ORDER BY 2 DESC"
    ).fetchall())
    con.close()
    return total, by_pillar


def render_markdown(week_rows: list[dict], total: int, by_pillar: dict,
                    week_start: str, week_end: str) -> str:
    lines = [
        f"# CreditDoc Drip — Weekly Report",
        "",
        f"**Window:** {week_start} → {week_end} UTC",
        f"**Published this week:** {len(week_rows)}",
        f"**Published total (all-time):** {total}",
        "",
        "## This week's pages",
        "",
    ]
    if not week_rows:
        lines.append("_No pages published in this window._")
    else:
        lines.append("| # | Date (UTC) | Pillar | Compliance | Slug |")
        lines.append("|---|-----------|--------|-----------:|------|")
        for i, r in enumerate(week_rows, 1):
            date = (r["published_at"] or "")[:10]
            comp = f"{r['compliance_score']}/10"
            lines.append(
                f"| {i} | {date} | {r['cluster_pillar']} | {comp} | "
                f"[{r['slug']}]({SITE_BASE}/{r['slug']}/) |"
            )
        lines.append("")
        lines.append("### Titles + meta")
        lines.append("")
        for r in week_rows:
            lines.append(f"**{r['title']}**  ")
            lines.append(f"URL: {SITE_BASE}/{r['slug']}/  ")
            lines.append(f"H1: {r['h1']}  ")
            lines.append(f"Meta: {r['meta_description']}  ")
            lines.append(f"Money page: {r['target_money_page']}  ")
            lines.append("")
    lines += [
        "## All-time by pillar",
        "",
        "| Pillar | Count |",
        "|--------|------:|",
    ]
    for pillar, count in by_pillar.items():
        lines.append(f"| {pillar} | {count} |")
    lines += [
        "",
        "---",
        f"_Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} "
        "by drip_weekly_report.py_",
    ]
    return "\n".join(lines)


def main():
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=7)
    cutoff_iso = cutoff.strftime("%Y-%m-%dT%H:%M:%S")
    week_start = cutoff.strftime("%Y-%m-%d %H:%M")
    week_end = now.strftime("%Y-%m-%d %H:%M")

    week_rows = fetch_week(cutoff_iso)
    total, by_pillar = fetch_all_to_date()
    md = render_markdown(week_rows, total, by_pillar, week_start, week_end)

    stamp = now.strftime("%Y-%m-%d")
    filename = f"CreditDoc_Drip_Weekly_{stamp}.pdf"

    with tempfile.TemporaryDirectory() as tmp:
        md_path = Path(tmp) / "report.md"
        md_path.write_text(md, encoding="utf-8")
        pdf_path = Path(tmp) / filename
        subprocess.run(
            [
                sys.executable,
                str(BUSINESSOPS / "tools" / "create_pdf.py"),
                str(pdf_path),
                "--from-markdown", str(md_path),
                "--title", f"CreditDoc Drip Weekly — {stamp}",
            ],
            check=True,
        )

        from tools.gdrive_mcp import upload_file
        result = upload_file(
            str(pdf_path), folder_id=DRIVE_FOLDER_ID, name=filename
        )
        print(result)
        print(f"Rows this week: {len(week_rows)}  | Total published: {total}")


if __name__ == "__main__":
    main()
