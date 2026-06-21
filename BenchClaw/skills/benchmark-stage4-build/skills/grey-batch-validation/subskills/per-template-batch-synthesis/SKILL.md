---
name: benchclaw-stage4-per-template-batch-synthesis
description: Use for the specific BenchClaw subskill `stage4-per-template-batch-synthesis` only when its parent node explicitly dispatches to it.
---

# Subskill — 每模板小批量合成

## 目标

按灰度配额逐模板生成小批量 item，并记录模板到 item、模板到过滤原因、模板到执行命令的追溯关系。该 subskill 不直接写最终 benchmark，只写 grey-batch validation 的中间产物。

## 输入

- `data_20_template_metric_code_bundle`
- `data_20_template_metric_code_bundle/scripts/generate_items.py`
- `data_20_template_metric_code_bundle/evidence_index.jsonl` 或 `source_inventory.jsonl`
- `data_20_template_metric_code_bundle/template_manifest.jsonl`、`metric_manifest.jsonl` 或 `synthesis_plan.yaml`

## 工具脚本

```text
scripts/per_template_batch_synthesis.py
```

推荐命令：

```bash
python scripts/per_template_batch_synthesis.py \
  --bundle artifacts/data_20_template_metric_code_bundle \
  --out-dir artifacts/data_21_grey_validation_report/per_template_batch \
  --limit-per-template 8 \
  --seed 20260601
```

可用参数：

- `--template-id <id>`：只跑指定模板，可重复传入。
- `--generator <path>`：覆盖 `scripts/generate_items.py` 路径。
- `--evidence-index <path>`：覆盖 evidence index 路径。
- `--limit-per-template <N>`：每模板灰度合成上限。

## tmux 后台小批量合成监控硬约束

本 subskill 的每模板灰度合成命令必须后台 `tmux` 执行，并每 15 秒检查一次直到结束。不得在前台长时间运行批量合成脚本。

1. 启动前必须创建 `WORKSPACE_ROOT/stage4/nodes/grey-batch-validation/run_logs/`。
2. 启动命令必须形如：

```text
tmux new-session -d -s <tmux_session_name> "<command> > <log_path> 2>&1; printf '\nEXIT_CODE:%s\n' \$? >> <log_path>"
```

3. `tmux_session_name` 建议格式：`benchclaw_s4_grey_batch_per_template_synthesis_<YYYYMMDDHHMMSS>`；日志写入 `run_logs/per-template-batch-synthesis.log`，监控记录写入 `run_logs/per-template-batch-synthesis.monitoring.jsonl`。
4. 启动后立即检查一次 `tmux has-session -t <tmux_session_name>`、`tmux capture-pane -pt <tmux_session_name>` 和 `tail -n 100 <log_path>`。
5. 只要会话仍存在，就必须每 15 秒检查一次状态；每次记录最近日志摘要、已完成模板数、`generated_items.jsonl` 行数、`filtered_items.jsonl` 行数、per-template 输出目录数和失败模板数。
6. 会话结束后必须读取最终日志和 `EXIT_CODE`，校验 `generated_items.jsonl`、`filtered_items.jsonl`、`template_status.csv`、`synthesis_manifest.json`；缺少 15 秒监控记录、最终日志、退出码或真实合成产物时，不得向父节点报告完成。

## 处理规则

1. 必须调用 `data_20_template_metric_code_bundle/scripts/generate_items.py` 或计划中声明的等价入口，不得手写伪造 item。
2. 每个 enabled 模板单独运行一次，输出到隔离目录：

```text
artifacts/data_21_grey_validation_report/per_template_batch/per_template/<template_id>/
  items.jsonl
  filtered_items.jsonl
  stdout.log
  stderr.log
  tmux_monitoring.jsonl
```

3. 所有模板完成后，串行汇总为：

```text
artifacts/data_21_grey_validation_report/per_template_batch/generated_items.jsonl
artifacts/data_21_grey_validation_report/per_template_batch/filtered_items.jsonl
artifacts/data_21_grey_validation_report/per_template_batch/template_status.csv
artifacts/data_21_grey_validation_report/per_template_batch/synthesis_manifest.json
```

4. `generated_items.jsonl` 中每条 item 必须至少包含 `item_id` 或 `id`、`template_id`、`question` 或 `question_text`、`answer` 或 `gold_answer`、媒体字段、评分字段或 `metric_id`。
5. 模板生成失败不得静默跳过；必须写入 `template_status.csv`，并保留 stdout/stderr。

## 输出

- `generated_items.jsonl`
- `filtered_items.jsonl`
- `template_status.csv`
- `synthesis_manifest.json`
- 每模板执行日志、tmux session、15 秒监控记录和退出状态
