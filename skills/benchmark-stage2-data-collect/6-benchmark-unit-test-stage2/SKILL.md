---
name: benchmark-unit-test-stage2
description: "Stage 2 Phase 6：单元测试。检查原始数据采集契约、三类数据源并行处理、图片与 JSON 一一对应、RAW_DATA_COLLECTION_REPORT.md 和禁止清洗框架/过滤规则。"
argument-hint: [stage2-dir]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob
---

## `~/benchclaw` 只读约束

- **BENCHCLAW_READONLY = true**：`~/benchclaw/` 只能作为共享只读资源根。
- 严禁在 `~/benchclaw/` 下创建、编辑、覆盖、删除、移动、重命名、复制写入、初始化 git、提交、打 tag、写日志、写缓存或写临时文件。
- 所有派生产物、补丁、快照、报告、脚本、配置、日志和测试输出必须写入 active `WORKSPACE_ROOT`。
- 如必须修改 `~/benchclaw/` 中的资源，只能在 workspace 中生成 patch 或修改建议，等待用户在外部处理；当前 skill 不得直接应用。

# Stage 2 单元测试

面向：*$ARGUMENTS*

本 phase 生成并执行 `stage2/unit_tests/test_stage2_contract.py`，输出 `results.json` 和 `STAGE2_UNIT_TEST_REPORT.md`。

## 测试输入

- `stage2/SOURCE_CAPABILITY_SURVEY.md`
- `stage2/COLLECTION_GUIDANCE_PLAN.md`
- `stage2/TEMPLATE_REFINEMENT_REPORT.md`
- `stage2/DATA_SCHEMA.md`
- `stage2/collected_data/`
- `stage2/RAW_DATA_COLLECTION_REPORT.md`
- `stage1/DATA_SOURCE_MAPPING.md`
- `~/benchclaw/simulator_cards/`
- `~/benchclaw/dataset_cards/`
- `~/benchclaw/realdata_cards/`

`~/benchclaw/` 只能作为只读测试输入。测试文件、结果、缓存、报告和临时文件都必须写入 `stage2/unit_tests/` 或其它当前 workspace 路径，不得写入 `~/benchclaw/`。

## 必测项

### 1. 固定产物存在

检查 Stage 2 必需文件是否存在，不得要求旧兼容产物或清洗阶段报告。

### 2. 三类数据源处理

根据 `DATA_SOURCE_MAPPING.md` 中实际出现的 `source_type`，检查对应 source 是否在报告、脚本目录和 `collected_data/` 中有记录。未启用的类型必须在报告中说明，不得伪造数据。

### 3. 图片与 JSON 一一对应

对每个 `collected_data/{source_type}/{source_name}/` 检查：

- `images/` 下的每张图片都有同编号 `records/{sample_id}.json`。
- `records/` 下的每个 JSON 都能对应到唯一图片。
- `manifest.jsonl` 每行都能同时定位图片和 JSON。
- `sample_id` 符合 `{source_type}_{source_name}_{000001}` 形式。
- 不得用 town、scene、shard 等子目录替代 `images/` 的平铺编号；这些信息应写入 JSON 字段。

### 4. 原始采集字段

每个 JSON 至少包含：

- `sample_id`
- `source_type`
- `source_name`
- `source_path`
- `capability_dimension`
- `source_role`
- `stage1_requirement_ref`
- `source_card_path`
- `source_card_fields_used`
- `image_path`
- `record_json_path`
- `gt_availability`
- `annotation_status`
- `raw_observation_flags`
- `integrity_notes`
- `annotation_gap`
- `needs_human_review`
- `provenance`
- `metadata`

### 5. 禁止 Stage 2 清洗过滤

测试必须扫描 Stage 2 产物，确认不存在以下行为声明或目录：

- 清洗配置目录
- `清洗阶段报告`
- Stage 2 执行清洗框架。
- Stage 2 清洗、过滤、质量拒收、去重删除可访问样本。
- 使用质量通过阈值决定是否进入 Stage 3。

允许出现“需要 Stage3 清洗/过滤/复核”的说明，但不能把这些动作作为 Stage2 已执行行为。

### 6. 数据源 card 契约

对每个启用 source 检查：

