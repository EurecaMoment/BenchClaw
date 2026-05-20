#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${1:-9001}"
HOST="${LLM_LOCAL_HOST:-127.0.0.1}"
BASE_URL="http://$HOST:$PORT"
LOG_FILE="$SCRIPT_DIR/service.log"
PID_FILE="$SCRIPT_DIR/service.pid"
CONDA_SH="/home/maqiang/miniconda3/etc/profile.d/conda.sh"
MODEL_DIR="${LLM_LOCAL_MODEL_DIR:-/home/maqiang/model/Qwen/Qwen3.5-0.8B}"
MODEL_NAME="${LLM_LOCAL_MODEL_NAME:-qwen3.5-0.8b}"
CUDA_DEVICES="${LLM_LOCAL_CUDA_VISIBLE_DEVICES:-0}"
TP_SIZE="${LLM_LOCAL_TP_SIZE:-1}"
GPU_MEM_UTIL="${LLM_LOCAL_GPU_MEMORY_UTILIZATION:-0.2}"

health_check() {
  python3 - "$BASE_URL" <<'PY'
import json
import sys
import urllib.request

base_url = sys.argv[1].rstrip("/")
with urllib.request.urlopen(f"{base_url}/health", timeout=5) as response:
    if response.status != 200:
        raise SystemExit(1)
    body = response.read().decode("utf-8")
try:
    payload = json.loads(body)
except json.JSONDecodeError:
    payload = {"raw": body}
if isinstance(payload, dict) and payload.get("error"):
    raise SystemExit(1)
print(body)
PY
}

if health_check; then
  printf 'LLM local service already healthy on %s\n' "$BASE_URL"
  LLM_LOCAL_BASE_URL="$BASE_URL" python3 "$SCRIPT_DIR/llm_local_client.py" models
  exit 0
fi

nohup bash -lc "source \"$CONDA_SH\" && conda activate vllm && export CUDA_VISIBLE_DEVICES=$CUDA_DEVICES && exec vllm serve \"$MODEL_DIR\" --served-model-name $MODEL_NAME --host $HOST --port $PORT --tensor-parallel-size $TP_SIZE --dtype auto --gpu-memory-utilization $GPU_MEM_UTIL" >"$LOG_FILE" 2>&1 &
PID=$!
printf '%s\n' "$PID" >"$PID_FILE"

for _ in $(seq 1 180); do
  if health_check; then
    printf 'LLM local service started on %s\n' "$BASE_URL"
    LLM_LOCAL_BASE_URL="$BASE_URL" python3 "$SCRIPT_DIR/llm_local_client.py" models
    exit 0
  fi
  if ! kill -0 "$PID" 2>/dev/null; then
    printf 'LLM local service exited before becoming healthy. Check %s\n' "$LOG_FILE" >&2
    exit 1
  fi
  sleep 2
done

printf 'Timed out waiting for LLM local service on %s. Check %s\n' "$BASE_URL" "$LOG_FILE" >&2
exit 1
