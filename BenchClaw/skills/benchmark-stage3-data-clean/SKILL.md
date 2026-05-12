---
name: benchmark-stage3-data-clean
description: "Stage 3 子流程：数据清洗、置信度提升、半监督候选标注与 Stage4 输入合并。编排清洗计划 → Data-Juicer 配置生成 → Data-Juicer 清洗执行 → 半监督候选标注 → 清洗验证与 final 合并 → Stage 3 单元测试。基于 Stage 2 的 raw data、schema、manifest 和采集报告，同一套流程处理 simulator、existing_dataset、real_data；目标是提升图文数据进入 benchmark 前的可信度、可追溯性和可复核性。"
argument-hint: [stage2-dir]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Skill
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

# Benchmark Stage 3: 数据清洗与置信度提升

面向：*$ARGUMENTS*

本 skill 是 Stage 3 的总控编排器，按 Stage1、Stage2 同样的 phase-by-phase 方式调度 Stage 3 子 skill。它必须继承 Stage 2 的 `source_type`、`source_name`、`sample_id` 和图像/JSON 一一对应关系，在同一套流程中处理 `simulator`、`existing_dataset`、`real_data`。

Stage 3 的核心目标不是重新采集数据，也不是伪造真值，而是提升 Stage 2 已采集图文数据的可信度、可用性、可追溯性和可复核性，并产出 Stage 4 可读取的 `stage3/final/` 合并结果。

## Overview

```text
Stage 2 artifacts
  |
  v
[1 清洗与半监督标注计划]
  |
  v
[2 Data-Juicer 配置与 manifest 生成]
  |
  v
[3 Data-Juicer 清洗执行]
  |
  v
[4 半监督候选标注 / audit]
  |
  v
[5 清洗验证与 final 合并]
  |
  v
[6 Stage 3 单元测试]
  |
  v
STAGE3_SUMMARY.md
```

每个 phase 都必须建立在前序产物之上，不可跳过。若 Data-Juicer 能力规格、Stage2 原始数据或前序报告缺失，必须停止并报告阻塞，不得凭经验臆造配置或产物。

## Workspace

- 当前运行目录为 `WORKSPACE_ROOT = ~/bench_workspace/workspace{i}`。
- Stage 3 必须继承 `/benchmark-pipeline`、Stage 1 或 Stage 2 已经创建并使用的 active `WORKSPACE_ROOT`，不得自行创建新的 `workspace{i}`，不得自动切换到序号最高的旧 workspace。
- 所有 Stage 3 中间过程文件、Data-Juicer manifest/config、清洗输出、annotation-tool 输出、日志、测试文件和报告都必须写入 `WORKSPACE_ROOT/stage3/`。
- 只能读写当前 workspace 的 `stage2/` 和 `stage3/` 目录。
- 允许只读访问明确需要的全局资源：`~/benchclaw/data-juicer_card/`、`~/benchclaw/annotation-tool/`、`~/benchclaw/templates/`、`~/benchclaw/skills/`。
- `~/benchclaw/` 下任何内容都不能被创建、编辑、覆盖、删除、移动、重命名、复制写入或作为日志/缓存/临时输出目录；工具输出和派生配置必须写入 `WORKSPACE_ROOT/stage3/`。
- 不得读取、复用、比较或借鉴其它 `workspace{j}` 的产物，除非用户明确指定路径和复用范围。
- 不得把 Stage 3 运行产物写入 skill 源码目录、Downloads、当前项目目录、缓存目录或任意非 active workspace 路径。

## Constants

