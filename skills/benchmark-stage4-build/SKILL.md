---
name: benchmark-stage4-build
description: "Stage 4 子流程：评测集生成与指标确立。编排benchmark-evalset-generate ->benchmark-metric-establish ->benchmark-validate-stage4 ->benchmark-unit-test-stage4，基 Stage 3 final/STAGE4_INPUT_MANIFEST.jsonl、final/cleaned_data 与清洗质量报告批量合成评测集、建立指标体系并联调验证。本阶段仅负责评测集与指标构建，不负责数据采集、Data-Juicer 清洗或模型评测执行。Use when user says '开始stage4'生成评测集评测集与指标'evalset build stage'build benchmark dataset'."
argument-hint: [stage3-dir]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, WebSearch, WebFetch, Skill
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

# Benchmark Stage 4: 评测集生成+ 指标确立

Orchestrate the complete Stage 4 evalset-build and metric-establishment workflow for: **$ARGUMENTS**

This skill is an **orchestrator only**.
It must **not** re-implement, expand, or substitute the internal logic of any sub-skill.

---

## Critical Hotfix: Do Not Advance With Documentation-Only Metrics

The Stage 4 orchestrator must treat an empty or documentation-only
`METRIC_LIBRARY/` as a hard failure in Phase 2, Phase 3, and Phase 4. A Stage 4
run is not complete unless it can automatically score model outputs.

After `/benchmark-metric-establish`, verify before checkpointing:

- `METRIC_LIBRARY/metrics/` contains executable metric files for every declared
  metric in `METRIC_SPEC.md`, `CAPABILITY_METRIC_MAP.md`, and template
  `downstream_metrics`.
- `METRIC_LIBRARY/aggregators/` contains executable dimension and overall
  aggregators.
- `METRIC_LIBRARY/tests/` contains tests, and the tests have been run.
- `METRIC_LIBRARY/interfaces.py` and `METRIC_LIBRARY/README.md` exist.
- `tools/evaluate_evalset.py` exists and has passed a smoke run.

If any item is missing, stop and rerun Phase 2.3. Do not proceed to validation,
do not write `VALIDATION_REPORT.md` as PASS, and do not ask the user to choose a
future repair option while presenting Stage 4 as complete.

## Critical Hotfix: Do Not Advance With Ungrounded Eval Questions

The Stage 4 orchestrator must treat visually/spatially ungrounded questions as a
hard Phase 1 failure. A sample is ungrounded if it can be answered from
instruction text, options, file names, paths, public metadata, or language/world
priors without reading the declared observation payload.

After `/benchmark-evalset-generate`, verify before checkpointing:

- Each template has `quality_constraints`.
- Each official sample has `grounding_check.verdict=PASS`.
- Non-`text_only_allowed` tasks have required observation files.
- GT strings/aliases and answer-bearing metadata do not appear in visible input
  text, options, file names, paths, or public metadata.
- `EVALSET_SYNTHESIS_RULES.md` documents observation-dependence, leakage checks,
  text-only baseline checks, and quarantine/exclusion behavior.

If any item is missing, stop and rerun Phase 1.1-1.3. Do not proceed to metric
establishment with a benchmark whose questions do not require the provided
image/observation.

## Overview

This skill chains Stage 4 sub-skills into a single automated pipeline:

```text
STAGE1 + STAGE2 templates + STAGE3 cleaned artifacts
->/benchmark-evalset-generate
->/benchmark-metric-establish
->/benchmark-validate-stage4
->/benchmark-unit-test-stage4
(评测集合->  (指标体系确立)  (联调验证)  (Stage 4 单元测试)
```

Each phase builds on the previous one's output。Phase 之间严格顺序依赖，不可跳过或乱序
## Workspace

所有产出写入当前workspace ->`~/bench_workspace/workspace{i}/stage4/` 子目录：

```
~/bench_workspace/workspace{i}/stage4/
```

其中 `{i}` 由父流程或用户指定。若未指定，默认使用 `workspace1`
## Constants

