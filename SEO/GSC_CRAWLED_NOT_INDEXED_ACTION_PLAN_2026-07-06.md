# CreditDoc GSC Crawled/Unindexed Action Plan - 2026-07-06

## Current Diagnosis

Source: `indexation_status` in `/srv/BusinessOps/creditdoc/data/creditdoc.db`, checked 2026-07-06.

The visible GSC problem is not one single failure. It is a mix of:

- Pages Google has crawled but not indexed.
- Pages still unknown to Google.
- Large review/state/city noise that must not consume the founder's 10 manual GSC submissions per day.

Current `Crawled - currently not indexed` counts by family:

| Family | Count |
|---|---:|
| review | 600 |
| state | 68 |
| city | 53 |
| financial wellness | 25 |
| blog | 13 |
| answers | 11 |
| money pages | 8 |
| other | 1 |

Important interpretation:

- The review/city/state totals are not the best first use of the daily manual limit.
- Manual GSC submissions should focus on high-value public assets: tools, course/learn pages, financial wellness, answers, and money pages.
- API/IndexNow submission is still useful for breadth, but it does not replace the founder's 10 manual URL Inspection submissions.

## Manual GSC Queue Rule

The manual queue is now set to **10 URLs/day**.

Updated script:

`/srv/BusinessOps/tools/creditdoc_daily_gsc_queue.py`

Cron:

`15 6 * * * /usr/bin/flock -w 7200 /tmp/creditdoc_db_writer.lock -c '/srv/BusinessOps/.venv/bin/python3 /srv/BusinessOps/tools/creditdoc_daily_gsc_queue.py --apply' >> /srv/BusinessOps/logs/creditdoc_daily_gsc_queue.log 2>&1`

Priority order:

1. `/tools/`
2. `/courses/` and `/learn/`
3. `/financial-wellness/`
4. `/answers/`
5. Money pages: `/best/`, `/categories/`, `/browse/`, `/compare/`
6. Research/regulatory/trust
7. Blog
8. State
9. Brand

Excluded from the manual email:

- City pages
- Credit-guide pages
- Indexed/PASS URLs
- Canonical-conflict URLs
- Random unpublished review-directory noise

## Today's Correct 10-URL Priority Set

Dry-run after the fix produced exactly 10 URLs:

1. `https://www.creditdoc.co/financial-wellness/credit-builder-loans/`
2. `https://www.creditdoc.co/financial-wellness/credit-building-after-prison/`
3. `https://www.creditdoc.co/financial-wellness/credit-repair-scams/`
4. `https://www.creditdoc.co/financial-wellness/credit-score-ranges-explained/`
5. `https://www.creditdoc.co/financial-wellness/credit-utilization-guide/`
6. `https://www.creditdoc.co/financial-wellness/emergency-fund-guide/`
7. `https://www.creditdoc.co/financial-wellness/hard-vs-soft-inquiries/`
8. `https://www.creditdoc.co/financial-wellness/how-credit-scores-calculated/`
9. `https://www.creditdoc.co/financial-wellness/identity-theft-prevention/`
10. `https://www.creditdoc.co/financial-wellness/medical-debt-guide/`

These are good manual candidates because Google has already crawled them and chosen not to index yet. Requesting indexing here gives Google a direct recrawl prompt on authority content.

## What To Validate In GSC Now

Ask Google to validate fixes for:

- Duplicate title/meta-description sample from `SEO/Table - Duplicates.csv`.
- Robots-blocked `/go/` issue after the deployed robots cleanup.

Do not ask validation on broad "Crawled - currently not indexed" as if it is one technical bug. For those, use the daily 10 manual submissions and then monitor status changes.

## Operating Plan

Daily:

- Let the 06:15 UTC queue email send exactly 10 priority URLs.
- Manually submit only those 10 in GSC URL Inspection.
- Do not manually submit city/review/go/search utility URLs.
- Keep API/IndexNow submission running separately for breadth.

Weekly:

- Pull GSC status and compare transitions:
  - `Crawled - currently not indexed` -> indexed
  - `URL is unknown to Google` -> crawled/indexed
  - duplicate/canonical/robots errors -> down
- If the same valuable page remains unindexed after repeated manual submissions and recrawls, treat it as a page-quality/internal-link/consolidation task, not just a submission task.

Quality escalation:

- For persistent unindexed tools/course/wellness/answer/money pages, add stronger internal links from indexed money pages, homepage modules, relevant blogs, and LinkedIn/Pinterest posts.
- If two answer/wellness pages overlap heavily, consolidate or differentiate them instead of repeatedly submitting both.
- Keep `/go/` URLs noindex via header and crawlable by robots so Google can see the noindex.

