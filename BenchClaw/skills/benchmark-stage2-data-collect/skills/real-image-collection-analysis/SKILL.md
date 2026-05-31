# Node Skill — 真实图片采集与分析

## 内部层级

本节点包含两个 subskill，按每个真实图片数据集独立运行：

```text
subskills/content-analysis/SKILL.md
subskills/data-structure-normalization/SKILL.md
```

## 输入

- `stage2_execution_plan.yaml`
- 真实图片数据源卡或用户授权的真实图片目录

## 处理

1. 对每个真实图片数据集执行内容分析。
2. 将媒体文件、元数据、来源记录、标注需求物化到 workspace。
3. 不只记录外部路径；后续 Stage3 必需消费的媒体必须可在 workspace 内稳定访问。

## 输出

- `artifacts/data_14_real_image_collection_bundle/media/`
- `artifacts/data_14_real_image_collection_bundle/metadata.jsonl`
- `artifacts/data_14_real_image_collection_bundle/annotation_requirements.yaml`
- `artifacts/data_14_real_image_collection_bundle/source_manifest.json`
- 节点执行记录文件
