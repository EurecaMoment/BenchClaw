---
name: benchmark-execution-plan-gen
description: "Atomic module: stage1 Phase 7 执行计划生成模块。只负责基于 benchmark 草稿为 stage2-stage5 生成具体的执行计划，包含任务分解、产出物、验收标准和风险评估，不负责执行任何 stage2-stage5 的实际工作。Use when user says '生成执行计划'、'generate execution plan'、'规划后续阶段'。"
argument-hint: [benchmark-context]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob
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

# Benchmark Execution Plan Generation

Execute downstream execution plan generation for: **$ARGUMENTS**

This skill is an **atomic single-responsibility skill**.
It must **only** do the work scoped to this module.

---

## Purpose

- 本模块负责基于 benchmark 草稿，为 stage2-stage5 的每个阶段生成具体的、可操作的执行计划。
- 本模块确保执行计划与 `BENCHMARK_DRAFT.md` 中的对应章节一一对应。
- 本模块位于 Stage 1 第七环节（最后一个环节），直接产物是 `EXECUTION_PLAN.md`。
- 本模块不负责执行任何 stage2-stage5 的实际工作，不调度下游 stage。

---

## Inputs

- `$ARGUMENTS`：执行计划的补充要求或用户偏好（如时间约束、资源限制）。
- 必需输入：`~/bench_workspace/workspace{i}/stage1/BENCHMARK_DRAFT.md`。
- 可选输入（用于更精确的计划生成）：
  - `~/bench_workspace/workspace{i}/stage1/IDEA_TARGET.md`
  - `~/bench_workspace/workspace{i}/stage1/LITERATURE_REVIEW.md`
  - `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md`
  - `~/bench_workspace/workspace{i}/stage1/DATA_SOURCE_MAPPING.md`
  - `~/bench_workspace/workspace{i}/stage1/EVALSET_PROTOTYPE.md`
- **若 `~/bench_workspace/workspace{i}/stage1/BENCHMARK_DRAFT.md` 缺失，应立即停止并报告缺失文件。**

---

## Procedure

1. **读取 benchmark 草稿**：读取 `~/bench_workspace/workspace{i}/stage1/BENCHMARK_DRAFT.md`，重点提取：
  - 需要继续完善的内容列表
  - 数据构造方案（仿真器、已有数据集、真实数据的组合方案）
   - 评测集设计（任务原型数量、指标体系复杂度）
   - 已知局限与风险
2. **读取补充上游产出**（若可用）：
  - `DATA_SOURCE_MAPPING.md` 的 Feasibility Assessment → 评估数据获取、接入与生成风险
  - `DATA_SOURCE_MAPPING.md` 的 Selected Data Source Set → 提取各数据源的采集对象与计划规模依据
  - `EVALSET_PROTOTYPE.md` 的任务原型数量 → 评估 Stage 4 工作量
  - `LITERATURE_REVIEW.md` 的 Duplication Risks → 识别需要差异化验证的环节
3. **为每个 stage 生成执行计划**，包含：
   - **阶段目标**：与 `BENCHMARK_DRAFT.md` 的对应章节对齐
   - **输入依赖**：需要哪些前序产出
   - **具体任务分解**：可执行的任务清单，其中 Stage 2 必须按数据源逐一写明计划采集数量与单位
   - **预期产出物**：文件列表与格式要求
   - **验收标准**：可检验的完成条件
   - **风险点与应对方案**：识别阻塞风险并给出应对策略
4. **建立跨阶段依赖关系**：绘制 stage2-stage5 之间的依赖关系，标注关键路径。
5. **预估时间线**：基于任务复杂度与风险评估，给出各阶段的时间预估。
6. **校验对齐**：确认执行计划中的每个阶段目标都可追溯到 `~/bench_workspace/workspace{i}/stage1/BENCHMARK_DRAFT.md` 中的对应章节。
7. **写入**：写入 `~/bench_workspace/workspace{i}/stage1/EXECUTION_PLAN.md`。

---

## Expected Outputs

- `~/bench_workspace/workspace{i}/stage1/EXECUTION_PLAN.md`

输出文件结构：

