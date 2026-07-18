# CreditDoc Bing Baseline — 2026-07-18

## Headline

**Bing is alive, not dead.** Prior "Bing collapsed" narrative was based on the `--action traffic` endpoint which returned 0 — this appears to be a bug or different aggregation. The `--action keywords` endpoint returns real data.

| Metric | Bing | Google (comparison) |
|---|---:|---:|
| Impressions (last 30d) | ~505 | 27,850 |
| Clicks (last 30d) | 4 | 1 |
| Unique queries | 247 | 10,996 |
| Pages in index | 18,851 | (n/a — different property model) |
| CTR | 0.79% | 0.0036% |
| Daily crawl rate | 2,000-3,000 pages | (n/a) |
| Crawl errors | 0 | (n/a) |

**Bing has ~1/55th Google's impression volume but ~200x higher CTR.** 4 clicks from Bing beats 1 click from Google in absolute terms.

## Index growth trajectory (last 14 days)

| Date | Pages Crawled | In Index |
|---|---:|---:|
| 2026-07-04 | 3,600 | 17,389 |
| 2026-07-07 | 2,206 | 17,744 |
| 2026-07-10 | 3,082 | 18,398 |
| 2026-07-13 | 2,795 | 18,888 |
| 2026-07-15 | 2,434 | 18,925 ← peak |
| 2026-07-16 | 2,101 | 18,889 (-36) |
| 2026-07-17 | 1,883 | 18,851 (-38) |

Index grew steadily then dropped 74 pages Jul 15-17. Coincides with fingerprint fixes shipped Jul 16 (Bing may be re-evaluating). Watch this trajectory over the next 2 weeks.

## Top 10 Bing queries

| Query | Impressions | Clicks | Avg Pos |
|---|---:|---:|---:|
| create credit union | 138 | 2 | 4.2 |
| unfcu | 37 | 0 | 8.0 |
| ent credit union | 30 | 0 | 8.5 |
| oneaz credit union | 27 | 0 | 7.0 |
| resound credit union nashville | 26 | 0 | 6.0 |
| giggle finance | 23 | 0 | 9.5 |
| mirastar credit union | 20 | 0 | 8.0 |
| orsa credit union michigan | 18 | 0 | 6.0 |
| rize credit union | 15 | 0 | 6.5 |
| clearone advantage bbb | 13 | 0 | 4.3 |

Notice: Bing rankings are much better (avg pos 4-9) than Google's (avg pos 40-80). If Bing volume grew even 10x, that CTR pattern would produce real traffic.

## Actionable

1. **Bing is a leading indicator.** It ranks CreditDoc pages 5-10x higher than Google does. If Google slowly starts trusting the site, we'd expect Bing rankings to be predictive.
2. **The Jul 15-17 index drop is worth monitoring.** Watch daily via existing `creditdoc_bing_indexnow_watchdog` cron.
3. **Bing URL submission cron is running healthy** — 100/day quota, no crawl errors, index growing.
4. **Nothing to actively fix on Bing.** The lane is working.
