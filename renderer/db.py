"""
DB helpers for the renderer — replaces the JSON-file reads in src/utils/data-build.ts.

Everything reads from data/creditdoc.db directly. No JSON cache layer.
This is the direct expression of the founder's original architecture:
DB is truth, renderer reads truth.
"""
from __future__ import annotations

import json
import sqlite3
from functools import lru_cache
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "creditdoc.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _merge_lender(row: sqlite3.Row) -> dict[str, Any]:
    """Merge column fields into the JSON blob, columns win."""
    blob = json.loads(row["data"] or "{}")
    merged: dict[str, Any] = dict(blob)
    for k in row.keys():
        if k == "data":
            continue
        v = row[k]
        if v is not None or k not in merged:
            merged[k] = v
    if "is_protected" in merged and merged["is_protected"] is not None:
        merged["is_protected"] = bool(merged["is_protected"])
    if "is_enriched" in merged and merged["is_enriched"] is not None:
        merged["is_enriched"] = bool(merged["is_enriched"])
    return merged


def load_lender(slug: str) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM lenders WHERE slug = ?", (slug,)).fetchone()
    return _merge_lender(row) if row else None


@lru_cache(maxsize=64)
def similar_lenders(category: str, exclude_slug: str, limit: int = 4) -> tuple[dict[str, Any], ...]:
    """Category peers for the Similar Companies block. Cached because many pages share categories."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM lenders "
            "WHERE category = ? AND slug != ? AND processing_status IN ('ready_for_index','approved') "
            "AND quality_score IS NOT NULL "
            "ORDER BY quality_score DESC, slug LIMIT ?",
            (category, exclude_slug, limit),
        ).fetchall()
    return tuple(_merge_lender(r) for r in rows)


@lru_cache(maxsize=32)
def related_answers(pillar: str, limit: int = 6) -> tuple[dict[str, Any], ...]:
    """Cluster answers matching a pillar — powers the Related Questions block."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT slug, title, h1, meta_description, primary_phrase "
            "FROM cluster_answers WHERE cluster_pillar = ? "
            "AND status IN ('published','approved') "
            "ORDER BY slug LIMIT ?",
            (pillar, limit),
        ).fetchall()
    return tuple(dict(r) for r in rows)


@lru_cache(maxsize=32)
def wellness_guides_by_category(category: str, limit: int = 4) -> tuple[dict[str, Any], ...]:
    """Wellness guides matching a category — powers Financial Wellness Guides block."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT slug, data FROM wellness_guides "
            "WHERE json_extract(data, '$.category') = ? "
            "ORDER BY slug LIMIT ?",
            (category, limit),
        ).fetchall()
    result = []
    for r in rows:
        d = json.loads(r["data"] or "{}")
        d["slug"] = r["slug"]
        result.append(d)
    return tuple(result)


_STATES_JSON_PATH = Path(__file__).resolve().parent.parent / "src" / "content" / "states.json"
_GLOSSARY_JSON_PATH = Path(__file__).resolve().parent.parent / "src" / "content" / "glossary-terms.json"
_states_cache: dict[str, dict[str, Any]] | None = None
_glossary_cache: list[dict[str, Any]] | None = None


def _load_glossary() -> list[dict[str, Any]]:
    global _glossary_cache
    if _glossary_cache is None:
        try:
            _glossary_cache = json.loads(_GLOSSARY_JSON_PATH.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            _glossary_cache = []
    return _glossary_cache


def glossary_for_review(category: str, limit: int = 12) -> list[dict[str, Any]]:
    """Return glossary terms matching a review-page context for the given category."""
    all_terms = _load_glossary()
    ctx = f"review-{category}"
    generic = "review-general"
    matches = []
    for t in all_terms:
        contexts = t.get("page_contexts") or []
        if ctx in contexts or generic in contexts or "review-all" in contexts:
            matches.append(t)
    # Category-agnostic: if too few matches, pad with credit-scoring terms
    if len(matches) < limit:
        for t in all_terms:
            if t in matches:
                continue
            cat = t.get("category", "")
            if cat in ("credit-and-scoring", "how-loans-work"):
                matches.append(t)
            if len(matches) >= limit:
                break
    return matches[:limit]


def _load_states_json() -> dict[str, dict[str, Any]]:
    global _states_cache
    if _states_cache is None:
        try:
            _states_cache = json.loads(_STATES_JSON_PATH.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            _states_cache = {}
    return _states_cache


@lru_cache(maxsize=64)
def state_context(state_name_or_abbr: str | None) -> dict[str, Any] | None:
    """Look up state regulatory context by name OR abbr.

    Two-tier: try DB state_regulatory_data first, fall back to src/content/states.json
    (which is the actual source for the Astro build until the DB table is populated).
    """
    if not state_name_or_abbr:
        return None
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM state_regulatory_data "
            "WHERE state_name = ? OR state_code = ? LIMIT 1",
            (state_name_or_abbr, state_name_or_abbr),
        ).fetchone()
    if row:
        return dict(row)
    # Fall back to states.json (Astro's actual data source)
    states = _load_states_json()
    if state_name_or_abbr in states:
        d = dict(states[state_name_or_abbr])
        d.setdefault("state_name", d.get("name"))
        d.setdefault("state_code", state_name_or_abbr)
        return d
    for abbr, info in states.items():
        if isinstance(info, dict) and info.get("name") == state_name_or_abbr:
            d = dict(info)
            d.setdefault("state_name", d.get("name"))
            d.setdefault("state_code", abbr)
            return d
    return None


def load_wellness_guide(slug: str) -> dict[str, Any] | None:
    """Load one wellness_guides row + merge JSON blob."""
    with _connect() as conn:
        row = conn.execute("SELECT * FROM wellness_guides WHERE slug = ?", (slug,)).fetchone()
    if not row:
        return None
    blob = json.loads(row["data"] or "{}")
    merged: dict[str, Any] = dict(blob)
    for k in row.keys():
        if k == "data":
            continue
        v = row[k]
        if v is not None or k not in merged:
            merged[k] = v
    return merged


@lru_cache(maxsize=32)
def sibling_wellness_guides(exclude_slug: str, category: str, limit: int = 4) -> tuple[dict[str, Any], ...]:
    """Sibling wellness guides in the same category."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT slug, data FROM wellness_guides "
            "WHERE slug != ? AND json_extract(data, '$.category') = ? "
            "ORDER BY slug LIMIT ?",
            (exclude_slug, category, limit),
        ).fetchall()
    result = []
    for r in rows:
        d = json.loads(r["data"] or "{}")
        d["slug"] = r["slug"]
        result.append(d)
    return tuple(result)


