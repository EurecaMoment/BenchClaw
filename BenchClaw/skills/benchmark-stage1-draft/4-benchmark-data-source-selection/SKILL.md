---
name: benchmark-data-source-selection
description: "Atomic orchestrator: stage1 Phase 4 数据源选取总领模块。并行调度仿真器、已有数据集、真实采集数据三个子技能，汇总维度-数据源映射、未覆盖维度与可行性评估，不负责下游评测集设计、草稿生成或实际采集执行。Use when user says '数据源选取'、'data source selection'、'并行选源'."
argument-hint: [benchmark-context]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Skill
metadata:
  openclaw:
    emoji: ""
    requires:
      bins: [python3]
---

## `BENCHCLAW_ROOT` 只读约束

- **BENCHCLAW_READONLY = true**：`BENCHCLAW_ROOT/` 只能作为 BenchClaw 仓库内共享只读资源根，必须从当前 skill 所在的 BenchClaw 仓库位置解析，不能依赖固定 home 路径或机器绝对路径。
- `BENCHCLAW_ROOT` 必须解析为当前 skill 所在 BenchClaw 仓库的根目录；只允许读取该根目录下、且被当前 skill 明确允许的子目录。
- 严禁在 `BENCHCLAW_ROOT/` 下创建、编辑、覆盖、删除、移动、重命名、复制写入、初始化 git、提交、打 tag、写日志、写缓存或写临时文件。
- 所有派生产物、补丁、快照、报告、脚本、配置、日志和测试输出必须写入 active `WORKSPACE_ROOT`。
- 如必须修改 `BENCHCLAW_ROOT/` 中的资源，只能在 workspace 中生成 patch 或修改建议，等待用户在外部处理；当前 skill 不得直接应用。


## Workspace and File Access Boundary

This skill must operate only inside the current run workspace.

