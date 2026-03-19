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
}

export interface Category {
  slug: string;
  name: string;
  description: string;
  icon: string;
  seo_title: string;
  seo_description: string;
  count: number;
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

const LENDERS_DIR = path.join(process.cwd(), 'src/content/lenders');
const CONTENT_DIR = path.join(process.cwd(), 'src/content');

let _lendersCache: Lender[] | null = null;

export function getAllLenders(): Lender[] {
  if (_lendersCache) return _lendersCache;
  const files = fs.readdirSync(LENDERS_DIR).filter(f => f.endsWith('.json'));
  _lendersCache = files.map(f => {
    const raw = fs.readFileSync(path.join(LENDERS_DIR, f), 'utf-8');
    return JSON.parse(raw) as Lender;
  }).filter(l => l.review_status === 'published');
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

export function getBbbClass(rating: string): string {
  if (rating === 'A+' || rating === 'A') return 'bbb-a';
  if (rating === 'B+' || rating === 'B') return 'bbb-b';
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
