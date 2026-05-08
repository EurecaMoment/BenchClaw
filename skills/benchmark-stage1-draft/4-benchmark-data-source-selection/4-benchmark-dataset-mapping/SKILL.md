---
name: benchmark-dataset-mapping
description: "Atomic module: stage1 Phase 4 已有数据集能力匹配模块。只负责将能力维度与已有数据集进行匹配，输出维度-数据集映射表、未覆盖维度分析和可行性评估，不负责真实数据采集、仿真器选择或下游设计。Use when user says '匹配数据集'、'dataset mapping'、'已有数据集选取'."
argument-hint: [benchmark-context]
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

# Benchmark Dataset Mapping

Execute dataset-to-capability mapping for: **$ARGUMENTS**

This skill is an **atomic single-responsibility skill**.
It must only do the work scoped to this module.

## Purpose

- 本模块负责将 `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md` 中的每个能力维度与已有数据集进行匹配，确定哪些维度可直接复用既有数据。
- 本模块评估数据集的领域覆盖、模态覆盖、标注完备性、schema 稳定性与复用效率。
- 本模块位于 Stage 1 第四环节的数据集分支，直接产物是 `~/bench_workspace/workspace{i}/stage1/data_source_selection/DATASET_MAPPING.md`。
- 本模块不负责真实数据采集、仿真器选择、评测集设计或草稿生成。

## Inputs

- `$ARGUMENTS`：数据集映射的补充要求或用户偏好（如优先复用某类数据集）。
- 必需输入：`~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md`。
- 必需输入：数据集能力卡片目录 `~/benchclaw/dataset_cards`（每张卡片描述一个数据集的任务类型、模态、标注方式、schema 等）。
- 可选输入：已有数据集目录 `~/benchclaw/datasets`、workspace `~/bench_workspace/workspace{i}/stage1/datasets/` 中的离线数据集。
- **若 `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md` 缺失，应立即停止并报告缺失文件。**
- **若 `~/benchclaw/dataset_cards` 目录缺失或为空，应标注为"无数据集卡片可用"并要求后续不使用该模块。**

## Procedure

1. **读取能力维度**：读取 `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md`，提取所有能力维度及其操作性定义与任务类型示例。
2. **读取数据集卡片**：遍历 `~/benchclaw/dataset_cards` 中的所有数据集能力卡片，提取每个数据集支持的任务类型、模态、标注结构、schema 约束等。
3. **逐维度匹配**：将每个能力维度与数据集能力进行匹配，判定：
   - 哪些维度可被哪些数据集直接支持（full coverage）
   - 哪些维度需要多个数据集组合覆盖（partial coverage, combination needed）
   - 哪些维度当前无数据集可支持（none, need offline data or manual construction）
4. **推荐方案**：为每个维度推荐首选数据集及备选方案，附选择理由。
5. **扫描离线数据**：轻量扫描已有数据集目录，识别 workspace 或本地已有的离线数据对未覆盖维度的补充覆盖能力。
6. **可行性评估**：评估选定数据集组合的：
   - 接入复杂度
   - schema 稳定性
   - 领域与模态多样性
   - 复用吞吐量
7. **确定最终组合**：综合匹配结果与可行性评估，选定最终数据集组合并给出选择理由。
8. **校验**：确认所有能力维度在映射表中均有对应条目（即使是 "none"）。
9. **写入**：确保 `~/bench_workspace/workspace{i}/stage1/data_source_selection/` 存在，并写入 `~/bench_workspace/workspace{i}/stage1/data_source_selection/DATASET_MAPPING.md`。

## Expected Outputs

- `~/bench_workspace/workspace{i}/stage1/data_source_selection/DATASET_MAPPING.md`

输出文件结构：

```markdown
# Dataset Mapping

## Available Datasets
| Dataset | Supported Tasks | Modalities | Schema / Annotation | Key Characteristics |
|---------|-----------------|------------|----------------------|--------------------|
| ...     | ...             | ...        | ...                  | ...                |

## Dimension-Dataset Mapping
| Capability Dimension | Primary Dataset | Backup Dataset | Coverage | Notes |
|---------------------|-----------------|---------------|----------|-------|
| ...                 | ...             | ...           | full/partial/none | ... |

## Uncovered Dimensions
[无数据集可直接支持的维度，需要离线数据或人工构造]

## Offline Data Sources
[workspace 中已有的离线数据集及其对能力维度的补充覆盖情况]

## Feasibility Assessment
- Integration complexity: [评估]
- Schema stability: [评估]
- Domain diversity: [评估]
- Reuse throughput: [评估]

## Selected Dataset Set
[最终选定的数据集组合及选择理由]
```

## Completion Criteria

- [ ] `~/bench_workspace/workspace{i}/stage1/data_source_selection/DATASET_MAPPING.md` 已存在且非空。
- [ ] Dimension-Dataset Mapping 表覆盖了 `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md` 中的所有维度。
- [ ] 每个维度至少标注了 coverage 等级（full / partial / none）。
- [ ] Uncovered Dimensions 对 "none" 类维度提供了离线数据或人工构造的替代方案建议。
- [ ] Feasibility Assessment 包含四项评估维度的具体结论。
- [ ] Selected Dataset Set 给出了最终选择及理由。

## Rules

- 不生成 `~/bench_workspace/workspace{i}/stage1/DATA_SOURCE_MAPPING.md`、`~/bench_workspace/workspace{i}/stage1/EVALSET_PROTOTYPE.md`、`~/bench_workspace/workspace{i}/stage1/BENCHMARK_DRAFT.md` 或任何后续 phase 产物。
- 不擅自改写 `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md` 或任何上游产物。
- 不执行数据集下载或真实数据采集——那是 stage2 的职责。
- 不因数据集限制而删减能力维度——应标注 "none" 并建议替代方案，由上游 Phase 3 决定是否调整维度。
- 卡片信息与自身知识冲突时，以卡片信息为准。
- 出错时必须明确指出阻塞原因（如卡片目录缺失、某关键数据集信息不足）。
- 如果 Write 因文件过大失败，立即 fallback 到 Bash 分块写入，不要询问用户许可。

## Downstream Handoff

- `benchmark-data-source-selection` 读取 `~/bench_workspace/workspace{i}/stage1/data_source_selection/DATASET_MAPPING.md` 作为统一汇总输入。
- `benchmark-evalset-prototype-gen` 以 `~/bench_workspace/workspace{i}/stage1/DATA_SOURCE_MAPPING.md` 为最终依据；如需追溯数据集分支细节，可读取 `~/bench_workspace/workspace{i}/stage1/data_source_selection/DATASET_MAPPING.md`。
- `benchmark-draft-gen` 以 `~/bench_workspace/workspace{i}/stage1/DATA_SOURCE_MAPPING.md` 为最终依据；如需追溯 Selected Dataset Set，可读取 `~/bench_workspace/workspace{i}/stage1/data_source_selection/DATASET_MAPPING.md`。
- 本模块只写交接关系，不调度下游模块。
