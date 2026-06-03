# Subskill — 仿真器数据清洗

## 作用域

本 subskill 只处理一个仿真器 work unit。不要写入其他 work unit，也不要直接写 `data_19` 根目录汇总文件。

## 输入

- `stage3_execution_plan`
- `work_unit_id`
- `data_16_simulator_collection_bundle` 中对应的观测、状态日志、GT、场景配置和 seed

## 处理

1. 必须先读取 `BENCHCLAW_ROOT/data-juicer_card/SKILL.md`，并按该卡的 Mandatory Workflow 执行；不得用纯手写逻辑替代 Data-Juicer。
2. 将当前 work unit 的观测索引、状态日志、动作记录、场景配置、seed、环境版本和 GT 摘要整理成 Data-Juicer 可读的 `data_juicer/input_manifest.jsonl`。每行至少包含 `text`、`work_unit_id`、step/episode ID、观测路径、状态字段摘要和 GT 来源摘要；`text` 可由状态字段、任务说明、事件描述、metadata 摘要拼接。
3. 从 `templates/data_juicer_stage3_cleaning_template.yaml` 复制生成 `data_juicer/process.yaml`，把 `dataset_path` 与 `export_path` 替换成当前 work unit 的绝对路径；若 stage plan 明确需要更多合法 operator，可在读取 `data-juicer_card` 后调整 YAML。
4. 必须执行 Data-Juicer：

```bash
conda run -n data_juicer dj-process --config <current_work_unit>/data_juicer/process.yaml
```

若该命令不可用，只能使用 `data-juicer_card/SKILL.md` 允许的备用 source-run 命令。
5. 读取 Data-Juicer 输出后，再校验观测媒体、状态日志、动作记录、场景配置、seed 和环境版本是否齐全。
6. 对齐 observation timestamp、state timestamp、action step 和 GT step。
7. 剔除或标记损坏观测、不完整 episode、不可复现 seed 和字段冲突。
8. 不得修改 Stage2 原始 collection bundle。
9. 必须保存真实执行证明：`command.txt` 写入实际命令，`stdout.log`/`stderr.log` 保存运行日志，`exit_code.txt` 保存退出码，`run_manifest.json` 记录 Data-Juicer 版本、配置路径、输入输出路径、开始/结束时间、仿真器/环境版本和样本计数。退出码非 0、没有 `cleaned_manifest.jsonl` 或日志缺失时必须 BLOCKED。
10. `cleaned_observation_index.jsonl` 与 `text_items.jsonl` 必须使用 workspace 相对观测路径；每条记录至少包含 `record_id`、`work_unit_id`、`simulator_id`、`task_family`、`scenario_id`、`seed`、`step_or_episode_id`、`workspace_observations`、`text`、`stage2_run_ref`、`cleaning_run_id` 和 `validation`。图片观测必须存在、非空、sha256 已记录且可解码。

## 输出

写入当前 work unit 目录：

```text
data_juicer/input_manifest.jsonl
data_juicer/process.yaml
data_juicer/cleaned_manifest.jsonl
data_juicer/command.txt
data_juicer/stdout.log
data_juicer/stderr.log
data_juicer/exit_code.txt
data_juicer/run_manifest.json
observations/
cleaned_state_logs.jsonl
cleaned_observation_index.jsonl
text_items.jsonl
invalid_steps.jsonl
cleaning_report.md
```
