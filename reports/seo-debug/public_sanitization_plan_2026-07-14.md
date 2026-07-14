# CreditDoc Public Sanitization Plan - 2026-07-14

Goal: make CreditDoc's important public pages feel like independent, useful landing pages instead of machine/template output, while preserving indexability, feeds, sitemaps, canonicals, robots, and publishing.

## Guardrails

- Do not bulk noindex, remove, redirect, canonical-change, robots-block, sitemap-remove, feed-stop, or route-suppress pages without explicit approval.
- Do not pause publishing, LinkedIn, Pinterest, IndexNow, GSC queue, or feed crons as part of sanitation work.
- Work in batches, beginning with pages that already have GSC signal or commercial intent.
- Every batch must run build/debug checks before commit.

## Priority Order

1. Top local pages already seen by Google:
   - First 40 `/city/` and `/browse/` URLs from `reports/local-seo/local_pages_with_gsc_impressions_2026-07-12.csv`.
   - These include Long Beach, West New York, Vernon, Pittsburgh, New Orleans, San Jose, Madison, Decatur, College Park, Midwest City, Rock Hill, Bakersfield, Bronx, Santa Clara, Seattle, Los Angeles, Marietta, Grand Prairie, Edmond, Arlington, Warren, Knoxville, Carrollton, Dallas, Dearborn, Sandy Springs, Philadelphia, Marrero, Omaha, National City, Norfolk, Miami, Oakland, Chula Vista, Highland Park, Opa Locka, Goodlettsville, San Ysidro, New York, and Jefferson.
2. Commercial tool and money pages:
   - `/tools/`, `/best/`, calculators, quizzes, answer pages tied to SBA, business lines of credit, commercial loans, merchant cash advance, debt payoff, credit repair, and credit score questions.
3. Trust and regulatory moat:
   - `/state/`, `/state/*/lending-laws/`, `/research/`, `/resources/`, regulatory directory, CFPB/complaint assets.
4. Remaining local/static pages:
   - Batch city and browse pages in groups of 10, prioritizing pages with impressions, strong local inventory, or useful regulatory capture opportunities.
5. Runtime/review surfaces:
   - Remove public debug headers and pilot wording first; later decide whether selected review/category pages should receive static snapshot treatment.

## Phase 1 - Implemented Today

- Removed public `x-cdm-*` debug/cache headers from public runtime paths and middleware/cache wrapper.
- Removed visible `/r/` SSR pilot and architecture wording.
- Removed internal city-page labels:
  - `Batch {n} priority #{n} local landing page`
  - `Current GSC signal`
  - `data-city-enhancement-batch`
- Added Cloudflare adapter static bypasses for prerendered priority route families:
  - `/best`, `/city`, `/browse`, `/state`, `/research`, `/resources`
  - Existing bypasses already covered `/answers`, `/blog`, `/tools`, `/financial-wellness`, `/courses`.
- Added `scripts/check_public_sanitization_contract.mjs`.
- Added `npm run check:public-sanitization`.

## Daily Cron

The daily cron should run after normal build/content jobs have had time to update the static output. It audits and alerts; it does not rewrite pages automatically.

Reason: auto-rewriting SEO pages in bulk is risky. The safe daily job is to detect and report public fingerprints immediately, then batch-fix intentionally.

Expected cron:

```cron
40 18 * * * cd /srv/BusinessOps/creditdoc && /srv/BusinessOps/.venv/bin/python3 /srv/BusinessOps/tools/cron_alert.py "creditdoc-public-sanitization-contract" /usr/bin/node scripts/check_public_sanitization_contract.mjs >> /srv/BusinessOps/logs/creditdoc_public_sanitization_contract.log 2>&1
```

## Batch Work Definition

Each sanitation batch should:

- Pick 10 priority URLs from the GSC/local backlog or commercial tool/money list.
- Confirm the current built HTML exists at `dist/<route>/index.html`.
- Remove visible operational language, duplicated section rhythm, generic CTAs, and repeated card patterns where possible.
- Add or improve local/commercial usefulness:
  - localized quiz/tool labels;
  - state regulator/contact context;
  - city-specific FAQ;
  - specific next action;
  - relevant internal links to tools, answers, best pages, state pages, and resources.
- Run:
  - `npm run build`
  - `npm run check:public-sanitization`
  - focused rendered HTML checks for edited URLs.

## Current Verification

- `npm run build` passed on 2026-07-14.
- Postbuild sitemap, `/best/`, feed, image, and AI-ingestion contracts passed.
- `npm run check:public-sanitization` passed after rebuild:
  - 53 priority static pages checked.
  - zero public `x-cdm-*`, `SSR pilot`, `Architecture:`, batch/priority, GSC signal, city-enhancement data marker, or machine-generated wording matches.
