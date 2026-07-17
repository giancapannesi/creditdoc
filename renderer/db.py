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
