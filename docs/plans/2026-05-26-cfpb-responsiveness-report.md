# CFPB Responsiveness Report Project Plan

Date: 2026-05-26  
Project: CreditDoc CFPB/data authority asset  
Working title: **America's Most Responsive Consumer Finance Providers 2026**

## Objective

Create an outreach-ready CreditDoc research asset that uses CFPB complaint-response data with positive framing to earn backlinks, provider engagement, media interest, and internal trust signals.

This is not another generic article. It is a citable data asset designed to support CreditDoc's local/entity SEO network and long-term lender intelligence graph.

## Strategic Context

CreditDoc already has the data layer:

- CFPB complaint stats
- matched company entities
- regulator/company trend pages
- `/research/consumer-complaints/`
- `/research/lending-transparency/`
- `/research/state-of-subprime-lending-2026/`
- `/about/creditdoc-data/`
- `/press/`

The gap is packaging and distribution:

- sharper positive-framed headline
- defensible eligibility/scoring
- downloadable/exportable findings
- press pitch
- provider outreach hook
- internal links from review/state/city/research pages

## Positioning

Use positive language:

- "Most responsive"
- "Strong consumer-response records"
- "High timely-response rates"
- "Public complaint-response transparency"

Avoid adversarial framing:

- no "worst lenders"
- no "scam" framing
- no "safe" or "approved" claims
- no claims that CFPB data alone proves overall provider quality

## Public Page Target

Proposed URL:

`/research/most-responsive-consumer-finance-providers-2026/`

Core sections:

1. Executive findings
2. What "responsive" means
3. National recognized providers
4. Category rankings where data is sufficient
5. State or regional slices if data quality supports them
6. Methodology and eligibility
7. Caveats and how to use the data
8. Source log
9. Press contact
10. Provider citation/badge copy

## Methodology Draft

Eligibility draft:

- matched regulator entity has `match_confidence >= 0.85`
- has a CreditDoc slug
- local lender/profile row exists
- minimum CFPB complaint count:
  - initial candidate threshold: `total_complaints_alltime >= 25`
  - stricter public threshold may be `total_complaints_12mo >= 10` or all-time >= 50, depending on data distribution
- exclude obvious duplicate subsidiaries/branches after manual review
- do not rank companies if core rate fields are missing

Candidate responsiveness score:

- 60% timely response rate
- 30% resolved-with-relief rate
- 10% complaint trend signal

Trend signal draft:

- `down`: 1.0
- `stable`: 0.7
- `up`: 0.3
- missing/unknown: 0.5

Complaint volume should be shown as context, not used as a penalty by default. High volume can reflect company size and customer base, not necessarily worse behavior.

## Caveats

Every public version must say:

- CFPB complaint data reflects submitted and published complaints, not every customer experience.
- Complaint volume is not normalized by customer count unless a reliable denominator exists.
- High complaint volume can reflect company size.
- A strong complaint-response record does not prove a company is the best, cheapest, safest, licensed, or suitable for every consumer.
- This report is one public-data signal and should be used alongside licensing, contract terms, costs, reviews, and personal fit.

## Deliverables

1. Candidate ranking CSV
2. Methodology note
3. Public Astro research page
4. Press pitch
5. Provider outreach copy
6. Internal link plan
7. Google Drive copy of report/workpack

## Build Sequence

1. Inspect regulator schema and data distribution.
2. Generate candidate ranking CSV.
3. Manually review top candidates for duplicate/mismatch problems.
4. Finalize eligibility and scoring.
5. Build the public page.
6. Add internal links:
   - `/research/`
   - `/research/consumer-complaints/`
   - `/about/creditdoc-data/`
   - `/press/`
   - relevant review pages / trends pages later
7. Build press and provider outreach assets.
8. Run `npm run build`.
9. Deploy through `./deploy.sh` only after release scope review.
10. Upload final docs to Google Drive.

## Progress - 2026-05-26

Phase 3 final input is generated:

- Final CSV:
  `/srv/BusinessOps/CreditDoc Project Improvement/CFPB_Responsiveness_Report_2026-05-26/cfpb_responsiveness_final_report_input_2026-05-26.csv`
- Methodology note:
  `/srv/BusinessOps/CreditDoc Project Improvement/CFPB_Responsiveness_Report_2026-05-26/methodology_note_most_responsive_providers_2026-05-26.md`
- Public-page data file:
  `src/data/cfpb-responsive-providers-2026.json`
- Final main report input contains 49 eligible consumer/provider candidates.
- Sarma is excluded from the first public consumer-facing provider ranking
  because it is primarily B2B credit reporting/data, debt collection,
  background screening, and mortgage-services infrastructure.

Public report scaffold:

- Added route:
  `/research/most-responsive-consumer-finance-providers-2026/`
- Added Research hub link from `/research/`.
- Provider names link directly to `/review/{slug}/`.
- Local dev SSR review links returned 404 because the local runtime data source
  does not mirror production for review pages, but production verification with
  a browser-like user agent returned 200 for all 25 visible report provider
  links.
- Local route verification passed for the report page and non-review
  report-body links.

## Success Metrics

Within 30 days after publication:

- report indexed
- at least 10 outreach replies or provider acknowledgements
- at least 3 referring domains or citations
- at least 25 internal clicks from review/research pages
- at least 1 provider correction/claim conversation, if claim path exists

Within 90 days:

- 10-15 referring domains target
- positive provider/citation usage
- measurable lift in impressions for linked review/research pages

## Strategic Dependency

This project complements, not replaces, the bottom-up city guide strategy.

The city/local pages are the land grab. CFPB/HMDA/data reports are the authority layer. Question clusters are the topical glue. Review pages are the entity graph. Tools/quizzes become the intent-capture layer.
