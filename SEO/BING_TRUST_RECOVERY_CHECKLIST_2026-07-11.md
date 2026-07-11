# CreditDoc Bing Trust Recovery Checklist - 2026-07-11

## Working Diagnosis

Bing is not technically blocked. Bingbot can fetch CreditDoc through Cloudflare, sitemaps parse, and Bing Webmaster Tools shows indexed/crawled pages. The current working diagnosis is domain-level quality/trust suppression after the late-April apex-to-www and rendering-stack transition.

Evidence:
- Bing traffic export shows the visible drop after 2026-04-28.
- Bing Webmaster API still shows crawling and pages in index.
- The previously verified BWT property was `https://creditdoc.co/` while the canonical site is now `https://www.creditdoc.co/`.
- Current sitemap footprint is dominated by programmatic URL families, especially `/review/` and `/credit-guide/`.

## Technical Hygiene

- [x] Add `https://www.creditdoc.co/` as a Bing Webmaster Tools property.
- [x] Add Bing verification signals to the site:
  - `/BingSiteAuth.xml`
  - `<meta name="msvalidate.01" ...>`
- [ ] Deploy and verify the `www` property in BWT.
- [ ] Submit `https://www.creditdoc.co/sitemap-index.xml` and `https://www.creditdoc.co/sitemap.xml` under the verified `www` property.
- [x] Keep daily Bing direct URL submission lane running.
- [x] Keep daily sitemap resubmission running.
- [x] Keep daily IndexNow watchdog running.
- [x] Include Bing in the weekly SEO report.
- [ ] Check Cloudflare bot/security events for verified Bingbot challenges.

## Footprint / Quality Density

- [x] Measure sitemap footprint by URL family with `tools/creditdoc_sitemap_footprint_audit.py`.
- [x] Remove `/credit-guide/<city>/<category>/` permutation URLs from XML sitemap.
- [x] Mark `/credit-guide/<city>/<category>/` pages `noindex, follow`.
- [ ] Rebuild and confirm sitemap URL count drops from the previous 25,927 baseline.
- [ ] Audit `/review/` quality tiers before any wider suppression; do not noindex high-quality ready provider profiles blindly.
- [ ] Create a review-profile quality report using local DB/Supabase fields: quality score, enrichment state, protected status, city/state/category, and content depth.

## Authority Recovery

- [ ] Prioritize CFPB/data research assets as linkable pages.
- [ ] Build outreach list for finance journalists, local business publications, university libraries, and legitimate directories.
- [ ] Track referring-domain count weekly.
- [ ] Use LinkedIn/Pinterest to promote tools, answers, courses, wellness, and research assets without duplicate posts.

## Bing Support

- [ ] Draft Bing support ticket:
  - mention migration dates and May 1 flatline;
  - state that crawling and sitemap parsing are OK;
  - ask whether the site is under algorithmic quality suppression after migration;
  - provide evidence of footprint reduction and verification of `www`.

## Recovery Signal

Do not call recovery complete because URLs were submitted. Recovery means Bing impressions, query visibility, and page visibility return for high-value pages.
