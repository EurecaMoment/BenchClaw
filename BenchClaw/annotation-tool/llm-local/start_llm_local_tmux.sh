#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SESSION_NAME="${LLM_LOCAL_TMUX_SESSION:-annot_llm_local}"
PORT="${1:-9001}"

if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
  printf 'tmux session %s already exists\n' "$SESSION_NAME"
  exit 0
fi

tmux new-session -d -s "$SESSION_NAME" \
  "cd '$SCRIPT_DIR' && ./deploy_llm_local_service.sh '$PORT' && exec tail -f '$SCRIPT_DIR/service.log'"

printf 'started tmux session %s for llm-local on port %s\n' "$SESSION_NAME" "$PORT"
