-- CDM-REV Phase 5.1.b — state-page aggregates (v2: with state-name normalization)
--
-- v2 supersedes 2026-04-30_cdm_rev_a5_state_aggregates.sql.
--
-- WHY v2 EXISTS:
--   v1's state_abbr was UPPER(NULLIF(TRIM(body_inline->company_info->>state), ''))
--   which only normalizes case. Verified 2026-04-30 17:18 UTC iter 23 against
--   prod (db.pndpnjjkhknmutlmlwsk.supabase.co): body_inline state values are
--   50/50 split between 2-char abbrev (8,515 rows) and full-name (8,155 rows).
--   v1 would produce a state_abbr column with BOTH "CA" and "CALIFORNIA" rows,
--   making state_lender_counts MV emit ~100 rows instead of 50, and breaking
--   /state/[slug] SSR ?state_abbr=eq.CA queries (would miss 8,155 rows globally).
--
--   v2 adds a 50-state CASE expression inside the generated column to map
--   full names → 2-char abbreviations. Already-abbrev rows pass through.
--
-- DEFECT DOC: docs/plans/2026-04-30_A5_DEFECT_STATE_NAME_NORMALIZATION.md
--
-- ROLLBACK:
--   DROP MATERIALIZED VIEW IF EXISTS state_city_lender_counts;
--   DROP MATERIALIZED VIEW IF EXISTS state_lender_counts;
--   DROP FUNCTION IF EXISTS refresh_state_aggregates();
--   ALTER TABLE lenders DROP COLUMN IF EXISTS state_abbr;
--   ALTER TABLE lenders DROP COLUMN IF EXISTS city_norm;

BEGIN;

-- 1. Generated column for state filtering — v2 with 50-state normalization.
--    Full state names map to 2-char USPS abbreviation. DC, PR, GU, VI, AS, MP,
--    FM, MH, PW pass through as-written (already 2-char or short codes).
--    Garbage values (LL, ST, HO, US — typos in source data) pass through
--    upper-cased; they won't match real state queries, harmless.
ALTER TABLE lenders
  ADD COLUMN IF NOT EXISTS state_abbr TEXT
  GENERATED ALWAYS AS (
    CASE UPPER(NULLIF(TRIM(body_inline->'company_info'->>'state'), ''))
      -- 50 US states (full name → 2-char abbrev)
      WHEN 'ALABAMA' THEN 'AL'
      WHEN 'ALASKA' THEN 'AK'
      WHEN 'ARIZONA' THEN 'AZ'
      WHEN 'ARKANSAS' THEN 'AR'
      WHEN 'CALIFORNIA' THEN 'CA'
      WHEN 'COLORADO' THEN 'CO'
      WHEN 'CONNECTICUT' THEN 'CT'
      WHEN 'DELAWARE' THEN 'DE'
      WHEN 'FLORIDA' THEN 'FL'
      WHEN 'GEORGIA' THEN 'GA'
      WHEN 'HAWAII' THEN 'HI'
      WHEN 'IDAHO' THEN 'ID'
      WHEN 'ILLINOIS' THEN 'IL'
      WHEN 'INDIANA' THEN 'IN'
      WHEN 'IOWA' THEN 'IA'
      WHEN 'KANSAS' THEN 'KS'
      WHEN 'KENTUCKY' THEN 'KY'
      WHEN 'LOUISIANA' THEN 'LA'
      WHEN 'MAINE' THEN 'ME'
      WHEN 'MARYLAND' THEN 'MD'
      WHEN 'MASSACHUSETTS' THEN 'MA'
      WHEN 'MICHIGAN' THEN 'MI'
      WHEN 'MINNESOTA' THEN 'MN'
      WHEN 'MISSISSIPPI' THEN 'MS'
      WHEN 'MISSOURI' THEN 'MO'
      WHEN 'MONTANA' THEN 'MT'
      WHEN 'NEBRASKA' THEN 'NE'
      WHEN 'NEVADA' THEN 'NV'
      WHEN 'NEW HAMPSHIRE' THEN 'NH'
      WHEN 'NEW JERSEY' THEN 'NJ'
      WHEN 'NEW MEXICO' THEN 'NM'
      WHEN 'NEW YORK' THEN 'NY'
      WHEN 'NORTH CAROLINA' THEN 'NC'
      WHEN 'NORTH DAKOTA' THEN 'ND'
      WHEN 'OHIO' THEN 'OH'
      WHEN 'OKLAHOMA' THEN 'OK'
      WHEN 'OREGON' THEN 'OR'
      WHEN 'PENNSYLVANIA' THEN 'PA'
      WHEN 'RHODE ISLAND' THEN 'RI'
      WHEN 'SOUTH CAROLINA' THEN 'SC'
      WHEN 'SOUTH DAKOTA' THEN 'SD'
      WHEN 'TENNESSEE' THEN 'TN'
      WHEN 'TEXAS' THEN 'TX'
      WHEN 'UTAH' THEN 'UT'
      WHEN 'VERMONT' THEN 'VT'
      WHEN 'VIRGINIA' THEN 'VA'
      WHEN 'WASHINGTON' THEN 'WA'
      WHEN 'WEST VIRGINIA' THEN 'WV'
      WHEN 'WISCONSIN' THEN 'WI'
      WHEN 'WYOMING' THEN 'WY'
      -- DC + territories (full → 2-char). Already-2-char passes through ELSE.
      WHEN 'DISTRICT OF COLUMBIA' THEN 'DC'
      WHEN 'PUERTO RICO' THEN 'PR'
      WHEN 'GUAM' THEN 'GU'
      WHEN 'U.S. VIRGIN ISLANDS' THEN 'VI'
      WHEN 'VIRGIN ISLANDS' THEN 'VI'
      WHEN 'AMERICAN SAMOA' THEN 'AS'
      WHEN 'NORTHERN MARIANA ISLANDS' THEN 'MP'
      -- Already-2-char (or short garbage) values pass through.
      ELSE UPPER(NULLIF(TRIM(body_inline->'company_info'->>'state'), ''))
    END
  ) STORED;

