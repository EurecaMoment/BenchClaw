---
name: benchclaw-stage1-template-metric-draft-generation
description: Use for the specific BenchClaw node skill `stage1-template-metric-draft-generation` only when its parent stage explicitly dispatches to it.
---

## Opencode 子 agent 触发契约

本文件是 BenchClaw child skill module。父级 stage、node 或 pipeline 调度到本文件时，必须通过 opencode 命令 `/benchclaw-subskill` 启动隔离子 agent；该命令在 `BENCHCLAW_ROOT/opencode.json` 中配置为 `subtask: true`，并绑定 `mode: "subagent"` 的 `child-skill-module-runner`。禁止父级 manager 直接在自己的对话上下文中内联执行本文件步骤。

调用 `/benchclaw-subskill` 时必须传入：目标 `SKILL.md` 绝对路径、注册 skill 名、冻结的 `PROJECT_ROOT` / `BENCHCLAW_ROOT` / `WORKSPACE_PARENT` / `WORKSPACE_ROOT`、当前 node 或 work_unit id、已满足的输入 artifact 路径、期望输出 artifact 路径、父级 DAG 依赖与完成判据。子 agent 只返回 `status`、artifact 路径、证据摘要和 blockers，不回灌长日志或完整中间内容。

如果当前执行上下文不是 `/benchclaw-subskill` 产生的 `child-skill-module-runner` 子 agent，本文件不得继续执行；应立即返回 `BLOCKED`，说明必须由父级使用 `/benchclaw-subskill` 重新派发。

# Node Skill — 模板/指标初稿生成

## 输入

- 根输入 `data_09_benchmark_data`
- `data_10_capability_dimension_doc`

## 处理

1. 为每个能力维度生成候选题目模板、输入字段、答案字段和评分指标。
2. 每个模板必须声明证据需求、可自动评分条件、失败条件和不适用场景。
3. 指标初稿必须区分 exact match、set matching、programmatic check、ranking/statistical analysis 等类型。
4. 本节点不得生成或修改 `data_09_benchmark_data`；它只能消费已物化的 benchmark 数据。

## 输出

- `artifacts/data_11_template_metric_initial_draft/templates.yaml`
- `artifacts/data_11_template_metric_initial_draft/metrics.yaml`
- `artifacts/data_11_template_metric_initial_draft/template_metric_traceability.csv`
- 节点执行记录文件