def load_blog_post(slug: str) -> dict[str, Any] | None:
    """Load one blog_posts row + merge JSON blob."""
    with _connect() as conn:
        row = conn.execute("SELECT * FROM blog_posts WHERE slug = ?", (slug,)).fetchone()
    if not row:
        return None
    blob = json.loads(row["data"] or "{}")
    merged: dict[str, Any] = dict(blob)
    for k in row.keys():
        if k == "data":
            continue
        v = row[k]
        if v is not None or k not in merged:
            merged[k] = v
    return merged


@lru_cache(maxsize=32)
def sibling_blog_posts(exclude_slug: str, category: str, limit: int = 4) -> tuple[dict[str, Any], ...]:
    """Sibling blog posts from the same category."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT slug, data FROM blog_posts "
            "WHERE slug != ? AND status = 'published' AND json_extract(data, '$.category') = ? "
            "ORDER BY json_extract(data, '$.publish_date') DESC LIMIT ?",
            (exclude_slug, category, limit),
        ).fetchall()
    result = []
    for r in rows:
        d = json.loads(r["data"] or "{}")
        d["slug"] = r["slug"]
        result.append(d)
    return tuple(result)


def load_cluster_answer(slug: str) -> dict[str, Any] | None:
    """Load one cluster_answer row + merge JSON blob."""
    with _connect() as conn:
        row = conn.execute("SELECT * FROM cluster_answers WHERE slug = ?", (slug,)).fetchone()
    if not row:
        return None
    blob = json.loads(row["data"] or "{}")
    merged: dict[str, Any] = dict(blob)
    for k in row.keys():
        if k == "data":
            continue
        v = row[k]
        if v is not None or k not in merged:
            merged[k] = v
    return merged


@lru_cache(maxsize=32)
def sibling_cluster_answers(exclude_slug: str, cluster_pillar: str, limit: int = 4) -> tuple[dict[str, Any], ...]:
    """Siblings from the same cluster pillar."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT slug, title, h1, cluster_pillar FROM cluster_answers "
            "WHERE cluster_pillar = ? AND slug != ? AND status IN ('published','approved') "
            "ORDER BY slug LIMIT ?",
            (cluster_pillar, exclude_slug, limit),
        ).fetchall()
    return tuple(dict(r) for r in rows)


def category_to_pillar(category: str) -> str:
    """Map lender category → cluster answer pillar (matches Astro logic)."""
    mapping = {
        "credit-repair": "credit-repair",
        "credit-monitoring": "credit-monitoring",
        "debt-relief": "debt-relief",
        "debt-consolidation": "debt-consolidation",
        "personal-loans": "personal-loans",
        "business-loans": "business-loans",
        "sba-loans": "sba-loans",
        "credit-unions": "credit-unions",
        "credit-cards": "credit-cards",
        "banking": "banking",
    }
    return mapping.get(category, "credit-repair")
