# CreditDoc City Landing Batch 001 - 2026-07-12

## Scope

Batch size: 10 city pages.

Source backlog:
- `reports/local-seo/city_page_enhancement_backlog_2026-07-12.csv`
- `reports/local-seo/city_page_enhancement_backlog_2026-07-12.md`

No crawl-control changes were made. This batch did not change robots, noindex, canonical, redirects, sitemap inclusion, RSS, feeds, or social automation.

## URLs Enhanced

1. https://www.creditdoc.co/city/long-beach-ca/
2. https://www.creditdoc.co/city/west-new-york-nj/
3. https://www.creditdoc.co/city/vernon-ca/
4. https://www.creditdoc.co/city/pittsburgh-pa/
5. https://www.creditdoc.co/city/new-orleans-la/
6. https://www.creditdoc.co/city/san-jose-ca/
7. https://www.creditdoc.co/city/madison-tn/
8. https://www.creditdoc.co/city/decatur-ga/
9. https://www.creditdoc.co/city/college-park-ga/
10. https://www.creditdoc.co/city/midwest-city-ok/

## What Changed

- Added `src/content/local-city-landing-enhancements.json` with city-specific landing-page strategy, action plans, tool links, priority internal links, and local FAQs for the first 10 priority cities.
- Added `src/components/CityLandingEnhancement.astro` to render those city-specific modules without hand-editing each generated page.
- Updated `src/pages/city/[slug].astro` to render the enhancement module when a city has batch data.
- Added FAQPage structured data for enhanced city pages.
- Kept the existing global local lead-capture form active on all city pages.

## Batch Pattern

Each city batch should add:
- City-specific intent and GSC context.
- Local action plan.
- Localized tool links, such as credit repair quiz, credit calculator, borrowing quiz, debt payoff, business calculators, or denial checker.
- Priority internal links into matching `/browse/`, `/tools/`, `/best/`, and `/state/` pages.
- Local FAQs and FAQPage schema.
- Build/debug verification before commit.

## Next Batch

Start with rows 11-20 in `city_page_enhancement_backlog_2026-07-12.csv`:

1. Rock Hill, SC
2. Bakersfield, CA
3. Bronx, NY
4. Santa Clara, CA
5. Seattle, WA
6. Los Angeles, CA
7. Marietta, GA
8. Grand Prairie, TX
9. Edmond, OK
10. Arlington, TX

## Verification Required

Run:

```bash
npm run build
```

Then inspect built pages for:
- `data-city-enhancement-batch="1"`
- Localized quiz/tool labels.
- FAQPage JSON-LD.
- No truncated title/meta descriptions.
- No feed, sitemap, schema, image-alt, or AI-ingestion contract failures.
