---
name: benchclaw-stage2-existing-benchmark-data-materialization
description: Use for the specific BenchClaw subskill `stage2-existing-benchmark-data-materialization` only when its parent node explicitly dispatches to it.
---

# Subskill — 已有 benchmark 数据物化

## 作用域

本 subskill 只物化一个 benchmark 数据集 work unit 的数据。不要写入其他数据集目录，也不要直接追加写 bundle 根目录下的汇总文件。

## 输入

- `dataset_id`
- `dataset_card_skill`
- `content-label-analysis` 产出的单数据集分析记录
- 数据集卡中声明的本地数据根、访问方式或授权数据目录

## tmux 采集监控硬约束

本 subskill 执行任何媒体复制/下载/解压、benchmark item 物化、官方标签导出、manifest 生成、校验或数据集卡声明的外部命令时，必须使用父节点传入的 `tmux_session_name`、`log_path`、`monitoring_log_path` 后台执行。

- 启动命令必须形如：`tmux new-session -d -s <tmux_session_name> "<command> > <log_path> 2>&1; printf '\nEXIT_CODE:%s\n' \$? >> <log_path>"`。
- 启动后立即检查一次 `tmux has-session -t <tmux_session_name>`、`tmux capture-pane -pt <tmux_session_name>` 和 `tail -n 100 <log_path>`。
- 只要会话仍在运行，必须每 15 秒检查一次采集状态并追加写 `monitoring_log_path`；检查必须持续到 tmux 会话结束。
- `DATASET_REPORT.md` 与 `source_manifest.json` 必须记录 tmux session、日志路径、每 15 秒监控摘要、最终退出状态、媒体计数、样本计数和标签计数；缺少这些证据时不得向父节点报告完成。

## 处理

1. 按当前 `dataset_card_skill` 定位原始媒体、样本元数据和官方标注。
2. 按 `templates/collection_bundle_contract.md` 规整 benchmark item。标准字段统一写入 envelope，benchmark 特有字段完整保留到 `raw_record`、`source_fields` 或 `extra_metadata`，不得因字段不匹配而丢弃问题文本、选项、上下文、媒体组、官方答案、评测 split 或任务类型。
3. 将后续 Stage3/Stage4 必须消费的媒体物化到 workspace 内稳定路径；不要只记录外部绝对路径。
4. 为每个落盘媒体写 `media_manifest.jsonl`。图片必须存在、非空、sha256 已记录、可解码，并记录宽高、通道或色彩模式；多图、多模态和视频帧必须保留顺序、角色和与题目的对应关系。
5. 将官方标注写入 `existing_labels.jsonl`，将样本索引写入 `raw_items.jsonl`，将新增标注需求写入 `new_annotation_requirements.yaml`。
6. 保留官方 label、原始元数据和新增语义描述的来源边界，不混写。
7. 若该数据集无法访问、格式与卡片不一致、许可不允许复用、媒体无法真实落盘或关键字段无法追溯，向父节点报告该数据集阻塞原因，由父节点写 `BLOCKED.json` 与 `BLOCKED.md`。

## 规整字段

`raw_items.jsonl` 每条记录必须包含统一 envelope 中的核心字段：

- `record_id`
- `data_source_type = existing_benchmark`
- `dataset_id`
- `split`
- `sample_id`
- `source_card_skill`
- `source_uri`
- `workspace_media`
- `media_ids`
- `text`
- `structured_inputs`
- `official_labels`
- `annotation_requirements`
- `source_fields`
- `raw_record`
- `extra_metadata`
- `provenance`
- `validation`

`existing_labels.jsonl` 必须通过 `record_id` 或 `sample_id` 与 `raw_items.jsonl` 对齐，并保留官方字段名、官方答案、标注来源、评测口径和任何不能归入标准字段的标签元数据。

## 反糊弄质量门

写入完成前必须检查：

- `raw_items.jsonl`、`existing_labels.jsonl` 和 `media_manifest.jsonl` 非空，除非执行计划明确允许该数据集某类内容为空。
- 每条含媒体样本引用的 `media_id` 都存在，并指向 workspace 内真实存在且非空的文件。
- 图片文件可解码，manifest 中尺寸与实际尺寸一致。
- benchmark 的关键输入没有丢失：问题/指令/上下文、媒体引用、候选项或结构化输入、官方答案/标签、任务类型、split、来源 ID。
- 不存在值为 `placeholder`、`dummy`、`fake`、`TODO`、`N/A` 且被当作有效关键字段的记录。
- 样本计数、媒体计数、标签计数、失败/剔除计数写入 `source_manifest.json` 和 `DATASET_REPORT.md`。

## 输出

只写入当前数据集的隔离目录：

```text
artifacts/data_15_existing_benchmark_collection_bundle/datasets/<dataset_id>/
  media/
  run_logs/
  media_manifest.jsonl
  raw_items.jsonl
  existing_labels.jsonl
  new_annotation_requirements.yaml
  source_manifest.json
  DATASET_REPORT.md
```

每条 JSONL 记录必须包含：

- `dataset_id`
- `source_card_skill`
- 原始样本 ID 或官方 ID
- workspace 内媒体路径或相对路径
- `raw_record` 或 `source_fields` 中的原始关键字段
