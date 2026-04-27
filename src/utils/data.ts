import fs from 'node:fs';
import path from 'node:path';
import { queryJsonRows, queryJsonRow, queryRows } from './db';

// Entity-type badge matrix (2026-04-19) — governs which category of lender
// is eligible to show the "Free Consultation" and "Free to Use" badges.
export const ENTITY_TYPE_BADGE_MATRIX: Record<string, {freeConsult: boolean; freeToUse: boolean}> = {
  'credit-repair':       {freeConsult: true,  freeToUse: false},
  'fix-my-credit':       {freeConsult: true,  freeToUse: false},
  'debt-relief':         {freeConsult: true,  freeToUse: false},
  'debt-settlement':     {freeConsult: true,  freeToUse: false},
  'credit-counseling':   {freeConsult: true,  freeToUse: false},
  'bankruptcy-services': {freeConsult: true,  freeToUse: false},
  'free-help':           {freeConsult: true,  freeToUse: true},
  'get-out-of-debt':     {freeConsult: true,  freeToUse: false},
  'insurance':           {freeConsult: true,  freeToUse: false},
  'build-my-credit':     {freeConsult: false, freeToUse: false},
  'monitor-protect':     {freeConsult: false, freeToUse: true},
  'credit-monitoring':   {freeConsult: false, freeToUse: true},
  'identity-theft':      {freeConsult: false, freeToUse: true},
  'personal-loans':      {freeConsult: false, freeToUse: false},
  'business-loans':      {freeConsult: false, freeToUse: false},
  'mortgages':           {freeConsult: false, freeToUse: false},
  'emergency-cash':      {freeConsult: false, freeToUse: false},
  'payday-alternatives': {freeConsult: false, freeToUse: false},
  'credit-cards':        {freeConsult: false, freeToUse: false},
  'banking':             {freeConsult: false, freeToUse: false},
  'banks':               {freeConsult: false, freeToUse: false},
  'credit-unions':       {freeConsult: false, freeToUse: false},
  'pawn-shops':          {freeConsult: false, freeToUse: false},
  'check-cashing':       {freeConsult: false, freeToUse: false},
  'atms-cash-access':    {freeConsult: false, freeToUse: false},
  'atms':                {freeConsult: false, freeToUse: false},
  'cash-access':         {freeConsult: false, freeToUse: false},
};

export function getBadgeEligibility(category: string): {freeConsult: boolean; freeToUse: boolean} {
  return ENTITY_TYPE_BADGE_MATRIX[category] || {freeConsult: false, freeToUse: false};
}

export interface LenderPricing {
  monthly_price: number;
  setup_fee: number;
  money_back_guarantee: boolean;
  guarantee_details: string;
  free_consultation: boolean;
  tiers: { name: string; price: number; features: string[] }[];
  currency: string;
}

export interface LenderFeatures {
  credit_monitoring: boolean;
  all_three_bureaus: boolean;
  goodwill_letters: boolean;
  cease_desist_letters: boolean;
  debt_validation: boolean;
  credit_education: boolean;
  identity_theft_protection: boolean;
  score_tracking: boolean;
  mobile_app: boolean;
  online_portal: boolean;
  personal_advisor: boolean;
  ai_powered: boolean;
}

