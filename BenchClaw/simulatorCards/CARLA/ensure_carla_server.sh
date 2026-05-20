#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CARLA_ROOT="/home/maqiang/simulators/CARLA"
PORT="${1:-2000}"
STREAM_PORT="$((PORT + 1))"
LOG_FILE="$ROOT_DIR/service.log"
PID_FILE="$ROOT_DIR/service.pid"
GRAPHICS_ADAPTER="${CARLA_GRAPHICS_ADAPTER:-0}"
RUNTIME_ROOT="${CARLA_RUNTIME_ROOT:-/tmp/carla_runtime_${PORT}}"

health_check() {
  conda run -n carla_py310 python "$ROOT_DIR/test_connect.py" --host 127.0.0.1 --port "$PORT" >/dev/null 2>&1
}

if health_check; then
  printf 'CARLA already healthy on 127.0.0.1:%s (stream %s)\n' "$PORT" "$STREAM_PORT"
  exit 0
fi

mkdir -p "$RUNTIME_ROOT"
nohup bash -lc "export XDG_RUNTIME_DIR=\"$RUNTIME_ROOT\" && cd \"$CARLA_ROOT\" && exec ./start_carla_offscreen.sh -graphicsadapter=$GRAPHICS_ADAPTER -carla-rpc-port=$PORT" >"$LOG_FILE" 2>&1 &
PID=$!
printf '%s\n' "$PID" >"$PID_FILE"

for _ in $(seq 1 90); do
  if health_check; then
    printf 'CARLA started on 127.0.0.1:%s (stream %s)\n' "$PORT" "$STREAM_PORT"
    exit 0
  fi
  if ! kill -0 "$PID" 2>/dev/null; then
    printf 'CARLA exited before becoming healthy. Check %s\n' "$LOG_FILE" >&2
    exit 1
  fi
  sleep 2
done

printf 'Timed out waiting for CARLA on port %s. Check %s\n' "$PORT" "$LOG_FILE" >&2
exit 1
