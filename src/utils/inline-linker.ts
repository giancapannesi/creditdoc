/**
 * Inline Linker — Auto-links glossary terms and money keywords in review page text.
 * 
 * Two link types:
 * 1. Money keywords → /best/slug/ or /categories/slug/ (bold green, commercial)
 * 2. Glossary terms → /glossary/#slug (dotted underline, educational)
 * 
 * Rules:
 * - Each unique term linked only ONCE across the entire description
 * - Whole-word matching only, case-insensitive
 * - Money links take priority over glossary for same phrase
 * - Longer phrases match first (prevents partial matches)
 * - Max ~5 money links + ~5 glossary links total across all paragraphs
 */

interface GlossaryTerm {
  term: string;
  slug: string;
  plain_definition: string;
}

interface MoneyLink {
  phrase: string;
  url: string;
  title: string;
}

const MONEY_LINKS: MoneyLink[] = [
  { phrase: 'credit repair companies', url: '/best/best-credit-repair-companies/', title: 'Best Credit Repair Companies' },
  { phrase: 'credit repair services', url: '/best/best-credit-repair-companies/', title: 'Best Credit Repair Companies' },
  { phrase: 'debt relief companies', url: '/best/best-debt-relief-companies/', title: 'Best Debt Relief Companies' },
  { phrase: 'debt relief programs', url: '/best/best-debt-relief-companies/', title: 'Best Debt Relief Companies' },
  { phrase: 'personal loans for bad credit', url: '/best/best-personal-loans-bad-credit/', title: 'Best Personal Loans for Bad Credit' },
  { phrase: 'personal loan lenders', url: '/best/best-personal-loan-lenders/', title: 'Best Personal Loan Lenders' },
  { phrase: 'debt consolidation loans', url: '/best/best-debt-consolidation-loans/', title: 'Best Debt Consolidation Loans' },
  { phrase: 'debt consolidation', url: '/best/best-debt-consolidation-loans/', title: 'Best Debt Consolidation Loans' },
  { phrase: 'credit builder loans', url: '/best/best-credit-builder-loans/', title: 'Best Credit Builder Loans' },
  { phrase: 'secured credit cards', url: '/best/best-secured-credit-cards/', title: 'Best Secured Credit Cards' },
  { phrase: 'credit monitoring services', url: '/best/best-credit-monitoring-services/', title: 'Best Credit Monitoring Services' },
  { phrase: 'credit monitoring', url: '/best/best-credit-monitoring-services/', title: 'Best Credit Monitoring Services' },
  { phrase: 'cash advance apps', url: '/best/best-cash-advance-apps/', title: 'Best Cash Advance Apps' },
  { phrase: 'payday loan alternatives', url: '/best/best-payday-loan-alternatives/', title: 'Best Payday Loan Alternatives' },
  { phrase: 'credit counseling', url: '/best/best-credit-counseling-agencies/', title: 'Best Credit Counseling Agencies' },
  { phrase: 'identity theft protection', url: '/best/best-identity-theft-protection/', title: 'Best Identity Theft Protection' },
  { phrase: 'rent reporting', url: '/best/best-rent-reporting-services/', title: 'Best Rent Reporting Services' },
  { phrase: 'credit score simulator', url: '/tools/credit-score-simulator/', title: 'Credit Score Simulator' },
  { phrase: 'borrowing power', url: '/tools/borrowing-power-quiz/', title: 'Borrowing Power Quiz' },
  { phrase: 'debt payoff calculator', url: '/tools/debt-payoff-calculator/', title: 'Debt Payoff Calculator' },
  { phrase: 'credit repair', url: '/categories/credit-repair/', title: 'Credit Repair Companies' },
  { phrase: 'fix my credit', url: '/categories/credit-repair/', title: 'Credit Repair Companies' },
  { phrase: 'debt relief', url: '/categories/debt-relief/', title: 'Debt Relief Services' },
  { phrase: 'best instalment loans', url: '/best/best-personal-loan-lenders/', title: 'Best Personal Loan Lenders' },
  { phrase: 'personal installment loans', url: '/best/best-personal-loan-lenders/', title: 'Best Personal Loan Lenders' },
  { phrase: 'installment lenders', url: '/best/best-personal-loan-lenders/', title: 'Best Personal Loan Lenders' },
  { phrase: 'instalment loan', url: '/categories/personal-loans/', title: 'Personal Loan Lenders' },
  { phrase: 'installment loans', url: '/categories/personal-loans/', title: 'Personal Loan Lenders' },
  { phrase: 'personal loans', url: '/categories/personal-loans/', title: 'Personal Loan Lenders' },
  // 2026-04-15: added to cover all 18 live /best/ listicles per INTERLINKING_MAP.md
  { phrase: 'no credit check credit cards', url: '/best/best-no-credit-check-cards/', title: 'Best No Credit Check Cards' },
  { phrase: 'no credit check cards', url: '/best/best-no-credit-check-cards/', title: 'Best No Credit Check Cards' },
  { phrase: 'cheapest personal loans', url: '/best/cheapest-personal-loans/', title: 'Cheapest Personal Loans' },
  { phrase: 'lowest rate personal loans', url: '/best/cheapest-personal-loans/', title: 'Cheapest Personal Loans' },
  { phrase: 'credit repair money back guarantee', url: '/best/best-credit-repair-money-back-guarantee/', title: 'Credit Repair with Money Back Guarantee' },
  { phrase: 'credit repair for veterans', url: '/best/best-credit-repair-veterans/', title: 'Best Credit Repair for Veterans' },
  { phrase: 'credit repair after bankruptcy', url: '/best/best-credit-repair-after-bankruptcy/', title: 'Best Credit Repair After Bankruptcy' },
];

