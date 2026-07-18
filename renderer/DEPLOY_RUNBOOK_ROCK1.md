# Rock 1 Production Deploy Runbook

**Change:** Kill `@astrojs/cloudflare` adapter → hand-rolled Cloudflare Worker.

**Risk profile:** HIGH. This is the first production deploy that shifts
CreditDoc's runtime off Astro's SSR adapter onto a from-scratch 250-line
worker. Everything that was hitting `dist/_worker.js/index.js` (Astro's
compiled SSR bundle) now hits `worker/index.ts`.

**Change scope:** commits `3b2f243493..bcfe2b9af9` on `cdm-rev-hybrid`.

## Pre-deploy state (2026-07-18)

- `wrangler.toml` main: `./worker/index.ts` (was `./dist/_worker.js/index.js`)
- `package.json` build: `python3 renderer/build_all.py` (was `astro build`)
- `astro.config.mjs` renamed to `.DISABLED_2026-07-17`
- Local `dist/` contents:
  - 26,961 HTML files
  - 68,432 total files (from wrangler read count)
  - `_worker.js/` purged (1.8 MB gone)
  - `_astro/` retains 15 files (interactive tool JS, CSS, Inter fonts)
- Worker bundle: 52.85 KiB (gzip 12.81 KiB)
- All 6 SSR handlers ported (/api/geo, /api/search, /api/email-signup,
  /api/origination-intake, /api/revalidate, /go/[slug])
- Pre-deploy audit: 8/8 PASS (agent `ac74908f54dbdd410`)

## Backup

**Astro rollback dist:** `dist.trashed_r1_1784269927/` (2.7 GB, Jul 16 20:59 UTC)
→ if renderer output causes prod issues, `mv dist dist.rock1_failed && cp -r dist.trashed_r1_1784269927 dist` restores the Jul 16 Astro build.

**Pre-deploy dist snapshot:** created just before deploy at
`dist.pre_rock1_deploy_<epoch>/` — captures exactly what we shipped so
we can diff post-deploy state.

**Code rollback:** all commits already pushed to `cdm-rev-hybrid` branch.
`git revert dad12eb0a8` reverses R1.3 wrangler.toml + package.json swap.

**Cloudflare rollback:** CF dashboard → Workers → creditdoc → Deployments
→ "Rollback to previous deployment" (single click, ~30s to propagate).

## Deploy procedure

```bash
cd /srv/BusinessOps/creditdoc
./deploy.sh
```

Under the hood, `deploy.sh` runs:

