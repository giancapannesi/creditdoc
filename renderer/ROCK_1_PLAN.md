# Rock 1 — Kill `@astrojs/cloudflare` adapter execution plan

**Goal:** Close mandate items 1 & 2. After this ships, `dist/` has
no `_astro/` or `_worker.js/`, and `astro build` runs only on
framework upgrades.

**Blocker:** ~1207 lines of TypeScript SSR endpoints + 676-line
middleware currently bundled by `@astrojs/cloudflare` into the
`dist/_worker.js/` shim. Removing the adapter means we hand-roll a
Cloudflare Worker for the runtime routes.

**Scope:** Everything below is scoped to CreditDoc. Same principles
transfer to TTH later, but that's a separate workstream.

---

## SSR route inventory (audited 2026-07-17)

| Route | LoC | Purpose | Dependencies |
|---|---:|---|---|
| `/go/[slug]` (`src/pages/go/[slug].ts`) | 87 | Affiliate redirect. Looks up lender by slug in Supabase, returns 302 to their affiliate URL with UTM tracking. | `lib/db.ts` `getLenderWithBodyBySlugRuntime`, `utils/outbound.ts` `getLenderDestination`. |
| `/api/email-signup` (`src/pages/api/email-signup.ts`) | 322 | Form submission handler. Writes to Supabase + calls email service. | Supabase runtime client, email service. |
| `/api/origination-intake` (`src/pages/api/origination-intake.ts`) | 358 | Origination form. Writes to Supabase. | Supabase runtime client. |
| `/api/search` (`src/pages/api/search.ts`) | 245 | Search over `lenders` table via PostgREST. | Supabase runtime client. |
| `/api/revalidate` (`src/pages/api/revalidate.ts`) | 182 | Cache invalidation webhook. | Supabase runtime auth. |
| `/api/geo` (`src/pages/api/geo.ts`) | 13 | Trivial CF geo echo (returns `request.cf`). | None. |

