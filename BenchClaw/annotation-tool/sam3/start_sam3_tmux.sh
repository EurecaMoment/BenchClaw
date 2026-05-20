#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SESSION_NAME="${SAM3_TMUX_SESSION:-annot_sam3}"
PORT="${1:-8765}"

if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
  printf 'tmux session %s already exists\n' "$SESSION_NAME"
  exit 0
fi

tmux new-session -d -s "$SESSION_NAME" \
  "cd '$SCRIPT_DIR' && ./deploy_sam3_service.sh '$PORT' && exec tail -f '$SCRIPT_DIR/service.log'"

printf 'started tmux session %s for SAM3 on port %s\n' "$SESSION_NAME" "$PORT"
