# Node Skill — 文献搜索

## 输入

- `data_02_rewritten_queries`
- `data_03_intent_expansion_doc`

## 处理

1. 按 query 检索与 benchmark、能力维度、任务形式、指标有关的论文、项目、数据集卡。
2. 记录来源、题名、年份、链接、摘要、与本 benchmark 的关系。
3. 保留不可访问、缺下载入口、需要授权的记录，不自行替代。

## 输出

- `artifacts/data_04_retrieved_literature/literature_index.jsonl`
- 节点执行记录文件
