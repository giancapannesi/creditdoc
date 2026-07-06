/**
 * CDM-REV-2026-04-30 Phase 5.6 — middleware cacheWrap for SSR Astro pages.
 *
 * Closes the OBJ-1 ≤10s hard-line for /answers/[slug] and /best/[slug]:
 *   - Without this: pages set Cache-Control: max-age=86400 → CF Pages may
 *     serve up to 24h stale HTML after a row UPDATE.
 *   - With this: cache key includes the row's updated_at_epoch, so a row
 *     UPDATE makes the OLD key-version useless — next request misses,
 *     re-renders, caches under the NEW key. Globally correct (per-PoP
 *     independent invalidation), no global purge call needed.
 *
 * Mirrors the cacheWrap pattern that /r/[slug].ts uses via src/lib/cache.ts.
 *
 * Cost: 1 extra PostgREST round-trip per cached request for version lookup.
 *   - On HIT: saves a full Astro render (~200ms+) → big net win.
 *   - On MISS: 2 PostgREST reads (version probe + page's full row fetch).
 *     Page-level row fetch is unavoidable for hydration anyway.
 *
 * /r/[slug] is NOT routed through this middleware — it already does its own
 * cacheWrap inside the endpoint, with the row already in hand.
 *
 * Index pages (/answers without slug) skip middleware caching for now.
 * They keep the plain max-age=86400 set in the page frontmatter; they're
 * cheap to render and traffic is low.
 */
import { defineMiddleware } from 'astro:middleware';
import { STATE_ABBREVIATIONS } from './utils/data';
import seRankingStaticSnapshotManifest from '../data/seranking_static_snapshot_urls_2026-07-05.json';

// Bump this when shared SSR templates change; DB updated_at alone does not
// invalidate cached HTML for code-only changes.
const NAMESPACE = 'creditdoc-v2-mw';

const CITY_STATE_SLUGS = Object.entries(STATE_ABBREVIATIONS)
  .map(([state, abbr]) => ({
    stateSlug: state.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, ''),
    abbr: abbr.toLowerCase(),
  }))
  .sort((a, b) => b.stateSlug.length - a.stateSlug.length);

const STATE_CODE_REDIRECTS = new Map(
  Object.entries(STATE_ABBREVIATIONS).map(([state, abbr]) => [
    abbr.toLowerCase(),
    `/state/${state.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '')}/`,
  ])
);

const NON_STATE_CODE_REDIRECTS = new Set(['dc', 'gu', 'ho', 'pm', 'pr', 'st', 'vi']);

const SERANKING_STATIC_SNAPSHOT_PATHS = new Set(
  (seRankingStaticSnapshotManifest.urls as string[]).map((href) => {
    return new URL(href).pathname;
  })
);

const LEGACY_CATEGORY_REDIRECTS = new Map<string, string>([
  ['fix-my-credit', 'credit-repair'],
]);

