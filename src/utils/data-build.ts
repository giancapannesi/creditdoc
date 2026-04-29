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
