-- CDM-REV Phase 5.1.b — state-page aggregates for runtime SSR.
--
-- Why this exists:
--   /state/[slug].astro currently uses fs-based getLendersInState +
--   getStatesWithLenders + getCitiesWithLenders, all of which iterate the
--   full 26K-row lender content collection. Naive runtime conversion
--   (fetch all 26K rows on every state page request) is unviable.
--
--   PostgREST also does NOT support jsonb deep-path URL filters
--   (body_inline->'company_info'->>'state' returns HTTP 500), so we cannot
--   filter by state at the REST layer without help.
--
-- What this provides:
--   1. lenders.state_abbr — generated stored column from
--      body_inline->'company_info'->>'state', UPPER-cased + normalized.
--      PostgREST can filter on this directly: ?state_abbr=eq.CA
--      Index makes per-state list queries fast.
--   2. lenders.city_norm — generated stored column from
--      body_inline->'company_info'->>'city', lower-cased + trimmed.
--      Lets us count lenders per (state, city) without jsonb-path filters.
--   3. state_lender_counts MV — (state_abbr, lender_count, city_count)
--      one row per US state. Refreshed nightly.
--   4. state_city_lender_counts MV — (state_abbr, city, lender_count)
--      one row per (state, city) with ≥1 lender. Refreshed nightly.
--   5. refresh_state_aggregates() function — single-call refresh used by
--      cron and by the daily DB→content pipeline.
--   6. Grants — anon role gets SELECT on the MVs and the new columns
--      (read-only, no PII exposure).
--
-- Rollback:
--   DROP MATERIALIZED VIEW IF EXISTS state_city_lender_counts;
--   DROP MATERIALIZED VIEW IF EXISTS state_lender_counts;
--   DROP FUNCTION IF EXISTS refresh_state_aggregates();
--   ALTER TABLE lenders DROP COLUMN IF EXISTS state_abbr;
--   ALTER TABLE lenders DROP COLUMN IF EXISTS city_norm;

BEGIN;

-- 1. Generated column for state filtering.
ALTER TABLE lenders
  ADD COLUMN IF NOT EXISTS state_abbr TEXT
  GENERATED ALWAYS AS (
    UPPER(NULLIF(TRIM(body_inline->'company_info'->>'state'), ''))
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

-- 5. Refresh function — wraps both MVs so cron + build pipeline can call once.
CREATE OR REPLACE FUNCTION refresh_state_aggregates()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
  REFRESH MATERIALIZED VIEW CONCURRENTLY state_lender_counts;
  REFRESH MATERIALIZED VIEW state_city_lender_counts;
  -- (state_city has no unique idx → cannot REFRESH CONCURRENTLY; that's OK,
  -- the table is small enough to swap atomically without read-lock pain.)
END;
$$;

COMMENT ON FUNCTION refresh_state_aggregates() IS
  'CDM-REV — refreshes state_lender_counts + state_city_lender_counts. Call nightly via cron.';

-- 6. Grants. Anon role gets read-only access for SSR runtime queries.
--    This is read-public data (count of lenders per state/city is not PII).
GRANT SELECT ON state_lender_counts TO anon, authenticated;
GRANT SELECT ON state_city_lender_counts TO anon, authenticated;

-- The new columns on lenders are auto-granted with the rest of the table.

-- Reload PostgREST schema so the new columns + views are immediately usable.
NOTIFY pgrst, 'reload schema';

COMMIT;
