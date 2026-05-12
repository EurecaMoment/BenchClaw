---
name: benchmark-data-cleaning-plan
description: "Stage 3 Phase 1：三类数据同一套清洗与半监督标注计划。为 simulator、existing_dataset、real_data 并行制定 Data-Juicer 清洗策略、annotation-tool 半监督标注策略、GT/annotation 保护策略和输出映射。Use when user says '制定清洗计划', 'datajuicer cleaning plan', '规划数据清洗'."
argument-hint: [stage2-context]
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

# 清洗计划制定（三类数据同一 Skill 并行）

面向：**$ARGUMENTS**

本 skill 只制定清洗计划和半监督标注计划，不生成 YAML、不运行 Data-Juicer、不调用 annotation-tool、不验证清洗结果。

## 中文优先原则

- 清洗目标、风险、保护策略、验收标准使用中文。
- 英文只用于 `source_type`、operator、字段名、路径名等辅助信息。

## 可选半监督标注工具

Stage 3 可以按需参考 `~/benchclaw/annotation-tool` 下的工具辅助标注样例，自行设计程序进行标注：

- `sam3`：候选分割 mask 或实例区域。
- `depthanything`：候选深度图或相对深度辅助信号。
- `yolo`：候选检测框、类别和置信度。

计划中必须明确每个 source 是否需要工具补标；若需要，写清工具、输入字段、输出字段、置信度阈值、人工复核要求和不得覆盖的保护字段。默认优先为 `existing_dataset` 和 `real_data` 规划半监督补标，因为它们往往缺乏完整 GT；`simulator` 已有程序 GT 时默认不规划补标，只能在确有必要时规划“审计模式”。工具输出只能是 `pseudo_annotation` 或审计信号，必须进入 `needs_human_review` 队列。

## 重要约束

本 skill 是三类数据源共同使用的唯一 Phase 1 skill。不得拆成 simulator cleaning plan、dataset cleaning plan、real-data cleaning plan 三套 skill；必须在同一次执行中并行制定三类清洗策略，并写入同一个 `DATA_CLEANING_PLAN.md`。

## 置信度规划要求

Stage3 的核心目标是提升 Stage2 采集图文数据的置信度。清洗计划必须为每个 source 明确：

- 需要提升的置信度维度：图片质量、文本质量、图文一致性、标注完整性、metadata 完整性、去重状态、lineage 完整性、人工复核需求。
- 每个维度使用的 Data-Juicer operator、annotation-tool、人工复核或 copy-only 保护策略。
- 置信度证据写入位置，例如 manifest 字段、lineage 字段、quality flag、annotation confidence、review queue、rejection reason。
- 进入 Stage4 的最低条件：哪些证据满足时可 `stage4_ready_status=ready`，哪些情况必须 `NEEDS_REVIEW` 或 rejected。
- 不得把半监督候选标注、清洗后的文本或格式修复当成真实 GT 置信度提升；它们只能作为复核证据。

## 输入

必需：

- `~/benchclaw/data-juicer_card/DATAJUICER_AGENT_CAPABILITY_SPEC.md`
- `~/bench_workspace/workspace{i}/stage2/DATA_SCHEMA.md`
- `~/bench_workspace/workspace{i}/stage2/DATA_QUALITY_REPORT.md`
- `~/bench_workspace/workspace{i}/stage2/collected_data/`
- `~/bench_workspace/workspace{i}/stage2/templates/*.yaml`

可选：

- `~/bench_workspace/workspace{i}/stage2/COLLECTION_GUIDANCE_PLAN.md`
- `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md`
- 用户指定的 retain rate、禁用 operator、重点保护字段

若 `~/benchclaw/data-juicer_card/DATAJUICER_AGENT_CAPABILITY_SPEC.md` 缺失或不可读，必须停止计划生成并报告阻塞；不得凭常识臆造 Data-Juicer operator 或 YAML 字段。

## Data-Juicer 能力规格读取

在制定任何清洗策略前，必须读取 `~/benchclaw/data-juicer_card/DATAJUICER_AGENT_CAPABILITY_SPEC.md`，并从中整理出：

- 可用 Data-Juicer operator 及适用数据类型。
- 每个 operator 的输入字段、输出字段、关键参数、默认值和风险。
- Data-Juicer manifest / YAML / CLI 的合法结构。
- 对图片、文本、metadata、QA、caption、label 等字段的处理能力边界。
- GT、annotation provenance、lineage、copy-only 字段的保护要求。
- 质量验证或 dry-run 建议。

计划产物必须新增 `## Data-Juicer Capability Summary` 小节，说明本次计划使用了 capability spec 中哪些能力；每个计划使用的 operator 都要能追溯到该 spec。

## 并行制定清洗策略

执行方式：读取 Stage 2 全部 source，按 `source_type` 分为三组并行制定策略；如果无法真实并行，也必须在同一 Phase 1 内完成三组计划。

## 中间产物分目录规划

计划中必须为每个 source 明确 Stage3 中间目录：

- `source_work/simulator/{source_name}/`
- `source_work/existing_dataset/{source_name}/`
- `source_work/real_data/{source_name}/`

Data-Juicer manifest、config、cleaned_data、rejected_samples、logs、半监督候选标注或审计输出都必须落在对应 source 目录下。最终合并结果只在验证阶段写入 `final/`，供 Stage4 调用。

### 仿真器数据 `simulator`

清洗目标：

- 清洗 caption、QA、文本 metadata、manifest 中的可清洗文本字段。
- 检查图片质量、重复样本、路径一致性。
- 验证 GT 引用和文件可读性。

保护策略：

