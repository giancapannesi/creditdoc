/**
 * CDM-REV-2026-04-29 Phase 1.3.B-A.1 — runtime data layer for Cloudflare Worker SSR.
 *
 * Why this file exists:
 *   src/utils/data.ts is a build-time helper — it uses fs.readdirSync / readFileSync
 *   over src/content/**. Cloudflare Workers have no filesystem, so SSR routes
 *   running on the Worker can't import from data.ts for data fetching.
 *
 *   This file mirrors the small subset of data.ts that /review/[slug].astro needs
 *   at request time, sourced from:
 *     1. Supabase (lender body_inline + catalog rows) — see src/lib/db.ts
 *     2. Vite-bundled JSON imports (categories, glossary, brands) — small files
 *        Vite inlines into the Worker bundle at build time
 *     3. Pure-function re-exports from data.ts (no fs access — safe in Worker)
 *
 * Stage A.2 (Apr 29) UPDATE — wellness_guides / comparisons / brands now live
 * in Postgres tables (the same OBJ-1 mechanism as lenders.body_inline). All
 * three are async DB-backed runtime fetchers; no JSON bundling.
 *
 * The shaping function shapeBodyInlineToLender() takes a RuntimeLenderWithBody
 * (catalog cols + body_inline jsonb) and returns the full Lender shape that
 * the .astro template expects. body_inline contains everything that used to
 * live in src/content/lenders/<slug>.json before A.1.
 */
import categoriesData from "../content/categories.json";
import glossaryData from "../content/glossary-terms.json";
import type {
  Lender,
  Category,
  Comparison,
  WellnessGuide,
  GlossaryTerm,
  BrandInfo,
} from "./data";
import {
  getRelatedLendersByCategoryRuntime,
  getLendersBySlugListRuntime,
  getWellnessGuidesByCategoryRuntime as _getWellnessGuidesByCategoryDb,
  getComparisonsForLenderRuntime as _getComparisonsForLenderDb,
  getBrandBySlugRuntime as _getBrandBySlugDb,
  // Stage A.3 — states / categories / glossary
  getAllCategoriesRuntime as _getAllCategoriesDb,
  getCategoryBySlugRuntime as _getCategoryBySlugDb,
  getGlossaryTermsForContextsRuntime as _getGlossaryTermsForContextsDb,
  getStateByCodeRuntime as _getStateByCodeDb,
  getAllStatesRuntime as _getAllStatesDb,
  // Stage A.4 — blog / listicles / answers / specials
  getBlogPostBySlugRuntime as _getBlogPostBySlugDb,
  getBlogPostsByCategoryRuntime as _getBlogPostsByCategoryDb,
  getListicleBySlugRuntime as _getListicleBySlugDb,
  getAnswerBySlugRuntime as _getAnswerBySlugDb,
  getSpecialsForLenderRuntime as _getSpecialsForLenderDb,
  type RuntimeLender,
  type RuntimeLenderWithBody,
  type RuntimeLenderEnv,
  type RuntimeWellnessGuide,
  type RuntimeComparison,
  type RuntimeBrand,
  type RuntimeCategory,
  type RuntimeGlossaryTerm,
  type RuntimeState,
  type RuntimeBlogPost,
  type RuntimeListicle,
  type RuntimeAnswer,
  type RuntimeSpecial,
} from "../lib/db";

// Re-export pure helpers from data.ts that are safe in Worker context (no fs).
export {
  formatPrice,
  getBbbClass,
  getBadgeEligibility,
  generateDiagnosis,
} from "./data";

/**
 * Brand lookup is now async + DB-backed (Stage A.2). Each call hits Supabase
 * — wrap in CF Cache API at the route level for hot brand slugs.
 *
 * Vite glob bundling (the prior approach) is retired because (a) brands moves
 * to the same OBJ-1 update path as lenders (DB row update → cache version bump),
 * and (b) keeps the Worker bundle slim.
 */
function _shapeBrand(row: RuntimeBrand): BrandInfo {
  const body = (row.body_inline ?? {}) as Partial<BrandInfo>;
  return {
    ...(body as BrandInfo),
    slug: row.slug,
    display_name: row.display_name || body.display_name || row.slug,
    category: row.category || body.category || "",
    last_reviewed: body.last_reviewed || row.updated_at,
    summary_short: body.summary_short || "",
    summary_long: body.summary_long || "",
    faq: Array.isArray(body.faq) ? body.faq : [],
    official_website: body.official_website ?? null,
  };
}

