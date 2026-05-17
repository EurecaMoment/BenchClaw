---
name: benchmark-stage5-eval
description: "Stage 5 子流程：灰度评测与全量评测执行。编排benchmark-build-eval-system-prompt ->benchmark-canary-eval ->benchmark-canary-localize-rollback（仅灰度失败时）benchmark-call-model-api ->benchmark-run-metrics ->benchmark-check-scores，先用灰金丝雀评测验证 prompt、API、schema、metric 与成本，再决定是否进入全量评测；灰度发现问题时必须定位并回退到相stage/phase/skill。Use when user says '开始stage5'先灰度再全量评测'跑评evaluation stage'run eval'."
argument-hint: [model-api-config-or-stage4-dir]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, WebSearch, WebFetch, Skill
---

## `BENCHCLAW_ROOT` 只读约束

- **BENCHCLAW_READONLY = true**：`BENCHCLAW_ROOT/` 只能作为 BenchClaw 仓库内共享只读资源根，必须从当前 skill 所在的 BenchClaw 仓库位置解析，不能依赖固定 home 路径或机器绝对路径。
- 严禁在 `BENCHCLAW_ROOT/` 下创建、编辑、覆盖、删除、移动、重命名、复制写入、初始化 git、提交、打 tag、写日志、写缓存或写临时文件。
- 所有派生产物、补丁、快照、报告、脚本、配置、日志和测试输出必须写入 active `WORKSPACE_ROOT`。
- 如必须修改 `BENCHCLAW_ROOT/` 中的资源，只能在 workspace 中生成 patch 或修改建议，等待用户在外部处理；当前 skill 不得直接应用。


## Workspace and File Access Boundary

This skill must operate only inside the current run workspace.

