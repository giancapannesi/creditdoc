#!/usr/bin/env python3
"""
CreditDoc production route-family monitor and guarded self-healer.

Purpose:
  Catch the Cloudflare Worker 1102/503 failure mode where SSR route families
  fail in production even though the current bundle can render locally.

Safety:
  - Checks live production URLs only.
  - Retries every failed URL before judging.
  - Only self-heals when at least two critical SSR route families fail.
  - Uses a filesystem lock so it cannot overlap another heal/build/deploy.
  - Enforces a cooldown between self-heal deployments.
  - Verifies the same URL set after deploy.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/srv/BusinessOps")
CREDITDOC = ROOT / "creditdoc"
LOG = ROOT / "logs" / "creditdoc_route_self_healer.log"
STATE = ROOT / "logs" / "creditdoc_route_self_healer_state.json"
LOCK = Path("/tmp/creditdoc_route_self_healer.lock")
DEPLOY_LOCK = Path("/tmp/creditdoc_deploy.lock")
DEPLOY = CREDITDOC / "deploy.sh"

USER_AGENT = "CreditDocRouteGuardian/1.0 (+https://www.creditdoc.co)"
MIN_BYTES = 2000
COOLDOWN_SECONDS = 6 * 60 * 60


@dataclass(frozen=True)
class Route:
    family: str
    url: str
    critical: bool = True


ROUTES = [
    Route("home", "https://www.creditdoc.co/", False),
    Route("review", "https://www.creditdoc.co/review/lexington-law/"),
    Route("best", "https://www.creditdoc.co/best/best-credit-repair-companies/"),
    Route("city-guide", "https://www.creditdoc.co/credit-guide/austin-tx/"),
    Route("state", "https://www.creditdoc.co/state/wyoming/"),
    Route("answers-index", "https://www.creditdoc.co/answers/"),
    Route("answer", "https://www.creditdoc.co/answers/best-debt-consolidation-loans-bad-credit/"),
    Route("category", "https://www.creditdoc.co/categories/credit-repair/"),
    Route("blog", "https://www.creditdoc.co/blog/how-to-get-a-personal-loan-with-bad-credit-in-2026/"),
    Route("wellness", "https://www.creditdoc.co/financial-wellness/credit-score-basics/"),
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def stdout_points_to_log() -> bool:
    try:
        return os.path.samefile("/proc/self/fd/1", LOG)
    except OSError:
        return False


def log(msg: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    line = f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] {msg}"
    print(line, flush=True)
    if not stdout_points_to_log():
        with LOG.open("a") as f:
            f.write(line + "\n")


def fetch(url: str, timeout: int) -> dict:
    req = urllib.request.Request(url, headers={"user-agent": USER_AGENT})
    started = time.perf_counter()
    rec = {
        "url": url,
        "status": None,
        "bytes": 0,
        "seconds": None,
        "error": None,
        "body_prefix": "",
    }
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            rec["status"] = resp.status
            rec["bytes"] = len(body)
            rec["body_prefix"] = body[:80].decode("utf-8", "replace").replace("\n", " ")
    except urllib.error.HTTPError as exc:
        body = exc.read()
        rec["status"] = exc.code
        rec["bytes"] = len(body)
        rec["body_prefix"] = body[:80].decode("utf-8", "replace").replace("\n", " ")
        rec["error"] = f"HTTPError: {exc}"
    except Exception as exc:
        rec["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        rec["seconds"] = round(time.perf_counter() - started, 3)
    return rec


def is_ok(rec: dict) -> bool:
    status = rec.get("status")
    if not isinstance(status, int) or not (200 <= status < 400):
        return False
    if rec.get("bytes", 0) < MIN_BYTES:
        return False
    prefix = (rec.get("body_prefix") or "").lower()
    if "error code: 1102" in prefix:
        return False
    return True


def check_routes(timeout: int, retry_sleep: int) -> tuple[list[dict], list[dict]]:
    records: list[dict] = []
    failures: list[dict] = []
    for route in ROUTES:
        first = fetch(route.url, timeout)
        first.update({"family": route.family, "critical": route.critical, "attempt": 1})
        if is_ok(first):
            records.append(first)
            continue

        time.sleep(retry_sleep)
        second = fetch(route.url, timeout)
        second.update({"family": route.family, "critical": route.critical, "attempt": 2})
        records.extend([first, second])
        if not is_ok(second):
            failures.append(second)
    return records, failures


def failing_critical_families(failures: list[dict]) -> set[str]:
    return {f["family"] for f in failures if f.get("critical")}


def read_state() -> dict:
    if not STATE.exists():
        return {}
    try:
        return json.loads(STATE.read_text())
    except Exception:
        return {}


def write_state(data: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def send_alert(subject: str, body: str) -> None:
    try:
        from agentmail import AgentMail

        key = (ROOT / "tools" / ".agentmail-api-key").read_text().strip()
        client = AgentMail(api_key=key)
        client.inboxes.messages.send(
            "longleader503@agentmail.to",
            to="gian.eao@gmail.com",
            subject=subject,
            text=body,
            html=f"<pre>{body}</pre>",
        )
    except Exception as exc:
        log(f"alert_email_failed error={exc}")


def run_deploy(timeout: int) -> tuple[int, str]:
    with DEPLOY_LOCK.open("w") as lock_f:
        try:
            fcntl.flock(lock_f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return 99, "deploy lock already held"

        proc = subprocess.run(
            [str(DEPLOY)],
            cwd=str(CREDITDOC),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
        return proc.returncode, proc.stdout


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true", help="monitor only; never deploy")
    parser.add_argument("--force-heal", action="store_true", help="deploy even if threshold/cooldown would skip")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--retry-sleep", type=int, default=3)
    parser.add_argument("--deploy-timeout", type=int, default=900)
    args = parser.parse_args(argv)

    with LOCK.open("w") as lock_f:
        try:
            fcntl.flock(lock_f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            log("skip reason=route_self_healer_already_running")
            return 0

        records, failures = check_routes(args.timeout, args.retry_sleep)
        families = failing_critical_families(failures)
        ok_count = len([r for r in records if r.get("attempt") == 1 and is_ok(r)])
        log(f"check ok_first_attempt={ok_count}/{len(ROUTES)} failures={len(failures)} critical_families={sorted(families)}")

        if not failures:
            write_state({"last_check": now_iso(), "status": "ok", "records": records[-len(ROUTES):]})
            return 0

        for failure in failures:
            log(
                "failure "
                f"family={failure['family']} status={failure.get('status')} "
                f"bytes={failure.get('bytes')} error={failure.get('error')} "
                f"url={failure['url']}"
            )

        should_heal = len(families) >= 2 or args.force_heal
        if args.check_only or not should_heal:
            write_state({
                "last_check": now_iso(),
                "status": "failed_no_heal",
                "critical_families": sorted(families),
                "failures": failures,
            })
            return 1

        state = read_state()
        last_heal = float(state.get("last_heal_epoch", 0) or 0)
        elapsed = time.time() - last_heal
        if not args.force_heal and elapsed < COOLDOWN_SECONDS:
            log(f"skip_heal reason=cooldown elapsed={int(elapsed)}s cooldown={COOLDOWN_SECONDS}s")
            write_state({
                "last_check": now_iso(),
                "status": "failed_heal_cooldown",
                "critical_families": sorted(families),
                "failures": failures,
                "last_heal_epoch": last_heal,
            })
            send_alert(
                f"CreditDoc route failures during heal cooldown — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
                "CreditDoc route self-healer found failures but skipped deployment due to cooldown.\n\n"
                + "\n".join(f"{f['family']} {f.get('status')} {f['url']}" for f in failures),
            )
            return 2

        log(f"heal_start critical_families={sorted(families)}")
        rc, output = run_deploy(args.deploy_timeout)
        output_tail = "\n".join(output.strip().splitlines()[-80:])
        log(f"heal_deploy_exit rc={rc}")
        if output_tail:
            log("heal_deploy_tail:\n" + output_tail)

        post_records, post_failures = check_routes(args.timeout, args.retry_sleep)
        post_families = failing_critical_families(post_failures)
        healed = rc == 0 and not post_failures
        write_state({
            "last_check": now_iso(),
            "status": "healed" if healed else "heal_failed",
            "critical_families": sorted(families),
            "post_critical_families": sorted(post_families),
            "failures": failures,
            "post_failures": post_failures,
            "last_heal_epoch": time.time(),
        })

        subject_status = "HEALED" if healed else "HEAL FAILED"
        send_alert(
            f"CreditDoc route self-healer {subject_status} — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            f"Initial critical failures: {sorted(families)}\n"
            f"Deploy exit code: {rc}\n"
            f"Post-deploy critical failures: {sorted(post_families)}\n\n"
            f"Initial failures:\n"
            + "\n".join(f"{f['family']} {f.get('status')} {f['url']}" for f in failures)
            + "\n\nDeploy output tail:\n"
            + output_tail,
        )
        return 0 if healed else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
