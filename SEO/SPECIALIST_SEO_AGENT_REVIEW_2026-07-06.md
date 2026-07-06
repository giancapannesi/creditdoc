# CreditDoc Specialist SEO Agent Review - 2026-07-06

Purpose: consolidate specialist AI review of CreditDoc's current SEO situation after the static page, duplicate meta, robots, feed, and social automation fixes.

## Executive Diagnosis

CreditDoc is being discovered by Google, but Google is mostly seeing the wrong surface.

The latest available GSC export in `Traffic Analysis/` shows the site receiving impressions, but those impressions are dominated by low-position provider/entity review pages rather than the strategic revenue assets: money pages, tools, answers, financial wellness, and course pages.

Important context: review pages make up the bulk of the discovered surface partly because they were the first/largest page family created. Local city pages also received manual URL Inspection submissions earlier, when the team believed the automatic API submission flow was producing more indexation impact than it actually was. Do not misread this as proof that Google prefers review/city pages strategically; it is partly a sequencing and submission-history artifact.

Key evidence from `Traffic Analysis/Pages.csv` for 2026-05-20 to 2026-06-19:

| Family | Impressions | Clicks | CTR | Avg position |
|---|---:|---:|---:|---:|
| `/review/` | 36,279 | 8 | 0.022% | 41.9 |
| `/best/` | 214 | 0 | 0% | 78.9 |
| `/tools/` | 1 | 0 | 0% | 1.0 |
| `/answers/` | 22 | 0 | 0% | 39.8 |
| `/financial-wellness/` | 149 | 0 | 0% | 77.0 |
| `/compare/` | 6 | 0 | 0% | 66.8 |

This is not an "invisible site" problem. It is a discovery, crawl-priority, authority, and commercial-routing problem.

## Specialist Findings

### 1. Technical SEO / Crawl

Recent fixes cleaned the obvious hygiene issues:

- tools, answers, blog, wellness, course, and money pages are now static/generated and safer;
- rendered SEO audit passes;
- feeds pass;
- robots/go handling is now technically correct;
- duplicate-meta and robots-blocked validation can be requested in GSC.

Remaining technical risk:

- The sitemap still advertises about 25k URLs, while over 22k do not exist as physical static HTML and depend on Worker/Supabase runtime behavior.
- The largest runtime families are `/review/`, `/credit-guide/`, `/brand/`, `/state/`, and `/categories/`.
- SE Ranking's reported 5XX class can recur under crawler pressure if runtime pages depend on live database fetches.
- The route registry is messy: redirects and fallbacks live across `_redirects`, middleware, review routes, sitemap injection, and static snapshots.
- Review-directory noise remains large, including unresolved old `/review/` 404 paths from SE exports.

Technical priority:

1. Shrink sitemap exposure for runtime review/city/category surfaces using allowlists based on quality, indexation, and impressions.
2. Stop exposing or internally linking unpublished `/review/` URLs.
3. Add a live sitemap validator that samples live sitemap URLs and fails on 3XX/4XX/5XX/noindex/runtime timeouts.
4. Staticize selectively: high-impression categories, selected credit-guide pages, and selected review pages. Do not bulk-staticize the whole review corpus blindly.

### 2. Content SEO / Keyword Architecture

The current content inventory is large, but authority is not concentrated enough into the target commercial clusters.

What is working:

- The broad architecture exists: money pages, tools, answers, wellness, courses, categories, and internal link tooling.
- Competitor research supports the tool + money page + exact-intent guide model, especially from Lendio.
- CreditDoc already has calculator pages and many answer pages.

What is not working yet:

- Google's current impressions are mainly provider/entity queries like `yrefy, llc`, `cfsc check cashing`, and `red canoe credit union`.
- Strategic commercial pages are too low or barely visible:
  - `best-sba-loans` around position 43;
  - `best-small-business-loans` around position 70;
  - `best-equipment-financing` around position 87;
  - `best-startup-business-loans` around position 93.
- Answers exist in volume but many do not carry explicit money-page or cluster routing fields, so authority flow depends too much on automatic phrase matching.
- There is answer cannibalization risk from near-duplicate intents.
- Credit card money-page coverage remains underbuilt relative to the competitor keyword files.

Content priority:

1. Build a GSC watchlist for strategic URLs already getting impressions.
2. Map the top 50 business/SBA/loan/card answers to one primary money page each.
3. Strengthen exact clusters:
   - SBA loans;
   - bad-credit/startup business loans;
   - business calculators;
   - secured/bad-credit cards.
