---
name: benchmark-capability-scope
description: "Atomic module: stage1 Phase 3 能力维度划分模块。只负责基于精炼目标与文献调研结论，将 benchmark 目标细化为具体的、可操作的能力维度集合，不负责数据源选取、评测集设计或草稿生成。Use when user says '划分能力维度'、'define capability dimensions'、'能力范围'。"
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

# Benchmark Capability Scope

Execute capability dimension scoping for: **$ARGUMENTS**

This skill is an **atomic single-responsibility skill**.
It must **only** do the work scoped to this module.

---

## Purpose

- 本模块负责将 benchmark 目标细化为具体的、可操作的能力维度集合。
- 本模块确保维度满足完整性、低重叠、可操作化、可区分四项原则。
- 本模块位于 Stage 1 第三环节，直接产物是 `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md`。
- 本模块不负责数据源选取、评测集设计、草稿合成或执行计划生成。

---

## Inputs

- `$ARGUMENTS`：能力维度划分的补充要求或用户偏好。
- 必需输入：`~/bench_workspace/workspace{i}/stage1/IDEA_TARGET.md`、`~/bench_workspace/workspace{i}/stage1/LITERATURE_REVIEW.md`。
- 可选输入：用户给出的维度草稿片段、已有 benchmark 的维度体系参考。
- **若任一必需输入缺失，应立即停止并报告缺失文件。**

---

## Procedure

1. **读取上游产出**：读取 `~/bench_workspace/workspace{i}/stage1/IDEA_TARGET.md` 中的 Core Evaluation Intent 和 Target Boundary，读取 `~/bench_workspace/workspace{i}/stage1/LITERATURE_REVIEW.md` 中的 Structural Gaps、Reusable Design Patterns 和 Constraints。
2. **初步维度枚举**：基于目标定义与调研约束，列出所有候选能力维度。
3. **维度质量检查**：对每个候选维度逐一验证四项原则：
   - **完整性**：是否覆盖 Core Evaluation Intent 所声称测试的全部核心能力
   - **低重叠**：维度之间是否语义正交，避免同一能力被多个维度重复测量
   - **可操作化**：是否可对应到具体的测试任务设计，不能是抽象概念
   - **可区分**：粒度是否足够细，能区分不同系统的能力差异
4. **维度定义**：为每个通过检查的维度定义——
   - 维度名称
   - 操作性定义（而非概念性定义）
   - 对应的任务类型示例
   - 评测信号来源
   - 新颖性标注（existing / partial / novel）
   - 与其他维度的依赖关系
5. **建立维度关系**：绘制维度之间的层次或依赖关系（平铺、分层或混合结构）。
6. **覆盖分析**：标注哪些维度在已有 benchmark 中已被充分覆盖、哪些是部分覆盖、哪些是本 benchmark 的差异化贡献。
7. **完整性自检**：对照 `~/bench_workspace/workspace{i}/stage1/IDEA_TARGET.md` 中的 Core Evaluation Intent，逐项确认每个评测意图都被至少一个维度覆盖。
8. **写入**：写入 `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md`。

---

## Expected Outputs

- `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md`

输出文件结构：

```markdown
# Capability Scope

## Dimension Overview
[维度总数与整体结构说明]

## Capability Dimensions

### Dimension 1: [名称]
- **Operational definition**: [操作性定义]
- **Task type examples**: [对应任务类型]
- **Evaluation signal**: [评测信号来源]
- **Novelty**: [existing / partial / novel]
- **Dependencies**: [依赖的其他维度，若无则 none]

### Dimension 2: [名称]
...

## Dimension Relationship Map
[维度之间的层次或依赖关系]

## Coverage Analysis
- Dimensions well-covered by existing benchmarks: [列表]
- Dimensions partially covered: [列表]
- Novel dimensions (this benchmark's contribution): [列表]

## Completeness Self-Check
[对照 IDEA_TARGET.md 中的 core evaluation intent，逐项确认覆盖情况]
```

---

## Completion Criteria

- [ ] `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md` 已存在且非空。
- [ ] 至少定义了 3 个能力维度，每个维度包含完整的五项定义字段。
- [ ] Novel dimensions 至少有 1 个（否则 benchmark 缺乏新颖性）。
- [ ] Completeness Self-Check 确认所有 Core Evaluation Intent 均被覆盖。
- [ ] 维度之间无明显语义重叠（已在 Procedure 步骤 3 中验证）。
- [ ] 若必需输入缺失，不得标记完成。

---

## Rules

- 不生成 `~/bench_workspace/workspace{i}/stage1/DATA_SOURCE_MAPPING.md`、`~/bench_workspace/workspace{i}/stage1/EVALSET_PROTOTYPE.md`、`~/bench_workspace/workspace{i}/stage1/BENCHMARK_DRAFT.md` 或任何后续 phase 产物。
- 不擅自改写 `~/bench_workspace/workspace{i}/stage1/IDEA_TARGET.md` 或 `~/bench_workspace/workspace{i}/stage1/LITERATURE_REVIEW.md`。
- 不在维度定义中预设数据源选择——那是 Phase 4 的职责。
- 不把抽象概念（如"智能"、"通用性"）作为能力维度——每个维度必须可操作化。
- 出错时必须明确指出阻塞原因（如目标定义过于模糊导致无法划分维度）。
- 如果 Write 因文件过大失败，立即 fallback 到 Bash 分块写入，不要询问用户许可.

---

## Downstream Handoff

- `benchmark-data-source-selection` 读取 `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md` 将每个维度与三类数据源能力匹配。
- `benchmark-evalset-prototype-gen` 读取 `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md` 为每个维度设计评测任务原型。
- `benchmark-draft-gen` 读取 `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md` 的维度体系写入草稿。
- 本模块只写交接关系，不调度下游模块.
