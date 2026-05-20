# CreditDoc Cleanup Log — 2026-05-19

CreditDoc is a live business site. All cleanup work below was done with a
non-destructive bias: no deploys, no cron edits, no database sync changes, no
production path moves, and no live site code rewrites were performed as part of
this cleanup pass.

## Repo Security And Hygiene

- Redacted exposed Sendy credential values from:
  - `CREDITDOC_NOW.md`
  - `GLOSSARY.md`
- Expanded `.gitignore` coverage for local/generated artifacts:
  - Python caches
  - local SQLite/database files
  - backup/archive dump files
  - Sendy zip exports
  - Wrangler caches
  - `.secrets/` folders
  - `tmp_*` scratch files
- Committed the first hygiene/security pass:
  - `32348f2dbb chore: secure CreditDoc repo hygiene docs`
- Committed the follow-up local secret/temp ignore pass:
  - `d08948b4d8 chore: ignore local secret and temp artifacts`
- Committed this cleanup log and the CreditDoc agent entrypoint:
  - `fe783f36cd docs: record CreditDoc cleanup handoff`
- Committed reviewed AI Council, strategy, SEO, and targeting documentation:
  - `57499eeefb docs: add CreditDoc strategy research`
- Committed ignore rules for bulky local research/import bundles and generated
  analysis outputs:
  - `0f90c68a91 chore: ignore local research outputs`
- Committed remaining reviewable buckets after `npm run build` passed:
  - `a037a06383 docs: update CreditDoc operating plans`
  - `4eabbbac47 feat: add resource templates and credit course`
  - `f96c723639 feat: add regulatory data layer tooling`
  - `3cf08ebe44 feat: preserve Cloudflare runtime migration`
  - `d48d93b322 feat: split credit guide category routes`
  - `5f798e7007 docs: add revalidate cron proposal`
  - `02ce8835d4 feat: polish CreditDoc page surfaces`

## Lender JSON Archive

- Created a copy-only archive of active lender JSON files:
  - `/srv/BusinessOps/_archive/creditdoc/lender-json-2026-05-19.tar.gz`
- Created an archive manifest:
  - `/srv/BusinessOps/_archive/creditdoc/lender-json-2026-05-19.MANIFEST.md`
- Archive SHA256:
  - `7931dfbf4a369b9f6411aa2f4f0d0555d7fe901f00fc2cf16831aa497ff01b1b`
- Active top-level lender JSON count at archive time:
  - `20,813`
- Recursive archive JSON count:
  - `20,814`, including `lenders/_removed/blue-mountain.json`
- No active lender files were moved or deleted.

## Lender JSON Churn Cleanup

- Classified dirty lender JSON changes.
- Found that most changes were generated `last_engine_run` timestamp churn.
- Saved a reversible pre-cleanup patch:
  - `/srv/BusinessOps/_archive/creditdoc/lender-json-dirty-diff-before-timestamp-cleanup-2026-05-19.patch`
- Patch SHA256:
  - `580ddbd4426d294b765180be83d7bf43f2798625129544dca4bd2aa05e8f6d51`
- Restored timestamp-only lender JSON churn after verifying it was not real
  content.

## CreditDoc Engine Pause

- Discovered `creditdoc-engine.service` was actively re-dirtying tracked lender
  JSON files by running:
  - `/srv/BusinessOps/tools/creditdoc_engine_loop.sh`
  - `/srv/BusinessOps/tools/creditdoc_autonomous_engine.py --count 500`
- User approved stopping the service because it was not doing useful work and
  was creating repo churn.
- Stopped the service with:
  - `systemctl stop creditdoc-engine.service`
- Verification after stop:
  - service was `inactive`
  - no `creditdoc_autonomous_engine` or `creditdoc_engine_loop` processes
    remained
  - lender JSON dirty count returned `0`
- The service was later disabled at user request so it remains stopped across
  reboot:
  - `systemctl disable creditdoc-engine.service`
- Final verification:
  - `systemctl is-active creditdoc-engine.service` returned `inactive`
  - `systemctl is-enabled creditdoc-engine.service` returned `disabled`
  - lender JSON dirty count remained `0`

## Engine Assessment

- The engine appeared to be producing repo churn rather than useful profile
  upgrades during this cleanup window.
- Logs showed repeated checks and website-unreachable outcomes, followed by
  `last_engine_run` updates in tracked lender JSON files.
- User noted the engine had likely run out of useful profiles to process.
- Current decision: keep `creditdoc-engine.service` stopped and disabled for
  now. Do not restart it without explicit user approval and a revised plan for
  where runtime state should be written.

## Current Caveats

- The repo was left with no visible unstaged or untracked files.
- Strategy docs, AI Council notes, and SEO research docs were reviewed for
  obvious credential leakage and committed as documentation.
- Bulky local research/import folders and generated analysis outputs were not
  moved or deleted; they were ignored so they stop obscuring reviewable source
  changes.
- Live-site code changes were committed only after `npm run build` completed
  successfully. No deploy was run during this cleanup continuation.
- The database remains the source of truth for live lender pages, but lender
  JSON files are still operationally sensitive because tooling can read or sync
  them.