4. Consolidate or clearly differentiate duplicate answer intents.
5. Prioritize `/best/credit-cards-for-bad-credit/` as the next card gap if not already sufficiently covered.

### 3. Authority / Digital PR

CreditDoc is a 4-month-old finance/YMYL site. Aggressive aged-domain, PBN, paid guest-post, exact-anchor, or microsite link schemes are not recommended because they can damage trust before the site has enough legitimate authority.

Best authority route:

1. Original data PR:
   - CFPB complaint trend reports;
   - SBA lending scorecards;
   - financial access maps;
   - credit rebuilding resource-gap reports.
2. Public-benefit outreach:
   - credit report checklist;
   - free credit course;
   - credit score simulator;
   - borrowing power quiz;
   - loan denial reason checker;
   - wellness guides.
3. Reporter/source program:
   - position CreditDoc as a data source, not just another finance blog.
4. Embeddable tools only if useful and branded:
   - no keyword-stuffed anchors;
   - no spammy badges;
   - start with checklist/calculator embeds for partners already in conversation.
5. LinkedIn/Pinterest:
   - use as brand proof and content distribution;
   - do not expect major direct traffic immediately.

Realistic authority targets for a 4-month-old finance site:

- Month 1: 2-5 legitimate referring domains.
- Month 2: 5-12 cumulative referring domains.
- Month 3: 15-25 cumulative referring domains.
- Month 4: 25-50 cumulative referring domains if a data report lands.

### 4. Commercial SEO / SERP Conversion

The current issue is not a broad CTR problem yet because the revenue assets barely have impressions. It is a revenue-asset discovery/routing problem.

Important findings:

- `/best` raw content uses high-intent "Best..." titles, but the rendered template softens titles/metas from "Best" to "Compare" in `src/pages/best/[slug].astro`.
- This may reduce exact SERP match for target queries such as `best small business loans`, `best SBA loans`, and `best credit repair companies`.
- Schema exists, but GSC `Search appearance.csv` shows only 3 product-snippet impressions, so rich results are not yet a material lever.
- `/best` pages need stronger above-the-fold commercial routing:
  - compare top picks;
  - check eligibility/fit;
  - use calculator first.
- Internal linker strategy may be diluted because `data/money_page_map.json` and `src/utils/inline-linker.ts` do not appear fully aligned.

Commercial priority:

1. Review whether `/best` SERP titles/metas should preserve "Best" while body copy remains cautious/compliant.
2. Align inline linking with the 11 priority money pages.
3. Route high-impression review pages into relevant money pages and tools with visible modules.
4. Add result-state monetization from calculators to exact matching money pages.
5. Use the manual GSC quota on tools, course, high-intent wellness, answers, and unindexed money pages, not review/city/state noise.

## Integrated Priority Plan

### P0 - This Week

1. Build a live sitemap status validator for the sitemap families.
2. Narrow sitemap exposure for runtime review/city/category surfaces.
3. Audit and align `money_page_map.json` with `inline-linker.ts`.
4. Review `/best` title/meta rewriting and restore exact commercial query language where legally acceptable.
5. Keep daily manual GSC queue at 10 priority URLs: tools, course, high-intent wellness, answers, money pages.

### P1 - Next 2 Weeks

1. Map top 50 business/SBA/loan/card answers to primary money pages.
2. Strengthen internal links from high-impression review/category pages to `/best` and tools.
3. Upgrade SBA, bad-credit business loan, startup business loan, business calculator, and secured/bad-credit card clusters.
4. Consolidate near-duplicate answers where they split the same intent.
5. Create the first data PR asset from existing complaint/lending data.

### P2 - Next 4-8 Weeks

1. Start public-benefit outreach to libraries, universities, nonprofits, and consumer resource pages.
2. Publish one data/report asset per month.
3. Run a reporter/source routine around consumer finance and lending data.
4. Monitor branded searches, referring domains, priority URL impressions, indexed priority pages, and position movement.

## What Not To Do

- Do not buy aged domains and point them at CreditDoc.
- Do not build PBN/microsite link networks.
- Do not spend manual GSC quota on review/city/state noise.
- Do not blindly produce more pages without cluster routing.
- Do not rely on sitemap/API submission as if it guarantees indexing.

## Google Guidance Anchor

Google's own documentation says sitemap submission is a hint and does not guarantee crawling or indexing. Google also says it does not guarantee every compliant page will be indexed or served. That matches the current diagnosis: the solution is not only submission volume; it is clearer crawl surface, stronger internal routing, better quality/authority signals, and fewer low-yield URLs competing for crawl/index attention.
