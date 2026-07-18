/**
 * /api/revalidate — auth-guarded cache pre-warm endpoint.
 * Ported from src/pages/api/revalidate.ts (182 LoC).
 *
 * Actual invalidation happens automatically via `updated_at` bumping the
 * cache key; this endpoint is observability + optional pre-warm.
 */
import type { Env } from "../index";

type ContentType =
  | "lender" | "wellness" | "comparison" | "brand"
  | "blog" | "listicle" | "answer" | "special"
  | "category" | "state" | "glossary";

interface RevalidatePayload {
  type: ContentType;
  slug: string;
}

const VALID_TYPES = new Set<ContentType>([
  "lender", "wellness", "comparison", "brand",
  "blog", "listicle", "answer", "special",
  "category", "state", "glossary",
]);

function canonicalUrlFor(type: ContentType, slug: string, origin: string): string | null {
  const s = encodeURIComponent(slug);
  switch (type) {
    case "lender": return `${origin}/review/${s}/`;
    case "wellness": return `${origin}/wellness/${s}/`;
    case "comparison": return `${origin}/compare/${s}/`;
    case "brand": return `${origin}/chains/${s}/`;
    case "blog": return `${origin}/blog/${s}/`;
    case "listicle": return `${origin}/best/${s}/`;
    case "answer": return `${origin}/answers/${s}/`;
    case "special": return null;
    case "category": return `${origin}/categories/${s}/`;
    case "state": return `${origin}/state/${s}/`;
    case "glossary": return `${origin}/glossary/${s}/`;
    default: return null;
  }
}

function jsonResponse(body: unknown, status: number, extraHeaders: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json", ...extraHeaders },
  });
}

export async function handleRevalidate(request: Request, env: Env): Promise<Response> {
  if (request.method !== "POST") {
    return jsonResponse({ ok: false, error: "POST only" }, 405, { allow: "POST" });
  }

  const expected = env.REVALIDATE_TOKEN;
  if (!expected) {
    return jsonResponse({ ok: false, error: "REVALIDATE_TOKEN not configured" }, 503);
  }
  const provided = request.headers.get("x-revalidate-token");
  if (provided !== expected) {
    return jsonResponse({ ok: false, error: "unauthorized" }, 401);
  }

  let payload: RevalidatePayload;
  try {
    payload = (await request.json()) as RevalidatePayload;
  } catch {
    return jsonResponse({ ok: false, error: "invalid json" }, 400);
  }

  if (
    !payload ||
    typeof payload.slug !== "string" ||
    !payload.slug ||
    !VALID_TYPES.has(payload.type)
  ) {
    return jsonResponse(
      {
        ok: false,
        error:
          "expected { type: 'lender'|'wellness'|'comparison'|'brand'|'blog'|'listicle'|'answer'|'special'|'category'|'state'|'glossary', slug: string }",
      },
      400,
    );
  }

  const origin = new URL(request.url).origin;
  const target = canonicalUrlFor(payload.type, payload.slug, origin);
  let prewarmed = false;
  if (target) {
    try {
      const res = await fetch(target, {
        signal: AbortSignal.timeout(5000),
        headers: { "x-revalidate-prewarm": "1" },
      });
      prewarmed = res.ok;
    } catch {
      // opportunistic — never block writer
    }
  }

  return jsonResponse(
    { ok: true, type: payload.type, slug: payload.slug, prewarmed, target },
    200,
  );
}
