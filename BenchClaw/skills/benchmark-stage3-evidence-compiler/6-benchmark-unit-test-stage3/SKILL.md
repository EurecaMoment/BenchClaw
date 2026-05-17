---
name: benchmark-unit-test-stage3
description: "Stage 3 Phase 6：Stage 3 契约单元测试。用同一套测试入口并行验证 simulator、existing_dataset、real_data 的分流中间文件、证据编译计划、配置、运行结果、pseudo annotation、lineage、schema、证据质量报告和 final 合并结果。Use when user says 'stage3 单元测试', 'unit test stage3', '检查 Stage 3 产物'."
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

# Stage 3 契约单元测试（三类数据同一 Skill 并行）

面向：**$ARGUMENTS**

本 skill 只生成并执行 Stage 3 契约测试，不修改证据编译结果，不运行 annotation-tool。

## 重要约束

本 skill 是三类数据源共同使用的唯一 Phase 6 skill。不得拆成三套测试 skill；必须在同一个 `test_stage3_contract.py` 中并行覆盖三类数据源，并输出统一 `STAGE3_UNIT_TEST_REPORT.md`。

## 置信度测试要求

- 单元测试必须把“Stage3 是否提升并证明了图文数据置信度”作为核心合约，而不仅测试文件是否存在。
- 测试必须覆盖计划、配置、运行、半监督标注、最终合并中的置信度证据字段。
- 缺少 `confidence_evidence`、`confidence_status`、`review_reason`、quality flags、consistency checks 或 lineage 的 ready 样本必须判为失败。
- 有 pseudo annotation 但无工具置信度、阈值、人工复核状态或原图映射的样本不得通过 ready 检查。

## 输入

必需：

- `BENCHCLAW_ROOT/data-juicer_card/references/DATAJUICER_AGENT_CAPABILITY_SPEC.md`
- `~/bench_workspace/workspace{i}/stage3/EVIDENCE_COMPILATION_PLAN.md`
- `~/bench_workspace/workspace{i}/stage3/DATAJUICER_CONFIG_INDEX.md`
- `~/bench_workspace/workspace{i}/stage3/DATAJUICER_RUN_REPORT.md`
- `~/bench_workspace/workspace{i}/stage3/CLEANING_LINEAGE.jsonl`
- `~/bench_workspace/workspace{i}/stage3/EVIDENCE_SCHEMA.md`
- `~/bench_workspace/workspace{i}/stage3/EVIDENCE_QUALITY_REPORT.md`
- `~/bench_workspace/workspace{i}/stage3/source_work/`
- `~/bench_workspace/workspace{i}/stage3/final/STAGE4_INPUT_MANIFEST.jsonl`
- `~/bench_workspace/workspace{i}/stage3/final/evidence/`
- `~/bench_workspace/workspace{i}/stage3/final/EVIDENCE_SCHEMA.md`
- `~/bench_workspace/workspace{i}/stage3/evidence/`
- `~/bench_workspace/workspace{i}/stage3/rejected_samples/`

可选：

- `~/bench_workspace/workspace{i}/stage3/ANNOTATION_TOOL_PLAN.md`
- `~/bench_workspace/workspace{i}/stage3/ANNOTATION_TOOL_RUN_REPORT.md`
- `~/bench_workspace/workspace{i}/stage3/annotation_tool_configs/`
- `~/bench_workspace/workspace{i}/stage3/source_work/{source_type}/{source_name}/pseudo_annotations/`
- `~/bench_workspace/workspace{i}/stage3/source_work/{source_type}/{source_name}/annotation_tool_logs/`

## 测试重点

### 通用契约

