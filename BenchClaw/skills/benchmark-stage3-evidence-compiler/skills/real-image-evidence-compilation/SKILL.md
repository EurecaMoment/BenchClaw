---
name: benchclaw-stage3-real-image-evidence-compilation
description: Use for the specific BenchClaw node skill `stage3-real-image-evidence-compilation` only when its parent stage explicitly dispatches to it.
---

# Node Skill — 真实图片清洗与标注

## 内部层级

本节点包含两个内部 subskill，按每个真实图片数据集 work unit 独立运行。运行时必须优先按已注册 skill 名调度，下面的路径仅用于源码定位：

```text
subskills/cleaning/SKILL.md
subskills/annotation/SKILL.md
```

## Registered Subskill Names

本节点的内部 DAG 在 opencode 中必须显式调用以下 skill 名：

- `cleaning` -> `benchclaw-stage3-real-image-cleaning`
- `annotation` -> `benchclaw-stage3-real-image-annotation`

## Work Unit Context Return Protocol

每个数据集 work unit 只返回：`dataset_id`、`status`、per-dataset 输出目录、cleaned/annotation 计数、review 数、阻塞原因和一句摘要。不要回灌 Data-Juicer 长日志、默认标注原始大结果或整包图片路径列表。

## 输入

- `stage3_execution_plan`
- `data_14_real_image_collection_bundle`

## tmux 后台半监督标注监控硬约束

本节点内所有默认标注、半监督候选生成、标注输出整理和 annotation record 物化命令，都必须按 `stage3_execution_plan` 中对应 `substage: annotation` DAG 节点的 tmux 字段执行。

1. 每个 annotation DAG 节点必须用 `tmux new-session -d -s <tmux_session_name> "<command> > <log_path> 2>&1; printf '\nEXIT_CODE:%s\n' \$? >> <log_path>"` 后台启动，不得在前台长时间运行默认标注。
2. 启动后立即用 `tmux has-session -t <tmux_session_name>`、`tmux capture-pane -pt <tmux_session_name>` 和 `tail -n 100 <log_path>` 检查一次。
3. 只要 tmux 会话仍存在，就必须每 15 秒检查一次标注状态；任一活跃 annotation 会话两次检查间隔不得超过 15 秒。检查内容至少包括会话是否存活、最近 pane 输出、最近 100 行日志、已产出 `result.json` 数、`annotation_records.jsonl` 记录数和失败/复核计数。
4. 每次检查必须追加写入 `monitoring_log_path`，记录 `timestamp`、`tmux_session_name`、`dag_node_id`、`status`、`log_tail_summary`、`artifact_counts`；直到 `tmux has-session` 显示会话结束为止。
5. 会话结束后必须读取最终日志和 `EXIT_CODE`，校验 `default_annotation_output/`、`default_annotation_manifest.jsonl`、`annotation_records.jsonl`、`review_queue.jsonl` 和 `evidence_manifest.json`；缺少 15 秒监控记录、最终日志或真实标注输出时，不得写 `DONE.json`。

## 每数据集 work unit

从 `data_14_real_image_collection_bundle/source_manifest.json` 和 `datasets/<dataset_id>/` 动态发现真实图片数据集；不要硬编码任何数据集名称。

执行时必须优先读取 `stage3_execution_plan` 的 `parallel_dag.nodes[]`，只选择 `category: real_image` 且 `parent_category_node: real-image-evidence-compilation` 的节点作为本节点内部 DAG。每个真实图片数据源 work unit 必须在计划中存在以下两个具体 DAG 节点：

```text
real_image::<dataset_id>::cleaning
real_image::<dataset_id>::annotation
```

这两个节点必须分别精确调用对应的已注册 skill 名；文件路径只作为源码定位：

```text
benchclaw-stage3-real-image-cleaning
benchclaw-stage3-real-image-annotation
```

如果 `stage3_execution_plan` 没有显式列出某个真实图片数据集的上述 DAG 节点、节点缺少 `subskill_path`、`subskill_path` 指向其他类别，或不同数据集之间被错误建立依赖，必须 BLOCKED，不得自行补一个隐式串行流程。

每个 work unit 必须先读取 Stage2 写出的 per-dataset 目录，再依次运行：

1. `benchclaw-stage3-real-image-cleaning`
2. `benchclaw-stage3-real-image-annotation`

不同数据集 work unit 可以并行处理。并行时必须遵守：

- `stage3_execution_plan` 与 `data_14` 只读。
- 每个 work unit 只能写入自己的 per-dataset 输出目录。
- 所有 work unit 完成后，再串行汇总到 `data_17` bundle 根目录。

## Per-dataset 输出目录

```text
artifacts/data_17_annotated_real_image_bundle/datasets/<dataset_id>/
  media/
  data_juicer/
  default_annotation_input/
  default_annotation_output/
  annotation_or_gt/
  cleaned_items.jsonl
  text_items.jsonl
  annotation_records.jsonl
  review_queue.jsonl
  evidence_manifest.json
  DATASET_REPORT.md
```

## 处理

1. 动态发现 `data_14` 中的真实图片数据集和可用媒体。
2. 对每个数据集先调用 `benchclaw-stage3-real-image-cleaning`，该 subskill 必须通过 `BENCHCLAW_ROOT/data-juicer_card/SKILL.md` 运行 Data-Juicer pipeline，不能只做手写清洗。
3. 基于清洗结果调用 `benchclaw-stage3-real-image-annotation`，该 subskill 必须调用 `BENCHCLAW_ROOT/annotation-tool/default-annotation/SKILL.md` 的默认标注流程；服务不可用、无可标注图片或默认标注失败时必须 BLOCKED。
4. 真实图片不得把模型推断直接提升为 GT；可验证人工标注或授权 GT 必须单独标明来源。
5. 将每条清洗样本的图像、文本、标注候选和来源字段完整写入 workspace：图片必须复制或链接到本 bundle 的 `media/`，`text_items.jsonl` 必须包含 Stage4 可读的文本字段，`annotation_records.jsonl` 必须引用默认标注真实输出和复核状态。
6. 每个 per-dataset `evidence_manifest.json` 必须记录 Data-Juicer 命令、配置、日志、退出码、输入/输出计数、默认标注命令、tmux session、15 秒监控日志、输出目录、样本到结果的映射、媒体 sha256/尺寸和阻塞/复核原因。
7. 写 `DONE.json` 前必须检查 `cleaned_items.jsonl`、`text_items.jsonl`、`annotation_records.jsonl` 非空，除非 `stage3_execution_plan` 显式允许该数据集为空；每条记录引用的 workspace 图片存在、非空、可解码且在 manifest 中可追溯。
8. 串行汇总 per-dataset 结果到 `data_17` 根目录。

## 汇总输出

- `artifacts/data_17_annotated_real_image_bundle/media/`
- `artifacts/data_17_annotated_real_image_bundle/datasets/<dataset_id>/...`
- `artifacts/data_17_annotated_real_image_bundle/cleaned_items.jsonl`
- `artifacts/data_17_annotated_real_image_bundle/text_items.jsonl`
- `artifacts/data_17_annotated_real_image_bundle/annotation_records.jsonl`
- `artifacts/data_17_annotated_real_image_bundle/default_annotation_manifest.jsonl`
- `artifacts/data_17_annotated_real_image_bundle/review_queue.jsonl`
- `artifacts/data_17_annotated_real_image_bundle/evidence_manifest.json`
- 节点执行记录文件
