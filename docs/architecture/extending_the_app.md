# Extending CreditDoc — adding a new SSR surface in 6 steps

**Audience:** future contributor (human or agent) who wants to add a new dynamic
route to CreditDoc without rebuilding the world. Written 2026-04-29 against the
CDM-REV-2026-04-29 hybrid architecture (Astro 5 + Cloudflare Pages + Supabase).

This doc serves **OBJ-2 (Future-proof — can grow with the business):** new
surface ships in <1 day, <50 LOC of new code, no infra rewrite, no vendor
swap. Treat it as the contract — if these 6 steps don't fit your case, the
plan is wrong, not the route.

---

## When to add an SSR route vs a static page

| Page kind                                  | Build mode  | Why                                                                                  |
|--------------------------------------------|-------------|--------------------------------------------------------------------------------------|
| Marketing copy (`/`, `/about`, `/privacy`) | Static      | Content rarely changes. Free CDN.                                                    |
| Money pages (`/best/...`)                  | Static      | Curated. Edited via PR. CDN-fronted.                                                 |
| Listicles + cluster answers (`/answers/`)  | Static      | Build-time render from DB export. SEO-locked URLs.                                   |
| Lender review (`/review/[slug]`)           | **SSR**     | 20K+ rows, churns daily. Stale-while-revalidate via Cache API + content-version.    |
| User-personalised page (quiz, dashboards)  | **SSR**     | Per-request data. No prerender possible.                                             |
| API endpoint (`/api/...`)                  | **SSR**     | Functions, not pages.                                                                |

**Rule of thumb:** if the page would change between two builds without code
edits, it's SSR.

---

## The 6 steps (each step is one commit)

### 1. Add the route file with `prerender = false`

```astro
---
// src/pages/r/[slug].astro
export const prerender = false;

import type { APIContext } from 'astro';
import { getLenderBySlugRuntime } from '../../lib/db';
import { cacheWrap } from '../../lib/cache';

const { slug } = Astro.params;
const env = Astro.locals.runtime?.env;
const lender = await getLenderBySlugRuntime(slug!, env);
if (!lender) return new Response('Not Found', { status: 404 });
---
<html><body>
  <h1>{lender.brand_name}</h1>
  <!-- … -->
</body></html>
```

The `prerender = false` flag is the opt-in. Without it, Astro 5 builds this
page statically (default) and the adapter is a no-op for that path. With it,
the page renders on the Worker per request.

### 2. Wire the data path (read-only)

Use `src/lib/db.ts`. It's the single read-side helper for runtime data.

- `getLenderBySlugRuntime(slug, env)` — single row, RLS-gated, 2.5s timeout
- `getLenderBody(lender, env)` — body from `body_inline` then R2 fallback
- `contentVersionOf(lender)` — monotonic int from `updated_at`

If you need a new query, **add a new exported function to `db.ts`**, don't
inline `fetch()` calls in route files. One module owns Supabase.

**Service-role NEVER ships to the Worker.** Only `SUPABASE_ANON_KEY` is in the
runtime. Writes go through `/api/revalidate` which lives in the same worker
but is a separate code path with token + IP allowlist.

### 3. Wrap the handler in the Cache API

Use `src/lib/cache.ts`:

```ts
const version = contentVersionOf(lender);
return cacheWrap(Astro.request, async () => {
  // your render fn — return a Response
}, { pathname: '/r/' + slug, contentVersion: version });
```

Cache key = `/__c/creditdoc-v1/{path}::v={ver}`. When the row's `updated_at`
ticks, the cache key changes — the next request misses cache and rebuilds.
This is OBJ-1 in one line of code.

`cacheWrap` adds `cache-control: public, max-age=86400, immutable` and an
`x-cdm-cache: HIT|MISS|BYPASS` header for telemetry.

### 4. Wire revalidation (only if the route's content can change)

Edit `src/pages/api/revalidate.ts` (the existing endpoint, not a new one):

