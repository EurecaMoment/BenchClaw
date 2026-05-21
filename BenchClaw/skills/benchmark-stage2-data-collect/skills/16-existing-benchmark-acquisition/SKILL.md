# Skill 16 — 已有 Benchmark 数据采集

全局路径约束：`BENCHCLAW_ROOT` 仅作只读输入；`WORKSPACE_ROOT` 是本次流程唯一总工作目录，所有写操作和流程产物只能落在其下。

## 角色

本节点对应手绘图中的 **已有 benchmark → benchmark + 已有标注 + 期望标注** 分支。  
它负责采集已有 benchmark 的原始样本、官方 QA/label、split、license，并记录后续需要补充的标注字段。

本节点必须严格受 13 号节点导出的 `execution_plan.md` 与 `stage2_collection_targets.json` 指导，只能实际处理其中 `existing_benchmark_targets` 明确选中的 benchmark 数据集；不得脱离 13 的采集目标自行扩展、替换、猜测或补充新的 benchmark 数据集。

本节点只能处理 `BENCHCLAW_ROOT/benchmarkDatasetCards/**/SKILL.md` 中声明并指向的数据集；不得下载、引用或登记 cards 目录之外未建卡的 benchmark 数据集，也不得把任意外部 parquet/压缩包/镜像路径直接冒充为已登记 benchmark 来源。

## 依赖

```text
parents = ["13"]
```

## 允许读取

```text
WORKSPACE_ROOT/stage2/13-execution-plan-ingest/**
WORKSPACE_ROOT/config/stage2_input_paths.json
BENCHCLAW_ROOT/benchmarkDatasetCards/**
```

## 禁止读取

```text
WORKSPACE_ROOT/stage2/14-simulator-skill-registry/**
WORKSPACE_ROOT/stage2/15-real-image-acquisition/**
WORKSPACE_ROOT/stage2/17-simulator-multimodal-gt-acquisition/**
```

## 必须输出

```text
WORKSPACE_ROOT/stage2/16-existing-benchmark-acquisition/
  benchmark_manifest.sqlite_export.jsonl
  existing_labels_manifest.sqlite_export.jsonl
  expected_extra_annotation_spec.json
  license_and_split_report.md
  raw/
  benchmarkdataset/
    <dataset_name>/
      <existing_dataset_split_or_category>/
        ...materialized samples and media...
  USED_INPUTS.json
  DONE.json
```

## SQLite canonical storage

本节点的规范化记录应写入 `WORKSPACE_ROOT/stage2/stage2.db` 的 `benchmark_records` 与 `benchmark_label_records` 表。`benchmark_manifest.sqlite_export.jsonl` 与 `existing_labels_manifest.sqlite_export.jsonl` 仅作为兼容性导出，不再是唯一真相源。

## benchmark_manifest.sqlite_export.jsonl

每行一条样本：

```json
{
  "sample_id": "bench_000001",
  "benchmark_name": "",
  "raw_data_path": "benchmarkdataset/<dataset_name>/<existing_dataset_split_or_category>/...",
  "modalities": ["image", "text"],
  "question": "",
  "answer": "",
  "split": "train|val|test|unknown",
  "target_dimensions": [],
  "official_label_available": true,
  "license": "",
  "provenance": {
    "source_url_or_path": "",
    "original_id": "",
    "hash_sha256": ""
  }
}
```

## existing_labels_manifest.sqlite_export.jsonl

只记录已有官方 label / QA / metadata，不新造标签：

```json
{
  "sample_id": "bench_000001",
  "label_type": "answer|bbox|segmentation|metadata|trajectory",
  "label_value_path_or_inline": "",
  "label_source": "official_benchmark",
  "confidence": 1.0
}
```

## expected_extra_annotation_spec.json

说明 Stage3 需要补什么，例如：

```json
{
  "needs_depth": true,
  "needs_object_boxes": true,
  "needs_instance_masks": false,
  "needs_spatial_relation_graph": true,
  "do_not_overwrite_official_labels": true
}
```

## 执行步骤

1. 从 13 的 `stage2_collection_targets.json` 读取已有 benchmark 目标。
2. 将 13 中声明的 `existing_benchmark_targets` 逐项绑定到 `BENCHCLAW_ROOT/benchmarkDatasetCards/**/SKILL.md` 中实际存在且被明确指向的数据集；若目标无法映射到 card，节点必须阻塞。
3. 仅对这些已映射且被 13 选中的 benchmarkDatasetCards 数据集执行实际采集/物化，并按 `existing_benchmark_flow_policy=full_selected_dataset` 全量纳入其图文数据；不得处理未被 13 选中的 benchmark，也不得在 Stage2 自行做二次抽样缩减。
4. 保留官方 label、QA、split、license。
5. 建立 sample_id 到 original_id 的映射。
6. 写期望额外标注规范。
7. 将后续 Stage3/Stage4 需要消费的原始样本、图像和官方标签物化到 `benchmarkdataset/<dataset_name>/<existing_dataset_split_or_category>/` 下；`raw/` 可作为兼容性索引或总入口，但 manifest 中应优先引用 `benchmarkdataset/` 子树中的真实文件。目录层级应优先复用数据集内部已有的 split/category/subset，而不是 Stage2 自行发明分类。不得只保留数据集元信息、外部下载目录位置或 parquet 路径。
8. 输出 manifest、label manifest 和 license/split report。

## 强制约束

- `stage2.db.benchmark_records` 与 `stage2.db.benchmark_label_records` 中引用的样本必须能在 `WORKSPACE_ROOT/stage2/16-existing-benchmark-acquisition/benchmarkdataset/` 下被直接解析与消费；若同时保留 `raw/` 入口，也不得只在 `raw/` 中保存少量示例样本。
- `stage2.db.benchmark_records` 中每条记录都必须能追溯到：`13` 中被选中的 `existing_benchmark_targets` 之一，以及 `BENCHCLAW_ROOT/benchmarkDatasetCards/**/SKILL.md` 中的某个已登记 benchmark 数据集；不得出现无法回溯到这两者的样本。
- 不得用“已知 benchmark 名称 + 外部数据位置 + 字段说明”冒充样本采集完成。
- 对被 13 选中的 benchmark 图像型数据，Stage2 必须把后续需要消费的图像/样本全量落盘到 `WORKSPACE_ROOT/stage2/16-existing-benchmark-acquisition/benchmarkdataset/` 下，不得只保存样例集、摘要集或部分代表样本。
- 若 `stage2_collection_targets.json` 已声明某个已有 benchmark 数据集被选中，本节点不得再以“规模太大”“先取 benchmark 子集”“仅保留部分 split”为理由缩减其图文数据；除非上游 Stage1 明确写了更强的用户限制，否则必须按全量执行。
- 若 13 未选择任何已有 benchmark 目标，或目标无法映射到 `BENCHCLAW_ROOT/benchmarkDatasetCards/**` 中的已登记数据集，本节点必须阻塞，不得自行改写采集范围或写 `DONE.json`。
- 若受 license 或体积限制不能全量物化，必须在 workspace 内提供可复现的受控副本、索引和最小必要媒体资产；否则节点必须阻塞。

## DONE.json 格式

```json
{
  "node_id": "16",
  "status": "done",
  "outputs": [
    "benchmark_manifest.sqlite_export.jsonl",
    "existing_labels_manifest.sqlite_export.jsonl",
    "expected_extra_annotation_spec.json",
    "license_and_split_report.md"
  ],
  "terminal": true,
  "notes": ""
}
```