export interface Lender {
  name: string;
  slug: string;
  category: string;
  subcategories: string[];
  description_short: string;
  description_long: string;
  logo_url: string;
  website_url: string;
  affiliate_url: string;
  affiliate_program: string;
  affiliate_anchors?: string[];
  pricing: LenderPricing;
  features: LenderFeatures;
  company_info: {
    founded_year: number;
    headquarters: string;
    city: string;
    state: string;
    employees: string;
    bbb_rating: string;
    bbb_accredited: boolean;
    certifications?: string[];
  };
  states_served: string[];
  cities_served: string[];
  rating: number;
  rating_breakdown: {
    value: number;
    effectiveness: number;
    customer_service: number;
    transparency: number;
    ease_of_use: number;
  };
  pros: string[];
  cons: string[];
  best_for: string[];
  similar_lenders: string[];
  diagnosis: string;
  services: string[];
  typical_results_timeline: string;
  last_updated: string;
  review_status: string;
  processing_status?: string;
  brand_slug?: string | null;
  data_source?: string;
  google_rating?: number;
  google_reviews_count?: number;
  phone?: string;
  address?: string;
  loan_details?: {
    min_amount: number;
    max_amount: number;
    min_term_months: number;
    max_term_months: number;
    apr_min: number;
    apr_max: number;
    origination_fee: string;
    min_credit_score: number;
    funding_speed: string;
    loan_purposes: string[];
    prequalification: boolean;
    direct_pay: boolean;
  };
  cfpb_data?: {
    found_in_cfpb: boolean;
    cfpb_company_name: string;
    resolution_rate: number;
    timely_response_rate: number;
    data_source: string;
    data_period: string;
    last_checked: string;
  };
}

export interface Category {
  slug: string;
  name: string;
  description: string;
  icon: string;
  seo_title: string;
  seo_description: string;
  count: number;
  filter_type: 'credit-repair' | 'loan' | 'service';
}

export interface Comparison {
  slug: string;
  lender_a: string;
  lender_b: string;
  title: string;
  target_keyword: string;
  summary: string;
  winner: string;
  winner_reason: string;
}

export interface Listicle {
  slug: string;
  title: string;
  target_keyword: string;
  category: string;
  description: string;
  intro: string;
  lenders: string[];
  seo_title: string;
  seo_description: string;
}

export interface Special {
  lender_slug: string;
  lender_name: string;
  deal_title: string;
  deal_description: string;
  promo_code: string;
  discount_percent: number;
  valid_until: string;
  url: string;
}

export interface WellnessGuide {
  slug: string;
  title: string;
  category: string;
  description: string;
  seo_title: string;
  seo_description: string;
  icon: string;
  read_time: string;
  last_updated: string;
  sections: { heading: string; content: string }[];
  key_takeaways: string[];
  related_guides: string[];
  related_categories: string[];
  faq: { question: string; answer: string }[];
}

const CONTENT_DIR = path.join(process.cwd(), 'src/content');

// === Lenders (DB-backed) ===

const LENDER_LIVE_FILTER = "processing_status IN ('ready_for_index', 'pending_approval')";

let _lendersCache: Lender[] | null = null;
let _lendersPromise: Promise<Lender[]> | null = null;

function normalizeLender(l: Lender): Lender {
  l.subcategories = Array.isArray(l.subcategories) ? l.subcategories : [];
  l.states_served = Array.isArray(l.states_served) ? l.states_served : [];
  l.cities_served = Array.isArray(l.cities_served) ? l.cities_served : [];
  l.best_for = Array.isArray(l.best_for) ? l.best_for : [];
  l.services = Array.isArray(l.services) ? l.services : [];
  l.similar_lenders = Array.isArray(l.similar_lenders) ? l.similar_lenders : [];
  l.pros = Array.isArray(l.pros) ? l.pros : [];
  l.cons = Array.isArray(l.cons) ? l.cons : [];
  return l;
}

export async function getAllLenders(): Promise<Lender[]> {
  if (_lendersCache) return _lendersCache;
  if (_lendersPromise) return _lendersPromise;
  _lendersPromise = queryJsonRows<Lender>(
    `SELECT data FROM lenders WHERE ${LENDER_LIVE_FILTER}`
  ).then(rows => {
    _lendersCache = rows.map(normalizeLender);
    return _lendersCache;
  });
  return _lendersPromise;
}

