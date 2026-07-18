# CreditDoc SE Ranking Baseline — 2026-07-18

**Source:** SE Ranking API via MCP `se-ranking`. Domain: creditdoc.co. Country: US.
**Subscription:** active until 2026-07-20 (renews). 10,000 units, 10K remaining.

## The one number that explains everything

**Domain InLink Rank (Authority) = 15 / 100**

For context:
- NerdWallet ~80
- Investopedia ~85
- The Balance ~78
- CreditDoc **15**

The 65-point authority gap is why:
- CreditDoc's pages rank position 40-80 on Google for informational queries
- Google surfaces bigger sites' pages first for the same queries
- Content-quality improvements on individual pages have limited ceiling until authority moves

## Backlink profile — the reason authority is 15

| Metric | Count |
|---|---:|
| Total backlinks | **6** |
| Unique referring domains | **4** |
| Unique subnets | 2 |
| Unique IPs | 2 |
| dofollow | 4 |
| nofollow | 2 |
| .edu backlinks | 0 |
| .gov backlinks | 0 |

Six backlinks. Real competitor lender directories have 500-5,000 referring domains. This is the single biggest input Google uses to decide trust.

## Ranking profile — 94% "dark middle"

SE Ranking's estimated metrics (US, July 2026):
- **Total ranking keywords: 3,987**
- **Estimated organic traffic: 1,759 visits/month** (model estimate, GSC shows ~1 actual click)
- **Estimated traffic value: $2,300/month** (what it would cost to buy via PPC)

Position distribution:
| Bucket | Keywords |
|---|---:|
| Top 1-5 | 1 |
| Top 6-10 | 5 |
| Top 11-20 | 39 |
| Top 21-50 | 1,524 |
| Top 51-100 | 2,417 |

Only 45 keywords in "click zone" (top 20). 3,941 keywords sitting position 21-100 = ghost rankings that don't convert. Matches GSC's 1-click reality despite 27K impressions.

Movement (last 30d):
- New keywords: 2,254 (huge — reflects credit-guide + answers push getting indexed)
- Up in position: 260
- Equal: 1,146
- Down: 327
- Lost: 1,230

## AI search visibility — zero

| Metric | Value |
|---|---|
| Average position across AI answers | null |
| AI opportunity traffic | 0 |
| Link presence (citations in AI answers) | 0 |
| Brand presence in AI results | null |

**CreditDoc is invisible to ChatGPT, Perplexity, Gemini, Google AI Overviews.** llms.txt is deployed but AI models aren't citing us. This will matter more each quarter.

## "Competitors" per SE Ranking

The only domains SE Ranking's algorithm identifies as sharing keyword footprint with CreditDoc:
- tipperarycu.ie (Irish credit union — 137 traffic, 4 shared keywords)
- palcofcu.org (Public Auto Loan CFCU — 348 traffic, 5 shared keywords)

Big lender directories (NerdWallet, Bankrate, WalletHub) don't appear because keyword overlap is low — CreditDoc ranks for niche lender brand terms; they rank for generic "best X" queries.

## What this baseline changes in the plan

The Month 2 "strike-zone execution" and Month 3 "/credit-guide/ dark zone" moves have a **ceiling problem**: without authority signals, page-level improvements top out at position 15-25 for most queries. You can move a page from position 50 to position 20, but position 20 → 3 requires trust the site doesn't yet have.

**Revised diagnosis:**

The single highest-leverage move is **backlink acquisition targeting DA 20+ referring domains**. Every 10 quality referring domains moves DA measurably. The goal for the next 3 months should be:
- Current: 4 referring domains
- Month 1 target: 15 referring domains
- Month 2 target: 40 referring domains
- Month 3 target: 100 referring domains

Existing Hermes backlinks pipeline (`/srv/BusinessOps/hermes-creditdoc-backlinks/`) is already running — needs a full audit of results.

**Priority 2 in the revised plan:** AI visibility. llms.txt deployed but citations are 0. Need to understand why (content quality? entity recognition? just time?).

**Priority 3 (still valid):** page-level strike-zone execution, but expectations reset: the win here is inclusion in the "author of choice for [lender brand X]" middle-tier, not top-3 for generic queries.

## Immediately actionable

1. Audit `hermes-creditdoc-backlinks` — what's it produced? What's the reply rate? Where's the pipeline stuck?
2. Check llms.txt live at `creditdoc.co/llms.txt` — validate content + accessibility
3. Consider paid content sponsorships / directory listings for fast DA lift (e.g. Crunchbase, Owler, industry press)
4. Publish/pitch original CFPB complaint analysis pieces — data journalism attracts natural backlinks
