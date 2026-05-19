# CreditDoc Project Glossary

> Searchable index of every named system, automation, and feature in the CreditDoc project.
> When building or debugging, search this file first to find what already exists.

---

## Inline Linking for Pages (Smart Links Automation)

**Name:** Inline Linking / Smart Links
**Status:** LIVE (deployed 2026-05-14, Worker `0b074d86`)
**System:** SSR-time keyword-to-money-page linker

### What it does
Automatically inserts contextual hyperlinks from content pages to money pages (`/best/*`), category pages (`/categories/*`), and research pages (`/research/*`) at render time. Links are placed on semantically relevant phrases — not random anchors.

### How it works
- **Engine:** `src/utils/inline-linker.ts` — 148 phrase-to-URL mappings sorted by phrase length (longest match wins)
- **Pattern:** `createLinker(glossaryTerms, { moneyBudget, glossaryBudget })` returns a stateful function. Each call tracks which phrases and URLs have already been used on the page via `usedPhrases` + `usedUrls` Sets — prevents duplicate links.
- **Runs at:** Cloudflare Workers SSR. One deploy = all pages updated. No build step, no batch job, no content rewrite needed.

### Where it's wired

| Page type | Template | Linker call | Budget | Verified |
|-----------|----------|-------------|--------|----------|
| Blog posts | `src/pages/blog/[slug].astro` | Line 83 — `linker(section.content)` | money: 6, glossary: 6 | 2026-05-14 |
| Wellness guides | `src/pages/financial-wellness/[slug].astro` | Line 64 — `linker(section.content)` | money: 8, glossary: 8 | 2026-05-14 |
| City guides | `src/pages/credit-guide/[slug].astro` | Lines 116-118 — editorial, FAQ answers, credit tips | money: 6, glossary: 0 | 2026-05-14 |
| Lender reviews | `src/pages/review/[slug].astro` | via `linkifyDescription` | money: 5, glossary: 5 | pre-existing |
| Answer pages | `src/pages/answers/[slug].astro` | via `linkifyDescription` | money: 5, glossary: 5 | pre-existing |

### What was fixed (2026-05-14)
- **City guides** imported `createLinker` at line 10 but never called it. Editorial, FAQ answers, and credit tips all rendered as raw HTML with zero smart links.
- Fix: created linker instance and applied to editorial (`linker(editorialRaw)`), FAQ answers (`linker(faq.a)`), and credit tips (`linker(tip)`). Changed credit tips `<li>` to use `set:html` for anchor tag rendering.
- Added 5 CFPB research phrases: "consumer complaints", "CFPB complaints", "CFPB data", "complaint resolution", "consumer protection data" → `/research/consumer-complaints/`.

### Verification
```bash
# Check any page type for smart links
curl -s "https://www.creditdoc.co/credit-guide/denver-co/" | grep -oP 'href="/best/[^"]*"'
curl -s "https://www.creditdoc.co/blog/<any-slug>/" | grep -oP 'href="/best/[^"]*"'
curl -s "https://www.creditdoc.co/financial-wellness/<any-slug>/" | grep -oP 'href="/best/[^"]*"'
```

### Key files
- `src/utils/inline-linker.ts` — the engine (148 mappings, dedup logic, budget caps)
- `src/pages/credit-guide/[slug].astro` — city guide template (fixed 2026-05-14)
- `src/pages/blog/[slug].astro` — blog template (was already working)
- `src/pages/financial-wellness/[slug].astro` — wellness template (was already working)

### Rules
- Links are contextual: "credit repair" links to `/best/best-credit-repair-companies/`, "personal loans" to `/best/best-personal-loan-lenders/`, etc.
- Budget caps prevent link spam (max 6-8 money links per page)
- Same URL never linked twice on one page
- Same phrase never linked twice on one page
- Longer phrases match first (prevents "credit" stealing from "credit repair companies")
- No automation change needed for new content — the linker runs at SSR render time on every page view

---

## City Guide SEO Titles & Metas

**Name:** City Guide SEO Optimization
**Status:** LIVE (updated 2026-05-14)
**System:** LLM prompt template + Supabase `seo_title` / `meta_description` fields

### What it does
Generates unique, long-tail, click-worthy SEO titles (50-60ch) and compelling meta descriptions (145-155ch) for every city guide page. Each title targets real search intent with city-specific power words — no generic "Credit Repair & Financial Services in X" templates.

### How it works
- **Generator prompt:** `tools/creditdoc_city_guide_generator.py` lines 403-412 — instructs the LLM to write unique, click-worthy titles with examples
- **Fallback:** `credit-guide/[slug].astro` lines 104-105 — SSR fallback generates `Credit Repair & Financial Services in {city}, {state_abbr} | CreditDoc` if DB fields are NULL
- **Storage:** Supabase `city_guides` table, `seo_title` and `meta_description` columns
- **Rendering:** SSR reads from Supabase at request time — no rebuild needed after DB update

