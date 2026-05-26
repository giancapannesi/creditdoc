# CreditDoc Local Authority Graph

Date: 2026-05-26  
Project: CreditDoc bottom-up SEO authority + lender intelligence graph  
Status: active execution plan

## Objective

Turn CreditDoc's growing page network into a deliberate authority graph:

`small-town/city pages -> city-category pages -> lender profiles -> state rules -> answer clusters -> tools/quizzes -> research reports -> provider/profile correction loops`

The goal is not simply more URLs. The goal is to make every new local page
strengthen a wider consumer-finance knowledge graph that Google, users,
journalists, and future partners can understand.

## Strategic Thesis

CreditDoc is young, so the site should not wait passively for Google rankings.
The next 60-90 days should build the assets that make rankings, citations, and
future routing possible:

- local coverage incumbents ignore;
- original public-data reports competitors can cite;
- lender/entity profiles that are cleaned and category-correct;
- state and city regulatory context;
- question clusters that answer consumer intent;
- tools/quizzes that capture intent without regulated integrations;
- provider correction/claim workflows that improve data quality.

This supports the long-term path:

`directory wedge -> lender intelligence graph -> matching/routing engine -> embedded finance marketplace/API`

The current stage is not embedded finance. The current stage is graph depth,
trust, and intent learning.

## Graph Layers

### 1. Local Entry Layer

Pages:

- `/credit-guide/{city-state}/`
- `/city/{city-state}/`
- `/browse/{category}/{city-state}/`

Purpose:

- Capture bottom-up local intent.
- Serve small towns and regional cities that larger directories ignore.
- Give each city page real local utility: providers, maps, directions, state
  rules, local context, and relevant questions.

Required links out:

- 3-8 local/category provider profiles.
- State lending law page.
- 2-4 relevant answer pages.
- 1 relevant tool/quiz.
- Research or data explainer page when the topic involves CFPB/HMDA/state data.

### 2. Entity/Profile Layer

Pages:

- `/review/{slug}/`
- `/trends/{slug}/`
- `/compare/{slug}/`

Purpose:

- Establish lender/provider entities.
- Connect national company data to local presence and consumer intent.
- Feed future matching/routing logic.

Required links out:

- Relevant city/category pages.
- State context where available.
- Similar lenders.
- CFPB/data explainer.
- Research reports when the profile appears in a report.

Quality rule:

- Weak, wrong-vertical, raw, quarantined, or unsupported pages stay noindexed or
  archived. Do not index pages just because they receive impressions.

### 3. Rules And Data Layer

Pages:

- `/state/{slug}/lending-laws/`
- `/about/creditdoc-data/`
- research reports under `/research/`

Purpose:

- Explain why local/provider recommendations vary by state.
- Build E-E-A-T and citation-worthy public-data assets.
- Support journalists and policy researchers.

Required links out:

- Relevant city guides.
- Relevant lender profiles.
- Research index and data methodology.
- Consumer questions that explain the rule in plain English.

### 4. Question Cluster Layer

Pages:

- `/answers/{slug}/`
- category and guide FAQ sections

Purpose:

- Capture long-tail informational intent.
- Glue city pages, lender profiles, and state rules together.
- Reduce thin-directory risk by adding real consumer education.

Required links out:

- One local/city path where relevant.
- One category page.
- One tool/resource when applicable.
- One research/data source when the answer depends on public data.

### 5. Tool And Intent Layer

Pages:

- `/tools/borrowing-power-quiz/`
- `/tools/credit-score-simulator/`
- `/tools/debt-payoff-calculator/`
- future no-risk routing quizzes

Purpose:

- Learn user intent before regulated product integrations.
- Create a bridge from anonymous SEO traffic to segmented consumer needs.
- Prepare future lead/routing logic without collecting sensitive credit data.

Allowed now:

- lightweight quiz completion events;
- email capture only where value is clear;
- non-regulated next-step recommendations;
- internal routing to CreditDoc pages.

