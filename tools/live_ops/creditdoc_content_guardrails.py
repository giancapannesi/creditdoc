#!/usr/bin/env python3
"""Shared CreditDoc content safety checks for generated pages.

These checks are intentionally narrow. They are not a legal rewrite layer; they
stop generated content from publishing invented current pricing, rates, ratings,
guarantees, or certainty claims that were not supplied as source facts.
"""

from __future__ import annotations

import re
from typing import Any, Iterable


CURRENT_FACT_KEYWORDS = re.compile(
    r"\b("
    r"price|pricing|cost|costs|fee|fees|APR|rate|rates|interest|origination|"
    r"monthly|month|setup|annual|subscription|plan|tier|guarantee|guaranteed|"
    r"approval|approvals?|approves?|applicants?|"
    r"BBB|Google|Google rating|reviews?|stars?|rating"
    r")\b",
    re.I,
)

PROVIDER_FACT_CONTEXT = re.compile(
    r"\b("
    r"company|provider|lender|loan|loans|card|app|service|program|plan|tier|package|"
    r"charges?|costs?|starts? at|as low as|monthly|setup|annual|subscription|"
    r"origination|application fee|late fee|guarantee|approval|approvals?|approves?|"
    r"applicants?|BBB|Google|reviews?|stars?|rating"
    r")\b",
    re.I,
)

CERTAINTY_CLAIMS = [
    re.compile(r"\bguaranteed approval\b", re.I),
    re.compile(r"\bguarantee(?:s|d)? (?:a|your)? ?(?:score increase|credit score|approval|results?)\b", re.I),
    re.compile(r"\bmoney[- ]back guarantee\b", re.I),
    re.compile(r"\b(?:will|can) (?:raise|increase|boost) your credit score by \d+", re.I),
    re.compile(r"\bapprove(?:s|d)? (?:everyone|all applicants|any borrower)\b", re.I),
    re.compile(r"\bapprove(?:s|d)?\s+\d+(?:\.\d+)?\s*%\s+of\s+applicants\b", re.I),
    re.compile(r"\bno one (?:beats|offers lower|is cheaper than)\b", re.I),
]

VALUE_RE = re.compile(
    r"(?<![\w/])(?:"
    r"\$[0-9][0-9,]*(?:\.[0-9]{1,2})?(?:\s+(?:k|m|million|billion)\b)?"
    r"|[0-9]+(?:\.[0-9]+)?\s*%(?:\s*(?:APR|MAPR|interest|rate))?"
    r"|(?:APR|MAPR)\s*(?:of|at|from|between|up to|as high as|as low as)?\s*[0-9]+(?:\.[0-9]+)?\s*%"
    r"|BBB\s+Rating:\s*[A-F][+-]?"
    r"|BBB\s+[A-F][+-]?\s*(?:rating|rated)"
    r"|[A-F][+-]?\s*(?:BBB\s*)?(?:rating|rated)"
    r"|\d+(?:\.\d+)?\s*(?:out of|/)\s*5(?:\s*(?:Google|star|rating|stars?))?"
    r")",
    re.I,
)

COMPARISON_CLAUSE_SPLIT_RE = re.compile(
    r"\s*(?:,?\s+\b(?:while|whereas)\b\s+|\s+\b(?:compared to|versus|vs\.?)\b\s+)\s*",
    re.I,
)


def content_text(obj: Any) -> str:
    """Flatten nested generated JSON into searchable text."""
    if obj is None:
        return ""
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict):
        return "\n".join(content_text(v) for v in obj.values())
    if isinstance(obj, list):
        return "\n".join(content_text(v) for v in obj)
    return str(obj)


def normalize_value(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def canonical_value(value: str) -> str:
    value = normalize_value(value)
    value = re.sub(r"[,.;:]+$", "", value)
    rating = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:out of|/)\s*5\b", value, re.I)
    if rating:
        return f"{rating.group(1)} out of 5"
    bbb_rating = re.search(r"\bBBB\s+Rating:\s*([A-F][+-]?)(?=\W|$)", value, re.I)
    if bbb_rating:
        return bbb_rating.group(1).lower()
    bbb_rating_reversed = re.search(r"\bRating:\s*([A-F][+-]?)(?=\W|$)", value, re.I)
    if bbb_rating_reversed:
        return bbb_rating_reversed.group(1).lower()
    bbb_prefix = re.search(r"\bBBB\s+([A-F][+-]?)(?=\W|$)\s*(?:rating|rated)\b", value, re.I)
    if bbb_prefix:
        return bbb_prefix.group(1).lower()
    value = re.sub(r"\s*(?:google|bbb|star|stars|rating|rated|reviews?)\b", "", value).strip()
    value = re.sub(r"\s+", " ", value)
    return value


