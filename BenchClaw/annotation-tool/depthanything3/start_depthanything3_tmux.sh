#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SESSION_NAME="${DEPTHANYTHING3_TMUX_SESSION:-annot_depthanything3}"
PORT="${1:-8008}"

# 固定使用 GPU 1
GPU_ID="${DEPTHANYTHING3_GPU_ID:-1}"

if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
  printf 'tmux session %s already exists\n' "$SESSION_NAME"
  exit 0
fi

tmux new-session -d -s "$SESSION_NAME" \
  "cd '$SCRIPT_DIR' && CUDA_VISIBLE_DEVICES='$GPU_ID' ./deploy_depthanything3_service.sh '$PORT' && exec tail -f '$SCRIPT_DIR/service.log'"

printf 'started tmux session %s for DepthAnything3 on GPU %s, port %s\n' "$SESSION_NAME" "$GPU_ID" "$PORT"