- Before reading or writing any run artifact, resolve and record the active `WORKSPACE_ROOT = ~/bench_workspace/workspace{i}` from the current task, parent stage, or pipeline state.
- Read and write only files under the active `WORKSPACE_ROOT` and the explicitly required global resource roots named by this skill, which must stay inside `BENCHCLAW_ROOT/`, such as `BENCHCLAW_ROOT/simulatorCards/`, `BENCHCLAW_ROOT/benchmarkDatasetCards/`, `BENCHCLAW_ROOT/realdata_cards/`, `BENCHCLAW_ROOT/templates/`, `BENCHCLAW_ROOT/model_api/`, `BENCHCLAW_ROOT/data-juicer_card/`, `BENCHCLAW_ROOT/annotation-tool/`, or `BENCHCLAW_ROOT/skills/` when the current skill explicitly requires them.
- Never read, list, grep, summarize, compare, copy, or infer from any other `~/bench_workspace/workspace{j}` where `j != i`, even if the current artifact is missing or another workspace appears newer or more complete.
- Never scan broad server directories such as `~`, `/`, `/home`, `/mnt`, `/data`, `/tmp`, `C:\Users`, `C:\`, or arbitrary project/download folders to discover context. Only inspect the exact current workspace paths and exact allowlisted resource roots needed for this skill.
- If an expected input is missing from the active workspace or an allowlisted resource root, stop and report the missing path. Do not search unrelated folders or borrow replacement artifacts from another workspace.
- Outputs must be written only to the active `WORKSPACE_ROOT` paths declared by this skill. Do not mirror or cache run artifacts into other workspaces or unrelated server folders.
- If the user explicitly provides an external path, use it only when it is directly relevant to this skill, record it as a user-provided exception, and do not expand access to sibling or parent directories.

This boundary overrides convenience behaviors such as auto-discovery, resume from latest workspace, reuse of previous artifacts, broad recursive grep/list, and fallback search.

# Benchmark Data Source Selection

Execute parallel data-source selection for: **$ARGUMENTS**

This skill is an **atomic orchestrator**.
It must only coordinate the three source-specific sub-skills and synthesize their results.

## Purpose

- 本模块负责将 `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md` 中的每个能力维度，分别与仿真器、已有数据集、真实采集数据进行匹配，确定各类数据源的覆盖边界。
- 本模块并行调度三个子技能：仿真器映射、数据集映射、真实数据映射。
- 本模块汇总三个子技能的结果，输出统一的数据源选择结果和最终推荐组合。
- 本模块位于 Stage 1 第四环节，直接产物是 `~/bench_workspace/workspace{i}/stage1/DATA_SOURCE_MAPPING.md`。
- 三个子技能的分支产物必须统一写入 `~/bench_workspace/workspace{i}/stage1/data_source_selection/`，不得直接散落在 `stage1/` 根目录。
- 本模块不负责评测集设计、草稿生成、数据安装/采集执行或 dry launch。

## Inputs

- `$ARGUMENTS`：数据源选取的补充要求或用户偏好（如优先复用已有数据集、优先真实数据等）。
- 必需输入：`~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md`。
- 必需输入：仿真器能力卡片目录 `BENCHCLAW_ROOT/simulatorCards/`、数据集能力卡片目录 `BENCHCLAW_ROOT/benchmarkDatasetCards/`、真实数据能力卡片目录 `BENCHCLAW_ROOT/realdata_cards/`。
- 可选输入：仿真器本体环境 `BENCHCLAW_ROOT/simulators/`、已有数据集目录 `BENCHCLAW_ROOT/datasets/`、真实采集数据目录 `BENCHCLAW_ROOT/realdatas/`。
- **若 `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md` 缺失，应立即停止并报告缺失文件。**
- **若任一卡片目录缺失或为空，应在对应来源章节标注“无可用卡片”，并基于自身知识提供候选来源建议，同时在输出中明确标注信息来源。**

## Procedure

1. **读取能力维度**：读取 `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md`，提取所有能力维度及其操作性定义与任务类型示例。
2. **并行调度子技能**：并行调用三个子技能，分别生成仿真器、已有数据集、真实采集数据的源内映射结果；三个分支产物必须写入 `~/bench_workspace/workspace{i}/stage1/data_source_selection/`。
3. **汇总各来源结果**：读取 `~/bench_workspace/workspace{i}/stage1/data_source_selection/SIMULATOR_MAPPING.md`、`~/bench_workspace/workspace{i}/stage1/data_source_selection/DATASET_MAPPING.md`、`~/bench_workspace/workspace{i}/stage1/data_source_selection/REALDATA_MAPPING.md`，整理每个能力维度的 full / partial / none 覆盖情况。
4. **跨源整合推荐**：为每个维度推荐首选数据源与备选数据源，明确单源覆盖还是跨源组合覆盖。
5. **识别未覆盖维度**：将完全无法由三类来源覆盖的维度标为 none，并给出离线数据或人工构造建议。
6. **可行性评估**：综合评估最终数据源组合的安装/接入复杂度、稳定性、场景或域多样性、数据获取或复用吞吐量。
7. **确定最终组合**：给出最终推荐的数据源组合，并说明为何采用该组合而不是单一来源。
8. **校验**：确认所有能力维度在映射表中均有对应条目（即使是 "none"）。
9. **写入**：写入 `~/bench_workspace/workspace{i}/stage1/DATA_SOURCE_MAPPING.md`。

## Expected Outputs

- `~/bench_workspace/workspace{i}/stage1/DATA_SOURCE_MAPPING.md`
- 子技能分支产物目录：`~/bench_workspace/workspace{i}/stage1/data_source_selection/`
  - `SIMULATOR_MAPPING.md`
  - `DATASET_MAPPING.md`
  - `REALDATA_MAPPING.md`

输出文件结构：

```markdown
# Data Source Mapping

## Available Sources
### Simulators
| Simulator | Supported Scenes | Perception Modalities | Action Space | Key Capabilities |
|-----------|-----------------|----------------------|--------------|-----------------|
| ...       | ...             | ...                  | ...          | ...             |

