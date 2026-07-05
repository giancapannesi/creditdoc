# CreditDoc — NEXT ACTIONS (updated 2026-07-03)

## 2026-07-05 - Next: remove remaining crawler dependence on dynamic Astro SSR

Follow-up from the SE Ranking 5XX audit:
- Treat `/review/`, `/categories/`, `/state/[slug]/`, `/brand/`, and `/credit-guide/[slug]/...` as the remaining dynamic SEO risk because they are sitemap-listed SSR routes.
- Prioritize staticizing or snapshotting the highest-value money/category/local pages first, rather than changing already-static tools, answers, blogs, wellness, courses, city, browse, comparison, trend, or resource pages.
- If full staticization is too large for one pass, add stale-cache fallback behavior for SSR routes so a version-probe or Supabase timeout can serve the last good cached HTML instead of forcing a fresh render.
- Expand the route self-healer beyond 10 sample URLs to include representative SE Ranking URLs from review/category/credit-guide route families, using a crawler-style user agent and enough concurrency to catch cold-cache/runtime failures.
- Keep the daily SE audit comparison focused on whether 5XX count drops from the July 5 baseline of 671 and sitemap 5XX/noindex drops from 27.

Execution plan now in progress:
1. Extract the exact URLs visible in `SEO/audit_creditdoc.co_2026-07-05_13-36-15.pdf` / `/tmp/creditdoc-se-ranking-audit.txt`.
2. Group the flagged URLs by route family and prioritize the externally flagged 5XX families first.
3. Start with the sitemap-listed 5XX examples from SE Ranking:
   - `/credit-guide/amarillo-tx/emergency-cash/`
   - `/credit-guide/austin-tx/emergency-cash/`
   - `/credit-guide/charlotte-nc/emergency-cash/`
   - `/categories/credit-unions/`
   - `/credit-guide/amarillo-tx/business-loans/`
   - `/credit-guide/austin-tx/business-loans/`
   - `/credit-guide/charlotte-nc/business-loans/`
   - `/credit-guide/amarillo-tx/debt-relief/`
   - `/credit-guide/austin-tx/debt-relief/`
   - `/credit-guide/amarillo-tx/mortgages/`
   - `/credit-guide/austin-tx/mortgages/`
   - `/credit-guide/charlotte-nc/mortgages/`
4. For review pages, begin with the review URLs listed in the SE 5XX examples, not every review page at once.
5. Prefer true Astro static generation from local content where feasible. If a whole family is too large/risky in one pass, create committed static snapshots for the SE-flagged URLs first, then follow with a broader route-family static migration.
6. After each phase: run `npm run build`, verify generated/static coverage for the target URLs, commit, push, deploy through `./deploy.sh`, and update memory.

## Active 2026-07-03 — SE Ranking Cleanup Verification

Latest completed:

- Local SE Ranking remediation pass completed for sitemap/noindex, short titles, duplicate titles, duplicate H1s, broken external favicon image fallbacks, and missing-anchor-text audit coverage.
- `scripts/seo_deep_audit.mjs` now checks rendered links for empty anchor text.
- `npm run build` passed with prebuild and postbuild contracts.
- `node scripts/seo_deep_audit.mjs` passed: 2,742 rendered HTML pages, 24,891 sitemap URLs, 0 errors, 0 warnings.
- Generated sitemap no longer includes `/linkedin-oauth-callback/`.
- Image alt and image filename contracts passed.

Immediate next:

1. Deploy the latest SEO cleanup commit if it is not already live.
2. After deploy, live-check representative URLs from `/tools/`, `/answers/`, `/best/`, `/blog/`, `/financial-wellness/`, `/courses/`, and `/review/`.
3. Confirm production headers no longer show old SSR route sources for staticized page families.
4. Use the next SE Ranking crawl as external confirmation; do not reopen fixed items unless the fresh crawl reproduces them on the current deployed build.
5. Continue strategic SEO work on internal link depth for important money/tool/course pages, since local technical crawl errors are now clean.

## Active 2026-07-02 — Static SEO Migration

Latest completed:

- Tools, answers/questions, blog detail pages, financial-wellness detail pages, and `/best/` money pages were converted or confirmed as static build output.
- Build evidence from `npm run build` on 2026-07-02:
  - `/answers/`: 492 generated `index.html` files including the answer index.
  - `/tools/`: 19 generated `index.html` files including the tools index.
  - `/blog/`: 104 generated `index.html` files including the blog index.
  - `/financial-wellness/`: 140 generated `index.html` files including the wellness index.
  - `/best/`: 27 generated `index.html` files.
- No `export const prerender = false` remains in `src/pages/blog`, `src/pages/financial-wellness`, `src/pages/best`, `src/pages/answers`, or `src/pages/tools`.
- `npm run build` passed with prebuild and postbuild checks, including sitemap/robots, critical URLs, feeds, rendered image alt tags, and image filename checks.
- Static migration tracker:
  `/srv/BusinessOps/creditdoc/SEO/STATIC_SEO_PAGE_MIGRATION_PLAN_2026-07-02.md`

Immediate next:

1. Commit the follow-up static editorial/money-page changes after final status review.
2. After deploy, verify production sitemap includes static URLs for `/tools/`, `/answers/`, `/blog/`, `/financial-wellness/`, and `/best/`.
3. Continue static work selectively only where evidence supports it: high-impression `/categories/`, `/credit-guide/`, and selected indexed/high-value `/review/` pages.
4. Do not bulk-staticize every route family blindly; check data freshness, sitemap size, and build-time impact first.
5. Keep `/search/`, `/api/*`, `/go/[slug]`, `/r/[slug]`, and OAuth/callback utility routes dynamic or non-indexable as appropriate.

## Active 2026-06-19 — Supabase Size Monitoring

Latest completed:

- CreditDoc Supabase database size incident resolved without paying for an upgrade.
- Database reduced from `513 MB` to `175 MB`.
- `public.audit_log` reduced from `370 MB` to `32 MB`.
- Full audit archive stored outside Supabase at:
  `/srv/BusinessOps/backups/creditdoc_supabase_audit_cleanup/20260619T114841Z/public_audit_log_before_prune.dump`
- Future audit rows now strip `body_inline` and retain compact marker fields so the same bloat should not recur from normal content updates.

Next checks:

1. Add this to the normal CreditDoc daily/weekly ops review: check `pg_database_size(current_database())` and `pg_total_relation_size('public.audit_log')`.
2. If `public.audit_log` grows unexpectedly, inspect row distribution by `table_name`, `operation`, and JSON payload size before pruning anything.
3. Keep audit archive files; do not delete the 2026-06-19 archive unless there is a separate retention decision.
4. If changing `public.fn_audit_row()` again, use the DB safety protocol and preserve the rollback function definition first.

## Active 2026-06-17 — Phase 1 Comparison Pricing Safety

Latest completed:

