# CreditDoc Agent Protocol

**Mandatory reading for any agent (Claude, SEO, content, scripts, or any automation) that touches CreditDoc.**

**Last updated:** 2026-04-09
**Status:** LIVE — All rules enforced by DB API + Guardian + pre-commit hook

---

## TL;DR

CreditDoc is a content archive. **Nothing gets lost.** All writes go through the SQLite database at `data/creditdoc.db`. Direct edits to JSON files are a mistake — they will either be blocked, reverted by the Guardian, or overwritten on the next sync.

Before modifying anything, read `PERSISTENCE.md`.

---

## The 5 Laws

### Law 1: DB is the source of truth
All CreditDoc data lives in `data/creditdoc.db`:
- `lenders` — 26,698 lender profiles (replaces the old `src/content/lenders/*.json` files)
- `blog_posts` — 25 blog articles (replaces `src/content/blog-posts.json`)
- `comparisons` — 90 comparison pages
- `wellness_guides` — 81 financial wellness guides
- `listicles` — 18 money pages
- `categories` — 17 category definitions
- `logos` — 8,191 logo files with SHA256 hashes
- `audit_log` — every write logged (who, when, what, old→new)

JSON files in `src/content/` are **exports from the DB**, not the source. Astro's build reads them, but they get regenerated from the DB.

### Law 2: Use the writer API, not file writes
```python
# CORRECT
from tools.creditdoc_db import CreditDocDB
db = CreditDocDB()
db.update_lender('some-lender', {'cfpb_data': {...}}, updated_by='your_script_name')
```

```python
# WRONG — will be reverted by Guardian within 1 hour
with open('src/content/lenders/some-lender.json', 'w') as f:
    json.dump(data, f)
```

If you MUST write to JSON (e.g., during the Phase 3 transition), the Guardian and sync will detect the drift and heal it. But the correct path is the API.

### Law 3: Persistent fields cannot be wiped or silently replaced
The 16 persistent fields contain the editorial work that drives SEO and affiliate revenue:

```
description_short, description_long, meta_description,
diagnosis, typical_results_timeline,
pros, cons, best_for, services, similar_lenders,
rating_breakdown, pricing, logo_url,
company_info, affiliate_url, affiliate_program
```

**Rules (enforced by `update_lender()` automatically):**

| Action | Default script | `force=True` | `updated_by='founder'` |
|--------|:---:|:---:|:---:|
| SET empty → value (new content) | ✅ allowed | ✅ | ✅ |
| REPLACE value → different value | ❌ blocked | ✅ | ✅ |
| WIPE value → empty | ❌ blocked | ❌ blocked | ✅ |

**If your script needs to improve existing content,** use `force=True`:
```python
db.update_lender(slug, {'description_long': new_text},
                 updated_by='my_enricher',
                 reason='Improved with CFPB data',
                 force=True)
```

This is logged to `audit_log` so the founder can review and roll back if needed.

### Law 4: FA profiles (195) are locked
The 195 Founder Approved profiles listed in `data/protected_profiles.json` reject ALL non-founder writes. The API raises `ProtectedProfileError` if any script tries to modify them.

**To update a protected profile, you must have founder authorization AND use `updated_by='founder'`:**
```python
db.update_lender('credit-saint', {...}, updated_by='founder', reason='Founder approved update')
```

If you're not sure whether a profile is protected:
```python
if db.is_protected(slug):
    # handle differently
```

### Law 5: Transient fields are free
You can update these freely without force or founder:
- State: `processing_status`, `has_been_enriched`, `review_status`, `no_index`, `quality_score`
- Timestamps: `last_updated`, `last_engine_run`, `qc_passed_at`, `enrichment_attempts`
- Location: `website_url`, `phone`, `address`, `contact`, `google_rating`, `cities_served`, `states_served`
- Additive: `cfpb_data`, `bbb_data`, `rating` (recalculated)

---

## API Cheat Sheet

