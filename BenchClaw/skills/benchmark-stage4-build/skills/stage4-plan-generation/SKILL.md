---
name: benchclaw-stage4-plan-generation
description: Use for the specific BenchClaw node skill `stage4-plan-generation` only when its parent stage explicitly dispatches to it.
---

# Node Skill — 本阶段执行计划生成

## 输入

- `data_11_template_metric_initial_draft`
- `data_13_execution_plan`
- `data_17_annotated_real_image_bundle`
- `data_18_annotated_existing_benchmark_bundle`
- `data_19_annotated_simulator_bundle`

## 处理

1. 固化模板生成、指标生成、答案程序生成、灰度验证和全量合成的执行顺序。
2. 明确每类数据源可参与的模板集合和 GT 来源。
3. 写入 Stage4 计划。
4. 在 `stage4_execution_plan.yaml` 中显式写出灰度批量合成、无效题筛选、小批量实际评测、CDM/IRT 分析和全量批量合成的 tmux 执行策略；不得让这些命令以前台长跑方式执行。
5. 每个会长时间运行的 Stage4 work unit 必须包含：`tmux_required: true`、`monitor_interval_seconds: 15`、`monitor_until: session_finished`、`tmux_session_name`、`log_path`、`monitoring_log_path`、`output_dir` 和完成质量门。

## `stage4_execution_plan.yaml` 必填 tmux 策略

`nodes/stage4-plan-generation/stage4_execution_plan.yaml` 必须至少包含下列结构；字段可扩展，但不得删除 tmux 监控字段。

```yaml
tmux_execution_policy:
  required: true
  monitor_interval_seconds: 15
  monitor_until: session_finished
  session_name_template: benchclaw_s4_<node_id>_<task>_<YYYYMMDDHHMMSS>
  log_path_template: WORKSPACE_ROOT/stage4/nodes/<node_id>/run_logs/<task>.log
  monitoring_log_path_template: WORKSPACE_ROOT/stage4/nodes/<node_id>/run_logs/<task>.monitoring.jsonl
  completion_evidence_required:
    - tmux_session_name
    - command
    - log_path
    - monitoring_log_path
    - every_15_seconds_monitoring_records
    - final_log_tail
    - exit_status_or_exit_code_marker
    - output_manifest
long_running_work_units:
  - node_id: grey-batch-validation
    task: per-template-batch-synthesis
    tmux_required: true
    monitor_interval_seconds: 15
    monitor_until: session_finished
    output_dir: artifacts/data_21_grey_validation_report/per_template_batch/
  - node_id: grey-batch-validation
    task: invalid-item-screening
    tmux_required: true
    monitor_interval_seconds: 15
    monitor_until: session_finished
    output_dir: artifacts/data_21_grey_validation_report/invalid_item_screening/
  - node_id: grey-batch-validation
    task: small-batch-result-evaluation
    tmux_required: true
    monitor_interval_seconds: 15
    monitor_until: session_finished
    output_dir: artifacts/data_21_grey_eval_results/
  - node_id: grey-batch-validation
    task: cdm-irt-analysis
    tmux_required: true
    monitor_interval_seconds: 15
    monitor_until: session_finished
    output_dir: artifacts/data_21_grey_validation_report/cdm_irt_analysis/
  - node_id: full-synthesis
    task: full-benchmark-synthesis
    tmux_required: true
    monitor_interval_seconds: 15
    monitor_until: session_finished
    output_dir: artifacts/data_22_full_benchmark_dataset/
```

执行者必须按上述 work unit 创建 `run_logs/`，后台启动 tmux，并每 15 秒写一次 `monitoring_log_path`。任一 work unit 缺少 tmux 字段、15 秒监控记录、最终日志、退出码或真实输出 manifest 时，本节点计划必须视为不可执行，后续节点必须 BLOCKED。

## 输出

- `nodes/stage4-plan-generation/stage4_execution_plan.yaml`
- 节点执行记录文件