```ts
// inside switch (table) case 'lenders':
await env.VERSIONS.put(`lender:${slug}`, String(Date.now()));
// optional: explicit cache.delete on the path keys you know
```

`tools/creditdoc_db.py` POSTs to `/api/revalidate` with a token after every
write. If your new route's data lives in an existing table, no Python change
is needed — the `/api/revalidate` switch already covers it. If it's a new
table, add the case + add the POST in `creditdoc_db.py`.

### 5. Smoke-test on `wrangler pages dev` BEFORE committing

```bash
cd creditdoc
npm run build  # or `astro build` — the new route is in the worker bundle
npx wrangler pages dev dist
# in another shell:
curl -i http://localhost:8788/r/<known-slug>
curl -i http://localhost:8788/r/<known-slug>  # second request → x-cdm-cache: HIT
```

If the second request doesn't show `HIT`, your `cacheWrap` call is wrong.
Don't ship until cache is provably warming.

### 6. Run the verifier and commit

```bash
python3 tools/verify_strategic_objectives.py
```

If OBJ-1 stayed RED, the route didn't ship the way you think it did. Either
`prerender = false` is missing, or the adapter isn't wired, or the route
file's name doesn't match the URL. Fix before committing.

If OBJ-1 went GREEN: commit, push, deploy to preview (`wrangler pages deploy
dist`), measure TTFB warm p95 against the preview URL. Acceptance bar:
warm <100ms p95.

---

## Anti-patterns (don't)

- **Don't** add a new top-level lib for "your route's data layer". Extend
  `db.ts`. Each module that talks to Supabase is one more place service-role
  could leak.
- **Don't** inline cache-control headers. Use `cacheWrap` so the cache key
  format stays consistent across routes (telemetry assumes the format).
- **Don't** revalidate by sending `Cache-Control: no-cache` from the worker.
  That defeats the entire architecture. Use cache-key versioning (step 3).
- **Don't** `import` from `src/content/` in an SSR route. The `src/`
  directory is NOT in the worker bundle — it's the source for the build.
  At runtime, `src/utils/data.ts` (which uses `fs.readdirSync`) does not
  exist.
- **Don't** ship without the verifier going GREEN. The verifier exists to
  catch exactly the class of "I shipped the config but not the behaviour"
  bug that has bitten this project twice already.

---

## Cost & blast-radius math (so you know what "<50 LOC" buys)

| Resource          | New SSR route adds                       |
|-------------------|------------------------------------------|
| CF Pages requests | +1 per uncached request                  |
| Workers CPU ms    | +1 per uncached request, ~5–20ms typical |
| Supabase rows/req | 1 PostgREST GET per uncached request     |
| R2 GETs           | 1 per body fetch (only if `body_r2_key`) |
| Cache API storage | bounded by max-age + key cardinality     |

At 100K req/day with 80% cache hit rate, this is well inside CF Pages'
free tier (100K/day) and the Supabase free tier (500MB egress, ample row
budget). You don't need to ask for cost approval to add a route. You DO
need approval to (a) flip a route to no-cache, (b) add a route that hits
external paid APIs (OpenAI, KE, DataForSEO), (c) add a write-side endpoint.

---

## When this doc is wrong

If your route doesn't fit the 6-step shape — for example, you need
WebSockets, or per-user auth state, or a cron-triggered backfill — STOP and
write a one-page ADR in `creditdoc/docs/plans/` before coding. Surface the
gap to the founder. Don't bend the architecture to fit a one-off; either
the architecture grows to absorb the new shape, or the new shape is the
wrong shape.

---

## See also

- `creditdoc/docs/plans/2026-04-29_REVISED_MIGRATION_PLAN_HYBRID_FIRST.md` — full plan rev 4
- `CreditDoc Project Improvement/2026-04-29_CREDITDOC_SITE_ARCHITECTURE.md` — A.1–A.14 build plan
- `creditdoc/src/lib/db.ts` — runtime data layer (read)
- `creditdoc/src/lib/cache.ts` — Cache API helper
- `creditdoc/tools/verify_strategic_objectives.py` — pre-ship gate
