---
name: benchclaw-stage4-metric-compilation
description: Use for the specific BenchClaw subskill `stage4-metric-compilation` only when its parent node explicitly dispatches to it.
---

# Subskill — 指标编译

## 目标

为每个 enabled 模板编译可执行、可解释、可聚合的评分指标。指标必须能被 `answer_programs/` 和 `scripts/score_predictions.py` 调用，并能对后续合成出的 item 进行自动评分或明确声明外部评估协议。

本 subskill 新增链式难度聚合维度，但评分本身仍只根据 item answer 与 prediction 判分；不得重新读取隐藏 GT 为预测找补。

## 输入

- `artifacts/data_20_template_metric_code_bundle/templates/<template_id>.json`
- `artifacts/data_20_template_metric_code_bundle/selected_template_sources.jsonl`
- `artifacts/data_20_template_metric_code_bundle/template_manifest.jsonl`
- `artifacts/data_20_template_metric_code_bundle/gt_kinship/gt_distant_reasoning_chains.jsonl`
- `data_11_template_metric_initial_draft/metrics.yaml`
- `stage4_execution_plan.yaml`
- 本 stage `templates/benchmark_item.schema.json`
- 统一模板包中的 `template_system/05_metrics_and_scoring.md`
- 本 skill `reference_library/answer_type_metric_registry.json` 和 `reference_library/template_family_registry.yaml`

## 指标契约

每个指标写入：

```text
artifacts/data_20_template_metric_code_bundle/metrics/<metric_id>.json
artifacts/data_20_template_metric_code_bundle/metrics/<metric_id>.py
artifacts/data_20_template_metric_code_bundle/contracts/metric_contract.schema.json
```

指标 JSON 除现有字段外，评分报告契约必须支持：

```json
{
  "by_reasoning_hop_count": {},
  "by_gt_distance_level": {},
  "by_depth_role": {},
  "by_chain_id": {}
}
```

## 处理

1. 读取所有 enabled 模板，按 `answer_format` 和 `metric_id` 分组。
2. 对照 Stage1 `metrics.yaml`、`selected_template_sources.jsonl` 和统一模板包评分说明，保留同一 metric 的语义一致性。
3. 每个 metric 必须能追溯到：
   - `unified_template_id`
   - `canonical_question_type`
   - `reference_metric_id`
   - `chain_id`
4. 聚合维度必须新增：
   - `by_reasoning_hop_count`
   - `by_gt_distance_level`
   - `by_depth_role`
   - `by_chain_id`
5. 评分代码必须只根据 item answer 与 prediction 判分，不允许评分脚本重新读取隐藏 GT 来给预测找补。
6. 链式信息只用于聚合分析和诊断，不用于泄漏答案。

## 质量要求

- 主指标仍然必须属于外挂参考库保留 deterministic metric。
- 评分脚本必须接受 item metadata 中的：
  - `chain_id`
  - `reasoning_hop_count`
  - `gt_distance_level`
  - `depth_role`
  但这些字段只用于分桶聚合。
- 完美预测必须满分；负例必须低于完美预测。

## 失败与阻塞

- 若评分代码需要读取 Stage3 私有 GT 才能判分，必须阻塞。
- 若新增聚合维度无法从 item metadata 获得，而试图从隐藏数据反查，必须阻塞。
