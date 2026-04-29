# Encryption-at-rest verification — CreditDoc data plane

**CDM-REV-2026-04-29 Phase 3.7.** Doc-only — records the encryption-at-rest
posture across CreditDoc's data plane. Serves OBJ-3 Tier 1 (marketing site
"free basics now"). No code change, no infra change.

Last verified: 2026-04-29. Re-verify whenever a new data-storage surface is
added (KV, D1, new R2 bucket, new Supabase project).

---

## Surface inventory + encryption posture

| Surface                                  | Provider     | At-rest encryption | KMS / key authority           | Source              |
|------------------------------------------|--------------|--------------------|-------------------------------|---------------------|
| Supabase Postgres `pndpnjjkhknmutlmlwsk` | Supabase     | AES-256            | AWS KMS (us-east-1, managed)  | Supabase docs §security |
| Supabase Storage (n/a — not in use)      | —            | —                  | —                             | —                   |
| Supabase Vault extension (`supabase_vault`) | Supabase  | AES-256 + per-row key | Postgres extension; key rotation per Supabase | Installed, not yet used |
| Daily PITR backups (Supabase)            | Supabase     | AES-256            | AWS KMS (managed)             | Supabase Pro feature; current project plan = free, **PITR not enabled** |
| R2 bucket `creditdoc-assets`             | Cloudflare   | AES-256            | Cloudflare-managed key        | CF R2 docs §encryption |
| CF Pages static assets in `dist/`        | Cloudflare   | AES-256            | Cloudflare-managed key        | CF Pages docs       |
| CF Workers KV (none yet — planned `creditdoc-versions`) | Cloudflare | AES-256 | Cloudflare-managed key | CF KV docs |
| CF Cache API objects                     | Cloudflare   | AES-256 in colos   | Cloudflare-managed key        | CF Cache API docs   |
| Local SQLite `data/creditdoc.db`         | Filesystem (VPS) | **NOT ENCRYPTED** at rest at the file level | — | This is a build-side cache. Never serves prod traffic. |
| Local backups in `creditdoc/data/backups/` | Filesystem (VPS) | **NOT ENCRYPTED** at rest at the file level | — | Server-side encryption is the VPS host's posture, not ours |

---

## Verification mechanism per provider

### Supabase Postgres
- AES-256 at-rest is the default for all Supabase projects since 2022 (no
  opt-in required).
- Source of truth: Supabase organization security page. The TraderTrac org
  this project belongs to inherits the same posture.
- **What's NOT encrypted column-by-column today:** all PII columns are
  currently in cleartext-at-rest behind disk encryption. Column-level
  envelope encryption (via `supabase_vault`) is NOT used yet. This is
  acceptable for Tier 1 (marketing site, no PCI/PII volume). When we ship
  Tier 2 (KYB / leads at scale), revisit this.

### Cloudflare R2 + KV + Cache API + Pages
- All Cloudflare-managed surfaces are AES-256 at rest by default. Per CF
  R2 docs: "All objects are encrypted at rest using AES-256."
- No customer-managed keys (CMK) feature is available on free / Pro plans.
  CMK is Enterprise-only on R2. Tier 1 doesn't need it.

### Local VPS storage
- `/srv/BusinessOps/creditdoc/data/creditdoc.db` is on the host filesystem.
  Whether it's encrypted at rest depends on the VPS provider's disk
  encryption posture — out of scope for this doc and out of scope for
  CreditDoc's compliance claims.
- This DB is a build-side mirror of the canonical Supabase data. Losing
  the file is not a data-loss event; rebuilding from Supabase is the
  recovery path.
- **Rule:** never store anything in `data/creditdoc.db` that doesn't also
  live in Supabase. If you do, you've created a single point of failure
  AND an encryption gap.

---

## In-transit encryption (adjacent, often confused)

| Hop                                       | TLS                    |
|-------------------------------------------|------------------------|
| Browser → `creditdoc.co`                  | TLS 1.2+ (Vercel cert today; CF cert at Phase 6 cutover) |
| Worker → Supabase PostgREST               | TLS 1.2+ (Supabase certs)  |
| Worker → R2                               | TLS 1.2+ (CF internal)     |
| `tools/creditdoc_db.py` → Supabase        | TLS 1.2+, `sslmode=require` enforced in connection string |
| `tools/creditdoc_db.py` → `/api/revalidate` | TLS 1.2+ via HTTPS |

All hops in the production data path are TLS-encrypted in transit. The only
non-TLS hop is on-disk reads from `data/creditdoc.db` on the VPS — which by
definition is not "in transit".

---

## Backup + recovery encryption

- Supabase automated backups (free tier = nightly, no PITR): AES-256, AWS
  KMS-managed. Same posture as the live DB.
- `tools/creditdoc_db_backup.py` writes to `creditdoc/data/backups/` on the
  VPS — **not encrypted by the tool**. If the VPS disk isn't encrypted,
  these snapshots aren't either. Acceptable for Tier 1 (the canonical
  source of truth — Supabase — is encrypted). Revisit when we ship Tier 2.

---

## Compliance claims this doc supports (and doesn't)

**Supports** (you can put these on the privacy page or a sub-processor list
without lying):
- "Customer data at rest in our primary database is encrypted with AES-256."
- "Static assets and CDN cache objects are encrypted at rest by our CDN
  provider (Cloudflare)."
- "Traffic between our systems and our database is encrypted using TLS."

**Does NOT support** (don't claim these):
- ❌ "All customer data is encrypted with customer-managed keys (CMK)."
- ❌ "All backups are encrypted under our control." (Supabase manages keys.)
- ❌ "We are SOC 2 / ISO 27001 / HIPAA compliant." (Tier 4 work, not done.)
- ❌ "PII columns are envelope-encrypted." (`supabase_vault` is installed
   but not in use yet.)

---

## Re-verification trigger list

Re-run this doc when ANY of these changes:
1. New Cloudflare resource is provisioned (KV, D1, new R2 bucket, Workers
   secret store entry, Stream).
2. New Supabase project is created OR `supabase_vault` is enabled for any
   column.
3. `tools/creditdoc_db_backup.py` writes to a new location.
4. CF Enterprise plan is purchased (CMK becomes available).
5. Tier 2/3/4 compliance work is greenlit (KYB / SOC 2 / HIPAA-adjacent).

---

## See also

- Memory: `creditdoc_north_star.md` — three OBJs, OBJ-3 tiered ladder
- `CreditDoc Project Improvement/2026-04-29_GAP_ANALYSIS_EMBEDDED_FINANCE_COMPLIANCE.md` — Tier A/B/C/D pre-flight, $40-60K/$80-150K compliance cost ladder
- `creditdoc/docs/plans/2026-04-29_REVISED_MIGRATION_PLAN_HYBRID_FIRST.md` §3 — full Phase 3 compliance baseline