- **CONFIDENCE_FIRST = true**：每个 phase 必须说明如何提升或证明图文数据置信度。
- **NO_RAW_OVERWRITE = true**：不得覆盖或删除 Stage 2 原始数据。
- **DATAJUICER_SPEC_REQUIRED = true**：所有 Data-Juicer 计划、配置和执行必须先读取 `~/benchclaw/data-juicer_card/DATAJUICER_AGENT_CAPABILITY_SPEC.md`。
- **NO_BENCHCLAW_WRITE = true**：`~/benchclaw/` 下所有内容只读，严禁增删改。
- **PSEUDO_IS_NOT_GT = true**：`sam3`、`depthanything`、`yolo` 等工具输出只能作为候选标注或审计信号，不得写成 GT。
- **ONE_IMAGE_ONE_METADATA = true**：Stage3 final 中每张标准图片必须有一个同 basename 的 metadata JSON。
- **STAGE_BOUNDARY_STOP = true**：Stage 3 完成 `STAGE3_SUMMARY.md` 后必须停止，由用户选择下一步；不得自动进入 Stage 4。

## Stage 3 置信度提升总目标

Stage 3 的每一步都必须回答：“本步骤如何提升或证明图文数据置信度？”

置信度提升证据可以来自：

- 图片质量检查、异常样本隔离、重复检测。
- 文本、QA、caption、label、metadata 标准化。
- 图文一致性检查。
- annotation provenance 保护。
- 仿真器 GT、pose、mask、trajectory、几何字段的 copy-only 保护。
- 半监督候选标注的工具来源、阈值、置信度和人工复核状态。
- lineage 完整性和 Stage4 readiness 判断。

任何无法通过证据提升置信度的样本，必须标记为 `NEEDS_REVIEW`、`rejected` 或保留明确风险说明；不得进入 `stage4_ready_status=ready`。

## 三类数据源清洗策略

| source_type | Stage 3 目标 | 禁止行为 |
|-------------|--------------|----------|
| `simulator` | 保留程序 GT、pose、mask、trajectory、几何字段和对齐索引；清洗文本、metadata、manifest；可做 GT/图像一致性 audit | 不得让 Data-Juicer 或 annotation-tool 改写 GT；不得生成替代 pseudo GT |
| `existing_dataset` | 清洗 QA、caption、label、metadata；去重；验证图文/标注一致性；保留原始 ID 和 annotation provenance；可生成候选 mask/depth/detection | 不得丢失 annotation provenance；不得把工具预测补成原始标注 |
| `real_data` | 清洗图片质量、重复样本、metadata 和已有说明；维护 annotation gap 和人工复核队列；可生成候选标注 | 不得把 pseudo annotation 当真值；缺少人工确认时不得自动 ready |

Stage 3 必须沿用 Stage 2 的 `source_name`，不得重新命名 source。所有中间产物必须按 `source_work/{source_type}/{source_name}/` 隔离，最后再合并到 `final/`。

## Required Stage 2 Inputs

必须读取：

- `stage2/SOURCE_CAPABILITY_SURVEY.md`
- `stage2/COLLECTION_GUIDANCE_PLAN.md`
- `stage2/TEMPLATE_REFINEMENT_REPORT.md`
- `stage2/templates/*.yaml`
- `stage2/DATA_SCHEMA.md`
- `stage2/collected_data/`
- `stage2/RAW_DATA_COLLECTION_REPORT.md`
- `stage2/STAGE2_SUMMARY.md`

还必须读取：

- `~/benchclaw/data-juicer_card/DATAJUICER_AGENT_CAPABILITY_SPEC.md`

若 capability spec 缺失或不可读，Stage 3 不得生成或运行 Data-Juicer 配置。

## Pipeline

### Phase 1: Data Cleaning Plan — 清洗与半监督标注计划

调用：

```text
/1-benchmark-data-cleaning-plan "$STAGE2_DIR"
```

输入：

- Stage 2 全部固定产物。
- `DATAJUICER_AGENT_CAPABILITY_SPEC.md`。
- 可选 `~/benchclaw/annotation-tool/` 工具目录。

执行内容：