export async function getBrandInfoRuntime(
  slug: string,
  env?: RuntimeLenderEnv
): Promise<BrandInfo | null> {
  if (!slug) return null;
  const row = await _getBrandBySlugDb(slug, env);
  return row ? _shapeBrand(row) : null;
}

export function getCategoriesRuntime(): Category[] {
  return categoriesData as Category[];
}

export function getGlossaryTermsForContextRuntime(
  contexts: string[]
): GlossaryTerm[] {
  if (!contexts.length) return [];
  const all = glossaryData as GlossaryTerm[];
  return all.filter(
    (t) =>
      Array.isArray(t.page_contexts) &&
      t.page_contexts.some((c) => contexts.includes(c))
  );
}

/**
 * Stage A.2 (Apr 29) — wellness + comparisons now live in Postgres.
 * Returned shape mirrors the build-time WellnessGuide / Comparison interfaces.
 * body_inline is the authoritative source; catalog cols (slug/title/etc.) override.
 */
function _shapeWellness(row: RuntimeWellnessGuide): WellnessGuide {
  const body = (row.body_inline ?? {}) as Partial<WellnessGuide>;
  return {
    ...(body as WellnessGuide),
    slug: row.slug,
    title: row.title || body.title || row.slug,
    category: row.category || body.category || "",
    last_updated: body.last_updated || row.updated_at,
    sections: Array.isArray(body.sections) ? body.sections : [],
    key_takeaways: Array.isArray(body.key_takeaways) ? body.key_takeaways : [],
    related_guides: Array.isArray(body.related_guides) ? body.related_guides : [],
    related_categories: Array.isArray(body.related_categories) ? body.related_categories : [],
    faq: Array.isArray(body.faq) ? body.faq : [],
  };
}

export async function getWellnessGuidesByCategoryRuntime(
  category: string,
  env?: RuntimeLenderEnv,
  limit = 6
): Promise<WellnessGuide[]> {
  if (!category) return [];
  const rows = await _getWellnessGuidesByCategoryDb(category, env, limit);
  return rows.map(_shapeWellness);
}

function _shapeComparison(row: RuntimeComparison): Comparison {
  const body = (row.body_inline ?? {}) as Partial<Comparison>;
  return {
    ...(body as Comparison),
    slug: row.slug,
    lender_a: row.lender_a || body.lender_a || "",
    lender_b: row.lender_b || body.lender_b || "",
    title: body.title || "",
    target_keyword: body.target_keyword || "",
    summary: body.summary || "",
    winner: body.winner || "",
    winner_reason: body.winner_reason || "",
  };
}

export async function getComparisonsForLenderRuntime(
  lenderSlug: string,
  env?: RuntimeLenderEnv,
  limit = 6
): Promise<Comparison[]> {
  if (!lenderSlug) return [];
  const rows = await _getComparisonsForLenderDb(lenderSlug, env, limit);
  return rows.map(_shapeComparison);
}

/**
 * Legacy zero-arg name kept for any callers that still expect the build-time
 * "all comparisons" shape. With A.2 live we shifted to lender-scoped queries —
 * use getComparisonsForLenderRuntime() instead. This function returns [].
 */
export function getComparisonsRuntime(): Comparison[] {
  return [];
}

// ============================================================================
// CDM-REV Stage A.3 / A.4 — DB-backed content shape adapters
// ============================================================================
// These coexist with the build-time bundled JSON imports above. Once the A.3
// + A.4 backfills are applied, call sites can flip from the sync bundled
// helpers (getCategoriesRuntime / getGlossaryTermsForContextRuntime) to the
// async DB-backed versions below. Until then, the bundled versions stay so
// build-mode preview works without env vars.

function _shapeCategoryFromRow(row: RuntimeCategory): Category {
  const body = (row.body_inline ?? {}) as Partial<Category>;
  return {
    ...(body as Category),
    slug: row.slug,
    name: row.name || (body as Category).name || row.slug,
  };
}