### Title format rules
- 50-60 characters (Google display limit)
- Must include city name and state abbreviation
- Must be unique across all city guides — no two identical formats
- Use power words: "Best", "Compare", "Top", "Guide", year tag
- Vary structure: some lead with city, some with topic, some with action verb

### Meta description rules
- 145-155 characters (Google snippet limit)
- Must include a specific stat or local fact (FDIC branches, SBA count, cost of living)
- Must include a call-to-action ("Compare", "Find", etc.)
- Must mention key services (credit repair, lenders, free resources)

### Verification
```bash
curl -s "https://www.creditdoc.co/credit-guide/<slug>/" | grep -o '<title>[^<]*</title>'
curl -s "https://www.creditdoc.co/credit-guide/<slug>/" | grep -oP '<meta name="description" content="[^"]*"'
```

### Key files
- `tools/creditdoc_city_guide_generator.py` — prompt template (lines 403-412)
- `src/pages/credit-guide/[slug].astro` — SSR rendering (lines 104-105)

---

## Sendy Email System

**Name:** Sendy / CreditDoc Email Marketing
**Status:** FULLY OPERATIONAL (2026-05-14) — emails delivering to Gmail inbox
**System:** Self-hosted email marketing platform at `sendy.creditdoc.co`

### What it does
Handles all CreditDoc email marketing: quiz lead capture, autoresponder drip sequences, course email delivery, and newsletters. Zero monthly cost — one-time 2016 license. Sends directly from VPS via Postfix with DKIM + SPF authentication.

