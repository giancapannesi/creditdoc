// Build-time fs-backed data accessors. Keeps node:fs out of the SSR Worker chunk.
// Pure types + pure helpers + constants stay in `data.ts` (zero-fs).
// Only import this module from build-time prerender pages — NEVER from components in BaseLayout.
import fs from 'node:fs';
import path from 'node:path';

import type {
  Lender,
  Category,
  Comparison,
  Listicle,
  Special,
  WellnessGuide,
  CityInfo,
  StateInfo,
  GlossaryTerm,
  BrandInfo,
  BlogPost,
  ClusterAnswer,
  ClusterPillar,
} from './data';
import { STATE_ABBREVIATIONS } from './data';

const LENDERS_DIR = path.join(process.cwd(), 'src/content/lenders');
const CONTENT_DIR = path.join(process.cwd(), 'src/content');
const BRANDS_DIR = path.join(process.cwd(), 'src/content/brands');
const ANSWERS_DIR = path.join(process.cwd(), 'src/content/answers');

let _lendersCache: Lender[] | null = null;

// DB is the live source of truth, but prerendered browse pages still read the
// static lender export. Keep archived review records out of static references.
const ARCHIVED_REVIEW_SLUGS = new Set([
  "vfs-global-india-passport-application-center",
  "fix-my-auto-credit-score",
  "autocarhouston-autos-usados",
  "ny-identity-theft-group",
  "auto-titles-and-bonds",
  "jm-auto-title-service-titulos-y-placas-surety-bond-title",
  "burns-buy-here-pay-here-of-spartanburg",
  "fraud",
  "good-price-title-auto-title-services-bonded-titles-by-appointment-only",
  "atlanta-buy-here-pay-here",
  "atlanta-international-auto-show",
  "austin-buy-here-pay-here",
  "auto-car-financing-oklahoma-city-ok",
  "auto-credit-chicago",
  "auto-financing-san-antonio",
  "auto-now",
  "auto-now-financial",
  "auto-now-financial-services",
  "auto-pawn-loans",
  "auto-smart-charlotte",
  "auto-title-loans",
  "auto-title-loans-personal-loans",
  "automatic-financing",
  "autovalley",
  "autowise-body-shop-used-cars-center",
  "b-and-b-auto-title-pawn",
  "buy-here-pay-here",
  "buy-here-pay-here-999-downcom",
  "buy-here-pay-here-bayonne",
  "buy-here-pay-here-clifton",
  "buy-here-pay-here-fl",
  "buy-here-pay-here-jersey-city",
  "buy-here-pay-here-newark",
  "buy-here-pay-here-of-long-island",
  "buy-here-pay-here-of-long-island-garden-city",
  "buy-here-pay-here-passaic",
  "buy-here-pay-here-union",
  "buy-here-pay-here-union-city",
  "cleveland-auto-nation",
  "cp-auto-center",
  "credex-auto-title-loans-west-flagler",
  "de-jesus-auto-tags",
  "dfw-buy-here-pay-here",
  "eazy-auto-finance",
  "echopark-automotive-atlanta-duluth",
  "echopark-los-angeles-long-beach-vehicle-buying-center",
  "equity-auto-loan",
  "finest-auto-leasing",
  "ganas-auto-fresno",
  "ganas-auto-long-beach",
  "ganas-auto-sacramento",
  "get-auto-title-loans-charlotte-mi",
  "hm-buy-here-pay-here",
  "kjc-auto-title-loans",
  "kjc-auto-title-loans-houston",
  "kjc-auto-title-loans-houston-tx",
  "kjc-auto-title-loans-san-antonio",
  "lease-with-ease-auto-awesome-leasing",
  "legacy-automotive-buy-here-pay-here",
  "loancenter-title-loans-at-georgia-peach-auto-sales",
  "louisville-buy-here-pay-here",
  "mars-auto-trade",
  "melrose-park-auto-credit",
  "pittsburgh-auto-shipping-group",
  "prestamo-por-titulo-de-auto-mvp-bell-gardens",
  "quick-cash-auto-loans",
  "quick-cash-auto-loans-cutler-bay",
  "rapid-auto-loans",
  "vehicles-for-sale-near-detroit-automotive",
  "youremergencycash-auto-title-loans",
  "fidelity-national-title-insurance-colorado-springs",
  "first-american-title-insurance-company-national-commercial",
  "first-american-title-insurance-company-national-commercial-pittsburgh",
  "houston-title",
  "title-one-agency-cincinnati-oh-title-company-with-best-rates",
  "consumer-frauds-and-protection-bureau",
  "emergency-expedited-passports-visa-expediting",
  "1st-merchant-advance",
  "aaca-ventures",
  "accepting-credit-cards",
  "all-american-credit-card",
  "ambitious-socialite",
  "america-title-loans",
  "apna-bazar-cash-carry",
  "arlington-legal-clinic",
  "as-confab",
  "atm-credit-card",
  "bankruptcy-lawyers-at-bankruptcy-done-right",
  "brownstone-law-group",
  "capital-pawn-gold-jewelry-buyers",
  "car-credit-giant",
  "car-fast-financial",
  "car-lease-deals-direct-new-york",
  "car-title-loans",
  "car-title-loans-paradise",
  "car-title-loans-san-francisco",
  "careone-credit",
  "careone-credit-chicago",
  "careone-credit-miami",
  "careone-credit-san-francis",
  "cash-carry-store",
  "cash-loans-on-car-titles-chicago",
  "cash-loans-on-car-titles-duncanville",
  "checks-cashed-loans-debit-cards",
  "chicago-legal-debt-solutions",
  "coinstar-kiosk-bitcoin-atm",
  "credit-card-line",
  "credit-card-processing",
  "credit-card-processing-seattle",
  "credit-card-services",
  "credit-cards",
  "credit-care-advocates",
  "debonair-credit-care",
  "gold-x-financial",
  "grand-jewelry-pawn-shop",
  "green-sheet-tax-debt-attorney",
  "inspired-merchant-credit-card-processing-services",
  "irs-debt-assistance-attorney",
  "isource-prepaid-credit-card",
  "jonny-g-title-pay-day-loans",
  "just-call-foreclosure-lawyer",
  "law-office-of-jack-g-lezman-pllc-charlotte-bankruptcy-attorney",
  "libertyx-bitcoin-atm-brooklyn",
  "loancenter-title-loans-at-rumba-money-centers-atlanta",
  "merchant-services-club-free-credit-card-terminal",
  "merchant-services-club-free-credit-card-terminal-charlotte",
  "merchant-services-club-free-credit-card-terminals-columbus",
]);

