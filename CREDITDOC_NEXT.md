# CreditDoc — NEXT

## Decisions waiting on Jammi
1. **Push `arch-overhaul` to remote and let Vercel deploy?** Bundle is 192M, smoke-tested, ISR routing wired. Risk: first prod request to a `/review/[slug]` proves whether the bundled better-sqlite3 binary actually loads on Vercel's Node 20 runtime (works locally, but Vercel's lambda env may differ for native modules — they ship the same Linux glibc so should be fine).
2. **Keep Turso as fallback or remove from runtime entirely?** Right now `db.ts` falls back to Turso if the bundled DB is missing. Costs nothing to keep. Recommend keep — defensive.
3. **Phase 5 (slim-DB rebuild before deploy)** — wire into `tools/creditdoc_build.py` or run as separate step? Until done, content edits in `creditdoc.db` will not reach the site until someone manually rebuilds the slim DB and pushes.

## Concrete next actions (in order)
1. **Founder reviews `CREDITDOC_NOW.md`** + this file.
2. **Push to remote:**
   ```bash
   cd /srv/BusinessOps/creditdoc-arch
   git add astro.config.mjs package.json package-lock.json src/utils/db.ts src/utils/data.ts data/creditdoc-slim.db scripts/sync_to_turso.mjs CREDITDOC_NOW.md CREDITDOC_NEXT.md
   git rm -r --cached src/content/lenders   # they're moved out
   git commit -m "Architecture overhaul: SSR + bundled SQLite (192M function bundle)"
   git push origin arch-overhaul
   ```
   Then open PR `arch-overhaul → main` (or push directly to main if Jammi confirms).
3. **Watch Vercel deploy logs** — first build should be ~1-2 min (no more 372s data export). First request to `/review/anywhere` will tell us if better-sqlite3 native loads.
4. **Smoke test in prod** — hit `https://creditdoc.co/review/chase-bank`, `https://creditdoc.co/categories/credit-repair`, `https://creditdoc.co/state/california`. Expect cold-start latency on first hit (~1s), warm <200ms.
5. **Wire Phase 5** — add a `--slim-db` mode to `tools/creditdoc_build.py` that regenerates `creditdoc-arch/data/creditdoc-slim.db` from `creditdoc/data/creditdoc.db`. The SQL is in `data/creditdoc-slim.db.sql` if it was saved (otherwise: `ATTACH ... ; CREATE TABLE ... AS SELECT ...; VACUUM;` — recreatable).

## What NOT to do
- **Do not delete `.archived-content/lenders/`.** Keep until prod is verified green for at least 48h. If something breaks, easy rollback.
- **Do not run `npm install --production`** in the `_isr.func/` bundle. Astro+Vercel handles that.
- **Do not bump astro to v6.** The `@astrojs/vercel` v10 upgrade requires it but breaks other things. Stay on astro@5.17.1 + @astrojs/vercel@9.0.5.
- **Do not put `output: 'hybrid'` back.** Astro 5 removed it. The static + per-route `prerender = false` pattern IS the hybrid replacement.
- **Do not query Turso for >100 rows from a serverless function.** It hits libsql HTTP timeout (~30s undici header timeout) by ~5K rows. Bundled DB is the runtime path.

## Open risk: Phase 5 staleness
Until Phase 5 is wired, the prod slim DB drifts from `creditdoc.db`. Hourly guardian/daily sync run against `creditdoc.db` only. If Jammi adds 50 lender profiles tomorrow, they won't show on creditdoc.co until someone runs the slim DB rebuild. Easy gotcha to forget.

**Suggested guardrail:** add a daily cron at 07:30 UTC (after the existing 07:00 daily sync) that runs:
```bash
cd /srv/BusinessOps/creditdoc-arch && npm run rebuild-slim-db && git commit -am "Daily slim DB refresh" && git push
```
…which triggers a Vercel rebuild automatically.

## How to roll back if prod breaks
```bash
git checkout main
git push origin main --force-with-lease   # ONLY if catastrophic
```
Or just revert the merge commit. Vercel will roll back to the previous build in <2 min.
