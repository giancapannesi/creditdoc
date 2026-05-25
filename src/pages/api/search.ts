/**
 * iter 37 — /api/search SSR endpoint.
 *
 * Replaces the 20MB inline-data /search/ page. Queries Supabase `lenders` via
 * PostgREST anon-key reads, applies coarse filters server-side, returns a
 * compact result set the client renders directly.
 *
 * Free-text `q` matches across name + description_short + services using
 * Postgres ILIKE substring — so "Eze" returns Eze Pawn, Eze Credit, anything
 * with those three letters anywhere in name/description/services.
 */
import type { APIRoute } from 'astro';

export const prerender = false;

interface RuntimeEnv {
  SUPABASE_URL?: string;
  SUPABASE_ANON_KEY?: string;
}

interface BodyInline {
  rating?: number;
  description_short?: string;
  services?: string[];
  best_for?: string[];
  states_served?: string[];
  cities_served?: string[];
  google_reviews_count?: number;
  quality_score?: number;
  has_been_enriched?: boolean;
  data_source?: string;
  subcategories?: string[];
  pricing?: {
    monthly_price?: number;
    setup_fee?: number;
    money_back_guarantee?: boolean;
    free_consultation?: boolean;
  };
  company_info?: {
    bbb_rating?: string;
  };
}

interface RawLender {
  slug: string;
  name: string;
  category: string;
  state: string | null;
  state_abbr: string | null;
  brand_slug: string | null;
  body_inline: BodyInline | null;
}

interface CompactLender {
  s: string; // slug
  n: string; // name
  c: string; // category
  sc: string[]; // subcategories
  r: number; // stored Google rating, only when paired with Google review count
  mp: number; // monthly_price
  bb: string; // bbb_rating
  mg: boolean; // money_back_guarantee
  fc: boolean; // free_consultation
  st: string[]; // states_served
  ct: string[]; // cities_served
  ds: string; // description_short (truncated)
  bf: string[]; // best_for (max 3)
  gr: number; // google_reviews_count
  qs: number; // quality_score
  en: number; // enriched flag (0|1)
  br: string | null; // brand_slug
}

