# CreditDoc Git Cleanup And Autonomous Engine Stop

Date: 2026-05-25  
Operator: Codex  
Site: `https://www.creditdoc.co`

## Summary

CreditDoc had a dirty git worktree caused mainly by generated lender JSON churn. The immediate visible symptom was hundreds of modified `src/content/lenders/*.json` files, mostly changes to operational metadata such as `last_engine_run`.

The deeper cause was not cron. The cron entry for `creditdoc_autonomous_engine.py` had already been commented out, but the systemd service `creditdoc-engine.service` was still running `/srv/BusinessOps/tools/creditdoc_engine_loop.sh`. That loop was repeatedly launching the autonomous engine and writing metadata into tracked lender JSON files.

The engine is now stopped and deliberately hard-disabled.

## What Was Archived

Before restoring the generated lender JSON changes, the dirty files and diffs were archived here:

`/srv/BusinessOps/CreditDoc Project Improvement/git-cleanup-2026-05-25/`

Archive contents:

- `dirty-lender-json-current-files.tar.gz`
- `dirty-lender-json-files.txt`
- `dirty-lender-json-files.null`
- `lender-json-diff-before-restore.patch`
- `full-worktree-diff-before-lender-json-restore.patch`

The archive preserves the generated state in case any individual JSON change ever needs to be inspected.

## Repo Cleanup Actions

- Archived 577 dirty tracked lender JSON files before cleanup.
- Restored tracked `src/content/lenders/*.json` files because the database is the source of truth.
- Confirmed `src/content/lenders` had zero remaining diffs after the engine was stopped.
- Committed the cleaned repo state:
  - `79f0d3b724 Clean CreditDoc repo state and guard sitemap`
  - `668f9b34a4 Fix sitemap redirect response`
- Pushed branch `cdm-rev-hybrid` to GitHub.

## Engine Stop Actions

Found live engine process:

- `creditdoc-engine.service`
- `/srv/BusinessOps/tools/creditdoc_engine_loop.sh`
- `/srv/BusinessOps/tools/creditdoc_autonomous_engine.py --count 500`

Actions taken:

- `systemctl stop creditdoc-engine.service`
- `systemctl disable creditdoc-engine.service`
- Changed `/etc/systemd/system/creditdoc-engine.service` from `Restart=always` to `Restart=no`.
- Removed stale lock file `/tmp/creditdoc_engine.lock`.
- Added an explicit enable-file guard to `/srv/BusinessOps/tools/creditdoc_engine_loop.sh`.

The loop now exits unless this file exists:

`/srv/BusinessOps/tools/.creditdoc-engine-enabled`

Current verified state:

- `systemctl is-active creditdoc-engine.service` -> `inactive`
- `systemctl is-enabled creditdoc-engine.service` -> `disabled`
- Unit restart policy -> `Restart=no`
- Enable flag -> absent
- No running `creditdoc_engine_loop` or `creditdoc_autonomous_engine.py` process

Do not restart this engine without Jammi approval. If it is ever deliberately re-enabled, first verify it no longer writes operational metadata into tracked lender JSON.

## Code/Build Guard Improvements

Committed supporting cleanup/guard work:

- `scripts/check_robots_contract.mjs`
- `scripts/check_sitemap_robots_conflicts.mjs`
- `package.json` now runs robots contract before build and sitemap/robots conflict check after build.
- `astro.config.mjs` excludes `/search/` from generated XML sitemaps.
- `src/pages/sitemap.xml.ts` redirects `/sitemap.xml` to `/sitemap-index.xml`.
- `scripts/export_cfpb_trends.py` had already been changed so identical CFPB trend exports do not rewrite the file.
- `tools/creditdoc_db.py` and `tools/creditdoc_db_sync.py` had already been changed so `last_engine_run` is excluded from public JSON export/checksum drift.

## Deployment

Deployed through the documented Cloudflare deploy script:

`/srv/BusinessOps/creditdoc/deploy.sh`

Final deploy:

- Cloudflare Worker Version ID: `577d7956-09e0-4f66-84b7-1891f6b4ed2c`
- Deploy completed successfully.
- Cloudflare cache purged.

## Verification

Build verification:

- `npm run build` passed.
- `[robots-contract] OK`
- `[ssr-sitemap-parity] OK`
- `[sitemap-robots] OK`

Live URL checks after final deploy:

- `https://www.creditdoc.co/` -> `200`
- `https://www.creditdoc.co/review/lexington-law/` -> `200`
- `https://www.creditdoc.co/review/sunbit/` -> `200`
- `https://www.creditdoc.co/answers/` -> `200`
- `https://www.creditdoc.co/credit-guide/new-york-ny/credit-cards/` -> `200`
- `https://www.creditdoc.co/sitemap.xml` -> `200`, final URL `https://www.creditdoc.co/sitemap-index.xml`
- `https://www.creditdoc.co/sitemap-index.xml` -> `200`
- `https://www.creditdoc.co/robots.txt` -> `200`

Final git verification:

- CreditDoc repo worktree clean.
- `src/content/lenders` dirty count stayed at `0`.

## Important Operational Note

The cron line was not the only control point. The service was still active independently through systemd. Future cleanup or automation shutdowns must check all three layers:

1. Cron.
2. Systemd services.
3. Long-running shell loops/processes.

For CreditDoc generated lender/profile work, database remains the source of truth. Do not treat generated JSON files as the live editing source.
