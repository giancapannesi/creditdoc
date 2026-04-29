// Pure types, constants, and side-effect-free helpers.
// fs-backed accessors live in `data-build.ts` (build-time prerender only).
// This module is safe to import from BaseLayout/Header/Footer + any SSR component.

// Entity-type badge matrix (2026-04-19) — governs which category of lender
// is eligible to show the "Free Consultation" and "Free to Use" badges.
// Background: pawn shops, check cashers, ATMs etc. don't offer consultations
// and aren't free to use (they charge per-transaction). Gate badges accordingly.
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

export interface CityInfo {
  city: string;
  state: string;
  stateAbbr: string;
  slug: string;
  count: number;
}

export interface StateInfo {
  name: string;
  abbr: string;
  slug: string;
  lenderCount: number;
  cityCount: number;
  topCities: string[];
}

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

// --- Pure helpers ---

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

// --- Constants ---

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
