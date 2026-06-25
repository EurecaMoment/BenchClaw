---
name: benchclaw-stage4-small-batch-result-evaluation
description: Use for the specific BenchClaw subskill `stage4-small-batch-result-evaluation` only when its parent node explicitly dispatches to it.
---

## Opencode 子 agent 触发契约

本文件是 BenchClaw child skill module。父级 stage、node 或 pipeline 调度到本文件时，必须通过 opencode 命令 `/benchclaw-subskill` 启动隔离子 agent；该命令在 `BENCHCLAW_ROOT/opencode.json` 中配置为 `subtask: true`，并绑定 `mode: "subagent"` 的 `child-skill-module-runner`。禁止父级 manager 直接在自己的对话上下文中内联执行本文件步骤。

调用 `/benchclaw-subskill` 时必须传入：目标 `SKILL.md` 绝对路径、注册 skill 名、冻结的 `PROJECT_ROOT` / `BENCHCLAW_ROOT` / `WORKSPACE_PARENT` / `WORKSPACE_ROOT`、当前 node 或 work_unit id、已满足的输入 artifact 路径、期望输出 artifact 路径、父级 DAG 依赖与完成判据。子 agent 只返回 `status`、artifact 路径、证据摘要和 blockers，不回灌长日志或完整中间内容。

如果当前执行上下文不是 `/benchclaw-subskill` 产生的 `child-skill-module-runner` 子 agent，本文件不得继续执行；应立即返回 `BLOCKED`，说明必须由父级使用 `/benchclaw-subskill` 重新派发。

# Subskill — 小批量结果评测

## 目标

验证灰度 valid items 的 scorer、题型解析、作答图像路径和模型响应矩阵。该 subskill 是 full-synthesis 的必达前置门，不允许因为没有外部模型配置而跳过。

## 必做输出

```text
scorer_smoke/perfect_predictions.jsonl
scorer_smoke/negative_predictions.jsonl
scorer_smoke/perfect_score_report.json
scorer_smoke/negative_score_report.json
small_model_eval/predictions.jsonl
small_model_eval/score_items.jsonl
small_model_eval/score_matrix.jsonl
small_model_eval/model_overall_scores.csv
small_model_eval/model_question_format_scores.csv
small_model_eval/status.json
```

## 执行规则

1. 先运行 deterministic scorer smoke：完美预测必须满分，负例必须低于满分。
2. 若 `modelNeedMeasured/model_config.json` 可用且 Stage4 plan 未禁用外部模型，则运行真实模型 mini eval。
3. 若外部模型不可用，必须运行内置 proxy responders：`oracle`、`biased_first`、`random_seeded`、`wrong_choice`。这些 responders 只用于验证灰度门与 CDM/IRT 输入矩阵，不得写成真实模型能力排名。
4. 所有输出必须包含 `model`、`item_id`、`score`、`template_id`、`question_format`、`difficulty_level`。

## 可执行脚本

```text
scripts/grey_batch_eval.py mandatory-proxy-eval   --gold invalid_item_screening/valid_items.jsonl   --out-dir small_model_eval
```

## 阻塞条件

- scorer smoke 失败。
- 既未完成真实模型 mini eval，也未完成 proxy eval。
- `score_matrix.jsonl` 为空或缺少 item/template/difficulty 字段。
