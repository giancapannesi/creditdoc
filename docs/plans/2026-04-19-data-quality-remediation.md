# CreditDoc Data Quality Remediation Plan

> **Trigger:** External audit (Apr 19, 2026) found 5 data quality issues across ~12 sampled review pages
> **Goal:** Fix all 5 issues systematically, add prevention gates so they never recur
> **Constraint:** No SEO impact — noindex bad pages, never delete URLs

---

## The 5 Issues

| # | Issue | Severity | Est. Pages Affected |
|---|-------|----------|-------------------|
| 1 | Wrong company content on page | CRITICAL | 500-1,500 |
| 2 | Empty/placeholder fields rendering | MEDIUM | ~2,552 worst case |
| 3 | Generic boilerplate on wrong entity types | MEDIUM | ~2,900 |
| 4 | Non-financial entities in directory | HIGH | 114 self-incriminating + ~297 broader |
| 5 | Unverifiable author (Harvey Brooks) | LOW-MEDIUM | All 15,322 pages |

---

## Issue 1 — CRITICAL: Wrong Company Content on Page

**Example:** `/review/money-line/` title says "Money Line San Diego" but body describes Money One Federal Credit Union in Maryland.

**Root cause:** Enrichment pipeline matched on entity name substring. `website_url` pointed to wrong entity's site, LLM generated content about the wrong company.

### Detection

New script: `scripts/detect_content_mismatch.py`

```python
# For each indexed lender:
#   1. Extract entity name from DB
#   2. Check if name appears in first 300 chars of description_long
#   3. If NOT, check if any OTHER entity's name appears instead
#   4. Flag as mismatch with confidence score
```

SQL to find candidates:
```sql
SELECT slug, json_extract(data, '$.name') as name,
       SUBSTR(json_extract(data, '$.description_long'), 1, 300) as desc_start
FROM lenders 
WHERE processing_status = 'ready_for_index'
  AND json_extract(data, '$.description_long') IS NOT NULL
  AND LENGTH(json_extract(data, '$.description_long')) > 200;
```

### Fix

**Day 1-2:** Run detection, output CSV. Immediately quarantine confirmed mismatches:
```python
db.update_lender(slug, {
    'processing_status': 'quarantine',
    'no_index': True,
    'quarantine_reason': 'content_identity_mismatch'
}, updated_by='data_quality_fix')
```

**Day 3-5:** For confirmed mismatches (non-protected): wipe description_long/short, pros, cons, services, best_for, diagnosis. Reset `has_been_enriched = False`. Requires `updated_by='founder'`.

**Day 6-15:** Re-enrich through fixed pipeline at 100/day.

### Prevention Gate

Add to `creditdoc_autonomous_engine.py` in `step_c_enrich_and_qc()`:
```python
# After enrichment, verify entity name appears in generated content
name_tokens = [t for t in name.split() if len(t) >= 3]
desc_lower = enrichment['description_long'][:300].lower()
if not any(t.lower() in desc_lower for t in name_tokens):
    lender['processing_status'] = 'failed_quarantine'
    lender['quarantine_reason'] = 'content_identity_mismatch'
    return lender, False
```

Add to `validate_build_data.py`:
```python
name_tokens = [t for t in data.get('name','').split() if len(t) >= 3]
desc = data.get('description_long', '')
if desc and len(desc) > 200 and name_tokens:
    if not any(t.lower() in desc[:300].lower() for t in name_tokens):
        errors.append(f"{f.name}: IDENTITY MISMATCH - name not in description")
```

### Monitoring

Daily cron after autonomous engine: scan all `ready_for_index` profiles, flag new mismatches, Telegram alert if count > 0.

---

## Issue 2 — Empty/Placeholder Fields Rendering Live

**Example:** FAQ says "headquartered in , , founded in [year]. They hold a rating with the Better Business Bureau." — city, state, BBB all empty.

**Root cause:** Template renders fields unconditionally. No conditional suppression when data is null/empty.

### Detection

```sql
-- Empty HQ + empty BBB (worst FAQ rendering)
SELECT COUNT(*) FROM lenders 
WHERE processing_status = 'ready_for_index'
AND (json_extract(data, '$.company_info.headquarters') IS NULL 
     OR json_extract(data, '$.company_info.headquarters') = '')
AND (json_extract(data, '$.company_info.bbb_rating') IS NULL 
     OR json_extract(data, '$.company_info.bbb_rating') = '');
```

Grep rendered HTML:
```python
PLACEHOLDER_PATTERNS = [
    r'headquartered in\s*,',
    r'hold a\s+rating',
    r'founded in\s*\.',
    r', ,',
]
```

### Fix

**Template fix in `src/pages/review/[slug].astro`** — replace hardcoded FAQ with conditional assembly:

