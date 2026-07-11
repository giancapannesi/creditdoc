# Sendy Contact Backup Guardrail - 2026-07-11

Purpose: protect CreditDoc and DentaFund subscribers, lists, autoresponders, and Sendy configuration before the future Amazon SES SMTP cutover.

## Current State

- Sendy scheduled sender remains active: `*/5 * * * * php7.4 /srv/sendy/scheduled.php`
- CreditDoc app still sends locally through `localhost:25`.
- DentaFund app still sends locally through `localhost:25`.
- No SES SMTP credentials are currently stored in Sendy app settings.
- SES migration must not change subscriber, list, or autoresponder tables.

## Verified Inventory

| App | List | Total | Active | Unsubscribed | Bounced | Complaints |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| CreditDoc | Credit Repair Quiz Leads | 1 | 1 | 0 | 0 | 0 |
| CreditDoc | Credit Fundamentals Course | 1 | 1 | 0 | 0 | 0 |
| DentaFund | DentaFund National Nurture | 0 | 0 | 0 | 0 | 0 |
| DentaFund | DentaFund Calculator Results | 1 | 1 | 0 | 0 | 0 |

Autoresponders:

| Name | List | Emails |
| --- | ---: | ---: |
| Credit Fundamentals Module Summaries | 2 | 8 |
| Calculator results follow-up | 4 | 3 |

## Backup Created

- Backup directory: `/srv/BusinessOps/backups/sendy/2026-07-11T14-12-34Z`
- Files:
  - `sendy_full.sql`
  - `sendy_inventory.tsv`
  - `SHA256SUMS`
- Checksum verification passed for dump and inventory.

## Permanent Backup Automation

Added `tools/sendy_backup.py`.

Daily cron installed:

```cron
35 6 * * * cd /srv/BusinessOps/creditdoc && /usr/bin/python3 tools/sendy_backup.py >> /srv/BusinessOps/logs/sendy_backup.log 2>&1 # sendy-daily-backup
```

Retention: 30 days.

Crontab safety:

- Existing crontab backed up before installation at `/srv/BusinessOps/backups/cron_manual/root_crontab_before_sendy_backup_20260711T141251Z.txt`.
- Active cron job count changed from 179 to 180.
- Existing Sendy scheduled sender was preserved.

## Cutover Rule

Before any SES/SMTP switch:

1. Run `python3 tools/sendy_backup.py`.
2. Confirm `sendy_inventory.tsv` includes all expected lists and autoresponder counts.
3. Change only SMTP/DNS settings needed for delivery.
4. Run a signup test end to end.
5. Verify the subscriber was recorded in Sendy.
6. Verify the autoresponder or confirmation email is sent from the intended sender.
7. Inspect received headers for SPF, DKIM, and DMARC alignment.

