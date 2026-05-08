---
name: benchmark-template-refinement
description: "Stage 2 Phase 3：模板与 schema 修整。按 simulator、existing_dataset、real_data 三类数据源分别生成或修整评测模板和字段约束。Use when user says '修整模板', 'template refinement', '对齐评测模板'."
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

# 模板与 Schema 修整（三类数据同一 Skill 并行）

面向：**$ARGUMENTS**

本 skill 只修整模板与 schema，不生成脚本、不采集数据。

重要约束：本 skill 是三类数据源共同使用的唯一 Phase 3 skill。不得拆成 simulator template skill、dataset template skill、real-data template skill；必须在同一次执行中并行生成三类模板，并用同一份 `TEMPLATE_REFINEMENT_REPORT.md` 汇总。

## 输入

必需：

- `~/bench_workspace/workspace{i}/stage1/EVALSET_PROTOTYPE.md`
- `~/bench_workspace/workspace{i}/stage2/SOURCE_CAPABILITY_SURVEY.md`
- `~/bench_workspace/workspace{i}/stage2/COLLECTION_GUIDANCE_PLAN.md`

可选：

- workspace `templates/`
- `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md`

## 三类数据模板策略

执行方式：读取 `COLLECTION_GUIDANCE_PLAN.md` 中全部 source，按 `source_type` 并行修整模板。模板可以按 source 分文件输出，但报告必须统一，字段角色和状态枚举必须一致。

### 仿真器 `simulator`

- 模板必须列出可采集 GT 字段。
- 坐标系、单位、图像格式、depth/segmentation/pose 格式必须明确。
- 对仿真器不能提供的必需字段，标记 `N/A` 或 `missing_gt`，并说明原因。
- 输出模板可用于采集脚本生成。

### 已有数据集 `existing_dataset`

- 模板必须包含原始数据集字段到 benchmark 字段的映射。
- 保留 `original_sample_id`、`original_split`、`annotation_provenance`。
- QA、caption、label、metadata 等字段标记为 `provided_annotation`。
- 缺失字段不得删除，应标记为 `missing_or_derived`。
- 若字段需要格式转换，写明转换规则。

### 真实数据 `real_data`

- 模板必须包含图片路径、metadata、质量检查字段和标注占位字段。
- 缺失真值字段标记为 `needs_annotation` 或 `not_observable`。
- 允许 `pseudo_annotation` 字段，但必须与 GT 字段分开。
- 输出模板主要用于登记、人工复核和后续构建阶段。

## 输出

- `~/bench_workspace/workspace{i}/stage2/TEMPLATE_REFINEMENT_REPORT.md`
- `~/bench_workspace/workspace{i}/stage2/templates/{source_type}_{source_name}_EVAL_TEMPLATE.yaml`

## YAML 模板必须包含

```yaml
source_type: simulator | existing_dataset | real_data
source_name: ...
source_path: ...
capability_dimensions: []
sample_id_fields: []
modalities: []
fields:
  - name: ...
    role: observation | gt | provided_annotation | metadata | annotation_gap | pseudo_annotation
    required: true | false
    availability: full_gt | partial_gt | provided_annotation | missing_or_derived | needs_annotation | not_observable
    format: ...
    notes: ...
```

## 报告结构

```markdown
# Template Refinement Report

## Summary
| Source Type | Source | Template File | Added Fields | Missing Fields | Notes |

## Simulator Template Changes
[GT 字段、格式、坐标系、API 依赖]

## Existing Dataset Schema Mapping
[原字段 -> benchmark 字段，annotation provenance]

## Real Data Registration Schema
[metadata、quality flags、annotation gaps]

## Unresolved Conflicts
[无法自动对齐的字段和建议]
```

## 完成标准

- `COLLECTION_GUIDANCE_PLAN.md` 中每个 source 都有模板。
- 每个模板含 `source_type`。
- 缺失字段保留状态，不被静默删除。
- existing_dataset 和 real_data 不被伪装成 simulator 模板。
- 三类模板使用同一套字段角色和状态枚举，汇总在同一份报告中。
