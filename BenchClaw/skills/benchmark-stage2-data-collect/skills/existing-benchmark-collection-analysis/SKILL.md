# Node Skill — 已有 benchmark 采集与分析

## 内部层级

本节点包含两个 subskill，按每个已有 benchmark 独立运行：

```text
subskills/content-label-analysis/SKILL.md
subskills/data-materialization/SKILL.md
```

## 输入

- `stage2_execution_plan.yaml`
- 已有 benchmark 卡、下载记录、用户授权数据目录

## 处理

1. 分析已有 benchmark 的内容、字段、媒体、官方标注、许可与可复用边界。
2. 将可用样本、媒体、官方标注、新增标注需求物化到 workspace。
3. 保留官方 label 与新增语义描述的来源边界，不混写。

## 输出

- `artifacts/data_15_existing_benchmark_collection_bundle/media/`
- `artifacts/data_15_existing_benchmark_collection_bundle/raw_items.jsonl`
- `artifacts/data_15_existing_benchmark_collection_bundle/existing_labels.jsonl`
- `artifacts/data_15_existing_benchmark_collection_bundle/new_annotation_requirements.yaml`
- `artifacts/data_15_existing_benchmark_collection_bundle/source_manifest.json`
- 节点执行记录文件