- `SOURCE_CAPABILITY_SURVEY.md`、`COLLECTION_GUIDANCE_PLAN.md`、模板、脚本配置、README、`RAW_DATA_COLLECTION_REPORT.md` 和样本 JSON/manifest 都记录同一个 `source_card_path`。
- `source_card_path` 必须位于对应根目录：`simulator` 对应 `~/benchclaw/simulator_cards/`，`existing_dataset` 对应 `~/benchclaw/dataset_cards/`，`real_data` 对应 `~/benchclaw/realdata_cards/`。
- 脚本和配置中的启动命令、endpoint、数据根目录、字段 schema、登记表、授权/隐私字段必须能追溯到 card 或显式用户 override。
- 如果 card 缺失，source 必须被标为 `NEEDS_CARD`、`NEEDS_CARD_DETAIL`、`NEEDS_USER_INPUT` 或 `BLOCKED`，不得伪造路径、字段或运行方式。

### 7. simulator 实采契约

对每个 `source_type=simulator` 的启用 source 检查：

- `RAW_DATA_COLLECTION_REPORT.md` 必须包含 `Simulator Runtime Evidence`，记录 `startup_command`、`simulator_started_at`、process/session、health check、`run_id/session_id` 和当前 run 样本数。
- 样本 JSON 和 manifest 必须记录当前 `run_id/session_id`、frame_id、scene/map/task、sensor config 或 seed；不得只有静态图片路径。
- `current_run_only` 必须为 `true`，`old_data_reuse` 必须为 `false`。
- `image_path`、`record_json_path`、`original_source_ref` 不得指向其它 workspace、下载目录、缓存目录、历史 `collected_data/` 或 card 未声明的外部输出目录。
- 如果 simulator 未启动、无 health check、无新 `run_id/session_id`，该 source 不能是 `PASS`。
- 如果报告发现 pre-existing files 被计入成功样本，或从旧目录复制图片/JSON，verdict 必须为 `FAIL`。

### 8. `~/benchclaw` 只读契约

测试必须检查 Stage 2 的脚本、配置、README、报告、manifest 和日志中不存在把 `~/benchclaw/` 作为输出、缓存、日志、临时文件、采集结果或写入目标的行为。若发现任何增删改 `~/benchclaw/` 的计划、命令或实际证据，verdict 必须为 `FAIL`。

## 报告格式

`STAGE2_UNIT_TEST_REPORT.md` 必须包含：

```markdown
# Stage 2 Unit Test Report

## Verdict
PASS / NEEDS_REVIEW / FAIL

## Raw-Only Contract
| Check | Result | Evidence |
|-------|--------|----------|

## File Contract
| Check | Result | Evidence |
|-------|--------|----------|

## Image-Record One-To-One Contract
| Source Type | Source Name | Images | Records | Manifest Rows | Result |
|-------------|-------------|--------|---------|---------------|--------|

## Source Coverage
| Source Type | Expected | Observed | Result |
|-------------|----------|----------|--------|

## Source Card Contract
| Source Type | Source Name | Card Path | Card Root Match | Card Referenced By Outputs | Runtime / Access Traceable | Result |
|-------------|-------------|-----------|-----------------|----------------------------|----------------------------|--------|

## Simulator Runtime Contract
| Source Name | Startup Evidence | Health Check | Run ID / Session ID | Current Run Only | Old Data Reuse | Result |
|-------------|------------------|--------------|---------------------|------------------|----------------|--------|

## Benchclaw Read-Only Contract
| Check | Result | Evidence |
|-------|--------|----------|

## Issues
| Severity | Path | Problem | Required Fix |
|----------|------|---------|--------------|

## Handoff
Stage 2 raw data can be handed to Stage 3 for cleaning, filtering, confidence improvement and readiness judgment.
```

## Verdict 规则

- `PASS`：固定产物、目录格式、一一对应、raw-only 契约全部通过；启用的 simulator 均有本轮启动/session 证据且没有旧数据复用。
- `NEEDS_REVIEW`：存在可解释缺口，但没有违反 raw-only 契约，用户可确认进入 Stage 3。
- `FAIL`：缺少关键产物、图片 JSON 不对应、manifest 无法追溯，Stage 2 出现清洗、过滤、质量拒收行为，启用 source 缺少可追溯 source card 却仍被标为成功，或 simulator 未启动/未创建新 session 却复用旧数据。
