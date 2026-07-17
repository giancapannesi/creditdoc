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
            "WHERE category = ? AND slug != ? AND processing_status IN ('ready_for_index','pending_approval') "
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


_BRANDS_DIR = Path(__file__).resolve().parent.parent / "src" / "content" / "brands"
_brands_cache: tuple[dict[str, Any], ...] | None = None


def all_brands() -> tuple[dict[str, Any], ...]:
    """Return all brand JSONs with location_count attached from lenders table.

    Matches Astro's getAllBrands: reads every JSON file in src/content/brands/,
    then counts rows in lenders WHERE brand_slug=brand.slug.
    """
    global _brands_cache
    if _brands_cache is not None:
        return _brands_cache
    if not _BRANDS_DIR.exists():
        _brands_cache = tuple()
        return _brands_cache
    files = sorted(f for f in _BRANDS_DIR.iterdir() if f.suffix == ".json")
    # Count once, then look up per brand.
    with _connect() as conn:
        rows = conn.execute(
            "SELECT brand_slug, COUNT(*) as c FROM lenders "
            "WHERE brand_slug IS NOT NULL "
            "AND processing_status IN ('ready_for_index','pending_approval') "
            "GROUP BY brand_slug"
        ).fetchall()
    counts = {r["brand_slug"]: r["c"] for r in rows}
    out: list[dict[str, Any]] = []
    for f in files:
        try:
            brand = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        brand["location_count"] = counts.get(brand.get("slug"), 0)
        out.append(brand)
    _brands_cache = tuple(out)
    return _brands_cache


_COMPARISONS_PATH = Path(__file__).resolve().parent.parent / "src" / "content" / "comparisons.json"
_comparisons_cache: tuple[dict[str, Any], ...] | None = None


def all_comparisons() -> tuple[dict[str, Any], ...]:
    """Return every comparison whose lender_a AND lender_b are in the lenders table."""
    global _comparisons_cache
    if _comparisons_cache is not None:
        return _comparisons_cache
    if not _COMPARISONS_PATH.exists():
        _comparisons_cache = tuple()
        return _comparisons_cache
    raw = json.loads(_COMPARISONS_PATH.read_text(encoding="utf-8"))
    if not raw:
        _comparisons_cache = tuple()
        return _comparisons_cache
    # Bulk-check lender existence in one query.
    all_slugs = set()
    for c in raw:
        if c.get("lender_a"): all_slugs.add(c["lender_a"])
        if c.get("lender_b"): all_slugs.add(c["lender_b"])
    with _connect() as conn:
        placeholders = ",".join("?" * len(all_slugs))
        rows = conn.execute(
            f"SELECT slug FROM lenders WHERE slug IN ({placeholders}) "
            f"AND processing_status != 'archived' "
            f"AND (json_extract(data, '$.no_index') IS NULL OR json_extract(data, '$.no_index') = 0)",
            list(all_slugs),
        ).fetchall()
    known = {r["slug"] for r in rows}
    out = tuple(c for c in raw if c.get("lender_a") in known and c.get("lender_b") in known)
    _comparisons_cache = out
    return out


def load_comparison(slug: str) -> dict[str, Any] | None:
    for c in all_comparisons():
        if c.get("slug") == slug:
            return c
    return None


_CFPB_TRENDS_PATH = Path(__file__).resolve().parent.parent / "src" / "content" / "cfpb-trends.json"
_trends_cache: tuple[dict[str, Any], ...] | None = None


def all_trends_entries() -> tuple[dict[str, Any], ...]:
    """Return every CFPB entry that should render a /trends/<slug>/ page.

    Matches Astro's filter: exclude entries whose lender row is either
    processing_status='archived' or no_index=True. Entries with no
    matching lender row (CFPB data for a company we haven't profiled)
    still render, matching Astro's behaviour.
    """
    global _trends_cache
    if _trends_cache is not None:
        return _trends_cache
    if not _CFPB_TRENDS_PATH.exists():
        _trends_cache = tuple()
        return _trends_cache
    entries = json.loads(_CFPB_TRENDS_PATH.read_text(encoding="utf-8"))
    if not entries:
        _trends_cache = tuple()
        return _trends_cache
    # Pull lender status/no_index for every slug in one query.
    slugs = [e["slug"] for e in entries if e.get("slug")]
    lookup: dict[str, dict[str, Any]] = {}
    with _connect() as conn:
        placeholders = ",".join("?" * len(slugs))
        rows = conn.execute(
            f"SELECT slug, processing_status, "
            f"       json_extract(data, '$.no_index') as no_index "
            f"FROM lenders WHERE slug IN ({placeholders})",
            slugs,
        ).fetchall()
    for r in rows:
        lookup[r["slug"]] = {"status": r["processing_status"], "no_index": r["no_index"]}
    out = []
    for e in entries:
        info = lookup.get(e["slug"])
        if info is not None:
            if info["status"] == "archived":
                continue
            if info["no_index"]:
                continue
        out.append(e)
    _trends_cache = tuple(out)
    return _trends_cache


