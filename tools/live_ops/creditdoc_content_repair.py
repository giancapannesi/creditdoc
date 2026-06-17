#!/usr/bin/env python3
"""Repair helpers for generated CreditDoc JSON content.

Guardrails should block unsafe output, but generators should first try to fix
model mistakes that are repairable. This module keeps that repair pass shared:
preserve JSON shape, remove unsupported current facts, then revalidate.
"""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Any, Iterable


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from creditdoc_content_guardrails import reject_if_unsafe  # noqa: E402


def _extract_json(text: str) -> Any:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end > start:
            return json.loads(cleaned[start:end + 1])
        raise


def repair_unsafe_json(
    obj: Any,
    failures: list[str],
    *,
    content_type: str,
    source_context: str = "",
    allowed_values: Iterable[str] = (),
    entity_allowed_values: dict[str, Iterable[str]] | None = None,
    max_tokens: int = 4096,
    timeout_secs: int = 120,
) -> tuple[Any, list[str]]:
    """Repair generated JSON once and return `(candidate, remaining_failures)`.

    The repair prompt is intentionally conservative. It does not ask the model
    to add facts. It asks it to remove or rewrite only the flagged unsupported
    current claims, preserve the existing structure, and return JSON only.
    """
    from creditdoc_oauth import call_ai

    prompt = f"""Repair this {content_type} JSON so it passes CreditDoc guardrails.

Guardrail failures:
{json.dumps(failures[:12], indent=2)}

Source facts that may be used:
{source_context or "No additional source facts supplied. Do not add new current prices, APRs, ratings, review counts, guarantees, approval odds, or company claims."}

Rules:
- Return one valid JSON object only. No markdown fences.
- Preserve the same top-level keys and JSON shape.
- Do not invent replacement facts.
- If a price, APR, rate, BBB rating, Google rating, review count, guarantee, approval rate, or current company claim is not clearly supplied in the source facts, remove it or rewrite it generically.
- For comparison pages, write fact claims one company at a time. Do not combine two companies and two values in a single sentence if that makes attribution ambiguous.
- Keep educational, legal, and public-program context only when it is sourced.
- Keep the content useful and natural after removing unsafe claims.

JSON to repair:
{json.dumps(obj, ensure_ascii=False)}
"""
    repaired_text = call_ai(prompt, model="opus", max_tokens=max_tokens, timeout_secs=timeout_secs)
    repaired = _extract_json(repaired_text)
    remaining = reject_if_unsafe(
        repaired,
        allowed_values=allowed_values,
        entity_allowed_values=entity_allowed_values,
    )
    return repaired, remaining
