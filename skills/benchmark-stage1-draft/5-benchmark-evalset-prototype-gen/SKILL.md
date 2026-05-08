---
name: benchmark-evalset-prototype-gen
description: "Atomic module: stage1 Phase 5 评测集原型生成模块。只负责基于能力维度与数据源映射结果，为每个维度设计评测任务原型并定义指标体系，不负责生成最终评测集数据或执行评测。Use when user says '设计评测任务'、'generate evalset prototype'、'评测集原型'。"
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

# Benchmark Eval-Set Prototype Generation

Execute eval-set prototype design for: **$ARGUMENTS**

This skill is an **atomic single-responsibility skill**.
It must **only** do the work scoped to this module.

---

## Purpose

- 本模块负责为每个能力维度设计评测任务原型，定义任务描述模板、输入输出规格、数据源类型、指标体系与难度分级。
- 本模块抽象出本 benchmark 的评测集模板方向。
- 本模块可以参考 `~/benchclaw/templates` 的结构经验，但必须根据用户意图、能力维度与数据源映射重新设计评测集模板，禁止全盘照抄。
- 本模块位于 Stage 1 第五环节，直接产物是 `~/bench_workspace/workspace{i}/stage1/EVALSET_PROTOTYPE.md`。
- 本模块不负责生成最终评测集数据、执行评测、草稿合成或计划生成。

---

## Inputs

- `$ARGUMENTS`：评测集设计的补充要求或用户偏好（如偏好某种指标类型）。
- 必需输入：`~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md`、`~/bench_workspace/workspace{i}/stage1/DATA_SOURCE_MAPPING.md`。
- 可选输入：`~/bench_workspace/workspace{i}/stage1/LITERATURE_REVIEW.md`（可借鉴的指标设计模式）。
- 可选参考：`~/benchclaw/templates`（仅用于理解评测模板的组织方式、字段风格、质量检查思路；不得全盘复制模板正文、字段组合或任务结构）。
- **若任一必需输入缺失，应立即停止并报告缺失文件。**

---

## Template Reference and Non-Copy Rule

- 中文任务优先：必须先用中文说明模板设计逻辑，英文仅作为字段名、术语或辅助说明。
- 可以参考 `~/benchclaw/templates` 中已有模板的结构经验，例如章节组织、字段命名习惯、指标呈现方式和质量检查清单。
- 不得照抄参考模板的任务文本、字段集合、指标描述、样例表达、任务结构或顺序；相似模板必须重新命名、重新定义槽位、重新推导输入输出与指标。
- 模板设计必须从三类上游信息推导：用户原始意图与 `$ARGUMENTS`、`CAPABILITY_SCOPE.md` 中的能力维度、`DATA_SOURCE_MAPPING.md` 中的数据源覆盖情况。
- 每个任务原型都要回答两个问题：为什么这个模板能测对应能力维度；它相对参考模板做了哪些面向本 benchmark 的改造。

---

## Procedure

1. **读取上游产出**：读取 `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md` 获取所有能力维度及其操作性定义，读取 `~/bench_workspace/workspace{i}/stage1/DATA_SOURCE_MAPPING.md` 获取每个维度的数据源分配与覆盖情况。
2. **参考模板但不复制**：若 `~/benchclaw/templates` 可用，只提炼可迁移的设计思想，并记录参考来源；不得把任何模板原文、字段组合或任务结构直接迁入本产物。
3. **基于能力维度重新设计任务原型**：为每个能力维度设计 1-3 个评测任务原型，每个原型必须从能力定义、用户意图和数据源可行性出发重新推导，并定义：
   - **任务描述模板**：自然语言指令格式，包含可变槽位
   - **输入规格**：场景配置、初始状态、提供给 agent 的信息
   - **期望输出规格**：动作序列、状态变化、生成物的格式与约束
   - **对应数据源**：来自 `~/bench_workspace/workspace{i}/stage1/DATA_SOURCE_MAPPING.md` 的分配结果
   - **难度分级方式**：若适用，说明如何从同一模板生成不同难度的实例
   - **能力映射理由**：说明该模板为什么能测对应能力维度
   - **差异化设计**：说明相对参考模板或通用模板做出的本 benchmark 专属改造
4. **设计指标体系**：
   - **维度级指标**：每个维度的独立评分指标与计算方式
   - **聚合指标**：跨维度的综合评分方式
   - **辅助诊断指标**：用于分析失败模式的细粒度指标
