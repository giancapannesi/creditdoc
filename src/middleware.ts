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

const NAMESPACE = 'creditdoc-v1-mw';

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
  table: 'answers' | 'lenders' | 'listicles';
  /** Maps URL pathname → row slug. Returns null if path is not an SSR row page. */
  match: (pathname: string) => string | null;
  /** Optional: route variant tag (for cache-key namespacing). */
  variant?: string;
}

// Slug-pattern routes — middleware will fetch updated_at for the matched row
// and key the cache by (pathname + updated_at_epoch).
//
// NOTE: /r/[slug] already does its own cacheWrap so it's intentionally absent.
// /answers/index and /answers/[slug] both ride /answers/* — the index is
// excluded by the slug-extraction returning null when no slug is present.
const CACHEABLE_ROUTES: CacheableRoute[] = [
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
];

interface RuntimeEnvLike {
  SUPABASE_URL?: string;
  SUPABASE_ANON_KEY?: string;
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

  const env = (context.locals as any)?.runtime?.env as RuntimeEnvLike | undefined;
  if (!env?.SUPABASE_URL || !env?.SUPABASE_ANON_KEY) {
    // Build-mode preview or env not configured — don't cache, just pass.
    const fresh = await next();
    fresh.headers.set('x-cdm-cache', 'BYPASS-NOENV');
    return applySecurityHeaders(fresh);
  }

  // Version probe — if it fails, skip caching for this request.
  const updatedAt = await fetchUpdatedAt(matched.route.table, matched.slug, env);
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