export async function getLenderBySlug(slug: string): Promise<Lender | undefined> {
  if (_lendersCache) return _lendersCache.find(l => l.slug === slug);
  const r = await queryJsonRow<Lender>(
    `SELECT data FROM lenders WHERE slug = ? AND ${LENDER_LIVE_FILTER}`,
    [slug]
  );
  return r ? normalizeLender(r) : undefined;
}

export async function getLendersByCategory(category: string): Promise<Lender[]> {
  if (_lendersCache) {
    return _lendersCache.filter(l => l.category === category || (l.subcategories ?? []).includes(category));
  }
  const rows = await queryJsonRows<Lender>(
    `SELECT data FROM lenders WHERE ${LENDER_LIVE_FILTER}
     AND (json_extract(data, '$.category') = ?
          OR EXISTS (SELECT 1 FROM json_each(json_extract(data, '$.subcategories')) WHERE value = ?))`,
    [category, category]
  );
  return rows.map(normalizeLender);
}

export async function getLendersByState(state: string): Promise<Lender[]> {
  if (_lendersCache) {
    const s = state.toLowerCase();
    return _lendersCache.filter(l => {
      const states = l.states_served ?? [];
      return states.some(st => st.toLowerCase() === s) || states.includes('All 50 States');
    });
  }
  const rows = await queryJsonRows<Lender>(
    `SELECT data FROM lenders WHERE ${LENDER_LIVE_FILTER}
     AND (EXISTS (SELECT 1 FROM json_each(json_extract(data, '$.states_served')) WHERE LOWER(value) = LOWER(?))
          OR EXISTS (SELECT 1 FROM json_each(json_extract(data, '$.states_served')) WHERE value = 'All 50 States'))`,
    [state]
  );
  return rows.map(normalizeLender);
}

export async function getLendersByCity(city: string): Promise<Lender[]> {
  if (_lendersCache) {
    const c = city.toLowerCase();
    return _lendersCache.filter(l => {
      const cities = l.cities_served ?? [];
      const states = l.states_served ?? [];
      return cities.some(ct => ct.toLowerCase() === c) || states.includes('All 50 States');
    });
  }
  const rows = await queryJsonRows<Lender>(
    `SELECT data FROM lenders WHERE ${LENDER_LIVE_FILTER}
     AND (EXISTS (SELECT 1 FROM json_each(json_extract(data, '$.cities_served')) WHERE LOWER(value) = LOWER(?))
          OR EXISTS (SELECT 1 FROM json_each(json_extract(data, '$.states_served')) WHERE value = 'All 50 States'))`,
    [city]
  );
  return rows.map(normalizeLender);
}

// === Categories (DB-backed, count derived from lenders) ===

let _categoriesCache: Category[] | null = null;

export async function getCategories(): Promise<Category[]> {
  if (_categoriesCache) return _categoriesCache;
  const rawCategories = await queryJsonRows<Category>("SELECT data FROM categories");
  // Count via SQL aggregation, not by pulling all 20K lenders.
  const countRows = await queryRows(
    `SELECT json_extract(data, '$.category') AS cat, COUNT(*) AS n
     FROM lenders WHERE ${LENDER_LIVE_FILTER}
     GROUP BY cat`
  );
  const subcatRows = await queryRows(
    `SELECT je.value AS cat, COUNT(*) AS n
     FROM lenders, json_each(json_extract(lenders.data, '$.subcategories')) AS je
     WHERE ${LENDER_LIVE_FILTER}
     GROUP BY je.value`
  );
  const countMap = new Map<string, number>();
  for (const r of countRows) countMap.set(String(r.cat), Number(r.n));
  for (const r of subcatRows) {
    const k = String(r.cat);
    countMap.set(k, (countMap.get(k) ?? 0) + Number(r.n));
  }
  _categoriesCache = rawCategories.map(c => ({
    ...c,
    count: countMap.get(c.slug) ?? 0,
  }));
  return _categoriesCache;
}

// === Comparisons (DB-backed) ===

let _comparisonsCache: Comparison[] | null = null;

