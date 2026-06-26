#!/usr/bin/env python3
"""Read-only quality monitor for CreditDoc city guide traffic assets.

Checks `city_guides` rows for localized question quality, metadata length,
and risky-looking local resource details. This does not write to Supabase.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


ENV_PATH = Path("/srv/BusinessOps/tools/.supabase-creditdoc.env")
DEFAULT_REPORT_DIR = Path("/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Easy_First_SEO_Project_2026-06-22")

QUESTION_TOPICS = {
    "credit repair": ("credit repair", "repair company", "dispute"),
    "build credit": ("credit score", "build credit", "improve my credit", "secured"),
    "sba/business loans": ("sba", "business loan", "small business"),
    "debt relief": ("debt", "consolidation", "relief"),
    "credit unions": ("credit union", "bank"),
    "payday alternatives": ("payday", "alternative", "emergency cash"),
    "identity theft": ("identity theft", "monitoring", "fraud"),
}

GENERIC_QUESTION_PATTERNS = (
    re.compile(r"^what is (credit repair|debt consolidation|a credit score)\??$", re.I),
    re.compile(r"^how does (credit repair|debt consolidation) work\??$", re.I),
    re.compile(r"^where can i get help\??$", re.I),
)

STREET_ADDRESS_RE = re.compile(
    r"\b\d{1,6}\s+[A-Za-z0-9.'-]+(?:\s+[A-Za-z0-9.'-]+){0,5}\s+"
    r"(?:st|street|ave|avenue|rd|road|blvd|boulevard|dr|drive|ln|lane|way|ct|court|pl|place|pkwy|parkway|hwy|highway)\b",
    re.I,
)


def load_env() -> dict[str, str]:
    if not ENV_PATH.exists():
        sys.exit(f"missing {ENV_PATH}")
    out: dict[str, str] = {}
    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        out[k.strip()] = v.strip().strip('"').strip("'")
    if not out.get("SUPABASE_URL"):
        sys.exit("SUPABASE_URL missing")
    if not (out.get("SUPABASE_ANON_KEY") or out.get("SUPABASE_SERVICE_ROLE_KEY")):
        sys.exit("SUPABASE_ANON_KEY or SUPABASE_SERVICE_ROLE_KEY missing")
    return out


def auth_key(env: dict[str, str]) -> str:
    return env.get("SUPABASE_ANON_KEY") or env["SUPABASE_SERVICE_ROLE_KEY"]


def pg_get(env: dict[str, str], path: str, timeout: int = 20) -> tuple[int, Any]:
    url = f"{env['SUPABASE_URL'].rstrip('/')}/rest/v1/{path}"
    req = Request(url)
    key = auth_key(env)
    req.add_header("apikey", key)
    req.add_header("authorization", f"Bearer {key}")
    req.add_header("accept", "application/json")
    try:
        with urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else None
    except HTTPError as e:
        return e.code, {"error": e.read().decode("utf-8", errors="replace")[:500]}
    except URLError as e:
        return 0, {"error": str(e.reason)}


def count_city_guides(env: dict[str, str]) -> int | None:
    url = f"{env['SUPABASE_URL'].rstrip('/')}/rest/v1/city_guides?select=*&limit=0"
    req = Request(url)
    key = auth_key(env)
    req.add_header("apikey", key)
    req.add_header("authorization", f"Bearer {key}")
    req.add_header("prefer", "count=exact")
    req.add_header("range", "0-0")
    try:
        with urlopen(req, timeout=20) as resp:
            content_range = resp.headers.get("content-range", "")
            if "/" in content_range:
                total = content_range.split("/", 1)[1]
                return int(total) if total.isdigit() else None
    except Exception:
        return None
    return None


def strip_html(value: str) -> str:
    return unescape(re.sub(r"<[^>]+>", " ", value or "")).replace("\xa0", " ")


def clean_space(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def body_inline(row: dict[str, Any]) -> dict[str, Any]:
    body = row.get("body_inline") or {}
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except json.JSONDecodeError:
            return {}
    return body if isinstance(body, dict) else {}


def has_city_or_state(text: str, city: str, state_abbr: str, state_name: str) -> bool:
    lower = text.lower()
    return city.lower() in lower or state_abbr.lower() in lower or state_name.lower() in lower


def question_topic_hits(questions: list[dict[str, Any]]) -> set[str]:
    haystack = " ".join(
        f"{q.get('q', '')} {strip_html(str(q.get('a', '')))}".lower()
        for q in questions
    )
    return {
        topic
        for topic, terms in QUESTION_TOPICS.items()
        if any(term in haystack for term in terms)
    }


def audit_row(row: dict[str, Any]) -> dict[str, Any]:
    slug = row.get("slug", "")
    city = row.get("city", "")
    state_abbr = row.get("state_abbr", "")
    state_name = row.get("state_name", "")
    title = row.get("seo_title") or ""
    meta = row.get("meta_description") or ""
    data = body_inline(row)
    questions = data.get("local_questions") if isinstance(data.get("local_questions"), list) else []
    resources = data.get("local_resources") if isinstance(data.get("local_resources"), list) else []

    issues: list[str] = []
    warnings: list[str] = []

    if len(title) < 35 or len(title) > 60:
        issues.append(f"seo_title_len={len(title)}")
    if len(meta) < 130 or len(meta) > 160:
        issues.append(f"meta_len={len(meta)}")
    elif not 145 <= len(meta) <= 155:
        warnings.append(f"meta_len_outside_target={len(meta)}")

    if len(questions) < 7:
        issues.append(f"local_questions_count={len(questions)}")

    generic_questions = 0
    unlocalized_questions = 0
    short_answers = 0
    risky_answer_claims = 0
    for q in questions:
        q_text = clean_space(str(q.get("q", "")))
        a_text = clean_space(strip_html(str(q.get("a", ""))))
        if any(pattern.search(q_text) for pattern in GENERIC_QUESTION_PATTERNS):
            generic_questions += 1
        if q_text and not has_city_or_state(q_text, city, state_abbr, state_name):
            unlocalized_questions += 1
        if len(a_text) < 120:
            short_answers += 1
        if re.search(r"\b(best|top|guaranteed|approved|approval|rating|reviews?)\b", a_text, re.I) and not re.search(
            r"\b(compare|verify|research|not a recommendation|check)\b", a_text, re.I
        ):
            risky_answer_claims += 1

    if generic_questions:
        issues.append(f"generic_questions={generic_questions}")
    if unlocalized_questions > 2:
        issues.append(f"unlocalized_questions={unlocalized_questions}")
    elif unlocalized_questions:
        warnings.append(f"unlocalized_questions={unlocalized_questions}")
    if short_answers:
        warnings.append(f"short_answers={short_answers}")
    if risky_answer_claims:
        warnings.append(f"risky_answer_claims={risky_answer_claims}")

    hits = question_topic_hits(questions)
    missing_topics = sorted(set(QUESTION_TOPICS) - hits)
    if len(missing_topics) >= 3:
        warnings.append("missing_question_topics=" + ",".join(missing_topics[:4]))

    specific_resources = []
    for resource in resources:
        if not isinstance(resource, dict):
            continue
        name = clean_space(str(resource.get("name", "")))
        address = clean_space(str(resource.get("address", "")))
        phone = clean_space(str(resource.get("phone", "")))
        url = clean_space(str(resource.get("url", "")))
        if STREET_ADDRESS_RE.search(address) or phone or (url and not re.search(r"\.(gov|org)(/|$)", url, re.I)):
            specific_resources.append(name or address or url or "unnamed resource")
    if specific_resources:
        warnings.append(f"specific_local_resources_review={len(specific_resources)}")

    return {
        "slug": slug,
        "city": city,
        "state_abbr": state_abbr,
        "question_count": len(questions),
        "title_len": len(title),
        "meta_len": len(meta),
        "topic_hits": sorted(hits),
        "issues": issues,
        "warnings": warnings,
        "resource_review_examples": specific_resources[:3],
    }


def fetch_rows(env: dict[str, str], limit: int, slug: str | None) -> list[dict[str, Any]]:
    select = "slug,city,state_abbr,state_name,seo_title,meta_description,updated_at,body_inline"
    if slug:
        path = f"city_guides?select={quote(select, safe=',')}&slug=eq.{quote(slug)}&limit=1"
    else:
        path = f"city_guides?select={quote(select, safe=',')}&order=updated_at.desc&limit={limit}"
    status, body = pg_get(env, path)
    if status != 200 or not isinstance(body, list):
        sys.exit(f"city_guides fetch failed: status={status} body={body}")
    return body


def markdown_report(total: int | None, audits: list[dict[str, Any]]) -> str:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    issue_counts = Counter(issue.split("=", 1)[0] for row in audits for issue in row["issues"])
    warning_counts = Counter(warn.split("=", 1)[0] for row in audits for warn in row["warnings"])
    failing = [row for row in audits if row["issues"]]
    review = [row for row in audits if row["warnings"] and not row["issues"]]

    lines = [
        f"# CreditDoc City Quality Monitor - {now}",
        "",
        f"- City guides total: {total if total is not None else 'unknown'}",
        f"- Rows checked: {len(audits)}",
        f"- Rows with issues: {len(failing)}",
        f"- Rows with warnings only: {len(review)}",
        "",
        "## Issue Summary",
        "",
    ]
    if issue_counts:
        lines.extend(f"- `{key}`: {count}" for key, count in sorted(issue_counts.items()))
    else:
        lines.append("- No hard issues found in checked rows.")

    lines.extend(["", "## Warning Summary", ""])
    if warning_counts:
        lines.extend(f"- `{key}`: {count}" for key, count in sorted(warning_counts.items()))
    else:
        lines.append("- No warnings found in checked rows.")

    lines.extend(["", "## Rows Needing Work", ""])
    if not failing and not review:
        lines.append("- None in this sample.")
    else:
        for row in failing + review[: max(0, 25 - len(failing))]:
            flags = row["issues"] + row["warnings"]
            lines.append(
                f"- `{row['slug']}` ({row['city']}, {row['state_abbr']}): "
                f"questions={row['question_count']}, title={row['title_len']}, meta={row['meta_len']}; "
                f"flags: {', '.join(flags)}"
            )
            if row["resource_review_examples"]:
                lines.append(f"  Resource review examples: {', '.join(row['resource_review_examples'])}")

    lines.extend(["", "## Next Actions", ""])
    lines.append("- Fix hard issues first: low question count, bad metadata length, generic or heavily unlocalized questions.")
    lines.append("- Treat specific local resources as review candidates, not automatic deletions.")
    lines.append("- Keep broad city coverage live while improving weak rows.")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only CreditDoc city-guide quality monitor.")
    parser.add_argument("--limit", type=int, default=50, help="Number of recent city guides to check.")
    parser.add_argument("--slug", help="Check one city guide slug.")
    parser.add_argument("--write-report", action="store_true", help="Write Markdown report into the easy-first workpack.")
    args = parser.parse_args()

    env = load_env()
    rows = fetch_rows(env, args.limit, args.slug)
    audits = [audit_row(row) for row in rows]
    report = markdown_report(count_city_guides(env), audits)
    print(report)

    if args.write_report:
        DEFAULT_REPORT_DIR.mkdir(parents=True, exist_ok=True)
        out = DEFAULT_REPORT_DIR / f"CITY_QUALITY_MONITOR_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.md"
        out.write_text(report)
        print(f"Wrote {out}")

    return 1 if any(row["issues"] for row in audits) else 0


if __name__ == "__main__":
    raise SystemExit(main())