- 读取 Stage 2 的全部 source，按 `simulator`、`existing_dataset`、`real_data` 并行或等价并行制定清洗策略。
- 从 Data-Juicer capability spec 中提取可用 operator、manifest/YAML/CLI 结构、字段保护规则和验证规则。
- 为每个 source 指定置信度提升目标：图片质量、文本质量、图文一致性、标注完整性、metadata 完整性、去重状态、lineage 完整性和人工复核需求。
- 规划 copy-only 字段，尤其是仿真器 GT、pose、mask、trajectory、几何字段和原始 annotation provenance。
- 按需规划 `sam3`、`depthanything`、`yolo` 等 annotation-tool 候选标注；默认优先用于 `existing_dataset` 和 `real_data`，`simulator` 只允许 audit_only。

输出：

- `stage3/DATA_CLEANING_PLAN.md`

该文件必须包含：

- `Data-Juicer Capability Summary`
- `Source-Type Cleaning Summary`
- `Confidence Improvement Plan`
- `Simulator Cleaning Policy`
- `Existing Dataset Cleaning Policy`
- `Real Data Cleaning Policy`
- `Data-Juicer Operator Plan`
- `Annotation Tool Plan`
- `Non-Data-Juicer Handling`
- `Output Mapping`
- `Source Work Directories`
- `Acceptance Criteria`

Checkpoint：

- 不生成 YAML、manifest 或 cleaned_data。
- 每个 operator 都必须能追溯到 `DATAJUICER_AGENT_CAPABILITY_SPEC.md`。
- 每个 source 都必须有清洗目标、保护字段和输出映射。

### Phase 2: Data-Juicer Config Generation — 配置与 manifest 生成

调用：

```text
/2-benchmark-datajuicer-config-gen "$STAGE3_CONTEXT"
```

输入：

- `stage3/DATA_CLEANING_PLAN.md`
- Stage 2 `collected_data/`、`DATA_SCHEMA.md`、templates 和采集报告。
- `DATAJUICER_AGENT_CAPABILITY_SPEC.md`

执行内容：

- 为每个 source 生成 Data-Juicer input manifest 和 clean YAML。
- 将 manifest/config 同时写入根目录索引位置和 `source_work/{source_type}/{source_name}/` 权威中间目录。
- 生成 `run_datajuicer_cleaning.sh` 和 `DATAJUICER_CONFIG_INDEX.md`。
- 按计划生成 annotation-tool 配置和 `run_annotation_tools.sh`，但本 phase 不执行工具。
- 静态校验 operator、YAML 字段、CLI 参数、copy-only 字段和输出路径是否符合 capability spec。

输出：

- `stage3/datajuicer_manifests/{source_type}_{source_name}_input.jsonl`
- `stage3/datajuicer_configs/{source_type}_{source_name}_clean.yaml`
- `stage3/source_work/{source_type}/{source_name}/datajuicer_manifest/input.jsonl`
- `stage3/source_work/{source_type}/{source_name}/datajuicer_config/clean.yaml`
- `stage3/run_datajuicer_cleaning.sh`
- `stage3/DATAJUICER_CONFIG_INDEX.md`
- `stage3/annotation_tool_configs/{source_type}_{source_name}_{tool}.yaml`（按需）
- `stage3/run_annotation_tools.sh`（按需）
- `stage3/ANNOTATION_TOOL_PLAN.md`（按需）

Checkpoint：

- 每个 source 都必须有 manifest/config，或有明确跳过理由。
- 输出不得覆盖 `stage2/collected_data/`。
- annotation-tool 配置只能生成 `pseudo_annotation` 或 audit 信号，不得覆盖 GT、原始 label 或 annotation provenance。

### Phase 3: Data-Juicer Run Clean — 清洗执行

调用：

```text
/3-benchmark-datajuicer-run-clean "$STAGE3_CONTEXT"
```

输入：