const ABBR_TO_FULL_STATE: Record<string, string> = Object.fromEntries(
  Object.entries(STATE_ABBREVIATIONS).map(([full, abbr]) => [abbr, full])
);

function normalizeStateAbbr(state: string | null | undefined): string | null {
  if (!state) return null;
  const trimmed = state.trim();
  if (!trimmed) return null;

  const upper = trimmed.toUpperCase();
  if (ABBR_TO_FULL_STATE[upper]) return upper;

  return STATE_ABBREVIATIONS[trimmed] ?? null;
}

function slugifyCity(city: string): string {
  return city
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

export function getAllLenders(): Lender[] {
  if (_lendersCache) return _lendersCache;
  const files = fs.readdirSync(LENDERS_DIR).filter(f => f.endsWith('.json'));
  _lendersCache = files.map(f => {
    const raw = fs.readFileSync(path.join(LENDERS_DIR, f), 'utf-8');
    const l = JSON.parse(raw) as Lender;
    l.subcategories = Array.isArray(l.subcategories) ? l.subcategories : [];
    l.states_served = Array.isArray(l.states_served) ? l.states_served : [];
    l.cities_served = Array.isArray(l.cities_served) ? l.cities_served : [];
    l.best_for = Array.isArray(l.best_for) ? l.best_for : [];
    l.services = Array.isArray(l.services) ? l.services : [];
    l.similar_lenders = Array.isArray(l.similar_lenders) ? l.similar_lenders : [];
    l.pros = Array.isArray(l.pros) ? l.pros : [];
    l.cons = Array.isArray(l.cons) ? l.cons : [];
    return l;
  }).filter(l => {
    if (ARCHIVED_REVIEW_SLUGS.has(l.slug)) return false;
    const ps = (l as any).processing_status;
    if (ps) return ps === 'ready_for_index' || ps === 'pending_approval';
    return l.review_status === 'published';
  });
  return _lendersCache;
}

export function getLenderBySlug(slug: string): Lender | undefined {
  return getAllLenders().find(l => l.slug === slug);
}

export function getLendersByCategory(category: string): Lender[] {
  return getAllLenders().filter(l => l.category === category || (l.subcategories ?? []).includes(category));
}

export function getLendersByState(state: string): Lender[] {
  const s = state.toLowerCase();
  return getAllLenders().filter(l => {
    const states = l.states_served ?? [];
    return states.some(st => st.toLowerCase() === s) || states.includes('All 50 States');
  });
}

export function getLendersByCity(city: string): Lender[] {
  const c = city.toLowerCase();
  return getAllLenders().filter(l => {
    const cities = l.cities_served ?? [];
    const states = l.states_served ?? [];
    return cities.some(ct => ct.toLowerCase() === c) || states.includes('All 50 States');
  });
}

export function getCategories(): Category[] {
  const raw = fs.readFileSync(path.join(CONTENT_DIR, 'categories.json'), 'utf-8');
  const categories = JSON.parse(raw) as Category[];
  const lenders = getAllLenders();
  return categories.map(c => ({
    ...c,
    count: lenders.filter(l => l.category === c.slug || (l.subcategories ?? []).includes(c.slug)).length,
  }));
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

export function getCitiesWithLenders(minCount: number = 5): CityInfo[] {
  const cityMap = new Map<string, { city: string; state: string; count: number }>();
  for (const l of getAllLenders()) {
    const city = l.company_info.city;
    const state = normalizeStateAbbr(l.company_info.state);
    if (!city || !state) continue;
    const cityKey = city.trim().toLowerCase();
    const key = `${cityKey}|${state}`;
    const existing = cityMap.get(key);
    if (existing) {
      existing.count++;
    } else {
      cityMap.set(key, { city: city.trim(), state, count: 1 });
    }
  }

  return Array.from(cityMap.values())
    .filter(c => c.count >= minCount)
    .map(c => {
      const fullState = ABBR_TO_FULL_STATE[c.state] || c.state;
      const slug = `${slugifyCity(c.city)}-${c.state.toLowerCase()}`;
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
  const cityKey = city.trim().toLowerCase();
  const targetState = normalizeStateAbbr(stateAbbr);
  return getAllLenders().filter(l =>
    l.company_info.city?.trim().toLowerCase() === cityKey &&
    normalizeStateAbbr(l.company_info.state) === targetState
  );
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

export function getAllStatesInfo(): { name: string; abbr: string; slug: string }[] {
  const data = getStateData();
  return Object.entries(data).map(([abbr, info]: [string, any]) => ({
    name: info.name,
    abbr,
    slug: info.name.toLowerCase().replace(/\s+/g, '-'),
  }));
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

let _brandsCache: BrandInfo[] | null = null;

export function getAllBrands(): BrandInfo[] {
  if (_brandsCache) return _brandsCache;
  if (!fs.existsSync(BRANDS_DIR)) {
    _brandsCache = [];
    return _brandsCache;
  }
  const files = fs.readdirSync(BRANDS_DIR).filter(f => f.endsWith('.json'));
  const lenders = getAllLenders();
  _brandsCache = files.map(f => {
    const raw = fs.readFileSync(path.join(BRANDS_DIR, f), 'utf-8');
    const brand = JSON.parse(raw) as BrandInfo;
    brand.location_count = lenders.filter(l => l.brand_slug === brand.slug).length;
    return brand;
  });
  return _brandsCache;
}

export function getBrandInfo(slug: string): BrandInfo | null {
  const brands = getAllBrands();
  return brands.find(b => b.slug === slug) ?? null;
}

export function getLendersByBrand(slug: string): Lender[] {
  return getAllLenders().filter(l => l.brand_slug === slug);
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

let _clusterAnswersCache: ClusterAnswer[] | null = null;

export function getClusterAnswers(): ClusterAnswer[] {
  if (_clusterAnswersCache) return _clusterAnswersCache;
  if (!fs.existsSync(ANSWERS_DIR)) {
    _clusterAnswersCache = [];
    return _clusterAnswersCache;
  }
  const files = fs.readdirSync(ANSWERS_DIR).filter(f => f.endsWith('.json'));
  _clusterAnswersCache = files.map(f => {
    const raw = fs.readFileSync(path.join(ANSWERS_DIR, f), 'utf-8');
    return JSON.parse(raw) as ClusterAnswer;
  });
  return _clusterAnswersCache;
}

export function getClusterAnswerBySlug(slug: string): ClusterAnswer | undefined {
  return getClusterAnswers().find(a => a.slug === slug);
}

export function getClusterAnswersByPillar(pillar: ClusterPillar): ClusterAnswer[] {
  return getClusterAnswers().filter(a => a.cluster_pillar === pillar);
}

export function getClusterAnswersByCluster(cluster_id: string): ClusterAnswer[] {
  return getClusterAnswers().filter(a => a.cluster_id === cluster_id);
}

export function getSiblingClusterAnswers(slug: string, limit: number = 4): ClusterAnswer[] {
  const self = getClusterAnswerBySlug(slug);
  if (!self) return [];
  return getClusterAnswers()
    .filter(a => a.slug !== slug && a.cluster_pillar === self.cluster_pillar)
    .slice(0, limit);
}

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
