---
name: benchmark-stage2-data-collect
description: "Stage 2 子流程：原始数据采集、已有数据集接入与真实数据登记。编排数据能力调研 → 采集指导 → 原始模板细化 → 采集代码生成 → 批量真实采集 → Stage 2 单元测试。基于 Stage 1 的能力维度、数据源映射、benchmark 草稿和评测原型，同一套流程并行处理 simulator、existing_dataset、real_data；只保存原始数据和问题标记，不做清洗、过滤或质量拒收。"
argument-hint: [stage1-dir]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, WebSearch, WebFetch, Skill
---

## `~/benchclaw` 只读约束

- **BENCHCLAW_READONLY = true**：`~/benchclaw/` 只能作为共享只读资源根。
- 严禁在 `~/benchclaw/` 下创建、编辑、覆盖、删除、移动、重命名、复制写入、初始化 git、提交、打 tag、写日志、写缓存或写临时文件。
- 所有派生产物、补丁、快照、报告、脚本、配置、日志和测试输出必须写入 active `WORKSPACE_ROOT`。
- 如必须修改 `~/benchclaw/` 中的资源，只能在 workspace 中生成 patch 或修改建议，等待用户在外部处理；当前 skill 不得直接应用。

# Benchmark Stage 2: 原始数据采集与接入

面向：*$ARGUMENTS*

本 skill 是 Stage 2 的总控编排器。它仿照 Stage 1 的 phase-by-phase 方式，顺序调用 6 个 Stage 2 子 skill，并在每个 phase 中保持三类数据源 `simulator`、`existing_dataset`、`real_data` 使用同一套流程并行或等价并行处理。

Stage 2 只负责真实采集、接入和登记原始数据。它不负责清洗、过滤、去重删除、置信度提升、样本拒收或 Stage 4 readiness 判断；这些工作属于 Stage 3。

## Overview

```text
Stage 1 artifacts
  |
  v
[1 数据能力调研]
  |
  v
[2 采集与接入指导]
  |
  v
[3 原始模板细化]
  |
  v
[4 采集/接入/登记代码生成]
  |
  v
[5 批量真实采集与格式校验]
  |
  v
[6 Stage 2 单元测试]
  |
  v
STAGE2_SUMMARY.md
```

每个 phase 都必须建立在前序 phase 的输出之上，不可跳过、乱序或凭空补产物。若前序产物缺失，必须停止并报告缺失路径。

## Workspace

- 当前运行目录为 `WORKSPACE_ROOT = ~/bench_workspace/workspace{i}`。
- Stage 2 必须继承 `/benchmark-pipeline` 或 Stage 1 已经创建的 active `WORKSPACE_ROOT`，不得自行创建新的 `workspace{i}`，不得自动切换到序号最高的旧 workspace。
- 所有 Stage 2 中间过程文件、采集脚本、配置、日志、manifest、测试文件、报告和 raw data 都必须写入 `WORKSPACE_ROOT/stage2/`。
- 只能读写当前 workspace 的 `stage1/` 和 `stage2/` 目录。
- 允许只读访问明确需要的全局资源，例如 `~/benchclaw/simulator_cards/`、`~/benchclaw/dataset_cards/`、`~/benchclaw/realdata_cards/`。
- `~/benchclaw/` 下任何内容都不能被创建、编辑、覆盖、删除、移动、重命名、复制写入或作为日志/缓存/临时输出目录；source card 只能读取和引用路径。
- 不得扫描、复用、比较或借鉴其它 `workspace{j}` 的产物，除非用户明确指定路径和复用范围。
- 不得把 Stage 2 运行产物写入 skill 源码目录、Downloads、当前项目目录、缓存目录或任意非 active workspace 路径。

## Constants

