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
  getLenderWithBodyBySlugRuntime,
  contentVersionOf,
  type RuntimeLenderWithBody,
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

function renderList(items: unknown, ordered = false): string {
  if (!Array.isArray(items) || items.length === 0) return "";
  const tag = ordered ? "ol" : "ul";
  return `<${tag}>${items
    .map((x) => `<li>${escapeHtml(String(x))}</li>`)
    .join("")}</${tag}>`;
}

function renderHtml(lender: RuntimeLenderWithBody, ver: number): string {
  const body = (lender.body_inline ?? {}) as Record<string, unknown>;
  const name = escapeHtml(lender.name);
  const cat = escapeHtml(lender.category);
  const state = lender.state ? escapeHtml(lender.state) : "";
  const reviewHref = `/review/${encodeURIComponent(lender.slug)}/`;
  const verIso = new Date(ver * 1000).toISOString();
  // CDM-REV Phase 2.4 — emit the source-of-truth last_updated string verbatim
  // so end-to-end propagation probes (e.g. cdm_rev_phase24_e2e_probe.py) can
  // observe sub-second writer activity. verIso above floors to whole seconds
  // because the Cache-API key uses second precision.
  const lastUpdatedRaw = body.last_updated
    ? escapeHtml(String(body.last_updated))
    : "";
  const descShort = body.description_short
    ? escapeHtml(String(body.description_short))
    : "";
  const descLong = body.description_long
    ? escapeHtml(String(body.description_long))
    : "";
  const rating = body.rating ? escapeHtml(String(body.rating)) : "";
  const pros = renderList(body.pros);
  const cons = renderList(body.cons);
  const services = renderList(body.services);
  const bodyFieldCount = Object.keys(body).length;
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="robots" content="noindex,nofollow">
  <title>${name} — CreditDoc (SSR pilot)</title>
  <meta name="description" content="${descShort}">
  <meta name="cdm-last-updated" content="${lastUpdatedRaw}">
  <link rel="canonical" href="${reviewHref}">
</head>
<body style="font-family: system-ui, sans-serif; max-width: 720px; margin: 2rem auto; padding: 0 1rem; line-height: 1.6;">
  <p style="color:#888;font-size:0.875rem">CreditDoc · SSR pilot · /r/${escapeHtml(lender.slug)} · body fields: ${bodyFieldCount}</p>
  <h1 style="margin:0.5rem 0">${name}${rating ? ` <span style="color:#c80;font-size:1rem">★ ${rating}</span>` : ""}</h1>
  <p style="color:#444">${cat}${state ? ` · ${state}` : ""}</p>
  ${descShort ? `<p style="font-style:italic;color:#222">${descShort}</p>` : ""}
  ${descLong ? `<h2>About</h2><p>${descLong}</p>` : ""}
  ${pros ? `<h2>Pros</h2>${pros}` : ""}
  ${cons ? `<h2>Cons</h2>${cons}` : ""}
  ${services ? `<h2>Services</h2>${services}` : ""}
  <hr style="margin:2rem 0;border:none;border-top:1px solid #eee">
  <p>For the full styled review, see <a href="${reviewHref}">${reviewHref}</a>.</p>
  <p style="color:#888;font-size:0.75rem">
    Content version: ${ver} (${verIso})<br>
    Architecture: Astro 5 hybrid · Cloudflare Pages Workers · Supabase PostgREST anon · body_inline jsonb
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

  const lender = await getLenderWithBodyBySlugRuntime(slug, env);
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
