---
name: benchmark-stage1-draft
 description: "Stage 1 子流程：草稿生成。编排 idea-target-refine → benchmark-literature-survey → benchmark-capability-scope → benchmark-data-source-selection → benchmark-evalset-prototype-gen → benchmark-draft-gen → benchmark-execution-plan-gen，从用户的粗糙 benchmark idea 生成精炼目标、文献调研、能力维度、数据源选取、评测集原型、benchmark 草稿与执行计划。本阶段仅负责草稿与计划，不负责采集数据、Data-Juicer 清洗、构建最终评测集或运行模型评测。Use when user says '先做 stage1'、'生成 benchmark 草稿'、'从粗糙 idea 先出草稿'、'benchmark draft stage'."
argument-hint: [benchmark-idea]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, WebSearch, WebFetch, Skill
---

## `~/benchclaw` 只读约束

- **BENCHCLAW_READONLY = true**：`~/benchclaw/` 只能作为共享只读资源根。
- 严禁在 `~/benchclaw/` 下创建、编辑、覆盖、删除、移动、重命名、复制写入、初始化 git、提交、打 tag、写日志、写缓存或写临时文件。
- 所有派生产物、补丁、快照、报告、脚本、配置、日志和测试输出必须写入 active `WORKSPACE_ROOT`。
- 如必须修改 `~/benchclaw/` 中的资源，只能在 workspace 中生成 patch 或修改建议，等待用户在外部处理；当前 skill 不得直接应用。


## Workspace and File Access Boundary

This skill must operate only inside the current run workspace.