- 每个 source 都有 `source_type`、`source_name`。
- `EVIDENCE_COMPILATION_PLAN.md`、`DATAJUICER_CONFIG_INDEX.md`、`DATAJUICER_RUN_REPORT.md` 均引用并记录 `BENCHCLAW_ROOT/data-juicer_card/references/DATAJUICER_AGENT_CAPABILITY_SPEC.md`。
- Data-Juicer operator、YAML 参数和 CLI 命令能追溯到 capability spec。
- 每个 source 的中间文件必须位于 `source_work/{source_type}/{source_name}/`，不得只存在于根目录平铺路径。
- 每个 compiled/rejected sample 都有 lineage。
- 输出不覆盖 Stage 2 raw data。
- `EVIDENCE_QUALITY_REPORT.md` verdict 可解释。
- `final/STAGE4_INPUT_MANIFEST.jsonl` 存在，且每条 ready 样本能回溯到 `source_work` 中的 source 级中间文件。
- `final/evidence/` 保持 `{source_type}/{source_name}/` 层级，作为 Stage4 的统一证据入口。
- `final/evidence/{source_type}/{source_name}/images/` 与 `metadata/` 必须存在；每张 `images/{sample_id}.{ext}` 必须有且仅有一个 `metadata/{sample_id}.json`。
- 每个 metadata JSON 必须可解析，并包含 `sample_id`、`source_type`、`source_name`、`original_image_path`、`final_image_path`、`record_json_path`、`processed_images`、`lineage_id`、`confidence_evidence`、`confidence_status`、`review_reason`、`stage4_ready_status`。
- `final/STAGE4_INPUT_MANIFEST.jsonl` 的每条 ready 样本必须包含 `final_image_path`、`metadata_json_path` 和数组字段 `processed_image_paths`。
- `final/STAGE4_INPUT_MANIFEST.jsonl` 的每条 ready 样本必须包含非空或明确 PASS 的 `confidence_evidence`，且 `confidence_status` 不得为 `UNKNOWN`。
- 若 `processed_image_paths` 或 metadata 的 `processed_images[]` 非空，所有派生图片文件必须存在于 `final/evidence/{source_type}/{source_name}/processed_images/`，并且 metadata 中必须说明 `derived_type`、`derived_image_path`、`source_image_path` 和工具来源。
- 派生图片 basename 必须以对应 `sample_id` 开头；派生图片不得与 `final_image_path` 指向同一文件。
- 若存在 `ANNOTATION_TOOL_PLAN.md`，必须存在对应的 `ANNOTATION_TOOL_RUN_REPORT.md` 或明确跳过理由。
- 若存在半监督候选标注，权威位置必须是 `source_work/{source_type}/{source_name}/pseudo_annotations/`；每条候选标注必须有 `annotation_tool`、`tool_version_or_path`、`annotation_confidence`、`annotation_review_status` 和 raw sample lineage。

### 仿真器 `simulator`

- GT copy-only 策略写入计划和配置。
- 证据编译结果中 GT 引用未丢失。
- scene/frame/sample 追溯链完整。
- simulator 默认不应有常规半监督补标输出；若存在 annotation-tool 输出，必须标记为 `audit_only`，只能作为审计或候选信号，不得覆盖 GT。

### 已有数据集 `existing_dataset`

- 原始 ID、split、annotation provenance 保留。
- QA/caption/label 字段规范化后仍可映射。
- 缺失 GT 保持 `missing_or_derived`。
- annotation-tool 输出若存在，必须标记为 `pseudo_annotation`，且不得覆盖原始 annotation provenance。

### 真实数据 `real_data`

- raw image 和 metadata 可追溯。
- annotation gap 保留。
- pseudo annotation 未被标记为 GT。
- 需要人工复核的样本进入 `NEEDS_REVIEW`。
- `sam3`、`depthanything`、`yolo` 等工具输出若存在，必须标记 `needs_human_review`。

## 输出

- `~/bench_workspace/workspace{i}/stage3/unit_tests/test_stage3_contract.py`
- `~/bench_workspace/workspace{i}/stage3/unit_tests/results.json`
- `~/bench_workspace/workspace{i}/stage3/STAGE3_UNIT_TEST_REPORT.md`

## Verdict

- `PASS`：三类证据编译契约、分流中间产物和 final 合并结果均满足，可进入 Stage 4。
- `NEEDS_REVIEW`：真实数据标注缺口、已有数据集弱标注或低保留率需要用户确认 waiver。
- `FAIL`：GT 被破坏、lineage 缺失、schema 不兼容、关键产物缺失、source_work 分流缺失、final 合并结果缺失、final 图片与 metadata 不是一一对应、置信度证据缺失、ready 样本缺少 review/quality/consistency 依据、派生图片未在 metadata 中声明或覆盖原图，Data-Juicer capability spec 缺失/不可追溯/配置不匹配，或 annotation-tool 输出覆盖 GT、缺少工具来源、被标记为真值，或 simulator 工具输出缺少 `audit_only` 依据。

## 规则

- 不修改数据。
- 不重跑 Data-Juicer。
- 不在缺少 `DATAJUICER_AGENT_CAPABILITY_SPEC.md` 证据时给出 PASS。
- 不运行 annotation-tool。
- 不用单一仿真器标准评估所有数据源。
- 不把半监督工具输出当作已确认标注。
- 不允许 final 阶段出现没有 metadata 的图片、没有图片的 metadata、或未声明来源的派生图片。
- 不要求 simulator 使用半监督工具；仿真器测试重点是程序 GT 的保留、追溯和一致性。
- 报告中文优先，英文只用于字段名和 verdict。
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