```typescript
const legitimacyParts: string[] = [`Yes. ${lender.name} is a registered company`];
if (lender.company_info?.headquarters?.trim()) {
  legitimacyParts.push(`headquartered in ${lender.company_info.headquarters}`);
}
if (lender.company_info?.founded_year) {
  legitimacyParts.push(`founded in ${lender.company_info.founded_year}`);
}
if (lender.company_info?.bbb_rating?.trim()) {
  legitimacyParts.push(`They hold a ${lender.company_info.bbb_rating} rating with the BBB`);
}
// Only include FAQ if we have at least one data point beyond the name
const legitimacyAnswer = legitimacyParts.length > 1 
  ? legitimacyParts.join(', ') + '.'
  : null;
```

Also fix BBB badge — wrap in conditional:
```typescript
{lender.company_info?.bbb_rating?.trim() && (
  <span>BBB: {lender.company_info.bbb_rating}</span>
)}
```

### Prevention Gate

Add to `validate_build_data.py`:
```python
ci = data.get('company_info', {}) or {}
if not ci.get('headquarters','').strip() and not ci.get('city','') and not ci.get('bbb_rating',''):
    if data.get('processing_status') == 'ready_for_index':
        warnings.append(f"{f.name}: PLACEHOLDER RISK - no HQ, city, or BBB")
```

### Monitoring

Rendered HTML scanner checks for placeholder patterns after every build.

---

## Issue 3 — Generic Boilerplate on Wrong Entity Types

**Example:** Pawn shops show "Free Consultation" CTA. Check cashers show "Free to Use" badge. All entity types get credit-union "membership approval" language.

**Root cause:** Single review template for all 19 categories. `free_consultation` defaulted to `true` during initial import for all entities.

### Detection

```sql
-- Pawn/check/ATM with Free Consultation
SELECT COUNT(*) FROM lenders 
WHERE processing_status = 'ready_for_index'
AND category IN ('pawn-shops', 'check-cashing', 'atm')
AND json_extract(data, '$.pricing.free_consultation') = 1;
```

### Fix

**Template fix in `[slug].astro`** — add entity type classification:

```typescript
const TRANSACTIONAL_TYPES = ['pawn-shops', 'check-cashing', 'atm'];
const isTransactional = TRANSACTIONAL_TYPES.includes(lender.category);

// Fix Free Consultation badge:
{lender.pricing?.free_consultation && !isTransactional && (
  <TrustBadge type="verified" text="Free Consultation" />
)}

// Fix "Free to Use" price display:
const priceDisplay = hasPricing ? `From ${formatPrice(lowestPrice)}/mo` 
  : isFreeService && !isTransactional ? 'Free to Use' 
  : isTransactional ? 'See Store for Pricing'
  : 'Contact for Pricing';
```

**Data fix** — batch update `free_consultation` to false for transactional entities:
```python
# scripts/fix_transactional_free_consultation.py
# Requires FOUNDER APPROVAL — touches pricing (persistent field)
```

### Prevention Gate

Add to enrichment QC prompt:
```
ENTITY TYPE RULES:
- pawn-shops, check-cashing, atm: NO free_consultation, NO membership language
- Only credit-unions and banking have membership
```

Add to `validate_build_data.py`:
```python
if cat in ('pawn-shops', 'check-cashing', 'atm') and pricing.get('free_consultation'):
    errors.append(f"{f.name}: CATEGORY MISMATCH - {cat} cannot have free_consultation=true")
```

---

## Issue 4 — Non-Financial Entities in Directory

**Example:** `/review/legacy-community/` is Legacy Community Health (healthcare). Body literally says "CreditDoc miscategorized this organization."

**Root cause:** Entity discovery from generic directories without finance-domain filter. LLM detected the problem but pipeline published anyway.

### Detection

```sql
SELECT slug, json_extract(data, '$.name') as name FROM lenders 
WHERE processing_status = 'ready_for_index'
AND (json_extract(data, '$.description_long') LIKE '%miscategorized%'
     OR json_extract(data, '$.description_long') LIKE '%not a financial%'
     OR json_extract(data, '$.description_long') LIKE '%not a lending%'
     OR json_extract(data, '$.description_long') LIKE '%does not provide financial%'
     OR json_extract(data, '$.description_long') LIKE '%is not a credit union%'
     OR json_extract(data, '$.description_long') LIKE '%is not a bank%');
```

### Fix

**Immediate (Day 1):** Quarantine all 114 self-incriminating pages:
```python
db.update_lender(slug, {
    'processing_status': 'failed_quarantine',
    'quarantine_reason': 'not_consumer_finance',
    'no_index': True,
}, updated_by='data_quality_fix')
```

Safe — these profiles literally say they're miscategorized. Transient fields only.

**Day 3-7:** Run broader healthcare/medical detection. Export CSV for manual triage of ~297 borderline cases.

### Prevention Gate

Add to enrichment engine after content generation:
```python
POISON_PHRASES = ['miscategorized', 'not a financial', 'not a lending',
                  'does not provide financial']
for phrase in POISON_PHRASES:
    if phrase in desc_lower:
        lender['processing_status'] = 'failed_quarantine'
        lender['quarantine_reason'] = 'self_incriminating_content'
        return lender, False
```

