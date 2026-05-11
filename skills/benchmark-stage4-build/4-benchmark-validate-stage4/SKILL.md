---
name: benchmark-validate-stage4
description: "Atomic module: stage4 Phase 4 联调验证模块。只负责对评测集与指标体系执行四项验证（输入输出契约、评分链dry-run、可复现性、覆盖完整性），输PASS/FAIL 判定与阻塞项分析，不负责评测集合成或指标实现。Use when user says '联调验证'validate stage4'验证评测集和指标'dry-run 评分'"
argument-hint: [stage4-context]
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

# Benchmark Stage 4 Validation

Execute joint validation of evalset and metrics for: **$ARGUMENTS**

This skill is an **atomic single-responsibility skill**.
It must **only** do the work scoped to this module.

---

## Critical Hotfix: Empty Metric Library Must Fail Validation

Before any dry-run, inspect `METRIC_LIBRARY/` and fail immediately if any of the
following are missing or empty:

- `metrics/` with concrete metric `.py` files
- `aggregators/` with concrete aggregator `.py` files
- `tests/` with executable tests
- `interfaces.py`
- `README.md`
- `tools/evaluate_evalset.py` under the Stage 4 root

Validation must compare declared metrics from `METRIC_SPEC.md`,
`CAPABILITY_METRIC_MAP.md`, and template `downstream_metrics` against actual
Python implementation files. Any declared-but-unimplemented metric is a
critical blocking issue with Suggested Fix Phase = `Phase 2.3
/benchmark-metric-establish`.

The scoring dry-run must execute code, not only inspect schemas. It must run at
least direct metric calls for GT-copy predictions, direct metric calls for empty
predictions, aggregator calls over sample scores, and the offline runner
`tools/evaluate_evalset.py` in smoke-test mode when present.

If GT-copy predictions fail to produce perfect exact-match scores, or empty
predictions fail to produce zero/refusal behavior, Validation verdict must be
FAIL.

## Critical Hotfix: Eval Questions Must Be Observation-Grounded

Validation must reject samples whose answers can be inferred without the
declared observation payload. During Input-Output Contract Validation, sample and
check:

- `quality_constraints` exists for each template used by sampled items.
- Each sampled official item has `grounding_check.verdict=PASS`.
- Required observation files exist and are referenced by the sample input.
- GT answer strings, normalized aliases, option labels, coordinates, counts,
  directions, scene IDs, floor-plan IDs, and answer-bearing metadata do not
  appear in instruction/options/public metadata/file names/paths.
- For non-`text_only_allowed` tasks, the text-only baseline is expected to be at
  or below chance and marked in `grounding_check.text_only_baseline_expected`.

Any leakage or metadata-only/text-only solvability is a critical blocking issue
with Suggested Fix Phase = `Phase 1.1-1.3 /benchmark-evalset-generate`.

## Critical Hotfix: Validate HuggingFace Evalset Folder Contract

Validation must fail if `EVALSET_DATASET/` is not a HuggingFace-friendly final
dataset root with one independent folder per question.

During Input-Output Contract Validation, check:

- Root files exist: `README.md`, `dataset_info.json`, `data.jsonl`,
  `manifest.json`, `statistics.json`, and `gt_generators/`.
- `data.jsonl` is valid JSONL, one row per question, with relative paths only.
- Each row includes `question_id`, `source_type`, `source_name`,
  `capability_dimension`, `question_dir`, `images`, `question_path`,
  `answer_path`, `ground_truth_path`, `gt_generator_file`,
  `gt_generator_function`, `metadata_path`, `template_id`, `metric_ids`, and
  `split`.
- Every `question_dir` matches
  `{source_type}/{source_name}/{capability_dimension}/{question_id}/`.
- Every question folder contains `images/`, `question.json`, `question.md`,
  `answer.json`, `ground_truth.json`, `gt_code_ref.json`, and `metadata.json`.
- Every image required by the question is inside that question's `images/`
  directory and uses stable numbering such as `image_0001.{ext}`.
- Every `gt_code_ref.json` points to an existing file under
  `EVALSET_DATASET/gt_generators/` and names the function/version used to
  generate that question's `ground_truth.json`.