- `stage3/DATAJUICER_CONFIG_INDEX.md`
- `stage3/datajuicer_configs/*.yaml`
- `stage3/datajuicer_manifests/*.jsonl`
- `stage3/run_datajuicer_cleaning.sh`
- `DATAJUICER_AGENT_CAPABILITY_SPEC.md`

执行内容：

- 按统一配置索引并行或等价并行运行三类数据源的清洗任务。
- 记录每个 source 的 Data-Juicer binary、CLI 参数、operator 统计、输入输出路径和退出状态。
- 将 cleaned samples、rejected samples、logs 和 lineage 写入 `source_work/{source_type}/{source_name}/`。
- 保留 rejected/review reason，不得只删除样本而不解释置信度风险。
- 本 phase 不运行 annotation-tool，不生成 pseudo_annotations。

输出：

- `stage3/source_work/{source_type}/{source_name}/cleaned_data/`
- `stage3/source_work/{source_type}/{source_name}/rejected_samples/rejected.jsonl`
- `stage3/source_work/{source_type}/{source_name}/datajuicer_logs/run.log`
- `stage3/CLEANING_LINEAGE.jsonl`
- `stage3/DATAJUICER_RUN_REPORT.md`

Checkpoint：

- 每个 cleaned/rejected 样本必须可追溯到 Stage 2 raw sample。
- 若某 source 清洗失败、输出为空或无法证明置信度提升，必须标记为 `FAIL` 或 `NEEDS_REVIEW`。

### Phase 4: Semi-Supervised Annotation — 半监督候选标注与审计

调用：

```text
/4-benchmark-semisupervised-annotation "$STAGE3_CONTEXT"
```

输入：

- `stage3/DATA_CLEANING_PLAN.md`
- `stage3/ANNOTATION_TOOL_PLAN.md`（若存在）
- `stage3/annotation_tool_configs/`（若存在）
- `stage3/run_annotation_tools.sh`（若存在）
- `stage3/source_work/{source_type}/{source_name}/cleaned_data/`
- `ANNOTATION_TOOL_HOME=~/benchclaw/annotation-tool`

执行内容：

- 按计划调用 `sam3`、`depthanything`、`yolo` 等工具生成候选标注或审计信号。
- `existing_dataset` 和 `real_data` 的工具输出写入 `pseudo_annotations/`，并标记 `annotation_review_status=needs_human_review`。
- `simulator` 默认不补标；若计划要求工具输出，必须是 `audit_only`，写入 `annotation_audit/`。
- 每条候选标注必须记录工具来源、版本、置信度、阈值、失败/跳过原因、原始样本 lineage。
- 若工具产生与原图不同的派生图片，如 YOLO 画框图、深度图、mask overlay、裁剪图或诊断图，必须保存派生图片路径，并在后续 final metadata 中声明。

输出：

- `stage3/source_work/{source_type}/{source_name}/pseudo_annotations/`（existing_dataset / real_data 按需）
- `stage3/source_work/{source_type}/{source_name}/annotation_audit/`（simulator audit_only 按需）
- `stage3/source_work/{source_type}/{source_name}/annotation_tool_logs/`
- `stage3/ANNOTATION_LINEAGE.jsonl`（按需）
- `stage3/ANNOTATION_TOOL_RUN_REPORT.md`（按需）

Checkpoint：

- 不把工具输出当作 GT。
- 不覆盖 cleaned image、Stage2 原图或原始 annotation。
- 若工具不可用，写入报告并标记 `NEEDS_REVIEW`，不得伪造输出。

### Phase 5: Cleaning Validate And Final Merge — 清洗验证与 Stage4 输入合并

调用：

```text
/4-benchmark-cleaning-validate "$STAGE3_CONTEXT"
```

说明：当前目录名是 `4-benchmark-cleaning-validate`，但逻辑上它是 Stage 3 的 Phase 5，位于半监督候选标注之后、单元测试之前。

输入：

