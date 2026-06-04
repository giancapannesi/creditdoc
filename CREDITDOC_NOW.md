# CreditDoc — LIVE STATE (LIVE / RESUME-CURSOR)

> **Read me first.** This file is rewritten at the end of every session. It is the resume-cursor — the next-spawned Claude reads this BEFORE MEMORY.md / DECISIONS.md to know "where are we right now."

---

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
