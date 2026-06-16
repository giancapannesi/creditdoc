import type { APIContext } from "astro";
import {
  getLenderWithBodyBySlugRuntime,
  type RuntimeLenderEnv,
} from "../../lib/db";
import { getLenderDestination } from "../../utils/outbound";

export const prerender = false;

function withTracking(url: URL, slug: string, source: string): URL {
  if (!url.searchParams.has("utm_source")) {
    url.searchParams.set("utm_source", "creditdoc");
  }
  if (!url.searchParams.has("utm_medium")) {
    url.searchParams.set("utm_medium", "referral");
  }
  if (!url.searchParams.has("utm_campaign")) {
    url.searchParams.set("utm_campaign", "lender_cta");
  }
  if (!url.searchParams.has("utm_content")) {
    url.searchParams.set("utm_content", `${source}_${slug}`);
  }
  return url;
}

export async function GET(ctx: APIContext): Promise<Response> {
  const slug = ctx.params.slug;
  if (!slug) {
    return new Response("Bad Request", { status: 400 });
  }

  const env = (ctx.locals as any)?.runtime?.env as RuntimeLenderEnv | undefined;
  const row = await getLenderWithBodyBySlugRuntime(slug, env);
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

  let url: URL;
  try {
    url = new URL(destination);
  } catch {
    return new Response("Invalid destination", {
      status: 502,
      headers: { "content-type": "text/plain; charset=utf-8" },
    });
  }

  if (!["http:", "https:"].includes(url.protocol)) {
    return new Response("Invalid destination", {
      status: 502,
      headers: { "content-type": "text/plain; charset=utf-8" },
    });
  }

  const source = new URL(ctx.request.url).searchParams.get("source") || "site";
  if (!affiliateUrl) {
    url = withTracking(url, slug, source);
  }

  return new Response(null, {
    status: 302,
    headers: {
      location: url.toString(),
      "cache-control": "no-store",
      "x-robots-tag": "noindex, nofollow",
      "x-cdm-route": "/go/[slug]",
      "x-cdm-slug": slug,
    },
  });
}
