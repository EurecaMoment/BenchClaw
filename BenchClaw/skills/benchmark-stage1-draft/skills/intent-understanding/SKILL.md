# Node Skill — 意图理解

## 输入

- `data_01_user_idea`

## 处理

1. 冻结用户原始 idea，不改写原文。
2. 抽取评测目标、对象域、能力边界、任务形态、数据约束、评分约束。
3. 生成检索 query 和意图扩写文档。
4. 本节点不得生成或修改 `data_05_source_capability_descriptions`、`data_06_semisupervised_capability_signals`、`data_09_benchmark_data`；这些是根输入数据。

## 输出

- `artifacts/data_02_rewritten_queries/queries.jsonl`
- `artifacts/data_03_intent_expansion_doc/intent.md`
- `nodes/intent-understanding/USED_INPUTS.json`
- `nodes/intent-understanding/DONE.json`
- `nodes/intent-understanding/NODE_REPORT.md`