- Before reading or writing any run artifact, resolve and record the active `WORKSPACE_ROOT = ~/bench_workspace/workspace{i}` from the current task, parent stage, or pipeline state.
- Read and write only files under the active `WORKSPACE_ROOT`. The explicitly required global resource roots named by this skill, such as `BENCHCLAW_ROOT/simulatorCards/`, `BENCHCLAW_ROOT/benchmarkDatasetCards/`, `BENCHCLAW_ROOT/realdata_cards/`, `BENCHCLAW_ROOT/templates/`, `BENCHCLAW_ROOT/model_api/`, `BENCHCLAW_ROOT/data-juicer_card/`, `BENCHCLAW_ROOT/annotation-tool/`, or `BENCHCLAW_ROOT/skills/`, are read-only inputs.
- Never create, edit, overwrite, delete, move, rename, copy files into, initialize git state in, commit, tag, cache, or log under any path inside `BENCHCLAW_ROOT/`.
- Never read, list, grep, summarize, compare, copy, or infer from any other `~/bench_workspace/workspace{j}` where `j != i`, even if the current artifact is missing or another workspace appears newer or more complete.
- Never scan broad server directories such as `~`, `/`, `/home`, `/mnt`, `/data`, `/tmp`, `C:\Users`, `C:\`, or arbitrary project/download folders to discover context. Only inspect the exact current workspace paths and exact allowlisted resource roots needed for this skill.
- If an expected input is missing from the active workspace or an allowlisted resource root, stop and report the missing path. Do not search unrelated folders or borrow replacement artifacts from another workspace.
- Outputs must be written only to the active `WORKSPACE_ROOT` paths declared by this skill. Do not mirror or cache run artifacts into other workspaces or unrelated server folders.
- If the user explicitly provides an external path, use it only when it is directly relevant to this skill, record it as a user-provided exception, and do not expand access to sibling or parent directories.

This boundary overrides convenience behaviors such as auto-discovery, resume from latest workspace, reuse of previous artifacts, broad recursive grep/list, and fallback search.

# Benchmark Stage 5: 灰度评测与全量评测执
Orchestrate the complete Stage 5 canary-first evaluation workflow for: **$ARGUMENTS**

This skill is an **orchestrator only**. It must not re-implement the internal logic of any atomic sub-skill.

## Overview

```text
STAGE1 + STAGE4 artifacts + model API config
->/benchmark-build-eval-system-prompt
->/benchmark-canary-eval
if canary FAIL: /benchmark-canary-localize-rollback ->stop full eval and request rollback
if canary PASS: /benchmark-call-model-api
->/benchmark-run-metrics
->/benchmark-check-scores
Stage 5 summary
(评测prompt构建)  (灰度/金丝雀评测)  (失败定位回退)  (全量推理)  (指标打分)  (结果质检)
```

Each phase builds on the previous one's output。Phase 之间严格顺序依赖，不可跳过或乱序
## Workspace

所有产出写入当前workspace ->`~/bench_workspace/workspace{i}/stage5/` 子目录：

```text
~/bench_workspace/workspace{i}/stage5/
```

其中 `{i}` 由父流程或用户指定。若未指定，默认使用序号最高的 `workspace{i}`
## Constants

* **AUTO_PROCEED = false** ->关卡处是否自动继续。默认等待用户确认* **HUMAN_CHECKPOINT = true** ->`true` 时，关键关卡必须暂停并展示阶段结果* **COMPACT = false** ->`true` 时，额外生成 `STAGE5_COMPACT.md`* **LOCAL_MODEL_API_AWARE = true** ->`MODEL_API_CONFIG.json` 缺失，允许从 `model_api/` 目录脚本推导 API 契约* **CANARY_REQUIRED = true** ->全量评测前必须先跑灰度评测集* **CANARY_MIN_SAMPLES = 20** ->灰度评测最低样本数据* **CANARY_MAX_SAMPLES = 200** ->灰度评测最高样本数据* **CANARY_SAMPLE_RATIO = 0.02** ->灰度样本默认比例* **CANARY_API_FAILURE_THRESHOLD = 0.03** ->灰度 API 失败率阈值* **CANARY_PARSE_FAILURE_THRESHOLD = 0.02** ->灰度输出解析失败率阈值* **CANARY_METRIC_RUNTIME_FAILURE_THRESHOLD = 0.00** ->指标运行失败阈值* **CANARY_GT_LEAKAGE_THRESHOLD = 0.00** ->GT 泄露容忍阈值* **API_FAILURE_THRESHOLD = 0.05** ->全量 API 响应失败率上限* **API_RETRY_COUNT = 3** ->单个样本 API 调用最大重试次数据* **API_CONCURRENCY = 5** ->全量推理并发请求数据* **SCORE_ANOMALY_IQR_FACTOR = 3.0** ->分数异常检查IQR 阈值* **CONTAMINATION_CHECK = true** ->检查模型输出中的模板GT 泄露信号
* **STAGE_BOUNDARY_STOP = true** ->Stage 5 完成 `STAGE5_SUMMARY.md` 后必须停止，由用户选择下一步；不得自动进入任何后续诊断维护阶段。
* **NO_BENCHCLAW_WRITE = true** ->`BENCHCLAW_ROOT/` 下所有内容只读，严禁增删改。
> Override example: `/benchmark-stage5-eval "gpt-5.5" ->CANARY_SAMPLE_RATIO: 0.05, API_CONCURRENCY: 10`

---

## Pipeline

### Phase 0: Load Context and Verify Prerequisites

在启动任何后续phase 之前
1. 读取 `~/bench_workspace/workspace{i}/stage4/` 目录，确认以下前置产物全部存在：
   * `~/bench_workspace/workspace{i}/stage4/EVALSET_DATASET/`
   * `~/bench_workspace/workspace{i}/stage4/EVALSET_SCHEMA.md`
   * `~/bench_workspace/workspace{i}/stage4/METRIC_SPEC.md`
   * `~/bench_workspace/workspace{i}/stage4/SCORING_RULES.md`
   * `~/bench_workspace/workspace{i}/stage4/METRIC_LIBRARY/`
   * `~/bench_workspace/workspace{i}/stage4/CAPABILITY_METRIC_MAP.md`
   * `~/bench_workspace/workspace{i}/stage4/VALIDATION_REPORT.md`，verdict 必须PASS
   * `~/bench_workspace/workspace{i}/stage4/STAGE4_UNIT_TEST_REPORT.md`，verdict 必须PASS 或带用户确认 waiver
2. 读取 `~/bench_workspace/workspace{i}/stage1/` 目录，确认以下前置产物存在：
   * `~/bench_workspace/workspace{i}/stage1/BENCHMARK_DRAFT.md`
   * `~/bench_workspace/workspace{i}/stage1/EVALSET_PROTOTYPE.md`
   * `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md`
3. 读取 `~/bench_workspace/workspace{i}/stage2/STAGE2_UNIT_TEST_REPORT.md` ->`~/bench_workspace/workspace{i}/stage3/STAGE3_UNIT_TEST_REPORT.md`，作为灰度失败定位的证据4. 定位模型 API 配置：优先读workspace 根目录或 `~/bench_workspace/workspace{i}/stage5/` 下的 `MODEL_API_CONFIG.json`；若缺失`LOCAL_MODEL_API_AWARE = true`，扫`model_api/` 推导 endpoint/model/auth/payload 契约5. 任一阻塞输入缺失时，终止并写入`~/bench_workspace/workspace{i}/stage5/STAGE5_BLOCKED.md`，不得进入灰度或全量评测集
---

### Phase 1: Build Eval System Prompt ->评测 Prompt 与运行配置构
Invoke:

```text
/benchmark-build-eval-system-prompt "$ARGUMENTS"
```

**Expected output:**

* `~/bench_workspace/workspace{i}/stage5/EVAL_SYSTEM_PROMPT.md`
* `~/bench_workspace/workspace{i}/stage5/RUN_CONFIG.json`
* `~/bench_workspace/workspace{i}/stage5/MODEL_API_CONFIG.snapshot.json`

**Checkpoint:** prompt 冒烟测试必须通过，且输出格式可被 Stage 4 metric library 解析；否则停留在 Phase 1 修复
---

### Phase 2: Canary / Gray Evaluation ->全量前灰度评
Invoke:

```text
/benchmark-canary-eval "$STAGE5_DIR"
```

**输入* `EVAL_SYSTEM_PROMPT.md` + `RUN_CONFIG.json` + `~/bench_workspace/workspace{i}/stage4/EVALSET_DATASET/` + `~/bench_workspace/workspace{i}/stage4/METRIC_LIBRARY/`

**执行内容*

* 按能力维度、难度、仿真器、任务类型分层抽取灰度样本* 调用模型 API，记录灰度输出、延迟、失败率、解析成功率、重试次数据* 运行指标库，检查metric runtime、聚合结果、异常值和 GT 泄露* 估算全量评测成本与耗时* 写入 canary verdict
**Expected output:**

* `~/bench_workspace/workspace{i}/stage5/CANARY_SAMPLE_MANIFEST.jsonl`
* `~/bench_workspace/workspace{i}/stage5/CANARY_RAW_OUTPUTS.jsonl`
* `~/bench_workspace/workspace{i}/stage5/CANARY_METRICS.json`
* `~/bench_workspace/workspace{i}/stage5/CANARY_VERDICT.json`
* `~/bench_workspace/workspace{i}/stage5/CANARY_EVAL_REPORT.md`

**🚦 Gate 5A ->Canary Gate**

```text
🐤 Canary evaluation complete:
- Verdict: PASS | FAIL | NEEDS_REVIEW
- API success rate: [...]
- Parse success rate: [...]
- Metric runtime pass rate: [...]
- GT leakage: yes/no
- Estimated full-eval cost/time: [...]

