#!/usr/bin/env python3
"""CreditDoc Cloudflare Worker error-tail sampler.

Runs `wrangler tail --format=json --status=error` for a fixed window
(default 300s = 5min). If ANY error events stream in, emails Harvey
with the parsed exception summary. Silent when the window closes clean.

Rationale (debugger next-step #2): the deploy health check catches
route-level 404/5xx from the outside. This catches Worker-internal
exceptions (subrequest failures, JS errors in handlers, Supabase auth
issues) that would return 200 to the client but degrade product quality.

Env: reads /srv/BusinessOps/.env for CLOUDFLARE_EMAIL + CLOUDFLARE_GLOBAL_API_KEY.
Cron: 0 3 * * * (03:00 UTC daily, off-peak).
Log:  /srv/BusinessOps/logs/creditdoc_worker_errors.log
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path("/srv/BusinessOps/creditdoc")
ENV_PATH = Path("/srv/BusinessOps/.env")
LOG_PATH = Path("/srv/BusinessOps/logs/creditdoc_worker_errors.log")
HARVEY_KEY_PATH = Path("/srv/BusinessOps/tools/.agentmail-api-key")
FOUNDER_EMAIL = "gian.eao@gmail.com"


def load_env() -> dict[str, str]:
    if not ENV_PATH.exists():
        return {}
    out = {}
    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def sample_errors(window_seconds: int) -> tuple[list[dict], str | None]:
    """Run wrangler tail for `window_seconds` and return (errors, wrangler_stderr)."""
    dotenv = load_env()
    email = os.environ.get("CLOUDFLARE_EMAIL") or dotenv.get("CLOUDFLARE_EMAIL", "")
    global_key = os.environ.get("CLOUDFLARE_GLOBAL_API_KEY") or dotenv.get("CLOUDFLARE_GLOBAL_API_KEY", "")
    if not email or not global_key:
        return ([], "CF creds missing (CLOUDFLARE_EMAIL + CLOUDFLARE_GLOBAL_API_KEY)")

    env = {k: v for k, v in os.environ.items() if k != "CLOUDFLARE_API_TOKEN"}
    env["CLOUDFLARE_EMAIL"] = email
    env["CLOUDFLARE_API_KEY"] = global_key
    env["PATH"] = os.environ.get("PATH", "")

    cmd = ["npx", "wrangler", "tail", "--format=json", "--status=error"]
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(REPO_ROOT),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        try:
            stdout, stderr = proc.communicate(timeout=window_seconds)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                stdout, stderr = proc.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                try:
                    stdout, stderr = proc.communicate(timeout=3)
                except subprocess.TimeoutExpired:
                    stdout, stderr = "", "wrangler-tail hang: SIGKILL of process group did not release pipes"
    except FileNotFoundError:
        return ([], "wrangler not found on PATH")

    errors: list[dict] = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            evt = json.loads(line)
        except json.JSONDecodeError:
            continue
        errors.append(evt)
    return (errors, stderr[-500:] if stderr and not errors else None)


def send_alert(errors: list[dict], window_seconds: int) -> None:
    try:
        key = HARVEY_KEY_PATH.read_text().strip()
    except FileNotFoundError:
        print("[worker-errors] no AgentMail key — cannot send alert", file=sys.stderr)
        return

    import urllib.request
    lines = [f"CreditDoc Worker emitted {len(errors)} error event(s) during {window_seconds}s sample:", ""]
    for evt in errors[:20]:
        req = evt.get("event", {}).get("request", {}) or {}
        excs = evt.get("exceptions", []) or []
        outcome = evt.get("outcome", "?")
        url = req.get("url", "?")
        exc_summary = "; ".join(f"{e.get('name','')}: {e.get('message','')}" for e in excs[:2]) or "(no exceptions field)"
        lines.append(f"  {outcome}  {url}")
        lines.append(f"    {exc_summary}")
    if len(errors) > 20:
        lines.append(f"  ... +{len(errors) - 20} more")
    lines += ["", f"Log: {LOG_PATH}", f"Timestamp: {datetime.now(timezone.utc).isoformat()}"]

    payload = {
        "from": "longleader503@agentmail.to",
        "to": [FOUNDER_EMAIL],
        "subject": f"[CreditDoc] Worker errors detected — {len(errors)} event(s) in {window_seconds}s",
        "text": "\n".join(lines),
    }
    req = urllib.request.Request(
        "https://api.agentmail.to/v0/inboxes/longleader503@agentmail.to/messages/send",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp.read()
        print("[worker-errors] Harvey alert sent", file=sys.stderr)
    except Exception as exc:
        print(f"[worker-errors] Harvey send failed: {exc}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--window", type=int, default=300, help="Sampling window in seconds (default 300)")
    parser.add_argument("--no-alert", action="store_true", help="Skip Harvey email on errors")
    parser.add_argument("--quiet", action="store_true", help="Silence stdout on clean run")
    args = parser.parse_args()

    now = datetime.now(timezone.utc).isoformat()
    errors, err = sample_errors(args.window)

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a") as fh:
        fh.write(json.dumps({
            "ts": now, "window_s": args.window,
            "error_count": len(errors), "wrangler_err": err,
        }) + "\n")

    if err:
        print(f"[worker-errors] {now}  WRANGLER ERROR: {err}", file=sys.stderr)
        return 2
    if not errors:
        if not args.quiet:
            print(f"[worker-errors] {now}  clean — 0 errors in {args.window}s")
        return 0

    print(f"[worker-errors] {now}  FAIL — {len(errors)} error events in {args.window}s", file=sys.stderr)
    if not args.no_alert:
        send_alert(errors, args.window)
    return 1


if __name__ == "__main__":
    sys.exit(main())
