# CreditDoc SE Ranking Audit Remediation Plan

Date: 2026-07-02

Source file:

- `/srv/BusinessOps/creditdoc/Traffic Analysis/audit_creditdoc.co_2026-07-02_21-54-22.pdf`

## Audit Summary

SE Ranking reported:

- Health score: 85/100
- Pages crawled: 1,000
- URLs found: 4,566
- Errors: 896
- Warnings: 87
- Notices: 508

Top reported issues:

- 738 pages with 5XX status during crawl
- 76 5XX pages in XML sitemap
- 76 noindex pages in XML sitemap
- 5 broken images
- 1 redirected image
- 11 noindex/nofollow search/filter pages
- 38 meta descriptions too long
- 2 title tags too short
- 2 duplicate H1s
- 63 pages with only one inbound internal link
- 141 pages with nofollow internal links
- 124 internal links missing anchor text
- 2 slow pages
- 1 unminified JavaScript warning

## Important Interpretation

Several sample URLs reported as 5XX returned 200 when checked live after the audit. That means the 5XX issue may be caused by runtime instability, crawl rate, cache misses, or temporary backend failures rather than permanently broken URLs.

Even if temporary, this still matters because Google and audit tools need stable responses.

## Remediation Tracker

| Priority | Status | Issue | Audit count | Diagnosis | Fix strategy | Owner action |
|---:|---:|---|---:|---|---|---|
| P0 | Fixed locally | Runtime/static instability | 738 5XX during crawl | Static SEO page families now emit physical HTML during build | Tools, answers, blog, wellness, best pages staticized; utility routes remain dynamic/nonindexable | Deploy and verify live cache/headers |
| P0 | Fixed locally | 5XX URLs in sitemap | 76 | Generated sitemap now validates locally against robots and critical URL rules | Static migration plus sitemap checks | Confirm after next SE Ranking crawl |
| P0 | Fixed locally | Noindex pages in sitemap | 76 | Local audit found LinkedIn OAuth callback in sitemap | Excluded `/linkedin-oauth-callback/` from sitemap; deep audit now 0 noindex-in-sitemap errors | Confirm after deploy/recrawl |
| P1 | Fixed locally | Nofollow internal links | 141 | Internal `/go/` sponsored redirects and noindex pages created crawl warnings | Noindex pages use `noindex, follow`; internal sponsored CTAs use `sponsored` without `nofollow` | Confirm after SE Ranking recrawl |
| P1 | Fixed locally | Search pages nofollow all links | 11 | `noindex, nofollow` blocked link following from search/filter pages | Changed noindex handling to `noindex, follow` | Confirm after SE Ranking recrawl |
| P1 | Fixed locally | Broken/redirected images | 6 | External favicon lookups on lender cards/review pages can return 3XX/4XX | Removed unreliable third-party favicon image fallbacks; stored logo or text initial remains | Confirm after SE Ranking recrawl |
| P1 | Pending | One inbound internal link | 63 | Important new tools and some pages are underlinked | Add hub links from tools, best, course, answers, wellness, and selected category pages | Build internal link pass after static Phase 1 |
| P2 | Fixed locally | Meta descriptions too long | 38 | Local rendered deep audit checks description length and now reports no long descriptions | Source/layout output normalized by generated HTML checks | Confirm after SE Ranking recrawl |
| P2 | Fixed locally | Title too short | 2 | `/review/lookout/`, `/review/gain/` titles were too generic | Added review SEO title/description overrides | Confirm after SE Ranking recrawl |
| P2 | Fixed locally | Duplicate H1 | 2 | `/review/sofi-bank/` and `/review/sofi/` collided | Added review H1 overrides to distinguish SoFi Bank from SoFi Financial Services | Confirm after SE Ranking recrawl |
| P2 | Fixed locally | Missing anchor text | 124 | Needed deterministic local rendered check | Added empty-anchor check to `scripts/seo_deep_audit.mjs`; current generated site has 0 warnings | Confirm after SE Ranking recrawl |
| P3 | Fixed locally | Slow pages | 2 | `/answers/` was previously runtime-heavy | `/answers/` and tool pages now emit static HTML; calculator JS bundles are Vite-minified | Confirm after SE Ranking recrawl |
| P3 | Fixed locally | JS not minified | 1 | `/tools/debt-payoff-calculator/` crawler warning | Build emits hashed Vite bundle; local build completed normally | Treat as crawler false positive unless SE repeats it |

