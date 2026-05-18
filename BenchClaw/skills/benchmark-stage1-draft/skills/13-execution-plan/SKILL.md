# 13 执行计划 Skill

## 节点定位

- 节点 ID：`13`
- 英文名：`execution-plan`
- 父节点：12
- 作用：根据 `12 benchmark 草稿` 生成 Stage2/Stage3/Stage4 可执行计划；13 只能依赖 12，不直接依赖 08/09/10/11。

## 必读输入

- 读取父节点 `12` 的 `DONE.json`。
- 读取 `stage1/12_benchmark_draft/benchmark_draft.md`。
- 读取 `stage1/12_benchmark_draft/design_traceability_table.csv`。

## 必写输出

- `stage1/13_execution_plan/execution_plan.md`
- `stage1/13_execution_plan/stage2_handoff.yaml`

## 中间文件含义

完整字段、消费方和边界统一维护在仓库根目录的 `contracts/intermediate_files.md`；本节点只保留摘要：

- `execution_plan.md`：Stage2/Stage3/Stage4 的可执行工作包、依赖、质量门和回退计划。
- `stage2_handoff.yaml`：交给 Stage2 的机器可读合同，只能从 `12` 的草稿和追踪表抽取。

## 具体步骤

1. 读取 `12` 的 benchmark 草稿与设计追踪表。
2. 生成 Stage2/Stage3/Stage4 的执行计划：数据采集、证据构造、模板合成、指标实现、质量门、失败回退。
3. 输出 `stage2_handoff.yaml`，其中 simulator routing、tool routing、template routing、Q-matrix 引用、evidence contracts 必须从 `12` 的草稿和追踪表中抽取，不重新直接读取 08/09/10/11。
4. 明确哪些任务可继续并行，哪些任务必须阻塞等待。

## 质量门

通用质量门见 `contracts/quality_gates.md`；本节点专属质量门：

- `13` 只能读取 `12` 的草稿、追踪表和 `DONE.json`，不得绕过 `12` 直接读取 `08/09/10/11`。
- `execution_plan.md` 必须是可执行任务合同，不是论文式描述。
- `stage2_handoff.yaml` 中的 routing、Q-matrix 引用和 evidence contracts 必须从 `12` 抽取。
