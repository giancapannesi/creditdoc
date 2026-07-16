/**
 * Build-time equivalents of the Supabase-backed runtime helpers in src/lib/db.ts.
 *
 * Rationale: /credit-guide/* was SSR (each request → Supabase fetch). To
 * prerender the entire route family, we need the same data at build time.
 *
 * Strategy: fetch all city_guides + all states ONCE via curl+execSync (same
 * pattern as astro.config.mjs), then hand out from an in-memory cache. Build
 * is fast (~1s total for ~412 guides + ~50 states).
 *
 * Reads Supabase creds from /srv/BusinessOps/tools/.supabase-creditdoc.env
 * (same file astro.config.mjs already reads). Never bundled into the runtime
 * Worker — build-time only.
 */
import { execSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const SUPABASE_ENV_PATH = join(process.cwd(), '..', 'tools', '.supabase-creditdoc.env');

function loadSupabaseEnv(): { url: string; anonKey: string } {
  let url = process.env.SUPABASE_URL || '';
  let anonKey = process.env.SUPABASE_ANON_KEY || '';
  try {
    const text = readFileSync(SUPABASE_ENV_PATH, 'utf8');
    for (const line of text.split('\n')) {
      const m = line.match(/^SUPABASE_(URL|ANON_KEY)=["']?([^"'\n]+)["']?/);
      if (!m) continue;
      if (m[1] === 'URL' && !url) url = m[2].trim();
      if (m[1] === 'ANON_KEY' && !anonKey) anonKey = m[2].trim();
    }
  } catch { /* env file optional — env vars may still be set */ }
  return { url, anonKey };
}

function supabaseFetch<T>(pathAndQuery: string): T[] {
  const { url, anonKey } = loadSupabaseEnv();
  if (!url || !anonKey) {
    console.warn(`[data-build-remote] Supabase creds unavailable — returning empty for ${pathAndQuery}`);
    return [];
  }
  const fullUrl = `${url}/rest/v1/${pathAndQuery}`;
  try {
    const out = execSync(
      `curl -sS "${fullUrl}" -H "apikey: ${anonKey}" -H "Authorization: Bearer ${anonKey}"`,
      { encoding: 'utf8', maxBuffer: 32 * 1024 * 1024, timeout: 60_000 }
    );
    return JSON.parse(out) as T[];
  } catch (err: any) {
    console.warn(`[data-build-remote] fetch failed for ${pathAndQuery}: ${err.message}`);
    return [];
  }
}

// ─── City Guides ─────────────────────────────────────────────────────

export interface BuildTimeCityGuide {
  slug: string;
  city: string;
  state_abbr: string;
  state_name: string;
  population?: number | null;
  status?: string;
  body_inline?: any;
  updated_at?: string;
}

let _cityGuidesCache: BuildTimeCityGuide[] | null = null;

export function getAllCityGuidesBuildTime(): BuildTimeCityGuide[] {
  if (_cityGuidesCache) return _cityGuidesCache;
  _cityGuidesCache = supabaseFetch<BuildTimeCityGuide>(
    'city_guides?status=eq.ready_for_index&select=slug,city,state_abbr,state_name,population,body_inline,updated_at'
  );
  console.log(`[data-build-remote] loaded ${_cityGuidesCache.length} city_guides`);
  return _cityGuidesCache;
}

export function getCityGuideBySlugBuildTime(slug: string): BuildTimeCityGuide | null {
  return getAllCityGuidesBuildTime().find((g) => g.slug === slug) ?? null;
}

export function getCityGuidesByStateBuildTime(
  stateAbbr: string,
  limit = 50
): BuildTimeCityGuide[] {
  const rows = getAllCityGuidesBuildTime()
    .filter((g) => g.state_abbr?.toUpperCase() === stateAbbr.toUpperCase())
    .sort((a, b) => (b.population ?? 0) - (a.population ?? 0));
  return rows.slice(0, limit);
}

// ─── States (from Supabase — mirrors getStateBySlugRuntime) ───────────
//
// Supabase `states` schema: code (abbr), name, abbr, body_inline. No dedicated
// `slug` column — runtime derives slug from name.

export interface BuildTimeState {
  slug: string;          // derived — not a Supabase column
  name: string;
  abbr: string;
  body_inline?: any;
}

interface RawSupabaseState {
  code?: string;
  name: string;
  abbr?: string;
  body_inline?: any;
}

function toSlug(name: string): string {
  return (name || '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
}

let _statesCache: BuildTimeState[] | null = null;

export function getAllStatesBuildTime(): BuildTimeState[] {
  if (_statesCache) return _statesCache;
  const raw = supabaseFetch<RawSupabaseState>('states?select=code,name,abbr,body_inline');
  _statesCache = raw
    .filter((r) => r?.name)
    .map((r) => ({
      slug: toSlug(r.name),
      name: r.name,
      abbr: (r.abbr || r.code || '').toUpperCase(),
      body_inline: r.body_inline ?? {},
    }));
  console.log(`[data-build-remote] loaded ${_statesCache.length} states`);
  return _statesCache;
}

export function getStateBySlugBuildTime(slug: string): BuildTimeState | null {
  const wanted = slug.toLowerCase();
  return getAllStatesBuildTime().find((s) => s.slug === wanted) ?? null;
}

// ─── Wellness guides (used by credit-guide "Learn more" section) ───────

export interface BuildTimeWellnessGuideRef {
  slug: string;
  title: string;
}

let _wellnessGuidesCache: BuildTimeWellnessGuideRef[] | null = null;

export function getWellnessGuideRefsBuildTime(limit = 6): BuildTimeWellnessGuideRef[] {
  if (_wellnessGuidesCache) return _wellnessGuidesCache.slice(0, limit);
  _wellnessGuidesCache = supabaseFetch<BuildTimeWellnessGuideRef>(
    'wellness_guides?select=slug,title&limit=50'
  );
  console.log(`[data-build-remote] loaded ${_wellnessGuidesCache.length} wellness_guides`);
  return _wellnessGuidesCache.slice(0, limit);
}

// ─── Answers pool (used by credit-guide "Popular questions" section) ───

export interface BuildTimeAnswerRef {
  slug: string;
  title: string;
}

let _answersCache: BuildTimeAnswerRef[] | null = null;

/**
 * Fixed answer pool used by credit-guide pages. Same 8 slug patterns as the
 * original runtime `or=(slug.ilike.*...)` query. Fetched once at build.
 */
export function getCreditGuideAnswerPoolBuildTime(): BuildTimeAnswerRef[] {
  if (_answersCache) return _answersCache;
  const patterns = [
    'personal-loans-bad-credit',
    'debt-consolidation',
    'build-credit',
    'how-to-get-a-personal-loan',
    'how-much-can-you-borrow',
    'small-business-loans',
    'secured-credit-card',
  ];
  const orClause = patterns.map((p) => `slug.ilike.*${p}*`).join(',');
  _answersCache = supabaseFetch<BuildTimeAnswerRef>(
    `answers?select=slug,title&or=(${orClause})&limit=8`
  );
  console.log(`[data-build-remote] loaded ${_answersCache.length} credit-guide answer refs`);
  return _answersCache;
}

// ─── HMDA geo stats per state ─────────────────────────────────────────

export interface BuildTimeHmdaGeo {
  slug: string;
  state_code: string;
  total_applications: number;
  total_originated: number;
  approval_rate: number;
  low_income_approval_rate: number | null;
}

let _hmdaCache: Map<string, BuildTimeHmdaGeo[]> | null = null;

function loadAllHmdaBuildTime(): Map<string, BuildTimeHmdaGeo[]> {
  if (_hmdaCache) return _hmdaCache;
  const rows = supabaseFetch<BuildTimeHmdaGeo>(
    'hmda_geo_stats?select=slug,state_code,total_applications,total_originated,approval_rate,low_income_approval_rate&total_applications=gte.100&order=approval_rate.desc&limit=5000'
  );
  const grouped = new Map<string, BuildTimeHmdaGeo[]>();
  for (const row of rows) {
    const key = (row.state_code || '').toUpperCase();
    if (!key) continue;
    if (!grouped.has(key)) grouped.set(key, []);
    grouped.get(key)!.push(row);
  }
  _hmdaCache = grouped;
  console.log(`[data-build-remote] loaded ${rows.length} hmda_geo_stats rows across ${grouped.size} states`);
  return _hmdaCache;
}

export function getHmdaTopLendersByStateBuildTime(stateAbbr: string, limit = 10): BuildTimeHmdaGeo[] {
  const map = loadAllHmdaBuildTime();
  return (map.get(stateAbbr.toUpperCase()) ?? []).slice(0, limit);
}

// ─── All answer refs — for category-page answer filtering ─────────────

let _allAnswerRefsCache: BuildTimeAnswerRef[] | null = null;

export function getAllAnswerRefsBuildTime(): BuildTimeAnswerRef[] {
  if (_allAnswerRefsCache) return _allAnswerRefsCache;
  // Fetch generous batch — answers table is ~a few hundred rows total.
  _allAnswerRefsCache = supabaseFetch<BuildTimeAnswerRef>(
    'answers?select=slug,title&limit=2000'
  );
  console.log(`[data-build-remote] loaded ${_allAnswerRefsCache.length} answer refs (all)`);
  return _allAnswerRefsCache;
}

/**
 * Filter cached answer refs by slug substring matches (mirrors PostgREST
 * or=(slug.ilike.*X*,slug.ilike.*Y*) semantics — but case-insensitive substring,
 * done in-memory after the one-shot fetch.
 */
export function filterAnswerRefsBySlugPatterns(
  patterns: string[],
  limit = 6
): BuildTimeAnswerRef[] {
  if (!patterns.length) return [];
  const lowerPatterns = patterns.map((p) => p.toLowerCase());
  const matched: BuildTimeAnswerRef[] = [];
  for (const ref of getAllAnswerRefsBuildTime()) {
    const slugLower = (ref.slug || '').toLowerCase();
    if (lowerPatterns.some((p) => slugLower.includes(p))) {
      matched.push(ref);
      if (matched.length >= limit) break;
    }
  }
  return matched;
}