Avoid now:

- hard loan prequalification;
- credit pulls;
- paid lender integrations;
- claims of approval odds;
- regulated financial advice.

### 6. Original Research Layer

Pages:

- `/research/most-responsive-consumer-finance-providers-2026/`
- `/research/consumer-complaints/`
- `/research/lending-transparency/`
- `/research/state-of-subprime-lending-2026/`

Purpose:

- Earn links and citations.
- Give providers a factual reason to engage.
- Provide authority nodes that local/profile pages can cite.

Distribution loop:

1. Publish report.
2. Link from `/research/`, `/press/`, `/about/creditdoc-data/`.
3. Link relevant provider profiles back to the report where the provider is
   included.
4. Send provider outreach.
5. Send journalist/policy outreach.
6. Track replies, citations, referring domains, and profile corrections.

## Immediate Execution Priorities

### Priority A: CFPB Report Release Loop

Status:

- Public report exists.
- Data explainer and press page now link to it.
- Press pitch and provider outreach copy exist in the CFPB workpack.

Next:

1. Add report links to included provider profiles where safe and factual.
2. Create a provider outreach tracker CSV.
3. Create a press/media outreach tracker CSV.
4. Add `/research/consumer-complaints/` link to the report.
5. After deploy, verify live internal links and start outreach.

### Priority B: Local Authority Internal-Link Standard

Create a repeatable standard for every city guide:

- city guide links to city-category pages;
- city-category pages link to relevant lender profiles;
- lender profiles link back to city/state/category context;
- answer pages link into the city/category/provider cluster;
- state law pages link back to major city guides.

Acceptance check:

- sample 10 city guides;
- each has at least 5 meaningful internal links across at least 3 graph layers;
- no links to archived/noindexed profiles.

### Priority C: Profile Quality Agent Lane

Use the profile-quality operating plan to improve profiles that matter most to
the graph:

- profiles included in research reports;
- profiles linked from high-value city pages;
- profiles with GSC impressions;
- profiles in new Fintech category;
- profiles with category/data mismatch risk.

### Priority D: No-Risk Intent Capture

Build or improve one consumer intent asset before embedded finance:

- "What kind of credit help do I need?" quiz;
- post-denial next-step guide;
- local borrowing readiness checklist;
- provider comparison worksheet.

The output should route users to internal pages first. No loan application or
paid integration is needed yet.

## Measurement

Weekly graph metrics:

- new city pages published;
- new city-category pages published;
- number of internal links into research reports;
- number of research-report clicks from internal pages;
- provider profile corrections/claims received;
- outreach sent/replies/citations;
- referring domains;
- GSC impressions/clicks by graph layer:
  - local;
  - provider;
  - answers;
  - research;
  - tools.

30-day target:

- 25+ internal links into CFPB report from relevant pages.
- 10+ provider outreach messages sent.
- 10+ journalist/policy outreach messages sent.
- 3+ replies or corrections.
- 3+ new referring domains or citations.

90-day target:

- Local pages begin showing impressions beyond brand searches.
- Research pages attract citation/backlink signals.
- Provider correction loop produces cleaner data.
- First intent-capture flow produces measurable completions.

## Operating Rules

- Do not pause local/small-town page velocity.
- Do not publish thin local pages; every page needs real local info, state
  context, provider links, and useful next steps.
- Do not let cleanup consume the whole day unless it blocks deploy or trust.
- Do not start embedded-finance integrations until there is traffic, intent
  data, and compliance review.
- Use DB/API paths for lender changes; JSON is export output.
- Document every graph-building batch in `CREDITDOC_NOW.md`, this plan, and the
  relevant workpack.

## Next Build Batch

Start with the CFPB report release loop:

1. Add `/research/consumer-complaints/` -> CFPB report link.
2. Add safe links from the top included provider profiles to the report if the
   profile template has a suitable data/research section.
3. Create outreach tracker CSVs in the CFPB workpack.
4. Build and commit.
