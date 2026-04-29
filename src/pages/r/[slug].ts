/**
 * CDM-REV-2026-04-29 Phase 1.3.B (Option C pilot) — SSR lender route.
 *
 * URL: /r/<slug>
 * Mode: SSR (prerender = false). Renders on Cloudflare Workers per request,
 * Cache-API-cached by content-version. Existing static /review/[slug] is
 * untouched — this is a parallel pilot proving OBJ-1 + OBJ-2A end-to-end
 * without needing an ALTER TABLE (which is off-limits this loop).
 *
 * Body content is intentionally minimal — the live `lenders` table is a
 * catalog index only (see src/lib/db.ts schema note). The pilot proves the
 * architecture; full body content needs Phase 1.3.B-Option-A first.
 *
 * Status: pilot — DO NOT link to from sitemap or marketing pages until
 * Jammi greenlights the cutover. `noindex` on the page prevents SERPs from
 * picking it up.
 */
import type { APIContext } from "astro";
import {
  getLenderBySlugRuntime,
  contentVersionOf,
  type RuntimeLender,
} from "../../lib/db";
import { cacheWrap } from "../../lib/cache";

export const prerender = false;

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderHtml(lender: RuntimeLender, ver: number): string {
  const name = escapeHtml(lender.name);
  const cat = escapeHtml(lender.category);
  const state = lender.state ? escapeHtml(lender.state) : "";
  const reviewHref = `/review/${encodeURIComponent(lender.slug)}/`;
  const verIso = new Date(ver * 1000).toISOString();
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="robots" content="noindex,nofollow">
  <title>${name} — CreditDoc (SSR pilot)</title>
  <link rel="canonical" href="${reviewHref}">
</head>
<body style="font-family: system-ui, sans-serif; max-width: 640px; margin: 2rem auto; padding: 0 1rem;">
  <p style="color:#888;font-size:0.875rem">CreditDoc · SSR pilot · /r/${escapeHtml(lender.slug)}</p>
  <h1 style="margin:0.5rem 0">${name}</h1>
  <p style="color:#444">${cat}${state ? ` · ${state}` : ""}</p>
  <hr style="margin:2rem 0;border:none;border-top:1px solid #eee">
  <p>This is the SSR-rendered catalog row for <strong>${name}</strong>.</p>
  <p>For the full lender review, see the static page at <a href="${reviewHref}">${reviewHref}</a>.</p>
  <hr style="margin:2rem 0;border:none;border-top:1px solid #eee">
  <p style="color:#888;font-size:0.75rem">
    Content version: ${ver} (${verIso})<br>
    Architecture: Astro 5 hybrid · Cloudflare Pages Workers · Supabase PostgREST anon
  </p>
</body>
</html>`;
}

export async function GET(ctx: APIContext): Promise<Response> {
  const slug = ctx.params.slug;
  if (!slug) {
    return new Response("Bad Request", { status: 400 });
  }

  // Astro Cloudflare adapter exposes runtime bindings on locals.runtime.env.
  const env = (ctx.locals as any)?.runtime?.env as
    | { SUPABASE_URL?: string; SUPABASE_ANON_KEY?: string }
    | undefined;

  const lender = await getLenderBySlugRuntime(slug, env);
  if (!lender) {
    return new Response("Lender not found", {
      status: 404,
      headers: { "content-type": "text/plain; charset=utf-8" },
    });
  }

  const ver = contentVersionOf(lender);

  return cacheWrap(
    ctx.request,
    async () => {
      const html = renderHtml(lender, ver);
      return new Response(html, {
        status: 200,
        headers: {
          "content-type": "text/html; charset=utf-8",
          "x-cdm-route": "/r/[slug]",
          "x-cdm-slug": lender.slug,
        },
      });
    },
    { contentVersion: ver }
  );
}