export async function getComparisons(): Promise<Comparison[]> {
  if (_comparisonsCache) return _comparisonsCache;
  _comparisonsCache = await queryJsonRows<Comparison>("SELECT data FROM comparisons");
  return _comparisonsCache;
}

export async function getComparisonBySlug(slug: string): Promise<Comparison | undefined> {
  if (_comparisonsCache) return _comparisonsCache.find(c => c.slug === slug);
  const r = await queryJsonRow<Comparison>("SELECT data FROM comparisons WHERE slug = ?", [slug]);
  return r ?? undefined;
}

// === Listicles (DB-backed) ===

let _listiclesCache: Listicle[] | null = null;

export async function getListicles(): Promise<Listicle[]> {
  if (_listiclesCache) return _listiclesCache;
  _listiclesCache = await queryJsonRows<Listicle>("SELECT data FROM listicles");
  return _listiclesCache;
}

export async function getListicleBySlug(slug: string): Promise<Listicle | undefined> {
  if (_listiclesCache) return _listiclesCache.find(l => l.slug === slug);
  const r = await queryJsonRow<Listicle>("SELECT data FROM listicles WHERE slug = ?", [slug]);
  return r ?? undefined;
}

// === Specials (JSON-only — no DB table) ===

export function getSpecials(): Special[] {
  const p = path.join(CONTENT_DIR, 'specials.json');
  if (!fs.existsSync(p)) return [];
  return JSON.parse(fs.readFileSync(p, 'utf-8')) as Special[];
}

// === Wellness guides (DB-backed) ===

let _wellnessCache: WellnessGuide[] | null = null;

export async function getWellnessGuides(): Promise<WellnessGuide[]> {
  if (_wellnessCache) return _wellnessCache;
  _wellnessCache = await queryJsonRows<WellnessGuide>("SELECT data FROM wellness_guides");
  return _wellnessCache;
}

export async function getWellnessGuideBySlug(slug: string): Promise<WellnessGuide | undefined> {
  if (_wellnessCache) return _wellnessCache.find(g => g.slug === slug);
  const r = await queryJsonRow<WellnessGuide>("SELECT data FROM wellness_guides WHERE slug = ?", [slug]);
  return r ?? undefined;
}

export async function getWellnessGuidesByCategory(category: string): Promise<WellnessGuide[]> {
  const all = await getWellnessGuides();
  return all.filter(g => g.category === category);
}

// === Pure helpers (sync) ===

export function getBbbClass(rating: string): string {
  if (rating === 'A+') return 'bbb-a-plus';
  if (rating === 'A') return 'bbb-a';
  if (rating === 'B+') return 'bbb-b-plus';
  if (rating === 'B') return 'bbb-b';
  if (rating === 'C' || rating === 'C+' || rating === 'C-') return 'bbb-c';
  if (rating === 'F') return 'bbb-f';
  return 'bbb-nr';
}

export function formatPrice(price: number): string {
  if (price === 0) return 'Free';
  return `$${price.toFixed(2)}`;
}

export function generateDiagnosis(lender: Lender): string {
  if (lender.diagnosis) return lender.diagnosis;
  const bestFor = lender.best_for.slice(0, 2).join(' and ');
  const topPro = lender.pros[0] || 'competitive pricing';
  const topCon = lender.cons[0] || 'limited availability in some areas';
  return `Ideal for ${bestFor}. Strength: ${topPro}. Watch out for: ${topCon}.`;
}

// === Geography aggregations (derived from lenders, async) ===

export async function getAllStates(): Promise<string[]> {
  const states = new Set<string>();
  for (const l of await getAllLenders()) {
    for (const s of l.states_served) {
      if (s !== 'All 50 States') states.add(s);
    }
  }
  return Array.from(states).sort();
}

