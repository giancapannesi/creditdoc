# Phase 3.9 — static content pages: verified clean (2026-07-17)

Fourteenth family "delivered" — but not via new renderer code. Prior
Phase 1a work (`tools/creditdoc_static/strip_astro_fingerprint.py`
wired into `package.json` postbuild) already handles static pages by
stripping Astro fingerprints from Astro's own build output. This
phase closes the loop by auditing the current state and confirming
no additional work is needed.

## Audit result

Full walk of 60 static-page HTML files across:

- `dist/about/`, `dist/about/creditdoc-data/`, `dist/about/harvey-brooks/`
- `dist/accessibility/`, `dist/contact/`, `dist/deals/`
- `dist/disclaimer/`, `dist/disclosure/`, `dist/do-not-sell/`
- `dist/editorial-policy/`, `dist/faq/`, `dist/glossary/`
- `dist/learn/`, `dist/methodology/`, `dist/press/`
- `dist/privacy/`, `dist/terms/`
- `dist/research/` (5 pages), `dist/resources/` (4 pages)
- `dist/tools/` (19 pages), `dist/courses/` (2 pages)

Findings:

| Astro fingerprint | Files affected | Interpretation |
|---|---:|---|
| `data-astro-cid-<hash>` attribute | **0 / 60** | Strip pipeline handled these on last Astro build |
| `/_astro/*.css` link refs | **0 / 60** | Rewritten to `/styles.css` by strip pipeline |
| `/_astro/*.js` script refs | **4 / 60** | Interactive tools (borrowing-power-quiz, credit-score-simulator, debt-payoff-calculator, LenderNameSearch) — legit runtime JS, needs Rock 1 handling |

## What this means

- **Hand-authored static content pages are already renderer-compatible.**
  No Jinja port needed. When copy changes, edit the .astro source →
  run `npm run build` → strip runs in postbuild → clean HTML lands in
  `dist/`.

- **Static-content update velocity is low.** About/disclaimer/faq/etc.
  change once a quarter at most. Running Astro when they change is
  acceptable — the mandate is about eliminating rebuilds on *content*
  changes (lender rows, blog posts) which are daily.

- **Interactive tools carry 4 hydrated JS bundles.** These are
  fingerprinted (`.C0BmcZCe.js` etc.). Rock 1 will need to either:
  (a) preserve these bundles as `/tools/*.js` with stable filenames,
  or (b) convert the ~4 tools to inline vanilla JS.

## Rolling total after Phase 3.9

| Family | Pages | Method |
|---|---:|---|
| /review/ | 15,775 | Jinja (Phase 2) |
| /trends/ | 713 | Jinja (Phase 3.6) |
| /answers/ | 495 | Jinja (Phase 2) |
| /browse/ | 467 | Jinja (Phase 3.5) |
| /compare/ | 394 | Jinja (Phase 3.7) |
| /city/ | 331 | Jinja (Phase 3.2) |
| /financial-wellness/ | 139 | Jinja (Phase 2) |
| /blog/ | 129 | Jinja (Phase 2) |
| /brand/ | 57 | Jinja (Phase 3.3B) |
| /state/ | 50 | Jinja (Phase 3.4) |
| /state/*/lending-laws/ | 50 | Jinja (Phase 3.4B) |
| /best/ | 27 | Jinja (Phase 3.8) |
| /categories/ | 19 | Jinja (Phase 3.1) |
| Static content | 60 | Astro + strip (Phase 1a + this audit) |
| **Total covered** | **18,706** | **14 families** |

## What remains for the mandate

Not covered:
- `/credit-guide/` 412 pages (Phase 3.3, Supabase ETL blocker)
- 4 interactive tools (need JS handling in Rock 1)

Rocks remaining:
- Rock 1 — kill `@astrojs/cloudflare` adapter, hand-roll worker
- Rock 3 — per-file wrangler push in `watch_and_rebuild.py`

Next: fire debugger agent to review this audit + Phases 3.4B/3.8,
then proceed to Rock 1.
