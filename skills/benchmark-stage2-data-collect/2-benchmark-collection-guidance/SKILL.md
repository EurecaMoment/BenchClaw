---
name: benchmark-collection-guidance
description: "Stage 2 Phase 2：收集与接入指导方案。根据三类 source_type 为仿真器、已有数据集、真实数据分别制定采集、接入、登记和质检策略。Use when user says '制定采集方案', 'collection guidance', '规划数据接入'."
argument-hint: [stage2-context]
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

# 收集与接入指导方案（三类数据同一 Skill 并行）

面向：**$ARGUMENTS**

本 skill 只制定方案，不修模板、不生成代码、不实际采集或接入。

重要约束：本 skill 是三类数据源共同使用的唯一 Phase 2 skill。不得为仿真器、已有数据集、真实数据分别创建独立指导 skill；必须在同一个 `COLLECTION_GUIDANCE_PLAN.md` 中并行规划三类来源。

## 输入

必需：

- `~/bench_workspace/workspace{i}/stage1/DATA_SOURCE_MAPPING.md`
- `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md`
- `~/bench_workspace/workspace{i}/stage1/EVALSET_PROTOTYPE.md`
- `~/bench_workspace/workspace{i}/stage2/SOURCE_CAPABILITY_SURVEY.md`

可选：

- `~/bench_workspace/workspace{i}/stage1/BENCHMARK_DRAFT.md`
- `~/bench_workspace/workspace{i}/stage1/EXECUTION_PLAN.md`

## 三类数据处理方案

执行方式：从同一个 `DATA_SOURCE_MAPPING.md` 读取所有 source，按 `source_type` 分成三组并行制定方案，最后合并为一个统一计划。每个能力维度可以由单一来源覆盖，也可以由多类来源互补覆盖。

### 仿真器 `simulator`

制定主动采集方案：

- 采集哪些场景、每个场景多少帧、每帧哪些视角/模态
- 需要哪些 GT 通道，哪些 GT 是必需，哪些是可选
- 轨迹、视角、随机种子、场景多样性策略
- GT 对齐策略：frame_id、timestamp、多模态文件、annotation 必须一一对应
- 最小规模：`MIN_SCENES`、`MIN_FRAMES_PER_SCENE`
- 失败后的补采策略

### 已有数据集 `existing_dataset`

制定被动接入方案：

- 接入哪个 split/subset，是否抽样
- 图片、QA、caption、label、metadata 字段如何映射到 benchmark schema
- 原始 ID、split、annotation provenance 如何保留
- 缺失字段如何标记：`missing_or_derived`
- 是否需要去重、格式转换、路径重写、标注一致性检查
- 不执行仿真器脚本，不要求 scene/frame GT 对齐率

### 真实数据 `real_data`

制定资产登记与补标方案：

- 登记哪些图片或记录，如何生成 manifest
- 抽取哪些 metadata：文件名、时间、设备、EXIF、场景描述（若存在）
- 做哪些质量检查：损坏、重复、模糊、曝光、分辨率、隐私/许可风险
- 列出 annotation gap：哪些字段 `needs_annotation`，哪些 `not_observable`
- 需要人工复核的优先级和理由
- 不把估计值当作 GT

## 输出

- `~/bench_workspace/workspace{i}/stage2/COLLECTION_GUIDANCE_PLAN.md`

## 输出结构

```markdown
# Collection Guidance Plan

## Source Routing Summary
| Capability Dimension | Source Type | Source Name | Handling Mode | Priority |
|---------------------|-------------|-------------|---------------|----------|

## Simulator Collection Plan
| Simulator | Scenes | Frames/Scene | GT Channels | Trajectory/View Strategy | Alignment Check |
|-----------|--------|--------------|-------------|--------------------------|-----------------|

## Existing Dataset Ingestion Plan
| Dataset | Split/Subset | Modalities | Field Mapping | Annotation Status | Missing Fields |
|---------|--------------|------------|---------------|-------------------|----------------|

## Real Data Registration Plan
| Source | Asset Path | Metadata Fields | Quality Checks | Annotation Gaps | Review Priority |
|--------|------------|-----------------|----------------|-----------------|-----------------|

## Scale And Storage Estimate
| Source Type | Source | Unit | Expected Count | Estimated Storage | Assumption |
|-------------|--------|------|----------------|------------------|------------|

## Risk And Fallback
[环境、路径、许可、标注缺口、GT 缺失、质量风险]
```

## 完成标准

- 每个能力维度都能映射到至少一个数据来源或明确标注无法覆盖。
- 每个 source 都有 source_type 对应的处理方法。
- 仿真器使用采集规模和 GT 对齐策略。
- 已有数据集使用字段映射和标注一致性策略。
- 真实数据使用登记、质量检查和 annotation gap 策略。
- 三类来源必须出现在同一份 `COLLECTION_GUIDANCE_PLAN.md`，不得拆分成三份计划。

## 规则

- 不生成模板、脚本或真实数据。
- 不修改上游文件。
- 不用仿真器指标强行评估 existing_dataset / real_data。
