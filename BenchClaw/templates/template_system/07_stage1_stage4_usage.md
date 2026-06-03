
# Stage1 与 Stage4 的统一使用说明

## Stage1：从资料到 benchmark 设计

Stage1 不直接造题，而是生成“可被 Stage4 执行”的设计包。

推荐输出：

1. `benchmark_scope.md`：说明场景、输入模态、任务边界、排除项。
2. `capability_dimensions.md`：能力维度、定义、GT 依赖、参考 benchmark。
3. `template_plan.md`：计划使用哪些 T 模板族、对应能力和题型。
4. `metric_plan.md`：主指标、辅助指标、聚合方式。
5. `quality_gate_plan.md`：过滤规则、人工抽查点、风险说明。

## Stage4：从模板到 eval dataset

Stage4 不重新定义能力，而是执行 Stage1 的设计。

推荐输出：

1. `eval_dataset.jsonl`：符合 `schemas/eval_item.schema.json`。
2. `template_instantiation_report.md`：每类模板实例化数量、失败原因。
3. `quality_gate_report.md`：过滤统计、歧义样本、缺字段样本。
4. `score_eval_dataset.py` 或项目评分入口。
5. `metric_report.json`：按题型、能力、模板族聚合的指标。

## 关键连接字段

| 字段 | Stage1 产生 | Stage4 消费 |
|---|---:|---:|
| capability_id | 是 | 是 |
| answer_format | 是 | 是 |
| template_id/template_family | 是 | 是 |
| required_gt_fields | 是 | 是 |
| scoring_metric | 是 | 是 |
| quality_gate | 是 | 是 |
| evidence_ref | 否 | 是 |
| gold_answer | 否 | 是 |