Any violation is a critical blocking issue with Suggested Fix Phase =
`Phase 1.3-1.4 /benchmark-evalset-generate`.

---

## Purpose

- 本模块负责对 Phase 1 合成的评测集Phase 2 建立的指标体系执行端到端联调验证- 本模块验证四项内容：输入输出契约一致性、评分链dry-run、可复现性、覆盖完整性- 本模块给出明确的 PASS/FAIL 判定，FAIL 时逐项列出阻塞项及建议回退 phase- 本模块位Stage 4 第三环节（最后一个执行环节），直接产物是 `VALIDATION_REPORT.md` ->`DRY_RUN_RESULTS.md`- 本模块不负责修复评测集或指标——只诊断问题并指出修复方向
---

## Inputs

- `$ARGUMENTS`：验证的补充要求（如指定 dry-run 预测策略、增加抽样量）- 必需输入->  - `~/bench_workspace/workspace{i}/stage4/EVALSET_DATASET/` ->合成后的评测集  - `~/bench_workspace/workspace{i}/stage4/EVALSET_SCHEMA.md` ->评测集schema 定义
  - `~/bench_workspace/workspace{i}/stage4/METRIC_SPEC.md` ->指标规范
  - `~/bench_workspace/workspace{i}/stage4/SCORING_RULES.md` ->打分与聚合规->  - `~/bench_workspace/workspace{i}/stage4/METRIC_LIBRARY/` ->可执行的指标算法->  - `~/bench_workspace/workspace{i}/stage4/CAPABILITY_METRIC_MAP.md` ->能力维度到指标的映射
- 可选输入：
  - `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md` ->维度列表（用于覆盖完整性验证）
  - 父流程Constants：`DRY_RUN_SAMPLE_SIZE`、`METRIC_REPRODUCIBILITY_RUNS`、`COVERAGE_THRESHOLD`
- **若任一必需输入缺失，应立即停止并报告缺失文件*

---

## Procedure

1. **读取全部上游产出**：加载评测集数据索引、schema 定义、指标规范、打分规则、指标代码库、维指标映射
2. **输入输出契约验证（子步骤 3.1*->   - ->`EVALSET_DATASET/` 中抽`DRY_RUN_SAMPLE_SIZE`（默50）个样本
   - 对每个样本逐字段验证：
     - 输入字段是否符合 `EVALSET_SCHEMA.md` § Input Fields 定义（类型、格式、必填性）
     - GT 字段是否符合 `EVALSET_SCHEMA.md` § GT Fields 定义
     - 元数据字段是否完整（source_simulator、scene_id、frame_id、dimension、difficulty->   - 验证 `METRIC_LIBRARY/interfaces.py` 的接口定义与 `EVALSET_SCHEMA.md` 的字段名/格式是否严格对齐
   - 记录所有不一致项，给PASS/FAIL

3. **评分链路 dry-run（子步骤 3.2*->   - 对抽取的样本构造模拟预测结果（策略：随机预测、全零预测、GT 复制三种，取并集覆盖->   - 用模拟预+ GT 调用 `METRIC_LIBRARY/metrics/` 中每个指标的计算函数
   - 验证->     - 每个指标是否能正常计算并返回有效值（无异常抛出）
     - 返回值是否在 `METRIC_SPEC.md` 定义的值域->     - 边界情况是否`METRIC_SPEC.md` 的规范处理（空预测、格式错误、超范围->   - 调用 `aggregators/dimension_aggregator.py` ->`overall_aggregator.py`，验证聚合逻辑
   - 记录每个指标的测试结果与示例输出
4. **可复现性验证（子步3.3*->   - 对相同样+ 相同模拟预测重复运行 `METRIC_REPRODUCIBILITY_RUNS`（默3）次
   - 对确定性指标：验证每次输出完全一致（bit-exact->   - 对随机性指标（若有）：验证输出在预期置信区间内
   - 记录复现性结构
5. **覆盖完整性验证（子步3.4*->   - ->`CAPABILITY_METRIC_MAP.md` 检查每个能力维度是否有对应主指->   - ->`EVALSET_DATASET/manifest.json` 检查每个有指标的维度是否有足够样本
   - 对未覆盖维度检查是否有显式豁免说明
   - 计算覆盖率，`COVERAGE_THRESHOLD` 比较
   - 给出 PASS/FAIL

