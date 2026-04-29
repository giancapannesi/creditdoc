/**
 * CDM-REV-2026-04-29 Phase 4.1 — growth-readiness probe.
 *
 * URL: /api/lender/<slug>
 * Mode: SSR JSON. Same data shape as the catalog row, served as
 *       application/json. Same db.ts + cache.ts as /r/[slug].
 *
 * Purpose: prove that adding a new product surface — here, a JSON API for
 * the same lender data — costs <50 LOC and zero infrastructure work.
 *
 * Measure (Phase 4.2):
 *   wc -l src/pages/api/lender/[slug].ts → file LOC
 *   diff vs src/pages/r/[slug].ts → same helpers, different content-type
 *
 * Phase 4.4 will decommission this route once growth-readiness is recorded.
 * Until then it's noindex via robots.txt (handled at the platform level).
 */
import type { APIContext } from "astro";
import {
  getLenderBySlugRuntime,
  contentVersionOf,
  type RuntimeLender,
} from "../../../lib/db";
import { cacheWrap } from "../../../lib/cache";

export const prerender = false;

function payload(lender: RuntimeLender, ver: number) {
  return {
    slug: lender.slug,
    name: lender.name,
    category: lender.category,
    state: lender.state,
    brand_slug: lender.brand_slug,
    has_logo: lender.has_logo,
    seo_tier: lender.seo_tier,
    updated_at: lender.updated_at,
    content_version: ver,
    canonical_html: `/review/${encodeURIComponent(lender.slug)}/`,
  };
}

export async function GET(ctx: APIContext): Promise<Response> {
  const slug = ctx.params.slug;
  if (!slug) return new Response("Bad Request", { status: 400 });

  const env = (ctx.locals as any)?.runtime?.env as
    | { SUPABASE_URL?: string; SUPABASE_ANON_KEY?: string }
    | undefined;

  const lender = await getLenderBySlugRuntime(slug, env);
  if (!lender) {
    return new Response(JSON.stringify({ error: "not_found", slug }), {
      status: 404,
      headers: { "content-type": "application/json; charset=utf-8" },
    });
  }
  const ver = contentVersionOf(lender);
  return cacheWrap(
    ctx.request,
    async () =>
      new Response(JSON.stringify(payload(lender, ver)), {
        status: 200,
        headers: {
          "content-type": "application/json; charset=utf-8",
          "x-cdm-route": "/api/lender/[slug]",
        },
      }),
    { contentVersion: ver }
  );
}