- Fourth guarded comparison batch completed 2026-06-20 and deployed.
- Batch 004 commit: `6bdd97a52b fix: clean guarded comparison batch 004`.
- Worker Version ID: `ee4df2a5-8169-48fe-a690-40b94fd57a13`.
- Batch 004 started from 20 next-risk candidates, but pre-edit claim safety found blockers on only two pages, so only `credit-supreme-credit-repair-miami-fix-credit-fast-miami-fl-vs-safeport-law` and `american-consumer-credit-counseling-vs-creditorg` were edited.
- The edit removed unsupported value/savings/recommendation language and unsafe accreditation framing while preserving pricing fields, review signals, service model, counseling scope, refund/program terms, and attorney/nonprofit context.
- Independent checker `Harvey` passed before commit.
- Verification passed: preflight 20-candidate manifest, edited claim safety, `npm run test:comparison-batch` 54/54, `git diff --check`, content text integrity, comparison DB freshness 345/345, guarded batch check 2 pages/0 blockers, deploy smoke, live comparison check 2/2 URLs 200 with 0 blockers, cumulative campaign report `ok: true`, and continue gate `ok: true`.
- Batch 004 workpack:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Comparison_Batch_004_2026-06-20/`
- Third guarded comparison batch completed 2026-06-20 and deployed.
- Batch 003 commit: `83ecf2238a fix: clean guarded comparison batch 003`.
- Worker Version ID: `012e4339-8052-4a6e-ba41-d77d368fb7df`.
- Batch 003 started from 20 high-risk unhandled candidates, but pre-edit claim safety found only one blocker, so only `capital-fundings-vs-refijet` was edited.
- The edit removed unsupported concrete rate/APR and exact amount claims from the changed fields while preserving use-case, fee-context, marketplace/refinance, review-signal, and investor-lending value.
- Independent checker `Averroes` passed before commit.
- Verification passed: preflight 20-candidate manifest, edited claim safety, `npm run test:comparison-batch` 54/54, `git diff --check`, content text integrity, comparison DB freshness 345/345, guarded batch check 1 page/0 blockers, deploy smoke, live comparison check 1/1 URL 200 with 0 blockers, cumulative campaign report `ok: true`, and continue gate `ok: true`.
- Batch 003 workpack:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Comparison_Batch_003_2026-06-20/`
- Second guarded difficult comparison batch completed 2026-06-20 and deployed.
- Batch 002 commit: `acc359f237 fix: clean guarded comparison batch 002`.
- Worker Version ID: `fef6e12d-6b01-4168-8d06-8144248f7be6`.
- Batch 002 updated only 12 high-risk records from a 20-candidate workpack, preserving comparison-page value while removing unsupported pricing, value, winner, and accreditation claims.
- National Credit Fixers source copy now says stored BBB A+ rating field, not BBB accreditation.
- Claim scanner now allows source-backed `$0` strings such as explicit `$0 down` pricing while still blocking fabricated free-pricing claims from default numeric zero.
- Independent checker `Dewey` passed before commit.
- Verification passed: `npm run test:comparison-batch` 54/54, `node --check`, `git diff --check`, content text integrity, comparison DB freshness 345/345, guarded batch check 12 pages/0 blockers, deploy smoke, live comparison check 12/12 URLs 200 with 0 blockers, campaign report `ok: true`, and continue gate `ok: true`.
- Batch 002 workpack:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Comparison_Batch_002_2026-06-20/`
- First reviewed 20-page comparison batch rendering/fact-safety work completed on 2026-06-19.
- Rendered fact alignment commit: `e0940e5526 fix: align comparison rendered facts`.
- Separate wellness cron content commit: `42ab02e0f3 content: add wellness guides`.
- The batch preserved comparison-page value sections and linked tools/blog/course/local/research sections.
- Fixed pricing contradictions for Brigit, Cosmo, Dovly, WalletHub, Experian, ACCC, InCharge, and other sampled pages where positive source pricing or paid tiers were being hidden by free/default tiers.
- Fixed stale TransUnion/Experian research text so it uses bureau/monitoring signals instead of credit-repair/counseling framing.
- Added `check:content-text-integrity` and wired it into `prebuild` to catch narrative JSON control-character/currency corruption.
- Repaired corrupted ACCC profile text through the DB writer/export path.
- Independent read-only reviewer `Dalton` passed after initially finding the Dovly/WalletHub and Experian paid-tier issue.
- Verification passed: `npm run test:comparison-batch` 50/50, `npm run check:content-text-integrity`, `git diff --check`, `node --check` for changed scripts, `npm run check:comparison-db-freshness` 345/345, and full `npm run build` with prebuild/postbuild checks.
- Scheduled comparison generator cron unexpectedly committed/pushed `85fa250de5 Add 5 comparison pages` during the batch. Do not rewrite history; continue from current branch state.
- Phase 0 reliability fixes were committed, deployed, and live-verified.
- Phase 1 workpack created at `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Comparison_Pricing_Safety_Phase_1_2026-06-17/`.
- First Phase 1 live-page patch slice updated 9 comparison records with stored-field comparison language and build verification.
- Single orphan comparison `kikoff-vs-a-better-way-auto-brokerage` was archived and removed from local DB, Supabase, and exported JSON.
- Phase 1 cleanup release deployed 2026-06-18, Cloudflare Worker Version ID `4f189f5a-1b95-4b74-acd4-c55866f8f9d4`.
- Second Phase 1 live-page patch slice updated 10 comparison records, including summaries, winner reasons, and SEO descriptions, with independent read-only review and build/live verification.
- Second slice deployed 2026-06-18, Cloudflare Worker Version ID `e3ebb3d1-1235-4b83-a47f-de94e35d0f86`.
- Third Phase 1 live-page patch slice updated 10 comparison records, including summaries, winner reasons, and SEO descriptions, with independent read-only review, build verification, deploy, and live verification.
- `CreditDocDB.add_comparison(...)` now uses row-preserving SQLite upsert instead of `INSERT OR REPLACE` to avoid comparison export reorder churn.
- Task 8 guardrail runner committed as `9861eb5159 feat: add guarded comparison batch runner`.
- Runner commands now available:
  - `npm run comparison:batch:preflight -- --manifest <manifest.json> --output-dir <reports-dir>`
  - `npm run comparison:batch:check -- --manifest <manifest.json> --output-dir <reports-dir>`
- Runner is report/check tooling only. It does not edit content or DB rows.
- Task 9/10 live verifier and campaign gate committed as `e2824fae5f feat: add comparison live and campaign gates`.
- Additional commands now available:
  - `npm run comparison:live-check -- --manifest <manifest.json> --output-dir <reports-dir>`
  - `npm run comparison:campaign:report -- --campaign <campaign.json> --batch-dir <batch-dir> --output-dir <campaign-report-dir>`
  - `npm run comparison:campaign:can-continue -- --campaign-report <campaign_report.json> --latest-batch-dir <batch-dir>`

Immediate next:

1. Campaign gate is open after batch 004, so the next comparison batch may start.
2. Pick the next difficult pages from the risk inventory and checker recommendations, but keep batches scoped to 10-25 pages and edit only records that fail claim safety or obviously need factual cleanup.
3. Batch 003 showed that high risk-score inventory rows can pass the current source-backed checks. Do not edit passing pages just to make a batch look larger.
4. Keep Phase 1 as small batches only; no bulk comparison rewrites.
5. Keep pricing/rating values only where they are current CreditDoc source fields, including paid tiers; do not let free/default tiers hide real paid pricing.
6. Keep copy framed as stored-field comparison rather than recommendation.
7. Patch `summary`, `winner_reason`, and `seo_description` together for each selected comparison because all three can render or influence snippets.
8. For every batch loop, require: preflight -> deterministic check -> independent content review -> final checker result file -> commit -> deploy when release scope is clear -> live check -> campaign report -> can-continue gate.
9. If the gate blocks, stop the loop and fix the specific blocker before selecting more pages.

## Active 2026-05-26 — Sitewide Page Upgrade Program

User direction: keep looping through priority page families until the pages are
upgraded, documented, build-verified, and committed. Do not deploy unless
requested.

Latest completed/active state:

- Batch 008 committed: `9c013cfa8f feat: add graph links to tools pages`.
- Batch 009 committed: `2d5c452abf feat: add graph links to resource pages`.
- Batch 009 scope: `/resources/`, `/resources/credit-report-checklist/`,
  `/resources/credit-report-checklist/print/`,
  `/resources/debt-credit-letter-templates/`, and individual letter-template
  pages through `src/components/LetterTemplatePage.astro`.
- Latest local GSC pull (`pull_id=12`) saw 0 `/resources/` URLs.
- Batch 009 verification passed: `npm run build`, robots contract, SSR sitemap
  parity, generated output scan, sitemap/robots check, and 18,411 SSR route URL
  injection.
- Batch 010 committed: `9cc4811945 feat: add graph links to wellness pages`.
- Batch 010 scope: `/financial-wellness/` and `/financial-wellness/{slug}/`.
- Local wellness guide inventory: 98 rows; latest local GSC pull (`pull_id=12`)
  saw 32 `/financial-wellness/` URLs.
- Batch 010 verification passed: `npm run build`, robots contract, SSR sitemap
  parity, generated output/server-bundle scan, sitemap/robots check, and 18,411
  SSR route URL injection.
- Batch 011 committed: `bc19ad1a9c feat: add graph links to blog pages`.
- Batch 011 scope: `/blog/` and `/blog/{slug}/`.
- Local blog inventory: 68 rows; latest local GSC pull (`pull_id=12`) saw 13
  `/blog/` URLs.
- Batch 011 verification passed: `npm run build`, robots contract, SSR sitemap
  parity, generated output/server-bundle scan, sitemap/robots check, and 18,411
  SSR route URL injection.
- Batch 012 committed: `c304df885c feat: add graph links to education pages`.
- Batch 012 scope: `/learn/`, `/glossary/`, `/courses/`,
  `/courses/credit-fundamentals/`, and every
  `/courses/credit-fundamentals/{slug}/` module page.
- Local education inventory: 71 glossary terms, 1 current course, 8 modules,
  and 40 lessons. Latest local GSC pull (`pull_id=12`) saw 0 `/learn/`,
  `/glossary/`, or `/courses/` URLs.
- Batch 012 verification passed: `npm run build`, robots contract, SSR sitemap
  parity, generated output scan, targeted route check, sitemap/robots check, and
  18,411 SSR route URL injection.

Immediate next:

1. Start Batch 013 by inspecting the static trust/support pages and upgrading
   the next suitable page family with graph links into local guides, categories,
   answers, tools, resources, research, and state context.
2. Keep every batch scoped, documented in the workpack, build-verified, and
   committed before starting the next batch.

## Strategic Direction — AI Council Session 6 (2026-05-16)

**Core insight:** "Not a content problem — a CTR and trust-signal problem."  
25,727 impressions / 27 clicks / 0.10% CTR. Pages rank but don't get clicked.

Full transcript: `CreditDoc Project Improvement/2026-05-16-AI-COUNCIL-SESSION-6.md`  
Previous sessions: `AI_COUNCIL_SESSION_[1-5]_2026-05-13.md`

---

## COMPLETED (2026-05-16)

1. AggregateRating JSON-LD — LIVE (real Google Reviews data only)
2. 766 CFPB Consumer Response Profile pages — LIVE at /trends/[slug]/
3. Comparison pages — already LIVE (185 at /compare/[slug]/)

## Immediate Next Actions (approved by founder)

### 0A. Review Page Growth Plan - Execute In Controlled Batches

Use the local Codex skill for this work:

- `/srv/BusinessOps/.agents/skills/creditdoc-seo-growth/SKILL.md`

Plan saved:

- `/srv/BusinessOps/creditdoc/docs/plans/2026-05-22-review-page-growth.md`
- Pointer: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Growth_Plan_2026-05-22.md`

