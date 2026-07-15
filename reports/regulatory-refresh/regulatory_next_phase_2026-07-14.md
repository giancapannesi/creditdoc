# CreditDoc Regulatory Next Phase Scheduler - 2026-07-14 11:10 UTC

## Indexing Queue
- Priority regulatory/money/tool URLs tracked: 23
- Newly added to force-Google queue: 23
- Force-Google queue size after merge: 23

## Checks
### regulatory execution - OK
```
CreditDoc regulatory SEO execution check: status=PASS report=/srv/BusinessOps/creditdoc/reports/regulatory-refresh/regulatory_seo_execution_2026-07-14.md
```

### priority regulatory dry-run - OK
```
CreditDoc Priority Indexing — 2026-07-14 11:10 UTC
============================================================
  Tools:    0
  Courses:  0
  Research: 0
  Reg/trust:0
  Resources:0
  Wellness: 0
  Money:    0
  Answers:  0
  City:     0
  Blog:     0
  Brand:    0
  Compare:  0
  State:    0
  (Skipped 3 already indexed (PASS), 0 unverified, 4 in tier-specific cooldown)

Total priority queue: 0 URLs
Nothing to push.
```

### social duplicate guard - OK
```
{
  "ok": true,
  "command": "audit-social-duplicates",
  "date": "2026-07-14",
  "guard_effective_date": "2026-07-06",
  "linkedin_repeat_block_days": 90,
  "pinterest_repeat_block_days": 90,
  "linkedin_duplicate_targets": [],
  "pinterest_duplicate_targets": [],
  "historical_linkedin_duplicate_targets": [],
  "historical_pinterest_duplicate_targets": [
    {
      "target_url": "https://www.creditdoc.co/tools/commercial-loan-calculator/",
      "count": 2,
      "entries": [
        {
          "id": "cd-pin-2026-07-02-commercial-loan-calculator",
          "created_at": "2026-07-02T12:54:52.817Z",
          "age_days": 12,
          "public_url": "https://www.pinterest.com/pin/484840716158293329",
          "source": "state"
        },
        {
          "id": "cd-li-2026-07-03-commercial-loan-calculator",
          "created_at": "2026-07-03T14:05:12.498Z",
          "age_days": 11,
          "public_url": "https://www.pinterest.com/pin/484840716158300001",
          "source": "jsonl"
        }
      ]
    }
  ]
}
```

## Next Phase Instructions
- Keep regulatory pages and priority tools in the forced indexing queue until the existing priority indexer accepts/removes them.
- Continue weekly regulatory execution checks and monthly link-drift checks.
- Regulatory-intent answer cluster is part of the forced indexing queue and should be checked in the weekly execution report.
- Do not pause feeds, city/blog/answers/wellness publishing, LinkedIn, Pinterest, or existing crons without explicit founder approval.
