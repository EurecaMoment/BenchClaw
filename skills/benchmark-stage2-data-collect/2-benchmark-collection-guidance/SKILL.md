---
name: benchmark-collection-guidance
description: "Stage 2 Phase 2：采集与接入指导。基于 Stage 1 的能力维度、数据源映射、benchmark 草稿和评测原型，逐个指导已有 benchmark 数据集、已有仿真器和已有真实数据如何采集、接入、登记，并对应到 Stage 1 生成的能力维度上；只规划原始保存和问题记录，不规划清洗或过滤。"
argument-hint: [stage2-context]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, WebSearch, WebFetch
---

## `~/benchclaw` 只读约束

- **BENCHCLAW_READONLY = true**：`~/benchclaw/` 只能作为共享只读资源根。
- 严禁在 `~/benchclaw/` 下创建、编辑、覆盖、删除、移动、重命名、复制写入、初始化 git、提交、打 tag、写日志、写缓存或写临时文件。
- 所有派生产物、补丁、快照、报告、脚本、配置、日志和测试输出必须写入 active `WORKSPACE_ROOT`。
- 如必须修改 `~/benchclaw/` 中的资源，只能在 workspace 中生成 patch 或修改建议，等待用户在外部处理；当前 skill 不得直接应用。

# 采集与接入指导方案

面向：*$ARGUMENTS*

本 phase 输出 `stage2/COLLECTION_GUIDANCE_PLAN.md`，用于指导后续代码生成和批量执行。它不是泛泛列采集任务，而是必须在 Stage 1 产物约束下，为每一个已有 benchmark 数据集、已有仿真器、已有真实数据源生成可执行的采集/接入/登记指导，并明确对应到 Stage 1 的 benchmark 能力维度。

## 输入

必须读取：

- `stage1/CAPABILITY_SCOPE.md`：能力维度、子能力、边界和排除项。
- `stage1/DATA_SOURCE_MAPPING.md`：Stage 1 选定的数据源、source_type、source_name、能力维度对应关系。
- `stage1/BENCHMARK_DRAFT.md`：benchmark 任务定义、评测目标、用户意图和约束。
- `stage1/EVALSET_PROTOTYPE.md`：题型、样例、输入输出形态和初始 GT 需求。
- `stage1/EXECUTION_PLAN.md`：阶段目标、优先级、资源和风险。
- `stage2/SOURCE_CAPABILITY_SURVEY.md`：每个 source 的实际可访问资产、字段、接口、GT/标注状态和采集风险。
- `~/benchclaw/simulator_cards/`：仿真器启动、运行、场景、传感器、GT 和采集接口说明。
- `~/benchclaw/dataset_cards/`：已有数据集访问路径、schema、字段、split、授权和原始 ID 说明。
- `~/benchclaw/realdata_cards/`：真实数据图片目录、登记表、批次、授权/隐私、metadata 和标注缺口说明。

如果上述任一关键文件缺失，必须停止并报告缺失路径，不得凭空生成采集指导。

对每个 `DATA_SOURCE_MAPPING.md` 中启用的 source，必须读取或复核 `SOURCE_CAPABILITY_SURVEY.md` 中记录的 `card_path`。如果缺少 card，采集指导只能输出 `NEEDS_CARD` / `NEEDS_USER_INPUT`，不得猜测采集命令、数据路径或字段 schema。

`~/benchclaw/` 下所有资源只能只读。不得为了完善采集指导而修改 card、补写字段、移动文件、创建新 card 或向 `~/benchclaw/` 写入缓存、草稿、报告、配置或日志；所有派生产物必须写入 `WORKSPACE_ROOT/stage2/`。

## 指导目标

本 phase 必须完成四件事：

