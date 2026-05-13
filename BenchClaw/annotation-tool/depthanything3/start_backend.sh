#!/usr/bin/env bash
set -euo pipefail

export DEPTHANYTHING3_HOST="${DEPTHANYTHING3_HOST:-127.0.0.1}"
export DEPTHANYTHING3_PORT="${DEPTHANYTHING3_PORT:-8008}"
export DEPTHANYTHING3_MODEL_DIR="${DEPTHANYTHING3_MODEL_DIR:-/home/maqiang/model/DA3NESTED-GIANT-LARGE-1.1}"
export DEPTHANYTHING3_GALLERY_DIR="${DEPTHANYTHING3_GALLERY_DIR:-/home/maqiang/BenchClaw/thirty_part/annotationTools/Depth-Anything-3/workspace/gallery}"

python3 /home/maqiang/BenchClaw/BenchClaw/annotation-tool/depthanything3/depthanything3_client.py ensure-server "$@"
