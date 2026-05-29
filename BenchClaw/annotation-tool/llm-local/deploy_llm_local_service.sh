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

# 默认仍用 0 卡；如果要换卡：
# LLM_LOCAL_CUDA_VISIBLE_DEVICES=3 ./deploy_llm_local_service.sh 9001
CUDA_DEVICES="${LLM_LOCAL_CUDA_VISIBLE_DEVICES:-0}"

TP_SIZE="${LLM_LOCAL_TP_SIZE:-1}"
GPU_MEM_UTIL="${LLM_LOCAL_GPU_MEMORY_UTILIZATION:-0.2}"

# 支持 32000 输出 token 时，vLLM 的最大上下文最好也拉高
MAX_MODEL_LEN="${LLM_LOCAL_MAX_MODEL_LEN:-32768}"

# 给 llm_local_client.py / pipeline 读取的默认请求参数
export LLM_LOCAL_BASE_URL="$BASE_URL"
export LLM_LOCAL_MODEL="$MODEL_NAME"
export LLM_LOCAL_MAX_TOKENS="${LLM_LOCAL_MAX_TOKENS:-32000}"
export LLM_LOCAL_REPETITION_PENALTY="${LLM_LOCAL_REPETITION_PENALTY:-1.15}"

health_check() {
  python3 - "$BASE_URL" <<'PY' >/dev/null 2>&1
import json
import sys
import urllib.request

base_url = sys.argv[1].rstrip("/")

try:
    with urllib.request.urlopen(f"{base_url}/health", timeout=5) as response:
        if response.status != 200:
            raise SystemExit(1)
        body = response.read().decode("utf-8")
except Exception:
    raise SystemExit(1)

try:
    payload = json.loads(body) if body else {}
except json.JSONDecodeError:
    payload = {"raw": body}

if isinstance(payload, dict) and payload.get("error"):
    raise SystemExit(1)
PY
}

print_models() {
  if [[ -f "$SCRIPT_DIR/llm_local_client.py" ]]; then
    LLM_LOCAL_BASE_URL="$BASE_URL" python3 "$SCRIPT_DIR/llm_local_client.py" models || true
  else
    curl -s "$BASE_URL/v1/models" || true
    echo
  fi
}

if health_check; then
  printf 'LLM local service already healthy on %s\n' "$BASE_URL"
  print_models
  exit 0
fi

# 如果端口被占用但 health 不通，直接报清楚，不要继续起第二个服务
if ss -lntp 2>/dev/null | grep -q ":$PORT "; then
  printf '[error] Port %s is already occupied, but health check failed.\n' "$PORT" >&2
  printf '[error] Current listener:\n' >&2
  ss -lntp | grep ":$PORT " >&2 || true
  printf '[error] Kill the old process first, for example:\n' >&2
  printf '        fuser -k %s/tcp\n' "$PORT" >&2
  exit 1
fi

if [[ ! -f "$CONDA_SH" ]]; then
  printf '[error] conda.sh not found: %s\n' "$CONDA_SH" >&2
  exit 1
fi

if [[ ! -d "$MODEL_DIR" ]]; then
  printf '[error] MODEL_DIR not found: %s\n' "$MODEL_DIR" >&2
  exit 1
fi

: > "$LOG_FILE"

{
  printf '[info] starting LLM local service\n'
  printf '[info] BASE_URL=%s\n' "$BASE_URL"
  printf '[info] MODEL_DIR=%s\n' "$MODEL_DIR"
  printf '[info] MODEL_NAME=%s\n' "$MODEL_NAME"
  printf '[info] CUDA_VISIBLE_DEVICES=%s\n' "$CUDA_DEVICES"
  printf '[info] TP_SIZE=%s\n' "$TP_SIZE"
  printf '[info] GPU_MEM_UTIL=%s\n' "$GPU_MEM_UTIL"
  printf '[info] MAX_MODEL_LEN=%s\n' "$MAX_MODEL_LEN"
  printf '[info] LLM_LOCAL_MAX_TOKENS=%s\n' "$LLM_LOCAL_MAX_TOKENS"
  printf '[info] LLM_LOCAL_REPETITION_PENALTY=%s\n' "$LLM_LOCAL_REPETITION_PENALTY"
} | tee -a "$LOG_FILE"

nohup bash -lc "
set -euo pipefail
source \"$CONDA_SH\"
conda activate vllm

export CUDA_DEVICE_ORDER=PCI_BUS_ID
export CUDA_VISIBLE_DEVICES=\"$CUDA_DEVICES\"

exec vllm serve \"$MODEL_DIR\" \
  --served-model-name \"$MODEL_NAME\" \
  --host \"$HOST\" \
  --port \"$PORT\" \
  --tensor-parallel-size \"$TP_SIZE\" \
  --dtype auto \
  --gpu-memory-utilization \"$GPU_MEM_UTIL\" \
  --max-model-len \"$MAX_MODEL_LEN\"
" >>"$LOG_FILE" 2>&1 &

PID=$!
printf '%s\n' "$PID" > "$PID_FILE"
printf '[info] launcher pid=%s\n' "$PID" | tee -a "$LOG_FILE"
printf '[info] waiting for health check: %s/health\n' "$BASE_URL" | tee -a "$LOG_FILE"

for _ in $(seq 1 300); do
  if health_check; then
    printf 'LLM local service started on %s\n' "$BASE_URL"
    print_models
    exit 0
  fi

  if ! kill -0 "$PID" 2>/dev/null; then
    printf '[error] LLM local service exited before becoming healthy. Last logs:\n' >&2
    tail -n 160 "$LOG_FILE" >&2 || true
    exit 1
  fi

  sleep 2
done

printf '[error] Timed out waiting for LLM local service on %s. Last logs:\n' "$BASE_URL" >&2
tail -n 160 "$LOG_FILE" >&2 || true
exit 1