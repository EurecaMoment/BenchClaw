---
name: benchmark-evalset-prototype-gen
description: "Stage 1 Phase 5：评测集原型与模板草稿生成。基于本次 benchmark 的用户意图、能力维度、数据源映射和调研结论，为每个能力维度设计评测任务原型、指标草案和模板初稿；必须显式写入附属模板草稿目录，严禁抄袭、翻译抄袭或轻改已有模板。"
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

# Benchmark Eval-Set Prototype Generation

面向：*$ARGUMENTS*

本 skill 是 Stage 1 Phase 5 的原子模块，只负责生成评测集原型、指标草案和模板初稿。它不生成最终评测集数据，不实例化具体题目，不运行模型评测，也不替代 Stage 4 的正式模板审查与评测集合成。

## Workspace 边界

- 只能读写当前 `WORKSPACE_ROOT = ~/bench_workspace/workspace{i}` 下的 `stage1/` 目录。
- 可选只读查看 `/home/maqiang/benchclaw/templates` 或 `~/benchclaw/templates/` 作为私有结构参考，但这些已有模板不是本次模板制造依据，不能在任何输出内容中显式提及、引用、命名或声明来源。
- 不得读取其它 workspace 的模板、草稿或评测集产物，除非用户明确指定。

## 输入

必须读取：

- `stage1/IDEA_TARGET.md`
- `stage1/CAPABILITY_SCOPE.md`
- `stage1/DATA_SOURCE_MAPPING.md`

可选读取：

- `stage1/LITERATURE_REVIEW.md`
- `stage1/SIMULATOR_MAPPING.md`
- `stage1/DATASET_MAPPING.md`
- `stage1/REALDATA_MAPPING.md`
- `/home/maqiang/benchclaw/templates`（只读、私有参考）
- `~/benchclaw/templates/`

若任一必需输入缺失，必须停止并报告缺失路径，不得凭空生成模板初稿。

## 核心要求：模板初稿必须由本次分析合成

本 phase 生成的模板初稿必须由以下本次上下文推导：

- 用户原始意图和 `IDEA_TARGET.md` 中的 benchmark 目标。
- `CAPABILITY_SCOPE.md` 中的能力维度、子能力、边界和非目标。
- `DATA_SOURCE_MAPPING.md` 中每个能力维度对应的 `simulator`、`existing_dataset`、`real_data` 数据源。
- `LITERATURE_REVIEW.md` 中已有 benchmark 的局限、可借鉴设计和本 benchmark 的差异化定位。

模板草稿不得是通用模板拼贴，也不得照搬 `/home/maqiang/benchclaw/templates` 或 `~/benchclaw/templates/`。这些已有模板只能作为私有参考，用于理解一般组织方式、命名习惯、质量检查思路和章节结构；它们不是模板制造依据，也不能作为 lineage、adaptation、reference、source 或 provenance 写入任何产物。最终模板初稿的任务目标、输入输出槽位、GT 需求、指标草案和质量约束必须只从本次用户意图、能力维度划分、论文调研分析和数据源映射中重新推导。

## 已有模板私有参考规则

允许只读查看 `/home/maqiang/benchclaw/templates` 或 `~/benchclaw/templates/`，但必须遵守：

- 这些模板只能作为私有参考，不是本次模板生成依据。
- 任何输出文件中都不得出现已有模板路径、文件名、模板名、模板 ID、来源说明、重组说明、改编说明或“来自/参考/借鉴某模板”的表达。
- 不得写“由哪些模板重组得到”“参考了哪些路径”“借鉴了哪个模板结构”“改写自某模板”等内容。
- 产物中的 lineage 只能追溯到 `IDEA_TARGET.md`、`CAPABILITY_SCOPE.md`、`DATA_SOURCE_MAPPING.md` 和 `LITERATURE_REVIEW.md`。
- 若需要说明非抄袭，只能说明模板是从本次 benchmark 目标、能力维度、数据映射和论文调研重新推导，不得披露私有参考模板信息。

## 禁止抄袭规则

严禁以下行为：

- 复制、翻译复制或轻微改写参考模板正文。
- 复用参考模板的字段组合、任务结构、任务顺序、示例表达或评分描述。
- 只替换能力维度名称，但保留参考模板的任务逻辑。
- 把 `/home/maqiang/benchclaw/templates` 或 `~/benchclaw/templates/` 中的模板当作本次模板初稿直接写入。
- 在任何输出中显式说明模板来自已有模板、由已有模板重组、参考了某路径、改写自某模板或受某具体模板启发。
- 没有写明本模板如何从本次能力维度和数据源映射推导而来。

