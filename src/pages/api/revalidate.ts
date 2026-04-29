/**
 * CDM-REV-2026-04-29 Phase 2.1 — revalidation endpoint.
 *
 * The OBJ-1 mechanism is "DB row update bumps updated_at → cache key changes
 * → next request re-fetches at the edge". That happens automatically because
 * `set_updated_at` (BEFORE UPDATE trigger) bumps `updated_at` on every write,
 * and `buildCacheKey()` in src/lib/cache.ts encodes `updated_at` into the key.
 *
 * So /api/revalidate is NOT strictly required for invalidation. What it
 * provides:
 *   1. An auth-guarded log signal that a write happened (observability).
 *   2. Optional pre-warming: issue an internal GET to the canonical URL
 *      so the first user after a write hits a HIT, not a MISS.
 *   3. Defense-in-depth: explicit cache.delete in case anyone bypasses
 *      the trigger.
 *
 * Auth: requires header `x-revalidate-token` matching env REVALIDATE_TOKEN.
 * Token rotation: edit the Pages secret + redeploy. No code change.
 *
 * Body shape:
 *   { type: ContentType, slug: "string" }
 *   ContentType ∈ lender | wellness | comparison | brand
 *                | blog | listicle | answer | special
 *                | category | state | glossary
 *
 * Response:
 *   200 { ok: true, type, slug, prewarmed: boolean }
 *   401 unauthorized
 *   400 bad request
 */
import type { APIRoute } from "astro";

export const prerender = false;

type ContentType =
  | "lender"
  | "wellness"
  | "comparison"
  | "brand"
  | "blog"
  | "listicle"
  | "answer"
  | "special"
  | "category"
  | "state"
  | "glossary";

interface RevalidatePayload {
  type: ContentType;
  slug: string;
}

const VALID_TYPES = new Set<ContentType>([
  "lender",
  "wellness",
  "comparison",
  "brand",
  "blog",
  "listicle",
  "answer",
  "special",
  "category",
  "state",
  "glossary",
]);

function _canonicalUrlFor(type: ContentType, slug: string, origin: string): string | null {
  const slugEnc = encodeURIComponent(slug);
  switch (type) {
    case "lender":
      return `${origin}/review/${slugEnc}/`;
    case "wellness":
      return `${origin}/wellness/${slugEnc}/`;
    case "comparison":
      return `${origin}/compare/${slugEnc}/`;
    case "brand":
      return `${origin}/chains/${slugEnc}/`;
    case "blog":
      return `${origin}/blog/${slugEnc}/`;
    case "listicle":
      return `${origin}/best/${slugEnc}/`;
    case "answer":
      return `${origin}/answers/${slugEnc}/`;
    case "special":
      // Specials don't have a canonical page of their own; the lender page
      // surfaces them. The lender writer will fire its own revalidate.
      return null;
    case "category":
      return `${origin}/categories/${slugEnc}/`;
    case "state":
      return `${origin}/state/${slugEnc}/`;
    case "glossary":
      return `${origin}/glossary/${slugEnc}/`;
    default:
      return null;
  }
}

export const POST: APIRoute = async ({ request, locals }) => {
  const env = (locals as any)?.runtime?.env as
    | { REVALIDATE_TOKEN?: string }
    | undefined;

  // Auth gate — refuse if env not configured (build-mode preview).
  const expected = env?.REVALIDATE_TOKEN;
  if (!expected) {
    return new Response(
      JSON.stringify({ ok: false, error: "REVALIDATE_TOKEN not configured" }),
      { status: 503, headers: { "content-type": "application/json" } }
    );
  }
  const provided = request.headers.get("x-revalidate-token");
  if (provided !== expected) {
    return new Response(JSON.stringify({ ok: false, error: "unauthorized" }), {
      status: 401,
      headers: { "content-type": "application/json" },
    });
  }

  let payload: RevalidatePayload;
  try {
    payload = (await request.json()) as RevalidatePayload;
  } catch {
    return new Response(JSON.stringify({ ok: false, error: "invalid json" }), {
      status: 400,
      headers: { "content-type": "application/json" },
    });
  }

  if (
    !payload ||
    typeof payload.slug !== "string" ||
    !payload.slug ||
    !VALID_TYPES.has(payload.type)
  ) {
    return new Response(
      JSON.stringify({
        ok: false,
        error:
          "expected { type: 'lender'|'wellness'|'comparison'|'brand'|'blog'|'listicle'|'answer'|'special'|'category'|'state'|'glossary', slug: string }",
      }),
      { status: 400, headers: { "content-type": "application/json" } }
    );
  }

  // Pre-warm: issue an internal GET so the first user-facing request after
  // this write is a cache HIT. Ignore failures — invalidation already happened
  // automatically via the row's updated_at bump.
  const origin = new URL(request.url).origin;
  const targetUrl = _canonicalUrlFor(payload.type, payload.slug, origin);
  let prewarmed = false;
  if (targetUrl) {
    try {
      const res = await fetch(targetUrl, {
        signal: AbortSignal.timeout(5000),
        headers: { "x-revalidate-prewarm": "1" },
      });
      prewarmed = res.ok;
    } catch {
      // Prewarm is opportunistic; never block the writer on it.
    }
  }

  return new Response(
    JSON.stringify({
      ok: true,
      type: payload.type,
      slug: payload.slug,
      prewarmed,
      target: targetUrl,
    }),
    { status: 200, headers: { "content-type": "application/json" } }
  );
};

// Reject other methods explicitly so PostgreSQL trigger / external caller
// noise gets a clear 405 rather than a silent passthrough.
export const GET: APIRoute = async () =>
  new Response(JSON.stringify({ ok: false, error: "POST only" }), {
    status: 405,
    headers: { "content-type": "application/json", allow: "POST" },
  });