const SAFE = /[^a-z0-9 \-_'&.,/]/gi;
function sanitizeSearchTerm(s: string): string {
  // Strip everything that isn't alphanumeric or basic punctuation, then
  // escape PostgREST wildcards. Keeps "Eze", "5-Star", "Bank of America".
  return s.replace(SAFE, '').replace(/[%_*]/g, '').slice(0, 80).trim();
}

function compact(r: RawLender): CompactLender {
  const b = r.body_inline || {};
  return {
    s: r.slug,
    n: r.name,
    c: r.category,
    sc: b.subcategories || [],
    r: b.google_rating && b.google_rating > 0 && !(b.google_rating > 5) && b.google_reviews_count && b.google_reviews_count >= 1 ? b.google_rating : 0,
    mp: b.pricing?.monthly_price || 0,
    bb: b.company_info?.bbb_rating || 'NR',
    mg: !!b.pricing?.money_back_guarantee,
    fc: !!b.pricing?.free_consultation,
    st: b.states_served || [],
    ct: (b.cities_served || []).slice(0, 30),
    ds: (b.description_short || '').slice(0, 200),
    bf: (b.best_for || []).slice(0, 3),
    gr: b.google_reviews_count || 0,
    qs: b.quality_score || 0,
    en:
      b.has_been_enriched ||
      b.data_source === 'enriched' ||
      b.data_source === 'editorial' ||
      b.data_source === 'verified'
        ? 1
        : 0,
    br: r.brand_slug,
  };
}

export const GET: APIRoute = async ({ url, locals }) => {
  const env = ((locals as any)?.runtime?.env || {}) as RuntimeEnv;
  if (!env.SUPABASE_URL || !env.SUPABASE_ANON_KEY) {
    return json({ error: 'config' }, 500);
  }

  const sp = url.searchParams;
  const q = sanitizeSearchTerm(sp.get('q') || '');
  const category = (sp.get('category') || '').trim();
  const state = (sp.get('state') || '').trim();
  const stateAbbr = (sp.get('state_abbr') || '').trim().toUpperCase();
  const bbbFilter = (sp.get('bbb') || '').trim();
  const guarantee = sp.get('guarantee') === '1';
  const freeConsult = sp.get('free_consult') === '1';
  const bbbAPlus = sp.get('bbb_a_plus') === '1';
  const limit = Math.min(parseInt(sp.get('limit') || '200', 10) || 200, 500);

  // Build PostgREST query string
  const params = new URLSearchParams();
  params.set(
    'select',
    'slug,name,category,state,state_abbr,brand_slug,body_inline'
  );
  params.set('processing_status', 'eq.ready_for_index');
  params.set('limit', String(Math.min(limit * 4, 1000))); // overfetch, then qs/en filter client-of-API-side

  if (category) {
    // Top-level category match. Subcategory contains-via-jsonb is messy in
    // PostgREST or=() syntax (URL-encoding of JSON brackets clashes with
    // PostgREST's parser); skip and fall back to client refinement if needed.
    params.set('category', `eq.${pcEnc(category)}`);
  }

  if (stateAbbr) {
    params.set('state_abbr', `eq.${stateAbbr}`);
  } else if (state) {
    params.append(
      'or',
      `(state.ilike.*${pcEnc(state)}*,body_inline->states_served.cs.${pcEnc(JSON.stringify([state]))})`
    );
  }

  if (q) {
    const t = q;
    // ILIKE substring across name + description_short + services-as-text.
    // services is a JSONB array; ::text cast lets ILIKE scan its serialized form.
    params.append(
      'or',
      `(name.ilike.*${pcEnc(t)}*,body_inline->>description_short.ilike.*${pcEnc(t)}*,body_inline->>services.ilike.*${pcEnc(t)}*,brand_slug.ilike.*${pcEnc(slugify(t))}*)`
    );
  }

  // Sort by has_been_enriched (jsonb bool) then quality_score then rating.
  // PostgREST jsonb sort syntax: order=body_inline->>quality_score.desc.nullslast
  // But booleans / numerics in jsonb don't always order well; sort applied
  // post-fetch instead.

  const supaUrl = `${env.SUPABASE_URL}/rest/v1/lenders?${params.toString()}`;

  let rows: RawLender[] = [];
  try {
    const res = await fetch(supaUrl, {
      headers: {
        apikey: env.SUPABASE_ANON_KEY,
        authorization: `Bearer ${env.SUPABASE_ANON_KEY}`,
        accept: 'application/json',
      },
      signal: AbortSignal.timeout(5000),
    });
    if (!res.ok) {
      const text = await res.text();
      return json({ error: 'upstream', status: res.status, detail: text.slice(0, 200) }, 502);
    }
    rows = (await res.json()) as RawLender[];
  } catch (err) {
    return json({ error: 'fetch_failed', detail: (err as Error).message }, 502);
  }

  // Quality + filter pass: reject low-quality unenriched, plus bbb/mg/fc.
  const compactRows = rows
    .map(compact)
    .filter((r) => r.qs >= 3 || r.en === 1)
    .filter((r) => (guarantee ? r.mg : true))
    .filter((r) => (freeConsult ? r.fc : true))
    .filter((r) => {
      if (bbbAPlus && r.bb !== 'A+') return false;
      if (bbbFilter === 'a-plus' && r.bb !== 'A+') return false;
      if (bbbFilter === 'a-or-higher' && r.bb !== 'A+' && r.bb !== 'A') return false;
      if (
        bbbFilter === 'b-or-higher' &&
        ['C', 'C+', 'C-', 'D', 'F', 'NR'].indexOf(r.bb) !== -1
      )
        return false;
      return true;
    });

  // Default ranking: enriched first, then quality_score desc, then stored Google rating desc.
  compactRows.sort((a, b) => {
    if (a.en !== b.en) return b.en - a.en;
    const aTier = a.qs >= 10 ? 2 : a.qs >= 5 ? 1 : 0;
    const bTier = b.qs >= 10 ? 2 : b.qs >= 5 ? 1 : 0;
    if (aTier !== bTier) return bTier - aTier;
    return (b.r || 0) - (a.r || 0);
  });

  const trimmed = compactRows.slice(0, limit);
  return json(
    { count: trimmed.length, total_matched: compactRows.length, results: trimmed },
    200,
    { 'cache-control': 'public, max-age=60, s-maxage=300' }
  );
};

function json(body: unknown, status: number, extraHeaders: Record<string, string> = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      'content-type': 'application/json; charset=utf-8',
      ...extraHeaders,
    },
  });
}

function pcEnc(s: string): string {
  // PostgREST URL value encoder — escape commas, parens, periods, *
  // Wildcards (*) are reserved, but we strip them upstream.
  return encodeURIComponent(s).replace(/'/g, '%27');
}

function slugify(s: string): string {
  return s
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '');
}
