---
name: benchclaw-stage4-build
description: Use for the BenchClaw skill `stage4-build` when the workflow is explicitly entering this stage or manager.
---

# Benchmark Stage4 Build Skill — 评测集合成与指标构建

## 角色

读取 Stage1 的模板/指标初稿与执行计划，以及 Stage3 的三类已标注数据，生成模板、指标、代码，小批量合成灰度验证，并最终合成全量 benchmark 数据集。

## 关键规则

- 只有本文件 DAG 表中的节点是本阶段节点；编号数据只进入 `artifacts/`，不得进入 `nodes/`。
- 启动本 stage 时，必须接收并复述冻结的 `PROJECT_ROOT`、`BENCHCLAW_ROOT`、`WORKSPACE_PARENT`、`WORKSPACE_ROOT` 实际值，并与 `WORKSPACE_ROOT/path_resolution.json` 对齐。
- 本 stage 只能写入 `WORKSPACE_ROOT/stage4/`。
- 每个节点完成后必须写：`nodes/<node-id>/USED_INPUTS.json`、`nodes/<node-id>/DONE.json`、`nodes/<node-id>/NODE_REPORT.md`。
- 继承总入口和 pipeline 的长任务 `tmux` 执行协议：任何下载、检索、外部工具调用、批处理、模型推理、训练、仿真、清洗、标注或全量评测等可能长时间运行的命令，必须在 `tmux` 会话中执行、写入 `nodes/<node-id>/run_logs/` 并定期监控；未使用 `tmux` 必须在 `NODE_REPORT.md` 说明短任务依据和实际耗时。
- 灰度批量合成、无效题筛选、小批量模型推理/评分、CDM/IRT 分析、全量 benchmark 合成、媒体/GT/评分配置批量落盘等 Stage4 关键命令必须后台 `tmux` 执行，并且每 15 秒检查一次 tmux 状态和日志，直到会话结束；缺少 15 秒监控记录、最终日志、退出码或真实产物时不得写 `DONE.json`。
- 每个编号数据必须写入：`artifacts/<data-id>/`。
- Stage4 的产物目录名必须使用当前契约：全量数据集必须包含 `dataset.jsonl`、`media/`、`ground_truth/`、`metrics/`、`cards/benchmark_card.md`、`checksums.json`；不得只写旧命名 `sample_images/`、`gt_bundle/` 或空目录。
- 在写 `stage4/_STAGE_DONE.json` 或向 pipeline 返回 `PASS` 前，必须运行可执行质量门：

```bash
python3 "$BENCHCLAW_ROOT/skills/validate_stage_gate.py" \
  --workspace-root "$WORKSPACE_ROOT" \
  --stage stage4 \
  --report "$WORKSPACE_ROOT/stage4/stage4_gate_report.json"
```

只有该命令退出码为 0 且报告 `status: PASS` 时，才允许写 `_STAGE_DONE.json`；报告路径和摘要必须写入 `_stage_report.md` 与 `_STAGE_DONE.json.quality_gate.validator`。若 validator 失败，必须写 `BLOCKED.json` 与 `BLOCKED.md`，不得继续 Stage5。
- 缺少必需输入、真实数据、标注结果、GT 或模型输出时，必须写 `BLOCKED.json` 与 `BLOCKED.md`，并停止本 stage。

## Registered Node Skill Names

本 stage 调度 ready 节点时，必须使用下面这些显式 skill 名：

- `stage4-plan-generation` -> `benchclaw-stage4-plan-generation`
- `template-metric-code-generation` -> `benchclaw-stage4-template-metric-code-generation`
- `grey-batch-validation` -> `benchclaw-stage4-grey-batch-validation`
- `full-synthesis` -> `benchclaw-stage4-full-synthesis`

## Node Context Return Protocol

每个节点只向 stage 返回：节点状态、artifact 根路径、质量门结果、关键计数、阻塞原因和简短摘要。不要把模板全文、代码全文、灰度日志全文或整段 dataset.jsonl 持续回灌。

## 输入

- `data_11_template_metric_initial_draft`
- `data_13_execution_plan`
- `data_17_annotated_real_image_bundle`
- `data_18_annotated_existing_benchmark_bundle`
- `data_19_annotated_simulator_bundle`

## DAG 节点

| Node ID | 椭圆节点名称 | Parents | 输出数据 |
|---|---|---|---|
| `stage4-plan-generation` | 本阶段执行计划生成 | 无 | `stage4_execution_plan` |
| `template-metric-code-generation` | 模板/指标/代码生成 | `stage4-plan-generation` | `data_20_template_metric_code_bundle` |
| `grey-batch-validation` | 小批量合成灰度验证 | `template-metric-code-generation` | `data_21_grey_validation_report` |
| `full-synthesis` | 全量合成 | `grey-batch-validation` | `data_22_full_benchmark_dataset` |

## Ready-set 调度

1. 从 `dag.json` 读取节点依赖。
2. 每轮选择所有 parents 已完成且未执行的 ready 节点。
3. 对 ready 节点调用对应的已注册 skill 名：`stage4-plan-generation -> benchclaw-stage4-plan-generation`，`template-metric-code-generation -> benchclaw-stage4-template-metric-code-generation`，`grey-batch-validation -> benchclaw-stage4-grey-batch-validation`，`full-synthesis -> benchclaw-stage4-full-synthesis`。
4. 并行分支可以并行处理，但共享输入必须只读，共享输出必须写入各自 artifact 目录。
5. 本 stage 只在所有 terminal artifacts 完成且 `validate_stage_gate.py --stage stage4` 通过后写 `_STAGE_DONE.json` 与 `_stage_report.md`。

## 终端数据

- `data_22_full_benchmark_dataset`

## 标准目录

```text
WORKSPACE_ROOT/stage4/
  nodes/<node-id>/
    run_logs/
  artifacts/
  _STAGE_DONE.json
  _stage_report.md
```
