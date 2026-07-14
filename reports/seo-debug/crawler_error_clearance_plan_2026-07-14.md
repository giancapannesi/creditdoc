# CreditDoc Crawler Error Clearance Plan - 2026-07-14

## Objective

Stop crawler-facing 404/5xx regressions from reaching Google, Bing, SE Ranking,
or validation workflows. Every exported error URL should be one of:

- a real static HTML page,
- a deliberate 301 to the best equivalent page,
- or, only with explicit approval, a removal/noindex/410 decision for genuinely
  harmful pages.

Do not bulk noindex, remove, robots-block, sitemap-remove, canonical-change, or
pause publishing as part of this cleanup without explicit approval.

## Current evidence

Current exports checked:

- `SEO/Table 404 Missing Pages.csv`: 1,000 rows.
- `SEO/Table - Duplicates.csv`: 71 rows.

Current local guard result:

- 1,071 exported URL rows checked.
- 77 resolve to static HTML.
- 994 resolve through explicit redirects.
- 0 unresolved exported crawler URLs.

The 71 duplicate-validation failure was not because the current rendered review
pages still share duplicate titles/metas. The pages that exist in the current
build have unique titles, meta descriptions, H1s, and canonicals. The batch also
contained stale city slug variants such as `/city/sugar-land-texas/`, which are
now covered by redirects to the current abbreviation slugs such as
`/city/sugar-land-tx/`.

## Workstream A - Stop known exported errors

Status: implemented.

- Add/maintain explicit redirects for stale city long-state slugs.
- Add/maintain explicit redirects for stale/quarantined review slugs.
- Keep review/state pages static where valid.
- Run `node scripts/check_crawler_error_exports.mjs` after every new crawler
  export is dropped into `SEO/`.

## Workstream B - Prevent regressions

Status: implemented for current exports.

- `scripts/check_crawler_error_exports.mjs` reads the current 404 and duplicate
  CSVs and fails unless each URL has a static HTML file or redirect.
- The check is wired into `postbuild`.
- `scripts/check_static_html_contract.mjs` remains in `postbuild` to protect
  high-value static route families.

## Workstream C - Continue static conversion by risk

Priority order:

1. Route families already appearing in crawler errors: `/review/`, `/city/`,
   `/browse/`, `/compare/`, `/categories/`.
2. Commercial and trust pages: `/tools/`, `/best/`, `/answers/`,
   `/financial-wellness/`, `/courses/`, `/state/`, `/research/`.
3. Remaining runtime/hybrid families: `/credit-guide/`, `/brand/`, `/search/`
   where static output is appropriate.

## Workstream D - Weekly validation loop

Every new GSC/Bing/SE export:

1. Save the raw export in `SEO/` with the source/date in the filename.
2. Run the crawler export contract.
3. Classify unresolved rows by route family.
4. Fix stale equivalents with 301s.
5. Convert valid recurring runtime URLs to static HTML.
6. Only request Google/Bing validation after the guard passes.
7. Track pass/fail and route-family counts in `CREDITDOC_NOW.md`.

## Validation command

```bash
cd /srv/BusinessOps/creditdoc
node scripts/check_crawler_error_exports.mjs
node scripts/check_static_html_contract.mjs
```