- Before reading or writing any run artifact, resolve and record the active `WORKSPACE_ROOT = ~/bench_workspace/workspace{i}` from the current task, parent stage, or pipeline state.
- If invoked by `/benchmark-pipeline`, inherit the exact `WORKSPACE_ROOT` created by the parent pipeline. If invoked standalone and no `WORKSPACE_ROOT` is provided, create a new workspace by scanning only `~/bench_workspace/workspace*`, choosing `i = max(existing_i) + 1`, and creating `~/bench_workspace/workspace{i}`; if none exist, create `workspace1`.
- Read and write only files under the active `WORKSPACE_ROOT`. The explicitly required global resource roots named by this skill, such as `~/benchclaw/simulator_cards/`, `~/benchclaw/dataset_cards/`, `~/benchclaw/realdata_cards/`, `~/benchclaw/templates/`, `~/benchclaw/model_api/`, `~/benchclaw/data-juicer_card/`, `~/benchclaw/annotation-tool/`, or `~/benchclaw/skills/`, are read-only inputs.
- Never create, edit, overwrite, delete, move, rename, copy files into, initialize git state in, commit, tag, cache, or log under any path inside `~/benchclaw/`.
- Never read, list, grep, summarize, compare, copy, or infer from any other `~/bench_workspace/workspace{j}` where `j != i`, even if the current artifact is missing or another workspace appears newer or more complete.
- Never scan broad server directories such as `~`, `/`, `/home`, `/mnt`, `/data`, `/tmp`, `C:\Users`, `C:\`, or arbitrary project/download folders to discover context. Only inspect the exact current workspace paths and exact allowlisted resource roots needed for this skill.
- If an expected input is missing from the active workspace or an allowlisted resource root, stop and report the missing path. Do not search unrelated folders or borrow replacement artifacts from another workspace.
- Outputs must be written only to the active `WORKSPACE_ROOT` paths declared by this skill. Do not mirror or cache run artifacts into other workspaces or unrelated server folders.
- All intermediate files, logs, temporary manifests, generated drafts, unit tests, and reports must stay under `WORKSPACE_ROOT/stage1/`.
- If the user explicitly provides an external path, use it only when it is directly relevant to this skill, record it as a user-provided exception, and do not expand access to sibling or parent directories.

This boundary overrides convenience behaviors such as auto-discovery, resume from latest workspace, reuse of previous artifacts, broad recursive grep/list, and fallback search.

# Benchmark Stage 1: 草稿生成

Orchestrate the complete Stage 1 draft-generation workflow for: **$ARGUMENTS**

This skill is an **orchestrator only**.
It must **not** re-implement, expand, or substitute the internal logic of any sub-skill.

## Overview

This skill chains Stage 1 sub-skills into a single automated pipeline:

```text
raw_idea
→ idea-target-refine
→ /benchmark-literature-survey
→ /benchmark-capability-scope
→ /benchmark-data-source-selection
→ /benchmark-evalset-prototype-gen
→ /benchmark-draft-gen
→ /benchmark-execution-plan-gen
→ /benchmark-unit-test-stage1
(目标提炼)  (文献与已有benchmark调研)  (能力维度精细划分)  (数据源选取)  (评测集与指标原型模板生成)  (benchmark草稿合成)  (执行计划生成)  (Stage 1 单元测试)
```

Each phase builds on the previous one's output。Phase 之间严格顺序依赖，不可跳过或乱序。

## Workspace

所有产出写入当前 workspace 的 `~/bench_workspace/workspace{i}/stage1/` 子目录：

```
~/bench_workspace/workspace{i}/stage1/
```

其中 `{i}` 由父流程或用户指定。若未指定，Stage 1 作为初始阶段必须创建新的递增 workspace：扫描 `~/bench_workspace/workspace*`，选择 `max(existing_i)+1`；若不存在旧 workspace，则创建 `workspace1`。不得默认使用序号最高的旧 workspace。

## Workspace Isolation Rule

本次 Stage 1 运行必须与其他 workspace 隔离。只能读写当前 `~/bench_workspace/workspace{i}/` 下的产物；明确允许的全局资源目录（如 `~/benchclaw/*_cards/`、`~/benchclaw/templates/`）只能只读参考。不得读取、参考、复制或借鉴其他 `~/bench_workspace/workspace{j}` 的内容（`j != i`），也不得让其他 workspace 里已经生成的草稿、数据源映射、评测结果或诊断报告影响本次生成。若确需复用其他 workspace，必须由用户显式指定路径和复用范围。所有中间过程文件都必须写入 `~/bench_workspace/workspace{i}/stage1/`，不得写入 skill 源码目录、Downloads、当前项目目录、缓存目录或 `~/benchclaw/`。

## Constants

* **AUTO_PROCEED = false** — 关卡处是否自动继续。默认等待用户确认。
* **NO_BENCHCLAW_WRITE = true** — `~/benchclaw/` 下所有内容只读，严禁增删改。
* **STAGE_BOUNDARY_STOP = true** — Stage 1 全部完成后必须停止，由用户选择下一步；即使 `AUTO_PROCEED = true`，也不得自动进入 Stage 2。
* **COMPACT = false** — 为 `true` 时，额外生成 `STAGE1_COMPACT.md` 供下游 skill 或长会话恢复使用。
* **LITERATURE_CRAWL = true** — 为 `true` 时，Phase 2 主动检索论文、已有 benchmark、公开评测框架。
* **MAX_REFINEMENT_ROUNDS = 2** — Stage 1 内部允许的轻量重整轮数上限。
* **WRITE_STAGE_LOG = true** — 每个 phase 完成后将结论追加写入 `STAGE1_SUMMARY.md` 的滚动记录。
* **TIMEOUT = 0** — 用户无响应超时秒数。仅当 `AUTO_PROCEED = false` 且 `TIMEOUT > 5000` 时自动继续。

> 💡 Override by telling the skill, e.g.
> `/benchmark-stage1-draft "多模态工具使用 benchmark" — AUTO_PROCEED: false, COMPACT: true`

## Pipeline

### Phase 1: Idea Target Refine — 目标提炼

从粗糙 idea 中提炼精确的 benchmark 目标定义。

**输入：** `$ARGUMENTS`

**执行内容：**

* 从粗糙描述中抽取核心评测意图：要测什么能力、面向什么类型的系统
* 明确 benchmark 的目标边界：测试对象（agent 类型）、任务场景类别、期望产出形式
* 区分目标与非目标：显式列出本 benchmark 不打算覆盖的方向
* 确定 benchmark 的定位语句：一句话说明这个 benchmark 为什么需要存在、与已有工作的预期差异点

**Expected output：**

写入 `~/bench_workspace/workspace{i}/stage1/IDEA_TARGET.md`，包含：

```markdown
# Benchmark Target Definition

## Core Evaluation Intent
[要测什么能力，面向什么系统]

## Target Boundary
- Test subject: [agent 类型]
- Scenario class: [任务场景类别]
- Expected output form: [期望产出形式]

## Non-Goals
- [非目标1]
- [非目标2]

## Positioning Statement
[一句话定位]

## Raw Idea Trace
[原始 idea 原文保留，供后续回溯]
```

**🚦 Checkpoint:**

```text
🎯 Target refinement complete:
- Core intent: [核心评测意图]
- Test subject: [测试对象]
- Positioning: [一句话定位]
- Non-goals: [非目标列表]

Proceed to literature survey?
```

* **User approves** → Phase 2
* **User requests revision** → 修订 `IDEA_TARGET.md`，重跑 Phase 1（计入 MAX_REFINEMENT_ROUNDS）

---

### Phase 2: Literature and Existing Benchmark Survey — 文献与已有 Benchmark 调研

Invoke:

```text
/benchmark-literature-survey "$ARGUMENTS"
```

**输入：** `IDEA_TARGET.md` 中精炼后的 benchmark 目标

**执行内容：**

* 检索与 benchmark 目标相关的学术论文、已有 benchmark、公开评测集与评测框架；如果有必要可以下载到本地进行分析
* 梳理每个已有 benchmark 的能力覆盖范围、评测维度设计、数据构造方式、指标体系
* 识别现有方案的结构性缺口：哪些能力没被测到、哪些维度设计粗糙、哪些数据构造方式有局限
* 提炼可借鉴的设计模式与需要规避的已知问题
* 评估本 benchmark 与已有工作的重叠风险，标注弱新颖性区域

**Expected output:**

`~/bench_workspace/workspace{i}/stage1/LITERATURE_REVIEW.md`，包含：

```markdown
# Literature and Existing Benchmark Survey

## Related Benchmarks
| Benchmark | Capabilities Covered | Data Source | Metrics | Limitations |
|-----------|---------------------|-------------|---------|-------------|
| ...       | ...                 | ...         | ...     | ...         |

## Related Papers
[按相关性排序的论文摘要与关键发现]

## Reusable Design Patterns
[可借鉴的评测维度设计、数据构造方式、指标设计]

## Structural Gaps
[现有工作未覆盖但本 benchmark 应覆盖的区域]

## Duplication and Weak Novelty Risks
[与已有工作高度重叠的区域，需要在草稿中显式差异化的点]

## Constraints Derived from Survey
[调研结论对后续能力维度划分和草稿生成的约束]
```

**🚦 Checkpoint:**

```text
📚 Literature survey complete:
- Surveyed benchmarks: [数量与列表]
- Key design patterns found: [摘要]
- Structural gaps identified: [摘要]
- Duplication risks: [摘要]

Proceed to capability scope definition?
```

* **User approves** → Phase 3
* **User requests broader/narrower scope** → 调整检索范围，重跑 Phase 2
* **User认为 benchmark 目标需调整** → 回退 Phase 1，重新提炼目标后重跑 Phase 2

---

### Phase 3: Capability Scope — 能力维度划分

Invoke:

```text
/benchmark-capability-scope "$ARGUMENTS"
```

**输入：** `IDEA_TARGET.md` + `LITERATURE_REVIEW.md`

**执行内容：**

* 基于精炼后的 benchmark 目标和文献调研结论，将 benchmark 目标细化为具体的能力维度集合
* 能力维度划分原则：
  * **完整性**：覆盖 benchmark 目标所声称测试的全部核心能力
  * **低重叠**：维度之间语义正交，避免同一能力被多个维度重复测量
  * **可操作化**：每个维度必须可对应到具体的测试任务设计，不能是抽象概念
  * **可区分**：维度粒度足够细，能区分不同系统的能力差异
* 为每个维度定义：维度名称、操作性定义、对应的任务类型示例、评测信号来源
* 建立维度之间的层次或依赖关系（若存在）
* 标注哪些维度在已有 benchmark 中已被充分覆盖、哪些是本 benchmark 的差异化贡献

**Expected output:**

`~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md`，包含：

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

**🚦 Checkpoint:**

```text
📐 Capability scope complete:
- Total dimensions: [数量]
- Novel dimensions: [数量与列表]
- Dimension structure: [层次/平铺/混合]

Proceed to data source selection?
```

* **User approves** → Phase 4
* **User认为维度不完整/有重叠** → 修订维度，重跑 Phase 3
* **User认为需要补充调研** → 回退 Phase 2

---

### Phase 4: Data Source Selection — 数据源选取

Invoke:

```text
/benchmark-data-source-selection "$ARGUMENTS"
```

**输入：** `CAPABILITY_SCOPE.md` + 仿真器能力卡片（`~/benchclaw/simulator_cards`）+ 数据集能力卡片（`~/benchclaw/dataset_cards`）+ 真实数据能力卡片（`~/benchclaw/realdata_cards`）

**执行内容：**

* 并行读取三类能力卡片：仿真器、已有数据集、真实采集数据
* 将 `CAPABILITY_SCOPE.md` 中的每个能力维度分别与三类数据源进行匹配：
  * 哪些维度可被单一数据源直接支持
  * 哪些维度需要跨数据源组合覆盖
  * 哪些维度当前无任何来源可支持（需要离线数据或人工构造）
* 为每个维度推荐首选数据源及备选方案
* 评估数据源组合的可行性：接入或采集复杂度、稳定性、场景或域多样性、复用或获取效率
* 汇总各来源对未覆盖维度的补充或替代能力

**Expected output:**

`~/bench_workspace/workspace{i}/stage1/DATA_SOURCE_MAPPING.md`，包含：

三个数据源分支子流程的中间产物必须放在 `~/bench_workspace/workspace{i}/stage1/data_source_selection/`：

- `SIMULATOR_MAPPING.md`
- `DATASET_MAPPING.md`
- `REALDATA_MAPPING.md`

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

**🚦 Checkpoint:**

```text
🧭 Data source selection complete:
- Sources selected: [列表]
- Fully covered dimensions: [数量]
- Partially covered: [数量]
- Uncovered (need offline data): [数量]

Proceed to eval-set prototype generation?
```

* **User approves** → Phase 5
* **User认为数据源选择不合理** → 修订映射，重跑 Phase 4
* **User认为能力维度需调整以匹配可用数据源** → 回退 Phase 3 调整维度后重跑 Phase 4

---

### Phase 5: Eval-Set Prototype Generation — 评测集原型生成

Invoke:

```text
/benchmark-evalset-prototype-gen "$ARGUMENTS"
```

**输入：** `IDEA_TARGET.md` + `CAPABILITY_SCOPE.md` + `DATA_SOURCE_MAPPING.md` + `LITERATURE_REVIEW.md`（若存在）+ `/home/maqiang/benchclaw/templates` 或 `~/benchclaw/templates`（可选只读、私有结构参考；不是模板制造依据，不得在产物中披露）

**执行内容：**

* 基于能力维度与选定数据源的匹配结果，为每个维度设计评测任务原型
* 每个任务原型定义：
  * 任务描述模板（自然语言指令格式）
  * 输入规格（场景配置、初始状态、提供给 agent 的信息）
  * 期望输出规格（动作序列、状态变化、生成物）
  * 评测指标及计算方式
  * 难度分级方式（若适用）
* 可私有查看 `/home/maqiang/benchclaw/templates` 或 `~/benchclaw/templates` 中已有模板的一般组织方式、字段风格和质量检查思路，但这些模板不是制造依据，不得照抄模板正文、字段集合、任务结构、指标描述或样例表达
* 必须只基于用户意图、`CAPABILITY_SCOPE.md` 中分析出的能力维度、`DATA_SOURCE_MAPPING.md` 中的数据源覆盖情况，以及 `LITERATURE_REVIEW.md` 中的论文调研分析，重新推导本 benchmark 的评测集模板方向
* 每个任务原型必须说明：
  * 为什么该模板能测对应能力维度
  * 如何由本次 benchmark 目标、能力维度、数据证据和论文调研重新推导而来
* 设计指标体系：
  * 维度级指标（每个维度的独立评分）
  * 聚合指标（跨维度的综合评分方式）
  * 辅助诊断指标（用于分析失败模式的细粒度指标）
* 显式生成模板草稿附属目录 `evalset_template_drafts/`：
  * 为每个能力维度至少生成一个模板初稿，或记录明确 blocking gap
  * 每个模板初稿同时写入 `.yaml` 和 `.md`
  * 每个模板初稿必须包含 `non_copy_declaration`
  * 写入 `TEMPLATE_DRAFT_INDEX.md`、`TEMPLATE_DRAFT_LINEAGE.md` 和 `ANTI_COPY_DECLARATION.md`
* 严禁抄袭模板：私有查看 `/home/maqiang/benchclaw/templates` 或 `~/benchclaw/templates` 时只能作为非依据的结构参考；不得复制、翻译复制、轻改或拼贴参考模板的正文、字段组合、任务结构、示例表达或评分描述，也不得在任何产物中写明参考路径、模板名称、借鉴点、改写关系或重组关系。

**Expected output:**

- `~/bench_workspace/workspace{i}/stage1/EVALSET_PROTOTYPE.md`
- `~/bench_workspace/workspace{i}/stage1/evalset_template_drafts/`
- `~/bench_workspace/workspace{i}/stage1/evalset_template_drafts/TEMPLATE_DRAFT_INDEX.md`
- `~/bench_workspace/workspace{i}/stage1/evalset_template_drafts/TEMPLATE_DRAFT_LINEAGE.md`
- `~/bench_workspace/workspace{i}/stage1/evalset_template_drafts/ANTI_COPY_DECLARATION.md`
- `~/bench_workspace/workspace{i}/stage1/evalset_template_drafts/{capability_dimension_slug}/{template_id}.yaml`
- `~/bench_workspace/workspace{i}/stage1/evalset_template_drafts/{capability_dimension_slug}/{template_id}.md`

`EVALSET_PROTOTYPE.md` 包含：

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
- **Benchmark-specific synthesis basis**: [本次用户意图、能力维度、数据源映射与论文调研如何共同支撑该模板]

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

## Template Synthesis Basis
[仅写本次用户意图、能力维度、数据源映射与论文调研如何支撑模板生成；不得写任何已有模板路径、名称、来源、借鉴点或重组关系]

## Template Draft Directory
| Template ID | YAML | Markdown | Capability Dimension | Source Binding |
|-------------|------|----------|----------------------|----------------|

## Anti-Copy Self-Check
| Check | Result | Evidence |
|-------|--------|----------|
```

**🚦 Checkpoint:**

```text
📝 Eval-set prototype complete:
- Task prototypes: [数量] across [维度数] dimensions
- Metrics defined: [维度级 + 聚合 + 诊断指标数量]
- Template draft files: [yaml 数量] YAML + [markdown 数量] Markdown under evalset_template_drafts/
- Template synthesis basis: [用户意图、能力维度、数据映射和论文调研如何支撑模板重新推导；不得披露已有模板来源]
- Anti-copy declaration: [PASS/NEEDS_REVIEW]

Proceed to benchmark draft synthesis?
```

* **User approves** → Phase 6
* **User认为任务原型不清晰或与维度不匹配** → 修订原型，重跑 Phase 5
* **User认为指标设计不合理** → 修订指标体系，重跑 Phase 5
* **User认为仿真器覆盖不足** → 回退 Phase 4

---

### Phase 6: Benchmark Draft Generation — Benchmark 草稿合成

Invoke:

```text
/benchmark-draft-gen "$ARGUMENTS"
```

**输入：** `IDEA_TARGET.md` + `LITERATURE_REVIEW.md` + `CAPABILITY_SCOPE.md` + `DATA_SOURCE_MAPPING.md` + `EVALSET_PROTOTYPE.md` + `evalset_template_drafts/`

**执行内容：**

* 将前序所有 phase 的产出整合为一份完整的 benchmark 草稿
* 草稿结构：
  * Benchmark 名称与一句话定位
  * 动机与背景（基于文献调研的 gap 分析）
  * 能力维度体系（来自 CAPABILITY_SCOPE.md）
  * 数据构造方案（仿真器、已有数据集、真实数据的组合选择，来自 DATA_SOURCE_MAPPING.md）
  * 评测集设计（任务原型 + 指标体系 + 模板草稿索引，来自 `EVALSET_PROTOTYPE.md` 和 `evalset_template_drafts/`）
  * 与已有 benchmark 的对比定位
  * 已知局限与后续扩展方向
* 草稿必须内部自洽：能力维度 → 数据源覆盖 → 任务原型 → 指标体系之间有清晰的追溯链
* 标注草稿中仍需 stage2-stage5 继续完善的内容

**Expected output:**

`~/bench_workspace/workspace{i}/stage1/BENCHMARK_DRAFT.md`，包含：

```markdown
# [Benchmark Name]: [一句话定位]

## 1. Motivation
[动机：基于文献调研的 gap 分析，为什么需要这个 benchmark]

## 2. Capability Dimensions
[能力维度体系概述，引用 CAPABILITY_SCOPE.md]

## 3. Data Construction
### 3.1 Source-Based Generation
[选定数据源组合与生成策略，引用 DATA_SOURCE_MAPPING.md]
### 3.2 Offline Data Sources
[离线数据补充方案]

## 4. Eval-Set Design
### 4.1 Task Design
[任务原型概述，引用 EVALSET_PROTOTYPE.md 和 evalset_template_drafts/]
### 4.2 Metric System
[指标体系概述]
### 4.3 Template Drafts and Anti-Copy Notes
[模板草稿目录、模板 lineage、anti-copy declaration 摘要]

## 5. Comparison with Existing Benchmarks
[与已有 benchmark 的对比定位表]

## 6. Known Limitations and Future Extensions
[已知局限、后续扩展方向]

## 7. Downstream Handoff Notes
[需要 stage2-stage5 继续完善的内容及其对应 stage]
```

**🚦 Checkpoint:**

```text
📄 Benchmark draft synthesized:
- Benchmark name: [名称]
- Positioning: [一句话定位]
- Dimensions: [数量]
- Simulators: [列表]
- Task prototypes: [数量]
- Remaining downstream items: [数量] (to be completed in stage2-5)

Proceed to execution plan generation?
```

* **User approves** → Phase 7
* **User requests changes** → 修订草稿，重跑 Phase 6
* **User认为 benchmark 方向根本错误** → 回退至 Phase 1 或 Phase 2

---

### Phase 7: Execution Plan Generation — 执行计划生成

Invoke:

```text
/benchmark-execution-plan-gen "$ARGUMENTS"
```

**输入：** `BENCHMARK_DRAFT.md` + 全部前序产出

**执行内容：**

* 根据 benchmark 草稿，为 stage2-stage5 的每个阶段生成具体的执行计划
* 每个阶段的执行计划必须包含：
  * 阶段目标（与 BENCHMARK_DRAFT.md 中的对应部分对齐）
  * 输入依赖（需要哪些前序产出）
  * 具体任务分解
  * 预期产出物
  * 验收标准
  * 风险点与应对方案
* 执行计划必须与 BENCHMARK_DRAFT.md 中的对应章节一一对应

**Expected output:**

`~/bench_workspace/workspace{i}/stage1/EXECUTION_PLAN.md`，包含：

```markdown
# Execution Plan

## Stage 2: Data Collection
- **Objective**: [与 BENCHMARK_DRAFT.md 对齐的阶段目标]
- **Input dependencies**: [前序产出列表]
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

**🚦 Checkpoint:**

```text
📋 Execution plan ready:
- Stage 2 target: [摘要]
- Stage 3 target: [摘要]
- Stage 4 target: [摘要]
- Stage 5 target: [摘要]
- Estimated total timeline: [预估]

Proceed to final summary?
```

* **User approves** → Phase 8
* **User requests changes** → 修订执行计划，重跑 Phase 7
* **User认为计划与草稿不一致** → 回退 Phase 6 先修订草稿

---

### Phase 8: Unit Test — Stage 1 草稿契约单元测试

Invoke:

```text
/benchmark-unit-test-stage1 "$STAGE1_DIR"
```

**输入：** Stage 1 全部产物。

**执行内容：**

* 检查 `IDEA_TARGET.md`、`LITERATURE_REVIEW.md`、`CAPABILITY_SCOPE.md`、`DATA_SOURCE_MAPPING.md`、`EVALSET_PROTOTYPE.md`、`evalset_template_drafts/`、`BENCHMARK_DRAFT.md`、`EXECUTION_PLAN.md` 是否存在且结构完整。
* 检查 `evalset_template_drafts/` 下是否存在 `TEMPLATE_DRAFT_INDEX.md`、`TEMPLATE_DRAFT_LINEAGE.md`、`ANTI_COPY_DECLARATION.md`，以及每个能力维度的 `.yaml` / `.md` 模板初稿。
* 检查每个模板初稿是否包含 `non_copy_declaration`，并能追溯到本次 `IDEA_TARGET.md`、`CAPABILITY_SCOPE.md` 和 `DATA_SOURCE_MAPPING.md`。
* 检查能力维度是否可操作、低重叠、可映射到 ground truth 或显式 waiver。
* 检查草稿、原型、执行计划之间的维度编号、数据需求、模板字段是否一致。
* 给出 `PASS | FAIL | NEEDS_REVIEW` verdict；FAIL 时必须定位到 Stage 1 的具体 phase 和 atomic skill。

**Expected output:**

* `~/bench_workspace/workspace{i}/stage1/unit_tests/test_stage1_contract.py`
* `~/bench_workspace/workspace{i}/stage1/unit_tests/results.json`
* `~/bench_workspace/workspace{i}/stage1/STAGE1_UNIT_TEST_REPORT.md`

**🚦 Quality Gate:**

* `PASS` → 可以进入 Stage 2。
* `NEEDS_REVIEW` → 用户确认 waiver 后才能进入 Stage 2。
* `FAIL` → 不得进入 Stage 2；按报告中的 fix target 回退重跑对应 Phase。

---

### Phase 8: Final Summary

Finalize `~/bench_workspace/workspace{i}/stage1/STAGE1_SUMMARY.md`。

```markdown
# Stage1 Summary

**Benchmark Idea**: $ARGUMENTS
**Date**: [today]
**Pipeline**: idea-target-refine → literature-survey → capability-scope → simulator-mapping → evalset-prototype-gen → draft-gen → execution-plan-gen

## Executive Summary
[2-3 sentences: benchmark 目标、能力维度数、仿真器选择、草稿状态、建议下一步]

## Phase Results

### Phase 1: Target Refinement
- Output: `IDEA_TARGET.md`
- Summary: [摘要]

### Phase 2: Literature Survey
- Output: `LITERATURE_REVIEW.md`
- Summary: [摘要]

### Phase 3: Capability Scope
- Output: `CAPABILITY_SCOPE.md`
- Summary: [摘要]

### Phase 4: Data Source Selection
- Output: `DATA_SOURCE_MAPPING.md`
- Summary: [摘要]

### Phase 5: Eval-Set Prototype
- Output: `EVALSET_PROTOTYPE.md` + `evalset_template_drafts/`
- Summary: [摘要]

### Phase 6: Benchmark Draft
- Output: `BENCHMARK_DRAFT.md`
- Summary: [摘要]

### Phase 7: Execution Plan
- Output: `EXECUTION_PLAN.md`
- Summary: [摘要]

## Final Deliverables
- `IDEA_TARGET.md`
- `LITERATURE_REVIEW.md`
- `CAPABILITY_SCOPE.md`
- `DATA_SOURCE_MAPPING.md`
- `data_source_selection/SIMULATOR_MAPPING.md`
- `data_source_selection/DATASET_MAPPING.md`
- `data_source_selection/REALDATA_MAPPING.md`
- `EVALSET_PROTOTYPE.md`
- `evalset_template_drafts/`
- `evalset_template_drafts/TEMPLATE_DRAFT_INDEX.md`
- `evalset_template_drafts/TEMPLATE_DRAFT_LINEAGE.md`
- `evalset_template_drafts/ANTI_COPY_DECLARATION.md`
- `BENCHMARK_DRAFT.md`
- `EXECUTION_PLAN.md`
- `STAGE1_SUMMARY.md`

## Refinement Log
[记录所有 phase 重跑的原因与变更摘要]

## Recommended Next Step
- [ ] Proceed to `/benchmark-stage2-data-collect`
- [ ] Or revise Stage 1 scope/draft before continuing
- [ ] Review Stage 1 artifacts only
- [ ] Pause pipeline
```

---

### Phase 8.5: Write Compact Files (when COMPACT = true)

**Skip entirely if `COMPACT` is `false`.**

Write `~/bench_workspace/workspace{i}/stage1/STAGE1_COMPACT.md`：

```markdown
# Stage1 Compact Summary

## Benchmark Direction
[一句话 benchmark 方向]

## Capability Dimensions
- [维度1]
- [维度2]
- ...

## Selected Data Sources
- [数据源1]: [覆盖维度]
- [数据源2]: [覆盖维度]

## Current Status
- Target definition: ready
- Literature review: ready
- Capability scope: ready
- Data source selection: ready
- Eval-set prototype: ready
- Benchmark draft: ready
- Execution plan: ready

## Next Step
/benchmark-stage2-data-collect
```

---

## 🚦 Gate 1 — Draft Checkpoint

After Stage 1 全部完成，展示最终 gate：

```text
📋 Stage1 complete. Draft summary:

1. Benchmark target: [任务目标]
2. Capability dimensions: [维度列表]
3. Simulators selected: [仿真器列表]
4. Eval-set prototype: [评测集与指标模板摘要]
5. Recommended next action: proceed to dataset analysis and selection

Choose the next step:
1. Proceed to Stage 2
2. Revise or rerun a Stage 1 phase
3. Review Stage 1 artifacts
4. Pause pipeline
```

Stage 1 必须在这里停止。不得自动调用 `/benchmark-stage2-data-collect`。`AUTO_PROCEED` 和 `TIMEOUT` 只允许影响 Stage 1 内部 phase 的轻量衔接，不允许跨越 Stage 1 → Stage 2 的大阶段边界。

## 重新执行 Stage 1 的触发条件

以下情况必须重跑对应 phase（计入 `MAX_REFINEMENT_ROUNDS`）：

| 问题 | 回退目标 |
|------|---------|
| Benchmark 目标定义不清晰或不连贯 | Phase 1 |
| 文献调研范围不足或遗漏关键已有工作 | Phase 2 |
| 能力维度不完整或存在重叠 | Phase 3 |
| 依据选定的仿真器无法实现所需能力维度 | Phase 4 |
| 评测集原型模板不清晰或与能力维度不匹配 | Phase 5 |
| Benchmark 草稿内部不自洽 | Phase 6 |
| 执行计划与草稿不对齐 | Phase 7 |

当 `MAX_REFINEMENT_ROUNDS` 耗尽时，将当前最佳草稿标记为 `[NEEDS_REVIEW]` 并继续至 Gate 1，由用户决定是否进入 Stage 2 或在 Stage 2 中修正。

## Key Rules

* **Large file handling**: 若 Write tool 因文件过大失败，立即改用 Bash（`cat << 'EOF' > file`）分块写入。不问用户。
* **Do not skip phases.** 7 个 phase 严格顺序执行。
* **Phase 之间必须 checkpoint.** 每个 phase 完成后展示摘要，等待确认（`HUMAN_CHECKPOINT = true` 时）。
* **Stage boundary stop.** Stage 1 完成后必须停住，展示下一步选项，等待用户选择；不得自动进入 Stage 2。
* **Never write to `~/benchclaw/`.** `~/benchclaw` 只能作为只读资源来源，任何输出、缓存、草稿、模板初稿、报告或补丁都必须写入 active workspace。
* **目标先行.** Phase 1 目标未稳定前，不启动后续 phase。
* **调研先于维度划分.** 文献调研结论是能力维度划分的输入约束，不可跳过。
* **仿真器选择约束维度可行性.** 若仿真器无法支持某维度，必须在 Phase 4 显式标注并在 Phase 3 回退调整或在 Phase 5 改用离线数据方案。
* **草稿内部自洽.** 能力维度 → 仿真器覆盖 → 任务原型 → 指标体系之间必须有清晰的追溯链。
* **执行计划与草稿对齐.** `EXECUTION_PLAN.md` 中的每个阶段目标必须可追溯到 `BENCHMARK_DRAFT.md` 中的对应章节。
* **Record all revisions.** 任何 phase 的重跑都必须在 `STAGE1_SUMMARY.md` 的 Refinement Log 中记录。

## Composing with Parent Pipeline

Stage 1 完成后，向父流程交出全部产出；父流程必须先等待用户选择，之后才能推进后续 stage：

```text
/benchmark-stage1-draft "$ARGUMENTS"
→ /benchmark-stage2-data-collect
→ /benchmark-stage3-data-clean
→ /benchmark-stage4-build
→ /benchmark-stage5-eval
```

Or invoke `/benchmark-pipeline` for the full end-to-end benchmark flow.
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