每个模板草稿必须包含 `non_copy_declaration`，说明：

- 本模板为本 benchmark 做了哪些重新推导。
- 为什么它不是对参考模板的照抄、翻译或轻改。
- 本模板的依据只来自用户意图、能力维度、数据源映射和论文调研分析。
- 不得列出、暗示或描述任何已有模板路径、名称、来源或重组关系。

## 输出目录

本 phase 必须输出主文档和附属模板草稿目录：

```text
stage1/
  EVALSET_PROTOTYPE.md
  evalset_template_drafts/
    TEMPLATE_DRAFT_INDEX.md
    TEMPLATE_DRAFT_LINEAGE.md
    ANTI_COPY_DECLARATION.md
    {capability_dimension_slug}/
      {template_id}.yaml
      {template_id}.md
```

`evalset_template_drafts/` 是本阶段的必需附属目录。它用于显式保存各类模板初稿，供 Stage2 模板细化和 Stage4 评测集模板发布审查使用。

## 执行流程

1. 读取 `IDEA_TARGET.md`，提取用户意图、评测目标、目标边界和非目标。
2. 读取 `CAPABILITY_SCOPE.md`，列出所有能力维度和子能力。
3. 读取 `DATA_SOURCE_MAPPING.md`，确定每个能力维度可用的数据源类型、source_name、GT/标注可用性和覆盖缺口。
4. 若读取 `LITERATURE_REVIEW.md`，可以提取论文调研中的设计约束、已有 benchmark 局限和差异化定位。若只读查看 `/home/maqiang/benchclaw/templates` 或 `~/benchclaw/templates/`，只能作为私有结构参考，不得复制内容，不得记录参考路径，不得在产物中披露模板来源或重组关系。
5. 为每个能力维度设计 1-3 个任务原型，每个原型必须包含：
   - instruction template
   - input spec
   - expected output spec
   - GT / answer source
   - data source binding
   - difficulty levels
   - capability rationale
   - metric sketch
   - quality constraints
   - non-copy declaration
6. 为每个任务原型写入一个 `.yaml` 和一个 `.md` 模板草稿文件。
7. 写入 `EVALSET_PROTOTYPE.md`，总结所有任务原型、指标体系、模板草稿索引和非抄袭说明。
8. 校验每个能力维度至少有一个任务原型；若无法设计，必须记录 blocking gap。

## 模板草稿 YAML 格式

每个 `evalset_template_drafts/{capability_dimension_slug}/{template_id}.yaml` 必须包含：

```yaml
template_id:
template_name:
capability_dimension:
sub_capability:
benchmark_goal_ref:
source_bindings:
  - source_type:
    source_name:
    required_fields:
    gt_or_annotation_fields:
instruction_template:
input_spec:
expected_output_spec:
ground_truth_spec:
metric_sketch:
  primary_metric:
  auxiliary_metrics: []
difficulty_levels:
  easy:
  medium:
  hard:
quality_constraints:
  requires_observation_to_answer: true
  leakage_risks: []
  shortcut_resistance_notes:
  required_observation_files: []
stage4_template_review_seed:
  user_intent_fit:
  discrimination_power:
  shortcut_resistance:
  capability_alignment:
lineage:
  idea_target_ref:
  capability_scope_ref:
  data_source_mapping_ref:
  literature_review_ref:
non_copy_declaration:
  synthesis_basis:
    user_intent:
    capability_dimension:
    data_source_mapping:
    literature_analysis:
  external_template_source_disclosure: forbidden
  benchmark_specific_rederivation:
  why_not_copy:
```

## 模板草稿 Markdown 格式

每个 `{template_id}.md` 必须包含：

```markdown
# Template Draft: {template_id}

## Capability Target

## Benchmark-Specific Design Rationale

## Task Instruction Draft

## Input And Output Specification

## Data Source Binding

## GT / Answer Source

## Difficulty Design

## Metric Sketch

## Quality And Shortcut-Resistance Notes

## Non-Copy Declaration
```

## EVALSET_PROTOTYPE.md 格式

`EVALSET_PROTOTYPE.md` 必须包含：

