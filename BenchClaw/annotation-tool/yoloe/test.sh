#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/maqiang/BenchClaw/BenchClaw/annotation-tool/yoloe"
ASSET="/home/maqiang/BenchClaw/thirty_part/annotationTools/yoloe/ultralytics/assets/bus.jpg"
RUNS="/home/maqiang/BenchClaw/thirty_part/annotationTools/yoloe/runs"
REQ="$ROOT/visual_smoke_request.json"

python3 "$ROOT/yoloe_client.py" ensure-server
python3 "$ROOT/yoloe_client.py" health

python3 "$ROOT/yoloe_client.py" text-infer \
  --image-path "$ASSET" \
  --names "person,bus" \
  --annotated-output-path "$RUNS/skill_text_bus.jpg"

python3 "$ROOT/yoloe_client.py" visual-infer --request-file "$REQ"

if [ -f "/home/maqiang/model/yoloe_11_l/yoloe-11l-seg-pf.pt" ]; then
  python3 "$ROOT/yoloe_client.py" prompt-free-infer \
    --image-path "$ASSET" \
    --names "person,bus,car" \
    --pf-checkpoint-path "/home/maqiang/model/yoloe_11_l/yoloe-11l-seg-pf.pt" \
    --annotated-output-path "$RUNS/skill_pf_bus.jpg"
else
  printf 'Skipping prompt-free smoke test: dedicated pf checkpoint not found\n'
fi
