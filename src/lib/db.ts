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
 * Catalog + body_inline fetch of multiple specific slugs. Used to resolve the
 * `similar_lenders` array (which stores slugs) into full hydratable rows for
 * the related-lender sidebar (logo, rating, pricing, BBB, services, etc.).
 *
 * Returns RuntimeLenderWithBody[] so the caller can hydrate via
 * shapeBodyInlineToLender. Payload is bounded — call sites pass ≤3 slugs.
 */
export async function getLendersBySlugListRuntime(
  slugs: string[],
  env?: RuntimeLenderEnv
): Promise<RuntimeLenderWithBody[]> {
  if (!env?.SUPABASE_URL || !env?.SUPABASE_ANON_KEY) return [];
  if (!slugs.length) return [];
  const inList = slugs.map(encodeURIComponent).join(",");
  // CDM-REV Phase 2.5b — drop ghost cards whose rating is null/0/missing.
  // `rating` lives inside body_inline (jsonb), not as a top-level column, so
  // a PostgREST `&rating=gt.0` filter returns 42703. Filter client-side.
  const url =
    `${env.SUPABASE_URL}/rest/v1/lenders` +
    `?slug=in.(${inList})` +
    `&processing_status=eq.ready_for_index` +
    `&select=${FULL_COLUMNS}` +
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
  const rows = (await res.json()) as RuntimeLenderWithBody[];
  return rows.filter((r) => {
    const raw = (r as { body_inline?: { rating?: unknown } })?.body_inline?.rating;
    const n = typeof raw === "number" ? raw : Number(raw);
    return Number.isFinite(n) && n > 0;
  });
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
  limit = 50
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

// ============================================================================
// CDM-REV Stage A.3 — states / categories / glossary_terms runtime fetchers
// ============================================================================
// Same pattern as A.2: PostgREST anon read, body_inline jsonb. Returns []/null
// when env not wired so build-mode doesn't crash. Apply A.3 DDL + backfill
// before pointing live SSR routes at these.

export interface RuntimeState {
  code: string;            // 'AL'
  name: string;
  abbr: string;
  body_inline: Record<string, unknown> | null;
  updated_at: string;
}

export async function getStateByCodeRuntime(
  code: string,
  env?: RuntimeLenderEnv
): Promise<RuntimeState | null> {
  if (!code) return null;
  const url =
    `${env?.SUPABASE_URL}/rest/v1/states` +
    `?code=eq.${encodeURIComponent(code.toUpperCase())}` +
    `&select=code,name,abbr,body_inline,updated_at` +
    `&limit=1`;
  const rows = await _restGet<RuntimeState>(url, env);
  return rows?.[0] ?? null;
}

export async function getAllStatesRuntime(
  env?: RuntimeLenderEnv
): Promise<RuntimeState[]> {
  const url =
    `${env?.SUPABASE_URL}/rest/v1/states` +
    `?select=code,name,abbr,body_inline,updated_at` +
    `&order=code.asc`;
  const rows = await _restGet<RuntimeState>(url, env);
  return rows ?? [];
}

export interface RuntimeCategory {
  slug: string;
  name: string;
  body_inline: Record<string, unknown> | null;
  updated_at: string;
}

export async function getAllCategoriesRuntime(
  env?: RuntimeLenderEnv
): Promise<RuntimeCategory[]> {
  const url =
    `${env?.SUPABASE_URL}/rest/v1/categories` +
    `?select=slug,name,body_inline,updated_at` +
    `&order=slug.asc`;
  const rows = await _restGet<RuntimeCategory>(url, env);
  return rows ?? [];
}

export async function getCategoryBySlugRuntime(
  slug: string,
  env?: RuntimeLenderEnv
): Promise<RuntimeCategory | null> {
  if (!slug) return null;
  const url =
    `${env?.SUPABASE_URL}/rest/v1/categories` +
    `?slug=eq.${encodeURIComponent(slug)}` +
    `&select=slug,name,body_inline,updated_at` +
    `&limit=1`;
  const rows = await _restGet<RuntimeCategory>(url, env);
  return rows?.[0] ?? null;
}

export interface RuntimeGlossaryTerm {
  slug: string;
  term: string;
  category: string | null;
  body_inline: Record<string, unknown> | null;
  updated_at: string;
}

/**
 * Fetch glossary terms whose body_inline.page_contexts intersects any of the
 * provided contexts. Uses PostgREST array-overlap on the jsonb path (GIN-indexed).
 * Returns [] if env is unwired or the contexts list is empty.
 */
export async function getGlossaryTermsForContextsRuntime(
  contexts: string[],
  env?: RuntimeLenderEnv
): Promise<RuntimeGlossaryTerm[]> {
  if (!contexts.length) return [];
  // PostgREST cs.{...} = jsonb @> array. We OR each context to mimic "any-of".
  // Simpler: pull all and filter client-side — only 71 rows, ~80 KB total. The
  // overhead vs. crafting a complex jsonb operator is not worth the bytes saved.
  const url =
    `${env?.SUPABASE_URL}/rest/v1/glossary_terms` +
    `?select=slug,term,category,body_inline,updated_at` +
    `&order=slug.asc`;
  const rows = await _restGet<RuntimeGlossaryTerm>(url, env);
  if (!rows) return [];
  const set = new Set(contexts);
  return rows.filter((row) => {
    const pc = (row.body_inline?.page_contexts ?? []) as unknown;
    if (!Array.isArray(pc)) return false;
    return pc.some((c) => typeof c === "string" && set.has(c));
  });
}

// ============================================================================
// CDM-REV Stage A.4 — blog_posts / listicles / answers / specials runtime fetchers
// ============================================================================

export interface RuntimeBlogPost {
  slug: string;
  title: string;
  category: string | null;
  status: string;          // 'published' (RLS already filters; this is for typing)
  publish_date: string | null;
  body_inline: Record<string, unknown> | null;
  updated_at: string;
}

export async function getBlogPostBySlugRuntime(
  slug: string,
  env?: RuntimeLenderEnv
): Promise<RuntimeBlogPost | null> {
  if (!slug) return null;
  const url =
    `${env?.SUPABASE_URL}/rest/v1/blog_posts` +
    `?slug=eq.${encodeURIComponent(slug)}` +
    `&select=slug,title,category,status,publish_date,body_inline,updated_at` +
    `&limit=1`;
  const rows = await _restGet<RuntimeBlogPost>(url, env);
  return rows?.[0] ?? null;
}

export async function getBlogPostsByCategoryRuntime(
  category: string,
  env?: RuntimeLenderEnv,
  limit = 6
): Promise<RuntimeBlogPost[]> {
  if (!category) return [];
  const url =
    `${env?.SUPABASE_URL}/rest/v1/blog_posts` +
    `?category=eq.${encodeURIComponent(category)}` +
    `&select=slug,title,category,status,publish_date,body_inline,updated_at` +
    `&order=publish_date.desc.nullslast` +
    `&limit=${limit}`;
  const rows = await _restGet<RuntimeBlogPost>(url, env);
  return rows ?? [];
}

export interface RuntimeListicle {
  slug: string;
  title: string;
  target_keyword: string | null;
  category: string | null;
  body_inline: Record<string, unknown> | null;
  updated_at: string;
}

export async function getListicleBySlugRuntime(
  slug: string,
  env?: RuntimeLenderEnv
): Promise<RuntimeListicle | null> {
  if (!slug) return null;
  const url =
    `${env?.SUPABASE_URL}/rest/v1/listicles` +
    `?slug=eq.${encodeURIComponent(slug)}` +
    `&select=slug,title,target_keyword,category,body_inline,updated_at` +
    `&limit=1`;
  const rows = await _restGet<RuntimeListicle>(url, env);
  return rows?.[0] ?? null;
}

export interface RuntimeAnswer {
  slug: string;
  title: string;
  cluster_id: string | null;
  cluster_pillar: string | null;
  banner_category: string | null;
  target_money_page: string | null;
  compliance_score: number | null;
  compliance_passed: boolean;
  body_inline: Record<string, unknown> | null;
  updated_at: string;
}

export async function getAnswerBySlugRuntime(
  slug: string,
  env?: RuntimeLenderEnv
): Promise<RuntimeAnswer | null> {
  if (!slug) return null;
  const url =
    `${env?.SUPABASE_URL}/rest/v1/answers` +
    `?slug=eq.${encodeURIComponent(slug)}` +
    `&select=slug,title,cluster_id,cluster_pillar,banner_category,target_money_page,compliance_score,compliance_passed,body_inline,updated_at` +
    `&limit=1`;
  const rows = await _restGet<RuntimeAnswer>(url, env);
  return rows?.[0] ?? null;
}

/**
 * Sibling answers in the same cluster_pillar, excluding the current slug.
 * Mirrors src/utils/data-build.getSiblingClusterAnswers but reads Supabase at
 * runtime so SSR /answers/[slug] doesn't need fs / build-time JSONs.
 */
export async function getSiblingAnswersByPillarRuntime(
  pillar: string,
  excludeSlug: string,
  env?: RuntimeLenderEnv,
  limit = 4
): Promise<RuntimeAnswer[]> {
  if (!pillar) return [];
  const url =
    `${env?.SUPABASE_URL}/rest/v1/answers` +
    `?cluster_pillar=eq.${encodeURIComponent(pillar)}` +
    `&slug=neq.${encodeURIComponent(excludeSlug)}` +
    `&select=slug,title,cluster_id,cluster_pillar,banner_category,target_money_page,compliance_score,compliance_passed,body_inline,updated_at` +
    `&order=updated_at.desc` +
    `&limit=${limit}`;
  const rows = await _restGet<RuntimeAnswer>(url, env);
  return rows ?? [];
}

/**
 * All published answers, ordered by recency. Used by /answers/index.astro
 * SSR (Phase 5.1) so the index page doesn't fs.readdirSync src/content/answers.
 * Hard cap at 500 to keep payload bounded; we only have ~14 rows today.
 */
export async function getAllAnswersRuntime(
  env?: RuntimeLenderEnv,
  limit = 500
): Promise<RuntimeAnswer[]> {
  const url =
    `${env?.SUPABASE_URL}/rest/v1/answers` +
    `?select=slug,title,cluster_id,cluster_pillar,banner_category,target_money_page,compliance_score,compliance_passed,body_inline,updated_at` +
    `&order=updated_at.desc` +
    `&limit=${limit}`;
  const rows = await _restGet<RuntimeAnswer>(url, env);
  return rows ?? [];
}

export interface RuntimeSpecial {
  id: string;
  lender_slug: string;
  deal_title: string;
  valid_until: string | null;
  body_inline: Record<string, unknown> | null;
  updated_at: string;
}

export async function getSpecialsForLenderRuntime(
  lenderSlug: string,
  env?: RuntimeLenderEnv,
  limit = 5
): Promise<RuntimeSpecial[]> {
  if (!lenderSlug) return [];
  const url =
    `${env?.SUPABASE_URL}/rest/v1/specials` +
    `?lender_slug=eq.${encodeURIComponent(lenderSlug)}` +
    `&select=id,lender_slug,deal_title,valid_until,body_inline,updated_at` +
    `&order=updated_at.desc` +
    `&limit=${limit}`;
  const rows = await _restGet<RuntimeSpecial>(url, env);
  return rows ?? [];
}

// ---------------------------------------------------------------------------
// CDM-REV Phase 5.1.b — state-page aggregates (depend on migration
// 2026-04-30_cdm_rev_a5_state_aggregates.sql which adds:
//   - lenders.state_abbr  (generated from body_inline.company_info.state)
//   - lenders.city_norm   (generated from body_inline.company_info.city)
//   - state_lender_counts MV       (state_abbr, lender_count, city_count)
//   - state_city_lender_counts MV  (state_abbr, city, city_display, lender_count)
// All four exposed read-only to anon via PostgREST.
// ---------------------------------------------------------------------------

export interface RuntimeStateAggregate {
  state_abbr: string;
  lender_count: number;
  city_count: number;
}

export async function getStateAggregateRuntime(
  abbr: string,
  env?: RuntimeLenderEnv
): Promise<RuntimeStateAggregate | null> {
  if (!abbr) return null;
  const url =
    `${env?.SUPABASE_URL}/rest/v1/state_lender_counts` +
    `?state_abbr=eq.${encodeURIComponent(abbr.toUpperCase())}` +
    `&select=state_abbr,lender_count,city_count` +
    `&limit=1`;
  const rows = await _restGet<RuntimeStateAggregate>(url, env);
  return rows?.[0] ?? null;
}

export async function getAllStateAggregatesRuntime(
  env?: RuntimeLenderEnv
): Promise<RuntimeStateAggregate[]> {
  const url =
    `${env?.SUPABASE_URL}/rest/v1/state_lender_counts` +
    `?select=state_abbr,lender_count,city_count` +
    `&order=lender_count.desc`;
  const rows = await _restGet<RuntimeStateAggregate>(url, env);
  return rows ?? [];
}

export interface RuntimeStateCityAggregate {
  state_abbr: string;
  city: string;
  city_display: string | null;
  lender_count: number;
}

export async function getStateCitiesAggregateRuntime(
  abbr: string,
  env?: RuntimeLenderEnv,
  limit = 50
): Promise<RuntimeStateCityAggregate[]> {
  if (!abbr) return [];
  const url =
    `${env?.SUPABASE_URL}/rest/v1/state_city_lender_counts` +
    `?state_abbr=eq.${encodeURIComponent(abbr.toUpperCase())}` +
    `&select=state_abbr,city,city_display,lender_count` +
    `&order=lender_count.desc` +
    `&limit=${limit}`;
  const rows = await _restGet<RuntimeStateCityAggregate>(url, env);
  return rows ?? [];
}

/**
 * Lenders in a given state — uses the new generated `state_abbr` column so
 * PostgREST can filter without jsonb deep-path (which returns 500s).
 * Returns the catalog projection + body_inline so the page can hydrate
 * existing card markup without a second round-trip.
 */
export async function getLendersByStateRuntime(
  abbr: string,
  env?: RuntimeLenderEnv,
  limit = 200
): Promise<Array<RuntimeLender & { body_inline: Record<string, unknown> | null }>> {
  if (!abbr) return [];
  const url =
    `${env?.SUPABASE_URL}/rest/v1/lenders` +
    `?state_abbr=eq.${encodeURIComponent(abbr.toUpperCase())}` +
    `&processing_status=eq.ready_for_index` +
    `&select=${CATALOG_COLUMNS},body_inline` +
    `&order=updated_at.desc` +
    `&limit=${limit}`;
  const rows = await _restGet<RuntimeLender & { body_inline: Record<string, unknown> | null }>(url, env);
  return rows ?? [];
}

// Type alias for Cloudflare Workers R2 binding (no @cloudflare/workers-types
// import to keep the dep graph tight; the adapter provides the runtime).
type R2Bucket = {
  get(key: string): Promise<R2Object | null>;
};
type R2Object = {
  json<T>(): Promise<T>;
};