export async function getAllCities(): Promise<string[]> {
  const cities = new Set<string>();
  for (const l of await getAllLenders()) {
    for (const c of l.cities_served) {
      cities.add(c);
    }
  }
  return Array.from(cities).sort();
}

export interface CityInfo {
  city: string;
  state: string;
  stateAbbr: string;
  slug: string;
  count: number;
}

export async function getCitiesWithLenders(minCount: number = 5): Promise<CityInfo[]> {
  const cityMap = new Map<string, { city: string; state: string; count: number }>();
  for (const l of await getAllLenders()) {
    const city = l.company_info.city;
    const state = l.company_info.state;
    if (!city || !state) continue;
    const key = `${city}|${state}`;
    const existing = cityMap.get(key);
    if (existing) {
      existing.count++;
    } else {
      cityMap.set(key, { city, state, count: 1 });
    }
  }

  const abbrevToFull: Record<string, string> = {};
  for (const [full, abbr] of Object.entries(STATE_ABBREVIATIONS)) {
    abbrevToFull[abbr] = full;
  }

  return Array.from(cityMap.values())
    .filter(c => c.count >= minCount)
    .map(c => {
      const fullState = abbrevToFull[c.state] || c.state;
      const slug = `${c.city.toLowerCase().replace(/[^a-z0-9]+/g, '-')}-${c.state.toLowerCase()}`;
      return {
        city: c.city,
        state: fullState,
        stateAbbr: c.state,
        slug,
        count: c.count,
      };
    })
    .sort((a, b) => b.count - a.count);
}

export async function getLendersByCityState(city: string, stateAbbr: string): Promise<Lender[]> {
  const all = await getAllLenders();
  return all.filter(l =>
    l.company_info.city === city && l.company_info.state === stateAbbr
  );
}

export const US_STATES = [
  'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 'Connecticut',
  'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa',
  'Kansas', 'Kentucky', 'Louisiana', 'Maine', 'Maryland', 'Massachusetts', 'Michigan',
  'Minnesota', 'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada', 'New Hampshire',
  'New Jersey', 'New Mexico', 'New York', 'North Carolina', 'North Dakota', 'Ohio',
  'Oklahoma', 'Oregon', 'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota',
  'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington', 'West Virginia',
  'Wisconsin', 'Wyoming'
];

export const STATE_ABBREVIATIONS: Record<string, string> = {
  'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA',
  'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE', 'Florida': 'FL', 'Georgia': 'GA',
  'Hawaii': 'HI', 'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA',
  'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
  'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS',
  'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV', 'New Hampshire': 'NH',
  'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY', 'North Carolina': 'NC',
  'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA',
  'Rhode Island': 'RI', 'South Carolina': 'SC', 'South Dakota': 'SD', 'Tennessee': 'TN',
  'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA',
  'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY'
};

export interface StateInfo {
  name: string;
  abbr: string;
  slug: string;
  lenderCount: number;
  cityCount: number;
  topCities: string[];
}

export async function getStatesWithLenders(minCount: number = 1): Promise<StateInfo[]> {
  const stateMap = new Map<string, { count: number; cities: Set<string> }>();
  for (const l of await getAllLenders()) {
    const abbr = l.company_info.state;
    if (!abbr) continue;
    if (!stateMap.has(abbr)) stateMap.set(abbr, { count: 0, cities: new Set() });
    const s = stateMap.get(abbr)!;
    s.count++;
    if (l.company_info.city) s.cities.add(l.company_info.city);
  }

  const abbrevToFull: Record<string, string> = {};
  for (const [full, abbr] of Object.entries(STATE_ABBREVIATIONS)) {
    abbrevToFull[abbr] = full;
  }

  return Array.from(stateMap.entries())
    .filter(([, v]) => v.count >= minCount)
    .map(([abbr, v]) => {
      const name = abbrevToFull[abbr] || abbr;
      return {
        name,
        abbr,
        slug: name.toLowerCase().replace(/\s+/g, '-'),
        lenderCount: v.count,
        cityCount: v.cities.size,
        topCities: Array.from(v.cities).slice(0, 10),
      };
    })
    .sort((a, b) => b.lenderCount - a.lenderCount);
}

