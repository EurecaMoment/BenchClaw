---
name: benchmark-stage3-data-clean
description: "Stage 3 子流程：同一套 Skill 的三类数据并行清洗与可选半监督标注。基于 Stage 2 的 simulator、existing_dataset、real_data 原始数据、schema 和质量报告，生成 Data-Juicer 配置，按需调用 annotation-tool 中的 sam3、depthanything、yolo 等工具生成候选标注，保留追溯链并验证清洗质量。Use when user says '开始 stage3', '数据清洗', 'data cleaning stage', 'clean collected data'."
argument-hint: [stage2-dir]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Skill
metadata:
  openclaw:
    emoji: ""
    requires:
      bins: [python3, dj-process]
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

# Benchmark Stage 3：同一套 Skill 的三类数据并行清洗与半监督标注

面向：**$ARGUMENTS**

本 skill 是 Stage 3 编排器，只调度同一套 Stage 3 子 skill，不为三类数据源拆分三套流程。

重要扩展：Stage 3 不只允许使用 Data-Juicer。除 Data-Juicer 清洗外，还可以调用 `~/benchclaw/annotation-tool` 下的半监督标注工具，例如 `sam3`、`depthanything`、`yolo`。这些工具主要面向缺乏完整 GT 的 `existing_dataset` 和 `real_data`；`simulator` 通常已有程序真值，默认不需要半监督补标。工具输出只生成候选标注或辅助几何/检测结果，必须标记为 `pseudo_annotation`、`tool_generated` 和 `needs_human_review`，不得写成仿真器 GT 或人工真值。

Data-Juicer 能力来源要求：所有 Data-Juicer 计划、配置生成和执行都必须先读取 `~/benchclaw/data-juicer_card/DATAJUICER_AGENT_CAPABILITY_SPEC.md`。该文件是本流程使用 Data-Juicer 的权威能力说明，必须从中提取可用 operator、配置 schema、CLI/调用方式、输入输出字段约束、GT/annotation 保护规则和质量验证规则。若该文件缺失或不可读，Stage 3 必须停止并报告环境阻塞，不得凭经验猜测 Data-Juicer 配置。

## 中文优先原则

- 清洗计划、风险说明、验证报告必须以中文为主。
- 英文只作为辅助，用于命令名、字段名、source type、operator、API、verdict 等。
- 如果中英文说明冲突，以中文任务目标和 Stage 2 产物契约为准。

## 三类数据源清洗总契约

Stage 3 必须继承 Stage 2 的 `source_type` 路由，同一套 Phase 1-6 skill 内并行处理三类数据：

| source_type | 中文名称 | Stage 3 清洗目标 | 禁止行为 |
|-------------|----------|------------------|----------|
| `simulator` | 仿真器数据 | 清洗文本、metadata、manifest；保护程序生成的 GT、几何、mask、pose、trajectory 和对齐索引；默认不调用 annotation-tool，只有在需要审计 GT/图像一致性时才可用工具做辅助检查 | 不得用 Data-Juicer 或 annotation-tool 改写 GT；不得为已有 full GT 的仿真器样本生成替代 pseudo GT |
| `existing_dataset` | 已有数据集 | 清洗 QA、caption、label、metadata；去重；验证图文/标注一致性；保留原始 ID 和标注来源；可用 annotation-tool 补充候选 mask/depth/detection | 不得丢失 annotation provenance，不得把工具预测补成原始标注 |
| `real_data` | 真实数据 | 清洗/筛选图片质量、重复样本、metadata 和已有说明；维护 annotation gap 和人工复核队列；可用 annotation-tool 生成半监督候选标注 | 不得把 pseudo annotation 当真值 |

所有 Stage 3 产物必须保留：

- `source_type`
- `source_name`
- `source_path`
- `sample_id`
- `capability_dimension`
- `gt_availability`
- `annotation_status`
- `raw_path`
- `cleaned_path`
- `rejection_reason`
- `lineage_id`
- `annotation_tool`
- `annotation_confidence`
- `annotation_review_status`

## 同一套 Skill 的并行处理方式

每个 Phase 都必须执行以下模式：

1. 读取 Stage 2 的统一产物：`DATA_SCHEMA.md`、`DATA_QUALITY_REPORT.md`、`collected_data/`、`templates/*.yaml`。
2. 按 `source_type` 分成 `simulator`、`existing_dataset`、`real_data` 三组。
3. 在同一个 skill 内并行或等价并行处理三组数据，并按计划选择是否运行 annotation-tool 半监督标注工具。
4. 如果运行环境不支持真实并行，也必须在同一个 Phase 内顺序完成三组处理，不得拆成独立阶段或独立 skill。
5. 输出统一报告，同时保留三类数据的小节、manifest、config 和 lineage。

