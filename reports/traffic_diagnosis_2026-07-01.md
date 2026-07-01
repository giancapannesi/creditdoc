# CreditDoc Traffic Diagnosis - 2026-07-01

## Read

CreditDoc is about 4 months old. The latest complete GSC window does not show a total disappearance; it shows very low clicks, unstable rank, and a Google-visible footprint still dominated by review/entity pages rather than the commercial tools/course/answer strategy.

## Latest 7-Day Window

- Window: 2026-06-23 to 2026-06-29
- Clicks: 3 vs 3 (+0)
- Impressions: 10,550 vs 9,568 (+982, +10.3%)
- CTR: 0.0284% vs 0.0314%
- Average position: 46.62 vs 35.47 (+11.15; higher is worse)

## Latest 28-Day Window

- Window: 2026-06-02 to 2026-06-29
- Clicks: 9 vs 13 (-4)
- Impressions: 35,786 vs 35,443 (+343, +1.0%)
- CTR: 0.0251% vs 0.0367%
- Average position: 39.97 vs 38.46 (+1.51; higher is worse)

## 28-Day Page-Family Mix

| Family | Clicks | Impressions | CTR | Avg position |
|---|---:|---:|---:|---:|
| review | 8 | 33,407 | 0.0239% | 40.89 |
| city_guides | 0 | 942 | 0.0% | 19.19 |
| best | 0 | 148 | 0.0% | 79.41 |
| answers | 0 | 18 | 0.0% | 13.33 |
| categories | 0 | 324 | 0.0% | 43.3 |
| wellness | 0 | 24 | 0.0% | 49.29 |
| browse | 0 | 172 | 0.0% | 51.46 |
| compare | 0 | 5 | 0.0% | 23.0 |
| blog | 0 | 17 | 0.0% | 45.53 |
| other | 1 | 729 | 0.1372% | 13.04 |

## Latest Indexation Audit

- Source: `/srv/BusinessOps/data/creditdoc_gsc_audit/gsc_audit_2026-07-01.md`

| Bucket | Inspected | Indexed | Not indexed | Top reason |
|---|---:|---:|---:|---|
| best | 27 | 25 | 2 | URL is unknown to Google (2) |
| answers | 50 | 0 | 50 | URL is unknown to Google (49) |
| financial-wellness | 60 | 18 | 42 | URL is unknown to Google (27) |
| blog | 35 | 3 | 32 | URL is unknown to Google (26) |
| categories | 19 | 16 | 3 | URL is unknown to Google (2) |
| compare | 50 | 10 | 40 | URL is unknown to Google (40) |
| brand | 50 | 1 | 49 | URL is unknown to Google (49) |
| state | 50 | 3 | 47 | Crawled - currently not indexed (33) |
| city | 40 | 7 | 33 | URL is unknown to Google (20) |
| browse | 40 | 0 | 40 | URL is unknown to Google (39) |
| root | 25 | 0 | 25 | URL is unknown to Google (25) |

Audit blind spot: `tools, courses` was not present in the latest completed audit. The audit script has now been patched to include those buckets on the next run.

## Tools And Course Indexation

| Bucket | Verdict | Coverage | URLs |
|---|---|---|---:|
| courses | NEUTRAL | URL is unknown to Google | 10 |
| tools | NEUTRAL | URL is unknown to Google | 16 |
| tools | NEUTRAL | Alternate page with proper canonical tag | 1 |
| tools | NEVER_POLLED | (blank) | 2 |

## Diagnosis

1. The short-term pain is rank/CTR quality, not a complete crawl failure.
2. Review pages still carry almost all impressions and nearly all clicks.
3. Best/tools/course/answers are not yet mature GSC traffic engines; several of those sections are still unknown or thinly indexed.
4. The immediate SEO work should prioritize indexation and internal routing for strategic assets, then use GSC watchlists to improve pages already visible in positions 4-20.

## Next Actions

1. Run the patched GSC coverage audit so tools and courses are measured in the same report as answers/money pages.
2. Keep daily priority indexing focused on tools, courses, answers, and money pages; do not spend Google quota on review pages.
3. Build a weekly strong-position zero-click list and only rewrite snippets where the page/query mismatch is proven.
4. Use city/review pages that Google already sees to route users and crawl equity into relevant calculators, course modules, and money pages.
