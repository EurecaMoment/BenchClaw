# Node 20 — simulator-clean-gt-pack

全局路径约束：`BENCHCLAW_ROOT` 仅作只读输入；`WORKSPACE_ROOT` 是本次流程唯一总工作目录，所有写操作和流程产物只能落在其下。

## Role

Produce cleaned simulator records plus privileged GT; no small-model annotation may override simulator GT.

For simulator image-based data, this node must materialize the final Stage3 simulator subtree under `WORKSPACE_ROOT/stage3/simulator/` and preserve three image classes plus GT for every retained sample:

```text
WORKSPACE_ROOT/stage3/simulator/<simulator_id>/<scene_or_map_id>/
  original/
  semantic_entity_segmentation/
  depth/
  gt/
```

Here:

1. `original/` means original simulator visual observations such as RGB frames;
2. `semantic_entity_segmentation/` means simulator-native semantic/instance render outputs or equivalent semantic entity segmentation images aligned with privileged GT;
3. `depth/` means simulator depth observations or equivalent depth renders;
4. `gt/` means privileged GT and derived geometry records that remain after cleaning.

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
- `WORKSPACE_ROOT/stage3/simulator/`
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
- 对被保留的 simulator 样本，`original/`、`semantic_entity_segmentation/`、`depth/` 三类图像必须在 `WORKSPACE_ROOT/stage3/simulator/<simulator_id>/<scene_or_map_id>/` 下全量保存；不得只保留抽样帧、汇总视频、缩略图、统计表或“可重新渲染”的说明。
- `cleaned_sim_records.jsonl` 与 `simulator_gt_manifest.jsonl` 中的 `artifact_paths` 或等价字段应能解析到上述 `original/`、`semantic_entity_segmentation/`、`depth/`、`gt/` 子目录中的真实文件。

## Blocking Conditions

- 若 `WORKSPACE_ROOT/stage3/simulator/` 下未按 `simulator/<simulator_id>/<scene_or_map_id>/` 层级对保留样本全量落盘三类图像与 GT，则不得写 `DONE.json`。
- 若图像型仿真器观测只剩抽样帧、摘要、视频导出或示例图片，而非逐样本完整文件集，则不得写 `DONE.json`。

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
