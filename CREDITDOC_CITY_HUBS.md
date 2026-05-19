# CreditDoc — City Hub Pages

**Status:** NOT STARTED — waiting for Regulatory Data Layer + Jammi GO
**Full plan:** `CreditDoc Project Improvement/2026-04-21_CITY_HUB_TEMPLATE_SPEC.md`
**Depends on:** Regulatory data layer (Phases 2-4 minimum), architecture fixes DONE, data quality DONE

---

## What This Is

One rich page per city at `/cities/[state]/[city-slug]/` covering everything financial: banks, credit unions, SBA lenders, credit repair, debt help, complaint transparency, local FAQ — all on one URL.

**The play:** implicit local intent. Someone in Boise googles "small business loans" without typing "Boise" — Google geolocates them, and our Boise hub ranks because of entity density + regulator data + schema markup. Nobody else ships a page that combines directory + editorial + regulator data at the city level.

**Farming/ag section** for rural hubs: cattle loans, equipment loans, poultry — SERPs nobody is serving. Renders conditionally for rural/ag counties only.

---

## Launch Sequence

| Phase | What | Status |
|-------|------|--------|
| 7.0 | Template design — build Boise as pure HTML mock | ⬜ |
| 7.1 | Data-bound pilot: Boise live with real data | ⬜ |
| 7.2 | Measurement: 6 weeks, GSC + rank tracking | ⬜ |
| 7.3 | Second city: Springfield MO (softest SERPs) | ⬜ |
| 7.4 | Rollout: 5 cities/week, 260/year | ⬜ |
| 7.5 | Full programmatic: 500+ cities (conditional on results) | ⬜ |

**Kill switch:** Boise fails to rank top 50 by Month 3 → template is broken, iterate before scaling.

---

## Data Sources Per Section

| Section | Source | Status |
|---------|--------|--------|
| Local banks | `regulator.db.fdic_locations` | Needs regulator Phase 3 |
| Credit unions | `creditdoc.db` category=credit-unions | Live |
| SBA lenders | `regulator.db.sba_lender_state_year` | Needs regulator Phase 4 |
| Farming/ag loans | USDA FSA + Farm Credit (scrape) | New — Phase 4.5 |
| Credit repair | `creditdoc.db` category=credit-repair | Live |
| Debt nonprofits | `creditdoc.db` category=debt-settlement | Live |
| Complaint stats | `regulator.db.cfpb_company_stats` | Needs regulator Phase 2 |
| Local FAQ | `creditdoc.db.cluster_answers` | Partially live |
| Related cities | New `cities` table needed | Not built |

---

## Open Questions (from original plan, still unanswered)

1. Pilot city: Boise or Springfield MO?
2. Content generator: manual first draft or Opus-generated with review?
3. URL shape: `/cities/idaho/boise/` or alternative?
4. Rollout speed: 5/week (conservative) or 20/week (aggressive)?
5. Top 10 cities priority list: Dallas, Houston, Atlanta, Phoenix, Denver, Miami, Seattle, Chicago, Philadelphia, Minneapolis — approved?

---

## Rules

- Pilot before scale. One city first. Measurement before rollout.
- 1,500 word minimum per hub or don't ship (no thin content).
- Every hub reviewed for factual accuracy before publish.
- No GBP spoofing — we are not a local business.
- Monthly refresh when FDIC/SBA data updates.