Batch 1 saved:

- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Growth_Batch_1_2026-05-22.csv`
- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Growth_Batch_1_Notes_2026-05-22.md`

Completed locally, not deployed:

- `src/lib/db.ts`: added `getAnswersByPillarRuntime()`.
- `src/pages/review/[slug].astro`: added category-aware related `/answers/` links.
- `src/pages/review/[slug].astro`: fixed mini-quiz scoring against actual category slugs.
- `npm run build` passed.

Next steps:

1. Continue one-page upgrades using `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Template_2026-05-23.md`.
2. Use the Marco's Credit Services pilot as the pattern for protected FA pages: DB API founder override, do not unset protection, verify audit log and live page.
3. Manually review Batch 1 pages, especially raw/pending/quarantined rows, before any indexability or metadata changes.
4. Improve SEO titles/metas for selected `ready_for_index` pages through the DB update path only.
5. Re-run `npm run build` when template/code changes are included.
6. Deploy only from a reviewed release scope.
7. Measure against GSC pull `10` baseline after the next GSC pull and again after 21-28 days.

### 0. Preserve ATM City-Category Count Fix

- User flagged `/credit-guide/anaheim-ca/atm/`: page claimed only `1` ATM/cash-access provider in Anaheim, which is obviously misleading.
- Root cause: `src/pages/credit-guide/[slug]/[category].astro` uses the partial CreditDoc ATM profile dataset as if it were an exhaustive local ATM inventory. The one listed item was a San Diego CoinFlip ATM.
- Local patch made 2026-05-19: for `category === 'atm'`, remove exhaustive count/stat-card copy, clarify these are selected cash-access profiles and not a complete city ATM count, relabel statewide-only lists, and hide irrelevant borrowing quiz / credit Q&A blocks on ATM pages.
- Verification: `npm run build` passed.
- Follow-up: once the working tree cleanup is complete, preserve this patch and deploy it. Do not reintroduce “Compare 1” or city ATM total claims unless there is a verified complete city-level ATM inventory.

### 1. FAQ schema on city guides
- Source: FAQ content already in city_guides DB (generated by the guide pipeline)
- Format: JSON-LD FAQPage schema on `/credit-guide/[slug]/` pages
- Impact: FAQ dropdowns in SERP = more real estate

### 2. Enhance top-10 position city pages
- Charlotte (pos 2), Las Vegas (pos 5), Detroit (pos 3)
- Add: comparison tables, local resource links, more content depth
- Goal: push from "showing" to "clicked" — featured snippet territory

### 3. Mini-quiz on /review/ pages
- "Is this lender right for you?" — 3 contextual questions
- Personalized recommendation based on answers
- Turns info page → interactive tool (Jobs' insight)

---

## Ongoing Automated Pipelines (DO NOT PAUSE)

| Pipeline | Schedule | Status |
|----------|----------|--------|
| City guides | 04:00 UTC, 10/day | 31 live, target 250 by June 7 |
| Blog posts | 10:00 UTC daily | Self-feeding from CSV |
| Wellness guides | 11:00 UTC daily | Self-feeds from answer topics |
| Answer pages | 12:00 UTC daily | Running |
| Indexation | 08:00 UTC daily | Deduped, tier-priority |
| Content audit | 09:00 UTC daily | Autofix + email report |
| Site monitor | */5 min | 6 routes + Harvey alert |
| Course drip | Sendy autoresponder | 8 emails, day 0→21 |

---

## Blocked / Waiting on Traffic

- Affiliate monetization (CJ advertisers rejecting due to low traffic)
- Embedded finance activation (needs 25K visitors/month)
- Lender outreach / dashboard (too early to pitch)

---

## Planned Resource Cluster — Debt And Credit Letter Templates

Plan file: `/srv/BusinessOps/CreditDoc Project Improvement/2026-05-19_DEBT_CREDIT_LETTER_TEMPLATE_LIBRARY_PLAN.md`

Use only the approved `/resources/` page format, modeled on:

- `src/pages/resources/index.astro`
- `src/pages/resources/credit-report-checklist/index.astro`
- `src/pages/resources/credit-report-checklist/print/index.astro`

Do not create a new layout or copy competitor templates. This should become a
CreditDoc-owned public resource library with no affiliate links inside the
resource pages.

Initial target pages:

- `/resources/debt-credit-letter-templates/`
- `/resources/debt-credit-letter-templates/debt-validation-letter/`
- `/resources/debt-credit-letter-templates/cease-and-desist-debt-collector-letter/`
- `/resources/debt-credit-letter-templates/pay-for-delete-letter/`
- `/resources/debt-credit-letter-templates/debt-settlement-offer-letter/`
- `/resources/debt-credit-letter-templates/debt-settlement-agreement-checklist/`

Implemented locally 2026-05-19:

- Shared approved-format component: `src/components/LetterTemplatePage.astro`
- Hub + first 3 pages: debt validation, cease-and-desist collector contact,
  pay-for-delete.
- Hub linked from `src/pages/resources/index.astro`.
- `npm run build` passed.
- Deployed 2026-05-19.
- Cloudflare Worker Version ID: `415115ec-4150-471a-a256-f7cef10ba526`
- Live URLs verified `200`:
  - `https://www.creditdoc.co/resources/debt-credit-letter-templates/`
  - `https://www.creditdoc.co/resources/debt-credit-letter-templates/debt-validation-letter/`
  - `https://www.creditdoc.co/resources/debt-credit-letter-templates/cease-and-desist-debt-collector-letter/`
  - `https://www.creditdoc.co/resources/debt-credit-letter-templates/pay-for-delete-letter/`

Next implementation step after founder review:

- Add `/resources/debt-credit-letter-templates/debt-settlement-offer-letter/`
- Add `/resources/debt-credit-letter-templates/debt-settlement-agreement-checklist/`
- Re-run `npm run build`.
- Only then consider deploy and indexing.

Treat this as a reviewed YMYL-adjacent resource project, not a general blog or
wellness-generator batch.

---

## Deferred — YouTube AI Videos (revisit when CTR >0.3% + clicks >200/mo)

- 60-90s AI answer videos embedded ON /answers/ and /wellness/ pages
- VideoObject schema → video thumbnails in SERP
- Cross-post to YouTube as bonus distribution
- Council unanimously said defer (2026-05-16): 27 clicks/mo = no audience

## DO NOT

- Don't write anything negative about lenders (CFPB pages = positive framing ONLY)
- Don't add new page types until CTR improves
- Don't rewrite titles/metas on pages indexed <7 days
- Don't rebuild the inline linker (patch the TS)
- Don't pause any content pipeline without Jammi approval
- Don't conflate Vercel with CreditDoc (it's Cloudflare Workers)
- Don't propose author bio / personal E-E-A-T (SCRAPPED permanently)
- Don't use bare `wrangler deploy` — always use `./deploy.sh`
- Don't robots-block pages that already carry page-level `noindex`. If Google
  cannot crawl them, it cannot see the noindex directive and GSC reports
  "Blocked by robots.txt". Keep `/search/` out of XML sitemaps, but allow crawl
  so its `noindex,nofollow` and canonical can be processed.