CREATE INDEX IF NOT EXISTS lenders_state_abbr_idx
  ON lenders (state_abbr)
  WHERE state_abbr IS NOT NULL;

-- 2. Generated column for city normalization (helps city aggregates +
--    eventual /city/[slug] page).
ALTER TABLE lenders
  ADD COLUMN IF NOT EXISTS city_norm TEXT
  GENERATED ALWAYS AS (
    LOWER(NULLIF(TRIM(body_inline->'company_info'->>'city'), ''))
  ) STORED;

CREATE INDEX IF NOT EXISTS lenders_city_state_idx
  ON lenders (state_abbr, city_norm)
  WHERE state_abbr IS NOT NULL AND city_norm IS NOT NULL;

-- 3. State-level aggregate MV.
DROP MATERIALIZED VIEW IF EXISTS state_lender_counts CASCADE;
CREATE MATERIALIZED VIEW state_lender_counts AS
SELECT
  state_abbr,
  COUNT(*)::int AS lender_count,
  COUNT(DISTINCT city_norm)::int AS city_count
FROM lenders
WHERE state_abbr IS NOT NULL
GROUP BY state_abbr;

CREATE UNIQUE INDEX state_lender_counts_state_idx
  ON state_lender_counts (state_abbr);

-- 4. (state, city) aggregate MV.
DROP MATERIALIZED VIEW IF EXISTS state_city_lender_counts CASCADE;
CREATE MATERIALIZED VIEW state_city_lender_counts AS
SELECT
  l.state_abbr,
  l.city_norm AS city,
  -- Display name: take the most common original-case city spelling
  (
    SELECT body_inline->'company_info'->>'city'
    FROM lenders l2
    WHERE l2.state_abbr = l.state_abbr
      AND l2.city_norm = l.city_norm
    GROUP BY body_inline->'company_info'->>'city'
    ORDER BY COUNT(*) DESC
    LIMIT 1
  ) AS city_display,
  COUNT(*)::int AS lender_count
FROM lenders l
WHERE l.state_abbr IS NOT NULL
  AND l.city_norm IS NOT NULL
GROUP BY l.state_abbr, l.city_norm;

CREATE INDEX state_city_lender_counts_state_idx
  ON state_city_lender_counts (state_abbr);

CREATE INDEX state_city_lender_counts_count_idx
  ON state_city_lender_counts (state_abbr, lender_count DESC);

-- 5. Refresh function.
CREATE OR REPLACE FUNCTION refresh_state_aggregates()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
  REFRESH MATERIALIZED VIEW CONCURRENTLY state_lender_counts;
  REFRESH MATERIALIZED VIEW state_city_lender_counts;
END;
$$;

COMMENT ON FUNCTION refresh_state_aggregates() IS
  'CDM-REV — refreshes state_lender_counts + state_city_lender_counts. Call nightly via cron.';

-- 6. Grants — anon role gets read-only access for SSR runtime queries.
GRANT SELECT ON state_lender_counts TO anon, authenticated;
GRANT SELECT ON state_city_lender_counts TO anon, authenticated;

-- Reload PostgREST schema.
NOTIFY pgrst, 'reload schema';

COMMIT;
