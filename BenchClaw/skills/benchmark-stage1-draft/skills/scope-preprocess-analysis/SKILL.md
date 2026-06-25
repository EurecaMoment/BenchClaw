---
name: benchclaw-stage1-scope-preprocess-analysis
description: Use for the specific BenchClaw node skill `stage1-scope-preprocess-analysis` only when its parent stage explicitly dispatches to it.
---

## Opencode 子 agent 触发契约

本文件是 BenchClaw child skill module。父级 stage、node 或 pipeline 调度到本文件时，必须通过 opencode 命令 `/benchclaw-subskill` 启动隔离子 agent；该命令在 `BENCHCLAW_ROOT/opencode.json` 中配置为 `subtask: true`，并绑定 `mode: "subagent"` 的 `child-skill-module-runner`。禁止父级 manager 直接在自己的对话上下文中内联执行本文件步骤。

调用 `/benchclaw-subskill` 时必须传入：目标 `SKILL.md` 绝对路径、注册 skill 名、冻结的 `PROJECT_ROOT` / `BENCHCLAW_ROOT` / `WORKSPACE_PARENT` / `WORKSPACE_ROOT`、当前 node 或 work_unit id、已满足的输入 artifact 路径、期望输出 artifact 路径、父级 DAG 依赖与完成判据。子 agent 只返回 `status`、artifact 路径、证据摘要和 blockers，不回灌长日志或完整中间内容。

如果当前执行上下文不是 `/benchclaw-subskill` 产生的 `child-skill-module-runner` 子 agent，本文件不得继续执行；应立即返回 `BLOCKED`，说明必须由父级使用 `/benchclaw-subskill` 重新派发。

# Node Skill — 模型 scope 预处理分析

## 运行策略

- 本 skill 是 Stage1 DAG 中的 offline 节点，只用于离线预处理，不进入正常在线调度。
- 本节点消费 `data_09_benchmark_data`，输出 `data_08_preprocessed_capability_pool`。
- 正常 `benchmark-pipeline` 不得自动调度本 skill；启动在线 Stage1 前必须已经有它的离线产物。
- 只有用户明确要求离线 scope 预处理时才运行；其产物是 Stage1 正常 pipeline 的必需输入。

## 输入

- `data_09_benchmark_data`
- 可选的外部模型 scope 分析结果或聚类结果

## 处理

1. 读取 `data_09_benchmark_data`，提取可用于能力覆盖分析的任务、数据形态、标签/GT 类型、输入输出模态和约束。
2. 可合并已存在的模型 scope 分析或聚类结果，但不得重新解释为 GT。
3. 将候选能力信号归一化为可被能力维度划分消费的候选能力池。
4. 记录每个能力信号的来源、证据、置信等级和限制。
5. 本节点不得生成或修改 `data_06_semisupervised_capability_signals`；标注工具能力是根输入数据，只能来自 `BENCHCLAW_ROOT/annotation-tool`。

## 输出

- `artifacts/data_08_preprocessed_capability_pool/capability_pool.jsonl`
- 节点执行记录文件
