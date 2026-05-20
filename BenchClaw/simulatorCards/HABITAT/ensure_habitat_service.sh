#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_SCRIPT="/home/maqiang/simulators/habitat/scripts/env_habitat.sh"
PORT="${1:-8401}"
LOG_FILE="$ROOT_DIR/service.log"
PID_FILE="$ROOT_DIR/service.pid"

health_check() {
  python3 - "$PORT" <<'PY'
import json
import sys
import urllib.request

port = int(sys.argv[1])
url = f"http://127.0.0.1:{port}/health"
with urllib.request.urlopen(url, timeout=2) as response:
    payload = json.load(response)
if not payload.get("ok") or payload.get("service") != "habitat":
    raise SystemExit(1)
print(json.dumps(payload, ensure_ascii=True))
PY
}

if health_check >/dev/null 2>&1; then
  printf 'Habitat service already healthy on http://127.0.0.1:%s\n' "$PORT"
  exit 0
fi

nohup bash -lc "source \"$ENV_SCRIPT\" && exec python \"$ROOT_DIR/habitat_service.py\" --port $PORT" >"$LOG_FILE" 2>&1 &
PID=$!
printf '%s\n' "$PID" >"$PID_FILE"

for _ in $(seq 1 45); do
  if health_check >/dev/null 2>&1; then
    printf 'Habitat service started on http://127.0.0.1:%s\n' "$PORT"
    exit 0
  fi
  if ! kill -0 "$PID" 2>/dev/null; then
    printf 'Habitat service exited before becoming healthy. Check %s\n' "$LOG_FILE" >&2
    exit 1
  fi
  sleep 2
done

printf 'Timed out waiting for Habitat service on port %s. Check %s\n' "$PORT" "$LOG_FILE" >&2
exit 1