- `stage3/DATA_CLEANING_PLAN.md`
- `stage3/DATAJUICER_CONFIG_INDEX.md`
- `stage3/DATAJUICER_RUN_REPORT.md`
- `stage3/ANNOTATION_TOOL_RUN_REPORT.md`（若存在）
- `stage3/CLEANING_LINEAGE.jsonl`
- `stage3/ANNOTATION_LINEAGE.jsonl`（若存在）
- `stage3/source_work/{source_type}/{source_name}/`

执行内容：

- 验证三类数据的 source_work 中间产物、GT/annotation 保护、pseudo annotation 状态、schema 兼容性和 lineage 完整性。
- 将三类数据合并到 `stage3/final/`，作为 Stage4 唯一权威输入。
- 为每个进入 Stage4 的样本写出最终标准图片和同 basename metadata JSON。
- 如果存在派生图片，写入 `processed_images/{sample_id}_{derived_type}.{ext}`，并在 metadata 的 `processed_images[]` 中记录原图、派生图、工具、目的和对齐状态。
- 生成 `final/STAGE4_INPUT_MANIFEST.jsonl`，每条样本必须说明为什么可以进入 Stage4，或为什么仍需复核。

输出：

- `stage3/CLEANING_QUALITY_REPORT.md`
- `stage3/final/cleaned_data/{source_type}/{source_name}/images/{sample_id}.{ext}`
- `stage3/final/cleaned_data/{source_type}/{source_name}/metadata/{sample_id}.json`
- `stage3/final/cleaned_data/{source_type}/{source_name}/processed_images/{sample_id}_{derived_type}.{ext}`（按需）
- `stage3/final/rejected_samples/`
- `stage3/final/pseudo_annotations/`（按需）
- `stage3/final/CLEANED_DATA_SCHEMA.md`
- `stage3/final/CLEANING_LINEAGE.jsonl`
- `stage3/final/ANNOTATION_LINEAGE.jsonl`（按需）
- `stage3/final/STAGE4_INPUT_MANIFEST.jsonl`

Checkpoint：

- `CLEANING_QUALITY_REPORT.md` 必须以图文数据置信度是否足以进入 Stage4 作为 verdict 依据。
- final 中每张标准图片必须有一个同 basename metadata JSON。
- 半监督工具输出缺少人工确认时只能作为 `NEEDS_REVIEW` 或辅助候选，不得作为真值通过。

### Phase 6: Unit Test — Stage 3 契约单元测试

调用：

```text
/5-benchmark-unit-test-stage3 "$STAGE3_DIR"
```

输入：

- Stage 3 全部计划、配置、运行报告、source_work 中间产物和 `final/` 合并产物。
- `stage3/CLEANING_QUALITY_REPORT.md`
- `stage3/final/STAGE4_INPUT_MANIFEST.jsonl`

执行内容：

- 生成并执行 `stage3/unit_tests/test_stage3_contract.py`。
- 检查同一套测试入口是否覆盖 `simulator`、`existing_dataset`、`real_data`。
- 检查 source_work 分流目录、Data-Juicer 配置、运行结果、pseudo annotation、lineage、schema 和质量报告。
- 检查 final 合并结果：每张图片一个 metadata JSON，派生图片不覆盖原图，manifest 字段完整。
- 检查 ready 样本是否具备 `confidence_evidence`、`confidence_status`、`review_reason`、quality/consistency/lineage 依据。

输出：

- `stage3/unit_tests/test_stage3_contract.py`
- `stage3/unit_tests/results.json`
- `stage3/STAGE3_UNIT_TEST_REPORT.md`

Verdict 规则：

- `PASS`：三类清洗契约、分流中间产物、置信度证据和 final 合并结果均满足，可进入 Stage 4。
- `NEEDS_REVIEW`：存在可解释缺口，但 GT 未被破坏、lineage 未断裂、final 入口可追溯，用户可确认 waiver。
- `FAIL`：GT 被破坏、lineage 缺失、schema 不兼容、final 合并缺失、图片与 metadata 不一一对应、置信度证据缺失、派生图片未声明、Data-Juicer spec 不可追溯，或 annotation-tool 输出覆盖 GT/被标为真值。

