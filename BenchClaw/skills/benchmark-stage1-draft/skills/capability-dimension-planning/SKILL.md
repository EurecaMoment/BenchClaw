---
name: benchclaw-stage1-capability-dimension-planning
description: Use for the specific BenchClaw node skill `stage1-capability-dimension-planning` only when its parent stage explicitly dispatches to it.
---

# Node Skill — 能力维度划分

## 输入

- `data_03_intent_expansion_doc`
- `data_05_source_capability_descriptions`，其数据源来源必须来自于 `BENCHCLAW_ROOT/simulatorCards` 、`BENCHCLAW_ROOT/realDataCards`和`BENCHCLAW_ROOT/benchmarkDatasetCards`
- `data_06_semisupervised_capability_signals`，其标注工具能力必须来源于 `BENCHCLAW_ROOT/annotation-tool`
- `data_07_literature_review`
- `data_08_preprocessed_capability_pool`，由离线节点 `scope-preprocess-analysis` 从 `data_09_benchmark_data` 物化

正常 pipeline 不在线运行 `scope-preprocess-analysis`，但必须消费其离线产物 `data_08`；缺失时写 `BLOCKED` 并停止本节点。

## 处理

1. 建立用户意图、数据源能力、半监督标注能力、文献证据、预处理能力池与可评分输出之间的映射。
2. 合并重复维度，标记覆盖空洞与过宽维度。
3. 使用 `data_06` 时，只能把来自 `annotation-tool` 的工具能力作为候选伪标注/辅助标注能力，不得把工具输出提升为真实 GT。
4. 输出能力维度组织文档，供模板、指标和 benchmark 草稿使用。

## 输出

- `artifacts/data_10_capability_dimension_doc/capability_dimensions.md`
- `artifacts/data_10_capability_dimension_doc/q_matrix_seed.csv`
- 节点执行记录文件