* **AUTO_PROCEED = false** ->关卡处是否自动继续。默认等待用户确认* **HUMAN_CHECKPOINT = true** ->`true` 时，关键关卡必须暂停并展示阶段结果，等待用户确认* **COMPACT = false** ->`true` 时，额外生成 `STAGE4_COMPACT.md` 供下skill 或长会话恢复使用* **MAX_REFINEMENT_ROUNDS = 2** ->Stage 4 内部允许的轻量重整轮数上限* **WRITE_STAGE_LOG = true** ->每个 phase 完成后将结论追加写入 `STAGE4_SUMMARY.md` 的滚动记录* **TIMEOUT = 0** ->用户无响应超时秒数。仅`AUTO_PROCEED = false` ->`TIMEOUT > 5000` 时自动继续* **DRY_RUN_SAMPLE_SIZE = 50** ->Phase 3 联调验证时抽样的评测样本数量* **METRIC_REPRODUCIBILITY_RUNS = 3** ->指标可复现性验证的重复运行次数据* **COVERAGE_THRESHOLD = 1.0** ->能力维度到指标的映射覆盖率下限；低于此值则 Phase 3 不可 pass.0 = 全覆盖，允许显式豁免）
> 💡 Override by telling the skill, e.g.
> `/benchmark-stage4-build "$STAGE3_DIR" ->DRY_RUN_SAMPLE_SIZE: 100, COMPACT: true`

## Pipeline

### Phase 0: Load Context from Stage 1 + Stage 2 + Stage 3

在启动任何后续phase 之前
1. 读取 `~/bench_workspace/workspace{i}/stage2/` 目录，确认以下模板与采集上下文产出存在：
   * `~/bench_workspace/workspace{i}/stage2/SIM_CAPABILITY_SURVEY.md`
   * `~/bench_workspace/workspace{i}/stage2/COLLECTION_GUIDANCE_PLAN.md`
   * `~/bench_workspace/workspace{i}/stage2/TEMPLATE_REFINEMENT_REPORT.md`
   * `~/bench_workspace/workspace{i}/stage2/templates/{sim_name}_EVAL_TEMPLATE.yaml`
2. 读取 `~/bench_workspace/workspace{i}/stage3/` 目录，确认以下清洗与合并产出全部存在：
   * `~/bench_workspace/workspace{i}/stage3/DATA_CLEANING_PLAN.md`
   * `~/bench_workspace/workspace{i}/stage3/source_work/` -> Stage 3 三条线分流中间产物
   * `~/bench_workspace/workspace{i}/stage3/final/STAGE4_INPUT_MANIFEST.jsonl` -> Stage 4 权威输入索引
   * `~/bench_workspace/workspace{i}/stage3/final/CLEANED_DATA_SCHEMA.md`
   * `~/bench_workspace/workspace{i}/stage3/final/cleaned_data/`
   * `~/bench_workspace/workspace{i}/stage3/final/CLEANING_LINEAGE.jsonl`
   * `~/bench_workspace/workspace{i}/stage3/CLEANING_QUALITY_REPORT.md` ->verdict 必须PASS，或 NEEDS_REVIEW 且有显式 waiver
3. 读取 `~/bench_workspace/workspace{i}/stage1/` 目录，确认以下前置产出存在：
   * `~/bench_workspace/workspace{i}/stage1/BENCHMARK_DRAFT.md`
   * `~/bench_workspace/workspace{i}/stage1/EVALSET_PROTOTYPE.md`
   * `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md`
4. 若任一前置产出缺失，报错终止并提示用户先完成对stage；若 Stage 3 清洗验证失败，提示用户先重跑 `/benchmark-stage3-data-clean`5. 从前置产出中提取stage 需要的共享上下文：
   * ->`BENCHMARK_DRAFT.md` 提取任务目标、能力边界、场景覆盖约->   * ->`EVALSET_PROTOTYPE.md` 提取评测集模板草稿与指标设计草稿，作为本 stage 的可追溯起点
   * ->`CAPABILITY_SCOPE.md` 提取能力维度列表及操作性定义   * ->`TEMPLATE_REFINEMENT_REPORT.md` 提取修整后的模板字段与格式约->   * ->`templates/*.yaml` 提取各仿真器的最终模板   * ->`DATA_SCHEMA.md` 提取数据存储结构GT 标注格式
   * ->`CLEANING_QUALITY_REPORT.md` 提取清洗质量状况、保留率、GT 保真结论与已知缺->   * ->`final/STAGE4_INPUT_MANIFEST.jsonl` 与 `final/cleaned_data/` 确认实际可用数据规模和 Stage4 ready 状态

6. 建立追溯链记录：`EVALSET_PROTOTYPE.md` ->`TEMPLATE_REFINEMENT_REPORT.md` ->`DATA_CLEANING_PLAN.md` / `final/CLEANING_LINEAGE.jsonl` / `final/STAGE4_INPUT_MANIFEST.jsonl` ->stage 产出，确保每一步变更可回溯

---

### Phase 1: Evalset Generation ->评测集合
Invoke:

```text
/benchmark-evalset-generate "$ARGUMENTS"
```