export async function getLendersInState(stateAbbr: string): Promise<Lender[]> {
  const all = await getAllLenders();
  return all.filter(l => l.company_info.state === stateAbbr);
}

// === States data (JSON-only — no DB table) ===

export function getStateData(): Record<string, any> {
  const dataPath = path.join(process.cwd(), 'src/content/states.json');
  if (!fs.existsSync(dataPath)) return {};
  return JSON.parse(fs.readFileSync(dataPath, 'utf-8'));
}

export function getAllStatesInfo(): { name: string; abbr: string; slug: string }[] {
  const data = getStateData();
  return Object.entries(data).map(([abbr, info]: [string, any]) => ({
    name: info.name,
    abbr,
    slug: info.name.toLowerCase().replace(/\s+/g, '-'),
  }));
}

// === Glossary terms (JSON-only — no DB table) ===

export interface GlossaryTerm {
  slug: string;
  term: string;
  full_form: string;
  category: string;
  plain_definition: string;
  why_it_matters: string;
  example: string;
  page_contexts: string[];
}

export function getGlossaryTerms(): GlossaryTerm[] {
  const raw = fs.readFileSync(path.join(CONTENT_DIR, 'glossary-terms.json'), 'utf-8');
  return JSON.parse(raw) as GlossaryTerm[];
}

export function getGlossaryTermsForContext(contexts: string[]): GlossaryTerm[] {
  return getGlossaryTerms().filter(t =>
    t.page_contexts.some(c => contexts.includes(c))
  );
}

// === Brands (JSON-only — no DB table) ===

export interface BrandFAQ {
  q: string;
  a: string;
}

export interface BrandInfo {
  slug: string;
  display_name: string;
  summary_short: string;
  summary_long: string;
  faq: BrandFAQ[];
  official_website: string | null;
  parent_company?: string;
  category: string;
  last_reviewed: string;
  location_count?: number;
}

const BRANDS_DIR = path.join(process.cwd(), 'src/content/brands');

let _brandsCache: BrandInfo[] | null = null;

export async function getAllBrands(): Promise<BrandInfo[]> {
  if (_brandsCache) return _brandsCache;
  if (!fs.existsSync(BRANDS_DIR)) {
    _brandsCache = [];
    return _brandsCache;
  }
  const files = fs.readdirSync(BRANDS_DIR).filter(f => f.endsWith('.json'));
  const lenders = await getAllLenders();
  _brandsCache = files.map(f => {
    const raw = fs.readFileSync(path.join(BRANDS_DIR, f), 'utf-8');
    const brand = JSON.parse(raw) as BrandInfo;
    brand.location_count = lenders.filter(l => l.brand_slug === brand.slug).length;
    return brand;
  });
  return _brandsCache;
}

export async function getBrandInfo(slug: string): Promise<BrandInfo | null> {
  const brands = await getAllBrands();
  return brands.find(b => b.slug === slug) ?? null;
}

export async function getLendersByBrand(slug: string): Promise<Lender[]> {
  const all = await getAllLenders();
  return all.filter(l => l.brand_slug === slug);
}

