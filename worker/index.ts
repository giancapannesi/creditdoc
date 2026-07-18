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
    if (path === "/api/geo") {
      return handleGeo(request);
    }
    if (path.startsWith("/go/")) {
      return handleGoRedirect(request, env);
    }

    if (path === "/api/search") {
      return handleSearch(request, env);
    }
    if (path === "/api/email-signup") {
      return handleEmailSignup(request, env);
    }
    if (path === "/api/origination-intake") {
      return handleOriginationIntake(request, env);
    }
    if (path === "/api/revalidate") {
      return handleRevalidate(request, env);
    }

    // Fall through to static assets (dist/ contents including _redirects, _headers).
    return env.ASSETS.fetch(request);
  },
};
