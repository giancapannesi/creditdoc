# CreditDoc Persistence Architecture

**Created:** 2026-04-08
**Last updated:** 2026-04-09
**Status:** Phase 1-2 complete (DB + protection + guardian). Phase 3 pending (script rewiring).

## The Problem This Solves

Before this architecture, CreditDoc stored all data in 26,698 individual JSON files inside `src/content/lenders/`. Every deploy was `git add -A` followed by commit and push. This meant:

- Any script could overwrite any profile
- Logos disappeared when scripts regenerated files without preserving `logo_url`
- Protected FA profiles got corrupted by rogue batch scripts
- Blog posts were lost when scripts rewrote `blog-posts.json`
- There was no audit trail of who changed what
- There was no way to recover from mistakes without a full restore

## The Core Principle

**CreditDoc is a content archive. Nothing gets lost.**

- Automation can **ADD** (empty → value) freely
- Automation cannot **WIPE** (value → empty) — ever
- Automation cannot silently **REPLACE** (value → different value) — must use `force=True`
- Founder can do **anything** — improvements always allowed
- Everything is logged to `audit_log` — so changes are visible and reversible

This lets the system build and improve daily while preventing accidents.

## Architecture

```
                    ┌──────────────────────────────┐
                    │  SQLite DB (source of truth) │
                    │    data/creditdoc.db         │
                    └──────────┬───────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
    ┌───▼────┐           ┌─────▼─────┐          ┌────▼────┐
    │ Writer │           │  Guardian │          │  Sync   │
    │  API   │           │  (hourly) │          │  (2 AM) │
    └───┬────┘           └─────┬─────┘          └────┬────┘
        │                      │                      │
        │ Scripts write        │ Heals drift          │ Imports JSON
        │ via update_lender()  │ Restores wipes       │ changes to DB
        │ (protection enforced)│ Restores logos       │
        │                      │ Restores content     │
        │                      │                      │
        └───────── JSON files in src/content/ ───────┘
                               │
                               ▼
                       ┌──────────────┐
                       │  Astro build │
                       │  + git push  │
                       └──────────────┘
```

## Persistence Rules

### Field Categories

**PERSISTENT FIELDS** — editorial content. Protected by default:
- `description_short`, `description_long`, `meta_description`
- `diagnosis`, `typical_results_timeline`
- `pros`, `cons`, `best_for`, `services`, `similar_lenders`
- `rating_breakdown`
- `pricing`
- `logo_url`
- `company_info`
- `affiliate_url`, `affiliate_program`

**TRANSIENT FIELDS** — state tracking. Free to update:
- `last_updated`, `last_engine_run`, `qc_passed_at`
- `processing_status`, `enrichment_attempts`, `has_been_enriched`
- `quality_score`, `review_status`, `no_index`
- `website_url`, `phone`, `address`, `contact`
- `google_rating`, `google_reviews_count`
- `cfpb_data`, `bbb_data`, `rating`
- `states_served`, `cities_served`

### Three-Level Protection

| Scenario | Default (no force) | `force=True` | `updated_by='founder'` |
|----------|:------------------:|:------------:|:----------------------:|
| SET empty field (None → value) | Allowed | Allowed | Allowed |
| REPLACE populated field (A → B) | **Blocked** | Allowed | Allowed |
| WIPE populated field (A → empty) | **Blocked** | **Blocked** | Allowed |
| Update transient field | Allowed | Allowed | Allowed |
| Any write to protected profile | **Blocked** (raises ProtectedProfileError) | **Blocked** | Allowed |

**Why:** This prevents accidents (wipes, silent overwrites) while still allowing daily improvements. Scripts that want to make improvements must declare intent via `force=True`. Founder retains full control.

### Protected Profiles (FA)

195 founder-approved profiles in `data/protected_profiles.json` are flagged `is_protected=1`. ANY non-founder write raises `ProtectedProfileError`. The Guardian additionally ensures their JSON files match the DB exactly — any drift is healed by overwriting the JSON.

## Components

### 1. Database — `data/creditdoc.db`

SQLite with WAL mode. 165 MB. Schema:

| Table | Purpose | Rows (current) |
|-------|---------|----------------|
| `lenders` | All lender profiles (replaces 26,698 JSON files) | 26,698 |
| `blog_posts` | Blog articles | 25 |
| `comparisons` | Comparison pages | 90 |
| `wellness_guides` | Wellness guide content | 81 |
| `listicles` | Listicle/money pages | 18 |
| `categories` | Category definitions | 17 |
| `logos` | Logo file tracking with SHA256 hashes | 8,191 |
| `audit_log` | Every field change logged | growing |
| `builds` | Build/export history | growing |
| `metadata` | DB state (schema version, timestamps) | system |

