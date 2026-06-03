#!/usr/bin/env bash
set -euo pipefail

# 固定 CUDA 设备编号按物理 PCI_BUS_ID 排序
export CUDA_DEVICE_ORDER=PCI_BUS_ID

# 默认使用物理 GPU 2；也可以外部覆盖：
# SAM3_GPU_ID=3 ./start_sam3_service.sh 8765
export CUDA_VISIBLE_DEVICES="${SAM3_GPU_ID:-2}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 默认监听 127.0.0.1:8765
# 可用第一个参数覆盖端口：
# ./start_sam3_service.sh 8766
export SAM3_HOST="${SAM3_HOST:-127.0.0.1}"
export SAM3_PORT="${SAM3_PORT:-${1:-8765}}"
export NO_PROXY="${NO_PROXY:-},127.0.0.1,localhost,$SAM3_HOST"
export no_proxy="${no_proxy:-},127.0.0.1,localhost,$SAM3_HOST"

cd "$SCRIPT_DIR"

echo "[info] starting SAM3 service in current shell/tmux pane"
echo "[info] script_dir           = $SCRIPT_DIR"
echo "[info] CUDA_DEVICE_ORDER    = $CUDA_DEVICE_ORDER"
echo "[info] CUDA_VISIBLE_DEVICES = $CUDA_VISIBLE_DEVICES"
echo "[info] SAM3_HOST            = $SAM3_HOST"
echo "[info] SAM3_PORT            = $SAM3_PORT"

python3 "$SCRIPT_DIR/sam3_client.py" ensure-server --timeout 180
python3 "$SCRIPT_DIR/sam3_client.py" health

echo "[info] SAM3 service is healthy"
echo "[info] following service.log ..."
exec tail -n 0 -F "$SCRIPT_DIR/service.log"
