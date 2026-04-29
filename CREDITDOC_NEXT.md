# CreditDoc — NEXT (RULE 10 handoff, last updated 2026-04-29 13:14 UTC)

## What needs Jammi greenlight, in order

All five items below are NOT-IN-LOOP — they touch the live DB or a production tool, so /loop directive "no live database or system" forbids them. Each block has the exact command to run after greenlight. Run them in order.

### 1. Apply Stage A.2 backfill — wellness + comparisons + brands (303 rows)

```bash
cd /srv/BusinessOps/creditdoc
python3 tools/creditdoc_db_backfill_a2_content.py --apply --i-have-jammi-greenlight
```

Pre-flight refuses if any of the 3 tables is non-empty. Loads CSVs already on disk at `tmp_a2_csv/{wellness,comparisons,brands}.csv`.

Post-apply spot-check (3 PostgREST GETs, anon key in `tools/.supabase-creditdoc.env`):
```bash
SUPA_URL=$(grep ^SUPABASE_URL tools/.supabase-creditdoc.env | cut -d= -f2)
ANON=$(grep ^SUPABASE_ANON_KEY tools/.supabase-creditdoc.env | cut -d= -f2)
curl -s "$SUPA_URL/rest/v1/wellness_guides?limit=1" -H "apikey: $ANON" | head -c 200
curl -s "$SUPA_URL/rest/v1/comparisons?limit=1" -H "apikey: $ANON" | head -c 200
curl -s "$SUPA_URL/rest/v1/brands?limit=1" -H "apikey: $ANON" | head -c 200
```

### 2. Apply Stage A.3 — states + categories + glossary_terms (139 rows)

DDL artifact: `supabase/migrations/2026-04-29_cdm_rev_a3_states_categories_glossary.sql`. Two steps:

```bash
# 2a. Apply DDL (Supabase MCP execute_sql or psql)
psql "$DB_URL" -f supabase/migrations/2026-04-29_cdm_rev_a3_states_categories_glossary.sql

# 2b. Backfill
python3 tools/creditdoc_db_backfill_a3_content.py --apply --i-have-jammi-greenlight
```

### 3. Apply Stage A.4 — blog + listicles + answers + specials (77 rows)

```bash
psql "$DB_URL" -f supabase/migrations/2026-04-29_cdm_rev_a4_blog_listicles_answers_specials.sql
python3 tools/creditdoc_db_backfill_a4_content.py --apply --i-have-jammi-greenlight
```

### 4. Set Pages preview env: `REVALIDATE_TOKEN`

```bash
TOKEN=$(openssl rand -hex 32)
echo "Token (save in 1Password as 'CreditDoc Revalidate Token'): $TOKEN"
# Set on cdm-rev-hybrid preview env:
curl -X PATCH "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT/pages/projects/creditdoc" \
  -H "X-Auth-Key: $CF_GLOBAL_KEY" -H "X-Auth-Email: $CF_EMAIL" \
  -H "Content-Type: application/json" \
  -d "{\"deployment_configs\":{\"preview\":{\"env_vars\":{\"REVALIDATE_TOKEN\":{\"value\":\"$TOKEN\",\"type\":\"secret_text\"}}}}}"
# Then redeploy preview so the secret is bound:
npx wrangler pages deploy dist --project-name creditdoc --branch cdm-rev-hybrid
```

### 5. Phase 2.3 — wire `tools/creditdoc_db.py` → POST /api/revalidate

Modify `tools/creditdoc_db.py` so every successful `update_lender / update_brand / update_wellness / update_comparison / update_blog / update_listicle / update_answer / update_special` writer also POSTs to the preview endpoint:

```python
import os, requests
TOKEN = os.environ.get("REVALIDATE_TOKEN")
def _ping_revalidate(type_: str, slug: str) -> None:
    if not TOKEN:
        return  # Soft-fail in dev
    try:
        requests.post(
            "https://cdm-rev-hybrid.creditdoc.pages.dev/api/revalidate",
            headers={"x-revalidate-token": TOKEN, "content-type": "application/json"},
            json={"type": type_, "slug": slug},
            timeout=8,
        )
    except Exception:
        pass  # Non-blocking. Cache busts via updated_at regardless.
```

Sequence: writer commits row → trigger bumps `updated_at` → Python pings `/api/revalidate` → endpoint pre-warms canonical URL → next user request hits a HIT not a MISS.

---

## After all 5 greenlights land

| Acceptance criterion | How to verify |
|---|---|
| OBJ-1 GREEN end-to-end | Edit a lender row → next request to `/review/<slug>/` on the preview shows new content within 10s globally |
| `/review/[slug]` HTML diff <0.1% vs Vercel | Run `tools/cdm_rev_html_diff.sh` against 20 sample slugs (script not yet written — list it here when written) |
| Build still <30s | `time npx astro build` on a clean checkout (was 372s before A.1) |
| Worker bundle <500 KB gzipped | `find dist/_worker.js -name '*.mjs' -exec cat {} + \| gzip -c \| wc -c` (currently 285 KB) |

Once all four are green, schedule the production cutover (Phase 6 — DNS flip from Vercel to CF Pages production branch). That step needs a separate greenlight + 24h notice.

---

## What NOT to do

- Do NOT touch `arch-overhaul` branch (parallel-window territory).
- Do NOT push `cdm-rev-hybrid` to remote without explicit "push it" from Jammi.
- Do NOT redo `/privacy/`, `/terms/`, `/disclosure/` — they are LIVE and 200 OK.
- Do NOT call `--apply` on any backfill script without `--i-have-jammi-greenlight`.
- Do NOT modify `tools/creditdoc_db.py` (production tool) before Phase 2.3 greenlight.
- Do NOT set `REVALIDATE_TOKEN` on Vercel — only on the CF Pages preview.
- Do NOT auto-flip DNS. Production cutover is a separate explicitly-approved step.

---

## Reference: branch state at handoff

- Working branch: `cdm-rev-hybrid` (15 commits ahead of `main`, NOT pushed)
- Latest commit: `8c8c790806` — A.3 + A.4 artifacts
- `main`: untouched
- `arch-overhaul`: parallel-window, off-limits
- Live `creditdoc.co`: serving previous Vercel static build, untouched

Re-check verifier any time:
```bash
python3 tools/verify_strategic_objectives.py
```
