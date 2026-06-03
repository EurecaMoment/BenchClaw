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
- 缺少必需输入、真实数据、标注结果、GT 或模型输出时，必须写 `BLOCKED.json` 与 `BLOCKED.md`，并停止本 stage。

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
3. 对 ready 节点调用 `skills/<node-id>/SKILL.md`。
4. 并行分支可以并行处理，但共享输入必须只读，共享输出必须写入各自 artifact 目录。
5. 本 stage 只在所有 terminal artifacts 完成且质量门通过后写 `_STAGE_DONE.json` 与 `_stage_report.md`。

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
