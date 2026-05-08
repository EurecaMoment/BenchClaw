---
name: benchmark-sim-capability-survey
description: "Stage 2 Phase 1：数据源能力与资产盘点。名称保留 simulator survey 以兼容旧调用，但本 skill 必须同时盘点 simulator、existing_dataset、real_data 三类数据源。Use when user asks to survey simulator GT capability, inventory datasets, or inspect real-data assets."
argument-hint: [stage1-dir]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob
metadata:
  openclaw:
    emoji: ""
    requires:
      bins: [python3]
---


## Workspace and File Access Boundary

This skill must operate only inside the current run workspace.

- Before reading or writing any run artifact, resolve and record the active `WORKSPACE_ROOT = ~/bench_workspace/workspace{i}` from the current task, parent stage, or pipeline state.
- Read and write only files under the active `WORKSPACE_ROOT` and the explicitly required global resource roots named by this skill, such as `~/benchclaw/simulator_cards/`, `~/benchclaw/dataset_cards/`, `~/benchclaw/realdata_cards/`, `~/benchclaw/templates/`, `~/benchclaw/model_api/`, `~/benchclaw/data-juicer_card/`, `~/benchclaw/annotation-tool/`, or `~/benchclaw/skills/` when the current skill explicitly requires them.
- Never read, list, grep, summarize, compare, copy, or infer from any other `~/bench_workspace/workspace{j}` where `j != i`, even if the current artifact is missing or another workspace appears newer or more complete.
- Never scan broad server directories such as `~`, `/`, `/home`, `/mnt`, `/data`, `/tmp`, `C:\Users`, `C:\`, or arbitrary project/download folders to discover context. Only inspect the exact current workspace paths and exact allowlisted resource roots needed for this skill.
- If an expected input is missing from the active workspace or an allowlisted resource root, stop and report the missing path. Do not search unrelated folders or borrow replacement artifacts from another workspace.
- Outputs must be written only to the active `WORKSPACE_ROOT` paths declared by this skill. Do not mirror or cache run artifacts into other workspaces or unrelated server folders.
- If the user explicitly provides an external path, use it only when it is directly relevant to this skill, record it as a user-provided exception, and do not expand access to sibling or parent directories.

This boundary overrides convenience behaviors such as auto-discovery, resume from latest workspace, reuse of previous artifacts, broad recursive grep/list, and fallback search.

# 数据源能力与资产盘点（三类数据同一 Skill 并行）

面向：**$ARGUMENTS**

本 skill 是单一职责模块：只做数据源盘点，不制定采集方案、不修模板、不生成脚本、不实际采集。

重要约束：本 skill 是三类数据源共同使用的唯一 Phase 1 skill。不得为 `simulator`、`existing_dataset`、`real_data` 另建三个盘点 skill；必须在同一次执行中并行盘点三类来源，并写入同一个 `SOURCE_CAPABILITY_SURVEY.md`。

## 中文优先原则

- 报告正文、判断理由、缺口说明使用中文。
- `source_type`、`source_name`、`GT`、`API`、`manifest` 等字段名可保留英文。

## 输入

必需：

- `~/bench_workspace/workspace{i}/stage1/DATA_SOURCE_MAPPING.md`
- `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md`

可选：

- `~/benchclaw/simulator_cards/`
- `~/benchclaw/dataset_cards/`
- `~/benchclaw/realdata_cards/`
- `~/benchclaw/simulators/`
- `~/benchclaw/datasets/`
- `~/benchclaw/realdatas/`

若 `DATA_SOURCE_MAPPING.md` 缺失，立即停止。

## 三类数据源盘点方法

执行方式：先读取 `DATA_SOURCE_MAPPING.md` 中全部 source，然后按三类 source_type 分组并行盘点。若工具环境不支持真实并行，也必须在同一次 Phase 1 中完成三组盘点，并在输出中保留三类结果。

### 1. 仿真器 `simulator`

目标：盘点程序可获取的真值 GT。

必须记录：

- 仿真器名称、版本、环境依赖、启动方式
- 可生成的观测：RGB、depth、normal、segmentation、optical flow、多视角图像等
- 可生成的几何真值：相机内外参、物体 6DoF、bbox、point cloud、mesh
- 可生成的物理/交互真值：碰撞、力/力矩、关节状态、动作成功/失败、状态变化日志
- 可生成的导航真值：可达区域、最短路径、拓扑图
- API / 方法、格式、坐标系、精度、采样限制
- 环境是否 ready，以及缺失依赖

### 2. 已有数据集 `existing_dataset`

目标：盘点已有图片、QA 对、caption、label、metadata 等可复用标注。

必须记录：

- 数据集名称、路径、卡片来源、split/subset
- 文件结构、图片路径字段、文本字段、QA 字段、caption 字段、label 字段
- annotation provenance：标注来自原数据集、人工、脚本、模型，还是未知
- 与 benchmark schema 的可映射字段
- 不可映射或缺失的字段，标记为 `missing_or_derived`
- 样本规模、重复情况、已知质量问题、许可/访问限制（若可获得）

注意：已有数据集中的标注是 `provided_annotation`，不是仿真器级 `full_gt`，除非数据集本身明确提供完整真值。

### 3. 真实数据 `real_data`

目标：盘点真实图片或不完整记录的可用信息和标注缺口。

必须记录：

- 数据来源名称、路径、采集场景、采集设备或未知状态
- 图片数量、分辨率、格式、EXIF/metadata 可用性
- 是否有局部标注、弱标注、文字描述或外部记录
- 缺失 GT 字段，标记为 `needs_annotation` 或 `not_observable`
- 需要人工复核的字段和优先级
- 质量风险：模糊、曝光、重复、损坏、隐私/许可风险（若可判断）

注意：真实数据不得把估计结果写成真值；如后续需要模型辅助 caption，应标记为 `pseudo_annotation`。

## 输出

主输出：

- `~/bench_workspace/workspace{i}/stage2/SOURCE_CAPABILITY_SURVEY.md`

兼容输出：

- `~/bench_workspace/workspace{i}/stage2/SIM_CAPABILITY_SURVEY.md`，仅包含 `source_type=simulator` 的摘要；若没有仿真器，写明“无仿真器来源，本文件仅为兼容占位”。

## 输出结构

```markdown
# Source Capability Survey

