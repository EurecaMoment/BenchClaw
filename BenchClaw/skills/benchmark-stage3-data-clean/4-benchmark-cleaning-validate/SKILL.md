---
name: benchmark-cleaning-validate
description: "Stage 3 Phase 5：三类数据同一套清洗与半监督标注验证及最终合并。并行验证 simulator、existing_dataset、real_data 的分流中间结果、GT/annotation 保护、pseudo annotation 状态、schema 兼容性和追溯链完整性，并合并为 Stage4 输入。Use when user says '验证清洗结果', 'cleaning validate', '检查 cleaned data'."
argument-hint: [stage3-dir]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob
metadata:
  openclaw:
    emoji: ""
    requires:
      bins: [python3]
---

## `~/benchclaw` 只读约束

- **BENCHCLAW_READONLY = true**：`~/benchclaw/` 只能作为共享只读资源根。
- 严禁在 `~/benchclaw/` 下创建、编辑、覆盖、删除、移动、重命名、复制写入、初始化 git、提交、打 tag、写日志、写缓存或写临时文件。
- 所有派生产物、补丁、快照、报告、脚本、配置、日志和测试输出必须写入 active `WORKSPACE_ROOT`。
- 如必须修改 `~/benchclaw/` 中的资源，只能在 workspace 中生成 patch 或修改建议，等待用户在外部处理；当前 skill 不得直接应用。


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

# 清洗验证（三类数据同一 Skill 并行）

面向：**$ARGUMENTS**

本 skill 验证清洗结果和半监督候选标注，并将三条线的结果合并为 Stage4 输入；不重新运行 Data-Juicer 或 annotation-tool，不修改原始数据。

## 重要约束

本 skill 是三类数据源共同使用的唯一 Phase 5 skill。不得拆成三套验证 skill；必须在同一份 `CLEANING_QUALITY_REPORT.md` 中并行验证三类数据并给出统一 verdict，然后写出 `final/` 下的合并结果。

## 置信度门禁要求

- 本阶段必须把“图文数据置信度是否足以进入 Stage4”作为核心 verdict 依据。
- 只有当样本具备可追溯原图/元数据、质量检查结果、图文或标注一致性证据、copy-only 字段保护证据、必要的人工复核状态时，才能写入 `stage4_ready_status=ready`。
- 任何样本如果缺少置信度证据、只有工具候选标注但无人审、annotation provenance 不完整、图文对应关系可疑或质量检查失败，必须标记为 `NEEDS_REVIEW` 或 rejected。
- `CLEANING_QUALITY_REPORT.md` 必须按 source 总结置信度提升证据，而不仅是文件存在性检查。

## 输入

必需：

- `~/benchclaw/data-juicer_card/DATAJUICER_AGENT_CAPABILITY_SPEC.md`
- `~/bench_workspace/workspace{i}/stage3/cleaned_data/`
- `~/bench_workspace/workspace{i}/stage3/source_work/`
- `~/bench_workspace/workspace{i}/stage3/rejected_samples/`
- `~/bench_workspace/workspace{i}/stage3/CLEANING_LINEAGE.jsonl`
- `~/bench_workspace/workspace{i}/stage3/DATAJUICER_RUN_REPORT.md`
- `~/bench_workspace/workspace{i}/stage2/DATA_SCHEMA.md`
- `~/bench_workspace/workspace{i}/stage2/templates/*.yaml`

若 Data-Juicer 清洗产物无法追溯到 `DATAJUICER_AGENT_CAPABILITY_SPEC.md`，验证 verdict 不能为 PASS。

可选：

- `~/bench_workspace/workspace{i}/stage3/ANNOTATION_TOOL_RUN_REPORT.md`
- `~/bench_workspace/workspace{i}/stage3/source_work/{source_type}/{source_name}/pseudo_annotations/`
- `~/bench_workspace/workspace{i}/stage3/source_work/{source_type}/{source_name}/annotation_tool_logs/`

## 三类验证策略

验证必须优先读取 `source_work/{source_type}/{source_name}/` 下的中间产物；根目录 `cleaned_data/`、`rejected_samples/` 只能作为兼容镜像。

### 仿真器 `simulator`

- 验证 GT 字段未被修改。
- 验证 cleaned sample 能回溯到 raw scene/frame。
- 验证 depth、pose、mask、trajectory 等引用仍可读。
- 验证维度覆盖没有因清洗被破坏。
- 若存在 simulator pseudo annotation，验证其必须是 `audit_only` 审计结果，且仅用于一致性检查或异常发现，未覆盖仿真器 GT。

