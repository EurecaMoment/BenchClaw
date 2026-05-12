---
name: benchmark-simulator-mapping
description: "Atomic module: stage1 Phase 4 仿真器能力匹配模块。只负责将能力维度与可用仿真器进行匹配，输出维度-仿真器映射表、未覆盖维度分析和可行性评估，不负责评测集设计、草稿生成或仿真器 dry launch。Use when user says '匹配仿真器'、'simulator mapping'、'仿真器选择'。"
argument-hint: [benchmark-context]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob
metadata:
  openclaw:
    emoji: ""
    requires:
      bins: [python3]
---

## `~/benchclaw` 只读约束

- **BENCHCLAW_READONLY = true**：`~/benchclaw/` 只能作为共享只读资源根。
- 严禁在 `~/benchclaw/` 下创建、编辑、覆盖、删除、移动、重命名、复制写入、初始化 git、提交、打 tag、写日志、写缓存或写临时文件。
- 所有派生产物、补丁、快照、报告、脚本、配置、日志和测试输出必须写入 active `WORKSPACE_ROOT`。
- 如必须修改 `~/benchclaw/` 中的资源，只能在 workspace 中生成 patch 或修改建议，等待用户在外部处理；当前 skill 不得直接应用。


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

# Benchmark Simulator Mapping

Execute simulator-to-capability mapping for: **$ARGUMENTS**

This skill is an **atomic single-responsibility skill**.
It must **only** do the work scoped to this module.

---

## Purpose

- 本模块负责将 `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md` 中的每个能力维度与可用仿真器进行匹配，确定数据生成方案的技术可行性。
- 本模块评估仿真器组合的安装难度、API 稳定性、场景多样性与数据生成效率。
- 本模块位于 Stage 1 第四环节，直接产物是 `~/bench_workspace/workspace{i}/stage1/data_source_selection/SIMULATOR_MAPPING.md`。
- 本模块不负责评测集设计、草稿生成、仿真器实际安装或 dry launch。

---

## Inputs

- `$ARGUMENTS`：仿真器映射的补充要求或用户偏好（如优先使用某仿真器）。
- 必需输入：`~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md`。
- 必需输入：仿真器能力卡片目录 `~/benchclaw/simulator_cards`（每张卡片描述一个仿真器的场景类型、感知模态、动作空间、物理交互能力等）。
- 可选输入：仿真器本体环境 `~/benchclaw/simulators`、workspace `~/bench_workspace/workspace{i}/stage1/datasets/` 中的离线数据集。
- **若 `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md` 缺失，应立即停止并报告缺失文件。**
- **若 `~/benchclaw/simulator_cards` 目录缺失或为空，应标注为"无仿真器卡片可用"并要求后续不使用该模块。**

---

## Procedure

1. **读取能力维度**：读取 `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md`，提取所有能力维度及其操作性定义与任务类型示例。
2. **读取仿真器卡片**：遍历 `~/benchclaw/simulator_cards` 中的所有仿真器能力卡片，提取每个仿真器支持的场景类型、感知模态、动作空间、物理交互能力等。
3. **逐维度匹配**：将每个能力维度与仿真器能力进行匹配，判定：
   - 哪些维度可被哪些仿真器直接支持（full coverage）
   - 哪些维度需要多个仿真器组合覆盖（partial coverage, combination needed）
   - 哪些维度当前无仿真器可支持（none, need offline data or manual construction）
4. **推荐方案**：为每个维度推荐首选仿真器及备选方案，附选择理由。
5. **扫描离线数据**：轻量扫描 workspace `~/bench_workspace/workspace{i}/stage1/datasets/` 目录，识别已有离线数据集对未覆盖维度的补充覆盖能力。
6. **可行性评估**：评估选定仿真器组合的：
   - 安装复杂度
   - API 稳定性
   - 场景多样性
   - 数据生成吞吐量
7. **确定最终组合**：综合匹配结果与可行性评估，选定最终仿真器组合并给出选择理由。
8. **校验**：确认所有能力维度在映射表中均有对应条目（即使是 "none"）。
9. **写入**：确保 `~/bench_workspace/workspace{i}/stage1/data_source_selection/` 存在，并写入 `~/bench_workspace/workspace{i}/stage1/data_source_selection/SIMULATOR_MAPPING.md`。

---

## Expected Outputs

- `~/bench_workspace/workspace{i}/stage1/data_source_selection/SIMULATOR_MAPPING.md`

输出文件结构：

```markdown
# Simulator Mapping

## Available Simulators
| Simulator | Supported Scenes | Perception Modalities | Action Space | Key Capabilities |
|-----------|-----------------|----------------------|--------------|-----------------|
| ...       | ...             | ...                  | ...          | ...             |

## Dimension-Simulator Mapping
| Capability Dimension | Primary Simulator | Backup Simulator | Coverage | Notes |
|---------------------|-------------------|------------------|----------|-------|
| ...                 | ...               | ...              | full/partial/none | ... |

## Uncovered Dimensions
[无仿真器可支持的维度，需要离线数据或人工构造]

## Offline Data Sources
[workspace 中已有的离线数据集及其对能力维度的补充覆盖情况]

## Feasibility Assessment
- Installation complexity: [评估]
- API stability: [评估]
- Scene diversity: [评估]
- Data generation throughput: [评估]

## Selected Simulator Set
[最终选定的仿真器组合及选择理由]
```

---

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

- [ ] `~/bench_workspace/workspace{i}/stage1/data_source_selection/SIMULATOR_MAPPING.md` 已存在且非空。
- [ ] Dimension-Simulator Mapping 表覆盖了 `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md` 中的所有维度。
- [ ] 每个维度至少标注了 coverage 等级（full / partial / none）。
- [ ] Uncovered Dimensions 对 "none" 类维度提供了离线数据或人工构造的替代方案建议。
- [ ] Feasibility Assessment 包含四项评估维度的具体结论。
- [ ] Selected Simulator Set 给出了最终选择及理由。

---

## Rules

- 不生成 `~/bench_workspace/workspace{i}/stage1/EVALSET_PROTOTYPE.md`、`~/bench_workspace/workspace{i}/stage1/BENCHMARK_DRAFT.md` 或任何后续 phase 产物。
- 不擅自改写 `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md` 或任何上游产物。
- 不执行仿真器安装或 dry launch——那是 stage2 的职责。
- 不因仿真器限制而擅自删减能力维度——应标注 "none" 并建议替代方案，由上游 Phase 3 决定是否调整维度。
- 仿真器卡片信息与自身知识冲突时，以卡片信息为准。
- 出错时必须明确指出阻塞原因（如仿真器卡片目录缺失、某关键仿真器信息不足）。
- 如果 Write 因文件过大失败，立即 fallback 到 Bash 分块写入，不要询问用户许可。

---

## Downstream Handoff

- `benchmark-data-source-selection` 读取 `~/bench_workspace/workspace{i}/stage1/data_source_selection/SIMULATOR_MAPPING.md` 作为统一汇总输入。
- `benchmark-evalset-prototype-gen`、`benchmark-draft-gen` 和 `benchmark-execution-plan-gen` 读取 `~/bench_workspace/workspace{i}/stage1/DATA_SOURCE_MAPPING.md` 作为最终下游依据。
- 本模块只写交接关系，不调度下游模块。