## Source Overview
| Source Type | Source Name | Path/Card | Capability Dimensions | Status |
|-------------|-------------|-----------|-----------------------|--------|

## Simulator GT Inventory
| Simulator | GT Type | Format | Coordinate System | API/Method | Limitation |
|-----------|---------|--------|-------------------|------------|------------|

## Existing Dataset Inventory
| Dataset | Modalities | Annotation Fields | Sample Count | Schema Mapping | Missing Fields |
|---------|------------|-------------------|--------------|----------------|----------------|

## Real Data Inventory
| Source | Modalities | Metadata | Sample Count | Annotation Gap | Review Priority |
|--------|------------|----------|--------------|----------------|-----------------|

## Cross-Source Coverage
| Capability Dimension | Simulator Coverage | Existing Dataset Coverage | Real Data Coverage | Recommendation |
|---------------------|--------------------|---------------------------|-------------------|----------------|

## Blocking Issues
[缺失卡片、路径不可读、环境不可用、标注缺口等]
```

## 完成标准

- 所有 `DATA_SOURCE_MAPPING.md` 中出现的数据源都有盘点条目。
- 每个条目都有 `source_type`、`source_name`、`source_path`、`gt_availability`、`annotation_status`。
- 仿真器列出可程序获取的 GT。
- 已有数据集列出可复用标注和缺失字段。
- 真实数据列出可用 metadata 和 annotation gap。
- 三类数据源写入同一个 `SOURCE_CAPABILITY_SURVEY.md`，不得拆成三份互不相干的报告。

## 规则

- 不生成采集计划、模板、脚本或数据质量报告。
- 不修改 Stage 1 文件。
- 信息来自推断时必须标注“推断”。
- 卡片信息和实际文件冲突时，优先记录冲突并说明证据。
