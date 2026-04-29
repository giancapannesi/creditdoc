-- CDM-REV-2026-04-29 Phase 1.3.B Stage A.4 — long-form content collections to Postgres.
--
-- Tables created:
--   public.blog_posts   (34 blog/wellness articles; PK = slug)
--   public.listicles    (26 money/listicle pages; PK = slug)
--   public.answers      (14 /answers/ pages; PK = slug)
--   public.specials     (3 promo deals; PK = id uuid, FK-style lender_slug)
--
-- Mirrors A.2/A.3 pattern: body_inline jsonb + catalog cols + RLS + set_updated_at trigger.
--
-- ARTIFACT — NOT YET APPLIED. Apply via Jammi greenlight only.
--
-- A.4 retires the last big bundled JSONs:
--   src/content/blog-posts.json    720 KB → DB
--   src/content/listicles.json      78 KB → DB
--   src/content/answers/*.json      14 files → DB
--   src/content/specials.json        1 KB  → DB
--
-- After A.4 lands, the only remaining src/content/* are:
--   authors.json     small (<1 KB)  — kept bundled (build-time only)
--   lenders/         retired (now in DB via A.1)
--   brands/          retired (now in DB via A.2)
--
-- Once A.2/A.3/A.4 are applied + wired, every content type follows OBJ-1:
--   row UPDATE → set_updated_at fires → cache key bumps → next request HITs DB.
--   Never a `git push` to publish content again.

BEGIN;

-- ============================================================================
-- blog_posts
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.blog_posts (
  slug            text PRIMARY KEY,                       -- 'how-to-fix-credit-fast'
  title           text NOT NULL,
  category        text,                                   -- 'credit-repair', 'wellness', etc.
  status          text NOT NULL DEFAULT 'published',      -- 'draft' | 'published' | 'archived'
  publish_date    date,                                   -- separate from updated_at; the editorial date
  body_inline     jsonb,                                  -- description, sections, faq, key_takeaways, tags, ...
  updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_blog_posts_category ON public.blog_posts (category);
CREATE INDEX IF NOT EXISTS idx_blog_posts_status   ON public.blog_posts (status);
CREATE INDEX IF NOT EXISTS idx_blog_posts_publish_date ON public.blog_posts (publish_date DESC);
CREATE INDEX IF NOT EXISTS idx_blog_posts_updated_at   ON public.blog_posts (updated_at DESC);

DROP TRIGGER IF EXISTS set_blog_posts_updated_at ON public.blog_posts;
CREATE TRIGGER set_blog_posts_updated_at
  BEFORE UPDATE ON public.blog_posts
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

ALTER TABLE public.blog_posts ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS blog_posts_anon_read ON public.blog_posts;
CREATE POLICY blog_posts_anon_read
  ON public.blog_posts
  FOR SELECT
  TO anon, authenticated
  USING (status = 'published');

-- ============================================================================
-- listicles  (money pages — /best/[slug])
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.listicles (
  slug            text PRIMARY KEY,                       -- 'best-credit-repair-companies-2026'
  title           text NOT NULL,
  target_keyword  text,                                   -- the SERP target phrase
  category        text,
  body_inline     jsonb,                                  -- description, intro, lenders[], faq, tldr, key_takeaways
  updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_listicles_category   ON public.listicles (category);
CREATE INDEX IF NOT EXISTS idx_listicles_updated_at ON public.listicles (updated_at DESC);

DROP TRIGGER IF EXISTS set_listicles_updated_at ON public.listicles;
CREATE TRIGGER set_listicles_updated_at
  BEFORE UPDATE ON public.listicles
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

ALTER TABLE public.listicles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS listicles_anon_read ON public.listicles;
CREATE POLICY listicles_anon_read
  ON public.listicles
  FOR SELECT
  TO anon, authenticated
  USING (true);

-- ============================================================================
-- answers  (/answers/<slug>)
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.answers (
  slug                 text PRIMARY KEY,                   -- 'build-credit-with-no-history'
  title                text NOT NULL,
  cluster_id           text,                               -- cluster engine bookkeeping
  cluster_pillar       text,
  banner_category      text,
  target_money_page    text,                               -- /best/<slug> the answer routes traffic to
  compliance_score     numeric,                            -- 0–100 from compliance_score check
  compliance_passed    boolean DEFAULT false,
  body_inline          jsonb,                              -- h1, meta_description, sections, faq_schema, internal_links, ...
  updated_at           timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_answers_cluster_id        ON public.answers (cluster_id);
CREATE INDEX IF NOT EXISTS idx_answers_target_money_page ON public.answers (target_money_page);
CREATE INDEX IF NOT EXISTS idx_answers_compliance        ON public.answers (compliance_passed);
CREATE INDEX IF NOT EXISTS idx_answers_updated_at        ON public.answers (updated_at DESC);

DROP TRIGGER IF EXISTS set_answers_updated_at ON public.answers;
CREATE TRIGGER set_answers_updated_at
  BEFORE UPDATE ON public.answers
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

ALTER TABLE public.answers ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS answers_anon_read ON public.answers;
CREATE POLICY answers_anon_read
  ON public.answers
  FOR SELECT
  TO anon, authenticated
  USING (compliance_passed = true);

-- ============================================================================
-- specials  (promo deals shown on lender review pages)
-- ============================================================================
-- Specials don't have a natural unique slug; we generate a uuid PK and use
-- (lender_slug, deal_title) as a unique tuple to prevent dup-loads.
CREATE TABLE IF NOT EXISTS public.specials (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  lender_slug         text NOT NULL,                       -- FK-style → lenders.slug (no enforced FK; soft ref)
  deal_title          text NOT NULL,
  valid_until         date,
  body_inline         jsonb,                               -- deal_description, promo_code, discount_percent, url, ...
  updated_at          timestamptz NOT NULL DEFAULT now(),
  UNIQUE (lender_slug, deal_title)
);

CREATE INDEX IF NOT EXISTS idx_specials_lender_slug ON public.specials (lender_slug);
CREATE INDEX IF NOT EXISTS idx_specials_valid_until ON public.specials (valid_until);
CREATE INDEX IF NOT EXISTS idx_specials_updated_at  ON public.specials (updated_at DESC);

DROP TRIGGER IF EXISTS set_specials_updated_at ON public.specials;
CREATE TRIGGER set_specials_updated_at
  BEFORE UPDATE ON public.specials
  FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

ALTER TABLE public.specials ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS specials_anon_read ON public.specials;
CREATE POLICY specials_anon_read
  ON public.specials
  FOR SELECT
  TO anon, authenticated
  USING (valid_until IS NULL OR valid_until >= CURRENT_DATE);

COMMIT;

-- ============================================================================
-- Rollback (run if smoke test fails post-apply)
-- ============================================================================
-- BEGIN;
--   DROP TABLE IF EXISTS public.specials;
--   DROP TABLE IF EXISTS public.answers;
--   DROP TABLE IF EXISTS public.listicles;
--   DROP TABLE IF EXISTS public.blog_posts;
-- COMMIT;
