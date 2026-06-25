---
name: benchclaw-stage1-benchmark-draft-generation
description: Use for the specific BenchClaw node skill `stage1-benchmark-draft-generation` only when its parent stage explicitly dispatches to it.
---

## Opencode 子 agent 触发契约

本文件是 BenchClaw child skill module。父级 stage、node 或 pipeline 调度到本文件时，必须通过 opencode 命令 `/benchclaw-subskill` 启动隔离子 agent；该命令在 `BENCHCLAW_ROOT/opencode.json` 中配置为 `subtask: true`，并绑定 `mode: "subagent"` 的 `child-skill-module-runner`。禁止父级 manager 直接在自己的对话上下文中内联执行本文件步骤。

调用 `/benchclaw-subskill` 时必须传入：目标 `SKILL.md` 绝对路径、注册 skill 名、冻结的 `PROJECT_ROOT` / `BENCHCLAW_ROOT` / `WORKSPACE_PARENT` / `WORKSPACE_ROOT`、当前 node 或 work_unit id、已满足的输入 artifact 路径、期望输出 artifact 路径、父级 DAG 依赖与完成判据。子 agent 只返回 `status`、artifact 路径、证据摘要和 blockers，不回灌长日志或完整中间内容。

如果当前执行上下文不是 `/benchclaw-subskill` 产生的 `child-skill-module-runner` 子 agent，本文件不得继续执行；应立即返回 `BLOCKED`，说明必须由父级使用 `/benchclaw-subskill` 重新派发。

# Node Skill — benchmark 草稿生成

## 输入

本节点生成 benchmark 草稿前，必须能读取从用户原始 idea 到模板/指标初稿的完整 Stage1 上游上下文：

- `data_01_user_idea`
- `data_02_rewritten_queries`
- `data_03_intent_expansion_doc`
- `data_04_retrieved_literature`
- `data_05_source_capability_descriptions`，其数据源能力必须只来自 `BENCHCLAW_ROOT/benchmarkDatasetCards`、`BENCHCLAW_ROOT/realDataCards`、`BENCHCLAW_ROOT/simulatorCards`
- 根输入 `data_06_semisupervised_capability_signals`，其标注工具能力必须只来自 `BENCHCLAW_ROOT/annotation-tool`
- `data_07_literature_review`
- 已离线物化的 `data_08_preprocessed_capability_pool`
- `data_09_benchmark_data`
- `data_10_capability_dimension_doc`
- `data_11_template_metric_initial_draft`

其中 `data_10_capability_dimension_doc` 与 `data_11_template_metric_initial_draft` 是 ready-set 父节点必需输入；`data_01` 到 `data_09` 是生成草稿时必须读取的只读上下文。若任一上游数据缺失、路径不可解析或内容不可读，必须在 `USED_INPUTS.json` 中记录；若缺失会影响 benchmark 范围、数据源计划、任务族或指标族判断，必须写 `BLOCKED.json` 与 `BLOCKED.md` 并停止本节点。

## 处理

1. 先解析并读取 `data_01` 到 `data_11` 的实际 artifact 路径，保持只读，不得修改任何上游 artifact。
2. 对每组已读取数据提炼其对 benchmark 草稿的约束：用户目标、改写 query、意图边界、真实下载并阅读的文献证据、三类数据源能力描述、annotation-tool 标注工具能力信号、文献综述、预处理能力池、benchmark 数据、能力维度、模板/指标初稿。
3. 生成 benchmark 范围、数据源计划、任务族、指标族、风险边界和验收标准；每个关键设计选择必须能追溯到 `data_01` 到 `data_11` 中至少一个上游依据。
4. 数据源计划只能引用 `benchmarkDatasetCards`、`realDataCards`、`simulatorCards` 中的卡片；标注/伪标注计划只能引用 `annotation-tool` 中的工具卡。
5. 明确 Stage2、Stage3、Stage4、Stage5 的依赖和阻塞条件。
6. 产出可转化为执行计划的 benchmark 草稿。

## 输出

- `artifacts/data_12_benchmark_draft/benchmark_draft.md`
- 节点执行记录文件