def load_trends_entry(slug: str) -> dict[str, Any] | None:
    for e in all_trends_entries():
        if e.get("slug") == slug:
            return e
    return None


@lru_cache(maxsize=1)
def browse_pairs(min_count: int = 5) -> tuple[tuple[str, str], ...]:
    """Enumerate every (category_slug, city_slug) pair with ≥ min_count indexable
    lenders. Matches Astro's /browse/[catSlug]/[citySlug] getStaticPaths.
    """
    out: list[tuple[str, str]] = []
    cats = [c.get("slug") for c in all_categories() if c.get("slug")]
    for city in cities_with_lenders(5):
        lenders = lenders_by_city_state(city["city"].lower(), city["state_abbr"])
        # Count by category, skip aliases (fix-my-credit collapse handled in render).
        counts: dict[str, int] = {}
        for l in lenders:
            cat = l.get("category") or ""
            counts[cat] = counts.get(cat, 0) + 1
        for cat in cats:
            if counts.get(cat, 0) >= min_count:
                out.append((cat, city["slug"]))
    return tuple(out)


def all_states_info() -> tuple[dict[str, Any], ...]:
    """Return all 50 states as {name, abbr, slug} — matches Astro's getAllStatesInfo."""
    out = []
    for abbr, full in _ABBR_TO_FULL_STATE.items():
        out.append({
            "name": full,
            "abbr": abbr,
            "slug": full.lower().replace(" ", "-"),
        })
    return tuple(sorted(out, key=lambda s: s["name"]))


@lru_cache(maxsize=64)
def lenders_in_state(state_abbr: str, limit: int | None = None) -> tuple[dict[str, Any], ...]:
    """All indexable lenders in a state (by company_info.state normalised)."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM lenders "
            "WHERE processing_status IN ('ready_for_index','pending_approval')"
        ).fetchall()
    out = []
    for r in rows:
        d = _merge_lender(r)
        ci = d.get("company_info") or {}
        if normalize_state_abbr(ci.get("state")) == state_abbr:
            out.append(d)
    if limit is not None:
        out = out[:limit]
    return tuple(out)


def state_lender_and_city_counts(state_abbr: str) -> dict[str, int]:
    """Total lender + distinct-city counts for a state."""
    rows = lenders_in_state(state_abbr)
    cities: set[str] = set()
    for l in rows:
        ci = l.get("company_info") or {}
        c = (ci.get("city") or "").strip()
        if c:
            cities.add(c.lower())
    return {"lender_count": len(rows), "city_count": len(cities)}


def load_brand(slug: str) -> dict[str, Any] | None:
    for b in all_brands():
        if b.get("slug") == slug:
            return b
    return None


@lru_cache(maxsize=64)
def lenders_by_brand(brand_slug: str) -> tuple[dict[str, Any], ...]:
    """All indexable lenders belonging to a brand (by lenders.brand_slug column)."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM lenders "
            "WHERE brand_slug = ? "
            "AND processing_status IN ('ready_for_index','pending_approval') "
            "ORDER BY slug",
            (brand_slug,),
        ).fetchall()
    return tuple(_merge_lender(r) for r in rows)


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


_STATE_ABBREVIATIONS: dict[str, str] = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA",
    "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE", "Florida": "FL", "Georgia": "GA",
    "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA",
    "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV", "New Hampshire": "NH",
    "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY", "North Carolina": "NC",
    "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA",
    "Rhode Island": "RI", "South Carolina": "SC", "South Dakota": "SD", "Tennessee": "TN",
    "Texas": "TX", "Utah": "UT", "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
    "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY",
    # NOTE: intentionally excludes "District of Columbia" to match Astro's
    # data.ts STATE_ABBREVIATIONS. Adding DC would emit a URL Astro
    # never produced.
}
_ABBR_TO_FULL_STATE: dict[str, str] = {v: k for k, v in _STATE_ABBREVIATIONS.items()}


def normalize_state_abbr(state: str | None) -> str | None:
    """Match Astro's normalizeStateAbbr: accept full name or abbr, return abbr."""
    if not state:
        return None
    trimmed = state.strip()
    if not trimmed:
        return None
    upper = trimmed.upper()
    if upper in _ABBR_TO_FULL_STATE:
        return upper
    return _STATE_ABBREVIATIONS.get(trimmed)


