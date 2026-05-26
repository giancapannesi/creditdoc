# Fintech Category Launch

Date: 2026-05-26  
Purpose: separate app-first financial technology providers from traditional banking, credit-builder, personal-loan, and emergency-cash categories.

## Decision

Create a public CreditDoc category:

- Slug: `fintech`
- Name: `Fintech`
- URL: `/categories/fintech/`

This category is for mobile-first financial technology companies offering cash
advances, digital banking, credit builder tools, investing, budgeting, or
marketplace products.

## Why

Several providers do not fit cleanly into one legacy category:

- `banking` if they are not chartered banks
- `personal-loans` if loans are only one part of the app
- `emergency-cash` if cash advances are only one feature
- `build-credit` if credit builder is one feature in a broader platform

The Fintech category lets CreditDoc compare app-first providers on terms that
match how consumers evaluate them: fees, subscriptions, repayment rules, cash
advance limits, banking partners, credit-builder mechanics, and whether the
product is a loan, advance, deposit account, or marketplace offer.

## Initial Cohort

Moved through the CreditDoc DB API and exported to JSON:

- `moneylion`
- `chime`
- `brigit`
- `earnin`
- `dave-banking`
- `kikoff`
- `self-credit-builder`
- `self-financial`
- `sofi`
- `sofi-bank`
- `varo-bank`

Founder authorization was used only where required by profile protection:

- `moneylion`
- `chime`
- `kikoff`
- `self-credit-builder`
- `sofi-bank`

Rows with FDIC/NCUA identifiers were not moved in this launch batch. For
example, `varo-bank-national-association-draper` remains in `banking` because
it has an FDIC certificate and should be handled under bank-policy rules.

## Site Wiring

Implemented:

- `src/content/categories.json` includes `fintech`
- `src/components/Header.astro` includes Fintech in the category dropdown
- `src/components/CategoryCard.astro` renders the Fintech mobile-app icon
- `src/pages/index.astro` includes Fintech in the home category grid
- `src/components/FilterBar.astro` includes Fintech as a searchable/filterable category
- `src/pages/search.astro` labels Fintech search results correctly
- Supabase `public.categories` upserted with the `fintech` row
- Supabase lender category rows verified for the 11-profile launch cohort

## CFPB Report Impact

MoneyLion is no longer a policy hold. It should be included as a Fintech /
multi-product app candidate, not as a traditional bank.

Sarma remains a separate policy hold because it is B2B credit reporting, data,
collections, background screening, and mortgage-services infrastructure rather
than a consumer-facing fintech app or lender.

## Follow-Up

Run the Profile Quality Agent workflow against the initial Fintech cohort:

- normalize official websites to HTTPS
- remove stale branch-style details where inappropriate
- clean draft profiles such as `dave-banking` and `sofi`
- decide duplicate policy for `sofi` vs `sofi-bank`
- decide whether some app-first providers should also keep secondary category
  tags once multi-category display is supported
