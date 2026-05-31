# Node Skill — 意图理解

## 输入

- `data_01_user_idea`
- 可读取的能力卡、数据卡、工具卡索引

## 处理

1. 冻结用户原始 idea，不改写原文。
2. 抽取评测目标、对象域、能力边界、任务形态、数据约束、评分约束。
3. 生成检索 query、意图扩写文档、数据源与能力描述。

## 输出

- `artifacts/data_02_rewritten_queries/queries.jsonl`
- `artifacts/data_03_intent_expansion_doc/intent.md`
- `artifacts/data_05_source_capability_descriptions/source_capability.md`
- `nodes/intent-understanding/USED_INPUTS.json`
- `nodes/intent-understanding/DONE.json`
- `nodes/intent-understanding/NODE_REPORT.md`