## Noindex Cleanup Queue — Active

Current project folder:

- `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Noindex_Review_2026-05-26/`

Latest completed state:

- Batch 006 title/title-service wrong-vertical archive deployed and live-verified.
- Batch 007 auto/vehicle/car-dealer wrong-vertical archive deployed and live-verified.
- Batch 008 reinstated 5 verified credit union profiles from noindex and
  deployed/live-verified them.
- Latest production Worker version: `3968f894-d02b-4867-8fc9-6ffac519303b`.
- Latest commit: `4240a47847 data: reinstate verified credit union noindex batch`.
- `npm run build` passed with 18,405 SSR route URLs injected and sitemap/robots
  guards passing for Batch 007; Batch 008 passed with 18,410 SSR route URLs.
- Live checks passed: all 12 Batch 007 review URLs are `404`; `/trends/ascent/`
  is `404`; Batch 008 credit union URLs are `200`, canonical, not noindex, and
  present in live sitemaps; normal smoke pages are `200` without noindex.

Continue next:

1. Finish Batch 009 release once the concurrent Batch 001 normalization files
   are committed or cleared:
   - deploy via `./deploy.sh`;
   - live-check all 15 Batch 009 review URLs return `404`;
   - confirm live sitemaps do not reference those 15 review URLs;
   - commit any final documentation if the deploy adds a Worker version.
2. Keep resolving noindex records by quality gate: reinstate genuine finance
   profiles with real value; archive/drop rubbish, wrong-vertical, blank, or
   unsafe pages.
3. Prioritize obvious rubbish/wrong-vertical clusters before weak finance pages.
4. For real lenders with real websites/regulatory data, fix/enrich instead of
   dropping.
5. End every section with:
   - `npm run build`
   - exact built reference scan for touched `/review/<slug>/` paths
   - deploy via `./deploy.sh`
   - live URL status checks for every touched page
   - live sitemap checks

Batch 001 completed and deployed 2026-05-26:

- Archived 77 obvious wrong-vertical rows.
- Redirected the 9 dropped rows with GSC demand.
- Left no-demand archived rows as 404.
- Added a static build denylist in `src/utils/data-build.ts` so archived records
  do not remain linked from prerendered browse pages while old JSON exports still
  exist.

Continue the noindex queue in small batches:

1. Fix/index: select the next small batch of real finance providers from
   `noindex_real_lenders_with_websites_fix_queue_2026-05-26.csv`; verify the
   website/category match and only remove noindex after the page meets the
   review checklist.
2. Chain-location rebuild: keep Vigo/MoneyGram/Barri/Amscot/DolEx-style rows
   out of blind dump batches; rebuild these with the chain-location treatment
   and state regulatory context before deciding indexability.
3. Dump/redirect: obvious auto, vehicle, title-only, passport, detective,
   fraud, and other wrong-vertical pages.
4. Escalate/manual: ambiguous rows where the website/category does not prove
   the page belongs on CreditDoc.

Rule for every batch: store the candidate list, archive list, DB backup path,
Supabase result count, redirect list, and live URL status checks in the project
folder before calling the batch done. Also scan live/static browse pages and
sitemaps for exact `/review/<slug>/` paths before closing the batch.

Batch 004 completed 2026-05-26:

- `continental-bank` reinstated and deployed as indexable.
- `check-cashing-payday-loans`, `credit-repair-finest`,
  `simple-fast-business-funding-same-day-loans`, and
  `smile-jewels-pawn-loans` archived and live-verified as `404`.
- Worker version: `46a1298e-a4d0-478f-9499-1edce895ca73`.
- Next noindex step: move into a 10-15 page fix/index batch from real lender
  candidates, not another blind drop batch, unless the candidate is clearly
  rubbish.

Batch 005 completed 2026-05-26:

- Promoted and deployed 3 verified provider pages:
  - `snap-loans-cash`
  - `reverse-mortgages-home-loans-with-christopher-gibson-at-c2-financial`
  - `public-loans`
- Worker version: `d0f3eb08-20cb-4368-b125-594ac77aded4`.
- Next noindex step: continue the real-lender fix queue, but skip rows with
  bad source evidence. Current examples to hold/skip until fixed:
  `the-debt-crushers` location conflict, `merchant-king-services-inc-credit-funding-experts`
  HTTP 500, `praxis-debt-solutions` suspended site, and rows sourced only from
  PDF/trademark/Google placeholder pages.

---

## Key Reference

| Item | Location |
|------|----------|
| Deploy command | `cd /srv/BusinessOps/creditdoc && source /srv/BusinessOps/.env && unset CLOUDFLARE_API_TOKEN && export CLOUDFLARE_API_KEY="$CLOUDFLARE_GLOBAL_API_KEY" && ./deploy.sh` |
| Inline linker | `src/utils/inline-linker.ts` |
| Review page template | `src/pages/review/[slug].astro` |
| City guide template | `src/pages/credit-guide/[slug].astro` |
| Money pages | `src/pages/best/[slug].astro` + `src/content/listicles.json` |
| Course pages | `src/pages/courses/credit-fundamentals/[slug].astro` |
| Sendy course list | ID=2, hash=`Yj7BPjltZ5YG9nUBw892y93g` |
| Autoresponder | ares_id=1, 8 emails |

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
- Wired `src/pages/review/[slug].astro` to fetch state context through `getStateByCodeRuntimeFromDb()` and render it beside the existing regulatory/HMDA area.
- `npm run build` passed with robots/sitemap checks.
- No deploy was performed.

Next sequencing:

1. Keep the 45 Vigo profiles noindexed while Jammi samples them.
2. Work the cleaned 17-row Phase 1 queue before indexing or expanding:
   `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/phase_1_remaining_action_queue_2026-05-23.csv`
3. After Phase 1 is clean, move into the 250 review-page upgrade queue in small batches.
4. Later enrichment opportunity: add official state money-transmitter/check-casher lookup URLs after source verification.

Phase 1 status tidy completed 2026-05-23:

- Backup: `data/backups/creditdoc_before_phase1_status_tidy_2026-05-23.sqlite`.
- 9 noindexed hold rows now have explicit hold/reject `review_status` values.
- Supabase mirror verified.
- Live spot checks remain `noindex,nofollow`.
- Report: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/PHASE_1_STATUS_TIDY_2026-05-23.md`.

Phase 1 validation classification completed 2026-05-23:

- Backup: `data/backups/creditdoc_before_phase1_validation_classification_2026-05-23.sqlite`.
- Classified weak/rejected rows with `validation_notes`.
- Corrected `envios-de-dinero-money-orders-pago-de-billes` to `category=check-cashing`.
- All remain `pending_approval` and `no_index=true`.
- Supabase verified; pending retry rows: `0`.
- Use the classified queue for the next pass:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/phase_1_remaining_action_queue_classified_2026-05-23.csv`

Phase 1 manual-candidate classification completed 2026-05-23:

- Backup: `data/backups/creditdoc_before_phase1_manual_candidate_classification_2026-05-23.sqlite`.
- All 8 manual-review candidates now have explicit `review_status` and `validation_notes`.
- All remain `pending_approval` and `no_index=true`.
- Supabase verified; pending retry rows: `0`.
- Final decision matrix:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/PHASE_1_FINAL_DECISION_MATRIX_2026-05-23.md`

Next safest Phase 1 task:

- Wrong website fields were removed on 2026-05-23 for:
  `credit-repair-outfit-philadelphia`, `ez-credit-disputes`,
  `rose-financial-solutions`, and `crushing-on-credit`.
- Held/skeleton/noindexed review pages now emit breadcrumb schema only; do not
  rely on this as a substitute for cleanup, because visible page copy still
  needs archive/rebuild/approval decisions.
- Decide archive/redirect/rebuild for clear category mismatches and non-validated rows.
- Do not promote/index anything from Phase 1 until its decision is completed and approved.

Suggested next decision groups:

- 15 unresolved rows have now been neutralized with held-for-review copy, but
  still need final archive/redirect/hold decisions.
- `envios-de-dinero-money-orders-pago-de-billes` has been rebuilt as a
  conservative money-services page and is pending manual review.
- `ez-credit-disputes` has been cleaned as a manual approval candidate and is
  pending manual review.
- Next pass should decide final treatment for the 15 neutralized rows:
  redirect, archive, or keep held for later source research.
- Do not index the two review-ready candidates until manual review confirms
  facts and suitability.

Final-treatment labels now exist for the 15 neutralized rows:

- Queue: `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/phase_1_neutralized_final_treatment_queue_2026-05-23.csv`
- Any redirect implementation is a separate code/deploy decision. Do not add
  redirects casually from the dirty working tree.
- Safest next loop is manual review of the two review-ready candidates, then
  move to the 250-page upgrade queue once Phase 1 is closed.

Review deploy completed 2026-05-23:

- Current cleanup state is live for review after a successful `deploy.sh` run.
- Review these first:
  `snap-loans-cash-orlando`, `ez-credit-disputes`,
  `envios-de-dinero-money-orders-pago-de-billes`, and `lexington-law`.
- After review, continue with final archive/redirect/hold decisions for the 15
  neutralized rows before moving into the 250-page upgrade queue.

Founder review status:

- Approved by Jammi for next indexing decision:
  `ez-credit-disputes`,
  `envios-de-dinero-money-orders-pago-de-billes`.
- Approved mature/indexable page:
  `lexington-law`.
- Do not flip indexing individually. Put approved pages into a small indexing
  decision batch after confirming title/meta/canonical/internal links.
- Continue fixing the remaining Phase 1 pages first: archive, redirect, research
  hold, or rebuild, depending on each row's evidence.

Phase 1 next execution:

- Do not spend upgrade effort on the 5 closed archive holds unless new source
  evidence appears.
- Redirect batch is separate and not implemented yet:
  `life-changers-agency`, `ny-identity-theft-group`,
  `rose-financial-solutions`.
- Best next rebuild candidates:
  review `the-debt-crushers` and `crushing-on-credit` with Jammi.
- YMYL template work is required before considering `snap-loans-cash-orlando`.
- Research holds need stronger source/category validation before index:
  `credit-repair-outfit-philadelphia`,
  `my-credit-advice-credit-repair-and-consultation`, `mycredit-smash`,
  `the-peeples-solution`.

The Debt Crushers is rebuilt and ready for Jammi review:

- Review URL: `https://www.creditdoc.co/review/the-debt-crushers/`
- Keep noindex until Jammi approves location wording and indexability.

Crushing on Credit is rebuilt and ready for Jammi review:

- Review URL: `https://www.creditdoc.co/review/crushing-on-credit/`
- Keep noindex until Jammi approves source caveat and indexability.

My Credit Advice is rebuilt and ready for Jammi review:

- Review URL:
  `https://www.creditdoc.co/review/my-credit-advice-credit-repair-and-consultation/`
- Keep noindex unless a provider-owned source is verified or Jammi approves
  indexability with the source caveat.

Credit Repair Outfit Philadelphia is rebuilt and ready for Jammi review:

- Review URL:
  `https://www.creditdoc.co/review/credit-repair-outfit-philadelphia/`
- Keep noindex unless a provider-owned source is verified or Jammi approves
  indexability with the thin-source caveat.

Snap Loans Cash Orlando is rebuilt and ready for Jammi review:

- Review URL: `https://www.creditdoc.co/review/snap-loans-cash-orlando/`
- Keep noindex until CreditDoc has an explicit lead-generation/YMYL index
  policy and Jammi approves the page treatment.

Immediate review queue:

- `the-debt-crushers`
- `crushing-on-credit`
- `my-credit-advice-credit-repair-and-consultation`
- `credit-repair-outfit-philadelphia`
- `snap-loans-cash-orlando`

All five are improved but remain noindexed. After Jammi review, decide whether
to keep held, request more source work, or move approved pages into a small
indexing decision batch.

250-page rollout progress:

- Completed metadata cleanup for `REVIEW-UPGRADE-01` through
  `REVIEW-UPGRADE-14`: 197 queue rows / 196 unique DB slugs due one duplicate
  queue slug.
- No index status changes were made in these batches.
- The 250-row queue now has a completion CSV:
  `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Review_Page_Upgrade_Rollout_2026-05-23/review_rollout_250_completion_status_2026-05-23.csv`
- Next work is not more blind batching. Next work is review/decision:
  - Jammi review of the 5 rebuilt noindex pages.
  - Decide whether `ez-credit-disputes` and
    `envios-de-dinero-money-orders-pago-de-billes` can enter a small indexing
    decision batch.
  - Decide Vigo chain indexing policy.
  - Separate redirect batch for stale/category-mismatch rows if desired.

## CFPB Responsiveness Report + Local Authority Graph

New strategic project added 2026-05-26:

- Plan: `/srv/BusinessOps/creditdoc/docs/plans/2026-05-26-cfpb-responsiveness-report.md`
- Working public asset:
  `/research/most-responsive-consumer-finance-providers-2026/`
- Working title: **America's Most Responsive Consumer Finance Providers 2026**

Important framing:

- CreditDoc already has CFPB/data research pages. The task is to package and
  distribute a sharper positive-framed report for backlinks, media, provider
  engagement, and authority.
- Use positive wording: "responsive", "strong consumer-response records",
  "public complaint-response transparency".
- Do not publish "worst lender" lists or adversarial CFPB rankings.
- Do not imply companies are safe, approved, licensed, cheapest, or best based
  only on CFPB data.
- Complaint volume is context, not a penalty, because large companies naturally
  receive more complaints.

Next steps:

1. Generate first candidate ranking CSV from `data/regulator.db`.
   - Completed initial pass 2026-05-26:
     `/srv/BusinessOps/CreditDoc Project Improvement/CFPB_Responsiveness_Report_2026-05-26/cfpb_responsiveness_candidates_enriched_2026-05-26.csv`
   - 131 deduped candidate rows.
   - Manual review required; top rows include category/profile mismatches.
2. Inspect top candidates manually for duplicate subsidiaries, weak matches, or
   misleading category/state assumptions.
3. Finalize eligibility/scoring thresholds.
4. Build public Astro report page.
   - Completed 2026-05-26:
     `/research/most-responsive-consumer-finance-providers-2026/`
5. Add internal links from `/research/`, `/research/consumer-complaints/`,
   `/about/creditdoc-data/`, `/press/`, and later relevant review/trends/city
   pages.
   - `/about/creditdoc-data/`, `/press/`, and
     `/research/consumer-complaints/` now link to the report.
6. Create press pitch, provider outreach copy, and Drive copy.
   - Press pitch, provider outreach copy, provider outreach tracker, and
     press/media outreach tracker now exist in the CFPB workpack.

Local authority context:

- Do not pause city/small-town guide velocity. Jammi's strategy is bottom-up
  authority: build useful local/regional pages incumbents ignore, then connect
  them through city-category pages, lender profiles, state regulations,
  question clusters, tools/quizzes, and research authority assets.
- CreditDoc Local Authority Graph plan added:
  `docs/plans/2026-05-26-creditdoc-local-authority-graph.md`

Immediate graph build batch:

1. Sitewide Page Upgrade Batch 001 is complete and committed:
   - 49 report-included provider profile pages receive a safe related-research
     callout through `src/pages/review/[slug].astro`.
   - Workpack:
     `/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Sitewide_Page_Upgrade_2026-05-26/`
2. Sitewide Page Upgrade Batch 002 is complete and committed:
   - `/credit-guide/{slug}/` template now adds a `Plan Your Next Step in {city}`
     local authority path.
   - `/credit-guide/{slug}/{category}/` template now adds a YMYL-safe
     `How to Use This {city} List` section, CFPB data context link, and removes
     blanket `best` wording from the meta description.
   - Latest GSC pull saw 26 `/credit-guide/` URLs; the template upgrade applies
     to every ready city guide and city-category page served by those templates.
3. Sitewide Page Upgrade Batch 003 is complete and committed:
   - `/answers/{slug}/` template now adds a `Continue Your Research` graph path.
   - Answer pages connect to matching category directories, local guide hub,
     state lending-rule hub, CFPB complaint-data context, and local comparison
     CTAs when `target_money_page` is available.
   - Local inventory: 35 answer rows; latest GSC pull saw 13 `/answers/` URLs.
   - Keep language advisory-neutral: no approval prediction, pricing promise,
     licensing determination, or recommendation claim.
4. Sitewide Page Upgrade Batch 004 is complete and committed:
   - `/compare/{slug}/` template now adds a `Check the Context Before You
     Contact a Company` graph path.
   - Comparison pages connect to both lender profiles, category context, local
     guides, and CFPB complaint-data context.
   - Template-level language was softened from `Our Pick` and `Choose...` to
     `Comparison Note` and `Review...`.
   - Local inventory: 280 comparison rows; latest GSC pull saw 7 `/compare/`
     URLs.
   - Residual risk: stored `comparison.winner_reason` copy still needs a later
     data-quality pass for assertive claims.