const LEGACY_PATH_REDIRECTS = new Map<string, string>([
  ['/categories/fix-my-credit/', '/categories/credit-repair/'],
  ['/browse/emergency-cash/houston-texas/', '/browse/emergency-cash/houston-tx/'],
  ['/browse/pawn-shops/houston-texas/', '/browse/pawn-shops/houston-tx/'],
  ['/browse/check-cashing/tucson-arizona/', '/browse/check-cashing/tucson-az/'],
  ['/browse/emergency-cash/north-las-vegas-nevada/', '/browse/emergency-cash/north-las-vegas-nv/'],
  ['/browse/pawn-shops/garland-texas/', '/browse/pawn-shops/garland-tx/'],
  ['/browse/pawn-shops/tucson-arizona/', '/browse/pawn-shops/tucson-az/'],
  ['/browse/fix-my-credit/brooklyn-ny/', '/browse/credit-repair/brooklyn-ny/'],
  ['/browse/emergency-cash/new-orleans-louisiana/', '/browse/emergency-cash/new-orleans-la/'],
  ['/browse/fix-my-credit/southfield-mi/', '/categories/credit-repair/'],
  ['/city/cedar-park-texas/', '/city/cedar-park-tx/'],
  ['/city/halethorpe-maryland/', '/state/maryland/'],
  ['/city/pflugerville-texas/', '/city/pflugerville-tx/'],
  ['/city/daly-city-california/', '/state/california/'],
  ['/city/stone-mountain-georgia/', '/city/stone-mountain-ga/'],
  ['/city/st-augustine-florida/', '/state/florida/'],
  ['/city/murfreesboro-tennessee/', '/state/tennessee/'],
  ['/city/leon-valley-texas/', '/state/texas/'],
  ['/city/hilliard-ohio/', '/state/ohio/'],
  ['/city/burien-washington/', '/state/washington/'],
  ['/city/miami-lakes-florida/', '/city/miami-lakes-fl/'],
  ['/city/covington-kentucky/', '/city/covington-ky/'],
  ['/city/redford-township-michigan/', '/state/michigan/'],
  ['/city/macclenny-florida/', '/city/macclenny-fl/'],
  ['/city/avondale-arizona/', '/city/avondale-az/'],
  ['/city/maple-heights-ohio/', '/state/ohio/'],
  ['/city/fairfield-ohio/', '/state/ohio/'],
  ['/city/newport-kentucky/', '/city/newport-ky/'],
  ['/city/spartanburg-south-carolina/', '/city/spartanburg-sc/'],
  ['/city/grove-city-ohio/', '/state/ohio/'],
  ['/city/southaven-mississippi/', '/state/mississippi/'],
  ['/city/goodlettsville-tennessee/', '/city/goodlettsville-tn/'],
  ['/compare/credit-saint-vs-disputebee/', '/compare/credit-saint-vs-the-credit-people/'],
  ['/compare/the-credit-pros-vs-credit-saint/', '/compare/credit-saint-vs-the-credit-pros/'],
  ['/compare/lexington-law-vs-the-credit-people/', '/compare/credit-saint-vs-the-credit-people/'],
  ['/compare/disputebee-vs-the-credit-people/', '/compare/credit-saint-vs-the-credit-people/'],
]);

function normalizeLegacyPath(pathname: string): string {
  let decoded = pathname;
  try {
    decoded = decodeURIComponent(pathname);
  } catch {
    decoded = pathname;
  }
  return decoded
    .toLowerCase()
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/\/+$/, '/');
}

function legacyRedirectTarget(pathname: string): string | null {
  const normalized = normalizeLegacyPath(pathname);
  return LEGACY_PATH_REDIRECTS.get(normalized) ?? null;
}

function categoryAliasRedirectTarget(pathname: string): string | null {
  const match = pathname.match(/^\/categories\/([^/]+)\/?$/);
  if (!match) return null;

  const category = LEGACY_CATEGORY_REDIRECTS.get(match[1].toLowerCase());
  if (!category) return null;
  const target = `/categories/${category}/`;
  return target === pathname ? null : target;
}

function stateCodeRedirectTarget(pathname: string): string | null {
  const match = pathname.match(/^\/state\/([a-z]{2})\/?$/i);
  if (!match) return null;

  const code = match[1].toLowerCase();
  const target = STATE_CODE_REDIRECTS.get(code);
  if (target) return target === pathname ? null : target;
  return NON_STATE_CODE_REDIRECTS.has(code) ? '/state/' : null;
}

function cityStateRedirectTarget(pathname: string): string | null {
  const match = pathname.match(/^\/city\/([^/]+)\/?$/);
  if (!match) return null;

  let slug: string;
  try {
    slug = decodeURIComponent(match[1]);
  } catch {
    slug = match[1];
  }
  slug = slug.toLowerCase().replace(/\s+/g, '-').replace(/-+/g, '-').replace(/^-+|-+$/g, '');

  for (const { stateSlug, abbr } of CITY_STATE_SLUGS) {
    const suffix = `-${stateSlug}`;
    if (!slug.endsWith(suffix)) continue;
    const citySlug = slug.slice(0, -suffix.length).replace(/-+$/g, '');
    if (!citySlug) return null;
    const target = `/city/${citySlug}-${abbr}/`;
    return target === pathname ? null : target;
  }

  return null;
}

function browseCityStateRedirectTarget(pathname: string): string | null {
  const match = pathname.match(/^\/browse\/([^/]+)\/([^/]+)\/?$/);
  if (!match) return null;

  const categorySlug = LEGACY_CATEGORY_REDIRECTS.get(match[1].toLowerCase()) ?? match[1];
  let cityStateSlug: string;
  try {
    cityStateSlug = decodeURIComponent(match[2]);
  } catch {
    cityStateSlug = match[2];
  }
  cityStateSlug = cityStateSlug
    .toLowerCase()
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-+|-+$/g, '');

  for (const { stateSlug, abbr } of CITY_STATE_SLUGS) {
    const suffix = `-${stateSlug}`;
    if (!cityStateSlug.endsWith(suffix)) continue;
    const citySlug = cityStateSlug.slice(0, -suffix.length).replace(/-+$/g, '');
    if (!citySlug) return null;
    const target = `/browse/${categorySlug}/${citySlug}-${abbr}/`;
    return target === pathname ? null : target;
  }

  return null;
}

