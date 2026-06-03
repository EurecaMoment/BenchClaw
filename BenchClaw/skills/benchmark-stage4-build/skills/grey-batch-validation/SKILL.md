# Node Skill — 小批量合成灰度验证

## 内部层级

```text
subskills/per-template-batch-synthesis/SKILL.md
subskills/invalid-item-screening/SKILL.md
subskills/small-batch-result-evaluation/SKILL.md
subskills/cdm-irt-analysis/SKILL.md
```

## 输入

- `data_20_template_metric_code_bundle`
- Stage3 三类已标注数据

## tmux 后台灰度合成与实际评测监控硬约束

本节点的四个内部 subskill 都必须按 `stage4_execution_plan.yaml` 的 `tmux_execution_policy` 后台执行，并把 stdout/stderr、15 秒监控记录和最终退出状态写入 `WORKSPACE_ROOT/stage4/nodes/grey-batch-validation/run_logs/`。不得在前台长期运行灰度合成、模型推理、评分或 CDM/IRT 分析。

1. 每个 subskill 启动命令必须使用：

```text
tmux new-session -d -s <tmux_session_name> "<command> > <log_path> 2>&1; printf '\nEXIT_CODE:%s\n' \$? >> <log_path>"
```

2. 启动后立即检查一次：`tmux has-session -t <tmux_session_name>`、`tmux capture-pane -pt <tmux_session_name>`、`tail -n 100 <log_path>`。
3. 只要 tmux 会话仍存在，就必须每 15 秒检查一次状态；任一活跃会话两次检查间隔不得超过 15 秒。
4. 每次检查必须追加写入 `monitoring_log_path`，记录 `timestamp`、`tmux_session_name`、`task`、`status`、最近 pane 输出摘要、最近 100 行日志摘要，以及当前已落盘 item、valid item、prediction、score、CDM/IRT 产物计数。
5. 会话结束后必须读取最终日志和 `EXIT_CODE`，校验对应输出目录非空且 manifest/report 可追溯；缺少 15 秒监控记录、最终日志、退出码或真实灰度产物时，不得写本节点 `DONE.json`。

## 处理

1. 按每个模板的灰度配额进行小批量合成。
2. 检查媒体存在性、GT 可计算性、答案唯一性、选项干扰项合理性、评分函数可执行性。
3. 对小批量合成数据集抽样、调用配置模型推理、打分并汇总模型 x 题型评测结果。
4. 对通过灰度验证的模板记录保留原因；对失败模板记录失败原因、修复建议和是否剔除。
5. 可执行 CDM/IRT 统计分析时，记录样本量、估计条件、结论适用范围。
6. `NODE_REPORT.md` 必须汇总每个 subskill 的 `tmux_session_name`、`log_path`、`monitoring_log_path`、开始/结束时间、退出码、每 15 秒监控记录摘要和产物计数。

## 输出

- `artifacts/data_21_grey_validation_report/report.md`
- `artifacts/data_21_grey_validation_report/template_status.csv`
- `artifacts/data_21_grey_validation_report/item_level_findings.jsonl`
- `artifacts/data_21_grey_eval_results/**/model_question_format_scores.csv`
- `artifacts/data_21_grey_eval_results/**/model_overall_scores.csv`
- 节点执行记录文件
