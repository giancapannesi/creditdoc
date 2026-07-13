# CreditDoc City Landing Batch 002 - 2026-07-13

## Scope

Batch size: 10 city pages.

Source backlog:
- `reports/local-seo/city_page_enhancement_backlog_2026-07-12.csv`
- `reports/local-seo/city_page_enhancement_backlog_2026-07-12.md`

No crawl-control changes were made. This batch did not change robots, noindex, canonical, redirects, sitemap inclusion, RSS, feeds, or social automation.

## URLs Enhanced

1. https://www.creditdoc.co/city/rock-hill-sc/
2. https://www.creditdoc.co/city/bakersfield-ca/
3. https://www.creditdoc.co/city/bronx-ny/
4. https://www.creditdoc.co/city/santa-clara-ca/
5. https://www.creditdoc.co/city/seattle-wa/
6. https://www.creditdoc.co/city/los-angeles-ca/
7. https://www.creditdoc.co/city/marietta-ga/
8. https://www.creditdoc.co/city/grand-prairie-tx/
9. https://www.creditdoc.co/city/edmond-ok/
10. https://www.creditdoc.co/city/arlington-tx/

## What Changed

- Added Batch 002 entries to `src/content/local-city-landing-enhancements.json`.
- Each city now has a bespoke local action plan, localized tool CTAs, priority internal links, local FAQs, and FAQPage schema through the existing city enhancement component.
- Internal links were checked against built `/browse/` coverage before selection. Cities without matching local browse pages use `/tools/`, `/best/`, and `/state/` links instead of unsupported local category URLs.
- The existing local email capture form remains active globally on city pages.

## Batch Notes

- Rock Hill: emergency-cash path, South Carolina rules, payday alternative support.
- Bakersfield: emergency cash and pawn coverage plus California consumer context.
- Bronx: pawn/collateral, debt payoff, and New York consumer context.
- Santa Clara: tool-first page because local browse coverage is limited.
- Seattle: business loans, banking, credit unions, free-help, and Washington context.
- Los Angeles: broad local hub with credit repair, loans, debt, business, and California context.
- Marietta: pawn/collateral and Georgia consumer context.
- Grand Prairie: pawn/collateral, bad-credit loan research, and Texas context.
- Edmond: tool-first page because local browse coverage is limited.
- Arlington: personal loans, emergency cash, pawn, and Texas context.

## Next Batch

Start with rows 21-30 in `city_page_enhancement_backlog_2026-07-12.csv`:

1. Warren, MI
2. Knoxville, TN
3. Carrollton, TX
4. Dallas, TX
5. Dearborn, MI
6. Sandy Springs, GA
7. Philadelphia, PA
8. Marrero, LA
9. Omaha, NE
10. National City, CA

## Verification Required

Run:

```bash
npm run build
```

Then inspect built pages for:
- `data-city-enhancement-batch="2"`
- Localized quiz/tool labels.
- FAQPage JSON-LD.
- No truncated title/meta descriptions.
- No feed, sitemap, schema, image-alt, or AI-ingestion contract failures.
