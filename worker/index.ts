/**
 * worker/index.ts — Hand-rolled Cloudflare Worker for CreditDoc runtime routes.
 *
 * Replaces the @astrojs/cloudflare adapter's `dist/_worker.js/` shim.
 * Once wired via wrangler.toml, `astro build` no longer emits an SSR runtime;
 * this file is the entire dynamic surface.
 *
 * Routes handled here (all `prerender = false` in the old Astro world):
 *   /api/geo                  → CF geo header echo (13 lines)
 *   /api/search               → PostgREST search (245 lines) [Phase R1.2b]
 *   /api/email-signup POST    → Supabase insert + email trigger (322 lines) [Phase R1.2b]
 *   /api/origination-intake POST → Supabase insert (358 lines) [Phase R1.2b]
 *   /api/revalidate POST      → Cache invalidation webhook (182 lines) [Phase R1.2b]
 *   /go/[slug]                → Affiliate redirect (87 lines)
 *
 * Everything else → env.ASSETS.fetch(request) which serves from `dist/`.
 *
 * Redirects (from src/middleware.ts LEGACY_PATH_REDIRECTS + STATE_CODE_REDIRECTS):
 *   Handled by dist/_redirects file (Cloudflare Static Assets native support).
 *   Rock 1 Phase R1.1 migrated all 36 legacy path + 50 state code entries.
 */

import { handleEmailSignup } from "./handlers/email-signup";
import { handleGeo } from "./handlers/geo";
import { handleGoRedirect } from "./handlers/go";
import { handleOriginationIntake } from "./handlers/origination-intake";
import { handleRevalidate } from "./handlers/revalidate";
import { handleSearch } from "./handlers/search";

// Ported 2026-07-27 from deleted src/middleware.ts (AstroKill 2026-07-18 commit
// e0c1be3041 deleted this without restoring the /search/?state= redirect).
// GSC flagged the resulting duplicate canonicals on /search/?state=Utah etc.
const STATE_NAME_SLUGS = new Set<string>([
  "alabama","alaska","arizona","arkansas","california","colorado","connecticut",
  "delaware","florida","georgia","hawaii","idaho","illinois","indiana","iowa",
  "kansas","kentucky","louisiana","maine","maryland","massachusetts","michigan",
  "minnesota","mississippi","missouri","montana","nebraska","nevada",
  "new-hampshire","new-jersey","new-mexico","new-york","north-carolina",
  "north-dakota","ohio","oklahoma","oregon","pennsylvania","rhode-island",
  "south-carolina","south-dakota","tennessee","texas","utah","vermont",
  "virginia","washington","west-virginia","wisconsin","wyoming",
]);

function searchStateTarget(url: URL): string | null {
  const stateRaw = url.searchParams.get("state");
  if (!stateRaw) return null;
  // Only fire on state-only searches. Compound queries stay on /search/.
  const keys = Array.from(url.searchParams.keys()).filter((k) => url.searchParams.get(k));
  if (keys.length !== 1 || keys[0] !== "state") return null;
  const slug = stateRaw.trim().toLowerCase().replace(/\s+/g, "-").replace(/-+/g, "-");
  if (!STATE_NAME_SLUGS.has(slug)) return null;
  return `/state/${slug}/`;
}

// 19 known category slugs (matches dist/categories/*/). Used for canonical
// rewrites — /search/?category=X is a functional filter (View All N Companies
// button on /categories/*/ pages needs it to work), so we do NOT 301 it.
// Rewriting the canonical tag tells Google the equivalent indexable page is
// /categories/X/ without breaking the button UX. Added 2026-07-27.
const CATEGORY_SLUGS = new Set<string>([
  "atm","banking","bankruptcy","build-credit","business-loans","check-cashing",
  "credit-cards","credit-monitoring","credit-repair","credit-unions",
  "debt-relief","emergency-cash","fintech","free-help","insurance","mortgages",
  "pawn-shops","payday-alternatives","personal-loans",
]);

