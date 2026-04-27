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
  // 2026-04-17: business loan keywords → /best/ listicle pages
  { phrase: 'small business loans', url: '/best/best-small-business-loans/', title: 'Best Small Business Loans' },
  { phrase: 'small business loan', url: '/best/best-small-business-loans/', title: 'Best Small Business Loans' },
  { phrase: 'business line of credit', url: '/best/best-business-lines-of-credit/', title: 'Best Business Lines of Credit' },
  { phrase: 'SBA loans', url: '/best/best-sba-loans/', title: 'Best SBA Loans' },
  { phrase: 'SBA loan', url: '/best/best-sba-loans/', title: 'Best SBA Loans' },
  { phrase: 'merchant cash advance', url: '/best/best-merchant-cash-advance/', title: 'Best Merchant Cash Advance' },
  { phrase: 'equipment financing', url: '/best/best-equipment-financing/', title: 'Best Equipment Financing' },
  { phrase: 'invoice factoring', url: '/best/best-invoice-factoring/', title: 'Best Invoice Factoring' },
  { phrase: 'startup business loans', url: '/best/best-startup-business-loans/', title: 'Best Startup Business Loans' },
  { phrase: 'bad credit business loans', url: '/best/best-bad-credit-business-loans/', title: 'Best Bad Credit Business Loans' },
  { phrase: 'business funding', url: '/best/best-small-business-loans/', title: 'Best Small Business Loans' },
  { phrase: 'working capital loan', url: '/best/best-small-business-loans/', title: 'Best Small Business Loans' },
  { phrase: 'business loans', url: '/best/best-small-business-loans/', title: 'Best Small Business Loans' },
  // 2026-04-27 P0.6 follow-up: fill remaining biz-loan keyword gaps from
  // BUSINESS_LOANS_CONTENT_PIPELINE_PLAN.md Phase B. Lifts inbound coverage
  // on 9 orphan biz-loan money pages across all /answers/ + /review/* text.
  { phrase: 'business loan', url: '/best/best-small-business-loans/', title: 'Best Small Business Loans' },
  { phrase: 'commercial loan', url: '/best/best-small-business-loans/', title: 'Best Small Business Loans' },
  { phrase: 'SBA 7(a) loan', url: '/best/best-sba-loans/', title: 'Best SBA Loans' },
  { phrase: 'SBA 7a loan', url: '/best/best-sba-loans/', title: 'Best SBA Loans' },
  { phrase: 'MCA', url: '/best/best-merchant-cash-advance/', title: 'Best Merchant Cash Advance' },
  { phrase: 'equipment loan', url: '/best/best-equipment-financing/', title: 'Best Equipment Financing' },
  { phrase: 'startup funding', url: '/best/best-startup-business-loans/', title: 'Best Startup Business Loans' },
  { phrase: 'startup loan', url: '/best/best-startup-business-loans/', title: 'Best Startup Business Loans' },
  { phrase: 'bad credit business loan', url: '/best/best-bad-credit-business-loans/', title: 'Best Bad Credit Business Loans' },
  { phrase: 'accounts receivable financing', url: '/best/best-invoice-factoring/', title: 'Best Invoice Factoring' },
  { phrase: 'working capital', url: '/best/best-business-lines-of-credit/', title: 'Best Business Lines of Credit' },
  // 2026-04-21: widen coverage for non-credit-repair verticals — pawn, bankruptcy,
  // mortgages, emergency-cash (title/payday), check-cashing, banking, credit unions,
  // auto finance. Fires inline links on the 117 Tier A Places-enriched profiles and
  // the 6,044 FDIC bank / 2,296 NCUA credit-union rows.
  // Pawn / gold / jewelry
  { phrase: 'pawn shop loans', url: '/categories/pawn-shops/', title: 'Pawn Shops' },
  { phrase: 'pawn shops', url: '/categories/pawn-shops/', title: 'Pawn Shops' },
  { phrase: 'pawn shop', url: '/categories/pawn-shops/', title: 'Pawn Shops' },
  { phrase: 'pawn loans', url: '/categories/pawn-shops/', title: 'Pawn Shops' },
  { phrase: 'pawn broker', url: '/categories/pawn-shops/', title: 'Pawn Shops' },
  { phrase: 'gold and jewelry', url: '/categories/pawn-shops/', title: 'Gold Dealers & Pawn' },
  { phrase: 'gold dealer', url: '/categories/pawn-shops/', title: 'Gold Dealers & Pawn' },
  { phrase: 'jewelry loan', url: '/categories/pawn-shops/', title: 'Jewelry Loans' },
  // Bankruptcy
  { phrase: 'chapter 7 bankruptcy', url: '/categories/bankruptcy/', title: 'Bankruptcy Services' },
  { phrase: 'chapter 13 bankruptcy', url: '/categories/bankruptcy/', title: 'Bankruptcy Services' },
  { phrase: 'bankruptcy attorney', url: '/categories/bankruptcy/', title: 'Bankruptcy Services' },
  { phrase: 'bankruptcy filing', url: '/categories/bankruptcy/', title: 'Bankruptcy Services' },
  { phrase: 'bankruptcy services', url: '/categories/bankruptcy/', title: 'Bankruptcy Services' },
  { phrase: 'bankruptcy law', url: '/categories/bankruptcy/', title: 'Bankruptcy Services' },
  { phrase: 'chapter 7', url: '/categories/bankruptcy/', title: 'Bankruptcy Services' },
  { phrase: 'chapter 13', url: '/categories/bankruptcy/', title: 'Bankruptcy Services' },
  { phrase: 'bankruptcy', url: '/categories/bankruptcy/', title: 'Bankruptcy Services' },
  // Mortgages / home loans
  { phrase: 'mortgage refinance', url: '/categories/mortgages/', title: 'Home Loans & Mortgages' },
  { phrase: 'mortgage lenders', url: '/categories/mortgages/', title: 'Home Loans & Mortgages' },
  { phrase: 'mortgage loans', url: '/categories/mortgages/', title: 'Home Loans & Mortgages' },
  { phrase: 'home loans', url: '/categories/mortgages/', title: 'Home Loans & Mortgages' },
  { phrase: 'home loan', url: '/categories/mortgages/', title: 'Home Loans & Mortgages' },
  { phrase: 'refinance', url: '/categories/mortgages/', title: 'Home Loans & Mortgages' },
  { phrase: 'mortgage', url: '/categories/mortgages/', title: 'Home Loans & Mortgages' },
  // Title loans / payday / emergency-cash
  { phrase: 'car title loans', url: '/categories/emergency-cash/', title: 'Emergency Cash & Title Loans' },
  { phrase: 'auto title loans', url: '/categories/emergency-cash/', title: 'Emergency Cash & Title Loans' },
  { phrase: 'title loans', url: '/categories/emergency-cash/', title: 'Emergency Cash & Title Loans' },
  { phrase: 'title loan', url: '/categories/emergency-cash/', title: 'Emergency Cash & Title Loans' },
  { phrase: 'payday loans', url: '/best/best-payday-loan-alternatives/', title: 'Best Payday Loan Alternatives' },
  { phrase: 'payday loan', url: '/best/best-payday-loan-alternatives/', title: 'Best Payday Loan Alternatives' },
  { phrase: 'cash advance', url: '/best/best-cash-advance-apps/', title: 'Best Cash Advance Apps' },
  { phrase: 'short-term lending', url: '/categories/emergency-cash/', title: 'Short-Term Lending' },
  { phrase: 'short-term loans', url: '/categories/emergency-cash/', title: 'Short-Term Loans' },
  { phrase: 'short term loans', url: '/categories/emergency-cash/', title: 'Short-Term Loans' },
  { phrase: 'emergency loan', url: '/categories/emergency-cash/', title: 'Emergency Cash Loans' },
  { phrase: 'quick cash', url: '/categories/emergency-cash/', title: 'Emergency Cash Loans' },
  // Check cashing / money services
  { phrase: 'check cashing services', url: '/categories/check-cashing/', title: 'Check Cashing Services' },
  { phrase: 'check cashing', url: '/categories/check-cashing/', title: 'Check Cashing Services' },
  { phrase: 'money orders', url: '/categories/check-cashing/', title: 'Money Orders & Check Cashing' },
  { phrase: 'money order', url: '/categories/check-cashing/', title: 'Money Orders & Check Cashing' },
  { phrase: 'wire transfers', url: '/categories/check-cashing/', title: 'Money Services' },
  { phrase: 'wire transfer', url: '/categories/check-cashing/', title: 'Money Services' },
  { phrase: 'money transfer', url: '/categories/check-cashing/', title: 'Money Transfer Services' },
  // Banking
  { phrase: 'checking accounts', url: '/categories/banking/', title: 'Banks & Banking' },
  { phrase: 'checking account', url: '/categories/banking/', title: 'Banks & Banking' },
  { phrase: 'savings accounts', url: '/categories/banking/', title: 'Banks & Banking' },
  { phrase: 'savings account', url: '/categories/banking/', title: 'Banks & Banking' },
  { phrase: 'certificates of deposit', url: '/categories/banking/', title: 'Banks & Banking' },
  // Credit unions
  { phrase: 'credit unions', url: '/categories/credit-unions/', title: 'Credit Unions' },
  { phrase: 'credit union', url: '/categories/credit-unions/', title: 'Credit Unions' },
  // Auto finance
  { phrase: 'used car financing', url: '/categories/personal-loans/', title: 'Personal & Auto Loans' },
  { phrase: 'auto loans', url: '/categories/personal-loans/', title: 'Personal & Auto Loans' },
  { phrase: 'auto loan', url: '/categories/personal-loans/', title: 'Personal & Auto Loans' },
  { phrase: 'car finance', url: '/categories/personal-loans/', title: 'Personal & Auto Loans' },
  { phrase: 'car loans', url: '/categories/personal-loans/', title: 'Personal & Auto Loans' },
  { phrase: 'car loan', url: '/categories/personal-loans/', title: 'Personal & Auto Loans' },
];

