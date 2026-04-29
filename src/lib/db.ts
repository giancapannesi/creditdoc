/**
 * CDM-REV-2026-04-29 Phase 1.3 — Supabase READ-ONLY runtime data layer.
 *
 * Used by SSR routes (e.g. /r/[slug]) running on Cloudflare Workers.
 * Uses the anon key + Postgres RLS for safety. Service-role NEVER ships to the
 * Worker; that path stays server-side only via tools/creditdoc_db.py + the
 * Phase 2 /api/revalidate endpoint.
 *
 * IMPORTANT: this file does not auto-call Supabase at module init. The client
 * is constructed lazily so that build-time imports don't reach over the network.
 *
 * Runtime env (set as Pages secrets at deploy time, NOT committed):
 *   SUPABASE_URL          — https://<ref>.supabase.co
 *   SUPABASE_ANON_KEY     — public anon JWT (RLS-protected)
 *
 * SCHEMA NOTE (2026-04-29 — Option A.1 LANDED):
 *   `lenders` now has 14 columns: the original 12-column catalog index plus
 *   `body_inline jsonb` (full review body — description, pros, cons, pricing,
 *   services, etc.) and `body_r2_key text` (reserved for future R2 split).
 *   body_inline backfilled from src/content/lenders/<slug>.json on 2026-04-29.
 *   Use getLenderWithBodyBySlugRuntime() for full-page SSR; use
 *   getLenderBySlugRuntime() for catalog-only views.
 */

export interface RuntimeLender {
  slug: string;
  name: string;
  category: string;
  state: string | null;
  brand_slug: string | null;
  has_logo: boolean;
  seo_tier: string | null;
  /** ISO8601 — used as the cache-busting content-version. */
  updated_at: string;
}

export interface RuntimeLenderEnv {
  SUPABASE_URL?: string;
  SUPABASE_ANON_KEY?: string;
  /** R2 bucket binding for body JSON (lazy-fetched per slug — Phase 1.6 wiring). */
  ASSETS?: R2Bucket;
}

const CATALOG_COLUMNS =
  "slug,name,category,state,brand_slug,has_logo,seo_tier,updated_at";

/**
 * Read-only lookup of one lender by slug.
 * Returns null on not-found OR if the runtime env isn't wired (build/preview).
 *
 * Phase 1.3 implementation note: the Supabase client construction is deferred
 * to keep imports cheap and to avoid module-init network calls. When the
 * env vars are absent (e.g. local dev without secrets), this returns null and
 * the caller should fall back to a 404.
 */
export async function getLenderBySlugRuntime(
  slug: string,
  env?: RuntimeLenderEnv
): Promise<RuntimeLender | null> {
  if (!env?.SUPABASE_URL || !env?.SUPABASE_ANON_KEY) {
    return null;
  }

  const url =
    `${env.SUPABASE_URL}/rest/v1/lenders` +
    `?slug=eq.${encodeURIComponent(slug)}` +
    `&select=${CATALOG_COLUMNS}` +
    `&processing_status=eq.ready_for_index` +
    `&limit=1`;

  const res = await fetch(url, {
    headers: {
      apikey: env.SUPABASE_ANON_KEY,
      authorization: `Bearer ${env.SUPABASE_ANON_KEY}`,
      accept: "application/json",
    },
    signal: AbortSignal.timeout(2500),
  });
  if (!res.ok) return null;
  const rows = (await res.json()) as RuntimeLender[];
  return rows[0] ?? null;
}

/**
 * Same as getLenderBySlugRuntime but also pulls the body_inline jsonb blob.
 * Use this for full /review/[slug]-style SSR. Returns null on not-found.
 */
export interface RuntimeLenderWithBody extends RuntimeLender {
  body_inline: Record<string, unknown> | null;
}

const FULL_COLUMNS = `${CATALOG_COLUMNS},body_inline`;

export async function getLenderWithBodyBySlugRuntime(
  slug: string,
  env?: RuntimeLenderEnv
): Promise<RuntimeLenderWithBody | null> {
  if (!env?.SUPABASE_URL || !env?.SUPABASE_ANON_KEY) return null;
  const url =
    `${env.SUPABASE_URL}/rest/v1/lenders` +
    `?slug=eq.${encodeURIComponent(slug)}` +
    `&select=${FULL_COLUMNS}` +
    `&processing_status=eq.ready_for_index` +
    `&limit=1`;
  const res = await fetch(url, {
    headers: {
      apikey: env.SUPABASE_ANON_KEY,
      authorization: `Bearer ${env.SUPABASE_ANON_KEY}`,
      accept: "application/json",
    },
    signal: AbortSignal.timeout(2500),
  });
  if (!res.ok) return null;
  const rows = (await res.json()) as RuntimeLenderWithBody[];
  return rows[0] ?? null;
}

/**
 * Catalog-only listing of lenders in a category, ordered by rating desc.
 * Used by /review/[slug] SSR for the related-lender sidebar (replaces the
 * build-time `getAllLenders().filter(...).sort(...)` chain). Returns up to
 * `limit` rows excluding `excludeSlug`.
 *
 * NOTE: PostgREST treats `select=` columns as projection — we use the catalog
 * columns only (no body_inline) to keep the response payload small.
 */