def extract_current_fact_values(text: str) -> list[str]:
    return [canonical_value(m.group(0)) for m in VALUE_RE.finditer(text or "")]


def supplied_fact_values(parts: Iterable[Any]) -> set[str]:
    values: set[str] = set()
    for part in parts:
        values.update(extract_current_fact_values(content_text(part)))
    return values


def unsupported_current_fact_claims(obj: Any, allowed_values: Iterable[str] = ()) -> list[str]:
    """Return value claims that look like current provider facts but lack support.

    Generic educational ranges are allowed unless they are phrased as current
    product/provider pricing, rates, ratings, or guarantees.
    """
    text = content_text(obj)
    allowed = {canonical_value(v) for v in allowed_values}
    violations: list[str] = []

    for match in VALUE_RE.finditer(text):
        value = canonical_value(match.group(0))
        window = text[max(0, match.start() - 130): match.end() + 130]
        if not CURRENT_FACT_KEYWORDS.search(window) or not PROVIDER_FACT_CONTEXT.search(window):
            continue
        if value in allowed:
            continue
        excerpt = " ".join(window.split())
        violations.append(f"{match.group(0)} :: {excerpt[:260]}")

    return violations


def unsupported_entity_value_claims(
    obj: Any,
    entity_allowed_values: dict[str, Iterable[str]],
) -> list[str]:
    """Return sourced-looking values assigned to the wrong named entity.

    This is mainly for comparison pages. A value being supplied somewhere in a
    two-company prompt is not enough; if a sentence names one company, the value
    in that sentence must be present in that company's own source summary.
    """
    text = content_text(obj)
    allowed_by_entity = {
        entity.lower(): {canonical_value(v) for v in values}
        for entity, values in entity_allowed_values.items()
        if entity
    }
    if not allowed_by_entity:
        return []

    sentences = re.split(r"(?<=[.!?])\s+|[;\n]", text)
    chunks = []
    for sentence in sentences:
        chunks.extend(part for part in COMPARISON_CLAUSE_SPLIT_RE.split(sentence) if part.strip())
    violations: list[str] = []
    for chunk in chunks:
        values = VALUE_RE.findall(chunk)
        if not values:
            continue
        lower_chunk = chunk.lower()
        for entity, allowed in allowed_by_entity.items():
            if entity not in lower_chunk:
                continue
            for raw_value in values:
                value = canonical_value(raw_value)
                if value in allowed:
                    continue
                excerpt = " ".join(chunk.split())
                violations.append(f"{entity}: {raw_value} :: {excerpt[:260]}")
    return violations


def prohibited_certainty_claims(obj: Any) -> list[str]:
    text = content_text(obj)
    violations: list[str] = []
    for pattern in CERTAINTY_CLAIMS:
        match = pattern.search(text)
        if not match:
            continue
        excerpt = " ".join(text[max(0, match.start() - 100): match.end() + 160].split())
        violations.append(excerpt[:260])
    return violations


def reject_if_unsafe(
    obj: Any,
    *,
    allowed_values: Iterable[str] = (),
    entity_allowed_values: dict[str, Iterable[str]] | None = None,
    allow_unsourced_current_facts: bool = False,
) -> list[str]:
    """Return blocking guardrail failures for generated CreditDoc content."""
    failures = []
    if not allow_unsourced_current_facts:
        for claim in unsupported_current_fact_claims(obj, allowed_values=allowed_values):
            failures.append(f"unsupported current pricing/rating/rate fact: {claim}")
    if entity_allowed_values:
        for claim in unsupported_entity_value_claims(obj, entity_allowed_values):
            failures.append(f"misattributed sourced value: {claim}")
    for claim in prohibited_certainty_claims(obj):
        failures.append(f"prohibited certainty claim: {claim}")
    return failures
