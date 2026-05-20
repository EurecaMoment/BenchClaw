# 12 benchmark 草稿 Skill

全局路径约束：`BENCHCLAW_ROOT` 仅作只读输入；`WORKSPACE_ROOT` 是本次流程唯一总工作目录，所有写操作和流程产物只能落在其下。

## 节点定位

- 节点 ID：`12`
- 英文名：`benchmark-draft`
- 父节点：00, 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11
- 作用：把 0–11 的结果汇总为 benchmark 设计草稿。注意：这是汇总节点，不代表前面节点串行执行。

## 必读输入

- 读取父节点 `00` 的 `DONE.json` 和其声明输出。
- 读取父节点 `01` 的 `DONE.json` 和其声明输出。
- 读取父节点 `02` 的 `DONE.json` 和其声明输出。
- 读取父节点 `03` 的 `DONE.json` 和其声明输出。
- 读取父节点 `04` 的 `DONE.json` 和其声明输出。
- 读取父节点 `05` 的 `DONE.json` 和其声明输出。
- 读取父节点 `06` 的 `DONE.json` 和其声明输出。
- 读取父节点 `07` 的 `DONE.json` 和其声明输出。
- 读取父节点 `08` 的 `DONE.json` 和其声明输出。
- 读取父节点 `09` 的 `DONE.json` 和其声明输出。
- 读取父节点 `10` 的 `DONE.json` 和其声明输出。
- 读取父节点 `11` 的 `DONE.json` 和其声明输出。

## 必写输出

- `stage1/12_benchmark_draft/benchmark_draft.md`
- `stage1/12_benchmark_draft/design_traceability_table.csv`

## 中间文件含义

完整字段、消费方和边界统一维护在仓库根目录的 `contracts/intermediate_files.md`；本节点只保留摘要：

- `benchmark_draft.md`：汇总 `00` 到 `11` 的 Stage1 benchmark 设计草稿，是 `13` 的唯一业务输入。
- `design_traceability_table.csv`：把每个设计决策连接到来源节点、证据文件、风险和下游阶段。

## 具体步骤

1. 读取 `00` 到 `11` 的全部已完成产物。
2. 汇总 benchmark 名称、目标、能力维度、细分能力考点、模板、模板-考点 Q-matrix、指标、数据来源、仿真器、标注工具和风险。
3. 在 benchmark 草稿中明确写出三类来源的执行数量约束：
   - 被选中的真实数据源图文数据默认全量流入后续全流程；
   - 被选中的已有 benchmark 图文数据默认全量流入后续全流程；
   - 被选中的仿真器对每个场景至少采集 50 个时刻帧的数据，且每个时刻可包含多模态或多视角图像。
4. 形成可供论文/系统设计使用的 Stage1 benchmark 草稿。
5. 生成 `design_traceability_table.csv`，每一行连接：设计决策 → 来源节点 → 证据文件 → 风险。

## 质量门

通用质量门见 `contracts/quality_gates.md`；本节点专属质量门：

- `benchmark_draft.md` 必须汇总 `00` 到 `11` 的结果，不得重新发明能力维度。
- `benchmark_draft.md` 必须保留 `08` 的考点 ID 和 `09` 的 Q-matrix 摘要，供后续教育学分析追踪。
- `design_traceability_table.csv` 中每个设计决策必须连接来源节点、证据文件和风险。
- 不得写入 `13` 的执行计划内容。
- `benchmark_draft.md` 不得把已选真实数据、已选 benchmark 数据集改写成抽样处理目标；除非用户明确要求缩减，否则必须把它们声明为后续全量流入。
- `benchmark_draft.md` 不得把仿真器采集规模写成开放式“按资源决定”；每个选中场景至少 50 个时刻帧必须作为最低执行基线出现。