5. Sitewide Page Upgrade Batch 005 is complete locally and build-verified:
   - `/categories/{category}/` template now adds an `Explore {category}
     Locally` authority path.
   - Category hubs connect into example local city-category pages, the answer
     hub, state lending-rule hub, CFPB complaint-data context, and CreditDoc
     tools.
   - Local inventory: 19 category rows; latest GSC pull saw 14 `/categories/`
     URLs.
6. Next Sitewide Page Upgrade Batch 006:
   - Upgrade `/state/` and `/state/{slug}/lending-laws/` pages so state hubs
     connect into local guide pages, relevant categories, answer clusters, and
     research/methodology pages with advisory-neutral wording.
7. Keep every batch scoped, build-verified, documented, and committed without
   getting pulled back into unrelated cleanup.

Sitewide upgrade program:

- `docs/plans/2026-05-26-sitewide-page-upgrade-program.md`

Completed batches:

- Batch 001 committed `bba672df72`: 49 CFPB report-included provider profiles
  now show the research callout through the review template.
- Batch 002 committed `07b046a396`: city guide and city-category templates now
  connect local pages to category, state, answer, tool, and CFPB data context.
- Batch 003 committed `1acbc51ecf`: answer pages now include `Continue Your
  Research` graph paths to category, local, state, and CFPB context pages.
- Batch 004 committed `d672d77841`: comparison pages now link lender profiles,
  category context, local guides, and CFPB complaint-data context with softened
  comparison wording.
- Batch 005 committed `f1e0e02d2d`: category hubs now link to local
  city-category examples, answer hub, state hub, CFPB data context, and tools.
- Batch 006 committed `e142c1650b`: state index, state directory pages, and
  lending-law pages now connect to local guides, categories, answers, and CFPB
  complaint-data context.
- Batch 007 committed `3b2cb3967d`: research index and four research reports
  now connect back to local guides, state context, provider categories, answer
  clusters, tools, CFPB methodology, and report-specific category context.
- Batch 008 completed locally and build-verified: tools pages now connect to
  local guides, state context, provider categories, answer clusters, resources,
  and CFPB/research pages. Commit next.

Next execution:

1. Commit Batch 008:
   - `src/pages/tools/index.astro`
   - `src/pages/tools/borrowing-power-quiz.astro`
   - `src/pages/tools/debt-payoff-calculator.astro`
   - `src/pages/tools/credit-score-simulator.astro`
   - `CREDITDOC_NOW.md`
   - `CREDITDOC_NEXT.md`
2. Start Batch 009 on resources pages:
   - inspect `src/pages/resources/index.astro`;
   - inspect `src/pages/resources/credit-report-checklist/`;
   - inspect `src/pages/resources/debt-credit-letter-templates/`;
   - add resource-to-tool/answer/local/category/state/research graph paths with
     advisory-neutral wording.
3. Build, verify generated output, document in the sitewide upgrade workpack,
   and commit before Batch 010.

## Regulator Match / Category Cleanup

Plan:

- `/srv/BusinessOps/creditdoc/docs/plans/2026-05-26-regulator-match-category-cleanup.md`

Phase 1 audit queue:

- `/srv/BusinessOps/CreditDoc Project Improvement/CFPB_Responsiveness_Report_2026-05-26/regulator_match_category_audit_phase1_2026-05-26.csv`

Current P1 findings:

- Obvious category-fix candidates:
  - `goldman-sachs-bank-usa`: `pawn-shops` -> `banking`
  - `bmo-bank`: `personal-loans` -> `banking`
  - `synovus-bank`: `mortgages` -> `banking`
- Canonical/brand review needed:
  - `firstbank`
  - `independent-bank-memphis`

Phase 1 write status:

- `synovus-bank`: fixed through DB API, `mortgages` -> `banking`.
- `goldman-sachs-bank-usa`: founder-authorized DB API correction completed,
  `pawn-shops` -> `banking`; `is_protected` remained `0`.
- `bmo-bank`: founder-authorized DB API correction completed,
  `personal-loans` -> `banking`; `is_protected` remained `1`.
- Post-fix candidate CSV regenerated:
  `/srv/BusinessOps/CreditDoc Project Improvement/CFPB_Responsiveness_Report_2026-05-26/cfpb_responsiveness_candidates_enriched_after_phase1_fixes_2026-05-26.csv`
- Phase 1B safe DB fixes completed:
  - `first-technology`: `banking` -> `credit-unions`; official URL set to
    `https://www.firsttechfed.com/`; pending profile review.
  - `mountain-america`: `banking` -> `credit-unions`; official URL set to
    `https://www.macu.com/`; pending profile review.
  - `sarma`: `mortgages` -> `credit-monitoring`; pending category-policy
    review because it is a B2B credit reporting/data/collections provider.
  - No unresolved Supabase retry rows for the three writes.
- Phase 1B candidate CSV regenerated:
  `/srv/BusinessOps/CreditDoc Project Improvement/CFPB_Responsiveness_Report_2026-05-26/cfpb_responsiveness_candidates_enriched_after_phase1b_fixes_2026-05-26.csv`
- Top-50 audit classification is complete. Current top-50 disposition:
  - 40 `yes_pending_final_methodology`
  - 5 `pending_profile_review`
  - 3 `pending_post_regen_review`
  - 1 `pending_fintech_policy` (`moneylion`; do not auto-change)
  - 1 `pending_category_policy` (`sarma`; B2B/data/collections policy needed)
- Profile review batch completed for the 5 `pending_profile_review` rows:
  `first-technology`, `mountain-america`, `wafd-bank-seattle`,
  `hancock-whitney-bank-gulfport`, and `san-diego-county`.
  - stale weak-source copy removed from First Tech and Mountain America
  - official websites aligned for WaFd and Hancock Whitney
  - category-correct names/meta/copy applied
  - all five set to `review_status: published`
  - no unresolved Supabase retry rows
- Post-regeneration profile review completed for:
  `goldman-sachs-bank-usa`, `bmo-bank`, and `synovus-bank`.
  - all three now have brand-level banking profile copy/meta
  - official public URLs are aligned
  - misleading branch phone/address fields were removed where appropriate
  - all three are `published`
  - no unresolved Supabase retry rows
- Updated top-50 disposition:
  - 49 `yes_pending_final_methodology`
  - 1 `pending_category_policy` (`sarma`)
- Profile-quality operating plan added:
  `docs/plans/2026-05-26-profile-quality-agent.md`
- Fintech category launched:
  - new public category `fintech` / `Fintech`
  - initial cohort moved through DB API and exported:
    `moneylion`, `chime`, `brigit`, `earnin`, `dave-banking`, `kikoff`,
    `self-credit-builder`, `self-financial`, `sofi`, `sofi-bank`,
    `varo-bank`
  - category row synced to Supabase and verified with 11 ready lenders
  - MoneyLion is no longer a CFPB policy hold; treat it as Fintech /
    multi-product app in methodology
  - detailed plan:
    `docs/plans/2026-05-26-fintech-category-launch.md`

Next execution:

1. Review the public report scaffold at
   `/research/most-responsive-consumer-finance-providers-2026/` for tone,
   methodology wording, and provider citation language.
2. Add the remaining release assets: press pitch, provider outreach copy, and
   internal link plan from `/about/creditdoc-data/`, `/press/`, and relevant
   complaint/transparency pages.
3. Run the profile-quality workflow continuously against the next CFPB/regulator
   candidates and high-internal-link lender profiles.
4. Start Fintech profile-quality cleanup: normalize official websites, clean
   draft profiles (`dave-banking`, `sofi`), and decide duplicate handling for
   `sofi` vs `sofi-bank`.
5. Keep updating the workpack README and `CREDITDOC_NOW/NEXT` after each batch.

## Sitewide Page Upgrade

Batch 013 trust/support pages are complete, build-verified, and committed as
`61f6875616`. Continue with Batch 014 on the remaining static support/trust
pages:

- inspect `src/pages/privacy.astro`
- inspect `src/pages/terms.astro`
- inspect `src/pages/accessibility.astro`
- inspect `src/pages/about/harvey-brooks.astro`
- inspect any other small static trust pages discovered by `rg --files`

For Batch 014, keep the same rules:

- connect into the bottom-up local graph without adding unsupported claims;
- avoid "best", endorsement, approval, safety, licensing, legal/financial
  advice, guaranteed outcome, and "right provider" language;
- build-check, generated-output-check, document, and commit before moving on.

Batch 014 is complete, build-verified, and committed as `05224c8ddd`. Move to
Batch 015 on the remaining broad navigation/commercial support pages:

