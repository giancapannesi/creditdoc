# CreditDoc — LIVE STATE (LIVE / RESUME-CURSOR)

> **Read me first.** This file is rewritten at the end of every session. It is the resume-cursor — the next-spawned Claude reads this BEFORE MEMORY.md / DECISIONS.md to know "where are we right now."

---

## 2026-07-15 - Geo architecture strategy adopted

Status: plan saved; first implementation pass in progress.

Source strategy:
- `/srv/BusinessOps/CreditDoc_SEO/creditdoc-city-page-targeting-strategy.md`
- `/srv/BusinessOps/CreditDoc_SEO/creditdoc-architecture-find-fix-plan v2.md`
- Repo plan: `reports/seo-debug/geo_architecture_resolution_plan_2026-07-15.md`

Core conclusion:
- CreditDoc's local problem is authority plus architecture, not thin city pages.
- City pages are strategic lead-capture assets. Do not noindex, remove, suppress, or blame them without measured evidence.
- Current authority is too low for the site footprint: Domain Trust 15, 3 referring domains, 4 backlinks, 19K sitemap URLs, and only about 7.8K estimated indexed pages.
- `/review/` pages currently carry most traffic and should route equity into the local architecture.

Geo route rules:
- `/city/{city}/` is the local hub for `loan companies in {city}`, `{city} credit repair companies`, and `financial services {city}`.
- `/browse/{category}/{city}/` is the preferred category-city money page for `personal loans {city}`, `business loans {city}`, and similar supported verticals.
- `/credit-guide/{city}/` can remain as supporting local education where useful.
- `/credit-guide/{city}/{category}/` is already `noindex, follow` and omitted from sitemap, but should stop receiving internal links as the ranking target when a valid `/browse/{category}/{city}/` page exists.
- Do not geo-target credit cards; the evidence shows effectively zero useful city-level credit-card demand. Fight credit cards on `/best/` and national category pages later.

Immediate implementation notes:
- Added the newer GSC coverage drilldown export as a crawler-error input:
  `/srv/BusinessOps/CreditDoc_SEO/gsc_reports/creditdoc.co-Coverage-Drilldown-2026-07-14 - Table.csv`
- Running `node scripts/check_crawler_error_exports.mjs` after adding that input exposed 154 unresolved rows / 94 unique paths.
- Those 154 unresolved rows were resolved with explicit 301 redirects. The crawler guard now checks 2,071 exported rows: 95 static, 1,976 redirected, 0 sitemap leaks, 0 bad redirect targets.
- `/credit-guide/{city}/` root links were patched so category links route to `/browse/{category}/{city}/` when there is enough city-specific provider coverage, otherwise back to the city guide; credit-card city links route to the category hub because useful city-level credit-card demand is effectively zero.
- Category pages no longer point priority local links at noindex `/credit-guide/{city}/{category}/` pages.
- Added `scripts/check_geo_architecture_contract.mjs` and wired it into `npm run postbuild` so priority source files fail if they reintroduce links to noindex city-category guide URLs.
- Next implementation steps:
  1. Finish the current full build and postbuild debugger run.
  2. Add a geo architecture inventory report for `/city/`, `/browse/`, `/credit-guide/`, `/state/`, and `/review/`.
  3. Patch `/review/` pages so profile equity routes into city hubs and valid `/browse/{category}/{city}/` pages.
  4. Add canonical coverage audit/fix after the current crawler-export/link-contract changes are committed.
  5. Commit and push only after checks pass.

## 2026-07-14 - Crawler error export guard and duplicate-validation diagnosis

Status: implemented and committed after the static state/review stabilization.

Why the 71-page validation failed:
- The current built HTML does not show duplicate titles, descriptions, canonicals, or H1s for the 59 listed pages that exist as static HTML.
- The exported validation set also contained 12 stale city URL variants using long state names, for example `/city/sugar-land-texas/`, while the real static page is `/city/sugar-land-tx/`.
- Google validation can fail the issue if its sampled URLs still include stale/unresolved variants, even when the original duplicate-meta template issue has been fixed.

What changed:
- Added `scripts/check_crawler_error_exports.mjs`.
- Wired the crawler export check into `postbuild`.
- Added an explicit 301 for the remaining homoglyph Jersey review slug from the 404 export.
- Wrote the operating plan: `reports/seo-debug/crawler_error_clearance_plan_2026-07-14.md`.

Verification:
- `node scripts/check_crawler_error_exports.mjs` passed:
  - 1,071 exported URL rows checked from the current 404 and duplicate CSVs.
  - 77 static HTML targets.
  - 994 explicit redirects.
  - 0 unresolved exported crawler URLs.
- `node scripts/check_static_html_contract.mjs` passed.

Operating rule:
- After every new GSC/Bing/SE crawler export is dropped into `SEO/`, run the crawler export contract before asking for validation.
- Fix stale URLs with 301s or convert valid recurring pages to static HTML.
- Do not bulk noindex, remove, robots-block, sitemap-remove, canonical-change, or pause publishing without Jammi's express approval.

## 2026-07-14 - Crawler 404/5xx stabilization for state and review pages

Status: implemented and build/debug verified locally.

What happened:
- Bing/GSC flagged valid `/state/` and `/review/` URLs as 404/5xx even though many opened normally in a browser later.
- The failure mode was delivery consistency: important pages could still be served through runtime/SSR paths, so a crawler could see a transient failure even when the content record and page quality were valid.
- This was not treated as a page-quality problem and no valid state/review/city pages were noindexed, removed, or suppressed.

What changed:
- Forced state roots and lending-law pages to prerender as static HTML:
  - `/state/`
  - `/state/<state>/`
  - `/state/<state>/lending-laws/`
- Converted review detail pages in the current build path to static HTML output and kept stale GSC review redirects in Cloudflare `_redirects` rather than runtime page code.
- Added `scripts/check_static_html_contract.mjs`.
- Wired the static HTML contract into `postbuild` so priority SEO surfaces fail the build if the expected static files disappear.

Verification:
- `npx astro build` passed on 2026-07-14 and emitted 19,074 HTML pages.
- Static state roots confirmed: 50 `/state/<state>/index.html` files.
- Exact Bing/GSC examples confirmed present as static HTML:
  - `/state/texas/`
  - `/review/minnesota-first-credit-and-savings-incorporated/`
  - `/review/ks-statebank/`
  - `/review/superior-national-bank/`
  - `/review/sam-check-cashing-machine-detroit-mi/`
  - `/review/city-of-wilmington/`
  - `/review/rey-cash-downtown-pawn-jewelry/`
  - `/review/the-state-exchange-bank/`
  - `/review/cash-city-pawn/`
  - `/review/citizens-bank-of-edinburg/`
  - `/review/first-hope-bank-a-national-banking-association/`
  - `/review/steer-financial-small-business-loans/`
  - `/review/advantage-credit-counseling/`
- Postbuild/debug contracts passed:
  - no truncated SEO fields
  - static HTML contract
  - sitemap/robots conflicts
  - critical sitemap URLs
  - schema/sitemap contract
  - `/best/` SERP title contract
  - feed contract
  - image alt and filename contracts
  - AI ingestion contract
  - internal static link contract

Follow-up:
- `npm run build` from a clean `dist` still needs a follow-up cleanup because `prebuild` runs `check_ai_ingestion_contract.mjs`, which expects existing built artifacts. For this stabilization pass the build was run directly with `npx astro build`, then the postbuild/debug contracts were run manually.
- Continue converting crawler-sensitive runtime surfaces in controlled batches only. Do not bulk noindex, remove, redirect, canonical-change, robots-block, sitemap-remove, feed-stop, or pause publishing without Jammi's express approval.

## 2026-07-14 - Public sanitation / Astro fingerprint reduction

Status: Phase 1 implemented, build verified, daily audit cron installed.

Operating rule:
- Treat this as a public-quality sanitation program, not a panic rewrite.
- Do not bulk noindex, remove, redirect, canonical-change, robots-block, sitemap-remove, feed-stop, or route-suppress pages without Jammi's express approval.
- Do not pause publishing, LinkedIn, Pinterest, IndexNow, GSC queue, or feed crons as part of sanitation work.
- Pick top pages first using evidence: GSC impressions, commercial value, local lead-capture potential, tools/money-page intent, and regulatory moat.
- Work in batches. Build/debug before commit.

What changed:
- Removed public `x-cdm-*` debug/cache headers from middleware/cache/runtime public paths.
- Removed visible `/r/` SSR pilot/architecture wording.
- Removed internal city-page labels from `CityLandingEnhancement.astro`:
  - `Batch {n} priority #{n} local landing page`
  - `Current GSC signal`
  - `data-city-enhancement-batch`
- Added Cloudflare adapter static bypasses for prerendered priority route families:
  - `/best`, `/city`, `/browse`, `/state`, `/research`, `/resources`
  - Existing bypasses already covered `/answers`, `/blog`, `/tools`, `/financial-wellness`, `/courses`.
- Added `scripts/check_public_sanitization_contract.mjs`.
- Added `npm run check:public-sanitization`.
- Added `scripts/check_internal_static_links.mjs`.
- Added `npm run check:internal-static-links` and wired it into postbuild so missing internal links to priority static surfaces fail the build instead of reaching Google/Bing.
- Wrote the full plan: `reports/seo-debug/public_sanitization_plan_2026-07-14.md`.
- Converted `/state/<state>/` roots from runtime rendering to static build output.
- Converted regulatory research pages to static build output:
  - `/research/consumer-complaints/`
  - `/research/lending-transparency/`
- Fixed crawler-facing stale links and installed 301s for:
  - `/financial-wellness/building-credit/` -> `/financial-wellness/building-credit-from-zero/`
  - `/best/best-free-credit-monitoring/` -> `/best/best-credit-monitoring-services/`
  - `/best/lower-cost-personal-loans/` -> `/best/cheapest-personal-loans/`
  - `/financial-wellness/understanding-credit-scores/` -> `/financial-wellness/credit-score-basics/`
  - `/best/best-debt-consolidation-companies/` -> `/best/best-debt-consolidation-loans/`
- Fixed local city/browse aliasing so `fix-my-credit` links resolve to the static `credit-repair` browse pages.
- Added runtime static fallback logic in middleware so a route with a built same-path static asset can serve that asset if runtime rendering throws.

Priority order:
1. Top 40 `/city/` and `/browse/` URLs with GSC signal from `reports/local-seo/local_pages_with_gsc_impressions_2026-07-12.csv`.
2. Commercial tool and money pages: calculators, quizzes, `/best/`, and related answers.
3. Regulatory moat: `/state/`, lending-law pages, `/research/`, `/resources/`, regulator directory, CFPB/complaint assets.
4. Remaining local pages in batches of 10.
5. Review/category/runtime surfaces after static-priority pages are clean.

Verification:
- `npm run build` passed on 2026-07-14.
- Build emitted and validated 2,987 HTML pages.
- Sitemap/schema contract passed with 19,115 sitemap URLs and 0 warnings.
- Internal static link contract passed:
  - 162,319 priority internal static links checked.
  - zero missing static targets after the city/browse alias and stale link fixes.
- Postbuild sitemap, `/best/`, feed, image alt/filename, and AI-ingestion contracts passed.
- `npm run check:public-sanitization` passed after rebuild:
  - 55 priority static pages checked.
  - zero public `x-cdm-*`, `SSR pilot`, `Architecture:`, batch/priority, GSC signal, city-enhancement data marker, or machine-generated wording matches.

Static status after this batch:
- Confirmed static SEO surfaces: `/answers/`, `/blog/`, `/best/`, `/tools/`, `/financial-wellness/`, `/courses/`, `/city/`, `/browse/`, `/state/`, `/research/`, `/resources/`, and state lending-law pages.
- Remaining public hybrid/runtime surfaces to convert in later controlled batches: `/review/`, `/categories/`, `/credit-guide/`, `/brand/`, and `/search/` where appropriate.
- API/utility routes intentionally remain runtime: `/api/*`, `/go/*`, `/r/*`, `/sitemap.xml`.

Daily cron:
- Install an alerting audit cron; do not auto-rewrite pages in bulk:
  - `40 18 * * * cd /srv/BusinessOps/creditdoc && /srv/BusinessOps/.venv/bin/python3 /srv/BusinessOps/tools/cron_alert.py "creditdoc-public-sanitization-contract" /usr/bin/node scripts/check_public_sanitization_contract.mjs >> /srv/BusinessOps/logs/creditdoc_public_sanitization_contract.log 2>&1`

## 2026-07-12 - City landing pages are being enhanced in batches of 10

Status: Batch 001 committed/pushed; Batch 002 implemented and build/debug verified locally.

Operating rule:
- CreditDoc city/local pages are strategic lead-capture assets, not pages to suppress by default.
- Work city pages in batches of 10 so quality can be checked and committed continuously.
- Do not bulk noindex, remove, redirect, canonical-change, sitemap-remove, robots-block, feed-stop, or route-suppress local pages without Jammi's express approval.
- Do not call local/city pages thin without measuring the actual built/live page.
- Every enhanced city page should improve local usefulness and lead capture: localized quiz/tool CTAs, email capture, city-specific FAQs, state/regulatory context, and links into the matching `/browse/`, `/tools/`, `/best/`, and `/state/` pages.
- Run a debugger/check pass every time before committing and pushing an SEO/local-page batch. Minimum checks: full build or approved focused build, postbuild contracts where applicable, rendered-page assertions for the edited URLs, truncation/SEO-field gate, and a short verification note in the batch report or this memory file.
- Bing/direct submission priority should favor new or newly improved tools, educational pages, and the local landing/capture pages we actively enhance. Keep cooldown as quota protection, but do not let the selector drift to low-value pages while improved capture pages are eligible.

Files added/updated for this lane:
- `src/content/local-city-landing-enhancements.json`
- `src/components/CityLandingEnhancement.astro`
- `src/components/LocalLeadCapture.astro`
- `src/pages/city/[slug].astro`
- `src/pages/browse/[catSlug]/[citySlug].astro`
- `src/pages/api/email-signup.ts`
- `reports/local-seo/city_page_enhancement_backlog_2026-07-12.csv`
- `reports/local-seo/city_page_enhancement_backlog_2026-07-12.md`
- `reports/local-seo/city_landing_batch_001_2026-07-12.md`

Batch 001 enhanced city URLs:
- `https://www.creditdoc.co/city/long-beach-ca/`
- `https://www.creditdoc.co/city/west-new-york-nj/`
- `https://www.creditdoc.co/city/vernon-ca/`
- `https://www.creditdoc.co/city/pittsburgh-pa/`
- `https://www.creditdoc.co/city/new-orleans-la/`
- `https://www.creditdoc.co/city/san-jose-ca/`
- `https://www.creditdoc.co/city/madison-tn/`
- `https://www.creditdoc.co/city/decatur-ga/`
- `https://www.creditdoc.co/city/college-park-ga/`
- `https://www.creditdoc.co/city/midwest-city-ok/`

Batch 002 enhanced city URLs:
- `https://www.creditdoc.co/city/rock-hill-sc/`
- `https://www.creditdoc.co/city/bakersfield-ca/`
- `https://www.creditdoc.co/city/bronx-ny/`
- `https://www.creditdoc.co/city/santa-clara-ca/`
- `https://www.creditdoc.co/city/seattle-wa/`
- `https://www.creditdoc.co/city/los-angeles-ca/`
- `https://www.creditdoc.co/city/marietta-ga/`
- `https://www.creditdoc.co/city/grand-prairie-tx/`
- `https://www.creditdoc.co/city/edmond-ok/`
- `https://www.creditdoc.co/city/arlington-tx/`

Batch 002 verification:
- `npm run build` passed on 2026-07-13.
- Postbuild contracts passed: sitemap/robots conflicts, critical URLs, schema/sitemap contract, best-page SERP contract, feed contract, image alt/filename contracts, and AI ingestion contract.
- Focused rendered-page debugger check passed for all 10 Batch 002 URLs: enhancement marker, FAQPage schema, Credit Repair Quiz link, Credit Calculator link, localized action plan, and local signup form were present.
- The build initially caught 336 existing SEO fields with ellipses in content JSON. Those source truncation markers were cleaned so the enforced `no-truncated-seo-fields` gate passes again.

What Batch 001 adds:
- Bespoke local action-plan block for each city.
- Localized tool links such as Credit Repair Quiz, Credit Calculator, Borrowing Power Quiz, Debt Payoff Calculator, business calculators, or denial/checklist tools.
- Priority internal links into matching `/browse/` and `/state/` pages.
- Local FAQ blocks plus FAQPage structured data for enhanced city pages.
- The existing local email capture block remains active globally on city and browse-local pages.

Next batch:
- Rows 21-30 of `reports/local-seo/city_page_enhancement_backlog_2026-07-12.csv`: Warren MI, Knoxville TN, Carrollton TX, Dallas TX, Dearborn MI, Sandy Springs GA, Philadelphia PA, Marrero LA, Omaha NE, National City CA.

Related status:
- The full 331-city backlog CSV was emailed to `gian.eao@gmail.com` via AgentMail on 2026-07-12.
- IndexNow was submitted for the main tools pages on 2026-07-12 and accepted by the API with HTTP 202; report: `reports/indexnow/creditdoc_tools_indexnow_2026-07-12.json`.
- Truncated SEO field cleanup passed after build: `reports/seo-debug/truncated_description_audit_2026-07-12.json` shows zero source JSON issues, zero rendered meta-description issues, and zero rendered title issues.

## 2026-07-12 - Evidence rule: do not call CreditDoc local pages thin without measuring

Status: checked against built/static output after the local programmatic SEO discussion.

Important working rule:
- Do not start CreditDoc SEO analysis with a generic "as long as the pages are not thin" caveat.
- First check the actual route family, built HTML, live status, sitemap/noindex status, and internal-link/profile depth.
- The current evidence says the main local layers are not thin.
- Do not blame city/local pages for Google or Bing performance without evidence from GSC/Bing/logs/live crawl data.
- Never make bulk indexability, sitemap, robots, canonical, redirect, route-family suppression, or crawl-control changes without Jammi's express approval first.
- Any proposed bulk SEO-control change must include URL count, route family, examples, measured reason, expected impact, risks, and rollback path before approval.

Measured evidence:
- `/city/` static pages:
  - 331 built pages sampled.
  - Word count min/median/average/max: 1,364 / 1,653 / 2,114.5 / 7,477.
  - Review-link count min/median/average/max: 6 / 13 / 19.4 / 89.
  - Shortest sampled examples still have 1,300+ words, 170+ links, H2 structure, and provider/review links.
- `/browse/<category>/<city>/` static service-city pages:
  - 467 built pages sampled.
  - Word count min/median/average/max: 720 / 1,352 / 1,549.7 / 6,282.
  - Review-link count min/median/average/max: 2 / 11 / 14.9 / 90.
- Live `/credit-guide/<city>/` root samples returned 200, were indexable, and had 2,000+ words with 200+ links and schema.
- `/credit-guide/<city>/<category>/` child pages are deliberately `noindex, follow`; this is a strategic footprint choice, not evidence that the pages are empty.

SEO implication:
- The question is not whether CreditDoc's core local pages are obviously thin. They are not, based on the current measurements.
- The next strategic decision is whether to selectively index/push stronger service-city pages, especially commercial-intent categories, while keeping weaker permutations controlled.

## 2026-07-12 - Local pages are now lead-capture priority

Status: planning started, no site behavior changed.

Files created:
- `reports/local-seo/live_local_page_inventory_2026-07-12.csv`
- `reports/local-seo/published_city_pages_2026-07-12.csv`
- `reports/local-seo/local_pages_with_gsc_impressions_2026-07-12.csv`
- `reports/local-seo/local_lead_capture_plan_2026-07-12.md`

Inventory:
- 331 published static `/city/` pages.
- 467 published static `/browse/<category>/<city>/` service-city pages.
- 798 local pages total in the built output.
- 0 embedded forms currently on those local pages.
- 798 local pages currently link to the Borrowing Power Quiz.

GSC evidence:
- 73 local pages matched impressions in the 2026-05-20 to 2026-06-19 GSC export.
- Top local impression pages include `/browse/pawn-shops/san-diego-ca/`, `/browse/pawn-shops/denver-co/`, `/browse/pawn-shops/phoenix-az/`, `/city/long-beach-ca/`, `/city/west-new-york-nj/`, `/city/vernon-ca/`, `/city/pittsburgh-pa/`, and `/city/new-orleans-la/`.

Strategic rule:
- Every meaningful local page is a possible client entry point.
- Add contextual email/quiz capture to local pages using the existing `/api/email-signup`, `/api/origination-intake`, Sendy, and Supabase `lead_captures` infrastructure.
- Do not gate the content.
- Do not make indexability, sitemap, robots, canonical, redirect, feed, or route-family suppression changes as part of lead-capture work.
- Rollout should start with the 73 local pages already showing GSC impressions, then expand to all `/browse/<category>/<city>/`, then `/city/`, then `/credit-guide/<city>/`.

## 2026-07-11 - Amazon SES DNS prepared for CreditDoc email

Status: DNS implemented; actual Sendy/SES send migration is blocked on SES SMTP/API credentials and sender-domain alignment.

What changed:
- Added the three Amazon SES DKIM CNAME records supplied for the `www.creditdoc.co` SES identity:
  - `chf6lh6etffrt5pu43vg6oqjfwu6vj5s._domainkey.www.creditdoc.co`
  - `nohyvjvjif3mw6la2h5buqwqmwnsgsiz._domainkey.www.creditdoc.co`
  - `q7jw7rhl3hlknvanw4m22tjfpmlma2ri._domainkey.www.creditdoc.co`
- Added Amazon SES to root SPF while keeping existing mail paths:
  - `v=spf1 include:simplelogin.co include:amazonses.com ip4:187.77.2.146 ip6:2a02:4780:4:a118::1 ~all`
- Added SPF for `www.creditdoc.co`:
  - `v=spf1 include:amazonses.com ~all`
- Report written:
  - `reports/email/amazon_ses_migration_2026-07-11.md`

Verification:
- Cloudflare API returned success for all SES DNS records.
- Public DNS checks passed via `1.1.1.1`, `8.8.8.8`, and `9.9.9.9`.
- Sendy status checked:
  - Sendy cron active every 5 minutes.
  - CreditDoc Sendy brand currently uses `noreply@creditdoc.co`, reply-to `gian.eao@gmail.com`.
  - Sendy main AWS key/secret fields are empty.
  - Sendy brand SMTP still points to `localhost:25`.
  - Postfix is not relaying through SES (`relayhost` empty).

Important:
- The supplied SES DKIM identity is `www.creditdoc.co`, but the active sender is `noreply@creditdoc.co`.
- DMARC is strict (`adkim=s; aspf=s`), so for best delivery we should verify the root `creditdoc.co` SES identity if we keep `noreply@creditdoc.co`.
- Do not change Sendy SMTP away from `localhost:25` until SES SMTP credentials or AWS IAM credentials are available; doing so without credentials would break course/autoresponder emails.

Next:
- Get SES SMTP credentials for the selected SES region.
- Prefer verifying root `creditdoc.co` in SES and using `noreply@creditdoc.co`.
- Then configure Sendy CreditDoc brand SMTP to SES (`email-smtp.<region>.amazonaws.com`, port `587`, TLS) and run the live signup E2E audit again.

## 2026-07-11 - Signup capture wiring verified end-to-end

Status: implemented, deployed, debugger-audited, test rows cleaned up.

What changed:
- Added a same-origin signup wrapper at `/api/email-signup` so forms no longer post directly from the browser to Sendy.
- The wrapper now returns structured confirmation data:
  - normalized email;
  - name;
  - signup type;
  - source page;
  - Sendy list name/status;
  - write confirmations.
- Course signups and Borrowing Power signups now also write durable rows to Supabase `lead_captures`.
- Credit repair and business loan quiz signups still use `/api/origination-intake` for Supabase quiz/lead capture, then `/api/email-signup` for Sendy.
- Fixed stale course module allowlist slugs in the signup wrapper.
- Fixed old browser-side `throw new Error(text)` paths that could hide the real signup failure after the wrapper change.
- Capped quiz `session_id` sanitization at 128 chars to match the Supabase `user_quiz_responses` RLS/check constraint.
- Added repeatable live debugger audit:
  - `tools/creditdoc_signup_e2e_audit.py`
  - latest report: `reports/signup-e2e/signup_e2e_2026-07-11.md`

Verification:
- `python3 -m py_compile tools/creditdoc_signup_e2e_audit.py` passed.
- `npm run build` passed all prebuild/postbuild contracts.
- Deployed to Cloudflare Worker version `d7674829-307f-4899-8e71-83ae0f0799cc`; deploy smoke checks returned 200 for the sampled routes.
- Live debugger audit passed 18/18 checks against `https://www.creditdoc.co`:
  - quiz API returned submitted email/source/tool/route/write confirmations;
  - quiz row existed in Supabase `user_quiz_responses`;
  - quiz lead existed in Supabase `lead_captures`;
  - course signup API returned submitted email/source/signup type/list/write confirmations;
  - course signup existed in Sendy course list;
  - course lead existed in Supabase `lead_captures`.
- The debugger removed its own test subscribers and Supabase rows after verification.

Operational rule:
- For signup/debug work, use `tools/creditdoc_signup_e2e_audit.py --cleanup` after deploy so live responses and backing stores are verified together.
- Do not reintroduce direct browser posts to `https://sendy.creditdoc.co/subscribe`; use the site API wrapper so responses are auditable.

Next:
- If more signup surfaces are added, register them in `/api/email-signup` with explicit source pages and add an audit case before deploying.

## 2026-07-11 - Hermes backlink lane pivoted to CreditDoc tools/data assets

Status: implemented and first batch sent.

What changed:
- Confirmed the old Hermes checklist/resource-page outreach was already executed and did not produce confirmed backlinks.
- Reclassified the old checklist-only strategy as exhausted; do not restart it as a new plan.
- Added a new Hermes outreach queue focused on stronger existing CreditDoc assets:
  - Credit Score Simulator
  - Debt Payoff Calculator
  - Borrowing Power Quiz
  - Credit Report Checklist
  - financial wellness guides
  - State Consumer Credit Regulator Directory
- New Hermes queue:
  - `/srv/BusinessOps/hermes-creditdoc-backlinks/OUTREACH_QUEUE_TOOLS_PR_2026-07-11.json`
- New sender:
  - `/srv/BusinessOps/hermes-creditdoc-backlinks/tools/send_tool_asset_outreach.py`
- Old exhausted wave2 cron entrypoint now delegates to the new sender:
  - `/srv/BusinessOps/hermes-creditdoc-backlinks/tools/send_wave2_university_library_outreach.py`
- Main Hermes autopilot now also runs the new sender after reply checks/research/reporting:
  - `/srv/BusinessOps/hermes-creditdoc-backlinks/tools/backlink_autopilot_daily.py`
- Guardrails:
  - email only;
  - no calls, forms, accounts, DMs, paid placements, or site publishing;
  - no duplicate recipient sends from previous Hermes logs;
  - shared daily cap of 3 tool/data asset outreach emails across both cron paths.

First live batch sent on 2026-07-11:
- University of Tennessee Center for Financial Wellness -> Credit Score Simulator / Debt Payoff / Credit Report Checklist.
- Marquette Money Matters -> Debt Payoff Calculator / Credit Score Simulator / Build Credit From Scratch.
- Foothill College Financial Aid -> Credit Score Simulator / Build Credit answer / Credit Report Checklist.

Verification:
- Python compile passed for the touched Hermes scripts.
- `tools/validate_outreach_queue.py` passed with no queue errors.
- First live batch succeeded and wrote `OUTREACH_SENT_LOG_2026-07-11.md`.
- Post-send dry run returned zero targets, confirming today's shared 3-send cap is enforced.
- Updated Hermes project memory at `/srv/BusinessOps/hermes-creditdoc-backlinks/PROJECT_MEMORY.md`.

Next:
- Let the weekday Hermes crons continue the remaining tool/data asset queue.
- Check reply reports daily before more sends.
- Do not judge this lane by reports generated; judge by replies and confirmed backlinks only.

## 2026-07-10 - Bing drop investigation and direct recovery lane

Status: implemented, first Bing batch accepted, daily cron installed, memory updated.

## 2026-07-11 - Bing www property verified and footprint reduced

Status: implemented, deployed, verified, Bing resubmitted, daily lane consumed for today.

What changed:
- Added `https://www.creditdoc.co/` as a Bing Webmaster Tools property via API.
- Deployed Bing verification signals:
  - `public/BingSiteAuth.xml`
  - `<meta name="msvalidate.01" content="4B5251D006A8437B1A0C7C45CB7C374D" />`
- Bing API verification succeeded: `https://www.creditdoc.co/` now returns `IsVerified: true`.
- Updated Bing-specific tooling to use the canonical verified www property:
  - repo: `tools/creditdoc_bing_recovery.py`
  - repo: `tools/creditdoc_sitemap_resubmit.py`
  - repo: `tools/creditdoc_bing_indexnow_watchdog.py`
  - external: `/srv/BusinessOps/tools/bing_webmaster.py`
  - external: `/srv/BusinessOps/tools/creditdoc_weekly_digest.py`
  - external: `/srv/BusinessOps/tools/seo_manager_daily.py`
- Submitted the www sitemaps to Bing under the verified www property:
  - `https://www.creditdoc.co/sitemap-index.xml`
  - `https://www.creditdoc.co/sitemap.xml`
- Ran today’s direct Bing recovery batch against the verified www property:
  - 100 URLs submitted.
  - Quota after submission: `0 daily / 2,000 monthly`.

Footprint reduction:
- Added `tools/creditdoc_sitemap_footprint_audit.py`.
- Added tracked plan: `SEO/BING_TRUST_RECOVERY_CHECKLIST_2026-07-11.md`.
- Removed `/credit-guide/<city>/<category>/` permutation URLs from XML sitemap generation.
- Marked `/credit-guide/<city>/<category>/` pages `noindex, follow` with both:
  - HTML meta via `BaseLayout noindex`.
  - `X-Robots-Tag: noindex, follow` response header.
- These pages still return 200 for users and preserve internal links, but they are no longer submitted as indexable search landing pages.

Verification:
- `npm run build` passed.
- Postbuild contracts passed:
  - sitemap/robots conflicts;
  - critical sitemap URLs;
  - schema/sitemap contract;
  - Best SERP contract;
  - feed contract;
  - image alt/filename contracts;
  - AI ingestion contract.
- Deployed with `./deploy.sh` to Cloudflare Worker version `a580e281-43c2-42c2-929e-67b7aff18506`; smoke checks passed.
- Live Bing verification file works: `https://www.creditdoc.co/BingSiteAuth.xml`.
- Live homepage contains `msvalidate.01`.
- Live city/category sample `/credit-guide/austin-tx/credit-repair/` returns `X-Robots-Tag: noindex, follow`.
- Live sitemap check:
  - 4 sitemap files.
  - 19,065 sitemap URLs.
  - 381 `/credit-guide/<city>/` root guides in sitemap.
  - 0 `/credit-guide/<city>/<category>/` subpages in sitemap.
- Previous measured local sitemap baseline before the cut was 25,927 URLs, so the first footprint reduction removed about 6,862 submitted URLs without touching tools, best pages, answers, blogs, wellness, courses, research, resources, state pages, or city root guides.

Current Bing status:
- Weekly digest dry run now reads the verified www property.
- Latest Bing crawl: 2026-07-10, 3,082 crawled, 143 errors, 18,398 in index.
- Bing traffic is still the active problem: 7d and 30d impressions remain 0.
- Treat this as trust/quality recovery, not solved by submission alone.

Next:
- Review `/review/` quality tiers before any wider footprint suppression. Do not noindex high-quality ready profiles blindly.
- Check Cloudflare security events/Bot settings for verified Bingbot challenge history.
- Draft Bing Webmaster Support ticket after the www property and footprint reduction are visible.
- Continue backlink/authority work around CFPB/data research assets; Bing recovery likely depends on authority signals, not only technical cleanup.

## 2026-07-10 - Bing added to weekly CreditDoc SEO review

Status: implemented in the existing Monday weekly SEO digest.

What changed:
- Updated `/srv/BusinessOps/tools/creditdoc_weekly_digest.py` so the existing Monday report now includes Bing Webmaster data every week.
- No new cron was needed because the weekly digest already runs:
  - `0 7 * * 1 /srv/BusinessOps/.venv/bin/python3 /srv/BusinessOps/tools/cron_alert.py "creditdoc-weekly-digest" /srv/BusinessOps/.venv/bin/python3 /srv/BusinessOps/tools/creditdoc_weekly_digest.py --send >> /srv/BusinessOps/logs/creditdoc_weekly_digest.log 2>&1`

Weekly Bing section now reports:
- 7-day and 30-day Bing impressions/clicks.
- Warning if Bing impressions remain zero.
- Latest Bing crawl date, crawled pages, crawl errors, and pages in index.
- Bing URL submission quota.
- Top Bing queries and top Bing pages when Bing reports them.

Verification:
- `python3 -m py_compile /srv/BusinessOps/tools/creditdoc_weekly_digest.py` passed.
- Dry run of `/srv/BusinessOps/tools/creditdoc_weekly_digest.py` succeeded and included the new Bing section.
- Current Bing facts in the dry run:
  - Traffic 7d: 0 impressions / 0 clicks.
  - Traffic 30d: 0 impressions / 0 clicks.
  - Latest crawl: 2026-07-09, 2,702 crawled, 115 errors, 18,180 in index.
  - URL submission quota: 0 daily / 2,100 monthly after the first direct recovery batch.

Operational rule:
- From now on, Bing must be included in the weekly CreditDoc SEO review, not treated as an occasional manual check.
- The recovery signal is Bing impressions and query/page visibility returning; crawl/index count alone is not enough.

Evidence checked:
- Bing performance export in `SEO/Bing Results/creditdoc.co_SearchPerformanceOverview_All_7_10_2026.csv` shows traffic fell from active April impressions/clicks to near-zero after 2026-04-28.
- Git history shows the timing lines up with the 2026-04-27/2026-05-02 canonical/SSR/Cloudflare transition:
  - 2026-04-27 robots/sitemap canonical changed to `www`.
  - 2026-04-27 through 2026-05-02 SSR/Cloudflare/Astro architecture cutover and sitemap injection changes landed.
- Bing Webmaster API confirms CreditDoc is not technically disconnected:
  - 2026-07-09: 2,702 pages crawled, 115 errors, 18,180 pages in index.
  - Current Bing API traffic for the last 30 days is still 0 impressions / 0 clicks.
- Interpretation: strongest evidence is not a robots/access outage. Bing is crawling and indexing, but search visibility appears to have reset/dropped after the late-April canonical/runtime transition. Treat as a Bing ranking/canonical trust recovery problem, not a hard crawl disconnect.

Fixes made:
- Hardened `tools/creditdoc_priority_indexing.py` so post-Google-push DB stamping retries SQLite locks instead of failing after the URL submission succeeds. This prevents local indexation tracking from drifting when the DB is busy.
- Added `tools/creditdoc_bing_recovery.py`:
  - Selects high-value CreditDoc pages first: tools, courses, regulatory answers, wellness, money, research/resources, then blog/state.
  - Live-validates each URL as HTTP 200 before submission.
  - Submits through Bing Webmaster Tools direct `SubmitUrlBatch`, separate from generic IndexNow.
  - Records a 14-day cooldown in `/srv/BusinessOps/data/creditdoc_bing_direct_submission_state.json`.
  - Writes run reports to `reports/bing-recovery/`.
- Ran the first live Bing recovery batch at 2026-07-10 18:13 UTC:
  - 100 URLs selected and submitted.
  - Bing quota moved from `100 daily / 2200 monthly` to `0 daily / 2100 monthly`, confirming acceptance.
  - Report: `reports/bing-recovery/bing_recovery_2026-07-10.md`.
- Installed daily cron:
  - `35 8 * * * cd /srv/BusinessOps/creditdoc && /srv/BusinessOps/.venv/bin/python3 tools/creditdoc_bing_recovery.py --apply --limit 100 >> /srv/BusinessOps/logs/creditdoc_bing_recovery.log 2>&1`

Verification:
- `python3 -m py_compile tools/creditdoc_priority_indexing.py tools/creditdoc_bing_recovery.py` passed.
- `creditdoc_bing_recovery.py --apply --limit 100` succeeded.
- Bing Webmaster quota after submission: `0 daily / 2100 monthly`.
- `creditdoc_feed_continuity_watchdog.py` passed: RSS/feed OK, 501 answers, 139 wellness, 19 tools, 10 courses all passed static HTML checks, all monitored content crons active.
- `verify_crons.sh` passed: all 59 expected crons present.

Next monitoring:
- Check Bing Webmaster traffic/crawl/page stats daily for 7-14 days.
- Do not infer recovery from crawl/index count alone; the recovery signal is impressions returning for high-value tools, answers, courses, wellness, and money pages.
- Keep the direct Bing recovery lane running unless explicitly stopped by the founder.

## 2026-07-10 - Bing sitemap resubmitted

Status: done and scheduled.

What happened:
- Founder correctly asked whether a fresh sitemap should be submitted to Bing after the Bing visibility collapse.
- Confirmed old public ping endpoints are no longer usable:
  - Google `/ping?sitemap=` returns HTTP 404 with deprecation message.
  - Bing `/ping?sitemap=` returns HTTP 410 Gone.
- Used the Bing Webmaster Tools API method `SubmitFeed` instead.

Submitted to Bing:
- `https://www.creditdoc.co/sitemap-index.xml`
- `https://www.creditdoc.co/sitemap.xml`

Result:
- Bing returned success for both submissions: `{"d": null}`.
- Added `tools/creditdoc_sitemap_resubmit.py` to make this repeatable.
- Run report: `reports/sitemap-resubmissions/sitemap_resubmit_2026-07-10.md`.
- Installed daily cron:
  - `45 8 * * * cd /srv/BusinessOps/creditdoc && /srv/BusinessOps/.venv/bin/python3 tools/creditdoc_sitemap_resubmit.py --apply >> /srv/BusinessOps/logs/creditdoc_sitemap_resubmit.log 2>&1`

Google note:
- GSC currently has the CreditDoc sitemaps listed under `sc-domain:creditdoc.co`.
- GSC readback showed:
  - `https://creditdoc.co/sitemap-index.xml` last submitted 2026-05-07, last downloaded 2026-07-01, 0 errors, 0 warnings.
  - `https://www.creditdoc.co/sitemap-index.xml` last submitted 2026-05-07, last downloaded 2026-07-06, 0 errors, 0 warnings.
- Stored GSC OAuth token is read-only (`webmasters.readonly`), so programmatic Google sitemap submission is blocked until OAuth is refreshed with full `https://www.googleapis.com/auth/webmasters` scope.

## 2026-07-10 - CreditDoc IndexNow key rotated and monitored

Status: fixed, deployed, tested, watchdog scheduled.

What happened:
- Founder provided the new IndexNow key: `1efee5eebbd54ea4812e2e77a9b73fcc`.
- Important correction: this is an IndexNow key, not a Bing Webmaster API key. The previous Bing Webmaster API key was restored after the new string failed strict Bing Webmaster API validation.

Fix:
- Added the required root key file:
  - `public/1efee5eebbd54ea4812e2e77a9b73fcc.txt`
  - Live production URL verified: `https://www.creditdoc.co/1efee5eebbd54ea4812e2e77a9b73fcc.txt`
- Corrected CreditDoc IndexNow payloads to match the protocol:
  - `host`: `www.creditdoc.co`
  - `key`: `1efee5eebbd54ea4812e2e77a9b73fcc`
  - `keyLocation`: `https://www.creditdoc.co/1efee5eebbd54ea4812e2e77a9b73fcc.txt`
  - URL lists use `https://www.creditdoc.co/...` URLs, so host/keyLocation now match and avoid 422 host mismatch.
- Updated repo scripts:
  - `tools/creditdoc_priority_indexing.py`
  - `tools/live_ops/creditdoc_blog.py`
  - `tools/live_ops/creditdoc_comparison_generator.py`
  - `tools/live_ops/creditdoc_wellness_generator.py`
- Updated external operational scripts outside this repo:
  - `/srv/BusinessOps/tools/indexnow.py` now uses the new key only for CreditDoc and keeps the old default for other sites.
  - `/srv/BusinessOps/tools/gsc_coverage_monitor.py` CreditDoc config now uses `www.creditdoc.co` and the new key.
  - CreditDoc-specific external generators were updated to the new key/host/keyLocation: blog, blog scheduler, blog generator, content drip, comparison generator, approval review, QA fixer, and wellness generator.

Deploy/verification:
- `npm run build` passed all SEO contracts.
- Deployed via `./deploy.sh` to Cloudflare Worker version `a788d095-07e2-4eaf-9318-be019a5bfd73`; targeted cache purge completed; route-family smoke checks all returned 200.
- Live key file returned HTTP 200 and exact key content.
- Direct IndexNow POST to `https://api.indexnow.org/IndexNow` using the new payload returned HTTP 202.
- `python3 tools/creditdoc_priority_indexing.py --tier tools --indexnow-only --limit 5` returned `IndexNow: 2 OK, 0 failed`.

Monitoring added:
- Added `tools/creditdoc_bing_indexnow_watchdog.py`.
- It checks:
  - live IndexNow key file;
  - Bing crawl/index stats;
  - Bing traffic/impressions.
- Current result at 2026-07-10 18:40 UTC:
  - key file OK;
  - Bing crawl OK: 2026-07-09 crawled 2,702, in index 18,180;
  - Bing traffic still bad: 30-day impressions=0, clicks=0.
- Installed daily alerting cron:
  - `5 9 * * * cd /srv/BusinessOps/creditdoc && /srv/BusinessOps/.venv/bin/python3 /srv/BusinessOps/tools/cron_alert.py "creditdoc-bing-indexnow-watchdog" /srv/BusinessOps/.venv/bin/python3 tools/creditdoc_bing_indexnow_watchdog.py >> /srv/BusinessOps/logs/creditdoc_bing_indexnow_watchdog.log 2>&1`
- This watchdog intentionally fails while Bing impressions remain zero, so this cannot silently disappear again.

## 2026-07-08 - CreditDoc health check, blog 404 fix, and title softener cleanup

Status: deployed, live-verified, memory updated, no cron/feed/social automation stopped.

What happened:
- Full CreditDoc health check found the site broadly working, but the daily content audit initially flagged 2 new blog URLs as HTTP 404:
  - `/blog/can-an-identity-theft-unfreeze-your-credit/`
  - `/blog/can-authorized-user-pay-credit-card/`
- Root cause was stale production assets after new blog source records were present in `src/content/blog-posts.json`; current source had not yet been deployed.
- While verifying the generated blog pages, found raw markdown link leakage risk in blog section rendering and an awkward title-softener output where `What You Need` became `key context`.

Fix:
- Updated `src/pages/blog/[slug].astro` so blog section content strips existing markdown links before the inline linker runs, preventing raw `[text](/url)` leakage/nested link artifacts.
- Updated `src/utils/safe-copy.ts` so `What You Need` / `What You Need to Know` softens to `What to Review` instead of `key context`.
- Rebuilt and deployed to Cloudflare Worker version `48e5eaf0-e411-4c2b-ac26-78951d74edf5`.
- Purged the Cloudflare cache for `/blog/can-authorized-user-pay-credit-card/` after confirming the local built asset was correct.

Verification:
- `npm run build` passed.
- Postbuild contracts passed: sitemap/robots conflicts, critical sitemap URLs, schema/sitemap contract, Best SERP contract, feed contract, image alt contract, image filename contract, and AI ingestion contract.
- Live checks returned HTTP 200 for homepage, the two fixed blog pages, a priority answer, a priority tool, the course hub, a wellness page, sitemap, RSS, and Atom feed.
- Live blog pages now have canonical tags, JSON-LD, no raw markdown links, and corrected schema/H1 for `Can Authorized User Pay Credit Card? What to Review`.
- `creditdoc_content_audit.py --preview --no-fix --stdout` returned `0 issues found`.
- `creditdoc_feed_continuity_watchdog.py` passed:
  - RSS newest `2026-07-08T00:00:00+00:00`
  - feed newest `2026-07-08T00:00:00+00:00`
  - answer HTML 495, wellness HTML 139, tools HTML 19, courses HTML 10 all passed title/meta/H1/canonical/content checks.
- `/srv/BusinessOps/tools/verify_crons.sh` returned `OK: All 59 expected crons present`.
- `node scripts/creditdoc_linkedin_manager.mjs audit-social-duplicates` returned no current LinkedIn/Pinterest duplicate targets. Historical Pinterest duplicate for the commercial-loan calculator remains recorded from July 2/3, before the current guard window.

Operational note:
- Today’s auto-generated two-week SEO calendar brief was kept at `SEO/two-week-action-calendar/2026-07-08-day-10.md`.
- Do not pause or stop feeds, city/blog/answers/wellness publishing, Pinterest, or LinkedIn automation without explicit founder approval.

## 2026-07-06 - GSC review 404 remediation

Status: implemented locally; build and deep SEO audit clean; deployment/live validation next.

What changed:
- Parsed `SEO/Table 404 Missing Pages.csv` from GSC.
- Confirmed the unresolved issue was the old `/review/` URL family: 805 unique review slugs in the export.
- Added `data/gsc_404_review_redirects_2026-07-06.json` with 802 permanent redirect targets.
- Excluded 3 slugs that are now live published review pages:
  - `/review/power-financial/`
  - `/review/pioneer-appalachia/`
  - `/review/mattel/`
- Added a static `/review/` research hub page with title/meta/canonical/schema and links to categories, best pages, tools, answers, wellness, city, and state hubs.
- Wired middleware to 301 the old missing/draft/noindex review URLs before the SSR review route runs.

SEO rationale:
- Do not publish raw, draft, pending, noindex, or quarantined lender records just to silence GSC. That would increase low-quality crawlable pages.
- Redirect exact local draft/noindex records to their live category where possible.
- Redirect missing records to a strong inferred category only when the slug is obvious; otherwise redirect to `/review/`.
- Avoid homepage redirects so Google sees a relevant consolidation path rather than a broad soft-404 pattern.

Verification:
- `npm run build` passed.
- Postbuild contracts passed: sitemap/robots conflicts, critical sitemap URLs, schema/sitemap contract, Best SERP contract, feed contract, image alt, image filename, AI ingestion.
- `node scripts/seo_deep_audit.mjs` passed with `errors=0,warnings=0` across 2,879 rendered HTML pages and 25,133 sitemap URLs.
- Redirect manifest validation passed: 802 redirects, 805 unique review slugs, 3 live review slugs excluded, 0 bad targets.
- `/review/` generated as static HTML with 50-character title, 145-character meta description, canonical `https://www.creditdoc.co/review/`, and H1 `Financial Service Reviews`.

Next:
- Commit, push, deploy, then live-sweep representative/all GSC review URLs to confirm no flagged review URL still returns 404.
- After live verification, GSC can be asked to validate the 404 fix. Expect GSC lag while Google recrawls old URLs.

## 2026-07-06 - Phase 1 KPI report marked as primary SEO operating report

Status: report reviewed; no automation changed.

Why it matters:
- The `CreditDoc Phase 1 KPI` email generated by `tools/creditdoc_phase1_kpi.py` is a high-value strategic report because it separates:
  - content production volume;
  - answer lifecycle from published to indexed to visible;
  - money-page indexation;
  - selected keyword universe coverage;
  - site-wide GSC query/page visibility;
  - intent mix;
  - mature gate scores;
  - long-tail phrase candidates by money page.

Key 2026-07-06 signals:
- `/answers/` production is large: 491 published vs Month 1 target of 27.
- Only 14/491 answers have `primary_phrase`; this is a clear metadata/routing gap.
- Answer lifecycle: S1_published=491, S2_indexed=14, S3_visible=3, S4_on_page_2=1, S5_on_page_1=1.
- Money pages indexed: 25/27 (92.6%), so the immediate money-page issue is more ranking/visibility/internal authority than raw indexation.
- Site-wide GSC 28-day pull: 9,203 queries, 3,876 pages, 23,093 impressions, 1 click, CTR 0.004%.
- Intent mix is still dominated by brand/entity search: 20,203 brand_search impressions vs 1,439 lending_intent impressions.
- Selected keyword universe coverage is nearly absent: only 2 of 7,964 selected phrases had any GSC impression in the last 28 days.
- The long-tail money-page table should drive the next writing/internal-linking plan, but must be filtered for real fit; do not blindly chase off-target high-volume phrases.

Operational use:
- Treat `tools/creditdoc_phase1_kpi.py` output as the weekly/primary SEO operating dashboard alongside GSC and SE Ranking.
- Use it to decide: which answers need primary phrases, which selected phrases are not entering GSC, which money pages need supporting content/internal links, and which mature gates remain closed.

## 2026-07-06 - Content audit blog 404s cleared

Status: verified clear; no cron, feed, publishing, Pinterest, or LinkedIn automation stopped.

What happened:
- User pasted a daily content audit showing 2 blog 404s:
  - `/blog/can-a-low-credit-score-get-a-mortgage/`
  - `/blog/can-a-student-get-credit-card/`
- Live production checks at 2026-07-06 12:01 UTC returned HTTP 200 for both URLs.
- Both pages have canonical tags and appear as the newest items in `/rss.xml`.

Verification:
- `/srv/BusinessOps/.venv/bin/python3 /srv/BusinessOps/tools/creditdoc_content_audit.py --preview --no-fix` returned `0 issues found`.
- The preview showed 12 city guides, 4 blogs, 0 answers, 0 wellness, required public surfaces OK, and all 4 recent blog posts OK.

Interpretation:
- The pasted audit was stale relative to the current production state, likely from before the later deploy/cache refresh made the two blog pages live.

## 2026-07-06 - Feed watchdog false robots failure fixed

Status: fixed and verified; no cron, feed, publishing, Pinterest, or LinkedIn automation stopped.

What happened:
- The 11:12 UTC feed continuity watchdog failed only on `required surfaces`.
- Root cause was a stale monitor rule in `/srv/BusinessOps/tools/creditdoc_required_surfaces.py` that still required `Disallow: /go/` in `/robots.txt`.
- That old requirement conflicted with the current SEO fix: `/go/*` must stay crawlable so Google can see `X-Robots-Tag: noindex, nofollow`.

Fix:
- Updated `creditdoc_required_surfaces.py` to reject `Disallow: /go/` and instead verify a representative `/go/` redirect returns `X-Robots-Tag` containing `noindex` and `nofollow`.

Verification:
- `/srv/BusinessOps/.venv/bin/python3 /srv/BusinessOps/tools/creditdoc_required_surfaces.py` passed.
- `/srv/BusinessOps/.venv/bin/python3 /srv/BusinessOps/tools/creditdoc_feed_continuity_watchdog.py` passed at 2026-07-06 12:00 UTC.
- Feeds, required surfaces, answer HTML, wellness HTML, tools HTML, courses HTML, and all monitored content crons were OK.

## 2026-07-06 - Specialist SEO agent review saved

Status: completed as a strategic review; no code, cron, feed, publishing, Pinterest, or LinkedIn automation changed.

What changed:
- Ran four specialist review lanes: technical SEO/crawl, content SEO/keyword architecture, authority/digital PR, and commercial SEO/SERP conversion.
- Saved the consolidated review to `SEO/SPECIALIST_SEO_AGENT_REVIEW_2026-07-06.md`.

Core diagnosis:
- CreditDoc is being discovered by Google, but Google is mostly seeing the wrong surface.
- Latest GSC export shows `/review/` pages produced 36,279 impressions and 8 clicks, while `/best/`, tools, answers, wellness, and course/revenue assets barely registered.
- Context: review pages dominate discovery partly because they were the first/largest page family created. Local city pages also received manual URL Inspection submissions earlier when the team believed automatic API submissions were materially moving indexation.
- Remaining technical risk is not duplicate metas/robots anymore; it is sitemap/runtime surface size and crawl priority: the sitemap advertises about 25k URLs, while most are runtime URLs rather than physical static HTML.
- Strategic work should focus on sitemap narrowing, live sitemap validation, money-page routing, answer-to-money-page cluster mapping, exact commercial title/meta alignment, and data-led authority outreach.

Do next:
- Build/live-run sitemap status validator.
- Narrow sitemap exposure for low-yield runtime review/city/category surfaces.
- Align `data/money_page_map.json` and `src/utils/inline-linker.ts`.
- Review `/best` title/meta softening from "Best" to "Compare".
- Keep manual GSC quota focused on tools, course, high-intent wellness, answers, and money pages.

## 2026-07-06 - LinkedIn footer link added

Status: implemented locally, build/audit clean, no cron or publishing automation changed.

What changed:
- Added the public CreditDoc LinkedIn company profile link to the standard site footer and the public resource footer.
- Profile URL used: `https://www.linkedin.com/company/creditdoc-co/`.
- External footer links render with `target="_blank"` and `rel="noopener noreferrer"`.

Verification:
- `npm run build` passed, including sitemap/robots, critical sitemap URL, feed, image alt, and image filename checks.
- Rendered homepage and resources page both include the LinkedIn footer links.
- `node scripts/seo_deep_audit.mjs` passed with `errors=0, warnings=0` across 2,875 rendered HTML pages and 25,129 sitemap URLs.

## 2026-07-06 - Manual GSC queue fixed to 10/day and unindexed action plan saved

Status: in progress operationally; automation corrected for the founder's actual 10 manual GSC URL Inspection submissions/day.

What changed:
- Saved the current GSC unindexed action plan to `SEO/GSC_CRAWLED_NOT_INDEXED_ACTION_PLAN_2026-07-06.md`.
- Updated `/srv/BusinessOps/tools/creditdoc_daily_gsc_queue.py` from 20 URLs/day to 10 URLs/day.
- Updated `/srv/BusinessOps/CRON_OPERATIONS.md` to state the CreditDoc GSC queue is a daily 10-URL manual queue.
- Did not pause, stop, or disable any publishing/feed/social cron.
- Repaired the local source JSON for `eagle-finance` and `eagle-loan` after a later export rewrote the duplicate meta descriptions; the rendered duplicate-meta fix must remain protected.

Evidence:
- The daily queue cron is installed at 06:15 UTC:
  `/usr/bin/flock -w 7200 /tmp/creditdoc_db_writer.lock -c '/srv/BusinessOps/.venv/bin/python3 /srv/BusinessOps/tools/creditdoc_daily_gsc_queue.py --apply'`
- Today's 06:15 UTC cron had already sent the old 20-URL email before the script was corrected. Do not send a second same-day email just to correct the count.
- Use the first 10 URLs from today's received email as today's manual submissions:
  `/courses/credit-fundamentals/`, `/tools/accounts-receivable-financing-calculator/`, `/tools/borrowing-power-quiz/`, `/tools/credit-repair-qualify-quiz/`, `/tools/credit-score-simulator/`, `/tools/equipment-financing-calculator/`, `/tools/loan-denial-reason-checker/`, `/tools/sba-guarantee-fee-calculator/`, `/financial-wellness/secured-credit-cards-complete-guide/`, `/financial-wellness/side-hustle-income-guide/`.
- Corrected the DB stamp for the old 20-URL email: positions 11-20 were unstamped so they are not hidden by cooldown when the founder only submits 10/day.
- Dry-run after the DB correction returns exactly 10 URLs for the next eligible queue: `/financial-wellness/store-credit-cards-worth-it/`, `/financial-wellness/subscription-audit-guide/`, `/financial-wellness/50-30-20-budget-rule/`, `/financial-wellness/609-dispute-letter-truth/`, `/financial-wellness/authorized-user-strategy/`, `/financial-wellness/auto-loans-bad-credit/`, `/financial-wellness/borrowing-money-explained/`, `/financial-wellness/building-credit-from-zero/`, `/financial-wellness/checking-savings-guide/`, `/financial-wellness/choosing-credit-repair-company/`.

Current indexation diagnosis from `indexation_status`:
- `Crawled - currently not indexed` by family:
  - review 600
  - state 68
  - city 53
  - financial wellness 25
  - blog 13
  - answers 11
  - money pages 8
  - other 1
- Manual GSC submissions must not be spent on review/city/state noise first. Use them on tools, course/learn, wellness, answers, and money pages.

GSC validation guidance:
- Yes, ask Google to validate the duplicate title/meta fixes from `SEO/Table - Duplicates.csv`.
- Yes, ask Google to validate the robots-blocked `/go/` fix after robots cleanup.
- Do not treat broad `Crawled - currently not indexed` as one validation bug; handle it by daily 10 manual submissions, API breadth, internal links, and page-level improvement/consolidation if a page remains excluded after recrawl.

## 2026-07-06 - Crawl integrity, GSC duplicates, and robots cleanup

Status: deployed, live-verified, and ready for GSC/SE Ranking validation.

Deploys:
- Legacy redirect/internal-link cleanup deployed to Cloudflare Worker version `38ac06ac-066e-4155-a329-7117ef0fa579`.
- Duplicate-meta snapshot cleanup deployed to Cloudflare Worker version `244b322b-297d-4496-9a17-6d525ffd2605`.
- Robots `/go/` cleanup deployed to Cloudflare Worker version `aa9fa260-5689-41e8-9d0e-99b5eace38b3`.

What changed:
- Parsed `/srv/BusinessOps/creditdoc/SEO/Table.csv`:
  - 1,000 rows: 964 `/review/`, 22 `/city/`, 9 `/browse/`, 4 `/compare/`, 1 `/categories/`.
  - 36 non-review legacy paths now have exact static redirects in `public/_redirects`.
  - Live verification after deploy: all 36 non-review legacy paths final-resolve to 200.
- Added middleware fallback redirects for legacy category/path variants.
- Changed `/search/?state=...` browse links to canonical `/state/<slug>/` links.
- Added shared lender review-link gating/fallback so cards/tables/compare pages do not push users/crawlers into unpublished review URLs.
- Parsed GSC duplicate export `/srv/BusinessOps/creditdoc/SEO/Table - Duplicates.csv`:
  - 71 rows: 57 `/review/`, 14 `/city/`.
  - Live validation after fixes: 0 duplicate title groups, 0 duplicate meta-description groups, 0 duplicate H1 groups across all 71 URLs.
- Fixed the only current rendered duplicate meta found by `scripts/seo_deep_audit.mjs`:
  - `/review/eagle-finance/`
  - `/review/eagle-loan/`
  - Updated review template overrides, lender JSON, and the static SE Ranking snapshot HTML files.
- Changed `robots.txt` so `/go/` is no longer robots-blocked. `/go/*` remains non-indexable via HTTP header `X-Robots-Tag: noindex, nofollow`, which lets Google see the noindex instead of reporting blocked-by-robots for discovered utility URLs.

Verification:
- `npm run build` passed after the redirect/internal-link changes.
- Postbuild checks passed: sitemap/robots conflicts, critical sitemap URLs, feed contract, rendered image alt contract, image filename contract.
- `node scripts/check_robots_contract.mjs` passed.
- `node scripts/check_sitemap_robots_conflicts.mjs` passed with no User-agent:* disallow rules to compare.
- `node scripts/seo_deep_audit.mjs` passed with `errors=0, warnings=0` across 2,875 rendered HTML pages and 25,129 sitemap URLs.
- Live `/robots.txt` shows no `/go/` disallow.
- Live `/go/advance-america/?source=check` returns 302 with `x-robots-tag: noindex, nofollow`.
- Live `/review/eagle-finance/` and `/review/eagle-loan/` return 200 with distinct titles and meta descriptions.

Important:
- No cron or publishing automation was stopped, paused, or disabled during this work.
- GSC validation can be requested for the duplicate-title/meta sample now. The robots-blocked `/go/` issue should clear after Google recrawls robots and the affected URLs.

## 2026-07-06 - SE Ranking 404 table diagnosis

Source checked: `/srv/BusinessOps/creditdoc/SEO/Table.csv` updated 2026-07-06 10:30 UTC.

Findings:
- CSV has 1,000 rows with only `URL` and `Last crawled`; it appears to be an exported SE Ranking issue bucket, not a full status table.
- Route-family split:
  - 964 `/review/` URLs
  - 22 `/city/` URLs
  - 9 `/browse/` URLs
  - 4 `/compare/` URLs
  - 1 `/categories/` URL
- Host duplicates exist: 159 duplicate paths from `creditdoc.co` vs `www.creditdoc.co` variants.
- Only 3 of the 1,000 reported paths are in the current generated sitemap:
  - `/review/power-financial/`
  - `/review/pioneer-appalachia/`
  - `/review/mattel/`
- None of the reported paths currently have static `dist/.../index.html` output.
- For `/review/` rows, about half have local lender JSON and half do not:
  - 484 rows have a matching `src/content/lenders/<slug>.json` row.
  - 480 review rows have no matching local lender JSON.
- Representative live checks confirm current real 404s for the reported review/city/compare/category paths, while known published review pages like `/review/prosper/` and `/review/deluxe-credit-solutions/` return 200.

Diagnosis:
- This is mainly review-directory crawl exposure, not a tools/answers/blog/wellness feed problem.
- SE Ranking is finding old or internally linked `/review/` URLs for providers that are not currently published/static/live. Some were likely generated historically from directory/listing data and later not included in the published review set.
- The city/browse rows are old full-state slugs, e.g. `/city/cedar-park-texas/`, while the live site uses abbreviation slugs such as `/city/cedar-park-tx/`. Some browse full-state URLs redirect correctly; others still 404 because no live category/city combination exists.
- `/categories/fix-my-credit/` is an old alias; live category is `/categories/credit-repair/`.
- The four `/compare/` rows are old comparison slugs that are not in the current generated comparison corpus.
- Separate small snippet with `/go/...` and `/search/?state=...`: live checks returned 200 after redirects. `/go/` is intentionally noindex/nofollow redirect utility; `/search/?state=Texas|Utah|Iowa` redirects to `/state/<state>/`.

Recommended fix order:
1. Remove/stop internal links to unpublished `/review/` pages, or route them to a safe category/city fallback when the review is not published.
2. Add redirect/alias handling for old full-state city and browse slugs to abbreviation slugs where an equivalent page exists.
3. Add alias redirect for `/categories/fix-my-credit/` to `/categories/credit-repair/`.
4. For the 3 sitemap-listed review 404s, either publish those review pages or remove them from sitemap injection immediately.
5. Treat old compare slugs as redirect candidates only if there is a current equivalent; otherwise leave 404/410 and stop internal links.

## 2026-07-06 - Feed health check and answer pipeline recovery

Status: all CreditDoc public/content feed checks are green as of 2026-07-06 10:28 UTC.

What was checked:
- Live `/rss.xml` and `/feed.xml`: both return 50 items; newest item is dated 2026-07-06.
- Required public surfaces: homepage, robots, llms, sitemap index, sitemap shard, search JSON, blog index, answers index, money page, representative answer page, and representative blog page all OK.
- Static HTML feed surfaces:
  - `/answers/`: 491 generated answer HTML pages passed title/meta/H1/canonical/content checks.
  - `/financial-wellness/`: 139 generated HTML pages passed title/meta/H1/canonical/content checks.
  - `/tools/`: 19 generated HTML pages passed title/meta/H1/canonical/content checks.
  - `/courses/`: 10 generated HTML pages passed title/meta/H1/canonical/content checks.
- Content audit preview: 0 issues; 12 city guides and 4 blogs created in the last 48 hours; course pages all OK.
- Blog/city feeds are running today. Wellness/comparison jobs were pending because their cron times had not yet arrived.

Fixes/actions:
- The answer feed was stale: `cluster_state.json` had last successful answer publish at 2026-06-19/21 while cron was only showing smoke-test dry runs before the scheduled 13:00 UTC job.
- Ran the answer publisher manually under the normal DB writer lock:
  `/srv/BusinessOps/tools/creditdoc_cluster_executor.py --apply`
- Published and pushed:
  `https://creditdoc.co/answers/can-you-transfer-a-credit-card-balance/`
- Verified the live page returns 200 and has:
  - title length 51
  - meta length 156
  - canonical `https://www.creditdoc.co/answers/can-you-transfer-a-credit-card-balance/`
  - static HTML in `dist/answers/can-you-transfer-a-credit-card-balance/index.html`
- Patched `/srv/BusinessOps/tools/cluster_pipeline_watchdog.py` so old historical failures before the latest successful publish do not keep the answer watchdog red forever. The watchdog now reports healthy after a new publish.
- Blog queue reserve was low at 9 pending against a 10 minimum. Refilled through the existing `creditdoc_blog.py` auto-refill path; queue is now 20 pending.

Verification after fixes:
- `creditdoc_content_engine_daily_verify.py --dry-run --allow-pending`: all OK, including blog queue reserve 20, answer queue reserve 674, wellness queue reserve 20, comparison queue reserve 355, and guardrail regression.
- `creditdoc_feed_continuity_watchdog.py`: all OK.
- `cluster_pipeline_watchdog.py`: healthy, DB 491 published / 2 draft.
- Latest repo commit after answer publish: `48f3d3705d DB export: 2 answers, 107 blog posts, 357 comparisons, 139 wellness guides, 19 categories (2026-07-06)`.

Notes:
- The only untracked repo file after this work is still `SEO/two-week-action-calendar/2026-07-06-day-08.md`; it was pre-existing/unrelated and was not touched.
- CreditDoc process rule remains: always read memory before CreditDoc work, update memory afterward, and push committed work whenever repo-tracked files change.

## 2026-07-03 - SE Ranking audit cleanup and static SEO verification

Status: code/build SEO cleanup completed, deployed, live-verified, and committed locally. Push to GitHub is blocked by invalid GitHub authentication on the VPS.

Process rule:
- For CreditDoc, finished work must be pushed after commit as a matter of process.
- Current exception: `git push origin cdm-rev-hybrid` failed on 2026-07-03 because the GitHub HTTPS token configured on `origin` is invalid; `gh auth status` also reports an invalid token; SSH auth is not configured.

What changed:
- Excluded `/linkedin-oauth-callback/` from generated sitemap while keeping the callback page noindex utility behavior.
- Fixed remaining short/duplicate title issues in generated pages:
  - `/sitemap/`
  - `/research/`
  - answer pages around balance transfers, small business loans, business line of credit variants, late payments, startups, and women-owned business loans.
  - wellness credit-score calculation pages.
- Added review SEO overrides for `/review/lookout/`, `/review/gain/`, `/review/sofi-bank/`, and `/review/sofi/` to fix short titles and duplicate H1s.
- Removed unreliable third-party favicon image fallback from review pages. Lender cards and top-picks fallbacks had already been removed.
- Extended `scripts/seo_deep_audit.mjs` to detect links with no visible text, image alt, aria-label, or title.

Verification:
- `npm run build` passed on 2026-07-03.
- Prebuild checks passed: content text integrity, robots contract, SSR sitemap parity.
- Postbuild checks passed: sitemap/robots conflicts, critical sitemap URLs, feed contract, image alt contract, and image filename contract.
- Image alt contract result: 11 source image tags and 14,548 rendered image tags include alt attributes.
- Image filename contract result: 14,439 public image filenames checked.
- `node scripts/seo_deep_audit.mjs` passed: 2,742 rendered HTML pages, 24,891 sitemap URLs, 0 errors, 0 warnings.
- Targeted check confirmed `/linkedin-oauth-callback/` is absent from generated XML sitemaps.
- Generated HTML confirms unique titles for the sitemap and credit-score wellness pages.
- Deployed through `/srv/BusinessOps/creditdoc/deploy.sh`.
- Cloudflare Worker Version ID: `0339224a-16ad-4954-b087-535c9be1760b`.
- Live checks confirmed 200 responses for representative `/answers/`, `/best/`, `/blog/`, `/financial-wellness/`, `/review/`, sitemap, homepage, CSS, and core route samples.

Next:
- Repair GitHub authentication on the VPS and push `cdm-rev-hybrid`; local branch is ahead of `origin/cdm-rev-hybrid` because push is currently blocked.
- Treat the next SE Ranking report as the external recrawl confirmation; local generated output is clean.

## 2026-07-02 - Static SEO migration: tools, answers, blog, wellness, and money pages

Status: static migration phase completed and build-verified for the ranking page families the user prioritized.

Commits:
- `7ace40d2d1 Improve SEO tooling and static answers`
- `1ba33061e5 Staticize editorial and money pages`
- `7781f144df Add traffic analysis audit export`

What changed:
- `/tools/*` kept static and strengthened with related-tool crawl links across the individual calculator/quiz/checklist pages.
- `/answers/` and `/answers/[slug]/` now build from local answer JSON through `getStaticPaths()` instead of runtime Supabase queries.
- `/blog/[slug]/` now builds statically from local blog data.
- `/financial-wellness/[slug]/` now builds statically from local wellness data.
- `/best/[slug]/` money pages now build statically from local listicle/lender JSON.
- Sitemap manual SSR injection was reduced so pages that Astro can discover statically are not duplicated through custom SSR sitemap SQL.
- Crawl-noise cleanup was applied: noindex pages now use `noindex, follow`, unreliable external favicon image fallbacks were removed, and internal sponsored CTAs no longer carry internal `nofollow`.

Build evidence:
- `npm run build` passed on 2026-07-02.
- Prebuild checks passed, including content text integrity, robots contract, and SSR sitemap parity.
- Postbuild checks passed: sitemap/robots conflicts, critical sitemap URLs, feed contract, rendered image alt contract, and image filename contract.
- Generated static HTML counts:
  - `/answers/`: 492 `index.html` files including the answer index.
  - `/tools/`: 19 `index.html` files including the tools index.
  - `/blog/`: 104 `index.html` files including the blog index.
  - `/financial-wellness/`: 140 `index.html` files including the wellness index.
  - `/best/`: 27 `index.html` files.
- No `export const prerender = false` remains in `src/pages/blog`, `src/pages/financial-wellness`, `src/pages/best`, `src/pages/answers`, or `src/pages/tools`.

Next:
- Do not re-argue whether these pages are static; they are now emitted as physical HTML during build.
- Next static work should be selective only: high-impression `/categories/`, `/credit-guide/`, and selected `/review/` pages after checking data freshness, sitemap size, and build-time impact.
- Keep `/search/`, `/api/*`, `/go/[slug]`, `/r/[slug]`, and OAuth/callback utility routes dynamic or non-indexable as appropriate.

## 2026-06-20 - Comparison guarded batch 004 deployed and live-verified

Status: fourth guarded comparison batch completed. The 20-candidate scan produced blockers on two pages, so only those two pages were edited, reviewed, committed, pushed, deployed, live-verified, and campaign-gated.

Commit:
- `6bdd97a52b fix: clean guarded comparison batch 004`

Deploy:
- Deployed through `/srv/BusinessOps/creditdoc/deploy.sh`.
- Cloudflare Worker Version ID: `ee4df2a5-8169-48fe-a690-40b94fd57a13`.
- Deploy smoke returned 200 for homepage, CSS, and core route families.

What changed:
- Edited only:
  - `credit-supreme-credit-repair-miami-fix-credit-fast-miami-fl-vs-safeport-law`
  - `american-consumer-credit-counseling-vs-creditorg`
- Changed only `summary`, `winner_reason`, and `seo_description`.
- Removed unsupported value/savings/recommendation language and unsafe accreditation framing.
- Preserved comparison value through pricing fields, review signals, service model, counseling scope, refund/program terms, and attorney/nonprofit context.
- No route, noindex, redirect, delete, sitemap, config, or template change.

Workpack:
- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Comparison_Batch_004_2026-06-20/`
- Live evidence:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Comparison_Batch_004_2026-06-20/live-check-after-deploy-20260620T1101Z/live_check_report.json`
- Campaign report:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Comparison_Batch_004_2026-06-20/campaign-report-after-deploy-20260620T1101Z/campaign_report.json`

Verification:
- Preflight on the 20-candidate manifest passed.
- Pre-edit claim safety found 5 blockers on 2 pages.
- Edited claim safety passed.
- Independent checker `Harvey` returned PASS before commit.
- `npm run test:comparison-batch` passed: 54/54.
- `git diff --check` passed.
- `npm run check:content-text-integrity` passed.
- `npm run check:comparison-db-freshness` passed: 345 JSON rows, 345 DB rows, 0 mismatches.
- `npm run comparison:batch:check` passed for the edited manifest with 2 pages and 0 blockers.
- `npm run comparison:live-check` passed: 2 live URLs returned 200, required sections present, blockers `[]`.
- Cumulative `comparison:campaign:report` across batches 001-004 passed: `ok: true`, `can_start_next_batch: true`, blockers `[]`.
- `comparison:campaign:can-continue` passed: `ok: true`, blockers `[]`.

Next:
- Campaign gate is open. Continue with the next difficult comparison batch only through the same guarded loop.

## 2026-06-20 - Comparison guarded batch 003 deployed and live-verified

Status: third guarded comparison batch completed. The 20-candidate scan produced only one raw blocker, so only one page was edited, reviewed, committed, pushed, deployed, live-verified, and campaign-gated.

Commit:
- `83ecf2238a fix: clean guarded comparison batch 003`

Deploy:
- Deployed through `/srv/BusinessOps/creditdoc/deploy.sh`.
- Cloudflare Worker Version ID: `012e4339-8052-4a6e-ba41-d77d368fb7df`.
- Deploy smoke returned 200 for homepage, CSS, and core route families.

What changed:
- Edited only `capital-fundings-vs-refijet`.
- Changed only `summary`, `winner_reason`, and `seo_description`.
- Removed unsupported concrete rate/APR and exact amount claims from the changed comparison copy.
- Preserved page value through use-case split, fee context, marketplace/refinance features, review signals, and investor-lending context.
- No route, noindex, redirect, delete, sitemap, or template change.

Workpack:
- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Comparison_Batch_003_2026-06-20/`
- Live evidence:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Comparison_Batch_003_2026-06-20/live-check-after-deploy-20260620T1050Z/live_check_report.json`
- Campaign report:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Comparison_Batch_003_2026-06-20/campaign-report-after-deploy-20260620T1050Z/campaign_report.json`

Verification:
- Preflight on the 20-candidate manifest passed.
- Pre-edit claim safety found exactly one blocker: unsupported rate claim on `capital-fundings-vs-refijet`.
- Edited claim safety passed.
- Independent checker `Averroes` returned PASS before commit.
- `npm run test:comparison-batch` passed: 54/54.
- `git diff --check` passed.
- `npm run check:content-text-integrity` passed.
- `npm run check:comparison-db-freshness` passed: 345 JSON rows, 345 DB rows, 0 mismatches.
- `npm run comparison:batch:check` passed for the edited manifest with 1 page and 0 blockers.
- `npm run comparison:live-check` passed: live URL returned 200, required sections present, blockers `[]`.
- Cumulative `comparison:campaign:report` across batches 001-003 passed: `ok: true`, `can_start_next_batch: true`, blockers `[]`.
- `comparison:campaign:can-continue` passed: `ok: true`, blockers `[]`.

Next:
- Campaign gate is open. Continue with the next difficult comparison batch only through the same guarded loop.
- Batch 003 showed that many high-risk inventory rows may already pass current source-backed checks; do not edit those unless a deterministic check or manual review finds a real issue.

## 2026-06-20 - Comparison guarded batch 002 deployed and live-verified

Status: second difficult comparison batch completed, independently reviewed, committed, pushed, deployed, live-verified, and campaign-gated.

Commit:
- `acc359f237 fix: clean guarded comparison batch 002`

Deploy:
- Deployed through `/srv/BusinessOps/creditdoc/deploy.sh`.
- Cloudflare Worker Version ID: `fef6e12d-6b01-4168-8d06-8144248f7be6`.
- Deploy smoke returned 200 for homepage, CSS, and core review/state/guide/answers/best/category/blog/wellness/brand routes.

What changed:
- Updated only 12 high-risk comparison records from the batch, not all 20 candidates.
- Preserved page value while removing unsupported winner/value/pricing/accreditation claims from `summary`, `winner_reason`, and `seo_description`.
- Corrected National Credit Fixers source wording so it no longer says BBB accreditation when current CreditDoc data only supports a stored BBB A+ rating field.
- Hardened the claim scanner so source-backed `$0` strings such as explicit `$0 down` lender pricing can pass, while default numeric zero still cannot support fabricated free-pricing claims.
- Added regression coverage for the source-backed zero-dollar pricing case.

Workpack:
- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Comparison_Batch_002_2026-06-20/`
- Final local/check folder:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Comparison_Batch_002_2026-06-20/check-edited-final/`
- Live production evidence:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Comparison_Batch_002_2026-06-20/live-check-after-deploy-20260620T1038Z/live_check_report.json`
- Campaign report:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Comparison_Batch_002_2026-06-20/campaign-report-after-deploy-20260620T1038Z/campaign_report.json`

Verification:
- Independent checker `Dewey` returned PASS before commit.
- `npm run test:comparison-batch` passed: 54/54.
- `node --check scripts/lib/comparison_batch_utils.mjs` passed.
- `git diff --check` passed.
- `npm run check:content-text-integrity` passed.
- `npm run check:comparison-db-freshness` passed: 345 JSON rows, 345 DB rows, 0 mismatches.
- `npm run comparison:batch:check -- --manifest .../manifest-edited.json --output-dir .../check-edited-final` passed with 12 pages and 0 blockers.
- `npm run comparison:live-check -- --manifest .../manifest-edited.json --output-dir .../live-check-after-deploy-20260620T1038Z` passed: 12/12 live URLs returned 200 with required comparison sections and 0 blockers.
- `npm run comparison:campaign:report` across batch 001 and batch 002 passed: `ok: true`, `can_start_next_batch: true`, blockers `[]`.
- `npm run comparison:campaign:can-continue` passed: `ok: true`, blockers `[]`.

Notes:
- The live checker still records review flags for the word `best` in rendered HTML, but these are non-blocking review flags, not live blockers.
- Continue only through the guarded loop. Do not bulk rewrite comparison pages.

## 2026-06-19 - Comparison first-20 rendered fact alignment

Status: first 20 comparison batch rendering/fact-safety work completed, independently reviewed, verified, and committed. Not deployed in this step.

### 2026-06-19 - Campaign gate follow-up

Status: first-20 local/final checker passed, campaign continuation is blocked by live production verification.

Additional commit:
- `2ff0c35d4c test: tighten comparison table claim scanner`

What changed:
- Tightened the comparison claim-safety checker after independent reviewer `Faraday` found that rendered side-by-side table prices could be swapped and still pass if both lender names appeared in the extracted table context.
- Added rendered-table-specific money checks for `Monthly Price` and `Setup Fee` rows so each value is checked against the correct lender column.
- Added regressions for sourced two-decimal monthly prices, legal names ending in punctuation such as `Inc.`, and swapped side-by-side table prices.
- This is checker/test code only. It does not change page content, DB rows, lender JSON, routes, indexability, redirects, or deploy state.

Verification:
- `npm run test:comparison-batch` passed: 53/53.
- `node --check scripts/lib/comparison_batch_utils.mjs` passed.
- `git diff --check` passed.
- `npm run check:content-text-integrity` passed.
- `npm run check:comparison-db-freshness` passed: 345 JSON rows, 345 DB rows, 0 mismatches.
- `npm run build` passed with prebuild and postbuild checks.
- Current local rendered first-20 report passed: 20 pages, 0 blockers.
- Independent reviewer `Faraday` first returned FAIL for the swapped-table gap, then PASS after the rendered table checker/regression was added.

Campaign artifacts:
- Batch final artifact dir:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Comparison_First_20_Batch_2026-06-19/final-campaign-batch-001/`
- Campaign report:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Comparison_First_20_Batch_2026-06-19/campaign-report/campaign_report.json`
- `comparison:campaign:can-continue` result: blocked.

Current blocker:
- Live production verifier fetched all 20 pages successfully with HTTP 200 and all required enrichment sections present.
- Live production claim-safety still failed with 15 blockers across 8 pages, so `can_start_next_batch` is false.
- Do not start the next comparison batch until production live verification passes or the live blockers are reviewed and resolved.
- Do not strip comparison-page value sections; local output already preserves the enriched sections and passes rendered checks.

Commits:
- `e0940e5526 fix: align comparison rendered facts`
- `42ab02e0f3 content: add wellness guides` (separate wellness cron content commit; not part of the comparison fix)

What changed:
- Preserved comparison-page value sections while aligning rendered facts across summary, profile cards, side-by-side table, research notes, and FAQ.
- Fixed monthly-price rendering when a provider has a real positive `pricing.monthly_price`; free tiers no longer hide the paid monthly value.
- Fixed monthly-price rendering when a provider has `monthly_price: 0` but paid tiers exist; the page now shows the lowest positive paid tier instead of "No monthly subscription listed."
- Fixed TransUnion/Experian credit-monitoring research copy so it uses bureau/monitoring service signals instead of stale credit-repair/counseling language.
- Fixed comparison source-fact extraction to prefer rendered `company_info` BBB fields over older top-level BBB fields.
- Added rendered/live claim scanning hardening so generated image metadata does not create false money-claim blockers.
- Added `scripts/check_content_text_integrity.mjs` and wired it into `prebuild`; it blocks narrative JSON control-character/currency corruption while exempting legacy top-level address control characters.
- Repaired corrupted American Consumer Credit Counseling profile text through the DB writer/export path:
  - `best_for`: restored `$3,000-$50,000`.
  - `diagnosis`: restored `$7/month` and `$3K-$50K`.

Important incident note:
- During the batch, the scheduled comparison generator cron committed and pushed `85fa250de5 Add 5 comparison pages`, which included the previously uncommitted comparison JSON changes plus 5 generated comparison rows.
- I did not rewrite history or reset this. The follow-up manual commits only cover the rendered-fact/checker/template/data-integrity fixes and the separate wellness cron output.

Verification:
- `npm run test:comparison-batch` passed: 50/50.
- `npm run check:content-text-integrity` passed.
- `git diff --check` passed.
- `node --check scripts/lib/comparison_batch_utils.mjs` passed.
- `node --check scripts/check_content_text_integrity.mjs` passed.
- `npm run check:comparison-db-freshness` passed: 345 JSON rows, 345 DB rows, 0 mismatches.
- `npm run build` passed after the final paid-tier fix.
- Prebuild checks passed: content text integrity, robots contract, SSR sitemap parity.
- Postbuild checks passed: sitemap/robots conflicts and critical sitemap URLs.
- Targeted rendered checks passed for:
  - `brigit-vs-advance-america-claymont`
  - `continental-credit-vs-cosmo-credit-repair`
  - `the-credit-repairmen-vs-cosmo-credit-repair`
  - `credit-supreme-credit-repair-miami--vs-cosmo-credit-repair`
  - `dovly-vs-wallethub`
  - `american-consumer-credit-counseling-vs-incharge-debt-solutions`
  - `transunion-vs-experian`
- Independent read-only reviewer `Dalton` initially failed the Dovly/WalletHub and Experian free-tier pricing issue, then passed after the final paid-tier fix and rebuild.

Repo state:
- After commits, the CreditDoc repo was locally clean before this memory/handoff update.
- `origin/cdm-rev-hybrid` still needed the two local commits pushed at this checkpoint.

Next:
- Push the new commits when ready.
- Do not deploy until release scope is reviewed.
- Continue first-20/campaign work only through the guarded loop: deterministic checks -> independent review -> campaign report -> can-continue gate.
- Keep the comparison pages rich; do not strip linked tools, blogs, courses, local pages, or research sections.

## 2026-06-19 - Supabase free-plan database size incident resolved

Status: CreditDoc Supabase database size reduced below the free-plan threshold without changing live content tables.

What happened:
- CreditDoc still uses Cloudflare Workers SSR with SQLite as the canonical write/source database and Supabase Postgres as the read-at-request mirror for runtime content.
- Supabase database size was `513 MB`.
- `public.audit_log` was `370 MB`; almost all bloat came from old `lenders UPDATE` audit rows storing full `old_data` and `new_data` JSON snapshots, including `body_inline`.

What was done:
- Archived the full `public.audit_log` table before pruning:
  `/srv/BusinessOps/backups/creditdoc_supabase_audit_cleanup/20260619T114841Z/public_audit_log_before_prune.dump`
- Verified archive checksum and `pg_restore --list`.
- Deleted only old audit rows matching:
  `table_name='lenders' AND operation='UPDATE' AND created_at < now() - interval '30 days'`.
- Deleted row count: `37,808`.
- Ran `VACUUM (FULL, ANALYZE) public.audit_log`.
- Updated `public.fn_audit_row()` so future audit snapshots strip `body_inline` and keep compact `body_inline_present` / `body_inline_changed` markers instead of duplicating full content blobs.
- Saved rollback function definition:
  `/srv/BusinessOps/backups/creditdoc_supabase_audit_cleanup/20260619T114841Z/fn_audit_row_before_body_inline_strip.sql`

Verification:
- Final Supabase database size: `175 MB`.
- Final `public.audit_log` size: `32 MB`.
- Remaining audit rows: `5,815`.
- Remaining old lender update rows matching the prune predicate: `0`.
- Rollback-transaction trigger test on `lexington-law` produced a compact audit row of `1132 bytes`, with no `body_inline` stored; transaction was rolled back.
- Live route checks returned `200` for homepage, Lexington Law review, Crushing on Credit review, answers index, Amarillo city guide, known comparison `credit-saint-vs-sky-blue-credit`, sitemap index, and search state URL.
- Independent debugger agent reviewed the approach before write/reclaim work and found no evidence that live rendering reads `public.audit_log`.

Important:
- Do not confuse this with TraderTrac. This incident was CreditDoc project `pndpnjjkhknmutlmlwsk`; the `lenders` table is CreditDoc-specific.
- Do not reintroduce full `body_inline` snapshots into Supabase audit logging unless the DB plan/budget has changed.

## 2026-06-19 - Comparison live verifier and campaign gate

Status: Task 9 and Task 10 guardrails implemented, independently reviewed, verified, committed, and repo-clean after docs handoff.

Code commit:
- `e2824fae5f feat: add comparison live and campaign gates`

What changed:
- Added `scripts/check_live_comparison_batch.mjs`.
- Added `scripts/write_comparison_campaign_report.mjs`.
- Added `scripts/check_comparison_campaign_can_continue.mjs`.
- Added npm scripts:
  - `comparison:live-check`
  - `comparison:campaign:report`
  - `comparison:campaign:can-continue`
- Live verifier fetches each selected live `/compare/<slug>/` URL, requires HTTP 200, requires the three enrichment sections, and scans live HTML against the same source-backed claim rules.
- Campaign reporter writes `campaign_report.json` and `campaign_report.md`.
- Continue gate fails closed when the latest batch failed, final checker did not pass, live verifier failed, cumulative report has blockers, campaign reached planned batch count, or repo is dirty.
- Fixed a scanner false positive by allowing dollar amounts found inside current source pricing strings, such as Credit Saint's `$195` setup-fee note.

Verification:
- Independent read-only checker agent `Ampere` returned PASS.
- `npm run test:comparison-batch` passed: 46/46.
- `node --check` passed for all new/changed comparison gate scripts.
- `git diff --check` passed.
- `npm run check:comparison-db-freshness` passed: 340 JSON rows, 340 DB rows, 0 mismatches.
- Empty-manifest live-check smoke passed.
- Campaign report and can-continue CLI smokes passed with clean temporary status.
- Real live smoke for `credit-saint-vs-sky-blue-credit` returned 200, confirmed all enrichment sections, and passed with no blockers after the source-string `$195` fix.
- Full guarded batch check smoke passed after the scanner fix and produced the complete evidence bundle.

Important:
- These scripts do not edit content pages, DB rows, lender JSON, routes, redirects, indexability, sitemap logic, or deploy state.
- They only write explicit report files in the chosen output directory.
- Campaign loops must run `comparison:campaign:can-continue`; the report writer alone is not the hard stop.

## 2026-06-19 - Comparison batch runner guardrail orchestrator

Status: Task 8 guardrail runner implemented, independently reviewed, verified, committed, and repo-clean. Not deployed; this is operator tooling only.

Code commit:
- `9861eb5159 feat: add guarded comparison batch runner`

What changed:
- Added `scripts/run_comparison_batch_guarded.mjs`.
- Added npm scripts `comparison:batch:preflight` and `comparison:batch:check`.
- Added shared `buildComparisonPreflightReport(...)` helper and unit coverage.
- Runner writes report/status artifacts only. It does not edit comparison records, lender JSON, page templates, routes, DB rows, redirects, or indexability.
- Preflight mode runs DB freshness, source fact extraction, scope preview, and preflight status.
- Check mode reruns preflight, enforces selected-slug/allowed-field scope, runs raw claim safety, runs `npm run build`, scans rendered output, and invokes the existing review-packet generator so both `review_packet.json` and `review_packet.md` are produced.

Verification:
- Independent read-only checker agent `Popper` returned PASS.
- `npm run test:comparison-batch` passed: 42/42.
- `node --check scripts/run_comparison_batch_guarded.mjs` passed.
- `git diff --check` passed.
- `npm run check:comparison-db-freshness` passed: 340 JSON rows, 340 DB rows, 0 mismatches.
- Selected-page preflight smoke passed for `continental-credit-vs-cosmo-credit-repair`.
- Selected-page check smoke failed intentionally at scope gate with `selected slug not changed: continental-credit-vs-cosmo-credit-repair` and did not run build/render/review-packet steps.
- Empty-manifest check smoke passed and wrote the complete bundle, including `review_packet_command_report.json`, `review_packet.json`, and `review_packet.md`.

Repo state:
- `git status --short --untracked-files=all` returned clean after commit.

Next:
- Do not start 20-page content batches yet. Next implementation step is the final checker result/evidence gate and campaign report wrapper so each batch can stop after deterministic checks, independent review, final checker pass, and cumulative reporting.

## 2026-06-17 - Phase 1 comparison pricing safety patch slice 1

Status: first live-page comparison cleanup slice implemented, build-verified, committed, deployed, and followed by one-record orphan cleanup.

What changed:
- Patched 9 first-batch comparison records in `src/content/comparisons.json` through `CreditDocDB.add_comparison(..., updated_by='founder')` and content export.
- Replaced winner-led/current-fact-heavy comparison summaries with stored-field comparison language.
- Corrected visible BBB/source-field contradictions on the first-batch pages.
- Kept listed pricing values where they came from current CreditDoc source fields; did not convert missing/zero pricing into "free".
- No pages were noindexed or bulk removed.

Verification:
- Independent read-only debug agent reviewed the first batch and confirmed raw-data cleanup was warranted for the 9 live pages.
- `npm run build` passed.
- Prebuild checks passed: robots contract and SSR sitemap parity.
- Postbuild checks passed: sitemap/robots conflict check and critical URL check.
- Rendered HTML scan for the 9 patched compare pages found no targeted unsafe phrases: `money-back guarantee`, `wins`, `superior value`, `better value`, `clear pick`, `safer choice`, `versus no BBB rating`, `no BBB rating`, or `red flag`.
- Deployed 2026-06-18 through `./deploy.sh`.
- Cloudflare Worker Version ID: `4f189f5a-1b95-4b74-acd4-c55866f8f9d4`.
- Deploy smoke checks returned 200 for homepage, CSS, and 11 core SSR route families.
- Targeted live checks: orphan `/compare/kikoff-vs-a-better-way-auto-brokerage/` returned 404; sampled patched comparison pages returned 200 with no targeted unsafe phrase hits.

Remaining Phase 1 follow-up:
- `kikoff-vs-a-better-way-auto-brokerage` was archived and removed on 2026-06-18 through founder-only `CreditDocDB.delete_comparison(...)`, then exported from `src/content/comparisons.json`.
- Local SQLite, Supabase, and exported JSON all show zero rows for the orphan slug after cleanup.
- Next Phase 1 step is the next 10 highest-risk live 200 comparison pages from the inventory.

## 2026-06-18 - Phase 1 comparison pricing safety patch slice 2

Status: second live-page comparison cleanup slice implemented, independently reviewed, build-verified, committed, deployed, and live-verified.

What changed:
- Patched the next 10 highest-risk live 200 comparison records from `comparison_risk_inventory_2026-06-17.csv`.
- Updated `summary`, `winner_reason`, and `seo_description` fields through `CreditDocDB.add_comparison(..., updated_by='founder')` and content export.
- Preserved useful stored facts: listed monthly/setup prices, refund-term notes, BBB context, review fields, product/use-case differences, and service features.
- Removed derived savings math, winner/value verdicts, old guarantee wording, unsupported BBB certainty, and strong reliability/trust conclusions.
- Changed `CreditDocDB.add_comparison(...)` from `INSERT OR REPLACE` to an SQLite upsert so comparison updates preserve row identity and avoid JSON export reorder churn.

Patched records:
- `credit-blueprint-vs-continental-credit`
- `credit-saint-vs-the-credit-people`
- `ecreditadvisor-vs-xperia-credit-solutions`
- `credit-blueprint-vs-elevate-my-scores`
- `xperia-credit-solutions-vs-national-credit-care`
- `greenlight-financial-vs-self-credit-builder`
- `ecreditadvisor-vs-credit-blueprint`
- `credit-blueprint-vs-xperia-credit-solutions`
- `credit-saint-vs-xperia-credit-solutions`
- `the-credit-repairmen-vs-national-credit-care`

Verification:
- Independent read-only debug agent reviewed the 10 candidates and agreed cleanup was warranted without deleting useful sourced content.
- Row-id checks confirmed the DB upsert preserved record identity during the patch.
- Raw-record scan across `summary`, `winner_reason`, and `seo_description` found no targeted unsafe phrases after patch.
- `npm run build` passed.
- Prebuild checks passed: robots contract and SSR sitemap parity.
- Postbuild checks passed: sitemap/robots conflict check and critical URL check.
- Rendered `dist/compare/.../index.html` scan for the 10 patched pages found no targeted unsafe phrase hits.
- Deployed 2026-06-18 through `./deploy.sh`.
- Cloudflare Worker Version ID: `e3ebb3d1-1235-4b83-a47f-de94e35d0f86`.
- Deploy smoke checks returned 200 for homepage, CSS, and 11 core SSR route families.
- Targeted live checks: all 10 patched comparison pages returned 200 and had no targeted unsafe phrase hits.

Remaining Phase 1 follow-up:
- Continue with the next 10 highest-risk remaining live 200 comparison pages from the inventory.
- Keep small batches only; do not bulk rewrite comparison history.
- Continue preserving sourced prices and facts while avoiding fabricated current-price, guarantee, winner, or trust verdict language.

## 2026-06-18 - Phase 1 comparison pricing safety patch slice 3

Status: third live-page comparison cleanup slice implemented, independently reviewed, build-verified, committed, deployed, and live-verified.

What changed:
- Patched the next 10 highest-risk live 200 comparison records from `comparison_risk_inventory_2026-06-17.csv`.
- Updated `summary`, `winner_reason`, and `seo_description` fields through `CreditDocDB.add_comparison(..., updated_by='founder')` and content export.
- Preserved useful stored facts: listed prices, setup fees, APR/rate examples, return/refund terms, BBB/profile context, review fields, product mechanics, and use-case distinctions.
- Removed derived savings claims, value verdicts, old guarantee wording, unsupported BBB certainty, negative trust conclusions, and payday-lender language that went beyond stored fields.
- No pages were noindexed, redirected, removed, or bulk rewritten.

Patched records:
- `the-credit-pros-vs-safeport-law`
- `ace-cash-express-new-orleans-la-vs-ace-cash-express`
- `advance-america-oklahoma-city-vs-ace-cash-express`
- `ace-cash-express-miami-fl-vs-advance-america-missouri-city`
- `apex-credit-fix-vs-credit-blueprint`
- `ecreditadvisor-vs-elevate-my-scores`
- `kikoff-vs-self-credit-builder`
- `capital-fundings-vs-refijet`
- `dovly-vs-the-credit-bureau`
- `the-credit-repairmen-vs-elevate-my-scores`

Verification:
- Independent read-only debug agent reviewed the 10 candidates and agreed cleanup was warranted without deleting useful sourced content.
- Raw-record scan across `summary`, `winner_reason`, and `seo_description` found no targeted unsafe phrases after patch.
- `npm run build` passed.
- Prebuild checks passed: robots contract and SSR sitemap parity.
- Postbuild checks passed: sitemap/robots conflict check and critical URL check.
- Rendered `dist/compare/.../index.html` scan for the 10 patched pages found no targeted unsafe phrase hits.
- Deployed 2026-06-18 through `/srv/BusinessOps/creditdoc/deploy.sh`.
- Deploy smoke checks returned 200 for homepage, CSS, and 11 core SSR route families.
- Targeted live checks: all 10 patched comparison pages returned 200 and had no targeted unsafe phrase hits.

Remaining Phase 1 follow-up:
- Continue with the next 10 highest-risk remaining live 200 comparison pages from the inventory.
- Keep small batches only; do not bulk rewrite comparison history.
- Continue preserving sourced prices and facts while avoiding fabricated current-price, guarantee, winner, or trust verdict language.

## 2026-06-16 - Feed audit comparison guardrail patch

Status: future-prevention patch implemented and locally verified; not deployed in this session.

What changed:
- Patched comparison generator source shaping in root tools and `tools/live_ops`.
- Future comparison prompts now strip numeric/current-fact free text from pros, cons, tier features, and descriptions.
- Structured CreditDoc, Google, and BBB ratings remain available per lender.
- Missing/zero monthly/setup price now renders as "Pricing: Not listed in current CreditDoc source data".
- Patched guardrails so side-by-side comparison sentences are split by clause before entity-value attribution.
- Patched BBB canonicalization so `BBB Rating: A+` and `BBB A+ rating` match.
- Patched repair prompt to ask for one-company-at-a-time fact sentences on comparison pages.

Verification:
- `python3 /srv/BusinessOps/tests/test_creditdoc_comparison_generator.py` passed.
- `python3 /srv/BusinessOps/tools/test_creditdoc_content_guardrails.py` passed.
- `python3 /srv/BusinessOps/creditdoc/tools/live_ops/test_creditdoc_content_guardrails.py` passed.
- `python3 -m py_compile ...` passed for changed Python files.
- `python3 /srv/BusinessOps/tools/creditdoc_comparison_generator.py --dry-run --count 5` returned the same next 5 queue pairs without writing.
- Prompt-source inspection for those 5 pairs returned `numeric_free_text_leaks=[]`.

Do not bulk rewrite historical comparisons. A scan found 309 existing comparison records with current-fact language (`$`, APR, percentages, or origination-fee terms). Build a reviewed workpack and remediate in small batches only.

Remaining feed follow-ups:
- `kikoff-vs-a-better-way-auto-brokerage` exists in DB/content but live route is 404 because lender `a-better-way-auto-brokerage` has no lender JSON.
- Wellness sitemap parity: `personal-loan-application-checklist` and `personal-loan-interest-how-calculated` are live 200 but absent from the sitemap during the check.
- Priority GSC Indexing API is currently healthy; latest log showed successful Google pushes Jun 10-14 and no URLs to push Jun 15-16.

## 2026-06-05 — SEO Title/Meta Stability Rule

**Operating rule:** CreditDoc titles and meta descriptions are now treated as
stable SEO assets. Do not rewrite them merely because a model suggests a nicer
variant.

Only change a title or meta description when one of these is true:

- Jammi explicitly asks for title/meta work on that page or batch.
- There is a verified defect: wrong entity, wrong location/category, broken
  wording, hallucinated claim, unsupported current fact, duplicate title at
  scale, missing canonical metadata, or a clear truncation/formatting problem.
- GSC shows measured underperformance after a real settling period, normally
  21-28 days after the last deployed title/meta change.

For normal SEO work, prioritize indexability, sitemap/robots health, internal
links, content quality, route health, publishing/index submission, and GSC
measurement. Do not make Google relearn page titles repeatedly without a
specific reason.

## 2026-06-05 — Guardian / Lender JSON Dirty-Tree Fix

**Root cause:** the daily answers engine exported protected lender JSON using
the public DB export shape, then the hourly CreditDoc Guardian compared those
files against the raw DB blob checksum and rewrote four protected files back to
the legacy/raw shape. The churn was serialization-only: `last_engine_run`
present/absent and `brand_slug: null` present/absent.

**Fix:** `tools/creditdoc_guardian.py` now normalizes protected-profile drift
checks before comparing checksums. It ignores DB-only export-excluded fields and
treats missing `brand_slug` the same as `brand_slug: null`. This keeps Guardian
protecting real DB/content drift without dirtying Git for bookkeeping shape
differences.

**Regression coverage:** `tests/test_guardian_public_export.py` verifies both
public-export JSON and legacy operational JSON are treated as matching when the
only differences are those serialization fields.

## 2026-06-05 — Quarantine Cleanup / 404 Fix / Dump-Lane Redirects

**Status: deployed, archived, and live-verified.**

Workpack:

- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_SEO_Tomorrow_Startpack_2026-06-04/`

Files created:

- `quarantine_decision_plan_2026-06-05.csv`
- `quarantine_dump_archive_batch_2026-06-05.csv`
- `quarantine_dump_archive_db_updates_2026-06-05.csv`
- `quarantine_dump_archive_final_live_status_2026-06-05.csv`

What happened:

- Audited 80 quarantine candidates against DB and live production URLs.
- Classification result:
  - 7 `resolved_redirect_monitor`
  - 3 `resolved_archived_redirect_monitor`
  - 1 `manual_keep_candidate_validate_sources`
  - 4 `manual_review_weak_or_missing_website`
  - 35 `chain_or_money_services_systematic`
  - 19 `optimize_later_lower_priority`
  - 8 `likely_dump_auto_or_title`
  - 3 `likely_dump_unrelated_or_low_priority`
- Fixed `credit-repair-outfit-philadelphia` from a live 404 to a controlled
  `pending_approval` noindex source-check page. Also cleared the wrong
  `creditrepair.com` website reference and replaced generated/rating copy with
  neutral held-for-review copy through the DB API.
- Added review-route redirects for 11 clear dump-lane pages:
  auto-title, pawn, and unrelated cargo/pawn entries.
- Deployed redirect patch through `/srv/BusinessOps/creditdoc/deploy.sh`.
- Archived/noindexed the 11 dump-lane DB rows after redirects were live.
- Cleared stale rating fields from `credit-repair-outfit-philadelphia` after
  live verification found an old `5.0/5` pro still rendering.

Verification:

- `npm run build` passed after the redirect patch.
- `credit-repair-outfit-philadelphia` live check returned HTTP 200, canonical,
  `noindex=true`, no wrong `creditrepair.com` website reference, and no stale
  `5.0/5`/high-rating claim.
- Final live sweep: all 11 dump-lane review URLs return 302 redirects to their
  category destinations.
- Deploy script passed build, Cloudflare deploy, cache purge, and smoke routes.
- Cloudflare Worker version: `330751c3-7419-4e7d-8844-e6624d940084`.

Next:

- Continue the quarantine plan with the 35 money-transfer/check-cashing chain
  pages as a systematic chain-template lane, not one-off rewrites.
- Keep the 4 weak/manual pages noindexed unless a real provider-owned source is
  found.

## 2026-06-05 — Linkable Asset Expansion Plan

**Status: planning package created; no site pages changed or deployed.**

Jammi approved the concept of expanding CreditDoc's backlink/linkable-asset
library, with a hard rule: nothing gets deleted, discarded, overwritten,
removed, replaced, or cleaned up without express approval.

Project folder:

- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Linkable_Assets_Plan_2026-06-05/`

Files:

- `README.md`
- `LINKABLE_ASSETS_IMPLEMENTATION_PLAN_2026-06-05.md`
- `asset_matrix_2026-06-05.csv`

Memory copy:

- `/root/.claude/projects/-srv-BusinessOps/memory/creditdoc_linkable_assets_plan_2026-06-05.md`

Plan summary:

- Keep all existing backlink outreach, prospect lists, reports, and assets.
- Do not rebuild existing assets such as the credit report checklist, debt
  templates, borrowing power quiz, credit score simulator, debt payoff
  calculator, or research reports.
- First recommended build:
  `/resources/loan-approval-readiness-toolkit/` and printable version.
- First recommended attached tool:
  `/tools/loan-denial-reason-checker/`.
- Additional planned assets:
  business loan readiness score, MCA repayment calculator, bank statement cash
  flow calculator, credit denial action checklist, and state consumer credit
  regulator directory.
- Menu placement is documented: tools surface through existing top-nav
  `/tools/`; public resources surface through `/resources/`; no new top-level
  Resources nav should be added unless Jammi approves.
- SEO titles, meta descriptions, schema types, internal links, hub placement,
  outreach targets, and verification requirements are all specified in the plan.

Next:

- Before implementing any asset, search for duplicate routes/names again and
  check the worktree because another agent may be active.
- Implement Phase 1 only first unless Jammi approves a larger build batch.

## 2026-06-05 — GSC-Visible Review Page Upgrade Batch 1

**Status: first 13-page batch audited; 11 pages changed or explicitly decided; all 13 live-verified.**

Workpack:

- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_SEO_Tomorrow_Startpack_2026-06-04/`

Files created:

- `first_batch_live_audit_2026-06-05.csv`
- `phase_2_3_first_safe_updates_2026-06-05.csv`
- `phase_3_rating_claim_metadata_fixes_2026-06-05.csv`
- `phase_3_remaining_page_decisions_2026-06-05.csv`
- `first_batch_final_live_status_2026-06-05.csv`

What changed:

- Added DB-backed `seo_title` and neutral, factual `meta_description` updates for:
  `velnor-credit-repair-san-diego`, `crisdon-credit-repair`,
  `savage-squad-credit`, `credit-pros`, `dc-lending`,
  `lakehills-commercial-lending`, `capdeck-business-loans-san-jose`,
  `cash-express-of-mwc`, `loandepot-new-york`, `bay-area-loan`.
- Removed unverifiable rating/loan-amount wording from the live metadata for:
  `capdeck-business-loans-san-jose`, `cash-express-of-mwc`,
  `loandepot-new-york`, `bay-area-loan`.
- Resolved `nanakuli-housing-corporation` stale DB mismatch:
  `review_status` moved from `draft` to `published`, with neutral title/meta.
- Left `consumer-credit-counseling-burlingame` unchanged because it already has
  usable metadata, healthy internal links, and prior April chain-rewrite work.
- Held `credit-repair-specialists` for source validation/drop decision because
  the stored source is a Super Lawyers attorney directory, not a clean direct
  finance/provider website.

Verification:

- DB writes used `CreditDocDB.update_lender(... updated_by='founder' ...)`.
- Audit log contains the expected field-level entries for every changed page.
- Protected flags stayed unchanged.
- Final Googlebot-style production sweep: all 13 batch URLs returned HTTP 200,
  canonical `/review/<slug>/`, and no `noindex`.
- No lender JSON export was run and the repo worktree remained clean.

Next:

- Use `first_batch_final_live_status_2026-06-05.csv` as the baseline for this
  batch.
- Continue with the next GSC-visible unworked review pages, but keep
  `credit-repair-specialists` in a source-validation/drop lane until the founder
  decides whether it belongs on CreditDoc.

## 2026-06-04 — SEO Tomorrow Startpack / Avoid Duplicate Review Work

**Status: prepared and saved to project memory.**

Built a consolidated SEO startpack for the next review-page CTR/indexing push:

- Project folder:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_SEO_Tomorrow_Startpack_2026-06-04/`
- Memory copy:
  `/root/.claude/projects/-srv-BusinessOps/memory/creditdoc_seo_tomorrow_startpack_2026-06-04.md`

Files:

- `README.md`
- `already_worked_review_slugs.csv`
- `next_optimize_candidates_unworked.csv`
- `tomorrow_first_batch_candidates.csv`
- `quarantine_candidates_need_decision.csv`
- `non_review_zero_click_candidates_latest.csv`

Summary:

- Found **1,610** review slugs with prior work/decisions from the May 22/23
  review rollout, Vigo repair, noindex review, and sitewide upgrade memory.
- Found **196** slugs from prior review metadata update batches.
- Found **45** Vigo chain-repair slugs.
- Found **1,374** noindex/drop/reinstate decision slugs.
- From the June 2 traffic/ranking workpack, only **13** optimize candidates
  remain unworked after excluding prior-work slugs.
- The suggested first batch for the next session is the 13-row
  `tomorrow_first_batch_candidates.csv`.
- The 80-row `quarantine_candidates_need_decision.csv` must not be optimized
  blindly; those need keep/dump decisions first.

First batch starts with:

- `velnor-credit-repair-san-diego`
- `crisdon-credit-repair`
- `savage-squad-credit`
- `credit-repair-specialists`
- `dc-lending`
- `consumer-credit-counseling-burlingame`
- `credit-pros`
- `lakehills-commercial-lending`
- `capdeck-business-loans-san-jose`
- `cash-express-of-mwc`

Tomorrow rule: check `already_worked_review_slugs.csv` before editing any GSC
candidate; do not redo Marco's, Vigo chain repair, Phase 1 held pages, or prior
metadata batches unless fresh GSC evidence shows a new issue.

Execution plan now saved:

- Repo plan:
  `/srv/BusinessOps/creditdoc/docs/plans/2026-06-04-creditdoc-seo-review-sequence.md`
- Project handoff:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_SEO_Tomorrow_Startpack_2026-06-04/SEO_REVIEW_SEQUENCE_PLAN_2026-06-04.md`
- Memory copy:
  `/root/.claude/projects/-srv-BusinessOps/memory/creditdoc_seo_review_sequence_plan_2026-06-04.md`

Plan sequence:

1. Reload context and duplicate-work guard.
2. Audit all 13 first-batch pages live before editing.
3. Edit the safest credit-repair pages first.
4. Edit non-credit-repair pages only after source/claim validation.
5. Classify quarantine rows into keep/dump/chain-systematic lanes.
6. Log indexing and measure after fresh GSC data.

## 2026-06-04 — New Blog/Wellness Metadata QA

**Status: live-verified and committed.**

Checked the new June 4 blog pages and June 3 wellness pages for live rendered
SEO title, meta description, canonical, and HTTP status:

- `/blog/are-credit-score-checks-free/`
- `/blog/are-credits-negative/`
- `/financial-wellness/couples-money-management/`
- `/financial-wellness/credit-score-car-insurance/`

Fixes:

- Tightened `/blog/are-credit-score-checks-free/` SEO title from 61 chars to
  49 chars.
- Tightened `/blog/are-credits-negative/` meta description from 158 chars to
  131 chars.
- Updated both `src/content/blog-posts.json` and the `blog_posts` DB row through
  `CreditDocDB.add_blog_post()`, which revalidated the affected blog slugs.
- Patched `/srv/BusinessOps/tools/creditdoc_blog.py` so generated blog metadata
  is normalized after generation: title <=55, description <=140, SEO title
  <=58, SEO description <=155.

Verification:

- Live Googlebot checks returned HTTP 200 for all four URLs with correct
  canonical URLs and title/meta lengths.
- `npm run build` passed, including robots contract, SSR sitemap parity, Astro
  build, and sitemap/robots postbuild check.
- `/srv/BusinessOps/tools/creditdoc_smoke_test.py` passed 10/10 at 08:42 UTC.
- Daily content verifier passed with later UTC jobs correctly marked pending.

Commit:

- `54674b4ebb fix: tighten new blog metadata`

## 2026-06-03 — Daily GSC Progress Calendar

**Status: active.**

Added a daily CreditDoc GSC progress calendar using the correct GSC domain
property: `sc-domain:creditdoc.co`.

Files:

- Script: `/srv/BusinessOps/tools/creditdoc_gsc_progress_calendar.py`
- JSONL history: `/srv/BusinessOps/CreditDoc_SEO/gsc_progress_calendar.jsonl`
- Markdown calendar:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_GSC_Progress_Calendar_2026-06.md`
- Cron log: `/srv/BusinessOps/logs/creditdoc_gsc_progress_calendar.log`

Cron:

- `5 10 * * * /srv/BusinessOps/.venv/bin/python3 /srv/BusinessOps/tools/creditdoc_gsc_progress_calendar.py >> /srv/BusinessOps/logs/creditdoc_gsc_progress_calendar.log 2>&1`

The script is idempotent by `run_date`, so rerunning the same day replaces the
same row rather than duplicating the calendar entry. It logs latest complete
7-day and 28-day GSC traffic, week-over-week change, and page-family breakdown
for review, city guides, answers, blogs, wellness, best, compare, state, and
other page groups.

Baseline written on 2026-06-03:

- GSC complete through: 2026-06-01
- Latest 7d: 2 clicks / 11,552 impressions
- Latest 28d: 13 clicks / 35,443 impressions
- Leading family: review pages

Verification:

- Manual run completed and wrote the JSONL + markdown calendar.
- `--print-only` returned valid JSON.
- `verify_crons.sh` passed: `OK: All 59 expected crons present`.

## 2026-06-02 — Search State Query Robots/GSC Fix

**Status: deployed, live-verified, and build-guarded.**

Jammi flagged that the correct GSC domain property still showed these URLs as
`Blocked by robots.txt`:

- `https://www.creditdoc.co/search/?state=Texas`
- `https://www.creditdoc.co/search/?state=Utah`
- `https://www.creditdoc.co/search/?state=Iowa`

Root cause: old state-filtered search parameter URLs had been crawled by Google
as `/search/?state=...` pages. Current live robots.txt allows crawling, but GSC
URL Inspection API still reports the old May 22-24 crawl state until Google
recrawls them.

Code fix:

- `src/pages/search.astro` now redirects state-only search filters with a 301 to
  the proper state landing page:
  `/search/?state=Texas` -> `/state/texas/`, etc.
- Clean `/search/` is no longer unconditional `noindex`.
- Remaining filtered search pages still use page-level `noindex` via
  `noindex={hasSearchFilters}`.
- `scripts/check_robots_contract.mjs` now fails prebuild if the state-filter
  redirect or conditional search noindex policy is removed.

Deployment:

- Deployed via `/srv/BusinessOps/creditdoc/deploy.sh`.
- Cloudflare Worker version:
  `0a984615-d8e2-48a1-abfd-a5cc24a9afcb`.

Verification:

- `npm run build` passed after the route fix.
- Deploy script passed build, Cloudflare deploy, cache purge, and live route
  checks.
- Second `npm run build` passed after adding the regression guard.
- Live Googlebot checks:
  - Texas state-query URL: `301 /state/texas/` then `200`.
  - Utah state-query URL: `301 /state/utah/` then `200`.
  - Iowa state-query URL: `301 /state/iowa/` then `200`.
  - Clean `/search/`: `200`.
- Live meta checks show `/search/` has canonical
  `https://www.creditdoc.co/search/` and no robots noindex tag; state-query
  redirects resolve to state-page canonicals.

GSC caveat:

- URL Inspection API still shows the three state-query URLs as
  `Blocked by robots.txt` with last crawl dates from May 22-24.
- This is stale Google crawl data, not the current live response.
- Do not tell Jammi to validate the GSC issue again until a fresh inspection or
  recrawl no longer shows the stale blocked state.

## 2026-06-02 — Generator Hallucination / Pricing Guardrails

**Status: patched and function-tested.**

Added operational guardrails to the active CreditDoc content creation scripts in
`/srv/BusinessOps/tools` so generated pages fail before publishing if they
invent current provider prices, fees, APRs, BBB ratings, Google ratings, star
ratings, guarantees, approval odds, or other certainty claims.

Patched active generators:

- `creditdoc_content_guardrails.py` added as the shared detector.
- `creditdoc_cluster_executor.py` now hard-fails answer pages with unsupported
  current provider facts or certainty claims, alongside the first-person claim
  gate.
- `templates/cluster_asset_prompt.md` now explicitly forbids invented current
  provider facts.
- `creditdoc_blog.py`, `creditdoc_wellness_generator.py`, and
  `creditdoc_city_guide_generator.py` now instruct the model not to invent
  provider facts and reject unsafe output before save.
- `creditdoc_comparison_generator.py` now rejects any dollar amount, rating, or
  guarantee that does not appear in the supplied source lender data.

Verification:

- Direct guardrail test: invented `$99/month`, `4.9/5 Google rating`, and
  `guaranteed approval` fails.
- Direct guardrail test: the same `$99` and `4.9/5` pass when supplied as source
  lender data.
- Legal/educational context such as a `36% MAPR` statutory cap passes.
- Answer compliance function forces unsafe generated answer content below the
  publish threshold.
- Comparison generator accepts sourced facts and rejects invented facts.
- `python3 -m py_compile` passed for all patched generator scripts.

## 2026-06-02 — Four Answer Pages First-Person Claim Fix

**Status: committed, pushed, deployed, DB-updated, cache-purged, and live-verified.**

Removed fabricated first-person/lived-experience anecdotes from these answer
pages and replaced them with neutral hypothetical examples:

- `/answers/can-you-get-a-business-loan-with-bad-credit/`
- `/answers/business-loan-rates-fees-explained/`
- `/answers/debt-to-income-ratio-explained/`
- `/answers/equipment-financing-explained/`

Important source-of-truth lesson: live `/answers/[slug]` pages read
`public.answers.body_inline` from Supabase at runtime, not only
`src/content/answers/*.json`. Static JSON edits alone do not change live answer
pages. For answer fixes, update both the repo JSON and the Supabase `answers`
row, then revalidate/purge cache and verify live HTML.

Commit: `556721ff47 fix: remove first-person answer anecdotes`.
Worker deployed: `bee68656-2b85-4221-a23b-1e4b31f98f31`.
Verification: four URLs returned HTTP 200; old phrases absent; replacement
neutral examples present. Repo clean after deploy.

## 2026-06-02 — Answer Generator First-Person Claim Gate

**Status: patched and verified.**

Patched the active answer creation path used by cron:

- `/srv/BusinessOps/tools/creditdoc_cluster_executor.py`
- `/srv/BusinessOps/tools/templates/cluster_asset_prompt.md`

Changes:

- Removed voice-profile instructions that encouraged fake personal experience
  such as "when I applied for my first SBA loan" and "I've been there" energy.
- Added a hard prompt boundary: CreditDoc must not invent first-person lived
  experience about applying for loans, having a FICO score, being declined,
  paying off debt, repairing credit, or using a lender.
- Added `detect_narrator_claim_violations()` to scan generated answer sections.
- Added a critical compliance failure:
  `critical: no fabricated first-person lived-experience claims`.
- The gate hard-fails the answer by capping the compliance score below the
  publish threshold when this issue appears.

Verification:

- `python3 -m py_compile /srv/BusinessOps/tools/creditdoc_cluster_executor.py`
  passed.
- Detector test caught the bad example and allowed the neutral example.
- `basic_compliance()` now fails the exact bad pattern below publish threshold.
- `--preview` prompt includes the new critical voice boundary.
- Active cron confirmed it runs the patched file:
  `/srv/BusinessOps/tools/creditdoc_cluster_executor.py --apply`.

## 2026-06-02 — CreditDoc AI Provider Hardening

**Status: patched and smoke-verified; no production deploy run for this change.**

Root cause found for the repeated Anthropic-key failures: CreditDoc automation
used inconsistent AI provider paths. Some scripts used Claude CLI/OAuth and
worked, while others still used direct Anthropic SDK paths or attempted to use
Claude OAuth token material like an Anthropic SDK API key.

Provider contract now lives in `/srv/BusinessOps/tools/creditdoc_oauth.py`:

- Claude CLI first, normalized to `claude-opus-4-6`.
- Real Anthropic SDK only if a real `ANTHROPIC_API_KEY` exists.
- OpenAI fallback using existing key files.
- Gemini fallback using existing key files.

Patched scripts include the global CreditDoc blog, city guide, autonomous
engine, state legislation, cluster executor, comparison, QA auditor/fixer,
validator, smoke-test paths, plus repo-side `tools/lead_rewriter.py`.

Verification evidence:

- Patched scripts passed `python3 -m py_compile`.
- Bad-pattern grep found no remaining CreditDoc matches for
  `ANTHROPIC_API_KEY is not set`, OAuth-token-as-SDK-key, or Haiku model calls.
- Claude CLI Opus smoke returned `OK`.
- Full `/srv/BusinessOps/tools/creditdoc_smoke_test.py` passed `10/10` at
  `2026-06-02 07:29 UTC`.

Audit/handover:
`/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_AI_Provider_Audit_2026-06-02.md`

## 2026-06-02 — Content Feeds Triggered, Fixed, Deployed

**Status: deployed and verified.**

Cloudflare Worker version:
`b24d47c1-8e2d-4312-b773-5a03f2641302`

Real feed paths triggered:

- Blog: generated `/blog/are-credit-repair-companies-legit-reddit/`.
  Final accepted article: 2,330 words, 8 sections, 5 FAQs.
- City guides: generated `/credit-guide/denton-tx/`.
- Financial wellness: rejected and deleted weak
  `credit-score-after-paying-debt`; accepted
  `/financial-wellness/credit-report-errors-common/` at 2,408 words,
  8 sections, 3 FAQs.
- Comparisons: generated `/compare/dollar-financial-group-vs-refijet/`.
- Answers/questions: generated
  `/answers/can-you-get-a-business-loan-with-bad-credit/`, compliance 10/10.

Code fixes found by real feed tests:

- `creditdoc_blog.py`: missing `time` import fixed; blog quality floor added.
- `creditdoc_wellness_generator.py`: quality floor, queue retry, JSON preface
  recovery, and quarantine for one repeatedly failing slug.
- `creditdoc_cluster_executor.py`: undefined `ROOT` provider import fixed.
- `creditdoc_oauth.py`: long-form Opus timeout raised.

Verification:

- `npm run build` passed.
- `/srv/BusinessOps/creditdoc/deploy.sh` passed.
- New/touched live pages returned HTTP 200.
- Rejected wellness slug returned HTTP 404.
- `/srv/BusinessOps/tools/creditdoc_smoke_test.py` passed `10/10`.
- `creditdoc_route_self_healer.py --check-only` passed `10/10`.
- `/srv/BusinessOps/tools/verify_crons.sh` passed all 57 expected crons.
- Money, answers, and blog IndexNow tier runs each submitted 20 URLs OK.
- Today’s five new/touched URLs were directly submitted to IndexNow and Bing
  with HTTP 200.

Full report:
`/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Content_Feed_Deployment_Report_2026-06-02.md`

## 2026-05-31 — Traffic Drop Investigation + Production Worker 503 Recovery

**Status: production recovered and verified.**

Jammi noticed CreditDoc traffic appeared to be dropping despite the volume of
SEO/content work. Investigation used local GSC reports and live route checks.

GSC facts from the latest local report:

- `gsc_report_2026-05-31.json` covers `2026-05-21 to 2026-05-28`.
- Summary: 1 click, 2,629 impressions, 0.04% CTR, average position 50.3.
- This is materially below the May 10 peak report
  (4 clicks, 5,153 impressions, 0.08% CTR, average position 18.8).
- Impressions had started recovering by May 31 from the May 29 low of 2,256.
- Main SEO read: this is not a Search Console “issue” report; it is a traffic
  and CTR/position problem in the performance data, while newer pages are still
  too fresh to judge.

Production reliability issue found:

- Direct live checks from the VPS found Cloudflare Worker `503` responses with
  body `error code: 1102` on `/review/`, `/best/`, `/credit-guide/`,
  `/state/`, and `/answers/` index route families.
- The exact same routes rendered locally through `wrangler dev --local` with
  Supabase env as HTTP 200, so the current clean bundle could render them.

Recovery:

- Redeployed from the clean current working tree using
  `/srv/BusinessOps/creditdoc/deploy.sh`.
- Cloudflare Worker version deployed:
  `44d0d733-3c99-4c70-90a8-a78cb879d861`.
- Cache purge succeeded.
- Post-deploy checks returned HTTP 200 for both Googlebot and browser user
  agents on:
  `/`, `/review/lexington-law/`, `/best/best-credit-repair-companies/`,
  `/credit-guide/austin-tx/`, `/state/wyoming/`,
  `/answers/best-debt-consolidation-loans-bad-credit/`, and `/answers/`.
- Repo working tree remained clean after deploy.

Safeguard added after recovery:

- Added `tools/creditdoc_route_self_healer.py`.
- It monitors 10 live route-family URLs: homepage, review, best/listicle, city
  guide, state, answers index, answer page, category, blog, and
  financial-wellness.
- It retries failures and only runs a self-heal deploy when at least two
  critical SSR route families fail after retry.
- Self-heal uses the existing safe deploy path: `./deploy.sh`, then verifies the
  same route set after deploy.
- Guardrails: one active self-healer at a time, one active deploy at a time,
  six-hour heal cooldown, AgentMail notification on heal/heal-failure/cooldown.
- Cron installed every 15 minutes:
  `/srv/BusinessOps/.venv/bin/python3 /srv/BusinessOps/creditdoc/tools/creditdoc_route_self_healer.py`.
- Verification passed: `py_compile`, monitor-only live run, normal live run
  (`10/10` healthy, no deploy), and `/srv/BusinessOps/tools/verify_crons.sh`.

## 2026-05-26 — Local Authority Graph Project Restart

**Status: original strategic project resumed after cleanup/deploy detour.**

## 2026-05-27 — Noindex Cleanup Batch 010

**Status: committed, deployed, cache-purged, and live-verified.**

Archived 25 obvious low-quality noindex rows from the dump queue:

- Selection rule: zero GSC impressions/clicks, no website, quality score `0-1`,
  very short description, one service or fewer, and not a chain/location brand
  such as Vigo, MoneyGram, ACE, Amscot, Barri, DolEx, Ria/PLS, or Moneytree.
- Backup:
  `data/backups/creditdoc_before_noindex_drop_batch_010_20260527T064039Z.sqlite`
- Workpack:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Noindex_Review_2026-05-26/noindex_drop_batch_010_2026-05-27.csv`
- Archive record:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Noindex_Review_2026-05-26/noindex_dropped_archive_batch_010_2026-05-27.json`
- Updated local DB and Supabase through `CreditDocDB.update_lender()`.
- Used `CreditDocDB.export_lender_to_json(slug)` per explicit slug only; did
  not use broad `export_changed_lenders()`.
- DB verification: 25 rows now have
  `processing_status=archived`,
  `review_status=archived_low_quality_no_website`,
  `no_index=true`, and
  `quarantine_reason=low_quality_no_website_no_gsc`.
- Supabase retry queue: 0 unresolved lender retry rows for the batch.
- `npm run build` passed with 18,415 SSR route URLs and sitemap/robots checks.
- Exact generated reference scan found zero `/review/<slug>/` references for
  the 25 touched pages.
- Deployed to Cloudflare Workers version
  `7a8b4f71-42e7-455d-8a5b-17e8443faca9`.
- Live verification after deploy: all 25 touched `/review/<slug>/` URLs return
  404, live sitemap has 0 references to them, and smoke checks for `/`,
  `/city/`, `/sitemap-index.xml`, `/review/lexington-law/`, and
  `/credit-guide/austin-tx/` return 200 without `noindex`.
- Unrelated generated files were preserved separately before verification and
  must remain outside noindex cleanup deploy scope unless explicitly reviewed:
  `src/content/comparisons.json` and `src/content/wellness-guides.json`.

## 2026-05-27 — Noindex Cleanup Batch 011

**Status: committed, deployed, cache-purged, and live-verified.**

Archived 30 explicit non-financial quarantine rows from the noindex queue:

- Selection rule: already `failed_quarantine`, zero GSC impressions/clicks,
  `quality_score` `0-1`, one service or fewer, not protected, and quarantine
  reason `gold_dealer_not_financial` or `cannabis_not_financial`.
- Excluded chain/location brands and money-transfer/check-cashing chains from
  this batch, including Ria, PLS, Vigo, MoneyGram, Western Union, Barri, DolEx,
  ACE, Amscot, Sigue, and envio/money-transfer slugs.
- Backup:
  `data/backups/creditdoc_before_noindex_drop_batch_011_20260527T065617Z.sqlite`
- Workpack:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Noindex_Review_2026-05-26/noindex_drop_batch_011_2026-05-27.csv`
- Archive record:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Noindex_Review_2026-05-26/noindex_dropped_archive_batch_011_2026-05-27.json`
- Updated local DB and Supabase through `CreditDocDB.update_lender()`.
- Used `CreditDocDB.export_lender_to_json(slug)` per explicit slug only; did
  not use broad `export_changed_lenders()`.
- DB verification: 30 rows now have
  `processing_status=archived`,
  `review_status=archived_non_financial_quarantine`,
  `no_index=true`, and
  `archive_batch=noindex_drop_batch_011_2026-05-27`.
- Supabase retry queue: 0 unresolved lender retry rows for the batch.
- `npm run build` passed with 18,415 SSR route URLs and sitemap/robots checks.
- `git diff --check` passed.
- Rebuilt `dist` reference scan found zero `/review/<slug>/` references for
  the 30 touched pages.
- Deployed to Cloudflare Workers version
  `422e3851-ade5-4e99-9fa1-3909088436a3`.
- Live verification after deploy: all 30 touched `/review/<slug>/` URLs return
  404, live sitemap has 0 references to them, and smoke checks for `/`,
  `/city/`, `/sitemap-index.xml`, `/review/lexington-law/`, and
  `/credit-guide/austin-tx/` return 200 without `noindex`.

## 2026-05-27 — Noindex Cleanup Batch 012

**Status: committed, deployed, cache-purged, and live-verified.**

Archived 24 obvious non-financial false-positive noindex rows:

- Selection rule: already `failed_quarantine`, zero GSC impressions/clicks,
  `quality_score` `0-1`, one service or fewer, not protected, and a plainly
  off-topic reason/name pattern such as government, medical, mental health,
  notary, title-company, car/dealer, retail/gift-card, or unrelated tech/career
  content.
- Excluded finance-adjacent chain/location records from this batch when the
  name still needed separate handling.
- Backup:
  `data/backups/creditdoc_before_noindex_drop_batch_012_20260527T071430Z.sqlite`
- Workpack:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Noindex_Review_2026-05-26/noindex_drop_batch_012_2026-05-27.csv`
- Archive record:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Noindex_Review_2026-05-26/noindex_dropped_archive_batch_012_2026-05-27.json`
- Updated local DB and Supabase through `CreditDocDB.update_lender()`.
- Used `CreditDocDB.export_lender_to_json(slug)` per explicit slug only; did
  not use broad `export_changed_lenders()`.
- DB verification: 24 rows now have
  `processing_status=archived`,
  `review_status=archived_obvious_non_financial_false_positive`,
  `no_index=true`, and
  `archive_batch=noindex_drop_batch_012_2026-05-27`.
- Supabase retry queue: 0 unresolved lender retry rows for the batch.
- `npm run build` passed with 18,415 SSR route URLs and sitemap/robots checks.
- `git diff --check` passed.
- Rebuilt `dist` reference scan found zero `/review/<slug>/` references for
  the 24 touched pages.
- Deployed to Cloudflare Workers version
  `5bd22900-a89f-41cb-a49a-bc6000fe3bcb`.
- Live verification after deploy: all 24 touched `/review/<slug>/` URLs return
  404, live sitemap has 0 references to them, and smoke checks for `/`,
  `/city/`, `/sitemap-index.xml`, `/review/lexington-law/`, and
  `/credit-guide/austin-tx/` return 200 without `noindex`.

## 2026-05-27 — Noindex Reinstatement Batch 013

**Status: committed locally after DB/build/sitemap verification; deploy pending.**

Reinstated 20 real-provider noindex rows:

- Selection rule: GSC impressions present, `quality_score` at least 7, official
  website present and verified reachable, services present, not protected, and
  no quarantine reason.
- Excluded suspicious cases from this batch, including suspended pages, PDFs,
  SSL failures/timeouts, and blocked sites.
- Backup:
  `data/backups/creditdoc_before_noindex_reinstate_batch_013_20260527T072117Z.sqlite`
- Workpack:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Noindex_Review_2026-05-26/noindex_reinstate_batch_013_2026-05-27.csv`
- Reinstatement record:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Noindex_Review_2026-05-26/noindex_reinstated_batch_013_2026-05-27.json`
- Updated local DB and Supabase through `CreditDocDB.update_lender()`.
- Used `CreditDocDB.export_lender_to_json(slug)` per explicit slug only; did
  not use broad `export_changed_lenders()`.
- DB verification: 20 rows now have
  `processing_status=ready_for_index`,
  `review_status=published`,
  `no_index=false`, and
  `reinstate_batch=noindex_reinstate_batch_013_2026-05-27`.
- Supabase retry queue: 0 unresolved lender retry rows for the batch.
- `npm run build` passed; SSR sitemap route count increased from 18,415 to
  18,435, matching the 20 reinstated review routes.
- `git diff --check` passed.
- Rebuilt sitemap includes all 20 reinstated `/review/<slug>/` routes.

## 2026-05-27 — Production Static Route Recovery + Comparison Batch 152

**Status: deployed, cache-purged, live-verified, and implementation committed.**

Recovered production after overlapping agent sessions caused a bad deploy where
static routes returned 404 while SSR routes still worked:

- Confirmed the clash source: one session was stashing unrelated files and
  running noindex deploys while this session was editing the comparison
  renderer.
- Rebuilt from a coordinated state after the other session paused.
- `npm run build` passed with 18,435 SSR route URLs, 124 city guides, and
  2,232 city-category sub-pages; postbuild sitemap/robots check passed.
- Deployed via `./deploy.sh`.
- Worker version:
  `c166a2b3-11a8-420a-9e7d-554e259fd083`.
- Cache purge passed.
- Deploy-script smoke checks returned 200 for `/`,
  `/credit-guide/austin-tx/`, `/review/lexington-law/`,
  `/answers/best-debt-consolidation-loans-bad-credit/`, and
  `/best/best-credit-repair-companies/`.
- Explicit production recovery checks returned 200 for `/`, `/city/`,
  `/sitemap-index.xml`, `/robots.txt`,
  `/compare/ecreditadvisor-vs-credit-saint/`, and
  `/compare/incharge-debt-solutions-vs-covenant-community-capital/`.

Batch 152 implementation:

- Commit: `970331423c` (`fix: soften comparison proven claims`).
- Scope: `src/pages/compare/[slug].astro`.
- Added comparison-page render-only softening for recurring `proven ...`
  claims in summaries, research notes, FAQs, and JSON-LD.
- Preserved source comparison records, lender records, route slugs, pricing
  fields, ratings, tables, and layout.
- Rendered `dist/compare` scan returned zero matches for:
  `proven 30-year track record`, `proven settlement track record`,
  `proven 36% successful DMP completion rate`,
  `proven 27-year nonprofit track record`, `proven institutional backing`,
  `proven reliability`, `proven market credibility`, `proven enforcement`,
  `proven success-based fee model`, `proven features`,
  `proven client satisfaction`, `proven customer base`,
  `proven debt elimination`, `proven stored public-review context`, and
  `proven 4.8/5 rating`.

Operating rule going forward:

- Do not run two concurrent CreditDoc agents against the same repository and
  deploy target.
- If parallel work is unavoidable, split by branch/worktree and assign exactly
  one owner for `npm run build`, `./deploy.sh`, Cloudflare deploy, and any
  stash/restore operation.
- Do not stash or restore files another active agent may be editing.

## 2026-05-27 — City-Category Availability Copy Batch 153

**Status: built, locally smoke-tested for static routes, documented, pending
deploy.**

Batch 153 implementation:

- Commit: `7c499ea0a2` (`fix: soften city-category availability copy`).
- Scope:
  `src/pages/credit-guide/[slug]/[category].astro` and
  `src/pages/browse/[catSlug]/[citySlug].astro`.
- Softened city-category availability and completeness language from broad
  `compare companies serving` and `statewide providers available` wording into
  listed-profile, associated-with-city, and verify-before-contact wording.
- Reframed category intros for personal loans, emergency cash, debt relief,
  build-credit, free-help, business-loans, and pawn-shops to avoid implied
  outcomes, complete availability, fee certainty, or licensing determinations.
- Preserved routes, provider cards, lender records, city/category counts,
  JSON-LD structure, graph links, and source data.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,435 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Focused source and rendered `dist/browse` scans returned zero matches for:
  `company profiles serving`, `get the help you need`,
  `statewide options available`, `Statewide providers available`,
  `predatory rates`, `understand all fees`, `Compare licensed pawn shops`, and
  `All {cityInfo.count} companies`.
- Rendered sample files checked clean:
  `/browse/personal-loans/new-york-ny/`,
  `/browse/emergency-cash/houston-tx/`, and
  `/browse/credit-unions/amarillo-tx/`.
- Local Wrangler smoke checks returned HTTP 200 for
  `/browse/personal-loans/new-york-ny/`,
  `/browse/emergency-cash/houston-tx/`, and `/sitemap-index.xml`.
- Local Wrangler SSR checks for `/credit-guide/.../.../` returned 404 because
  the local worker was not running with the runtime Supabase binding; the SSR
  city-category template is covered by source scan plus successful worker
  build, not by local HTTP.

## 2026-05-27 — CFPB Trends Response Context Batch 154

**Status: built, locally smoke-tested, documented, pending deploy.**

Batch 154 implementation:

- Commit: `144c5aa12e` (`fix: clarify CFPB trend response context`).
- Scope:
  `src/pages/trends/[slug].astro` and `src/pages/trends/index.astro`.
- Replaced `resolution rate` presentation with `recorded response-outcome`
  wording so CFPB complaint data is not implied to prove consumer satisfaction
  or actual dispute resolution.
- Reframed trend index counts from generic consumer interactions to public CFPB
  complaint records.
- Removed `complete profile`, `user reviews`, and `handles consumer inquiries`
  overstatements from trend detail metadata and CTAs.
- Added stronger trend-page disclaimers that CFPB response data is
  transparency context, not proof of wrongdoing, endorsement, safety rating,
  customer-satisfaction evidence, or suitability determination.
- Preserved trend routes, CFPB source records, response metrics, index
  grouping, provider-profile links, research links, city/state/context links,
  and JSON-LD structure.

Verification:

- `git diff --check` passed.
- `npm run build` passed.
- Build generated 124 city guides and 2,232 city-category sub-pages.
- Build injected 18,435 SSR route URLs.
- Postbuild sitemap/robots check passed.
- Rendered `dist/trends` scan returned zero matches for:
  `Resolution Rate`, `resolution rate`, `complete profile`, `user reviews`,
  `consumer interactions`, `handles consumer inquiries`, `Total
  Interactions`, `Services Used by Consumers`, `Consumer Feedback Categories`,
  and `Response rates are transparency`.
- Rendered sample files exist for `/trends/`, `/trends/lexington-law/`,
  `/trends/american-consumer-credit-counseling/`, and
  `/trends/advance-america/`.
- Local Wrangler smoke checks returned HTTP 200 for `/trends/`,
  `/trends/lexington-law/`, `/trends/american-consumer-credit-counseling/`,
  `/trends/advance-america/`, and `/sitemap-index.xml`.
- Local rendered copy check for `/trends/lexington-law/` found none of the old
  phrases and confirmed the new `Recorded Response Outcome` and `not proof of
  wrongdoing` markers.

Created the operating plan for the bottom-up local authority strategy:

- `docs/plans/2026-05-26-creditdoc-local-authority-graph.md`

This plan turns CreditDoc's page network into a deliberate graph:

- local/city pages;
- lender/entity profiles;
- state rules and data explainers;
- answer clusters;
- tools/quizzes;
- original research reports;
- provider correction/outreach loops.

Current CFPB report release-loop progress:

1. Added `/research/consumer-complaints/` -> CFPB responsiveness report link.
2. Created provider and press/media outreach tracker CSVs in the CFPB workpack.
3. Documented those release assets in:
   `/srv/BusinessOps/CreditDoc Project Improvement/CFPB_Responsiveness_Report_2026-05-26/release_assets_log_2026-05-26.md`

Sitewide upgrade program restarted:

- Plan: `docs/plans/2026-05-26-sitewide-page-upgrade-program.md`
- Batch 001 workpack:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/`
- Latest cleanup batch completed:
  `97f2d6b394 fix: hide failed extraction artifacts`.
  Batch 145 cleaned rendered browse/provider-card and comparison-page failed
  extraction artifacts. Browse pages now count/display only profiles with usable
  card copy, LenderCard falls back to neutral review copy if extraction text is
  bad, and comparison pages soften raw `403 Forbidden`, `Unable to verify`, and
  `Unable to generate` wording.
- Batch 145 verification passed: `git diff --check`, `npm run build`, 124 city
  guides, 2,232 city-category sub-pages, 18,413 SSR route URLs,
  sitemap/robots OK, targeted rendered `dist/browse` and `dist/compare` scan
  returned zero matches for `403 Forbidden`, `Unable to verify`, and `Unable to
  generate`, local static route checks all HTTP 200, and production spot checks
  all HTTP 200.
- Batch 145 preserved the two unrelated unstaged files:
  `src/content/comparisons.json` and `src/content/wellness-guides.json`.
- Previous cleanup batch:
  `31724b28e4 fix: clean comparison context residue`.
  Batch 144 cleaned rendered comparison and browse-page context residue,
  including `stored outcome context`, `consumer research context credit
  monitoring`, `more consumer research context accountability`, emergency,
  debt-relief, public-profile, listed-cost, and `provider-stated outcome context
  to verify.2` patterns.
- Batch 144 verification passed: `git diff --check`, `npm run build`, 124 city
  guides, 2,232 city-category sub-pages, 18,413 SSR route URLs,
  sitemap/robots OK, targeted rendered comparison/browse residue scan clean,
  local static route checks all HTTP 200, and production spot checks all HTTP
  200.
- Batch 144 preserved the two unrelated unstaged files:
  `src/content/comparisons.json` and `src/content/wellness-guides.json`.
- Previous cleanup batch:
  `bb312cc51b fix: soften comparison result residue`.
  Batch 143 softened rendered comparison-page result and claim residue found
  during quality monitoring, including `for borrowers comparing listed cost
  prioritizing`, `more option for consumers comparing users reviewing...`,
  `dramatically better credit-building results`, `actual financial return`,
  `lower total costs`, `suggesting greater operational maturity and client
  satisfaction`, `regulatory compliance`, `significant transparency and trust
  concerns`, and `exclude many users`.
- Batch 143 verification passed: `git diff --check`, `npm run build`, 124 city
  guides, 2,232 city-category sub-pages, 18,413 SSR route URLs,
  sitemap/robots OK, targeted rendered comparison residue scan clean, local
  static route checks all HTTP 200, and production spot checks all HTTP 200.
- Batch 143 preserved the two unrelated unstaged files:
  `src/content/comparisons.json` and `src/content/wellness-guides.json`.
- Previous cleanup batch:
  `7e3454f706 fix: clean comparison grammar residue`.
  Batch 142 cleaned comparison-page grammar residue found during quality
  monitoring, including `for consumers comparing listed cost prioritizing`,
  lowercase sentence-start residue after listed-cost rewrites,
  `higher in listed context stored public-review context`,
  `clearer listed-cost context proposition`,
  `making it the profile with more context for...`, and awkward
  `consumers reviewing credit repair seekers` phrasing.
- Batch 142 verification passed: `git diff --check`, `npm run build`, 124 city
  guides, 2,232 city-category sub-pages, 18,413 SSR route URLs,
  sitemap/robots OK, targeted rendered comparison residue scans clean, local
  static route checks all HTTP 200, and production spot checks all HTTP 200.
- Batch 142 preserved the two unrelated unstaged files:
  `src/content/comparisons.json` and `src/content/wellness-guides.json`.
- Previous cleanup batch:
  `b12ab69fa4 fix: clean comparison copy artifacts`.
  Batch 141 cleaned live-quality comparison-page copy artifacts found during
  health monitoring, including the broken InCharge `to verify.2 million`
  rendered phrase, duplicated `listed, listed credit-building` wording,
  `stored outcome context (49-point average increase)` residue,
  overconfident `100% refund policy` and `claims of 2-week posting` wording,
  and `profile with more context for debt management` grammar.
- Batch 141 verification passed: `git diff --check`, `npm run build`, 124 city
  guides, 2,232 city-category sub-pages, 18,413 SSR route URLs,
  sitemap/robots OK, targeted rendered comparison residue scan clean, local
  static route checks all HTTP 200, and production spot checks all HTTP 200.
- Batch 141 preserved the two unrelated unstaged files:
  `src/content/comparisons.json` and `src/content/wellness-guides.json`.
- Previous cleanup batch:
  `a695ba76ec fix: soften comparison residual claims`.
  Batch 140 cleaned comparison-page residual claim and grammar artifacts around
  Brigit/ACE, ACE location-to-location, and Midland/APR examples, including
  long-term financial-improvement phrasing, budget-conscious borrower framing,
  hard suitability language, BBB/fair-lending overclaims, high-APR phrasing,
  debt-relief framing, and duplicated `to review` wording.
- Batch 140 verification passed: `git diff --check`, `npm run build`, 124 city
  guides, 2,232 city-category sub-pages, 18,413 SSR route URLs,
  sitemap/robots OK, targeted rendered comparison residue scans clean, local
  static route checks all HTTP 200, and production spot checks all HTTP 200.
- Batch 140 preserved the two unrelated unstaged files:
  `src/content/comparisons.json` and `src/content/wellness-guides.json`.
- Previous cleanup batch:
  `c55b2a579d fix: clean course module render artifacts`.
  Batch 139 cleaned Credit Fundamentals course rendering by removing leaked
  authoring notes from module content/previews, softening module meta
  descriptions through the shared safe-copy path, cleaning stale CTA wording,
  and fixing quiz wording/grammar artifacts around score-increase promises,
  complaint-agency framing, automatic deletion claims, and broad scam wording.
- Batch 139 verification passed: `git diff --check`, `npm run build`, 124 city
  guides, 2,232 city-category sub-pages, 18,413 SSR route URLs,
  sitemap/robots OK, targeted rendered course residue scans clean, local static
  route checks all HTTP 200, and production spot checks all HTTP 200.
- Batch 139 preserved the two unrelated unstaged files:
  `src/content/comparisons.json` and `src/content/wellness-guides.json`.
- Previous cleanup batch:
  `b605275bff fix: soften faq claims`.
  Batch 138 softened static FAQ copy around CreditDoc purpose, update cadence,
  ratings visibility, correction review timing, credit-repair outcomes,
  pricing/timing, self-repair, and debt-relief framing. FAQ JSON-LD receives the
  same cleaned answers from the shared FAQ array.
- Batch 138 verification passed: `git diff --check`, `npm run build`, 124 city
  guides, 2,232 city-category sub-pages, 18,413 SSR route URLs,
  sitemap/robots OK, targeted source/rendered FAQ residue scans clean, local
  static route checks all HTTP 200, and production spot checks all HTTP 200.
- Batch 138 preserved the two unrelated unstaged files:
  `src/content/comparisons.json` and `src/content/wellness-guides.json`.
- Previous cleanup batch:
  `cda882eca5 fix: soften blog and glossary outcome copy`.
  Batch 137 cleaned rendered blog-index teaser copy and glossary educational
  examples, softening hard approval/outcome language, numeric score-change
  claims, score/rate determinism, and grammar artifacts from earlier safe-copy
  passes.
- Batch 137 verification passed: `git diff --check`, `npm run build`, 124 city
  guides, 2,232 city-category sub-pages, 18,413 SSR route URLs,
  sitemap/robots OK, targeted rendered blog/glossary residue scan clean, local
  static route checks all HTTP 200, and production spot checks all HTTP 200.
- Batch 137 preserved the two unrelated unstaged files:
  `src/content/comparisons.json` and `src/content/wellness-guides.json`.
- Previous cleanup batch:
  `78ffaec0c5 fix: soften residual comparison and card claims`.
  Batch 136 cleaned rendered provider-card and comparison-page residue including
  lingering no-credit-check wording, eligibility/timing phrasing, `starts at
  just`, `faster credit rebuilding`, `budget-conscious consumers`, unsupported
  reputation/review-volume phrasing, success-rate claims, `established track
  record`, and security/red-flag comparison language.
- Batch 136 verification passed: `git diff --check`, `npm run build`, 124 city
  guides, 2,232 city-category sub-pages, 18,413 SSR route URLs,
  sitemap/robots OK, targeted rendered residue scan clean, local static route
  checks all HTTP 200, and production spot checks all HTTP 200.
- Previous cleanup batch:
  `3d53c7b4d0 fix: soften provider and comparison claim residue`.
  Batch 135 cleaned provider-card and comparison-page residue including
  awkward no-credit-check phrases, `option to compare Capital Inc provides`,
  credit-repair timing claims, `stored outcome fields`, `27-year track record`,
  `accuracy and affordability make it`, `last-resort settlement option`,
  `unsuitable for`, and timeline/outcome claims.
- Batch 135 verification passed: `git diff --check`, `npm run build`, 124 city
  guides, 2,232 city-category sub-pages, 18,413 SSR route URLs,
  sitemap/robots OK, targeted rendered residue scan clean, local static route
  checks all HTTP 200, and production spot checks all HTTP 200.
- Previous cleanup batch:
  `382300397d fix: clean comparison residual grammar claims`.
  Batch 134 verification passed: `npm run build`, 124 city guides, 2,232
  city-category sub-pages, 18,413 SSR route URLs, sitemap/robots OK, targeted
  rendered comparison residue scan clean, local static route checks all HTTP
  200, and production spot checks all HTTP 200.
- Batch 001 completed and committed:
  `bba672df72 feat: add cfpb report profile links`.
- Batch 001 scope: 49 report-included `/review/{slug}/` provider pages get an
  `Included in CreditDoc research` callout through the review template when the
  provider appears in `src/data/cfpb-responsive-providers-2026.json`.
- Batch 002 completed and committed:
  `07b046a396 feat: add local graph links to credit guides`.
  `/credit-guide/{slug}/` and `/credit-guide/{slug}/{category}/` templates now
  include local authority graph paths that connect city pages to city-category
  pages, state lending laws, answer clusters, tools, and CFPB data context.
- Latest local GSC pull (`pull_id=12`) saw 26 `/credit-guide/` URLs; the
  Batch 002 template changes apply beyond those rows to every ready city guide
  and city-category page served by the two templates.
- Batch 002 workpack:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_002_notes_2026-05-26.md`
- Batch 003 completed and committed:
  `1acbc51ecf feat: add graph links to answer pages`.
  `/answers/{slug}/` template now includes a `Continue Your Research` graph path
  connecting answer pages to the matching category directory, local credit
  guides, state lending-rule pages, and CFPB complaint-data context.
- Local answer inventory: 35 `cluster_answers` rows; latest GSC pull saw 13
  `/answers/` URLs. Batch 003 applies to every answer served by the SSR answer
  template.
- Batch 003 workpack:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_003_notes_2026-05-26.md`
- Batch 004 completed and committed:
  `d672d77841 feat: add graph context to comparison pages`.
  `/compare/{slug}/` template now includes a `Check the Context Before You
  Contact a Company` graph path connecting comparison pages to lender profiles,
  category context, local guides, and CFPB complaint-data context.
- Batch 004 also softened template-level comparison language:
  `Our Pick` -> `Comparison Note`, `Which One Is Right for You?` ->
  `How to Compare These Two`, and `Choose ...` -> `Review ...`.
- Local comparison inventory: 280 `comparisons` rows; latest GSC pull saw 7
  `/compare/` URLs. Batch 004 applies to every generated comparison page.
- Batch 004 workpack:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_004_notes_2026-05-26.md`
- Batch 005 completed and committed:
  `f1e0e02d2d feat: add graph links to category pages`.
  `/categories/{category}/` template now includes an `Explore {category}
  Locally` authority path and `Research the Next Step` cards.
- Category hubs now connect to example local city-category pages for Amarillo,
  Austin, and Charlotte, plus answer hub, state lending-rule hub, CFPB complaint
  data context, and CreditDoc tools.
- Local category inventory: 19 `categories` rows; latest GSC pull saw 14
  `/categories/` URLs. Batch 005 applies to every SSR category page.
- Batch 005 workpack:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_005_notes_2026-05-26.md`
- Batch 006 completed and committed:
  `e142c1650b feat: add graph links to state pages`.
  `/state/`, `/state/{slug}/`, and `/state/{slug}/lending-laws/` now include
  state-to-local authority paths connecting state hubs, lending-law pages,
  city guides, category pages, answer clusters, and CFPB complaint-data context.
- Batch 006 uses advisory-neutral wording: state pages provide
  directory/legal-context research, not legal advice, recommendations, approval
  predictions, price quotes, or licensing determinations.
- Latest local GSC pull (`pull_id=12`) saw 10 `/state/` URLs. Batch 006 applies
  beyond those rows to the state index, every SSR state directory page, and
  every generated lending-law page.
- Batch 006 build verification passed:
  `npm run build`, robots contract, SSR sitemap parity, Astro build, generated
  output/server-bundle section scan, and sitemap/robots conflict check. This run
  injected 18,411 SSR route URLs and successfully added 124 city guides plus
  2,232 city-category sub-pages.
- Batch 006 workpack:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_006_notes_2026-05-26.md`
- Batch 007 completed and committed:
  `3b2cb3967d feat: add graph links to research pages`.
  research pages now link original-data reports back into local guides, state
  pages, provider categories, answer clusters, CreditDoc tools, CFPB
  methodology, and report-specific category context.
- Batch 007 scope: `/research/`, `/research/consumer-complaints/`,
  `/research/lending-transparency/`,
  `/research/most-responsive-consumer-finance-providers-2026/`, and
  `/research/state-of-subprime-lending-2026/`.
- Latest local GSC pull (`pull_id=12`) saw 0 `/research/` URLs. This batch is a
  pre-visibility authority-graph upgrade for all current research pages.
- Batch 007 also softened the consumer-complaints title/meta away from
  "protect borrowers" wording and fixed the State of Subprime Lending breadcrumb
  from `/press/` to `/research/`.
- Batch 007 build verification passed:
  `npm run build`, robots contract, SSR sitemap parity, Astro build, generated
  output/server-bundle section scan, and sitemap/robots conflict check. This run
  injected 18,411 SSR route URLs and successfully added 124 city guides plus
  2,232 city-category sub-pages.
- Batch 007 workpack:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_007_notes_2026-05-26.md`
- Batch 008 completed and committed:
  `9c013cfa8f feat: add graph links to tools pages`.
  tools pages now link calculators/quizzes into local guides, state context,
  provider categories, answer clusters, resources, and CFPB/research pages.
- Batch 008 scope: `/tools/`, `/tools/borrowing-power-quiz/`,
  `/tools/debt-payoff-calculator/`, and `/tools/credit-score-simulator/`.
- Latest local GSC pull (`pull_id=12`) saw 0 `/tools/` URLs. This batch is a
  pre-visibility authority-graph upgrade for the current tool pages.
- Batch 008 also softened visible tool copy: no `Our Recommendation` label, no
  "best method" claim, no personalized lender-recommendation framing, and less
  assertive credit-score impact language.
- Batch 008 build verification passed:
  `npm run build`, robots contract, SSR sitemap parity, Astro build, generated
  output section scan, and sitemap/robots conflict check. This run injected
  18,411 SSR route URLs and successfully added 124 city guides plus 2,232
  city-category sub-pages.
- Batch 008 workpack:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_008_notes_2026-05-26.md`
- Batch 009 completed and committed:
  `2d5c452abf feat: add graph links to resource pages`.
  resources pages now link checklist/template resources into tools, answers,
  local guides, provider categories, and CFPB complaint-data context.
- Batch 009 scope: `/resources/`, `/resources/credit-report-checklist/`,
  `/resources/credit-report-checklist/print/`,
  `/resources/debt-credit-letter-templates/`, and individual letter-template
  pages through `src/components/LetterTemplatePage.astro`.
- Latest local GSC pull (`pull_id=12`) saw 0 `/resources/` URLs. This batch is
  a pre-visibility authority-graph upgrade for the current resource pages.
- Batch 009 also softened checklist copy from "highest-impact" to "major
  credit-building habits" and added CFPB complaint-data context to the printable
  checklist.
- Batch 009 build verification passed:
  `npm run build`, robots contract, SSR sitemap parity, Astro build, generated
  output section scan, and sitemap/robots conflict check. This run injected
  18,411 SSR route URLs and successfully added 124 city guides plus 2,232
  city-category sub-pages.
- Batch 009 workpack:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_009_notes_2026-05-26.md`
- Batch 010 completed and committed:
  `9cc4811945 feat: add graph links to wellness pages`.
  financial-wellness pages now link the education layer into local guides,
  answer clusters, tools/resources, related provider categories, and CFPB
  complaint-data context.
- Batch 010 scope: `/financial-wellness/` and `/financial-wellness/{slug}/`
  through `src/pages/financial-wellness/[slug].astro`.
- Local wellness guide inventory: 98 `wellness_guides` rows. Latest local GSC
  pull (`pull_id=12`) saw 32 `/financial-wellness/` URLs.
- Batch 010 also fixed wellness category label mappings for
  `building-credit`, `budgeting-and-saving`, `loans-and-interest`,
  `everyday-finance`, and `credit-repair`, and softened index copy toward
  verifiable education plus local/provider/public-data context.
- Batch 010 build verification passed:
  `npm run build`, robots contract, SSR sitemap parity, Astro build, generated
  output/server-bundle scan, and sitemap/robots conflict check. This run
  injected 18,411 SSR route URLs and successfully added 124 city guides plus
  2,232 city-category sub-pages.
- Batch 010 workpack:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_010_notes_2026-05-26.md`
- Batch 011 completed and committed:
  `bc19ad1a9c feat: add graph links to blog pages`.
  blog pages now link editorial posts into local guides, answer clusters,
  tools/resources, related provider categories, and CFPB complaint-data context.
- Batch 011 scope: `/blog/` and `/blog/{slug}/` through
  `src/pages/blog/[slug].astro`.
- Local blog inventory: 68 `blog_posts` rows. Latest local GSC pull
  (`pull_id=12`) saw 13 `/blog/` URLs.
- Batch 011 also softened blog index and sidebar wording away from
  recommendation/top-pick and qualification phrasing toward neutral comparison,
  research-path, and context language.
- Batch 011 build verification passed:
  `npm run build`, robots contract, SSR sitemap parity, Astro build, generated
  output/server-bundle scan, and sitemap/robots conflict check. This run
  injected 18,411 SSR route URLs and successfully added 124 city guides plus
  2,232 city-category sub-pages.
- Batch 011 workpack:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_011_notes_2026-05-26.md`
- Batch 012 completed and committed:
  `c304df885c feat: add graph links to education pages`.
  education-support pages now link the learn/search, glossary, and course layer
  into local guides, answer clusters, tools, resources, provider categories,
  state context, and CFPB complaint-data research.
- Batch 012 scope: `/learn/`, `/glossary/`, `/courses/`,
  `/courses/credit-fundamentals/`, and every
  `/courses/credit-fundamentals/{slug}/` module page through the shared course
  module template.
- Local education inventory: 71 glossary terms, 1 current course, 8 course
  modules, and 40 course lessons. Latest local GSC pull (`pull_id=12`) saw 0
  `/learn/`, `/glossary/`, or `/courses/` URLs.
- Batch 012 also softened the Credit Fundamentals overview away from unsupported
  savings, endorsement, "right answer", and strong outcome claims.
- Batch 012 build verification passed:
  `npm run build`, robots contract, SSR sitemap parity, Astro build, generated
  output scan, targeted route check, and sitemap/robots conflict check. This run
  injected 18,411 SSR route URLs and successfully added 124 city guides plus
  2,232 city-category sub-pages.
- Batch 012 workpack:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_012_notes_2026-05-26.md`

Immediate next:

1. Continue to Batch 013: inspect static trust/support pages such as about,
   methodology, editorial policy, FAQ, disclosure, disclaimer, privacy/terms,
   accessibility, and contact; upgrade the suitable next family with graph links
   and YMYL-safe wording.
2. Keep every batch scoped, build-verified, documented, and committed before
   starting the next one.

## 2026-05-26 — Static Asset Routing Fix + Noindex Cleanup Batch 009

**Status: deployed and live-verified.**

Root cause found for repeated unrelated lender JSON dirtiness: the broad
`export_changed_lenders()` path exports every lender where `exported_at IS NULL`
or `updated_at > exported_at`, not just the current cleanup batch. For controlled
noindex batches, use `CreditDocDB.export_lender_to_json(slug)` per explicit slug
only.

Static asset routing issue fixed:

- Symptoms after the previous deploy: `/`, `/city/`, and `/sitemap-index.xml`
  returned `404`, while dynamic SSR pages such as `/review/lexington-law/`
  still returned `200`.
- Cause: Cloudflare static assets had no explicit HTML handling, so `/path/`
  was not resolving to `/path/index.html`; sitemap XML was also being routed to
  the Worker instead of static assets.
- Fix: `wrangler.toml` now sets `html_handling = "auto-trailing-slash"` and
  `not_found_handling = "404-page"`; `astro.config.mjs` excludes
  `/sitemap-index.xml` and `/sitemap-*.xml` from Worker routing.
- Deploy via `./deploy.sh` passed.
- Cloudflare Worker version: `11d2be7e-624f-4b23-8d9c-31db1923a411`.
- Live smoke checks passed: `/`, `/city/`, `/sitemap-index.xml`,
  `/robots.txt`, `/review/lexington-law/`, and `/credit-guide/austin-tx/`
  all return `200` and no `noindex`.

Archived 15 zero-impression, raw, no-website, low-quality noindex profiles:

- `1-checks-cashed`
- `12-30-financial`
- `123-credit-debt-counseling`
- `123fixcredit`
- `2-raise-my-credit-score`
- `2020-vision-credit-repair`
- `2nd-chance-budget-debt`
- `44-financial-corporation`
- `50kcreditsystem`
- `5m-capital`
- `60-percent-debt-settlement`
- `866-get-paid`
- `8fiftycredit`
- `accelerateyourcredit`
- `advance-case-lending`

Verification completed:

- SQLite backup:
  `data/backups/creditdoc_before_noindex_drop_batch_009_20260526T111210Z.sqlite`
- Workpack records:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Noindex_Review_2026-05-26/noindex_drop_batch_009_2026-05-26.csv`
  and
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Noindex_Review_2026-05-26/noindex_dropped_archive_batch_009_2026-05-26.json`
- Local DB and exported JSON agree:
  `processing_status=archived`,
  `review_status=archived_low_quality_no_website`,
  `no_index=true`, `quarantine_reason=low_quality_no_website`.
- No unresolved Supabase retry rows for the 15 touched slugs.
- `npm run build` passed.
- Exact built static scan found zero `/review/<slug>/` references for the 15
  touched slugs.

Also archived and redirected 9 wrong-vertical or unsafe GSC-visible profiles:

- `auto-titles-and-bonds` -> `/credit-guide/dallas-tx/personal-loans/`
- `autocarhouston-autos-usados` -> `/credit-guide/houston-tx/personal-loans/`
- `burns-buy-here-pay-here-of-spartanburg` -> `/categories/personal-loans/`
- `fix-my-auto-credit-score` -> `/categories/personal-loans/`
- `fraud` -> `/categories/credit-repair/`
- `good-price-title-auto-title-services-bonded-titles-by-appointment-only` ->
  `/categories/personal-loans/`
- `jm-auto-title-service-titulos-y-placas-surety-bond-title` ->
  `/credit-guide/dallas-tx/personal-loans/`
- `ny-identity-theft-group` -> `/categories/credit-repair/`
- `vfs-global-india-passport-application-center` ->
  `/categories/credit-repair/`

Live Batch 009 checks:

- All 9 redirected review URLs return `302` to the expected target.
- Live sitemap index and all five sitemap XML files return `200`.
- None of the 9 redirected review URLs appear in live sitemaps.
- Deploy verification passed through `./deploy.sh`.

Repo commits before this routing fix:

- `7961ce8df7` — `data: archive low-quality noindex batch`
- `253db0cf96` — `data: archive redirected wrong-vertical noindex batch`
- `546476de43` — `docs: add cfpb report release links`

## 2026-05-26 — CFPB Report Release Assets

**Status: in progress. Do not touch concurrent dirty Batch 001 lender files.**

Release-assets work started for the public CFPB responsiveness report:

- Report route:
  `/research/most-responsive-consumer-finance-providers-2026/`
- Workpack log:
  `/srv/BusinessOps/CreditDoc Project Improvement/CFPB_Responsiveness_Report_2026-05-26/release_assets_log_2026-05-26.md`
- Added an internal link from `/about/creditdoc-data/` CFPB methodology copy to
  the public report.
- Added an "Original Research Reports" section on `/about/creditdoc-data/`
  linking to the report.
- Added a "Latest Research" card on `/press/` linking to the report.
- Drafted press pitch and provider outreach copy in the CFPB workpack.

Next within this release-assets thread:

- Verify build for the release-assets changes.
- Commit only the release-assets files; leave the nine dirty Batch 001 lender
  normalization files alone.

## 2026-05-26 — Noindex Cleanup Batches 006-007

**Status: deployed and live-verified. Worktree clean after commit.**

Batch 006 archived 10 title/title-service wrong-vertical profiles:

- `stewart-title-of-oklahoma-inc-okc-title`
- `citywide-title-corporation-chicago-il`
- `definitive-title`
- `empire-title-of-colorado-springs`
- `fidelity-national-title`
- `pennsylvania-land-titles`
- `titlesmart`
- `warranty-title`
- `signloc-title-escrow`
- `title-exchange-of-east-point`

Batch 007 archived 12 hard auto/vehicle/car-dealer wrong-vertical profiles:

- `alamo-city`
- `american-pride`
- `ascent`
- `bachman-buys`
- `battery-employees`
- `buyright`
- `byrider-colorado-springs`
- `byrider-pittsburgh`
- `byrider-san-antonio-west`
- `chapman-speedway`
- `hudson-pre-owned`
- `napletons-aston-martin-chicago`

Verification completed:

- Local JSON, local SQLite, and Supabase were verified for Batch 007:
  `processing_status=archived`, `review_status=archived_wrong_vertical`,
  `no_index=true`, `quarantine_reason=wrong_vertical_auto_vehicle`.
- `npm run build` passed after restoring `/city/` to `src/pages/city/index.astro`
  and preserving the trends filter from commit `c40a3a3025`.
- Static exact-path scan found no `/review/<slug>/` references for all 12 Batch
  007 slugs.
- `/trends/ascent/` is no longer generated and no longer appears in live
  sitemaps.
- Batch 006 deploy: Worker version `95c04a59-9fcf-442e-89a0-b14dd45e2959`.
- Batch 007 deploy: Worker version `1d5be9ba-6f92-4125-8029-7393e086aad2`.
- Live Batch 007 checks: all 12 review URLs return `404`; `/trends/ascent/`
  returns `404`; live sitemaps have no references to the 12 review URLs or
  `/trends/ascent/`.
- Live smoke checks return `200` with no `noindex`: `/review/lexington-law/`,
  `/categories/fintech/`, `/review/moneylion/`,
  `/research/most-responsive-consumer-finance-providers-2026/`,
  `/credit-guide/austin-tx/`, and `/city/`.

Repo commits:

- `93f38ad0a7` — archive title-service noindex cleanup batch.
- `c40a3a3025` — verify report links and trend filtering.
- `de5ccdea7f` — archive auto-vehicle noindex cleanup batch.
- `25bd492a1c` — record noindex cleanup batches.

Coordination note:

- `c40a3a3025` was intentionally kept scoped while another agent completed the
  Batch 007 lender updates. Do not revert the Batch 007 lender changes when
  working on CFPB/report links or trend filtering.
- The trends index/detail filters must stay aligned: the index removes
  archived/noindex lender-backed entries, and `[slug].astro` must not generate
  those same archived/noindex trend detail pages.
- Memory mirror:
  `/root/.claude/projects/-srv-BusinessOps/memory/creditdoc_cfpb_noindex_coordination_2026-05-26.md`

Continue noindex cleanup in controlled batches only. Every batch must end with
build verification, exact static reference scan, deploy via `./deploy.sh`, live
URL checks, and live sitemap checks.

## 2026-05-26 — Noindex Cleanup Batch 008

**Status: deployed and live-verified.**

Batch 008 reinstated 5 real credit union profiles from noindex after validating
official websites and stored NCUA charter data:

- `u-f-c-w-local-1776`
- `mattel`
- `midwest-family`
- `telco-community-credit-union`
- `pioneer-appalachia`

Rules applied:

- Used `CreditDocDB.update_lender()` with founder override; no direct JSON
  surgery.
- Required working official-looking credit union website plus NCUA charter
  context already present in the profile.
- Set `processing_status=ready_for_index`, `review_status=published`, and
  `no_index=false`.
- Added neutral, factual title/meta/description copy and official `website_url`.
- Did not reinstate candidates with SSL/domain mismatch or weak website signals.

Verification:

- Local SQLite and exported JSON agree for all five touched slugs.
- `npm run build` passed with robots/sitemap guards and 18,410 injected SSR
  route URLs.
- Generated sitemap includes all five `/review/<slug>/` paths.
- Deployed via `./deploy.sh`.
- Cloudflare Worker version:
  `3968f894-d02b-4867-8fc9-6ffac519303b`.
- Live: all five review URLs return `200`, have canonical review URLs, and do
  not contain a `noindex` robots meta.
- Live sitemaps include all five review URLs.
- Live smoke pages return `200` with no noindex: `/review/lexington-law/`,
  `/city/`, `/credit-guide/austin-tx/`, `/sitemap-index.xml`, and
  `/robots.txt`.

Repo commit:

- `4240a47847` — `data: reinstate verified credit union noindex batch`.

## 2026-05-18 — SEO FIXES BATCH + PRICING REMOVAL + AI COUNCIL

**Status: 18 fixes shipped. Pricing stripped. Council rebuilt with real characters. FREEZE ON-PAGE CHANGES.**

**Shipped 2026-05-17:**
1. City x category sub-pages — 756 new pages (42 cities × 18 categories). Worker `8bb70ada`.
2. City guide linking overhaul — inline linker phrases, HMDA table links, lender matching. Worker `e7d4d4fd`.
3. Category sub-pages: schema (CollectionPage+ItemList+BreadcrumbList), sitemap (756+ URLs), breadcrumb URL fix, localized intros, alt text.
4. FAQ keyword mapping tightened (exact slug fragments replacing broad keywords).
5. /trends/ index dedup — 767→378 entries.
6. CFPB labels clarity — "Response Rate*" / "On-Time Response**" with footnotes.
7. Data explainer page at `/about/creditdoc-data/` — 10 anchored sections.
8. Company count fix — uses `getStateCountRuntime()` (lightweight DB view).

**Shipped 2026-05-18:**
9. Data-driven FAQ — 8-candidate priority system with real per-company data. Worker `51f5a284`.
10. Free/mo pricing fix — subscription-category-aware display; 834 pages fixed. Worker `be8ec518`.
11. Generic best_for — 9 fintech companies updated with specific text.
12. Inline linker BNPL/fintech — 24 new phrase mappings. Worker `df5b1641`.
13. Tooltip ⓘ component — `InfoLink.astro` wired to 6 locations on every /review/ page (rating, CFPB, similar companies). Worker `e5af42cc`.
14. **PRICING REMOVAL** — ALL unverified AI-generated pricing stripped from entire site. Pricing cards, header badges, FAQ candidates, sidebar fields, schema priceRange, card product schema, LenderCard price badges. 272 lines deleted. Workers `9f92c790` → `77f6711a` → `cf366386`. Commits `4e5f7012c4` + `2806923784`.

**Production incident (2026-05-17):**
- Worker 1102 crash — removing `limit=30` from `getLendersByStateRuntime` caused CPU exceeded on states with 1,800+ lenders. Fixed: restored limit=30, count from `state_lender_counts` view.
- Monitor email spam — cooldown hash changed per-run. Fixed: single cooldown key.

**Current Worker:** `cf366386` (latest deploy)

---

## AI Council Session 7 (REAL — 6 independent agents)

Unanimous: **backlinks are #1 bottleneck.** Freeze on-page changes 3-4 weeks.

Council members now have real character profiles at `ai_council/members/`:
| Role | Character |
|------|-----------|
| Growth Strategist | Chamath Palihapitiya |
| Technical Architect | Elon Musk |
| SEO & Distribution | Jack Dorsey |
| Monetization Advisor | Bill Ackman |
| Content & Strategy Auditor | Peter Thiel |
| Devil's Advocate | Naval Ravikant |

Full minutes: `ai_council/sessions/2026-05-18/MINUTES.md`

---

## What's Next (from Council Session 7)

1. **Backlink outreach** — CFPB data as hook, "America's Most Responsive Lenders" research piece. Target 10-15 referring domains in 30 days.
2. **Freeze on-page changes** for 3-4 weeks — let Google measure recent work.
3. **Conversion tracking** — quiz/email funnel events.
4. **817 failed_quarantine audit** — ~445 wrongly quarantined. Needs Jammi decision.
5. **HMDA data pages** — linkable asset for outreach.

## 2026-05-19 — Planned Resource Cluster

New plan added: `/srv/BusinessOps/CreditDoc Project Improvement/2026-05-19_DEBT_CREDIT_LETTER_TEMPLATE_LIBRARY_PLAN.md`

Idea: build a CreditDoc-owned Debt And Credit Letter Template Library under
`/resources/`, using only the existing approved resource-page format from
`src/pages/resources/credit-report-checklist/`. Do not create a new layout and
do not copy competitor templates.

Implementation slice completed locally 2026-05-19:

- Shared component: `src/components/LetterTemplatePage.astro`
- Hub: `/resources/debt-credit-letter-templates/`
- Pages:
  - `/resources/debt-credit-letter-templates/debt-validation-letter/`
  - `/resources/debt-credit-letter-templates/cease-and-desist-debt-collector-letter/`
  - `/resources/debt-credit-letter-templates/pay-for-delete-letter/`
- Added hub card to `src/pages/resources/index.astro`.
- `npm run build` passed.
- Deployed 2026-05-19 after founder reported live 404.
- Cloudflare Worker Version ID: `415115ec-4150-471a-a256-f7cef10ba526`
- Verified live `200`:
  - `https://www.creditdoc.co/resources/debt-credit-letter-templates/`
  - `https://www.creditdoc.co/resources/debt-credit-letter-templates/debt-validation-letter/`
  - `https://www.creditdoc.co/resources/debt-credit-letter-templates/cease-and-desist-debt-collector-letter/`
  - `https://www.creditdoc.co/resources/debt-credit-letter-templates/pay-for-delete-letter/`

## 2026-05-21 — Robots/Sitemap Search Console Incident

Founder reported new GSC reason: `Blocked by robots.txt`.

Root cause verified at the time: the new letter pages were not blocked. The
conflict was `https://www.creditdoc.co/search/`: `public/robots.txt` blocked
`/search/`, and Astro sitemap auto-discovered `src/pages/search.astro` and
submitted `/search/` in `sitemap-3.xml`.

Fix shipped 2026-05-21:

- Historical action, superseded 2026-05-25: kept `public/robots.txt` protected
  with the old `/search/` disallow rule.
- Add `@astrojs/sitemap` `filter()` in `astro.config.mjs` to exclude `/search/`.
- Add post-build guard `scripts/check_sitemap_robots_conflicts.mjs`.
- Add `npm run postbuild` so future builds fail if a robots-blocked URL is
  submitted in generated XML sitemaps.
- Cloudflare Worker Version ID: `d21bbcf9-0414-4dd1-8997-d6467a1fe5e0`
- Verified live:
  - `https://www.creditdoc.co/robots.txt` returned `200 text/plain` and still
    contained the old `/search/` disallow rule at that time.
  - `sitemap-0.xml` through `sitemap-3.xml` contain zero `/search/` URLs.
  - Letter-template pages still return `200 text/html`.

Superseded 2026-05-25: this handled sitemap submission, but GSC later showed
parameterized `/search/?state=...` URLs under "Blocked by robots.txt". Because
`/search/` already has `<meta name="robots" content="noindex, nofollow">` and
canonicalizes to `https://www.creditdoc.co/search/`, robots-blocking it prevents
Google from seeing the noindex directive. The correct current policy is:

- keep `/search/` out of XML sitemaps;
- keep `/search/` page-level `noindex, nofollow`;
- do not block `/search/` in `robots.txt`.

Follow-up shipped 2026-05-21:

- Added explicit `/sitemap.xml` route redirecting `301` to `/sitemap-index.xml`
  because live `/sitemap.xml` returned `404` even though robots pointed at the
  correct sitemap index.
- Cloudflare Worker Version ID: `2af08802-edd7-47c6-852f-4a6128d69689`
- Verified live:
  - `https://www.creditdoc.co/sitemap.xml` returns `301` to
    `https://www.creditdoc.co/sitemap-index.xml`.
  - `https://www.creditdoc.co/sitemap-index.xml` returns `200 application/xml`.

## 2026-05-26 — Noindex Cleanup Batch 001

Founder decision: obvious wrong-vertical noindex pages should come off the site
completely, with redirects only where Google has already shown demand.

Batch 001 files:

- Work folder: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Noindex_Review_2026-05-26/`
- Drop batch: `noindex_drop_batch_001_2026-05-26.csv`
- Archive record: `noindex_dropped_archive_batch_001_2026-05-26.json`

Batch 001 action:

- Archived 77 obvious wrong-vertical records in local SQLite and Supabase.
- Categories archived: auto/vehicle/buy-here-pay-here rows, title-service rows,
  passport rows, detective/fraud/wrong-vertical rows.
- Local backup before archive:
  `data/backups/creditdoc_before_noindex_drop_batch_001_20260526T080717Z.sqlite`
- Supabase update succeeded for all 77 rows.
- `src/pages/review/[slug].astro` now redirects the 9 dropped rows that had GSC
  impressions to relevant category or city-guide pages.
- Dropped rows with no GSC demand are intended to leave the site as 404 after
  archive.

Verification:

- `npm run build` passed after the redirect-map change.
- Deployed to Cloudflare Worker version
  `11102048-c6e3-4e3f-b70e-fe92d47d6f1f`.
- Commits:
  - `e5be2bf3ae` — archive batch notes + redirect map.
  - `0c5008f055` — exclude archived review records from static browse data.
- Live checks passed:
  - All 9 GSC-demand dropped review URLs redirect to replacement category or
    city-guide pages.
  - Sample no-demand archived URLs return `404`.
  - The five browse pages that previously linked to archived records now have
    no archived review links.
  - Live `sitemap-0.xml` through `sitemap-4.xml` contain no archived review
    paths; `sitemap-5.xml` returns `404`.

Every future cleanup section must end with live status checks for all touched
pages and a static/browse reference scan.

Same-day GSC audit:

- Report: `/srv/BusinessOps/data/creditdoc_gsc_audit/gsc_audit_2026-05-21.md`
- Inspected 528 URLs across 12 buckets: 253 indexed, 275 not indexed.
- Main non-indexing reason is `URL is unknown to Google`, concentrated in
  brand, browse, compare, state, city, and newer root/guide URLs.
- Review-page non-indexing is mostly `Alternate page with proper canonical tag`;
  sample URLs inspected live during the incident had current `www` canonicals,
  so these rows appear mostly stale from older Google crawls.
- One review URL was reported as `Excluded by noindex tag`:
  `/review/electrical-workers-no-22/`. Local content has
  `processing_status: ready_for_index`; recheck live HTML and GSC after DNS is
  stable before changing content.

---

## CRITICAL RULES

- **NEVER display pricing data.** All pricing fields in DB are unverified AI guesswork. YMYL liability. Can ONLY be re-enabled with written confirmation from Jammi + verified first-party data. See `feedback_creditdoc_no_unverified_pricing.md`.
- **NEVER display unverified data as fact on a financial site.** If it wasn't confirmed by a human or pulled from a verified public source, it doesn't go on the page.

---

## Traffic Reality (GSC 28-day as of 2026-05-16)

| Metric | Value |
|--------|-------|
| Impressions | 25,727 |
| Clicks | 27 |
| CTR | 0.10% |
| Avg position | 27.4 |
| Pages with impressions | 2,355 |

**By type:** /review/ 17,934 imp (70%) | /city/ 624 | /categories/ 89 | /best/ 72 | /blog/ 24 | /answers/ 20

**Best city positions:** Charlotte (2), Detroit (3), College Park (4), Las Vegas (5)

---

## Content Pipelines (all running, all self-feeding)

| Pipeline | Cron | Status |
|----------|------|--------|
| City guides | 04:00 UTC daily | 10/day, 42+ live, target 250 by June 7 |
| Blog posts | 10:00 UTC daily | Auto-refills from CSV topics |
| Wellness guides | 11:00 UTC daily | Self-feeds from answer titles at <10 queue |
| Answer pages | 12:00 UTC daily | Running |
| Indexation | 08:00 UTC daily | Deduped, tier-priority, daily GSC push |
| Content audit | 09:00 UTC daily | Autofix titles/metas + email report |
| Site monitor | */5 minutes | 9 routes + content checks + Harvey alert |

---

## Sendy Email System

| Item | Value |
|------|-------|
| Quiz leads list | `rCzcu8brUim88T892Y85IqRQ` |
| Course list | `Yj7BPjltZ5YG9nUBw892y93g` (ID=2) |
| Autoresponder | ares_id=1, 8 emails, immediately→+21d |
| API key | Stored in the Sendy credential store / environment; do not record secrets in repo docs |
| Login | Stored in the Sendy credential store / password manager; do not record secrets in repo docs |

---

## Current Counts

| Type | Count |
|------|-------|
| Lender profiles (total) | ~15,762 (ready_for_index) |
| CFPB trend pages | 378 (+index, deduped) |
| City x category pages | 756 (42 × 18) |
| Comparison pages | 185 |
| City guides | 42+ |
| Money pages (/best/) | 13 |
| Course pages | 10 |
| Tools/quizzes | 4 |

---

## What NOT to do

- **Don't display any pricing data** — stripped 2026-05-18, needs Jammi written approval + verified data to restore
- Don't make on-page changes for 3-4 weeks — Google needs to measure
- Don't rewrite titles/metas on pages indexed <7 days
- Don't rebuild the inline linker (patch the TS at `src/utils/inline-linker.ts`)
- Don't pause any content pipeline without Jammi approval
- Don't conflate Vercel with CreditDoc (it's Cloudflare Workers)
- Don't display unverified data as fact — ever — on a YMYL financial site


## 2026-05-22 - CreditDoc Click Growth Review Pages Workpack

Saved a memorable review-page SEO workpack at:

`/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Click_Growth_Review_Pages_2026-05-22`

The workpack uses real stored GSC data only. Latest pull used: `pull_id=10`, window `2026-04-17` to `2026-05-15`. It contains top review pages by impressions, page-one review pages, a scored priority worklist, latest top queries, and verified findings from `src/pages/review/[slug].astro`.

Immediate next SEO task: optimise review pages that already have impressions/page-one positions but low or zero clicks, especially commercial categories and pages whose listing status/metadata may be weak. Memory Palace mirror: `/root/.claude/projects/-srv-BusinessOps/memory/creditdoc_click_growth_review_pages_2026-05-22.md`.

## 2026-05-22 - Review Page Growth Plan + Safe Slice

Saved the comprehensive implementation plan:

`/srv/BusinessOps/creditdoc/docs/plans/2026-05-22-review-page-growth.md`

Easy pointer in Project Improvement:

`/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Growth_Plan_2026-05-22.md`

Created Batch 1 from real GSC data only:

`/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Growth_Batch_1_2026-05-22.csv`

Batch notes:

`/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Growth_Batch_1_Notes_2026-05-22.md`

Safe code slice completed locally:

- Added `getAnswersByPillarRuntime()` in `src/lib/db.ts`.
- Added a category-aware `Related Questions` block to `src/pages/review/[slug].astro`, linking review pages to existing `/answers/` rows by answer pillar.
- Fixed the review page mini-quiz category matching so it uses actual slug categories like `credit-repair`, `personal-loans`, and `debt-relief` instead of phrase checks like `credit repair`.
- Ran `npm run build`; build passed, including robots contract, SSR sitemap parity, and sitemap/robots conflict postbuild checks.

No deployment performed. Do not deploy from the current dirty worktree unless the release scope is intentionally reviewed.

## 2026-05-23 - CreditDoc SEO Growth Skill

Created and validated a dedicated Codex skill for CreditDoc SEO work:

`/srv/BusinessOps/.agents/skills/creditdoc-seo-growth/SKILL.md`

Purpose: make future Codex sessions follow the CreditDoc-specific SEO operating method: real GSC data first, database as source of truth, YMYL-safe metadata, review-page batching, internal linking, build verification, and post-change measurement.

Validation: `python3 /root/.codex/skills/.system/skill-creator/scripts/quick_validate.py /srv/BusinessOps/.agents/skills/creditdoc-seo-growth` returned `Skill is valid!`

## 2026-05-23 - Review Page Upgrade Pilot: Marco's Credit Services

Completed the first one-page review upgrade pilot using the protected-page workflow.

Pilot page:

`https://www.creditdoc.co/review/marcos-credit/`

Why this page:

- Batch 1 page with 72 impressions, 0 clicks, average position 4.4.
- `ready_for_index`, `quality_score=11`.
- `is_protected=1`, so it proved the FA/founder-protected workflow.

Reusable template saved:

`/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Template_2026-05-23.md`

Pilot notes saved:

`/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Marcos_Credit_2026-05-23.md`

DB changes applied via `CreditDocDB.update_lender(..., updated_by='founder')`:

- Added `seo_title`: `Marco's Credit Services Review: Credit Repair in Dallas, TX`
- Replaced truncated `meta_description` with a complete factual description.
- Replaced messy/off-category `similar_lenders` with cleaner credit-repair comparables from existing DB rows.

Verification:

- DB update changed 3 fields, with no blocked wipes or replacements.
- `is_protected` remained `1`.
- Audit log recorded all 3 fields changed by `founder`.
- Live page returned `200`.
- Live title/meta/canonical updated.
- Live page has no `noindex`.

## 2026-05-23 - Review Template Deploy For Live Preview

Deployed the reviewed review-page template/runtime slice from an isolated clean worktree, not from the dirty main repo.

Deploy copy:

`/tmp/creditdoc-review-deploy-20260523070435`

Files intentionally included in the deploy copy:

- `astro.config.mjs`
- `package.json`
- `scripts/check_robots_contract.mjs`
- `scripts/check_sitemap_robots_conflicts.mjs`
- `src/pages/sitemap.xml.ts`
- `src/lib/db.ts`
- `src/pages/review/[slug].astro`
- Current local DB mirror copied only for build-time sitemap generation.

Files intentionally not included: unrelated modified `src/content/lenders/*.json` files from the dirty main worktree.

What shipped:

- Review pages now render a category-aware `Related Questions` block from existing `/answers/` rows.
- Review-page mini quiz category scoring now uses real category slugs instead of phrase substring checks.
- Existing sitemap/robots safeguards remained active.

Verification:

- Isolated build passed after copying the current local DB mirror: robots contract OK, SSR sitemap parity OK, `16051` SSR route URLs injected, sitemap/robots postbuild OK.
- `./deploy.sh` succeeded.
- Cloudflare Worker Version ID: `c150ba08-345c-4d94-b7c8-1746f3119764`
- Live smoke checks passed: homepage, CSS, `/credit-guide/austin-tx/`, `/review/lexington-law/`, `/answers/best-debt-consolidation-loans-bad-credit/`, `/best/best-credit-repair-companies/`.
- `https://www.creditdoc.co/review/marcos-credit/` returns `200`, remains indexable, has the new title/meta, and now shows the `Related Questions` block.

## 2026-05-23 - Review Page Stickiness / Intent Bridge Deploy

Added and deployed a compact review-page intent bridge after `Related Questions`.

Purpose: make review pages more useful to real visitors and AI readers without dumping more content onto the page. The section is visible and factual, not hidden SEO text.

What shipped:

- `Quick Summary` with three factual bullets: what the provider is, what the page helps verify, and where the user can continue.
- `Next Steps` links mapped to common visitor intent:
  - Find contact or location
  - Check specific services
  - Match your need via the fit quiz
  - Compare alternatives
  - Improve your position via the relevant financial wellness guide
  - Learn the basics via the free Credit Fundamentals course
- Added section anchors for `#services`, `#contact-location`, `#related-companies`, and existing `#fit-quiz`.

Deploy safety:

- Built and deployed from isolated worktree `/tmp/creditdoc-review-deploy-20260523070435`.
- Repaired the isolated `/tmp/tools/.supabase-creditdoc.env` lookup before deploy so sitemap enrichment matched the main build: 85 city guides, 1530 category sub-pages, 17666 SSR URLs injected.
- Did not include unrelated dirty lender JSON changes.

Verification:

- Main build passed.
- Isolated build passed with full sitemap enrichment and sitemap/robots postbuild check.
- `./deploy.sh` passed.
- Cloudflare Worker Version ID: `aac915bf-29b9-411f-8446-fd1111ac9a4c`
- Live `https://www.creditdoc.co/review/marcos-credit/` returned `200` and contains `Quick Summary`, `Find contact or location`, `Check specific services`, `Match your need`, `Compare alternatives`, `Improve your position`, and `Learn the basics`.

## 2026-05-23 - Review Rollout Order Changed: Raw/Blank Rows First

Jammi corrected the rollout order: before upgrading the clean `ready_for_index`
review pages in normal SEO batches, handle the raw/quarantine/pending and blank
GSC rows first because they are already getting impressions and could receive
potential clicks.

New rollout folder:

`/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/`

Files:

- `README.md` - phased rollout plan.
- `review_page_rollout_queue_250.csv` - full 250-page GSC-visible queue.
- `phase_1_raw_blank_triage_queue.csv` - first-priority risky rows.

Phase 1 audit result from the 250-page GSC priority workpack:

- `53` risky rows total.
- `19` DB-backed raw/quarantine rows are live `404` at the review URL.
- `1` pending page is live `200` with `noindex, nofollow`.
- `32` rows are missing from the local DB under the GSC slug and are live `404`.
- `1` URL-encoded slug join gap: `joyeria-empe%C3%B1os` maps to DB slug `joyeria-empeños` and resolves live.

New execution order:

1. Resolve/classify all `53` risky rows first.
2. Only then start `REVIEW-UPGRADE-01` through `REVIEW-UPGRADE-14` for the `197` clean `ready_for_index` GSC-visible pages.
3. Keep batches small and live-audited; do not do a giant all-pages update.

## 2026-05-23 - Phase 1 Risky Review Queue Cleaned From Live 404s

Phase 1 of the review-page cleanup now has a verified live state:

- `32` risky rows were rescued to DB-backed `pending_approval` pages and return `200` with `noindex, nofollow`.
- `20` true missing/stale GSC review slugs now `302` to relevant live category or city/category pages.
- `1` encoded slug, `joyeria-empe%C3%B1os`, resolves live `200`.
- `0` rows in the Phase 1 risky queue remain live `404`.

Deploy:

- Isolated worktree: `/tmp/creditdoc-review-deploy-20260523070435`.
- Command: `./deploy.sh`.
- Worker Version ID: `fffa9c34-048a-45c0-a8ea-6808ffadc509`.
- Deploy smoke checks passed.

Evidence:

- Queue: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/phase_1_raw_blank_triage_queue.csv`.
- Checkpoint: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/PHASE_1_CHECKPOINT_2026-05-23.md`.

Important:

- The rescued pages are not approved for indexing yet.
- Next work is manual quality review of the `32` pending/noindex rows in small batches: keep noindex, archive, enrich, or approve only after factual review.

Follow-on quality audit:

- Created `phase_1_pending_noindex_quality_review_queue.csv`.
- Created `PHASE_1_PENDING_NOINDEX_QUALITY_REVIEW.md`.
- Initial split: `12` rows need enrichment/manual review before indexing; `20` rows should stay noindex or be considered for archive/rebuild after validation.
- Redirected 3 suspect rescued profiles instead of showing weak/bad review pages: `greater-metro`, `jm-auto-title-service-titulos-y-placas-surety-bond-title`, `the-ivy-league-solutions`.
- Increased sitemap city-guide fetch timeout from `5s` to `20s`; verified full sitemap enrichment before deploy.
- Follow-up Worker Version ID: `b3b57d61-d978-4201-a9d2-5d947b8eee8f`.
- Final Phase 1 audit: `29` rescued rows are `200 noindex,nofollow`; `23` rows are `302` to live `200` destinations; `1` encoded slug resolves `200`; `0` rows remain live `404`.
- Added factual DB-backed `seo_title` and `meta_description` to the 9 manual-review lane rows. Live verification confirmed updated titles/metas are visible and all 9 still return `noindex, nofollow`.
- Final follow-up redirected 4 additional mismatched hold-lane pages. Latest Worker Version ID: `f599f32b-a481-416e-924f-294c1e5d3fc3`.
- Current final Phase 1 audit: `25` rescued rows are `200 noindex,nofollow`; `27` rows are `302` to live `200` destinations; `1` encoded slug resolves `200`; `0` rows remain live `404`.
- Jammi approved `tax-debt-relief-alphabet-city` after manual review. DB-only update set it `ready_for_index`, removed `no_index`, and marked `review_status=approved`; live verification confirmed no robots `noindex`.
- Current queues were uploaded to Google Drive as Google Sheets in `SEO Reports / CreditDoc`.
- Operating rule: individual manual approvals are incremental DB updates. Do not rebuild/redeploy the full site for each single approval; batch sitemap refreshes unless immediate sitemap deployment is specifically requested.
- Manual review correction: Jammi said the original list was not good; treat the Phase 1 list as a cleanup worklist, not approval-ready pages.
- Rejected/held: `ny-identity-theft-group` category mismatch, `four-brothers-money-orders-and-bill-payment` missing content.
- Deleted/archived: `luxury-lifestyles-the-buying-house`.
- Vigo group: 45 Vigo records removed from index eligibility via DB-only updates (`no_index=true`, `review_status=needs_vigo_group_rework`, `vigo_group_fix_required=true`; ready rows moved to `pending_approval`). Representative live checks confirmed `noindex,nofollow`.
- Drive sheets refreshed: `CreditDoc Phase 1 Cleanup Worklist - 2026-05-23` and `CreditDoc Vigo Group Fix Audit - 2026-05-23`.

Vigo follow-up repair completed 2026-05-23:

- DB backup before writes: `data/backups/creditdoc_before_vigo_chain_repair_2026-05-23.sqlite`.
- Patched `tools/creditdoc_db.py` so `CreditDocDB.update_lender()` carries `brand_slug` and `state` through local catalog writes and Supabase upsert payloads.
- Applied DB-only noindex-safe chain/location repair to all 45 Vigo rows:
  - `brand_slug=vigo`
  - `category=check-cashing`
  - `processing_status=pending_approval`
  - `no_index=true`
  - `review_status=chain_repaired_pending_founder_review`
  - factual location-led title/meta/description/best_for/pros/cons from existing DB fields only
- Verification:
  - `python3 -m py_compile tools/creditdoc_db.py` passed.
  - Local DB count: 45 Vigo rows under `brand_slug=vigo`, `category=check-cashing`, `pending_approval`, `no_index=true`.
  - Supabase samples (`vigo-kansas-city`, `vigo-seattle-wa`, `vigo-long-beach`, `vigo-west-new-york`) show `brand_slug=vigo`, `category=check-cashing`, `no_index=true`.
  - Live samples still show `noindex,nofollow` and now show location-led Vigo copy.
- Report: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/VIGO_CHAIN_REPAIR_2026-05-23.md`.
- Applied CSV: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/CreditDoc_vigo_chain_repair_applied_2026-05-23.csv`.
- Do not index Vigo until Jammi samples the batch. Create/review a `/brand/vigo/` record before any future promotion.

# CreditDoc Review Page Regulatory Context Discovery - 2026-05-23

Jammi identified that CreditDoc's regulatory data layer should be one of the strongest differentiators and expected it to be wired into review pages. Discovery confirmed it is only partially wired.

Key finding:

- Federal/company regulator data is present in `/srv/BusinessOps/creditdoc/data/regulator.db` and synced to Supabase tables:
  - `regulator_company_stats`
  - `regulator_enforcement`
  - `regulator_sba_rankings`
- State-law regulatory data is present in Supabase `states.body_inline` and local `src/content/states.json`.
- Local `state_regulatory_data` table exists in `creditdoc.db`, but has `0` rows and is not available in Supabase.
- Review pages currently render only company-level regulator data through `getRegulatorDataRuntime(lender.slug, env)` in `src/lib/db.ts` / `src/pages/review/[slug].astro`.
- `getRegulatorDataRuntime()` is gated by `ENABLE_REGULATOR_BLOCKS=true` and only returns data when a matched company has `match_confidence >= 0.85` and `total_complaints_alltime >= 5`.
- Vigo has no company-level CFPB/enforcement match in `regulator.db`, so no regulator block appears.
- State-law data is already used on `/state/`, `/state/[slug]/lending-laws/`, `/city/`, `/browse/`, and `/credit-guide/`, but it is not wired into `/review/[slug]/`.

Strategic conclusion:

- The next high-leverage quality improvement is a reusable review-page `State Consumer Finance Context` / `Regulatory Context` block.
- It should fetch existing `states.body_inline` by lender `company_info.state` / state abbreviation and render conservative, category-aware state context.
- This is a major differentiator: directory + location + services + regulatory context.

Safe wording rules:

- Present state-level consumer finance context only.
- Do not claim a specific lender/location is licensed unless direct license proof is present.
- Do not apply FDIC/NCUA/HMDA data unless the lender record is actually matched to bank/credit-union/mortgage data.
- For Vigo/check-cashing/money-services pages, use state regulator, complaint resources, payday/installment/check-cashing/money-services context where available; avoid bank-specific claims.

Recommended implementation order:

1. Add a reusable review-page regulatory context component fed from `states.body_inline`.
2. Show it only when the lender has a state.
3. Start with noindexed Vigo pages as pilot.
4. Verify wording/live rendering while noindexed.
5. Roll out more broadly to review pages after build/deploy review.
6. Later enrich state data further with official money-transmitter/check-casher license lookup URLs where verifiable.

Important: This touches YMYL presentation. Keep language factual and cautious. No unverified licensing, pricing, or compliance claims.

Implementation progress 2026-05-23:

- Added `src/components/StateRegulatoryContext.astro`.
- Wired `/review/[slug]/` to fetch `getStateByCodeRuntimeFromDb(stateAbbr, env)` and render the new block when a lender row has a resolvable state.
- The block is deliberately conservative:
  - labels the section as state-level consumer finance context;
  - says it does not confirm that the lender or location is licensed;
  - separates this from company-specific CFPB/enforcement/HMDA blocks;
  - shows state regulator, consumer protection agency, complaint resources, selected statute links, and category-aware credit/loan/money-services context from existing `states.body_inline`.
- Verification: `npm run build` passed on 2026-05-23, including prebuild robots/parity checks and postbuild sitemap/robots conflict check.
- No deploy was performed in this step.
- Sequencing remains: finish the original Phase 1 bad-page cleanup / 33-page work first, then move to the 250 review-page upgrade queue in controlled batches.

Phase 1 status tidy 2026-05-23:

- Created DB backup: `data/backups/creditdoc_before_phase1_status_tidy_2026-05-23.sqlite`.
- Marked 9 noindexed Phase 1 hold rows with explicit `review_status` values so they stop appearing as generic `draft` rows:
  - 7 weak rows -> `quality_hold_noindex_needs_validation`
  - `ny-identity-theft-group` -> `category_mismatch_noindex_founder_review`
  - `four-brothers-money-orders-and-bill-payment` -> `content_rebuild_required_noindex_founder_review`
- All 9 remain `processing_status=pending_approval` and `no_index=true`.
- Supabase mirror verified after replaying 6 timed-out writes from the retry queue.
- Live spot checks confirmed `noindex,nofollow` for `ny-identity-theft-group`, `four-brothers-money-orders-and-bill-payment`, and `the-debt-crushers`.
- Created cleaned queue: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/phase_1_remaining_action_queue_2026-05-23.csv`.
- Remaining Phase 1 action rows: 17.
- Report: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/PHASE_1_STATUS_TIDY_2026-05-23.md`.

Phase 1 validation classification 2026-05-23:

- Created DB backup: `data/backups/creditdoc_before_phase1_validation_classification_2026-05-23.sqlite`.
- Classified 9 weak/rejected noindex rows using public validation evidence where available.
- Category-corrected `envios-de-dinero-money-orders-pago-de-billes` from `emergency-cash` to `check-cashing` because it is a money-transfer / money-orders / bill-payment listing and CreditDoc's closest category is `Check Cashing & Money Services`.
- Added `validation_notes` and specific `review_status` values for:
  - `the-debt-crushers`
  - `a-loans-checks-cashed`
  - `fix-my-auto-credit-score`
  - `my-credit-advice-credit-repair-and-consultation`
  - `envios-de-dinero-money-orders-pago-de-billes`
  - `808-credit-pros`
  - `dac-credit-repair`
  - `ny-identity-theft-group`
  - `four-brothers-money-orders-and-bill-payment`
- All affected rows remain `pending_approval` and `no_index=true`.
- Supabase mirror verified; pending retry rows for these slugs: `0`.
- Report: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/PHASE_1_VALIDATION_CLASSIFICATION_2026-05-23.md`.
- Classified CSV: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/phase_1_remaining_action_queue_classified_2026-05-23.csv`.

Phase 1 manual-candidate classification 2026-05-23:

- Created backup: `data/backups/creditdoc_before_phase1_manual_candidate_classification_2026-05-23.sqlite`.
- Classified all 8 metadata-enriched manual-review rows; all remain `pending_approval` and `no_index=true`.
- Notable findings:
  - `ez-credit-disputes` is BBB-validated as credit repair, but stored website is wrong.
  - `snap-loans-cash-orlando` official site returns 200, but needs YMYL review before indexing because it is loan matching / lead-gen.
  - `life-changers-agency` appears to be tax preparation, not credit repair.
  - `rose-financial-solutions` official site is outsourced finance/accounting/FaaS, not consumer credit repair.
  - `credit-repair-outfit-philadelphia` has public listing evidence, but stored website is likely wrong.
- Supabase mirror verified; pending retry rows: `0`.
- Final decision matrix saved:
  - `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/phase_1_final_decision_matrix_2026-05-23.csv`
  - `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/PHASE_1_FINAL_DECISION_MATRIX_2026-05-23.md`

Phase 1 wrong website cleanup 2026-05-23:

- Created backup: `data/backups/creditdoc_before_phase1_wrong_website_cleanup_2026-05-23.sqlite`.
- Removed clearly wrong/nonfunctional website fields from 4 noindexed rows:
  - `credit-repair-outfit-philadelphia`
  - `ez-credit-disputes`
  - `rose-financial-solutions`
  - `crushing-on-credit`
- All 4 remain `processing_status=pending_approval` and `no_index=true`.
- Supabase retry rows for these 4 slugs: `0`.
- Live verification confirmed all 4 still show `noindex,nofollow`, and removed outbound domains no longer appear in the live HTML.
- Report: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/PHASE_1_WRONG_WEBSITE_CLEANUP_2026-05-23.md`.
- Remaining issue: some noindexed generated page copy/schema can still carry old category assumptions. Next pass should decide archive, redirect, rebuild, or manual approval before any indexing.

Review held-page schema guard 2026-05-23:

- Updated `src/pages/review/[slug].astro` so held/skeleton/noindexed pages emit breadcrumb schema only.
- Ready/indexable review pages keep existing entity/review/aggregate-rating/FAQ schema behavior.
- Removed stale fallback meta wording that said `review with pricing, ratings, and features`; fallback now uses services/contact/review signals/alternatives.
- Verification: `npm run build` passed, including robots contract, SSR sitemap parity, and sitemap/robots conflict check.
- No deploy was performed.
- Report: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/REVIEW_HELD_PAGE_SCHEMA_GUARD_2026-05-23.md`.

Phase 1 decision buckets and neutralization 2026-05-23:

- Added durable `phase1_decision_*` fields to the 17 remaining held rows.
- Refreshed queue:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/phase_1_decision_bucket_queue_2026-05-23.csv`
- Neutralized visible generated claims on 12 unresolved rows so accidental visitors see held-for-review copy instead of confident category/service claims:
  - archive candidates: `808-credit-pros`, `fix-my-auto-credit-score`, `four-brothers-money-orders-and-bill-payment`
  - archive/redirect candidates: `ny-identity-theft-group`, `rose-financial-solutions`, `life-changers-agency`
  - source/category/location holds: `a-loans-checks-cashed`, `dac-credit-repair`, `my-credit-advice-credit-repair-and-consultation`, `the-debt-crushers`, `mycredit-smash`, `the-peeples-solution`
- Removed TaxBuzz website/logo from `life-changers-agency`.
- Rebuilt `envios-de-dinero-money-orders-pago-de-billes` as conservative money-services copy; still noindexed pending manual review.
- Cleaned `ez-credit-disputes` as a manual approval candidate after wrong website removal; still noindexed pending manual review.
- All 17 rows remain `pending_approval` and `no_index=true`.
- Supabase unresolved retry rows for these 17 slugs: `0`.
- No `REVALIDATE_TOKEN` was present in `/srv/BusinessOps/.env`, so cache revalidation was not forced.
- No deploy was performed.
- Report: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/PHASE_1_DECISION_BUCKET_AND_NEUTRALIZATION_2026-05-23.md`.

Phase 1 final three neutralization 2026-05-23:

- Neutralized the remaining 3 non-neutral held pages:
  - `snap-loans-cash-orlando`
  - `credit-repair-outfit-philadelphia`
  - `crushing-on-credit`
- Removed outbound `orlando.snaploans.cash` and logo from `snap-loans-cash-orlando` while YMYL/manual review is pending.
- All 17 remaining Phase 1 rows remain `pending_approval` and `no_index=true`.
- Full Phase 1 state now:
  - 15 neutralized held pages
  - 1 rebuilt pending manual review: `envios-de-dinero-money-orders-pago-de-billes`
  - 1 cleaned pending manual review: `ez-credit-disputes`
- Narrow scan of the 15 neutralized rows found no remaining dollar loan amounts, next-business-day funding, bad-credit marketing, guarantee/money-back language, verified-lender claims, or inflated 5.0/exceptional-reputation phrasing in visible description/pros/cons/service fields.
- Supabase unresolved retry rows for the final 3 slugs: `0`.
- No deploy was performed.
- Report: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/PHASE_1_FINAL_THREE_NEUTRALIZATION_2026-05-23.md`.

Phase 1 final treatment labels 2026-05-23:

- Added proposed final-treatment labels to the 15 neutralized held rows.
- No redirects were implemented; this is decision labeling only.
- Queue:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/phase_1_neutralized_final_treatment_queue_2026-05-23.csv`
- Treatment counts:
  - `archive_hold`: 5
  - `redirect_candidate`: 3
  - `hold_for_research`: 4
  - `hold_for_manual_review`: 1
  - `resolve_or_redirect_candidate`: 1
  - `ymyl_hold_or_redirect_candidate`: 1
- All labeled rows remain `pending_approval` and `no_index=true`.
- Supabase unresolved retry rows for the 15 labeled slugs: `0`.
- No deploy was performed.
- Report: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/PHASE_1_FINAL_TREATMENT_LABELS_2026-05-23.md`.

Phase 1 review deploy 2026-05-23:

- Deployed via `/srv/BusinessOps/creditdoc/deploy.sh`.
- Build, deploy, cache purge, and smoke checks passed.
- Worker version: `24ffa62d-d8ba-48fa-b8b3-c7c60b0ffa35`.
- Live checks confirmed:
  - `snap-loans-cash-orlando` is held/noindex and the removed Snap outbound domain did not appear.
  - `ez-credit-disputes` is noindex.
  - `envios-de-dinero-money-orders-pago-de-billes` is noindex with rebuilt money-services copy.
  - `lexington-law` still emits rich review schema signals.
- Report: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/PHASE_1_REVIEW_DEPLOY_2026-05-23.md`.

Founder live review approvals 2026-05-23:

- Jammi reviewed and approved these live pages as acceptable:
  - `ez-credit-disputes`
  - `envios-de-dinero-money-orders-pago-de-billes`
- Database fields added:
  - `founder_review_status=approved_by_jammi`
  - `phase1_manual_review_result=approved_for_next_indexing_decision`
  - `founder_reviewed_at=2026-05-23`
- Both pages remain `no_index=true` until an explicit indexing batch decision.
- Backup before approval markers:
  `data/backups/creditdoc_before_jammi_manual_approvals_2026-05-23.sqlite`

Lexington Law approval 2026-05-23:

- Jammi reviewed and approved `lexington-law` live page quality.
- Current status remains `ready_for_index`; `no_index=false`.
- Added `founder_review_status=approved_by_jammi` and
  `founder_reviewed_at=2026-05-23`.
- Backup before marker:
  `data/backups/creditdoc_before_jammi_lexington_approval_2026-05-23.sqlite`

Phase 1 remaining resolution pass 2026-05-23:

- Closed 5 archive-hold rows as excluded from future review upgrade/index queues
  unless new source evidence appears:
  `808-credit-pros`, `a-loans-checks-cashed`, `dac-credit-repair`,
  `fix-my-auto-credit-score`, `four-brothers-money-orders-and-bill-payment`.
- Marked 3 category-mismatch pages as redirect-ready holds, but did not
  implement redirects:
  `life-changers-agency`, `ny-identity-theft-group`,
  `rose-financial-solutions`.
- Marked rebuild candidates:
  `the-debt-crushers`, `crushing-on-credit`.
- Kept research holds:
  `credit-repair-outfit-philadelphia`,
  `my-credit-advice-credit-repair-and-consultation`, `mycredit-smash`,
  `the-peeples-solution`.
- Kept `snap-loans-cash-orlando` as YMYL lead-generation hold.
- All 15 remain `no_index=true`; unresolved Supabase retry rows: `0`.
- Queue:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/phase_1_remaining_resolution_queue_2026-05-23.csv`
- Split queues:
  - `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/phase_1_rebuild_candidates_2026-05-23.csv`
  - `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/phase_1_redirect_candidates_2026-05-23.csv`
  - `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/phase_1_research_and_ymyl_holds_2026-05-23.csv`
- Live verification after classification: all 15 URLs return `200`, show
  `noindex`, and do not emit `FinancialService` or `FAQPage` schema.
- Report:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/PHASE_1_REMAINING_RESOLUTION_PASS_2026-05-23.md`

The Debt Crushers rebuild 2026-05-23:

- Rebuilt `the-debt-crushers` from reachable official-site evidence.
- Added cautious location caveat because sources reference both San Francisco
  origin/listing evidence and Las Vegas expansion.
- Kept `no_index=true`.
- Set `review_status=rebuilt_pending_location_review_noindex`.
- Set `founder_review_status=pending_jammi_review`.
- Live check: page returns `200`, includes the rebuilt wording, remains
  `noindex`, and does not emit `FinancialService` or `FAQPage` schema.
- Report:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/THE_DEBT_CRUSHERS_REBUILD_2026-05-23.md`

Crushing on Credit rebuild 2026-05-23:

- Rebuilt `crushing-on-credit` from trademark evidence and third-party New York
  credit-repair listing evidence.
- Kept provider website removed/unlinked because SSL/default-hosting issues
  remain.
- Kept `no_index=true`.
- Set `review_status=rebuilt_pending_source_review_noindex`.
- Set `founder_review_status=pending_jammi_review`.
- Live check: page returns `200`, includes rebuilt credit consultation/credit
  restoration wording, remains `noindex`, and does not emit `FinancialService`
  or `FAQPage` schema.
- Report:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/CRUSHING_ON_CREDIT_REBUILD_2026-05-23.md`

My Credit Advice rebuild 2026-05-23:

- Rebuilt `my-credit-advice-credit-repair-and-consultation` as a cautious
  noindex source-hold page from third-party address/phone/category evidence.
- Kept explicit caveat that `mycreditadvice.com` still fails DNS from the VPS.
- Kept `no_index=true`.
- Set `review_status=rebuilt_third_party_source_hold_noindex`.
- Set `founder_review_status=pending_jammi_review`.
- Live check: page returns `200`, includes rebuilt Miami Gardens / DNS caveat,
  remains `noindex`, and does not emit `FinancialService` or `FAQPage` schema.
- Report:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/MY_CREDIT_ADVICE_REBUILD_2026-05-23.md`

Credit Repair Outfit Philadelphia rebuild 2026-05-23:

- Rebuilt `credit-repair-outfit-philadelphia` as a cautious noindex source-check
  page from exact third-party listing evidence.
- Kept explicit caveat that no provider-owned website/source has been verified.
- Kept `no_index=true`.
- Set `review_status=rebuilt_thin_source_hold_noindex`.
- Set `founder_review_status=pending_jammi_review`.
- Live check: page returns `200`, includes the rebuilt third-party-source
  caveat, remains `noindex`, and does not emit `FinancialService` or `FAQPage`
  schema.
- Report:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/CREDIT_REPAIR_OUTFIT_REBUILD_2026-05-23.md`

Snap Loans Cash Orlando YMYL rebuild 2026-05-23:

- Rebuilt `snap-loans-cash-orlando` as a cautious noindex YMYL lead-generation
  page.
- Added clear marketplace / not-a-direct-lender / third-party-provider caveats.
- Kept `no_index=true` and did not restore outbound provider link.
- Set `review_status=rebuilt_ymyl_leadgen_hold_noindex`.
- Set `founder_review_status=pending_jammi_review`.
- Live check: page returns `200`, includes the rebuilt lead-gen caveat, remains
  `noindex`, does not emit `FinancialService` or `FAQPage` schema, and
  `orlando.snaploans.cash` remains absent.
- Report:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/SNAP_LOANS_CASH_ORLANDO_YMYL_REBUILD_2026-05-23.md`

Phase 1 current outcome 2026-05-23:

- Closed archive holds: 6.
- Closed category-mismatch redirect-ready holds: 3.
- Closed category-mismatch hold: 1.
- Rebuilt / pending Jammi review or source policy: 5.
- Pending Jammi review queue:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/phase_1_rebuilt_pending_jammi_review_2026-05-23.csv`
- Final safety verification: all 15 held URLs return `200`, remain `noindex`,
  emit no `FinancialService` schema, emit no `FAQPage` schema.
- Unresolved Supabase retry rows for the batch: `0`.

Review upgrade batch 01 meta cleanup 2026-05-23:

- Updated SEO titles/metas for 15 `REVIEW-UPGRADE-01` pages from the 250-page
  rollout queue.
- No index status changes.
- All titles <=65 chars; all metas <=155 chars.
- Unresolved Supabase retry rows: `0`.
- Live spot checks confirmed updated title/meta output and no accidental
  noindex on sampled pages.
- CSV:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/review_upgrade_01_meta_updates_2026-05-23.csv`
- Report:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/REVIEW_UPGRADE_01_META_2026-05-23.md`

Review upgrade batch 02 meta cleanup 2026-05-23:

- Updated SEO titles/metas for 15 `REVIEW-UPGRADE-02` pages from the 250-page
  rollout queue.
- No index status changes.
- All titles <=65 chars; all metas <=155 chars.
- Unresolved Supabase retry rows: `0`.
- Live spot checks confirmed updated title/meta output and no accidental
  noindex on sampled pages.
- CSV:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/review_upgrade_02_meta_updates_2026-05-23.csv`
- Report:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/REVIEW_UPGRADE_02_META_2026-05-23.md`

Review upgrade batch 03 meta cleanup 2026-05-23:

- Updated SEO titles/metas for 15 `REVIEW-UPGRADE-03` pages from the 250-page
  rollout queue.
- No index status changes.
- All titles <=65 chars; all metas <=155 chars.
- Unresolved Supabase retry rows: `0`.
- Live spot checks confirmed updated title/meta output and no accidental
  noindex on sampled pages.
- CSV:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/review_upgrade_03_meta_updates_2026-05-23.csv`
- Report:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/REVIEW_UPGRADE_03_META_2026-05-23.md`

Review upgrade batch 04 meta cleanup 2026-05-23:

- Updated SEO titles/metas for 15 `REVIEW-UPGRADE-04` pages from the 250-page
  rollout queue.
- No index status changes.
- All titles <=65 chars; all metas <=155 chars.
- Unresolved Supabase retry rows: `0`.
- Live spot checks confirmed updated title/meta output and no accidental
  noindex on sampled pages.
- CSV:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/review_upgrade_04_meta_updates_2026-05-23.csv`
- Report:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/REVIEW_UPGRADE_04_META_2026-05-23.md`

Review upgrade batch 05 meta cleanup 2026-05-23:

- Updated SEO titles/metas for 15 `REVIEW-UPGRADE-05` pages from the 250-page
  rollout queue.
- No index status changes.
- All titles <=65 chars; all metas <=155 chars.
- Unresolved Supabase retry rows: `0`.
- Live spot checks confirmed updated title/meta output and no accidental
  noindex on sampled pages.
- Total review upgrade meta updates completed today: `75`.
- CSV:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/review_upgrade_05_meta_updates_2026-05-23.csv`
- Report:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/REVIEW_UPGRADE_05_META_2026-05-23.md`

Review rollout 250 completion 2026-05-23:

- Completed all 250 rows in
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/review_page_rollout_queue_250.csv`.
- Updated metadata for `REVIEW-UPGRADE-01` through `REVIEW-UPGRADE-14`:
  197 queue rows / 196 unique DB slugs due one duplicate queue slug.
- Resolved encoded HOLD-JOIN slug `joyeria-empe%C3%B1os` to DB slug
  `joyeria-empeños` and updated metadata.
- Classified all `TRIAGE-DATA` and `HOLD-JOIN` rows instead of forcing unsafe
  normal upgrades.
- Completion CSV:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/review_rollout_250_completion_status_2026-05-23.csv`
- Verification:
  - every queue row has a recorded outcome;
  - no SEO title over 65 chars where present;
  - no meta over 155 chars where present;
  - queue-specific unresolved Supabase retry rows: `0`;
  - sampled live pages showed updated metadata and correct index/noindex state.
- Report:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/REVIEW_ROLLOUT_250_COMPLETION_2026-05-23.md`

Git cleanup and autonomous engine stop 2026-05-25:

- Archived 577 dirty generated lender JSON versions to:
  `/srv/BusinessOps/CreditDoc Project Improvement/git-cleanup-2026-05-25/`
- Restored `src/content/lenders/*.json` tracked files because the database is
  the source of truth and the dirty changes were generated/export churn.
- Found the active writer: `creditdoc-engine.service` was still running
  `/srv/BusinessOps/tools/creditdoc_engine_loop.sh` even though the cron entry
  for `creditdoc_autonomous_engine.py` had been disabled.
- Stopped and disabled `creditdoc-engine.service`.
- Set `/etc/systemd/system/creditdoc-engine.service` to `Restart=no`.
- Added an explicit guard to `/srv/BusinessOps/tools/creditdoc_engine_loop.sh`;
  it now exits unless `/srv/BusinessOps/tools/.creditdoc-engine-enabled`
  exists.
- Do not restart this engine without Jammi approval. If it is intentionally
  restarted later, first verify it no longer writes operational metadata such as
  `last_engine_run` into tracked lender JSON files.

Autonomous growth ops plan ready for activation 2026-05-25:

- Plan file:
  `/srv/BusinessOps/creditdoc/docs/plans/2026-05-25-autonomous-creditdoc-growth-ops-plan.md`
- Commit:
  `bd0355b00c Plan autonomous CreditDoc growth ops`
- Google Drive copy:
  `https://drive.google.com/file/d/1pzPBFUtP4lVoFnQj3yKYJ7JHHxPeOdhb/view?usp=drivesdk`
- Email sent to `gian.eao@gmail.com` using the correct AgentMail path:
  `/srv/BusinessOps/.venv/bin/python /srv/BusinessOps/tools/harvey_email.py send ...`
- Do not use system `python3` for AgentMail. The `agentmail` dependency is in
  the BusinessOps venv.
- Tomorrow's intended action: activate the autonomous CreditDoc growth operating
  loop from the plan, starting with safe daily checks, GSC workpack generation,
  repo cleanliness, automation status, and live URL status verification. Keep
  `creditdoc-engine.service` stopped unless Jammi explicitly approves restart.

Search robots/noindex regression prevention 2026-05-26:

- Problem: the 2026-05-21 fix excluded `/search/` from XML sitemaps but left
  `Disallow: /search/` in `robots.txt`, and the build contract required that
  old rule. GSC then surfaced `/search/?state=Utah`, `/search/?state=Iowa`, and
  `https://creditdoc.co/search/` under "Blocked by robots.txt".
- Permanent policy: `/search/` and parameterized search URLs must be crawlable
  but not indexable. Keep them out of XML sitemaps, keep page-level
  `noindex,nofollow`, canonical to `https://www.creditdoc.co/search/`, and do
  not robots-block `/search/`.
- Commit `1d02f03cd2 Allow search noindex crawling` removed the robots block and
  changed `scripts/check_robots_contract.mjs` so future builds fail if the old
  `/search/` robots block returns.
- Added live operational guards outside the repo:
  `/srv/BusinessOps/tools/creditdoc_smoke_test.py` now checks this daily, and
  `/srv/BusinessOps/tools/creditdoc_site_monitor.sh` checks it once every
  24 hours at 05:30 UTC.
- Verification on 2026-05-26: smoke test passed `10/10`; site monitor exited
  `0`; live `robots.txt` does not block `/search/`; live search URL has
  `noindex,nofollow` and canonical to `/search/`.

Content engine firing verification 2026-05-26:

- Jammi clarified that CreditDoc content engines firing every working day is
  non-negotiable: blog, financial wellness/health, city guides, and
  questions/answers must run on schedule.
- Added `/srv/BusinessOps/tools/creditdoc_content_engine_daily_verify.py`.
  It does not generate content; it verifies today's scheduled engine logs after
  all weekday engines are due and emails Jammi if any required engine did not
  fire or did not show a success marker.
- Added weekday cron:
  `45 16 * * 1-5 /srv/BusinessOps/.venv/bin/python3 /srv/BusinessOps/tools/creditdoc_content_engine_daily_verify.py >> /srv/BusinessOps/logs/creditdoc_content_engine_verify.log 2>&1`
- Crontab backup:
  `/srv/BusinessOps/backups/crontab-before-creditdoc-content-engine-verifier-20260526T060638Z.txt`
- Manual verifier run at 2026-05-26 06:06 UTC confirmed:
  blog scheduler already fired; blog generator, city guides, questions/answers,
  financial wellness, and comparisons were correctly pending because their
  scheduled times had not arrived.

Content engine queue reserve guard 2026-05-26:

- Expanded `/srv/BusinessOps/tools/creditdoc_content_engine_daily_verify.py`
  so it checks queue reserves as well as same-day firing:
  blog queue, city guide queue, questions/answers clusters, financial wellness
  queue, and comparison queue.
- Queue thresholds at time of change:
  blog minimum 10 pending, city guides minimum 100 tracked, answers minimum
  50 pending, wellness minimum 10 remaining, comparisons minimum 50 remaining.
  The legacy content drip queue is not a daily growth queue.
- Found a real near-miss: blog queue had only 5 pending items. Tightened
  `/srv/BusinessOps/tools/creditdoc_blog.py` so it auto-refills when pending
  count is `<= 10`, not only `< 5`.
- Refilled the blog queue through the existing question-bank refill path.
  It rose from 5 pending to 20 pending, then today's blog runs generated new
  posts and left 16 pending.
- Found another real reliability bug: Anthropic SDK calls could hang because
  the timeout was only applied to the CLI fallback. Added SDK request timeouts
  in the blog generator, city guide generator, shared `creditdoc_oauth.py`, and
  autonomous engine helper.
- Added a conservative timeout to `/srv/BusinessOps/tools/cron_alert.py`:
  default 3600 seconds, configurable with `CRON_ALERT_TIMEOUT_SECS`. Hung cron
  jobs now exit `124` and send the same AgentMail failure alert instead of
  running silently forever.
- Verification at 2026-05-26 06:37 UTC:
  `creditdoc_content_engine_daily_verify.py --dry-run --allow-pending` passed
  all due/pending engine checks and all queue reserve checks.
- Today's blog generation verified live:
  `/blog/are-credit-card-balance-transfers-a-good-idea/`,
  `/blog/are-credit-card-balance-transfers-worth-it/`,
  `/blog/are-credit-card-interest-rates-capped/`, and
  `/blog/are-credit-card-interest-rates-going-down/` all returned HTTP 200.

CreditDoc lender/business onboarding drip disabled 2026-05-26:

- Jammi confirmed the lender/business onboarding drip should not run daily.
  It should be treated as a periodic refresh job, likely once or twice per
  year, to discover new businesses and identify closed businesses.
- Disabled the daily noon cron by commenting it out:
  `creditdoc-content-drip / creditdoc_content_drip.py`.
- Crontab backup before the change:
  `/srv/BusinessOps/backups/crontab-before-disable-creditdoc-content-drip-20260526T070607Z.txt`
- Removed content drip from the daily content-engine verifier so it does not
  alert on a deliberately disabled job.
- During this change, 41 generated lender JSON diffs reappeared with the same
  export metadata churn pattern (`last_engine_run` / `brand_slug`). They were
  restored because the database remains the source of truth.

Bottom-up local authority + CFPB responsiveness project 2026-05-26:

- Jammi clarified the strategic reason for the city/small-town guide buildout:
  CreditDoc is intentionally coming at incumbents from local and regional
  markets they ignore, building a web of small-town/city guides, city-category
  pages, lender/entity pages, state regulations, maps/directions, local help,
  and question clusters.
- Do not interpret city-guide velocity as generic doorway-page expansion. The
  existing pages, e.g. `/credit-guide/amarillo-tx/`, include local context,
  state regulations, maps/directions/entity links, HMDA/lender data, local
  resources, and question-cluster links. This is a core moat, not a side quest.
- Strategic model:
  `research authority + state law pages + city guides + city/category pages + lender profiles + question clusters + tools/quizzes`.
- A future artifact should document this as the **CreditDoc Local Authority
  Graph** so the linking strategy remains explicit across sessions.
- CFPB/data research already exists (`/research/consumer-complaints/`,
  `/research/lending-transparency/`,
  `/research/state-of-subprime-lending-2026/`, `/about/creditdoc-data/`,
  `/trends/[slug]/`). The current gap is packaging and distribution, not raw
  data availability.
- New plan added:
  `docs/plans/2026-05-26-cfpb-responsiveness-report.md`
- Working title: **America's Most Responsive Consumer Finance Providers 2026**.
  Use positive framing only. No "worst lender" or adversarial CFPB pages.
- Goal: create an outreach-ready backlink/authority asset from CFPB complaint
  response data with methodology, caveats, provider-friendly citation hooks,
  press pitch, and internal links into the local authority graph.
- Current build sequence: inspect regulator data, generate candidate ranking
  CSV, manually review duplicates/mismatches, finalize scoring, then build the
  public research page and outreach assets.
- First candidate CSVs generated:
  `/srv/BusinessOps/CreditDoc Project Improvement/CFPB_Responsiveness_Report_2026-05-26/`
- Initial candidate set: 131 deduped CFPB/provider rows after
  `match_confidence >= 0.85`, all-time complaints >=25, and available response
  metrics. All map to `ready_for_index` CreditDoc rows, but manual review is
  required before publication.
- First-pass issue: category/profile mismatches appear in the top candidates
  (example: `Goldman Sachs Bank USA` mapped to `pawn-shops`; `BMO Bank National
  Association` mapped to `personal-loans`). Do not build the public report until
  top candidates are manually classified.
- Regulator match/category cleanup plan added:
  `docs/plans/2026-05-26-regulator-match-category-cleanup.md`
- Phase 1 audit queue created:
  `/srv/BusinessOps/CreditDoc Project Improvement/CFPB_Responsiveness_Report_2026-05-26/regulator_match_category_audit_phase1_2026-05-26.csv`
- Initial top-50 classification found 3 obvious category-fix candidates
  (`goldman-sachs-bank-usa`, `bmo-bank`, `synovus-bank`) and 2 canonical-review
  rows (`firstbank`, `independent-bank-memphis`). Apply obvious fixes through
  DB API only; if federal-ID guard blocks category changes, leave them for
  founder-reviewed fixes.
- Phase 1 safe fix attempt completed:
  - DB backup:
    `data/backups/creditdoc_before_regulator_category_cleanup_2026-05-26.sqlite`
  - `synovus-bank` category corrected `mortgages` -> `banking` through DB API.
  - `goldman-sachs-bank-usa` category correction blocked by federal-ID guard
    (FDIC row); now marked founder override required.
  - `bmo-bank` category correction blocked because profile is founder-protected;
    now marked founder override required.
  - Do not include Goldman Sachs or BMO in the public CFPB report until Jammi
    approves category correction or exclusion.
- Jammi then granted explicit permission to use founder-level updates for this
  cleanup project and restore/preserve protection states.
- Founder-authorized corrections completed:
  - Backup:
    `data/backups/creditdoc_before_founder_authorized_regulator_category_cleanup_2026-05-26.sqlite`
  - `goldman-sachs-bank-usa`: `pawn-shops` -> `banking`, audit logged by
    `founder`, `is_protected` remained `0`.
  - `bmo-bank`: `personal-loans` -> `banking`, audit logged by `founder`,
    `is_protected` remained `1`.
  - No unresolved Supabase retry rows for either slug.
  - Audit queue updated to `category_fixed_founder_override`.
- Regenerated post-fix candidate CSV:
  `/srv/BusinessOps/CreditDoc Project Improvement/CFPB_Responsiveness_Report_2026-05-26/cfpb_responsiveness_candidates_enriched_after_phase1_fixes_2026-05-26.csv`
- Regenerated set remains 131 rows. Corrected rows now appear as `banking`;
  banking count increased to 57, personal-loans decreased to 18, mortgages
  decreased to 9.
- Phase 1B category/profile cleanup completed:
  - Backup:
    `data/backups/creditdoc_before_regulator_category_cleanup_phase1b_2026-05-26.sqlite`
  - `first-technology`: `banking` -> `credit-unions`; weak Instrumentl URL
    replaced with official `https://www.firsttechfed.com/`.
  - `mountain-america`: `banking` -> `credit-unions`; Wikipedia URL replaced
    with official `https://www.macu.com/`.
  - `sarma`: `mortgages` -> `credit-monitoring`; kept pending category-policy
    review because it is a B2B credit reporting/data/collections provider, not
    a lender.
  - All three writes used `CreditDocDB.update_lender(...,
    updated_by='regulator_category_cleanup')`, audit logged, with no unresolved
    Supabase retry rows.
  - `moneylion` was deliberately not changed. It is founder-protected and
    genuinely multi-product, so it is marked `pending_fintech_policy` instead
    of forced into `personal-loans`.
- Regenerated Phase 1B candidate CSV:
  `/srv/BusinessOps/CreditDoc Project Improvement/CFPB_Responsiveness_Report_2026-05-26/cfpb_responsiveness_candidates_enriched_after_phase1b_fixes_2026-05-26.csv`
- Phase 1 top-50 audit status:
  - all top-50 rows classified
  - 40 `yes_pending_final_methodology`
  - 5 `pending_profile_review`
  - 3 `pending_post_regen_review`
  - 1 `pending_fintech_policy`
  - 1 `pending_category_policy`
- Confirmed entity/profile notes:
  - `firstbank` and `independent-bank-memphis` are confirmed by FDIC cert and
    official website; use clarifying location/entity context in public copy.
  - `wafd-bank-seattle`, `hancock-whitney-bank-gulfport`, and
    `san-diego-county` are confirmed matches but remain pending profile review
    because their CreditDoc rows are draft/brand-profile review candidates.
- Profile review batch completed:
  - Backup:
    `data/backups/creditdoc_before_cfpb_profile_review_batch_2026-05-26.sqlite`
  - Updated through `CreditDocDB.update_lender(...,
    updated_by='regulator_profile_review', force=True)`.
  - `first-technology`: display name now `First Tech Federal Credit Union`;
    stale Instrumentl/source-derived copy removed; category remains
    `credit-unions`; `review_status` set to `published`.
  - `mountain-america`: display name now `Mountain America Credit Union`;
    stale Wikipedia/source-derived copy removed; category remains
    `credit-unions`; `review_status` set to `published`.
  - `wafd-bank-seattle`: official website aligned to
    `https://www.wafdbank.com`; brand-level banking copy/meta cleaned;
    `review_status` set to `published`.
  - `hancock-whitney-bank-gulfport`: official website aligned to
    `https://www.hancockwhitney.com`; brand-level banking copy/meta cleaned;
    `review_status` set to `published`.
  - `san-diego-county`: display name now `San Diego County Credit Union`;
    credit-union copy/meta cleaned; `review_status` set to `published`.
  - No unresolved Supabase retry rows for these five slugs.
  - Exported changed lender JSON files.
  - Regenerated candidate CSV:
    `/srv/BusinessOps/CreditDoc Project Improvement/CFPB_Responsiveness_Report_2026-05-26/cfpb_responsiveness_candidates_enriched_after_profile_review_2026-05-26.csv`
- Updated Phase 1 top-50 status after profile review:
  - 45 `yes_pending_final_methodology`
  - 3 `pending_post_regen_review`
  - 1 `pending_fintech_policy` (`moneylion`)
  - 1 `pending_category_policy` (`sarma`)
- Post-regeneration profile review batch completed:
  - Backup:
    `data/backups/creditdoc_before_post_regen_profile_batch_2026-05-26.sqlite`
  - `goldman-sachs-bank-usa`: exported public profile now shows `banking`,
    official Marcus URL, brand-level copy/meta, no misleading branch address,
    and `review_status: published`.
  - `bmo-bank`: founder-authorized profile cleanup preserved protection and
    now shows `banking`, official BMO U.S. personal banking URL, brand-level
    copy/meta, no branch phone/address, and `review_status: published`.
  - `synovus-bank`: exported public profile now shows `banking`, official
    Synovus URL, brand-level copy/meta, no branch phone/address, and
    `review_status: published`.
  - No unresolved Supabase retry rows for the three slugs.
  - Audit queue now marks all three
    `post_regen_profile_reviewed_approved_for_report_candidate`.
  - Updated Phase 1 top-50 status:
    - 48 `yes_pending_final_methodology`
    - 1 `pending_fintech_policy` (`moneylion`)
    - 1 `pending_category_policy` (`sarma`)
- Added profile-quality operating plan:
  `docs/plans/2026-05-26-profile-quality-agent.md`
- Fintech category launched:
  - Backup:
    `data/backups/creditdoc_before_fintech_category_launch_2026-05-26.sqlite`
  - New category slug/name: `fintech` / `Fintech`.
  - Added category to SQLite, exported `src/content/categories.json`, and
    upserted Supabase `public.categories`.
  - Moved initial app-first cohort to `fintech` through DB API:
    `moneylion`, `chime`, `brigit`, `earnin`, `dave-banking`, `kikoff`,
    `self-credit-builder`, `self-financial`, `sofi`, `sofi-bank`, and
    `varo-bank`.
  - Founder authorization was used where profile protection required it:
    `moneylion`, `chime`, `kikoff`, `self-credit-builder`, and `sofi-bank`.
  - Verified Supabase has 11 ready Fintech lenders.
  - MoneyLion moved from CFPB policy hold to
    `yes_pending_final_methodology` as a Fintech / multi-product app.
  - Sarma remains the only top-50 policy hold.
- CFPB responsiveness report Phase 3 advanced:
  - Sarma policy decision completed: exclude from the first public
    consumer-facing provider ranking because it is B2B credit reporting/data,
    debt collection, background screening, and mortgage-services
    infrastructure.
  - Final report input generated with 49 eligible candidates:
    `/srv/BusinessOps/CreditDoc Project Improvement/CFPB_Responsiveness_Report_2026-05-26/cfpb_responsiveness_final_report_input_2026-05-26.csv`
  - Methodology note generated:
    `/srv/BusinessOps/CreditDoc Project Improvement/CFPB_Responsiveness_Report_2026-05-26/methodology_note_most_responsive_providers_2026-05-26.md`
  - Public page scaffold added:
    `/research/most-responsive-consumer-finance-providers-2026/`
  - Local report page renders. Non-review report-body links passed local checks.
  - Provider names link directly to `/review/{slug}/`; production verification
    returned 200 for all 25 visible report provider links.

## 2026-05-26 — Noindex Cleanup Batch 004

Workpack:

- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Noindex_Review_2026-05-26/`

Batch 004 resolved the 5 `ready_for_index` rows that still had
`data.no_index=true`:

- Reinstated `continental-bank`: `no_index=false`, published, neutral meta
  title/description, and unsupported rating wording removed from the meta
  description.
- Archived 4 weak/mismatched zero-GSC rows:
  - `check-cashing-payday-loans`
  - `credit-repair-finest`
  - `simple-fast-business-funding-same-day-loans`
  - `smile-jewels-pawn-loans`

Verification:

- Local SQLite and Supabase agree for all 5 touched slugs.
- No Supabase retry rows for the 5 touched slugs.
- `npm run build` passed.
- Exact built HTML/XML scan found no `/review/<slug>/` references for the 4
  archived paths.
- Deployed via `./deploy.sh`.
- Cloudflare Worker version:
  `46a1298e-a4d0-478f-9499-1edce895ca73`.
- Live status:
  - `https://www.creditdoc.co/review/continental-bank/` returns `200` with no
    `noindex` robots meta.
  - The 4 archived review URLs return `404`.
  - Live `sitemap-0.xml` through `sitemap-4.xml` contain none of the 4
    archived review paths; `sitemap-5.xml` and above return `404`.

## 2026-05-26 — Noindex Fix/Index Batch 005

Promoted 3 verified provider pages from noindex/pending state:

- `snap-loans-cash`
- `reverse-mortgages-home-loans-with-christopher-gibson-at-c2-financial`
- `public-loans`

Rules applied:

- Required a working official-looking website, matching category, useful stored
  profile data, and GSC signal.
- Did not promote `the-debt-crushers` because its profile still records
  unresolved San Francisco/Las Vegas location signals.
- Did not promote rows whose stored source was a suspended website, HTTP 500,
  trademark page, PDF, or Google business placeholder.

Verification:

- Local SQLite and Supabase agree for all 3 promoted slugs.
- No Supabase retry rows for the 3 promoted slugs.
- `npm run build` passed.
- Generated sitemap included all 3 review paths.
- Deployed via `./deploy.sh`.
- Cloudflare Worker version:
  `d0f3eb08-20cb-4368-b125-594ac77aded4`.
- Live status:
  - all 3 promoted review URLs return `200`;
  - none have a `noindex` robots meta;
  - live `sitemap-3.xml` contains all 3 review paths.

## 2026-05-26 — Sitewide Page Upgrade Batch 013

Batch 013 committed as `61f6875616` for trust/support pages:

- `/about/`
- `/about/creditdoc-data/`
- `/methodology/`
- `/editorial-policy/`
- `/faq/`
- `/disclosure/`
- `/disclaimer/`
- `/contact/`

Changes:

- Added trust-page graph/context blocks into local guides, state rules, answer
  clusters, tools, resources, categories, and CFPB complaint-data research.
- Softened unsupported YMYL-sensitive wording around recommendations, "best" or
  "right" provider framing, guarantees, price currentness, privacy protection,
  licensing, and financial outcomes.
- Left the legal disclaimer's negated "No Endorsement" language in place.

Verification:

- `npm run build` passed.
- Build injected 18,411 SSR route URLs.
- Output scan confirmed all eight new Batch 013 context blocks.
- Static route checks passed for touched trust/support pages and core graph
  destination routes.

Workpack:

- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_013_notes_2026-05-26.md`
- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_013_trust_support_pages_gsc_seen_2026-05-26.csv`

## 2026-05-26 — Sitewide Page Upgrade Batch 014

Batch 014 committed as `05224c8ddd` for remaining static support/trust pages:

- `/privacy/`
- `/terms/`
- `/accessibility/`
- `/do-not-sell/`
- `/about/harvey-brooks/`

Changes:

- Added contextual graph blocks into methodology, editorial policy, disclosure,
  data explanations, local guides, state pages, tools, resources, and CFPB
  complaint-data research.
- Softened unsupported recommendation, guarantee, privacy-protection, licensing,
  and stale editorial-review inventory language.
- Updated the editor/founder page to describe selected editorial review without
  implying directory-wide manual review coverage.

Verification:

- Initial `npm run build` passed but had a non-fatal sitemap city-guide fetch
  timeout and injected 16,055 SSR URLs.
- Reran `npm run build`; second build passed with 124 city guides, 2,232
  city-category sub-pages, and 18,411 SSR route URLs injected.
- Output scan confirmed all five Batch 014 context blocks.
- Static route checks passed for touched support/trust pages and graph
  destinations.

Workpack:

- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_014_notes_2026-05-26.md`
- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_014_static_support_pages_gsc_seen_2026-05-26.csv`

## 2026-05-26 — Sitewide Page Upgrade Batch 015

Batch 015 committed as `7a2f4b0ddb` for navigation/commercial support pages:

- `/`
- `/press/`
- `/sitemap/`
- `/search/` (runtime SSR)
- `/deals/` (founder-protected, changed under cleanup authorization)
- `/specials/` inspected; remains a 301 redirect to `/deals/`

Changes:

- Added graph/context blocks into city guides, state pages, categories,
  Fintech, answers, resources, tools, methodology, data explanations, and CFPB
  complaint-data research.
- Softened homepage/search wording away from unsupported "best", "top picks",
  expert-pick, approval, guarantee, licensing, diagnosis, and matching claims.
- Softened press data/verification wording and deals offer wording.

Verification:

- `npm run build` passed.
- Build injected 18,411 SSR route URLs and generated 124 city guides plus 2,232
  city-category sub-pages.
- Generated-output scan confirmed context blocks on `/`, `/press/`,
  `/sitemap/`, and `/deals/`.
- `/search/` is `prerender = false`, so no static `dist/search/index.html` is
  expected; source scan confirmed the context block and the full build passed.
- Static route checks passed for static Batch 015 pages and core graph
  destinations.

Workpack:

- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_015_notes_2026-05-26.md`
- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_015_navigation_commercial_pages_gsc_seen_2026-05-26.csv`

## 2026-05-26 — Sitewide Page Upgrade Batch 016

Batch 016 committed as `0157185c6f` for dynamic graph templates:

- `/brand/{brand}/`
- `/trends/`
- `/trends/{slug}/`
- `/best/{slug}/`
- `/review/{slug}/` follow-up language cleanup

Changes:

- Added contextual graph blocks from dynamic brand, trends, and list-style guide
  templates into local guides, state rules, categories, Fintech, tools, data
  methodology, and CFPB complaint-data research.
- Softened CFPB trend language so response metrics are described as public
  response patterns and transparency signals, not consumer-service quality,
  successful resolution, endorsement, rating, or suitability claims.
- Softened list/review wording away from unsupported "best fit",
  recommendation, guarantee, and broad independent-review claims.

Verification:

- First `npm run build` passed but hit the known non-fatal city-guide sitemap
  fetch timeout and injected 16,055 SSR route URLs.
- Reran `npm run build`; second build passed with 124 city guides, 2,232
  city-category sub-pages, and 18,411 SSR route URLs injected.
- Generated-output scan confirmed blocks on `/trends/` and
  `/trends/american-consumer-credit-counseling/`.
- Source scan confirmed runtime SSR blocks in brand and best templates.
- YMYL phrase scan found no remaining unsafe Batch 016 target phrases; the only
  "suitability recommendation" wording is explicitly negated in a CFPB
  transparency disclaimer.

Workpack:

- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_016_notes_2026-05-26.md`
- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_016_dynamic_templates_gsc_seen_2026-05-26.csv`

## 2026-05-26 — Sitewide Page Upgrade Batch 017

Batch 017 committed as `67cab54fa8` for shared components and sitewide
commercial/YMYL language cleanup:

- `CategoryCard`
- `ComparisonTable`
- `DiagnosisCard`
- `Footer`
- `LenderCard`
- `SearchBar`
- `TopPicksTable`
- `TrustBadge`
- comparison-page template follow-up
- review-page cross-sell follow-up

Changes:

- Reframed shared UI labels away from unsupported ranking, diagnosis,
  guarantee, and verification wording.
- Added display-time softeners for legacy provider/category/comparison strings
  so rendered pages show `Refund Term`, `Profile Signals`, `Profiled`,
  `CreditDoc Profile Note`, `Research Note`, `listed refund term`, and
  `listed pricing context` language.
- Replaced the visible footer quick-link label `Best Credit Repair` with
  `Credit Repair Guide`.
- Softened compare-page FAQ, summary, profile-note, explore-more, and affiliate
  disclosure language.
- Softened review-page personal-loan cross-sell language.
- Preserved existing slugs, query params, and raw data files for compatibility.

Verification:

- `npm run build` passed.
- Final build injected 18,411 SSR route URLs and generated 124 city guides plus
  2,232 city-category sub-pages.
- Generated-output scan on `dist/index.html` and
  `dist/compare/credit-saint-vs-sky-blue-credit/index.html` found no Batch 017
  blocked phrases for guarantee, best-value, wins, diagnosis/verdict,
  independent-evaluation, approval, and old explore-more labels.
- Positive output scan confirmed the expected replacement language.

Workpack:

- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_017_notes_2026-05-26.md`
- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_017_shared_components_gsc_seen_2026-05-26.csv`

## 2026-05-26 — Sitewide Page Upgrade Batch 018

Batch 018 implementation committed as `49b38174a0` for runtime content
boundaries:

- `src/utils/safe-copy.ts`
- `src/components/ProsCons.astro`
- `src/pages/answers/[slug].astro`
- `src/pages/categories/[category].astro`
- `src/pages/review/[slug].astro`

Changes:

- Added a shared `softenYmylCopy()` display-time boundary for legacy content
  phrases that still exist in raw JSON/content sources.
- Applied the boundary to answer body sections, answer takeaways, answer FAQ
  schema and visible FAQ copy, category description/meta copy, review long
  descriptions, review profile notes, review pros/cons, and review profile
  signals.
- Softened runtime CTA, affiliate disclosure, category `ItemList` schema, and
  secured-card cross-sell wording away from unsupported "best", "top",
  guarantee, approval, recommendation, value, and diagnosis-style phrasing.
- Preserved existing routes, slugs, raw content files, and link targets.

Verification:

- `npm run build` passed.
- Build injected 18,411 SSR route URLs and generated 124 city guides plus 2,232
  city-category sub-pages.
- Touched SSR-template source scan found no remaining direct risky phrase
  matches outside the explicit replacement patterns in `safe-copy.ts`.
- Generated-output scan on `dist/index.html` and
  `dist/compare/credit-saint-vs-sky-blue-credit/index.html` found no Batch 018
  blocked phrases.
- `git diff --check` passed for the touched implementation files.

Workpack:

- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_018_notes_2026-05-26.md`
- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_018_runtime_content_boundaries_gsc_seen_2026-05-26.csv`

## 2026-05-26 — Sitewide Page Upgrade Batch 019

Batch 019 implementation committed as `04eec9f88c` for residual guide/tool
copy cleanup:

- `src/components/AffiliateInline.astro`
- `src/pages/about/creditdoc-data.astro`
- `src/pages/browse/[catSlug]/[citySlug].astro`
- `src/pages/city/[slug].astro`
- `src/pages/credit-guide/[slug]/[category].astro`
- `src/pages/tools/debt-payoff-calculator.astro`

Changes:

- Softened inline affiliate blocks away from approval-odds, top-ranked,
  guaranteed result, and strong service-claim wording.
- Reframed debt calculator output from recommendations and "saves" language to
  educational calculation notes and estimated scenario comparisons.
- Updated CreditDoc Data terminology from diagnosis/verdict/guarantee language
  to profile-note, research-note, and refund-terms language.
- Softened browse/city guide CTAs and city guide resource blocks away from
  "best options", "top-rated services", and broad independent-review claims.
- Rephrased personal-loan city-category copy from determining that a lender is
  properly licensed to checking licensing or registration with the state.

Verification:

- `npm run build` passed after the main Batch 019 edits with 18,411 SSR route
  URLs injected.
- A final post-copy build also passed; it hit the known non-fatal city-guide
  sitemap timeout and injected 16,055 SSR route URLs on that attempt.
- Generated-output scans on CreditDoc Data, the debt payoff calculator,
  Amarillo city, and an Amarillo browse page found no Batch 019 blocked
  phrases.
- Source scan confirmed the SSR credit-guide category copy now uses licensing
  lookup language.
- `git diff --check` passed.

Workpack:

- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_019_notes_2026-05-26.md`
- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_019_residual_guide_tool_copy_gsc_seen_2026-05-26.csv`

## 2026-05-26 — Sitewide Page Upgrade Batch 020

Batch 020 implementation committed as `c0b49e5c13` for remaining state, FAQ,
research, and tool copy cleanup:

- `src/pages/state/index.astro`
- `src/pages/faq.astro`
- `src/pages/research/consumer-complaints.astro`
- `src/pages/tools/credit-score-simulator.astro`
- `src/pages/tools/debt-payoff-calculator.astro`

Changes:

- Replaced state-index "top-rated lenders" wording with provider profile
  context language.
- Replaced older FAQ independent-review language with a more precise
  compensation-boundary statement.
- Rephrased complaint-data research copy from direct licensing verification to
  state license or registration checks.
- Reframed the credit-score simulator CTA away from top-rated/removal claims and
  toward provider profile comparison.
- Replaced debt-snowball "psychological wins" language in FAQ schema and visible
  FAQ copy with early payoff milestone language.

Verification:

- `npm run build` passed.
- Build injected 18,411 SSR route URLs and generated 124 city guides plus 2,232
  city-category sub-pages.
- Postbuild sitemap/robots conflict check passed.
- Generated-output scan confirmed the old Batch 020 phrases were absent from
  the state index, FAQ, credit-score simulator, and debt payoff calculator.
- Source check confirmed the complaint research page now uses state license or
  registration check language.
- `git diff --check` passed.

Workpack:

- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_020_notes_2026-05-26.md`
- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_020_remaining_state_tool_copy_gsc_seen_2026-05-26.csv`

## 2026-05-26 — Sitewide Page Upgrade Batch 021

Batch 021 implementation committed as `421bd7122f` for shared YMYL copy boundary
expansion:

- `src/utils/safe-copy.ts`
- `src/components/LenderCard.astro`
- `src/components/TopPicksTable.astro`
- `src/pages/compare/[slug].astro`

Changes:

- Expanded `softenYmylCopy()` for additional raw content phrases around
  satisfaction guarantees, guaranteed results, remove-negative-item claims,
  better-value claims, top-ranked profile signals, recommendation language, and
  professional recommendations.
- Moved lender card short descriptions and profile signals onto the shared
  display-time softening boundary.
- Moved top-picks profile signals onto the shared boundary.
- Wrapped compare summaries, research notes, FAQ answers, and JSON-LD text with
  the shared boundary after comparison-specific softening.

Verification:

- `npm run build` passed.
- Build injected 18,413 SSR route URLs because an unrelated unstaged
  `src/content/wellness-guides.json` change added two generated wellness URLs;
  that file was not staged or committed in Batch 021.
- Build generated 124 city guides plus 2,232 city-category sub-pages.
- Postbuild sitemap/robots conflict check passed.
- Targeted generated-output scan was clean across representative compare and
  browse pages that previously exposed the raw phrases.
- Source scan found only explicit replacement-rule patterns in the touched
  files.
- `git diff --check` passed.

Workpack:

- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_021_notes_2026-05-26.md`
- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_021_shared_ymyl_boundary_gsc_seen_2026-05-26.csv`

## 2026-05-26 — Sitewide Page Upgrade Batch 022

Batch 022 implementation committed as `a6bb2e77dc` for static guide, sidebar,
course, and quiz label cleanup:

- `src/components/AffiliateSidebar.astro`
- `src/pages/city/[slug].astro`
- `src/pages/state/[slug].astro`
- `src/pages/browse/[catSlug]/[citySlug].astro`
- `src/pages/credit-guide/[slug]/index.astro`
- `src/pages/courses/credit-fundamentals/[slug].astro`
- `src/pages/tools/borrowing-power-quiz.astro`
- `src/utils/safe-copy.ts`

Changes:

- Reframed affiliate sidebar credit-repair copy away from removal/result claims
  and through the shared `softenYmylCopy()` display boundary.
- Replaced remaining visible `Top-Rated`, `Top Picks`, `Recommended Next
  Steps`, and `Matched Lenders for You` labels with provider/profile/review
  context language.
- Replaced city `ItemList` schema wording from top-rated financial services to
  financial service profiles.
- Added shared softening to course CTA text and expanded `softenYmylCopy()` for
  remaining `top-rated` course/listicle phrasing.

Verification:

- `npm run build` passed.
- Build injected 18,413 SSR route URLs because an unrelated unstaged
  `src/content/wellness-guides.json` change added two generated wellness URLs;
  that file was not staged or committed in Batch 022.
- Build generated 124 city guides plus 2,232 city-category sub-pages.
- Postbuild sitemap/robots conflict check passed.
- Targeted generated-output/source scan confirmed the old Batch 022 phrases
  were absent from representative city, browse, course, quiz, state, guide, and
  affiliate-sidebar surfaces.
- `git diff --check` passed.

Workpack:

- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_022_notes_2026-05-26.md`
- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_022_static_guide_quiz_labels_gsc_seen_2026-05-26.csv`

## 2026-05-26 — Sitewide Page Upgrade Batch 023

Batch 023 implementation committed as `4737bde7ec` for listicle and quiz
cross-link copy cleanup:

- `src/pages/best/[slug].astro`
- `src/pages/tools/borrowing-power-quiz.astro`
- `src/pages/financial-wellness/[slug].astro`
- `src/pages/state/[slug].astro`
- `src/pages/answers/index.astro`
- `src/utils/safe-copy.ts`

Changes:

- Routed `/best/[slug]` listicle descriptions, intros, TL;DR text, key
  takeaways, FAQ text/schema, lender summaries, and pros through
  `softenYmylCopy()` at render time.
- Expanded `softenYmylCopy()` for remaining listicle-style best/risk-free,
  strongest-guarantee, refund-policy, lower-rate, and matched-provider wording.
- Replaced visible `Best`/`Top` cross-link labels on quiz, answers, wellness,
  and state surfaces with profile/comparison language while preserving URLs.
- Softened borrowing-power quiz copy around matching, lower rates, credit-repair
  outcomes, and result follow-up text.

Verification:

- `npm run build` passed after the implementation and again after the final
  quiz wording tweak.
- Build injected 18,413 SSR route URLs because an unrelated unstaged
  `src/content/wellness-guides.json` change added two generated wellness URLs;
  that file was not staged or committed in Batch 023.
- Build generated 124 city guides plus 2,232 city-category sub-pages.
- Postbuild sitemap/robots conflict check passed.
- Targeted source/generated-output scan confirmed old Batch 023 phrases were
  absent from the SSR listicle template, financial-wellness template, state
  template, answers index source, and generated borrowing-power quiz page.
- `git diff --check` passed.

Workpack:

- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_023_notes_2026-05-26.md`
- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_023_listicle_quiz_crosslinks_gsc_seen_2026-05-26.csv`

## 2026-05-26 — Sitewide Page Upgrade Batch 024

Batch 024 implementation committed as `35683faede` for homepage and research
support copy cleanup:

- `src/pages/index.astro`
- `src/pages/research/most-responsive-consumer-finance-providers-2026.astro`
- `src/pages/research/consumer-complaints.astro`
- `src/pages/resources/index.astro`

Changes:

- Reframed homepage `Independent Reviews` copy as independent research and
  comparison context, without implying CreditDoc reviews as a lender/broker.
- Softened homepage category and business-finance blurbs away from rebuild,
  top, startup-friendly, flexible-cash, and direct funding outcome language.
- Rephrased research-report language from matching/ranking/strong records to
  linked provider profiles, notable public records, and report context.
- Reframed consumer-complaint support copy from `better bet`/ratings language
  to documented relief context and profile signals.
- Softened resources copy from choosing tools to comparing tools.

Verification:

- `npm run build` passed.
- Build injected 18,413 SSR route URLs because an unrelated unstaged
  `src/content/wellness-guides.json` change added two generated wellness URLs;
  that file was not staged or committed in Batch 024.
- Build generated 124 city guides plus 2,232 city-category sub-pages.
- Postbuild sitemap/robots conflict check passed.
- Targeted old-copy scan was clean across the touched source files and
  generated homepage, resources, and responsive-provider research pages.
- The complaint research page is SSR-only (`prerender = false`), so generated
  verification used source-level checks for that route.
- `git diff --check` passed.

Workpack:

- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_024_notes_2026-05-26.md`
- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_024_homepage_research_support_copy_gsc_seen_2026-05-26.csv`

## 2026-05-26 — Sitewide Page Upgrade Batch 025

Batch 025 implementation committed as `5c9a831a8a` for research and support page
label cleanup:

- `src/pages/research/most-responsive-consumer-finance-providers-2026.astro`
- `src/pages/research/consumer-complaints.astro`
- `src/pages/research/lending-transparency.astro`
- `src/pages/about/creditdoc-data.astro`
- `src/pages/tools/borrowing-power-quiz.astro`

Changes:

- Reframed research headings from `Top`/ranking language to provider-record,
  reviewed-row, and approval-rate-record language.
- Rephrased the most-responsive report citation line from `strong CFPB` to
  `notable CFPB` and softened candidate-set methodology language.
- Reframed complaint research table labels from `Top` complaint categories and
  `Top 25` companies to common categories and large complaint-count records.
- Replaced remaining support-page `diagnosis`, `CreditDoc rating`, and
  `licensed to operate` language with profile notes, stored Google rating
  fields, and state-level availability context.
- Softened borrowing-power quiz cross-link subtitles away from best/right/work
  phrasing while preserving existing strategic URLs.

Verification:

- `npm run build` passed.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json` changes
  affected generated URL/content inventory; neither file was staged or
  committed in Batch 025.
- Build generated 124 city guides plus 2,232 city-category sub-pages.
- Postbuild sitemap/robots conflict check passed.
- Targeted old-copy scan was clean across static generated pages and SSR-only
  source routes.
- `consumer-complaints` and `lending-transparency` are SSR-only in the static
  build, so those routes were source-verified.
- `git diff --check` passed.

Workpack:

- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_025_notes_2026-05-26.md`
- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_025_research_support_labels_gsc_seen_2026-05-26.csv`

## 2026-05-26 — Sitewide Page Upgrade Batch 026

Batch 026 implementation committed as `92a87a80a3` for comparison-page copy
boundary cleanup:

- `src/utils/safe-copy.ts`

Changes:

- Expanded the shared YMYL copy softener for comparison-data phrases that can
  leak from raw comparison records into summaries, research notes, FAQ answers,
  and JSON-LD.
- Neutralized comparison wording around preferable/reliable/trustworthy/safe,
  stronger or better consumer/borrower protections, superior credibility or
  transparency, value proposition, strong BBB/Google-review phrasing, and
  guarantee/refund framing.
- Added render-time replacements for older comparison-record patterns such as
  `stronger choice`, `proven results`, `proven track record`, `is better for`,
  and `Choose ... for`.
- Left raw `src/content/comparisons.json` untouched because it is currently an
  unrelated unstaged change from another agent/user; this batch protects
  generated output without taking ownership of that file.

Verification:

- `npm run build` passed after the final copy-boundary update.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json` changes
  affected generated inventory; neither file was staged or committed.
- Build generated 124 city guides plus 2,232 city-category sub-pages.
- Postbuild sitemap/robots conflict check passed.
- Targeted generated `/compare/` hit-list scan was clean for the risky raw
  phrases addressed in this batch.
- Replacement-language scan confirmed the shared boundary is producing neutral
  profile/context wording in generated comparison pages.
- `git diff --check` passed.

Workpack:

- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_026_notes_2026-05-26.md`
- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_026_compare_copy_boundary_gsc_seen_2026-05-26.csv`

## 2026-05-26 — Sitewide Page Upgrade Batch 027

Batch 027 implementation committed as `41a648a0d2` for browse city-category
title and intro cleanup:

- `src/pages/browse/[catSlug]/[citySlug].astro`

Changes:

- Reframed generated city-category titles from `Best {category} in {city}` to
  `{category} Provider Profiles in {city}`.
- Replaced meta/OG/Twitter description language from `find trusted local
  providers` to profile-comparison wording focused on pricing fields, public
  ratings, and local provider context.
- Reframed the ItemList JSON-LD name from `Top {category}` to provider-profile
  wording.
- Updated visible H1 and intro copy to avoid ranking-style claims while
  preserving local page intent, category URLs, city URLs, and internal linking.

Verification:

- `npm run build` passed.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json` changes
  affected generated inventory; neither file was staged or committed.
- Build generated 124 city guides plus 2,232 city-category sub-pages.
- Postbuild sitemap/robots conflict check passed.
- Source scan for old `Best`/`Top`/`trusted local providers` browse-template
  wording was clean.
- Generated sample scan across New York credit cards, Baton Rouge credit
  unions, and Fresno check cashing pages was clean for the old wording and
  confirmed the new provider-profile copy.
- `git diff --check` passed.

Workpack:

- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_027_notes_2026-05-26.md`
- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_027_browse_city_category_titles_gsc_seen_2026-05-26.csv`

## 2026-05-26 — Sitewide Page Upgrade Batch 028

Batch 028 implementation committed as `e3cb9feef6` for SSR review-page fit
copy and lending-record labels:

- `src/pages/review/[slug].astro`
- `src/components/HMDARecord.astro`
- `src/components/RegulatoryRecord.astro`

Changes:

- Reframed review FAQ copy from `best suited for` to listed profile-signal
  wording.
- Reframed the review mini quiz away from `Right for You`, `matches your
  needs`, `strong match`, `good option`, and `better match` language.
- Replaced quiz priority label `Reputation & trust` with public-rating-field
  wording and `Fast results` with timing-note wording.
- Reframed the related next-step link from `Match your need` to `Review fit
  context`.
- Rephrased HMDA text from active `approving` wording to recorded approval
  outcomes, and changed `Top Denial Reasons` / `Top Lending States` labels to
  common-denial and recorded-application labels.
- Rephrased SBA component copy from `Approved` to recorded approvals.

Verification:

- `npm run build` passed.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json` changes
  affected generated inventory; neither file was staged or committed.
- Build generated 124 city guides plus 2,232 city-category sub-pages.
- Postbuild sitemap/robots conflict check passed.
- Targeted source scan was clean for the old review/HMDA/SBA phrases addressed
  in this batch.
- Generated static scan found separate blog index teaser copy using `right for
  you`; that is outside the SSR review scope and is queued for Batch 029.
- `git diff --check` passed.

Workpack:

- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_028_notes_2026-05-26.md`
- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_028_review_fit_lending_records_gsc_seen_2026-05-26.csv`

## 2026-05-26 — Sitewide Page Upgrade Batch 029

Batch 029 implementation committed as `bbaefb5b44` for blog and learn
education teaser copy:

- `src/utils/safe-copy.ts`
- `src/pages/blog/index.astro`
- `src/pages/blog/[slug].astro`
- `src/utils/data-build.ts`

Changes:

- Added `softenEducationalTeaserCopy()` as a shared presentation-layer helper
  for education teasers and embedded search data.
- Reframed blog index cards, blog detail titles/descriptions/JSON-LD headlines,
  key takeaways, and related-post labels away from suitability/judgment wording
  such as `right for you`, `good idea`, `bad`, `truth`, and `worth it`.
- Applied the same softening to `/learn/` embedded search data for wellness
  guides, glossary terms, and blog posts without editing the raw content JSON.
- Tightened the shared YMYL copy boundary so `quick wins` becomes neutral
  progress-marker wording instead of the previous awkward `quick is flagged`
  output.

Verification:

- `npm run build` passed.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json` changes
  affected generated inventory; neither file was staged or committed.
- Build generated 124 city guides plus 2,232 city-category sub-pages.
- Postbuild sitemap/robots conflict check passed.
- Generated `/blog/` and `/learn/` scans were clean for targeted old teaser
  phrases and awkward replacement patterns.
- `git diff --check` passed.

Workpack:

- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_029_notes_2026-05-26.md`
- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_029_blog_learn_teasers_gsc_seen_2026-05-26.csv`

## 2026-05-26 — Sitewide Page Upgrade Batch 030

Batch 030 implementation committed as `39f756b067` for financial-wellness guide
presentation copy:

- `src/pages/financial-wellness/index.astro`
- `src/pages/financial-wellness/[slug].astro`

Changes:

- Applied `softenEducationalTeaserCopy()` to wellness index topic-list guide
  titles and featured guide cards.
- Applied presentation-layer softening to SSR wellness guide titles,
  descriptions, SEO metadata, JSON-LD headlines/breadcrumb labels, section
  headings, key takeaways, table-of-contents labels, and related-guide titles.
- Rephrased hardcoded financial-wellness landing copy from `best way to pay
  down debt` and `stronger financial future` toward neutral comparison and
  planning language.
- Preserved all wellness guide URLs and did not edit raw
  `src/content/wellness-guides.json`.

Verification:

- `npm run build` passed.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json` changes
  affected generated inventory; neither file was staged or committed.
- Build generated 124 city guides plus 2,232 city-category sub-pages.
- Postbuild sitemap/robots conflict check passed.
- Generated `/financial-wellness/` scan was clean for targeted old phrases.
- `git diff --check` passed.

Workpack:

- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_030_notes_2026-05-26.md`
- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_030_wellness_presentation_copy_gsc_seen_2026-05-26.csv`

## 2026-05-26 — Sitewide Page Upgrade Batch 031

Batch 031 implementation committed as `53e8386d4a` for credit-fundamentals
course module phrasing:

- `src/pages/courses/credit-fundamentals/[slug].astro`

Changes:

- Added narrow render-time cleanup for external course markdown lesson HTML:
  `may be worth it` / `worth it` now renders as evaluation wording, and
  `top lenders` now renders as `major lenders`.
- Reframed quiz instruction copy from `Pick the best answer` to `Pick the most
  accurate answer`.
- Preserved quiz correctness, `data-correct` attributes, answer text semantics,
  and intentional guarantee/scam red-flag examples.

Verification:

- `npm run build` passed.
- Build injected 18,413 SSR route URLs because unrelated unstaged
  `src/content/wellness-guides.json` and `src/content/comparisons.json` changes
  affected generated inventory; neither file was staged or committed.
- Build generated 124 city guides plus 2,232 city-category sub-pages.
- Postbuild sitemap/robots conflict check passed.
- Rendered course-page scan was clean for `worth it`, `top lenders`, and
  `best answer`; source-only hits are the replacement rules themselves.
- Generated scam/red-flag course pages still render guarantee examples in the
  intended warning context.
- `git diff --check` passed.

Workpack:

- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_031_notes_2026-05-26.md`
- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_031_course_module_copy_gsc_seen_2026-05-26.csv`

## 2026-05-27 - Sitewide Page Upgrade Batch 120

Batch 120 implementation committed as `6245f10fc7` for cross-page educational
residue normalization:

- `src/utils/safe-copy.ts`

Changes:

- Added render-time cleanup for residual educational, glossary, learn,
  wellness, course, blog, resource, and comparison artifacts.
- Normalized `Financial Account Protection net`, `has more listed context a
  judgment`, `makes overspending easy to overspend`, `claimed certain by`,
  `it can be useful to Try`, `more listed context-cost context`, `listed
  context-cost context`, and `advertised approval claim to verify`.
- Preserved source comparison, wellness-guide, lender, city, and category data.

Verification:

- `npm run build` passed with 18,413 SSR route URLs, 124 city guides, and 2,232
  city-category sub-pages.
- Postbuild sitemap/robots check passed.
- Targeted rendered scan returned zero matches across `dist/compare`,
  `dist/financial-wellness`, `dist/learn`, `dist/glossary`, `dist/blog`,
  `dist/courses`, and `dist/resources`.
- Live spot checks returned HTTP 200 for `/`, `/learn/`,
  `/financial-wellness/`, `/glossary/`,
  `/blog/are-guaranteed-approval-personal-loans-real-the-truth/`,
  `/courses/credit-fundamentals/avoiding-scams-and-predatory-lending/`,
  `/compare/self-credit-builder-vs-first-progress-platinum-elite/`,
  `/compare/dickmann-tax-group-vs-grt-financial/`,
  `/credit-guide/amarillo-tx/`, and `/sitemap-index.xml`.
- `git diff --check` passed.

Workpack:

- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_120_notes_2026-05-27.md`

## 2026-05-27 - Sitewide Page Upgrade Batch 121

Batch 121 implementation committed as `66f051d864` for comparison
listed-context residue normalization:

- `src/utils/safe-copy.ts`

Changes:

- Added render-time cleanup for comparison pages where previous safe-copy
  passes left duplicated listed-context wording and hard risk language.
- Normalized `more listed cost context`, `lists more listed cost context`,
  `offers more listed cost context`, `provides more listed consumer-protection
  context`, `stronger regulatory compliance`, `perpetuates repeat-borrowing
  cycles`, `predatory APRs`, `predatory 304%-688% APRs`, `designed to
  encourage costly rollovers`, `costly rollovers`, `proven credit repair`,
  `stronger accreditation`, and `more practical benefits`.
- Preserved source comparison and lender data.

Verification:

- `npm run build` passed with 18,413 SSR route URLs, 124 city guides, and 2,232
  city-category sub-pages.
- Postbuild sitemap/robots check passed.
- Targeted rendered `dist/compare` scan returned zero matches for the Batch
  121 phrase set.
- Live spot checks returned HTTP 200 for `/`,
  `/compare/brigit-vs-ace-cash-express/`,
  `/compare/brigit-vs-advance-america-montebello/`,
  `/compare/brigit-vs-advance-america-oklahoma-city/`,
  `/compare/ace-cash-express-terrytown-vs-ace-cash-express-miami-fl/`,
  `/compare/dickmann-tax-group-vs-lakeview-law-group/`,
  `/compare/credit-saint-vs-safeport-law/`,
  `/compare/safeport-law-vs-the-credit-people/`,
  `/credit-guide/amarillo-tx/`, and `/sitemap-index.xml`.
- `git diff --check` passed.

Workpack:

- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_121_notes_2026-05-27.md`

## 2026-05-27 - Sitewide Page Upgrade Batch 122

Batch 122 implementation committed as `a835d70ba2` for emergency-cash
comparison residue normalization:

- `src/utils/safe-copy.ts`

Changes:

- Added render-time cleanup for comparison pages where previous safe-copy
  passes left hard emergency-cash cost/risk wording and awkward listed-context
  residue.
- Normalized `extremely expensive`, `unless no alternatives exist`, `notable
  avoided unless`, `makes it with more listed context`, `significantly more
  expensive and predatory`, and `and predatory`.
- Preserved source comparison and lender data.

Verification:

- `npm run build` passed with 18,413 SSR route URLs, 124 city guides, and 2,232
  city-category sub-pages.
- Postbuild sitemap/robots check passed.
- Targeted rendered `dist/compare` scan returned zero matches for the Batch
  122 phrase set.
- Targeted rendered checks confirmed replacement language on
  `/compare/brigit-vs-advance-america-oklahoma-city/`.
- Live spot checks returned HTTP 200 for `/`,
  `/compare/brigit-vs-advance-america-oklahoma-city/`,
  `/compare/ace-cash-express-terrytown-vs-ace-cash-express-miami-fl/`,
  `/compare/brigit-vs-advance-america-montebello/`,
  `/credit-guide/amarillo-tx/`, and `/sitemap-index.xml`.
- `git diff --check` passed.

Workpack:

- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_122_notes_2026-05-27.md`

## 2026-05-27 - Sitewide Page Upgrade Batch 123

Batch 123 implementation committed as `902784f11c` for listed-context residue
normalization:

- `src/utils/safe-copy.ts`

Changes:

- Added render-time cleanup for remaining `more listed context` residue across
  comparison pages and educational teaser/index output.
- Normalized `with more listed context`, `has more listed context`, `more
  listed context for`, `more listed value context`, `more listed risk context`,
  `more listed profile context`, `more listed comparison context`, `more listed
  regulatory context`, `more listed feature context`, `more listed
  accreditation context`, `more listed risk-context`, and `more listed-cost
  context`.
- Reframed remaining `better overall choice` language to `stored comparison
  pick`.
- Cleaned second-order grammar artifacts in comparison, course, learn, and blog
  output.
- Preserved source comparison, education, and lender data.

Verification:

- `npm run build` passed with 18,413 SSR route URLs, 124 city guides, and 2,232
  city-category sub-pages.
- Postbuild sitemap/robots check passed.
- Targeted rendered scan across `dist/compare`, `dist/blog`, `dist/courses`,
  `dist/learn`, and `dist/financial-wellness` returned zero matches for the
  Batch 123 phrase set.
- Live spot checks returned HTTP 200 for `/`,
  `/compare/smartcredit-vs-lookout/`,
  `/compare/kikoff-vs-opensky-secured-credit-card/`,
  `/courses/credit-fundamentals/managing-debt-effectively/`,
  `/courses/credit-fundamentals/know-your-rights/`, `/blog/`,
  `/credit-guide/amarillo-tx/`, and `/sitemap-index.xml`.
- `git diff --check` passed.

Workpack:

- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_123_notes_2026-05-27.md`

## 2026-05-27 - Sitewide Page Upgrade Batch 124

Batch 124 implementation committed as `341d91dda0` for comparison context
grammar normalization:

- `src/utils/safe-copy.ts`

Changes:

- Added final render-time cleanup for comparison grammar created by previous
  safe-copy passes.
- Normalized remaining `risk-context fields` residue to `risk context`.
- Cleaned `more [topic] context with` and `more [topic] context proposition`
  residue after listed-context reductions.
- Normalized `consumer context protection/researching/comparing/compared/seeking`
  into readable consumer-protection, consumer-research, and comparison context.
- Preserved source comparison, education, lender, city, and category data.

Verification:

- `npm run build` passed with 18,413 SSR route URLs, 124 city guides, and 2,232
  city-category sub-pages.
- Postbuild sitemap/robots check passed.
- Targeted rendered scan across `dist/compare`, `dist/blog`, `dist/courses`,
  `dist/learn`, and `dist/financial-wellness` returned zero matches for the
  Batch 124 phrase set.
- Live spot checks returned HTTP 200 for `/`,
  `/compare/brigit-vs-ace-cash-express/`,
  `/compare/smartcredit-vs-regal-credit-management/`,
  `/compare/creditassociates-vs-new-era-debt-solutions/`,
  `/courses/credit-fundamentals/personal-loans-and-borrowing-smart/`,
  `/credit-guide/amarillo-tx/`, and `/sitemap-index.xml`.
- `git diff --check` passed.

Workpack:

- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_124_notes_2026-05-27.md`

## 2026-05-27 - Sitewide Page Upgrade Batch 125

Batch 125 implementation committed as `9b33d02b47` for comparison FAQ fallback
copy consolidation:

- `src/pages/compare/[slug].astro`

Changes:

- Consolidated comparison FAQ answers when both profiles lack a recurring
  monthly subscription fee.
- Consolidated refund-term FAQ answers when neither profile lists a refund term
  in the stored comparison data.
- Preserved provider-specific setup-fee context and one-provider refund-term
  details when only one side has data.
- Trimmed trailing punctuation from provider-stated refund details to prevent
  double periods in rendered FAQs and FAQ JSON-LD.
- Preserved source comparison, lender, city, category, and education data.

Verification:

- `npm run build` passed with 18,413 SSR route URLs, 124 city guides, and 2,232
  city-category sub-pages.
- Postbuild sitemap/robots check passed.
- Targeted rendered scan across `dist/compare` returned zero matches for
  duplicate monthly-subscription fallback text, duplicate missing-refund-term
  fallback text, and listed-refund double-period residue.
- Targeted rendered checks confirmed consolidated FAQ copy on representative
  comparison pages.
- Live spot checks returned HTTP 200 for `/`,
  `/compare/creditassociates-vs-new-era-debt-solutions/`,
  `/compare/cambridge-credit-counseling-vs-greenpath-financial-wellness/`,
  `/compare/greenlight-financial-vs-boost-credit-101/`,
  `/credit-guide/amarillo-tx/`, and `/sitemap-index.xml`.
- `git diff --check` passed.

Workpack:

- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_125_notes_2026-05-27.md`

## 2026-05-27 - Sitewide Page Upgrade Batch 126

Batch 126 implementation committed as `1b83026a91` for emergency-cash
comparison claim softening:

- `src/pages/compare/[slug].astro`

Changes:

- Added comparison-only render-time cleanup for emergency-cash claim language.
- Reframed `predatory` comparison phrases to high-cost/risk-context wording on
  comparison pages.
- Replaced broad `for most borrowers` wording with stored-profile comparison
  framing.
- Preserved educational content, source comparison data, lender data, pricing,
  ratings, slugs, table/schema layout, city pages, and category pages.

Verification:

- `git diff --check` passed.
- `npm run build` passed with 18,413 SSR route URLs, 124 city guides, and 2,232
  city-category sub-pages.
- Postbuild sitemap/robots check passed.
- Targeted rendered scan across `dist/compare` returned zero matches for the
  targeted hard/broad phrases.
- Positive rendered checks confirmed softer language on representative
  emergency-cash comparison pages.
- Live spot checks returned HTTP 200 for `/`,
  `/compare/brigit-vs-ace-cash-express-terrytown/`,
  `/compare/ace-cash-express-new-orleans-la-vs-amscot-the-money-superstore-orlando/`,
  `/compare/brigit-vs-advance-america-montebello/`,
  `/credit-guide/amarillo-tx/`, and `/sitemap-index.xml`.

Workpack:

- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_126_notes_2026-05-27.md`

## 2026-05-27 - Sitewide Page Upgrade Batch 127

Batch 127 implementation committed as `385d0feb52` for lender-card profile
signal softening:

- `src/components/LenderCard.astro`

Changes:

- Added provider-card-specific render-time softening for lender descriptions and
  profile signals.
- Reframed visible card phrases such as `guaranteed returns`, `without
  predatory lending`, and `predatory practices` into provider-stated,
  lending-cost, and verification-context language.
- Improved shared card output for city pages and category browse pages without
  changing lender source records, city data, category data, comparison pages, or
  educational content.

Verification:

- `git diff --check` passed.
- `npm run build` passed with 18,413 SSR route URLs, 124 city guides, and 2,232
  city-category sub-pages.
- Postbuild sitemap/robots check passed.
- Targeted profile-signal rendered scan across `dist/city` and `dist/browse`
  returned zero card matches for the targeted raw phrases.
- Positive rendered checks confirmed replacement language including `stated
  return terms to verify`, `lending-cost context to verify`, `lending-cost and
  title-loan comparison context to verify`, and `high-cost lending practices`.
- Live spot checks returned HTTP 200 for `/`, `/city/irvine-ca/`,
  `/city/arlington-tx/`, `/browse/banking/wilmington-de/`,
  `/browse/free-help/birmingham-al/`, `/browse/bankruptcy/philadelphia-pa/`,
  `/credit-guide/amarillo-tx/`, and `/sitemap-index.xml`.
- A first check against `/browse/credit-unions/arlington-tx/` returned 404
  because that route is not generated in `dist`; it was replaced with generated
  browse-route checks above.

Workpack:

- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_127_notes_2026-05-27.md`

## 2026-05-27 - Sitewide Page Upgrade Batch 128

Batch 128 implementation committed as `60061f54f0` for lender-card proper-name
restoration:

- `src/components/LenderCard.astro`

Changes:

- Added a provider-card restoration pass for proper-name contexts damaged by a
  previous broad `superior` safe-copy replacement.
- Restored visible lender-card copy such as `Superior Pawn`, `Superior Loan`,
  `Superior Credit Repair`, `Superior Ave`, and `Superior rating`.
- Preserved the Batch 127 claim-softening behavior for card descriptions and
  profile signals.

Verification:

- `git diff --check` passed.
- `npm run build` passed with 18,413 SSR route URLs, 124 city guides, and 2,232
  city-category sub-pages.
- Postbuild sitemap/robots check passed.
- Targeted rendered scan across `dist/city` and `dist/browse` returned zero
  matches for damaged `more listed Pawn`, `more listed Loan`, `more listed
  Credit Repair`, `more listed Ave`, and `more listed rating` artifacts.
- Positive rendered checks confirmed restored copy on Virginia Beach pawn,
  Oklahoma City personal-loan, Chicago credit-repair, Cleveland emergency-cash,
  and Las Vegas banking browse pages.
- Live spot checks returned HTTP 200 for `/`,
  `/browse/pawn-shops/virginia-beach-va/`,
  `/browse/personal-loans/oklahoma-city-ok/`,
  `/browse/credit-repair/chicago-il/`,
  `/browse/emergency-cash/cleveland-oh/`,
  `/browse/banking/las-vegas-nv/`, and `/sitemap-index.xml`.

Workpack:

- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_128_notes_2026-05-27.md`

## 2026-05-27 - Sitewide Page Upgrade Batch 129

Batch 129 implementation committed as `0ce68411b3` for lender-card residual
grammar cleanup:

- `src/components/LenderCard.astro`

Changes:

- Added final provider-card cleanup for duplicate `short-term short-term`
  wording in visible city and browse card profile signals.
- Normalized `short-term cash access shortfalls` to `short-term cash
  shortfalls`.
- Cleaned second-order high-cost wording such as `high-cost lending risk
  context lending`.
- Restored remaining proper-name contexts damaged by earlier broad `superior`
  replacements: `Superior Business` and `Superior Mercado`.
- Preserved source lender, city, category, comparison, and education records.

Verification:

- `git diff --check` passed.
- `npm run build` passed with 18,413 SSR route URLs, 124 city guides, and 2,232
  city-category sub-pages.
- Postbuild sitemap/robots check passed.
- Targeted rendered scan across `dist/city` and `dist/browse` returned zero
  matches for `short-term short-term`, `short-term cash access shortfalls`,
  `high-cost lending risk context lending`, `risk context lending`, `more
  listed Business`, and `more listed Mercado`.
- Positive rendered checks confirmed replacement/restored language on Virginia
  Beach pawn, Las Vegas pawn, Chicago business-loan, and Sacramento
  check-cashing browse pages.
- Live spot checks returned HTTP 200 for `/`, `/city/virginia-beach-va/`,
  `/browse/pawn-shops/virginia-beach-va/`,
  `/browse/pawn-shops/las-vegas-nv/`,
  `/browse/business-loans/chicago-il/`,
  `/browse/check-cashing/sacramento-ca/`, and `/sitemap-index.xml`.

Workpack:

- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_129_notes_2026-05-27.md`

## 2026-05-27 - Sitewide Page Upgrade Batch 146

Batch 146 implementation committed as `81b668307c` for index, local, state,
blog, and card hard-claim copy softening.

Changes:

- Applied shared YMYL copy softening to state consumer-rights summaries rendered
  on city, browse, and state lending-law pages.
- Softened visible provider-card refund, total-cost, and regulatory-compliance
  wording.
- Cleaned education/blog teaser wording around advertised approval, score
  improvement, `Perfect for`, and `dramatically` phrasing.

Verification:

- `git diff --check` passed.
- `npm run build` passed with 18,413 SSR route URLs, 124 city guides, and 2,232
  city-category sub-pages.
- Postbuild sitemap/robots check passed.
- Rendered HTML scan, excluding bundled sanitizer source chunks, returned zero
  matches for the Batch 146 hard-claim phrase set.
- Local and production spot checks returned HTTP 200 for `/`, `/learn/`,
  `/blog/`, `/city/omaha-ne/`, `/browse/credit-unions/omaha-ne/`,
  `/state/nebraska/lending-laws/`, `/city/denver-co/`, and
  `/sitemap-index.xml`.

Workpack:

- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_146_notes_2026-05-27.md`

## 2026-05-27 - Sitewide Page Upgrade Batch 147

Batch 147 implementation committed as `ff8683d253` for provider-card
assurance wording and blog/learn teaser residue.

Changes:

- Softened visible city and browse lender-card wording around expert appraisals,
  expert guidance, expert authentication, quality grading, verified lenders,
  verified ATF credentials, and verified luxury items.
- Cleaned the remaining quoted advertised-approval artifact on blog and learn
  teaser/search data.
- Preserved source lender, blog, city, category, comparison, and generated
  inventory records.

Verification:

- `git diff --check` passed.
- `npm run build` passed with 18,413 SSR route URLs, 124 city guides, and 2,232
  city-category sub-pages.
- Postbuild sitemap/robots check passed.
- Rendered HTML scan, excluding bundled source chunks and sitemap XML, returned
  zero matches for the Batch 147 raw phrase set.
- Local and production spot checks returned HTTP 200 for `/`, `/blog/`,
  `/learn/`, `/city/houston-tx/`, `/city/mesa-az/`,
  `/browse/pawn-shops/las-vegas-nv/`, `/browse/pawn-shops/houston-tx/`,
  `/browse/business-loans/nashville-tn/`, and `/sitemap-index.xml`.

Workpack:

- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_147_notes_2026-05-27.md`

## 2026-05-27 - Sitewide Page Upgrade Batch 148

Batch 148 implementation committed as `3d0c32256c` for education/blog teaser
residue cleanup.

Changes:

- Cleaned the emergency-loan blog teaser grammar from `are researching...` to
  `Researching...`.
- Replaced the remaining hard-sell emergency-loan teaser sentence with
  review-oriented wording around options, timing claims, costs, and payday-loan
  risks.
- Softened visible credit-repair teaser wording from scam-first phrasing to
  warning-sign and consumer-protection wording.
- Relabeled the blog category filter from `Predatory Lending` to
  `High-Cost Lending` while preserving the existing slug and route behavior.

Verification:

- `git diff --check` passed.
- `npm run build` passed with 18,415 SSR route URLs, 124 city guides, and 2,232
  city-category sub-pages.
- Postbuild sitemap/robots check passed.
- Targeted rendered scan returned zero matches for the Batch 148 visible blog
  teaser phrase set: broken emergency-cash grammar, old $100-$50,000
  hard-sell wording, `predatory payday loan traps`, `Credit Repair Scams: How
  to Spot`, and `legitimate ways to repair your credit`.
- Positive rendered checks confirmed replacement language on `/blog/` and
  `/learn/`.
- Local static route checks returned HTTP 200 for `/`, `/blog/`, `/learn/`,
  `/financial-wellness/`, and `/sitemap-index.xml`.
- Production spot checks returned HTTP 200 for `/`, `/blog/`, `/learn/`,
  `/financial-wellness/`, `/sitemap-index.xml`,
  `/blog/emergency-loans-bad-credit-options-within-24-hours/`, and
  `/blog/credit-repair-scams-how-to-spot-them-and-what-to-do-instead/`.

Notes:

- The two blog article routes are SSR routes and returned 404 from a simple
  local static server, but production returned HTTP 200.
- Additional unrelated content JSON edits were present in the working tree and
  were not staged or committed.

Workpack:

- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_148_notes_2026-05-27.md`

## 2026-05-27 - Sitewide Page Upgrade Batch 149

Batch 149 implementation committed as `a28fb2e726` for provider-card
funding and approval timing residue cleanup.

Changes:

- Added final shared safe-copy cleanup for city and browse provider-card
  wording that previously rendered as `funding-timing claims to verify`.
- Normalized `next-day funding-timing claims to verify`,
  `same-day approval claim to verify`, and `instant approval decisions` into
  clearer provider-stated timing/context wording.
- Mirrored the cleanup in `LenderCard.astro` so card-specific output catches
  final residue after broader YMYL transformations.
- Preserved source lender records, city/category routes, generated inventory,
  and profile slugs.

Verification:

- `git diff --check` passed.
- Clean `npm run build` passed with 18,415 SSR route URLs, 124 city guides, and
  2,232 city-category sub-pages.
- Postbuild sitemap/robots check passed.
- Rendered scan across `dist/city` and `dist/browse` returned zero matches for
  `same-day to next-day funding-timing claims to verify`,
  `next-day funding-timing claims to verify`, `funding-timing claims to
  verify`, `same-day approval claim to verify`, and `instant approval
  decisions`.
- Positive rendered checks confirmed replacement wording such as
  `provider-stated funding timing` and `provider-stated same-day approval
  timing`.
- Local static route checks returned HTTP 200 for `/`,
  `/city/colorado-springs-co/`, `/city/norfolk-va/`,
  `/browse/business-loans/new-york-ny/`,
  `/browse/emergency-cash/miami-fl/`, and `/sitemap-index.xml`.
- Production spot checks returned HTTP 200 for the same routes.

Notes:

- A concurrently started `deploy.sh` was stopped before deployment because it
  was building from a working tree that contained uncommitted Batch 149 edits.
  No files were modified by stopping that process.

Workpack:

- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_149_notes_2026-05-27.md`

## 2026-05-27 - Sitewide Page Upgrade Batch 150

Batch 150 implementation committed as `0da6966ded` for no-credit-check and
approval-timing residue cleanup across city, browse, and comparison pages.

Changes:

- Added plural no-credit-check cleanup in shared YMYL safe-copy output.
- Mirrored the cleanup in provider cards and comparison-page text sanitizers.
- Normalized `no credit checks required`, `no credit checks`,
  `with no-credit-check...`, and hyphenated `no-credit-check option(s)` profile
  signals into eligibility-context wording.
- Normalized plural `same-day approvals` into provider-stated same-day approval
  timing language.
- Preserved source lender records, comparison records, city/category routes,
  generated inventory, and profile slugs.

Verification:

- `git diff --check` passed.
- `npm run build` passed with 18,415 SSR route URLs, 124 city guides, and 2,232
  city-category sub-pages.
- Postbuild sitemap/robots check passed.
- Rendered scan across `dist/city`, `dist/browse`, and `dist/compare` returned
  zero matches for `no credit checks required`, `no credit checks`,
  `with no-credit-check`, `no-credit-check options`, `no-credit-check option`,
  `no-credit-check claims to verify`, `no-credit-check claim to verify`,
  `same-day approvals`, and `funding-timing claims to verify`.
- Local static route checks returned HTTP 200 for `/`,
  `/city/virginia-beach-va/`, `/browse/pawn-shops/virginia-beach-va/`,
  `/browse/credit-unions/memphis-tn/`,
  `/compare/kikoff-vs-the-credit-gal/`, and `/sitemap-index.xml`.
- Production spot checks returned HTTP 200 for the same routes.

Notes:

- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged content changes and were not staged or committed in this
  batch.

Workpack:

- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_150_notes_2026-05-27.md`

## 2026-05-27 - Sitewide Page Upgrade Batch 151

Batch 151 implementation committed as `49d19238b2` for city-page regulatory
bullet safe-copy coverage.

Changes:

- Updated the city page "Key Regulations" bullet renderer to pass state-law
  bullet text through `softenYmylCopy`.
- Removed remaining city-page regulatory `predatory lending` wording from
  rendered output while preserving the underlying state-law source records.
- Preserved city routes, provider cards, category sections, source lender
  records, and generated inventory.

Verification:

- `git diff --check` passed.
- `npm run build` passed with 18,415 SSR route URLs, 124 city guides, and 2,232
  city-category sub-pages.
- Postbuild sitemap/robots check passed.
- Rendered scan across `dist/city`, `dist/browse`, and `dist/compare` returned
  zero matches for `predatory lending`, `anti-predatory lending protections`,
  `protections against predatory lending`, and
  `consumer protection against predatory lending`.
- Local static route checks returned HTTP 200 for `/`,
  `/city/virginia-beach-va/`, `/city/baltimore-md/`,
  `/city/minneapolis-mn/`, `/city/little-rock-ar/`, and
  `/sitemap-index.xml`.
- Production spot checks returned HTTP 200 for the same routes.

Notes:

- Render-time template cleanup only; no source state-law, comparison, or lender
  records changed.
- `src/content/comparisons.json` and `src/content/wellness-guides.json` remain
  unrelated unstaged content changes and were not staged or committed in this
  batch.

Workpack:

- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/batch_151_notes_2026-05-27.md`

## 2026-06-01 - Route Self-Healer Log De-Dupe

Fixed duplicate logging in
`tools/creditdoc_route_self_healer.py`.

Finding:

- The monitor wrote each log line directly to
  `/srv/BusinessOps/logs/creditdoc_route_self_healer.log`.
- Cron also redirected stdout to that same file.
- Result: historical self-healer counts were doubled in the raw log.

Change:

- `log()` now detects whether stdout already points at the self-healer log.
- If cron is already redirecting stdout to the log, the script does not append a
  second copy.
- Manual runs still print and append normally.

Verification:

- `python3 -m py_compile tools/creditdoc_route_self_healer.py` passed.
- Cron-style redirected `--check-only` run wrote one line, not two.
- Live production route check returned `10/10` route families healthy.
- Correct de-duplicated historical heal count as of 2026-06-01 06:00 UTC:
  2 actual heal starts, not 4.

## 2026-06-01 - SSR Versioned Cache Coverage Pass 1

Expanded existing middleware versioned cache coverage to the main SSR route
families that were still relying on page `Cache-Control` headers only:

- `/review/[slug]/`
- `/state/[slug]/`
- `/credit-guide/[slug]/`
- `/credit-guide/[slug]/[category]/`
- `/blog/[slug]/`
- `/financial-wellness/[slug]/`

Implementation notes:

- Reused the existing Cloudflare Cache API middleware pattern.
- Version keys use each route family's existing source table `updated_at`.
- State pages use a custom slug-to-state-name version lookup because the
  `states` table has no slug column.

Verification:

- `npm run build` passed.
- `git diff --check` passed.
- Live status checks returned HTTP 200 for Lexington Law review, Wyoming state,
  Austin city guide, Austin credit-repair city-guide category, a blog post, and
  a financial-wellness guide.

## 2026-06-01 - Deploy Route Warmer Coverage

Expanded `deploy.sh` post-deploy verification so it also warms the main
versioned-cache SSR route families after every cache purge/deploy:

- review
- state
- city guide
- city guide category
- answer
- best/listicle
- category
- blog
- financial wellness

Verification:

- `bash -n deploy.sh` passed.
- Live checks for every warmer URL returned HTTP 200.
- All checked cacheable routes returned `x-cdm-cache: HIT` after warming.

## 2026-06-01 - Self-Healer Diagnostics Pass

Enhanced `tools/creditdoc_route_self_healer.py` route records with:

- Cloudflare `cf-ray`
- CreditDoc `x-cdm-cache`
- response seconds in failure log lines

Verification:

- `python3 -m py_compile tools/creditdoc_route_self_healer.py` passed.
- `--check-only` returned `10/10` route families healthy.
- State file now records cache/ray evidence for checked routes.

## 2026-06-01 - Answers Index Versioned Cache

Added middleware versioned cache coverage for `/answers/`, which was one of the
SSR route families that previously appeared in self-healer failures.

Implementation notes:

- `/answers/` uses the latest visible `answers.updated_at` value as the cache
  version.
- Added `/answers/` to the deploy warmer URL list.

Verification:

- `npm run build` passed.
- Deployed Worker version `b045b169-8217-436c-b450-4767becc0703`.
- Initial deploy script verification exited early because `set -e` treated a
  missing optional `x-cdm-cache` header as fatal in the deploy warmer pipeline.
  Fixed the script with an explicit `|| true` on that optional header read.
- Manual post-deploy checks returned HTTP 200 for all warmed route families.
- Second-pass checks showed `x-cdm-cache: HIT` for `/answers/`, answer slug,
  best/listicle, category, blog, and financial-wellness routes.
- Self-healer `--check-only` returned `10/10` route families healthy.

## 2026-06-01 - Brand Page Versioned Cache

Added middleware versioned cache coverage for `/brand/[brand]/` public SEO
pages using `brands.updated_at`.

Verification:

- `npm run build` passed.
- `/brand/advance-america/` returned HTTP 200 before deployment and was added
  to the deploy warmer URL list.

## 2026-06-02 - Debugger Follow-Up: Guardrails and Comparison Copy

Fixed the issues found by the debugger review of the CreditDoc content
guardrails:

- Existing comparison render safety now also softens `clear pick`, which had
  leaked into one rendered comparison page.
- Public policy pages no longer promise hard monthly pricing verification or
  quarterly full reviews unless a proven process backs that exact cadence. They
  now describe scheduled data refreshes, editorial passes, and source updates.
- Operational generator guardrails in `/srv/BusinessOps/tools` now catch
  natural-language current fact claims such as `$99 per month`, `4.9 out of 5
  on Google`, `12% APR`, `approves 95% of applicants`, and `money-back
  guarantee`.
- Comparison generator guardrails now validate sourced values per named company,
  so a price/rating from Company A cannot be assigned to Company B just because
  the value appeared somewhere in the two-company prompt.

Repo commit and deploy:

- Commit: `619955e7c1 fix: strengthen CreditDoc comparison safety copy`.
- Deployed Cloudflare Worker version
  `07b46d6f-a5a0-4e99-832f-2d174c7e010a`.

Verification:

- `npm run build` passed with robots/sitemap checks.
- Guardrail regression checks passed: unsafe provider claims fail, legal
  educational `36% MAPR` context passes, right-company sourced values pass, and
  wrong-company sourced values fail.
- Live `/disclaimer/`, `/editorial-policy/`, `/methodology/`, and the touched
  comparison URL returned HTTP 200.
- Live touched comparison page no longer contains `clear pick`.
- Route self-healer check-only returned `10/10` with zero failures.

## 2026-06-09 - City Guide Guardrail Recovery

Fixed a live city-guide content-engine regression where recent guides were
generating but being blocked by false-positive guardrail failures.

What happened:

- The city-guide generator correctly supplied FDIC/SBA/CFPB/state-law facts to
  the prompt, but validation only allowed exact raw values from
  `city_info`, `state_data`, and `local_stats`.
- Generated copy often rewrote sourced public facts into normal reader-facing
  forms, for example `$27372.6M` as `$27.3 billion` or `$500,000` followed by a
  comma in prose.
- The shared current-fact guardrail then misread those sourced public facts as
  unsupported provider prices, rates, or ratings.

Live tool fixes:

- `/srv/BusinessOps/tools/creditdoc_city_guide_generator.py` now builds a
  city-guide-specific allowed-value set that includes normalized SBA totals,
  standard SBA program limits, payday-law/PAL public-program values, state
  income variants, and common credit-education percentages.
- `/srv/BusinessOps/tools/creditdoc_content_guardrails.py` now canonicalizes
  trailing punctuation so sourced values such as `$500,000,` match `$500,000`.
- `/srv/BusinessOps/tools/creditdoc_comparison_generator.py` now passes imported
  `google_rating` and `google_reviews_count` explicitly as `Google Rating`
  source facts, separate from the internal CreditDoc rating.

Important source-data rule:

- Google/BBB values must not be assumed fake. CreditDoc has imported source
  records in `src/content/lenders/*.json` and `data/creditdoc.db` with
  `data_source: outscraper`, `google_rating`, `google_reviews_count`,
  `google_place_id`, and BBB fields. Future validator work must trust values
  present in those source records and block only model-invented values outside
  the supplied/imported source data.

Recovery completed:

- Reprocessed and live-verified HTTP 200:
  `visalia-ca`, `topeka-ks`, `coral-springs-fl`, `warren-mi`,
  `sterling-heights-mi`, `elizabeth-nj`, `norman-ok`, `kent-wa`,
  `west-palm-beach-fl`.
- Final recovery batch ended `Generated: 5 | Failed: 0`.
- Queue advanced past the previously blocked cities to Hampton, New Haven,
  Clearwater, West Valley City, and Miramar.

Verification:

- `python3 -m py_compile` passed for both patched live scripts.
- Debugger-style validation confirmed sourced public facts pass, imported
  Google comparison facts pass, and unsourced BBB/Google company rating claims
  still block.
- All nine recovered live city-guide URLs returned HTTP 200.

## 2026-06-09 - Guardrail Repeat-Proofing

Completed the follow-up hardening so this class of failure is checked
automatically.

Implemented:

- Extended `/srv/BusinessOps/tools/test_creditdoc_content_guardrails.py` with
  regression cases for city-guide sourced SBA/public-law facts, money
  punctuation variants, imported Google rating/review source facts, and
  invented Google rating claims.
- Confirmed `/srv/BusinessOps/tools/creditdoc_content_engine_daily_verify.py`
  runs that regression test as a command check.
- Mirrored the live guardrail/generator/verifier scripts into tracked repo path
  `tools/live_ops/` because `/srv/BusinessOps/tools` is not itself a git
  repository.

Verification:

- Direct guardrail regression command passed.
- `python3 -m py_compile` passed for the patched live scripts.
- Daily verifier dry-run with `--allow-pending` passed at 2026-06-09 12:03 UTC,
  including the guardrail regression hook and all queue reserve checks.

Operational rule:

- Whenever a live script under `/srv/BusinessOps/tools` is changed for
  CreditDoc, mirror the changed file into `tools/live_ops/` and commit it with
  the related handoff/memory update.

## 2026-06-09 - Repair-And-Revalidate Generator Hardening

Added the missing constructive guardrail behavior across the content engines.

Implemented:

- Added `/srv/BusinessOps/tools/creditdoc_content_repair.py`.
- Wired one conservative repair pass into:
  `/srv/BusinessOps/tools/creditdoc_city_guide_generator.py`,
  `/srv/BusinessOps/tools/creditdoc_comparison_generator.py`,
  `/srv/BusinessOps/tools/creditdoc_blog.py`,
  `/srv/BusinessOps/tools/creditdoc_wellness_generator.py`, and
  `/srv/BusinessOps/tools/creditdoc_cluster_executor.py`.
- Flow is now: generate JSON, validate guardrails, repair once if needed,
  revalidate, then publish/reject/save draft based on the same guardrails.

Repair behavior:

- Preserves JSON shape.
- Does not invent replacement facts.
- Removes or rewrites unsupported current prices, APRs, ratings, review
  counts, guarantees, approval odds, or company claims.
- Uses source context where available, including city public facts and
  comparison lender summaries.

Verification:

- `python3 -m py_compile` passed for the repair helper and all wired live
  generators.
- Direct guardrail regression test passed.
- Daily verifier dry-run with `--allow-pending` passed at 2026-06-09 12:07 UTC,
  including queue reserves and generated-content guardrail regression.
- Mirrored the changed live scripts into `tools/live_ops/` for committed
  rollback/reference because `/srv/BusinessOps/tools` is not a git repo.

## 2026-06-09 - Tools Directory Cleanup

Committed the remaining tools-page work after debug review.

Added:

- `/tools/loan-denial-reason-checker/`
  - Educational denial-pattern checker for personal loans, credit cards,
    business/SBA loans, debt consolidation, and MCA/fast funding.
  - Uses adverse-action notice framing and links to published CreditDoc answer,
    research, checklist, and calculator resources.
- `/tools/credit-repair-qualify-quiz/`
  - Educational credit-repair fit quiz that routes users toward credit repair
    research, DIY report review, or credit-building/debt tools.
  - Uses imported credit-repair profile data for optional research cards.
  - Profile cards render user/data text with DOM `textContent`, not raw
    interpolated HTML.
- `/tools/`
  - Added cards for the two new tools.
  - Added a courses/checklists section linking to credit fundamentals and the
    credit report checklist.
- `tools/creditdoc_priority_indexing.py`
  - Promoted verified tools, courses/learn, research, regulatory/trust, and
    wellness pages ahead of money/answer/city/blog pages in the priority
    indexing queue.
  - Kept the existing safety rule that unchecked URLs are not submitted blind.
  - Updated tier reporting so future alerts show the new queue mix accurately.

Verification:

- Independent debug agent reviewed the tool pages, live-op mirrors, and
  handoff documentation. No loan-tool syntax/schema/link issues were found.
- Dynamic links referenced by the tools were verified against repo pages or DB
  content tables.
- Priority indexer dry-run passed at 2026-06-09 12:19 UTC and returned verified
  tools, course/learn, research, regulatory/trust, and wellness URLs.
- `npm run prebuild` passed.
- `npx astro sync` passed.
- `git diff --check` passed for the tool pages.
- Full `npm run build` passed at 2026-06-09 12:21 UTC, including Astro
  prerender and the postbuild sitemap/robots check.

## 2026-06-09 - Tools + Regulatory Quiz Strategy Memory

Saved Faraday's reviewer findings as a strategic workstream, not a loose bug
list.

Memory/project locations:

- `/root/.claude/projects/-srv-BusinessOps/memory/creditdoc_tools_regulatory_quiz_strategy_2026-06-09.md`
- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Tools_Regulatory_Quiz_Strategy_2026-06-09/`

Key direction:

- Review pages were created first; tools/quizzes must now sit on top of that
  review/regulatory data layer.
- Do not treat the credit-repair quiz as complete until provider filtering
  excludes quarantined/noindex/held profiles, provider text is safely escaped,
  quiz answers/results feed the real lead/quiz layer, and results route users
  through CreditDoc-specific review, regulatory, complaint, state, course,
  checklist, wellness, and listicle assets.
- This should be embedded into the short- to mid-term AI workforce goals:
  build useful tools and quizzes in tandem with indexing/backlink work, while
  making CreditDoc's regulatory track-record data the differentiator.

## 2026-06-09 - Origination Capture System Direction

Saved Jammi's clarification that interactive CreditDoc assets should feed an
origination system, not just standalone tools or email-only funnels.

Memory/project locations:

- `/root/.claude/projects/-srv-BusinessOps/memory/creditdoc_origination_capture_system_2026-06-09.md`
- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Origination_Capture_System_2026-06-09/`

Execution direction:

- Visitor uses a quiz, checker, calculator, course CTA, or checklist CTA.
- We capture email and send the response/nurture through the existing Sendy
  system.
- We also persist structured answers/result path/source URL/category/consent
  into the CreditDoc lead/quiz layer.
- Those records become the future input for embedded-finance matching and
  origination routing: affiliate, BrokerOS/direct broker, or later embedded
  partners.

Guardrails:

- Do not build a separate disconnected lead system.
- Do not ask for SSNs or sensitive documents in the front-end tools.
- Do not imply approval, underwriting, or prequalification unless a real
  partner/API supports it.

## 2026-06-09 - Temporary Autonomous Tools Continuation

Set up a temporary cron handoff so CreditDoc tools/origination construction can
continue while Jammi is away.

Operational details:

- Cron entry: `7 */4 * * * /srv/BusinessOps/creditdoc/tools/creditdoc_tools_autonomous_continue.sh`
- Cutoff: `2026-06-12T00:00:00Z`
- Log: `/srv/BusinessOps/logs/creditdoc_tools_autonomous_continue.log`
- Isolated worktree: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Tools_Autonomous_Worktree_2026-06-09`
- Branch: `creditdoc-tools-autonomous-2026-06-09`
- Prompt: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Origination_Capture_System_2026-06-09/AUTONOMOUS_TOOLS_PROMPT.md`

Safety behavior:

- The runner uses `flock` so two runs cannot overlap.
- It skips if `/srv/BusinessOps/creditdoc` is dirty, to avoid clashing with
  another agent.
- It skips if the isolated worktree is dirty from a prior run.
- It runs `npm run build` before committing autonomous changes.
- It commits locally only. It does not push or deploy from cron.
## 2026-06-16 - Indexing Priority Guardrail

Tools, quizzes, questionnaires, courses, answer/question pages, and money pages are the priority for indexing. City pages must be last.

Implemented and verified in both indexing paths:

- /srv/BusinessOps/tools/creditdoc_daily_gsc_queue.py
- /srv/BusinessOps/creditdoc/tools/creditdoc_priority_indexing.py

Current order: tools/quizzes/questionnaires, courses/learn, answers/questions, money pages (/best/, /categories/, /browse/, /compare/), then trust/resource/supporting pages. City guides are last.

Tracking check on 2026-06-16: request_indexing_count and last_request_indexing_submitted are consistent across indexation_status; 1,049 rows have both fields set and there are 0 mismatched submission-tracking rows.

Verification: py_compile passed for both scripts; daily GSC queue dry-run selected 10 money /browse/ URLs and no city URLs; priority indexer dry-run selected money URLs first and reported City: 0.

## 2026-06-16 - Loan Approval Toolkit Phase 0

Plan saved at `/srv/BusinessOps/creditdoc/docs/plans/2026-06-16-loan-approval-readiness-toolkit.md`.
Existing indexing-priority changes were committed separately as `279f452c55` before toolkit implementation. Next task: create the toolkit and printable pages, build-verify, then commit. No deploy unless Jammi approves.
## 2026-06-16 - CreditDoc loan approval toolkit Phase 1 complete

Implemented the public Loan Approval Readiness Toolkit as the first missing linkable asset from the 2026-06-05 plan. No deploy was performed.

Files added:
- /srv/BusinessOps/creditdoc/src/pages/resources/loan-approval-readiness-toolkit/index.astro
- /srv/BusinessOps/creditdoc/src/pages/resources/loan-approval-readiness-toolkit/print/index.astro

What shipped locally:
- Public no-signup resource page for personal loans, business loans, SBA loans, credit cards, debt consolidation, denial follow-up, and cash-flow funding prep.
- Printable checklist page for advisors/libraries/small-business helpers.
- Internal links to the existing tools, answer cluster pages, and money category pages.
- Official-source links to AnnualCreditReport.com, CFPB, FTC, and SBA.
- Article, ItemList, and Breadcrumb JSON-LD; avoided HowTo schema because the content is a branching checklist rather than a linear process.
- Print-page CSS hides global header/footer/cookie banner during printing.

Verification:
- Full npm run build passed on 2026-06-16, including Astro build, prerender, sitemap generation, and postbuild sitemap/robots check.
- git diff --check passed.
- Generated routes exist at /resources/loan-approval-readiness-toolkit/ and /resources/loan-approval-readiness-toolkit/print/.
- Independent debug agent reviewed the two files, found print chrome, nested-main, and HowTo schema issues, then re-reviewed after fixes and reported no findings.

Next recommended step: commit Phase 1, then add hub/internal links from /resources/, /tools/, and relevant answer/category pages before any deploy.
## 2026-06-16 - CreditDoc loan approval toolkit deployed

Deployed the Loan Approval Readiness Toolkit work to Cloudflare Workers on 2026-06-16.

Code commits deployed:
- b7c294eb73 feat: add loan approval readiness toolkit
- 7d2ea36cdf fix: link loan readiness toolkit from resources

Cloudflare deploy result:
- Worker deploy completed successfully.
- Current Version ID: 534ba7ba-1606-4eca-a76c-c490a82f93a5.
- Cloudflare cache purge succeeded.
- Deploy script smoke tests returned 200 for homepage, CSS, and core SSR route families.

Targeted live checks:
- https://www.creditdoc.co/resources/loan-approval-readiness-toolkit/ returned 200.
- https://www.creditdoc.co/resources/loan-approval-readiness-toolkit/print/ returned 200.
- https://www.creditdoc.co/resources/ returned 200.
- Live toolkit HTML contains the Loan Approval Readiness Toolkit title, ItemList JSON-LD, and printable checklist CTA.
- Live print HTML contains Printable Loan Readiness Checklist, window.print, and print CSS hiding body header/footer and the cookie banner.
- Live resources hub HTML contains the toolkit card and public-resource footer link.

Independent debug agent result:
- Initial deploy review found one Medium non-blocking issue: toolkit was not linked from the resources hub/footer.
- Fixed with a hub card in src/pages/resources/index.astro and footer link in src/layouts/BaseLayout.astro.
## 2026-07-05 - CreditDoc SE Ranking 5XX diagnosis and runtime hardening

Investigated the SE Ranking audit at `SEO/audit_creditdoc.co_2026-07-05_13-36-15.pdf`.

Findings:
- The audit reported 671 URLs with 5XX, including review, category, and credit-guide category URLs.
- Spot checks and a 160-URL SEBot-style probe returned current 200s, so these are not permanently broken URLs.
- The affected URL families are dynamic Astro SSR routes listed in the sitemap, especially `/review/[slug]/`, `/categories/[category]/`, and `/credit-guide/[slug]/[category]/`.
- Static tools, answers, blog, wellness, course, city, browse, comparison, trend, and resource pages were confirmed by `npm run build` to prerender as real HTML in `dist/`.
- The immediate failure mode was uncaught `fetch(... AbortSignal.timeout(...))` calls in `src/lib/db.ts`. During crawler bursts or cold-cache requests, Supabase/PostgREST timeouts could throw through Astro SSR and produce Worker 5XX, then later look fine once cached or under lighter load.

Fix applied:
- Added safe runtime JSON fetch handling in `src/lib/db.ts`.
- Runtime Supabase network/timeouts now degrade to `null` or `[]` instead of throwing into page render for the shared DB data layer.
- Category count/top-lender fetches now catch timeout/network exceptions as well.

Verification:
- `npm run build` passed on 2026-07-05.
- Prebuild checks passed: content text integrity, robots contract, SSR sitemap parity.
- Postbuild checks passed: sitemap/robots conflicts, critical sitemap URLs, feed contract, image alt contract, image filename contract.
- Build output explicitly generated static HTML for `/answers/`, `/blog/`, `/financial-wellness/`, `/courses/`, `/tools/`, `/city/`, `/browse/`, `/compare/`, `/trends/`, and resources.

Remaining structural SEO risk:
- `/review/`, `/categories/`, `/state/[slug]/`, `/brand/`, and `/credit-guide/[slug]/...` still depend on Astro SSR + Supabase at request time.
- The durable fix is to staticize the highest-value sitemap-listed SSR families or add stale-cache fallback behavior so crawlers never depend on live DB reads for critical SEO pages.

- Final debug pass confirmed the finding was resolved and no deploy blockers remained.

Standing next step: review the live page manually, then consider adding contextual links from relevant answer/category pages and submitting the new resource URLs for priority indexing.

## 2026-06-16 - CreditDoc printable resource logo deployed

Added the CreditDoc logo lockup to the printable/downloadable resource headers for:
- /resources/loan-approval-readiness-toolkit/print/
- /resources/credit-report-checklist/print/

Code commit: c75e652de8 fix: brand printable resources.
Cloudflare deploy successful on 2026-06-16; Worker Version ID: 702a2b3b-e386-4fe9-9eee-34324543a1a4.

Verification:
- npm run build passed, including sitemap generation and postbuild sitemap/robots check.
- git diff --check passed.
- Live HTML for both print URLs contains aria-label=CreditDoc and the appropriate printable resource label.
- Credit report checklist print CSS was hardened to hide only global site header/footer and the cookie banner, preserving the printable article header/logo.

## 2026-06-16 - CreditDoc loan toolkit tools hub placement

Completed Task 2 tools-hub placement for the Loan Approval Readiness Toolkit.

Code commit: 92452f6d3d feat: feature loan toolkit on tools hub.

What changed:
- Added Loan Approval Readiness Toolkit to /tools/ Courses And Checklists section.
- Link target: /resources/loan-approval-readiness-toolkit/.
- Preserved tablet two-column layout and added large-screen three-column layout with sm:grid-cols-2 lg:grid-cols-3.

Verification:
- npm run build passed after the responsive class fix, including prebuild robots/SSR sitemap parity and postbuild sitemap/robots conflict checks.
- Generated /tools/ output contains the toolkit card and link.
- Debug agent Anscombe reviewed the scoped change and reported no blocking findings; only noted the unrelated untracked Engine readiness markdown should stay out of commits.

## 2026-06-16 - CreditDoc loan toolkit tools hub deployed

Deployed the tools hub placement for the Loan Approval Readiness Toolkit to Cloudflare Workers.

Code commits deployed:
- 92452f6d3d feat: feature loan toolkit on tools hub
- cbfe718d82 docs: log loan toolkit tools placement

Cloudflare deploy result:
- Deploy completed successfully.
- Current Version ID: 5100fcc8-82ef-4bed-a121-a507d0192ad8.
- Cloudflare cache purge succeeded.
- Deploy script smoke tests returned 200 for homepage, CSS, and core SSR route families.

Targeted live check:
- https://www.creditdoc.co/tools/ contains Loan Approval Readiness Toolkit, links to /resources/loan-approval-readiness-toolkit/, and uses sm:grid-cols-2 lg:grid-cols-3 for the Courses And Checklists cards.

Repo note: unrelated untracked file remains excluded from commits: CreditDoc_Engine_Embedding_Readiness_Activities_2026-06-16.md.

## 2026-06-16 - CreditDoc lender category and outbound tracking fixes build-verified

Fixed the validated issues from the CreditDoc Free Fixes review in the local CreditDoc repo. This is not deployed yet.

What changed:
- Upstart was corrected from credit-repair to personal-loans in the live DB via creditdoc_db.py update/export flow and local mirror file src/content/lenders/upstart.json.
- Added src/utils/outbound.ts for lender destination selection, /go/ href generation, and normalized tel: links.
- Added SSR route src/pages/go/[slug].ts for outbound CTA redirects. It prefers affiliate_url, falls back to website_url, validates http/https, adds UTM tracking to non-affiliate website fallbacks, and returns no-store plus x-robots-tag noindex/nofollow.
- Review, best, and compare templates now route provider CTAs through /go/<slug>/ with source parameters and sponsored/nofollow rel values.
- Review phone links now use normalized tel: hrefs.
- Best/listicle loan cards no longer show credit-repair subscription-style From Free/mo for loan categories; loan categories show Rates and terms vary.
- Review quiz Compare alternatives link is category-aware instead of hardcoding best-credit-repair-companies for every provider category.
- robots.txt blocks /go/ for wildcard and each named AI crawler group; SSR sitemap parity exempts go/[slug].ts as an intentional redirect-only robot-blocked route.

AI bug auditor result:
- Auditor flagged two real issues after the first pass: named robots groups still allowed /go/, and /go/[slug].ts checked raw affiliate_url instead of normalized affiliate URL for UTM decisions.
- Both issues were fixed before final verification.

Verification:
- node --check src/pages/go/[slug].ts passed.
- git diff --check passed.
- npm run build passed on 2026-06-16, including robots contract, SSR sitemap parity, Astro build, sitemap generation, and postbuild sitemap/robots conflict check.

Repo note:
- Unrelated untracked file remains excluded: CreditDoc_Engine_Embedding_Readiness_Activities_2026-06-16.md.
- Changes are not committed or deployed yet as of this note.

## 2026-07-05 - CreditDoc SE Ranking 5XX static snapshot remediation

Implemented the first structural remediation for the SE Ranking 5XX report by
committing static HTML snapshots for the exact URLs extracted from the report's
5XX sections.

What changed:
- Added `scripts/create_seranking_static_snapshots.mjs`.
- Added `data/seranking_static_snapshot_urls_2026-07-05.json` with 124 URLs:
  97 review pages, 26 credit-guide city/category pages, and 1 category page.
- Added 124 committed `public/.../index.html` snapshots with a static marker.
- Updated `src/middleware.ts` so exact trailing-slash manifest paths are served
  from the Cloudflare `ASSETS` binding before SSR/Supabase cache logic.

Verification:
- `npm run build` passed after the debugger-agent fix.
- Postbuild sitemap/robots, critical sitemap, feed, image-alt, and image-file
  contracts passed.
- Focused snapshot check passed: 124 unique URLs, no bad families, no query
  URLs, no `/go` or `/search`, all generated in `dist`, all include the static
  marker, and none contain `noindex`.
- Built Worker check confirmed exact-path matching with
  `SERANKING_STATIC_SNAPSHOT_PATHS.has(pathname)`.
- Debugger agent Schrodinger reviewed the patch and found one issue: slashless
  variants were also matched. Fixed before commit by preserving exact manifest
  pathnames including trailing slash.

Deployment still required after commit: push, Cloudflare deploy, targeted purge
of the 124 snapshot URLs, and live sample checks for the `x-cdm-static-snapshot:
seranking-2026-07-05` header.

Deployment completed:
- Code commit: `ab7add9942` (`Staticize SE Ranking flagged pages`).
- Pushed to GitHub branch `cdm-rev-hybrid`.
- Cloudflare deploy succeeded on 2026-07-05; Worker Version ID:
  `6f2b68cc-d565-4541-93f9-9fab8de269d7`.
- Purged all 124 manifest URLs from Cloudflare cache in five successful purge
  batches.
- Live representative checks returned 200 with static snapshot marker and no
  `noindex` for `/review/deluxe-credit-solutions/`, `/review/prosper/`,
  `/categories/credit-unions/`, `/credit-guide/amarillo-tx/business-loans/`,
  `/credit-guide/austin-tx/mortgages/`, and
  `/credit-guide/charlotte-nc/banking/`.
- Live slashless variants returned 307 redirects to trailing-slash canonical
  paths.
- Full live 124-URL sweep passed: 124 checked, 0 failures. Each URL returned
  200, included the static snapshot marker, and did not include `noindex`.

Note: Cloudflare served these URLs as static assets directly, so the custom
middleware header was not present live. That is acceptable because the responses
had the committed static marker and no `x-cdm-cache`/`x-cdm-route` SSR headers.

## 2026-07-05 - Static SEO surface debugger audit and route hardening

Debugger agent Godel audited the requested static SEO surfaces:
answers/questions, blogs, tools, financial wellness, and courses.

Confirmed static HTML counts in `dist`:
- `answers`: 492 HTML files, including 491 leaf pages plus index.
- `blog`: 106 HTML files, including 105 leaf pages plus index.
- `tools`: 19 HTML files, including 18 tool pages plus index.
- `financial-wellness`: 140 HTML files, including 139 leaf pages plus index.
- `courses`: 10 HTML files, including course root/module pages.

Source checks:
- Dynamic routes use `getStaticPaths()`.
- `astro.config.mjs` keeps `output: 'static'`.
- No `export const prerender = false` exists under the requested route
  directories.

Issue found and fixed:
- The generated `_routes.json` previously had `include: ["/*"]` with no broad
  excludes for `/answers`, `/blog`, `/tools`, `/financial-wellness`, or
  `/courses`, so those static SEO families were Worker-eligible.
- Added exact and wildcard Cloudflare route excludes for all five families in
  `astro.config.mjs`.

Verification:
- `npm run build` passed, including prebuild and postbuild contracts.
- Local audit across all 767 requested HTML files passed for title, meta
  description, canonical, H1, and no `noindex`.
- Generated `_routes.json` now includes excludes for `/answers`, `/answers/*`,
  `/blog`, `/blog/*`, `/tools`, `/tools/*`, `/financial-wellness`,
  `/financial-wellness/*`, `/courses`, and `/courses/*`.
- Deployed to Cloudflare Workers; Version ID:
  `d2cb8be0-ae1f-498f-bb43-a599dd8dfca2`.
- Full live sweep passed: 767 URLs checked, 767 HTTP 200, 767
  `cf-cache-status: HIT`, 0 `x-cdm-cache`/`x-cdm-route` SSR headers, and 0
  `noindex`.

Rule going forward: answers/questions, blogs, tools, financial wellness, and
courses are important SEO surfaces and should stay static HTML plus excluded
from Worker routing unless the user explicitly approves a change.

## 2026-07-06 - Follow-up verification after static SEO hardening

Rechecked the 2026-07-05 fixes on current HEAD after the automated blog commit
`82e7d63da1` (`blog: add 2 article(s) — 2026-07-06`).

Verification:
- Repo was clean before verification.
- `npm run build` passed on current HEAD.
- Prebuild checks passed: content text integrity, robots contract, SSR sitemap
  parity.
- Postbuild checks passed: sitemap/robots conflicts, critical sitemap URLs,
  feed contract, image alt contract, and image filename contract.
- Generated static SEO counts after build:
  - `answers`: 492.
  - `blog`: 108.
  - `tools`: 19.
  - `financial-wellness`: 140.
  - `courses`: 10.
- Generated `_routes.json` still contains all required exact/wildcard excludes
  for `/answers`, `/blog`, `/tools`, `/financial-wellness`, and `/courses`.
- Live SE Ranking snapshot sweep still passed: 124/124 URLs returned 200,
  included the static snapshot marker, and had no `noindex`.

Operational gap found and fixed:
- The two new 2026-07-06 blog URLs built locally but were initially 404 on
  production because the latest content commit had not been deployed yet.
- Deployed the current build to Cloudflare Workers; Version ID:
  `2a2724fc-85c0-4120-9b87-99e09785e1bb`.
- Confirmed both new blog URLs are now live:
  `/blog/can-a-low-credit-score-get-a-mortgage/` and
  `/blog/can-a-student-get-credit-card/`.
- Full live static SEO sweep passed after deploy: 769/769 URLs returned HTTP
  200, with 0 `x-cdm-cache`/`x-cdm-route` SSR headers and 0 `noindex`.

## 2026-07-06 - Answer SEO metadata, schema keywords, and AI ingestion guard

Implemented the answer-page SEO metadata improvement requested from the Phase 1
KPI report.

Changes:
- Added `scripts/creditdoc_answer_meta_audit.mjs`.
- Added npm scripts:
  - `npm run check:answer-meta`
  - `npm run seo:answer-meta:apply`
  - `npm run check:ai-ingestion`
- Added the answer metadata audit and AI-ingestion audit to
  `automation/two_week_seo_calendar.json` and
  `scripts/creditdoc_two_week_seo_runner.mjs`.
- Backfilled answer `primary_phrase`/secondary phrase metadata in controlled
  batches: 162/491 published answers now have `primary_phrase`; 329 remain.
- Repaired bad generated primary phrases; `needs_primary_repair=0`.
- Answer meta audit now reports `meta_too_short=0`, `meta_too_long=0`, and
  `needs_meta_review=0`.
- Added answer keyword output to Article JSON-LD on
  `src/pages/answers/[slug].astro`.
- Added `scripts/check_ai_ingestion_contract.mjs` to prebuild so robots and
  `llms.txt` stay aligned for AI crawlers.
- Added the same AI-ingestion contract to postbuild so built artifact checks
  run after fresh `dist` generation, not only before build.
- Tightened `public/llms.txt` to high-value static surfaces: sitemap index,
  feeds, answers/tools/wellness/course hubs, key tools, key money pages, and
  selected wellness resources. It must not point AI crawlers at `/go/`, `/api/`,
  `/search/`, `/specials/`, or the non-existent `/sitemap.xml`.
- Corrected `feed.xml` wording in `llms.txt`; both feed endpoints are RSS.
- Fixed title normalization in `src/layouts/BaseLayout.astro` to avoid broken
  ellipsis titles and keep rendered titles unique.
- Shortened browse city/category title templates so category pages keep the
  city/state in the title instead of collapsing to duplicates.
- Debugger agent Mencius reviewed the changes. Its non-blocking findings were
  addressed: audit-mode answer metadata reports now use `selected_candidates`
  instead of falsely labeling candidates as `applied`, and the summary now
  exposes `candidate_count`, `selected_candidate_count`, and
  `primary_phrase_coverage_complete=false` while 329 answers remain.

Verification:
- `npm run build` passed with prebuild and postbuild contracts, including the
  postbuild AI-ingestion artifact check.
- `npm run check:seo-deep` passed: 2,875 rendered HTML pages checked,
  25,129 sitemap URLs checked, `errors=0`, `warnings=0`.
- `node scripts/check_ai_ingestion_contract.mjs` passed: robots advertises
  `llms.txt`; `llms.txt` covers 17 high-value URLs and 151 built artifacts.
- `npm run check:answer-meta` passed: 491 published answers, 0 missing answer
  JSON files, 162 with `primary_phrase`, 329 missing `primary_phrase`, 0 meta
  length/review issues, 329 remaining candidates, and 50 selected candidates for
  the next controlled batch.
- Dry-run of the two-week SEO runner for 2026-07-09 passed and includes answer
  metadata plus AI-ingestion audits.
- Rendered spot checks passed for answer pages, `/best/best-sba-loans/`,
  `/tools/sba-loan-calculator/`, `/courses/credit-fundamentals/`,
  `/financial-wellness/sba-loan-application-guide/`, and the formerly duplicate
  browse check-cashing city pages.
- Committed and pushed as `209b1c9ee9`:
  `Improve CreditDoc answer SEO metadata and AI ingestion`.
- Deployed to Cloudflare Workers with Version ID:
  `523f5478-ec63-4411-8a2b-ee28f52a7085`.
- Live smoke checks passed for:
  - `/llms.txt`
  - `/answers/how-to-get-an-sba-loan/`
  - `/tools/sba-loan-calculator/`
  - `/browse/check-cashing/indianapolis-in/`

Important interpretation:
- Regenerating pages is required because the SEO fields are compiled into the
  static HTML in `dist`; the source changes are not visible to Google until the
  static output is rebuilt and deployed.
- This work did not stop or disable cron, feeds, publishing, Pinterest, or
  LinkedIn automation.

## 2026-07-06 - Eagle lender meta cleanup

Cleaned up the two remaining dirty lender files:
- `src/content/lenders/eagle-finance.json`
- `src/content/lenders/eagle-loan.json`

Fix:
- Replaced duplicated/overlapping meta descriptions with unique page-specific
  descriptions.
- Restored the previously removed `last_engine_run` fields.
- Removed unnecessary `brand_slug: null` churn.
- Restored clean JSON formatting with final newlines.

Verification:
- Both files parse as valid JSON.
- Both meta descriptions are 139 characters.
- Duplicate-meta scan confirmed each Eagle meta description is unique across
  `src/content/lenders/*.json`.

## 2026-07-06 - Clean-deploy state sitemap hardening

While attempting to deploy the `/best/` SERP fix from a clean temporary
worktree, the postbuild critical sitemap guard caught a clean-source issue:
`/state/utah/` was missing from the generated sitemap even though
`/state/utah/lending-laws/` was present.

Cause:
- `astro.config.mjs` added SSR state-root sitemap URLs inside
  `ssrSitemapPages()` only after the optional local SQLite export query
  succeeded.
- In a clean deploy worktree the DB-backed category/review/brand export can be
  absent, stale, or empty. That optional failure must not remove SEO-critical
  `/state/<slug>/` root URLs.

Fix:
- Moved state-root injection ahead of DB-backed sitemap URL collection.
- Wrapped DB-backed category/review/brand sitemap collection in its own
  non-fatal `try/catch`.
- State root URLs are now always added from committed `src/content/states.json`
  before optional DB-backed sitemap work.

Verification:
- `npm run build` passed after the fix.
- Postbuild passed: sitemap/robots, critical sitemap URLs, schema/sitemap,
  `/best/` SERP contract, feed, image alt, image filename, and AI-ingestion
  contracts.
- Build log confirmed `[sitemap] added 50 state root URL(s)` before DB-backed
  sitemap collection.

Important interpretation:
- This was a real clean-deploy robustness issue. The live/main working tree
  could pass while a clean deploy could fail because local generated DB state
  masked the dependency. Sitemap-critical SEO surfaces must be derived from
  committed source wherever possible.
- This work did not stop or disable cron, feeds, publishing, Pinterest, or
  LinkedIn automation.

## 2026-07-06 - Restored Best intent on money-page SERPs

Fixed an over-broad YMYL/listicle softening helper that rewrote `/best/`
money-page SEO identity from `Best` to `Compare` at render time. The source
listicles still carried `Best`, but `src/pages/best/[slug].astro` was changing
SEO-critical fields during rendering.

Changes:
- Removed the `Best`/`best` -> `Compare`/`compare` rewrite from
  `softenListicleTitle` so `/best/` page titles, H1s, and Article schema
  headlines preserve exact commercial search intent.
- Added `bestIntentSeoDescription` so meta descriptions keep `Best` when the
  source SEO title uses `Best`, while still allowing cautious comparison wording
  in body copy.
- Added `scripts/check_best_serp_contract.mjs`, `npm run check:best-serp`, and
  a postbuild guard so `/best/` rendered title, H1, meta description, and
  Article schema headline cannot silently lose `Best` or render as `Compare`.

Verification:
- `npm run build` passed, including the new postbuild
  `[best-serp-contract]` check.
- `npm run check:best-serp` passed: 26 `/best/` listicle pages preserve source
  `Best` title intent.
- `npm run check:seo-deep` passed: 2,875 rendered HTML pages, 25,129 sitemap
  URLs, `errors=0`, `warnings=0`.
- `npm run check:schema-sitemap` passed: 25,123 sitemap page URLs, 2,875 HTML
  pages, `warnings=0`.
- Rendered spot checks confirmed `Best` in title/H1/meta description for
  `/best/best-sba-loans/`, `/best/best-small-business-loans/`,
  `/best/best-business-lines-of-credit/`, and
  `/best/best-credit-repair-companies/`.

Important rule:
- Compliance caution should not erase exact SEO intent in page identity. Keep
  caution in claims/body language, but do not let scripts rewrite high-intent
  `/best/` title, H1, meta description, canonical identity, or schema headline
  away from the source page promise.
- This work did not stop or disable cron, feeds, publishing, Pinterest, or
  LinkedIn automation.

## 2026-07-06 - GSC review 404 route-level guard

The first GSC review 404 remediation added a manifest and middleware redirect
map for 802 stale `/review/` URLs from `SEO/Table 404 Missing Pages.csv`, plus a
static `/review/` hub. Live testing showed sample stale review URLs still
returned 404 after deploy, even though the manifest was present in the worker
and other middleware redirects worked.

Second-pass fix:
- Added the same GSC stale-review redirect lookup directly inside
  `src/pages/review/[slug].astro`, before the review database lookup.
- This keeps known stale GSC review URLs from reaching the SSR 404 path even if
  middleware routing does not catch the request first.
- Keep legitimate live review pages excluded from the manifest:
  `/review/power-financial/`, `/review/pioneer-appalachia/`, and
  `/review/mattel/`.

Verification before deploy:
- `npm run build` passed with all postbuild contracts.
- `node scripts/seo_deep_audit.mjs` passed: 2,879 rendered HTML pages, 25,133
  sitemap URLs, `errors=0`, `warnings=0`.
- Full live sweep after deploy initially found 3 remaining non-ASCII encoded
  stale review URLs. The redirect manifest keys and incoming route paths are now
  normalized consistently in both middleware and `src/pages/review/[slug].astro`
  so encoded and decoded Unicode variants hit the same redirect target.
- Follow-up verification: `npm run build` passed, `node scripts/seo_deep_audit.mjs`
  passed, and local redirect-map checks passed for encoded and decoded versions
  of the 3 problem URLs.
- Final deployed version: Cloudflare Workers
  `1337ba0c-0b3c-43fe-97f3-6072f0768700`.
- Final production sweep after purging all 802 stale review URLs from
  Cloudflare cache: 805 unique `/review/` URLs from the GSC CSV checked,
  `805` ended HTTP 200, `badCount=0`. Final destinations: 469 category pages,
  332 `/review/` hub redirects, and 3 legitimate live review pages.

Operational rule:
- For GSC 404 cleanup, do not publish weak/draft review pages just to hide
  errors. Redirect stale/bad crawl paths to the most relevant durable category
  or hub, and prove the behavior with live `curl` checks after deploy.
- This work did not stop or disable cron, feeds, publishing, Pinterest, or
  LinkedIn automation.

## 2026-07-06 - Sitemap and schema contract guard

Added a postbuild contract so sitemap structure and rendered JSON-LD schema are
validated every time the site is built.

Changes:
- Added `scripts/check_schema_sitemap_contract.mjs`.
- Added `npm run check:schema-sitemap`.
- Added the schema/sitemap contract to `postbuild`, after critical sitemap URL
  checks and before feed/image/AI ingestion checks.
- The contract validates sitemap index/files, Google URL/file limits, duplicate
  sitemap URLs, same-origin canonical URL shape, forbidden utility URLs, sitemap
  family crawl-budget guardrails, and static HTML artifacts for important SEO
  families.
- The contract validates rendered JSON-LD syntax, `@context`, `@type`,
  required schema types for answers/best/blog/courses/financial-wellness/tools,
  self-canonicals, title/meta presence, and minimum rendered content depth.
- Legitimate supporting schema URLs for publisher, author, breadcrumbs, related
  links, and hub-level defined-term schema are not treated as page canonical
  mismatches.

Verification:
- `npm run build` passed, including the new postbuild contract.
- `npm run check:schema-sitemap` passed: 25,123 sitemap page URLs, 2,875
  rendered HTML pages, `warnings=0`.
- `npm run check:seo-deep` passed: 2,875 rendered HTML pages, 25,129 sitemap
  URLs, `errors=0`, `warnings=0`.

Important interpretation:
- The sitemap is not missing the core surfaces. Current family counts are
  intentionally measured and guarded; `/review/` and `/credit-guide/` still
  dominate sitemap volume, so future strategy should narrow low-yield crawl
  noise carefully rather than accidentally removing revenue or helpful-content
  surfaces.
- This work did not stop or disable cron, feeds, publishing, Pinterest, or
  LinkedIn automation.
## 2026-07-07 14:49 UTC - Secured/bad-credit cards traffic chunk

Status:
- Deployed secured/bad-credit credit-card exact-intent cluster to Cloudflare Workers version `fafe58f8-a5c2-4fba-8910-564d6f6fa2ef`.

Implemented:
- Added `/answers/credit-cards-for-bad-credit-guide/`.
- Updated `/answers/top-secured-credit-cards/`, `/answers/how-to-apply-for-secured-credit-cards/`, and `/answers/how-does-secured-credit-card-work-for-capital-one/` for exact-intent title/meta/phrase support.
- Updated `/tools/credit-score-simulator/` internal links toward secured cards, credit-builder loans, and relevant answer support.
- Patched `src/pages/answers/[slug].astro` so answer pages strip markdown links before inline auto-linking and exclude markdown tables from TL;DR/key-takeaway extraction.
- Cleaned simulator `WebApplication` author schema to `Organization: CreditDoc Editorial`.

Verification:
- `npm run build` passed all postbuild contracts.
- Live target checks passed: 200 status, canonicals present, JSON-LD present, no raw markdown links, no table leakage in takeaways, no bad safe-copy phrases, no stale executive-person schema.
- `/srv/BusinessOps/.venv/bin/python3 /srv/BusinessOps/tools/creditdoc_feed_continuity_watchdog.py`: all OK.
- `/srv/BusinessOps/.venv/bin/python3 /srv/BusinessOps/tools/creditdoc_content_audit.py --preview --no-fix --stdout`: `0 issues found`.
- `/srv/BusinessOps/tools/verify_crons.sh`: all 59 expected crons present.
- `node scripts/creditdoc_linkedin_manager.mjs audit-social-duplicates`: no current LinkedIn or Pinterest duplicate targets.

Operational note:
- No cron, feed, Pinterest, or LinkedIn automation was stopped or paused.
## 2026-07-07 14:58 UTC - Startup/no-revenue line-of-credit traffic chunk

Status:
- Deployed the next exact-intent business-loan support page to Cloudflare Workers version `14f6a95c-3e49-4970-813c-3def3663eafb`.

Implemented:
- Added `/answers/business-line-of-credit-for-startup-without-revenue/` for the Lendio-research opportunity around `business line of credit for startup without revenue`, `business loan with no revenue`, `startup line of credit`, and related terms.
- Updated `/tools/business-line-of-credit-calculator/` to route users and crawlers to the new guide from the calculator research block and startup FAQ.
- Adjusted source wording after rendered checks showed the safe-copy layer rewrote `safer` and `personal guarantee` badly.

Verification:
- `npm run build` passed all postbuild contracts.
- Rendered checks passed for the new answer and calculator: title/canonical/schema present, no raw markdown, no bad safe-copy phrases.
- Live checks passed for both URLs with HTTP 200 and correct canonicals.
- `/srv/BusinessOps/.venv/bin/python3 /srv/BusinessOps/tools/creditdoc_feed_continuity_watchdog.py`: all OK; answer HTML count now 495.
- `/srv/BusinessOps/.venv/bin/python3 /srv/BusinessOps/tools/creditdoc_content_audit.py --preview --no-fix --stdout`: `0 issues found`.
- `/srv/BusinessOps/tools/verify_crons.sh`: all 59 expected crons present.
- `node scripts/creditdoc_linkedin_manager.mjs audit-social-duplicates`: no current social duplicate targets.

Operational note:
- No cron, feed, Pinterest, or LinkedIn automation was stopped or paused.
## 2026-07-07 - Saved next SEO traffic actions

Next work must be actioned from data, not guesses. Use GSC, SE Ranking, the Phase 1 KPI report, and `data/exports/longtail_picks_*.csv`.

Priority sequence:
1. Build/retarget exact-intent support pages for the business line-of-credit cluster:
   - `business lines of credit lenders`
   - `business lines of credit interest rates`
   - `business line of credit unsecured`
   - `business lines of credit for bad credit`
   - `business line of credit calculator` support/internal-link work.
2. Every support page should route to:
   - `/best/best-business-lines-of-credit/`
   - `/tools/business-line-of-credit-calculator/`
   - one related answer
   - one adjacent commercial page where relevant.
3. Manual GSC submissions should prioritize:
   - `/answers/credit-cards-for-bad-credit-guide/`
   - `/answers/business-line-of-credit-for-startup-without-revenue/`
   - `/tools/business-line-of-credit-calculator/`
   - `/tools/credit-score-simulator/`
   - highest-value money/tool URLs still not indexed or weakly discovered.
4. Weekly monitoring:
   - GSC impressions for new exact-intent pages.
   - selected keyword coverage in the KPI report.
   - `/best/` and `/tools/` impression growth.
   - SE Ranking exact-phrase movement.
5. Social:
   - distribute answer/tool/course/wellness pages through LinkedIn and Pinterest,
   - unique image per post,
   - narrative text plus direct page link,
   - no duplicate target URL inside the 90-day guard.

Next chunk:
- Implement `business lines of credit lenders` first.

## 2026-07-09 09:02 UTC - CreditDoc health, feeds, and SEO status check

Status:
- Deployed today's health fixes to Cloudflare Workers version `97accfb9-dee1-4dc9-9ae5-2f98c24a0c9e`.
- No cron, feed, Pinterest, LinkedIn, or content publishing automation was stopped or paused.

Fixes:
- Fixed two 2026-07-09 blog posts that were present in source but not yet live on production:
  - `/blog/can-authorized-user-see-credit-card-on-chase-app/`
  - `/blog/can-authorized-users-pay-credit-card-bill/`
- Fixed new blog SEO titles/descriptions for those two posts.
- Tightened `scripts/check_no_truncated_seo_fields.mjs` so title-like SEO fields fail if they contain an ellipsis anywhere, including cases like `|...`.

Verification:
- Live checks for both fixed blog URLs returned HTTP 200.
- `creditdoc_feed_continuity_watchdog.py`: OK.
  - `/rss.xml`: 50 items, newest `2026-07-09T00:00:00+00:00`.
  - `/feed.xml`: 50 items, newest `2026-07-08T00:00:00+00:00`.
  - Answers HTML: 495 pages passed title/meta/H1/canonical/content checks.
  - Financial wellness HTML: 139 pages passed.
  - Tools HTML: 19 pages passed.
  - Courses HTML: 10 pages passed.
- `creditdoc_content_audit.py --preview --no-fix --stdout`: `0 issues found`; 20 city guides and 4 blogs in the last 48h passed.
- `verify_crons.sh`: all 59 expected crons present.
- `creditdoc_linkedin_manager.mjs audit-social-duplicates`: no current LinkedIn or Pinterest duplicate targets. Historical July 2/3 Pinterest duplicate remains recorded, before the 2026-07-06 guard window.
- `npm run build`: passed all prebuild/postbuild contracts, including sitemap/robots, schema-sitemap contract, feed contract, image alt/filename contracts, AI ingestion, and Best-page title intent.

SEO read:
- Current traffic diagnosis report written to `reports/traffic_diagnosis_2026-07-09.md`.
- Latest 7-day GSC window, 2026-06-30 to 2026-07-06: 1 click vs 3 prior, 8,353 impressions vs 10,550 prior (-20.8%), avg position 51.33 vs 46.62.
- Latest 28-day GSC window, 2026-06-09 to 2026-07-06: 9 clicks vs 7 prior, 38,803 impressions vs 31,698 prior (+22.4%), avg position 41.04 vs 44.75.
- Diagnosis: technical health is green today; SEO weakness is still traffic quality/indexation maturity. Google visibility is dominated by review/entity pages. Tools/courses/answers/blog/wellness are live/static and technically valid, but many newer pages are still unknown to Google or thinly visible.
- Latest GSC coverage audit available is `/srv/BusinessOps/data/creditdoc_gsc_audit/gsc_audit_2026-07-07.md`: tools 17/19 indexed, courses 9/10 indexed, best 25/27 indexed, answers 3/50 sampled indexed, financial wellness 22/60 sampled indexed, blog 4/35 sampled indexed.

Next SEO focus:
- Continue priority indexing and internal routing for tools, courses, answers, wellness, and money pages.
- Do not spend manual GSC quota on review pages unless there is a specific revenue reason.
- Use GSC watchlists for pages already visible in positions 4-20 and rewrite titles/meta only where query/page mismatch is proven.

## 2026-07-09 09:10 UTC - Regulatory layer SEO moat audit

Finding:
- CreditDoc has a real regulatory/data layer and it is likely a meaningful differentiator versus generic affiliate/comparison sites.
- It is present in source and rendered output, but should be pushed harder as an SEO/E-E-A-T moat.

Current implementation:
- `src/components/StateRegulatoryContext.astro` renders state-level consumer finance context: state regulator, consumer protection agency, credit/debt/loan/payday/title/money-services context, complaint resources, statute links, and cautious source/disclaimer copy.
- `src/components/RegulatoryRecord.astro` renders company-level federal data where matched: CFPB complaint stats, enforcement actions, FDIC branch count, and SBA lending records.
- `/review/[slug].astro` imports both components:
  - company regulator data via `getRegulatorDataRuntime(lender.slug, env)`;
  - state context via `getStateByCodeRuntimeFromDb(stateAbbr, env)`.
- Rendered build check on 2026-07-09:
  - 97 built review pages include `State Consumer Finance Context`.
  - 9 built review pages include `Consumer Complaint Record`.
- The standalone tool/resource page exists at `/tools/state-consumer-credit-regulator-directory/` with CollectionPage, FAQPage, and BreadcrumbList schema and links to all state lending-law pages.
- Local regulator data inventory in `data/regulator.db`:
  - `cfpb_company_stats`: 2,514 rows.
  - `cfpb_enforcement_actions`: 385 rows.
  - `regulator_entities`: 7,193 rows.
  - `sba_lender_national_year`: 5,704 rows.
  - `sba_lender_state_year`: 16,263 rows.
  - `hmda_lender_stats`: 2,506 rows.
  - `fdic_institutions`: 27,832 rows.

Strategic interpretation:
- We are using the regulatory layer, but not yet enough.
- It appears strongly on some review pages and exists as a directory/tool, but it should also support high-value money pages, tools, answers, wellness/course material, and comparison pages more explicitly.
- This should be framed as consumer research context, not a claim that providers are licensed, safe, approved, best, cheapest, or compliant.

Next recommended SEO actions:
1. Add a visible `Regulatory research` trust module to major money pages and tools, linking to `/tools/state-consumer-credit-regulator-directory/`, `/state/`, and `/research/consumer-complaints/`.
2. Add schema-supported sameAs/mentions/about links where pages discuss CFPB, state lending laws, complaint routing, licensing checks, or regulator context.
3. Expand review-page state context coverage beyond the current 97 rendered review pages where the lender has resolvable state data.
4. Build exact-intent answer pages around regulatory queries such as `how to check if a lender is licensed`, `where to complain about a lender`, `state payday loan laws`, `credit repair laws by state`, and `CFPB complaint meaning`.
5. Use this layer in social distribution: pins/posts should occasionally lead with "check the regulator before you apply" and link to the directory/tool/state pages.

## 2026-07-09 09:18 UTC - Plan to use CreditDoc regulatory layer

Objective:
- Turn CreditDoc's regulatory/state-law/complaint-data layer into a visible trust and SEO differentiator across commercial, educational, and social surfaces.
- Do this without making unsafe licensing, legal, compliance, approval, or suitability claims.

Phase 1 - Make the moat visible on money pages and tools:
- Add a reusable `RegulatoryResearchModule` or equivalent page section.
- Install it on the highest-value `/best/` pages first:
  - `/best/best-business-lines-of-credit/`
  - `/best/best-sba-loans/`
  - `/best/best-small-business-loans/`
  - `/best/best-personal-loan-lenders/`
  - `/best/best-personal-loans-bad-credit/`
  - `/best/best-credit-repair-companies/`
  - `/best/best-debt-relief-companies/`
  - `/best/best-secured-credit-cards/`
- Install a compact version on high-value tools:
  - `/tools/business-line-of-credit-calculator/`
  - `/tools/sba-loan-calculator/`
  - `/tools/business-loan-calculator/`
  - `/tools/commercial-loan-calculator/`
  - `/tools/credit-score-simulator/`
  - `/tools/debt-payoff-calculator/`
- Links should route to:
  - `/tools/state-consumer-credit-regulator-directory/`
  - `/state/`
  - relevant `/state/[slug]/lending-laws/` where state context is known
  - `/research/consumer-complaints/`
  - `/about/creditdoc-data/`

Phase 2 - Create regulatory-intent answer cluster:
- Build or improve answer pages targeting:
  - `how to check if a lender is licensed`
  - `where to complain about a lender`
  - `how to file a CFPB complaint`
  - `what does a CFPB complaint mean`
  - `credit repair laws by state`
  - `payday loan laws by state`
  - `business loan licensing requirements`
  - `how to check a debt relief company`
  - `how to check a credit repair company`
- Every page must link back to:
  - regulator directory
  - relevant money/tool page
  - one state-law page
  - one research/data page

Phase 3 - Strengthen structured data and AI ingestion:
- Add schema `about` / `mentions` references where appropriate for:
  - CFPB
  - FTC
  - state regulators
  - consumer complaint routing
  - lending laws
  - credit repair law
- Make sure `/llms.txt` and AI ingestion surfaces include:
  - regulator directory
  - state law hub
  - CFPB complaint research
  - top regulatory answer pages
  - methodology and CreditDoc data pages.
- Avoid adding legal-service schema or implying legal advice.

Phase 4 - Expand review-page coverage safely:
- Audit why only 97 rendered review pages currently show `State Consumer Finance Context`.
- Increase coverage where lender records have reliable state data.
- Keep copy conservative:
  - state-level context only;
  - no claim that the provider/location is licensed unless direct proof exists;
  - no claim that regulator data proves safety, quality, approval odds, or suitability.

Phase 5 - Use it in social and outreach:
- LinkedIn/Pinterest content should periodically highlight:
  - "Check the regulator before applying"
  - "Where to file a complaint"
  - "How to compare lenders beyond advertised rates"
  - "What CFPB complaint data can and cannot tell you"
- Social posts must use unique images, direct page links, and no repeated target URL within the 90-day guard.
- Use the regulatory layer as a backlink/outreach hook for journalists, consumer advocates, financial educators, and local resources.

Measurement:
- Track GSC impressions/clicks for regulatory pages and queries.
- Track internal clicks from money/tools pages into regulator resources.
- Track indexation of regulatory answer cluster.
- Track whether `/best/` and `/tools/` pages with the module improve impressions or CTR over 14/28-day windows.

Refresh cadence:
- Regulatory/state-law/complaint-resource data must have a scheduled refresh at least every 6 months.
- Add a monthly lightweight drift check for broken regulator/statute/complaint-resource links.
- Six-month refresh should check:
  - state regulator names and URLs;
  - attorney general / consumer protection complaint links;
  - lending-law/statute references;
  - CFPB/FTC complaint-routing links;
  - outdated rate-cap or fee-context wording;
  - schema/dateModified updates on refreshed pages.
- Any page using regulatory copy should keep cautious language: educational context only, verify with official regulator, no legal advice, no licensing claim unless directly proven.

Implementation order:
1. Build reusable regulatory module and add it to priority money/tool pages.
2. Regenerate/build/deploy and run schema/sitemap/feed/content audits.
3. Create first 5 regulatory answer pages from exact-intent list.
4. Add regulatory pages to priority indexing queue.
5. Add cron/reminder for monthly link drift checks and six-month full regulatory refresh.
6. Update LinkedIn/Pinterest rotation with regulatory content slots.

## 2026-07-09 09:28 UTC - Regulatory SEO scheduler and first deployment pass

Implemented now:
- Added reusable regulatory SEO module: `src/components/RegulatoryResearchModule.astro`.
- Installed the module on all `/best/` money pages via `src/pages/best/[slug].astro`.
- Added Article schema `about` / `mentions` references for consumer finance comparison, state lending laws, complaint data, CFPB, FTC, and the CreditDoc regulator directory.
- Installed compact regulatory module on priority tools:
  - `/tools/business-line-of-credit-calculator/`
  - `/tools/sba-loan-calculator/`
  - `/tools/business-loan-calculator/`
  - `/tools/commercial-loan-calculator/`
  - `/tools/credit-score-simulator/`
  - `/tools/debt-payoff-calculator/`
- Added regulatory AI-ingestion entries to `public/llms.txt`:
  - `/tools/state-consumer-credit-regulator-directory/`
  - `/state/`
  - `/about/creditdoc-data/`
- Patched the shared VPS `llms_txt_regenerator.py` so future automated llms regeneration preserves CreditDoc's curated AI-ingestion file instead of replacing it with a broad unsafe URL dump.
- Added execution plan doc: `docs/plans/2026-07-09-regulatory-layer-execution-schedule.md`.
- Added regulatory automation scripts:
  - `tools/creditdoc_regulatory_refresh_check.py`
  - `tools/creditdoc_regulatory_seo_execution_check.py`
  - `tools/creditdoc_regulatory_next_phase_scheduler.py`
- Fixed stale official regulator/consumer-resource links in `src/content/states.json` discovered during the link drift sample.
- Ran the next-phase scheduler once immediately; it queued 18 priority regulatory/money/tool URLs into the existing forced Google indexing queue for the next priority indexing run.

Crons added and verified:
- Monthly link drift: `creditdoc-regulatory-link-drift`, runs at 09:35 UTC on the 2nd of every month.
- Six-month full refresh checklist: `creditdoc-regulatory-full-refresh`, runs at 09:45 UTC on Jan 2 and Jul 2.
- Weekly regulatory SEO execution check: `creditdoc-regulatory-seo-execution`, runs Mondays at 10:20 UTC.
- Daily next-phase scheduler while founder is traveling: `creditdoc-regulatory-next-phase`, runs daily at 11:10 UTC.
- `/srv/BusinessOps/tools/verify_crons.sh` passed after adding these; all 59 expected crons present.

Verification:
- `npm run build` passed.
- Postbuild contracts passed:
  - sitemap/robots conflict check OK
  - critical sitemap URLs OK
  - schema-sitemap contract OK, sitemap URLs=25,716, HTML pages=2,898, warnings=0
  - best SERP title intent OK
  - feed contract OK
  - image alt contract OK
  - image filename contract OK
  - AI ingestion OK: robots advertises `llms.txt`; 17 high-value URLs and 154 built artifacts covered.
- Content audit: 0 issues; required public surfaces OK; 20 city guides and 4 blogs created in last 48h.
- Feed watchdog: RSS/feed OK; answers 495 HTML pages OK; wellness 139 HTML pages OK; tools 19 HTML pages OK; courses 10 HTML pages OK; publishing crons active.
- Regulatory execution check: PASS.
- Regulatory link drift sample: checked 25 URLs, failed=0, warnings=2. Warnings were official sites blocking bot-style checks, not confirmed broken public pages.
- Social duplicate audit: active guard OK; no current LinkedIn/Pinterest duplicate targets. Historical Pinterest duplicate for commercial loan calculator from July 2/3 remains recorded; guard effective date is July 6 with 90-day repeat block.

Deployment:
- Deployed to Cloudflare Workers.
- Current deployed Worker version: `76c9e1fe-8f27-430c-982e-a6f46da66c66`.
- Live checks passed after edge cache settled:
  - `/best/best-business-lines-of-credit/` contains the regulatory research module and schema references.
  - `/tools/business-line-of-credit-calculator/` contains `Check The Regulatory Context`.
  - `/llms.txt` contains the regulatory directory, state-law hub, and CreditDoc data methodology entries.
  - `/rss.xml` and `/feed.xml` return HTTP 200.

Remaining scheduled next phases:
- Create/improve first regulatory-intent answer pages from the saved exact-intent list.
- Add these regulatory URLs to the priority indexing queue after publication.
- Expand safe review-page state context coverage where lender/location data is reliable.
- Add regulatory-content slots to LinkedIn/Pinterest rotation, using unique images and no repeated URL inside the 90-day guard.
- Watch GSC 14/28-day impact for money/tool pages with the module and for regulatory query impressions.

## 2026-07-09 15:05 UTC - Manual GSC and social rollout schedule for regulatory URLs

Manual GSC URL Inspection emails:
- Patched `/srv/BusinessOps/tools/creditdoc_daily_gsc_queue.py` so it can read a dated founder manual-submit schedule before the general priority queue.
- Added `/srv/BusinessOps/data/creditdoc_manual_gsc_submit_schedule.json`.
- Added `--date YYYY-MM-DD` dry-run support to verify future daily email contents without waiting for cron.
- The normal daily cron remains unchanged: 06:15 UTC via `creditdoc_daily_gsc_queue.py --apply`.

Scheduled manual-submit batches:
- 2026-07-10 email will contain these 10 URLs:
  - `/tools/state-consumer-credit-regulator-directory/`
  - `/state/`
  - `/about/creditdoc-data/`
  - `/research/consumer-complaints/`
  - `/best/best-business-lines-of-credit/`
  - `/best/best-sba-loans/`
  - `/best/best-small-business-loans/`
  - `/best/best-personal-loan-lenders/`
  - `/best/best-personal-loans-bad-credit/`
  - `/best/best-credit-repair-companies/`
- 2026-07-11 email will contain these 8 scheduled URLs, then fill the final 2 slots from the normal high-priority queue:
  - `/best/best-debt-relief-companies/`
  - `/best/best-secured-credit-cards/`
  - `/tools/business-line-of-credit-calculator/`
  - `/tools/sba-loan-calculator/`
  - `/tools/business-loan-calculator/`
  - `/tools/commercial-loan-calculator/`
  - `/tools/credit-score-simulator/`
  - `/tools/debt-payoff-calculator/`
- Verified dry runs for 2026-07-10 and 2026-07-11. The schedule now prevents July 11 filler rows from repeating URLs already scheduled for July 10.

Social rollout:
- Added regulatory campaigns to `scripts/creditdoc_linkedin_manager.mjs`, placed after the first three existing campaigns so Pinterest's `next_campaign_index=3` starts the regulatory sequence next.
- Added LinkedIn drafts to `/srv/BusinessOps/data/creditdoc_linkedin_queue.json`:
  - 2026-07-14: State consumer credit regulator directory
  - 2026-07-17: Business line of credit comparison with regulatory context
  - 2026-07-21: State lending law hub
  - 2026-07-24: CreditDoc data methodology
- Existing 2026-07-10 LinkedIn draft for MCA repayment calculator remains first and should publish before the regulatory sequence.
- Pinterest preview for 2026-07-09 through 2026-07-24 shows:
  - 2026-07-11: State consumer credit regulator directory
  - 2026-07-14: State lending law hub
  - 2026-07-17: CreditDoc data methodology
  - 2026-07-20: Business line of credit comparison with regulatory context
  - 2026-07-23: Accounts receivable financing calculator
- Social duplicate audit remains OK for active duplicate targets; historical July 2/3 commercial-loan duplicate remains recorded only as historical.
## 2026-07-10 - Regulatory answer pages deployed and GSC manual queue corrected

- Added and deployed five static HTML regulatory answer pages:
  - `/answers/how-to-check-if-a-lender-is-licensed/`
  - `/answers/where-to-complain-about-a-lender/`
  - `/answers/how-to-file-a-cfpb-complaint/`
  - `/answers/what-does-a-cfpb-complaint-mean/`
  - `/answers/how-to-check-a-credit-repair-company/`
- Live verification after Cloudflare deploy/cache purge:
  - all five canonical URLs return HTTP 200 with the intended titles.
  - GSC URL Inspection reports all five as `NEUTRAL / URL is unknown to Google`, not 404.
- The earlier manual GSC queue was wrong because it mixed strategic priority pages with verified-unindexed pages. Confirmed indexed and excluded from future manual GSC emails:
  - `/state/`
  - `/best/best-business-lines-of-credit/`
  - `/best/best-sba-loans/`
  - `/best/best-small-business-loans/`
  - `/best/best-personal-loan-lenders/`
  - `/best/best-personal-loans-bad-credit/`
  - `/best/best-credit-repair-companies/`
  - `/financial-wellness/credit-repair-rights-fcra-croa/`
  - `/financial-wellness/debt-validation-letters/`
- Patched `/srv/BusinessOps/tools/creditdoc_daily_gsc_queue.py` so dated manual schedule rows must pass the same eligibility check as forced rows and cannot include confirmed-indexed exclusions.
- Fixed daily queue suppression so old scheduled URLs do not hide future forced/scheduled URLs.
- Updated `/srv/BusinessOps/data/creditdoc_manual_gsc_submit_schedule.json` for `2026-07-11` with verified-live, non-indexed URLs:
  - the five new regulatory answer pages;
  - `/about/creditdoc-data/`;
  - `/research/consumer-complaints/`;
  - `/financial-wellness/predatory-lending-signs/`;
  - `/financial-wellness/understanding-loan-terms/`;
  - `/financial-wellness/vantagescore-vs-fico/`.
- Feed/static verifier passed after deploy:
  - `/rss.xml` and `/feed.xml` OK, newest `2026-07-10T00:00:00+00:00`;
  - 501 generated `/answers/` HTML pages passed title/meta/H1/canonical/content checks;
  - wellness/tools/courses static HTML checks OK;
  - publishing crons active.
- Founder submitted the seven verified URLs above on `2026-07-10`. Stamped them in `indexation_status` with `last_manual_request_indexing_submitted`.
- Permanent guardrail added to `/srv/BusinessOps/tools/creditdoc_daily_gsc_queue.py`: every row is live-fetched before email output; URLs are skipped if the canonical page does not return HTTP 200 or looks like 404 content.
- Forced-queue guardrail added: URLs manually submitted in the last 7 days do not resurface from the force queue.
- Removed the submitted seven from `/srv/BusinessOps/data/creditdoc_force_google_indexing_urls.json`.
- Updated `2026-07-11` manual schedule to avoid the seven already submitted today.
- Verified tomorrow filler URLs through live GSC:
  - `/financial-wellness/what-happens-miss-payment/`: `NEUTRAL / Crawled - currently not indexed`
  - `/answers/are-collections-on-credit-report/`: `NEUTRAL / URL is unknown to Google`
  - `/answers/are-credit-card-balance-transfers-bad/`: `NEUTRAL / URL is unknown to Google`
  - `/answers/are-credit-card-balance-transfers-worth-it/`: `NEUTRAL / URL is unknown to Google`

## 2026-07-10 - Regulatory moat static vs SSR audit

- Audited public regulatory/moat routes against `dist/` static HTML output and `src/pages` prerender settings.
- Static regulatory/moat assets:
  - 477 answer JSON pages with regulatory/compliance/consumer-rights terms, all present as static `/answers/.../index.html`.
  - 50 `/state/<state>/lending-laws/` pages, all static HTML.
  - `/tools/state-consumer-credit-regulator-directory/` static HTML.
  - `/about/creditdoc-data/`, `/methodology/`, `/editorial-policy/`, `/disclaimer/`, `/disclosure/`, `/privacy/`, `/terms/`, `/research/`, `/research/most-responsive-consumer-finance-providers-2026/`, and `/research/state-of-subprime-lending-2026/` static HTML.
  - Relevant resources and credit/fraud/debt-letter pages under `/resources/` are static HTML.
- Important regulatory/moat routes still using `export const prerender = false` and therefore not emitted as static HTML:
  - `/research/consumer-complaints/`
  - `/research/lending-transparency/`
  - `/state/<state>/` root pages
- Note: `/state/<state>/lending-laws/` is static; the non-static part is the state root route only.
- Recommended follow-up: convert the two research pages first, then decide whether `/state/<state>/` roots should be statically generated from build-time data or left SSR because they hydrate broader lender/state runtime data.

## 2026-07-11 - Sendy contacts/autoresponders protected before SES cutover

- Created a verified Sendy database backup before any Amazon SES SMTP cutover:
  - `/srv/BusinessOps/backups/sendy/2026-07-11T14-12-34Z`
  - `sendy_full.sql`, `sendy_inventory.tsv`, and `SHA256SUMS`
  - `sha256sum -c` passed.
- Current Sendy inventory at backup time:
  - CreditDoc / `Credit Repair Quiz Leads`: 1 total, 1 active.
  - CreditDoc / `Credit Fundamentals Course`: 1 total, 1 active.
  - DentaFund / `DentaFund National Nurture`: 0 total, 0 active.
  - DentaFund / `DentaFund Calculator Results`: 1 total, 1 active.
  - `Credit Fundamentals Module Summaries`: 8 autoresponder emails.
  - `Calculator results follow-up`: 3 autoresponder emails.
- Added `tools/sendy_backup.py` to back up the full Sendy MySQL DB plus an inventory report with list counts, autoresponder counts, and app SMTP state.
- Installed daily Sendy backup cron at 06:35 UTC:
  - `35 6 * * * cd /srv/BusinessOps/creditdoc && /usr/bin/python3 tools/sendy_backup.py >> /srv/BusinessOps/logs/sendy_backup.log 2>&1 # sendy-daily-backup`
- Preserved existing Sendy sending cron:
  - `*/5 * * * * php7.4 /srv/sendy/scheduled.php > /dev/null 2>&1`
- Backed up root crontab before installing the new line:
  - `/srv/BusinessOps/backups/cron_manual/root_crontab_before_sendy_backup_20260711T141251Z.txt`
- Rule going forward: before changing Sendy SMTP/SES settings, run `python3 tools/sendy_backup.py`; after any SMTP switch, test a real signup, confirm the subscriber row, confirm the expected email/autoresponder fires, and inspect SPF/DKIM/DMARC alignment.
- Full report: `reports/email/sendy_contact_backup_guardrail_2026-07-11.md`.

## 2026-07-11 - Truthful sitemap lastmod dates

- Implemented sitemap `<lastmod>` enrichment in `astro.config.mjs`; it only writes a date when a real source date exists, not blanket "today" freshness.
- Date sources now include SQLite `updated_at`/published fields for reviews, categories, blogs, financial wellness, answers, listicles, and comparisons; JSON dates for answer/course/listicle content; Supabase `city_guides.updated_at`; state/content file mtimes; tool page mtimes; and static page mtimes.
- Homepage plus `/blog/`, `/answers/`, `/financial-wellness/`, and `/review/` inherit the newest relevant child content date, so publishing new content updates the section freshness shown in the sitemap.
- Corrected the city-guide lastmod fetch to use the actual Supabase city guide schema (`slug,updated_at`), restoring lastmod on `/credit-guide/` URLs.
- Final build passed all prebuild/postbuild contracts:
  - content integrity, truncated SEO fields, robots, AI-ingestion, SSR sitemap parity;
  - sitemap/robots conflicts, critical sitemap URLs, schema/sitemap contract, Best-title contract, feed contract, image alt and filename contracts.
- Final generated sitemap evidence:
  - `19078` sitemap URLs total;
  - `17555` URLs with `<lastmod>`;
  - `1523` URLs without `<lastmod>` because no reliable source date was available.
- Spot checks with `<lastmod>` present:
  - `/` -> `2026-07-11`;
  - `/blog/` -> `2026-07-11`;
  - `/answers/` -> `2026-07-10`;
  - `/financial-wellness/` -> `2026-07-08`;
  - `/review/` -> `2026-07-08`;
  - `/tools/sba-loan-calculator/` -> `2026-07-09`;
  - `/credit-guide/spokane-wa/` -> `2026-05-23`.
- RSS/feed generation was not changed and feed contract passed. No manual Google indexing requests were consumed by this work.

## 2026-07-12 - Manual GSC quota used mostly by DentaFund

- Founder used the available Google manual Request Indexing quota mostly on DentaFund, so CreditDoc should not treat the full 2026-07-12 queue as submitted.
- CreditDoc URL actually submitted manually on 2026-07-12:
  - `/tools/mca-repayment-calculator/`
- Corrected CreditDoc tracking in `data/creditdoc.db`:
  - removed the false 06:15 UTC manual-submission stamps for the other nine CreditDoc queue URLs;
  - stamped only `/tools/mca-repayment-calculator/` with `last_manual_request_indexing_submitted=2026-07-12 14:49:15`;
  - its `manual_request_indexing_count` is now `4`.
- Backed up the DB before the correction:
  - `/srv/BusinessOps/creditdoc/data/creditdoc.db.before_manual_gsc_rollback_20260712T144802Z`
  - `/srv/BusinessOps/creditdoc/data/creditdoc.db.before_mca_manual_stamp_20260712T144914Z`
- Updated `/srv/BusinessOps/data/creditdoc_manual_gsc_submit_schedule.json`:
  - removed `/tools/mca-repayment-calculator/` from the 2026-07-13 batch;
  - kept the remaining nine deferred CreditDoc URLs for 2026-07-13;
  - preserved the strategic 2026-07-12 batch by copying it to 2026-07-14.
- Verification:
  - `stamped_today=1` in `indexation_status`;
  - 2026-07-13 dry-run queue contains the nine deferred scheduled URLs plus one filler answer page;
  - `/tools/mca-repayment-calculator/` does not reappear in the 2026-07-13 queue.

## 2026-07-13 - Exported lender meta descriptions fixed

- Resolved dirty SEO export files after a database export reintroduced terminal ellipses into 336 `src/content/lenders/*.json` `meta_description` fields.
- Patched `tools/creditdoc_db.py` so `sanitize_export_seo_titles()` now also sanitizes description-like SEO fields, including `meta_description`, `seo_description`, `description`, `summary`, and `excerpt`.
- For exported `meta_description` values ending in `...`/`…`, the sanitizer now rebuilds from full source copy where available (`description_short`, `answer_summary`, `summary`, `excerpt`, `description_long`) and trims cleanly without an ellipsis.
- Cleaned the current 336 lender JSON files so no title or description SEO field contains an ellipsis.
- Captured and kept 2026-07-13 operational reports:
  - Bing IndexNow watchdog: key file OK, Bing crawl data present, traffic still 0 impressions/clicks in the 30d Bing snapshot.
  - Bing recovery direct submission: 100 selected URLs submitted, 300 skipped.
  - Sitemap resubmission: Bing sitemap submissions succeeded; Google sitemap read-only check showed no sitemap errors/warnings.
  - Regulatory SEO execution: PASS, including reusable regulatory module, priority tool coverage, answer cluster, and regulatory cron markers.
- Verification passed:
  - `node scripts/check_no_truncated_seo_fields.mjs`
  - `python3 -m py_compile tools/creditdoc_db.py tools/creditdoc_build.py`
  - `npm run build`
  - postbuild contracts: sitemap/robots, critical URLs, schema/sitemap, Best-title intent, feeds, image alt, image filenames, and AI ingestion.

## 2026-07-14 - City guide publishing slowed to one every two days

- Founder requested slowing CreditDoc city guide generation to give the city landing-page/capture project time to catch up.
- Updated root crontab from daily `creditdoc_city_guide_generator.py --batch 10` to one guide every two UTC days:
  - active line uses `/usr/bin/python3 -c 'import datetime,sys; sys.exit(datetime.date.today().toordinal() & 1)' && ... creditdoc_city_guide_generator.py --batch 1`;
  - July 14, 2026 skips; July 15, 2026 runs; then alternates every other UTC day.
- Backups created before crontab edits:
  - `/srv/BusinessOps/backups/cron_manual/root_crontab_before_creditdoc_city_guides_cadence_20260714T085005Z.txt`
  - `/srv/BusinessOps/backups/cron_manual/root_crontab_before_creditdoc_city_guides_cadence_fix_20260714T085017Z.txt`
- Updated `/srv/BusinessOps/tools/creditdoc_feed_continuity_watchdog.py` so the required active cron check expects `creditdoc_city_guide_generator.py --batch 1`, not `--batch 10`.
- Updated `/srv/BusinessOps/tools/creditdoc_content_engine_daily_verify.py` so the city guide job is skipped cleanly on off-days instead of generating false failure emails.
- Verification:
  - July 14 guard exits `1` (skip); July 15 guard exits `0` (run).
  - `python3 -m py_compile` passed for city guide generator, feed watchdog, and content verifier.
  - `creditdoc_content_engine_daily_verify.py --dry-run --allow-pending` passed and reported `city guides: skipped on alternating-day cadence`.
  - Feed watchdog cron requirement check passed with `cron: city guides active`.
- This does not pause city guides; it reduces velocity to one new guide every two days while keeping the pipeline monitored.

## 2026-07-14 - Truncated SEO field guard cleaned again

- After the cadence work, `node scripts/check_no_truncated_seo_fields.mjs` found SEO ellipses again.
- Cleaned committed source issues:
  - `src/content/blog-posts.json`: fixed two chopped blog title fields from the July 14 blog output.
  - `src/content/lenders/server-unavailable-possibly-it-is-restarting-please-try-later.json`: replaced literal `...` punctuation in the profile name/match/meta description with normal sentence punctuation.
- Patched active generator scripts outside the CreditDoc repo so new generated metadata trims cleanly without appending `...`:
  - `/srv/BusinessOps/tools/creditdoc_blog.py`
  - `/srv/BusinessOps/tools/creditdoc_cluster_executor.py`
  - `/srv/BusinessOps/tools/creditdoc_answer_dedication_loop.py`
- Verification:
  - `node scripts/check_no_truncated_seo_fields.mjs` passed.
  - `python3 -m py_compile` passed for the patched active generator scripts and the cadence verifier/watchdog scripts.
- Note: `/srv/BusinessOps/tools/*` is outside the CreditDoc git repo, so those active-script changes are saved on the VPS and documented here, but only repo files can be committed to `giancapannesi/creditdoc`.

## 2026-07-14 - Guardian SEO regression path fixed

- Root cause found for recurring truncated lender meta descriptions: the hourly `creditdoc_guardian.py` job was restoring 336 protected profiles from stale DB data after clean builds.
- Guardian was not paused. The code path was fixed so DB reads and Guardian writes sanitize SEO title/description fields before exporting JSON.
- Added the truncation guard to `npm run postbuild` so future builds fail if any title or description SEO field contains an ellipsis.
- Re-ran Guardian in protected-only mode after the fix; it rewrote the affected lender JSON files through the sanitized path.
- Verification:
  - `node scripts/check_no_truncated_seo_fields.mjs` passes.
- Next crawler-risk target:
  - convert `/review/[slug]/` away from runtime Astro, because Bing's 5XX report is dominated by review URLs and this is the largest remaining public SEO route family still served dynamically.

## 2026-07-14 - Crawler export failures hardened to zero

- Implemented non-destructive cleanup for the GSC/Bing exported 404/duplicate crawler rows:
  - valid pages remain live/static;
  - stale exported URLs are removed from XML sitemaps;
  - stale review redirects now point at real static category hubs instead of missing `/credit-guide/...` category URLs;
  - category pages are prerendered static HTML from the canonical category list.
- Added `scripts/check_crawler_error_exports.mjs` and wired it into `npm run postbuild`.
  - It parses `SEO/Table 404 Missing Pages.csv` and `SEO/Table - Duplicates.csv`.
  - It fails if any exported row is neither static nor redirected.
  - It fails if any exported problem URL leaks into `dist/sitemap*.xml`.
  - It fails if any local redirect target points at a missing static page.
- Fixed sitemap exclusion normalization so apex and `www` versions from crawler exports normalize to the canonical `https://www.creditdoc.co/...` host before comparison.
- Added category URL canonicalization helpers so stale aliases such as `payday-loans`, `debt-consolidation`, and `fix-my-credit` resolve to the live static hubs.
- Fixed two duplicate-export rows that were valid pages but had stale noindex/publishing metadata:
  - `vigo-new-york`
  - `winscott-credit-repair`
- Full rebuild completed successfully on 2026-07-14.
- Debugger/postbuild verification passed:
  - `node scripts/check_crawler_error_exports.mjs`
    - `1071` exported URL rows checked;
    - `77` static;
    - `994` redirected;
    - `sitemap leaks=0`;
    - `bad redirect targets=0`.
  - `npm run postbuild`
    - no truncated SEO fields;
    - required static HTML contract OK;
    - crawler export guard OK;
    - sitemap/robots OK;
    - critical sitemap URLs OK;
    - schema/sitemap contract OK (`sitemap URLs=19454`, `HTML pages=19092`, `warnings=0`);
    - Best title intent OK;
    - feeds OK;
    - image alt/filename checks OK;
    - AI ingestion OK;
    - internal static links OK (`1042675` links checked).
- Google validation guidance:
  - The crawler-export guard is now green, so it is reasonable to request validation for the duplicate-canonical and 404 fix groups.
  - Do not bulk noindex or remove valid city/review pages; this fix keeps valid pages live and stops stale/bad URLs from being advertised.