### Final Summary

完成 Phase 6 后必须写入：

- `stage3/STAGE3_SUMMARY.md`

`STAGE3_SUMMARY.md` 必须包含：

```markdown
# Stage3 Summary

## Executive Summary

## Phase Results
### Phase 1: Data Cleaning Plan
### Phase 2: Data-Juicer Config Generation
### Phase 3: Data-Juicer Run Clean
### Phase 4: Semi-Supervised Annotation
### Phase 5: Cleaning Validate And Final Merge
### Phase 6: Unit Test

## Source Type Results
| Source Type | Source Name | Cleaned Samples | Rejected Samples | Needs Review | Ready Samples | Notes |
|-------------|-------------|-----------------|------------------|--------------|---------------|-------|

## Confidence Improvement Evidence
| Source Type | Source Name | Evidence | Stage4 Ready Impact |
|-------------|-------------|----------|---------------------|

## Final Deliverables

## Handoff To Stage 4
```

Stage 3 完成后必须停在这里，展示下一步选项：

1. Proceed to Stage 4
2. Rerun a Stage 3 phase
3. Review cleaned data, confidence report, final manifest, or tests
4. Pause pipeline

不得自动调用 `/benchmark-stage4-build`。即使 Gate 3 为 `PASS`，也只能说明“可以进入 Stage 4”，必须等待用户选择。

## Gate 3 — Confidence And Stage4 Readiness Checkpoint

进入 Stage 4 前必须满足：

- `STAGE3_UNIT_TEST_REPORT.md` verdict 为 `PASS`，或为 `NEEDS_REVIEW` 且用户明确确认 waiver。
- `CLEANING_QUALITY_REPORT.md` 存在，并给出统一 verdict。
- `stage3/final/STAGE4_INPUT_MANIFEST.jsonl` 存在。
- `stage3/final/cleaned_data/{source_type}/{source_name}/images/` 与 `metadata/` 一一对应。
- 每个 ready 样本都有 `confidence_evidence`、`confidence_status`、`review_reason` 和 lineage。
- 派生图片若存在，必须保存在 `processed_images/`，并在 metadata 中声明。

若 verdict 为 `FAIL`，不得进入 Stage 4；必须根据报告回退到对应 phase 修复。

## 重新执行 Stage 3 的触发条件

| 问题 | 回退 phase |
|------|------------|
| Data-Juicer capability spec 缺失或清洗目标不清晰 | Phase 1 |
| YAML、manifest、operator、copy-only 字段配置错误 | Phase 2 |
| Data-Juicer 运行失败、输出为空或 lineage 缺失 | Phase 3 |
| 半监督候选标注缺工具来源、置信度或人工复核状态 | Phase 4 |
| final 合并缺失、一图一 metadata 不成立或 Stage4 manifest 不完整 | Phase 5 |
| 单元测试发现契约不一致 | Phase 6 |

## Key Rules

- **Do not skip phases.** 6 个逻辑 phase 严格顺序执行。
- **Confidence first.** 每个 phase 都必须留下置信度提升或验证证据。
- **Same skill set for three source types.** 三类数据源不得拆成三套独立阶段。
- **Protect raw data.** 不得覆盖或删除 Stage2 原始图片和单图 JSON。
- **Never write to `~/benchclaw/`.** Data-Juicer spec、annotation-tool、templates 和 skills 只能只读；所有 manifest、config、logs、pseudo annotations 和 reports 必须写入 active workspace。
- **Protect GT and annotation provenance.** Data-Juicer 和 annotation-tool 不得改写仿真器 GT 或原始标注来源。
- **Pseudo is not GT.** 半监督工具输出只能是候选标注或 audit 信号，必须记录工具来源、置信度和人工复核状态。
- **One final image, one metadata JSON.** final 中每张标准图片必须有同 basename metadata。
- **Derived images are separate.** YOLO 画框图、深度图、mask overlay、裁剪图、诊断图等派生图片必须独立保存并写入 metadata。
- **Stage4 reads final only.** Stage4 优先读取 `stage3/final/STAGE4_INPUT_MANIFEST.jsonl` 和 `stage3/final/cleaned_data/`，不得把 source_work 当作唯一入口。
- **Stage boundary stop.** Stage 3 完成后必须停住，展示下一步选项，等待用户选择；不得自动进入 Stage 4。