// Returns the canonical target path for a /search/?* request when the query
// maps cleanly to an indexable page. Returns null for compound queries or
// unknown values (canonical stays /search/).
function searchCanonicalTarget(url: URL): string | null {
  const catRaw = url.searchParams.get("category");
  if (catRaw) {
    const keys = Array.from(url.searchParams.keys()).filter((k) => url.searchParams.get(k));
    if (keys.length === 1 && keys[0] === "category") {
      const slug = catRaw.trim().toLowerCase();
      if (CATEGORY_SLUGS.has(slug)) return `/categories/${slug}/`;
    }
  }
  return null;
}

// Rewrites the canonical + og:url tags in the /search/ static HTML before
// returning to the client. Only for known single-param queries that map to
// an indexable page. Fail-open — any anomaly returns the original asset.
async function serveSearchWithCanonicalRewrite(
  request: Request,
  env: Env,
  canonicalPath: string
): Promise<Response> {
  try {
    const bareSearchUrl = new URL("/search/", request.url).toString();
    const asset = await env.ASSETS.fetch(new Request(bareSearchUrl, request));
    const ct = asset.headers.get("content-type") || "";
    if (asset.status !== 200 || !ct.includes("html")) return asset;
    const html = await asset.text();
    const origin = new URL(request.url).origin;
    const newHref = `${origin}${canonicalPath}`;
    const rewritten = html
      .replace(
        /<link rel="canonical" href="[^"]*\/search\/"\s*\/?>/,
        `<link rel="canonical" href="${newHref}">`
      )
      .replace(
        /<meta property="og:url" content="[^"]*\/search\/"\s*\/?>/,
        `<meta property="og:url" content="${newHref}">`
      );
    const headers = new Headers(asset.headers);
    headers.delete("content-length");
    return new Response(rewritten, { status: 200, headers });
  } catch {
    return env.ASSETS.fetch(request);
  }
}

// STATE_NAME_TO_ABBR — for /browse/<cat>/<city>-<fullstate>/ → /browse/<cat>/<city>-<ab>/
// Ported 2026-07-27 from deleted src/middleware.ts browseCityStateRedirectTarget.
// 467 /browse/ URLs live; long-state-name variants were 404ing since 2026-07-18.
const STATE_NAME_TO_ABBR: Record<string, string> = {
  "alabama": "al", "alaska": "ak", "arizona": "az", "arkansas": "ar",
  "california": "ca", "colorado": "co", "connecticut": "ct", "delaware": "de",
  "florida": "fl", "georgia": "ga", "hawaii": "hi", "idaho": "id",
  "illinois": "il", "indiana": "in", "iowa": "ia", "kansas": "ks",
  "kentucky": "ky", "louisiana": "la", "maine": "me", "maryland": "md",
  "massachusetts": "ma", "michigan": "mi", "minnesota": "mn", "mississippi": "ms",
  "missouri": "mo", "montana": "mt", "nebraska": "ne", "nevada": "nv",
  "new-hampshire": "nh", "new-jersey": "nj", "new-mexico": "nm", "new-york": "ny",
  "north-carolina": "nc", "north-dakota": "nd", "ohio": "oh", "oklahoma": "ok",
  "oregon": "or", "pennsylvania": "pa", "rhode-island": "ri",
  "south-carolina": "sc", "south-dakota": "sd", "tennessee": "tn",
  "texas": "tx", "utah": "ut", "vermont": "vt", "virginia": "va",
  "washington": "wa", "west-virginia": "wv", "wisconsin": "wi", "wyoming": "wy",
};
// Sort state slugs by length DESC so multi-word states match before single-word
// (e.g. "new-york" checked before "york" — though "york" isn't a state, the
// principle holds for "north-carolina" vs "carolina" etc.)
const STATE_NAME_SLUGS_SORTED = Object.keys(STATE_NAME_TO_ABBR).sort((a, b) => b.length - a.length);