// CDM-REV iter 35 — Tier 1 OBJ-3 security-header hardening.
// Applied to every response (cached HIT, fresh MISS, BYPASS, non-cacheable, non-GET).
// Headers chosen with Jammi (2026-05-01): full safe set, HTTPS-only posture confirmed.
function applySecurityHeaders(res: Response): Response {
  // X-Content-Type-Options: stop browsers MIME-sniffing — defends against
  // a non-JS file being interpreted as a script.
  if (!res.headers.has('x-content-type-options')) {
    res.headers.set('x-content-type-options', 'nosniff');
  }
  // X-Frame-Options: SAMEORIGIN allows our own pages to embed each other
  // (e.g. future widgets) but blocks third-party iframe embedding (clickjacking).
  if (!res.headers.has('x-frame-options')) {
    res.headers.set('x-frame-options', 'SAMEORIGIN');
  }
  // Referrer-Policy: send only the origin (creditdoc.co) on cross-origin
  // navigation, full URL on same-origin. Affiliate networks still get the
  // origin so attribution should keep working.
  if (!res.headers.has('referrer-policy')) {
    res.headers.set('referrer-policy', 'strict-origin-when-cross-origin');
  }
  // Permissions-Policy: disable browser APIs we don't use. Defense against
  // a hijacked script silently activating camera/mic/geolocation/etc.
  if (!res.headers.has('permissions-policy')) {
    res.headers.set(
      'permissions-policy',
      'camera=(), microphone=(), geolocation=(), payment=(), usb=(), bluetooth=(), magnetometer=(), gyroscope=(), accelerometer=()'
    );
  }
  // HSTS: 2 years, includeSubDomains. HTTPS-only confirmed by Jammi.
  // No `preload` directive yet — that requires explicit submission to
  // Chrome's preload list and is irreversible.
  if (!res.headers.has('strict-transport-security')) {
    res.headers.set('strict-transport-security', 'max-age=63072000; includeSubDomains');
  }
  return res;
}

interface CacheableRoute {
  table: 'answers' | 'lenders' | 'listicles' | 'categories' | 'states' | 'city_guides' | 'blog_posts' | 'wellness_guides' | 'brands';
  /** Maps URL pathname → row slug. Returns null if path is not an SSR row page. */
  match: (pathname: string) => string | null;
  /** Optional: route variant tag (for cache-key namespacing). */
  variant?: string;
  /**
   * Optional override for version lookup. Default behavior: fetch
   * <table>.updated_at WHERE slug=<slug>. Aggregate routes (categories, etc.)
   * supply a custom function that returns MAX(updated_at) across all rows
   * the page renders, so any underlying row edit busts the cache key.
   */
  versionFetch?: (slug: string, env: RuntimeEnvLike) => Promise<string | null>;
}

