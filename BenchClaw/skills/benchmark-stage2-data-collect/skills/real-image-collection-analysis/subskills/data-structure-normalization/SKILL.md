---
name: benchclaw-stage2-real-image-data-structure-normalization
description: Use for the specific BenchClaw subskill `stage2-real-image-data-structure-normalization` only when its parent node explicitly dispatches to it.
---

# Subskill — 真实图片数据结构整理

## 作用域

本 subskill 只整理一个真实图片数据集 work unit 的数据。不要写入其他数据集目录，也不要直接追加写 bundle 根目录下的汇总文件。

## 输入

- `dataset_id`
- `real_data_card_skill`
- `content-analysis` 产出的单数据集分析记录
- 数据卡中声明的本地数据根、访问方式或授权媒体目录

## tmux 采集监控硬约束

本 subskill 执行任何媒体复制/下载/解压、样本规整、manifest 生成、校验或数据卡声明的外部命令时，必须使用父节点传入的 `tmux_session_name`、`log_path`、`monitoring_log_path` 后台执行。

- 启动命令必须形如：`tmux new-session -d -s <tmux_session_name> "<command> > <log_path> 2>&1; printf '\nEXIT_CODE:%s\n' \$? >> <log_path>"`。
- 启动后立即检查一次 `tmux has-session -t <tmux_session_name>`、`tmux capture-pane -pt <tmux_session_name>` 和 `tail -n 100 <log_path>`。
- 只要会话仍在运行，必须每 15 秒检查一次采集状态并追加写 `monitoring_log_path`；检查必须持续到 tmux 会话结束。
- `DATASET_REPORT.md` 与 `source_manifest.json` 必须记录 tmux session、日志路径、每 15 秒监控摘要、最终退出状态、媒体计数和样本计数；缺少这些证据时不得向父节点报告完成。

## 处理

1. 按当前 `real_data_card_skill` 定位原始媒体、元数据和来源记录。
2. 按 `templates/collection_bundle_contract.md` 规整样本。标准字段统一写入 envelope，数据集特有字段完整保留到 `raw_record`、`source_fields` 或 `extra_metadata`，不得因字段不匹配而丢弃关键内容。
3. 将后续 Stage3/Stage4 必须消费的媒体物化到 workspace 内稳定路径；不要只记录外部绝对路径。
4. 为每个落盘媒体写 `media_manifest.jsonl`。图片必须存在、非空、sha256 已记录、可解码，并记录宽高、通道或色彩模式。
5. 将样本元数据写入 `metadata.jsonl`，将新增标注需求写入 `annotation_requirements.yaml`，将来源和校验信息写入 `source_manifest.json`。
6. 写入校验和、路径索引和来源记录，确保每个 workspace 媒体文件能追溯到原始图片。
7. 若该数据集无法访问、格式与卡片不一致、授权不允许复用、图片无法真实落盘或关键字段无法追溯，向父节点报告该数据集阻塞原因，由父节点写 `BLOCKED.json` 与 `BLOCKED.md`。

## 规整字段

`metadata.jsonl` 每条记录必须包含统一 envelope 中的核心字段：

- `record_id`
- `data_source_type = real_image`
- `dataset_id`
- `sample_id`
- `source_card_skill`
- `source_uri`
- `workspace_media`
- `media_ids`
- `structured_inputs`
- `annotation_requirements`
- `source_fields`
- `raw_record`
- `extra_metadata`
- `provenance`
- `validation`

不要把来源中不认识的字段丢掉；把它们放入 `source_fields` 或 `raw_record`，并在 `DATASET_REPORT.md` 中说明字段映射覆盖情况。

## 反糊弄质量门

写入完成前必须检查：

- `metadata.jsonl` 和 `media_manifest.jsonl` 非空，除非执行计划明确允许该数据集为空。
- 每条 `metadata.jsonl` 至少引用一个真实存在的 `media_id`。
- 每个 `workspace_path` 指向 workspace 内真实存在且非空的文件。
- 图片文件可解码，manifest 中尺寸与实际尺寸一致。
- 不存在值为 `placeholder`、`dummy`、`fake`、`TODO`、`N/A` 且被当作有效关键字段的记录。
- 样本计数、媒体计数、失败/剔除计数写入 `source_manifest.json` 和 `DATASET_REPORT.md`。

## 输出

只写入当前数据集的隔离目录：

```text
artifacts/data_14_real_image_collection_bundle/datasets/<dataset_id>/
  media/
  run_logs/
  media_manifest.jsonl
  metadata.jsonl
  annotation_requirements.yaml
  source_manifest.json
  DATASET_REPORT.md
```

每条 `metadata.jsonl` 记录必须包含：

- `dataset_id`
- `source_card_skill`
- 原始图片 ID 或可追溯来源 ID
- workspace 内媒体路径或相对路径
- `raw_record` 或 `source_fields` 中的原始关键字段