**输入* `~/bench_workspace/workspace{i}/stage1/BENCHMARK_DRAFT.md` + `~/bench_workspace/workspace{i}/stage1/EVALSET_PROTOTYPE.md` + `~/bench_workspace/workspace{i}/stage2/templates/*.yaml` + `~/bench_workspace/workspace{i}/stage3/final/CLEANED_DATA_SCHEMA.md` + `~/bench_workspace/workspace{i}/stage3/final/STAGE4_INPUT_MANIFEST.jsonl` + `~/bench_workspace/workspace{i}/stage3/final/cleaned_data/` + `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md`

**执行内容*

* **1.1 构建任务专属模板*
  * ->`EVALSET_PROTOTYPE.md` 中的任务原型为起点，结合 Stage 2 修整后的仿真器模板与 Stage 3 cleaned data schema，为每个能力维度 × 仿真器组合生成最终评测任务模板  * 每个模板定义：任务指令格式、输入字段列表（从采集数据中取哪些字段）、期望输出格式、GT 参考答案来源字段  * 模板须记录其`EVALSET_PROTOTYPE.md` ->`TEMPLATE_REFINEMENT_REPORT.md` 到本模板的变更链
  * 务必检查模板的合理性、可评测性、区分度，确保其能有效区分不同能力水平的模型表现
  * 输出`EVALSET_TEMPLATE_LIBRARY/`

* **1.2 制定评测集合成规*
  * 定义从采集数据到评测样本的转换规则：
    * 采样策略：从每个场景/帧中如何抽取评测样本（全部vs 按条件筛vs 分层抽样->    * 难度分级规则：基于场景复杂度（物体数量、遮挡率、光照条件等）划分难度等->    * 跨仿真器平衡策略：确保各仿真器的样本量与能力维度覆盖比例合理
    * 样本去重与质量过滤规则：排除异常帧、低质量 GT、重复场->  * 合成规则必须保证可复现：给定相同采集数据 + 相同规则 = 相同评测集  * 输出`EVALSET_SYNTHESIS_RULES.md`

* **1.3 批量合成评测集*
  * 按合成规则遍`collected_data/`，逐样本生成评测数据  * 每个评测样本包含->    * 输入数据（提供给被评测系统的信息->    * GT 参考答案（用于评分的标准答案）
    * 元数据（来源仿真器、场ID、帧 ID、能力维度标签、难度等级）
  * 按统一 schema 组织存储
  * 输出`EVALSET_DATASET/`

* **1.4 定义评测集schema**
  * 将评测集的目录结构、文件格式、字段定义、元数据规范写入文档
  * schema 必须与下游指标算法的输入契约对齐
  * 输出`EVALSET_SCHEMA.md`

**Expected output:**

* `~/bench_workspace/workspace{i}/stage4/EVALSET_TEMPLATE_LIBRARY/` ->任务专属模板* `~/bench_workspace/workspace{i}/stage4/EVALSET_SYNTHESIS_RULES.md` ->合成规则
* `~/bench_workspace/workspace{i}/stage4/EVALSET_DATASET/` ->合成后的评测集* `~/bench_workspace/workspace{i}/stage4/EVALSET_SCHEMA.md` ->评测集schema

`EVALSET_TEMPLATE_LIBRARY/` 目录结构
```
EVALSET_TEMPLATE_LIBRARY/
├── {dimension_1}/
->  ├── {sim_a}_task_template.yaml
->  └── {sim_b}_task_template.yaml
├── {dimension_2}/
->  └── {sim_a}_task_template.yaml
└── TEMPLATE_LINEAGE.md          # 模板变更追溯```

`EVALSET_SYNTHESIS_RULES.md` 包含
```markdown
# Evalset Synthesis Rules

## Sampling Strategy
[从采集数据到评测样本的抽取方式]

## Difficulty Grading
| Grade | Criteria | Expected Proportion |
|-------|----------|-------------------|
| easy  | ...      | ...               |
| medium| ...      | ...               |
| hard  | ...      | ...               |

## Cross-Simulator Balancing
[各仿真器样本量分配策略]

## Quality Filtering
[排除条件列表]

## Deduplication
[去重规则]

## Reproducibility Guarantee
[随机种子、排序规则等确保可复现的机制]
```

`EVALSET_DATASET/` 目录结构
```
EVALSET_DATASET/
├── {dimension_1}/
->  ├── sample_{id}/
->  ->  ├── input/           # 提供给被评测系统的数据->  ->  ├── gt/              # GT 参考答->  ->  └── metadata.json    # 元数据->  └── ...
├── {dimension_2}/
->  └── ...
├── manifest.json            # 全量样本索引
└── statistics.json          # 统计摘要
```

