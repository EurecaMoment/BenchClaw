# Node Skill — 模板/指标/代码生成

## 内部层级

```text
subskills/template-compilation/SKILL.md
subskills/metric-compilation/SKILL.md
subskills/answer-program-generation/SKILL.md
subskills/contract-checking/SKILL.md
```

## 输入

- `data_11_template_metric_initial_draft`
- `data_17_annotated_real_image_bundle`
- `data_18_annotated_existing_benchmark_bundle`
- `data_19_annotated_simulator_bundle`
- `stage4_execution_plan.yaml`

## 处理

1. 以图像、GT、证据字段为约束编译题目模板。
2. 为每个模板生成答案程序、评分指标、字段契约和失败条件。
3. 进行静态契约检查，确认每个模板均能从 Stage3 产物中取到所需证据。

## 输出

- `artifacts/data_20_template_metric_code_bundle/templates/`
- `artifacts/data_20_template_metric_code_bundle/metrics/`
- `artifacts/data_20_template_metric_code_bundle/answer_programs/`
- `artifacts/data_20_template_metric_code_bundle/contracts/`
- `artifacts/data_20_template_metric_code_bundle/traceability.csv`
- 节点执行记录文件
