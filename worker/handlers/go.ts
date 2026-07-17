/**
 * /go/[slug] — affiliate redirect. Ported from src/pages/go/[slug].ts (87 LoC).
 *
 * Uses runtime Supabase for lender lookup + shared outbound helpers for
 * destination URL selection. Runs on the anon key + RLS.
 */
import { getLenderWithBodyBySlugRuntime, type RuntimeLenderEnv } from "../../src/lib/db";
import { getLenderDestination } from "../../src/utils/outbound";
import type { Env } from "../index";

function withTracking(url: URL, slug: string, source: string): URL {
  if (!url.searchParams.has("utm_source")) url.searchParams.set("utm_source", "creditdoc");
  if (!url.searchParams.has("utm_medium")) url.searchParams.set("utm_medium", "referral");
  if (!url.searchParams.has("utm_campaign")) url.searchParams.set("utm_campaign", "lender_cta");
  if (!url.searchParams.has("utm_content")) url.searchParams.set("utm_content", `${source}_${slug}`);
  return url;
}

export async function handleGoRedirect(request: Request, env: Env): Promise<Response> {
  const url = new URL(request.url);
  const parts = url.pathname.replace(/^\/+|\/+$/g, "").split("/");
  const slug = parts[1] || "";
  if (!slug) {
    return new Response("Bad Request", { status: 400 });
  }

  const runtimeEnv: RuntimeLenderEnv = {
    SUPABASE_URL: env.SUPABASE_URL,
    SUPABASE_ANON_KEY: env.SUPABASE_ANON_KEY,
  };
  const row = await getLenderWithBodyBySlugRuntime(slug, runtimeEnv);
  if (!row) {
    return new Response("Lender not found", {
      status: 404,
      headers: { "content-type": "text/plain; charset=utf-8" },
    });
  }

  const body = (row.body_inline ?? {}) as Record<string, unknown>;
  const affiliateUrl = typeof body.affiliate_url === "string" ? body.affiliate_url.trim() : "";
  const websiteUrl = typeof body.website_url === "string" ? body.website_url.trim() : "";
  const destination = getLenderDestination({
    slug,
    affiliate_url: affiliateUrl,
    website_url: websiteUrl,
  });

  if (!destination) {
    return new Response("No destination available", {
      status: 404,
      headers: { "content-type": "text/plain; charset=utf-8" },
    });
  }

  let dest: URL;
  try {
    dest = new URL(destination);
  } catch {
    return new Response("Invalid destination", {
      status: 502,
      headers: { "content-type": "text/plain; charset=utf-8" },
    });
  }
  if (!["http:", "https:"].includes(dest.protocol)) {
    return new Response("Invalid destination", {
      status: 502,
      headers: { "content-type": "text/plain; charset=utf-8" },
    });
  }

  const source = url.searchParams.get("source") || "site";
  if (!affiliateUrl) dest = withTracking(dest, slug, source);

  return new Response(null, {
    status: 302,
    headers: {
      location: dest.toString(),
      "cache-control": "no-store",
      "x-robots-tag": "noindex, nofollow",
    },
  });
}
