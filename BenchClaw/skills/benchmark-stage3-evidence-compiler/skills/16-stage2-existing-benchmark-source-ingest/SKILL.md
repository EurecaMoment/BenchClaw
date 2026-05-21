# Node 16 — stage2-existing-benchmark-source-ingest

全局路径约束：`BENCHCLAW_ROOT` 仅作只读输入；`WORKSPACE_ROOT` 是本次流程唯一总工作目录，所有写操作和流程产物只能落在其下。

## Role

Ingest Stage2 node-16 existing benchmark acquisition output as a read-only Stage3 source.

This node only reads and re-indexes existing-benchmark data that has already been collected and materialized by Stage2 node 16. It must not re-download, re-fetch, replace, extend, or otherwise obtain new benchmark samples from dataset hosts or external caches.

## Parents

```text
(none)
```

## May read

- `WORKSPACE_ROOT/stage2/16-existing-benchmark-acquisition/**`
- `WORKSPACE_ROOT/config/stage3_input_paths.json`

## Must write

- `WORKSPACE_ROOT/stage3/stage3.db`
- `WORKSPACE_ROOT/stage3/16-stage2-existing-benchmark-source-ingest/source_manifest.sqlite_export.jsonl`
- `WORKSPACE_ROOT/stage3/16-stage2-existing-benchmark-source-ingest/source_summary.md`
- `WORKSPACE_ROOT/stage3/16-stage2-existing-benchmark-source-ingest/DONE.json`
- `WORKSPACE_ROOT/stage3/16-stage2-existing-benchmark-source-ingest/USED_INPUTS.json`

本节点的规范化真相源应写入 `stage3.db` 的 `stage2_benchmark_sources` 表；`source_manifest.sqlite_export.jsonl` 仅作为兼容性导出。

## Must not read

- `WORKSPACE_ROOT/stage3/15-stage2-real-image-source-ingest/**`
- `WORKSPACE_ROOT/stage3/17-stage2-simulator-gt-source-ingest/**`

## Non-negotiable Constraint

- 若 Stage2 node 16 没有提供足够的已落盘 benchmark 图文或官方标签，本节点必须阻塞并报告缺口；不得自行回到外部 benchmark 数据源重新下载或重新获取样本。

## Completion

完成后必须写：

```json
{
  "node_id": "16",
  "status": "DONE",
  "output_dir": "WORKSPACE_ROOT/stage3/16-stage2-existing-benchmark-source-ingest",
  "timestamp_utc": "<ISO-8601>"
}
```

并运行：

```bash
python scripts/check_used_inputs.py --node 16
python scripts/ready_set_runner.py --workspace WORKSPACE_ROOT
```