- **RAW_ONLY = true**：Stage 2 只能保存原始数据和问题标记。
- **NO_FILTERING = true**：不得因为质量、重复、缺少 GT、标注缺口或低置信度删除可访问样本。
- **NO_PLACEHOLDER = true**：不得用 placeholder、dummy、mock、fake、示例图、空 JSON 或模板 JSON 冒充真实采集结果。
- **SOURCE_TYPES = simulator, existing_dataset, real_data**：三个 source_type 使用同一套 Phase 1-6 skill，并行或等价并行处理。
- **SOURCE_CARDS_REQUIRED = true**：制定采集计划、细化模板、生成脚本和执行采集前，必须读取对应数据源 card。
- **SOURCE_CARD_ROOTS**：`~/benchclaw/simulator_cards/`、`~/benchclaw/dataset_cards/`、`~/benchclaw/realdata_cards/`。
- **NO_BENCHCLAW_WRITE = true**：`~/benchclaw/` 是只读共享资源根，严禁对其中任何文件或目录做增删改。
- **SIMULATOR_MUST_START = true**：启用的 simulator source 在 Phase 5 必须按 card 启动仿真器或创建新的仿真 session，并从该 session 实际采集。
- **NO_OLD_DATA_REUSE = true**：不得从其它 workspace、其它文件夹、历史 `collected_data/`、缓存目录或旧运行产物复制/搬运/登记样本来冒充本轮采集。
- **STAGE_BOUNDARY_STOP = true**：Stage 2 完成 `STAGE2_SUMMARY.md` 后必须停止，由用户选择下一步；不得自动进入 Stage 3。

## Stage 2 核心规则

只要样本在法律和技术上可访问，就必须进入 `collected_data/`。问题只能记录为 `raw_observation_flags`、`integrity_notes`、`annotation_gap`、`access_error`、`needs_human_review` 等字段。

Stage 2 禁止：

- 运行清洗框架或生成清洗阶段配置。
- 清洗、过滤、去重删除、质量拒收或置信度筛选样本。
- 因为模糊、重复、缺少 GT、标注缺失、低置信度、不完整而丢弃可访问样本。
- 明明有数据源可访问，却用占位数据冒充采集成功。
- 对 simulator source，不启动仿真器、不创建新运行 session，却复用旧图片或其它目录产物冒充本轮采集。

## 三类数据源统一处理

| source_type | 含义 | Stage 2 目标 | 禁止行为 |
|-------------|------|--------------|----------|
| `simulator` | 仿真器数据 | 启动仿真器或创建新仿真 session，采集本轮新生成的图像、多模态观测和原始 GT 引用 | 不得因 GT 对齐差而删除样本；不得复用旧数据冒充新采集 |
| `existing_dataset` | 已有 benchmark 数据集 | 接入已有图片、QA、caption、label、metadata，映射到统一 raw schema | 不得伪造成仿真器级 GT，不得清洗过滤 |
| `real_data` | 真实数据 | 登记真实图片和不完整记录，保存 metadata、授权和标注缺口 | 不得把推断结果当作真值，不得质量拒收 |

`source_name` 是某个 source 分支的稳定目录名和标识符。它可以表示一次处理的数据批次、一个仿真器场景/地图/任务配置、一个已有数据集切片或一个真实采集批次；不要求等于官方数据源名称。它必须在同一 `source_type` 下唯一，并在目录、manifest、JSON 记录、报告和日志中保持一致。

## 数据源 Cards 强制读取规则

Stage 2 的采集计划不能只依赖 Stage 1 的抽象映射。每个 source 都必须回到对应 card 获取真实可执行信息：

所有 `~/benchclaw/*_cards/` 只能只读；不得为了补齐信息而修改 card、生成新 card、移动 card 或向 `~/benchclaw/` 写入任何派生文件。缺失信息必须记录为 `NEEDS_CARD`、`NEEDS_CARD_DETAIL` 或 `NEEDS_USER_INPUT`。

