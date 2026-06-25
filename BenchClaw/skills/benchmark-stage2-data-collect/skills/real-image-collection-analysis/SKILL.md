---
name: benchclaw-stage2-real-image-collection-analysis
description: Use for the specific BenchClaw node skill `stage2-real-image-collection-analysis` only when its parent stage explicitly dispatches to it.
---

## Opencode 子 agent 触发契约

本文件是 BenchClaw child skill module。父级 stage、node 或 pipeline 调度到本文件时，必须通过 opencode 命令 `/benchclaw-subskill` 启动隔离子 agent；该命令在 `BENCHCLAW_ROOT/opencode.json` 中配置为 `subtask: true`，并绑定 `mode: "subagent"` 的 `child-skill-module-runner`。禁止父级 manager 直接在自己的对话上下文中内联执行本文件步骤。

调用 `/benchclaw-subskill` 时必须传入：目标 `SKILL.md` 绝对路径、注册 skill 名、冻结的 `PROJECT_ROOT` / `BENCHCLAW_ROOT` / `WORKSPACE_PARENT` / `WORKSPACE_ROOT`、当前 node 或 work_unit id、已满足的输入 artifact 路径、期望输出 artifact 路径、父级 DAG 依赖与完成判据。子 agent 只返回 `status`、artifact 路径、证据摘要和 blockers，不回灌长日志或完整中间内容。

如果当前执行上下文不是 `/benchclaw-subskill` 产生的 `child-skill-module-runner` 子 agent，本文件不得继续执行；应立即返回 `BLOCKED`，说明必须由父级使用 `/benchclaw-subskill` 重新派发。

# Node Skill — 真实图片采集与分析

## 内部层级

本节点包含两个 subskill，按每个真实图片数据集独立运行。运行时必须优先通过 `/benchclaw-subskill` 按已注册 skill 名调度，下面的路径仅用于源码定位：

```text
subskills/content-analysis/SKILL.md
subskills/data-structure-normalization/SKILL.md
```

## Registered Subskill Names

本节点的内部 DAG 在 opencode 中必须通过 `/benchclaw-subskill` 显式派发以下 skill 名：

- `content-analysis` -> `benchclaw-stage2-real-image-content-analysis`
- `data-structure-normalization` -> `benchclaw-stage2-real-image-data-structure-normalization`

## Work Unit Context Return Protocol

每个真实图片数据集 work unit 只返回：`dataset_id`、`status`、per-dataset 输出目录、媒体/样本计数、阻塞原因和一句摘要。不要把数据卡原文、长目录枚举、日志全文或大批 metadata 记录继续塞回父节点。

## 动态数据集发现

1. 使用冻结的 `BENCHCLAW_ROOT`，定位真实图片数据卡根目录：

```text
BENCHCLAW_ROOT/realDataCards
```

2. 运行时枚举该目录的直接子文件夹；不要硬编码任何数据集名称，也不要修改该目录下的任何文件。
3. 每个直接子文件夹代表一个候选真实图片数据集。该文件夹必须包含：

```text
<dataset_folder>/SKILL.md
```

4. 若某个直接子文件夹缺少 `SKILL.md`，该数据集不可被静默跳过；必须在本节点写入 `BLOCKED.json` 与 `BLOCKED.md`，说明缺失的数据集文件夹和期望的 skill 路径。
5. 若没有发现任何数据集文件夹，只有在 `stage2_execution_plan.yaml` 明确说明本项目不需要真实图片数据时，才可写入空 bundle；否则必须阻塞。

## 输入

- `stage2_execution_plan.yaml`
- `BENCHCLAW_ROOT/realDataCards/*/SKILL.md` 动态发现到的真实图片数据卡
- 每个数据卡中声明的本地数据根、来源记录、授权数据目录或访问方式

## tmux 后台采集监控硬约束

本节点内所有数据源 work unit 的内容分析、媒体扫描、下载/复制、解压、索引和数据结构规整命令，都必须按 `stage2_execution_plan.yaml` 中对应 DAG 节点的 `tmux_required: true` 执行。

1. 每个可执行 DAG 节点必须用 `tmux new-session -d -s <tmux_session_name> "<command> > <log_path> 2>&1; printf '\nEXIT_CODE:%s\n' \$? >> <log_path>"` 后台启动，不得在前台长时间采集。
2. 启动后立即用 `tmux has-session -t <tmux_session_name>`、`tmux capture-pane -pt <tmux_session_name>` 和 `tail -n 100 <log_path>` 检查一次。
3. 只要 tmux 会话仍存在，就必须每 15 秒检查一次采集状态；任一活跃会话两次检查间隔不得超过 15 秒。检查内容至少包括会话是否存活、最近 pane 输出、最近 100 行日志、已落盘媒体/样本计数。
4. 每次检查必须追加写入 `monitoring_log_path`，记录 `timestamp`、`tmux_session_name`、`dag_node_id`、`status`、`log_tail_summary`、`artifact_counts`；直到 `tmux has-session` 显示会话结束为止。
5. 会话结束后必须读取最终日志和 `EXIT_CODE`，校验 per-dataset 输出目录、媒体文件、manifest 和样本计数；缺少 15 秒监控记录、最终日志或真实落盘产物时，不得写 `DONE.json`。

