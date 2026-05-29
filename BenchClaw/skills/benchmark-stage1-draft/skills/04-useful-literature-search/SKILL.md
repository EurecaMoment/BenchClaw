# 04 搜索可用文献 Skill

全局路径约束：`BENCHCLAW_ROOT` 仅作只读输入；`WORKSPACE_ROOT` 是本次流程唯一总工作目录，所有写操作和流程产物只能落在其下。

## 节点定位

- 节点 ID：`04`
- 英文名：`useful-literature-search`
- 父节点：02
- 作用：基于 query_pack 并行检索与筛选候选文献，只做召回和去重，不做最终论证。

## 必读输入

- 读取父节点 `02` 的 `DONE.json` 和其声明输出。

## 必写输出

- `stage1/04_literature_search/candidate_papers.jsonl`
- `stage1/04_literature_search/candidate_papers.jsonl`
- `stage1/04_literature_search/search_log.md`

## 中间文件含义

完整字段、消费方和边界统一维护在仓库根目录的 `contracts/intermediate_files.md`；本节点只保留摘要：

- `candidate_papers.jsonl`：去重后的候选文献/benchmark/指标/工具材料列表的兼容性导出；规范真相源应写入 `candidate_papers.jsonl`。
- `search_log.md`：检索过程审计记录，解释 query 执行、筛选、去重和偏差风险。

## 具体步骤

1. 读取 `02_query/query_pack.json`。
2. 按 query 类型并行检索候选文献/benchmark/指标/工具材料。
3. 做去重、粗筛和用途标注。
4. 输出 `candidate_papers.jsonl`，字段至少包含：title、year、venue、url_or_id、matched_query、candidate_use、risk_note；规范真相源应同时写入 `candidate_papers.jsonl`。

## 质量门

通用质量门见 `contracts/quality_gates.md`；本节点专属质量门：

- `candidate_papers.jsonl` 与兼容性导出 `candidate_papers.jsonl` 只能表示候选召回结果，不得写成设计依据。
- 每条候选记录必须保留匹配 query、候选用途和风险说明。
- `search_log.md` 必须记录空结果、去重和粗筛决策。
- 不写综述结论，不把低置信候选直接写成设计依据。
