---
name: benchmark-run-metrics
description: "Atomic module: stage5 Phase 3 指标打分与聚合模块。只负责读取模型推理结果GT，调METRIC_LIBRARY 对每个样本计算指标分数，按维度和 overall 聚合，输出分数文件与汇总报告，不负责推理执行、异常检查或最终评测报告生成。Use when user says '打分'run metrics'计算指标'算分'"
argument-hint: [stage5-context]
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

# Benchmark Run Metrics

Execute metric scoring and aggregation for: **$ARGUMENTS**

This skill is an **atomic single-responsibility skill**.
It must **only** do the work scoped to this module.

---

## Purpose

- 本模块负责对模型推理结果逐样本计算指标分数，并按维度级和 overall 级聚合- 本模块严格调`METRIC_LIBRARY/` 中的已有指标代码，不重新实现指标逻辑- 本模块位Stage 5 第三环节，直接产物是 `SCORES.csv` ->`SCORE_SUMMARY.md`- 本模块不负责模型推理、异常检查、污染检查或最终评测报告
---

## Inputs

- `$ARGUMENTS`：打分的补充要求（如仅对特定维度打分、使用替代聚合权重）- 必需输入->  - `~/bench_workspace/workspace{i}/stage5/RAW_MODEL_OUTPUTS.jsonl` ->模型推理结果
  - `~/bench_workspace/workspace{i}/stage4/METRIC_LIBRARY/` ->指标算法代码->  - `~/bench_workspace/workspace{i}/stage4/METRIC_SPEC.md` ->指标规范（值域、边界处理）
  - `~/bench_workspace/workspace{i}/stage4/SCORING_RULES.md` ->打分与聚合规->  - `~/bench_workspace/workspace{i}/stage4/CAPABILITY_METRIC_MAP.md` ->维度-指标映射
  - `~/bench_workspace/workspace{i}/stage4/EVALSET_DATASET/` ->GT 参考答- 可选输入：
  - `~/bench_workspace/workspace{i}/stage4/EVALSET_SCHEMA.md` ->辅助确认字段对齐
- **若任一必需输入缺失，应立即停止并报告缺失文件*

---

## Procedure

### Step 1: 样本级打
1. 读取 `RAW_MODEL_OUTPUTS.jsonl`，按 `eval_status` 分类->   - `success`（`parse_success = true`）→ 正常打分
   - `parse_failed` ->`METRIC_SPEC.md` 边界情况处理规则赋分（通常最低分N/A->   - `api_failed` ->标记`eval_failed`，不参与分数统计
2. 读取 `CAPABILITY_METRIC_MAP.md` 确定每个维度适用的指标列表3. 对每个`success` 样本->   - ->`sample_id` ->`EVALSET_DATASET/` 加载对应 GT
   - 调用 `METRIC_LIBRARY/metrics/` 中对应维度的指标计算函数
   - 传入 `parsed_output`（预测）GT
   - 记录该样本在所有适用指标上的原始分数
4. ->`parse_failed` 样本->   - ->`METRIC_SPEC.md` § Edge cases 中的 "Format error" ->"Empty prediction" 规则赋分
   - 在记录中标注赋分来源为边界处
### Step 2: 维度级聚
5. ->`SCORING_RULES.md` § Dimension-Level Aggregation 中的聚合方式，对每个能力维度汇总样本级分数据6. 计算每个维度的描述性统计：均值、中位数、标准差7. 按难度等级分层统计：easy / medium / hard 各自的均值
### Step 3: Overall 聚合

8. ->`SCORING_RULES.md` § Overall Aggregation 中的公式和权重，从维度级分数计算总分
### Step 4: 输出分数文件

9. 写入 `SCORES.csv`（样本级详细分数）10. 写入 `SCORE_SUMMARY.md`（汇总级结果）
### Step 5: 校验