Proceed to full-scale evaluation?
```

* `PASS` ->可以进入 Phase 4 全量评测集* `NEEDS_REVIEW` ->暂停，等待用户确waiver；无 waiver 不得全量* `FAIL` ->必须进入 Phase 3 定位回退；不得执`/benchmark-call-model-api`
---

### Phase 3: Canary Failure Localization and Rollback ->灰度失败定位回退

Only run this phase when `CANARY_VERDICT.json.verdict != PASS`.

Invoke:

```text
/benchmark-canary-localize-rollback "$STAGE5_DIR/CANARY_EVAL_REPORT.md"
```

**执行内容*

* 汇总灰度失败、Stage 1-4 单元测试、Stage 4 dry-run、Stage 5 prompt 冒烟测试证据* 将症状映射到最小回退点：Stage、Phase、Skill、Artifact* 明确哪些下游产物需要废弃并重跑* 写入 pipeline state patch，使父流程进入`rollback_required` 状态
**Expected output:**

* `~/bench_workspace/workspace{i}/stage5/CANARY_ROLLBACK_PLAN.md`
* `~/bench_workspace/workspace{i}/stage5/ROLLBACK_STATE_PATCH.json`

**Stop condition:** Phase 3 完成后，Stage 必须停止；只有按回退计划修复并重跑对应阶段后，才能再次进入Stage 5
---

### Phase 4: Full-Scale Model API Call ->全量模型推理

Invoke only when Canary Gate is `PASS` or user explicitly confirms a documented waiver for `NEEDS_REVIEW`:

```text
/benchmark-call-model-api "$STAGE5_DIR/RUN_CONFIG.json"
```

**Expected output:**

* `~/bench_workspace/workspace{i}/stage5/RAW_MODEL_OUTPUTS.jsonl`
* `~/bench_workspace/workspace{i}/stage5/API_RUN_SUMMARY.json`
* `~/bench_workspace/workspace{i}/stage5/API_FAILURES.jsonl`

**Failure handling:** 若全量失败率超过 `API_FAILURE_THRESHOLD`，暂停全量推理，生成 `FULL_EVAL_ABORT_REPORT.md`，不得继续打分
---

### Phase 5: Run Metrics ->指标打分与聚
Invoke:

```text
/benchmark-run-metrics "$STAGE5_DIR/RAW_MODEL_OUTPUTS.jsonl"
```

**Expected output:**

* `~/bench_workspace/workspace{i}/stage5/SCORES.jsonl`
* `~/bench_workspace/workspace{i}/stage5/AGGREGATED_METRICS.json`
* `~/bench_workspace/workspace{i}/stage5/DIMENSION_WISE_ANALYSIS.md`

---

### Phase 6: Check Scores ->结果质检与报告
Invoke:

```text
/benchmark-check-scores "$STAGE5_DIR/AGGREGATED_METRICS.json"
```

**Expected output:**

* `~/bench_workspace/workspace{i}/stage5/SCORE_CHECK_REPORT.md`
* `~/bench_workspace/workspace{i}/stage5/FAILURE_CASES.md`
* `~/bench_workspace/workspace{i}/stage5/EVALUATION_REPORT.md`

结果质检必须覆盖：异常分数、维度缺口、样本失败聚类、潜在污泄露、API 异常、模型输出格式异常、指标运行异常
---

### Phase 7: Final Summary

Finalize `~/bench_workspace/workspace{i}/stage5/STAGE5_SUMMARY.md`
```markdown
# Stage5 Summary