export async function getCategoriesRuntimeFromDb(
  env?: RuntimeLenderEnv
): Promise<Category[]> {
  const rows = await _getAllCategoriesDb(env);
  return rows.map(_shapeCategoryFromRow);
}

export async function getCategoryBySlugRuntimeFromDb(
  slug: string,
  env?: RuntimeLenderEnv
): Promise<Category | null> {
  const row = await _getCategoryBySlugDb(slug, env);
  return row ? _shapeCategoryFromRow(row) : null;
}

function _shapeGlossaryTermFromRow(row: RuntimeGlossaryTerm): GlossaryTerm {
  const body = (row.body_inline ?? {}) as Partial<GlossaryTerm>;
  return {
    ...(body as GlossaryTerm),
    slug: row.slug,
    term: row.term || (body as GlossaryTerm).term || row.slug,
    category: row.category ?? body.category ?? "",
    page_contexts: Array.isArray(body.page_contexts) ? body.page_contexts : [],
  };
}

export async function getGlossaryTermsForContextRuntimeFromDb(
  contexts: string[],
  env?: RuntimeLenderEnv
): Promise<GlossaryTerm[]> {
  if (!contexts.length) return [];
  const rows = await _getGlossaryTermsForContextsDb(contexts, env);
  return rows.map(_shapeGlossaryTermFromRow);
}

/**
 * State shape adapter — there is no build-time interface, so we return the
 * raw body_inline merged with the catalog cols. Call sites should spread
 * what they need.
 */
export interface StateInfoRuntime {
  code: string;
  name: string;
  abbr: string;
  // Spread fields from body_inline: capital, usury_cap, consumer_protection_*,
  // licensing_board, payday_loan_status, max_payday_amount, etc.
  [key: string]: unknown;
}

function _shapeState(row: RuntimeState): StateInfoRuntime {
  const body = (row.body_inline ?? {}) as Record<string, unknown>;
  return {
    ...body,
    code: row.code,
    name: row.name,
    abbr: row.abbr,
  };
}

export async function getStateByCodeRuntimeFromDb(
  code: string,
  env?: RuntimeLenderEnv
): Promise<StateInfoRuntime | null> {
  const row = await _getStateByCodeDb(code, env);
  return row ? _shapeState(row) : null;
}

export async function getAllStatesRuntimeFromDb(
  env?: RuntimeLenderEnv
): Promise<StateInfoRuntime[]> {
  const rows = await _getAllStatesDb(env);
  return rows.map(_shapeState);
}

/**
 * Blog post / listicle / answer / special shape adapters. These mirror the
 * build-time interfaces (e.g. BlogPost) but the DB is the source of truth —
 * body_inline keys override duplicated catalog cols.
 */

export interface BlogPostRuntime {
  slug: string;
  title: string;
  category: string | null;
  status: string;
  publish_date: string | null;
  last_updated: string;
  [key: string]: unknown;
}

function _shapeBlogPost(row: RuntimeBlogPost): BlogPostRuntime {
  const body = (row.body_inline ?? {}) as Record<string, unknown>;
  return {
    ...body,
    slug: row.slug,
    title: row.title || (body.title as string) || row.slug,
    category: row.category,
    status: row.status,
    publish_date: row.publish_date,
    last_updated: row.updated_at,
  };
}

export async function getBlogPostBySlugRuntimeFromDb(
  slug: string,
  env?: RuntimeLenderEnv
): Promise<BlogPostRuntime | null> {
  const row = await _getBlogPostBySlugDb(slug, env);
  return row ? _shapeBlogPost(row) : null;
}

export async function getBlogPostsByCategoryRuntimeFromDb(
  category: string,
  env?: RuntimeLenderEnv,
  limit = 6
): Promise<BlogPostRuntime[]> {
  const rows = await _getBlogPostsByCategoryDb(category, env, limit);
  return rows.map(_shapeBlogPost);
}

export interface ListicleRuntime {
  slug: string;
  title: string;
  target_keyword: string | null;
  category: string | null;
  last_updated: string;
  [key: string]: unknown;
}

