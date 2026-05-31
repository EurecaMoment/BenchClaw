# Node Skill — 本阶段执行计划生成

## 输入

- `data_11_template_metric_initial_draft`
- `data_13_execution_plan`
- `data_17_annotated_real_image_bundle`
- `data_18_annotated_existing_benchmark_bundle`
- `data_19_annotated_simulator_bundle`

## 处理

1. 固化模板生成、指标生成、答案程序生成、灰度验证和全量合成的执行顺序。
2. 明确每类数据源可参与的模板集合和 GT 来源。
3. 写入 Stage4 计划。

## 输出

- `nodes/stage4-plan-generation/stage4_execution_plan.yaml`
- 节点执行记录文件