export const TOP_CITIES: { city: string; state: string; lat: number; lng: number }[] = [
  { city: 'New York', state: 'New York', lat: 40.7128, lng: -74.0060 },
  { city: 'Los Angeles', state: 'California', lat: 34.0522, lng: -118.2437 },
  { city: 'Chicago', state: 'Illinois', lat: 41.8781, lng: -87.6298 },
  { city: 'Houston', state: 'Texas', lat: 29.7604, lng: -95.3698 },
  { city: 'Phoenix', state: 'Arizona', lat: 33.4484, lng: -112.0740 },
  { city: 'Philadelphia', state: 'Pennsylvania', lat: 39.9526, lng: -75.1652 },
  { city: 'San Antonio', state: 'Texas', lat: 29.4241, lng: -98.4936 },
  { city: 'San Diego', state: 'California', lat: 32.7157, lng: -117.1611 },
  { city: 'Dallas', state: 'Texas', lat: 32.7767, lng: -96.7970 },
  { city: 'Jacksonville', state: 'Florida', lat: 30.3322, lng: -81.6557 },
  { city: 'Austin', state: 'Texas', lat: 30.2672, lng: -97.7431 },
  { city: 'San Jose', state: 'California', lat: 37.3382, lng: -121.8863 },
  { city: 'Fort Worth', state: 'Texas', lat: 32.7555, lng: -97.3308 },
  { city: 'Columbus', state: 'Ohio', lat: 39.9612, lng: -82.9988 },
  { city: 'Charlotte', state: 'North Carolina', lat: 35.2271, lng: -80.8431 },
  { city: 'Indianapolis', state: 'Indiana', lat: 39.7684, lng: -86.1581 },
  { city: 'San Francisco', state: 'California', lat: 37.7749, lng: -122.4194 },
  { city: 'Seattle', state: 'Washington', lat: 47.6062, lng: -122.3321 },
  { city: 'Denver', state: 'Colorado', lat: 39.7392, lng: -104.9903 },
  { city: 'Nashville', state: 'Tennessee', lat: 36.1627, lng: -86.7816 },
  { city: 'Atlanta', state: 'Georgia', lat: 33.7490, lng: -84.3880 },
  { city: 'Miami', state: 'Florida', lat: 25.7617, lng: -80.1918 },
  { city: 'Las Vegas', state: 'Nevada', lat: 36.1699, lng: -115.1398 },
  { city: 'Detroit', state: 'Michigan', lat: 42.3314, lng: -83.0458 },
  { city: 'Memphis', state: 'Tennessee', lat: 35.1495, lng: -90.0490 },
];

// === Blog posts (DB-backed, status-filtered) ===

export interface BlogPost {
  slug: string;
  title: string;
  category: string;
  category_label: string;
  description: string;
  seo_title: string;
  seo_description: string;
  read_time: string;
  publish_date: string;
  status: 'draft' | 'scheduled' | 'published';
  last_updated: string;
  sections: { heading: string; content: string }[];
  key_takeaways: string[];
  related_guides: string[];
  related_categories: string[];
  faq: { question: string; answer: string }[];
  tags: string[];
}

let _publishedBlogCache: BlogPost[] | null = null;
let _allBlogCache: BlogPost[] | null = null;

export async function getBlogPosts(): Promise<BlogPost[]> {
  if (_publishedBlogCache) return _publishedBlogCache;
  _publishedBlogCache = await queryJsonRows<BlogPost>(
    "SELECT data FROM blog_posts WHERE status = 'published'"
  );
  return _publishedBlogCache;
}

export async function getAllBlogPosts(): Promise<BlogPost[]> {
  if (_allBlogCache) return _allBlogCache;
  _allBlogCache = await queryJsonRows<BlogPost>("SELECT data FROM blog_posts");
  return _allBlogCache;
}

export async function getBlogPostBySlug(slug: string): Promise<BlogPost | undefined> {
  const all = await getBlogPosts();
  return all.find(p => p.slug === slug);
}

export async function getBlogPostsByCategory(category: string): Promise<BlogPost[]> {
  const all = await getBlogPosts();
  return all.filter(p => p.category === category);
}

// === Cluster answers (DB-backed) ===

export type ClusterPillar =
  | 'credit-score'
  | 'credit-repair'
  | 'build-credit'
  | 'personal-loans'
  | 'debt-relief'
  | 'credit-cards'
  | 'credit-monitoring'
  | 'identity-theft'
  | 'financial-wellness';

