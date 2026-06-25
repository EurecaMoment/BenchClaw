---
name: benchclaw-stage1-execution-plan-generation
description: Use for the specific BenchClaw node skill `stage1-execution-plan-generation` only when its parent stage explicitly dispatches to it.
---

## Opencode 子 agent 触发契约

本文件是 BenchClaw child skill module。父级 stage、node 或 pipeline 调度到本文件时，必须通过 opencode 命令 `/benchclaw-subskill` 启动隔离子 agent；该命令在 `BENCHCLAW_ROOT/opencode.json` 中配置为 `subtask: true`，并绑定 `mode: "subagent"` 的 `child-skill-module-runner`。禁止父级 manager 直接在自己的对话上下文中内联执行本文件步骤。

调用 `/benchclaw-subskill` 时必须传入：目标 `SKILL.md` 绝对路径、注册 skill 名、冻结的 `PROJECT_ROOT` / `BENCHCLAW_ROOT` / `WORKSPACE_PARENT` / `WORKSPACE_ROOT`、当前 node 或 work_unit id、已满足的输入 artifact 路径、期望输出 artifact 路径、父级 DAG 依赖与完成判据。子 agent 只返回 `status`、artifact 路径、证据摘要和 blockers，不回灌长日志或完整中间内容。

如果当前执行上下文不是 `/benchclaw-subskill` 产生的 `child-skill-module-runner` 子 agent，本文件不得继续执行；应立即返回 `BLOCKED`，说明必须由父级使用 `/benchclaw-subskill` 重新派发。

# Node Skill — 执行计划生成

## 输入

- `data_12_benchmark_draft`

## 处理

1. 将 benchmark 草稿转化为 Stage2 到 Stage5 可执行计划。
2. 固化数据源、采集数量、目录结构、标注工具、GT 来源、模板合成策略、评测模型配置要求。
3. 数据源路径只能来自 benchmark 草稿中追溯到的 `BENCHCLAW_ROOT/benchmarkDatasetCards`、`BENCHCLAW_ROOT/realDataCards`、`BENCHCLAW_ROOT/simulatorCards` 三类卡片；标注工具路径只能来自 benchmark 草稿中追溯到的 `BENCHCLAW_ROOT/annotation-tool`。
4. 若 `data_12_benchmark_draft` 缺少对 `data_01` 到 `data_11` 的必要追溯，必须写 `BLOCKED`，不得绕过草稿直接读取上游数据补洞。
5. 生成给 Stage2 的 handoff 文件和全流程执行计划。

## 输出

- `artifacts/data_13_execution_plan/execution_plan.yaml`
- `artifacts/data_13_execution_plan/stage2_handoff.yaml`
- `artifacts/data_13_execution_plan/stage3_handoff.yaml`
- `artifacts/data_13_execution_plan/stage4_handoff.yaml`
- `artifacts/data_13_execution_plan/stage5_handoff.yaml`
- 节点执行记录文件