```python
from tools.creditdoc_db import CreditDocDB

with CreditDocDB() as db:
    # READ
    lender = db.get_lender('credit-saint')        # full row with metadata
    data = db.get_lender_data('credit-saint')      # just the data dict
    exists = db.lender_exists('some-slug')
    protected = db.is_protected('credit-saint')
    stats = db.get_stats()

    # WRITE (returns dict: {changed, unchanged, blocked_wipe, blocked_replace})
    result = db.update_lender('some-lender', {'key': 'value'},
                               updated_by='my_script',
                               reason='Why')

    # FORCE UPDATE (for legitimate improvements to persistent fields)
    result = db.update_lender('some-lender', {'description_long': 'new'},
                               updated_by='enricher',
                               reason='Improved',
                               force=True)

    # STATUS CHANGE (transient — no force needed)
    db.update_lender_status('some-lender', 'ready_for_index', updated_by='engine')

    # CREATE NEW
    db.create_lender('new-slug', data_dict, updated_by='discovery')

    # CONTENT
    db.add_blog_post({'slug': 'my-post', ...}, updated_by='blog_generator')
    db.add_comparison({...}, updated_by='comparison_gen')
    db.add_wellness_guide({...}, updated_by='wellness_gen')
    db.add_listicle({...}, updated_by='editor')

    # LOGOS
    db.update_logo(slug, file_path, file_hash, updated_by='logo_fetcher')
    missing = db.get_lenders_missing_logos(limit=100)

    # QUERIES
    personal_loans = db.get_lenders_by_category('personal-loans')
    pending = db.get_lenders_by_status('pending_approval', limit=100)
    count = db.count_lenders(status='ready_for_index', category='credit-repair')

    # EXPORT (DB → JSON for Astro build)
    changed_count = db.export_changed_lenders()   # incremental
    full_count = db.export_all_lenders()          # full rebuild
    db.export_all_content()                        # content tables
```

---

## CLI Cheat Sheet

```bash
# Database
python3 tools/creditdoc_db.py stats                 # Full stats
python3 tools/creditdoc_db.py get <slug>             # Inspect profile
python3 tools/creditdoc_db.py audit [slug]           # Audit log (last 20)
python3 tools/creditdoc_db.py logo-stats             # Logo coverage
python3 tools/creditdoc_db.py export-changed        # Export changed → JSON
python3 tools/creditdoc_db.py export-all             # Full export

# Sync (manual trigger)
python3 tools/creditdoc_db_sync.py                   # Incremental sync
python3 tools/creditdoc_db_sync.py --dry-run         # Preview
python3 tools/creditdoc_db_sync.py --status          # Last sync time

# Guardian (manual trigger)
python3 tools/creditdoc_guardian.py                  # Heal all drift
python3 tools/creditdoc_guardian.py --dry-run        # Preview what would heal
python3 tools/creditdoc_guardian.py --protected-only # Only FA profiles
python3 tools/creditdoc_guardian.py --logos-only     # Only logos

# Backup
python3 tools/creditdoc_db_backup.py                 # Create backup + rotate
python3 tools/creditdoc_db_backup.py --list          # List all backups
python3 tools/creditdoc_db_backup.py --stats         # Stats

# Build (DB → JSON → git)
python3 tools/creditdoc_build.py --status            # What would be exported
python3 tools/creditdoc_build.py --export-only       # Export only
python3 tools/creditdoc_build.py --export-and-commit # Export + commit
python3 tools/creditdoc_build.py --export-and-push   # Export + commit + push
```

---

## What Gets Enforced Automatically

| Enforcement | Where | What it blocks |
|-------------|-------|----------------|
| `ProtectedProfileError` | `update_lender()` | Any non-founder write to 195 FA profiles |
| `blocked_wipe` | `update_lender()` | Setting persistent field to empty/null |
| `blocked_replace` | `update_lender()` | Changing persistent field without `force=True` |
| Pre-commit hook | `.git/hooks/pre-commit` | Direct git commits to protected profile JSONs |
| Guardian (hourly) | `creditdoc_guardian.py` | Heals drift: restores protected profiles, logos, persistent fields, content tables |
| Sync (daily) | `creditdoc_db_sync.py` | Pulls JSON changes to DB with protection rules |
| Backup (daily) | `creditdoc_db_backup.py` | Max 24-hour rollback window |

---

## Common Agent Tasks — How To Do Them Right

### I want to add CFPB data to a lender
```python
db.update_lender(slug, {'cfpb_data': cfpb_dict}, updated_by='cfpb_script')
# cfpb_data is transient — no force needed
```