## Stage 3 目录契约：中间分流，最终合并

Stage 3 虽然使用同一套 skill 编排三类数据，但每条 source 的中间文件必须分目录隔离，最后再合并为 Stage 4 读取的一套结果。

```text
stage3/
  source_work/
    simulator/{source_name}/
      datajuicer_manifest/input.jsonl
      datajuicer_config/clean.yaml
      cleaned_data/
      rejected_samples/rejected.jsonl
      datajuicer_logs/run.log
      annotation_audit/                 # 仅 audit_only 时允许
    existing_dataset/{source_name}/
      datajuicer_manifest/input.jsonl
      datajuicer_config/clean.yaml
      cleaned_data/
      rejected_samples/rejected.jsonl
      datajuicer_logs/run.log
      pseudo_annotations/               # 半监督候选标注
      annotation_tool_logs/
    real_data/{source_name}/
      datajuicer_manifest/input.jsonl
      datajuicer_config/clean.yaml
      cleaned_data/
      rejected_samples/rejected.jsonl
      datajuicer_logs/run.log
      pseudo_annotations/               # 半监督候选标注
      annotation_tool_logs/
  final/
    cleaned_data/
    rejected_samples/
    pseudo_annotations/
    CLEANED_DATA_SCHEMA.md
    CLEANING_LINEAGE.jsonl
    ANNOTATION_LINEAGE.jsonl
    STAGE4_INPUT_MANIFEST.jsonl
```

兼容输出可以保留在 Stage3 根目录，例如 `cleaned_data/{source_type}/{source_name}/`、`rejected_samples/`、`CLEANING_LINEAGE.jsonl`，但权威中间产物应以 `source_work/{source_type}/{source_name}/` 为准；Stage4 优先读取 `stage3/final/STAGE4_INPUT_MANIFEST.jsonl` 和 `stage3/final/cleaned_data/`。

## 半监督标注工具契约

可选工具目录：`~/benchclaw/annotation-tool`

允许调用的工具包括但不限于：

- `sam3`：候选分割 mask、区域 proposal、实例轮廓。
- `depthanything`：候选 depth map、相对深度、几何辅助信号。
- `yolo`：候选检测框、类别、置信度。

调用规则：

- 只有当 `DATA_CLEANING_PLAN.md` 明确列出某 source 需要半监督补标时才调用。
- 默认优先调用对象是 `existing_dataset` 和 `real_data`，因为它们更常缺乏完整 GT；`simulator` 默认不调用。
- 对 `simulator` 的唯一例外是“审计模式”：检查程序 GT 与图像观测的一致性、发现异常样本或生成非评分用诊断信号。审计结果必须写成 `audit_annotation` 或 `pseudo_annotation_for_audit`，不得进入评测真值字段。
- 工具输出必须写入 `~/bench_workspace/workspace{i}/stage3/source_work/{source_type}/{source_name}/pseudo_annotations/`；simulator audit_only 输出写入 `source_work/simulator/{source_name}/annotation_audit/`。
- 工具日志必须写入 `~/bench_workspace/workspace{i}/stage3/source_work/{source_type}/{source_name}/annotation_tool_logs/`。
- 工具运行摘要必须写入 `~/bench_workspace/workspace{i}/stage3/ANNOTATION_TOOL_RUN_REPORT.md`。
- 所有候选标注必须记录 `annotation_tool`、`tool_version_or_path`、`annotation_confidence`、`annotation_review_status=needs_human_review`、`derived_from_sample_id`。
- 对 simulator，工具输出只能用于一致性检查或辅助分析；若已有 `gt_availability=full_gt`，通常不应生成 `pseudo_annotations/simulator/{source_name}/`，除非计划明确说明审计目的。
- 对 existing_dataset，工具输出只能作为补充候选标注，不得覆盖原始 annotation provenance。
- 对 real_data，工具输出可以填补 annotation gap 的候选项，但评测可用状态仍应是 `NEEDS_REVIEW`，直到人工确认。

## 流程

```text
Stage 2 artifacts
-> /benchmark-data-cleaning-plan
-> /benchmark-datajuicer-config-gen
-> /benchmark-datajuicer-run-clean
-> /benchmark-semisupervised-annotation
-> /benchmark-cleaning-validate
-> /benchmark-unit-test-stage3
```

## Phase 0：读取上下文

必需检查：