11. 确认 `SCORES.csv` 中的样本= `RAW_MODEL_OUTPUTS.jsonl` ->`eval_status ->api_failed` 的样本数据12. 确认每个能力维度`SCORE_SUMMARY.md` 中都有对应的分数行13. 确认所有分数值在 `METRIC_SPEC.md` 定义的值域内
---

## Expected Outputs

- `~/bench_workspace/workspace{i}/stage5/SCORES.csv`
- `~/bench_workspace/workspace{i}/stage5/SCORE_SUMMARY.md`

`SCORES.csv` 字段
```csv
sample_id,dimension,difficulty,metric_1,metric_2,...,eval_status,scoring_note
dim1_sample_001,dimension_1,medium,0.85,0.72,...,scored,
dim1_sample_002,dimension_1,hard,0.0,0.0,...,scored,parse_failed_boundary_rule
dim2_sample_001,dimension_2,easy,0.91,0.88,...,scored,
```

`eval_status` 取值：`scored`（正常打分或边界规则赋分）、`eval_failed`（API 失败，不打分）
`SCORE_SUMMARY.md` 结构
```markdown
# Score Summary

## Overall Score
- **Overall**: [总分] (method: [聚合方式])

## Per-Dimension Scores
| Dimension | Mean | Median | Std | Easy | Medium | Hard | Samples |
|-----------|------|--------|-----|------|--------|------|---------|
| ...       | ...  | ...    | ... | ...  | ...    | ...  | ...     |

## Per-Metric Scores
| Metric | Mean | Median | Std | Range |
|--------|------|--------|-----|-------|
| ...    | ...  | ...    | ... | ...   |

## Scoring Coverage
- Samples scored: [N] / [total]
- Parse failures (boundary-scored): [N]
- API failures (excluded): [N]
- Effective scoring rate: [百分比]

## Score Distribution
[各维各难度的分数分布描述性统计]
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

- [ ] `~/bench_workspace/workspace{i}/stage5/SCORES.csv` 存在且样本数与预期一致- [ ] `~/bench_workspace/workspace{i}/stage5/SCORE_SUMMARY.md` 存在且包Overall Score、Per-Dimension Scores、Scoring Coverage 三个章节- [ ] 每个能力维度Per-Dimension Scores 表中都有对应行- [ ] 所有分数值在 `METRIC_SPEC.md` 定义的值域内- [ ] `parse_failed` 样本已按边界规则赋分并在 `scoring_note` 中标注- [ ] `api_failed` 样本已排除出分数统计并在 Scoring Coverage 中记录- [ ] 若必需输入缺失，不得标记完成功
---

## Rules

- 不执行模型推理——那Phase 2 的职责- 不执行异常检查、污染检查或生成最终评测报告——那Phase 4 的职责- 不擅自改`RAW_MODEL_OUTPUTS.jsonl`、`METRIC_LIBRARY/` 或任何上游产出- 必须使用 `METRIC_LIBRARY/` 中的已有代码打分——不可重新实现指标逻辑或绕过已有代码- 分数必须可追溯——`SCORES.csv` 中的每个分数必须可追溯到 `RAW_MODEL_OUTPUTS.jsonl` 中的 `parsed_output` ->`EVALSET_DATASET/` 中的 GT- 不可丢弃 `parse_failed` 样本——必须按边界规则赋分并标注，不可静默排除- 聚合权重和方式必须严格遵`SCORING_RULES.md`——不可自行调整权重跑- 出错时必须明确指出阻塞原因（`METRIC_LIBRARY/` 代码执行失败、GT 文件缺失、字段不匹配）- 如果 Write 因文件过大失败，立即 fallback ->Bash 分块写入，不要询问用户许可选
---

## Downstream Handoff

- `benchmark-check-scores` 读取 `~/bench_workspace/workspace{i}/stage5/SCORES.csv` ->`~/bench_workspace/workspace{i}/stage5/SCORE_SUMMARY.md` 执行异常分数检查和报告生成功- 本模块只写交接关系，不调度下游模块