const SORTED_MONEY_LINKS = [...MONEY_LINKS].sort((a, b) => b.phrase.length - a.phrase.length);

function escapeHtml(text: string): string {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function escapeRegex(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function linkifyParagraph(
  text: string,
  glossaryTerms: GlossaryTerm[],
  usedPhrases: Set<string>,
  moneyBudget: { remaining: number },
  glossaryBudget: { remaining: number },
): string {
  const linked = new Array(text.length).fill(false);
  const replacements: [number, number, string][] = [];

  // Money links
  for (const ml of SORTED_MONEY_LINKS) {
    if (moneyBudget.remaining <= 0) break;
    const lower = ml.phrase.toLowerCase();
    if (usedPhrases.has(lower)) continue;

    const regex = new RegExp(`\\b(${escapeRegex(ml.phrase)})\\b`, 'i');
    const match = regex.exec(text);
    if (!match) continue;

    const start = match.index;
    const end = start + match[0].length;
    if (linked.slice(start, end).some(Boolean)) continue;

    replacements.push([start, end,
      `<a href="${ml.url}" class="text-primary font-semibold hover:underline" title="${escapeHtml(ml.title)}">${escapeHtml(match[0])}</a>`
    ]);
    for (let i = start; i < end; i++) linked[i] = true;
    usedPhrases.add(lower);
    moneyBudget.remaining--;
  }

  // Glossary links
  const sortedTerms = [...glossaryTerms].sort((a, b) => b.term.length - a.term.length);
  for (const term of sortedTerms) {
    if (glossaryBudget.remaining <= 0) break;
    const lower = term.term.toLowerCase();
    if (usedPhrases.has(lower)) continue;

    const regex = new RegExp(`\\b(${escapeRegex(term.term)})\\b`, 'i');
    const match = regex.exec(text);
    if (!match) continue;

    const start = match.index;
    const end = start + match[0].length;
    if (linked.slice(start, end).some(Boolean)) continue;

    replacements.push([start, end,
      `<a href="/glossary/#${term.slug}" class="text-muted underline decoration-dotted decoration-primary/40 hover:text-primary hover:decoration-solid transition-colors" title="${escapeHtml(term.plain_definition.slice(0, 120))}">${escapeHtml(match[0])}</a>`
    ]);
    for (let i = start; i < end; i++) linked[i] = true;
    usedPhrases.add(lower);
    glossaryBudget.remaining--;
  }

  // Build result
  replacements.sort((a, b) => a[0] - b[0]);
  if (replacements.length === 0) return escapeHtml(text);

  let result = '';
  let lastEnd = 0;
  for (const [start, end, html] of replacements) {
    result += escapeHtml(text.slice(lastEnd, start));
    result += html;
    lastEnd = end;
  }
  result += escapeHtml(text.slice(lastEnd));
  return result;
}

/**
 * Process full description_long. Each term linked only once across all paragraphs.
 * Used by /review/[slug].astro — caps stay at 5 money + 5 glossary (legacy behaviour).
 */
export function linkifyDescription(
  descriptionLong: string,
  glossaryTerms: GlossaryTerm[],
  currentSlug: string = '',
): string[] {
  const usedPhrases = new Set<string>();
  const moneyBudget = { remaining: 5 };
  const glossaryBudget = { remaining: 5 };

  return descriptionLong.split('\n\n').map(paragraph =>
    linkifyParagraph(paragraph, glossaryTerms, usedPhrases, moneyBudget, glossaryBudget)
  );
}

/**
 * Per-page linker factory. Holds usedPhrases + budget ACROSS multiple calls,
 * so a template rendering N sections can call linker(section1) ... linker(sectionN)
 * and the "each term linked once per page" rule persists across sections.
 *
 * Used by /answers/[slug].astro — default caps 8 money + 8 glossary (per Apr 12 plan).
 */
export interface PageLinker {
  (text: string): string[];
  usedPhrases: Set<string>;
  moneyRemaining: () => number;
  glossaryRemaining: () => number;
}

export function createLinker(
  glossaryTerms: GlossaryTerm[],
  opts: { moneyBudget?: number; glossaryBudget?: number } = {},
): PageLinker {
  const usedPhrases = new Set<string>();
  const moneyBudget = { remaining: opts.moneyBudget ?? 8 };
  const glossaryBudget = { remaining: opts.glossaryBudget ?? 8 };

  const fn = ((text: string): string[] =>
    text.split('\n\n').map(paragraph =>
      linkifyParagraph(paragraph, glossaryTerms, usedPhrases, moneyBudget, glossaryBudget)
    )) as PageLinker;
  fn.usedPhrases = usedPhrases;
  fn.moneyRemaining = () => moneyBudget.remaining;
  fn.glossaryRemaining = () => glossaryBudget.remaining;
  return fn;
}