def slugify_city(city: str) -> str:
    """Match Astro's slugifyCity: lower, non-alnum → '-', strip edges."""
    import re as _re
    s = city.strip().lower()
    s = _re.sub(r"[^a-z0-9]+", "-", s)
    s = _re.sub(r"^-+|-+$", "", s)
    return s


@lru_cache(maxsize=1)
def cities_with_lenders(min_count: int = 5) -> tuple[dict[str, Any], ...]:
    """Cities with at least `min_count` indexable lenders.

    Groups by lower(city)+normalized-state-abbr. Slug = f"{slugify_city(city)}-{abbr.lower()}".
    """
    with _connect() as conn:
        rows = conn.execute(
            "SELECT json_extract(data, '$.company_info.city') AS city, "
            "       json_extract(data, '$.company_info.state') AS state "
            "FROM lenders "
            "WHERE processing_status IN ('ready_for_index','pending_approval')"
        ).fetchall()
    agg: dict[tuple[str, str], dict[str, Any]] = {}
    for r in rows:
        c = (r["city"] or "").strip()
        s = normalize_state_abbr(r["state"])
        if not c or not s:
            continue
        key = (c.lower(), s)
        if key in agg:
            agg[key]["count"] += 1
        else:
            agg[key] = {"city": c, "state_abbr": s, "count": 1}
    out: list[dict[str, Any]] = []
    for v in agg.values():
        if v["count"] < min_count:
            continue
        full = _ABBR_TO_FULL_STATE.get(v["state_abbr"], v["state_abbr"])
        out.append({
            "city": v["city"],
            "state": full,
            "state_abbr": v["state_abbr"],
            "slug": f"{slugify_city(v['city'])}-{v['state_abbr'].lower()}",
            "count": v["count"],
        })
    out.sort(key=lambda x: (-x["count"], x["slug"]))
    return tuple(out)


@lru_cache(maxsize=2048)
def lenders_by_city_state(city_lower: str, state_abbr: str) -> tuple[dict[str, Any], ...]:
    """All indexable lenders in a city (lowercase city, uppercase 2-letter abbr).

    Matches Astro's getLendersByCityState. Runs a broad SQL then filters in
    Python because state values in the JSON blob use both full-name and abbr
    forms and we need normalize_state_abbr semantics.
    """
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM lenders "
            "WHERE processing_status IN ('ready_for_index','pending_approval') "
            "AND LOWER(TRIM(COALESCE(json_extract(data, '$.company_info.city'), ''))) = ?",
            (city_lower,),
        ).fetchall()
    out = []
    for r in rows:
        d = _merge_lender(r)
        ci = d.get("company_info") or {}
        if normalize_state_abbr(ci.get("state")) != state_abbr:
            continue
        out.append(d)
    return tuple(out)


@lru_cache(maxsize=1)
def all_categories() -> tuple[dict[str, Any], ...]:
    """All categories rows (slug + name), for display-name lookup on hub pages."""
    with _connect() as conn:
        rows = conn.execute("SELECT slug, data FROM categories ORDER BY slug").fetchall()
    out = []
    for r in rows:
        d = json.loads(r["data"] or "{}")
        d.setdefault("slug", r["slug"])
        out.append(d)
    return tuple(out)


@lru_cache(maxsize=64)
def load_category(slug: str) -> dict[str, Any] | None:
    """Return the category row merged with its data JSON blob."""
    with _connect() as conn:
        row = conn.execute("SELECT * FROM categories WHERE slug = ?", (slug,)).fetchone()
    if row is None:
        return None
    blob = json.loads(row["data"] or "{}")
    out: dict[str, Any] = dict(blob)
    out.setdefault("slug", row["slug"])
    return out


@lru_cache(maxsize=32)
def top_lenders_by_category(category: str, limit: int = 48) -> tuple[dict[str, Any], ...]:
    """Ordered top lenders in a category for the category-grid.

    Matches Astro's getTopLendersByCategoryRuntime ordering:
    quality_score DESC (nulls last), then slug asc, restricted to indexable statuses.
    """
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM lenders "
            "WHERE category = ? AND processing_status IN ('ready_for_index','pending_approval') "
            "ORDER BY quality_score IS NULL, quality_score DESC, slug LIMIT ?",
            (category, limit),
        ).fetchall()
    return tuple(_merge_lender(r) for r in rows)


@lru_cache(maxsize=32)
def category_count(category: str) -> int:
    """Total indexable lenders in the category."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM lenders WHERE category = ? "
            "AND processing_status IN ('ready_for_index','pending_approval')",
            (category,),
        ).fetchone()
    return int(row[0]) if row else 0


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