Latest local validation, 2026-07-03:

```bash
npm run build
node scripts/seo_deep_audit.mjs
```

Result:

- Build passed with prebuild checks and postbuild sitemap/feed/image contracts.
- Rendered SEO audit checked 2,742 HTML pages and 24,891 sitemap URLs.
- Rendered SEO audit result: 0 errors, 0 warnings.

## Work Order

### Batch 0: Immediate Cleanup

Status: complete locally.

Changes completed:

- `BaseLayout.astro`: noindex pages now use `noindex, follow`.
- `LenderCard.astro`: removed unreliable external favicon fallback.
- `TopPicksTable.astro`: removed unreliable external favicon fallback.
- `review/[slug].astro`: removed unreliable external favicon fallback from review pages.
- Review/best/compare CTA links: removed `nofollow` from internal sponsored redirects, leaving `sponsored`.
- `astro.config.mjs`: excluded `/linkedin-oauth-callback/` from generated sitemap.
- `scripts/seo_deep_audit.mjs`: added empty-anchor-text detection.

Validation:

- `npm run build` passed.
- Image alt contract passed.
- Image filename contract passed.

Next:

- Deploy and confirm production no longer serves stale SSR route headers for the staticized page families.

### Batch 1: Static Editorial Pages

Target:

- `/blog/[slug]/`
- `/financial-wellness/[slug]/`

Reason:

- This directly reduces runtime crawl failures for helpful editorial pages.
- Blog and wellness index pages are already static.

Validation:

- Build generates `dist/blog/<slug>/index.html`.
- Build generates `dist/financial-wellness/<slug>/index.html`.
- Blog/wellness URLs remain in sitemap.
- Live deployed pages return 200 without runtime headers.

### Batch 2: Static Money/Answer Pages

Target:

- `/best/[slug]/`
- `/answers/[slug]/`
- `/answers/`

Reason:

- These support the keywords we care about: business loans, SBA loans, credit cards, credit repair, calculators, and answer queries.

Validation:

- Required money URLs in sitemap.
- No noindex.
- 200 responses under curl.
- GSC manual priority list uses these URLs first.

### Batch 3: Sitemap Hygiene

Target:

- XML sitemap only contains pages intended to rank.
- Remove dynamic/utility/filter URLs.
- Remove noindex URLs.
- Remove unstable route families until static or verified stable.

Validation:

```bash
node scripts/check_sitemap_robots_conflicts.mjs
node scripts/check_sitemap_critical_urls.mjs
```

Additional live validation:

- Extract URLs from sitemap.
- Curl a sample from every route family.
- Flag any 3XX, 4XX, 5XX, or noindex response.

### Batch 4: Internal Linking

Target:

- Tools
- Course
- Answers
- Wellness
- Money pages
- Selected city/category pages

Fix:

- Add related-resource blocks where needed.
- Ensure every important page has multiple followed internal links.
- Use exact/partial match anchors naturally:
  - SBA loan calculator
  - business line of credit calculator
  - commercial loan calculator
  - credit score simulator
  - debt payoff calculator
  - credit fundamentals course

Validation:

- Re-run SE Ranking crawl.
- Issue count for “one inbound internal link” should drop.

### Batch 5: Metadata Cleanup

Status: complete locally.

Target:

- 38 long descriptions
- 2 short titles
- 2 duplicate H1s

Fix:

- Create/update script to enforce:
  - title: 20-65 characters where practical
  - description: 120-155 characters
  - unique H1 for review collisions

Validation:

- `node scripts/seo_deep_audit.mjs` now reports 0 rendered SEO warnings.

### Batch 6: Performance Cleanup

Target:

- `/answers/`
- `/tools/working-capital-calculator/`
- `/tools/debt-payoff-calculator/`

Fix:

- Staticize `/answers/`.
- Inspect rendered payload and JS bundles for the calculators.
- Only change calculator JS if the warning is real after build.

Validation:

- Page loads under curl quickly.
- Audit warning reduced or documented as false positive.

## Weekly Audit Process

Every weekly SE Ranking report:

1. Save report under `Traffic Analysis/`.
2. Extract issue counts into this tracker.
3. Compare against prior week.
4. Separate real issues from crawler artifacts using live curl checks.
5. Fix P0/P1 first.
6. Do not chase low-value warnings before static migration and sitemap hygiene are stable.
