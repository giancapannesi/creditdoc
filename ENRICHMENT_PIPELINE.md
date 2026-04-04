# CreditDoc Enrichment Pipeline — DO NOT MODIFY WITHOUT FOUNDER APPROVAL

**Last updated:** 2026-04-02
**Owner:** Founder (Gian Capannesi) — manual approval required for all promotions

---

## HARD RULES

1. **NO lender gets indexed without founder's manual daily approval.** No agent, no script, no cron may auto-promote lenders from `pending_approval` to `ready_for_index`. This is non-negotiable.
2. **NO cron entry may be removed.** Crontab guard at `/usr/local/bin/crontab` blocks any write that reduces cron count. Alerts Telegram if triggered.
3. **Engine must skip lenders without URLs.** Don't waste enrichment cycles on lenders the website finder hasn't reached yet.
4. **Don't touch working scripts.** If it's running and producing results, leave it alone.

---

## Pipeline Flow

```
┌─────────────────────────────────────────────────────────┐
│                    WEBSITE FINDER                        │
│  Every 2 hours — finds URLs for lenders without them    │
│  creditdoc_website_finder.py --count 1000               │
└──────────────────────┬──────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│                    URL RESETTER                          │
│  Every 10 min — resets newly-URL'd lenders to 'raw'     │
│  so the engine picks them up on next run                │
│  creditdoc_url_resetter.sh                              │
└──────────────────────┬──────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│                 ENRICHMENT ENGINE                        │
│  14:00 UTC daily — 500 per batch                        │
│  creditdoc_autonomous_engine.py --count 500             │
│                                                         │
│  For each lender with a URL:                            │
│    1. Category check (Claude Haiku)                     │
│    2. URL reachability check (HTTP HEAD)                │
│    3. Website scrape (Playwright)                       │
│    4. Full enrichment (Claude Sonnet)                   │
│    5. Quality control (Claude Haiku)                    │
│    6. If QC passes → pending_approval                   │
│    7. If QC fails → stays raw or failed_quarantine      │
│                                                         │
│  SKIPS lenders without URLs (fixed Apr 2)               │
└──────────────────────┬──────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│              PENDING APPROVAL (noindex)                  │
│  Pages are built on the live site but have              │
│  <meta name="robots" content="noindex">                 │
│  Google cannot see them. Founder can review them.       │
└──────────────────────┬──────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│              PROMOTION REPORT (05:00 UTC)                │
│  creditdoc_promotion_report.py                          │
│                                                         │
│  1. Generates CSV of all pending_approval lenders       │
│  2. Includes CreditDoc page URLs for live review        │
│  3. Uploads to Google Drive as Google Sheet             │
│  4. Sends Telegram notification with link               │
│  5. Founder opens Sheet, clicks URLs, reviews quality   │
└──────────────────────┬──────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│             FOUNDER MANUAL APPROVAL                      │
│                                                         │
│  Telegram: !approve all    → promote all pending        │
│  Telegram: !reject slug1   → reject specific ones       │
│                                                         │
│  On approval:                                           │
│    1. Flips processing_status → ready_for_index         │
│    2. Sets no_index → false                             │
│    3. Git commit + push → Vercel deploys                │
│    4. IndexNow submits URLs to Google                   │
│                                                         │
│  Script: creditdoc_approval_review.py --approve-all     │
└──────────────────────┬──────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│              LIVE + INDEXED                              │
│  Pages visible on site, noindex removed,                │
│  Google can crawl and index them.                       │
└─────────────────────────────────────────────────────────┘
```

---

## Processing Status State Machine

```
raw ──→ enriching ──→ verifying ──→ pending_approval ──→ ready_for_index
 │                        │                                    ↑
 │                        ↓                                    │
 │                  failed_quarantine                    (founder approves)
 │                        ↑
 └────────────────────────┘
        (no URL, QC fail, non-financial)
```

---

## All CreditDoc Cron Jobs (21 total)

