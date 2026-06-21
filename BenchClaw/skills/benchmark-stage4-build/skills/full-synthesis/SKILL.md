---
name: benchclaw-stage4-full-synthesis
description: Use for the specific BenchClaw node skill `stage4-full-synthesis` only when its parent stage explicitly dispatches to it.
---

# Node Skill — 全量合成

## 输入

- `data_20_template_metric_code_bundle`
- `data_21_grey_validation_report`
- Stage3 三类已标注数据

## tmux 后台全量批量合成监控硬约束

全量 benchmark item 生成、媒体复制/链接、GT 落盘、评分配置生成、数据集卡生成和 checksum 计算都属于长任务风险区，必须使用 tmux 后台执行并每 15 秒监控直到结束。

1. 启动前必须创建 `WORKSPACE_ROOT/stage4/nodes/full-synthesis/run_logs/`。
2. 启动命令必须使用：

```text
tmux new-session -d -s <tmux_session_name> "<command> > <log_path> 2>&1; printf '\nEXIT_CODE:%s\n' \$? >> <log_path>"
```

3. `tmux_session_name` 建议格式：`benchclaw_s4_full_synthesis_full_benchmark_<YYYYMMDDHHMMSS>`；`log_path` 必须位于 `nodes/full-synthesis/run_logs/full-benchmark-synthesis.log`，监控记录必须写入 `nodes/full-synthesis/run_logs/full-benchmark-synthesis.monitoring.jsonl`。
4. 启动后立即检查一次 `tmux has-session`、`tmux capture-pane` 和 `tail -n 100 <log_path>`。
5. 只要 tmux 会话仍存在，就必须每 15 秒检查一次状态；每次记录已生成 item 数、媒体文件数、GT 文件数、metric/config 文件数、checksum 进度和最近日志摘要。
6. 会话结束后必须读取最终日志和 `EXIT_CODE`，校验 `dataset.jsonl`、`media/`、`ground_truth/`、`metrics/`、`cards/benchmark_card.md`、`checksums.json` 和 manifest；缺少 15 秒监控记录、最终日志、退出码或真实全量产物时，不得写 `DONE.json`。
7. 写 `DONE.json` 前必须保证本节点产物能通过 stage gate 中的 full-synthesis 检查；至少要有 `nodes/full-synthesis/run_logs/*.monitoring.jsonl`、包含 `EXIT_CODE:0` 的最终日志、非空 `dataset.jsonl`、非空 `media/`、非空 `ground_truth/`、非空 `metrics/`、`manifest.json`、`cards/benchmark_card.md` 和 `checksums.json`。

## 处理

1. 只使用通过灰度验证的模板与指标。
2. 按执行计划生成全量 benchmark item、媒体副本、GT、评分配置、数据集卡和校验和。
3. 所有媒体引用必须指向 workspace 内稳定存在的文件。
4. 每个 item 必须能追溯到数据源、证据记录、模板、答案程序与能力维度。
5. 禁止只输出旧版目录名 `sample_images/`、`gt_bundle/`；如果需要兼容旧调用，可额外写这些目录，但当前契约目录 `media/` 和 `ground_truth/` 必须存在且非空。
6. `NODE_REPORT.md` 必须记录全量合成 tmux session、完整命令、日志路径、15 秒监控记录摘要、退出状态、输出文件计数和质量门结果。

## 输出

- `artifacts/data_22_full_benchmark_dataset/dataset.jsonl`
- `artifacts/data_22_full_benchmark_dataset/manifest.json`
- `artifacts/data_22_full_benchmark_dataset/media/`
- `artifacts/data_22_full_benchmark_dataset/ground_truth/`
- `artifacts/data_22_full_benchmark_dataset/metrics/`
- `artifacts/data_22_full_benchmark_dataset/cards/benchmark_card.md`
- `artifacts/data_22_full_benchmark_dataset/checksums.json`
- 节点执行记录文件
