# CreditDoc Local Lead Capture Plan - 2026-07-12

## Scope

CreditDoc local pages are treated as strategic traffic assets. This plan does not change indexability, sitemap inclusion, robots, canonical, redirects, feeds, or publishing behavior.

## Published Local Inventory

Generated inventory:
- `reports/local-seo/published_city_pages_2026-07-12.csv`
- `reports/local-seo/live_local_page_inventory_2026-07-12.csv`
- `reports/local-seo/local_pages_with_gsc_impressions_2026-07-12.csv`

Counts from built HTML:
- `/city/` pages: 331
- `/browse/<category>/<city>/` service-city pages: 467
- Total local pages inventoried: 798
- Embedded forms currently present: 0
- Borrowing Power Quiz links currently present: 798

Current conclusion:
- Local pages already send users to a quiz, but they do not directly capture email/contact intent on-page.
- Every meaningful local page should have a contextual, non-gated capture path because each page is a possible first client touch.

## GSC Evidence

From `Traffic Analysis/Pages.csv` covering 2026-05-20 to 2026-06-19:
- 73 local pages matched GSC impressions.
- Top matched local pages include:
  - `/browse/pawn-shops/san-diego-ca/` - 95 impressions
  - `/browse/pawn-shops/denver-co/` - 51 impressions
  - `/browse/pawn-shops/phoenix-az/` - 45 impressions
  - `/city/long-beach-ca/` - 42 impressions, avg position 4.29
  - `/city/west-new-york-nj/` - 40 impressions, avg position 4.93
  - `/city/vernon-ca/` - 32 impressions, avg position 7
  - `/city/pittsburgh-pa/` - 27 impressions, avg position 5.7
  - `/city/new-orleans-la/` - 26 impressions, avg position 8.04

These pages are not a problem to suppress. They are the local pages already showing demand.

## SERP Sample

Live sample checks on 2026-07-12 showed local/service pages competing against:
- Local pawn shops and multi-location pawn operators for `pawn shops San Diego CA`.
- Local pawn/shop directory pages for San Diego pawn terms.
- Credit-repair service pages, BBB local category pages, and local firm pages for `credit repair Long Beach CA`.
- BBB/local credit-repair profiles and New Jersey credit repair providers for `credit repair West New York NJ`.

Implication:
- Competitors are capturing visitors with phone/contact forms, consultation CTAs, store pages, and local service pages.
- CreditDoc should keep the educational trust layer but add a capture path on the page, not force every user to click through to a separate quiz first.

## Capture Architecture

Use existing infrastructure:
- `/api/email-signup`
- `/api/origination-intake`
- Supabase `lead_captures`
- Sendy response/nurture path

Do not create a parallel lead system.

Add a reusable local capture component with:
- email
- optional first name
- city
- state
- category/page intent
- source URL
- route family
- CTA variant
- consent timestamp

No SSN, bank login, hard-credit language, or underwriting/prequalification claim.

## CTA Mapping

City root pages:
- Primary: "Send me the local credit checklist"
- Secondary: Borrowing Power Quiz link
- Lead intent: `local-finance`

Credit repair local/category pages:
- Primary: "Get the credit report checklist"
- Secondary: Credit Repair Qualify Quiz
- Lead intent: `credit-repair`

Business loan / SBA / commercial local pages:
- Primary: "Get the business funding prep checklist"
- Secondary: Business Loan Readiness Quiz
- Lead intent: `business-loans`

Personal loan / emergency cash pages:
- Primary: "Send me safer borrowing steps"
- Secondary: Borrowing Power Quiz
- Lead intent: `personal-loans`

Debt relief pages:
- Primary: "Get the debt payoff checklist"
- Secondary: debt education / calculator route
- Lead intent: `debt-relief`

Banking / credit union pages:
- Primary: "Send me the account comparison checklist"
- Secondary: credit-building education
- Lead intent: `banking`

Pawn / check-cashing pages:
- Primary: "Send me safer short-term cash options"
- Secondary: emergency borrowing education
- Lead intent: `emergency-cash`

## Rollout Order

1. Start with the 73 local pages already showing GSC impressions.
2. Prioritize the top 20 by impressions and positions already near page 1 or page 2.
3. Add the capture component to `/browse/<category>/<city>/` first because these pages express the clearest commercial intent.
4. Add the capture component to `/city/[slug]` second.
5. Add the capture component to `/credit-guide/[slug]/` after confirming the same API wrapper handles route family/source metadata cleanly.
6. Do not touch `/credit-guide/[slug]/[category]/` indexability as part of this work. Any indexing-policy correction requires separate approval.

## Tracking

Add client-side events:
- `local_lead_capture_view`
- `local_lead_capture_submit`
- `local_lead_capture_success`
- `local_lead_capture_error`

Report weekly:
- capture views by route family
- submissions by route family
- success rate
- top city/category lead sources
- GSC impressions and clicks for the same URLs

## Acceptance Tests

Before deploy:
- `npm run build`
- verify no SEO-control changes in diff
- local static sample checks for `/city/long-beach-ca/` and `/browse/pawn-shops/san-diego-ca/`
- API validation against `/api/email-signup` with test email and cleanup

After deploy:
- live form submit test
- confirm Sendy record or API confirmation
- confirm Supabase `lead_captures`
- confirm no content is gated
- confirm pages still return 200 and no new noindex/canonical/robots changes
