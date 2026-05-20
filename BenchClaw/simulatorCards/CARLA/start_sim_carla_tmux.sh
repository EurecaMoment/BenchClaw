#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SESSION_NAME="${CARLA_TMUX_SESSION:-sim_carla}"
PORT="${1:-2000}"
GRAPHICS_ADAPTER="${CARLA_GRAPHICS_ADAPTER:-0}"
RUN_ID="${CARLA_RUN_ID:-$(date +%s)}"
RUNTIME_ROOT="${CARLA_RUNTIME_ROOT:-/tmp/carla_fix_run_${PORT}_${RUN_ID}}"
LOG_FILE="${CARLA_LOG_FILE:-${RUNTIME_ROOT}/supervisor.log}"

mkdir -p "$RUNTIME_ROOT"

if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
  printf 'tmux session %s already exists\n' "$SESSION_NAME"
  exit 0
fi

tmux new-session -d -s "$SESSION_NAME" \
  "source /home/maqiang/miniconda3/etc/profile.d/conda.sh && conda activate carla_py310 && exec '$ROOT_DIR/run_sim_carla_supervisor.sh' '$PORT' '$GRAPHICS_ADAPTER' '$RUNTIME_ROOT' '$LOG_FILE'"

printf 'started tmux session %s for CARLA on port %s\n' "$SESSION_NAME" "$PORT"
printf 'runtime_root=%s\n' "$RUNTIME_ROOT"
