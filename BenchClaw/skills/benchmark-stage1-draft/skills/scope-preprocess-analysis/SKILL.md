# Node Skill — 模型 scope 预处理分析

## 运行策略

- 本 skill 是 Stage1 DAG 中的 offline 节点，只用于离线预处理，不进入正常在线调度。
- 本节点消费 `data_09_benchmark_data`，输出 `data_08_preprocessed_capability_pool`。
- 正常 `benchmark-pipeline` 不得自动调度本 skill；启动在线 Stage1 前必须已经有它的离线产物。
- 只有用户明确要求离线 scope 预处理时才运行；其产物是 Stage1 正常 pipeline 的必需输入。

## 输入

- `data_09_benchmark_data`
- 可选的外部模型 scope 分析结果或聚类结果

## 处理

1. 读取 `data_09_benchmark_data`，提取可用于能力覆盖分析的任务、数据形态、标签/GT 类型、输入输出模态和约束。
2. 可合并已存在的模型 scope 分析或聚类结果，但不得重新解释为 GT。
3. 将候选能力信号归一化为可被能力维度划分消费的候选能力池。
4. 记录每个能力信号的来源、证据、置信等级和限制。
5. 本节点不得生成或修改 `data_06_semisupervised_capability_signals`；标注工具能力是根输入数据，只能来自 `BENCHCLAW_ROOT/annotation-tool`。

## 输出

- `artifacts/data_08_preprocessed_capability_pool/capability_pool.jsonl`
- 节点执行记录文件
