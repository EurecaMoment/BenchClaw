---
name: benchclaw-stage2-existing-benchmark-content-label-analysis
description: Use for the specific BenchClaw subskill `stage2-existing-benchmark-content-label-analysis` only when its parent node explicitly dispatches to it.
---

## Opencode 子 agent 触发契约

本文件是 BenchClaw child skill module。父级 stage、node 或 pipeline 调度到本文件时，必须通过 opencode 命令 `/benchclaw-subskill` 启动隔离子 agent；该命令在 `BENCHCLAW_ROOT/opencode.json` 中配置为 `subtask: true`，并绑定 `mode: "subagent"` 的 `child-skill-module-runner`。禁止父级 manager 直接在自己的对话上下文中内联执行本文件步骤。

调用 `/benchclaw-subskill` 时必须传入：目标 `SKILL.md` 绝对路径、注册 skill 名、冻结的 `PROJECT_ROOT` / `BENCHCLAW_ROOT` / `WORKSPACE_PARENT` / `WORKSPACE_ROOT`、当前 node 或 work_unit id、已满足的输入 artifact 路径、期望输出 artifact 路径、父级 DAG 依赖与完成判据。子 agent 只返回 `status`、artifact 路径、证据摘要和 blockers，不回灌长日志或完整中间内容。

如果当前执行上下文不是 `/benchclaw-subskill` 产生的 `child-skill-module-runner` 子 agent，本文件不得继续执行；应立即返回 `BLOCKED`，说明必须由父级使用 `/benchclaw-subskill` 重新派发。

# Subskill — 已有 benchmark 内容与标注分析

## 作用域

本 subskill 只处理一个 benchmark 数据集 work unit。work unit 由父节点动态创建：

```text
dataset_id = benchmarkDatasetCards 下的直接子文件夹名
dataset_card_skill = BENCHCLAW_ROOT/benchmarkDatasetCards/<dataset_id>/SKILL.md
```

不要假设固定数据集名单；必须以传入的 `dataset_card_skill` 为该数据集的执行来源。

## 输入

- `stage2_execution_plan.yaml`
- `dataset_id`
- `dataset_card_skill`
- 数据集卡中声明的本地数据根、访问方式、任务格式和限制

## tmux 采集监控硬约束

本 subskill 执行任何数据目录扫描、远程访问、下载、解压、索引、官方标签清单生成或数据集卡声明的外部命令时，必须使用父节点传入的 `tmux_session_name`、`log_path`、`monitoring_log_path` 后台执行。

- 启动命令必须形如：`tmux new-session -d -s <tmux_session_name> "<command> > <log_path> 2>&1; printf '\nEXIT_CODE:%s\n' \$? >> <log_path>"`。
- 启动后立即检查一次 `tmux has-session -t <tmux_session_name>`、`tmux capture-pane -pt <tmux_session_name>` 和 `tail -n 100 <log_path>`。
- 只要会话仍在运行，必须每 15 秒检查一次采集状态并追加写 `monitoring_log_path`；检查必须持续到 tmux 会话结束。
- 输出报告必须记录 tmux session、日志路径、每 15 秒监控摘要、最终退出状态和分析出的媒体/样本/官方标签计数；缺少这些证据时不得向父节点报告完成。

## 处理

1. 读取且仅按当前 `dataset_card_skill` 理解该数据集。
2. 建立字段清单和媒体清单：官方样本 ID、问题/指令/上下文、候选项、结构化输入、媒体组与顺序、官方答案、标签字段、split、任务类型、评测口径、许可边界、数据集特有字段。
3. 分析任务类型、输入字段、输出字段、媒体组织方式、官方标注、许可约束和可复用边界。
4. 标出规整映射：哪些字段进入统一 envelope，哪些字段必须保留到 `source_fields`、`raw_record` 或 `extra_metadata`。
5. 识别后续 Stage3/Stage4 需要但官方数据未直接提供的新增标注需求。
6. 不修改 `benchmarkDatasetCards` 中的任何文件；数据集卡与原始数据目录均视为只读。

## 输出给本数据集 work unit

写入父节点为该数据集分配的隔离目录：

```text
artifacts/data_15_existing_benchmark_collection_bundle/datasets/<dataset_id>/
  run_logs/
```

至少产出可被 `data-materialization` 消费的分析记录，记录中必须保留：

- `dataset_id`
- `source_card_skill`
- 官方样本 ID 或可追溯来源 ID
- 可复用字段、官方标签字段和新增标注需求的边界
- 完整字段清单、媒体清单、字段到统一 envelope 的映射和不能丢弃的数据集特有字段