6. **形成验证结论（子步骤 3.5*->   - 汇总四项验证结构   - PASS 条件（必须全部满足）->     - 输入输出契约无不一致项
     - 所有指dry-run 成功且值域合法
     - 可复现性验证通过
     - 覆盖`COVERAGE_THRESHOLD`
   - FAIL 时逐项列出阻塞项、严重等级、影响组件及建议修复 phase
   - 记录非阻塞但建议关注warning

7. **写入**：写入`~/bench_workspace/workspace{i}/stage4/VALIDATION_REPORT.md` ->`~/bench_workspace/workspace{i}/stage4/DRY_RUN_RESULTS.md`
---

## Expected Outputs

- `~/bench_workspace/workspace{i}/stage4/VALIDATION_REPORT.md`
- `~/bench_workspace/workspace{i}/stage4/DRY_RUN_RESULTS.md`

`VALIDATION_REPORT.md` 结构
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
| ...   | critical/major | EVALSET_SCHEMA / METRIC_LIBRARY / ... | Phase {N} |

## 6. Non-Blocking Warnings
[不影pass 但建议后续关注的问题]
```

`DRY_RUN_RESULTS.md` 结构
```markdown
# Dry-Run Results

## Test Configuration
- Sample size: [DRY_RUN_SAMPLE_SIZE]
- Prediction strategies: random, zero, gt-copy
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

- [ ] Empty `METRIC_LIBRARY` subdirectories are treated as FAIL, not warning.
- [ ] Every declared metric is matched to an importable implementation file.
- [ ] `tools/evaluate_evalset.py` smoke mode is executed or its absence is marked FAIL.
- [ ] GT-copy and empty-prediction smoke checks are recorded in `DRY_RUN_RESULTS.md`.
- [ ] HuggingFace evalset root files, `data.jsonl`, per-question folders, numbered `images/`, and `gt_code_ref.json` references are validated.
- [ ] Sampled eval questions pass observation-grounding and leakage checks.
- [ ] Any text-only-solvable non-text task is marked FAIL with Phase 1 fix target.

- [ ] `VALIDATION_REPORT.md` 存在且包含明确的 Verdict（PASS ->FAIL）- [ ] 四项验证（契约、dry-run、可复现性、覆盖完整性）全部执行且每项有独立PASS/FAIL 状态- [ ] `DRY_RUN_RESULTS.md` 存在Per-Metric Results 表覆盖`METRIC_SPEC.md` 中的所有指标- [ ] ->Verdict = FAIL，Blocking Issues 表非空且每项包含 Suggested Fix Phase- [ ] dry-run 实际执行了指标代码（不可仅做静态检查）- [ ] 若必需输入缺失，不得标记完成功
---

## Rules

- 不修复评测集数据或指标代码——本模块只诊断问题，修复是上phase 的职责- 不擅自改`EVALSET_DATASET/`、`METRIC_LIBRARY/`、`EVALSET_SCHEMA.md` 或任何上游产出- 不跳过任何一项验证——四项验证全部执行是硬性要求- dry-run 必须实际调用指标代码——不可仅schema 级静态对比而不执行计算- 模拟预测必须包含至少三种策略（随机、全零、GT 复制），以覆盖正常和边界情况- Verdict = FAIL 时不可将阻塞项降级为 warning 以强PASS- Blocking Issues ->Suggested Fix Phase 必须指向具体的上phase（如"Phase 2.3"而非"Phase 2"），帮助精确定位回退目标- 出错时必须明确指出阻塞原因（如指标代码抛出未捕获异常、schema 字段不存在）- 如果 Write 因文件过大失败，立即 fallback ->Bash 分块写入，不要询问用户许可选
---

## Downstream Handoff

- 父流程`benchmark-stage4-build` 读取 `~/bench_workspace/workspace{i}/stage4/VALIDATION_REPORT.md` ->Verdict 决定是否展示 Gate 4 或触发回退到- Stage 5 评测执行Verdict = PASS 为前提条件- 本模块只写交接关系，不调度下游模块