1. 从 Stage 1 产物中抽取 benchmark 能力维度、数据需求、评测题型、GT/答案需求和用户意图。
2. 结合 `SOURCE_CAPABILITY_SURVEY.md` 和对应 source card，逐个检查每个已有 benchmark 数据集、已有仿真器和已有真实数据源能支持哪些能力维度。
3. 为每个 source 给出采集、接入或登记指导，包括采什么、采多少、保留哪些 metadata、如何编号、如何记录风险。
4. 输出能力维度到数据源的对应关系，确保后续 Stage 2 批量采集的每个 raw sample 都能追溯到 Stage 1 的能力维度。

## 原始保存原则

- 可访问样本必须保存到 `collected_data/`。
- `~/benchclaw/` 只能作为只读依据，不能作为任何输出目录或中间目录。
- 问题样本不在 Stage 2 删除，只记录问题标记。
- 计划中不得包含清洗框架、清洗、过滤、去重删除、质量门槛或拒收规则。
- 对不可访问 source unit，只记录 `access_error` 和跳过原因。
- 数据是否足够干净、是否可进入 Stage 4、是否需要拒收，由 Stage 3 判断。

## 逐源指导规则

### 已有 benchmark 数据集：`existing_dataset`

对 `DATA_SOURCE_MAPPING.md` 中每个 `source_type=existing_dataset` 的 source，必须输出：

- 它覆盖的 Stage 1 能力维度和子能力。
- 它与 `BENCHMARK_DRAFT.md` 中任务目标的关系。
- 它能提供的图片、QA、caption、label、metadata、原始样本 ID 和标注来源。
- 需要接入的字段映射、缺失字段、授权状态、原始路径和样本规模；这些必须来自 dataset card 或显式用户补充。
- dataset card 中的数据根目录、下载/访问方式、split、字段 schema、license 和原始 ID 必须作为后续 `field_mapping.yaml` 的依据。
- 每条样本如何写入 `images/{sample_id}.{ext}`、`records/{sample_id}.json` 和 `manifest.jsonl`。
- 不能覆盖的能力维度和需要后续仿真器/真实数据补充的部分。

### 已有仿真器：`simulator`

对 `DATA_SOURCE_MAPPING.md` 中每个 `source_type=simulator` 的 source，必须输出：

- 它覆盖的 Stage 1 能力维度、环境变量、场景/地图/任务配置。
- 它应采集的场景、视角、帧、传感器、模态和原始 GT 引用。
- 它如何服务于 `EVALSET_PROTOTYPE.md` 中的题型或 GT 生成需求。
- simulator card 中的启动命令、SDK/API、依赖、endpoint、可用 scene/map/task、传感器、GT 输出和运行限制。
- 必须要求 Phase 5 启动仿真器或创建新的仿真 `run_id/session_id` 后再采集；不能把旧图片、旧 JSON、缓存文件或其它目录旧产物作为 simulator 采集结果。
- 需要记录的 seed、配置、版本、运行命令、frame、scene、town、run、传感器参数。
- 需要记录的 runtime 启动证据，包括 `startup_command`、`simulator_started_at`、process/session、health check 和当前 `run_id/session_id`。
- 异常帧、GT 对齐问题或采集失败如何记录到 `raw_observation_flags`，而不是删除样本。

### 已有真实数据：`real_data`

对 `DATA_SOURCE_MAPPING.md` 中每个 `source_type=real_data` 的 source，必须输出：

- 它覆盖或补充的 Stage 1 能力维度。
- 它相对 benchmark 草稿的价值，例如真实分布、真实噪声、长尾场景、现实约束。
- 需要登记的图片、来源、采集批次、授权/隐私状态、设备、时间、地点或可公开 metadata。
- realdata card 中的图片根目录、登记表/清单、批次字段、授权/隐私状态和 metadata 字段必须作为后续 `register_config.yaml` 的依据。
- 标注缺口、人工复核需求和不可观测 GT 如何记录。
- 哪些能力维度只能作为真实数据补充证据，不能直接当作完整 GT。

## 能力维度路由要求

`COLLECTION_GUIDANCE_PLAN.md` 必须有一张总表，把 Stage 1 的每个能力维度路由到可用 source：

