---
name: benchclaw-stage3-real-image-cleaning
description: Use for the specific BenchClaw subskill `stage3-real-image-cleaning` only when its parent node explicitly dispatches to it.
---

## Opencode 子 agent 触发契约

本文件是 BenchClaw child skill module。父级 stage、node 或 pipeline 调度到本文件时，必须通过 opencode 命令 `/benchclaw-subskill` 启动隔离子 agent；该命令在 `BENCHCLAW_ROOT/opencode.json` 中配置为 `subtask: true`，并绑定 `mode: "subagent"` 的 `child-skill-module-runner`。禁止父级 manager 直接在自己的对话上下文中内联执行本文件步骤。

调用 `/benchclaw-subskill` 时必须传入：目标 `SKILL.md` 绝对路径、注册 skill 名、冻结的 `PROJECT_ROOT` / `BENCHCLAW_ROOT` / `WORKSPACE_PARENT` / `WORKSPACE_ROOT`、当前 node 或 work_unit id、已满足的输入 artifact 路径、期望输出 artifact 路径、父级 DAG 依赖与完成判据。子 agent 只返回 `status`、artifact 路径、证据摘要和 blockers，不回灌长日志或完整中间内容。

如果当前执行上下文不是 `/benchclaw-subskill` 产生的 `child-skill-module-runner` 子 agent，本文件不得继续执行；应立即返回 `BLOCKED`，说明必须由父级使用 `/benchclaw-subskill` 重新派发。

# Subskill — 真实图片清洗

## 作用域

本 subskill 只处理一个真实图片数据集 work unit。不要写入其他数据集目录，也不要直接写 `data_17` 根目录汇总文件。

## 输入

- `stage3_execution_plan`
- `dataset_id`
- `data_14_real_image_collection_bundle/datasets/<dataset_id>/`
- Stage2 的 `metadata.jsonl`、`annotation_requirements.yaml`、`source_manifest.json` 和媒体文件

## 处理

1. 必须先读取 `BENCHCLAW_ROOT/data-juicer_card/SKILL.md`，并按该卡的 Mandatory Workflow 执行；不得用纯手写逻辑替代 Data-Juicer。
2. 将 Stage2 per-dataset 记录整理成 Data-Juicer 可读的 `data_juicer/input_manifest.jsonl`。每行至少包含 `text`、`dataset_id`、样本 ID、媒体路径、来源字段和待标注需求；`text` 可由 caption、任务字段、metadata 摘要、标注需求等拼接而成。
3. 从 `templates/data_juicer_stage3_cleaning_template.yaml` 复制生成 `data_juicer/process.yaml`，把 `dataset_path` 与 `export_path` 替换成当前 work unit 的绝对路径；若 stage plan 明确需要更多合法 operator，可在读取 `data-juicer_card` 后调整 YAML。
4. 必须执行 Data-Juicer：

```bash
conda run -n data_juicer dj-process --config <current_work_unit>/data_juicer/process.yaml
```

若该命令不可用，只能使用 `data-juicer_card/SKILL.md` 允许的备用 source-run 命令。
5. 读取 Data-Juicer 输出，回填媒体存在性、可读性、重复样本、损坏样本和元数据字段完整性检查，产出可标注样本、不可用样本和需复核样本。
6. 保留 Stage2 来源信息，不覆盖原始 `source_card_skill`、原始图片 ID 或可追溯来源 ID。
7. 清洗剔除必须有 Data-Juicer 输出或显式校验原因；清洗结果只供同一 work unit 的 `annotation` subskill 消费。
8. 必须保存真实执行证明：`command.txt` 写入实际命令，`stdout.log`/`stderr.log` 保存运行日志，`exit_code.txt` 保存退出码，`run_manifest.json` 记录 Data-Juicer 版本、配置路径、输入输出路径、开始/结束时间和样本计数。退出码非 0、没有 `cleaned_manifest.jsonl` 或日志缺失时必须 BLOCKED。
9. `cleaned_items.jsonl` 与 `text_items.jsonl` 必须使用 workspace 相对媒体路径；每条记录至少包含 `record_id`、`dataset_id`、`source_item_id`、`workspace_media`、`text`、`source_card_skill`、`stage2_record_ref`、`cleaning_run_id` 和 `validation`。图片必须存在、非空、sha256 已记录且可解码。

## 输出

写入父节点分配的 per-dataset 目录：

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
invalid_items.jsonl
cleaning_report.md
```
