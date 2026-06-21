---
name: benchclaw-stage1-template-metric-draft-generation
description: Use for the specific BenchClaw node skill `stage1-template-metric-draft-generation` only when its parent stage explicitly dispatches to it.
---

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
