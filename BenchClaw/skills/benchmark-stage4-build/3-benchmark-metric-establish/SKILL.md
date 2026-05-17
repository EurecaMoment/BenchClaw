---
name: benchmark-metric-establish
description: "Atomic module: stage4 Phase 3 指标体系确立模块。只负责建立能力维度到指标的映射、制定指标规范与打分规则、实现可执行的指标算法库（含单元测试），不负责评测集合成或联调验证。Use when user says '确立指标'establish metrics'设计打分规则'实现指标代码'"
argument-hint: [stage4-context]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob
metadata:
  openclaw:
    emoji: ""
    requires:
      bins: [python3]
---

## `BENCHCLAW_ROOT` 只读约束

- **BENCHCLAW_READONLY = true**：`BENCHCLAW_ROOT/` 只能作为 BenchClaw 仓库内共享只读资源根，必须从当前 skill 所在的 BenchClaw 仓库位置解析，不能依赖固定 home 路径或机器绝对路径。
- 严禁在 `BENCHCLAW_ROOT/` 下创建、编辑、覆盖、删除、移动、重命名、复制写入、初始化 git、提交、打 tag、写日志、写缓存或写临时文件。
- 所有派生产物、补丁、快照、报告、脚本、配置、日志和测试输出必须写入 active `WORKSPACE_ROOT`。
- 如必须修改 `BENCHCLAW_ROOT/` 中的资源，只能在 workspace 中生成 patch 或修改建议，等待用户在外部处理；当前 skill 不得直接应用。


## Workspace and File Access Boundary

This skill must operate only inside the current run workspace.

