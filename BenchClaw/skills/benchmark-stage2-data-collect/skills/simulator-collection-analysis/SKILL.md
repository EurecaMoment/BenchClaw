# Node Skill — 仿真器采集与分析

## 内部层级

本节点包含两个 subskill，按每个仿真器和任务族独立运行：

```text
subskills/data-acquisition/SKILL.md
subskills/gt-materialization/SKILL.md
```

## 输入

- `stage2_execution_plan.yaml`
- 仿真器卡、环境配置、任务需求

## 处理

1. 按计划运行仿真器采集观测、状态、动作、场景配置和 privileged GT。
2. 将观测媒体、状态日志、GT、随机种子、环境版本物化到 workspace。
3. 采集失败必须记录失败原因与复现命令，不可改用未授权数据替代。

## 输出

- `artifacts/data_16_simulator_collection_bundle/observations/`
- `artifacts/data_16_simulator_collection_bundle/state_logs.jsonl`
- `artifacts/data_16_simulator_collection_bundle/privileged_gt.jsonl`
- `artifacts/data_16_simulator_collection_bundle/scenario_manifest.json`
- 节点执行记录文件