function _shapeListicle(row: RuntimeListicle): ListicleRuntime {
  const body = (row.body_inline ?? {}) as Record<string, unknown>;
  return {
    ...body,
    slug: row.slug,
    title: row.title || (body.title as string) || row.slug,
    target_keyword: row.target_keyword,
    category: row.category,
    last_updated: row.updated_at,
  };
}

export async function getListicleBySlugRuntimeFromDb(
  slug: string,
  env?: RuntimeLenderEnv
): Promise<ListicleRuntime | null> {
  const row = await _getListicleBySlugDb(slug, env);
  return row ? _shapeListicle(row) : null;
}

export interface AnswerRuntime {
  slug: string;
  title: string;
  cluster_id: string | null;
  cluster_pillar: string | null;
  banner_category: string | null;
  target_money_page: string | null;
  compliance_passed: boolean;
  last_updated: string;
  [key: string]: unknown;
}

function _shapeAnswer(row: RuntimeAnswer): AnswerRuntime {
  const body = (row.body_inline ?? {}) as Record<string, unknown>;
  return {
    ...body,
    slug: row.slug,
    title: row.title || (body.title as string) || row.slug,
    cluster_id: row.cluster_id,
    cluster_pillar: row.cluster_pillar,
    banner_category: row.banner_category,
    target_money_page: row.target_money_page,
    compliance_passed: row.compliance_passed,
    last_updated: row.updated_at,
  };
}

export async function getAnswerBySlugRuntimeFromDb(
  slug: string,
  env?: RuntimeLenderEnv
): Promise<AnswerRuntime | null> {
  const row = await _getAnswerBySlugDb(slug, env);
  return row ? _shapeAnswer(row) : null;
}

export interface SpecialRuntime {
  id: string;
  lender_slug: string;
  deal_title: string;
  valid_until: string | null;
  last_updated: string;
  [key: string]: unknown;
}

function _shapeSpecial(row: RuntimeSpecial): SpecialRuntime {
  const body = (row.body_inline ?? {}) as Record<string, unknown>;
  return {
    ...body,
    id: row.id,
    lender_slug: row.lender_slug,
    deal_title: row.deal_title,
    valid_until: row.valid_until,
    last_updated: row.updated_at,
  };
}

export async function getSpecialsForLenderRuntimeFromDb(
  lenderSlug: string,
  env?: RuntimeLenderEnv,
  limit = 5
): Promise<SpecialRuntime[]> {
  const rows = await _getSpecialsForLenderDb(lenderSlug, env, limit);
  return rows.map(_shapeSpecial);
}

/**
 * Default values for Lender fields when body_inline omits them. Shapes a
 * minimum-viable Lender so the .astro template never throws on missing keys.
 */
function defaults(): Partial<Lender> {
  return {
    subcategories: [],
    description_short: "",
    description_long: "",
    logo_url: "",
    website_url: "",
    affiliate_url: "",
    affiliate_program: "",
    pricing: {
      monthly_price: 0,
      setup_fee: 0,
      money_back_guarantee: false,
      guarantee_details: "",
      first_work_fee: 0,
      free_consultation: false,
      tiers: [],
    } as unknown as Lender["pricing"],
    features: {} as Lender["features"],
    company_info: {
      founded_year: 0,
      headquarters: "",
      city: "",
      state: "",
      employees: "",
      bbb_rating: "",
      bbb_accredited: false,
      certifications: [],
    },
    states_served: [],
    cities_served: [],
    rating: 0,
    rating_breakdown: {
      value: 0,
      effectiveness: 0,
      customer_service: 0,
      transparency: 0,
      ease_of_use: 0,
    },
    pros: [],
    cons: [],
    best_for: [],
    similar_lenders: [],
    diagnosis: "",
    services: [],
    typical_results_timeline: "",
    last_updated: "",
    review_status: "published",
  };
}

/**
 * Take a RuntimeLenderWithBody (catalog cols + body_inline jsonb) and return a
 * full Lender that the .astro template can render.
 *
 * body_inline was backfilled 2026-04-29 from src/content/lenders/<slug>.json
 * so its shape matches the Lender interface (modulo missing optional fields).
 * We merge defaults() so undefined keys don't crash the template.
 */
