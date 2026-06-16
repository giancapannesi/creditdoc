# Loan Approval Readiness Toolkit Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the missing CreditDoc linkable asset layer around a free Loan Approval Readiness Toolkit and printable checklist, then place it on the Resources and Tools hubs.

**Architecture:** Add static Astro resource pages using the existing `BaseLayout` public-resource pattern. Keep the pages educational, ungated, and link-focused, with internal links to existing tools, answers, resources, research, and money/category pages.

**Tech Stack:** Astro 5, Tailwind utility classes, CreditDoc `BaseLayout`, JSON-LD objects, existing static resource and tool hub patterns.

---

## Live-Site Safety

- Do not deploy during implementation.
- Do not touch lender data, Supabase policies, crons, or Cloudflare config.
- Keep unrelated untracked files out of commits.
- Run `git status --short --untracked-files=all` before each commit.
- Run `npm run build` before any final claim.
- Use `/srv/BusinessOps/creditdoc/deploy.sh` only if Jammi explicitly approves deploy later.

## Task 0: Baseline And Prior Commit

**Files:**
- Existing modified: `CREDITDOC_NOW.md`
- Existing modified: `tools/creditdoc_priority_indexing.py`

**Steps:**
1. Check repo status.
2. Review existing indexing-priority diff.
3. Run `git diff --check` for the two files.
4. Commit the existing indexing-priority fix separately.

**Completed:**
- Commit `279f452c55` (`fix: prioritize answer and money indexing queues`).

## Task 1: Build Toolkit Pages

**Files:**
- Create: `src/pages/resources/loan-approval-readiness-toolkit/index.astro`
- Create: `src/pages/resources/loan-approval-readiness-toolkit/print/index.astro`

**Content requirements:**
- Before you apply
- Personal loan readiness
- Business loan readiness
- Documents to gather
- Credit report review
- DTI/utilization/cash-flow basics
- What to do after denial
- MCA risk check
- Official sources
- Printable checklist

**Safety requirements:**
- No approval, underwriting, prequalification, rate, pricing, or guarantee claims.
- No affiliate links inside the resource.
- Visible page content must match HowTo/Article schema.

**Verification:**
- Run `npm run build` after page creation.
- Confirm generated output contains toolkit title and printable route.

**Commit:**
- `feat: add loan approval readiness toolkit`

## Task 2: Hub Placement

**Files:**
- Modify: `src/pages/resources/index.astro`
- Modify: `src/pages/tools/index.astro`

**Changes:**
- Add toolkit as featured resource card on `/resources/`.
- Add toolkit module/card on `/tools/` so tools point to the public checklist hub.
- Link toolkit to existing tools and answers.

**Verification:**
- Run `npm run build`.
- Confirm hub HTML contains `/resources/loan-approval-readiness-toolkit/`.

**Commit:**
- `feat: feature loan readiness toolkit in hubs`

## Task 3: Optional Resource Placement Follow-Up

**Scope for after review, not first build:**
- Create `/resources/credit-denial-action-checklist/` and print page.
- Create `/resources/state-consumer-credit-regulator-directory/` or resource wrapper.
- Decide whether existing `/tools/` pages remain canonical or link to resource pages.

## Handoff Rule

After each completed task, append a short status note to:

- `/srv/BusinessOps/memory/PULSE.md`
- `/srv/BusinessOps/memory/DECISIONS.md` when behavior/priority changes
- `/srv/BusinessOps/creditdoc/CREDITDOC_NOW.md` for CreditDoc-specific resume context