export type BannerCategory =
  | 'credit-repair'
  | 'personal-loans'
  | 'build-credit'
  | 'debt-relief'
  | 'credit-monitoring'
  | 'identity-theft';

export interface ClusterAnswerSection {
  heading: string;
  content: string;
}

export interface ClusterAnswerFAQ {
  question: string;
  answer: string;
}

export interface ClusterAnswerInternalLink {
  phrase: string;
  url: string;
  type: 'glossary' | 'money_listicle' | 'lender_profile' | 'sibling_answer' | 'category';
}

export interface ClusterAnswerPrimarySource {
  name: string;
  url: string;
}

export interface ClusterAnswer {
  slug: string;
  cluster_id: string;
  cluster_pillar: ClusterPillar;
  title: string;
  h1: string;
  meta_description: string;
  target_money_page: string;
  banner_category: BannerCategory;
  questions_answered: string[];
  sections: ClusterAnswerSection[];
  faq_schema: ClusterAnswerFAQ[];
  internal_links: ClusterAnswerInternalLink[];
  primary_sources: ClusterAnswerPrimarySource[];
  author?: string;
  reviewed_by?: string;
  published_at?: string;
  last_updated?: string;
  youtube_script?: string;
  reel_script?: string;
  email_snippet?: string;
  compliance_score?: number;
  compliance_passed?: boolean;
  status?: 'draft' | 'ready_for_review' | 'approved' | 'published';
}

let _clusterAnswersCache: ClusterAnswer[] | null = null;

export async function getClusterAnswers(): Promise<ClusterAnswer[]> {
  if (_clusterAnswersCache) return _clusterAnswersCache;
  _clusterAnswersCache = await queryJsonRows<ClusterAnswer>(
    "SELECT data FROM cluster_answers WHERE status = 'published'"
  );
  return _clusterAnswersCache;
}

export async function getClusterAnswerBySlug(slug: string): Promise<ClusterAnswer | undefined> {
  const all = await getClusterAnswers();
  return all.find(a => a.slug === slug);
}

export async function getClusterAnswersByPillar(pillar: ClusterPillar): Promise<ClusterAnswer[]> {
  const all = await getClusterAnswers();
  return all.filter(a => a.cluster_pillar === pillar);
}

export async function getClusterAnswersByCluster(cluster_id: string): Promise<ClusterAnswer[]> {
  const all = await getClusterAnswers();
  return all.filter(a => a.cluster_id === cluster_id);
}

export async function getSiblingClusterAnswers(slug: string, limit: number = 4): Promise<ClusterAnswer[]> {
  const self = await getClusterAnswerBySlug(slug);
  if (!self) return [];
  const all = await getClusterAnswers();
  return all
    .filter(a => a.slug !== slug && a.cluster_pillar === self.cluster_pillar)
    .slice(0, limit);
}

// === Education search composite ===

export async function getEducationSearchData() {
  const [guides, posts] = await Promise.all([getWellnessGuides(), getBlogPosts()]);
  const terms = getGlossaryTerms();

  return {
    guides: guides.map(g => ({
      slug: g.slug,
      title: g.title,
      description: g.description,
      category: g.category,
      read_time: g.read_time,
      type: 'guide' as const,
      url: `/financial-wellness/${g.slug}/`,
      key_takeaways: g.key_takeaways,
    })),
    terms: terms.map(t => ({
      slug: t.slug,
      title: t.term,
      description: t.plain_definition,
      category: t.category,
      full_form: t.full_form,
      type: 'term' as const,
      url: `/glossary/#${t.slug}`,
    })),
    posts: posts.map(p => ({
      slug: p.slug,
      title: p.title,
      description: p.description,
      category: p.category,
      read_time: p.read_time,
      tags: p.tags,
      type: 'post' as const,
      url: `/blog/${p.slug}/`,
      key_takeaways: p.key_takeaways,
    })),
  };
}
