---
name: benchmark-template-refinement
description: "Stage 2 Phase 3：原始数据模板细化。为三类数据源生成统一 raw schema 和模板占位，不生成清洗框架模板，不做清洗过滤设计。"
argument-hint: [stage2-context]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob
---

## `~/benchclaw` 只读约束

- **BENCHCLAW_READONLY = true**：`~/benchclaw/` 只能作为共享只读资源根。
- 严禁在 `~/benchclaw/` 下创建、编辑、覆盖、删除、移动、重命名、复制写入、初始化 git、提交、打 tag、写日志、写缓存或写临时文件。
- 所有派生产物、补丁、快照、报告、脚本、配置、日志和测试输出必须写入 active `WORKSPACE_ROOT`。
- 如必须修改 `~/benchclaw/` 中的资源，只能在 workspace 中生成 patch 或修改建议，等待用户在外部处理；当前 skill 不得直接应用。

# 模板细化

面向：*$ARGUMENTS*

本 phase 输出 `stage2/TEMPLATE_REFINEMENT_REPORT.md` 和 `stage2/templates/{source_type}_{source_name}_RAW_TEMPLATE.yaml`。

## 输入

- `stage2/COLLECTION_GUIDANCE_PLAN.md`
- `stage2/SOURCE_CAPABILITY_SURVEY.md`
- `stage1/EVALSET_PROTOTYPE.md`
- `~/benchclaw/simulator_cards/`
- `~/benchclaw/dataset_cards/`
- `~/benchclaw/realdata_cards/`

必须读取 `COLLECTION_GUIDANCE_PLAN.md` 中的 `Source Card Basis`，并复核每个 source 的 `card_path`。模板字段不得凭空定义；运行方式、数据根目录、字段 schema、登记表、授权/隐私等 source-specific 字段必须来自对应 card 或显式用户补充。

`~/benchclaw/` 下的 source card 只能读取，不得修改、补写、移动、删除或生成派生 card。所有模板、报告和缓存都必须写入 `WORKSPACE_ROOT/stage2/`，不得写回 `~/benchclaw/`。

## 模板目标

模板用于统一记录原始样本，不用于清洗或筛选。模板必须覆盖：

- 图像路径和记录路径。
- 原始 source 信息。
- 能力维度。
- GT 或标注可用性。
- 原始 metadata。
- source card 路径、card 中使用过的字段和运行/访问依据。
- 问题标记字段。
- 后续 Stage 3 可读取的可追溯字段。

## 必备字段

每个样本记录模板必须包含：

```yaml
sample_id:
source_type:
source_name:
source_path:
capability_dimension:
source_role:
stage1_requirement_ref:
source_card_path:
source_card_fields_used: []
runtime_or_access_ref:
image_path:
record_json_path:
original_sample_id:
gt_availability:
annotation_status:
raw_observation_flags: []
integrity_notes: []
annotation_gap: []
access_error:
needs_human_review: false
provenance:
  collected_by:
  collected_at:
  script_or_method:
metadata: {}
raw_payload_refs: []
```

`sample_id` 使用 `{source_type}_{source_name}_{000001}` 格式递增。`source_name` 可以是数据批次、仿真器场景/地图/任务配置、已有数据集切片或真实采集批次。

## 输出报告结构

`TEMPLATE_REFINEMENT_REPORT.md` 必须包含：

```markdown
# Template Refinement Report

## Template List
| Source Type | Source Name | Template File | Purpose |
|-------------|-------------|---------------|---------|

## Unified Raw Record Fields
| Field | Required | Meaning | Stage3 Usage |
|-------|----------|---------|--------------|

## Source-Specific Extensions
| Source Type | Source Name | Extra Fields | Reason |
|-------------|-------------|--------------|--------|

## Source Card Field Mapping
| Source Type | Source Name | Card Path | Card Fields Used | Template Fields Added | Missing Items |
|-------------|-------------|-----------|------------------|-----------------------|---------------|

## Raw-Only Statement
These templates preserve raw collected data and issue flags only. They do not define cleaning or filtering behavior.
```

## 禁止事项

- 不得对 `~/benchclaw/` 下任何文件或目录做增删改。
- 不得写入任何清洗配置目录。
- 不得定义过滤阈值、质量通过阈值或删除策略。
- 不得把任何问题标记作为 Stage2 筛选字段；应使用 `raw_observation_flags` 记录观察到的问题。