```markdown
# Execution Plan

## Stage 2: Multi-Source Data Collection
- **Objective**: [与 BENCHMARK_DRAFT.md 对齐的阶段目标]
- **Input dependencies**: [前序产出列表]
- **Per-source collection quotas**:
  | Source Type | Source Name | Planned Collection Amount | Unit | Linked Dimensions / Tasks |
  |-------------|-------------|---------------------------|------|---------------------------|
  | ...         | ...         | ...                       | ...  | ...                       |
- **Tasks**:
  1. [具体任务]
  2. [具体任务]
- **Expected outputs**: [产出物列表]
- **Acceptance criteria**: [验收标准]
- **Risks**: [风险点与应对]

## Stage 3: Data-Juicer Data Cleaning
- **Objective**: ...
- **Input dependencies**: ...
- **Tasks**: ...
- **Expected outputs**: ...
- **Acceptance criteria**: ...
- **Risks**: ...

## Stage 4: Eval-Set Build and Metric Establishment
- **Objective**: ...
- **Input dependencies**: ...
- **Tasks**: ...
- **Expected outputs**: ...
- **Acceptance criteria**: ...
- **Risks**: ...

## Stage 5: Evaluation Run
- **Objective**: ...
- **Input dependencies**: ...
- **Tasks**: ...
- **Expected outputs**: ...
- **Acceptance criteria**: ...
- **Risks**: ...

## Cross-Stage Dependencies
[跨阶段依赖关系图]

## Timeline Estimate
[各阶段预估时间]
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

- [ ] `~/bench_workspace/workspace{i}/stage1/EXECUTION_PLAN.md` 已存在且非空。
- [ ] 覆盖 stage2-stage5 全部四个阶段，每个阶段包含完整的六项内容（Objective、Input dependencies、Tasks、Expected outputs、Acceptance criteria、Risks）。
- [ ] 每个阶段的 Objective 可追溯到 `~/bench_workspace/workspace{i}/stage1/BENCHMARK_DRAFT.md` 中的对应章节。
- [ ] Stage 2 明确列出每个数据源的计划采集数量与单位，且与 `BENCHMARK_DRAFT.md` 中的数据构造方案一致。
- [ ] Cross-Stage Dependencies 明确标注了关键路径。
- [ ] Timeline Estimate 包含各阶段的时间预估。
- [ ] 若 `~/bench_workspace/workspace{i}/stage1/BENCHMARK_DRAFT.md` 缺失，不得标记完成。

---

## Rules

- 不执行任何 stage2-stage5 的实际工作（不安装仿真器、不生成数据、不构建评测集、不跑评测）。
- 不擅自改写 `~/bench_workspace/workspace{i}/stage1/BENCHMARK_DRAFT.md` 或任何上游产出。
- 不在计划中虚构 `~/bench_workspace/workspace{i}/stage1/BENCHMARK_DRAFT.md` 中不存在的任务或产出。
- 时间预估必须标注假设前提（如"假设仿真器已预装"、"假设标注人力 2 人"）。
- Risks 必须包含具体的应对方案，不能只列风险不给对策。
- Stage 2 必须为每个选定数据源单独列出采集目标数量与计量单位，不得使用模糊规模描述替代。
- 出错时必须明确指出阻塞原因（如 benchmark 草稿中对应章节定义不清）。
- 如果 Write 因文件过大失败，立即 fallback 到 Bash 分块写入，不要询问用户许可。

---

## Downstream Handoff

- `benchmark-stage2-data-collect` 读取 `~/bench_workspace/workspace{i}/stage1/EXECUTION_PLAN.md` 中 Stage 2 章节作为工作指导。
- `benchmark-stage3-evidence-compiler` 读取 Stage 3 章节。
- `benchmark-stage4-build` 读取 Stage 4 章节。
- `benchmark-stage5-eval` 读取 Stage 5 章节。
- 父流程 `benchmark-stage1-draft` 读取 `~/bench_workspace/workspace{i}/stage1/EXECUTION_PLAN.md` 展示 Gate 1 checkpoint。
- 本模块只写交接关系，不调度下游模块。