- `simulator` 必须读取 `~/benchclaw/simulator_cards/` 中对应 card，确认仿真器启动方式、SDK/API、依赖、场景/地图/任务、传感器、可输出 GT、采集命令和运行限制。
- `existing_dataset` 必须读取 `~/benchclaw/dataset_cards/` 中对应 card，确认数据集根目录或下载/访问方式、字段 schema、split、图片字段、QA/caption/label/metadata、原始 ID、授权和缺失字段。
- `real_data` 必须读取 `~/benchclaw/realdata_cards/` 中对应 card，确认真实数据目录、登记表/清单、批次、授权/隐私、metadata 字段、标注缺口和可公开使用限制。

如果找不到对应 card，必须把该 source 标记为 `BLOCKED`、`NEEDS_CARD` 或 `NEEDS_USER_INPUT`，并在报告中列出缺失项。不得凭空猜测仿真器运行方式、数据集路径、字段 schema、真实数据目录或授权状态。

## Pipeline

### Phase 1: Data Capability Survey — 数据能力调研

调用：

```text
/1-benchmark-data-capability-survey "$STAGE1_DIR"
```

输入：

- `stage1/DATA_SOURCE_MAPPING.md`
- `stage1/CAPABILITY_SCOPE.md`
- `stage1/EVALSET_PROTOTYPE.md`
- `~/benchclaw/simulator_cards/`
- `~/benchclaw/dataset_cards/`
- `~/benchclaw/realdata_cards/`

执行内容：

- 读取 Stage 1 选定的数据源，并按 `simulator`、`existing_dataset`、`real_data` 分组。
- 为每个 source 定位并读取对应 card，记录 `card_path`、`card_status`、card 中可验证的运行/访问/schema/授权依据。
- 盘点每个 source 的可访问性、资产、字段、接口、GT/标注状态、授权状态和采集风险。
- 为每个 source 确认稳定 `source_name`，确保后续可作为目录名和 manifest 字段。
- 只做能力与资产调研，不运行采集脚本，不生成清洗方案，不筛选样本。

输出：

- `stage2/SOURCE_CAPABILITY_SURVEY.md`

该文件必须包含 `Source Inventory`、`Source Card Evidence`、`Simulator Sources`、`Existing Dataset Sources`、`Real Data Sources` 和 `Raw-Only Notes`。

Checkpoint：

- 若 `DATA_SOURCE_MAPPING.md` 缺失，停止并要求先完成 Stage 1 Phase 4。
- 若某个 source 不可访问，记录访问状态和原因，不得擅自删除该 source。

### Phase 2: Collection Guidance — 采集与接入指导

调用：

```text
/2-benchmark-collection-guidance "$STAGE2_CONTEXT"
```

输入：

- `stage1/CAPABILITY_SCOPE.md`
- `stage1/DATA_SOURCE_MAPPING.md`
- `stage1/BENCHMARK_DRAFT.md`
- `stage1/EVALSET_PROTOTYPE.md`
- `stage1/EXECUTION_PLAN.md`
- `stage2/SOURCE_CAPABILITY_SURVEY.md`
- `~/benchclaw/simulator_cards/`
- `~/benchclaw/dataset_cards/`
- `~/benchclaw/realdata_cards/`

执行内容：

- 从 Stage 1 产物中抽取 benchmark 能力维度、数据需求、评测题型、GT/答案需求和用户意图。
- 结合数据能力调研结果和对应 source card，逐个判断已有 benchmark 数据集、已有仿真器和已有真实数据源能支持哪些能力维度。
- 为每个 source 给出采集、接入或登记指导：采什么、采多少、如何编号、保留哪些 metadata、记录哪些风险。
- 对每个 source 明确 card-derived 采集依据，例如仿真器启动命令、数据集访问路径、真实数据登记表、字段 schema、授权限制和缺失项。
- 生成 `Capability-To-Source Routing`，将 Stage 1 的能力维度路由到具体 source，并标注 `source_role`。

输出：

- `stage2/COLLECTION_GUIDANCE_PLAN.md`

该文件必须包含：