5. **校验**：
   - 确认每个能力维度都有至少一个任务原型
   - 确认每个任务原型的数据源分配与 `~/bench_workspace/workspace{i}/stage1/DATA_SOURCE_MAPPING.md` 一致
   - 确认指标体系覆盖所有维度
   - 确认所有模板参考都有差异化说明，且不存在照抄参考模板的内容
6. **写入**：写入 `~/bench_workspace/workspace{i}/stage1/EVALSET_PROTOTYPE.md`。

---

## Expected Outputs

- `~/bench_workspace/workspace{i}/stage1/EVALSET_PROTOTYPE.md`

输出文件结构：

```markdown
# Eval-Set Prototype

## Task Prototype Overview
[任务原型总数、覆盖维度、难度分布]

## Task Prototypes

### Dimension: [维度名称]

#### Task Prototype 1: [任务名称]
- **Instruction template**: [自然语言指令模板]
- **Input spec**: [场景配置、初始状态]
- **Expected output spec**: [期望输出格式]
- **Data source**: [对应数据源类型与名称]
- **Difficulty levels**: [难度分级]
- **Capability rationale**: [为什么该任务能测该能力维度]
- **Template adaptation**: [参考模板启发与本 benchmark 专属改造；若未参考模板则写 none]

#### Task Prototype 2: [任务名称]
...

### Dimension: [维度名称]
...

## Metric System

### Dimension-Level Metrics
| Dimension | Metric | Computation | Range |
|-----------|--------|-------------|-------|
| ...       | ...    | ...         | ...   |

### Aggregate Metrics
[跨维度综合评分方式]

### Diagnostic Metrics
[细粒度诊断指标]

## Template Reference and Adaptation Notes
[参考 `~/benchclaw/templates` 或 workspace templates/ 的路径、只借鉴了哪些结构思想、做了哪些面向用户意图与能力维度的改造、如何确认没有照抄]
```

---

## Completion Criteria

- [ ] `~/bench_workspace/workspace{i}/stage1/EVALSET_PROTOTYPE.md` 已存在且非空。
- [ ] 每个能力维度（来自 `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md`）都有至少 1 个任务原型。
- [ ] 每个任务原型包含完整定义字段（instruction template、input spec、output spec、data source、difficulty levels、capability rationale、template adaptation）。
- [ ] Metric System 包含维度级、聚合和诊断三个层级的指标定义。
- [ ] 任务原型中引用的数据源与 `~/bench_workspace/workspace{i}/stage1/DATA_SOURCE_MAPPING.md` 的分配一致。
- [ ] 若参考 `~/benchclaw/templates` 或 workspace templates/，必须写明参考路径、借鉴点、改造点和非照抄依据。
- [ ] 若必需输入缺失，不得标记完成。

---

## Rules

- 不生成最终评测集数据——本模块只设计原型框架，不实例化具体测试样本。
- 不生成 `~/bench_workspace/workspace{i}/stage1/BENCHMARK_DRAFT.md`、`~/bench_workspace/workspace{i}/stage1/EXECUTION_PLAN.md` 或任何后续 phase 产物。
- 不擅自改写 `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md` 或 `~/bench_workspace/workspace{i}/stage1/DATA_SOURCE_MAPPING.md`。
- 可以参考 `~/benchclaw/templates`，但不得照抄、翻译照抄或轻微改写式搬运；必须体现对用户意图和能力维度的重新思考。
- 不把任务原型当作最终 stage4 评测集——原型会在 stage2-stage4 中迭代细化，其中 Stage 3 负责 Data-Juicer 清洗。
- 指标计算方式必须足够具体，不能使用"合理性评估"等无法自动化的表述。
- 出错时必须明确指出阻塞原因（如某维度在 DATA_SOURCE_MAPPING 中标记为 none 导致无法设计可执行任务）。
- 如果 Write 因文件过大失败，立即 fallback 到 Bash 分块写入，不要询问用户许可。

---

## Downstream Handoff

- `benchmark-draft-gen` 读取 `~/bench_workspace/workspace{i}/stage1/EVALSET_PROTOTYPE.md` 中的任务原型与指标体系写入草稿的评测集设计章节。
- `benchmark-execution-plan-gen` 读取 `~/bench_workspace/workspace{i}/stage1/EVALSET_PROTOTYPE.md` 规划 Stage 4 的评测集构建任务分解。
- stage4 evalset 构建分支参考 `~/bench_workspace/workspace{i}/stage1/EVALSET_PROTOTYPE.md` 的原型框架实例化最终测试样本。
- 本模块只写交接关系，不调度下游模块.
