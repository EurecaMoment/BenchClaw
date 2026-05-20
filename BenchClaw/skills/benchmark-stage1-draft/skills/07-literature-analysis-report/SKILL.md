# 07 文献调研分析报告 Skill

全局路径约束：`BENCHCLAW_ROOT` 仅作只读输入；`WORKSPACE_ROOT` 是本次流程唯一总工作目录，所有写操作和流程产物只能落在其下。

## 节点定位

- 节点 ID：`07`
- 英文名：`literature-analysis-report`
- 父节点：03, 04
- 作用：把候选文献转化为 benchmark 设计证据，支撑后续能力划分与模板设计。

## 必读输入

- 读取父节点 `03` 的 `DONE.json` 和其声明输出。
- 读取父节点 `04` 的 `DONE.json` 和其声明输出。

## 必写输出

- `stage1/07_literature_analysis/literature_analysis_report.md`
- `stage1/07_literature_analysis/benchmark_design_evidence.md`

## 中间文件含义

完整字段、消费方和边界统一维护在仓库根目录的 `contracts/intermediate_files.md`；本节点只保留摘要：

- `literature_analysis_report.md`：围绕 benchmark 设计问题组织文献分析，不写泛泛综述。
- `benchmark_design_evidence.md`：把可引用的设计证据整理成账本，说明每条证据支持的设计决策。

## 具体步骤

1. 读取 `03_intent_doc/expanded_intent.md` 与 `04_literature_search/candidate_papers.jsonl`。
2. 对候选文献进行分组：已有 benchmark、构念定义、任务模板、指标、质量控制、失效模式。
3. 提取对 Stage1 有用的设计证据，而不是写泛泛综述。
4. 输出 `literature_analysis_report.md` 与 `benchmark_design_evidence.md`。

## 质量门

通用质量门见 `contracts/quality_gates.md`；本节点专属质量门：

- 文献分析必须围绕 benchmark 设计问题，不写泛泛综述。
- 每条 `benchmark_design_evidence.md` 证据必须说明支持的设计决策和限制。
- 文献不能替代用户意图，只能用于解释、约束或补强设计。
- 不把引用堆砌成设计理由。