### How it works
- **Platform:** Sendy v2.1.2.8, self-hosted on VPS at `/srv/sendy/`
- **URL:** `https://sendy.creditdoc.co/`
- **PHP:** 7.4 FPM (separate from system PHP 8.3 — Sendy's obfuscated code requires PHP 7.x)
- **Database:** MySQL 8.0, database `sendy`, user `sendy` on localhost
- **Email delivery:** Postfix → DKIM signing (OpenDKIM) → direct delivery via IPv6
- **SSL:** Let's Encrypt via Cloudflare DNS challenge
- **DNS:** `sendy.creditdoc.co` → VPS `187.77.2.146` (Cloudflare proxied)
- **Cron:** `*/5 * * * * php7.4 /srv/sendy/scheduled.php` (campaign processing)

### Login
- **Email:** `gian.eao@gmail.com`
- **Password:** Stored in the credential store / password manager; do not record secrets in repo docs
- **API key:** Stored in the Sendy credential store / environment; do not record secrets in repo docs
- **License:** Stored in the Sendy credential store / environment; do not record secrets in repo docs

### Email authentication (DNS)
- **SPF:** `v=spf1 include:simplelogin.co ip4:187.77.2.146 ip6:2a02:4780:4:a118::1 ~all`
- **DKIM:** `sendy._domainkey.creditdoc.co` TXT record with RSA public key (selector `sendy`)
- **Critical:** IPv4 port 25 blocked at Hostinger network level. All email delivers via IPv6. Postfix `inet_protocols = all`. DO NOT set to `ipv4`.

### Subscribe API (for quiz integration)
```bash
curl -X POST "https://sendy.creditdoc.co/subscribe" \
  -d "list=rCzcu8brUim88T892Y85IqRQ" \
  -d "email=user@example.com" \
  -d "name=User Name" \
  -d "boolean=true"
# Returns "1" on success
```

### Campaign API
```bash
curl -X POST "https://sendy.creditdoc.co/api/campaigns/create.php" \
  -d "api_key=$SENDY_API_KEY" \
  -d "from_name=CreditDoc" \
  -d "from_email=noreply@creditdoc.co" \
  -d "reply_to=noreply@creditdoc.co" \
  -d "subject=Subject" \
  -d "html_text=<p>HTML body</p>" \
  -d "list_ids=rCzcu8brUim88T892Y85IqRQ" \
  -d "send_campaign=1" \
  -d "brand_id=1"
```

### Key files
| File | Purpose |
|------|---------|
| `/srv/sendy/` | Installation root |
| `/srv/sendy/includes/config.php` | DB creds + APP_PATH |
| `/srv/sendy/scheduled.php` | Campaign send processor (cron every 5min) |
| `/etc/nginx/sites-available/sendy` | nginx vhost (SSL + clean URL rewrites) |
| `/etc/postfix/main.cf` | Postfix config (inet_protocols=all) |
| `/etc/opendkim.conf` | DKIM signing config |
| `/etc/opendkim/keys/creditdoc.co/sendy.private` | DKIM private key |
| `/etc/mysql/mysql.conf.d/sendy.cnf` | MySQL sql_mode override for Sendy |
| `/srv/BusinessOps/tools/.sendy-db-creds` | DB password (chmod 600) |

### Patches applied (2026-05-14)
- `scheduled.php`, `includes/create/send-now.php`, `includes/create/test-send.php`: Added localhost SMTP branch (no auth, no auto-TLS) — original code required username+password
- `includes/update.php`: Empty wrapper (original lost during install)
- MySQL: ~20 missing columns added across campaigns/subscribers/login/apps/lists tables
- `/etc/mysql/mysql.conf.d/sendy.cnf`: Disabled `ONLY_FULL_GROUP_BY` (Sendy uses non-standard GROUP BY)

### What's next
1. Wire quiz results page to POST to subscribe endpoint
2. Build autoresponder drip sequence in Sendy UI
3. Sprint 2: "Credit Repair 101" course email drip

### Verification
```bash
curl -s -o /dev/null -w "%{http_code}" "https://sendy.creditdoc.co/login"  # 200
echo "Test" | sendmail gian.eao@gmail.com && tail -3 /var/log/mail.log  # status=sent
systemctl status php7.4-fpm postfix opendkim  # all active
```

---

## GSC Indexation Tracking & Daily Queue

**Name:** GSC Indexation Automation
**Status:** LIVE (fixed 2026-05-14)
**System:** SQLite verdict tracking + daily email queue + URL Inspection API polling

### What it does
Tracks Google indexation status of every CreditDoc page. Sends Jammi a daily email with 10 priority URLs to manually submit via GSC Request Indexing. Auto-refreshes verdicts so already-indexed pages drop out of the queue.

### How it works
- **Verdict poller:** `tools/gsc_indexation_check.py` — calls Google URL Inspection API, updates `indexation_status` table with PASS/NEUTRAL/FAIL verdicts. Checks 50 URLs/day, prioritizing NEVER_POLLED and oldest-checked.
- **Daily queue:** `tools/creditdoc_daily_gsc_queue.py` — picks 10 highest-priority non-PASS URLs, emails via Harvey, uploads CSV to Drive. Deduplicates rows before picking. 30-day cooldown prevents re-queuing recently submitted URLs.
- **Sitemap sync:** runs on every queue invocation, adds new sitemap URLs as NEVER_POLLED.

### Crons
| Time (UTC) | Script | What |
|------------|--------|------|
| 07:00 daily | `gsc_indexation_check.py 50` | Poll 50 URLs via Inspection API |
| 06:15 daily | `creditdoc_daily_gsc_queue.py --apply` | Build + email daily queue |

### Priority tiers (queue order — AI Council 2026-05-13, reordered 2026-05-14)
city (/credit-guide/) > money (/best/) > answers > wellness > blog > state > brand > compare > categories

### Priority indexer tiers (`creditdoc_priority_indexing.py`)
city > money > blog > brand > compare > state (answers + wellness excluded — Jammi submits manually)

### What was fixed (2026-05-14)
- **727 duplicate rows** in `indexation_status` — sitemap sync wrote `answers/slug`, indexation checker wrote `answers:slug`. Queue read stale duplicates, kept sending already-indexed pages.
- Fix: dedup step before queue pick, indexation checker expanded from `/answers/`-only to all page types, cron upgraded from weekly to daily.

### Key files
- `tools/gsc_indexation_check.py` — URL Inspection API poller
- `tools/creditdoc_daily_gsc_queue.py` — daily queue builder + emailer
- `data/creditdoc.db` table `indexation_status` — verdict store

### Verification
```bash
python3 -c "
import sqlite3; con=sqlite3.connect('data/creditdoc.db')
r=con.execute('SELECT verdict, COUNT(*) FROM indexation_status GROUP BY verdict').fetchall()
print(dict(r))
"
```

---

## Deploy Script

**Name:** CreditDoc Deploy Pipeline
**Status:** LIVE (created 2026-05-14)
**System:** `deploy.sh` — build + deploy + cache purge + verify

### What it does
Single command to deploy CreditDoc: builds Astro, deploys to Cloudflare Workers via wrangler, purges Cloudflare CDN cache, then verifies homepage + CSS return 200. Prevents stale-CSS breakage where new HTML references new asset hashes but CDN serves old cached HTML.

### Usage
```bash
cd /srv/BusinessOps/creditdoc && ./deploy.sh
```

### Why it exists
2026-05-14: deployed quiz meta changes via bare `wrangler deploy` without cache purge. Cloudflare CDN served stale HTML referencing old CSS filenames. Entire site appeared broken (unstyled, giant purple logo) until manual cache purge. deploy.sh prevents this by always purging after deploy.

### Key files
- `deploy.sh` — the script (chmod +x)

---

<!-- Add new glossary entries above this line -->
