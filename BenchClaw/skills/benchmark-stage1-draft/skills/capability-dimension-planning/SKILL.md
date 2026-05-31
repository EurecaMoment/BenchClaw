# Node Skill — 能力维度划分

## 输入

- `data_03_intent_expansion_doc`
- `data_07_literature_review`
- 已离线物化的 `data_06_semisupervised_capability_signals`
- 已离线物化的 `data_08_preprocessed_capability_pool`

正常 pipeline 不在线运行 `scope-preprocess-analysis`，但必须消费上述离线产物；缺失时写 `BLOCKED` 并停止本节点。

## 处理

1. 建立能力维度、子能力、任务证据、可观测行为和可评分输出之间的映射。
2. 合并重复维度，标记覆盖空洞与过宽维度。
3. 输出能力维度组织文档，供模板、指标和 benchmark 草稿使用。

## 输出

- `artifacts/data_10_capability_dimension_doc/capability_dimensions.md`
- `artifacts/data_10_capability_dimension_doc/q_matrix_seed.csv`
- 节点执行记录文件