| # | Schedule | Script | Purpose |
|---|---------|--------|---------|
| 1 | Every 10 min | `creditdoc_url_resetter.sh` | Reset newly-URL'd lenders for engine |
| 2 | Every 2 hours | `creditdoc_website_finder.py --count 1000` | Find URLs for lenders without them |
| 3 | 04:00 Sun | `creditdoc_ssl_checker.py` | Weekly SSL cert check |
| 4 | 05:00 daily | `creditdoc_daily_summary.py` | Morning summary (AgentMail) |
| 5 | 05:00 daily | `creditdoc_promotion_report.py` | Google Sheet → Drive + Telegram |
| 6 | 05:00 daily | `creditdoc_daily_promoted.py` | Daily promoted lenders report |
| 7 | 06:00 daily | `creditdoc_blog_scheduler.py` | Flip scheduled→published blog posts |
| 8 | 06:30 daily | `creditdoc_blog.py --count 2` | Generate 2 blog posts |
| 9 | 06:30 Mon | `seo_keyword_tracker.py --site creditdoc` | Weekly keyword tracking |
| 10 | 07:00 Tue | `seo_content_queue.py --site creditdoc` | Content gap analysis |
| 11 | 09:00 daily | `seo_engine.py --site creditdoc` | SEO daily report |
| 12 | 10:00 Mon | `creditdoc_kpi_report.py --snapshot` | Weekly KPI snapshot |
| 13 | 12:00 daily | `creditdoc_content_drip.py` | Content drip |
| 14 | 14:00 daily | `creditdoc_autonomous_engine.py --count 500` | **Main enrichment engine** |
| 15 | 15:00 daily | `creditdoc_wellness_generator.py --count 2` | Generate wellness guides |
| 16 | 15:30 daily | `creditdoc_comparison_generator.py --count 5` | Generate comparisons |
| 17 | 16:00 daily | `creditdoc_cfpb.py --count 100` | CFPB complaint data |
| 18 | 16:00 daily | `creditdoc_self_healer.py --count 30` | Recover quarantined lenders |
| 19 | 19:00 daily | Git auto-push | Commit + push lender changes |
| 20 | 20:00 daily | `creditdoc_daily_summary.py` | Evening summary (AgentMail) |
| 21 | Quarterly | `creditdoc_legislation_review.py` | State legislation updates |

---

## Protections

- **Crontab guard** (`/usr/local/bin/crontab`): Blocks any write that reduces cron count. Backs up before every write. Alerts Telegram if blocked. Reverts if `verify_crons.sh` fails.
- **Known-good backup**: `/srv/BusinessOps/backups/crontab_known_good.txt`
- **Verify script**: `/srv/BusinessOps/tools/verify_crons.sh` — checks all expected crons are present
- **Noindex guard** (`[slug].astro`): `pending_approval` pages always have noindex regardless of quality score
- **Build filter** (`data.ts`): Only `ready_for_index` and `pending_approval` pages are built. Raw/quarantined pages don't exist on the site.

---

## Key Files

| File | Purpose |
|------|---------|
| `tools/creditdoc_autonomous_engine.py` | Main enrichment engine |
| `tools/creditdoc_website_finder.py` | URL discovery for lenders |
| `tools/creditdoc_url_resetter.sh` | Reset lenders after URL found |
| `tools/creditdoc_promotion_report.py` | Daily Drive sheet for approval |
| `tools/creditdoc_approval_review.py` | Approve/reject handler |
| `tools/creditdoc_self_healer.py` | Recover quarantined lenders |
| `tools/creditdoc_daily_summary.py` | Pipeline status reports |
| `src/utils/data.ts` | Build filter (line 177-178) |
| `src/pages/review/[slug].astro` | Noindex guard (line 167-169) |
| `data/creditdoc_engine.db` | Engine state database |

---

## Lender Stats (Apr 2, 2026)

| Status | Count | Description |
|--------|------:|-------------|
| raw | 15,831 | Waiting for enrichment (8,048 have URL, 7,783 don't) |
| failed_quarantine | 6,804 | Non-financial, dead, or failed QC |
| ready_for_index | 3,849 | Live and indexed |
| enriching | 124 | Currently being processed |
| pending_approval | ~100+ | Enriched today, waiting for tomorrow's approval |
| **Total** | **26,684** | |

---

## What NOT to do

- Do NOT auto-promote lenders. Founder approves manually.
- Do NOT remove or modify cron entries. Append only.
- Do NOT run the engine on lenders without URLs. It wastes API credits.
- Do NOT modify `creditdoc_autonomous_engine.py` without checking the queue logic skips no-URL lenders.
- Do NOT change the build filter in `data.ts` without understanding the noindex implications.
- Do NOT rewrite this document without founder approval.