`EVALSET_SCHEMA.md` 包含
```markdown
# Evalset Schema

## Directory Structure
[目录结构说明]

## Sample Schema
### Input Fields
| Field | Type | Format | Description | Source |
|-------|------|--------|-------------|--------|
| ...   | ...  | ...    | ...         | ~/bench_workspace/workspace{i}/stage2/{sim}/{field} |

### GT Fields
| Field | Type | Format | Description | Source |
|-------|------|--------|-------------|--------|
| ...   | ...  | ...    | ...         | ~/bench_workspace/workspace{i}/stage2/{sim}/{field} |

### Metadata Fields
| Field | Type | Description |
|-------|------|-------------|
| source_simulator | string | ... |
| scene_id | string | ... |
| frame_id | string | ... |
| dimension | string | 能力维度标签 |
| difficulty | enum | easy/medium/hard |

## Manifest Schema
[manifest.json 字段定义]

## Downstream Contract
[指标算法期望的输入格式，与上schema 的对齐说明]
```

**🚦 Checkpoint:**

```text
📦 Evalset generation complete:
- Template library: [模板数量] templates across [维度数] dimensions
- Synthesis rules: defined (reproducible: yes)
- Evalset scale: [总样本数] samples ([各难度分布])
- Dimension coverage: [各维度样本数]
- Schema: defined, downstream contract aligned
- Question grounding gate: templates constrained [yes/no], official samples grounded [yes/no], leakage/text-only baseline checks [PASS/FAIL]

Proceed to metric establishment?
```

* **User approves** ->Phase 2
* **User requests synthesis rule adjustments** ->修改规则并重新合成，重跑 Phase 1.2-1.4
* **User认为模板需修改** ->修订模板库，重跑 Phase 1.1 ->* **User认为采集数据不足** ->回退 Stage 2 补采

---

### Phase 2: Metric Establishment ->指标体系确立

Invoke:

```text
/benchmark-metric-establish "$ARGUMENTS"
```

**输入* `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md` + `~/bench_workspace/workspace{i}/stage1/EVALSET_PROTOTYPE.md` + `EVALSET_SCHEMA.md` + `EVALSET_DATASET/`（抽样）

**执行内容*

* **2.1 建立能力维度到指标的映射**
  * ->`EVALSET_PROTOTYPE.md` 中的指标设计草稿为起点，结合实际评测集schema 落地
  * 为每个能力维度确定：
    * 主指标（该维度的核心评分->    * 辅助指标（补充诊断信息）
    * 指标计算所需的输入字段（必须存在`EVALSET_SCHEMA.md` ->GT Fields ->Input Fields 中）
  * 定义跨维度聚合指标（overall score 的计算方式）
  * 记录`EVALSET_PROTOTYPE.md` 草稿到最终指标的变更理由
  * 输出`CAPABILITY_METRIC_MAP.md`

* **2.2 制定指标规范与打分规*
  * 对每个指标编写规范：
    * 指标名称、数学定义、值域、方向（越高越好 / 越低越好->    * 输入类型（预测值格式、GT 格式->    * 边界情况处理（空预测、格式错误、超出范围）
    * 置信区间或统计显著性计算方式（若适用->  * 对每个指标定义打分规则：
    * 原始分数计算公式
    * 归一化方式（若有->    * 聚合方式（样本级 ->维度overall->    * 打分粒度（连->/ 离散等级 / 二值）
  * 输出`METRIC_SPEC.md` + `SCORING_RULES.md`

* **2.3 实现指标算法*
  * 为每个指标实现可执行的计算代->  * 代码要求->    * 输入接口`EVALSET_SCHEMA.md` 的字段名和格式严格对->    * 输出接口`SCORING_RULES.md` 的聚合逻辑一->    * 包含单元测试（覆盖正常用+ 边界情况->    * 包含 docstring 引用 `METRIC_SPEC.md` 中的对应指标定义
  * 实现聚合器：维度级聚+ overall 聚合
  * 输出`METRIC_LIBRARY/`

**Expected output:**

* `~/bench_workspace/workspace{i}/stage4/CAPABILITY_METRIC_MAP.md`
* `~/bench_workspace/workspace{i}/stage4/METRIC_SPEC.md`
* `~/bench_workspace/workspace{i}/stage4/SCORING_RULES.md`
* `~/bench_workspace/workspace{i}/stage4/METRIC_LIBRARY/`
* `~/bench_workspace/workspace{i}/stage4/tools/evaluate_evalset.py`

