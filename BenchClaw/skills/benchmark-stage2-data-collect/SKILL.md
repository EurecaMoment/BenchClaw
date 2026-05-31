# Benchmark Stage2 Data Collect Skill — 原始数据采集

## 角色

根据 Stage1 执行计划，分别采集并分析真实图片、已有 benchmark 和仿真器数据，并把后续阶段需要消费的媒体、元数据、标注需求与 GT 物化到 workspace。

## 关键规则

- 只有本文件 DAG 表中的节点是本阶段节点；编号数据只进入 `artifacts/`，不得进入 `nodes/`。
- 启动本 stage 时，必须接收并复述冻结的 `PROJECT_ROOT`、`BENCHCLAW_ROOT`、`WORKSPACE_PARENT`、`WORKSPACE_ROOT` 实际值，并与 `WORKSPACE_ROOT/path_resolution.json` 对齐。
- 本 stage 只能写入 `WORKSPACE_ROOT/stage2/`。
- 每个节点完成后必须写：`nodes/<node-id>/USED_INPUTS.json`、`nodes/<node-id>/DONE.json`、`nodes/<node-id>/NODE_REPORT.md`。
- 每个编号数据必须写入：`artifacts/<data-id>/`。
- 缺少必需输入、真实数据、标注结果、GT 或模型输出时，必须写 `BLOCKED.json` 与 `BLOCKED.md`，并停止本 stage。

## 输入

- `data_13_execution_plan`

## DAG 节点

| Node ID | 椭圆节点名称 | Parents | 输出数据 |
|---|---|---|---|
| `stage2-plan-generation` | 本阶段执行计划生成 | 无 | `stage2_execution_plan` |
| `real-image-collection-analysis` | 真实图片采集与分析 | `stage2-plan-generation` | `data_14_real_image_collection_bundle` |
| `existing-benchmark-collection-analysis` | 已有 benchmark 采集与分析 | `stage2-plan-generation` | `data_15_existing_benchmark_collection_bundle` |
| `simulator-collection-analysis` | 仿真器采集与分析 | `stage2-plan-generation` | `data_16_simulator_collection_bundle` |

## Ready-set 调度

1. 从 `dag.json` 读取节点依赖。
2. 每轮选择所有 parents 已完成且未执行的 ready 节点。
3. 对 ready 节点调用 `skills/<node-id>/SKILL.md`。
4. 并行分支可以并行处理，但共享输入必须只读，共享输出必须写入各自 artifact 目录。
5. 本 stage 只在所有 terminal artifacts 完成且质量门通过后写 `_STAGE_DONE.json` 与 `_stage_report.md`。

## 终端数据

- `data_14_real_image_collection_bundle`
- `data_15_existing_benchmark_collection_bundle`
- `data_16_simulator_collection_bundle`

## 标准目录

```text
WORKSPACE_ROOT/stage2/
  nodes/
  artifacts/
  _STAGE_DONE.json
  _stage_report.md
```
