---
name: benchmark-data-capability-survey
description: "Stage 2 Phase 1：数据能力调研。盘点 simulator、existing_dataset、real_data 三类数据源的可访问性、字段、资产、GT/标注状态和采集风险；只做调研，不采集、不清洗、不过滤。"
argument-hint: [stage1-dir]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, WebSearch, WebFetch
---

## `~/benchclaw` 只读约束

- **BENCHCLAW_READONLY = true**：`~/benchclaw/` 只能作为共享只读资源根。
- 严禁在 `~/benchclaw/` 下创建、编辑、覆盖、删除、移动、重命名、复制写入、初始化 git、提交、打 tag、写日志、写缓存或写临时文件。
- 所有派生产物、补丁、快照、报告、脚本、配置、日志和测试输出必须写入 active `WORKSPACE_ROOT`。
- 如必须修改 `~/benchclaw/` 中的资源，只能在 workspace 中生成 patch 或修改建议，等待用户在外部处理；当前 skill 不得直接应用。

# 数据能力调研

面向：*$ARGUMENTS*

本 phase 输出 `stage2/SOURCE_CAPABILITY_SURVEY.md`。它只盘点数据源能力和资产，不运行采集脚本，不生成清洗方案，不筛选样本。

## 输入

- `stage1/DATA_SOURCE_MAPPING.md`
- `stage1/CAPABILITY_SCOPE.md`
- `stage1/EVALSET_PROTOTYPE.md`
- `~/benchclaw/simulator_cards/`
- `~/benchclaw/dataset_cards/`
- `~/benchclaw/realdata_cards/`

## 数据源 card 读取规则

必须按 `DATA_SOURCE_MAPPING.md` 中的每个 source 读取对应 card：

`~/benchclaw/` 下所有 card 都是只读输入。严禁在 `~/benchclaw/` 内创建、编辑、覆盖、删除、移动、重命名任何文件或目录；如果 card 缺字段，只能在 `SOURCE_CAPABILITY_SURVEY.md` 中记录缺失项，不能回写 card。

- `source_type=simulator`：从 `~/benchclaw/simulator_cards/` 读取仿真器 card，确认启动方式、SDK/API、场景/地图/任务、传感器、GT 输出、依赖和采集命令。
- `source_type=existing_dataset`：从 `~/benchclaw/dataset_cards/` 读取数据集 card，确认数据根目录或访问方式、字段 schema、split、图片字段、QA/caption/label/metadata、原始 ID 和授权。
- `source_type=real_data`：从 `~/benchclaw/realdata_cards/` 读取真实数据 card，确认图片目录、登记表/清单、批次、授权/隐私、metadata 字段和标注缺口。

`SOURCE_CAPABILITY_SURVEY.md` 必须记录每个 source 的 `card_path`、`card_status`、card 中用到的证据字段和缺失项。若 card 不存在或无法读取，不得猜测运行方式、数据路径或字段 schema；必须标记为 `NEEDS_CARD` 或 `NEEDS_USER_INPUT`。

## 必须覆盖三类数据源

- `simulator`：仿真器名称、可运行接口、场景/地图/任务配置、可输出图像模态、可输出 GT、复现配置、已知采集风险。
- `existing_dataset`：数据集位置、样本规模、图像字段、文本/QA/label 字段、metadata 字段、授权状态、原始 ID、标注来源、缺失字段。
- `real_data`：真实图片来源、采集批次、授权/隐私状态、metadata 可用性、标注缺口、人工复核需求。

## source_name 规则

`source_name` 是稳定目录名，可以表示一次处理的数据批次、仿真器场景/地图/任务配置、已有数据集切片或真实采集批次。必须在同一 `source_type` 下唯一，并可用于后续 `collected_data/{source_type}/{source_name}/`。

## 输出格式

`SOURCE_CAPABILITY_SURVEY.md` 必须包含：

```markdown
# Source Capability Survey

## Source Inventory
| Source Type | Source Name | Capability Dimension | Card Path | Card Status | Asset / Interface | Access Status | GT / Annotation Status | Notes |
|-------------|-------------|----------------------|-----------|-------------|-------------------|---------------|------------------------|-------|

## Source Card Evidence
| Source Type | Source Name | Card Path | Runtime / Access Evidence | Schema / Field Evidence | License / Risk Evidence | Missing Card Items |
|-------------|-------------|-----------|---------------------------|-------------------------|-------------------------|--------------------|

## Simulator Sources
| Source Name | Card Path | Runtime / Startup | Scenario / Map / Task | Modalities | GT Fields | Reproducibility Config | Known Risks |
|-------------|-----------|-------------------|-----------------------|------------|-----------|------------------------|-------------|

## Existing Dataset Sources
| Source Name | Card Path | Dataset Root / Access Method | Dataset Slice | Image Fields | Text / QA / Label Fields | Metadata Fields | License | Missing Fields |
|-------------|-----------|------------------------------|---------------|--------------|--------------------------|-----------------|---------|----------------|

## Real Data Sources
| Source Name | Card Path | Batch / Location | Register Sheet / Image Root | Image Count Estimate | Metadata | Annotation Gap | Privacy / License | Review Need |
|-------------|-----------|------------------|-----------------------------|----------------------|----------|----------------|-------------------|-------------|

## Raw-Only Notes
Stage 2 will preserve accessible raw samples and record issues only. Cleaning, filtering, rejection and confidence improvement belong to Stage 3.
```

## 禁止事项

- 不得修改、补写、移动、删除或生成任何 `~/benchclaw/` 下的文件或目录。
- 不得生成清洗阶段报告。
- 不得提议在 Stage 2 执行任何清洗框架。
- 不得把缺失、重复、模糊、低置信度作为 Stage 2 删除理由。
