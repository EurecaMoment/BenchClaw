---
name: benchmark-weak-evidence-annotation
description: "Stage 3 Phase 4：弱感知候选标注生成。基于 evidence 和 EVIDENCE_COMPILATION_PLAN.md，对 existing_dataset 与 real_data 优先调用 BENCHCLAW_ROOT/annotation-tool 下的 sam3、depthanything、yolo 等工具生成候选标注；simulator 默认不补标，只允许 audit_only 审计。Use when user says '半监督标注', 'pseudo annotation', '运行 sam3/depthanything/yolo', 'annotation-tool'."
argument-hint: [stage3-dir]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob
metadata:
  openclaw:
    emoji: ""
    requires:
      bins: [python3]
---

## `BENCHCLAW_ROOT` 只读约束

- **BENCHCLAW_READONLY = true**：`BENCHCLAW_ROOT/` 只能作为 BenchClaw 仓库内共享只读资源根，必须从当前 skill 所在的 BenchClaw 仓库位置解析，不能依赖固定 home 路径或机器绝对路径。
- 严禁在 `BENCHCLAW_ROOT/` 下创建、编辑、覆盖、删除、移动、重命名、复制写入、初始化 git、提交、打 tag、写日志、写缓存或写临时文件。
- 所有派生产物、补丁、快照、报告、脚本、配置、日志和测试输出必须写入 active `WORKSPACE_ROOT`。
- 如必须修改 `BENCHCLAW_ROOT/` 中的资源，只能在 workspace 中生成 patch 或修改建议，等待用户在外部处理；当前 skill 不得直接应用。


## Workspace and File Access Boundary

This skill must operate only inside the current run workspace.

