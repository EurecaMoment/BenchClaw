# Node Skill — 执行计划生成

## 输入

- `data_12_benchmark_draft`

## 处理

1. 将 benchmark 草稿转化为 Stage2 到 Stage5 可执行计划。
2. 固化数据源、采集数量、目录结构、标注工具、GT 来源、模板合成策略、评测模型配置要求。
3. 数据源路径只能来自 benchmark 草稿中追溯到的 `BENCHCLAW_ROOT/benchmarkDatasetCards`、`BENCHCLAW_ROOT/realDataCards`、`BENCHCLAW_ROOT/simulatorCards` 三类卡片；标注工具路径只能来自 benchmark 草稿中追溯到的 `BENCHCLAW_ROOT/annotation-tool`。
4. 若 `data_12_benchmark_draft` 缺少对 `data_01` 到 `data_11` 的必要追溯，必须写 `BLOCKED`，不得绕过草稿直接读取上游数据补洞。
5. 生成给 Stage2 的 handoff 文件和全流程执行计划。

## 输出

- `artifacts/data_13_execution_plan/execution_plan.yaml`
- `artifacts/data_13_execution_plan/stage2_handoff.yaml`
- `artifacts/data_13_execution_plan/stage3_handoff.yaml`
- `artifacts/data_13_execution_plan/stage4_handoff.yaml`
- `artifacts/data_13_execution_plan/stage5_handoff.yaml`
- 节点执行记录文件