export function shapeBodyInlineToLender(row: RuntimeLenderWithBody): Lender {
  const body = (row.body_inline ?? {}) as Partial<Lender>;
  const merged: Lender = {
    ...(defaults() as Lender),
    ...body,
    // Authoritative columns from `lenders` table override anything in body_inline.
    name: row.name,
    slug: row.slug,
    category: row.category,
    last_updated: row.updated_at,
  };
  // Defensive normalization (mirrors the build-time path in getAllLenders).
  merged.subcategories = Array.isArray(merged.subcategories) ? merged.subcategories : [];
  merged.states_served = Array.isArray(merged.states_served) ? merged.states_served : [];
  merged.cities_served = Array.isArray(merged.cities_served) ? merged.cities_served : [];
  merged.best_for = Array.isArray(merged.best_for) ? merged.best_for : [];
  merged.services = Array.isArray(merged.services) ? merged.services : [];
  merged.similar_lenders = Array.isArray(merged.similar_lenders) ? merged.similar_lenders : [];
  merged.pros = Array.isArray(merged.pros) ? merged.pros : [];
  merged.cons = Array.isArray(merged.cons) ? merged.cons : [];
  return merged;
}

/**
 * Catalog row → Lender stub (no body content). Used to render related-lender
 * sidebar cards which only need name/slug/category/state/rating/logo/brand.
 */
export function shapeCatalogToLenderStub(row: RuntimeLender): Lender {
  const stub: Lender = {
    ...(defaults() as Lender),
    name: row.name,
    slug: row.slug,
    category: row.category,
    last_updated: row.updated_at,
  };
  stub.brand_slug = row.brand_slug ?? null;
  if (row.state) {
    stub.company_info = { ...stub.company_info, state: row.state };
  }
  // logo_url is NOT in the catalog projection — LenderCard uses has_logo to fall back
  // to the placeholder logo path. We hint via has_logo-ish behaviour by leaving logo_url
  // empty; the template's existing fallback chain takes over.
  return stub;
}

/**
 * High-level: fetch primary lender + related lender stubs + sidebar widgets
 * for /review/[slug] SSR. Returns null if the primary lender is missing OR
 * the env isn't wired (build-mode preview without secrets).
 *
 * Stage A.2 (Apr 29): wellness + comparisons + brand are now async DB pulls
 * that run in parallel with the related-lender query (Promise.all). Total
 * extra latency ~one round-trip-time vs the prior empty-stub version.
 */
export async function fetchReviewPageData(
  slug: string,
  env: RuntimeLenderEnv | undefined,
  primary: RuntimeLenderWithBody
): Promise<{
  lender: Lender;
  relatedLenders: Lender[];
  wellnessGuides: WellnessGuide[];
  comparisons: Comparison[];
  brand: BrandInfo | null;
}> {
  const lender = shapeBodyInlineToLender(primary);

  // Related-lender resolution: 2-tier (explicit similar_lenders → category top).
  const similarSlugs = (lender.similar_lenders ?? []).filter(
    (s): s is string => typeof s === "string" && s.length > 0
  );
  const relatedTask = (async (): Promise<RuntimeLender[]> => {
    let rows: RuntimeLender[] = [];
    if (similarSlugs.length > 0) {
      rows = await getLendersBySlugListRuntime(similarSlugs.slice(0, 3), env);
    }
    if (rows.length < 3) {
      const more = await getRelatedLendersByCategoryRuntime(
        lender.category,
        lender.slug,
        env,
        3 - rows.length
      );
      rows = [...rows, ...more];
    }
    return rows.slice(0, 3);
  })();

  const wellnessTask = getWellnessGuidesByCategoryRuntime(lender.category, env, 4);
  const comparisonsTask = getComparisonsForLenderRuntime(lender.slug, env, 4);
  const brandTask = lender.brand_slug
    ? getBrandInfoRuntime(lender.brand_slug, env)
    : Promise.resolve<BrandInfo | null>(null);

  const [relatedRows, wellnessGuides, comparisons, brand] = await Promise.all([
    relatedTask,
    wellnessTask,
    comparisonsTask,
    brandTask,
  ]);

  return {
    lender,
    relatedLenders: relatedRows.map(shapeCatalogToLenderStub),
    wellnessGuides,
    comparisons,
    brand,
  };
}