## 每数据集并行 work unit

对每个合法数据集文件夹创建一个独立 work unit：

```text
dataset_id = 文件夹名
real_data_card_skill = BENCHCLAW_ROOT/realDataCards/<dataset_id>/SKILL.md
```

执行时必须优先读取 `stage2_execution_plan.yaml` 的 `parallel_dag.nodes[]`，只选择 `category: real_image` 且 `parent_category_node: real-image-collection-analysis` 的节点作为本节点内部 DAG。每个真实图片数据源 work unit 必须在计划中存在以下两个具体 DAG 节点：

```text
real_image::<dataset_id>::content-analysis
real_image::<dataset_id>::data-structure-normalization
```

这两个节点必须分别通过 `/benchclaw-subskill` 精确调用对应的已注册 skill 名；文件路径只作为源码定位：

```text
benchclaw-stage2-real-image-content-analysis
benchclaw-stage2-real-image-data-structure-normalization
```

如果 `stage2_execution_plan.yaml` 没有显式列出某个真实图片数据集的上述 DAG 节点、节点缺少 `subskill_path`、`subskill_path` 指向其他类别，或不同数据集之间被错误建立依赖，必须 BLOCKED，不得自行补一个隐式串行流程。

每个 work unit 必须先读取自己的 `real_data_card_skill`，再在该数据卡的指导下依次通过 `/benchclaw-subskill` 运行：

1. `benchclaw-stage2-real-image-content-analysis`
2. `benchclaw-stage2-real-image-data-structure-normalization`

不同数据集 work unit 之间可以并行处理。并行时必须遵守：

- `stage2_execution_plan.yaml`、数据卡和原始数据目录只读。
- 每个 work unit 只能写入自己的 per-dataset 输出目录。
- 不允许多个 work unit 同时追加写 bundle 根目录下的汇总 JSONL/YAML。
- 所有 per-dataset work unit 完成后，再进行一次串行汇总。

## Per-dataset 输出目录

每个数据集先写入隔离目录：

```text
artifacts/data_14_real_image_collection_bundle/datasets/<dataset_id>/
  media/
  run_logs/
  media_manifest.jsonl
  metadata.jsonl
  annotation_requirements.yaml
  source_manifest.json
  DATASET_REPORT.md
```

每条 `metadata.jsonl` 记录必须遵守 `templates/collection_bundle_contract.md` 的统一样本 envelope，并至少带有：

- `dataset_id`
- `source_card_skill`
- 原始图片 ID 或可追溯来源 ID
- workspace 内稳定可访问的媒体路径或相对路径
- 原始元数据、不可归一化字段和新增标注需求边界

## 处理

1. 动态发现 `realDataCards` 下的所有数据集文件夹和对应 `SKILL.md`。
2. 对每个真实图片数据集独立执行内容分析。
3. 在各自 per-dataset 目录中物化媒体文件、媒体 manifest、元数据、来源记录和标注需求。
4. 不只记录外部路径；后续 Stage3 必需消费的媒体必须真实落盘到 workspace 内，图片必须存在、非空、sha256 已记录且可解码。
5. 统计本分支贡献的有效图片数：根 `media_manifest.jsonl` 中 `modality: image`、`decode_status: ok`、文件存在且非空的唯一 `workspace_path`。若 Stage2 汇总默认 100 张下限尚未满足且本分支仍有可采集数据，必须继续采集或补采，不能只因本分支非空就结束。
6. 所有数据集完成后，串行汇总 per-dataset 结果到 bundle 根目录。

## 汇总输出

- `artifacts/data_14_real_image_collection_bundle/media/`
- `artifacts/data_14_real_image_collection_bundle/datasets/<dataset_id>/...`
- `artifacts/data_14_real_image_collection_bundle/media_manifest.jsonl`
- `artifacts/data_14_real_image_collection_bundle/metadata.jsonl`
- `artifacts/data_14_real_image_collection_bundle/annotation_requirements.yaml`
- `artifacts/data_14_real_image_collection_bundle/source_manifest.json`
- 节点执行记录文件

`source_manifest.json` 必须记录：

- `real_data_cards_root`
- 动态发现到的所有数据集文件夹
- 每个数据集的 `real_data_card_skill`
- 每个数据集 work unit 的状态和 per-dataset 输出目录
- 每个 work unit 的 `tmux_session_name`、`log_path`、`monitoring_log_path`、15 秒监控记录摘要和最终退出状态
- 本分支有效图片总数，以及对 Stage2 默认 100 张总下限的贡献
- 被阻塞的数据集及原因，如有