- `Stage 1 Guidance Basis`
- `Source Card Basis`
- `Execution Mode`
- `Capability-To-Source Routing`
- `Per-Source Collection Guidance`
- `Existing Benchmark Dataset Guidance`
- `Simulator Guidance`
- `Real Data Guidance`
- `Coverage Gaps And Compensation`
- `Failure And Access Logging`

Checkpoint：

- 每个 raw sample 的后续采集都必须能追溯到 Stage 1 的能力维度。
- 如果能力维度没有可用 source，必须在 `Coverage Gaps And Compensation` 中显式列出。

### Phase 3: Template Refinement — 原始模板细化

调用：

```text
/3-benchmark-template-refinement "$STAGE2_CONTEXT"
```

输入：

- `stage2/COLLECTION_GUIDANCE_PLAN.md`
- `stage2/SOURCE_CAPABILITY_SURVEY.md`
- `stage1/EVALSET_PROTOTYPE.md`
- `~/benchclaw/simulator_cards/`
- `~/benchclaw/dataset_cards/`
- `~/benchclaw/realdata_cards/`

执行内容：

- 为每个 source 生成 raw record 模板，而不是清洗模板。
- 统一规定图像路径、JSON 路径、原始 source 信息、能力维度、GT/标注状态、metadata、问题标记和 provenance。
- 将 Phase 2 的 `source_role`、`stage1_requirement_ref` 和能力维度路由要求固化到模板字段。
- 将对应 card 的路径、card 中使用过的字段、运行/访问依据和缺失项固化到模板字段。

输出：

- `stage2/TEMPLATE_REFINEMENT_REPORT.md`
- `stage2/templates/{source_type}_{source_name}_RAW_TEMPLATE.yaml`

