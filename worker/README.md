# CreditDoc Worker — Hand-rolled Cloudflare Worker

Replaces the `@astrojs/cloudflare` adapter's `dist/_worker.js/` shim. Once
`astro.config.mjs` sets `output: 'static'` and `wrangler.toml` points
`main = "worker/index.ts"`, the Astro build stops emitting an SSR runtime
and this file is the entire dynamic surface.

## Layout

```
worker/
├── index.ts              # Router — path-matches, delegates to handlers
├── handlers/
│   ├── geo.ts            # /api/geo — CF geo header echo
│   ├── go.ts             # /go/[slug] — affiliate redirect
│   ├── search.ts         # /api/search — PostgREST search      [pending]
│   ├── email-signup.ts   # /api/email-signup POST              [pending]
│   ├── origination.ts    # /api/origination-intake POST        [pending]
│   └── revalidate.ts     # /api/revalidate POST                [pending]
└── README.md
```

## Port checklist (Rock 1 Phase R1.2)

- [x] `worker/index.ts` router skeleton — 4 endpoints return 501 stub
- [x] `worker/handlers/geo.ts` (13 → 15 LoC, byte-equivalent behavior)
- [x] `worker/handlers/go.ts` (87 → 78 LoC, path parsed from URL rather than Astro `ctx.params`)
- [ ] `worker/handlers/search.ts` (port from `src/pages/api/search.ts` 245 LoC)
- [ ] `worker/handlers/email-signup.ts` (port from `src/pages/api/email-signup.ts` 322 LoC)
- [ ] `worker/handlers/origination.ts` (port from `src/pages/api/origination-intake.ts` 358 LoC)
- [ ] `worker/handlers/revalidate.ts` (port from `src/pages/api/revalidate.ts` 182 LoC)

## Env vars (set as Cloudflare Worker secrets)

- `SUPABASE_URL` — https://pndpnjjkhknmutlmlwsk.supabase.co
- `SUPABASE_ANON_KEY` — RLS-protected anon JWT
- `SUPABASE_SERVICE_ROLE_KEY` — needed only for `/api/revalidate`; other endpoints use anon
- `REVALIDATE_SECRET` — HMAC secret for revalidate endpoint
- `EMAIL_SIGNUP_WEBHOOK` — outbound email service URL

## Local dev

```bash
npx wrangler dev worker/index.ts --assets dist
# → http://localhost:8788
curl http://localhost:8788/api/geo
curl -sI http://localhost:8788/go/credit-saint
```

## Deploy

Not deployable yet — the wrangler.toml swap in Phase R1.3 will point
`main` here.  Currently `wrangler deploy` builds Astro's adapter output.
The parallel worker structure lets us iterate + test without breaking prod.

Once R1.2b completes all 6 handlers, the R1.3 swap is a wrangler.toml edit
+ astro.config.mjs edit + wrangler deploy.

## Dependencies

Imports from `../src/lib/db.ts` (Supabase runtime data layer, worker-safe)
and `../src/utils/outbound.ts` (affiliate URL selection). These modules
have no Astro-specific dependencies per their own headers.

TypeScript compilation: uses root `tsconfig.json`. Wrangler's esbuild
bundles imports at deploy time — no separate build step needed.
