# Stage2 Collection Bundle Contract

本契约适用于 Stage2 的三类采集 bundle：

- `data_14_real_image_collection_bundle`
- `data_15_existing_benchmark_collection_bundle`
- `data_16_simulator_collection_bundle`

目标是把来源各异的数据规整为大致一致、可追溯、可校验的结构，同时保留数据源特有字段，避免为了统一格式而遗漏关键内容。

## 硬规则

1. 不能写 placeholder、dummy、fake、TODO、空 JSONL、空媒体文件或无法追溯来源的记录。
2. 媒体必须真实落盘到 `WORKSPACE_ROOT/stage2/artifacts/<data-id>/...` 内。后续阶段必须能在 workspace 内稳定读取，不能只保存外部绝对路径、URL、卡片说明或下载提示。
3. 图片类媒体必须校验文件存在、`size_bytes > 0`、sha256 非空、可被常用图像库解码，并记录 `width`、`height`、`mode/color_space`。解码失败必须阻塞或剔除并记录原因，不能进入有效样本。
4. 每条样本记录必须能追溯到数据卡/仿真器卡、原始样本 ID、原始路径或原始记录；若来源不可追溯，不能进入有效样本。
5. 允许字段宽松扩展，但不得丢失关键内容。无法归入标准字段的来源字段必须进入 `raw_record`、`source_fields` 或 `extra_metadata`。
6. 每个 per-dataset 或 per-simulator 目录必须先独立产出完整文件；根目录汇总只能在所有 work unit 完成后串行生成。
7. 对 `data_16_simulator_collection_bundle`，零图像/零渲染帧不是合法空结果；任何仿真器 work unit 在没有真实图像落盘时必须继续重试采集，不能写完成态，不能用 placeholder、历史缓存或手写媒体替代。
8. 除非用户请求或 `data_13_execution_plan` 明确写出其他采集规模、或明确禁用相关分支，Stage2 三个根 bundle 汇总后必须至少包含 100 张真实落盘、非空、可解码且 `decode_status: ok` 的图片或渲染帧；若另有要求，必须在 `stage2_execution_plan.yaml` 写明 `minimum_total_collected_images` 及原因。有效图片总数不足要求时，不得写 stage 完成态，必须继续采集或在报告中引用显式例外依据。

## 统一目录

每个 work unit 的隔离目录至少包含：

```text
media/ or observations/
media_manifest.jsonl
items.jsonl or metadata.jsonl or raw_items.jsonl
labels/GT/annotation requirement files
source_manifest.json
DATASET_REPORT.md or SIMULATOR_REPORT.md
```

根 bundle 目录汇总时必须保留同名汇总文件或语义等价文件，并保留 `datasets/<dataset_id>/...` 或 `simulators/<simulator_id>/<task_family>/...` 原始隔离输出。

## 统一样本 envelope

每条样本、观测或 benchmark item 记录至少使用以下 envelope。没有的字段填 `null`，但不能省略关键 provenance 和 media 信息：

```json
{
  "record_id": "stable unique id inside this bundle",
  "data_source_type": "real_image | existing_benchmark | simulator",
  "dataset_id": "real or benchmark dataset id, if applicable",
  "simulator_id": "simulator id, if applicable",
  "task_family": "task family, if applicable",
  "split": "train | val | test | unknown | custom",
  "sample_id": "source sample id",
  "source_card_skill": "card SKILL.md path",
  "source_uri": "original local path, URL, archive member, simulator run id, or official id",
  "workspace_media": ["workspace-relative media paths"],
  "media_ids": ["ids from media_manifest.jsonl"],
  "text": {},
  "structured_inputs": {},
  "official_labels": {},
  "gt_refs": {},
  "annotation_requirements": [],
  "source_fields": {},
  "raw_record": {},
  "extra_metadata": {},
  "provenance": {
    "acquired_at": "ISO-8601 timestamp if known",
    "license": "license or usage boundary if known",
    "download_or_run_command": "command/API/replay source if applicable",
    "checksum_source": "how checksums were computed"
  },
  "validation": {
    "media_landed": true,
    "required_fields_present": true,
    "decode_checked": true,
    "notes": []
  }
}
```

## 媒体 manifest

`media_manifest.jsonl` 每条记录至少包含：

```json
{
  "media_id": "stable unique id",
  "record_id": "linked item/observation id",
  "data_source_type": "real_image | existing_benchmark | simulator",
  "dataset_id": "if applicable",
  "simulator_id": "if applicable",
  "task_family": "if applicable",
  "role": "primary_image | context_image | rgb | depth | segmentation | mask | video | audio | point_cloud | document | other",
  "modality": "image | video | text | state | audio | point_cloud | other",
  "workspace_path": "path relative to artifact root",
  "original_uri": "source path/url/archive member/simulator output",
  "mime_type": "detected or inferred MIME type",
  "extension": "file extension",
  "sha256": "hex checksum",
  "size_bytes": 123,
  "width": 0,
  "height": 0,
  "frames": null,
  "channels": null,
  "color_space": null,
  "timestamp": null,
  "decode_status": "ok | failed | not_applicable",
  "validation_notes": []
}
```

图片媒体的 `width` 和 `height` 必须为正整数，`decode_status` 必须为 `ok`。非图片媒体也必须有 `sha256` 和 `size_bytes`。

## 质量门

写 `DONE.json` 前必须检查：

- 所有 JSONL 非空，除非执行计划明确允许该数据源为空。
- 每个样本引用的 `media_id` 都存在于 `media_manifest.jsonl`。
- 每个 `workspace_path` 指向真实存在且非空的文件。
- 图片文件可以解码，尺寸与 manifest 一致。
- 对仿真器 bundle，`observations/` 与 `media_manifest.jsonl` 至少包含一个真实、非空、可解码的图像或渲染帧；若计数为 0，必须继续重试采集，不得写 `DONE.json`。
- Stage2 最终完成门必须检查三个 terminal bundle 的图片/渲染帧总量是否达到 `stage2_execution_plan.yaml` 的 `minimum_total_collected_images`；若计划未显式覆盖，默认阈值为 100。
- source manifest 覆盖动态发现的所有 work unit、处理状态、输入卡片路径、输出目录、阻塞原因和汇总计数。
- 关键字段覆盖情况已记录：原始 ID、媒体、文本/问题、标签/GT、任务类型、split、许可或使用边界、来源路径。