### 2. Writer API — `tools/creditdoc_db.py`

```python
from creditdoc_db import CreditDocDB

db = CreditDocDB()

# READ
lender = db.get_lender('credit-saint')          # full profile + metadata
data = db.get_lender_data('credit-saint')        # just the JSON data
stats = db.get_stats()

# WRITE (auto-logged to audit_log)
result = db.update_lender('some-lender', {
    'cfpb_data': {...},
    'last_updated': '2026-04-09'
}, updated_by='cfpb_enricher', reason='CFPB data update')

# Result: {'changed': 2, 'unchanged': 0, 'blocked_wipe': [], 'blocked_replace': []}

# IMPROVEMENT (force=True)
db.update_lender('some-lender', {
    'description_long': 'Improved text...'
}, updated_by='editor', reason='Content improvement', force=True)

# FOUNDER (no protection)
db.update_lender('credit-saint', {...}, updated_by='founder')

# CREATE
db.create_lender('new-slug', {...}, updated_by='discovery')

# CONTENT
db.add_blog_post({...}, updated_by='blog_generator')
db.add_comparison({...}, updated_by='comparison_gen')
db.add_wellness_guide({...}, updated_by='wellness_gen')
db.add_listicle({...}, updated_by='editor')

# LOGOS
db.update_logo('slug', '/logos/slug.png', file_hash, updated_by='logo_fetcher')
missing = db.get_lenders_missing_logos(limit=100)

# EXPORT (DB → JSON for Astro build)
count = db.export_changed_lenders()   # only changed since last export
count = db.export_all_lenders()       # full rebuild
db.export_all_content()               # blog, comparisons, wellness, listicles, categories

# INTEGRITY
result = db.check_json_integrity('credit-saint')  # compare DB vs file checksum
```

**CLI:**
```bash
python3 tools/creditdoc_db.py stats              # database stats
python3 tools/creditdoc_db.py get <slug>          # inspect a profile
python3 tools/creditdoc_db.py audit [slug]        # audit log
python3 tools/creditdoc_db.py logo-stats          # logo coverage
python3 tools/creditdoc_db.py export-changed      # export changed profiles
python3 tools/creditdoc_db.py export-all          # full export
```

### 3. Daily Sync — `tools/creditdoc_db_sync.py`

**Cron:** 07:00 UTC daily (2:00 AM EST)
**Purpose:** Bridge script that syncs JSON file changes back to the DB.

While Phase 3 is in progress (rewiring scripts to use the DB API directly), legacy scripts still write to JSON files. This sync catches those changes and pulls them into the DB with protection enforcement.

**How it works:**
1. Finds JSON files modified since `last_sync_at` (mtime check)
2. For each changed file, computes checksum and compares to DB
3. Calls `update_lender()` — protection rules apply automatically
4. Protected profile drift is LOGGED but NOT applied to DB (Guardian heals)
5. Wipes and replaces to persistent fields are BLOCKED (logged to audit)
6. Records sync in `builds` table

**Commands:**
```bash
python3 tools/creditdoc_db_sync.py              # Incremental sync
python3 tools/creditdoc_db_sync.py --dry-run    # Preview changes
python3 tools/creditdoc_db_sync.py --full       # Check ALL files (slow)
python3 tools/creditdoc_db_sync.py --since <ts> # Force sync files newer than ts
python3 tools/creditdoc_db_sync.py --status     # Show last sync time
```

**Max drift:** 24 hours
**Manual trigger:** Safe anytime, idempotent
**Performance:** ~5 seconds for a day's changes, ~0.2s if nothing changed

### 4. Guardian — `tools/creditdoc_guardian.py`

**Cron:** 5 minutes past every hour (lightweight, runs hourly)
**Purpose:** Active persistence enforcer. Heals drift that the passive sync can't.

**Four responsibilities:**

#### 4.1 Protected Profile Healing
For each of the 195 protected profiles:
- Compares JSON file checksum to DB checksum
- If drift detected, **overwrites JSON with DB version**
- Logs the heal to `audit_log` with `field_changed='HEALED_FROM_DB'`

#### 4.2 Logo Persistence
For each file in `public/logos/`:
- Ensures the corresponding lender's `logo_url` = `/logos/{slug}.png`
- If DB has wrong/missing value, restores it (uses `force=True`)
- If JSON file has wrong/missing value, restores it
- Logos never disappear once found