`CAPABILITY_METRIC_MAP.md` 包含
```markdown
# Capability-Metric Mapping

## Lineage
- Source draft: `~/bench_workspace/workspace{i}/stage1/EVALSET_PROTOTYPE.md` § Metric System
- Changes from draft: [变更摘要与理由]

## Per-Dimension Mapping
| Capability Dimension | Primary Metric | Auxiliary Metrics | Required Input Fields | Required GT Fields |
|---------------------|---------------|-------------------|----------------------|-------------------|
| ...                 | ...           | ...               | ...                  | ...               |

## Aggregate Metrics
| Metric | Aggregation Method | Component Dimensions | Weight/Formula |
|--------|-------------------|---------------------|---------------|
| overall_score | ... | all | ... |
| ...    | ...               | ...                 | ...           |

## Coverage Check
- Total dimensions: [N]
- Dimensions with primary metric: [N]
- Dimensions explicitly exempted: [列表及豁免理由]
- Coverage rate: [百分比] (threshold: COVERAGE_THRESHOLD)
```

`METRIC_SPEC.md` 包含
```markdown
# Metric Specification

## Metric: [metric_name]
- **Mathematical definition**: [公式]
- **Range**: [值域]
- **Direction**: higher-is-better / lower-is-better
- **Input**: prediction=[格式], gt=[格式]
- **Edge cases**:
  - Empty prediction: [处理方式]
  - Format error: [处理方式]
  - Out of range: [处理方式]
- **Statistical significance**: [计算方式，若适用]

## Metric: [metric_name]
...
```

`SCORING_RULES.md` 包含
```markdown
# Scoring Rules

## Sample-Level Scoring
| Metric | Raw Score Formula | Normalization | Granularity |
|--------|------------------|---------------|-------------|
| ...    | ...              | ...           | continuous/discrete/binary |

## Dimension-Level Aggregation
| Dimension | Aggregation Method | Weighting |
|-----------|-------------------|-----------|
| ...       | mean / median / ... | uniform / ... |

## Overall Aggregation
- Method: [加权平均 / 层次聚合 / ...]
- Dimension weights: [权重表或计算方式]
- Formula: [最终公式]

## Reporting Format
[输出结果的结构化格式定义]
```

`METRIC_LIBRARY/` 目录结构
```
METRIC_LIBRARY/
├── metrics/
->  ├── {metric_name}.py       # 单指标计算实际->  ├── {metric_name}.py
->  └── ...
├── aggregators/
->  ├── dimension_aggregator.py
->  └── overall_aggregator.py
├── tests/
->  ├── test_{metric_name}.py
->  └── ...
├── interfaces.py              # 输入输出接口定义
└── README.md
```

**🚦 Checkpoint:**

```text
📏 Metric establishment complete:
- Metrics defined: [数量] primary + [数量] auxiliary + [数量] aggregate
- Dimension coverage: [百分比] (threshold: [COVERAGE_THRESHOLD])
- Metric library: [代码文件数], unit tests: [通过/总数]
- Runtime gate: metrics non-empty [yes/no], aggregators non-empty [yes/no], tests executed [yes/no], evaluator smoke run [PASS/FAIL]
- Lineage from EVALSET_PROTOTYPE: tracked

Proceed to validation?
```

* **User approves** ->Phase 3
* **User requests metric adjustments** ->修订指标定义，重跑Phase 2（计MAX_REFINEMENT_ROUNDS* **User认为评测集schema 与指标不对齐** ->回退 Phase 1 调整 schema 后重跑Phase 2
* **单元测试未通过** ->修复实现后重跑Phase 2.3

---

### Phase 3: Validation ->联调验证

Invoke:

```text
/benchmark-validate-stage4 "$ARGUMENTS"
```

**输入* `EVALSET_DATASET/` + `EVALSET_SCHEMA.md` + `METRIC_SPEC.md` + `SCORING_RULES.md` + `METRIC_LIBRARY/` + `CAPABILITY_METRIC_MAP.md`

**执行内容*

* **3.1 输入输出契约验证**
  * ->`EVALSET_DATASET/` 中抽`DRY_RUN_SAMPLE_SIZE` 个样->  * 对每个样本验证：
    * 输入字段是否符合 `EVALSET_SCHEMA.md` 定义
    * GT 字段是否符合 `EVALSET_SCHEMA.md` 定义
    * 元数据字段是否完成  * 验证 `METRIC_LIBRARY/` 的接口定义与 `EVALSET_SCHEMA.md` 的字段名/格式是否严格对齐
  * 记录所有不一致项

* **3.2 评分链路 dry-run**
  * 对抽取的样本构造模拟预测结果（可使用随机预测、全零预测、GT 复制等策略）
  * 用模拟预+ GT 调用 `METRIC_LIBRARY/` 中每个指标的计算函数
  * 验证->    * 每个指标是否能正常计算并返回有效->    * 返回值是否在 `METRIC_SPEC.md` 定义的值域->    * 边界情况是否按规范处->  * 调用聚合器，验证维度级聚合和 overall 聚合逻辑

