---
name: benchmark-datajuicer-config-gen
description: "Stage 3 Phase 2：三类数据同一套 Data-Juicer manifest、配置与可选 annotation-tool 配置生成。根据 DATA_CLEANING_PLAN.md 为 simulator、existing_dataset、real_data 并行生成 manifest、YAML、运行脚本、半监督标注工具配置和配置索引。Use when user says '生成 datajuicer 配置', 'Data-Juicer config', '生成清洗 yaml'."
argument-hint: [cleaning-plan]
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

# Data-Juicer 配置生成（三类数据同一 Skill 并行）

面向：**$ARGUMENTS**

本 skill 只生成 manifest、YAML、Data-Juicer 运行脚本和可选 annotation-tool 配置脚本，不执行清洗或半监督标注。

## 重要约束

本 skill 是三类数据源共同使用的唯一 Phase 2 skill。不得拆出独立 config-gen skill；必须在同一次执行中并行生成 `simulator`、`existing_dataset`、`real_data` 的配置，并写入同一个 `DATAJUICER_CONFIG_INDEX.md`。若 `DATA_CLEANING_PLAN.md` 中存在 `Annotation Tool Plan`，还必须生成 `ANNOTATION_TOOL_PLAN.md`、`annotation_tool_configs/` 和 `run_annotation_tools.sh`。半监督标注配置默认只为 `existing_dataset` 和 `real_data` 生成；`simulator` 只有在计划明确标注 `audit_only` 时才允许生成 annotation-tool 配置。

## 置信度配置要求

- 配置生成必须把 `DATA_CLEANING_PLAN.md` 中的 `Confidence Improvement Plan` 落到 manifest 字段、YAML operator、annotation-tool 配置和静态校验项中。
- 每个 source 的 manifest 必须保留或生成用于后续验证的置信度证据字段，例如 `confidence_dimensions`、`quality_flags`、`consistency_checks`、`lineage_id`、`review_required`、`review_reason`。
- YAML 只能配置能提升图文数据置信度或证据完整性的 operator；不得加入无法解释置信度收益的装饰性处理。
- 对会降低可追溯性、覆盖原图/GT、删除 annotation provenance 或丢弃低置信样本原因的配置，静态校验必须为 `FAIL`。

## 输入

必需：

- `~/benchclaw/data-juicer_card/DATAJUICER_AGENT_CAPABILITY_SPEC.md`
- `~/bench_workspace/workspace{i}/stage3/DATA_CLEANING_PLAN.md`
- `~/bench_workspace/workspace{i}/stage2/DATA_SCHEMA.md`
- `~/bench_workspace/workspace{i}/stage2/collected_data/`
- `~/bench_workspace/workspace{i}/stage2/templates/*.yaml`

若 `DATAJUICER_AGENT_CAPABILITY_SPEC.md` 缺失或不可读，必须停止配置生成；不得生成未经 spec 支撑的 YAML、manifest 或 CLI 脚本。

## Data-Juicer Capability Spec 使用要求

生成配置前必须读取 `~/benchclaw/data-juicer_card/DATAJUICER_AGENT_CAPABILITY_SPEC.md`，并以其中定义为准：

- manifest 输入格式与字段命名。
- YAML 配置结构、operator 名称、参数名和参数类型。
- CLI / `dj-process` 调用方式。
- 支持的质量过滤、去重、文本清洗、图文一致性、metadata 标准化等能力。
- copy-only / protected fields 的表达方式。

`DATAJUICER_CONFIG_INDEX.md` 必须记录 `Capability Spec Path`、读取状态、使用到的 operator 与 spec 证据。`run_datajuicer_cleaning.sh` 中的命令必须符合 capability spec 中声明的调用方式。

## 三类配置生成策略

### 仿真器 `simulator`

- manifest 只暴露可清洗文本、metadata、image-text 引用字段。
- GT、geometry、mask、pose、trajectory 只写引用，不进入 destructive operator。
- YAML 中必须显式排除 copy-only 字段。
- 默认不生成 annotation-tool 配置，因为仿真器已有程序 GT。
- 若计划明确要求 `audit_only`，只生成一致性审计配置，不得生成覆盖 GT 或替代 GT 的配置。

### 已有数据集 `existing_dataset`

