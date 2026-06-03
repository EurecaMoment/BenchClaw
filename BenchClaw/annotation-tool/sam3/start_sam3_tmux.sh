#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SESSION_NAME="${SAM3_TMUX_SESSION:-annot_sam3}"
PORT="${1:-8765}"

# 固定使用物理 GPU 2
GPU_ID="${SAM3_GPU_ID:-2}"
export SAM3_HOST="${SAM3_HOST:-127.0.0.1}"
export SAM3_PORT="${SAM3_PORT:-$PORT}"
export NO_PROXY="${NO_PROXY:-},127.0.0.1,localhost,$SAM3_HOST"
export no_proxy="${no_proxy:-},127.0.0.1,localhost,$SAM3_HOST"

cd "$SCRIPT_DIR"

printf '[info] ensuring SAM3 service before opening tmux...\n'
CUDA_VISIBLE_DEVICES="$GPU_ID" ./deploy_sam3_service.sh "$PORT"

if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
  printf '[info] tmux session %s already exists; service has been verified.\n' "$SESSION_NAME"
  exit 0
fi

tmux new-session -d -s "$SESSION_NAME" \
  "cd '$SCRIPT_DIR' && export SAM3_HOST='$SAM3_HOST' SAM3_PORT='$SAM3_PORT' NO_PROXY=\"\${NO_PROXY:-},127.0.0.1,localhost,$SAM3_HOST\" no_proxy=\"\${no_proxy:-},127.0.0.1,localhost,$SAM3_HOST\" CUDA_VISIBLE_DEVICES='$GPU_ID' && exec tail -n 0 -F '$SCRIPT_DIR/service.log'"

printf 'started tmux session %s for SAM3 on GPU %s, port %s\n' "$SESSION_NAME" "$GPU_ID" "$PORT"
