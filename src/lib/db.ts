/**
 * CDM-REV-2026-04-29 Phase 1.3 — Supabase READ-ONLY runtime data layer.
 *
 * Used by SSR routes (e.g. /review/[slug]) running on Cloudflare Workers.
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
 */

// Phase 1.3 status: SCAFFOLDING ONLY. The actual Supabase client is added in
// the next iteration once Jammi greenlights the data-flow change. The shape
// + interface below are stable so callers can be written against them today.

export interface RuntimeLender {
  slug: string;
  brand_name: string;
  category: string;
  state?: string;
  city?: string;
  rating?: number;
  /** ISO8601 — used as the cache-busting content-version. */
  updated_at: string;
  /** R2 object key for the body JSON; null if body lives in catalog row. */
  body_r2_key?: string | null;
  /** Catalog-row body (used while R2 migration is incomplete). */
  body_inline?: Record<string, unknown> | null;
}

export interface RuntimeLenderEnv {
  SUPABASE_URL?: string;
  SUPABASE_ANON_KEY?: string;
  /** R2 bucket binding for body JSON (lazy-fetched per slug). */
  ASSETS?: R2Bucket;
}

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
    // Build-time / preview without secrets — caller falls back to 404 or
    // build-time content-collection helper.
    return null;
  }

  // PostgREST GET with RLS. Single-row fetch.
  const url = `${env.SUPABASE_URL}/rest/v1/lenders` +
    `?slug=eq.${encodeURIComponent(slug)}` +
    `&select=slug,brand_name,category,state,city,rating,updated_at,body_r2_key,body_inline` +
    `&processing_status=eq.ready_for_index` +
    `&limit=1`;

  const res = await fetch(url, {
    headers: {
      apikey: env.SUPABASE_ANON_KEY,
      authorization: `Bearer ${env.SUPABASE_ANON_KEY}`,
      accept: 'application/json',
    },
    // Tight timeout — SSR routes must stay fast.
    signal: AbortSignal.timeout(2500),
  });
  if (!res.ok) return null;
  const rows = (await res.json()) as RuntimeLender[];
  return rows[0] ?? null;
}

/**
 * Fetch the body JSON for a lender from R2 if the catalog row points to one.
 * Falls back to body_inline if no R2 key.
 */
export async function getLenderBody(
  lender: RuntimeLender,
  env?: RuntimeLenderEnv
): Promise<Record<string, unknown> | null> {
  if (lender.body_inline) return lender.body_inline;
  if (!lender.body_r2_key || !env?.ASSETS) return null;
  const obj = await env.ASSETS.get(lender.body_r2_key);
  if (!obj) return null;
  return (await obj.json<Record<string, unknown>>()) ?? null;
}

/**
 * Convert ISO updated_at to a stable monotonic int for cache key.
 */
export function contentVersionOf(lender: RuntimeLender): number {
  const t = Date.parse(lender.updated_at);
  return Number.isFinite(t) ? Math.floor(t / 1000) : 0;
}

// Type alias for Cloudflare Workers R2 binding (no @cloudflare/workers-types
// import to keep the dep graph tight; the adapter provides the runtime).
type R2Bucket = {
  get(key: string): Promise<R2Object | null>;
};
type R2Object = {
  json<T>(): Promise<T>;
};
