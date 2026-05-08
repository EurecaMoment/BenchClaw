---
name: benchmark-batch-collect
description: "Stage 2 Phase 5：批量采集、接入、登记与质量检查。按 simulator、existing_dataset、real_data 三类数据源分别执行采集脚本、接入脚本和登记脚本，并生成 DATA_QUALITY_REPORT.md。Use when user says '开始采集', 'batch collect', '执行采集脚本', '批量接入数据'."
argument-hint: [stage2-context]
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

# 批量采集、接入、登记与质量检查（三类数据同一 Skill 并行）

面向：**$ARGUMENTS**

本 skill 执行 Stage 2 的实际数据落地和原始质量检查，不生成新模板，不执行 Stage 3 清洗。

重要约束：本 skill 是三类数据源共同使用的唯一 Phase 5 skill。不得拆成采集、接入、登记三套 skill；必须在同一次执行中并行处理 `simulator`、`existing_dataset`、`real_data`，并输出同一份 `DATA_QUALITY_REPORT.md`。

## 输入

必需：

- `~/bench_workspace/workspace{i}/stage2/COLLECTION_GUIDANCE_PLAN.md`
- `~/bench_workspace/workspace{i}/stage2/DATA_SCHEMA.md`

按 source_type 需要：

- `simulator`: `collect_scripts/simulator/{source_name}/`
- `existing_dataset`: `ingest_scripts/existing_dataset/{source_name}/`
- `real_data`: `register_scripts/real_data/{source_name}/`；若本轮没有真实数据源，`register_scripts/README.md` 必须说明未执行真实数据登记

可选：

- `~/bench_workspace/workspace{i}/stage2/templates/*.yaml`
- `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md`

## 三类执行方法

执行方式：按 `COLLECTION_GUIDANCE_PLAN.md` 中的优先级启动三类任务。能够并行执行时，应并行运行仿真器采集、数据集接入和真实数据登记；不能并行时，也必须在同一 Phase 5 中顺序完成三类处理，并在报告中注明执行方式。

### 仿真器 `simulator`

执行：

```text
python collect_scripts/simulator/{source_name}/collect.py --config config.yaml
```

质量检查：

- 场景数和帧数是否达到计划
- RGB / depth / segmentation / pose 等文件是否完整
- 每帧 observation 与 GT 是否对齐
- `GT_ALIGNMENT_THRESHOLD` 是否达标
- 异常帧：全黑、NaN depth、空标注、损坏文件
- 失败时使用 `resume_state.json` 补采

输出目录：

- `collected_data/simulator/{source_name}/`

目录细节必须包括：

- `images/{scene_or_town}/{shard_or_run}/...`：例如 CARLA 可按 `images/Town10HD_Opt/0/`、`images/Town10HD_Opt/1/` 分批存放
- `manifest.jsonl`：逐样本记录 `sample_id`、`scene_id`、`frame_id`、图片路径、GT 引用和采集配置
- `skipped_towns.json` 或等价跳过记录：仅当存在跳过 town/scene 时生成
- 运行日志写入 `logs/`，例如 `logs/carla_server.log`

### 已有数据集 `existing_dataset`

执行：

```text
python ingest_scripts/existing_dataset/{source_name}/ingest.py --mapping field_mapping.yaml
```

质量检查：

- 图片、QA、caption、label、metadata 路径是否存在
- 字段映射是否完整
- `original_sample_id` 是否唯一
- 是否有重复图片或重复 QA
- annotation provenance 是否保留
- 缺失字段是否标记为 `missing_or_derived`
- 不计算仿真器 GT 对齐率

输出目录：

- `collected_data/existing_dataset/{source_name}/`

目录细节必须包括：

- `images/`：接入后的图片或软链接
- `manifest.jsonl`：逐样本记录 `sample_id`、`original_sample_id`、字段映射、annotation provenance
- `ingest_errors.jsonl`：接入错误、缺失字段或跳过样本；即使为空也保留文件
- `question_type_histogram.json`：当数据集包含 QA 或 question type 字段时生成，用于检查问题类型分布

### 真实数据 `real_data`

执行：

```text
python register_scripts/real_data/{source_name}/register.py --config quality_config.yaml
```

质量检查：

- 图片是否可读、是否损坏
- 是否重复、模糊、过曝/欠曝、分辨率过低
- metadata 是否可抽取
- annotation gap 是否完整列出
- 是否存在需要人工复核的隐私、许可或质量风险
- 缺失 GT 不算失败，但必须标记为 `needs_annotation` 或 `not_observable`

输出目录：

- `collected_data/real_data/{source_name}/`

若本轮没有 `real_data` source，不得伪造 `collected_data/real_data/{source_name}/`；只需在 `DATA_QUALITY_REPORT.md` 和 `register_scripts/README.md` 中说明未选中真实数据源。

## DATA_QUALITY_REPORT.md 结构

```markdown
# Data Quality Report

## Source Summary
| Source Type | Source | Unit | Expected | Actual | Status |
|-------------|--------|------|----------|--------|--------|

## Simulator Quality
| Simulator | Scenes | Frames | GT Alignment Rate | Anomalies | Status |
|-----------|--------|--------|-------------------|-----------|--------|

## Existing Dataset Quality
| Dataset | Samples | Image/Text Valid | Duplicate Count | Missing Fields | Status |
|---------|---------|------------------|-----------------|----------------|--------|

## Real Data Quality
| Source | Images | Quality Pass | Annotation Gaps | Review Items | Status |
|--------|--------|--------------|-----------------|--------------|--------|

## Capability Coverage
| Capability Dimension | Source Type | Source | Available Data | Coverage | Notes |
|---------------------|-------------|--------|----------------|----------|-------|

## Remediation Actions
[补采、重新接入、人工复核、无法自动处理的事项]
```

## 完成标准

- 三类输出目录按 source_type 分开。
- 每个已选中的 source 都有 `manifest.jsonl`。
- 目录结构必须匹配 Stage 2 产物树：`collect_scripts/`、`ingest_scripts/`、`register_scripts/`、`collected_data/`、`logs/`、`templates/`、`unit_tests/`。
- 已有数据集 source 必须保留 `ingest_errors.jsonl`；有 QA/question type 时必须保留 `question_type_histogram.json`。
- 仿真器 source 必须在 `logs/` 中保留采集或服务日志；有 town/scene 跳过时必须保留跳过记录。
- 每个 source 都进入 `DATA_QUALITY_REPORT.md`。
- 仿真器通过 GT 对齐检查或标记 `NEEDS_REVIEW`。
- 已有数据集通过 schema / annotation consistency 检查或标记 `NEEDS_REVIEW`。
- 真实数据通过资产登记和质量检查；annotation gap 必须显式保留。
- 三类数据的质量结果合并到同一份 `DATA_QUALITY_REPORT.md`，不得拆分成互不关联的报告。

## 规则

- 不删除原始数据。
- 不覆盖 Stage 1 或 Stage 2 上游产物。
- 不对真实数据生成伪 GT。
- 不把 existing_dataset 的 QA/caption 当作仿真器真值。
