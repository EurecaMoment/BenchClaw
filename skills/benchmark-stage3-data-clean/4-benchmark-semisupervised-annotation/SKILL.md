---
name: benchmark-semisupervised-annotation
description: "Stage 3 Phase 4：半监督候选标注生成。基于 cleaned_data 和 DATA_CLEANING_PLAN.md，对 existing_dataset 与 real_data 优先调用 ~/benchclaw/annotation-tool 下的 sam3、depthanything、yolo 等工具生成候选标注；simulator 默认不补标，只允许 audit_only 审计。Use when user says '半监督标注', 'pseudo annotation', '运行 sam3/depthanything/yolo', 'annotation-tool'."
argument-hint: [stage3-dir]
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

# 半监督候选标注生成（三类数据同一 Skill，并按 source 分目录）

面向：**$ARGUMENTS**

本 skill 只执行半监督候选标注或审计，不运行 Data-Juicer，不修改 Stage 2 原始数据，不把候选标注写成 GT。

## 中文优先原则

- 计划说明、运行报告、风险说明必须以中文为主。
- 英文只用于工具名、字段名、source type、路径名和 verdict。

## 重要约束

- 本 skill 是 Stage 3 的半监督标注专用 skill，服务于同一套 Stage3 流程，不为三类数据源拆成三套 skill。
- 默认处理对象是 `existing_dataset` 和 `real_data`，因为它们通常缺乏完整 GT。
- `simulator` 默认不运行半监督补标；只有 `DATA_CLEANING_PLAN.md` 或 `ANNOTATION_TOOL_PLAN.md` 明确写明 `audit_only` 时，才允许运行工具做 GT/图像一致性审计。
- 所有中间产物必须写入 `~/bench_workspace/workspace{i}/stage3/source_work/{source_type}/{source_name}/` 下对应子目录。
- 工具位置固定为 `~/benchclaw/annotation-tool`，除非用户显式覆盖 `ANNOTATION_TOOL_HOME`。

## 输入

必需：

- `~/bench_workspace/workspace{i}/stage3/DATA_CLEANING_PLAN.md`
- `~/bench_workspace/workspace{i}/stage3/cleaned_data/` 或 `~/bench_workspace/workspace{i}/stage3/source_work/{source_type}/{source_name}/cleaned_data/`
- `~/bench_workspace/workspace{i}/stage3/CLEANING_LINEAGE.jsonl`

可选：

- `~/bench_workspace/workspace{i}/stage3/ANNOTATION_TOOL_PLAN.md`
- `~/bench_workspace/workspace{i}/stage3/annotation_tool_configs/`
- `~/bench_workspace/workspace{i}/stage3/run_annotation_tools.sh`
- `ANNOTATION_TOOL_HOME=~/benchclaw/annotation-tool`

## 执行策略

### 已有数据集 `existing_dataset`

- 优先对缺失 mask、depth、detection、region grounding 等字段的样本运行工具。
- 可调用：
  - `sam3`：生成候选 mask、区域 proposal、实例轮廓。
  - `depthanything`：生成候选深度图或相对深度。
  - `yolo`：生成候选 bbox、类别和置信度。
- 输出必须写入 `source_work/existing_dataset/{source_name}/pseudo_annotations/`。
- 每条结果必须保留 `original_sample_id`、`annotation_provenance`、`derived_from_sample_id`。

### 真实数据 `real_data`

- 优先为 annotation gap 中列出的样本生成候选检测、分割、深度或区域提示。
- 输出必须写入 `source_work/real_data/{source_name}/pseudo_annotations/`。
- 每条结果必须标记 `annotation_review_status=needs_human_review`。
- 这些候选标注只能缩小人工复核范围，不得直接进入评测真值。

### 仿真器 `simulator`

- 默认跳过半监督补标，因为仿真器应使用程序/API 生成的 full GT。
- 仅当计划明确写明 `audit_only` 时，可以调用工具做一致性审计。
- 审计输出必须写入 `source_work/simulator/{source_name}/annotation_audit/`，不得写入 GT 字段，不得作为评分真值。

## 输出

- `~/bench_workspace/workspace{i}/stage3/source_work/{source_type}/{source_name}/pseudo_annotations/`（existing_dataset / real_data 按需）
- `~/bench_workspace/workspace{i}/stage3/source_work/{source_type}/{source_name}/annotation_audit/`（simulator audit_only 按需）
- `~/bench_workspace/workspace{i}/stage3/source_work/{source_type}/{source_name}/annotation_tool_logs/`
- `~/bench_workspace/workspace{i}/stage3/ANNOTATION_TOOL_RUN_REPORT.md`
- `~/bench_workspace/workspace{i}/stage3/ANNOTATION_LINEAGE.jsonl`

## 输出记录字段

每条候选标注或审计记录必须包含：

- `source_type`
- `source_name`
- `sample_id`
- `derived_from_sample_id`
- `annotation_tool`
- `tool_version_or_path`
- `annotation_output_path`
- `annotation_confidence`
- `annotation_status=pseudo_annotation` 或 `annotation_status=audit_annotation`
- `annotation_review_status=needs_human_review`
- `lineage_id`

## 完成标准

- `ANNOTATION_TOOL_RUN_REPORT.md` 已生成，记录每个 source 的执行、跳过或失败原因。
- `existing_dataset` 和 `real_data` 的工具输出均位于各自 `source_work/{source_type}/{source_name}/` 目录下。
- simulator 若存在工具输出，必须是 `audit_only`，且输出位于 `annotation_audit/`。
- 所有候选标注都有工具来源、置信度、review status 和 raw sample lineage。

## 规则

- 不把 `sam3`、`depthanything`、`yolo` 的输出当作 GT。
- 不覆盖 `cleaned_data/`、Stage 2 原始数据或原始 annotation。
- 不为 simulator 常规生成 pseudo GT。
- 若工具不可用，写入 `ANNOTATION_TOOL_RUN_REPORT.md`，将对应 source 标记为 `NEEDS_REVIEW`，不要伪造输出。
