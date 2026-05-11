---
name: benchmark-datajuicer-run-clean
description: "Stage 3 Phase 3：三类数据同一套 Data-Juicer 清洗执行。按统一配置索引并行运行 simulator、existing_dataset、real_data 的清洗任务，输出 source_work 分流 cleaned_data、rejected_samples、CLEANING_LINEAGE.jsonl 和运行报告；半监督标注由后续 benchmark-semisupervised-annotation 执行。Use when user says '运行 datajuicer', '执行数据清洗', 'run Data-Juicer cleaning'."
argument-hint: [datajuicer-config-dir]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob
metadata:
  openclaw:
    emoji: ""
    requires:
      bins: [python3, dj-process]
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

# Data-Juicer 清洗执行（三类数据同一 Skill 并行）

面向：**$ARGUMENTS**

本 skill 只执行已生成的 Data-Juicer 配置，不运行 annotation-tool，不修改清洗策略、不改 YAML、不验证 Stage 4。

## 重要约束

本 skill 是三类数据源共同使用的唯一 Phase 3 skill。不得拆成三套执行 skill；必须根据同一个 `DATAJUICER_CONFIG_INDEX.md` 并行运行三类数据配置，并输出统一运行报告。若存在 `ANNOTATION_TOOL_PLAN.md` 或 `run_annotation_tools.sh`，不得在本 skill 中执行；应交给 `/benchmark-semisupervised-annotation`。

## 置信度执行要求

- 执行 Data-Juicer 的目的必须是落实清洗计划中的置信度提升策略，而不是盲目产出 cleaned_data。
- 每个 source 的运行日志和 `DATAJUICER_RUN_REPORT.md` 必须记录哪些 operator 实际提升或验证了图片质量、文本质量、图文一致性、metadata 完整性、去重状态或 lineage 完整性。
- 被拒收或降级的样本必须保留 rejection reason / review reason；不得只删除样本而不解释置信度风险。
- 若某 source 的清洗运行失败、输出为空、证据字段缺失或无法证明置信度提升，运行报告必须把该 source 标记为 `FAIL` 或 `NEEDS_REVIEW`。

## 输入

必需：

- `~/benchclaw/data-juicer_card/DATAJUICER_AGENT_CAPABILITY_SPEC.md`
- `~/bench_workspace/workspace{i}/stage3/DATAJUICER_CONFIG_INDEX.md`
- `~/bench_workspace/workspace{i}/stage3/datajuicer_configs/*.yaml`
- `~/bench_workspace/workspace{i}/stage3/datajuicer_manifests/*.jsonl`
- `~/bench_workspace/workspace{i}/stage3/run_datajuicer_cleaning.sh`

若 capability spec 缺失，或 `DATAJUICER_CONFIG_INDEX.md` 未记录 capability spec 的读取状态与 operator 证据，不得执行 Data-Juicer。

可选：

- `DATAJUICER_BIN`
- `DRY_RUN=true`
- 并行度参数

## Data-Juicer Capability Spec 执行约束

执行前必须复核 `~/benchclaw/data-juicer_card/DATAJUICER_AGENT_CAPABILITY_SPEC.md` 与 `DATAJUICER_CONFIG_INDEX.md`：

- `run_datajuicer_cleaning.sh` 使用的二进制、CLI 参数、输入输出路径必须符合 spec。
- 每个 YAML 中的 operator 和参数必须能在 spec 中找到。
- 如果 spec 与现有配置冲突，以 spec 为准，停止执行并报告 `CONFIG_SPEC_MISMATCH`。
- 运行报告必须记录 capability spec 路径、读取状态和 spec 校验结果。

## 三类执行策略

### 仿真器 `simulator`

- 只运行保护 GT 的配置。
- 清洗后必须检查 GT 引用仍可追溯。
- rejected samples 必须保留 `scene_id`、`frame_id` 和 rejection reason。
- 本阶段不运行 annotation-tool；仿真器 GT 只做保留与追溯检查。

### 已有数据集 `existing_dataset`

- 运行 QA/caption/label/metadata 清洗与去重配置。
- rejected samples 必须保留 `original_sample_id` 和 annotation provenance。
- 清洗结果不得丢失 split 信息。
- 半监督候选标注由后续 `/benchmark-semisupervised-annotation` 处理。

### 真实数据 `real_data`

- 运行图片质量、重复检测、metadata 标准化和已有说明文本清洗配置。
- annotation gap 必须原样保留或追加状态，不得删除。
- pseudo annotation 必须保留 `needs_human_review`。
- 半监督候选标注由后续 `/benchmark-semisupervised-annotation` 处理。

## 输出

- `~/bench_workspace/workspace{i}/stage3/cleaned_data/{source_type}/{source_name}/`
- `~/bench_workspace/workspace{i}/stage3/rejected_samples/{source_type}_{source_name}_rejected.jsonl`
- `~/bench_workspace/workspace{i}/stage3/datajuicer_logs/{source_type}_{source_name}.log`
- `~/bench_workspace/workspace{i}/stage3/source_work/{source_type}/{source_name}/cleaned_data/`
- `~/bench_workspace/workspace{i}/stage3/source_work/{source_type}/{source_name}/rejected_samples/rejected.jsonl`
- `~/bench_workspace/workspace{i}/stage3/source_work/{source_type}/{source_name}/datajuicer_logs/run.log`
- `~/bench_workspace/workspace{i}/stage3/CLEANING_LINEAGE.jsonl`
- `~/bench_workspace/workspace{i}/stage3/DATAJUICER_RUN_REPORT.md`

## 运行报告结构

```markdown
# Data-Juicer Run Report

## Environment
- Data-Juicer binary: ...
- Capability spec: `~/benchclaw/data-juicer_card/DATAJUICER_AGENT_CAPABILITY_SPEC.md`
- Capability spec validation: PASS/FAIL
- Dry-run: true/false

## Per-Source Results
| Source Type | Source | Input Samples | Kept | Rejected | Retain Rate | Status |
|-------------|--------|---------------|------|----------|-------------|--------|

## Operator Statistics
[按 source_type 和 operator 汇总]

## Confidence Improvement Evidence
| Source Type | Source | Confidence Dimension | Evidence Field / Artifact | Passed | Review Reason |
|-------------|--------|----------------------|---------------------------|--------|---------------|

## Failed Runs
[失败配置、日志路径、恢复命令]

## Output Paths
[cleaned_data、rejected_samples、logs、lineage]
```

## 完成标准

- 三类数据配置由同一个执行入口覆盖。
- 执行前通过 capability spec 校验。
- 每个成功配置都有 cleaned output 和 log。
- 每个 source 的 cleaned output、rejected samples 和 log 必须位于 `source_work/{source_type}/{source_name}/` 下；根目录平铺输出只作为兼容镜像。
- `DATAJUICER_RUN_REPORT.md` 记录每个 source 的置信度提升证据、被过滤样本原因和需要人工复核的原因。
- 每个 cleaned/rejected 样本都有 lineage。
- 不覆盖或删除 Stage 2 原始数据。
- 不运行 annotation-tool，不生成 pseudo_annotations。
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
