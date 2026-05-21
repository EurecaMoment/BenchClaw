# Skill 15 — 真实图片数据采集

全局路径约束：`BENCHCLAW_ROOT` 仅作只读输入；`WORKSPACE_ROOT` 是本次流程唯一总工作目录，所有写操作和流程产物只能落在其下。

## 角色

本节点对应手绘图中的 **真实图片 → 真实图片 + 期望标注** 分支。  
它负责收集真实图片，并记录这些图片后续在 Stage3 需要做什么半监督标注。  
本节点不制造 GT，也不让 LLM 直接标注为事实。

本节点必须严格受 13 号节点导出的 `execution_plan.md` 与 `stage2_collection_targets.json` 指导，只能实际处理其中 `real_image_targets` 明确选中的真实数据源；不得脱离 13 的采集目标自行扩展、替换、猜测或补充新的真实图片数据集。

本节点只能处理 `BENCHCLAW_ROOT/realDataCards/**/SKILL.md` 中声明并指向的真实数据集或真实图片来源；不得采集 cards 目录之外未登记的数据源，不得把任意用户路径、临时目录、搜索结果或未建卡的数据集写入本节点产物。

## 依赖

```text
parents = ["13"]
```

## 允许读取

```text
WORKSPACE_ROOT/stage2/13-execution-plan-ingest/**
WORKSPACE_ROOT/config/stage2_input_paths.json
BENCHCLAW_ROOT/realDataCards/**
```

## 禁止读取

```text
WORKSPACE_ROOT/stage2/14-simulator-skill-registry/**
WORKSPACE_ROOT/stage2/16-existing-benchmark-acquisition/**
WORKSPACE_ROOT/stage2/17-simulator-multimodal-gt-acquisition/**
```

## 必须输出

```text
WORKSPACE_ROOT/stage2/stage2.db
WORKSPACE_ROOT/stage2/15-real-image-acquisition/
  images/
  realdata/
    <real_scene_or_source>/
      ...materialized image files...
  real_image_manifest.sqlite_export.jsonl
  expected_annotation_spec.json
  acquisition_report.md
  USED_INPUTS.json
  DONE.json
```

## SQLite canonical storage

本节点的规范化记录应写入 `WORKSPACE_ROOT/stage2/stage2.db` 的 `real_image_records` 表。`real_image_manifest.sqlite_export.jsonl` 仅作为兼容性导出，不再是唯一真相源。

## real_image_manifest.sqlite_export.jsonl

每行一条图片记录：

```json
{
  "sample_id": "real_000001",
  "image_path": "realdata/<real_scene_or_source>/real_000001.jpg",
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
2. 将 13 中声明的 `real_image_targets` 逐项绑定到 `BENCHCLAW_ROOT/realDataCards/**/SKILL.md` 中实际存在且被明确指向的数据集/图片来源；若目标无法映射到 card，节点必须阻塞。
3. 仅对这些已映射且被 13 选中的 realDataCards 数据源执行实际采集/物化，并按 `real_image_flow_policy=full_selected_dataset` 全量纳入其图文数据；不得处理未被 13 选中的来源，也不得在 Stage2 自行做二次抽样缩减。
4. 去重：至少计算文件 hash。
5. 记录 license、来源、分辨率、模态、采集上下文。
6. 只写“期望标注字段”，不写未经验证的 GT。
7. 将后续 Stage3/Stage4 需要消费的真实图像稳定物化到 `realdata/<real_scene_or_source>/` 下；`images/` 可作为兼容性索引或轻量入口，但 manifest 中应优先引用 `realdata/` 子树中的真实文件。允许复制、硬链接或其他在 workspace 内可复现的方式，但不得只在 manifest 中保留外部绝对路径。
8. 输出 manifest 和 report。

## 强制约束

- `stage2.db.real_image_records` 中的 `image_path` 必须优先指向 `WORKSPACE_ROOT/stage2/15-real-image-acquisition/realdata/` 下按真实场景或稳定来源分层保存的已物化文件；若同时保留 `images/` 入口，也不得只在 `images/` 中保存少量示例图。
- `stage2.db.real_image_records` 中每条记录都必须能追溯到：`13` 中被选中的 `real_image_targets` 之一，以及 `BENCHCLAW_ROOT/realDataCards/**/SKILL.md` 中的某个已登记真实数据源；不得出现无法回溯到这两者的样本。
- 不得只写 `source_path`、`raw_source_path`、样本统计或 `manifest_truncated` 说明而省略真实图像物化。
- 对被 13 选中的真实图片数据，Stage2 必须把后续需要消费的图像全量落盘到 `WORKSPACE_ROOT/stage2/15-real-image-acquisition/realdata/` 下，不得只保存代表图、抽样图、缩略图或样例集。
- 若 `stage2_collection_targets.json` 已声明某个真实数据源被选中，本节点不得再以“体量过大”“先取代表样本”“先跑一部分”为理由缩减其图文数据；除非上游 Stage1 明确写了更强的用户限制，否则必须按全量执行。
- 若 13 未选择任何真实图片目标，或目标无法映射到 `BENCHCLAW_ROOT/realDataCards/**` 中的已登记数据源，本节点必须阻塞，不得自行改写采集范围或写 `DONE.json`。
- 若受存储限制无法全量复制，必须显式记录采用的稳定物化方式（如硬链接）并确保后续 stage 在不访问外部目录的情况下仍可消费这些文件；否则节点必须阻塞，不得写 `DONE.json`。

## DONE.json 格式

```json
{
  "node_id": "15",
  "status": "done",
  "outputs": [
    "images/",
    "real_image_manifest.sqlite_export.jsonl",
    "expected_annotation_spec.json",
    "acquisition_report.md"
  ],
  "terminal": true,
  "notes": ""
}
```
