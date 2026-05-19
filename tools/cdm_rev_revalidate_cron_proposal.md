# CDM-REV Phase 2.3.B — REVALIDATE_TOKEN cron wiring proposal

**Status:** AWAITING JAMMI GREENLIGHT — no crontab modifications until approved.
**Author:** Claude (cdm-rev loop, Apr 30)
**Risk class:** Low — env injection only, no logic changes, append-only crontab edit.

---

## Why this exists

Phase 2.3 is wired in `tools/creditdoc_db.py` (`_ping_revalidate()` at line 151) and
`/api/revalidate` accepts 11 ContentTypes. But `_ping_revalidate()` soft-fails when
`REVALIDATE_TOKEN` is missing — which is the case in cron context today.

To activate the ping in production, the token must be on the env of every cron unit
that calls `creditdoc_db.update_*`. Token already exists at
`/srv/BusinessOps/tools/.creditdoc-revalidate.env` (chmod 600).

---

## Cron units that need the env source

Ranked by write frequency:

| Cron unit | Schedule | Writers it calls | Priority |
|---|---|---|---|
| `creditdoc_guardian.py` | `0 * * * *` (hourly) | update_lender on drift heal | HIGH |
| `creditdoc_db_sync.py` | `0 7 * * *` (07:00 UTC daily) | update_lender bulk JSON→DB | HIGH |
| `publish_blog_posts.py` | `0 13 * * *` | update_blog_post / update_listicle | MEDIUM |
| `daily_seo_content.py` | `0 10 * * *` | update_lender on enrichment | MEDIUM |
| Any cluster_answer publisher | varies | update_answer | LOW (drips) |

---

## Proposed crontab patch (append-only, NEVER replace whole crontab)

The pattern below is what the safety doc requires (`(crontab -l; echo …) | crontab -`).
Each cron unit gets prefixed with `. /srv/BusinessOps/tools/.creditdoc-revalidate.env && export REVALIDATE_TOKEN &&`.

```diff
- 0 * * * * cd /srv/BusinessOps && /srv/BusinessOps/.venv/bin/python creditdoc/tools/creditdoc_guardian.py >> logs/cd_guardian.log 2>&1
+ 0 * * * * . /srv/BusinessOps/tools/.creditdoc-revalidate.env && export REVALIDATE_TOKEN && cd /srv/BusinessOps && /srv/BusinessOps/.venv/bin/python creditdoc/tools/creditdoc_guardian.py >> logs/cd_guardian.log 2>&1

- 0 7 * * * cd /srv/BusinessOps && /srv/BusinessOps/.venv/bin/python creditdoc/tools/creditdoc_db_sync.py >> logs/cd_db_sync.log 2>&1
+ 0 7 * * * . /srv/BusinessOps/tools/.creditdoc-revalidate.env && export REVALIDATE_TOKEN && cd /srv/BusinessOps && /srv/BusinessOps/.venv/bin/python creditdoc/tools/creditdoc_db_sync.py >> logs/cd_db_sync.log 2>&1
```

(Repeat the same pattern for each MEDIUM-priority unit. LOW can ship in a follow-up.)

---

## Application protocol (ON GREENLIGHT)

1. `crontab -l > /srv/BusinessOps/backups/crontab_pre_revalidate_$(date +%s).txt`
2. Apply the diff via line-by-line `(crontab -l; echo "<new line>") | crontab -` for each new entry, then remove the old equivalent. NEVER `crontab <file>`.
3. Run `/srv/BusinessOps/tools/verify_crons.sh`
4. Trigger guardian manually with the env sourced; tail logs/cd_guardian.log for the next minute looking for `[revalidate] 200`.
5. Confirm against `/api/revalidate` access log on the worker (counter increments).

## Rollback (if anything fails)

```bash
crontab /srv/BusinessOps/backups/crontab_pre_revalidate_<timestamp>.txt
```

(Backup is the FULL crontab snapshot taken in step 1.)

## Why this is safe

- Token is read-only injection; can't break the writer (it soft-fails on bad/empty token).
- Ping is fire-and-forget; if `/api/revalidate` 4xxs, writer log shows it but the DB write completes anyway.
- No logic changes inside `creditdoc_db.py` — it's already wired and tested. This is just env propagation.

## What this does NOT do

- Does NOT touch live DB (writes happen as a side effect of normal cron runs, not from this change).
- Does NOT modify the crontab in any way until Jammi greenlights and the protocol above is run.
- Does NOT enable production-DNS revalidate. `_REVALIDATE_URL` is still the preview origin
  (`cdm-rev-hybrid.creditdoc.pages.dev`) until cutover.
