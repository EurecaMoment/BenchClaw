#!/usr/bin/env bash
set -euo pipefail

export CUDA_DEVICE_ORDER=PCI_BUS_ID
export CUDA_VISIBLE_DEVICES="${SAM3_GPU_ID:-2}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export SAM3_HOST="${SAM3_HOST:-127.0.0.1}"
export SAM3_PORT="${SAM3_PORT:-${1:-8765}}"
export NO_PROXY="${NO_PROXY:-},127.0.0.1,localhost,$SAM3_HOST"
export no_proxy="${no_proxy:-},127.0.0.1,localhost,$SAM3_HOST"

python3 "$SCRIPT_DIR/sam3_client.py" ensure-server --timeout 180
python3 "$SCRIPT_DIR/sam3_client.py" warmup --timeout "${SAM3_WARMUP_TIMEOUT:-300}"
python3 "$SCRIPT_DIR/sam3_client.py" health
