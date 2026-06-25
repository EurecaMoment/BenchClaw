---
name: benchclaw-stage3-existing-benchmark-annotation
description: Use for the specific BenchClaw subskill `stage3-existing-benchmark-annotation` only when its parent node explicitly dispatches to it.
---

## Opencode 子 agent 触发契约

本文件是 BenchClaw child skill module。父级 stage、node 或 pipeline 调度到本文件时，必须通过 opencode 命令 `/benchclaw-subskill` 启动隔离子 agent；该命令在 `BENCHCLAW_ROOT/opencode.json` 中配置为 `subtask: true`，并绑定 `mode: "subagent"` 的 `child-skill-module-runner`。禁止父级 manager 直接在自己的对话上下文中内联执行本文件步骤。

调用 `/benchclaw-subskill` 时必须传入：目标 `SKILL.md` 绝对路径、注册 skill 名、冻结的 `PROJECT_ROOT` / `BENCHCLAW_ROOT` / `WORKSPACE_PARENT` / `WORKSPACE_ROOT`、当前 node 或 work_unit id、已满足的输入 artifact 路径、期望输出 artifact 路径、父级 DAG 依赖与完成判据。子 agent 只返回 `status`、artifact 路径、证据摘要和 blockers，不回灌长日志或完整中间内容。

如果当前执行上下文不是 `/benchclaw-subskill` 产生的 `child-skill-module-runner` 子 agent，本文件不得继续执行；应立即返回 `BLOCKED`，说明必须由父级使用 `/benchclaw-subskill` 重新派发。

# Subskill — 已有 benchmark 新增标注

## 作用域

本 subskill 只处理一个已有 benchmark 数据集 work unit 的新增标注需求。官方 label 只能作为已有证据引用，不能被覆盖。

## 输入

- `stage3_execution_plan`
- `dataset_id`
- `cleaning` subskill 产出的 `new_annotation_targets.jsonl`
- 官方 label 和新增标注需求

## tmux 半监督标注监控硬约束

本 subskill 调用 `BENCHCLAW_ROOT/annotation-tool/default-annotation/SKILL.md` 进行默认标注、新增半监督候选生成、结果整理或 manifest 生成时，必须使用 `stage3_execution_plan` 对应 annotation DAG 节点传入的 `tmux_session_name`、`log_path`、`monitoring_log_path` 后台执行。

- 启动命令必须形如：`tmux new-session -d -s <tmux_session_name> "<command> > <log_path> 2>&1; printf '\nEXIT_CODE:%s\n' \$? >> <log_path>"`。
- 启动后立即检查一次 `tmux has-session -t <tmux_session_name>`、`tmux capture-pane -pt <tmux_session_name>` 和 `tail -n 100 <log_path>`。
- 只要会话仍在运行，必须每 15 秒检查一次标注状态并追加写 `monitoring_log_path`；检查必须持续到 tmux 会话结束。
- 每次监控记录必须包含 `timestamp`、`tmux_session_name`、`dag_node_id`、会话状态、最近输出摘要、最近日志摘要、`default_annotation_output/` 中 `result.json` 计数、`added_annotation_records.jsonl` 计数、保留官方 label 计数和 `review_queue.jsonl` 计数。
- `annotation_or_gt/run_manifest.json` 和 `evidence_manifest.json` 必须记录 tmux session、日志路径、`monitoring_log_path`、开始/结束时间、每 15 秒监控摘要、最终 `EXIT_CODE`、输入图片数、输出 `result.json` 数、官方 label 引用数和失败/复核数；缺少这些证据时不得写 `DONE.json` 或向父节点报告完成。

## 处理

1. 必须先读取 `BENCHCLAW_ROOT/annotation-tool/default-annotation/SKILL.md`，并使用其中的 batch 或 single-image 默认标注流程；不得跳过默认标注改用其他工具链。
2. 对 `new_annotation_targets.jsonl` 中每条含可访问图片媒体的样本运行默认标注，推荐按 work unit 批量执行：

```bash
BENCHCLAW_ROOT=<frozen BENCHCLAW_ROOT> \
IMG_DIR=<current_work_unit>/default_annotation_input \
OUT_ROOT=<current_work_unit>/default_annotation_output \
ENABLE_STAGE3=1 \
WORKSPACE_ROOT=<frozen WORKSPACE_ROOT> \
BRANCH=benchmarkdataset \
GROUP_NAME=<dataset_id> \
SPLIT_NAME=<split_or_default> \
bash "$BENCHCLAW_ROOT/annotation-tool/default-annotation/run_batch_image_to_gt.sh"
```

3. 如果 cleaned media 不在同一输入目录，必须为本 work unit 构造 `default_annotation_input/`，用复制或 symlink 方式放入要标注的图片，并保留官方样本 ID 到文件名/manifest 的映射。
4. 每条新增标注必须记录标注来源、默认标注输出目录、`result.json`、工具版本或服务响应、置信度、是否人工复核和关联的官方样本 ID。
5. 默认标注输出必须标记为 `tool_generated_candidate`，默认进入复核队列；不得修改或重写 `official_labels.jsonl`。
6. 若样本没有图片媒体、默认标注服务不可用、没有生成 `result.json` 或无法追溯官方样本 ID，必须写入 `BLOCKED.json`/`BLOCKED.md` 或 `review_queue.jsonl`，不得静默跳过。
7. 必须保存真实标注执行证明到 `annotation_or_gt/`：实际命令或 API 调用、tmux session、stdout/stderr 或服务日志、15 秒监控日志、退出码或响应状态、工具版本、开始/结束时间、输入图片清单、输出 `result.json` 清单和样本计数。缺少执行证明时不得写 `DONE.json`。
8. `added_annotation_records.jsonl` 每条记录必须符合 `templates/annotation_record.schema.json`，并至少包含 workspace 媒体路径、文本字段、官方样本 ID、默认标注输出文件、`label_role: tool_generated_candidate`、`gt_status: candidate_needs_review`、`official_label_refs`、`cleaning_run_id`、`annotation_run_id` 和 Stage2 来源引用。
9. `evidence_manifest.json` 必须覆盖 `new_annotation_targets.jsonl` 中每个目标：成功标注的样本指向真实 `result.json`，已有官方 GT 的样本指向 `official_labels.jsonl`，失败或无法标注的样本进入 `review_queue.jsonl` 并记录原因；不得遗漏样本。

## 输出

写入当前 per-dataset 目录：

```text
default_annotation_input/
default_annotation_output/
annotation_or_gt/command_or_call.json
annotation_or_gt/stdout.log
annotation_or_gt/stderr.log
annotation_or_gt/exit_code.txt
annotation_or_gt/tmux_monitoring.jsonl
annotation_or_gt/run_manifest.json
added_annotation_records.jsonl
default_annotation_manifest.jsonl
review_queue.jsonl
evidence_manifest.json
DATASET_REPORT.md
```