- inspect `/press/`
- inspect `/sitemap/`
- inspect `/search/`
- inspect `/deals/` and `/specials/`
- inspect the homepage only if it has not already received the local graph
  treatment in a prior branch

Keep Batch 015 scoped and YMYL-safe. Do not deploy unless requested.

Batch 015 is complete, build-verified, and committed as `7a2f4b0ddb`. Move to
Batch 016 on remaining template families not yet covered by the sitewide graph
upgrade, starting with:

- `src/pages/brand/[brand].astro`
- `src/pages/trends/index.astro`
- `src/pages/trends/[slug].astro`
- any `/best/[slug].astro` or `/review/[slug].astro` follow-up needed after
  checking whether previous batches already covered them

Continue the same loop: inspect, edit narrowly, build, output-check, document,
commit, then proceed.

Batch 016 is complete, build-verified, and committed as `0157185c6f`. Move to
Batch 017 by inventorying remaining uncovered page/templates and shared rendered
components, especially components that inject sitewide commercial/YMYL language
into many page families.

Initial Batch 017 targets:

- run a full `src/pages` inventory against completed batches to find any missed
  user-facing routes;
- scan `src/components` for recommendation, ranking, guarantee, licensing,
  approval, safety, "best fit", and matching language;
- prioritize shared components used by lender/profile/category/comparison cards
  because small wording changes there can improve thousands of rendered pages;
- keep the same loop: inspect, edit narrowly, build, output-check/source-check,
  document, commit, then continue.

Batch 017 is complete, build-verified, and committed as `67cab54fa8`. Move to
Batch 018 by inventorying any remaining page/template families and raw content
sources that still render old commercial/YMYL wording outside the Batch 017
sample pages.

Initial Batch 018 targets:

- run a broader generated-output or source-data scan for remaining
  user-visible `best`, `guarantee`, `wins`, `better value`, approval,
  licensing, recommendation, and diagnosis-style wording across high-value
  routes;
- inspect raw `src/content/comparisons.json`, `src/content/categories.json`,
  and selected lender profiles only where display-time softening is not enough;
- decide whether each finding should be fixed in raw data, page templates, or a
  shared sanitizer;
- keep routes and existing slugs stable unless there is a clear broken-link or
  legal-risk reason to change them;
- build-check, generated-output-check, document, commit, then continue.

Batch 018 implementation is complete, build-verified, and committed as
`49b38174a0`. Move to Batch 019 by inventorying the remaining visible-risk
surface that is not covered by the new runtime content boundary.

Initial Batch 019 targets:

- scan `src/pages`, `src/components`, and high-value `src/content` files for
  remaining unsupported `best`, `top`, `recommended`, guarantee, approval,
  licensing, safety, matching, value, and diagnosis-style wording;
- prioritize templates that render city/browse pages, state pages, research
  pages, tools/resources, and remaining static pages because those are part of
  the bottom-up authority graph;
- decide whether each remaining issue belongs in raw data cleanup, a template
  label change, or the shared `softenYmylCopy()` boundary;
- keep slugs and URLs stable;
- build-check, source/output-check, document, commit, then continue.

Batch 019 implementation is complete, build-verified, and committed as
`04eec9f88c`. Move to Batch 020 by scanning the remaining content-heavy
families and shared labels that still produce unsupported YMYL/commercial
wording.

Initial Batch 020 targets:

- inspect remaining direct matches in `src/pages` and `src/components` after
  excluding explicit negated disclaimers and replacement-rule patterns;
- prioritize `src/pages/tools/borrowing-power-quiz.astro`,
  `src/pages/research/consumer-complaints.astro`, financial-wellness pages, and
  any source-visible labels that still say recommendation/recommended;
- decide whether variable/internal names should be left alone or renamed only
  where they leak into markup, IDs, JSON-LD, or generated HTML;
- keep URLs stable;
- build-check, output/source-check, document, commit, then continue.

Batch 020 implementation is complete, build-verified, and committed as
`c0b49e5c13`. Move to Batch 021 by broadening from direct static-template copy
to source-data and generated-output risk surfaces that can affect many pages.

Initial Batch 021 targets:

- run source and generated-output scans across representative `dist/trends`,
  `dist/review`, `dist/categories`, `dist/answers`, `dist/compare`, and
  `dist/browse` pages for remaining unsupported recommendation, top/best,
  guarantee, approval, licensing, safety, and matching language;
- inspect whether remaining matches are explicit disclaimers, replacement-rule
  patterns, raw provider names, or visible copy that needs softening;
- prefer display-time boundaries or template labels where raw data changes would
  churn many records without improving user-visible quality;
- keep URLs stable;
- build-check, output/source-check, document, commit, then continue.

Batch 021 implementation is complete, build-verified, and committed as
`421bd7122f`. Move to Batch 022 by separating source-data cleanup from
display-time softening and checking the remaining static content areas that are
not yet covered by `softenYmylCopy()`.

Initial Batch 022 targets:

- scan generated `/trends/`, `/financial-wellness/`, `/resources/`, `/courses/`,
  `/best/`, and home/support pages for remaining visible unsupported claims;
- inspect `AffiliateSidebar`, listicle pages, course CTA content, glossary
  examples, and category/listicle content sources to decide where raw copy
  should be edited versus softened at render time;
- preserve explicit legal/scam examples when they are clearly warnings rather
  than CreditDoc claims;
- keep URLs stable and do not stage the unrelated
  `src/content/wellness-guides.json` change unless the user explicitly confirms
  it is intended for this batch;
- build-check, output/source-check, document, commit, then continue.

Batch 022 implementation is complete, build-verified, and committed as
`a6bb2e77dc`. Move to Batch 023 by inspecting source-data and listicle/template
surfaces where remaining YMYL risk may come from raw content rather than static
labels.

Initial Batch 023 targets:

- inspect `src/content/listicles.json` and the listicle renderer before making
  any broad data edits;
- scan generated `/best/`, `/guides/`, `/resources/`, `/financial-wellness/`,
  and selected `/trends/` pages for remaining unsupported best/top,
  guarantee, approval, licensing, endorsement, recommendation, and
  safety-style wording;
- preserve explicit warning/scam/legal examples when they are clearly framed as
  consumer-protection education rather than CreditDoc claims;
- prefer render-time softening for shared presentation issues and raw data
  cleanup only where the source copy itself is misleading or likely to leak
  across many templates;
- keep routes stable and continue excluding the unrelated
  `src/content/wellness-guides.json` change unless the user explicitly confirms
  it belongs in this project batch;
- build-check, output/source-check, document, commit, then continue.

Batch 023 implementation is complete, build-verified, and committed as
`4737bde7ec`. Move to Batch 024 by scanning the remaining generated support
surfaces and raw content sources that were intentionally not rewritten in Batch
023.

Initial Batch 024 targets:

- scan homepage, answers index/source, state sidebar source, generated tools,
  generated resources, generated research, generated trends samples, and source
  listicle content for residual unsupported best/top/recommendation/guarantee,
  approval, licensing, safety, and outcome wording;
- decide case by case whether remaining `best` language is strategic SEO title
  language, route slug/anchor context, a raw content issue, or a visible claim
  that should be softened;
- inspect `src/content/listicles.json` only for raw phrases that are not covered
  by the `/best/[slug]` render boundary or that leak into other templates;
- preserve explicit warning/scam/legal examples;
- keep routes and slugs stable;
- continue excluding unrelated `src/content/wellness-guides.json` unless the
  user explicitly confirms it belongs in this cleanup;
- build-check, output/source-check, document, commit, then continue.

Batch 024 implementation is complete, build-verified, and committed as
`35683faede`. Move to Batch 025 by scanning remaining high-traffic support
pages and dynamic templates for residual YMYL-risk labels that are not already
covered by the shared copy boundary.

Initial Batch 025 targets:

- scan homepage-adjacent static pages, research pages, tools, resources,
  privacy/disclaimer/about pages, and generated trend/review samples for
  remaining visible unsupported best/top/recommendation/guarantee, approval,
  licensing, safety, matching, and outcome wording;
- inspect whether remaining matches are route slugs, explicit disclaimers,
  warning examples, raw provider names, or visible claims that need softening;
- preserve strategic `/best/.../` URLs and existing slugs unless a real broken
  link or legal-risk issue is found;
- continue excluding unrelated `src/content/wellness-guides.json` unless the
  user explicitly confirms it belongs in this cleanup;
- build-check, output/source-check, document, commit, then continue.

Batch 025 implementation is complete, build-verified, and committed as
`5c9a831a8a`. Move to Batch 026 by inspecting the remaining generated compare
pages and raw comparison data surfaces, especially because an unrelated
unstaged `src/content/comparisons.json` change currently contains fresh
unsupported winner/value/guarantee copy.