- manifest 包含 QA、caption、label、metadata、图片路径、原始 ID。
- YAML 可配置文本清洗、去重、图文一致性、label 标准化。
- 保留 `original_sample_id`、`original_split`、`annotation_provenance`。
- 若计划调用 `sam3`、`depthanything`、`yolo`，配置必须把输出写入 `source_work/existing_dataset/{source_name}/pseudo_annotations/`，并保留原始标注来源。
- 若工具会生成与原图不同的图片产物，配置必须要求输出记录包含 `original_image_path`、`derived_image_path`、`derived_image_type` 和 `metadata_update_required=true`，以便 Phase 5 合并到 final metadata。

### 真实数据 `real_data`

- manifest 包含图片路径、metadata、quality flags、annotation gap。
- YAML 可配置图片质量过滤、重复检测、metadata 标准化、已有说明文本清洗。
- annotation gap 字段不得被删除；pseudo annotation 必须保留状态标签。
- 若计划调用 annotation-tool，配置必须把候选标注写入 `source_work/real_data/{source_name}/pseudo_annotations/`，并强制 `annotation_review_status=needs_human_review`。
- 若 annotation-tool 生成 YOLO 画框图、深度图、mask overlay、裁剪图或诊断可视化图，配置必须要求派生图片独立保存，并输出 `original_image_path`、`derived_image_path`、`derived_image_type`、`metadata_update_required=true`。

## 输出

- `~/bench_workspace/workspace{i}/stage3/datajuicer_manifests/{source_type}_{source_name}_input.jsonl`
- `~/bench_workspace/workspace{i}/stage3/datajuicer_configs/{source_type}_{source_name}_clean.yaml`
- `~/bench_workspace/workspace{i}/stage3/source_work/{source_type}/{source_name}/datajuicer_manifest/input.jsonl`
- `~/bench_workspace/workspace{i}/stage3/source_work/{source_type}/{source_name}/datajuicer_config/clean.yaml`
- `~/bench_workspace/workspace{i}/stage3/run_datajuicer_cleaning.sh`
- `~/bench_workspace/workspace{i}/stage3/DATAJUICER_CONFIG_INDEX.md`
- `~/bench_workspace/workspace{i}/stage3/annotation_tool_configs/{source_type}_{source_name}_{tool}.yaml`（按需）
- `~/bench_workspace/workspace{i}/stage3/run_annotation_tools.sh`（按需）
- `~/bench_workspace/workspace{i}/stage3/ANNOTATION_TOOL_PLAN.md`（按需）

## 配置索引结构

```markdown
# Data-Juicer Config Index

## Config Summary
| Source Type | Source | Manifest | Config | Export Path | Operators | Spec Evidence | Copy-Only Encoded |
|-------------|--------|----------|--------|-------------|-----------|---------------|-------------------|

## Capability Spec
- Path: `~/benchclaw/data-juicer_card/DATAJUICER_AGENT_CAPABILITY_SPEC.md`
- Read status: PASS/FAIL
- CLI mode: [from spec]
- YAML schema version / config style: [from spec]

## Static Validation
- YAML parse: PASS/FAIL
- Manifest non-empty: PASS/FAIL
- Raw output isolation: PASS/FAIL
- Protected field policy encoded: PASS/FAIL
- Confidence evidence fields encoded: PASS/FAIL

## Run Command
```bash
bash ~/bench_workspace/workspace{i}/stage3/run_datajuicer_cleaning.sh
```
```

## Annotation Tool Config Index
[若启用半监督标注，列出 `~/benchclaw/annotation-tool` 下的工具、配置、输入、输出、置信度阈值、人工复核策略；若不启用则写 none]

## 完成标准

- 每个 source 都有 manifest 和 config，或有明确跳过理由。
- 已读取 `DATAJUICER_AGENT_CAPABILITY_SPEC.md`，且 `DATAJUICER_CONFIG_INDEX.md` 记录读取状态和使用证据。
- YAML operator 名称、参数名、CLI 命令均来自 capability spec。
- 每个 source 的 manifest 和 config 必须复制或直接写入 `source_work/{source_type}/{source_name}/` 下，不得只保留根目录平铺文件。
- 三类配置都登记在同一份 `DATAJUICER_CONFIG_INDEX.md`。
- 输出路径全部位于 `stage3/`，不得覆盖 `stage2/collected_data/`。
- 每个配置都能说明对应的置信度提升目标、证据字段和 Stage4 ready 风险。
- copy-only 字段不会被 Data-Juicer operator 修改。
- annotation-tool 配置只生成 `pseudo_annotation`，不得覆盖 GT、原始 label 或 annotation provenance。
- simulator 的 annotation-tool 配置默认不存在；若存在，必须在 `ANNOTATION_TOOL_PLAN.md` 中标明 `audit_only` 和非评分用途。
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