**Input**: $ARGUMENTS
**Pipeline**: prompt ->canary ->rollback-if-needed ->full inference ->metrics ->score check

## Executive Summary
[灰度结果、是否进入全量、全量评测结果、主要风险]

## Canary Gate
- Report: `CANARY_EVAL_REPORT.md`
- Verdict: PASS | FAIL | NEEDS_REVIEW
- Rollback plan, if any: `CANARY_ROLLBACK_PLAN.md`

## Full Evaluation
- Raw outputs: `RAW_MODEL_OUTPUTS.jsonl`
- Scores: `SCORES.jsonl`
- Aggregated metrics: `AGGREGATED_METRICS.json`
- Report: `EVALUATION_REPORT.md`

## Handoff Notes
- Process-level issues: [...]
- Skill-level suspected issues: [...]
- Version-control revision needed: yes/no
```

If `COMPACT = true`, also write `~/bench_workspace/workspace{i}/stage5/STAGE5_COMPACT.md` for later manual diagnosis or follow-up review.

Stage 5 完成后必须停在这里，展示下一步选项：

1. Start a manual follow-up diagnosis flow
2. Rerun a Stage 5 phase
3. Review canary, full evaluation, scores, failure cases, or rollback plan
4. Pause pipeline

不得自动调用任何已删除或未注册的后续诊断维护 stage。Stage 5 结束后只能停在当前阶段，等待用户显式选择下一步。

---

## Failure Handling

* 灰度 FAIL：必须执`/benchmark-canary-localize-rollback`，然后停止* 灰度 NEEDS_REVIEW：必须等待用户确waiver；否则停止* 全量 API failure：暂停，`FULL_EVAL_ABORT_REPORT.md`，根据错误类型回退 Phase 1 ->API 配置* 指标运行失败：回退 Stage 4 `/benchmark-metric-establish` ->`/benchmark-validate-stage4`* GT 泄露：回退 Stage 4 evalset generation；若来源cleaned data，回退 Stage 3 validation
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

- [ ] `CANARY_EVAL_REPORT.md` 已生成功- [ ] 灰度 PASS 或已记录用户 waiver 后才存在全量 `RAW_MODEL_OUTPUTS.jsonl`- [ ] 全量评测完成时，`EVALUATION_REPORT.md`、`SCORE_CHECK_REPORT.md`、`FAILURE_CASES.md` 均存在- [ ] 灰度失败时，`CANARY_ROLLBACK_PLAN.md` ->`ROLLBACK_STATE_PATCH.json` 均存在，且没有启动全量评测集- [ ] `STAGE5_SUMMARY.md` 明确记录后续处理建议- [ ] Stage 5 完成后已停止，并展示用户可选下一步；未自动调用任何已删除阶段
