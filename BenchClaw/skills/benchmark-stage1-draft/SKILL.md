# Benchmark Stage1 Draft Skill — 草稿与执行计划

## 角色

从用户 benchmark idea 出发，完成意图理解、文献调研、能力维度划分、模板/指标初稿、benchmark 草稿和执行计划。

## 关键规则

- 只有本文件 DAG 表中的节点是本阶段节点；用户和外部资源不是节点；编号数据只进入 `artifacts/`，不得进入 `nodes/`。
- `skills/scope-preprocess-analysis/SKILL.md` 是图中的离线 DAG 节点，负责从 `data_09_benchmark_data` 物化 `data_08_preprocessed_capability_pool`。正常在线 pipeline 不得自动运行它，除非用户明确要求；否则必须校验其已离线物化的输出。
- 启动本 stage 时，必须接收并复述冻结的 `PROJECT_ROOT`、`BENCHCLAW_ROOT`、`WORKSPACE_PARENT`、`WORKSPACE_ROOT` 实际值，并与 `WORKSPACE_ROOT/path_resolution.json` 对齐。
- 本 stage 只能写入 `WORKSPACE_ROOT/stage1/`。
- 每个节点完成后必须写：`nodes/<node-id>/USED_INPUTS.json`、`nodes/<node-id>/DONE.json`、`nodes/<node-id>/NODE_REPORT.md`。
- 继承总入口和 pipeline 的长任务 `tmux` 执行协议：任何下载、检索、外部工具调用、批处理、模型推理、训练、仿真、清洗、标注或全量评测等可能长时间运行的命令，必须在 `tmux` 会话中执行、写入 `nodes/<node-id>/run_logs/` 并定期监控；未使用 `tmux` 必须在 `NODE_REPORT.md` 说明短任务依据和实际耗时。
- 每个编号数据必须写入：`artifacts/<data-id>/`。
- 缺少必需输入、真实数据、标注结果、GT 或模型输出时，必须写 `BLOCKED.json` 与 `BLOCKED.md`，并停止本 stage。
- `data_05_source_capability_descriptions` 的数据源能力只能来自 `BENCHCLAW_ROOT/benchmarkDatasetCards/`、`BENCHCLAW_ROOT/realDataCards/`、`BENCHCLAW_ROOT/simulatorCards/` 三类数据源卡目录。
- `data_06_semisupervised_capability_signals` 的标注工具能力只能来自 `BENCHCLAW_ROOT/annotation-tool/` 标注工具卡目录。

## 输入

根输入数据不算节点，但必须先物化到 `WORKSPACE_ROOT/stage1/artifacts/`：

- `data_01_user_idea`：用户原始 benchmark idea
- `data_05_source_capability_descriptions`：只能来自 `BENCHCLAW_ROOT/benchmarkDatasetCards`、`BENCHCLAW_ROOT/realDataCards`、`BENCHCLAW_ROOT/simulatorCards`
- `data_06_semisupervised_capability_signals`：只能来自 `BENCHCLAW_ROOT/annotation-tool`
- `data_09_benchmark_data`：外部 benchmark 数据或用户授权的数据索引

## DAG 节点

| Node ID | 椭圆节点名称 | Mode | Parents | 输入数据 | 输出数据 |
|---|---|---|---|---|---|
| `intent-understanding` | 意图理解 | online | 无 | `data_01` | `data_02`, `data_03` |
| `scope-preprocess-analysis` | 模型 scope 预处理分析 | offline | 无 | `data_09` | `data_08` |
| `literature-search` | 文献搜索 | online | `intent-understanding` | `data_02`, `data_03` | `data_04` |
| `literature-review` | 文献调研 | online | `literature-search`, `intent-understanding` | `data_03`, `data_04` | `data_07` |
| `capability-dimension-planning` | 能力维度划分 | online | `intent-understanding`, `literature-review`, `scope-preprocess-analysis` | `data_03`, `data_05`, `data_06`, `data_07`, `data_08` | `data_10` |
| `template-metric-draft-generation` | 模板/指标初稿生成 | online | `capability-dimension-planning` | `data_09`, `data_10` | `data_11` |
| `benchmark-draft-generation` | benchmark 草稿生成 | online | `template-metric-draft-generation`, `capability-dimension-planning` | `data_01` 到 `data_11` | `data_12` |
| `execution-plan-generation` | 执行计划生成 | online | `benchmark-draft-generation` | `data_12` | `data_13` |

## Ready-set 调度

1. 从 `dag.json` 读取节点依赖。
2. 每轮选择所有 parents 已完成且未执行的 ready 节点。
3. `scope-preprocess-analysis` 是 offline 节点：只有用户明确要求离线预处理时才运行；正常在线调度只校验其 `data_08` 输出已存在。
4. 并行分支可以并行处理，但共享输入必须只读，共享输出必须写入各自 artifact 目录。
5. 本 stage 只在所有 terminal artifacts 完成且质量门通过后写 `_STAGE_DONE.json` 与 `_stage_report.md`。

## 终端数据

- `data_13_execution_plan`

## 标准目录

```text
WORKSPACE_ROOT/stage1/
  nodes/<node-id>/
    run_logs/
  artifacts/
  _STAGE_DONE.json
  _stage_report.md
```