- Before reading or writing any run artifact, resolve and record the active `WORKSPACE_ROOT = ~/bench_workspace/workspace{i}` from the current task, parent stage, or pipeline state.
- Read and write only files under the active `WORKSPACE_ROOT` and the explicitly required global resource roots named by this skill, such as `BENCHCLAW_ROOT/simulatorCards/`, `BENCHCLAW_ROOT/benchmarkDatasetCards/`, `BENCHCLAW_ROOT/realdata_cards/`, `BENCHCLAW_ROOT/templates/`, `BENCHCLAW_ROOT/model_api/`, `BENCHCLAW_ROOT/data-juicer_card/`, `BENCHCLAW_ROOT/annotation-tool/`, or `BENCHCLAW_ROOT/skills/` when the current skill explicitly requires them.
- Never read, list, grep, summarize, compare, copy, or infer from any other `~/bench_workspace/workspace{j}` where `j != i`, even if the current artifact is missing or another workspace appears newer or more complete.
- Never scan broad server directories such as `~`, `/`, `/home`, `/mnt`, `/data`, `/tmp`, `C:\Users`, `C:\`, or arbitrary project/download folders to discover context. Only inspect the exact current workspace paths and exact allowlisted resource roots needed for this skill.
- If an expected input is missing from the active workspace or an allowlisted resource root, stop and report the missing path. Do not search unrelated folders or borrow replacement artifacts from another workspace.
- Outputs must be written only to the active `WORKSPACE_ROOT` paths declared by this skill. Do not mirror or cache run artifacts into other workspaces or unrelated server folders.
- If the user explicitly provides an external path, use it only when it is directly relevant to this skill, record it as a user-provided exception, and do not expand access to sibling or parent directories.

This boundary overrides convenience behaviors such as auto-discovery, resume from latest workspace, reuse of previous artifacts, broad recursive grep/list, and fallback search.

# Benchmark Metric Establishment

Execute metric system establishment for: **$ARGUMENTS**

This skill is an **atomic single-responsibility skill**.
It must **only** do the work scoped to this module.

---

## Critical Hotfix: Executable Metric Library Is Mandatory

This module owns the Stage 4 failure mode where `METRIC_LIBRARY/metrics/`,
`METRIC_LIBRARY/aggregators/`, or `METRIC_LIBRARY/tests/` are empty. That output
is invalid. Do not mark Phase 2 complete unless the metric library is importable,
executable, documented, and covered by tests.

Minimum required runtime artifacts:

- `METRIC_LIBRARY/interfaces.py`
- `METRIC_LIBRARY/metrics/__init__.py`
- one concrete metric implementation for every metric named in
  `METRIC_SPEC.md`, `CAPABILITY_METRIC_MAP.md`, or template
  `downstream_metrics`
- `METRIC_LIBRARY/aggregators/dimension_aggregator.py`
- `METRIC_LIBRARY/aggregators/overall_aggregator.py`
- `METRIC_LIBRARY/README.md`
- executable tests under `METRIC_LIBRARY/tests/`
- `tools/evaluate_evalset.py`, an offline runner that loads
  `EVALSET_DATASET/`, model/system outputs, calls `METRIC_LIBRARY`, and writes
  per-sample plus aggregate scores

For short-answer or single-choice evalsets, provide these baseline metrics
unless the schema proves they are irrelevant:

- `D_acc_short_answer`: normalized exact-match accuracy against
  `gt/answer_canonical.json` or the schema-equivalent canonical answer field.
  Normalize case, surrounding whitespace, common trailing punctuation, and
  choice wrappers such as `A.` or `(A)`.
- `refusal_rate`: binary sample metric detecting empty output or explicit
  refusal; aggregate as mean.
- `response_length`: token or whitespace-word count diagnostic; aggregate as
  mean.
- `per_source_acc`: aggregation grouped by source fields such as `source_name`,
  `source_simulator`, `source_type`, or schema-equivalent fields.

If a metric is declared anywhere but cannot be implemented because required GT
fields are missing, write a blocking issue into `METRIC_SPEC.md` and stop with
Phase 2 = FAIL. Never leave a declared metric as an empty file, placeholder, or
documentation-only entry.

The evaluator runner must support a deterministic smoke-test mode using GT-copy
predictions. GT-copy must score perfectly for exact-match metrics; empty
predictions must score zero and increment refusal diagnostics. These conditions
are hard gates for Phase 2 completion.

---

## Purpose

- 本模块负责以 `EVALSET_PROTOTYPE.md` 的指标设计草稿为起点，结合实际评测集 schema，落地完整的指标体系- 本模块为每个能力维度建立指标映射，编写数学定义与打分规则，并实现可执行、可测试的指标算法库- 本模块记录从 `EVALSET_PROTOTYPE.md` 草稿到最终指标的变更理由- 本模块位Stage 4 第二环节，直接产物是 `CAPABILITY_METRIC_MAP.md`、`METRIC_SPEC.md`、`SCORING_RULES.md`、`METRIC_LIBRARY/`- 本模块不负责评测集合成或联调验证
---

## Inputs

- `$ARGUMENTS`：指标设计的补充要求（如偏好特定指标类型、聚合方式偏好）- 必需输入->  - `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md` ->能力维度列表及操作性定义  - `~/bench_workspace/workspace{i}/stage1/EVALSET_PROTOTYPE.md` ->指标设计草稿（追溯起点，§ Metric System->  - `~/bench_workspace/workspace{i}/stage4/EVALSET_SCHEMA.md` ->评测集字段定义与下游契约
- 新增必需输入：`~/bench_workspace/workspace{i}/stage4/CAPABILITY_TEMPLATE_METRIC_MAP.json` -> Phase 1 产出的能力维度-模板-指标接口映射，必须优先读取并作为指标覆盖基准。
- 可选输入：
  - `~/bench_workspace/workspace{i}/stage4/EVALSET_DATASET/` ->用于抽样验证指标实现的实际数据  - `~/bench_workspace/workspace{i}/stage4/EVALSET_SYNTHESIS_RULES.md` ->了解难度分级以设计难度加权指->  - 父流程Constants：`COVERAGE_THRESHOLD`
- **若任一必需输入缺失，应立即停止并报告缺失文件*

---

## Procedure

1. **读取上游产出**->   - ->`CAPABILITY_SCOPE.md` 提取能力维度列表及操作性定义   - ->`EVALSET_PROTOTYPE.md` § Metric System 提取指标设计草稿（维度级、聚合、诊断指标）
   - ->`CAPABILITY_TEMPLATE_METRIC_MAP.json` 提取每个能力维度声明的 `metric_ids`、required input fields、required GT fields 和适用 source_type；该映射优先级高于旧草稿。
   - ->`EVALSET_SCHEMA.md` 提取 Input Fields、GT Fields ->Downstream Contract

2. **建立能力维度到指标的映射（子步骤 2.1*->   - ->`EVALSET_PROTOTYPE.md` 草稿为起点，逐维度落地指标映->   - 为每个能力维度确定：
     - **主指*：该维度的核心评->     - **辅助指标**：补充诊断信息     - **所需输入字段**：必须存在于 `EVALSET_SCHEMA.md` ->GT Fields ->Input Fields ->   - 定义跨维度聚合指标（overall score 计算方式->   - 记录从草稿到最终指标的每项变更及理由   - 计算覆盖率：有指标的维度->/ 总维度数，与 `COVERAGE_THRESHOLD` 比较
   - 输出`CAPABILITY_METRIC_MAP.md`

3. **制定指标规范（子步骤 2.2a*：对每个指标编写规范—->   - 指标名称、数学定义（公式）、值域、方向（越高越好 / 越低越好->   - 输入类型（预测值格式、GT 格式->   - 边界情况处理（空预测、格式错误、超出范围）
   - 置信区间或统计显著性计算方式（若适用->   - 输出`METRIC_SPEC.md`

4. **制定打分规则（子步骤 2.2b*：对每个指标定义打分规则—->   - 原始分数计算公式
   - 归一化方式（若有->   - 聚合方式：样本级 ->维度overall
   - 打分粒度：连->/ 离散等级 / 二->   - 定义结果输出的结构化格式
   - 输出`SCORING_RULES.md`

5. **实现指标算法库（子步2.3*->   - 为每个指标实际Python 计算代码
   - 代码要求->     - 输入接口`EVALSET_SCHEMA.md` 的字段名和格式严格对->     - 输出接口`SCORING_RULES.md` 的聚合逻辑一->     - 包含 docstring 引用 `METRIC_SPEC.md` 中的对应指标定义
   - 实现聚合器：`dimension_aggregator.py`（维度级聚合-> `overall_aggregator.py`（全局聚合->   - 定义 `interfaces.py`（输入输出接口类型定义）
   - 编写单元测试：覆盖正常用+ 边界情况（空预测、格式错误、超范围、完美预测、全错预测）
   - 运行单元测试并记录通过状况
   - 输出`METRIC_LIBRARY/`

6. **校验**->   - 确认覆盖`COVERAGE_THRESHOLD`（或未覆盖维度有显式豁免说明->   - 确认 `METRIC_LIBRARY/` 中的每个指标函数都有对应`METRIC_SPEC.md` 条目
   - 确认接口定义`EVALSET_SCHEMA.md` 字段名一->   - 确认单元测试全部通过

---

## Expected Outputs

- `~/bench_workspace/workspace{i}/stage4/CAPABILITY_METRIC_MAP.md`
- `~/bench_workspace/workspace{i}/stage4/METRIC_SPEC.md`
- `~/bench_workspace/workspace{i}/stage4/SCORING_RULES.md`
- `~/bench_workspace/workspace{i}/stage4/METRIC_LIBRARY/`
- `~/bench_workspace/workspace{i}/stage4/tools/evaluate_evalset.py`
  ```
  METRIC_LIBRARY/
  ├── metrics/
  ->  ├── {metric_name}.py
  ->  └── ...
  ├── aggregators/
  ->  ├── dimension_aggregator.py
  ->  └── overall_aggregator.py
  ├── tests/
  ->  ├── test_{metric_name}.py
  ->  └── ...
  ├── interfaces.py
  └── README.md
  ```

`CAPABILITY_METRIC_MAP.md` 结构
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

## Coverage Check
- Total dimensions: [N]
- Dimensions with primary metric: [N]
- Dimensions explicitly exempted: [列表及豁免理由]
- Coverage rate: [百分比] (threshold: COVERAGE_THRESHOLD)
```