### I want to update a lender's phone number
```python
db.update_lender(slug, {'phone': '+1-800-...', 'contact': {...}},
                 updated_by='website_finder')
# phone/contact are transient — no force needed
```

### I want to add a new blog post
```python
post = {
    'slug': 'my-new-post',
    'title': 'My Post',
    'content': '...',
    'status': 'published',
    'publishedAt': '2026-04-09',
    # ... other fields
}
db.add_blog_post(post, updated_by='blog_generator')
```
Blog posts are append-only. Once added, they persist forever.

### I want to add a new lender
```python
data = {
    'slug': 'new-lender-slug',
    'name': 'New Lender',
    'category': 'credit-repair',
    'website_url': 'https://...',
    # ... other fields
}
db.create_lender('new-lender-slug', data, updated_by='discovery_script')
```

### I want to improve a description
```python
# Option A: Get founder approval, then:
db.update_lender(slug, {'description_long': better_text},
                 updated_by='founder',
                 reason='Founder approved improvement')

# Option B: Automated improvement with explicit intent:
db.update_lender(slug, {'description_long': better_text},
                 updated_by='content_improver',
                 reason='Enriched with CFPB data + better structure',
                 force=True)
# This is logged to audit_log — founder can review and roll back
```

### I want to update a logo
```python
# Preferred: use the 2-step pipeline
# 1. scraper/creditdoc_logo_fetcher.py (scrapes website for real logo)
# 2. tools/creditdoc_logo_downloader.py --missing (downloads + DDG/icon.horse fallback)

# Or directly via API after downloading:
db.update_logo(slug,
               file_path='/logos/slug.png',
               file_hash=sha256_of_file,
               source_url='https://...',
               updated_by='logo_script')
# logo_url is persistent, but update_logo handles this correctly
```

### I want to change a lender's status to ready_for_index
```python
db.update_lender_status(slug, 'ready_for_index', updated_by='my_script')
# Transient field — no force needed
```

### I want to see recent changes for a profile
```python
entries = db.get_audit_log(slug='credit-saint', limit=20)
for e in entries:
    print(f"{e['changed_at']} {e['field_changed']} by {e['changed_by']}")
```

---

## What NOT To Do

| ❌ DON'T | ✅ DO INSTEAD |
|----------|---------------|
| `json.dump(data, open('file.json', 'w'))` | `db.update_lender(...)` |
| `git add -A src/content/lenders/` | `python3 tools/creditdoc_build.py --export-and-commit` |
| Overwrite a protected profile's JSON | Use `updated_by='founder'` with founder approval |
| Run bulk scripts across 26,000+ profiles | Stop. Ask the founder. Use `is_protected` + per-profile logic. |
| Delete old rows from `blog_posts` / `comparisons` / etc. | Content tables are append-only. Ask founder. |
| Set a persistent field to empty string | Leave it as-is. Use the API; wipes are blocked. |
| Rebuild existing tools | Check `tools/creditdoc_*.py` first. Dozens of tools already exist. |
| Read 26,698 JSON files into memory | Use `db.get_lenders_by_category()` or `db.conn.execute(...)` — SQLite is fast. |

---

## How To Debug Drift

If something seems off (content changed, logo disappeared, profile corrupted):

```bash
# 1. Check audit log for the profile
python3 tools/creditdoc_db.py audit <slug>

# 2. Check DB vs file integrity
python3 -c "
from tools.creditdoc_db import CreditDocDB
db = CreditDocDB()
print(db.check_json_integrity('<slug>'))
"

# 3. Run guardian dry-run to see all drift
python3 tools/creditdoc_guardian.py --dry-run

# 4. If drift is confirmed, let guardian heal it
python3 tools/creditdoc_guardian.py

# 5. If you need to roll back to a previous DB state
ls /srv/BusinessOps/backups/creditdoc_db/
gunzip -c /srv/BusinessOps/backups/creditdoc_db/creditdoc_daily_YYYY-MM-DD.db.gz > data/creditdoc.db
```

---

## Cron Schedule (Automated Runs)