export async function getRelatedLendersByCategoryRuntime(
  category: string,
  excludeSlug: string,
  env?: RuntimeLenderEnv,
  limit = 10
): Promise<RuntimeLender[]> {
  if (!env?.SUPABASE_URL || !env?.SUPABASE_ANON_KEY) return [];
  const url =
    `${env.SUPABASE_URL}/rest/v1/lenders` +
    `?category=eq.${encodeURIComponent(category)}` +
    `&slug=neq.${encodeURIComponent(excludeSlug)}` +
    `&processing_status=eq.ready_for_index` +
    `&select=${CATALOG_COLUMNS}` +
    `&order=updated_at.desc` +
    `&limit=${limit}`;
  const res = await fetch(url, {
    headers: {
      apikey: env.SUPABASE_ANON_KEY,
      authorization: `Bearer ${env.SUPABASE_ANON_KEY}`,
      accept: "application/json",
    },
    signal: AbortSignal.timeout(2500),
  });
  if (!res.ok) return [];
  return (await res.json()) as RuntimeLender[];
}

/**
 * Catalog-only fetch of multiple specific slugs. Used to resolve the
 * `similar_lenders` array (which stores slugs) into catalog rows for the
 * related-lender sidebar.
 */
export async function getLendersBySlugListRuntime(
  slugs: string[],
  env?: RuntimeLenderEnv
): Promise<RuntimeLender[]> {
  if (!env?.SUPABASE_URL || !env?.SUPABASE_ANON_KEY) return [];
  if (!slugs.length) return [];
  const inList = slugs.map(encodeURIComponent).join(",");
  const url =
    `${env.SUPABASE_URL}/rest/v1/lenders` +
    `?slug=in.(${inList})` +
    `&processing_status=eq.ready_for_index` +
    `&select=${CATALOG_COLUMNS}` +
    `&limit=${slugs.length}`;
  const res = await fetch(url, {
    headers: {
      apikey: env.SUPABASE_ANON_KEY,
      authorization: `Bearer ${env.SUPABASE_ANON_KEY}`,
      accept: "application/json",
    },
    signal: AbortSignal.timeout(2500),
  });
  if (!res.ok) return [];
  return (await res.json()) as RuntimeLender[];
}

/**
 * Convert ISO updated_at to a stable monotonic int for cache key.
 */
export function contentVersionOf(lender: RuntimeLender): number {
  const t = Date.parse(lender.updated_at);
  return Number.isFinite(t) ? Math.floor(t / 1000) : 0;
}

// ============================================================================
// CDM-REV Stage A.2 — wellness_guides / comparisons / brands runtime fetchers
// ============================================================================
// Same pattern as lenders: PostgREST anon read, body_inline jsonb holds the
// full document, RLS-protected, set_updated_at trigger bumps cache key on any
// row write. Returns [] / null when env not wired (build/preview without secrets)
// so callers degrade gracefully.

async function _restGet<T>(
  url: string,
  env: RuntimeLenderEnv | undefined
): Promise<T[] | null> {
  if (!env?.SUPABASE_URL || !env?.SUPABASE_ANON_KEY) return null;
  const res = await fetch(url, {
    headers: {
      apikey: env.SUPABASE_ANON_KEY,
      authorization: `Bearer ${env.SUPABASE_ANON_KEY}`,
      accept: "application/json",
    },
    signal: AbortSignal.timeout(2500),
  });
  if (!res.ok) return null;
  return (await res.json()) as T[];
}

export interface RuntimeWellnessGuide {
  slug: string;
  title: string;
  category: string | null;
  body_inline: Record<string, unknown> | null;
  updated_at: string;
}

export async function getWellnessGuidesByCategoryRuntime(
  category: string,
  env?: RuntimeLenderEnv,
  limit = 6
): Promise<RuntimeWellnessGuide[]> {
  if (!category) return [];
  const url =
    `${env?.SUPABASE_URL}/rest/v1/wellness_guides` +
    `?category=eq.${encodeURIComponent(category)}` +
    `&select=slug,title,category,body_inline,updated_at` +
    `&order=updated_at.desc` +
    `&limit=${limit}`;
  const rows = await _restGet<RuntimeWellnessGuide>(url, env);
  return rows ?? [];
}

export interface RuntimeComparison {
  slug: string;
  lender_a: string;
  lender_b: string;
  body_inline: Record<string, unknown> | null;
  updated_at: string;
}

/**
 * Comparisons that mention the given lender slug as either side.
 * Used by /review/[slug] to render the "vs other lenders" sidebar.
 */
export async function getComparisonsForLenderRuntime(
  lenderSlug: string,
  env?: RuntimeLenderEnv,
  limit = 6
): Promise<RuntimeComparison[]> {
  if (!lenderSlug) return [];
  const slugEnc = encodeURIComponent(lenderSlug);
  const url =
    `${env?.SUPABASE_URL}/rest/v1/comparisons` +
    `?or=(lender_a.eq.${slugEnc},lender_b.eq.${slugEnc})` +
    `&select=slug,lender_a,lender_b,body_inline,updated_at` +
    `&order=updated_at.desc` +
    `&limit=${limit}`;
  const rows = await _restGet<RuntimeComparison>(url, env);
  return rows ?? [];
}

export interface RuntimeBrand {
  slug: string;
  display_name: string;
  category: string | null;
  body_inline: Record<string, unknown> | null;
  updated_at: string;
}

export async function getBrandBySlugRuntime(
  slug: string,
  env?: RuntimeLenderEnv
): Promise<RuntimeBrand | null> {
  if (!slug) return null;
  const url =
    `${env?.SUPABASE_URL}/rest/v1/brands` +
    `?slug=eq.${encodeURIComponent(slug)}` +
    `&select=slug,display_name,category,body_inline,updated_at` +
    `&limit=1`;
  const rows = await _restGet<RuntimeBrand>(url, env);
  return rows?.[0] ?? null;
}

// Type alias for Cloudflare Workers R2 binding (no @cloudflare/workers-types
// import to keep the dep graph tight; the adapter provides the runtime).
type R2Bucket = {
  get(key: string): Promise<R2Object | null>;
};
type R2Object = {
  json<T>(): Promise<T>;
};
