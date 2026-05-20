#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CARLA_ROOT="/home/maqiang/simulators/CARLA"
PORT="${1:-2000}"
GRAPHICS_ADAPTER="${2:-0}"
BASE_RUNTIME_ROOT="${3:-/tmp/carla_fix_run_${PORT}}"
SUPERVISOR_LOG="${4:-${BASE_RUNTIME_ROOT}/supervisor.log}"
STREAM_PORT="$((PORT + 1))"

mkdir -p "$BASE_RUNTIME_ROOT"
exec > >(tee -a "$SUPERVISOR_LOG") 2>&1

health_check() {
  python "$ROOT_DIR/test_connect.py" --host 127.0.0.1 --port "$PORT" >/dev/null 2>&1
}

cleanup_stale_listeners() {
  local pids
  pids="$(ss -ltnp | grep -E ":${PORT}|:${STREAM_PORT}" | grep CarlaUE4-Linux- | sed -E 's/.*pid=([0-9]+).*/\1/' | sort -u || true)"
  if [ -n "$pids" ]; then
    echo "[$(date --iso-8601=seconds)] killing stale CARLA listener pids: $pids"
    kill $pids || true
    sleep 2
  fi
}

attempt=0
backoff_seconds=5

echo "[$(date --iso-8601=seconds)] sim_carla supervisor started for port ${PORT}, adapter ${GRAPHICS_ADAPTER}, base runtime ${BASE_RUNTIME_ROOT}"

while true; do
  attempt=$((attempt + 1))
  runtime_root="${BASE_RUNTIME_ROOT}/attempt_${attempt}_$(date +%s)"
  start_log="${runtime_root}/start.log"
  mkdir -p "$runtime_root"
  printf '%s\n' "$runtime_root" >"${BASE_RUNTIME_ROOT}/current_runtime.txt"

  cleanup_stale_listeners

  echo "[$(date --iso-8601=seconds)] attempt ${attempt}: launching CARLA with runtime root ${runtime_root}"
  (
    export XDG_RUNTIME_DIR="$runtime_root"
    cd "$CARLA_ROOT"
    exec ./start_carla_offscreen.sh -graphicsadapter="$GRAPHICS_ADAPTER" -carla-rpc-port="$PORT" >"$start_log" 2>&1
  ) &
  pid=$!
  echo "[$(date --iso-8601=seconds)] attempt ${attempt}: child pid=${pid}"

  healthy=0
  for _ in $(seq 1 90); do
    if health_check; then
      healthy=1
      break
    fi
    if ! kill -0 "$pid" 2>/dev/null; then
      break
    fi
    sleep 2
  done

  if [ "$healthy" -eq 1 ]; then
    echo "[$(date --iso-8601=seconds)] attempt ${attempt}: CARLA healthy on 127.0.0.1:${PORT}"
    while kill -0 "$pid" 2>/dev/null; do
      sleep 5
    done
    set +e
    wait "$pid"
    status=$?
    set -e
    echo "[$(date --iso-8601=seconds)] attempt ${attempt}: CARLA exited after being healthy with status ${status}; restarting after ${backoff_seconds}s"
  else
    if kill -0 "$pid" 2>/dev/null; then
      echo "[$(date --iso-8601=seconds)] attempt ${attempt}: CARLA did not become healthy in time; terminating pid ${pid}"
      kill "$pid" || true
    fi
    set +e
    wait "$pid"
    status=$?
    set -e
    echo "[$(date --iso-8601=seconds)] attempt ${attempt}: CARLA exited before healthy with status ${status}"
  fi

  if [ -f "$start_log" ]; then
    if grep -q 'VK_ERROR_OUT_OF_DEVICE_MEMORY' "$start_log"; then
      backoff_seconds=30
      echo "[$(date --iso-8601=seconds)] detected GPU memory pressure; using backoff ${backoff_seconds}s"
    elif grep -q 'std::bad_cast' "$start_log"; then
      backoff_seconds=5
      echo "[$(date --iso-8601=seconds)] detected msgpack bad_cast; retrying with a fresh runtime root"
    else
      backoff_seconds=10
    fi
  fi

  sleep "$backoff_seconds"
done
