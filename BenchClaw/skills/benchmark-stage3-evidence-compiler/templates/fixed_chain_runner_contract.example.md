# fixed_chain_runner_contract

## Purpose

This document specifies the executable interface for the non-simulator semi-supervised chain used by Stage3 nodes 18 and 19. It is the canonical contract for `scripts/run_semi_supervised_annotation.py`, which is the **only** allowed execution entry point in those nodes.

## Script

`scripts/run_semi_supervised_annotation.py`  (conda env: `sam3`)

## Required inputs (CLI flags)

- `--image`              absolute path to the input image
- `--out-dir`            per-record working directory (free-form scratch space)
- `--workspace-root`     BenchClaw workspace root used to materialize the Stage3 contract
- `--branch`             `realdata` or `benchmarkdataset`
- `--group-name`         `realdata` scene/source name, or `benchmarkdataset` dataset name
- `--split-name`         (only for benchmarkdataset) split or category name
- `--record-id`          stable record identifier; defaults to the image stem

## Required outputs

For every retained sample the script writes:

- `WORKSPACE_ROOT/stage3/<branch>/<group>[/<split>]/<record_id>/original/<record_id>.<ext>`
- `WORKSPACE_ROOT/stage3/<branch>/<group>[/<split>]/<record_id>/semantic_entity_segmentation/<record_id>.png`
- `WORKSPACE_ROOT/stage3/<branch>/<group>[/<split>]/<record_id>/depth/<record_id>.png`
- `WORKSPACE_ROOT/stage3/<branch>/<group>[/<split>]/<record_id>/gt/<record_id>.json`
- one appended record in:
  `WORKSPACE_ROOT/stage3/{18-real-image-semi-supervised-gt|19-benchmark-image-semi-supervised-gt}/semi_gt_manifest.jsonl`
- canonical truth-source rows in `WORKSPACE_ROOT/stage3/<node>/manifest.jsonl`, table `semi_gt_candidates`, with `artifact_paths_json` referencing the four files above

## Non-negotiable rules

- The runner does not replace real YOLOE / SAM3 / Depth Anything 3 / LLM inference; if any of the four services fails, the node must block.
- Nodes 18 and 19 must call the script via `subprocess`; they must not handcraft `semi_gt_manifest.jsonl` rows nor insert rows into `semi_gt_manifest.jsonl` directly.
- No retained sample may skip any of the four asset classes (`original`, `semantic_entity_segmentation`, `depth`, `gt`).
- Manifest and JSONL rows must remain in sync: every JSONL row must be reproducible from the JSONL truth source.
