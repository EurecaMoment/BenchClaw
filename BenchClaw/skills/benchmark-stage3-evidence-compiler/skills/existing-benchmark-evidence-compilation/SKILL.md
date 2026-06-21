---
name: benchclaw-stage3-existing-benchmark-evidence-compilation
description: Use for the specific BenchClaw node skill `stage3-existing-benchmark-evidence-compilation` only when its parent stage explicitly dispatches to it.
---

# Node Skill — 已有 benchmark 清洗与标注

## 内部层级

本节点包含两个内部 subskill，按每个已有 benchmark 数据集 work unit 独立运行。运行时必须优先按已注册 skill 名调度，下面的路径仅用于源码定位：

```text
subskills/cleaning/SKILL.md
subskills/annotation/SKILL.md
```

## Registered Subskill Names

本节点的内部 DAG 在 opencode 中必须显式调用以下 skill 名：

- `cleaning` -> `benchclaw-stage3-existing-benchmark-cleaning`
- `annotation` -> `benchclaw-stage3-existing-benchmark-annotation`

## Work Unit Context Return Protocol

每个数据集 work unit 只返回：`dataset_id`、`status`、per-dataset 输出目录、cleaned/official-label/added-annotation 计数、阻塞原因和一句摘要。不要回灌官方标签全文、长清洗日志或全量样本正文。

## 输入

- `stage3_execution_plan`
- `data_15_existing_benchmark_collection_bundle`

## tmux 后台半监督标注监控硬约束

本节点内所有默认标注、新增半监督候选生成、标注输出整理和 annotation record 物化命令，都必须按 `stage3_execution_plan` 中对应 `substage: annotation` DAG 节点的 tmux 字段执行。

1. 每个 annotation DAG 节点必须用 `tmux new-session -d -s <tmux_session_name> "<command> > <log_path> 2>&1; printf '\nEXIT_CODE:%s\n' \$? >> <log_path>"` 后台启动，不得在前台长时间运行默认标注。
2. 启动后立即用 `tmux has-session -t <tmux_session_name>`、`tmux capture-pane -pt <tmux_session_name>` 和 `tail -n 100 <log_path>` 检查一次。
3. 只要 tmux 会话仍存在，就必须每 15 秒检查一次标注状态；任一活跃 annotation 会话两次检查间隔不得超过 15 秒。检查内容至少包括会话是否存活、最近 pane 输出、最近 100 行日志、已产出 `result.json` 数、`added_annotation_records.jsonl` 记录数、保留官方 label 数和失败/复核计数。
4. 每次检查必须追加写入 `monitoring_log_path`，记录 `timestamp`、`tmux_session_name`、`dag_node_id`、`status`、`log_tail_summary`、`artifact_counts`；直到 `tmux has-session` 显示会话结束为止。
5. 会话结束后必须读取最终日志和 `EXIT_CODE`，校验 `default_annotation_output/`、`default_annotation_manifest.jsonl`、`added_annotation_records.jsonl`、`review_queue.jsonl` 和 `evidence_manifest.json`；缺少 15 秒监控记录、最终日志或真实标注输出时，不得写 `DONE.json`。

## 每数据集 work unit

从 `data_15_existing_benchmark_collection_bundle/source_manifest.json` 和 `datasets/<dataset_id>/` 动态发现已有 benchmark 数据集；不要硬编码任何数据集名称。

执行时必须优先读取 `stage3_execution_plan` 的 `parallel_dag.nodes[]`，只选择 `category: existing_benchmark` 且 `parent_category_node: existing-benchmark-evidence-compilation` 的节点作为本节点内部 DAG。每个已有 benchmark 数据源 work unit 必须在计划中存在以下两个具体 DAG 节点：

```text
existing_benchmark::<dataset_id>::cleaning
existing_benchmark::<dataset_id>::annotation
```

这两个节点必须分别精确调用对应的已注册 skill 名；文件路径只作为源码定位：

```text
benchclaw-stage3-existing-benchmark-cleaning
benchclaw-stage3-existing-benchmark-annotation
```

如果 `stage3_execution_plan` 没有显式列出某个 benchmark 数据集的上述 DAG 节点、节点缺少 `subskill_path`、`subskill_path` 指向其他类别，或不同数据集之间被错误建立依赖，必须 BLOCKED，不得自行补一个隐式串行流程。

每个 work unit 必须依次运行：

1. `benchclaw-stage3-existing-benchmark-cleaning`
2. `benchclaw-stage3-existing-benchmark-annotation`

## Per-dataset 输出目录

```text
artifacts/data_18_annotated_existing_benchmark_bundle/datasets/<dataset_id>/
  media/
  data_juicer/
  default_annotation_input/
  default_annotation_output/
  annotation_or_gt/
  cleaned_items.jsonl
  text_items.jsonl
  official_labels.jsonl
  added_annotation_records.jsonl
  review_queue.jsonl
  evidence_manifest.json
  DATASET_REPORT.md
```

## 处理

1. 动态发现 `data_15` 中的已有 benchmark 数据集和官方标注。
2. 对每个数据集先调用 `benchclaw-stage3-existing-benchmark-cleaning`，该 subskill 必须通过 `BENCHCLAW_ROOT/data-juicer_card/SKILL.md` 运行 Data-Juicer pipeline，不能只做手写清洗。
3. 基于清洗结果调用 `benchclaw-stage3-existing-benchmark-annotation`，该 subskill 必须调用 `BENCHCLAW_ROOT/annotation-tool/default-annotation/SKILL.md` 的默认标注流程；默认标注输出作为新增候选，不得覆盖官方 label。
4. 对缺失媒体、字段冲突、官方 label 不可解释或新增标注失败的样本写入复核队列。
5. 将每条清洗样本的媒体、文本、官方 label、新增标注候选和来源字段完整写入 workspace：媒体必须复制或链接到本 bundle 的 `media/`，`text_items.jsonl` 必须包含题干、答案字段、label 文本、任务字段或可追溯文本摘要。
6. 每个 per-dataset `evidence_manifest.json` 必须记录 Data-Juicer 命令、配置、日志、退出码、输入/输出计数、默认标注命令、tmux session、15 秒监控日志、输出目录、样本到结果的映射、官方 label 来源、媒体 sha256/尺寸和阻塞/复核原因。
7. 写 `DONE.json` 前必须检查 `cleaned_items.jsonl`、`text_items.jsonl`、`official_labels.jsonl` 或 `added_annotation_records.jsonl` 至少有一个有效 GT/候选来源，且所有新增标注目标都真实运行默认标注或进入复核队列；不得用空文件、未执行样例或复述官方说明替代。
8. 串行汇总 per-dataset 结果到 `data_18` 根目录。

## 汇总输出

- `artifacts/data_18_annotated_existing_benchmark_bundle/media/`
- `artifacts/data_18_annotated_existing_benchmark_bundle/datasets/<dataset_id>/...`
- `artifacts/data_18_annotated_existing_benchmark_bundle/cleaned_items.jsonl`
- `artifacts/data_18_annotated_existing_benchmark_bundle/text_items.jsonl`
- `artifacts/data_18_annotated_existing_benchmark_bundle/official_labels.jsonl`
- `artifacts/data_18_annotated_existing_benchmark_bundle/added_annotation_records.jsonl`
- `artifacts/data_18_annotated_existing_benchmark_bundle/default_annotation_manifest.jsonl`
- `artifacts/data_18_annotated_existing_benchmark_bundle/review_queue.jsonl`
- `artifacts/data_18_annotated_existing_benchmark_bundle/evidence_manifest.json`
- 节点执行记录文件
