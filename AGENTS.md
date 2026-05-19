# CreditDoc Agent Entrypoint

This is the Codex-facing project entrypoint for CreditDoc.

## Load First

Before changing CreditDoc, read:

1. `/srv/BusinessOps/AGENTS.md`
2. `/srv/BusinessOps/CLAUDE.md`
3. `/srv/BusinessOps/creditdoc/CREDITDOC_NOW.md`
4. `/srv/BusinessOps/creditdoc/CREDITDOC_NEXT.md`
5. Relevant `/root/.claude/projects/-srv-BusinessOps/memory/creditdoc*.md`
6. Relevant `/root/.claude/projects/-srv-BusinessOps/memory/project_creditdoc_*.md`
7. Relevant `/root/.claude/projects/-srv-BusinessOps/memory/feedback_creditdoc_*.md`

Also check `/srv/BusinessOps/CreditDoc Project Improvement/` for dated plans and
greenlight queues before acting.

## Project Shape

- Primary site: `https://www.creditdoc.co`
- Code path: `/srv/BusinessOps/creditdoc`
- Current branch may be migration-specific. Check Git status before edits.
- Runtime architecture is Cloudflare Worker / SSR backed by Supabase plus legacy
  static/content export paths. Do not assume Vercel is authoritative.
- Data/content automation is substantial. Avoid broad `git add -A` operations.

## Useful Files

- `/srv/BusinessOps/creditdoc/CREDITDOC_NOW.md`
- `/srv/BusinessOps/creditdoc/CREDITDOC_NEXT.md`
- `/srv/BusinessOps/CreditDoc_SEO/content_queue.json`
- `/srv/BusinessOps/CreditDoc_SEO/blog_queue.json`
- `/srv/BusinessOps/logs/creditdoc_*.log`

## Safety Rules

- Read live architecture memory before deploying or changing infrastructure.
- Do not edit protected production data files blindly.
- Use existing CreditDoc tools and DB APIs instead of direct JSON surgery when the
  memory says a DB path is authoritative.
- Do not rotate, print, or copy service role keys. Report credential hygiene issues
  without repeating secret values.
- Do not change crons without the append-only cron protocol and verification.

