---
name: benchclaw-stage4-metric-compilation
description: Use for the specific BenchClaw subskill `stage4-metric-compilation` only when its parent node explicitly dispatches to it.
---

## Opencode 子 agent 触发契约

本文件是 BenchClaw child skill module。父级 stage、node 或 pipeline 调度到本文件时，必须通过 opencode 命令 `/benchclaw-subskill` 启动隔离子 agent；该命令在 `BENCHCLAW_ROOT/opencode.json` 中配置为 `subtask: true`，并绑定 `mode: "subagent"` 的 `child-skill-module-runner`。禁止父级 manager 直接在自己的对话上下文中内联执行本文件步骤。

调用 `/benchclaw-subskill` 时必须传入：目标 `SKILL.md` 绝对路径、注册 skill 名、冻结的 `PROJECT_ROOT` / `BENCHCLAW_ROOT` / `WORKSPACE_PARENT` / `WORKSPACE_ROOT`、当前 node 或 work_unit id、已满足的输入 artifact 路径、期望输出 artifact 路径、父级 DAG 依赖与完成判据。子 agent 只返回 `status`、artifact 路径、证据摘要和 blockers，不回灌长日志或完整中间内容。

如果当前执行上下文不是 `/benchclaw-subskill` 产生的 `child-skill-module-runner` 子 agent，本文件不得继续执行；应立即返回 `BLOCKED`，说明必须由父级使用 `/benchclaw-subskill` 重新派发。

# Subskill — 指标编译

## 目标

为 enabled 模板生成确定性评分契约和 scorer。Stage4 主指标必须可复现、可离线执行，不能依赖 LLM judge 作为主判分。

## 输入

- `template_manifest.jsonl`
- `reference_library/answer_type_metric_registry.json`
- 父类 runtime scorer：`run_scoring_cli()` 或等价 deterministic scorer。

## 输出

```text
data_20_template_metric_code_bundle/metric_manifest.jsonl
data_20_template_metric_code_bundle/scripts/score_predictions.py
data_20_template_metric_code_bundle/contrib/metric_registry/metric_registry.json
```

`metric_manifest.jsonl` 每个 enabled 模板至少包含：

```json
{
  "template_id": "...",
  "answer_type": "single_choice|multi_choice|ordered_list|interval_choice|...",
  "metric_id": "accuracy|set_f1|order_exact_accuracy|...",
  "primary_metric": true,
  "prediction_parser": "choice_key|choice_set|ordered_keys|json_object|numeric_interval",
  "score_function": "score_exact_choice",
  "qwen_generation_notes": [
    "score_predictions.py must inspect only item/prediction/gold answer files, never Stage3 private GT."
  ]
}
```

`contrib/metric_registry/metric_registry.json` 必须把 scorer 可执行接口和 answer_type 映射写成机器可读格式，供 `answer-program-generation`、`package_evalset.py` 和 `audit_format/generation_report.json` 消费：

```json
{
  "schema_version": "benchclaw.stage4.metric_registry.v1",
  "scorer_cli": "scripts/score_predictions.py --items <items> --predictions <predictions> --gold <answers> --out <report>",
  "metrics": {
    "accuracy": {
      "answer_types": ["single_choice", "yes_no", "interval_choice"],
      "prediction_parser": "choice_key",
      "score_function": "score_exact_choice",
      "requires_complete_prediction_set": true
    }
  }
}
```

## 指标规则

- 单选/二选/区间选择：exact choice。
- 多选：set exact 与 F1；若父类当前只支持 exact choice，则多选模板不得 enabled。
- 排序：exact order 或 pairwise accuracy；当前 scorer 不支持时不得 enabled。
- 连续数值：必须转为区间、容差成功率或结构化 metric；不得裸数字答案。
- 评分只读取 item/answer 与 prediction，不得重新读取 Stage3 私有 GT 为预测找补。
- scorer 必须输出 item-level 分数、parse 状态和 summary。
- `score_predictions.py` 必须支持灰度和最终包共用的 CLI：

```bash
python scripts/score_predictions.py \
  --items items.jsonl \
  --predictions predictions.jsonl \
  --out score_report.json
```

如果最终打包后答案被移到 `ground_truth/answers.jsonl`，scorer 还必须支持 `--gold ground_truth/answers.jsonl`。本地 Qwen 生成 scorer 时只能实现 `metric_manifest.jsonl` 中声明的 deterministic metrics，不能新增 LLM judge 或主观评分。

## 阻塞条件

- enabled 模板没有 metric_id。
- 完美预测不能满分。
- 负例与完美预测同分。
- 评分脚本不可编译或不可执行。