### 已有数据集 `existing_dataset`

- 验证 `original_sample_id`、split、annotation provenance 保留。
- 验证 QA/caption/label 清洗后仍和图片对应。
- 验证缺失字段仍标记为 `missing_or_derived`。
- 验证去重和过滤原因可解释。
- 若存在 annotation-tool 输出，验证其标记为 `pseudo_annotation`，并保留原始 annotation provenance。

### 真实数据 `real_data`

- 验证 raw image 路径和 metadata 可追溯。
- 验证 quality flags 和 rejected reason 合理。
- 验证 annotation gap 未丢失。
- 若关键标注仍缺失，样本可通过登记质量验证，但 benchmark scoring 状态必须是 `NEEDS_REVIEW`。
- 若存在 `sam3`、`depthanything`、`yolo` 输出，验证其包含 `annotation_tool`、`annotation_confidence`、`annotation_review_status=needs_human_review`。

## 输出

- `~/bench_workspace/workspace{i}/stage3/CLEANED_DATA_SCHEMA.md`
- `~/bench_workspace/workspace{i}/stage3/CLEANING_QUALITY_REPORT.md`
- `~/bench_workspace/workspace{i}/stage3/cleaning_audit_sample/`
- `~/bench_workspace/workspace{i}/stage3/final/cleaned_data/`
- `~/bench_workspace/workspace{i}/stage3/final/cleaned_data/{source_type}/{source_name}/images/{sample_id}.{ext}`
- `~/bench_workspace/workspace{i}/stage3/final/cleaned_data/{source_type}/{source_name}/metadata/{sample_id}.json`
- `~/bench_workspace/workspace{i}/stage3/final/cleaned_data/{source_type}/{source_name}/processed_images/{sample_id}_{derived_type}.{ext}`（按需）
- `~/bench_workspace/workspace{i}/stage3/final/rejected_samples/`
- `~/bench_workspace/workspace{i}/stage3/final/pseudo_annotations/`（按需）
- `~/bench_workspace/workspace{i}/stage3/final/CLEANED_DATA_SCHEMA.md`
- `~/bench_workspace/workspace{i}/stage3/final/CLEANING_LINEAGE.jsonl`
- `~/bench_workspace/workspace{i}/stage3/final/ANNOTATION_LINEAGE.jsonl`（按需）
- `~/bench_workspace/workspace{i}/stage3/final/STAGE4_INPUT_MANIFEST.jsonl`

## 合并策略

- 从 `source_work/simulator/{source_name}/cleaned_data/`、`source_work/existing_dataset/{source_name}/cleaned_data/`、`source_work/real_data/{source_name}/cleaned_data/` 汇总样本。
- 统一写入 `final/cleaned_data/{source_type}/{source_name}/`，保持 source_type 和 source_name 层级。
- 每个 source 的 final cleaned_data 目录必须包含 `images/`、`metadata/`，并在存在派生图片时包含 `processed_images/`。
- 每个进入 Stage4 的样本必须写出一张最终标准图片 `images/{sample_id}.{ext}` 和一个同 basename 的 `metadata/{sample_id}.json`；二者必须一一对应。
- 若清洗或标注工具产生与原图不同的图片（如 YOLO 画框、深度图、mask overlay、裁剪/增强/诊断图），必须同时保留原图/标准图和派生图。派生图写入 `processed_images/{sample_id}_{derived_type}.{ext}`，并在 `metadata/{sample_id}.json` 的 `processed_images[]` 中记录。
- `metadata/{sample_id}.json` 必须包含 `original_image_path`（Stage2 原图路径）、`final_image_path`（final/images 路径）、`record_json_path`（Stage2 单图 JSON）、`processed_images`（派生图数组）、`cleaned_path`、`lineage_id`、`confidence_evidence`、`confidence_status`、`review_reason`、`stage4_ready_status`。
- 合并 rejected samples 到 `final/rejected_samples/{source_type}_{source_name}_rejected.jsonl`。
- 合并半监督候选标注到 `final/pseudo_annotations/{source_type}/{source_name}/`，但 simulator 的 `audit_only` 输出只能作为审计附件，不能进入评分 GT 字段。
- 生成 `final/STAGE4_INPUT_MANIFEST.jsonl`，每条样本必须包含 `source_type`、`source_name`、`sample_id`、`image_path`、`original_image_path`、`final_image_path`、`record_json_path`、`metadata_json_path`、`processed_image_paths`、`cleaned_path`、`gt_availability`、`annotation_status`、`pseudo_annotation_path`（如有）、`lineage_id`、`confidence_evidence`、`confidence_status`、`review_reason`、`stage4_ready_status`。
- `image_path` 与 `record_json_path` 必须继承 Stage 2 的一一对应关系：图片位于 `collected_data/{source_type}/{source_name}/images/{sample_id}.{ext}`，JSON 位于 `collected_data/{source_type}/{source_name}/records/{sample_id}.json`，二者 basename 必须等于 `sample_id`。
- `image_path` 为兼容字段，必须等于或可追溯到 `original_image_path`；Stage4 新逻辑应优先读取 `final_image_path` 和 `metadata_json_path`。
- `processed_image_paths` 必须为数组；没有派生图片时写 `[]`，不得省略字段。
- 若某 source 验证为 `FAIL`，不得把该 source 写入 `stage4_ready_status=ready`。