- `~/benchclaw/data-juicer_card/DATAJUICER_AGENT_CAPABILITY_SPEC.md`
- `~/bench_workspace/workspace{i}/stage2/SOURCE_CAPABILITY_SURVEY.md`
- `~/bench_workspace/workspace{i}/stage2/COLLECTION_GUIDANCE_PLAN.md`
- `~/bench_workspace/workspace{i}/stage2/TEMPLATE_REFINEMENT_REPORT.md`
- `~/bench_workspace/workspace{i}/stage2/templates/*.yaml`
- `~/bench_workspace/workspace{i}/stage2/DATA_SCHEMA.md`
- `~/bench_workspace/workspace{i}/stage2/collected_data/`
- `~/bench_workspace/workspace{i}/stage2/DATA_QUALITY_REPORT.md`
- `~/bench_workspace/workspace{i}/stage2/STAGE2_SUMMARY.md`

同时检查 `DATAJUICER_AGENT_CAPABILITY_SPEC.md` 中声明的 Data-Juicer 调用方式，以及 `dj-process` 或用户指定的 `DATAJUICER_BIN` 是否可执行。若 capability spec 或可执行入口不可用，停止并说明环境阻塞。

## 统一输出

- `DATA_CLEANING_PLAN.md`
- `DATAJUICER_CAPABILITY_SUMMARY.md`
- `datajuicer_manifests/{source_type}_{source_name}_input.jsonl`
- `datajuicer_configs/{source_type}_{source_name}_clean.yaml`
- `source_work/{source_type}/{source_name}/datajuicer_manifest/input.jsonl`
- `source_work/{source_type}/{source_name}/datajuicer_config/clean.yaml`
- `annotation_tool_configs/{source_type}_{source_name}_{tool}.yaml`（按需）
- `run_datajuicer_cleaning.sh`
- `run_annotation_tools.sh`（按需）
- `DATAJUICER_CONFIG_INDEX.md`
- `ANNOTATION_TOOL_PLAN.md`（按需）
- `cleaned_data/{source_type}/{source_name}/`
- `source_work/{source_type}/{source_name}/cleaned_data/`
- `pseudo_annotations/{source_type}/{source_name}/`（兼容镜像，按需）
- `source_work/{source_type}/{source_name}/pseudo_annotations/`（existing_dataset / real_data 按需）
- `source_work/{source_type}/{source_name}/annotation_audit/`（simulator audit_only 按需）
- `rejected_samples/{source_type}_{source_name}_rejected.jsonl`
- `source_work/{source_type}/{source_name}/rejected_samples/rejected.jsonl`
- `CLEANING_LINEAGE.jsonl`
- `ANNOTATION_LINEAGE.jsonl`（按需）
- `DATAJUICER_RUN_REPORT.md`
- `ANNOTATION_TOOL_RUN_REPORT.md`（按需）
- `CLEANED_DATA_SCHEMA.md`
- `CLEANING_QUALITY_REPORT.md`
- `final/STAGE4_INPUT_MANIFEST.jsonl`
- `final/cleaned_data/`
- `final/CLEANED_DATA_SCHEMA.md`
- `STAGE3_UNIT_TEST_REPORT.md`
- `STAGE3_SUMMARY.md`

## 关键规则

- 不得为三类数据源拆出三套独立 skill。
- 不得在未读取 `DATAJUICER_AGENT_CAPABILITY_SPEC.md` 的情况下生成或运行 Data-Juicer 配置。
- Data-Juicer operator、YAML 字段、CLI 参数和验证规则必须可追溯到 `DATAJUICER_AGENT_CAPABILITY_SPEC.md`。
- 不得把三条线的中间文件混写到同一目录；中间产物必须按 `source_work/{source_type}/{source_name}/` 隔离。
- Stage4 调用前必须生成 `final/` 下的合并结果。
- 不得覆盖 Stage 2 原始数据。
- 不得删除 raw data。
- 不得把真实数据的推断标签写成 GT。
- 不得让 Data-Juicer 改写仿真器 GT、几何、pose、mask、trajectory。
- 不得让 `sam3`、`depthanything`、`yolo` 等工具输出覆盖原始标注或仿真器 GT。
- 不得把半监督标注工具作为仿真器 GT 的常规替代流程；仿真器数据优先使用程序真值。
- 半监督标注必须保留工具来源、置信度和人工复核状态。
- 每个 cleaned/rejected 样本必须能追溯到 raw sample。
- 没有 `CLEANING_QUALITY_REPORT.md` verdict 时，不得进入 Stage 4。
