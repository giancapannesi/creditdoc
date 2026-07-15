# CreditDoc Geo Architecture Resolution Plan — 2026-07-15

## Evidence Being Used

- Source strategy: `/srv/BusinessOps/CreditDoc_SEO/creditdoc-city-page-targeting-strategy.md`.
- Source architecture plan: `/srv/BusinessOps/CreditDoc_SEO/creditdoc-architecture-find-fix-plan v2.md`.
- Sitemap size observed in the strategy: 19,078 URLs.
- Authority constraint: Domain Trust 15, 3 referring domains, 4 backlinks.
- Indexation estimate: about 7.8K indexed URLs, roughly 41% of sitemap.
- Local visibility gap: 322 of 331 `/city/` pages rank for nothing.
- Current traffic source: `/review/` pages ranking mostly for third-party brand queries.
- City pages are not assumed thin. The strategy verified `/city/denver-co/` as a deep page with strong structure, provider listings, links, and schema.

## Architecture Problem

CreditDoc has three geo route families that can overlap:

1. `/city/{city}/`
   - Should be the local hub.
   - Primary intent: `loan companies in {city}`, `{city} credit repair companies`, `financial services {city}`.

2. `/browse/{category}/{city}/`
   - Should be the city-category money page.
   - Primary intent: `personal loans {city}`, `business loans {city}`, `credit repair {city}` where keyword data supports it.

3. `/credit-guide/{city}/{category}/`
   - Currently `noindex, follow` and omitted from sitemap.
   - Not directly competing in the Google index, but still creates internal-link and crawler noise if site links point there instead of the chosen `/browse/` destination.

The fix is not bulk noindexing city pages. The fix is one query, one preferred URL, with internal links and sitemaps supporting that choice.

## Routing Rules

- Keep `/city/{city}/` indexable as the hub.
- Keep `/browse/{category}/{city}/` indexable when it is the best category-city landing page.
- Keep `/credit-guide/{city}/` as supporting local guide content where it has unique value.
- Stop linking internally to `/credit-guide/{city}/{category}/` as a money destination.
- Consolidate `/credit-guide/{city}/{category}/` category intent into `/browse/{category}/{city}/` only where the matching `/browse/` page exists and is valid.
- If no valid `/browse/` equivalent exists, route category-intent links to the city hub rather than creating another crawlable duplicate.
- Do not bulk noindex, delete, robots-block, or redirect valid pages without explicit approval and a rollback path.

## Keyword Targeting Rules

- Do not geo-target credit cards. Evidence: `credit cards dallas` has zero useful city demand.
- Prioritize:
  - `loan companies in {city}`
  - `personal loans {city}`
  - `{city} credit repair`
  - `business loans {city}` only for Tier A metros where volume/CPC justify it.
- Use city/state word order from keyword evidence, for example `Dallas credit repair` where that beats `credit repair Dallas`.

## Execution Phases

### Phase 1 — Safety And Measurement

- Add every GSC/Bing/SE crawler export to the crawler-error guard.
- Current new input found: `/srv/BusinessOps/CreditDoc_SEO/gsc_reports/creditdoc.co-Coverage-Drilldown-2026-07-14 - Table.csv`.
- Require each exported URL to be either:
  - a valid static HTML page,
  - a valid explicit 301/302 redirect target,
  - or intentionally absent from sitemap with an approved reason.
- Keep sitemap exclusions aligned with crawler exports.
- Produce a repeatable report showing unresolved, static, redirected, sitemap leaks, and bad redirect targets.

### Phase 2 — Geo Template Inventory

- Build a route inventory for:
  - `/city/`
  - `/browse/`
  - `/credit-guide/`
  - `/state/`
  - `/review/`
- For each geo URL, record:
  - status in `dist`,
  - sitemap inclusion,
  - robots/noindex state,
  - canonical,
  - incoming internal links,
  - GSC impressions/clicks if available,
  - SE/Bing/GSC error membership.
- Flag collisions where more than one URL targets the same city/category query.

### Phase 3 — Internal Link Consolidation

- Review pages are the current equity source, so route their local links into the chosen local architecture:
  - profile -> city hub,
  - profile -> relevant `/browse/{category}/{city}/` where available,
  - profile -> state lending-law page when useful.
- Replace internal links from `/credit-guide/{city}/` to `/credit-guide/{city}/{category}/` with preferred `/browse/{category}/{city}/` links where the browse page exists.
- Where a browse page does not exist, link to `/city/{city}/` or the relevant `/categories/{category}/` page.
- Add a checker so priority internal links do not point at noindex category-guide URLs.

### Phase 4 — Controlled Consolidation

- For `/credit-guide/{city}/{category}/` pages with valid `/browse/` equivalents:
  - prefer 301 to `/browse/{category}/{city}/` or canonical/noindex depending on existing GSC signals.
  - Do not redirect if the guide page has unique indexed value until GSC/SE data confirms the safer target.
- Keep `/credit-guide/{city}/` roots if they provide distinct local educational value.
- Validate with build, static-link checker, crawler-export guard, and sitemap/schema contracts.

### Phase 5 — City Tier Rollout

- Tier A: 40–60 major metros.
  - Target loan companies, personal loans, credit repair, and business loans where keyword volume supports it.
  - Add strongest internal links and unique local data blocks.
- Tier B: mid cities.
  - Target personal loans and loan companies first.
- Tier C:
  - Monitor indexation and impressions before investing heavy page work.
  - Do not suppress by default.

### Phase 6 — Authority Layer

- Use the current `/review/` visibility to build internal equity.
- Use CFPB complaint data and 16K profiles for external link acquisition:
  - data PR,
  - provider profile badges,
  - state/nonprofit resource outreach.
- Track referring domains and page-level links to Tier A city/browse pages.

## Validation Gates

Before asking Google/Bing to validate:

- `node scripts/check_crawler_error_exports.mjs` must pass.
- `npm run postbuild` must pass after a build.
- No exported crawler-error URL may appear in sitemap XML.
- No redirect target may be missing static HTML.
- No priority internal link should point to a noindex city-category guide if an indexable browse equivalent exists.

## Immediate Next Actions

1. Resolve the 154 unresolved rows exposed by the July 14 GSC drilldown export. Status: done with explicit 301s; crawler-export guard now passes.
2. Add a geo architecture inventory script/report. Status: next.
3. Patch `/credit-guide/{city}/` internal category links so they route to preferred `/browse/` pages where valid. Status: done for the priority root guide template.
4. Add a checker for internal links into noindex `/credit-guide/{city}/{category}/` pages. Status: done and wired into `npm run postbuild`.
5. Build and run the debugger contracts. Status: in progress.
6. Commit only after the crawler-error guard and postbuild checks pass.

## Find & Fix Plan Mapping

The architecture find-and-fix plan is the controlling order of operations:

1. Crawler 5XX access must be monitored first. This is partly infrastructure/CDN and cannot be solved by deleting valid pages.
2. Sitemap truth must stay enforced. The current build omits noindex city-category guide pages from sitemap XML and excludes crawler-export problem URLs.
3. Geo template competition must be reduced by making one URL the preferred target per query. The first code pass stops priority links from pointing at noindex `/credit-guide/{city}/{category}/` URLs.
4. Canonical coverage remains a planned follow-up after the current crawler-export and link-contract changes are committed.
5. Internal equity should flow from reviews and city hubs into `/city/` and valid `/browse/` pages, especially personal loans, business loans, loan companies, and credit repair city targets.
6. Pruning/removal remains data-led only. Do not noindex, delete, or redirect valid city pages without explicit approval and evidence that the page is low value after crawler access and internal linking have been fixed.
