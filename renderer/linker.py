"""
Inline linker — Python port of src/utils/inline-linker.ts (money links only).

Wraps whole-word matches of high-value phrases with <a> tags pointing to the
mapped destination. Enforces:
    - Each unique phrase linked at most once per description
    - Each destination URL linked at most once per description
    - Total money links capped by budget (default 4)
    - Longest phrase wins on overlap
    - Case-insensitive whole-word matching only

Glossary + affiliate variants are Phase-2 additions; this MVP covers the
biggest parity gap (money links account for most of Astro's inline <a> tags
in description_long bodies).
"""
from __future__ import annotations

import html
import re
from typing import Iterable

from _money_links import MONEY_LINKS  # type: ignore

# Sort longest-first so "credit repair companies" matches before "credit repair".
_SORTED = sorted(MONEY_LINKS, key=lambda p: -len(p[0]))


def _escape(text: str) -> str:
    return html.escape(text, quote=True)


def linkify_description(
    text: str,
    current_slug: str = "",
    current_category: str = "",
    money_budget: int = 4,
) -> str:
    """Return text with money-link phrases wrapped as <a> tags."""
    if not text:
        return text

    self_ref_url = f"/categories/{current_category}/" if current_category else ""
    used_phrases: set[str] = set()
    used_urls: set[str] = set()
    remaining = money_budget

    # Build a mask of already-linked character positions to prevent overlap.
    linked_mask = [False] * len(text)
    # Replacements collected as (start, end, replacement_html), applied right-to-left.
    replacements: list[tuple[int, int, str]] = []

    for phrase, url in _SORTED:
        if remaining <= 0:
            break
        low = phrase.lower()
        if low in used_phrases:
            continue
        if url in used_urls:
            continue
        if url == self_ref_url:
            continue
        # Whole-word, case-insensitive. Escape regex specials in the phrase.
        pattern = re.compile(r"\b" + re.escape(phrase) + r"\b", re.IGNORECASE)
        m = pattern.search(text)
        if not m:
            continue
        start, end = m.span()
        if any(linked_mask[start:end]):
            continue
        matched_text = m.group(0)
        replacement = (
            f'<a href="{_escape(url)}" class="text-primary hover:underline">'
            f"{_escape(matched_text)}</a>"
        )
        replacements.append((start, end, replacement))
        for i in range(start, end):
            linked_mask[i] = True
        used_phrases.add(low)
        used_urls.add(url)
        remaining -= 1

    if not replacements:
        return text

    # Apply right-to-left so earlier offsets remain valid.
    replacements.sort(key=lambda r: -r[0])
    out = text
    for start, end, replacement in replacements:
        out = out[:start] + replacement + out[end:]
    return out


def auto_paragraphs(text: str) -> str:
    """Ensure the text is split into paragraphs on double newlines. Passthrough for now."""
    if not text:
        return ""
    return text
