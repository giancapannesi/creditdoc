#!/usr/bin/env python3
"""
CreditDoc content engine daily verifier.

Runs after the weekday content engines have had time to fire. It does not
generate content. It verifies that today's scheduled content jobs actually ran
and produced the expected success markers, then emails Jammi if anything is
missing.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, time, timezone
from pathlib import Path


AGENTMAIL_API_KEY_FILE = Path("/srv/BusinessOps/tools/.agentmail-api-key")
AGENTMAIL_INBOX = "longleader503@agentmail.to"
RECIPIENT = "gian.eao@gmail.com"


@dataclass(frozen=True)
class Job:
    name: str
    due_utc: time
    log_path: Path
    required_patterns: tuple[str, ...]
    date_pattern: str | None = None
    weekdays_only: bool = False


@dataclass(frozen=True)
class QueueCheck:
    name: str
    command: tuple[str, ...]
    pattern: str
    minimum: int
    zero_ok: bool = False


@dataclass(frozen=True)
class CommandCheck:
    name: str
    command: tuple[str, ...]
    required_pattern: str


def today_start(ts: datetime) -> datetime:
    return datetime(ts.year, ts.month, ts.day, tzinfo=timezone.utc)


def due_datetime(ts: datetime, due: time) -> datetime:
    return datetime(ts.year, ts.month, ts.day, due.hour, due.minute, tzinfo=timezone.utc)


def read_tail(path: Path, max_bytes: int = 16000) -> str:
    with path.open("rb") as f:
        try:
            f.seek(-max_bytes, os.SEEK_END)
        except OSError:
            f.seek(0)
        return f.read().decode("utf-8", errors="replace")


def check_job(job: Job, now: datetime, allow_pending: bool) -> tuple[str, bool, str]:
    if job.weekdays_only and now.weekday() >= 5:
        return job.name, True, "skipped on weekend"

    due = due_datetime(now, job.due_utc)
    if now < due:
        status = f"pending until {due.strftime('%H:%M UTC')}"
        return job.name, (True if allow_pending else False), status

    if not job.log_path.exists():
        return job.name, False, f"missing log: {job.log_path}"

    mtime = datetime.fromtimestamp(job.log_path.stat().st_mtime, tz=timezone.utc)
    if mtime < due:
        return job.name, False, f"log not updated since due time; mtime={mtime.isoformat()}"

    text = read_tail(job.log_path)
    if job.date_pattern and job.date_pattern not in text:
        return job.name, False, f"today marker not found: {job.date_pattern}"

    missing = [pat for pat in job.required_patterns if not re.search(pat, text, re.I | re.M)]
    if missing:
        return job.name, False, "success marker missing: " + ", ".join(missing)

    return job.name, True, f"ran; log mtime={mtime.strftime('%H:%M:%S UTC')}"


def check_queue(check: QueueCheck) -> tuple[str, bool, str]:
    try:
        proc = subprocess.run(
            check.command,
            cwd="/srv/BusinessOps",
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=90,
            check=False,
        )
    except Exception as exc:
        return check.name, False, f"queue check failed: {type(exc).__name__}: {exc}"

    output = proc.stdout.strip()
    if proc.returncode != 0:
        return check.name, False, f"queue command exited {proc.returncode}: {output[-500:]}"

    match = re.search(check.pattern, output, re.I | re.M)
    if not match:
        return check.name, False, f"queue count marker missing: {output[-500:]}"

    count = int(match.group(1).replace(",", ""))
    if check.zero_ok and count == 0:
        return check.name, True, "0 remaining; legacy queue fully processed"

    if count < check.minimum:
        return check.name, False, f"queue low: {count} remaining; minimum {check.minimum}"

    return check.name, True, f"queue healthy: {count} remaining"


def check_command(check: CommandCheck) -> tuple[str, bool, str]:
    try:
        proc = subprocess.run(
            check.command,
            cwd="/srv/BusinessOps",
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=90,
            check=False,
        )
    except Exception as exc:
        return check.name, False, f"command check failed: {type(exc).__name__}: {exc}"

    output = proc.stdout.strip()
    if proc.returncode != 0:
        return check.name, False, f"command exited {proc.returncode}: {output[-500:]}"
    if not re.search(check.required_pattern, output, re.I | re.M):
        return check.name, False, f"success marker missing: {output[-500:]}"
    return check.name, True, output.splitlines()[-1] if output else "passed"


def send_failure_email(failures: list[tuple[str, bool, str]], results: list[tuple[str, bool, str]]) -> None:
    from agentmail import AgentMail

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    fail_lines = "\n".join(f"FAIL: {name} - {detail}" for name, _, detail in failures)
    all_lines = "\n".join(("OK: " if ok else "FAIL: ") + f"{name} - {detail}" for name, ok, detail in results)
    subject = f"CreditDoc content engine failure - {ts}"
    body = (
        f"CreditDoc content engine verifier found {len(failures)} failure(s) at {ts}.\n\n"
        f"{fail_lines}\n\n"
        f"All results:\n{all_lines}\n"
    )

    api_key = AGENTMAIL_API_KEY_FILE.read_text().strip()
    client = AgentMail(api_key=api_key)
    client.inboxes.messages.send(
        AGENTMAIL_INBOX,
        to=RECIPIENT,
        subject=subject,
        text=body,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Do not send email")
    parser.add_argument("--allow-pending", action="store_true", help="Do not fail jobs that are not due yet")
    parser.add_argument("--late-index-only", action="store_true", help="Only verify the late IndexNow tier jobs")
    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")

    jobs = [
        Job(
            "blog scheduler",
            time(6, 0),
            Path("/srv/BusinessOps/logs/creditdoc_blog_scheduler.log"),
            (r"Loaded \d+ blog post",),
            date_pattern=f"CreditDoc Blog Scheduler — {today}",
        ),
        Job(
            "blog generator",
            time(6, 30),
            Path("/srv/BusinessOps/logs/creditdoc_blog.log"),
            (r"Done\. Generated: [1-9]", r"DB mirror:"),
        ),
        Job(
            "city guides",
            time(9, 0),
            Path("/srv/BusinessOps/logs/creditdoc_city_guides.log"),
            (r"Generated: [1-9]\d* \| Failed: 0",),
        ),
        Job(
            "questions / answers",
            time(13, 0),
            Path("/srv/BusinessOps/logs/cluster_executor.log"),
            (rf"\[{today}T.*\] DONE: https://creditdoc\.co/answers/",),
            weekdays_only=True,
        ),
        Job(
            "financial wellness",
            time(15, 0),
            Path("/srv/BusinessOps/logs/creditdoc_wellness.log"),
            (r"Saved \d+ total guides \(2 new\)", r"DB mirror: 2/2 new wellness guides added"),
        ),
        Job(
            "comparisons",
            time(15, 30),
            Path("/srv/BusinessOps/logs/creditdoc_comparisons.log"),
            (r"Saved \d+ total comparisons \(5 new\)", r"DB mirror: 5/5 new comparisons added"),
        ),
        Job(
            "daily GSC manual queue",
            time(6, 15),
            Path("/srv/BusinessOps/logs/creditdoc_daily_gsc_queue.log"),
            (r"Email sent: True", r"DB stamped: \d+ rows"),
            date_pattern=f"Daily GSC queue — {today}",
        ),
        Job(
            "priority indexing",
            time(8, 0),
            Path("/srv/BusinessOps/logs/creditdoc_indexing.log"),
            (r"IndexNow: \d+ OK, 0 failed", r"Google: \d+ OK, 0 failed", r"✓ Done\."),
            date_pattern=f"CreditDoc Priority Indexing — {today} 08:00 UTC",
        ),
        Job(
            "money IndexNow tier",
            time(14, 15),
            Path("/srv/BusinessOps/logs/creditdoc_indexnow_money.log"),
            (r"Money:\s+[1-9]\d*", r"IndexNow: \d+ OK, 0 failed", r"✓ Done\."),
            date_pattern=f"CreditDoc Priority Indexing — {today} 14:15 UTC",
        ),
        Job(
            "answers IndexNow tier",
            time(14, 20),
            Path("/srv/BusinessOps/logs/creditdoc_indexnow_answers.log"),
            (r"Answers:\s+[1-9]\d*", r"IndexNow: \d+ OK, 0 failed", r"✓ Done\."),
            date_pattern=f"CreditDoc Priority Indexing — {today} 14:20 UTC",
        ),
        Job(
            "blog IndexNow tier",
            time(14, 25),
            Path("/srv/BusinessOps/logs/creditdoc_indexnow_blog.log"),
            (r"Blog:\s+[1-9]\d*", r"IndexNow: \d+ OK, 0 failed", r"✓ Done\."),
            date_pattern=f"CreditDoc Priority Indexing — {today} 14:25 UTC",
        ),
    ]

    late_index_jobs = [
        Job(
            "late money IndexNow tier",
            time(22, 15),
            Path("/srv/BusinessOps/logs/creditdoc_indexnow_money.log"),
            (r"Money:\s+[1-9]\d*", r"IndexNow: \d+ OK, 0 failed", r"✓ Done\."),
            date_pattern=f"CreditDoc Priority Indexing — {today} 22:15 UTC",
        ),
        Job(
            "late answers IndexNow tier",
            time(22, 20),
            Path("/srv/BusinessOps/logs/creditdoc_indexnow_answers.log"),
            (r"Answers:\s+[1-9]\d*", r"IndexNow: \d+ OK, 0 failed", r"✓ Done\."),
            date_pattern=f"CreditDoc Priority Indexing — {today} 22:20 UTC",
        ),
        Job(
            "late blog IndexNow tier",
            time(22, 25),
            Path("/srv/BusinessOps/logs/creditdoc_indexnow_blog.log"),
            (r"Blog:\s+[1-9]\d*", r"IndexNow: \d+ OK, 0 failed", r"✓ Done\."),
            date_pattern=f"CreditDoc Priority Indexing — {today} 22:25 UTC",
        ),
    ]

    queue_checks = [
        QueueCheck(
            "blog queue reserve",
            (
                "/srv/BusinessOps/.venv/bin/python3",
                "/srv/BusinessOps/tools/creditdoc_blog.py",
                "--list-queue",
            ),
            r"Queue:\s+(\d+)\s+pending",
            minimum=10,
        ),
        QueueCheck(
            "city guide queue reserve",
            (
                "/srv/BusinessOps/.venv/bin/python3",
                "/srv/BusinessOps/tools/creditdoc_city_guide_generator.py",
                "--list-next",
                "20",
            ),
            r"Next\s+\d+\s+cities\s+\(of\s+([\d,]+)\s+tracked\)",
            minimum=100,
        ),
        QueueCheck(
            "questions / answers queue reserve",
            (
                "/srv/BusinessOps/.venv/bin/python3",
                "/srv/BusinessOps/tools/creditdoc_cluster_executor.py",
                "--status",
            ),
            r"Pending:\s+([\d,]+)",
            minimum=50,
        ),
        QueueCheck(
            "financial wellness queue reserve",
            (
                "/srv/BusinessOps/.venv/bin/python3",
                "/srv/BusinessOps/tools/creditdoc_wellness_generator.py",
                "--list-queue",
            ),
            r"Queue:\s+(\d+)\s+remaining",
            minimum=10,
        ),
        QueueCheck(
            "comparison queue reserve",
            (
                "/srv/BusinessOps/.venv/bin/python3",
                "/srv/BusinessOps/tools/creditdoc_comparison_generator.py",
                "--stats",
            ),
            r"Queue remaining:\s+([\d,]+)",
            minimum=50,
        ),
    ]

    command_checks = [
        CommandCheck(
            "generated-content guardrail regression",
            (
                "/srv/BusinessOps/.venv/bin/python3",
                "/srv/BusinessOps/tools/test_creditdoc_content_guardrails.py",
            ),
            r"guardrail regression tests passed",
        ),
    ]

    print(f"CreditDoc content engine verifier - {now.strftime('%Y-%m-%d %H:%M UTC')}")
    if args.late_index_only:
        results = [check_job(job, now, args.allow_pending) for job in late_index_jobs]
    else:
        results = [check_job(job, now, args.allow_pending) for job in jobs]
        results.extend(check_queue(check) for check in queue_checks)
        results.extend(check_command(check) for check in command_checks)
    for name, ok, detail in results:
        print(f"[{'OK' if ok else 'FAIL'}] {name}: {detail}")

    failures = [result for result in results if not result[1]]
    if failures and not args.dry_run:
        send_failure_email(failures, results)
        print(f"Alert email sent for {len(failures)} failure(s).")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