function browseFullstateRedirect(pathname: string): string | null {
  const m = pathname.match(/^\/browse\/([^/]+)\/([^/]+)\/?$/);
  if (!m) return null;
  const category = m[1];
  const cityStateSlug = m[2].toLowerCase();
  for (const stateSlug of STATE_NAME_SLUGS_SORTED) {
    const suffix = `-${stateSlug}`;
    if (cityStateSlug.endsWith(suffix)) {
      const citySlug = cityStateSlug.slice(0, -suffix.length);
      if (!citySlug) return null;
      const abbr = STATE_NAME_TO_ABBR[stateSlug];
      const target = `/browse/${category}/${citySlug}-${abbr}/`;
      return target === pathname ? null : target;
    }
  }
  return null;
}

export interface Env {
  ASSETS: Fetcher;
  SUPABASE_URL?: string;
  SUPABASE_ANON_KEY?: string;
  SUPABASE_SERVICE_ROLE_KEY?: string;
  REVALIDATE_TOKEN?: string;
  EMAIL_SIGNUP_WEBHOOK?: string;
}

interface Fetcher {
  fetch(request: Request): Promise<Response>;
}

export default {
  async fetch(request: Request, env: Env, _ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;

    // Runtime API routes — order matters, most-specific first.
    if (path === "/api/geo" || path === "/api/geo/") {
      return handleGeo(request);
    }
    if (path.startsWith("/go/")) {
      return handleGoRedirect(request, env);
    }

    if (path === "/api/search" || path === "/api/search/") {
      return handleSearch(request, env);
    }
    if (path === "/api/email-signup" || path === "/api/email-signup/") {
      return handleEmailSignup(request, env);
    }
    if (path === "/api/origination-intake" || path === "/api/origination-intake/") {
      return handleOriginationIntake(request, env);
    }
    if (path === "/api/revalidate" || path === "/api/revalidate/") {
      return handleRevalidate(request, env);
    }

    // Regulatory consolidation 2026-07-19: /trends/ family retired.
    // Handled here (not _redirects) because Cloudflare's dynamic-rule limit is 100.
    if (path === "/trends" || path === "/trends/") {
      return Response.redirect(new URL("/research/consumer-complaints/", url).toString(), 301);
    }
    if (path.startsWith("/trends/")) {
      // 2026-07-27: was redirecting every /trends/{slug}/ to /review/{slug}/#cfpb-profile
      // but ~50% of trend slugs (wells-fargo, chase, discover, ally, consumer-complaints,
      // debt-collection, etc.) have NO /review/ counterpart → 301 chain landed on 404.
      // Founder reported "lots of indexing problems"; this was one source.
      // Safest fix: send everything /trends/* to /research/consumer-complaints/ (200,
      // topically the closest equivalent for the retired CFPB entity trend data).
      return Response.redirect(new URL("/research/consumer-complaints/", url).toString(), 301);
    }

    if (path === "/search" || path === "/search/") {
      const stateTarget = searchStateTarget(url);
      if (stateTarget) {
        return Response.redirect(new URL(stateTarget, url.origin).toString(), 301);
      }
      const canonTarget = searchCanonicalTarget(url);
      if (canonTarget) {
        return serveSearchWithCanonicalRewrite(request, env, canonTarget);
      }
    }

    // Ported 2026-07-27: /browse/<cat>/<city>-<fullstate>/ → /browse/<cat>/<city>-<ab>/
    // Deleted middleware behavior — long-state-name variants were 404ing.
    if (path.startsWith("/browse/")) {
      const browseTarget = browseFullstateRedirect(path);
      if (browseTarget) {
        return Response.redirect(new URL(browseTarget, url.origin).toString(), 301);
      }
    }

    // Fall through to static assets (dist/ contents including _redirects, _headers).
    return env.ASSETS.fetch(request);
  },
};
