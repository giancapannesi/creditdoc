"""Build-time equivalents of Supabase-backed data for the renderer.

Mirrors `src/utils/data-build-remote.ts` (which the Astro build used). The
Python renderer needs the same shape: fetch all `city_guides` + related
tables ONCE via HTTP, cache in-memory, hand out from cache during the
render pass.

Never called from the runtime Cloudflare Worker — build-time only. The
Worker reads Supabase directly via PostgREST in `worker/handlers/*.ts`
where dynamic freshness is required.

Env: reads SUPABASE_URL + SUPABASE_ANON_KEY from
`/srv/BusinessOps/tools/.supabase-creditdoc.env` if not already exported.
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

_SUPABASE_ENV_PATH = Path("/srv/BusinessOps/tools/.supabase-creditdoc.env")


def _load_env() -> tuple[str, str]:
    url = os.environ.get("SUPABASE_URL", "")
    anon = os.environ.get("SUPABASE_ANON_KEY", "")
    if url and anon:
        return url, anon
    try:
        for line in _SUPABASE_ENV_PATH.read_text().splitlines():
            if line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            v = v.strip().strip('"').strip("'")
            if k == "SUPABASE_URL" and not url:
                url = v
            elif k == "SUPABASE_ANON_KEY" and not anon:
                anon = v
    except FileNotFoundError:
        pass
    return url, anon


def _fetch(path_and_query: str) -> list[dict[str, Any]]:
    url, anon = _load_env()
    if not url or not anon:
        return []
    full = f"{url.rstrip('/')}/rest/v1/{path_and_query}"
    req = urllib.request.Request(
        full,
        headers={"apikey": anon, "Authorization": f"Bearer {anon}"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ─── city_guides ──────────────────────────────────────────────────────

_city_guides_cache: list[dict[str, Any]] | None = None


def all_city_guides() -> list[dict[str, Any]]:
    """All city_guides rows with status='ready_for_index'. Cached."""
    global _city_guides_cache
    if _city_guides_cache is not None:
        return _city_guides_cache
    query = urllib.parse.quote(
        "status=eq.ready_for_index"
        "&select=slug,city,state_abbr,state_name,population,body_inline,updated_at",
        safe="=&",
    )
    _city_guides_cache = _fetch(f"city_guides?{query}")
    return _city_guides_cache


def get_city_guide(slug: str) -> dict[str, Any] | None:
    for g in all_city_guides():
        if g.get("slug") == slug:
            return g
    return None


def city_guides_by_state(state_abbr: str) -> list[dict[str, Any]]:
    return [g for g in all_city_guides() if g.get("state_abbr") == state_abbr]


# ─── HMDA top lenders (for local trust signal on hub) ─────────────────

_hmda_cache: dict[str, list[dict[str, Any]]] = {}


def hmda_top_lenders_by_state(state_abbr: str, limit: int = 10) -> list[dict[str, Any]]:
    if state_abbr in _hmda_cache:
        return _hmda_cache[state_abbr][:limit]
    query = urllib.parse.quote(
        f"state_abbr=eq.{state_abbr}"
        "&select=lei,institution_name,total_originations,total_applications"
        "&order=total_originations.desc.nullslast"
        f"&limit={max(limit, 25)}",
        safe="=&",
    )
    try:
        rows = _fetch(f"hmda_geo?{query}")
    except Exception:
        rows = []
    _hmda_cache[state_abbr] = rows
    return rows[:limit]


# ─── smoke test ───────────────────────────────────────────────────────

if __name__ == "__main__":
    guides = all_city_guides()
    print(f"[db_remote] loaded {len(guides)} city_guides")
    if guides:
        sample = guides[0]
        print(f"[db_remote] sample: slug={sample.get('slug')} city={sample.get('city')} "
              f"state={sample.get('state_abbr')} body_keys="
              f"{list((sample.get('body_inline') or {}).keys())[:5]}")
    hmda_ca = hmda_top_lenders_by_state("CA", limit=3)
    print(f"[db_remote] HMDA CA top 3: {[r.get('institution_name') for r in hmda_ca]}")
