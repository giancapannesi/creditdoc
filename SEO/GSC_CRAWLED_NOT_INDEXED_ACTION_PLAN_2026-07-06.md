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

## Today's Manual Submission Handling

The 06:15 UTC cron had already sent a 20-URL email before the script was corrected to 10/day.

Use the first 10 URLs from that email as today's manual GSC submissions:

1. `https://www.creditdoc.co/courses/credit-fundamentals/`
2. `https://www.creditdoc.co/tools/accounts-receivable-financing-calculator/`
3. `https://www.creditdoc.co/tools/borrowing-power-quiz/`
4. `https://www.creditdoc.co/tools/credit-repair-qualify-quiz/`
5. `https://www.creditdoc.co/tools/credit-score-simulator/`
6. `https://www.creditdoc.co/tools/equipment-financing-calculator/`
7. `https://www.creditdoc.co/tools/loan-denial-reason-checker/`
8. `https://www.creditdoc.co/tools/sba-guarantee-fee-calculator/`
9. `https://www.creditdoc.co/financial-wellness/secured-credit-cards-complete-guide/`
10. `https://www.creditdoc.co/financial-wellness/side-hustle-income-guide/`

The database stamp was corrected after the script fix: positions 11-20 from the old email were unstamped so they are not hidden by cooldown.

Dry-run after the DB correction now returns exactly 10 URLs for the next eligible queue:

1. `https://www.creditdoc.co/financial-wellness/store-credit-cards-worth-it/`
2. `https://www.creditdoc.co/financial-wellness/subscription-audit-guide/`
3. `https://www.creditdoc.co/financial-wellness/50-30-20-budget-rule/`
4. `https://www.creditdoc.co/financial-wellness/609-dispute-letter-truth/`
5. `https://www.creditdoc.co/financial-wellness/authorized-user-strategy/`
6. `https://www.creditdoc.co/financial-wellness/auto-loans-bad-credit/`
7. `https://www.creditdoc.co/financial-wellness/borrowing-money-explained/`
8. `https://www.creditdoc.co/financial-wellness/building-credit-from-zero/`
9. `https://www.creditdoc.co/financial-wellness/checking-savings-guide/`
10. `https://www.creditdoc.co/financial-wellness/choosing-credit-repair-company/`

These are good next manual candidates because they are authority content pages that are either unknown to Google or crawled but not indexed.

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
