#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BENCHCLAW_ROOT="${BENCHCLAW_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
BENCHCLAW_PARENT="$(cd "$BENCHCLAW_ROOT/.." && pwd)"
THIRD_PARTY_ROOT="${THIRD_PARTY_ROOT:-$BENCHCLAW_PARENT/thirty_part}"

export DEPTHANYTHING3_HOST="${DEPTHANYTHING3_HOST:-127.0.0.1}"
export DEPTHANYTHING3_PORT="${DEPTHANYTHING3_PORT:-${1:-8008}}"
export DEPTHANYTHING3_CONDA_ENV="${DEPTHANYTHING3_CONDA_ENV:-depthanythingv3}"
export DEPTHANYTHING3_PROJECT_DIR="${DEPTHANYTHING3_PROJECT_DIR:-$THIRD_PARTY_ROOT/annotationTools/Depth-Anything-3}"
export DEPTHANYTHING3_MODEL_DIR="${DEPTHANYTHING3_MODEL_DIR:-/home/maqiang/model/DA3NESTED-GIANT-LARGE-1.1}"
export DEPTHANYTHING3_GALLERY_DIR="${DEPTHANYTHING3_GALLERY_DIR:-$THIRD_PARTY_ROOT/annotationTools/Depth-Anything-3/workspace/gallery}"
export CUDA_VISIBLE_DEVICES=2
python3 "$SCRIPT_DIR/depthanything3_client.py" ensure-server --timeout 240 --model-dir "$DEPTHANYTHING3_MODEL_DIR" --device "${DEPTHANYTHING3_DEVICE:-cuda}" --gallery-dir "$DEPTHANYTHING3_GALLERY_DIR"
python3 "$SCRIPT_DIR/depthanything3_client.py" status