## Fixed Artifact Format Contract

```text
stage3/
  DATA_CLEANING_PLAN.md
  DATAJUICER_CONFIG_INDEX.md
  DATAJUICER_RUN_REPORT.md
  ANNOTATION_TOOL_PLAN.md                       # 按需
  ANNOTATION_TOOL_RUN_REPORT.md                 # 按需
  datajuicer_manifests/{source_type}_{source_name}_input.jsonl
  datajuicer_configs/{source_type}_{source_name}_clean.yaml
  annotation_tool_configs/{source_type}_{source_name}_{tool}.yaml  # 按需
  run_datajuicer_cleaning.sh
  run_annotation_tools.sh                       # 按需
  source_work/{source_type}/{source_name}/datajuicer_manifest/input.jsonl
  source_work/{source_type}/{source_name}/datajuicer_config/clean.yaml
  source_work/{source_type}/{source_name}/cleaned_data/
  source_work/{source_type}/{source_name}/rejected_samples/rejected.jsonl
  source_work/{source_type}/{source_name}/datajuicer_logs/run.log
  source_work/{source_type}/{source_name}/pseudo_annotations/       # existing_dataset / real_data 按需
  source_work/{source_type}/{source_name}/annotation_audit/          # simulator audit_only 按需
  source_work/{source_type}/{source_name}/annotation_tool_logs/      # 按需
  CLEANING_LINEAGE.jsonl
  ANNOTATION_LINEAGE.jsonl                     # 按需
  CLEANING_QUALITY_REPORT.md
  final/CLEANED_DATA_SCHEMA.md
  final/CLEANING_LINEAGE.jsonl
  final/ANNOTATION_LINEAGE.jsonl               # 按需
  final/STAGE4_INPUT_MANIFEST.jsonl
  final/rejected_samples/
  final/pseudo_annotations/                    # 按需
  final/cleaned_data/{source_type}/{source_name}/images/{sample_id}.{ext}
  final/cleaned_data/{source_type}/{source_name}/metadata/{sample_id}.json
  final/cleaned_data/{source_type}/{source_name}/processed_images/{sample_id}_{derived_type}.{ext}  # 按需
  unit_tests/test_stage3_contract.py
  unit_tests/results.json
  STAGE3_UNIT_TEST_REPORT.md
  STAGE3_SUMMARY.md
```

`metadata/{sample_id}.json` 必须至少包含：

```json
{
  "sample_id": "...",
  "source_type": "...",
  "source_name": "...",
  "original_image_path": "...",
  "final_image_path": "...",
  "record_json_path": "...",
  "processed_images": [],
  "cleaned_path": "...",
  "gt_availability": "...",
  "annotation_status": "...",
  "lineage_id": "...",
  "confidence_evidence": [],
  "confidence_status": "...",
  "review_reason": "...",
  "stage4_ready_status": "ready | needs_review | rejected"
}
```

`final/STAGE4_INPUT_MANIFEST.jsonl` 每行必须包含 `source_type`、`source_name`、`sample_id`、`final_image_path`、`metadata_json_path`、`record_json_path`、`processed_image_paths`、`lineage_id`、`confidence_evidence`、`confidence_status`、`review_reason` 和 `stage4_ready_status`。没有派生图片时，`processed_image_paths` 必须为 `[]`。