#### 4.3 Persistent Field Healing
For each lender JSON file modified since last guardian run:
- Checks every persistent field against the DB
- If a field was **wiped** (DB has value, file is empty), restores from DB
- If a field was **shrunken** (file value is <50% of DB length), restores from DB
- Writes restored fields back to JSON
- Logs each restoration to `audit_log`

#### 4.4 Content Table Completeness
For each content JSON file (blog, comparisons, wellness, listicles, categories):
- Compares row count: DB vs file
- If file has **fewer** rows than DB, **regenerates file from DB**
- This prevents scripts that rewrite content files with only their own additions from deleting everything else

**Commands:**
```bash
python3 tools/creditdoc_guardian.py              # Run all checks (hourly)
python3 tools/creditdoc_guardian.py --dry-run    # Preview without fixing
python3 tools/creditdoc_guardian.py --report     # Same as --dry-run
python3 tools/creditdoc_guardian.py --protected-only  # Only protected profiles
python3 tools/creditdoc_guardian.py --logos-only      # Only logos
python3 tools/creditdoc_guardian.py --persistent-only # Only persistent fields
python3 tools/creditdoc_guardian.py --content-only    # Only content tables
```

**Performance:**
- First run: ~7 seconds (full scan of 26,698 files)
- Subsequent runs: ~1-2 seconds (only files modified since last run)

### 5. Build Script — `tools/creditdoc_build.py`

**Purpose:** Incremental export from DB → JSON → git commit → push.

Replaces the old dangerous pattern of `git add -A src/content/lenders/`.

```bash
python3 tools/creditdoc_build.py --status              # Show what would be exported
python3 tools/creditdoc_build.py --export-only         # Export changes, no git
python3 tools/creditdoc_build.py --export-and-commit   # Export + commit changed files
python3 tools/creditdoc_build.py --export-and-push     # Export + commit + push
python3 tools/creditdoc_build.py --full-export         # Export ALL profiles (rebuilds)
python3 tools/creditdoc_build.py --export-content      # Only content tables
```

Only files where `updated_at > exported_at` are written. Only changed files are staged for commit.

### 6. Rolling DB Backups — `tools/creditdoc_db_backup.py`

**Cron:** 06:50 UTC daily (10 min before sync, 1:50 AM EST)
**Purpose:** Daily rotating backup of the SQLite database.

**Retention:**
- 7 daily backups (one per day)
- 4 weekly backups (from Sundays)
- 12 monthly backups (from the 1st of each month)