```markdown
# Eval-Set Prototype

## Task Prototype Overview

## Capability-To-Template Draft Map
| Capability Dimension | Template Drafts | Source Types | Metric Sketch | Gaps |
|----------------------|-----------------|--------------|---------------|------|

## Task Prototypes

### Dimension: [维度名称]

#### Task Prototype 1: [任务名称]
- **Template draft files**: [yaml path], [md path]
- **Instruction template**: [...]
- **Input spec**: [...]
- **Expected output spec**: [...]
- **Data source**: [...]
- **GT / answer source**: [...]
- **Difficulty levels**: [...]
- **Capability rationale**: [...]
- **Metric sketch**: [...]
- **Quality constraints**: [...]
- **Benchmark-specific synthesis basis**: [...]
- **Non-copy declaration**: [...]

## Metric System

### Dimension-Level Metrics
| Dimension | Metric | Computation | Range | Required GT |
|-----------|--------|-------------|-------|-------------|

### Aggregate Metrics

### Diagnostic Metrics

## Template Draft Directory
| Template ID | YAML | Markdown | Capability Dimension | Source Binding |
|-------------|------|----------|----------------------|----------------|

## Template Synthesis Basis

## Anti-Copy Self-Check
| Check | Result | Evidence |
|-------|--------|----------|
```

## TEMPLATE_DRAFT_INDEX.md 格式

```markdown
# Template Draft Index

| Template ID | Capability Dimension | YAML Path | Markdown Path | Source Types | Status |
|-------------|----------------------|-----------|---------------|--------------|--------|
```

## TEMPLATE_DRAFT_LINEAGE.md 格式

```markdown
# Template Draft Lineage

| Template ID | Derived From Capability | Data Source Evidence | Literature Analysis Basis | Benchmark-Specific Redesign |
|-------------|-------------------------|----------------------|---------------------------|-----------------------------|
```

## ANTI_COPY_DECLARATION.md 格式

```markdown
# Anti-Copy Declaration

## Generation Basis Policy

All declarations must state only the run-specific basis: user intent, capability analysis, data-source mapping and literature-survey analysis. Do not name, cite, disclose, list as lineage, or describe any private reference template as the source of a generated template draft.

## Per-Template Declarations
| Template ID | User Intent Basis | Capability / Literature Basis | Data Source Basis | Benchmark-Specific Re-Derivation | Copy Risk Verdict |
|-------------|-------------------|-------------------------------|-------------------|--------------------------------|-------------------|

## Final Statement
All template drafts are benchmark-specific initial drafts synthesized only from this run's user intent, capability analysis, data-source mapping and literature-survey analysis. They are not copied, translated, lightly rewritten, recombined from, or attributed to external templates.
```

## 完成标准

- `stage1/EVALSET_PROTOTYPE.md` 存在且非空。
- `stage1/evalset_template_drafts/` 存在。
- 每个能力维度至少有一个模板草稿，或有明确 blocking gap。
- 每个模板草稿同时有 `.yaml` 和 `.md` 文件。
- 每个模板草稿都包含 `non_copy_declaration`。
- `TEMPLATE_DRAFT_INDEX.md`、`TEMPLATE_DRAFT_LINEAGE.md`、`ANTI_COPY_DECLARATION.md` 均存在。
- 所有模板草稿都能追溯到 `IDEA_TARGET.md`、`CAPABILITY_SCOPE.md`、`DATA_SOURCE_MAPPING.md`。
- 若私有查看 `/home/maqiang/benchclaw/templates` 或 `~/benchclaw/templates/`，不得在任何产物中写明参考路径、模板名称、借鉴点或重组关系；只能写本次用户意图、能力维度、数据源映射和论文调研如何支撑模板重新推导。

## 规则

- 不生成最终评测集数据，不实例化具体题目。
- 不修改 `CAPABILITY_SCOPE.md` 或 `DATA_SOURCE_MAPPING.md`。
- 不生成 Stage2、Stage3、Stage4 产物。
- 不抄袭、翻译抄袭、轻改或拼贴参考模板。
- 指标草案必须足够具体，不能只写“合理性评分”“人工评估”等无法自动化的描述。
- 若某能力维度因为数据源缺失无法设计模板，必须在 `EVALSET_PROTOTYPE.md` 和 `TEMPLATE_DRAFT_INDEX.md` 中标记 `BLOCKED`。

## Downstream Handoff

- `benchmark-draft-gen` 读取 `EVALSET_PROTOTYPE.md` 和 `evalset_template_drafts/`，写入 benchmark 草稿中的评测集设计章节。
- `benchmark-execution-plan-gen` 读取模板草稿目录，规划 Stage2-Stage4 的模板细化、数据清洗和评测集合成工作。
- Stage4 的 `/benchmark-evalset-plan-route` 可读取 `evalset_template_drafts/` 作为模板候选来源，但仍必须重新执行模板 fitness review。