### Existing Datasets
| Dataset | Supported Tasks | Modalities | Schema / Annotation | Key Characteristics |
|---------|-----------------|------------|----------------------|--------------------|
| ...     | ...             | ...        | ...                  | ...                |

### Real-Data Sources
| Source | Collection Scenarios | Modalities | Constraints | Key Characteristics |
|--------|----------------------|------------|-------------|---------------------|
| ...    | ...                  | ...        | ...         | ...                 |

## Dimension-Source Mapping
| Capability Dimension | Primary Source Type | Primary Source | Backup Source | Coverage | Notes |
|---------------------|---------------------|---------------|---------------|----------|-------|
| ...                 | ...                 | ...           | ...           | full/partial/none | ... |

## Uncovered Dimensions
[三类数据源都无法充分覆盖的维度，需要离线数据或人工构造]

## Offline / Existing Data Sources
[workspace 中已有的数据集与真实数据资产及其对能力维度的补充覆盖情况]

## Feasibility Assessment
- Simulator suitability: [评估]
- Existing dataset reuse: [评估]
- Real-data collection: [评估]
- Overall data-source mix: [评估]

## Selected Data Source Set
[最终选定的数据源组合及选择理由]
```

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

## Completion Criteria

- [ ] `~/bench_workspace/workspace{i}/stage1/DATA_SOURCE_MAPPING.md` 已存在且非空。
- [ ] 三个子技能分支产物均位于 `~/bench_workspace/workspace{i}/stage1/data_source_selection/`，不得直接写在 `stage1/` 根目录。
- [ ] Dimension-Source Mapping 表覆盖了 `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md` 中的所有维度。
- [ ] 每个维度至少标注了 coverage 等级（full / partial / none）。
- [ ] Uncovered Dimensions 对 "none" 类维度提供了离线数据或人工构造的替代方案建议。
- [ ] Feasibility Assessment 包含四项评估维度的具体结论。
- [ ] Selected Data Source Set 给出了最终选择及理由。

## Rules

- 不生成 `~/bench_workspace/workspace{i}/stage1/EVALSET_PROTOTYPE.md`、`~/bench_workspace/workspace{i}/stage1/BENCHMARK_DRAFT.md` 或任何后续 phase 产物。
- 不把 `SIMULATOR_MAPPING.md`、`DATASET_MAPPING.md`、`REALDATA_MAPPING.md` 直接写入 `~/bench_workspace/workspace{i}/stage1/`；它们只能写入 `~/bench_workspace/workspace{i}/stage1/data_source_selection/`。
- 不擅自改写 `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md` 或任何上游产物。
- 不执行仿真器安装、数据集下载或真实数据采集——那是 stage2 的职责。
- 不因单一来源限制而删减能力维度——应标注 "none" 并建议替代方案，由上游 Phase 3 决定是否调整维度。
- 卡片信息与自身知识冲突时，以卡片信息为准。
- 出错时必须明确指出阻塞原因（如卡片目录缺失、某关键来源信息不足）。
- 如果 Write 因文件过大失败，立即 fallback 到 Bash 分块写入，不要询问用户许可。

## Downstream Handoff

- `benchmark-evalset-prototype-gen` 读取 `~/bench_workspace/workspace{i}/stage1/DATA_SOURCE_MAPPING.md` 确定每个任务原型使用的数据源。
- `benchmark-draft-gen` 读取 `~/bench_workspace/workspace{i}/stage1/DATA_SOURCE_MAPPING.md` 中的 Selected Data Source Set 写入草稿的数据构造方案。
- `benchmark-execution-plan-gen` 读取 `~/bench_workspace/workspace{i}/stage1/DATA_SOURCE_MAPPING.md` 的 Feasibility Assessment 评估 stage2 的数据生成与接入风险。
- 本模块只写交接关系，不调度下游模块。
