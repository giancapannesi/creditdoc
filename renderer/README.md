# CreditDoc Renderer — Astro Replacement

**Status:** Phase 1 in progress (2026-07-17).  
**Goal:** Replace Astro with a plain Python + Jinja2 renderer that reads the DB directly and writes static HTML files.

## Why this exists

Astro forces a full 27,000-page rebuild for any change. One word in a template → 45 minutes. One row in the DB → 45 minutes. That's the friction we tried to escape from Vercel.

This renderer:
- Reads the DB directly (`data/creditdoc.db`) — no JSON cache layer
- Uses Jinja2 templates (portable, standard, non-framework)
- Renders **one page at a time** on demand
- Writes to `dist/` — same output location as Astro
- Runs alongside Astro during the parity phase; replaces it after cutover

## Phases

| Phase | Duration | Description |
|---|---|---|
| **1. Skeleton + parity harness** | 2 days | Render one `/review/[slug]` page from DB, byte-diff against Astro output |
| **2. Cover all page families** | 3-4 days | Extract templates for all 12 route families |
| **3. Trigger integration** | 1-2 days | DB row UPDATE → renderer → wrangler upload for one page |
| **4. API relocation** | 2 days | Hand-write CF Worker for /api/*, /go/[slug] |
| **5. Cutover + Astro delete** | 1 day | Remove Astro entirely |

**Total: 11-14 days careful work.** Zero-risk parallel-run means Bing sees no change during the swap.

## Directory

```
renderer/
├── README.md                          # This file
├── render.py                          # Main renderer CLI
├── templates/
│   ├── base.html.j2                   # Layout shell (nav, footer)
│   ├── review.html.j2                 # /review/[slug]/index.html
│   ├── credit-guide.html.j2           # /credit-guide/[slug]/
│   ├── credit-guide-category.html.j2  # /credit-guide/[slug]/[category]/
│   └── ... (one per page family)
└── tests/
    ├── parity_check.py                # Byte-diff dist/ vs renderer_dist/
    └── fixtures/                      # Golden files for known lenders
```

## Usage (planned)

```bash
# Render one page from DB
python3 renderer/render.py review --slug lexington-law

# Render all reviews (parity comparison run)
python3 renderer/render.py review --all --output-dir renderer_dist/

# Byte-diff against Astro
python3 renderer/tests/parity_check.py --astro dist/ --renderer renderer_dist/
```

## Rules

1. **DB is source of truth.** No reads from JSON files. Read `data/creditdoc.db` or Supabase directly.
2. **Same URLs, same HTML structure.** Parity check must be clean before any file is served from the renderer instead of Astro.
3. **Per-page updates.** `render.py review --slug X` must complete in <5 seconds for one lender.
4. **No framework runtime.** Just Python + Jinja2. Output is plain HTML files.