Total: **1,207 lines** across 6 files. Everything else in `src/pages/`
is `prerender = true` (or has no directive, defaulting to prerender
under Astro's static output).

**Not SSR (despite past confusion):**
- `linkedin-oauth-callback.astro` has `prerender = true`.
- `search.astro` is a static shell that fetches `/api/search` client-side.
- `feed.xml.ts` and `rss.xml.ts` are prerendered.
- `sitemap.astro` — check but probably prerendered.

## Middleware audit

`src/middleware.ts` (676 lines) does five things:

1. **Legacy redirects** (~250 LoC): `LEGACY_PATH_REDIRECTS`,
   `LEGACY_CATEGORY_REDIRECTS`, `STATE_CODE_REDIRECTS`, city↔state
   normalization, `search?state=` → `/state/[X]/` shortcut. **Move to
   `dist/_redirects` file** — Cloudflare Static Assets natively
   consumes the same format as Netlify. Zero-code migration path.
2. **Security headers** (~50 LoC): CSP, X-Content-Type-Options,
   Referrer-Policy. **Move to `dist/_headers`** (same story) or set
   in the hand-rolled worker.
3. **Cache wrap** (~250 LoC): version-key cache for SSR pages. **DEAD
   CODE after Rock 1** — no more SSR content pages, so nothing to
   wrap.
4. **SERANKING static snapshot serving** (~50 LoC): serves preserved
   snapshots for a shortlist of URLs from `data/seranking_static_snapshot_urls_*.json`.
   **Keep in worker** — this is genuine runtime logic.
5. **Bookkeeping / imports / types** (~76 LoC).

Middleware essentials to preserve: **~50 LoC** (SERANKING snapshot +
security header default). The rest is either data or dead-code post-Rock-1.

---

## Execution phases

### Phase R1.1 — Move redirects to static config (½ day)

Author `dist/_redirects` from `LEGACY_PATH_REDIRECTS`,
`LEGACY_CATEGORY_REDIRECTS`, and the state-code shortcuts. Cloudflare
Static Assets picks it up automatically — no worker code needed.

Test: `curl -sIL https://staging.creditdoc.co/best/best-personal-loans-2024/`
resolves to the new URL via 308.

### Phase R1.2 — Author `worker/index.ts` skeleton (½ day)

New directory `worker/` alongside `renderer/`. Skeleton:

```ts
// worker/index.ts
export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext) {
    const url = new URL(request.url);
    if (url.pathname === '/api/geo') return handleGeo(request);
    if (url.pathname === '/api/search') return handleSearch(request, env);
    if (url.pathname === '/api/email-signup' && request.method === 'POST') return handleEmailSignup(request, env);
    if (url.pathname === '/api/origination-intake' && request.method === 'POST') return handleOriginationIntake(request, env);
    if (url.pathname === '/api/revalidate' && request.method === 'POST') return handleRevalidate(request, env);
    if (url.pathname.startsWith('/go/')) return handleGoRedirect(url, env);
    // Fall through to static assets binding.
    return env.ASSETS.fetch(request);
  }
};
```

Copy each endpoint's body from `src/pages/api/*.ts` and `src/pages/go/[slug].ts`
into corresponding `worker/handlers/*.ts` files. Update `lib/db.ts`
imports to work in a plain worker (should already work — `lib/db.ts`
uses `fetch` for PostgREST, not Astro-specific APIs).

Test: `wrangler dev worker/index.ts` on port 8788; hit each endpoint.

### Phase R1.3 — Wire `wrangler.toml` and swap adapter (½ day)

```toml
name = "creditdoc"
compatibility_date = "2026-04-01"
main = "worker/index.ts"
assets = { directory = "dist", binding = "ASSETS" }
```

Change `astro.config.mjs`:
- Remove `adapter: cloudflare(...)`
- Set `output: 'static'`
- Remove middleware entirely (or reduce to no-op)

Delete `_worker.js/` from dist after next Astro build. Delete `_astro/` too — the renderer output has zero references to `/_astro/*.css`.

The 4 interactive tools (`borrowing-power-quiz`, `credit-score-simulator`, `debt-payoff-calculator`, `loan-denial-reason-checker`) reference `/_astro/*.js`. Options:

a. Preserve just those 4 bundles at stable paths and rewrite the HTML refs
   in a post-strip pass (small extension of `strip_astro_fingerprint.py`).
b. Convert the 4 tools to plain vanilla JS files served from `/tools/*.js`.

Pick (a) first — 1 hour of work vs a day for (b).

Test: `astro build && ls dist/` → confirms no `_worker.js`. `wrangler deploy`
→ site works end-to-end.

### Phase R1.4 — Delete dead code (½ day)

- Delete `src/middleware.ts` (or trim to security-header no-op if any
  static assets rely on the CSP).
- Remove `@astrojs/cloudflare` from `package.json`.
- Update `scripts/check_no_ssr_regression.mjs` — no SSR pages remain
  in `src/pages/`, so the allowlist becomes empty. Or delete the guard
  entirely.
- Update `README`, `AGENT_PROTOCOL.md` mentions of the adapter.

Test: `npm run build` produces `dist/` with only HTML/CSS/assets, no
`_worker.js/` or `_astro/`. Worker still deploys.

## Risk register

| Risk | Prob | Impact | Mitigation |
|---|---|---|---|
| Supabase runtime client (`lib/db.ts`) references Astro globals | Med | High | Audit before phase R1.2. If any exist, refactor to plain fetch. |
| Legacy redirects list is longer than `_redirects` file supports (2000-line limit on CF Pages) | Low | Med | Count entries — likely <500 total. If over, split into multiple `_redirects` files or fall back to worker route table. |
| Middleware cache-wrap semantics were load-bearing for cache freshness | Low | Med | With no SSR pages, static assets get straight Cloudflare cache. The row-version key was solving the SSR cache-invalidation problem which no longer exists. |
| Interactive tool JS bundles have inline references to Astro's hydration runtime | Med | Med | Inspect one bundle. If it imports Astro modules, convert tool to vanilla JS (option b above). |

## Definition of Rock 1 done

- `dist/_worker.js/` does not exist after `wrangler deploy`.
- `dist/_astro/` does not exist (or contains only preserved tool JS with stable names).
- `curl https://www.creditdoc.co/api/geo` returns CF context JSON.
- `curl https://www.creditdoc.co/go/credit-saint` returns 302 to Credit Saint's affiliate URL.
- `curl -sIL https://www.creditdoc.co/best/best-personal-loans-2024/` resolves via `_redirects`.

## After Rock 1

Mandate items 1 & 2 close. Combined with Rock 3 already done, all
three done items = mandate complete. Then:

- Backfill: convert 4 interactive tool bundles to stable-path artifacts.
- Cleanup: delete `src/middleware.ts` if unused, remove `@astrojs/cloudflare`
  from package.json.
- Docs: update `renderer/CREDITDOC_ARCH_REMEDIATION_PLAN_v3.md` marking
  all three rocks done, and archive as historical record.

## Estimated total: 2 days

- R1.1 redirects → static: 0.5d
- R1.2 worker skeleton + endpoint ports: 0.5d
- R1.3 wrangler + adapter swap + tool bundle preservation: 0.5d
- R1.4 dead-code delete + verification: 0.5d
