# CreditDoc Project — Claude Instructions

**CRITICAL: Read `AGENT_PROTOCOL.md` before making any changes to this project.**

## THE RULE

CreditDoc uses a SQLite database at `data/creditdoc.db` as the single source of truth.
**Do not write directly to JSON files in `src/content/`.** Use the DB API.

```python
from tools.creditdoc_db import CreditDocDB
with CreditDocDB() as db:
    db.update_lender(slug, fields, updated_by='your_script_name')
```

## Why

Before this system existed, scripts overwrote each other's work. Logos disappeared.
Protected FA profiles got corrupted. Blog posts vanished. The founder spent weeks
rebuilding lost content.

The DB fixes this. But only if you use it.

## Protection Rules (Enforced Automatically)

| Scenario | Default | `force=True` | `updated_by='founder'` |
|----------|:---:|:---:|:---:|
| SET empty → value | ✅ | ✅ | ✅ |
| REPLACE value → different | ❌ | ✅ | ✅ |
| WIPE value → empty | ❌ | ❌ | ✅ |
| Protected FA profile (195) | ❌ | ❌ | ✅ |

**Persistent fields** (protected from wipes/silent replaces):
`description_short`, `description_long`, `meta_description`, `diagnosis`,
`typical_results_timeline`, `pros`, `cons`, `best_for`, `services`,
`similar_lenders`, `rating_breakdown`, `pricing`, `logo_url`, `company_info`,
`affiliate_url`, `affiliate_program`

**Transient fields** (update freely):
`last_updated`, `processing_status`, `has_been_enriched`, `quality_score`,
`website_url`, `phone`, `address`, `cfpb_data`, `google_rating`, etc.

## Safety Nets (All Automatic)

- **Guardian** runs hourly and heals any drift
- **Sync** runs daily 07:00 UTC and pulls JSON changes to DB
- **Backup** runs daily 06:50 UTC, max 24-hour rollback
- **Pre-commit hook** blocks direct commits to protected profile JSONs
- **Audit log** tracks every change with who/when/what/old/new

## Quick Commands

```bash
# Check state
python3 tools/creditdoc_db.py stats
python3 tools/creditdoc_db.py get <slug>
python3 tools/creditdoc_db.py audit [slug]

# Heal drift
python3 tools/creditdoc_guardian.py --dry-run  # Preview
python3 tools/creditdoc_guardian.py            # Apply

# Backup
python3 tools/creditdoc_db_backup.py --list

# Export DB → JSON for build
python3 tools/creditdoc_build.py --status
python3 tools/creditdoc_build.py --export-only
```

## Files You Need To Know

| File | Purpose |
|------|---------|
| `AGENT_PROTOCOL.md` | **READ FIRST** — full agent protocol with examples |
| `PERSISTENCE.md` | Full architecture + rationale + cron schedule |
| `data/creditdoc.db` | SQLite database (source of truth) |
| `data/protected_profiles.json` | 195 FA slugs that can't be auto-edited |
| `tools/creditdoc_db.py` | Writer API |
| `tools/creditdoc_guardian.py` | Drift healer (hourly) |
| `tools/creditdoc_db_sync.py` | Daily sync (07:00 UTC) |
| `tools/creditdoc_db_backup.py` | Daily backup (06:50 UTC) |
| `tools/creditdoc_build.py` | Incremental DB → JSON export |
| `CREDITDOC_MASTER_STRATEGY.md` | SEO/content/affiliate strategy |

## What You Will Break If You Don't Follow This

1. **Logos disappear** — scripts regenerate profiles without `logo_url`. Guardian will restore them, but your script wastes time.
2. **FA content gets lost** — protected profiles get clobbered. Guardian restores them, your changes get thrown away.
3. **Blog posts vanish** — scripts write `blog-posts.json` with only their own additions. Guardian regenerates from DB, but the JSON file is briefly wrong.
4. **Protection violations log** — every blocked attempt appears in audit_log. Founder will see and ask why.
5. **Drift spreads** — your changes don't make it to the DB. Next sync or guardian run reverts them.

## The Cardinal Sins

1. **`git add -A src/content/lenders/`** — Use `creditdoc_build.py --export-and-commit`
2. **Direct JSON write to protected profiles** — Use founder override or don't touch
3. **Bulk operations without founder approval** — Founder directive: NO bulk changes ever
4. **Rebuilding existing tools** — There are 37+ creditdoc_*.py tools already. Check first.
5. **Rewriting SEO content in the last 7 days** — Google needs measurement time

## Read The Memory

Before any non-trivial CreditDoc task:
1. Read `/root/.claude/projects/-srv-BusinessOps/memory/lending_directory.md`
2. Read `/root/.claude/projects/-srv-BusinessOps/memory/creditdoc_enrichment_template.md`
3. Read `/root/.claude/projects/-srv-BusinessOps/memory/creditdoc_monetization_phases.md`
4. Read `/root/.claude/projects/-srv-BusinessOps/memory/creditdoc_directory_strategy.md`

These have the business context, affiliate status, KE-verified keywords, FA profile status,
and everything else you need to do good work here.
