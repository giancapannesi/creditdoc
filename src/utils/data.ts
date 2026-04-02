import fs from 'node:fs';
import path from 'node:path';

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
  // Directory listing fields (optional — from Outscraper DB)
  data_source?: string;
  google_rating?: number;
  google_reviews_count?: number;
  phone?: string;
  address?: string;
  // Loan-specific fields (optional — only for loan lenders)
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

const LENDERS_DIR = path.join(process.cwd(), 'src/content/lenders');
const CONTENT_DIR = path.join(process.cwd(), 'src/content');

let _lendersCache: Lender[] | null = null;

export function getAllLenders(): Lender[] {
  if (_lendersCache) return _lendersCache;
  const files = fs.readdirSync(LENDERS_DIR).filter(f => f.endsWith('.json'));
  _lendersCache = files.map(f => {
    const raw = fs.readFileSync(path.join(LENDERS_DIR, f), 'utf-8');
    return JSON.parse(raw) as Lender;
  }).filter(l => {
    // State-machine gate: ready_for_index + pending_approval (for founder review)
    if (l.processing_status) return l.processing_status === 'ready_for_index' || l.processing_status === 'pending_approval';
    // Backward compatibility: if migration hasn't run yet, use old logic
    return l.review_status === 'published';
  });
  return _lendersCache;
}

export function getLenderBySlug(slug: string): Lender | undefined {
  return getAllLenders().find(l => l.slug === slug);
}

export function getLendersByCategory(category: string): Lender[] {
  return getAllLenders().filter(l => l.category === category || l.subcategories.includes(category));
}

export function getLendersByState(state: string): Lender[] {
  const s = state.toLowerCase();
  return getAllLenders().filter(l =>
    l.states_served.some(st => st.toLowerCase() === s) ||
    l.states_served.includes('All 50 States')
  );
}

export function getLendersByCity(city: string): Lender[] {
  const c = city.toLowerCase();
  return getAllLenders().filter(l =>
    l.cities_served.some(ct => ct.toLowerCase() === c) ||
    l.states_served.includes('All 50 States')
  );
}

export function getCategories(): Category[] {
  const raw = fs.readFileSync(path.join(CONTENT_DIR, 'categories.json'), 'utf-8');
  return JSON.parse(raw) as Category[];
}

export function getComparisons(): Comparison[] {
  const raw = fs.readFileSync(path.join(CONTENT_DIR, 'comparisons.json'), 'utf-8');
  return JSON.parse(raw) as Comparison[];
}

export function getComparisonBySlug(slug: string): Comparison | undefined {
  return getComparisons().find(c => c.slug === slug);
}

export function getListicles(): Listicle[] {
  const raw = fs.readFileSync(path.join(CONTENT_DIR, 'listicles.json'), 'utf-8');
  return JSON.parse(raw) as Listicle[];
}

export function getListicleBySlug(slug: string): Listicle | undefined {
  return getListicles().find(l => l.slug === slug);
}

export function getSpecials(): Special[] {
  const raw = fs.readFileSync(path.join(CONTENT_DIR, 'specials.json'), 'utf-8');
  return JSON.parse(raw) as Special[];
}

export function getWellnessGuides(): WellnessGuide[] {
  const raw = fs.readFileSync(path.join(CONTENT_DIR, 'wellness-guides.json'), 'utf-8');
  return JSON.parse(raw) as WellnessGuide[];
}

export function getWellnessGuideBySlug(slug: string): WellnessGuide | undefined {
  return getWellnessGuides().find(g => g.slug === slug);
}

export function getWellnessGuidesByCategory(category: string): WellnessGuide[] {
  return getWellnessGuides().filter(g => g.category === category);
}

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

export function getAllStates(): string[] {
  const states = new Set<string>();
  for (const l of getAllLenders()) {
    for (const s of l.states_served) {
      if (s !== 'All 50 States') states.add(s);
    }
  }
  return Array.from(states).sort();
}

export function getAllCities(): string[] {
  const cities = new Set<string>();
  for (const l of getAllLenders()) {
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

export function getCitiesWithLenders(minCount: number = 5): CityInfo[] {
  const cityMap = new Map<string, { city: string; state: string; count: number }>();
  for (const l of getAllLenders()) {
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

export function getLendersByCityState(city: string, stateAbbr: string): Lender[] {
  return getAllLenders().filter(l =>
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

export function getStatesWithLenders(minCount: number = 1): StateInfo[] {
  const stateMap = new Map<string, { count: number; cities: Set<string> }>();
  for (const l of getAllLenders()) {
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

export function getLendersInState(stateAbbr: string): Lender[] {
  return getAllLenders().filter(l => l.company_info.state === stateAbbr);
}

export function getStateData(): Record<string, any> {
  const dataPath = path.join(process.cwd(), 'src/content/states.json');
  if (!fs.existsSync(dataPath)) return {};
  return JSON.parse(fs.readFileSync(dataPath, 'utf-8'));
}

/** Returns all 50 states from states.json — no lender-count dependency */
export function getAllStatesInfo(): { name: string; abbr: string; slug: string }[] {
  const data = getStateData();
  return Object.entries(data).map(([abbr, info]: [string, any]) => ({
    name: info.name,
    abbr,
    slug: info.name.toLowerCase().replace(/\s+/g, '-'),
  }));
}

// --- Glossary Terms ---

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

// --- Blog Posts ---

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

export function getBlogPosts(): BlogPost[] {
  const raw = fs.readFileSync(path.join(CONTENT_DIR, 'blog-posts.json'), 'utf-8');
  const all = JSON.parse(raw) as BlogPost[];
  return all.filter(p => p.status === 'published');
}

export function getAllBlogPosts(): BlogPost[] {
  const raw = fs.readFileSync(path.join(CONTENT_DIR, 'blog-posts.json'), 'utf-8');
  return JSON.parse(raw) as BlogPost[];
}

export function getBlogPostBySlug(slug: string): BlogPost | undefined {
  return getBlogPosts().find(p => p.slug === slug);
}

export function getBlogPostsByCategory(category: string): BlogPost[] {
  return getBlogPosts().filter(p => p.category === category);
}

// --- Education Search Data ---

export function getEducationSearchData() {
  const guides = getWellnessGuides().map(g => ({
    slug: g.slug,
    title: g.title,
    description: g.description,
    category: g.category,
    read_time: g.read_time,
    type: 'guide' as const,
    url: `/financial-wellness/${g.slug}/`,
    key_takeaways: g.key_takeaways,
  }));

  const terms = getGlossaryTerms().map(t => ({
    slug: t.slug,
    title: t.term,
    description: t.plain_definition,
    category: t.category,
    full_form: t.full_form,
    type: 'term' as const,
    url: `/glossary/#${t.slug}`,
  }));

  const posts = getBlogPosts().map(p => ({
    slug: p.slug,
    title: p.title,
    description: p.description,
    category: p.category,
    read_time: p.read_time,
    tags: p.tags,
    type: 'post' as const,
    url: `/blog/${p.slug}/`,
    key_takeaways: p.key_takeaways,
  }));

  return { guides, terms, posts };
}
