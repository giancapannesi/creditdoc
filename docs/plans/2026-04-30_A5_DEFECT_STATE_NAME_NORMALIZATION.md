# A.5 Migration Defect — State Name Normalization

**Discovered:** 2026-04-30 17:15 UTC (iter 23)
**File:** `supabase/migrations/2026-04-30_cdm_rev_a5_state_aggregates.sql`
**Status:** ⚠️ DEFECT — DO NOT APPLY AS-WRITTEN
**Owner:** Jammi (decide normalization approach) + Claude (apply fix)

---

## The defect

A.5 generates `lenders.state_abbr` as:
```sql
state_abbr TEXT GENERATED ALWAYS AS (
  UPPER(NULLIF(TRIM(body_inline->'company_info'->>'state'), ''))
) STORED
```

But `body_inline->'company_info'->>'state'` is **50/50 split** between formats:

| Shape | Rows | Examples |
|---|---|---|
| 2-char abbrev | **8,515** | `CA`, `TX`, `NY` |
| Full name | **8,155** | `California`, `Texas`, `New York` |
| Empty/null | 4,155 | (no state info) |
| **Total** | **20,825** | |

`UPPER()` only normalizes case. It does NOT map "California" → "CA". So after A.5:

- `state_abbr` column would have BOTH `CA` and `CALIFORNIA` for California rows
- `state_lender_counts` MV would emit **two rows for every state** — one per shape
- `/state/[slug]` SSR querying `?state_abbr=eq.CA` would miss 8,155 full-name rows
- `state_city_lender_counts` would similarly fragment

**Impact:** A.5 as-written creates an unusable column. Cutover gate (Phase 1 acceptance) for /state would fail.

---

## Verification

```bash
source /srv/BusinessOps/tools/.supabase-creditdoc.env
PGPASSWORD="$SUPABASE_DB_PASSWORD" psql "$SUPABASE_DB_URL" -tAc "
SELECT
  CASE
    WHEN length(trim(body_inline->'company_info'->>'state')) = 2 THEN '2char_abbrev'
    WHEN length(trim(body_inline->'company_info'->>'state')) > 2 THEN 'full_name'
    ELSE 'other'
  END AS shape,
  count(*)
FROM lenders
WHERE body_inline->'company_info'->>'state' IS NOT NULL
  AND trim(body_inline->'company_info'->>'state') != ''
GROUP BY shape ORDER BY count DESC;
"
# 2char_abbrev | 8515
# full_name    | 8155
```

---

## Fix options (pick one before applying A.5)

### Option 1 — Add a normalization CASE in the migration (recommended)

Replace the `state_abbr` definition with a CASE expression that maps the 50 full names to 2-char abbreviations. Pros: keeps data clean at column level. Cons: 50-row CASE; brittle if a row has a typo ("Calif." etc). Risk: low — generated columns evaluate per row, errors are silent (row gets NULL).

```sql
state_abbr TEXT GENERATED ALWAYS AS (
  CASE UPPER(NULLIF(TRIM(body_inline->'company_info'->>'state'), ''))
    WHEN 'ALABAMA' THEN 'AL'
    WHEN 'ALASKA' THEN 'AK'
    -- ...50 cases...
    WHEN 'WYOMING' THEN 'WY'
    -- 2-char passthrough:
    ELSE UPPER(NULLIF(TRIM(body_inline->'company_info'->>'state'), ''))
  END
) STORED
```

### Option 2 — Pre-normalize body_inline once, then apply A.5 as-written

Runs a one-shot UPDATE that sets `body_inline.company_info.state` to the 2-char abbrev for all 8,155 full-name rows. Then A.5 applies cleanly. Pros: data canonical. Cons: mutates jsonb across 8,155 rows; needs RLS bypass + audit log entry; slow.

### Option 3 — Use a normalization function

Create a `normalize_state_abbr(text)` immutable function and reference it from the generated column. Pros: reusable; testable. Cons: adds a function dependency; Postgres requires function be IMMUTABLE for STORED generated columns.

```sql
CREATE OR REPLACE FUNCTION normalize_state_abbr(s text)
RETURNS text LANGUAGE sql IMMUTABLE PARALLEL SAFE AS $$
  SELECT CASE UPPER(NULLIF(TRIM(s), ''))
    WHEN 'ALABAMA' THEN 'AL' /*…*/ END
$$;
```

---

## Recommended path

**Option 1** — single-file migration update, no separate UPDATE pass, idempotent generated column.

**Action:** rewrite `supabase/migrations/2026-04-30_cdm_rev_a5_state_aggregates.sql` with the 50-state CASE inside the `state_abbr` GENERATED column, then re-run pre-flight smoke (`tools/cdm_rev_snapshot_counts.py`) and confirm `state_lender_counts` returns ~50 rows, not ~100.

---

## Why this matters now

- A.5 is a **Phase 6 cutover pre-flight gate** (`docs/plans/2026-04-30_PHASE_6_CUTOVER_PLAYBOOK.md` row 3).
- Applying broken A.5 → cutover gate fails → cutover blocked.
- Applying correct A.5 → cutover unblocked.
- This is hygiene before going live, not a blocker for the CF Pages deploy itself.

---

## Status

- **Defect identified:** ✅ DONE 2026-04-30 17:15 UTC (iter 23)
- **Fix selected:** 🟡 RECOMMENDED Option 1 — Jammi to confirm
- **v2 migration rewritten:** ✅ DONE 2026-04-30 17:46 UTC (iter 24) — `supabase/migrations/2026-04-30_cdm_rev_a5_state_aggregates_v2.sql`
- **v2 CASE validated against prod (read-only):** ✅ DONE 2026-04-30 17:46 UTC
  - Distinct `state_abbr` values: **60** (50 states + DC + 9 territories/garbage codes), down from 103 raw shapes
  - Texas correctly merges: full-name "Texas" 1,246 + abbrev "TX" 973 → **TX = 2,219**
  - California correctly merges: 1,073 + 616 → **CA = 1,689**
  - Garbage codes (LL/ST/HO/US/FM/PM) pass through harmlessly (3+2+1+1+1+1 = 9 rows total, won't match real /state queries)
- **Migration applied:** ⬜ TODO — awaits Jammi confirm of Option 1
- **/state SSR ships:** ⬜ TODO (post-A.5 apply)

**Iter 23 conclusion:** caught the defect before applying. RULE 4 (no stupid shit) prevented a bad migration to prod. Documented for next iter.

**Iter 24 conclusion:** v2 migration written + read-only validated. Distribution confirms CASE produces clean 60-value column (Texas 2,219, California 1,689, etc.). Apply is now a single `psql` command once Jammi approves.
