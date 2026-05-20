#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SESSION_NAME="${CARLA_TMUX_SESSION:-sim_carla}"
PORT="${1:-2000}"
RUN_ID="${CARLA_RUN_ID:-$(date +%s)}"
RUNTIME_ROOT="/tmp/carla_fix_run_${PORT}_${RUN_ID}"

if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
  tmux kill-session -t "$SESSION_NAME"
fi

PIDS="$(ss -ltnp | grep -E ":${PORT}|:$((PORT + 1))" | grep CarlaUE4-Linux- | sed -E 's/.*pid=([0-9]+).*/\1/' | sort -u || true)"
if [ -n "$PIDS" ]; then
  kill $PIDS || true
  sleep 2
fi

CARLA_RUN_ID="$RUN_ID" CARLA_RUNTIME_ROOT="$RUNTIME_ROOT" "$ROOT_DIR/start_sim_carla_tmux.sh" "$PORT"
