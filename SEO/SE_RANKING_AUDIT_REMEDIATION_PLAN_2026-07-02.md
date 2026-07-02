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
| P0 | In progress | Runtime/static instability | 738 5XX during crawl | Live spot checks now return 200, suggesting crawl-time SSR/runtime instability | Move SEO pages to static; keep utility routes dynamic | Follow static migration plan |
| P0 | Pending | 5XX URLs in sitemap | 76 | Sitemap included pages that failed during crawl | After static migration, recrawl generated sitemap and remove/avoid any unstable route family | Verify sitemap after each build |
| P0 | Pending | Noindex pages in sitemap | 76 | Audit claims sitemap/noindex conflict; live spot checks did not show noindex on tested sitemap examples | Run local generated sitemap conflict checks and live curl against exact audit list | Remove noindex URLs from sitemap or remove noindex from pages if they should rank |
| P1 | In progress | Nofollow internal links | 141 | Internal `/go/` sponsored redirects and noindex pages create crawl warnings | Use `sponsored` for internal monetized redirects; avoid `nofollow` on internal utility paths where possible | First cleanup started |
| P1 | In progress | Search pages nofollow all links | 11 | `noindex, nofollow` blocks link following from search/filter pages | Change to `noindex, follow` | First cleanup started |
| P1 | In progress | Broken/redirected images | 6 | External favicon lookups on lender cards can return 3XX/4XX | Remove unreliable third-party favicon fallback; use stored logo or text initial | First cleanup started |
| P1 | Pending | One inbound internal link | 63 | Important new tools and some pages are underlinked | Add hub links from tools, best, course, answers, wellness, and selected category pages | Build internal link pass after static Phase 1 |
| P2 | Pending | Meta descriptions too long | 38 | Some descriptions exceed crawler threshold despite layout truncation | Normalize source descriptions to <= 155 chars for affected pages | Script/source pass |
| P2 | Pending | Title too short | 2 | `/review/lookout/`, `/review/gain/` titles are too generic | Update source title/meta data for those reviews | Source data patch |
| P2 | Pending | Duplicate H1 | 2 | `/review/sofi-bank/` and `/review/sofi/` collide | Make H1s distinguish bank vs SoFi profile | Source/template patch |
| P2 | Pending | Missing anchor text | 124 | Likely icon/empty links in cards/buttons | Audit rendered HTML and add aria-label/text where needed | Template pass |
| P3 | Pending | Slow pages | 2 | `/answers/`, `/tools/working-capital-calculator/` | Staticize `/answers/`; inspect working capital JS/CSS and payload | Phase 2 plus page-specific cleanup |
| P3 | Pending | JS not minified | 1 | `/tools/debt-payoff-calculator/` crawler warning | Verify if bundled JS is actually minified; ignore if false positive | Check after build |

## Work Order

### Batch 0: Immediate Cleanup

Status: in progress.

Changes already started:

- `BaseLayout.astro`: noindex pages now use `noindex, follow`.
- `LenderCard.astro`: removed unreliable external favicon fallback.
- `TopPicksTable.astro`: removed unreliable external favicon fallback.
- Review/best/compare CTA links: removed `nofollow` from internal sponsored redirects, leaving `sponsored`.

Validation:

- `npm run build` passed.
- Image alt contract passed.
- Image filename contract passed.

Next:

- Commit this cleanup once we decide whether to include the new audit/plan files.

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

- Build page samples.
- Re-run audit.

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

