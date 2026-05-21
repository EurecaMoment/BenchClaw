# fixed_chain_runner_contract

## Purpose

This document specifies the executable reference interface for the non-simulator fixed semi-supervised chain used by Stage3 nodes 18 and 19.

## Script

`scripts/run_fixed_semi_supervised_chain.py`

## Required inputs

- original image file
- llm-local output JSON
- YOLOE output JSON
- SAM3 output JSON
- Depth Anything 3 output JSON
- branch name: `realdata` or `benchmarkdataset`
- logical group name and optional split name
- target output paths for fused record and stage3 asset tree

## Required outputs

- `original/` image file
- `semantic_entity_segmentation/` image file
- `depth/` image file
- `gt/` fused GT candidate JSON
- appended `semi_gt_manifest.sqlite_export.jsonl` compatibility record with `artifact_paths.original`, `artifact_paths.semantic_entity_segmentation`, `artifact_paths.depth`, and `artifact_paths.gt`, while the canonical truth is stored in `stage3.db.semi_gt_candidates`

## Non-negotiable rules

- the runner is a reference interface for path organization and manifest closure;
- it does not replace real YOLOE, SAM3, Depth Anything 3, or LLM inference;
- nodes 18 and 19 must still ensure the upstream tool outputs are real and correspond to the same `record_id`;
- no retained sample may skip any of the four asset classes.
