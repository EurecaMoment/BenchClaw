---
name: default-annotation
description: "Use this skill when BenchClaw needs the default local image annotation pipeline that turns a folder of images into tool-generated semantic entity masks, depth maps, entity annotations, and optional Stage3 candidate records. It orchestrates local VLM, YOLOE, SAM3, and Depth Anything 3 services; outputs are pseudo/assistant annotations and must not be treated as final GT without the stage plan's verification or human review."
license: Proprietary. Local workspace tool.
---

# Default Annotation Skill

This folder contains a copied, self-contained launcher for the default image annotation workflow:

```text
run_batch_image_to_gt.sh
run_image_to_semantic_depth.py
```

The pipeline uses sibling BenchClaw annotation tools:

- `BENCHCLAW_ROOT/annotation-tool/llm-local/llm_local_client.py`
- `BENCHCLAW_ROOT/annotation-tool/yoloe/yoloe_client.py`
- `BENCHCLAW_ROOT/annotation-tool/sam3/sam3_client.py`
- `BENCHCLAW_ROOT/annotation-tool/depthanything3/depthanything3_client.py`

## When To Use

Use this tool for default, broad-coverage image pseudo annotation when a Stage3 source branch needs:

- VLM-proposed candidate object/category terms
- YOLOE existence verification for candidate terms
- SAM3 text-prompt semantic/entity masks
- Depth Anything 3 depth maps
- per-image `result.json`, `entity_annotations.json`, masks, semantic visualization, and depth visualization

Do not use this tool as an automatic final-GT source. Its outputs are `tool_generated_candidate` records unless the current stage plan defines a separate verification path.

## Service Preconditions

Before running a batch, verify the local services are already reachable:

```bash
python3 "$BENCHCLAW_ROOT/annotation-tool/yoloe/yoloe_client.py" health
python3 "$BENCHCLAW_ROOT/annotation-tool/sam3/sam3_client.py" health
python3 "$BENCHCLAW_ROOT/annotation-tool/depthanything3/depthanything3_client.py" status
python3 "$BENCHCLAW_ROOT/annotation-tool/llm-local/llm_local_client.py" health
```

Expected ports:

- YOLOE: `127.0.0.1:8766`
- SAM3: `127.0.0.1:8765`
- Depth Anything 3: `127.0.0.1:8008`
- local VLM/LLM: `127.0.0.1:9001`

If any service is unavailable, write a blocker instead of silently producing partial GT.

## Batch Usage

Run from any directory. Prefer environment variables instead of editing the script:

```bash
export BENCHCLAW_ROOT=/abs/path/to/BenchClaw/BenchClaw
IMG_DIR=/abs/path/to/images \
  OUT_ROOT=/abs/path/to/default_annotation_output \
  MAX_VLM_TERMS=100 \
  YOLOE_CONF=0.18 \
  SAM3_MAX_MASKS_PER_LABEL=200 \
  bash "$BENCHCLAW_ROOT/annotation-tool/default-annotation/run_batch_image_to_gt.sh"
```

For BenchClaw Stage3 candidate archival, explicitly enable it:

```bash
export BENCHCLAW_ROOT=/abs/path/to/BenchClaw/BenchClaw
IMG_DIR=/abs/path/to/images \
  OUT_ROOT=/abs/path/to/default_annotation_output \
  ENABLE_STAGE3=1 \
  WORKSPACE_ROOT=/abs/path/to/workspace \
  BRANCH=realdata \
  GROUP_NAME=<source_or_dataset_name> \
  bash "$BENCHCLAW_ROOT/annotation-tool/default-annotation/run_batch_image_to_gt.sh"
```

Supported `BRANCH` values:

- `realdata`
- `benchmarkdataset`

For `benchmarkdataset`, set `SPLIT_NAME=<split_or_category>` when using the batch script.

## Single-Image Usage

```bash
python3 "$BENCHCLAW_ROOT/annotation-tool/default-annotation/run_image_to_semantic_depth.py" \
  --image /abs/path/to/image.jpg \
  --out-dir /abs/path/to/output/image_id \
  --max-vlm-terms 100 \
  --yoloe-conf 0.18 \
  --sam3-max-masks-per-label 200 \
  --record-id image_id
```

Optional Stage3 archival:

```bash
python3 "$BENCHCLAW_ROOT/annotation-tool/default-annotation/run_image_to_semantic_depth.py" \
  --image /abs/path/to/image.jpg \
  --out-dir /abs/path/to/output/image_id \
  --workspace-root "$WORKSPACE_ROOT" \
  --branch realdata \
  --group-name <source_or_dataset_name> \
  --record-id image_id
```

## Outputs

Each image writes:

```text
<OUT_ROOT>/<image_stem>/
  result.json
  entity_annotations.json
  semantic_entity_segmentation.png
  depth_map.png
  instance_masks/
  da3_export/
  stdout.log
  stderr.log
```

The batch runner also writes:

```text
<OUT_ROOT>/_batch_logs/
  success.txt
  failed.txt
  skipped.txt
  run_<timestamp>.log
```

When Stage3 archival is enabled, the Python tool writes candidate artifacts under:

```text
WORKSPACE_ROOT/stage3/artifacts/data_17_annotated_real_image_bundle/
WORKSPACE_ROOT/stage3/artifacts/data_18_annotated_existing_benchmark_bundle/
```

depending on `BRANCH`.

## Integrity Rules

- Treat all generated records as pseudo annotations unless verified by a separate stage gate.
- Preserve image path, `record_id`, service responses, confidence values, and generated artifact paths in `result.json`.
- Do not overwrite existing successful per-image `result.json`; the batch runner skips it.
- Do not write into other annotation-tool folders except by calling their clients.
- If service calls fail, keep `stderr.log` and record the image in `_batch_logs/failed.txt`.
