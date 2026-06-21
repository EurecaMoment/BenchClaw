---
name: benchclaw-stage3-simulator-annotation
description: Use for the specific BenchClaw subskill `stage3-simulator-annotation` only when its parent node explicitly dispatches to it.
---

# Subskill — 仿真器 GT 整理与标注

## 作用域

本 subskill 只处理一个仿真器 work unit 的清洗结果。

## 输入

- `stage3_execution_plan`
- `work_unit_id`
- `cleaning` subskill 产出的清洗状态日志和观测索引
- Stage2 的 privileged GT 或可验证状态记录

## tmux GT/半监督标注监控硬约束

本 subskill 执行 privileged GT 导出、GT 整理、annotation record 物化，或在 `stage3_execution_plan` 明确要求时调用 `BENCHCLAW_ROOT/annotation-tool/default-annotation/SKILL.md` 做额外视觉伪标注，都必须使用对应 annotation DAG 节点传入的 `tmux_session_name`、`log_path`、`monitoring_log_path` 后台执行。

- 启动命令必须形如：`tmux new-session -d -s <tmux_session_name> "<command> > <log_path> 2>&1; printf '\nEXIT_CODE:%s\n' \$? >> <log_path>"`。
- 启动后立即检查一次 `tmux has-session -t <tmux_session_name>`、`tmux capture-pane -pt <tmux_session_name>` 和 `tail -n 100 <log_path>`。
- 只要会话仍在运行，必须每 15 秒检查一次 GT/标注状态并追加写 `monitoring_log_path`；检查必须持续到 tmux 会话结束。
- 每次监控记录必须包含 `timestamp`、`tmux_session_name`、`dag_node_id`、会话状态、最近输出摘要、最近日志摘要、`privileged_gt.jsonl` 记录数、`annotation_records.jsonl` 记录数、`review_queue.jsonl` 计数；若执行额外视觉伪标注，还必须记录 `default_annotation_output/` 中 `result.json` 计数。
- `annotation_or_gt/run_manifest.json` 和 `evidence_manifest.json` 必须记录 tmux session、日志路径、`monitoring_log_path`、开始/结束时间、每 15 秒监控摘要、最终 `EXIT_CODE`、输入 step/episode 数、GT 记录数、annotation record 数和失败/复核数；缺少这些证据时不得写 `DONE.json` 或向父节点报告完成。

## 处理

1. 从 privileged state、仿真器 API 或可验证计算中导出 GT 和 annotation records。
2. 每条记录必须保留仿真器、场景、seed、step、观测路径、状态字段来源和计算规则。
3. 若 GT 无法从 privileged state 或可验证计算得到，必须写入阻塞或复核队列，不得用模型推断替代。
4. 默认情况下不得调用默认标注，也不得用默认标注替代仿真器 GT。
5. 只有当 `stage3_execution_plan` 明确要求额外视觉伪标注时，才可读取并调用 `BENCHCLAW_ROOT/annotation-tool/default-annotation/SKILL.md`。这些输出必须写成 `tool_generated_candidate`、`auxiliary_only: true`，并与 privileged GT 分开保存。
6. 记录环境版本、仿真器版本和复现命令。
7. 必须保存真实 GT 整理执行证明到 `annotation_or_gt/`：privileged state 输入路径、GT 计算或导出命令/API 调用、计算规则、tmux session、stdout/stderr 或日志、15 秒监控日志、退出码或响应状态、环境/仿真器版本、开始/结束时间、输入/输出样本计数和失败 step 计数。缺少执行证明时不得写 `DONE.json`。
8. `privileged_gt.jsonl` 每条记录必须包含 `record_id`、`work_unit_id`、`simulator_id`、`task_family`、`scenario_id`、`seed`、`step_or_episode_id`、`workspace_observations`、`text`、`gt`、`gt_source: privileged_state_or_verifiable_computation`、`gt_derivation`、`stage2_run_ref`、`cleaning_run_id`、`gt_run_id` 和 `validation`。
9. `annotation_records.jsonl` 必须引用 `privileged_gt.jsonl` 的记录；若额外视觉伪标注被显式要求，辅助候选必须另存默认标注输出并标记 `auxiliary_only: true`，不得覆盖或删除 privileged GT。
10. `evidence_manifest.json` 必须覆盖清洗后的每个 step/episode：成功 GT 指向 `privileged_gt.jsonl`，失败或无法计算的 step 进入 `review_queue.jsonl` 并记录原因；不得遗漏样本。

## 输出

写入当前 work unit 目录：

```text
annotation_or_gt/command_or_call.json
annotation_or_gt/stdout.log
annotation_or_gt/stderr.log
annotation_or_gt/exit_code.txt
annotation_or_gt/tmux_monitoring.jsonl
annotation_or_gt/run_manifest.json
privileged_gt.jsonl
annotation_records.jsonl
default_annotation_output/   # only when explicitly required by stage3_execution_plan
default_annotation_manifest.jsonl # only when explicitly required by stage3_execution_plan
review_queue.jsonl
evidence_manifest.json
WORK_UNIT_REPORT.md
```
