# Hermes Backlink Pipeline Audit — 2026-07-18

## Ground truth

| Metric | Value |
|---|---|
| Confirmed backlinks won | **0** |
| Total outreach emails sent (lifetime) | 43 |
| Last outreach email sent | **2026-05-18** (60 days ago) |
| Current ready queue count | 15 items (BUT — see below) |
| Daily cron | Running every 2:25 PM UTC weekdays |
| Reply checks | Running daily, 0 replies matched |
| Referring domains per SE Ranking | 4 |
| Total backlinks per SE Ranking | 6 |

## What actually broke

The pipeline is technically running but structurally empty:

1. **Queue bookkeeping is stale.** `OUTREACH_QUEUE_WAVE6.json` and `OUTREACH_QUEUE_TOOLS_PR_2026-07-11.json` still mark 15 items as `ready_after_approval`. But all 15 are already in `OUTREACH_SENT_LOG_2026-05-18.md` / `2026-05-19.md`. The send script correctly detects the sent status and skips them → `count: 0, targets: []` every run.

2. **No new waves queued since May 18.** The idea-miner cron generates ideas daily (see `ideas/backlink-ideas-*.md`) but doesn't convert them into new `OUTREACH_QUEUE_*.json` files. Manual step gap.

3. **Reply conversion has been zero.** 43 emails sent → 0 replies matched → 0 backlinks. This isn't a coding bug; it's a channel-viability problem. Cold email to university librarians and state consumer offices asking to link to a private lender directory has near-zero conversion by design.

## Strategy audit

The `BACKLINK_ACQUISITION_PLAN.md` and current waves target:
- University libraries / financial wellness offices
- State consumer protection agencies
- Public libraries
- CFPB / FTC / educational .gov pages

These targets have three killing problems for CreditDoc:
1. **Selection bias:** they curate .gov/.org educational resources, not private for-profit lender directories.
2. **Compliance:** universities and .gov agencies are risk-averse and won't link to unverified third-party financial content.
3. **Signal misfit:** even if they linked, high-authority link from a university library to a for-profit lender site could look like paid placement to Google.

**In short:** these are not the right targets. This channel would have converted at 0% even if the pipeline had been running perfectly.

## Higher-conversion channels the plan should pivot to

Reordered by realistic ROI:

### 1. Data journalism placements (highest ROI)
CreditDoc has unique CFPB complaint dataset + HMDA lending data + 27K lender directory. Financial journalists at Bloomberg, Reuters, NYT Business, WSJ, Marketwatch actively look for original data angles. One well-pitched dataset story = 5-50 high-authority backlinks + AI citations.
- Cost: engineering time to package the data
- Cadence: 1-2 pitches/month
- Realistic conversion: 5-15%

### 2. HARO / Qwoted / Muck Rack expert responses
Journalists post source requests daily. CreditDoc's existing lender data + regulatory analysis is directly quotable. Consistent contributions build DA-70+ backlinks + brand mentions.
- Cost: 15 min/response × 5-10 responses/week
- Realistic conversion: 5-10%
- Existing infra: hermes-agent could handle discovery

### 3. Industry aggregator listings (fastest DA lift)
- Crunchbase profile
- Owler profile  
- G2, Trustpilot, BBB profiles
- LinkedIn company page + relevant industry lists
- Reddit /r/personalfinance verified sources
Realistic backlinks: 5-15 within 30 days if pursued directly.

### 4. Reciprocal / partnership links
Payment app comparisons, credit repair firm partnerships already in the review directory could be asked for reciprocal profile links.

### 5. Broken-link opportunities
`hermes-creditdoc-backlinks/BACKLINK_IDEAS_LATEST.md` already has some. Automate discovery, but replace the "email librarian" pattern with "email the actual page owner about their broken link, offer a replacement."

## Immediate fixes needed

1. **Un-block the queue bookkeeping.** Add a `sent_log_check` to `send_approved_outreach_queue.py` that marks items sent in the JSON file, not just the log. One-time script to backfill Wave 6.
2. **Deprecate the university-library outreach path.** Delete or archive the existing queues; stop generating more of the same.
3. **Rewrite `BACKLINK_ACQUISITION_PLAN.md` around the 5 channels above.**
4. **Do not un-pause daily sends** until strategy #1-5 is scoped and approved.

## What DIDN'T need auditing (already verified working)

- Cron itself fires reliably (14:25 UTC daily)
- Reply checks work (uses AgentMail digital access, 0 false negatives)
- Progress emails work (sent daily to founder via Harvey)
- Autopilot policy file (`AUTONOMOUS_BACKLINK_POLICY.json`) is enabled and correct
