# Node Skill — 模型 scope 预处理分析

## 运行策略

- 本 skill 只用于离线预处理，不属于 `benchmark-stage1-draft` 的正常 pipeline DAG。
- 正常 `benchmark-pipeline` 不得自动调度本 skill；启动 Stage1 前必须已经有它的离线产物。
- 只有用户明确要求离线 scope 预处理时才运行；其产物是 Stage1 正常 pipeline 的必需输入。

## 输入

- 外部模型 scope 分析结果、能力卡、聚类结果或用户授权的数据索引

## 处理

1. 读取已存在的 scope/聚类/能力信号，不重新解释为 GT。
2. 将能力信号归一化为可被能力维度划分消费的候选能力池。
3. 记录每个能力信号的来源、证据、置信等级和限制。

## 输出

- `artifacts/data_06_semisupervised_capability_signals/signals.jsonl`
- `artifacts/data_08_preprocessed_capability_pool/capability_pool.jsonl`
- 节点执行记录文件
