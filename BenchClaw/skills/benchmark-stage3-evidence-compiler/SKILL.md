# Benchmark Stage3 Evidence Compiler Skill — 证据编译、清洗与 GT 整理

## 角色

读取 Stage2 已物化数据，分别完成真实图片、已有 benchmark、仿真器数据的清洗、标注与 GT 整理。

## 关键规则

- 只有本文件 DAG 表中的节点是本阶段节点；编号数据只进入 `artifacts/`，不得进入 `nodes/`。
- 启动本 stage 时，必须接收并复述冻结的 `PROJECT_ROOT`、`BENCHCLAW_ROOT`、`WORKSPACE_PARENT`、`WORKSPACE_ROOT` 实际值，并与 `WORKSPACE_ROOT/path_resolution.json` 对齐。
- 本 stage 只能写入 `WORKSPACE_ROOT/stage3/`。
- 每个节点完成后必须写：`nodes/<node-id>/USED_INPUTS.json`、`nodes/<node-id>/DONE.json`、`nodes/<node-id>/NODE_REPORT.md`。
- 每个编号数据必须写入：`artifacts/<data-id>/`。
- 缺少必需输入、真实数据、标注结果、GT 或模型输出时，必须写 `BLOCKED.json` 与 `BLOCKED.md`，并停止本 stage。

## 输入

- `data_13_execution_plan`
- `data_14_real_image_collection_bundle`
- `data_15_existing_benchmark_collection_bundle`
- `data_16_simulator_collection_bundle`

## DAG 节点

| Node ID | 椭圆节点名称 | Parents | 输出数据 |
|---|---|---|---|
| `stage3-plan-generation` | 本阶段执行计划生成 | 无 | `stage3_execution_plan` |
| `real-image-cleaning` | 真实图片清洗 | `stage3-plan-generation` | `real_image_clean_bundle` |
| `existing-benchmark-cleaning` | 已有 benchmark 数据清洗 | `stage3-plan-generation` | `existing_benchmark_clean_bundle` |
| `simulator-data-cleaning` | 仿真器数据清洗 | `stage3-plan-generation` | `simulator_clean_bundle` |
| `real-image-annotation` | 真实图片标注 | `real-image-cleaning` | `data_17_annotated_real_image_bundle` |
| `existing-benchmark-annotation` | 已有 benchmark 标注 | `existing-benchmark-cleaning` | `data_18_annotated_existing_benchmark_bundle` |
| `simulator-data-organization` | 仿真器数据整理 | `simulator-data-cleaning` | `data_19_annotated_simulator_bundle` |

## Ready-set 调度

1. 从 `dag.json` 读取节点依赖。
2. 每轮选择所有 parents 已完成且未执行的 ready 节点。
3. 对 ready 节点调用 `skills/<node-id>/SKILL.md`。
4. 并行分支可以并行处理，但共享输入必须只读，共享输出必须写入各自 artifact 目录。
5. 本 stage 只在所有 terminal artifacts 完成且质量门通过后写 `_STAGE_DONE.json` 与 `_stage_report.md`。

## 终端数据

- `data_17_annotated_real_image_bundle`
- `data_18_annotated_existing_benchmark_bundle`
- `data_19_annotated_simulator_bundle`

## 标准目录

```text
WORKSPACE_ROOT/stage3/
  nodes/
  artifacts/
  _STAGE_DONE.json
  _stage_report.md
```