- `gt.*`、depth、segmentation、pose、bbox、point cloud、mesh、trajectory、frame_id、scene_id、timestamp、alignment index 均为 copy-only。
- Data-Juicer 不得修改上述字段，只能复制、索引、验证。
- 默认不为仿真器数据调用 annotation-tool 进行半监督补标，因为仿真器已经能够通过程序/API 产生 GT。
- annotation-tool 只能在审计模式下用于检测 GT 与图片是否一致、发现异常样本、生成非评分用诊断信号；不得覆盖程序生成 GT，也不得生成替代 pseudo GT。

### 已有数据集 `existing_dataset`

清洗目标：

- 清洗 QA、caption、label、metadata 文本。
- 去重图片、重复 QA、重复 caption。
- 检查图文一致性和标注字段完整性。
- 标准化 label / answer 格式。

保护策略：

- 保留 `original_sample_id`、`original_split`、`annotation_provenance`、license/access note。
- 缺失 GT 保持 `missing_or_derived`，不得补成 `full_gt`。
- 可用 `sam3`、`depthanything`、`yolo` 生成候选 mask/depth/detection，但必须保留原始 annotation provenance，并将工具结果标记为 `pseudo_annotation`。

### 真实数据 `real_data`

清洗目标：

- 检查图片损坏、模糊、曝光、低分辨率、重复。
- 清洗已有说明文本或 metadata。
- 维护 annotation gap 和人工复核队列。

保护策略：

- 原始图片和原始 metadata copy-only。
- pseudo caption / pseudo label 必须标记为 `pseudo_annotation` 和 `needs_human_review`。
- 缺失 GT 保持 `needs_annotation` 或 `not_observable`。
- 可用 annotation-tool 生成候选检测、分割或深度结果，用于缩小人工标注范围；这些结果不得直接进入自动评分真值。

## 输出

- `~/bench_workspace/workspace{i}/stage3/DATA_CLEANING_PLAN.md`

## 输出结构

```markdown
# Data Cleaning Plan

## Data-Juicer Capability Summary
[从 `~/benchclaw/data-juicer_card/DATAJUICER_AGENT_CAPABILITY_SPEC.md` 提取的可用 operator、配置 schema、CLI、字段保护和质量验证规则]

## Source-Type Cleaning Summary
| Source Type | Source | Cleaning Goal | Protected Fields | Review Trigger |
|-------------|--------|---------------|------------------|----------------|

## Confidence Improvement Plan
| Source Type | Source | Confidence Dimensions | Evidence Artifacts | Stage4 Ready Criteria | Review / Reject Criteria |
|-------------|--------|-----------------------|--------------------|-----------------------|--------------------------|

## Simulator Cleaning Policy
[仿真器 GT 保护、可清洗字段、非 Data-Juicer 处理]

## Existing Dataset Cleaning Policy
[QA/caption/label 清洗、去重、图文一致性、标注来源保护]

## Real Data Cleaning Policy
[图片质量、metadata、annotation gap、人工复核]

## Data-Juicer Operator Plan
| Source Type | Source | Target Field | Operator Category | Operator Name | Spec Evidence | Action | Risk |

## Annotation Tool Plan
| Source Type | Source | Tool | Input Field | Output Field | Confidence Threshold | Review Policy |
|-------------|--------|------|-------------|--------------|----------------------|---------------|

要求：

- `existing_dataset` 和 `real_data` 是默认优先规划对象。
- `simulator` 默认填写 `none`；只有当存在 GT/图像一致性审计需求时才允许填写工具，并必须在 Review Policy 中写明 `audit_only`。

## Non-Data-Juicer Handling
[copy-only 字段、二进制 GT、真实数据 annotation gap、annotation-tool pseudo annotation、人工复核项]

## Output Mapping
| Source Type | Raw Input | Manifest | Config | Cleaned Output | Rejected Output |

## Source Work Directories
| Source Type | Source | Source Work Dir | Data-Juicer Files | Annotation Files | Final Merge Policy |
|-------------|--------|-----------------|-------------------|------------------|--------------------|

## Acceptance Criteria
[保留率、GT 保护、annotation 保护、schema 对齐、lineage 完整性]
```

## 完成标准

- 三类数据源都出现在同一份 `DATA_CLEANING_PLAN.md`。
- 已读取 `DATAJUICER_AGENT_CAPABILITY_SPEC.md`，并在 `Data-Juicer Capability Summary` 中总结可用能力。
- 每个 Data-Juicer operator 都有 `Spec Evidence`，可追溯到 capability spec。
- 每个 source 都有清洗目标、保护字段、输出映射。
- 每个 source 都有明确的置信度提升维度、证据产物、Stage4 ready 条件和复核/拒收条件。
- 每个 source 都有明确的 `source_work/{source_type}/{source_name}/` 中间目录规划。
- 仿真器 GT 保护策略明确。
- 已有数据集 annotation provenance 保护策略明确。
- 真实数据 annotation gap 处理策略明确。
- 若计划调用 annotation-tool，必须明确工具路径、输出目录、pseudo annotation 状态和人工复核要求。
- 若对 simulator 计划调用 annotation-tool，必须说明为什么程序 GT 不足以完成审计，并标明输出不得用于替代 GT。

## 规则

- 不生成 YAML、manifest 或 cleaned_data。
- 不修改 Stage 2 原始数据。
- 不在未读取 `DATAJUICER_AGENT_CAPABILITY_SPEC.md` 的情况下制定 Data-Juicer operator 计划。
- 不建议删除 GT 字段。
- 不把真实数据或已有数据集缺失字段伪造成完整真值。
- 不把 `sam3`、`depthanything`、`yolo` 的输出当成 GT；它们只能作为候选标注或审计信号。
- 不把仿真器数据作为半监督补标的默认对象；仿真器优先使用程序生成的 GT。
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
