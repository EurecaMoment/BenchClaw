#!/usr/bin/env bash
set -u
set -o pipefail

# ========= 用户配置区 =========

TOOL_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BENCHCLAW_ROOT="${BENCHCLAW_ROOT:-$(cd "$TOOL_ROOT/../.." && pwd)}"
BENCHCLAW_PARENT="$(cd "$BENCHCLAW_ROOT/.." && pwd)"

SCRIPT="${DEFAULT_ANNOTATION_SCRIPT:-$TOOL_ROOT/run_image_to_semantic_depth.py}"

IMG_DIR="${IMG_DIR:-}"
OUT_ROOT="${OUT_ROOT:-}"

MAX_VLM_TERMS="${MAX_VLM_TERMS:-100}"
YOLOE_CONF="${YOLOE_CONF:-0.18}"
SAM3_MAX_MASKS_PER_LABEL="${SAM3_MAX_MASKS_PER_LABEL:-200}"

# 是否启用 BenchClaw Stage3 归档
ENABLE_STAGE3="${ENABLE_STAGE3:-0}"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$BENCHCLAW_PARENT/workspace}"
BRANCH="${BRANCH:-realdata}"
GROUP_NAME="${GROUP_NAME:-Uav_photos}"
SPLIT_NAME="${SPLIT_NAME:-}"

# ========= 不建议改下面 =========

if [[ -z "$IMG_DIR" ]]; then
  echo "[error] IMG_DIR is required. Example: IMG_DIR=/abs/path/to/images bash $0" >&2
  exit 2
fi

if [[ -z "$OUT_ROOT" ]]; then
  echo "[error] OUT_ROOT is required. Example: OUT_ROOT=/abs/path/to/output bash $0" >&2
  exit 2
fi

mkdir -p "$OUT_ROOT"

LOG_DIR="$OUT_ROOT/_batch_logs"
mkdir -p "$LOG_DIR"

SUCCESS_LOG="$LOG_DIR/success.txt"
FAILED_LOG="$LOG_DIR/failed.txt"
SKIPPED_LOG="$LOG_DIR/skipped.txt"
RUN_LOG="$LOG_DIR/run_$(date +%Y%m%d_%H%M%S).log"

touch "$SUCCESS_LOG" "$FAILED_LOG" "$SKIPPED_LOG"

echo "[info] SCRIPT   = $SCRIPT" | tee -a "$RUN_LOG"
echo "[info] IMG_DIR  = $IMG_DIR" | tee -a "$RUN_LOG"
echo "[info] OUT_ROOT = $OUT_ROOT" | tee -a "$RUN_LOG"
echo "[info] LOG_DIR  = $LOG_DIR" | tee -a "$RUN_LOG"

if [[ ! -f "$SCRIPT" ]]; then
  echo "[error] script not found: $SCRIPT" | tee -a "$RUN_LOG"
  exit 2
fi

if [[ ! -d "$IMG_DIR" ]]; then
  echo "[error] image dir not found: $IMG_DIR" | tee -a "$RUN_LOG"
  exit 2
fi

# 先检查关键服务端口
echo "[step] checking services ..." | tee -a "$RUN_LOG"

for port in 8766 8765 8008 9001; do
  if ss -lnt | grep -q ":${port} "; then
    echo "[ok] port ${port} is listening" | tee -a "$RUN_LOG"
  else
    echo "[warn] port ${port} is NOT listening" | tee -a "$RUN_LOG"
  fi
done

echo "[step] collecting images ..." | tee -a "$RUN_LOG"

mapfile -d '' IMAGES < <(
  find "$IMG_DIR" -type f \( \
    -iname "*.jpg" -o \
    -iname "*.jpeg" -o \
    -iname "*.png" -o \
    -iname "*.webp" -o \
    -iname "*.bmp" \
  \) -print0 | sort -z
)

TOTAL="${#IMAGES[@]}"
echo "[info] total images = $TOTAL" | tee -a "$RUN_LOG"

if [[ "$TOTAL" -eq 0 ]]; then
  echo "[warn] no image found in $IMG_DIR" | tee -a "$RUN_LOG"
  exit 0
fi

OK=0
FAIL=0
SKIP=0
IDX=0

for img in "${IMAGES[@]}"; do
  IDX=$((IDX + 1))

  filename="$(basename "$img")"
  stem="${filename%.*}"

  out_dir="$OUT_ROOT/$stem"
  result_json="$out_dir/result.json"

  echo "" | tee -a "$RUN_LOG"
  echo "============================================================" | tee -a "$RUN_LOG"
  echo "[run] $IDX / $TOTAL" | tee -a "$RUN_LOG"
  echo "[img] $img" | tee -a "$RUN_LOG"
  echo "[out] $out_dir" | tee -a "$RUN_LOG"

  # 已经成功生成 result.json 就跳过
  if [[ -s "$result_json" ]]; then
    echo "[skip] result exists: $result_json" | tee -a "$RUN_LOG"
    echo "$img" >> "$SKIPPED_LOG"
    SKIP=$((SKIP + 1))
    continue
  fi

  mkdir -p "$out_dir"

  cmd=(
    python3 "$SCRIPT"
    --image "$img"
    --out-dir "$out_dir"
    --max-vlm-terms "$MAX_VLM_TERMS"
    --yoloe-conf "$YOLOE_CONF"
    --sam3-max-masks-per-label "$SAM3_MAX_MASKS_PER_LABEL"
    --record-id "$stem"
  )

  if [[ "$ENABLE_STAGE3" -eq 1 ]]; then
    cmd+=(
      --workspace-root "$WORKSPACE_ROOT"
      --branch "$BRANCH"
      --group-name "$GROUP_NAME"
    )
    if [[ -n "$SPLIT_NAME" ]]; then
      cmd+=(--split-name "$SPLIT_NAME")
    fi
  fi

  echo "[cmd] ${cmd[*]}" | tee -a "$RUN_LOG"

  if "${cmd[@]}" >"$out_dir/stdout.log" 2>"$out_dir/stderr.log"; then
    if [[ -s "$result_json" ]]; then
      echo "[success] $img" | tee -a "$RUN_LOG"
      echo "$img" >> "$SUCCESS_LOG"
      OK=$((OK + 1))
    else
      echo "[fail] command finished but result.json missing: $img" | tee -a "$RUN_LOG"
      echo "$img" >> "$FAILED_LOG"
      FAIL=$((FAIL + 1))
    fi
  else
    echo "[fail] command failed: $img" | tee -a "$RUN_LOG"
    echo "[hint] see: $out_dir/stderr.log" | tee -a "$RUN_LOG"
    echo "$img" >> "$FAILED_LOG"
    FAIL=$((FAIL + 1))
  fi

  echo "[progress] ok=$OK fail=$FAIL skip=$SKIP total=$TOTAL" | tee -a "$RUN_LOG"
done

echo "" | tee -a "$RUN_LOG"
echo "==================== batch finished ====================" | tee -a "$RUN_LOG"
echo "[summary] total=$TOTAL ok=$OK fail=$FAIL skip=$SKIP" | tee -a "$RUN_LOG"
echo "[log] success = $SUCCESS_LOG" | tee -a "$RUN_LOG"
echo "[log] failed  = $FAILED_LOG" | tee -a "$RUN_LOG"
echo "[log] skipped = $SKIPPED_LOG" | tee -a "$RUN_LOG"
echo "[log] run     = $RUN_LOG" | tee -a "$RUN_LOG"

if [[ "$FAIL" -gt 0 ]]; then
  exit 1
fi
