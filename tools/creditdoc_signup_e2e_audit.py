#!/usr/bin/env python3
"""Live end-to-end audit for CreditDoc signup and quiz capture wiring."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUPABASE_ENV = Path("/srv/BusinessOps/tools/.supabase-creditdoc.env")
SENDY_CONFIG = Path("/srv/sendy/includes/config.php")
REPORT_DIR = ROOT / "reports" / "signup-e2e"


def load_supabase_db_url() -> str:
  if not SUPABASE_ENV.exists():
    raise RuntimeError(f"missing {SUPABASE_ENV}")
  for line in SUPABASE_ENV.read_text().splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
      continue
    key, value = line.split("=", 1)
    if key == "SUPABASE_DB_URL":
      return shlex.split(value)[0] if value else ""
  raise RuntimeError("SUPABASE_DB_URL not found")


def load_sendy_config() -> dict[str, str]:
  if not SENDY_CONFIG.exists():
    raise RuntimeError(f"missing {SENDY_CONFIG}")
  text = SENDY_CONFIG.read_text()
  values: dict[str, str] = {}
  for key in ("dbHost", "dbUser", "dbPass", "dbName"):
    match = re.search(rf"\${key}\s*=\s*'([^']*)'", text)
    if not match:
      raise RuntimeError(f"{key} not found in Sendy config")
    values[key] = match.group(1)
  return values


def http_post_json(url: str, payload: dict, base_url: str) -> tuple[int, dict]:
  body = json.dumps(payload).encode()
  req = urllib.request.Request(
    url,
    data=body,
    method="POST",
    headers={
      "content-type": "application/json",
      "origin": base_url.rstrip("/"),
      "referer": f"{base_url.rstrip('/')}{payload.get('source_page', '/')}",
      "user-agent": "CreditDocSignupE2EAudit/1.0",
    },
  )
  try:
    with urllib.request.urlopen(req, timeout=20) as res:
      return res.status, json.loads(res.read().decode())
  except urllib.error.HTTPError as exc:
    raw = exc.read().decode()
    try:
      return exc.code, json.loads(raw)
    except json.JSONDecodeError:
      return exc.code, {"ok": False, "raw": raw[:500]}


def psql_scalar(db_url: str, sql: str) -> str:
  result = subprocess.run(
    ["psql", db_url, "-At", "-c", sql],
    check=True,
    text=True,
    capture_output=True,
  )
  return result.stdout.strip()


def mysql_scalar(config: dict[str, str], sql: str) -> str:
  env = os.environ.copy()
  env["MYSQL_PWD"] = config["dbPass"]
  result = subprocess.run(
    [
      "mysql",
      f"-h{config['dbHost']}",
      f"-u{config['dbUser']}",
      "-N",
      "-B",
      config["dbName"],
      "-e",
      sql,
    ],
    check=True,
    text=True,
    capture_output=True,
    env=env,
  )
  return result.stdout.strip()


def sql_quote(value: str) -> str:
  return "'" + value.replace("'", "''") + "'"


def expect(condition: bool, message: str, checks: list[dict]) -> None:
  checks.append({"ok": bool(condition), "check": message})
  if not condition:
    raise AssertionError(message)


def run(base_url: str, cleanup: bool) -> dict:
  ts = int(time.time())
  stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
  quiz_email = f"creditdoc-e2e-quiz-{ts}@example.com"
  course_email = f"creditdoc-e2e-course-{ts}@example.com"
  quiz_session = f"e2e-{ts}"
  checks: list[dict] = []
  db_url = load_supabase_db_url()
  sendy = load_sendy_config()

  quiz_payload = {
    "tool_id": "credit-repair-qualify-quiz",
    "source_page": "/tools/credit-repair-qualify-quiz/",
    "result_label": "repair_research",
    "email": quiz_email,
    "name": "CreditDoc E2E Quiz",
    "elapsed_ms": 5000,
    "responses": {
      "session_id": quiz_session,
      "reportStatus": "recent-errors",
      "negativeItems": "errors",
      "accuracy": "not-accurate",
      "timeline": "mortgage-loan",
      "capacity": "yes",
      "risk": "no",
    },
    "utm": {"source": "signup-e2e"},
  }
  quiz_status, quiz_body = http_post_json(
    f"{base_url.rstrip('/')}/api/origination-intake", quiz_payload, base_url
  )
  expect(quiz_status == 200 and quiz_body.get("ok") is True, "quiz API returns ok", checks)
  capture = quiz_body.get("capture", {})
  expect(capture.get("email") == quiz_email, "quiz response returns submitted email", checks)
  expect(capture.get("source_page") == quiz_payload["source_page"], "quiz response returns source page", checks)
  expect(capture.get("tool_id") == quiz_payload["tool_id"], "quiz response returns tool id", checks)
  expect(capture.get("recommended_route") == "/best/best-credit-repair-companies/", "quiz response returns route", checks)
  expect(capture.get("writes", {}).get("user_quiz_responses") is True, "quiz response confirms quiz write", checks)
  expect(capture.get("writes", {}).get("lead_captures") is True, "quiz response confirms lead write", checks)

  quiz_db_count = psql_scalar(
    db_url,
    "select count(*) from user_quiz_responses "
    f"where email={sql_quote(quiz_email)} and session_id={sql_quote(quiz_session)};",
  )
  quiz_lead_count = psql_scalar(
    db_url,
    f"select count(*) from lead_captures where email={sql_quote(quiz_email)} "
    "and source_page='/tools/credit-repair-qualify-quiz/';",
  )
  expect(quiz_db_count == "1", "quiz row exists in Supabase user_quiz_responses", checks)
  expect(quiz_lead_count == "1", "quiz lead exists in Supabase lead_captures", checks)

  course_payload = {
    "signup_type": "credit-fundamentals-course",
    "source_page": "/courses/credit-fundamentals/how-to-read-your-credit-report/",
    "email": course_email,
    "name": "CreditDoc E2E Course",
    "elapsed_ms": 3000,
  }
  course_status, course_body = http_post_json(
    f"{base_url.rstrip('/')}/api/email-signup", course_payload, base_url
  )
  expect(course_status == 200 and course_body.get("ok") is True, "course signup API returns ok", checks)
  signup = course_body.get("signup", {})
  expect(signup.get("email") == course_email, "course response returns submitted email", checks)
  expect(signup.get("signup_type") == "credit-fundamentals-course", "course response returns signup type", checks)
  expect(signup.get("source_page") == course_payload["source_page"], "course response returns source page", checks)
  expect(signup.get("list_name") == "Credit Fundamentals Course", "course response returns list name", checks)
  expect(signup.get("writes", {}).get("sendy_subscribers") is True, "course response confirms Sendy write", checks)
  expect(signup.get("writes", {}).get("lead_captures") is True, "course response confirms lead write", checks)

  sendy_count = mysql_scalar(
    sendy,
    "select count(*) from subscribers where "
    f"email={sql_quote(course_email)} and list=2 and unsubscribed=0 and bounced=0;",
  )
  course_lead_count = psql_scalar(
    db_url,
    f"select count(*) from lead_captures where email={sql_quote(course_email)} "
    "and source_page='/courses/credit-fundamentals/how-to-read-your-credit-report/';",
  )
  expect(sendy_count == "1", "course signup exists in Sendy course list", checks)
  expect(course_lead_count == "1", "course lead exists in Supabase lead_captures", checks)

  cleanup_actions: list[str] = []
  if cleanup:
    subscriber_ids = mysql_scalar(
      sendy,
      f"select group_concat(id) from subscribers where email in ({sql_quote(quiz_email)}, {sql_quote(course_email)});",
    )
    if subscriber_ids:
      mysql_scalar(sendy, f"delete from ares_emails_sent where subscriber_id in ({subscriber_ids});")
      mysql_scalar(sendy, f"delete from subscribers where id in ({subscriber_ids});")
      cleanup_actions.append("removed Sendy test subscribers")
    psql_scalar(db_url, f"delete from lead_captures where email in ({sql_quote(quiz_email)}, {sql_quote(course_email)});")
    psql_scalar(db_url, f"delete from user_quiz_responses where email={sql_quote(quiz_email)};")
    cleanup_actions.append("removed Supabase test rows")

  return {
    "ok": all(check["ok"] for check in checks),
    "checked_at": stamp,
    "base_url": base_url.rstrip("/"),
    "checks": checks,
    "cleanup": cleanup,
    "cleanup_actions": cleanup_actions,
    "test_emails": [quiz_email, course_email],
  }


def write_report(result: dict) -> None:
  REPORT_DIR.mkdir(parents=True, exist_ok=True)
  day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
  json_path = REPORT_DIR / f"signup_e2e_{day}.json"
  md_path = REPORT_DIR / f"signup_e2e_{day}.md"
  json_path.write_text(json.dumps(result, indent=2) + "\n")
  lines = [
    f"# CreditDoc Signup E2E Audit - {result['checked_at']}",
    "",
    f"Base URL: {result['base_url']}",
    f"Result: {'PASS' if result['ok'] else 'FAIL'}",
    f"Cleanup: {'yes' if result['cleanup'] else 'no'}",
    "",
    "## Checks",
  ]
  for check in result["checks"]:
    lines.append(f"- {'OK' if check['ok'] else 'FAIL'}: {check['check']}")
  if result["cleanup_actions"]:
    lines.extend(["", "## Cleanup"])
    lines.extend(f"- {action}" for action in result["cleanup_actions"])
  md_path.write_text("\n".join(lines) + "\n")


def main() -> int:
  parser = argparse.ArgumentParser()
  parser.add_argument("--base-url", default="https://www.creditdoc.co")
  parser.add_argument("--cleanup", action="store_true")
  args = parser.parse_args()

  try:
    result = run(args.base_url, args.cleanup)
    write_report(result)
  except Exception as exc:
    result = {
      "ok": False,
      "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
      "base_url": args.base_url.rstrip("/"),
      "error": str(exc),
    }
    write_report(result)
    print(json.dumps(result, indent=2), file=sys.stderr)
    return 1

  print(json.dumps(result, indent=2))
  return 0 if result["ok"] else 1


if __name__ == "__main__":
  raise SystemExit(main())
