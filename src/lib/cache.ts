/**
 * CDM-REV-2026-04-29 Phase 1.4 — Cloudflare Cache API helper.
 *
 * Wraps SSR responses with edge caching keyed by:
 *   `${url.pathname}::v=${contentVersion}`
 *
 * Where `contentVersion` is a monotonic int derived from `lenders.updated_at`
 * (or the per-tag KV value once Phase 2 ships).
 *
 * On cache miss: render → cache.put with public, max-age=86400, immutable.
 * On cache hit:  return the cached Response unchanged.
 *
 * Phase 2 invalidation: bumping the content-version in KV changes the cache
 * key, so the next request misses without explicit cache.delete.
 *
 * Runs on Cloudflare Workers — no Node/fs deps.
 */

const DEFAULT_MAX_AGE = 60 * 60 * 24; // 24h
const NAMESPACE = 'creditdoc-v1';

export interface CacheKeyParts {
  /** Pathname incl. query if it changes the rendered HTML (usually no query). */
  pathname: string;
  /** Monotonic int — bump to invalidate. */
  contentVersion: number | string;
  /** Optional discriminator for variants (locale, A/B test, etc.). */
  variant?: string;
}

export function buildCacheKey(req: Request, parts: CacheKeyParts): Request {
  const url = new URL(req.url);
  const v = String(parts.contentVersion);
  const variant = parts.variant ? `::var=${parts.variant}` : '';
  url.pathname = `/__c/${NAMESPACE}/${encodeURIComponent(parts.pathname)}::v=${v}${variant}`;
  // Returning a Request lets cf cache.match / cache.put treat it as the canonical key.
  return new Request(url.toString(), { method: 'GET' });
}

export interface CacheWrapOptions {
  contentVersion: number | string;
  maxAgeSeconds?: number;
  variant?: string;
}

/**
 * Wraps an SSR render with the CF Cache API. Use inside an Astro page like:
 *
 *     export const prerender = false;
 *     ---
 *     const cacheable = await cacheWrap(Astro.request, async () => {
 *       const lender = await getLenderBySlug(slug);
 *       return new Response(htmlString, { headers: { 'content-type': 'text/html' }});
 *     }, { contentVersion: lender.updated_at_epoch });
 *     return cacheable;
 *
 * Caller MUST return the result as the page response.
 */
export async function cacheWrap(
  req: Request,
  render: () => Promise<Response>,
  opts: CacheWrapOptions
): Promise<Response> {
  // @ts-expect-error caches global is provided by Cloudflare Workers runtime
  const cache: Cache = caches.default;
  const url = new URL(req.url);
  const key = buildCacheKey(req, {
    pathname: url.pathname,
    contentVersion: opts.contentVersion,
    variant: opts.variant,
  });

  const cached = await cache.match(key);
  if (cached) {
    const hit = new Response(cached.body, cached);
    hit.headers.set('x-cdm-cache', 'HIT');
    hit.headers.set('x-cdm-version', String(opts.contentVersion));
    return hit;
  }

  const fresh = await render();
  // Only cache successful, non-personalized responses.
  if (fresh.status !== 200 || fresh.headers.get('cache-control')?.includes('private')) {
    fresh.headers.set('x-cdm-cache', 'BYPASS');
    return fresh;
  }

  const cacheable = fresh.clone();
  const maxAge = opts.maxAgeSeconds ?? DEFAULT_MAX_AGE;
  cacheable.headers.set(
    'cache-control',
    `public, max-age=${maxAge}, s-maxage=${maxAge}, immutable`
  );
  cacheable.headers.set('x-cdm-version', String(opts.contentVersion));
  cacheable.headers.set('x-cdm-cache', 'MISS');

  // Fire-and-forget cache.put per CF Workers pattern.
  // In Astro middleware/endpoints we use ctx.waitUntil; here we await for safety.
  await cache.put(key, cacheable);

  fresh.headers.set('x-cdm-cache', 'MISS');
  fresh.headers.set('x-cdm-version', String(opts.contentVersion));
  return fresh;
}
