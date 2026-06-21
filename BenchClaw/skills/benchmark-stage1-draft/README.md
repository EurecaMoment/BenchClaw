# benchmark-stage1-draft

从用户 benchmark idea 出发，完成意图理解、文献调研、能力维度划分、模板/指标初稿、benchmark 草稿和执行计划。

该目录是生产 skill 定义，不包含总驱动脚本。节点由 `dag.json` 与已注册的显式 skill 名调度；`skills/<node-id>/SKILL.md` 只作为源码落盘位置，不作为 opencode 运行时的首选调度键。
`skills/scope-preprocess-analysis/SKILL.md` 是离线 DAG 节点，不在正常在线 pipeline 中自动运行；它从 `data_09_benchmark_data` 物化 `data_08_preprocessed_capability_pool`。

Stage1 的数据源能力卡只允许来自 `BENCHCLAW_ROOT/benchmarkDatasetCards/`、`BENCHCLAW_ROOT/realDataCards/`、`BENCHCLAW_ROOT/simulatorCards/`。标注工具能力卡只允许来自 `BENCHCLAW_ROOT/annotation-tool/`。
