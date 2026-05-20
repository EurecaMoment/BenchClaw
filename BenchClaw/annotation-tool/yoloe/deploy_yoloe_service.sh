#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BENCHCLAW_ROOT="${BENCHCLAW_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
BENCHCLAW_PARENT="$(cd "$BENCHCLAW_ROOT/.." && pwd)"
THIRD_PARTY_ROOT="${THIRD_PARTY_ROOT:-$BENCHCLAW_PARENT/thirty_part}"

export YOLOE_SERVICE_HOST="${YOLOE_SERVICE_HOST:-127.0.0.1}"
export YOLOE_SERVICE_PORT="${YOLOE_SERVICE_PORT:-${1:-8766}}"
export YOLOE_CONDA_ENV="${YOLOE_CONDA_ENV:-yoloe}"
export YOLOE_REPO="${YOLOE_REPO:-$THIRD_PARTY_ROOT/annotationTools/yoloe}"
export YOLOE_CHECKPOINT="${YOLOE_CHECKPOINT:-/home/maqiang/model/yoloe_11_l/yoloe-11l-seg.pt}"
export YOLOE_MOBILECLIP="${YOLOE_MOBILECLIP:-/home/maqiang/model/yoloe_11_l/mobileclip_blt.pt}"
export YOLOE_PF_CHECKPOINT="${YOLOE_PF_CHECKPOINT:-/home/maqiang/model/yoloe_11_l/yoloe-11l-seg-pf.pt}"

python3 "$SCRIPT_DIR/yoloe_client.py" ensure-server --timeout 180
python3 "$SCRIPT_DIR/yoloe_client.py" health