`METRIC_SPEC.md` 结构
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

`SCORING_RULES.md` 结构
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

- [ ] No declared metric is missing an executable implementation.
- [ ] `METRIC_LIBRARY/metrics/`, `METRIC_LIBRARY/aggregators/`, and `METRIC_LIBRARY/tests/` are non-empty.
- [ ] `tools/evaluate_evalset.py` exists and can run an offline smoke eval.
- [ ] GT-copy smoke predictions produce expected perfect scores for exact-match metrics; empty predictions produce expected zero/refusal behavior.
- [ ] Unit tests are actually executed, and their command plus pass/fail result is recorded in `METRIC_LIBRARY/README.md` or `STAGE4_SUMMARY.md`.

- [ ] `CAPABILITY_METRIC_MAP.md` 存在Coverage Check 中覆盖率 ->`COVERAGE_THRESHOLD`（或未覆盖维度有显式豁免）- [ ] `METRIC_SPEC.md` 存在且为每个指标包含完整的六项规范字段（定义、值域、方向、输入、边界、统计显著性）- [ ] `SCORING_RULES.md` 存在且包含三级聚合规则（样本级、维度级、overall）- [ ] `METRIC_LIBRARY/` 存在且每个`METRIC_SPEC.md` 中的指标都有对应`.py` 实现文件- [ ] `METRIC_LIBRARY/tests/` 中的单元测试全部通过- [ ] `interfaces.py` 中的字段名与 `EVALSET_SCHEMA.md` 一致- [ ] Lineage 章节记录了从 `EVALSET_PROTOTYPE.md` 到最终指标的变更理由- [ ] 若必需输入缺失，不得标记完成功
---

