---
name: benchclaw-stage4-cdm-irt-analysis
description: Use for the specific BenchClaw subskill `stage4-cdm-irt-analysis` only when its parent node explicitly dispatches to it.
---

## Opencode 子 agent 触发契约

本文件是 BenchClaw child skill module。父级 stage、node 或 pipeline 调度到本文件时，必须通过 opencode 命令 `/benchclaw-subskill` 启动隔离子 agent；该命令在 `BENCHCLAW_ROOT/opencode.json` 中配置为 `subtask: true`，并绑定 `mode: "subagent"` 的 `child-skill-module-runner`。禁止父级 manager 直接在自己的对话上下文中内联执行本文件步骤。

调用 `/benchclaw-subskill` 时必须传入：目标 `SKILL.md` 绝对路径、注册 skill 名、冻结的 `PROJECT_ROOT` / `BENCHCLAW_ROOT` / `WORKSPACE_PARENT` / `WORKSPACE_ROOT`、当前 node 或 work_unit id、已满足的输入 artifact 路径、期望输出 artifact 路径、父级 DAG 依赖与完成判据。子 agent 只返回 `status`、artifact 路径、证据摘要和 blockers，不回灌长日志或完整中间内容。

如果当前执行上下文不是 `/benchclaw-subskill` 产生的 `child-skill-module-runner` 子 agent，本文件不得继续执行；应立即返回 `BLOCKED`，说明必须由父级使用 `/benchclaw-subskill` 重新派发。

# Subskill — CDM/IRT 必达诊断

## 目标

基于 small-batch-result-evaluation 产生的 score matrix，估计题目难度、区分度代理指标、能力覆盖和难度配比风险。该 subskill 是 full-synthesis 的必达前置门。

## 输入

```text
small_model_eval/score_matrix.jsonl
invalid_item_screening/valid_items.jsonl
```

## 输出

```text
cdm_irt/status.json
cdm_irt/item_parameters.csv
cdm_irt/model_ability.csv
cdm_irt/capability_mastery.csv
cdm_irt/template_diagnostics.csv
cdm_irt/item_level_findings.jsonl
cdm_irt/cdm_irt_summary.json
cdm_irt/cdm_irt_report.md
```

## 规则

- 有外部模型矩阵时，按真实模型 score matrix 做诊断。
- 无外部模型时，必须使用 proxy score matrix 做灰度门诊断，并在 status/summary 中标记 `matrix_source=proxy`。
- 小样本可以标记 `limited_matrix`，但仍必须输出 item/model/capability 三类诊断表；不得 N/A 放行。
- full-synthesis 只能读取 `cdm_irt/status.json` 为 `PASS` 或 `LIMITED_PASS` 的灰度结果。

## 阻塞条件

- 没有 score matrix。
- score matrix 全 0 或全 1，无法计算任何难度/区分度代理。
- 输出为空或声称 PASS 却没有 item-level diagnostics。