每个样本模板至少包含：

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
provenance: {}
metadata: {}
raw_payload_refs: []
```

Checkpoint：

- 模板只能定义原始数据记录字段，不得定义过滤阈值、质量通过阈值或删除策略。

### Phase 4: Collect Codegen — 采集、接入、登记代码生成

调用：

```text
/4-benchmark-collect-codegen "$STAGE2_CONTEXT"
```

输入：

- `stage2/COLLECTION_GUIDANCE_PLAN.md`
- `stage2/TEMPLATE_REFINEMENT_REPORT.md`
- `stage2/templates/*.yaml`
- `stage2/SOURCE_CAPABILITY_SURVEY.md`
- `stage1/DATA_SOURCE_MAPPING.md`
- `stage1/CAPABILITY_SCOPE.md`
- `stage1/BENCHMARK_DRAFT.md`
- `stage1/EVALSET_PROTOTYPE.md`
- `~/benchclaw/simulator_cards/`
- `~/benchclaw/dataset_cards/`
- `~/benchclaw/realdata_cards/`

执行内容：

- 根据 Phase 2 的逐源指导，为每个 source 生成自己的入口脚本、配置和 README，不得只生成一个泛化空壳。
- 对 `simulator` 生成实际采集控制代码：依据 simulator card 启动仿真器 runtime 或创建新的仿真 session，执行 health check、场景/地图/任务循环、传感器采集、GT 引用、异常记录、resume 状态。
- simulator 脚本必须显式禁止从其它文件夹、其它 workspace、旧 `collected_data/` 或缓存目录复制旧图片/旧 JSON；只有本次启动/本次 session 产生的样本可计入成功。
- 对 `existing_dataset` 生成读写和字段映射代码：依据 dataset card 读取原始数据集、映射 QA/caption/label/metadata、保存图片/JSON/manifest。
- 对 `real_data` 生成登记和读写代码：依据 realdata card 遍历真实图片或登记表、保存 metadata、授权/隐私状态、标注缺口和人工复核需求。
- 生成 `DATA_SCHEMA.md`，固定 Stage 2 raw data 的目录、字段和 manifest 契约。

输出：

```text
stage2/
  collect_scripts/simulator/{source_name}/collect.py
  collect_scripts/simulator/{source_name}/config.yaml
  collect_scripts/simulator/{source_name}/README.md
  ingest_scripts/existing_dataset/{source_name}/ingest.py
  ingest_scripts/existing_dataset/{source_name}/field_mapping.yaml
  ingest_scripts/existing_dataset/{source_name}/README.md
  register_scripts/real_data/{source_name}/register.py
  register_scripts/real_data/{source_name}/register_config.yaml
  register_scripts/real_data/{source_name}/README.md
  DATA_SCHEMA.md
```

Checkpoint：

- 每个启用 source 必须有脚本、配置和 README。
- 脚本必须写入 `capability_dimension`、`source_role`、`stage1_requirement_ref`、`source_card_path` 和 `source_card_fields_used`。
- simulator 脚本必须写入 `simulator_started_at`、`simulator_start_command`、`run_id/session_id`、`frame_id`、`current_run_only=true` 和旧数据排除记录。
- 脚本禁止清洗、过滤、删除或质量拒收样本。

### Phase 5: Batch Collect — 批量真实采集、接入与登记

调用：

```text
/5-benchmark-batch-collect "$STAGE2_CONTEXT"
```

输入：

- `stage2/COLLECTION_GUIDANCE_PLAN.md`
- `stage2/DATA_SCHEMA.md`
- `stage2/collect_scripts/`
- `stage2/ingest_scripts/`
- `stage2/register_scripts/`
- `stage1/DATA_SOURCE_MAPPING.md`
- `stage1/CAPABILITY_SCOPE.md`
- `stage1/BENCHMARK_DRAFT.md`
- `stage1/EVALSET_PROTOTYPE.md`
- `~/benchclaw/simulator_cards/`
- `~/benchclaw/dataset_cards/`
- `~/benchclaw/realdata_cards/`

执行内容：

- 对每个 source 执行 preflight check，检查脚本、配置、source card、输入路径、数据集根目录、真实数据目录或 simulator runtime。
- 校验脚本和配置使用的启动命令、数据根目录、字段 schema、登记表、授权/隐私要求是否来自对应 card 或显式用户 override。
- 真实运行 Phase 4 生成的脚本，将数据落到 `collected_data/`。
- 对 `simulator` 必须先执行 card 指定的启动命令或新建仿真 session，再执行 `collect.py`，保存本轮真实仿真器图片或可验证传感器输出、run/frame、scene/map/task、sensor config 和 GT 引用。
- 对 `simulator` 必须在执行前记录目标输出目录已有文件清单；本轮成功样本只能来自当前 `run_id/session_id`，旧文件不得计入 `Collected Samples`。
- 对 `existing_dataset` 执行 `ingest.py`，保存真实已有数据集图片或真实外部路径、原始样本 ID、字段映射和标注来源。
- 对 `real_data` 执行 `register.py`，保存真实图片或真实登记路径、采集批次、授权/隐私状态和标注缺口。
- 执行 anti-placeholder validation，禁止 placeholder、dummy、mock、fake、示例图、空 JSON 或模板 JSON 冒充真实数据。
- 校验 `images/`、`records/`、`manifest.jsonl` 一一对应。

输出：

```text
stage2/collected_data/{source_type}/{source_name}/images/{sample_id}.{ext}
stage2/collected_data/{source_type}/{source_name}/records/{sample_id}.json
stage2/collected_data/{source_type}/{source_name}/manifest.jsonl
stage2/logs/{source_or_service}.log
stage2/RAW_DATA_COLLECTION_REPORT.md
```

Checkpoint：

- 如果 source 可访问但脚本失败，必须标为 `FAIL` 或 `NEEDS_RETRY`，不得用占位数据替代。
- 如果仿真器 runtime 不可启动或不能创建新 session，必须标为 `NEEDS_RUNTIME` 或 `FAIL`，不能生成示例图片，不能复用旧数据。
- 如果发现 placeholder 或不可追溯样本，不得计入 `Collected Samples`。

### Phase 6: Unit Test — Stage 2 契约单元测试

调用：

```text
/6-benchmark-unit-test-stage2 "$STAGE2_DIR"
```

输入：

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

执行内容：

- 生成并执行 `stage2/unit_tests/test_stage2_contract.py`。
- 检查固定产物是否存在。
- 检查三类数据源是否按 `DATA_SOURCE_MAPPING.md` 被处理。
- 检查每个启用 source 是否记录并使用正确的 `source_card_path`，且脚本/配置/报告中的运行方式、访问路径和字段 schema 能追溯到对应 card。
- 对 simulator source，检查是否存在本轮仿真器启动或新 session 证据、当前 `run_id/session_id`、启动命令、退出码/健康检查、frame 证据和旧数据排除记录。
- 检查每个 `collected_data/{source_type}/{source_name}/` 下图片与 JSON 一一对应。
- 检查 JSON 必备字段、manifest 行、sample_id 编号、source_role 和能力维度追溯。
- 检查 Stage 2 是否违反 raw-only 契约，包括清洗、过滤、质量拒收或伪造数据。

输出：

- `stage2/unit_tests/test_stage2_contract.py`
- `stage2/unit_tests/results.json`
- `stage2/STAGE2_UNIT_TEST_REPORT.md`

Verdict 规则：

- `PASS`：固定产物、目录格式、一一对应、真实采集和 raw-only 契约全部通过。
- `NEEDS_REVIEW`：存在可解释缺口，但没有违反 raw-only 或反 placeholder 契约，用户可确认进入 Stage 3。
- `FAIL`：缺少关键产物、图片 JSON 不对应、manifest 无法追溯，或 Stage 2 出现清洗、过滤、质量拒收、占位数据冒充真实采集等行为。

### Final Summary

完成 Phase 6 后必须写入：

- `stage2/STAGE2_SUMMARY.md`

`STAGE2_SUMMARY.md` 必须包含：

```markdown
# Stage2 Summary

## Executive Summary

## Phase Results
### Phase 1: Data Capability Survey
### Phase 2: Collection Guidance
### Phase 3: Template Refinement
### Phase 4: Collect Codegen
### Phase 5: Batch Collect
### Phase 6: Unit Test

## Source Type Results
| Source Type | Source Name | Status | Raw Samples | Notes |
|-------------|-------------|--------|-------------|-------|

## Capability Coverage
| Capability Dimension | Source Type | Source Name | Raw Samples | Gap |
|----------------------|-------------|-------------|-------------|-----|

## Final Deliverables

## Raw-Only Statement
Stage 2 did not clean, filter, reject, deduplicate-delete, or confidence-screen accessible samples.

## Handoff To Stage 3
```

Stage 2 完成后必须停在这里，展示下一步选项：

1. Proceed to Stage 3
2. Rerun a Stage 2 phase
3. Review raw data, reports, scripts, or tests
4. Pause pipeline

不得自动调用 `/benchmark-stage3-data-clean`。即使 Gate 2 为 `PASS`，也只能说明“可以进入 Stage 3”，必须等待用户选择。

## Gate 2 — Raw Data Checkpoint

进入 Stage 3 前必须满足：

- `STAGE2_UNIT_TEST_REPORT.md` verdict 为 `PASS`，或为 `NEEDS_REVIEW` 且用户明确确认 waiver。
- `RAW_DATA_COLLECTION_REPORT.md` 存在，并能说明每个启用 source 的真实输入证据、采集命令、退出码和产物计数。
- 对 simulator source，`RAW_DATA_COLLECTION_REPORT.md` 必须说明仿真器启动命令、新 `run_id/session_id`、健康检查结果、采集时间窗口和旧数据排除结果。
- `collected_data/` 中每个 source 都满足图片、JSON、manifest 一一对应。
- 没有 placeholder、dummy、mock、fake 或空模板样本被计入成功样本。

若 verdict 为 `FAIL`，不得进入 Stage 3；必须根据报告回退到对应 phase 修复。

## 重新执行 Stage 2 的触发条件

| 问题 | 回退 phase |
|------|------------|
| 数据源能力盘点缺失或 source_name 不稳定 | Phase 1 |
| 能力维度到 source 的路由不清晰 | Phase 2 |
| raw record 字段不完整或与 Stage 1 追溯断裂 | Phase 3 |
| 逐源脚本缺失、脚本为空壳或配置不完整 | Phase 4 |
| 数据未真实采集、目录格式错误或出现占位数据 | Phase 5 |
| 单元测试发现契约不一致 | Phase 6 |

## Key Rules

- **Do not skip phases.** 6 个 phase 严格顺序执行。
- **Stage 1 drives Stage 2.** 能力维度、数据源映射、benchmark 草稿和评测原型必须指导 Stage 2 的采集范围。
- **Cards are authoritative.** 采集计划、模板、脚本和执行报告必须引用并使用对应 source card；card 缺失时必须阻塞或请求用户输入。
- **Cards are read-only.** `~/benchclaw/` 下的 card、模板、工具和配置只能读取，不得增删改；所有派生配置、日志、patch 和报告必须写入 active workspace。
- **Same skill set for three source types.** `simulator`、`existing_dataset`、`real_data` 不得拆成三套独立阶段。
- **Raw-only.** Stage 2 只采集、接入、登记，不清洗、不过滤、不质量拒收。
- **No placeholder.** 有真实数据时必须真实采集；没有 runtime 或输入时必须报告失败/待运行，不得伪造样本。
- **Simulator must run.** 启用的 simulator source 必须启动仿真器或创建新的仿真 session 实采；不能只连接旧产物、复制旧图片或复用其它目录数据。
- **No old data reuse.** 本轮 Stage 2 成功样本只能来自当前 workspace 当前 phase 的执行；其它 workspace、下载目录、缓存目录、历史 `collected_data/` 和旧 run 产物都不得计入成功样本。
- **One image, one JSON.** 每张图片必须有同编号 JSON，manifest 必须可同时定位唯一图片和唯一 JSON。
- **Trace to Stage 1.** 每个样本必须记录 `capability_dimension`、`source_role`、`stage1_requirement_ref`。
- **Record all failures.** 访问失败、运行失败、缺字段、标注缺口和 runtime 缺失必须写入报告和日志。
- **Stage boundary stop.** Stage 2 完成后必须停住，展示下一步选项，等待用户选择；不得自动进入 Stage 3。

## Fixed Artifact Format Contract

```text
stage2/
  SOURCE_CAPABILITY_SURVEY.md
  COLLECTION_GUIDANCE_PLAN.md
  TEMPLATE_REFINEMENT_REPORT.md
  templates/{source_type}_{source_name}_RAW_TEMPLATE.yaml
  DATA_SCHEMA.md
  collect_scripts/simulator/{source_name}/collect.py
  collect_scripts/simulator/{source_name}/config.yaml
  ingest_scripts/existing_dataset/{source_name}/ingest.py
  ingest_scripts/existing_dataset/{source_name}/field_mapping.yaml
  register_scripts/real_data/{source_name}/register.py
  register_scripts/real_data/{source_name}/register_config.yaml
  logs/{source_or_service}.log
  collected_data/{source_type}/{source_name}/images/{sample_id}.{ext}
  collected_data/{source_type}/{source_name}/records/{sample_id}.json
  collected_data/{source_type}/{source_name}/manifest.jsonl
  RAW_DATA_COLLECTION_REPORT.md
  unit_tests/test_stage2_contract.py
  unit_tests/results.json
  STAGE2_UNIT_TEST_REPORT.md
  STAGE2_SUMMARY.md
```

`sample_id` 必须使用 `{source_type}_{source_name}_{000001}` 形式递增。如果 `source_name` 含空格或特殊字符，必须先归一化为安全目录名，并在 JSON 中保留原始 source 名称。
