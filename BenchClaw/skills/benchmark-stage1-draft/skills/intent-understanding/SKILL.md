---
name: benchclaw-stage1-intent-understanding
description: Use for the specific BenchClaw node skill `stage1-intent-understanding` only when its parent stage explicitly dispatches to it.
---

## Opencode 子 agent 触发契约

本文件是 BenchClaw child skill module。父级 stage、node 或 pipeline 调度到本文件时，必须通过 opencode 命令 `/benchclaw-subskill` 启动隔离子 agent；该命令在 `BENCHCLAW_ROOT/opencode.json` 中配置为 `subtask: true`，并绑定 `mode: "subagent"` 的 `child-skill-module-runner`。禁止父级 manager 直接在自己的对话上下文中内联执行本文件步骤。

调用 `/benchclaw-subskill` 时必须传入：目标 `SKILL.md` 绝对路径、注册 skill 名、冻结的 `PROJECT_ROOT` / `BENCHCLAW_ROOT` / `WORKSPACE_PARENT` / `WORKSPACE_ROOT`、当前 node 或 work_unit id、已满足的输入 artifact 路径、期望输出 artifact 路径、父级 DAG 依赖与完成判据。子 agent 只返回 `status`、artifact 路径、证据摘要和 blockers，不回灌长日志或完整中间内容。

如果当前执行上下文不是 `/benchclaw-subskill` 产生的 `child-skill-module-runner` 子 agent，本文件不得继续执行；应立即返回 `BLOCKED`，说明必须由父级使用 `/benchclaw-subskill` 重新派发。

# Node Skill — 意图理解

## 输入

- `data_01_user_idea`

## 处理

1. 冻结用户原始 idea，不改写原文。
2. 抽取评测目标、对象域、能力边界、任务形态、数据约束、评分约束。
3. 生成检索 query 和意图扩写文档。
4. 本节点不得生成或修改 `data_05_source_capability_descriptions`、`data_06_semisupervised_capability_signals`、`data_09_benchmark_data`；这些是根输入数据。

## 输出

- `artifacts/data_02_rewritten_queries/queries.jsonl`
- `artifacts/data_03_intent_expansion_doc/intent.md`
- `nodes/intent-understanding/USED_INPUTS.json`
- `nodes/intent-understanding/DONE.json`
- `nodes/intent-understanding/NODE_REPORT.md`
