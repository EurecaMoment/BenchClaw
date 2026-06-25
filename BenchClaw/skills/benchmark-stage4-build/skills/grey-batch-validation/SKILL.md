---
name: benchclaw-stage4-grey-batch-validation
description: Use for the specific BenchClaw node skill `stage4-grey-batch-validation` only when its parent stage explicitly dispatches to it.
---

## Opencode 子 agent 触发契约

本文件是 BenchClaw child skill module。父级 stage、node 或 pipeline 调度到本文件时，必须通过 opencode 命令 `/benchclaw-subskill` 启动隔离子 agent；该命令在 `BENCHCLAW_ROOT/opencode.json` 中配置为 `subtask: true`，并绑定 `mode: "subagent"` 的 `child-skill-module-runner`。禁止父级 manager 直接在自己的对话上下文中内联执行本文件步骤。

调用 `/benchclaw-subskill` 时必须传入：目标 `SKILL.md` 绝对路径、注册 skill 名、冻结的 `PROJECT_ROOT` / `BENCHCLAW_ROOT` / `WORKSPACE_PARENT` / `WORKSPACE_ROOT`、当前 node 或 work_unit id、已满足的输入 artifact 路径、期望输出 artifact 路径、父级 DAG 依赖与完成判据。子 agent 只返回 `status`、artifact 路径、证据摘要和 blockers，不回灌长日志或完整中间内容。

如果当前执行上下文不是 `/benchclaw-subskill` 产生的 `child-skill-module-runner` 子 agent，本文件不得继续执行；应立即返回 `BLOCKED`，说明必须由父级使用 `/benchclaw-subskill` 重新派发。

# Node Skill — 小批量合成灰度验证

## 目标

用 `data_20_template_metric_code_bundle` 的公开 CLI 真实合成小批量 item，筛除无效题，完成 mandatory small-batch result evaluation，并执行 mandatory CDM/IRT 诊断。该节点 PASS 后，`full-synthesis` 才允许开始。

## 内部顺序

以下每个内部 subskill 都必须通过 `/benchclaw-subskill` 作为新的 `child-skill-module-runner` 子 agent 派发；本 node 只负责编排顺序、传递冻结路径与 artifact 契约、汇总返回摘要，不得直接内联执行 subskill 步骤。

1. `per-template-batch-synthesis` -> `benchclaw-stage4-per-template-batch-synthesis`
2. `invalid-item-screening` -> `benchclaw-stage4-invalid-item-screening`
3. `small-batch-result-evaluation` -> `benchclaw-stage4-small-batch-result-evaluation`
4. `cdm-irt-analysis` -> `benchclaw-stage4-cdm-irt-analysis`

## 必达输出

```text
artifacts/data_21_grey_validation_report/
  per_template_batch/generated_items.jsonl
  per_template_batch/filtered_items.jsonl
  per_template_batch/template_status.csv
  invalid_item_screening/valid_items.jsonl
  invalid_item_screening/invalid_items.jsonl
  invalid_item_screening/item_level_findings.jsonl
  scorer_smoke/perfect_score_report.json
  scorer_smoke/negative_score_report.json
  small_model_eval/predictions.jsonl
  small_model_eval/score_items.jsonl
  small_model_eval/score_matrix.jsonl
  small_model_eval/model_overall_scores.csv
  cdm_irt/status.json
  cdm_irt/item_parameters.csv
  cdm_irt/model_ability.csv
  cdm_irt/capability_mastery.csv
  cdm_irt/item_level_findings.jsonl
  cdm_irt/cdm_irt_summary.json
  template_status.csv
  item_level_findings.jsonl
  report.md
```

## 通过条件

- 至少 1 个模板真实产出 item。
- `valid_items.jsonl` 至少 1 行。
- 无效题筛查没有 error 级问题进入 valid 集。
- 完美预测满分，负例低于满分。
- `small_model_eval/score_matrix.jsonl` 非空；外部模型不可用时必须运行内置 deterministic/proxy responders，并在 `small_model_eval/status.json` 标记 `evaluation_mode=proxy`。
- `cdm_irt/cdm_irt_summary.json`、`item_parameters.csv`、`model_ability.csv` 非空；若是小样本，状态可为 `limited_matrix`，但不得为 `NA`。
- `difficulty_mix_report.json` 对灰度 valid items PASS。

## tmux

灰度合成、筛查、外部模型调用、CDM/IRT 可能长运行时必须使用 tmux，并在 `nodes/grey-batch-validation/run_logs/` 记录命令、日志、退出码和监控摘要。极小 smoke 可前台运行，但必须在 `NODE_REPORT.md` 写明耗时。