## Rules

- 不生成或修改评测集数据——那Phase 1 `benchmark-evalset-generate` 的职责- 不执行联调验证——那Phase 3 `benchmark-validate-stage4` 的职责- 不擅自改写任Stage 1、Stage 2 ->Phase 1 产出文件- 指标必须可执行——`METRIC_LIBRARY/` 中的代码必须能实际运行并通过单元测试，不可只是伪代码或规范文档- 指标输入接口必须`EVALSET_SCHEMA.md` 严格对齐——字段名、数据类型、格式不可有偏差- 边界情况处理必须`METRIC_SPEC.md` 和代码中同时体现——不可规范写了但代码未实现- 追溯链不可断——`CAPABILITY_METRIC_MAP.md` ->Lineage 章节必须存在- 出错时必须明确指出阻塞原因（`EVALSET_SCHEMA.md` 中缺少某指标所需求GT 字段）- 如果 Write 因文件过大失败，立即 fallback ->Bash 分块写入，不要询问用户许可选
---

## Downstream Handoff

- `benchmark-validate-stage4` 读取 `~/bench_workspace/workspace{i}/stage4/METRIC_SPEC.md` + `~/bench_workspace/workspace{i}/stage4/SCORING_RULES.md` + `~/bench_workspace/workspace{i}/stage4/METRIC_LIBRARY/` + `~/bench_workspace/workspace{i}/stage4/CAPABILITY_METRIC_MAP.md` 执行联调验证- Stage 5 评测执行读取 `~/bench_workspace/workspace{i}/stage4/METRIC_LIBRARY/` 对被评测系统的输出计算分数据- 本模块只写交接关系，不调度下游模块
