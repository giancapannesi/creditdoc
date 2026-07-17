"""
Category-specific FAQ fallback for review pages that have no lender-level faqs.

Astro emits a data-driven FAQ block on every review; when a lender has no
custom faqs, it falls back to category templates. We mirror that here.
Questions are generic, evergreen, and safe (no YMYL specifics).
"""
from __future__ import annotations

_TEMPLATES: dict[str, list[tuple[str, str]]] = {
    "credit-repair": [
        ("How does credit repair work?",
         "Credit repair companies review your credit reports for inaccurate, incomplete, or unverifiable items and dispute them with the credit bureaus on your behalf. Under the Fair Credit Reporting Act, bureaus must investigate disputes within 30 days and remove items that cannot be verified."),
        ("How much does credit repair cost?",
         "Most credit repair companies charge $50–$150 per month plus an initial setup fee ($50–$150). Some states prohibit charging fees before services are performed. Compare packages carefully — higher price does not guarantee better results."),
        ("How long does credit repair take?",
         "Legitimate credit repair typically takes 3–6 months for meaningful score changes, with some cases taking up to 12 months. Companies promising overnight results or specific score guarantees should be avoided — these are red flags under the federal Credit Repair Organizations Act (CROA)."),
        ("Can I do credit repair myself?",
         "Yes. You can dispute inaccuracies directly with the credit bureaus at no cost through their online portals or by mailing dispute letters. Free resources are available from the CFPB and non-profit credit counseling agencies. Paid services save time but do not have access to disputes you cannot file yourself."),
        ("What items can credit repair remove?",
         "Credit repair can dispute — and potentially remove — inaccurate late payments, collections, charge-offs, incorrect account information, duplicate items, and items past the statutory reporting period (typically 7 years, or 10 for bankruptcies). Accurate negative items cannot be legally removed before their statutory expiration."),
        ("Is credit repair a scam?",
         "Legitimate credit repair is a regulated service, but the industry has a high concentration of scams. Warning signs include upfront fees before services are performed, promises of specific score increases, guarantees to remove accurate items, and pressure to sign contracts without a written explanation of rights. Verify state licensing and read the contract before paying anything."),
    ],
    "credit-monitoring": [
        ("What is credit monitoring?",
         "Credit monitoring services track changes to your credit reports across the three major bureaus and alert you to new accounts, inquiries, and score changes. Most services include identity theft insurance and dark-web monitoring."),
        ("Is credit monitoring worth it?",
         "For consumers actively rebuilding credit or concerned about identity theft, credit monitoring provides useful early warnings. Free options (Credit Karma, Experian free) cover most use cases; paid services add tri-bureau monitoring, higher-frequency updates, and identity theft insurance."),
        ("Does credit monitoring hurt my score?",
         "No. Checking your own credit through a monitoring service is a soft inquiry and does not affect your score. Only hard inquiries from new credit applications lower your score."),
    ],
    "debt-relief": [
        ("What is debt relief?",
         "Debt relief refers to programs that reduce, restructure, or discharge consumer debt. Common approaches include debt settlement (negotiating a lump-sum payoff for less than owed), debt management plans (consolidated payment through a counseling agency), and bankruptcy. Each has different credit-score, tax, and legal implications."),
        ("How much does debt relief cost?",
         "Debt settlement companies typically charge 15%–25% of the enrolled debt or 15%–25% of the amount saved. Under FTC rules, they cannot collect fees until they have settled a debt on your behalf. Debt management plans from non-profit agencies typically charge $25–$75 per month."),
        ("Does debt relief hurt your credit?",
         "Debt settlement typically causes significant short-term credit score damage because accounts must go delinquent before creditors will negotiate. Settled accounts show as \"settled for less than full amount\" on credit reports for 7 years. Debt management plans have less impact if payments are made on time."),
    ],
    "personal-loans": [
        ("What credit score do I need for a personal loan?",
         "Most personal loan lenders require a minimum credit score of 580–660 for approval, though the best rates go to borrowers with scores of 720 or higher. Some lenders specialize in bad-credit personal loans with scores as low as 550, but APRs on those loans typically exceed 30%."),
        ("How do personal loan APRs work?",
         "Personal loan APRs typically range from 6% to 36% depending on your credit score, income, and the lender. The APR includes both the interest rate and origination fees, so it is the truest cost-of-borrowing metric to compare across lenders."),
        ("How quickly can I get a personal loan?",
         "Online lenders can approve and fund personal loans within 1–3 business days. Banks and credit unions typically take 3–7 business days. Some lenders advertise same-day funding for approved applicants who complete the process by mid-morning."),
    ],
    "business-loans": [
        ("What credit score do I need for a business loan?",
         "SBA loans typically require 640+ personal credit score plus 2+ years in business. Online lenders may approve with scores as low as 550 but at higher APRs. Traditional bank business loans usually require 700+ personal credit plus strong business financials."),
        ("How much can I borrow with a business loan?",
         "Business loan amounts range from $5,000 (microloans) to $5 million (SBA 7(a) maximum). Amount depends on business revenue, time in business, credit profile, and collateral. Term loans typically go up to 10x monthly revenue for online lenders."),
    ],
    "sba-loans": [
        ("How long does SBA loan approval take?",
         "SBA 7(a) loan approval typically takes 60–90 days from application to funding. SBA Express loans can close in 30–45 days. Prepared borrowers with complete documentation, tax returns, and business plans move fastest through the process."),
        ("What credit score do I need for an SBA loan?",
         "SBA lenders typically require a minimum personal credit score of 640, though most approved borrowers have 680+. The SBA does not set a hard credit minimum — individual SBA-approved lenders set their own overlays."),
    ],
}

_FALLBACK = [
    ("What should I check before contracting with this provider?",
     "Verify current state licensing with your state regulator, check CFPB complaint data for the company name, read the contract before paying any upfront fees, and confirm the total cost including any fees over the full term."),
    ("How does this company make money?",
     "Financial services providers earn revenue through fees (monthly, setup, transaction), interest on loans, commissions on affiliate products, and in some cases from data-monetization partnerships. Ask for a written explanation of all fees before signing anything."),
    ("What consumer protections apply?",
     "Federal protections include the Fair Credit Reporting Act (credit reporting accuracy), the Credit Repair Organizations Act (credit repair contract requirements), the Fair Debt Collection Practices Act (debt collection conduct), and the Consumer Financial Protection Bureau's complaint and enforcement authority. State-level protections vary."),
]


def category_faqs(category: str, lender_name: str) -> list[dict[str, str]]:
    """Return a list of {q, a} dicts for the given category. Uses a fallback set if unknown."""
    tmpl = _TEMPLATES.get(category, _FALLBACK)
    return [{"q": q, "a": a} for q, a in tmpl]
