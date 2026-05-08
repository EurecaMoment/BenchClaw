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
- `~/bench_workspace/workspace{i}/stage3/final/rejected_samples/`
- `~/bench_workspace/workspace{i}/stage3/final/pseudo_annotations/`（按需）
- `~/bench_workspace/workspace{i}/stage3/final/CLEANED_DATA_SCHEMA.md`
- `~/bench_workspace/workspace{i}/stage3/final/CLEANING_LINEAGE.jsonl`
- `~/bench_workspace/workspace{i}/stage3/final/ANNOTATION_LINEAGE.jsonl`（按需）
- `~/bench_workspace/workspace{i}/stage3/final/STAGE4_INPUT_MANIFEST.jsonl`

## 合并策略

- 从 `source_work/simulator/{source_name}/cleaned_data/`、`source_work/existing_dataset/{source_name}/cleaned_data/`、`source_work/real_data/{source_name}/cleaned_data/` 汇总样本。
- 统一写入 `final/cleaned_data/{source_type}/{source_name}/`，保持 source_type 和 source_name 层级。
- 合并 rejected samples 到 `final/rejected_samples/{source_type}_{source_name}_rejected.jsonl`。
- 合并半监督候选标注到 `final/pseudo_annotations/{source_type}/{source_name}/`，但 simulator 的 `audit_only` 输出只能作为审计附件，不能进入评分 GT 字段。
- 生成 `final/STAGE4_INPUT_MANIFEST.jsonl`，每条样本必须包含 `source_type`、`source_name`、`sample_id`、`cleaned_path`、`gt_availability`、`annotation_status`、`pseudo_annotation_path`（如有）、`lineage_id`、`stage4_ready_status`。
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
- 仿真器 GT 保护检查通过或明确失败。
- 已有数据集 annotation provenance 未丢失。
- 真实数据 annotation gap 未丢失。
- annotation-tool 输出若存在，必须全部标记为 pseudo annotation 并进入人工复核状态。
- simulator 默认不应存在半监督补标输出；若存在，必须有计划中的 `audit_only` 依据和非评分用途说明。

## 规则

- 不用仿真器 full GT 标准强行判定 existing_dataset / real_data。
- 不把真实数据的 annotation gap 当作清洗失败；但必须标记评测可用性风险。
- 不把半监督工具输出当作真值通过验证；缺少人工确认时只能是 `NEEDS_REVIEW` 或辅助候选。
- 不把仿真器数据纳入常规半监督补标验证；仿真器应优先验证程序 GT 是否保留和可追溯。
- 不允许 Stage4 直接读取未合并的 source_work 作为唯一入口；Stage4 入口必须是 `final/STAGE4_INPUT_MANIFEST.jsonl`。
