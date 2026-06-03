# Node Skill — 已有 benchmark 采集与分析

## 内部层级

本节点包含两个 subskill，按每个已有 benchmark 数据集独立运行：

```text
subskills/content-label-analysis/SKILL.md
subskills/data-materialization/SKILL.md
```

## 动态数据集发现

1. 使用冻结的 `BENCHCLAW_ROOT`，定位 benchmark 数据集卡根目录：

```text
BENCHCLAW_ROOT/benchmarkDatasetCards
```

2. 运行时枚举该目录的直接子文件夹；不要硬编码任何数据集名称，也不要修改该目录下的任何文件。
3. 每个直接子文件夹代表一个候选 benchmark 数据集。该文件夹必须包含：

```text
<dataset_folder>/SKILL.md
```

4. 若某个直接子文件夹缺少 `SKILL.md`，该数据集不可被静默跳过；必须在本节点写入 `BLOCKED.json` 与 `BLOCKED.md`，说明缺失的数据集文件夹和期望的 skill 路径。
5. 若没有发现任何数据集文件夹，只有在 `stage2_execution_plan.yaml` 明确说明本项目不需要已有 benchmark 数据时，才可写入空 bundle；否则必须阻塞。

## 输入

- `stage2_execution_plan.yaml`
- `BENCHCLAW_ROOT/benchmarkDatasetCards/*/SKILL.md` 动态发现到的 benchmark 数据集卡
- 每个数据集卡中声明的本地数据根、下载记录、授权数据目录或访问方式

## tmux 后台采集监控硬约束

本节点内所有数据源 work unit 的内容/标注分析、媒体扫描、下载/复制、解压、索引和数据物化命令，都必须按 `stage2_execution_plan.yaml` 中对应 DAG 节点的 `tmux_required: true` 执行。

1. 每个可执行 DAG 节点必须用 `tmux new-session -d -s <tmux_session_name> "<command> > <log_path> 2>&1; printf '\nEXIT_CODE:%s\n' \$? >> <log_path>"` 后台启动，不得在前台长时间采集。
2. 启动后立即用 `tmux has-session -t <tmux_session_name>`、`tmux capture-pane -pt <tmux_session_name>` 和 `tail -n 100 <log_path>` 检查一次。
3. 只要 tmux 会话仍存在，就必须每 15 秒检查一次采集状态；任一活跃会话两次检查间隔不得超过 15 秒。检查内容至少包括会话是否存活、最近 pane 输出、最近 100 行日志、已落盘媒体/样本/官方标签计数。
4. 每次检查必须追加写入 `monitoring_log_path`，记录 `timestamp`、`tmux_session_name`、`dag_node_id`、`status`、`log_tail_summary`、`artifact_counts`；直到 `tmux has-session` 显示会话结束为止。
5. 会话结束后必须读取最终日志和 `EXIT_CODE`，校验 per-dataset 输出目录、媒体文件、raw items、official labels、manifest 和样本计数；缺少 15 秒监控记录、最终日志或真实落盘产物时，不得写 `DONE.json`。

## 每数据集并行 work unit

对每个合法数据集文件夹创建一个独立 work unit：

```text
dataset_id = 文件夹名
dataset_card_skill = BENCHCLAW_ROOT/benchmarkDatasetCards/<dataset_id>/SKILL.md
```

执行时必须优先读取 `stage2_execution_plan.yaml` 的 `parallel_dag.nodes[]`，只选择 `category: existing_benchmark` 且 `parent_category_node: existing-benchmark-collection-analysis` 的节点作为本节点内部 DAG。每个已有 benchmark 数据源 work unit 必须在计划中存在以下两个具体 DAG 节点：

```text
existing_benchmark::<dataset_id>::content-label-analysis
existing_benchmark::<dataset_id>::data-materialization
```

这两个节点必须分别精确调用：

```text
skills/existing-benchmark-collection-analysis/subskills/content-label-analysis/SKILL.md
skills/existing-benchmark-collection-analysis/subskills/data-materialization/SKILL.md
```

如果 `stage2_execution_plan.yaml` 没有显式列出某个 benchmark 数据集的上述 DAG 节点、节点缺少 `subskill_path`、`subskill_path` 指向其他类别，或不同数据集之间被错误建立依赖，必须 BLOCKED，不得自行补一个隐式串行流程。

每个 work unit 必须先读取自己的 `dataset_card_skill`，再在该数据集卡的指导下依次运行：

1. `subskills/content-label-analysis/SKILL.md`
2. `subskills/data-materialization/SKILL.md`

不同数据集 work unit 之间可以并行处理。并行时必须遵守：

- `stage2_execution_plan.yaml`、数据集卡和原始数据目录只读。
- 每个 work unit 只能写入自己的 per-dataset 输出目录。
- 不允许多个 work unit 同时追加写 bundle 根目录下的汇总 JSONL/YAML。
- 所有 per-dataset work unit 完成后，再进行一次串行汇总。

## Per-dataset 输出目录

每个数据集先写入隔离目录：

```text
artifacts/data_15_existing_benchmark_collection_bundle/datasets/<dataset_id>/
  media/
  run_logs/
  media_manifest.jsonl
  raw_items.jsonl
  existing_labels.jsonl
  new_annotation_requirements.yaml
  source_manifest.json
  DATASET_REPORT.md
```

每条 `raw_items.jsonl` 与 `existing_labels.jsonl` 记录必须遵守 `templates/collection_bundle_contract.md` 的统一样本 envelope，并至少带有：

- `dataset_id`
- `source_card_skill`
- 原始样本 ID 或官方 ID
- workspace 内稳定可访问的媒体路径或相对路径
- benchmark 原始输入字段、官方标签字段、任务类型和不可归一化字段

## 处理

1. 动态发现 `benchmarkDatasetCards` 下的所有数据集文件夹和对应 `SKILL.md`。
2. 对每个数据集独立分析内容、字段、媒体、官方标注、许可与可复用边界。
3. 在各自 per-dataset 目录中物化可用样本、媒体、媒体 manifest、官方标注和新增标注需求。
4. 保留官方 label 与新增语义描述的来源边界，不混写。
5. 所有数据集完成后，串行汇总 per-dataset 结果到 bundle 根目录。

## 汇总输出

- `artifacts/data_15_existing_benchmark_collection_bundle/media/`
- `artifacts/data_15_existing_benchmark_collection_bundle/datasets/<dataset_id>/...`
- `artifacts/data_15_existing_benchmark_collection_bundle/media_manifest.jsonl`
- `artifacts/data_15_existing_benchmark_collection_bundle/raw_items.jsonl`
- `artifacts/data_15_existing_benchmark_collection_bundle/existing_labels.jsonl`
- `artifacts/data_15_existing_benchmark_collection_bundle/new_annotation_requirements.yaml`
- `artifacts/data_15_existing_benchmark_collection_bundle/source_manifest.json`
- 节点执行记录文件

`source_manifest.json` 必须记录：

- `benchmark_dataset_cards_root`
- 动态发现到的所有数据集文件夹
- 每个数据集的 `dataset_card_skill`
- 每个数据集 work unit 的状态和 per-dataset 输出目录
- 每个 work unit 的 `tmux_session_name`、`log_path`、`monitoring_log_path`、15 秒监控记录摘要和最终退出状态
- 被阻塞的数据集及原因，如有
