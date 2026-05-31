# Benchmark Stage1 Draft Skill — 草稿与执行计划

## 角色

从用户 benchmark idea 出发，完成意图理解、文献调研、模型 scope 预处理分析、能力维度划分、模板/指标初稿、benchmark 草稿和执行计划。

## 关键规则

- 只有本文件 DAG 表中的节点是本阶段节点；编号数据只进入 `artifacts/`，不得进入 `nodes/`。
- 启动本 stage 时，必须接收并复述冻结的 `PROJECT_ROOT`、`BENCHCLAW_ROOT`、`WORKSPACE_PARENT`、`WORKSPACE_ROOT` 实际值，并与 `WORKSPACE_ROOT/path_resolution.json` 对齐。
- 本 stage 只能写入 `WORKSPACE_ROOT/stage1/`。
- 每个节点完成后必须写：`nodes/<node-id>/USED_INPUTS.json`、`nodes/<node-id>/DONE.json`、`nodes/<node-id>/NODE_REPORT.md`。
- 每个编号数据必须写入：`artifacts/<data-id>/`。
- 缺少必需输入、真实数据、标注结果、GT 或模型输出时，必须写 `BLOCKED.json` 与 `BLOCKED.md`，并停止本 stage。

## 输入

- `data_01_user_idea`
- `external capability cards`
- `external dataset cards`
- `model scope preprocessing resources`

## DAG 节点

| Node ID | 椭圆节点名称 | Parents | 输出数据 |
|---|---|---|---|
| `intent-understanding` | 意图理解 | 无 | `data_02_rewritten_queries`, `data_03_intent_expansion_doc`, `data_05_source_capability_descriptions` |
| `literature-search` | 文献搜索 | `intent-understanding` | `data_04_retrieved_literature` |
| `literature-review` | 文献调研 | `literature-search`, `intent-understanding` | `data_07_literature_review` |
| `scope-preprocess-analysis` | 模型 scope 预处理分析 | 无 | `data_06_semisupervised_capability_signals`, `data_08_preprocessed_capability_pool` |
| `capability-dimension-planning` | 能力维度划分 | `intent-understanding`, `literature-review`, `scope-preprocess-analysis` | `data_10_capability_dimension_doc` |
| `template-metric-draft-generation` | 模板/指标初稿生成 | `capability-dimension-planning` | `data_11_template_metric_initial_draft` |
| `benchmark-draft-generation` | benchmark 草稿生成 | `template-metric-draft-generation`, `capability-dimension-planning` | `data_12_benchmark_draft` |
| `execution-plan-generation` | 执行计划生成 | `benchmark-draft-generation` | `data_13_execution_plan` |

## Ready-set 调度

1. 从 `dag.json` 读取节点依赖。
2. 每轮选择所有 parents 已完成且未执行的 ready 节点。
3. 对 ready 节点调用 `skills/<node-id>/SKILL.md`。
4. 并行分支可以并行处理，但共享输入必须只读，共享输出必须写入各自 artifact 目录。
5. 本 stage 只在所有 terminal artifacts 完成且质量门通过后写 `_STAGE_DONE.json` 与 `_stage_report.md`。

## 终端数据

- `data_13_execution_plan`

## 标准目录

```text
WORKSPACE_ROOT/stage1/
  nodes/
  artifacts/
  _STAGE_DONE.json
  _stage_report.md
```