```markdown
## Capability-To-Source Routing
| Capability Dimension | Sub Capability | Benchmark Need | Source Type | Source Name | Source Role | Expected Raw Evidence | GT / Annotation Need | Gap |
|----------------------|----------------|----------------|-------------|-------------|-------------|-----------------------|----------------------|-----|
```

`Source Role` 必须使用以下之一：

- `primary`：该 source 是此能力维度的主要数据来源。
- `supplemental`：该 source 补充真实分布、长尾或覆盖缺口。
- `gt_provider`：该 source 主要提供 GT 或可复现答案生成条件。
- `negative_or_control`：该 source 用于对照、捷径检查或负例。
- `needs_stage3_annotation`：该 source 可采集原始数据，但需要 Stage 3 标注或置信度提升。

## 输出格式

`COLLECTION_GUIDANCE_PLAN.md` 必须包含：

```markdown
# Collection Guidance Plan

## Stage 1 Guidance Basis
| Stage 1 Artifact | Extracted Requirement | Impact On Collection |
|------------------|----------------------|----------------------|

## Source Card Basis
| Source Type | Source Name | Card Path | Card-Derived Runtime / Access | Card-Derived Fields | Missing Card Items |
|-------------|-------------|-----------|-------------------------------|---------------------|--------------------|

## Execution Mode
- Parallel groups: simulator, existing_dataset, real_data
- Raw-only guarantee: no cleaning framework, no cleaning, no filtering, no quality rejection

## Capability-To-Source Routing
| Capability Dimension | Sub Capability | Benchmark Need | Source Type | Source Name | Source Role | Expected Raw Evidence | GT / Annotation Need | Gap |
|----------------------|----------------|----------------|-------------|-------------|-------------|-----------------------|----------------------|-----|

## Per-Source Collection Guidance
| Source Type | Source Name | Card Path | Related Capability Dimension | Stage1 Evidence | Collection / Ingest / Register Action | Expected Raw Samples | Required Metadata | Raw Flags To Record |
|-------------|-------------|-----------|------------------------------|-----------------|---------------------------------------|----------------------|-------------------|---------------------|

## Existing Benchmark Dataset Guidance
| Source Name | Dataset Slice | Related Capability Dimension | Field Mapping Need | Image Handling | Record Handling | Missing Fields / Gaps |
|-------------|---------------|------------------------------|--------------------|----------------|-----------------|-----------------------|

## Simulator Guidance
| Source Name | Scenario / Map / Task | Related Capability Dimension | Startup Command / Session Requirement | Command Inputs | Output Modalities | GT References | Old Data Reuse Ban | Raw Flags To Record |
|-------------|-----------------------|------------------------------|---------------------------------------|----------------|-------------------|---------------|--------------------|---------------------|

## Real Data Guidance
| Source Name | Batch / Source Unit | Related Capability Dimension | Registration Inputs | Metadata Need | Annotation Gap Handling | Raw Flags To Record |
|-------------|---------------------|------------------------------|---------------------|---------------|-------------------------|---------------------|

## Coverage Gaps And Compensation
| Capability Dimension | Gap | Preferred Compensation Source | Stage2 Action | Stage3 Dependency |
|----------------------|-----|-------------------------------|---------------|-------------------|

## Failure And Access Logging
| Failure Type | Required Field | Report Location |
|--------------|----------------|-----------------|
```

## 传递给后续 phase 的要求

后续脚本必须依据 `Capability-To-Source Routing`、`Per-Source Collection Guidance` 和 `Source Card Basis` 生成采集、接入和登记代码。所有脚本必须输出 `images/`、`records/`、`manifest.jsonl`，并保证每张图片对应一个 JSON 记录。

`source_name` 必须延续本计划中的命名。`records/{sample_id}.json` 和 `manifest.jsonl` 中必须写入 `capability_dimension`、`source_type`、`source_name`、`source_role`、`stage1_requirement_ref`、`source_card_path`、`source_card_fields_used` 和 `raw_observation_flags`，保证每个 raw sample 都能追溯回 Stage 1 的能力维度、source card 与 benchmark 设计意图。