1. `python3 scripts/export_cfpb_trends.py` (best-effort CFPB data refresh)
2. `npm run build` = `python3 renderer/build_all.py` (~5-20 min depending on scope)
3. Sanity check: dist/ must have ≥10,000 HTML files
4. `wrangler deploy` with `CLOUDFLARE_EMAIL` + `CLOUDFLARE_API_KEY` env
   (Global API Key path per lies_caught #2; API TOKEN unset to avoid conflict)
5. Targeted Cloudflare cache purge (17 warm-up URLs — not full zone)
6. Post-deploy smoke tests on 11 SSR URLs — abort with exit code 1 if any 200-check fails

## Smoke tests (embedded in deploy.sh)

The script auto-verifies these 11 URLs:

- `/` (homepage + first CSS ref)
- `/review/lexington-law/`
- `/state/wyoming/`
- `/credit-guide/austin-tx/`
- `/credit-guide/austin-tx/credit-repair/`
- `/answers/`
- `/answers/best-debt-consolidation-loans-bad-credit/`
- `/best/best-credit-repair-companies/`
- `/categories/credit-repair/`
- `/blog/how-to-get-a-personal-loan-with-bad-credit-in-2026/`
- `/financial-wellness/credit-score-basics/`
- `/brand/advance-america/`

## Extended smoke tests (manual, post-deploy)

Beyond deploy.sh's built-in checks, verify the 6 dynamic endpoints
(new hand-rolled worker code — first time in prod):

```bash
# 1. /api/geo — CF geo header echo
curl -s https://www.creditdoc.co/api/geo | jq

# 2. /go/[slug] — affiliate redirect (should 302)
curl -sI "https://www.creditdoc.co/go/credit-saint" | head -10

# 3. /api/search — PostgREST search (should return count + results)
curl -s "https://www.creditdoc.co/api/search?q=credit+saint&limit=5" | jq '.count'

# 4. /api/revalidate — auth-guarded (should 401 without token)
curl -sI -X POST https://www.creditdoc.co/api/revalidate

# 5. /api/email-signup — CSRF-guarded (should 403 no origin)
curl -sI -X POST https://www.creditdoc.co/api/email-signup

# 6. /api/origination-intake — CSRF-guarded (should 403 no origin)
curl -sI -X POST https://www.creditdoc.co/api/origination-intake

# Additional: redirect logic (moved from middleware to _redirects)
curl -sI "https://www.creditdoc.co/state/ca/" | head -3   # → 301 /state/california/
curl -sI "https://www.creditdoc.co/categories/fix-my-credit/" | head -3  # → 301 /categories/credit-repair/
```

## Rollback procedure

**Fast (Cloudflare-side):**
1. CF dashboard → Workers & Pages → creditdoc → Deployments
2. Click previous deployment → "Rollback to this deployment"
3. Propagation ~30 seconds

**Full (local + Cloudflare):**
```bash
cd /srv/BusinessOps/creditdoc

# 1. Restore prior git state
git revert dad12eb0a8 bcfe2b9af9   # R1.3 wrangler swap + closeout doc

# 2. Restore prior dist output (Astro Jul 16)
mv dist dist.rock1_failed
cp -r dist.trashed_r1_1784269927 dist

# 3. Restore prior astro.config.mjs
mv astro.config.mjs.DISABLED_2026-07-17 astro.config.mjs

# 4. Redeploy the Astro-era worker
./deploy.sh
```

## Post-deploy tasks

- [ ] Monitor Cloudflare Analytics for 5xx spike (first 10 min post-deploy)
- [ ] Run additional smoke tests above (6 endpoints + redirects)
- [ ] Update `renderer/CREDITDOC_ARCH_REMEDIATION_PLAN_v3.md` to mark
      Rocks 1/2/3 DEPLOYED
- [ ] Commit the 8 pending lender JSON updates in `src/content/lenders/`
      (enrichment metadata churn, unrelated to Rock 1 but stale)
- [ ] Update memory at `project_creditdoc_renderer_migration.md` with
      deployed-at timestamp

## What could go wrong (contingencies)

| Failure | Symptom | Response |
|---|---|---|
| Worker throws in module init | wrangler deploy succeeds, all requests → 1101 error | CF dashboard rollback |
| /api/search 500s | `curl /api/search?q=X` returns 500 | Check SUPABASE_URL/SUPABASE_ANON_KEY are Worker secrets, not just env |
| /go/[slug] redirects to wrong URL | 302 targets appear malformed | Check body_inline JSON parsing in `worker/handlers/go.ts` |
| Static assets miss | Any /review/ /best/ URL 404s | dist/ upload was incomplete — re-run `./deploy.sh` |
| Interactive tools broken | /tools/borrowing-power-quiz/ shows empty results | `_astro/` bundle mismatch — restore Jul 16 backup |
| Redirects don't fire | `/state/ca/` returns 404 instead of 301 | Verify dist/_redirects has the 50 new state-code lines (public/_redirects committed at `80abb83f12`) |

## Deploy window

Choose off-peak (US low traffic, EU-CAT sleeping): 02:00-06:00 UTC ideal.
Not a hard constraint — mandate says continuous deploy latency ≤90s so
even during traffic peak the blast radius is bounded.
