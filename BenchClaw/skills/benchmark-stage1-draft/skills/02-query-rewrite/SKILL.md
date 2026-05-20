# 02 query 改写 Skill

全局路径约束：`BENCHCLAW_ROOT` 仅作只读输入；`WORKSPACE_ROOT` 是本次流程唯一总工作目录，所有写操作和流程产物只能落在其下。

## 节点定位

- 节点 ID：`02`
- 英文名：`query-rewrite`
- 父节点：01
- 作用：将意图理解改写为多组检索 query，而不是直接进入文献综述。

## 必读输入

- 读取父节点 `01` 的 `DONE.json` 和其声明输出。

## 必写输出

- `stage1/02_query/query_pack.json`
- `stage1/02_query/search_strategy.md`

## 中间文件含义

完整字段、消费方和边界统一维护在仓库根目录的 `contracts/intermediate_files.md`；本节点只保留摘要：

- `query_pack.json`：面向文献/benchmark/指标/工具召回的机器可读 query 集。
- `search_strategy.md`：说明检索空间、筛选规则、去重策略和风险，不承载文献结论。

## 具体步骤

1. 读取 `01_intent/intent_interpretation.md`。
2. 将意图转换为多类 query：核心概念、近义词、benchmark 名称、数据集名称、任务类型、评价指标、反例/失效模式。
3. 每条 query 标注用途：召回综述、召回 benchmark、召回指标、召回工具、召回负例。
4. 输出机器可读 `query_pack.json`。

## 质量门

通用质量门见 `contracts/quality_gates.md`；本节点专属质量门：

- `query_pack.json` 中每条 query 必须声明用途和对应意图链接。
- query 只能用于召回候选材料，不能被写成事实证据。
- `search_strategy.md` 必须说明纳入/排除和去重策略。
- 不分析文献内容。
