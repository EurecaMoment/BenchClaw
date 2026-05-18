# Skill 15 — 真实图片数据采集

## 角色

本节点对应手绘图中的 **真实图片 → 真实图片 + 期望标注** 分支。  
它负责收集真实图片，并记录这些图片后续在 Stage3 需要做什么半监督标注。  
本节点不制造 GT，也不让 LLM 直接标注为事实。

## 依赖

```text
parents = ["13"]
```

## 允许读取

```text
WORKSPACE_ROOT/stage2/13-execution-plan-ingest/**
user_provided_real_image_roots/**
dataset_download_cache/real_images/**
```

## 禁止读取

```text
WORKSPACE_ROOT/stage2/14-simulator-skill-registry/**
WORKSPACE_ROOT/stage2/16-existing-benchmark-acquisition/**
WORKSPACE_ROOT/stage2/17-simulator-multimodal-gt-acquisition/**
```

## 必须输出

```text
WORKSPACE_ROOT/stage2/15-real-image-acquisition/
  images/
  real_image_manifest.jsonl
  expected_annotation_spec.json
  acquisition_report.md
  USED_INPUTS.json
  DONE.json
```

## real_image_manifest.jsonl

每行一条图片记录：

```json
{
  "sample_id": "real_000001",
  "image_path": "images/real_000001.jpg",
  "source": "user_provided|public_dataset|camera_capture",
  "license": "unknown|...",
  "capture_metadata": {},
  "target_dimensions": [],
  "expected_annotation_fields": [],
  "gt_status": "not_available",
  "provenance": {
    "raw_source_path": "",
    "hash_sha256": ""
  }
}
```

## expected_annotation_spec.json

必须写明 Stage3 需要标注的字段，例如：

```json
{
  "object_detection": true,
  "instance_segmentation": true,
  "depth_estimation": true,
  "camera_geometry": true,
  "spatial_relations": true,
  "forbidden_as_gt": ["LLM free-form captions without verification"]
}
```

## 执行步骤

1. 从 13 的 `stage2_collection_targets.json` 中读取真实图片目标。
2. 定位或采集真实图片。
3. 去重：至少计算文件 hash。
4. 记录 license、来源、分辨率、模态、采集上下文。
5. 只写“期望标注字段”，不写未经验证的 GT。
6. 输出 manifest 和 report。

## DONE.json 格式

```json
{
  "node_id": "15",
  "status": "done",
  "outputs": [
    "images/",
    "real_image_manifest.jsonl",
    "expected_annotation_spec.json",
    "acquisition_report.md"
  ],
  "terminal": true,
  "notes": ""
}
```