// Slug-pattern routes — middleware will fetch updated_at for the matched row
// and key the cache by (pathname + updated_at_epoch).
//
// NOTE: /r/[slug] already does its own cacheWrap so it's intentionally absent.
// /answers/index and /answers/[slug] both ride /answers/* — the index is
// excluded by the slug-extraction returning null when no slug is present.
const CACHEABLE_ROUTES: CacheableRoute[] = [
  {
    table: 'lenders',
    variant: 'review-slug',
    match: (p) => {
      const m = p.match(/^\/review\/([^/]+)\/?$/);
      return m ? m[1] : null;
    },
  },
  {
    table: 'states',
    variant: 'state-slug',
    match: (p) => {
      const m = p.match(/^\/state\/([^/]+)\/?$/);
      return m ? m[1] : null;
    },
    versionFetch: fetchStateVersionBySlug,
  },
  {
    table: 'city_guides',
    variant: 'credit-guide-slug',
    match: (p) => {
      const m = p.match(/^\/credit-guide\/([^/]+)\/?$/);
      return m ? m[1] : null;
    },
  },
  {
    table: 'city_guides',
    variant: 'credit-guide-category',
    match: (p) => {
      const m = p.match(/^\/credit-guide\/([^/]+)\/([^/]+)\/?$/);
      return m ? m[1] : null;
    },
  },
  {
    table: 'blog_posts',
    variant: 'blog-slug',
    match: (p) => {
      const m = p.match(/^\/blog\/([^/]+)\/?$/);
      return m ? m[1] : null;
    },
  },
  {
    table: 'wellness_guides',
    variant: 'wellness-slug',
    match: (p) => {
      const m = p.match(/^\/financial-wellness\/([^/]+)\/?$/);
      return m ? m[1] : null;
    },
  },
  {
    table: 'brands',
    variant: 'brand-slug',
    match: (p) => {
      const m = p.match(/^\/brand\/([^/]+)\/?$/);
      return m ? m[1] : null;
    },
  },
  {
    table: 'answers',
    variant: 'answers-index',
    match: (p) => (/^\/answers\/?$/.test(p) ? '__index' : null),
    versionFetch: (_slug, env) => fetchLatestTableVersion('answers', env),
  },
  {
    table: 'answers',
    variant: 'answers-slug',
    match: (p) => {
      const m = p.match(/^\/answers\/([^/]+)\/?$/);
      if (!m) return null;
      // Exclude bare /answers/ index — the path /answers/ is captured here too
      // because the trailing-slash regex matches; require non-empty slug.
      const slug = m[1];
      return slug && slug.length > 0 ? slug : null;
    },
  },
  {
    table: 'listicles',
    variant: 'best-slug',
    match: (p) => {
      const m = p.match(/^\/best\/([^/]+)\/?$/);
      return m ? m[1] : null;
    },
  },
  {
    // /categories/[category] — aggregate route. The page renders the category
    // metadata row + top-48 lenders sorted by rating. Any of those underlying
    // rows updating must bust the cache key. We compute version as the max of
    // (categories.updated_at, MAX(lenders.updated_at WHERE category=slug AND ready_for_index)).
    // Lender edits dominate in practice; category metadata edits are rare but
    // also covered.
    table: 'categories',
    variant: 'category-slug',
    match: (p) => {
      const m = p.match(/^\/categories\/([^/]+)\/?$/);
      return m ? m[1] : null;
    },
    versionFetch: fetchCategoryAggregateVersion,
  },
];