* **3.3 可复现性验证*
  * 对相同样+ 相同模拟预测重复运行 `METRIC_REPRODUCIBILITY_RUNS` ->  * 验证每次运行的输出是否完全一致（确定性指标）或在预期置信区间内（随机性指标）

* **3.4 覆盖完整性验证*
  * 验证每个能力维度是否`CAPABILITY_METRIC_MAP.md` 中有对应指标
  * 验证每个有指标的维度是否`EVALSET_DATASET/` 中有足够样本
  * 对未覆盖维度检查是否有显式豁免说明
  * 计算覆盖率，`COVERAGE_THRESHOLD` 比较

* **3.5 形成验证结论**
  * 汇总所有验证结果，给出 pass/fail 判定
  * pass 条件（必须全部满足）->    * 输入输出契约无不一致项
    * 所有指dry-run 成功且值域合法
    * 可复现性验证通过
    * 覆盖`COVERAGE_THRESHOLD`
  * ->fail，逐项列出阻塞项及建议修复 phase

**Expected output:**

* `~/bench_workspace/workspace{i}/stage4/VALIDATION_REPORT.md`
* `~/bench_workspace/workspace{i}/stage4/DRY_RUN_RESULTS.md`

`VALIDATION_REPORT.md` 包含
```markdown
# Validation Report

## Verdict: [PASS / FAIL]

## 1. Input-Output Contract Validation
- Samples checked: [DRY_RUN_SAMPLE_SIZE]
- Schema violations: [数量]
- Details: [逐项列出不一致]
- Status: PASS / FAIL

## 2. Scoring Pipeline Dry-Run
- Metrics tested: [数量]
- All metrics returned valid values: [yes/no]
- Value range violations: [数量]
- Edge case handling verified: [yes/no]
- Aggregation logic verified: [yes/no]
- Status: PASS / FAIL

## 3. Reproducibility
- Runs: [METRIC_REPRODUCIBILITY_RUNS]
- Deterministic metrics consistent: [yes/no]
- Stochastic metrics within CI: [yes/no/N/A]
- Status: PASS / FAIL

## 4. Coverage Completeness
- Dimensions with metrics: [N] / [total]
- Dimensions with sufficient samples: [N] / [total]
- Explicit exemptions: [列表]
- Coverage rate: [百分比]
- Threshold: [COVERAGE_THRESHOLD]
- Status: PASS / FAIL

## 5. Blocking Issues (if FAIL)
| Issue | Severity | Affected Component | Suggested Fix Phase |
|-------|----------|-------------------|-------------------|
| ...   | ...      | ...               | Phase {M}         |

## 6. Non-Blocking Warnings
[不影pass 但建议后续关注的问题]
```

`DRY_RUN_RESULTS.md` 包含
```markdown
# Dry-Run Results

## Test Configuration
- Sample size: [DRY_RUN_SAMPLE_SIZE]
- Prediction strategy: [random / zero / gt-copy / mixed]
- Reproducibility runs: [METRIC_REPRODUCIBILITY_RUNS]

## Per-Metric Results
| Metric | Status | Sample Output | Value Range Check | Edge Cases | Reproducible |
|--------|--------|--------------|-------------------|------------|-------------|
| ...    | PASS/FAIL | [示例值] | PASS/FAIL | PASS/FAIL | yes/no |

## Aggregation Results
| Level | Aggregator | Status | Sample Output |
|-------|-----------|--------|--------------|
| dimension | ... | PASS/FAIL | [示例值] |
| overall | ... | PASS/FAIL | [示例值] |

## Error Log
[dry-run 中出现的错误详情]
```

**🚦 Checkpoint:**

```text
Validation complete:
- Verdict: [PASS / FAIL]
- Contract check: [PASS/FAIL]
- Scoring dry-run: [PASS/FAIL]
- Reproducibility: [PASS/FAIL]
- Coverage: [百分比] ([PASS/FAIL])
- Blocking issues: [数量]

Proceed to final summary?
```

* **Verdict = PASS, User approves** ->Phase 4
* **Verdict = FAIL** ->根据 `VALIDATION_REPORT.md` 中的 Suggested Fix Phase 回退修复->  * 契约不一回退 Phase 1（调schema）或 Phase 2（调整指标接口）
  * 指标 dry-run 失败 ->回退 Phase 2.3（修复实现）
  * 可复现性失回退 Phase 2.3（排查非确定性来源）
  * 覆盖率不回退 Phase 2.1（补充指标映射）或回退 Phase 1（补充样本）

---

### Phase 4: Unit Test ->Stage 4 评测集与协议单元测试

Invoke:

```text
/benchmark-unit-test-stage4 "$STAGE4_DIR"
```

