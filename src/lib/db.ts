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
 * SCHEMA NOTE (2026-04-29):
 *   The live `lenders` table is a catalog index — it has slug + name +
 *   category + state + processing_status + brand_slug + has_logo +
 *   seo_tier + checksum + updated_at, AND NOTHING ELSE. Body content
 *   (description, services, hours, etc.) lives in src/content/lenders/*.json
 *   today and is NOT runtime-readable from the Worker.
 *
 *   To serve a full lender body via SSR we will need either:
 *     (a) ALTER TABLE public.lenders ADD body_r2_key text, body_inline jsonb
 *         + backfill (requires Jammi greenlight — Option A in CREDITDOC_NEXT.md), OR
 *     (b) `lender_bodies` side table joined on slug.
 *
 *   Until then, this helper returns the catalog row only. The /r/[slug] pilot
 *   route renders a minimal page from the catalog row — proof-of-concept for
 *   OBJ-1, not the final UX.
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