---

## Issue 5 — Author Attribution (Harvey Brooks)

**Current:** Every page says "Editorially reviewed by Harvey Brooks" with no author bio page.

**Decision:** Harvey Brooks is our created editorial persona. We keep him but make him credible.

### Fix

1. **Create author bio page** at `/about/harvey-brooks/` or add Harvey's section to `/about/`:
   - Consumer finance researcher with X years experience
   - Methodology: how reviews are researched and verified
   - Photo (Gemini-generated professional headshot)
   - Credentials appropriate for YMYL finance content

2. **Update template link** to point to the author bio section:
```typescript
Editorially reviewed by <a href="/about/#editorial-team">Harvey Brooks</a>
```

3. **Update schema.org** to include proper author bio URL:
```typescript
author: {
  '@type': 'Person',
  name: 'Harvey Brooks',
  url: 'https://creditdoc.co/about/#editorial-team',
  jobTitle: 'Consumer Finance Researcher',
}
```

4. **Add editorial methodology section** to `/about/` or `/methodology/` — review process, fact-checking standards, correction policy.

5. **Differentiate FA vs auto pages:** Only FA (Founder Approved) pages get "Editorially reviewed by Harvey Brooks". Auto-generated pages get "Compiled by the CreditDoc Research Team" or "Data sourced from [NCUA/FDIC/HUD]."

---

## New Infrastructure

### Tool 1: Rendered HTML Scanner (`scripts/rendered_html_scanner.py`)

Scans built HTML in `dist/review/*/index.html` for visible quality issues:
1. Placeholder text patterns ("headquartered in , ")
2. Content identity (h1 name vs body name)
3. Wrong badges ("Free to Use" on transactional entities)
4. Self-incriminating phrases
5. Empty sections
6. Schema validity

Runs AFTER Astro build, BEFORE git push. Integrated into `creditdoc_build.py`.

### Tool 2: Pre-Publish Gate (`scripts/pre_publish_gate.py`)

10-check validation that must pass before any profile goes to `ready_for_index`:
1. Entity name in description (identity check)
2. Description length >= 200 chars
3. No self-incriminating phrases
4. Valid category
5. Company info populated (city+state or HQ)
6. No placeholder-triggering empty fields
7. Category-appropriate pricing fields
8. Rating breakdown has 5 dimensions
9. Services >= 3 items
10. No duplicate content with other entities

Integrated into autonomous engine before promotion.

---

## Priority Order

```
P0 (Day 1):    Issue 4 quarantine (114 pages, no approval needed)
P0 (Day 1-2):  Issue 1 detection + quarantine (500-1500 pages)
P1 (Day 1):    Issues 2,3,5 template fixes (same file, one commit)
P1 (Day 3):    Issue 3 data fix (free_consultation batch — NEEDS APPROVAL)
P2 (Day 3-5):  Issue 1 data wipe + re-enrich setup (NEEDS APPROVAL)
P2 (Day 5-7):  Prevention gates in enrichment engine + validate_build_data.py
P3 (Day 8-10): Rendered HTML Scanner + Pre-Publish Gate
P3 (Day 8-10): Harvey Brooks author bio page
P3 (Day 10-21): Re-enrichment of quarantined profiles (100/day)
P4 (Day 22+):  Daily monitoring crons, final verification
```

---

## Approval Gates (Founder Required)

| Action | Why | When |
|--------|-----|------|
| Issue 1: Wipe descriptions on mismatched profiles | Persistent fields | Day 3-5 |
| Issue 3: Batch update free_consultation on 2,693 profiles | Pricing = persistent | Day 3 |
| Issue 4: Broader non-financial triage (297 borderline) | Manual judgment | Day 3-7 |

All other actions (quarantine, template fixes, prevention gates, new tools) modify only transient fields or code — no approval needed.

---

## Files Changed

| File | Issues | Change |
|------|--------|--------|
| `src/pages/review/[slug].astro` | 2,3,5 | Conditional FAQ, entity-type badges, author attribution |
| `tools/creditdoc_autonomous_engine.py` | 1,3,4 | Identity check, poison phrase gate, entity-type QC rules |
| `tools/validate_build_data.py` | 1,2,3,4 | All detection patterns added to pre-push validator |
| `scripts/detect_content_mismatch.py` | 1 | New — daily identity mismatch scanner |
| `scripts/quarantine_non_financial.py` | 4 | New — one-time quarantine of self-incriminating pages |
| `scripts/fix_transactional_free_consultation.py` | 3 | New — batch data fix (needs approval) |
| `scripts/pre_publish_gate.py` | ALL | New — 10-check validation before indexing |
| `scripts/rendered_html_scanner.py` | ALL | New — post-build HTML quality check |
| `src/pages/about.astro` | 5 | Harvey Brooks bio + editorial methodology |
