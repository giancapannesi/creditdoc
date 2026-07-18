#!/usr/bin/env bash
set -euo pipefail

export PATH="/root/.nvm/versions/node/v24.15.0/bin:/usr/local/bin:/usr/bin:/bin:${PATH:-}"

REPO="/srv/BusinessOps/creditdoc"
WORKTREE="/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Tools_Autonomous_Worktree_2026-06-09"
BRANCH="creditdoc-tools-autonomous-2026-06-09"
PROMPT="/srv/BusinessOps/CreditDoc Project Improvement/CreditDoc_Origination_Capture_System_2026-06-09/AUTONOMOUS_TOOLS_PROMPT.md"
LOG="/srv/BusinessOps/logs/creditdoc_tools_autonomous_continue.log"
LAST_MESSAGE="/srv/BusinessOps/logs/creditdoc_tools_autonomous_last_message.md"
LOCK="/tmp/creditdoc_tools_autonomous_continue.lock"
CUTOFF_UTC="2026-06-12T00:00:00Z"

mkdir -p "$(dirname "$LOG")"

if [[ "${CREDITDOC_TOOLS_AUTONOMOUS_LOCKED:-0}" != "1" ]]; then
  exec /usr/bin/flock -n "$LOCK" env CREDITDOC_TOOLS_AUTONOMOUS_LOCKED=1 "$0" "$@"
fi

{
  echo "===== $(date -u '+%Y-%m-%dT%H:%M:%SZ') CreditDoc tools autonomous continue ====="

  if [[ "$(date -u +%s)" -ge "$(date -u -d "$CUTOFF_UTC" +%s)" ]]; then
    echo "Cutoff reached ($CUTOFF_UTC); exiting."
    exit 0
  fi

  if ! command -v codex >/dev/null 2>&1; then
    echo "codex CLI not found; exiting."
    exit 1
  fi

  if [[ ! -f "$PROMPT" ]]; then
    echo "Prompt missing: $PROMPT"
    exit 1
  fi

  cd "$REPO"
  if [[ -n "$(git status --porcelain=v1)" ]]; then
    echo "Main repo is dirty; another agent may be working. Skipping to avoid clash."
    git status --short
    exit 0
  fi

  if [[ ! -e "$WORKTREE/.git" ]]; then
    if git show-ref --verify --quiet "refs/heads/$BRANCH"; then
      git worktree add "$WORKTREE" "$BRANCH"
    else
      git worktree add -b "$BRANCH" "$WORKTREE" HEAD
    fi
  fi

  cd "$WORKTREE"
  if [[ -n "$(git status --porcelain=v1)" ]]; then
    echo "Autonomous worktree is dirty from a prior run; skipping so a human/agent can inspect."
    git status --short
    exit 0
  fi

  git status --short --branch

  codex exec \
    --cd "$WORKTREE" \
    --dangerously-bypass-approvals-and-sandbox \
    --output-last-message "$LAST_MESSAGE" \
    - < "$PROMPT"

  echo "--- post-agent status ---"
  git status --short

  if [[ -n "$(git status --porcelain=v1)" ]]; then
    # Renderer watcher (*/5 * * * *) picks up DB changes and deploys per-slug — no full rebuild needed
    git add -A
    git commit -m "tools: continue CreditDoc origination funnel work"
    echo "Committed autonomous progress on $BRANCH."
  else
    echo "No changes produced."
  fi
} >> "$LOG" 2>&1
