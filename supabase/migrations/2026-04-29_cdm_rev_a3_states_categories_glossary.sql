-- CDM-REV-2026-04-29 Phase 1.3.B Stage A.3 — content collections to Postgres.
--
-- Tables created:
--   public.states          (50 US states; PK = state code, e.g. 'AL')
--   public.categories      (18 lender categories; PK = slug)
--   public.glossary_terms  (71 finance terms; PK = slug)
--
-- Mirrors A.2 pattern (wellness_guides / comparisons / brands):
--   - body_inline jsonb holds full document content
--   - Catalog cols (name/term/category) duplicated for cheap PostgREST filters
--   - RLS on, anon read-only SELECT
--   - set_updated_at() BEFORE UPDATE trigger bumps updated_at on every write
--     → /api/revalidate cache key changes → next request re-fetches at edge
--     This is the OBJ-1 invalidation mechanism.
--
-- ARTIFACT — NOT YET APPLIED to live Supabase. Apply via Jammi greenlight only.
--
-- Why all three at once: A.3 sources are 552 KB + 10 KB + 61 KB JSONs that
-- currently bundle into the Worker. Moving them removes ~600 KB from the
-- compressed bundle (every byte counts under the 1 MB Workers cap) AND
-- aligns content updates with OBJ-1 (no rebuild on edit).

BEGIN;

-- ============================================================================
-- states
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.states (
  code         text PRIMARY KEY,                  -- 'AL', 'AK', etc. (uppercased)
  name         text NOT NULL,                     -- 'Alabama'
  abbr         text NOT NULL,                     -- 'AL' (denorm of code)
  body_inline  jsonb,                             -- full state document (capital, usury_cap, ...)
  updated_at   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_states_updated_at
  ON public.states (updated_at DESC);

DROP TRIGGER IF EXISTS set_states_updated_at ON public.states;
CREATE TRIGGER set_states_updated_at
  BEFORE UPDATE ON public.states
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

ALTER TABLE public.states ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS states_anon_read ON public.states;
CREATE POLICY states_anon_read
  ON public.states
  FOR SELECT
  TO anon, authenticated
  USING (true);

-- ============================================================================
-- categories
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.categories (
  slug         text PRIMARY KEY,                  -- 'credit-repair'
  name         text NOT NULL,                     -- 'Credit Repair'
  body_inline  jsonb,                             -- description, icon, seo_title, seo_description, count, filter_type
  updated_at   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_categories_updated_at
  ON public.categories (updated_at DESC);

DROP TRIGGER IF EXISTS set_categories_updated_at ON public.categories;
CREATE TRIGGER set_categories_updated_at
  BEFORE UPDATE ON public.categories
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

ALTER TABLE public.categories ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS categories_anon_read ON public.categories;
CREATE POLICY categories_anon_read
  ON public.categories
  FOR SELECT
  TO anon, authenticated
  USING (true);

-- ============================================================================
-- glossary_terms
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.glossary_terms (
  slug         text PRIMARY KEY,                  -- 'apr' (acronym) or full slug
  term         text NOT NULL,                     -- 'APR'
  category     text,                              -- 'credit', 'lending', etc.
  body_inline  jsonb,                             -- full_form, plain_definition, why_it_matters, example, page_contexts
  updated_at   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_glossary_terms_category
  ON public.glossary_terms (category);

CREATE INDEX IF NOT EXISTS idx_glossary_terms_updated_at
  ON public.glossary_terms (updated_at DESC);

-- page_contexts is an array inside body_inline → GIN over the jsonb path so
-- "give me all glossary terms used on /review/* pages" stays cheap.
CREATE INDEX IF NOT EXISTS idx_glossary_terms_page_contexts
  ON public.glossary_terms USING GIN ((body_inline -> 'page_contexts'));

DROP TRIGGER IF EXISTS set_glossary_terms_updated_at ON public.glossary_terms;
CREATE TRIGGER set_glossary_terms_updated_at
  BEFORE UPDATE ON public.glossary_terms
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

ALTER TABLE public.glossary_terms ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS glossary_terms_anon_read ON public.glossary_terms;
CREATE POLICY glossary_terms_anon_read
  ON public.glossary_terms
  FOR SELECT
  TO anon, authenticated
  USING (true);

COMMIT;

-- ============================================================================
-- Rollback (run if smoke test fails post-apply)
-- ============================================================================
-- BEGIN;
--   DROP TABLE IF EXISTS public.glossary_terms;
--   DROP TABLE IF EXISTS public.categories;
--   DROP TABLE IF EXISTS public.states;
-- COMMIT;