const SORTED_MONEY_LINKS = [...MONEY_LINKS].sort((a, b) => b.phrase.length - a.phrase.length);

function escapeHtml(text: string): string {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function escapeRegex(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

export interface AffiliateConfig {
  url: string;
  anchors: string[];
}

function linkifyParagraph(
  text: string,
  glossaryTerms: GlossaryTerm[],
  usedPhrases: Set<string>,
  moneyBudget: { remaining: number },
  glossaryBudget: { remaining: number },
  affiliateConfig?: AffiliateConfig,
  currentCategory: string = '',
): string {
  const selfRefUrl = currentCategory ? `/categories/${currentCategory}/` : '';
  const linked = new Array(text.length).fill(false);
  const replacements: [number, number, string][] = [];

  // Affiliate anchors (highest priority, highlighted pill style, no budget)
  if (affiliateConfig?.url && affiliateConfig.anchors?.length) {
    for (const anchor of affiliateConfig.anchors) {
      const lower = anchor.toLowerCase();
      if (usedPhrases.has(lower)) continue;
      const regex = new RegExp(`\\b(${escapeRegex(anchor)})\\b`, 'i');
      const match = regex.exec(text);
      if (!match) continue;
      const start = match.index;
      const end = start + match[0].length;
      if (linked.slice(start, end).some(Boolean)) continue;

      replacements.push([start, end,
        `<a href="${affiliateConfig.url}" target="_blank" rel="noopener noreferrer nofollow sponsored" class="inline-flex items-center gap-1 bg-primary/10 text-primary font-semibold px-2 py-0.5 rounded-md border border-primary/30 hover:bg-primary hover:text-white transition-colors no-underline">${escapeHtml(match[0])}<svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4.25 5.5a.75.75 0 00-.75.75v8.5c0 .414.336.75.75.75h8.5a.75.75 0 00.75-.75v-4a.75.75 0 011.5 0v4A2.25 2.25 0 0112.75 17h-8.5A2.25 2.25 0 012 14.75v-8.5A2.25 2.25 0 014.25 4h5a.75.75 0 010 1.5h-5zm7.5-2.25a.75.75 0 01.75-.75h4a.75.75 0 01.75.75v4a.75.75 0 01-1.5 0V5.56l-5.22 5.22a.75.75 0 11-1.06-1.06l5.22-5.22h-2.19a.75.75 0 01-.75-.75z" clip-rule="evenodd"/></svg></a>`
      ]);
      for (let i = start; i < end; i++) linked[i] = true;
      usedPhrases.add(lower);
    }
  }

  // Money links
  for (const ml of SORTED_MONEY_LINKS) {
    if (moneyBudget.remaining <= 0) break;
    // Skip self-referential links (e.g. "savings accounts" on a banking page
    // pointing at /categories/banking/ — that's the page the user is on).
    if (selfRefUrl && ml.url === selfRefUrl) continue;
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
 * Auto-insert paragraph breaks into walls of text that have none.
 * Groups sentences into paragraphs of ~3 sentences so the description renders
 * as readable chunks instead of one massive block. If the text already has
 * explicit \n\n breaks, leave it alone.
 */
export function autoParagraphs(text: string): string {
  if (!text) return text;
  if (text.includes('\n\n')) return text;
  const sentences = text.match(/[^.!?]+[.!?]+(?:\s+|$)/g);
  if (!sentences || sentences.length <= 3) return text;
  const out: string[] = [];
  for (let i = 0; i < sentences.length; i += 3) {
    out.push(sentences.slice(i, i + 3).join('').trim());
  }
  return out.filter(Boolean).join('\n\n');
}

/**
 * Process full description_long. Each term linked only once across all paragraphs.
 * Used by /review/[slug].astro — caps stay at 5 money + 5 glossary (legacy behaviour).
 */
export function linkifyDescription(
  descriptionLong: string,
  glossaryTerms: GlossaryTerm[],
  currentSlug: string = '',
  affiliateConfig?: AffiliateConfig,
  currentCategory: string = '',
): string[] {
  const usedPhrases = new Set<string>();
  const moneyBudget = { remaining: 5 };
  const glossaryBudget = { remaining: 5 };

  return autoParagraphs(descriptionLong).split('\n\n').map(paragraph =>
    linkifyParagraph(paragraph, glossaryTerms, usedPhrases, moneyBudget, glossaryBudget, affiliateConfig, currentCategory)
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
    autoParagraphs(text).split('\n\n').map(paragraph =>
      linkifyParagraph(paragraph, glossaryTerms, usedPhrases, moneyBudget, glossaryBudget)
    )) as PageLinker;
  fn.usedPhrases = usedPhrases;
  fn.moneyRemaining = () => moneyBudget.remaining;
  fn.glossaryRemaining = () => glossaryBudget.remaining;
  return fn;
}