**输入* Stage 4 全部产物 + Stage 3 单元测试报告
**执行内容*

* 检查评测集、schema、metric library、打分规则、维度指标映射、dry-run 报告是否完整* 验证样本 manifest、输入字段、GT 字段、指标输入契约、聚合输出契约的一致性* 检查GT 泄露、指标不可复现、样本分布严重偏斜、维度覆盖缺口等阻塞问题* 给出 `PASS | FAIL | NEEDS_REVIEW` verdict；FAIL 时定位到 Stage 4 合成、指标或联调验证 phase，必要时回退 Stage 3
**Expected output:**

* `~/bench_workspace/workspace{i}/stage4/unit_tests/test_stage4_contract.py`
* `~/bench_workspace/workspace{i}/stage4/unit_tests/results.json`
* `~/bench_workspace/workspace{i}/stage4/STAGE4_UNIT_TEST_REPORT.md`

**🚦 Quality Gate:**

* `PASS` ->可以进入 Stage 5 灰度评测集* `NEEDS_REVIEW` ->用户确认 waiver 后才能进入Stage 5* `FAIL` ->不得进入 Stage 5；按报告中的 fix target 回退重跑
---

### Phase 4: Final Summary

Finalize `~/bench_workspace/workspace{i}/stage4/STAGE4_SUMMARY.md`
```markdown
# Stage4 Summary

**Benchmark Idea**: $ARGUMENTS
**Date**: [today]
**Pipeline**: evalset-generate ->metric-establish ->validate-stage4

## Executive Summary
[2-3 sentences: 评测集规模与结构、指标体系、验证结论、建议下一步]

## Phase Results

### Phase 1: Evalset Generation
- Output: `EVALSET_TEMPLATE_LIBRARY/` + `EVALSET_SYNTHESIS_RULES.md` + `EVALSET_DATASET/` + `EVALSET_SCHEMA.md`
- Summary: [摘要]

### Phase 2: Metric Establishment
- Output: `CAPABILITY_METRIC_MAP.md` + `METRIC_SPEC.md` + `SCORING_RULES.md` + `METRIC_LIBRARY/`
- Summary: [摘要]

### Phase 3: Validation
- Output: `VALIDATION_REPORT.md` + `DRY_RUN_RESULTS.md`
- Verdict: [PASS/FAIL]
- Summary: [摘要]

## Lineage Trace
- `~/bench_workspace/workspace{i}/stage1/EVALSET_PROTOTYPE.md` ->`~/bench_workspace/workspace{i}/stage2/TEMPLATE_REFINEMENT_REPORT.md` ->`~/bench_workspace/workspace{i}/stage4/EVALSET_TEMPLATE_LIBRARY/TEMPLATE_LINEAGE.md`
- `~/bench_workspace/workspace{i}/stage1/EVALSET_PROTOTYPE.md` § Metric System ->`~/bench_workspace/workspace{i}/stage4/CAPABILITY_METRIC_MAP.md` § Lineage

## Final Deliverables
- `EVALSET_TEMPLATE_LIBRARY/`
- `EVALSET_SYNTHESIS_RULES.md`
- `EVALSET_DATASET/`
- `EVALSET_SCHEMA.md`
- `METRIC_SPEC.md`
- `SCORING_RULES.md`
- `METRIC_LIBRARY/`
- `CAPABILITY_METRIC_MAP.md`
- `VALIDATION_REPORT.md`
- `DRY_RUN_RESULTS.md`
- `STAGE4_SUMMARY.md`

## Refinement Log
[记录所有phase 重跑的原因与变更摘要]

## Recommended Next Step
- [ ] Proceed to `/benchmark-stage5-eval`
- [ ] Or revise Stage 4 before continuing
```

---

### Phase 4.5: Write Compact Files (when COMPACT = true)

**Skip entirely if `COMPACT` is `false`.**

Write `~/bench_workspace/workspace{i}/stage4/STAGE4_COMPACT.md`
```markdown
# Stage4 Compact Summary

## Evalset
- Scale: [总样本数] samples across [维度数] dimensions
- Difficulty distribution: easy [N] / medium [N] / hard [N]

## Metrics
- Primary: [数量]
- Auxiliary: [数量]
- Aggregate: [数量]
- Coverage: [百分比]

## Validation
- Verdict: [PASS/FAIL]
- Blocking issues: [数量]

## Current Status
- Evalset: ready
- Metrics: ready
- Validation: [PASS/FAIL]

## Next Step
/benchmark-stage5-eval
```

---

## 🚦 Gate 4 ->Evalset & Metric Checkpoint

