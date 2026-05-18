# Skill 16 — 已有 Benchmark 数据采集

## 角色

本节点对应手绘图中的 **已有 benchmark → benchmark + 已有标注 + 期望标注** 分支。  
它负责采集已有 benchmark 的原始样本、官方 QA/label、split、license，并记录后续需要补充的标注字段。

## 依赖

```text
parents = ["13"]
```

## 允许读取

```text
WORKSPACE_ROOT/stage2/13-execution-plan-ingest/**
dataset_download_cache/benchmarks/**
user_provided_benchmark_roots/**
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
  benchmark_manifest.jsonl
  existing_labels_manifest.jsonl
  expected_extra_annotation_spec.json
  license_and_split_report.md
  raw/
  USED_INPUTS.json
  DONE.json
```

## benchmark_manifest.jsonl

每行一条样本：

```json
{
  "sample_id": "bench_000001",
  "benchmark_name": "",
  "raw_data_path": "raw/...",
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

## existing_labels_manifest.jsonl

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
2. 定位或下载已有 benchmark 原始样本。
3. 保留官方 label、QA、split、license。
4. 建立 sample_id 到 original_id 的映射。
5. 写期望额外标注规范。
6. 输出 manifest、label manifest 和 license/split report。

## DONE.json 格式

```json
{
  "node_id": "16",
  "status": "done",
  "outputs": [
    "benchmark_manifest.jsonl",
    "existing_labels_manifest.jsonl",
    "expected_extra_annotation_spec.json",
    "license_and_split_report.md"
  ],
  "terminal": true,
  "notes": ""
}
```