interface RuntimeEnvLike {
  SUPABASE_URL?: string;
  SUPABASE_ANON_KEY?: string;
  ASSETS?: {
    fetch: (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;
  };
}

/**
 * Aggregate version for /categories/[slug] — returns the max updated_at across
 * the category metadata row AND every lender row in that category.
 *
 * Two parallel PostgREST round-trips (~30-40ms each from a Worker, negligible).
 * If either fails we return null and the request bypasses cache (BYPASS-NOVERSION).
 *
 * The lender query relies on the same composite partial index that powers
 * the page's main query (lenders_category_rating_ready_idx) — but we order by
 * updated_at DESC instead of rating, so the index isn't used. Workload is
 * tiny (~5K rows for banking), and `select=updated_at&limit=1` keeps the
 * payload minimal. If category sizes grow 10×, add a second partial index
 * `(category, updated_at DESC) WHERE processing_status='ready_for_index'`.
 */
async function fetchCategoryAggregateVersion(
  slug: string,
  env: RuntimeEnvLike
): Promise<string | null> {
  if (!env.SUPABASE_URL || !env.SUPABASE_ANON_KEY) return null;
  const headers = {
    apikey: env.SUPABASE_ANON_KEY,
    authorization: `Bearer ${env.SUPABASE_ANON_KEY}`,
  };
  const catUrl =
    `${env.SUPABASE_URL}/rest/v1/categories` +
    `?slug=eq.${encodeURIComponent(slug)}` +
    `&select=updated_at` +
    `&limit=1`;
  const lenderUrl =
    `${env.SUPABASE_URL}/rest/v1/lenders` +
    `?category=eq.${encodeURIComponent(slug)}` +
    `&processing_status=eq.ready_for_index` +
    `&select=updated_at` +
    `&order=updated_at.desc` +
    `&limit=1`;
  try {
    const [catRes, lenderRes] = await Promise.all([
      fetch(catUrl, { headers, signal: AbortSignal.timeout(2000) }),
      fetch(lenderUrl, { headers, signal: AbortSignal.timeout(2000) }),
    ]);
    if (!catRes.ok || !lenderRes.ok) return null;
    const [catRows, lenderRows] = await Promise.all([
      catRes.json() as Promise<Array<{ updated_at?: string }>>,
      lenderRes.json() as Promise<Array<{ updated_at?: string }>>,
    ]);
    const candidates = [
      catRows?.[0]?.updated_at,
      lenderRows?.[0]?.updated_at,
    ].filter((s): s is string => typeof s === 'string' && s.length > 0);
    if (candidates.length === 0) return null;
    // Lex compare works for ISO 8601 timestamps; both come from PostgreSQL
    // timestamp with time zone so format is consistent.
    candidates.sort();
    return candidates[candidates.length - 1];
  } catch {
    return null;
  }
}

async function fetchStateVersionBySlug(
  slug: string,
  env: RuntimeEnvLike
): Promise<string | null> {
  if (!env.SUPABASE_URL || !env.SUPABASE_ANON_KEY) return null;
  const name = slug.replace(/-/g, " ");
  const url =
    `${env.SUPABASE_URL}/rest/v1/states` +
    `?name=ilike.${encodeURIComponent(name)}` +
    `&select=updated_at` +
    `&limit=1`;
  try {
    const res = await fetch(url, {
      headers: {
        apikey: env.SUPABASE_ANON_KEY,
        authorization: `Bearer ${env.SUPABASE_ANON_KEY}`,
      },
      signal: AbortSignal.timeout(2000),
    });
    if (!res.ok) return null;
    const rows = (await res.json()) as Array<{ updated_at?: string }>;
    return rows?.[0]?.updated_at ?? null;
  } catch {
    return null;
  }
}

async function fetchLatestTableVersion(
  table: string,
  env: RuntimeEnvLike
): Promise<string | null> {
  if (!env.SUPABASE_URL || !env.SUPABASE_ANON_KEY) return null;
  const url =
    `${env.SUPABASE_URL}/rest/v1/${table}` +
    `?select=updated_at` +
    `&order=updated_at.desc` +
    `&limit=1`;
  try {
    const res = await fetch(url, {
      headers: {
        apikey: env.SUPABASE_ANON_KEY,
        authorization: `Bearer ${env.SUPABASE_ANON_KEY}`,
      },
      signal: AbortSignal.timeout(2000),
    });
    if (!res.ok) return null;
    const rows = (await res.json()) as Array<{ updated_at?: string }>;
    return rows?.[0]?.updated_at ?? null;
  } catch {
    return null;
  }
}

async function fetchUpdatedAt(
  table: string,
  slug: string,
  env: RuntimeEnvLike
): Promise<string | null> {
  if (!env.SUPABASE_URL || !env.SUPABASE_ANON_KEY) return null;
  const url =
    `${env.SUPABASE_URL}/rest/v1/${table}` +
    `?slug=eq.${encodeURIComponent(slug)}` +
    `&select=updated_at` +
    `&limit=1`;
  try {
    const res = await fetch(url, {
      headers: {
        apikey: env.SUPABASE_ANON_KEY,
        authorization: `Bearer ${env.SUPABASE_ANON_KEY}`,
      },
      // Tight timeout — version probe must be fast or we just bypass cache.
      signal: AbortSignal.timeout(2000),
    });
    if (!res.ok) return null;
    const rows = (await res.json()) as Array<{ updated_at?: string }>;
    return rows?.[0]?.updated_at ?? null;
  } catch {
    return null;
  }
}

function buildCacheKey(req: Request, pathname: string, verSec: number, variant: string): Request {
  const url = new URL(req.url);
  url.pathname = `/__c/${NAMESPACE}/${variant}/${encodeURIComponent(pathname)}::v=${verSec}`;
  url.search = '';
  return new Request(url.toString(), { method: 'GET' });
}

export const onRequest = defineMiddleware(async (context, next) => {
  // Only cache GETs of HTML routes.
  if (context.request.method !== 'GET') return applySecurityHeaders(await next());

  const url = new URL(context.request.url);
  const pathname = url.pathname;
  const env = (context.locals as any)?.runtime?.env as RuntimeEnvLike | undefined;

  const legacyTarget = legacyRedirectTarget(pathname);
  if (legacyTarget) {
    return Response.redirect(new URL(legacyTarget, url.origin), 301);
  }

  if (/^\/categories\/?$/.test(pathname)) {
    return Response.redirect(new URL('/city/', url.origin), 301);
  }

  const categoryRedirectTarget = categoryAliasRedirectTarget(pathname);
  if (categoryRedirectTarget) {
    return Response.redirect(new URL(categoryRedirectTarget, url.origin), 301);
  }

  const stateRedirectTarget = stateCodeRedirectTarget(pathname);
  if (stateRedirectTarget) {
    return Response.redirect(new URL(stateRedirectTarget, url.origin), 301);
  }

  const cityRedirectTarget = cityStateRedirectTarget(pathname);
  if (cityRedirectTarget) {
    return Response.redirect(new URL(cityRedirectTarget, url.origin), 301);
  }

  const browseRedirectTarget = browseCityStateRedirectTarget(pathname);
  if (browseRedirectTarget) {
    return Response.redirect(new URL(browseRedirectTarget, url.origin), 301);
  }

  if (
    url.search === '' &&
    env?.ASSETS &&
    SERANKING_STATIC_SNAPSHOT_PATHS.has(pathname)
  ) {
    const assetUrl = new URL(`${pathname}index.html`, url.origin);
    const asset = await env.ASSETS.fetch(new Request(assetUrl.toString(), context.request));
    if (asset.status === 200) {
      const out = new Response(asset.body, asset);
      out.headers.set('content-type', 'text/html; charset=utf-8');
      out.headers.set('cache-control', 'public, max-age=86400, s-maxage=86400, immutable');
      out.headers.set('x-cdm-static-snapshot', 'seranking-2026-07-05');
      return applySecurityHeaders(out);
    }
  }

  // Find the first matching cacheable route (returns slug or null).
  let matched: { route: CacheableRoute; slug: string } | null = null;
  for (const route of CACHEABLE_ROUTES) {
    const slug = route.match(pathname);
    if (slug) {
      matched = { route, slug };
      break;
    }
  }
  if (!matched) return applySecurityHeaders(await next());

  if (!env?.SUPABASE_URL || !env?.SUPABASE_ANON_KEY) {
    // Build-mode preview or env not configured — don't cache, just pass.
    const fresh = await next();
    fresh.headers.set('x-cdm-cache', 'BYPASS-NOENV');
    return applySecurityHeaders(fresh);
  }

  // Version probe — if it fails, skip caching for this request.
  // Aggregate routes (e.g. /categories/) supply their own versionFetch that
  // returns MAX(updated_at) across all underlying rows so any edit busts the
  // cache key globally.
  const updatedAt = matched.route.versionFetch
    ? await matched.route.versionFetch(matched.slug, env)
    : await fetchUpdatedAt(matched.route.table, matched.slug, env);
  if (!updatedAt) {
    const fresh = await next();
    fresh.headers.set('x-cdm-cache', 'BYPASS-NOVERSION');
    return applySecurityHeaders(fresh);
  }

  const verSec = Math.floor(Date.parse(updatedAt) / 1000);
  if (!Number.isFinite(verSec) || verSec <= 0) {
    const fresh = await next();
    fresh.headers.set('x-cdm-cache', 'BYPASS-BADVERSION');
    return applySecurityHeaders(fresh);
  }

  // @ts-expect-error caches global is provided by Cloudflare Workers runtime
  const cache: Cache = caches.default;
  const key = buildCacheKey(context.request, pathname, verSec, matched.route.variant ?? 'default');

  const hit = await cache.match(key);
  if (hit) {
    const out = new Response(hit.body, hit);
    out.headers.set('x-cdm-cache', 'HIT');
    out.headers.set('x-cdm-version', String(verSec));
    out.headers.set('x-cdm-route', `mw:${matched.route.variant}`);
    return applySecurityHeaders(out);
  }

  // Miss → render → cache.put with version-keyed key.
  const fresh = await next();
  if (
    fresh.status === 200 &&
    !fresh.headers.get('cache-control')?.includes('private')
  ) {
    const cacheable = fresh.clone();
    cacheable.headers.set(
      'cache-control',
      'public, max-age=86400, s-maxage=86400, immutable'
    );
    cacheable.headers.set('x-cdm-version', String(verSec));
    cacheable.headers.set('x-cdm-cache', 'MISS-STORED');
    cacheable.headers.set('x-cdm-route', `mw:${matched.route.variant}`);
    // Security headers are baked into the cached copy too — so a HIT served
    // from a stale PoP still carries the protection.
    applySecurityHeaders(cacheable);
    try {
      await cache.put(key, cacheable);
    } catch {
      // cache.put can fail on certain response shapes — never block render.
    }
  }
  fresh.headers.set('x-cdm-cache', 'MISS');
  fresh.headers.set('x-cdm-version', String(verSec));
  fresh.headers.set('x-cdm-route', `mw:${matched.route.variant}`);
  return applySecurityHeaders(fresh);
});
