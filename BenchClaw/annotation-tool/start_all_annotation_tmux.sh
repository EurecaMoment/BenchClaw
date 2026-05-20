#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

"$ROOT_DIR/yoloe/start_yoloe_tmux.sh" 8766
"$ROOT_DIR/sam3/start_sam3_tmux.sh" 8765
"$ROOT_DIR/depthanything3/start_depthanything3_tmux.sh" 8008
"$ROOT_DIR/llm-local/start_llm_local_tmux.sh" 9001