## 报告结构

```markdown
# Cleaning Quality Report

## Verdict
PASS / NEEDS_REVIEW / FAIL

## Per-Source Retain Rate
| Source Type | Source | Raw | Cleaned | Rejected | Retain Rate | Status |

## Simulator GT Preservation
[GT 字段、对齐链、引用文件检查]

## Existing Dataset Annotation Preservation
[原始 ID、split、annotation provenance、图文一致性]

## Real Data Annotation Gap Preservation
[quality flags、metadata、annotation gaps、review priority]

## Semi-Supervised Annotation Validation
[annotation-tool 路径、工具输出、pseudo annotation 字段、置信度、人工复核状态、未覆盖 GT/原始标注的证据]

## Confidence Improvement Evidence
| Source Type | Source | Confidence Dimension | Evidence Artifact | Result | Stage4 Impact |

## Schema Compatibility
[Stage 4 所需字段是否满足]

## Data-Juicer Spec Compliance
[是否读取 `~/benchclaw/data-juicer_card/DATAJUICER_AGENT_CAPABILITY_SPEC.md`、配置/执行是否符合 spec、operator 是否可追溯、是否存在 CONFIG_SPEC_MISMATCH]

## Known Limitations
[仍需人工复核或 waiver 的事项]
```

## 完成标准

- 三类数据验证结果写入同一份报告。
- 三类中间产物按 `source_work/{source_type}/{source_name}/` 分开验证。
- Data-Juicer operator、配置和执行记录可追溯到 `DATAJUICER_AGENT_CAPABILITY_SPEC.md`。
- Stage4 调用所需的合并产物写入 `final/`。
- 每个 cleaned/rejected 样本能回溯 raw sample。
- 每个 ready 样本都有置信度证据；缺少证据的样本进入 `NEEDS_REVIEW` 或 rejected。
- 仿真器 GT 保护检查通过或明确失败。
- 已有数据集 annotation provenance 未丢失。
- 真实数据 annotation gap 未丢失。
- annotation-tool 输出若存在，必须全部标记为 pseudo annotation 并进入人工复核状态。
- final 中每张标准图片必须有一个同 basename 的 metadata JSON；metadata 必须显式映射原图、最终标准图和所有派生图。
- 派生图片若存在，必须保存为独立文件，不得覆盖原图或标准图。
- simulator 默认不应存在半监督补标输出；若存在，必须有计划中的 `audit_only` 依据和非评分用途说明。

## 规则

- 不用仿真器 full GT 标准强行判定 existing_dataset / real_data。
- 不把真实数据的 annotation gap 当作清洗失败；但必须标记评测可用性风险。
- 不把半监督工具输出当作真值通过验证；缺少人工确认时只能是 `NEEDS_REVIEW` 或辅助候选。
- 不允许将 YOLO 画框图、深度图、mask overlay 等派生图片当作原图交给 Stage4；Stage4 必须通过 metadata 读取这些派生关系。
- 不把仿真器数据纳入常规半监督补标验证；仿真器应优先验证程序 GT 是否保留和可追溯。
- 不允许 Stage4 直接读取未合并的 source_work 作为唯一入口；Stage4 入口必须是 `final/STAGE4_INPUT_MANIFEST.jsonl`。
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
