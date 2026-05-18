# Node 20 — simulator-clean-gt-pack

## Role

Produce cleaned simulator records plus privileged GT; no small-model annotation may override simulator GT.

## Parents

```text
26
```

## May read

- `WORKSPACE_ROOT/stage3/26-simulator-data-juicer-cleaning/**`
- `schemas/simulator_gt_record.schema.json`

## Must write

- `WORKSPACE_ROOT/stage3/20-simulator-clean-gt-pack/cleaned_sim_records.jsonl`
- `WORKSPACE_ROOT/stage3/20-simulator-clean-gt-pack/simulator_gt_manifest.jsonl`
- `WORKSPACE_ROOT/stage3/20-simulator-clean-gt-pack/provenance/`
- `WORKSPACE_ROOT/stage3/20-simulator-clean-gt-pack/consistency_report.md`
- `WORKSPACE_ROOT/stage3/20-simulator-clean-gt-pack/quality_report.md`
- `WORKSPACE_ROOT/stage3/20-simulator-clean-gt-pack/DONE.json`
- `WORKSPACE_ROOT/stage3/20-simulator-clean-gt-pack/USED_INPUTS.json`

## Must not read

- `WORKSPACE_ROOT/stage3/18-real-image-semi-supervised-gt/**`
- `WORKSPACE_ROOT/stage3/19-benchmark-image-semi-supervised-gt/**`
- `WORKSPACE_ROOT/stage3/27-semi-supervised-tool-registry/**`

## 仿真器 GT 规则

- `simulator_privileged_gt` 是本节点最高优先级 GT；
- 小模型输出不得覆盖 simulator pose、object state、depth、segmentation、collision、visibility、affordance 等 privileged GT；
- 允许从 privileged GT 派生几何字段，但必须标为 `derived_geometry` 并写明公式/代码路径；
- 若 sensor 渲染与 privileged GT 冲突，写入 `consistency_report.md`，不得静默修正。

## Completion

完成后必须写：

```json
{
  "node_id": "20",
  "status": "DONE",
  "output_dir": "WORKSPACE_ROOT/stage3/20-simulator-clean-gt-pack",
  "timestamp_utc": "<ISO-8601>"
}
```

并运行：

```bash
python scripts/check_used_inputs.py --node 20
python scripts/ready_set_runner.py --workspace WORKSPACE_ROOT
```