Initial Batch 026 targets:

- inspect the uncommitted `src/content/comparisons.json` additions separately
  from the committed cleanup work before deciding whether to normalize,
  revert-by-owner, or leave them for the other agent;
- scan generated `/compare/` pages, `src/content/comparisons.json`, and the
  compare renderer for winner/preferable/better-value/guarantee/safe/reliable
  language that may bypass the shared `softenYmylCopy()` boundary;
- prefer template-level or render-time softening if the same unsupported
  comparison patterns appear across many records;
- preserve comparison URLs unless a broken-link issue is found;
- continue excluding unrelated `src/content/wellness-guides.json` unless the
  user explicitly confirms it belongs in this cleanup;
- build-check, output/source-check, document, commit, then continue.

Batch 026 implementation is complete, build-verified, and committed as
`92a87a80a3`. Move to Batch 027 by scanning remaining generated comparison,
trend, review, and directory surfaces for residual tone issues that are not
covered by the shared copy boundary.

Initial Batch 027 targets:

- run a broader but carefully filtered scan across generated `/compare/`,
  `/review/`, `/trends/`, `/browse/`, and `/city/` pages for residual
  recommendation, outcome, safety, approval, licensing, guarantee, and
  best/top wording;
- separate real visible claims from explicit disclaimers, route names, provider
  names, and strategic SEO URL labels;
- inspect whether any remaining comparison wording should be handled by
  `softenYmylCopy()`, comparison-template rendering, or later raw data cleanup
  once the other agent's `src/content/comparisons.json` work is committed or
  abandoned;
- continue excluding unrelated `src/content/wellness-guides.json` and
  `src/content/comparisons.json` from staging unless the user explicitly asks to
  take ownership of those raw content files;
- build-check, output/source-check, document, commit, then continue.

Batch 027 implementation is complete, build-verified, and committed as
`41a648a0d2`. Move to Batch 028 by scanning review, trend, and remaining
directory surfaces for unsupported best/top/recommendation/outcome wording that
is not already covered by `softenYmylCopy()`.

Initial Batch 028 targets:

- inspect generated `/review/` pages and `src/pages/review/[slug].astro` for
  remaining unsupported recommendation, approval, licensing, safety, guarantee,
  top/best, trust, and outcome wording;
- scan generated `/trends/` and selected directory pages for residual phrases
  that are real visible claims rather than route names, provider names,
  disclaimers, or warning examples;
- prefer shared render-time softening only when a pattern leaks across many
  records; otherwise keep changes tightly scoped to the affected template;
- preserve local/category URLs and strategic SEO routes unless a broken-link
  issue is found;
- continue excluding unrelated `src/content/wellness-guides.json` and
  `src/content/comparisons.json` from staging unless the user explicitly asks to
  take ownership of those raw content files;
- build-check, output/source-check, document, commit, then continue.

Batch 028 implementation is complete, build-verified, and committed as
`e3cb9feef6`. Move to Batch 029 by handling residual blog/learn teaser copy
surfaced by the generated scan, especially `right for you`, `good`, `bad`,
`truth`, and similar YMYL suitability/outcome framing in generated static
indexes.

Initial Batch 029 targets:

- inspect the generated `/blog/` index and its source/content feed for teaser
  descriptions containing `right for you`, `good`, `bad`, `truth`, `worth it`,
  and similar judgment/suitability framing;
- decide whether the issue should be handled in blog metadata, an index-only
  teaser softener, or a shared blog-card presentation helper;
- scan `/learn/` because its embedded search data exposed the same blog
  descriptions and key takeaways in generated output;
- preserve blog URLs and titles unless changing a title is necessary for a
  visible YMYL claim; prefer description/teaser softening first;
- continue excluding unrelated `src/content/wellness-guides.json` and
  `src/content/comparisons.json` from staging unless the user explicitly asks to
  take ownership of those raw content files;
- build-check, output/source-check, document, commit, then continue.

Batch 029 implementation is complete, build-verified, and committed as
`bbaefb5b44`. Move to Batch 030 by scanning the remaining generated education
and trend surfaces for residual raw body-copy claims that are outside the
blog/learn teaser boundary.

Initial Batch 030 targets:

- inspect generated `/financial-wellness/`, `/courses/`, `/answers/`, and
  `/trends/` surfaces for remaining unsupported best/top/right-fit/outcome,
  urgency, approval, guarantee, diagnosis, or safety wording;
- separate raw long-form educational body copy from navigation cards, JSON-LD,
  search payloads, and generated snippets so fixes stay in the safest layer;
- avoid touching the unrelated unstaged `src/content/wellness-guides.json` and
  `src/content/comparisons.json` unless the next scan proves those files are the
  correct owner for a visible issue and no render-time boundary is appropriate;
- preserve strategic local/city/category URLs and existing blog/education URLs;
- build-check, output/source-check, document, commit, then continue.

Batch 030 implementation is complete, build-verified, and committed as
`39f756b067`. Move to Batch 031 by handling the course-module raw body-copy
issues found during the Batch 030 generated scan.

Initial Batch 031 targets:

- inspect `src/pages/courses/credit-fundamentals/[slug].astro` and the external
  markdown course module content rendered from
  `/srv/BusinessOps/data/outreach/edu_gov/course/modules`;
- focus on visible course module phrases such as `worth it`, `guarantee`,
  `guarantees results`, `best answer`, and `top lenders` while preserving
  legitimate warning examples where the page is explicitly teaching red flags;
- prefer render-time softening of lesson HTML and navigation snippets if it can
  avoid editing external raw markdown files;
- keep quiz correctness intact and do not change `data-correct` attributes or
  answer semantics;
- build-check, output/source-check, document, commit, then continue.

Batch 031 implementation is complete, build-verified, and committed as
`53e8386d4a`. Move to Batch 032 by scanning answer-cluster and trend pages for
remaining recommendation/outcome phrasing, with special care around route names
and provider names that should not be rewritten.

Initial Batch 032 targets:

- scan generated `/answers/` and `/trends/` pages for remaining visible
  best/top/recommended/right-fit/approval/safe/guarantee/diagnosis/outcome
  wording;
- separate URL slug text, provider names, and legitimate warning examples from
  visible copy that should be softened;
- prefer answer/trend template rendering fixes before raw JSON edits;
- preserve strategic answer URLs, trend URLs, and internal links;
- build-check, output/source-check, document, commit, then continue.

## 2026-06-16 - Next: CreditDoc outbound/category fix release

Before deploying the CreditDoc lender category/outbound tracking fix set:
- review git status and stage only the scoped CreditDoc files, excluding CreditDoc_Engine_Embedding_Readiness_Activities_2026-06-16.md;
- commit the build-verified changes;
- deploy through the documented Cloudflare deploy path, not Vercel;
- live-check /review/upstart/, /best/best-personal-loans-bad-credit/, a representative /compare/ URL, robots.txt, and one /go/upstart/?source=smoke redirect response;
- after deploy, monitor outbound click behavior and GSC/indexing impact over the normal crawl window.

## 2026-07-05 - Next: deploy and expand SE Ranking staticization

Current completed local work:
- Exact SE Ranking 5XX snapshot set generated from
  `/tmp/creditdoc-se-ranking-audit.txt`.
- 124 committed static snapshots prepared under `public/`:
  97 `/review/`, 26 `/credit-guide/<city>/<category>/`, and
  1 `/categories/credit-unions/`.
- Middleware static bypass prepared for exact trailing-slash manifest paths only.
- Build and focused snapshot checks passed after debugger-agent review.

Immediate next steps:
- Commit and push the static snapshot remediation.
- Deploy to Cloudflare Workers via `./deploy.sh`.
- Purge the 124 URLs from Cloudflare cache using the manifest.
- Live-check representative URLs:
  `/review/deluxe-credit-solutions/`,
  `/review/prosper/`,
  `/categories/credit-unions/`,
  `/credit-guide/amarillo-tx/business-loans/`,
  `/credit-guide/austin-tx/mortgages/`,
  `/credit-guide/charlotte-nc/banking/`.
- Confirm live 200s and `x-cdm-static-snapshot: seranking-2026-07-05`.

Then continue structural work:
- Expand staticization beyond the first SE sample set to the full high-value
  `/review/`, `/categories/`, `/credit-guide/`, `/state/`, and `/brand/`
  SEO surfaces, preferably from local/static content generation instead of
  runtime snapshots where feasible.
- Keep `/go/`, `/search/`, query-string URLs, affiliate redirects, and utility
  surfaces out of static SEO snapshots.
