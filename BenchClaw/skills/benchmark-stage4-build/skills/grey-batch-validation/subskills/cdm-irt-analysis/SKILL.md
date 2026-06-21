---
name: benchclaw-stage4-cdm-irt-analysis
description: Use for the specific BenchClaw subskill `stage4-cdm-irt-analysis` only when its parent node explicitly dispatches to it.
---

# Subskill — CDM/IRT 分析

## 目标

基于灰度小批量模型评测的 item-level score，进行诊断性 CDM/IRT 分析，输出模型能力代理、题目难度、题目区分度、能力维度覆盖/掌握度和适用性说明。

该 subskill 必须实现代码并真实运行。样本量不足时不得伪造精确 IRT 结论，只能输出诊断性 Rasch proxy、CDM mastery 聚合和适用范围警告。

## 输入

- `small-batch-result-evaluation` 输出的 item-level score：

```text
artifacts/data_21_grey_eval_results/**/scores/*_score_items.jsonl
artifacts/data_21_grey_eval_results/**/scores/*_score_items.csv
artifacts/data_21_grey_eval_results/**/score_items.jsonl
```

- 可选 item metadata：

```text
artifacts/data_21_grey_eval_results/**/sampled_gold.jsonl
artifacts/data_21_grey_validation_report/invalid_item_screening/valid_items.jsonl
artifacts/data_21_grey_validation_report/per_template_batch/generated_items.jsonl
```

## 工具脚本

```text
scripts/cdm_irt_analysis.py
```

推荐命令：

```bash
python scripts/cdm_irt_analysis.py \
  --score-root artifacts/data_21_grey_eval_results \
  --items artifacts/data_21_grey_validation_report/invalid_item_screening/valid_items.jsonl \
  --out-dir artifacts/data_21_grey_validation_report/cdm_irt_analysis \
  --threshold 0.5 \
  --min-models 5 \
  --min-items 30
```

也可以直接传 score 文件或 glob：

```bash
python scripts/cdm_irt_analysis.py \
  --scores 'artifacts/data_21_grey_eval_results/**/scores/*_score_items.jsonl' \
  --out-dir artifacts/data_21_grey_validation_report/cdm_irt_analysis
```

## tmux 后台分析监控硬约束

CDM/IRT 分析必须真实运行脚本，并后台 `tmux` 执行、每 15 秒检查一次直到结束。不得只写分析报告或手工汇总表冒充脚本输出。

1. 启动前必须创建 `WORKSPACE_ROOT/stage4/nodes/grey-batch-validation/run_logs/`。
2. 启动命令必须形如：

```text
tmux new-session -d -s <tmux_session_name> "<command> > <log_path> 2>&1; printf '\nEXIT_CODE:%s\n' \$? >> <log_path>"
```

3. `tmux_session_name` 建议格式：`benchclaw_s4_grey_batch_cdm_irt_analysis_<YYYYMMDDHHMMSS>`；日志写入 `run_logs/cdm-irt-analysis.log`，监控记录写入 `run_logs/cdm-irt-analysis.monitoring.jsonl`。
4. 启动后立即检查一次 `tmux has-session -t <tmux_session_name>`、`tmux capture-pane -pt <tmux_session_name>` 和 `tail -n 100 <log_path>`。
5. 只要会话仍存在，就必须每 15 秒检查一次状态；每次记录最近日志摘要、已读取 score 文件数、score record 数、模型数、item 数，以及输出表是否已生成。
6. 会话结束后必须读取最终日志和 `EXIT_CODE`，校验 `item_parameters.csv`、`model_ability.csv`、`capability_mastery.csv`、`template_diagnostics.csv`、`item_level_findings.jsonl`、`cdm_irt_summary.json`、`cdm_irt_report.md`；缺少 15 秒监控记录、最终日志、退出码或真实分析产物时，不得向父节点报告完成。

## 实现方法

脚本使用 Python 标准库实现：

- 构建 `model x item` 响应矩阵。
- 使用 `score >= threshold` 二值化响应，同时保留原始 `mean_score`。
- IRT：输出 Rasch-style proxy。
  - `model theta proxy = logit((correct + 0.5) / (n + 1))`
  - `item difficulty proxy = -logit((correct_by_models + 0.5) / (n_models + 1))`
- 区分度：item 与模型总分去本题后的 point-biserial/Pearson 相关。
- CDM：从 `capability_tags`、`capability`、`capabilities`、`skills`、`question_format` 或 `template_id` 推断 Q-matrix 维度，按模型和能力维度聚合 mastery。
- 样本量门控：少于 `--min-models` 或 `--min-items` 时，`usable_for_full_irt=false`，结论仅作灰度诊断。

## 输出

写入：

```text
artifacts/data_21_grey_validation_report/cdm_irt_analysis/
  item_parameters.csv
  model_ability.csv
  capability_mastery.csv
  template_diagnostics.csv
  item_level_findings.jsonl
  cdm_irt_summary.json
  cdm_irt_report.md
  tmux_monitoring.jsonl
```

字段说明：

- `item_parameters.csv`：每题 p-value、Rasch 难度代理、point-biserial 区分度、诊断 flags。
- `model_ability.csv`：每模型 mean score、binary accuracy、theta proxy。
- `capability_mastery.csv`：每模型在每能力维度上的 mastery 状态。
- `template_diagnostics.csv`：模板级平均难度、平均区分度和 flag 计数。
- `item_level_findings.jsonl`：`too_easy`、`too_hard`、`low_discrimination`、`negative_discrimination`、`too_few_model_responses` 等 item 级问题。
- `cdm_irt_report.md`：面向人工审核的摘要。

## 阻塞与降级

- 没有任何 score file 或没有可用 score record 时，必须阻塞或标记 `usable_for_full_irt=false` 并报告原因。
- 模型数或题目数不足时不得输出“正式 IRT 已拟合”结论，只能输出 proxy 分析。
- 任一 item 的 score 缺失不会阻塞全局分析，但会影响该 item 的 `n_model_responses` 和 flags。