| Time (UTC) | Time (EST) | Job | Purpose |
|------------|------------|-----|---------|
| :05 every hour | :05 every hour | `creditdoc_guardian.py` | Heal drift, enforce persistence |
| 06:50 | 1:50 AM | `creditdoc_db_backup.py` | Rotating DB backup (max 24h old) |
| 07:00 | 2:00 AM | `creditdoc_db_sync.py` | JSON → DB incremental sync |
| 14:00 | 9:00 AM | `creditdoc_autonomous_engine.py --count 500` | Daily enrichment (legacy, still writes JSON) |
| 19:00 | 2:00 PM | git push cron | Legacy deploy pipeline (being replaced) |

---

## For SEO Agents Specifically

When doing SEO work:
1. **Do not edit JSON files directly.** Use the DB API.
2. **Do not bulk-update profiles** — talk to the founder first.
3. **Persistent fields** — if you're adding meta descriptions, keyword-optimized titles, etc., these ARE protected. Use `force=True` with a clear reason. They will be logged.
4. **Internal linking** — the `similar_lenders` field is persistent. Once set, it's protected. Use `force=True` to add improvements.
5. **The `inline-linker.ts` auto-linker** handles money keyword linking at render time — it reads from `description_long`. To improve internal linking, improve the description text, not hardcoded links.
6. **Sitemap** — regenerated automatically by Astro from DB data. Don't hand-edit.
7. **Schema JSON-LD** — rendered by `src/pages/review/[slug].astro` from DB data. Don't hand-edit HTML.
8. **IndexNow** — submit URLs to crawlers via `tools/gsc_indexing.py` or Bing indexNow endpoint. Don't try to force re-crawl by modifying files.

When you see a problem:
- **Missing meta description** → `db.update_lender(slug, {'meta_description': new}, updated_by='seo_agent', force=True, reason='Added for SEO')`
- **Thin content** → `db.update_lender(slug, {'description_long': expanded}, updated_by='seo_agent', force=True, reason='Expanded thin content')`
- **Broken logo** → Use the 2-step pipeline (fetcher + downloader) OR `db.update_logo(...)`
- **Wrong category** → Transient, no force needed

---

## For Content Agents Specifically

When creating new content:
1. **Blog posts** — use `db.add_blog_post({...}, updated_by='your_name')`. INSERT OR REPLACE, so same slug updates existing.
2. **Comparisons** — use `db.add_comparison(...)`.
3. **Wellness guides** — use `db.add_wellness_guide(...)`.
4. **Listicles** — use `db.add_listicle(...)`.
5. **Do not write to the JSON files directly.** The sync might not catch your changes fast enough, and the Guardian will regenerate the file from the DB if counts drop.

Every content addition should include:
- `slug` (required, used as primary key)
- `title`
- `description` or `excerpt`
- Schema fields (for structured data)
- `publishedAt` / `created_at`
- `status` ('draft' or 'published')

---

## Where Everything Lives

| What | Where |
|------|-------|
| Database | `data/creditdoc.db` |
| Protected profiles list | `data/protected_profiles.json` |
| Writer API | `tools/creditdoc_db.py` |
| Migration script | `tools/creditdoc_migrate_to_db.py` |
| Daily sync | `tools/creditdoc_db_sync.py` |
| Daily backup | `tools/creditdoc_db_backup.py` |
| Hourly guardian | `tools/creditdoc_guardian.py` |
| Build script | `tools/creditdoc_build.py` |
| This protocol | `AGENT_PROTOCOL.md` |
| Full architecture docs | `PERSISTENCE.md` |
| Pre-commit hook | `.git/hooks/pre-commit` |
| Backups | `/srv/BusinessOps/backups/creditdoc_db/` |
| Full file backup | `/srv/BusinessOps/backups/creditdoc_full_2026-04-08/` |

---

## When In Doubt

1. Read `PERSISTENCE.md` (architecture + rationale)
2. Check `python3 tools/creditdoc_db.py stats` (current state)
3. Check `python3 tools/creditdoc_db.py audit <slug>` (recent changes)
4. Run `python3 tools/creditdoc_guardian.py --dry-run` (see any drift)
5. Ask the founder before bulk operations or risky changes

**The system is designed to catch mistakes. But don't rely on that — do it right the first time.**
