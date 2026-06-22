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
6. 会话结束后必须读取最终日志和 `EXIT_CODE`，校验 `dataset.jsonl`、`media/`、`ground_truth/`、`metrics/`、`cards/benchmark_card.md`、`checksums.json`、manifest 以及 `WORKSPACE_ROOT/EVALSET_DATASET/` 完整包；缺少 15 秒监控记录、最终日志、退出码或真实全量产物时，不得写 `DONE.json`。
7. 写 `DONE.json` 前必须保证本节点产物能通过 stage gate 中的 full-synthesis 检查；至少要有 `nodes/full-synthesis/run_logs/*.monitoring.jsonl`、包含 `EXIT_CODE:0` 的最终日志、非空 `dataset.jsonl`、非空 `media/`、非空 `ground_truth/`、非空 `metrics/`、`manifest.json`、`cards/benchmark_card.md`、`checksums.json`，以及非空 `WORKSPACE_ROOT/EVALSET_DATASET/` 完整评测包。

## 处理

1. 只使用通过灰度验证的模板与指标。
2. 按执行计划生成全量 benchmark item、媒体副本、GT、评分配置、数据集卡和校验和。
3. 所有媒体引用必须指向当前 `WORKSPACE_ROOT` 内稳定存在的文件，且在最终 `dataset.jsonl` 中必须写为可直接访问的本地绝对路径。
4. 默认应把最终 benchmark 使用的媒体统一收敛到 `artifacts/data_22_full_benchmark_dataset/media/` 或当前 workspace 内其他稳定目录；禁止把 `dataset.jsonl` 中的图片路径继续写成 `stage3/...`、相对路径或其他 workspace 的绝对路径。
5. 最终 benchmark item 必须同时保留原图列与作答图列：
   - `source_media`：原图；
   - `media`：给模型作答使用的处理图，可能是 GT overlay 图，也可能是无标识的回退处理图。
6. 若某题启用了 GT 图片标识处理，则必须同步落盘 sidecar 映射文件，使 label ↔ object_id ↔ GT evidence 可追溯；映射缺失的题不得进入最终 benchmark。
7. 每个 item 必须能追溯到数据源、证据记录、模板、答案程序与能力维度。
8. 除了 `artifacts/data_22_full_benchmark_dataset/` 外，必须同步生成 `WORKSPACE_ROOT/EVALSET_DATASET/`，作为 Stage5 默认消费的完整评测包。该目录必须至少包含：
   - `README.md`
   - `data/test.jsonl` 或等价的评测题目文件
   - `images/` 或等价的评测媒体目录
   - `metrics/` 中可直接执行的评测指标代码
   - 供评测或审计使用的答案/GT 数据
9. `WORKSPACE_ROOT/EVALSET_DATASET/` 中的内容必须与 `artifacts/data_22_full_benchmark_dataset/` 保持一致的评测语义，不能是另一套降级样本、占位图文或缺答案的空壳目录。
10. 禁止只输出旧版目录名 `sample_images/`、`gt_bundle/`；如果需要兼容旧调用，可额外写这些目录，但当前契约目录 `media/` 和 `ground_truth/` 必须存在且非空。
11. `NODE_REPORT.md` 必须记录全量合成 tmux session、完整命令、日志路径、15 秒监控记录摘要、退出状态、输出文件计数、`WORKSPACE_ROOT/EVALSET_DATASET/` 落盘位置和质量门结果。

## 输出

- `artifacts/data_22_full_benchmark_dataset/dataset.jsonl`
- `artifacts/data_22_full_benchmark_dataset/manifest.json`
- `artifacts/data_22_full_benchmark_dataset/media/`
- `artifacts/data_22_full_benchmark_dataset/ground_truth/`
- `artifacts/data_22_full_benchmark_dataset/metrics/`
- `artifacts/data_22_full_benchmark_dataset/cards/benchmark_card.md`
- `artifacts/data_22_full_benchmark_dataset/checksums.json`
- `WORKSPACE_ROOT/EVALSET_DATASET/`
- 节点执行记录文件
