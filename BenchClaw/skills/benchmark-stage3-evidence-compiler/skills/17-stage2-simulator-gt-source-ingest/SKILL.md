# Node 17 — stage2-simulator-gt-source-ingest

## Role

Ingest Stage2 node-17 simulator multimodal observations and privileged GT as a read-only Stage3 source.

## Parents

```text
(none)
```

## May read

- `WORKSPACE_ROOT/stage2/17-simulator-multimodal-gt-acquisition/**`
- `WORKSPACE_ROOT/config/stage3_input_paths.json`

## Must write

- `WORKSPACE_ROOT/stage3/17-stage2-simulator-gt-source-ingest/source_manifest.jsonl`
- `WORKSPACE_ROOT/stage3/17-stage2-simulator-gt-source-ingest/gt_source_manifest.jsonl`
- `WORKSPACE_ROOT/stage3/17-stage2-simulator-gt-source-ingest/source_summary.md`
- `WORKSPACE_ROOT/stage3/17-stage2-simulator-gt-source-ingest/DONE.json`
- `WORKSPACE_ROOT/stage3/17-stage2-simulator-gt-source-ingest/USED_INPUTS.json`

## Must not read

- `WORKSPACE_ROOT/stage3/15-stage2-real-image-source-ingest/**`
- `WORKSPACE_ROOT/stage3/16-stage2-existing-benchmark-source-ingest/**`

## Completion

完成后必须写：

```json
{
  "node_id": "17",
  "status": "DONE",
  "output_dir": "WORKSPACE_ROOT/stage3/17-stage2-simulator-gt-source-ingest",
  "timestamp_utc": "<ISO-8601>"
}
```

并运行：

```bash
python scripts/check_used_inputs.py --node 17
python scripts/ready_set_runner.py --workspace WORKSPACE_ROOT
```