- Before reading or writing any run artifact, resolve and record the active `WORKSPACE_ROOT = ~/bench_workspace/workspace{i}` from the current task, parent stage, or pipeline state.
- Read and write only files under the active `WORKSPACE_ROOT` and the explicitly required global resource roots named by this skill, such as `BENCHCLAW_ROOT/simulatorCards/`, `BENCHCLAW_ROOT/benchmarkDatasetCards/`, `BENCHCLAW_ROOT/realdata_cards/`, `BENCHCLAW_ROOT/templates/`, `BENCHCLAW_ROOT/model_api/`, `BENCHCLAW_ROOT/data-juicer_card/`, `BENCHCLAW_ROOT/annotation-tool/`, or `BENCHCLAW_ROOT/skills/` when the current skill explicitly requires them.
- Never read, list, grep, summarize, compare, copy, or infer from any other `~/bench_workspace/workspace{j}` where `j != i`, even if the current artifact is missing or another workspace appears newer or more complete.
- Never scan broad server directories such as `~`, `/`, `/home`, `/mnt`, `/data`, `/tmp`, `C:\Users`, `C:\`, or arbitrary project/download folders to discover context. Only inspect the exact current workspace paths and exact allowlisted resource roots needed for this skill.
- If an expected input is missing from the active workspace or an allowlisted resource root, stop and report the missing path. Do not search unrelated folders or borrow replacement artifacts from another workspace.
- Outputs must be written only to the active `WORKSPACE_ROOT` paths declared by this skill. Do not mirror or cache run artifacts into other workspaces or unrelated server folders.
- If the user explicitly provides an external path, use it only when it is directly relevant to this skill, record it as a user-provided exception, and do not expand access to sibling or parent directories.

This boundary overrides convenience behaviors such as auto-discovery, resume from latest workspace, reuse of previous artifacts, broad recursive grep/list, and fallback search.

# 弱感知候选证据生成（三类数据同一 Skill，并按 source 分目录）

面向：**$ARGUMENTS**

本 skill 只执行弱感知候选证据生成或审计，不运行 Data-Juicer，不修改 Stage 2 原始数据，不把候选证据写成 GT。

## 中文优先原则

- 计划说明、运行报告、风险说明必须以中文为主。
- 英文只用于工具名、字段名、source type、路径名和 verdict。

## 重要约束

- 本 skill 是 Stage 3 的半监督标注专用 skill，服务于同一套 Stage3 流程，不为三类数据源拆成三套 skill。
- 默认处理对象是 `existing_dataset` 和 `real_data`，因为它们通常缺乏完整 GT。
- `simulator` 默认不运行半监督补标；只有 `EVIDENCE_COMPILATION_PLAN.md` 或 `ANNOTATION_TOOL_PLAN.md` 明确写明 `audit_only` 时，才允许运行工具做 GT/图像一致性审计。
- 所有中间产物必须写入 `~/bench_workspace/workspace{i}/stage3/source_work/{source_type}/{source_name}/` 下对应子目录。
- 工具位置固定为 `BENCHCLAW_ROOT/annotation-tool`，除非用户显式覆盖 `ANNOTATION_TOOL_HOME`。

## 置信度标注要求

- 弱感知候选证据的作用是补充置信度证据和缩小人工复核范围，不是生成可直接评分的真值。
- 每条候选证据必须记录工具置信度、阈值、失败/跳过原因、人工复核状态和原始样本 lineage。
- 低于计划阈值、缺少工具来源、缺少原图映射或无法解释的输出必须标记为 `NEEDS_REVIEW`，不得进入 Stage4 ready 依据。
- 对 simulator 的 audit 输出只能提升一致性审计置信度，不能提升或替代程序 GT 置信度。

## 输入

必需：

- `~/bench_workspace/workspace{i}/stage3/EVIDENCE_COMPILATION_PLAN.md`
- `~/bench_workspace/workspace{i}/stage3/evidence/` 或 `~/bench_workspace/workspace{i}/stage3/source_work/{source_type}/{source_name}/evidence/`
- `~/bench_workspace/workspace{i}/stage3/CLEANING_LINEAGE.jsonl`

可选：

- `~/bench_workspace/workspace{i}/stage3/ANNOTATION_TOOL_PLAN.md`
- `~/bench_workspace/workspace{i}/stage3/annotation_tool_configs/`
- `~/bench_workspace/workspace{i}/stage3/run_annotation_tools.sh`
- `ANNOTATION_TOOL_HOME=BENCHCLAW_ROOT/annotation-tool`

## 执行策略

### 已有数据集 `existing_dataset`

- 优先对缺失 mask、depth、detection、region grounding 等字段的样本运行工具。
- 可调用：
  - `sam3`：生成候选 mask、区域 proposal、实例轮廓。
  - `depthanything`：生成候选深度图或相对深度。
  - `yolo`：生成候选 bbox、类别和置信度。
- 输出必须写入 `source_work/existing_dataset/{source_name}/pseudo_annotations/`。
- 每条结果必须保留 `original_sample_id`、`annotation_provenance`、`derived_from_sample_id`。
- 若工具产生与原图不同的图片产物（如 YOLO 画框图、depth map、mask overlay、裁剪图或诊断可视化图），必须另存为派生图片，不得覆盖 evidence image 或 Stage2 原图。

### 真实数据 `real_data`

- 优先为 annotation gap 中列出的样本生成候选检测、分割、深度或区域提示。
- 输出必须写入 `source_work/real_data/{source_name}/pseudo_annotations/`。
- 每条结果必须标记 `annotation_review_status=needs_human_review`。
- 这些候选证据只能缩小人工复核范围，不得直接进入评测真值。
- 若工具产生与原图不同的图片产物，必须保存派生图片路径，并在候选标注记录中声明它来自哪个原图样本。

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
- `original_image_path`
- `derived_image_path`（若存在可视化、深度图、mask 图、裁剪图等派生图片）
- `derived_image_type`（如 `yolo_overlay`、`depth_map`、`mask_overlay`、`crop`、`diagnostic_render`）
- `metadata_update_required=true`（存在派生图片时必须为 true，供 final metadata 合并）
- `annotation_confidence`
- `confidence_threshold`
- `confidence_evidence`
- `review_reason`
- `annotation_status=pseudo_annotation` 或 `annotation_status=audit_annotation`
- `annotation_review_status=needs_human_review`
- `lineage_id`

## 完成标准

- `ANNOTATION_TOOL_RUN_REPORT.md` 已生成，记录每个 source 的执行、跳过或失败原因。
- `existing_dataset` 和 `real_data` 的工具输出均位于各自 `source_work/{source_type}/{source_name}/` 目录下。
- simulator 若存在工具输出，必须是 `audit_only`，且输出位于 `annotation_audit/`。
- 所有候选标注都有工具来源、置信度、review status 和 raw sample lineage。
- 所有候选标注都说明其对图文数据置信度的贡献、阈值判断和人工复核原因。

## 规则

- 不把 `sam3`、`depthanything`、`yolo` 的输出当作 GT。
- 不覆盖 `evidence/`、Stage 2 原始数据或原始 annotation。
- 不把画框图、深度图、mask overlay 等派生图片当作原图；这些图片只能作为 `processed_images` 进入最终 metadata 映射。
- 不为 simulator 常规生成 pseudo GT。
- 若工具不可用，写入 `ANNOTATION_TOOL_RUN_REPORT.md`，将对应 source 标记为 `NEEDS_REVIEW`，不要伪造输出。
---

## Fixed Artifact Format Contract

All artifacts produced by this skill have fixed file formats. The format block under `Expected Outputs`, `Output`, `Output Structure`, `Unified Output`, or the nearest equivalent output section is normative, not illustrative.

Mandatory rules:

- Produce every declared artifact at the exact declared path and with the exact declared extension. Do not rename, relocate, split, merge, or substitute artifacts unless this skill explicitly permits it.
- Markdown artifacts (`.md`) must keep the declared top-level title and section heading order exactly. Required tables must keep the declared column names and column order exactly. If a value is unknown, write `UNKNOWN`; if it is not applicable, write `N/A`; do not omit the row, section, or column.
- JSON artifacts (`.json`) must be valid UTF-8 JSON with a single top-level object unless this skill explicitly declares a top-level array. Required keys must always be present. Use `null`, `[]`, or `{}` for empty values instead of deleting keys.
- JSONL artifacts (`.jsonl`) must contain exactly one valid JSON object per non-empty line. Every line must share the same required key set declared by this skill or by the upstream schema.
- CSV/TSV artifacts must include a header row. Header names and order are fixed. Quote fields when needed and keep one logical record per row.
- YAML artifacts must be parseable YAML and must preserve the declared top-level keys. Generated config YAML must include enough comments or companion fields to trace each operator, field, or rule back to the source artifact named by this skill.
- Directory artifacts must contain the declared files plus a `MANIFEST.json` or `manifest.jsonl` when the skill declares one. The manifest must enumerate relative paths, artifact type, source_type/source_name when applicable, producer skill name, and creation timestamp.
- Validation or gate reports must include a fixed `verdict` value from `PASS`, `FAIL`, `WARNING`, `BLOCKED`, or `NEEDS_REVIEW`, plus `checked_artifacts`, `blocking_issues`, and `next_action` sections or keys.
- Handoff artifacts consumed by downstream skills must be backward-compatible: add optional fields only under an `extras` section/key, never by changing or deleting required fields.
- Before marking the skill complete, perform a format check against this contract and mention any deviation explicitly in the completion or gate report.
