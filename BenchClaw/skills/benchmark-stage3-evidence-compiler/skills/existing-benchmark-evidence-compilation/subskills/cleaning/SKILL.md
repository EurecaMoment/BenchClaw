# Subskill — 已有 benchmark 数据清洗

## 作用域

本 subskill 只处理一个已有 benchmark 数据集 work unit。不要写入其他数据集目录，也不要直接写 `data_18` 根目录汇总文件。

## 输入

- `stage3_execution_plan`
- `dataset_id`
- `data_15_existing_benchmark_collection_bundle/datasets/<dataset_id>/`
- Stage2 的 `raw_items.jsonl`、`existing_labels.jsonl`、`new_annotation_requirements.yaml`、`source_manifest.json`

## 处理

1. 必须先读取 `BENCHCLAW_ROOT/data-juicer_card/SKILL.md`，并按该卡的 Mandatory Workflow 执行；不得用纯手写逻辑替代 Data-Juicer。
2. 将 Stage2 per-dataset 记录整理成 Data-Juicer 可读的 `data_juicer/input_manifest.jsonl`。每行至少包含 `text`、`dataset_id`、官方样本 ID、媒体路径、官方 label 摘要、任务字段和新增标注需求；`text` 可由题干、答案字段、label 文本、metadata 摘要和新增标注需求拼接。
3. 从 `templates/data_juicer_stage3_cleaning_template.yaml` 复制生成 `data_juicer/process.yaml`，把 `dataset_path` 与 `export_path` 替换成当前 work unit 的绝对路径；若 stage plan 明确需要更多合法 operator，可在读取 `data-juicer_card` 后调整 YAML。
4. 必须执行 Data-Juicer：

```bash
conda run -n data_juicer dj-process --config <current_work_unit>/data_juicer/process.yaml
```

若该命令不可用，只能使用 `data-juicer_card/SKILL.md` 允许的备用 source-run 命令。
5. 读取 Data-Juicer 输出后，再校验样本、媒体、官方标签字段、任务字段和来源记录的一致性。
6. 保留官方样本 ID、官方 label、来源数据集卡和许可边界。
7. 将官方可复用标签写成 `official_labels.jsonl`，将需要默认标注补充的样本单独列出到 `new_annotation_targets.jsonl`。
8. 官方 label 与新增标注需求不得混写。
9. 必须保存真实执行证明：`command.txt` 写入实际命令，`stdout.log`/`stderr.log` 保存运行日志，`exit_code.txt` 保存退出码，`run_manifest.json` 记录 Data-Juicer 版本、配置路径、输入输出路径、开始/结束时间和样本计数。退出码非 0、没有 `cleaned_manifest.jsonl` 或日志缺失时必须 BLOCKED。
10. `cleaned_items.jsonl` 与 `text_items.jsonl` 必须使用 workspace 相对媒体路径；每条记录至少包含 `record_id`、`dataset_id`、`source_item_id`、`workspace_media`、`text`、`official_label_refs`、`source_card_skill`、`stage2_record_ref`、`cleaning_run_id` 和 `validation`。图片必须存在、非空、sha256 已记录且可解码；无图片样本必须明确记录可消费文本字段和原因。

## 输出

写入当前 per-dataset 目录：

```text
data_juicer/input_manifest.jsonl
data_juicer/process.yaml
data_juicer/cleaned_manifest.jsonl
data_juicer/command.txt
data_juicer/stdout.log
data_juicer/stderr.log
data_juicer/exit_code.txt
data_juicer/run_manifest.json
cleaned_items.jsonl
text_items.jsonl
official_labels.jsonl
new_annotation_targets.jsonl
invalid_items.jsonl
cleaning_report.md
```