**How it works:**
- Uses SQLite `.backup` API (atomic, doesn't block writes)
- Compresses with gzip (165 MB → 31 MB, 81% reduction)
- Runs integrity check after each backup
- Deletes invalid backups automatically
- Rotates old backups per retention policy

**Location:** `/srv/BusinessOps/backups/creditdoc_db/`
**Max backup age:** 24 hours (guaranteed by daily cron)

```bash
python3 tools/creditdoc_db_backup.py              # Run backup + rotate
python3 tools/creditdoc_db_backup.py --list        # List all backups
python3 tools/creditdoc_db_backup.py --stats       # Show backup stats
python3 tools/creditdoc_db_backup.py --verify <f>  # Verify a backup file
```

### 7. Pre-Commit Hook — `.git/hooks/pre-commit`

Blocks git commits that modify protected profile JSON files directly. Bypass options:
- Emergency: `git commit --no-verify`
- DB-approved: `CREDITDOC_SKIP_PROTECTION=1 git commit ...` (used by build script)

### 8. Migration Script — `tools/creditdoc_migrate_to_db.py`

One-time (and re-runnable) import of JSON → DB.

```bash
python3 tools/creditdoc_migrate_to_db.py --create-schema   # Create tables
python3 tools/creditdoc_migrate_to_db.py --migrate-all     # Import everything
python3 tools/creditdoc_migrate_to_db.py --migrate-lenders # Just lenders
python3 tools/creditdoc_migrate_to_db.py --migrate-content # Just content
python3 tools/creditdoc_migrate_to_db.py --migrate-logos   # Just logos
python3 tools/creditdoc_migrate_to_db.py --verify          # Integrity check
```

## Cron Schedule

| Time (UTC) | Time (EST) | Job | Purpose |
|------------|------------|-----|---------|
| 05:00 + 00:00 | 5 past every hour | `creditdoc_guardian.py` | Heal drift, enforce persistence |
| 06:50 | 1:50 AM | `creditdoc_db_backup.py` | Rotating DB backup |
| 07:00 | 2:00 AM | `creditdoc_db_sync.py` | Incremental JSON → DB sync |

## Backup Strategy

### 1. One-time file backup (pre-migration)
- **Location:** `/srv/BusinessOps/backups/creditdoc_full_2026-04-08/` (58 MB)
- **Contents:** All 26,698 JSON files, 6,879 logos, all content, config, git HEAD
- **Restore:** `bash backups/creditdoc_full_2026-04-08/RESTORE.sh`

### 2. Rolling DB backups (daily)
- **Location:** `/srv/BusinessOps/backups/creditdoc_db/`
- **Retention:** 7 daily + 4 weekly + 12 monthly = up to 23 backups
- **Max age:** 24 hours
- **Restore:** `gunzip -c <backup>.db.gz > data/creditdoc.db`

## Files Reference

| File | Purpose | Size |
|------|---------|------|
| `data/creditdoc.db` | SQLite database (source of truth) | 165 MB |
| `data/protected_profiles.json` | List of 195 founder-protected slugs | 6 KB |
| `tools/creditdoc_db.py` | Writer API with persistent field enforcement | 36 KB |
| `tools/creditdoc_db_sync.py` | Daily JSON → DB incremental sync | 13 KB |
| `tools/creditdoc_db_backup.py` | Daily DB backup with rotation | 8 KB |
| `tools/creditdoc_guardian.py` | Hourly drift healer | 14 KB |
| `tools/creditdoc_build.py` | Incremental build + git commit | 11 KB |
| `tools/creditdoc_migrate_to_db.py` | JSON → DB migration | 20 KB |
| `.git/hooks/pre-commit` | Blocks edits to protected profiles | 2 KB |
| `PERSISTENCE.md` | This document | — |

## Audit Trail

Every write is logged to `audit_log` with:
- `slug` — which profile
- `field_changed` — which field (or `BLOCKED_WIPE:field`, `BLOCKED_REPLACE:field`, `HEALED_FROM_DB`, `RESTORED:field`)
- `old_value` — what it was (truncated to 500 chars)
- `new_value` — what it became
- `changed_by` — who made the change (`engine`, `founder`, `json_sync`, `guardian`, etc.)
- `changed_at` — ISO timestamp
- `reason` — optional explanation

**View audit log:**
```bash
python3 tools/creditdoc_db.py audit              # Last 20 entries
python3 tools/creditdoc_db.py audit credit-saint # Specific profile
sqlite3 data/creditdoc.db "SELECT * FROM audit_log WHERE field_changed LIKE 'BLOCKED%'" # All blocked attempts
```

## How This Prevents the Failures That Motivated This Build

| Old Failure | New Protection |
|-------------|----------------|
| Logo disappearing after engine run | Persistent field check blocks wipe; Guardian restores from DB |
| Protected FA profile overwritten | `is_protected=1` blocks all non-founder writes; Guardian heals JSON |
| Blog posts lost when script rewrites `blog-posts.json` | Append-only API; Guardian regenerates file from DB if shorter |
| Wellness guides deleted | Same append-only protection |
| Meta descriptions wiped | Persistent field wipe protection |
| Internal links (money keywords) erased | `similar_lenders` is a persistent field; wipes blocked |
| Full `git add -A` clobbering everything | Incremental export only writes changed files |
| No audit trail of changes | Every write logged to `audit_log` |
| No recovery from mistakes | DB backups every 24 hours, 30-day rolling window |
| Claude recreating existing tools | Documentation makes existing tools discoverable |

## Current State (Verified 2026-04-09)

- **DB:** 165 MB, 26,698 lenders, 25 blog posts, 90 comparisons, 81 wellness, 18 listicles, 17 categories, 8,191 logos
- **Protected profiles:** 195, all integrity-verified
- **Audit entries:** growing (test runs + logo pipeline sync captured)
- **Backups:** 1 (creditdoc_daily_2026-04-09.db.gz, 31.3 MB)
- **Last sync:** 2026-04-09T08:37:53Z
- **Last guardian run:** 2026-04-09T08:48:00Z
- **Drift check:** all clean

## What's Next (Phase 3)

Phase 3 will rewire existing scripts to use the DB API directly instead of writing to JSON files. This removes the sync bridge entirely.

Scripts to rewire:
1. `creditdoc_autonomous_engine.py` (highest priority — daily enrichment cron)
2. `creditdoc_cfpb.py`
3. `creditdoc_blog.py` / `creditdoc_blog_generator.py`
4. `creditdoc_comparison_generator.py`
5. `creditdoc_wellness_generator.py`
6. `creditdoc_logo_downloader.py`
7. `creditdoc_website_finder.py`
8. `creditdoc_self_healer.py`
9. `calculate_ratings.py`

Each gets rewired one at a time, tested, verified, committed. Reversible per-script.