After Stage 4 全部完成，展示最gate
```text
📋 Stage 4 complete. Evalset + metric summary:

1. Evalset scale: [样本量] samples, [维度覆盖] dimensions, difficulty: [分布]
2. Metric coverage: [能力维度到指标映射覆盖率]
3. Validation result: [PASS/FAIL + 关键统计]
4. Main risks: [schema 不一->/ 指标稳定义/ 样本质量]
5. Recommended next action: proceed to evaluation

Shall I proceed to Stage 5?
```

**If `AUTO_PROCEED = false`:**

* Always wait for user confirmation before Stage 5, except when `TIMEOUT > 5000s`

**If `AUTO_PROCEED = true`:**

* Continue automatically unless `VALIDATION_REPORT.md` verdict is FAIL

## 重新执行 Stage 4 的触发条件
| 问题 | 回退目标 |
|------|---------|
| `VALIDATION_REPORT.md` 不存在或 verdict 不是 PASS | Phase 3（重新验证）或按阻塞项回退 |
| 评测集schema 与指标输入契约不一| Phase 1（调schema-> Phase 2（调整接口） |
| 指标实现无法完成 dry-run | Phase 2.3（修复实现） |
| 聚合结果不可复现 | Phase 2.3（排查非确定性来源） |
| 能力维度存在未覆盖且无明确豁免说| Phase 2.1（补充映射）或回退 Stage 1（调整维度） |
| 评测集样本量不足以支撑指标统计显著| Phase 1（调整合成规则）或回退 Stage 2（补采） |
| 模板追溯链断裂（无法追溯EVALSET_PROTOTYPE.md| Phase 1.1（补采TEMPLATE_LINEAGE.md|

`MAX_REFINEMENT_ROUNDS` 耗尽时，将当前产出标记为 `[NEEDS_REVIEW]` 并继续至 Gate 4，由用户决定是否进入 Stage 5 或先修复
## Key Rules

* **Questions must be observation-grounded.** Image/video/spatial tasks must require the declared observation payload; text-only-solvable samples cannot enter the official evalset.
* **No answer leakage.** GT strings, aliases, scene labels, coordinates, counts, directions, answer-bearing metadata, and path/file-name hints must not appear in model-visible inputs.
* **Grounding metadata required.** Templates must include `quality_constraints`, and samples must include `grounding_check.verdict=PASS`.
* **No empty scorer library.** `METRIC_LIBRARY/metrics/`, `METRIC_LIBRARY/aggregators/`, and `METRIC_LIBRARY/tests/` must be non-empty and executable before Stage 4 can pass.
* **Declared metrics must resolve.** Every metric named in `METRIC_SPEC.md`, `CAPABILITY_METRIC_MAP.md`, or template `downstream_metrics` must have matching code or an explicit Phase 2 FAIL.
* **Runner required.** Stage 4 must include `tools/evaluate_evalset.py` so Stage 5 can score outputs without reimplementing metrics.
* **Large file handling**: ->Write tool 因文件过大失败，立即改用 Bash（`cat << 'EOF' > file`）分块写入。不问用户* **Do not skip phases.** 3 ->phase 严格顺序执行* **Phase 之间必须 checkpoint.** 每个 phase 完成后展示摘要，等待确认（`HUMAN_CHECKPOINT = true` 时）* **追溯链不可断.** 评测集模板和指标设计必须可追溯到 `~/bench_workspace/workspace{i}/stage1/EVALSET_PROTOTYPE.md`，每一步变更必须记录理由。Stage 4 不是从零设计，而是Stage 1 草稿 + Stage 2 修整结果 + Stage 3 清洗结果上做可追溯的继承与落地* **Schema 先于指标.** 评测集schema 确定后才能开始指标实现，因为指标的输入接口取决于 schema* **指标必须可执** `METRIC_LIBRARY/` 中的代码必须能实际运行并通过单元测试，不可只是伪代码或规范文档* **验证不可跳过.** Phase 3 ->pass/fail 判定义Stage 4 的硬性出口条件。verdict = FAIL 时不可直接进入Stage 5* **Record all revisions.** 任何 phase 的重跑都必须`STAGE4_SUMMARY.md` ->Refinement Log 中记录
## Composing with Parent Pipeline

Stage 4 完成后，向父流程交出全部产出，由父流程推进后续stage
```text
/benchmark-stage1-draft "$ARGUMENTS"
->/benchmark-stage2-data-collect "$STAGE1_DIR"
->/benchmark-stage3-data-clean "$STAGE2_DIR"
->/benchmark-stage4-build "$STAGE3_DIR"
->/benchmark-stage5-eval
parent pipeline final report
```

Or invoke `/benchmark-pipeline` for the full end-to-end benchmark flow.
