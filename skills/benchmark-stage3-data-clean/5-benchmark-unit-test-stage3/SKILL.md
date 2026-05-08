---
name: benchmark-unit-test-stage3
description: "Stage 3 Phase 6：Stage 3 契约单元测试。用同一套测试入口并行验证 simulator、existing_dataset、real_data 的分流中间文件、清洗计划、配置、运行结果、pseudo annotation、lineage、schema、质量报告和 final 合并结果。Use when user says 'stage3 单元测试', 'unit test stage3', '检查 Stage 3 产物'."
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

# Stage 3 契约单元测试（三类数据同一 Skill 并行）

面向：**$ARGUMENTS**

本 skill 只生成并执行 Stage 3 契约测试，不修改清洗结果，不运行 annotation-tool。

## 重要约束

本 skill 是三类数据源共同使用的唯一 Phase 6 skill。不得拆成三套测试 skill；必须在同一个 `test_stage3_contract.py` 中并行覆盖三类数据源，并输出统一 `STAGE3_UNIT_TEST_REPORT.md`。

## 输入

必需：

- `~/benchclaw/data-juicer_card/DATAJUICER_AGENT_CAPABILITY_SPEC.md`
- `~/bench_workspace/workspace{i}/stage3/DATA_CLEANING_PLAN.md`
- `~/bench_workspace/workspace{i}/stage3/DATAJUICER_CONFIG_INDEX.md`
- `~/bench_workspace/workspace{i}/stage3/DATAJUICER_RUN_REPORT.md`
- `~/bench_workspace/workspace{i}/stage3/CLEANING_LINEAGE.jsonl`
- `~/bench_workspace/workspace{i}/stage3/CLEANED_DATA_SCHEMA.md`
- `~/bench_workspace/workspace{i}/stage3/CLEANING_QUALITY_REPORT.md`
- `~/bench_workspace/workspace{i}/stage3/source_work/`
- `~/bench_workspace/workspace{i}/stage3/final/STAGE4_INPUT_MANIFEST.jsonl`
- `~/bench_workspace/workspace{i}/stage3/final/cleaned_data/`
- `~/bench_workspace/workspace{i}/stage3/final/CLEANED_DATA_SCHEMA.md`
- `~/bench_workspace/workspace{i}/stage3/cleaned_data/`
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
- `DATA_CLEANING_PLAN.md`、`DATAJUICER_CONFIG_INDEX.md`、`DATAJUICER_RUN_REPORT.md` 均引用并记录 `~/benchclaw/data-juicer_card/DATAJUICER_AGENT_CAPABILITY_SPEC.md`。
- Data-Juicer operator、YAML 参数和 CLI 命令能追溯到 capability spec。
- 每个 source 的中间文件必须位于 `source_work/{source_type}/{source_name}/`，不得只存在于根目录平铺路径。
- 每个 cleaned/rejected sample 都有 lineage。
- 输出不覆盖 Stage 2 raw data。
- `CLEANING_QUALITY_REPORT.md` verdict 可解释。
- `final/STAGE4_INPUT_MANIFEST.jsonl` 存在，且每条 ready 样本能回溯到 `source_work` 中的 source 级中间文件。
- `final/cleaned_data/` 保持 `{source_type}/{source_name}/` 层级，作为 Stage4 的统一入口。
- 若存在 `ANNOTATION_TOOL_PLAN.md`，必须存在对应的 `ANNOTATION_TOOL_RUN_REPORT.md` 或明确跳过理由。
- 若存在半监督候选标注，权威位置必须是 `source_work/{source_type}/{source_name}/pseudo_annotations/`；每条候选标注必须有 `annotation_tool`、`tool_version_or_path`、`annotation_confidence`、`annotation_review_status` 和 raw sample lineage。

### 仿真器 `simulator`

- GT copy-only 策略写入计划和配置。
- 清洗结果中 GT 引用未丢失。
- scene/frame/sample 追溯链完整。
- simulator 默认不应有常规半监督补标输出；若存在 annotation-tool 输出，必须标记为 `audit_only`，只能作为审计或候选信号，不得覆盖 GT。

### 已有数据集 `existing_dataset`

- 原始 ID、split、annotation provenance 保留。
- QA/caption/label 字段清洗后仍可映射。
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

- `PASS`：三类清洗契约、分流中间产物和 final 合并结果均满足，可进入 Stage 4。
- `NEEDS_REVIEW`：真实数据标注缺口、已有数据集弱标注或低保留率需要用户确认 waiver。
- `FAIL`：GT 被破坏、lineage 缺失、schema 不兼容、关键产物缺失、source_work 分流缺失、final 合并结果缺失，Data-Juicer capability spec 缺失/不可追溯/配置不匹配，或 annotation-tool 输出覆盖 GT、缺少工具来源、被标记为真值，或 simulator 工具输出缺少 `audit_only` 依据。

## 规则

- 不修改数据。
- 不重跑 Data-Juicer。
- 不在缺少 `DATAJUICER_AGENT_CAPABILITY_SPEC.md` 证据时给出 PASS。
- 不运行 annotation-tool。
- 不用单一仿真器标准评估所有数据源。
- 不把半监督工具输出当作已确认标注。
- 不要求 simulator 使用半监督工具；仿真器测试重点是程序 GT 的保留、追溯和一致性。
- 报告中文优先，英文只用于字段名和 verdict。
