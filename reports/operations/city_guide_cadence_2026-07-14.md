# CreditDoc City Guide Cadence Change - 2026-07-14

## Change

CreditDoc city guide generation was reduced from a daily batch to one city guide every two UTC days while the city landing-page and lead-capture enhancement project catches up.

## Active Cron

```cron
0 9 * * * /usr/bin/python3 -c 'import datetime,sys; sys.exit(datetime.date.today().toordinal() & 1)' && /srv/BusinessOps/.venv/bin/python3 /srv/BusinessOps/tools/cron_alert.py "creditdoc_city_guides" /srv/BusinessOps/.venv/bin/python3 /srv/BusinessOps/tools/creditdoc_city_guide_generator.py --batch 1 >> /srv/BusinessOps/logs/creditdoc_city_guides.log 2>&1 # CADENCE 2026-07-14: one guide every two UTC days
```

This skips July 14, 2026, runs July 15, 2026, then alternates every other UTC day.

## Monitoring Adjusted

- `/srv/BusinessOps/tools/creditdoc_feed_continuity_watchdog.py` now expects the active city guide cron to contain `creditdoc_city_guide_generator.py --batch 1`.
- `/srv/BusinessOps/tools/creditdoc_content_engine_daily_verify.py` now skips the city guide job on off-days instead of creating false failure alerts.

## Verification

- July 14 guard exits `1`, so the job skips.
- July 15 guard exits `0`, so the job runs.
- Python compile passed for the generator, feed watchdog, and content verifier.
- Content engine verifier dry run passed and reported `city guides: skipped on alternating-day cadence`.
- Feed watchdog cron requirement check passed with `cron: city guides active`.

## Crontab Backups

- `/srv/BusinessOps/backups/cron_manual/root_crontab_before_creditdoc_city_guides_cadence_20260714T085005Z.txt`
- `/srv/BusinessOps/backups/cron_manual/root_crontab_before_creditdoc_city_guides_cadence_fix_20260714T085017Z.txt`
