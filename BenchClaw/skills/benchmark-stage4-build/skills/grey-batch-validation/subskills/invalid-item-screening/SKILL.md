---
name: benchclaw-stage4-invalid-item-screening
description: Use for the specific BenchClaw subskill `stage4-invalid-item-screening` only when its parent node explicitly dispatches to it.
---

# Subskill — 无效题目筛除

## 目标

在模型评测前筛掉无效灰度题目，避免把媒体缺失、答案缺失、选项错误、评分契约缺失或证据不可追溯的 item 送入小批量评测。

## 输入

- `per-template-batch-synthesis` 产出的 `generated_items.jsonl`
- 冻结的 `WORKSPACE_ROOT`
- 可选：`data_20_template_metric_code_bundle/contracts/benchmark_item.schema.json`

## 工具脚本

```text
scripts/screen_invalid_items.py
```

推荐命令：

```bash
python scripts/screen_invalid_items.py \
  --items artifacts/data_21_grey_validation_report/per_template_batch/generated_items.jsonl \
  --out-dir artifacts/data_21_grey_validation_report/invalid_item_screening \
  --workspace-root "$WORKSPACE_ROOT" \
  --require-media
```

## tmux 后台筛选监控硬约束

无效题筛选会批量读取媒体、GT、评分契约和追溯字段，必须后台 `tmux` 执行并每 15 秒检查一次直到结束。

1. 启动前必须创建 `WORKSPACE_ROOT/stage4/nodes/grey-batch-validation/run_logs/`。
2. 启动命令必须形如：

```text
tmux new-session -d -s <tmux_session_name> "<command> > <log_path> 2>&1; printf '\nEXIT_CODE:%s\n' \$? >> <log_path>"
```

3. `tmux_session_name` 建议格式：`benchclaw_s4_grey_batch_invalid_item_screening_<YYYYMMDDHHMMSS>`；日志写入 `run_logs/invalid-item-screening.log`，监控记录写入 `run_logs/invalid-item-screening.monitoring.jsonl`。
4. 启动后立即检查一次 `tmux has-session -t <tmux_session_name>`、`tmux capture-pane -pt <tmux_session_name>` 和 `tail -n 100 <log_path>`。
5. 只要会话仍存在，就必须每 15 秒检查一次状态；每次记录最近日志摘要、已扫描 item 数、valid/invalid item 数、媒体缺失数和评分契约缺失数。
6. 会话结束后必须读取最终日志和 `EXIT_CODE`，校验 `valid_items.jsonl`、`invalid_items.jsonl`、`item_level_findings.jsonl`、`template_status.csv`、`screening_report.json`；缺少 15 秒监控记录、最终日志、退出码或真实筛选产物时，不得向父节点报告完成。

## 检查项

1. 题干字段存在：`question` 或 `question_text`。
2. 标准答案存在：`answer` 或 `gold_answer`。
3. `template_id` 存在，便于模板级灰度决策。
4. 视觉题媒体路径存在、非空，图片可通过文件头签名或可用时的 PIL 解码。
5. 选择题必须有 `options`；答案必须在选项 key 或选项文本中。
6. 选项文本不得重复。
7. 必须有 `metric_id` 或 `scoring`。
8. 必须有 `evidence_refs`、`evidence_ref`、`provenance` 或 `metadata` 中至少一种追溯信息。

## 输出

写入：

```text
artifacts/data_21_grey_validation_report/invalid_item_screening/
  valid_items.jsonl
  invalid_items.jsonl
  item_level_findings.jsonl
  template_status.csv
  screening_report.json
  tmux_monitoring.jsonl
```

其中：

- `valid_items.jsonl` 作为 `small-batch-result-evaluation prepare` 的首选输入。
- `item_level_findings.jsonl` 汇总到 `data_21_grey_validation_report/item_level_findings.jsonl`。
- `template_status.csv` 用于模板 pass/review/fail 决策。

## 阻塞条件

- 输入 `generated_items.jsonl` 不存在或为空。
- 所有 item 都被判为 invalid。
- 媒体路径大量缺失且无法确认该批次为纯文本题。
