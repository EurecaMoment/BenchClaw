# Node 17 — stage2-simulator-gt-source-ingest

全局路径约束：`BENCHCLAW_ROOT` 仅作只读输入；`WORKSPACE_ROOT` 是本次流程唯一总工作目录，所有写操作和流程产物只能落在其下。

## Role

Ingest Stage2 node-17 simulator multimodal observations and privileged GT as a read-only Stage3 source.

This node only reads and re-indexes simulator observations and privileged GT that have already been collected and materialized by Stage2 node 17. It must not reconnect to simulator services to capture fresh frames, rerun scenes, or regenerate raw simulator GT inside Stage3.

## Parents

```text
(none)
```

## May read

- `WORKSPACE_ROOT/stage2/17-simulator-multimodal-gt-acquisition/**`
- `WORKSPACE_ROOT/config/stage3_input_paths.json`

## Must write

- `WORKSPACE_ROOT/stage3/stage3.db`
- `WORKSPACE_ROOT/stage3/17-stage2-simulator-gt-source-ingest/source_manifest.sqlite_export.jsonl`
- `WORKSPACE_ROOT/stage3/17-stage2-simulator-gt-source-ingest/gt_source_manifest.sqlite_export.jsonl`
- `WORKSPACE_ROOT/stage3/17-stage2-simulator-gt-source-ingest/source_summary.md`
- `WORKSPACE_ROOT/stage3/17-stage2-simulator-gt-source-ingest/DONE.json`
- `WORKSPACE_ROOT/stage3/17-stage2-simulator-gt-source-ingest/USED_INPUTS.json`

本节点的规范化真相源应写入 `stage3.db` 的 `stage2_simulator_sources` 与 `stage2_simulator_gt_sources` 表；导出 `jsonl` 仅作为兼容性副本。

## Must not read

- `WORKSPACE_ROOT/stage3/15-stage2-real-image-source-ingest/**`
- `WORKSPACE_ROOT/stage3/16-stage2-existing-benchmark-source-ingest/**`

## Non-negotiable Constraint

- 若 Stage2 node 17 没有提供足够的已落盘 simulator 观测或 GT，本节点必须阻塞并报告缺口；不得在 Stage3 中重新调用仿真器补采原始数据。

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
