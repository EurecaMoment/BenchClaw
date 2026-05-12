---
name: benchmark-unit-test-stage4
description: "Atomic module: Stage 4 单元测试。只负责Stage 4 的输出契约、内部一致性、可复现性与下游可用性做可重复测试，不负责生成主产物、修复上游设计或执行下游 stage。Use when user says 'stage4 unit test'测试 stage4'验证 stage4 产物'."
argument-hint: [stage4-dir]
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

# Benchmark Stage 4 Unit Test

Execute deterministic unit tests for Stage 4 outputs: **$ARGUMENTS**

This skill is an **atomic single-responsibility skill**. It must only validate Stage 4 artifacts and write machine-readable plus human-readable test reports.

---

## Critical Hotfix: Stage 4 Unit Tests Must Catch Missing Scorers

The unit-test module must fail Stage 4 when metrics are declared but not
implemented. Add deterministic contract tests for:

- `METRIC_LIBRARY/metrics/` is non-empty and contains one `.py` file per
  declared metric.
- `METRIC_LIBRARY/aggregators/` is non-empty and contains dimension plus overall
  aggregation implementations.
- `METRIC_LIBRARY/tests/` is non-empty and the tests pass.
- `METRIC_LIBRARY/interfaces.py` can be imported.
- `tools/evaluate_evalset.py` exists and runs in smoke-test mode against a small
  synthetic or sampled GT-copy output set.
- Declared template `downstream_metrics` such as `D_acc_short_answer`,
  `per_source_acc`, `refusal_rate`, and `response_length_mean` resolve to
  executable metric or aggregator code.

If any of these fail, `STAGE4_UNIT_TEST_REPORT.md` verdict must be `FAIL`, with
fix target `Stage 4 Phase 2 /benchmark-metric-establish`. Do not classify this
as `NEEDS_REVIEW` or waiver unless the user explicitly accepts a benchmark that
cannot be automatically scored.

## Critical Hotfix: Unit Tests Must Catch Ungrounded Questions

The generated `unit_tests/test_stage4_contract.py` must include deterministic
question-quality tests:

- All templates contain `quality_constraints`.
- All official samples contain `grounding_check.verdict=PASS`.
- Non-`text_only_allowed` samples have at least one required observation file.
- Normalized GT strings and aliases do not appear in `input/instruction.txt`,
  answer options, public metadata, file names, or visible paths.
- Multiple-choice options do not have obvious pattern giveaways such as only one
  option with a unique type, length, coordinate format, or copied metadata token.
- A text-only baseline check is recorded; non-text tasks expected to be solvable
  without observation force verdict `FAIL`.

Failures in these tests must target `Stage 4 Phase 1
/benchmark-evalset-generate`, not the metric phase.

## Critical Hotfix: Unit Tests Must Catch Invalid HuggingFace Evalset Layout

The generated `unit_tests/test_stage4_contract.py` must include deterministic
filesystem and schema tests for the final evalset folder:

- `EVALSET_DATASET/` contains `README.md`, `dataset_info.json`, `data.jsonl`,
  `manifest.json`, `statistics.json`, and `gt_generators/`.
- `data.jsonl` is valid JSONL and every row uses relative paths.
- Every row has required fields: `question_id`, `source_type`, `source_name`,
  `capability_dimension`, `question_dir`, `images`, `question_path`,
  `answer_path`, `ground_truth_path`, `gt_generator_file`,
  `gt_generator_function`, `metadata_path`, `template_id`, `metric_ids`, and
  `split`.
- Every question folder path follows
  `{source_type}/{source_name}/{capability_dimension}/{question_id}/`.
- Every question folder contains `images/`, `question.json`, `question.md`,
  `answer.json`, `ground_truth.json`, `gt_code_ref.json`, and `metadata.json`.
- Every referenced image exists under the local question `images/` directory and
  is named `image_0001.{ext}`, `image_0002.{ext}`, etc.
- Every `gt_code_ref.json` points to an existing GT generator file under
  `EVALSET_DATASET/gt_generators/`.

Failures in these tests must target `Stage 4 Phase 1
/benchmark-evalset-generate`.

---

## Purpose

- 本模块负责对 Stage 4（评测集合成与协议设计）的关键产物做单元测试，确认其满足stage 内部契约和下游输入契约- 本模块位Stage 4 的最后一个质量门，直接产物是 `~/bench_workspace/workspace{i}/stage4/STAGE4_UNIT_TEST_REPORT.md`- 本模块不负责生成 Stage 4 主产物、不负责修改 skill、不负责运行下游 stage- 本模块必须给出明verdict：`PASS`、`FAIL` ->`NEEDS_REVIEW`
---

## Inputs

- `$ARGUMENTS`：Stage 4 目录路径；若为空，默认使用当前workspace ->`~/bench_workspace/workspace{i}/stage4/`- 必需输入->  - `~/bench_workspace/workspace{i}/stage4/EVALSET_TEMPLATE_LIBRARY/`
  - `~/bench_workspace/workspace{i}/stage4/EVALSET_SYNTHESIS_RULES.md`
  - `~/bench_workspace/workspace{i}/stage4/EVALSET_DATASET/`
  - `~/bench_workspace/workspace{i}/stage4/EVALSET_SCHEMA.md`
  - `~/bench_workspace/workspace{i}/stage4/CAPABILITY_METRIC_MAP.md`
  - `~/bench_workspace/workspace{i}/stage4/METRIC_SPEC.md`
  - `~/bench_workspace/workspace{i}/stage4/SCORING_RULES.md`
  - `~/bench_workspace/workspace{i}/stage4/METRIC_LIBRARY/`
  - `~/bench_workspace/workspace{i}/stage4/VALIDATION_REPORT.md`
  - `~/bench_workspace/workspace{i}/stage4/DRY_RUN_RESULTS.md`
- 上游依赖->  - `~/bench_workspace/workspace{i}/stage3/final/STAGE4_INPUT_MANIFEST.jsonl`
  - `~/bench_workspace/workspace{i}/stage3/final/cleaned_data/`
  - `~/bench_workspace/workspace{i}/stage3/final/CLEANED_DATA_SCHEMA.md`
  - `~/bench_workspace/workspace{i}/stage3/final/CLEANING_LINEAGE.jsonl`
  - `~/bench_workspace/workspace{i}/stage3/STAGE3_UNIT_TEST_REPORT.md` verdict 应为 PASS 或带 waiver
若任一必需输入缺失，立即停止主测试，写入FAIL 报告，并列出缺失路径
---

## Procedure

1. **定位 workspace**：根`$ARGUMENTS` 或最近的 `~/bench_workspace/workspace{i}/stage4/` 定位待测目录2. **生成测试脚本**：写入`~/bench_workspace/workspace{i}/stage4/unit_tests/test_stage4_contract.py`，测试必须离线、确定性、可重复运行3. **执行契约测试**：至少覆盖以下测试项
- 评测集schema、manifest、样本目录与 metric library 输入契约一致- 能力维度到任务模板、样本、GT、指标至少存在一条完整链路- 指标库可对抽样样deterministic dry-run，并产生可复现聚合结果- 评测输入不暴GT 答案、评分公式、内部路径或不可给模型看的元数据- 样本分布满足覆盖度、难度分布、仿真器平衡和去重要求- `VALIDATION_REPORT.md` verdict ->PASS；否则必须给出阻塞原因和回退目标
4. **记录机器可读结果**：写入`~/bench_workspace/workspace{i}/stage4/unit_tests/results.json`，每条测试记`id`、`status`、`evidence`、`blocking`、`fix_target`5. **生成报告**：写入`~/bench_workspace/workspace{i}/stage4/STAGE4_UNIT_TEST_REPORT.md`6. **更新阶段摘要**：在 `~/bench_workspace/workspace{i}/stage4/STAGE4_SUMMARY.md` 中追加单元测verdict 和阻塞项；若摘要不存在，不创建主摘要，只在报告中说明
---

## Rollback Target Map

当测试失败时，必须使用以下映射给出精确回退目标
- 合成规则不合Stage 4 Phase 1 `/benchmark-evalset-generate`
- schema/manifest 不一Stage 4 Phase 1 `/benchmark-evalset-generate`
- 指标不可运行或不稳定 ->Stage 4 Phase 2 `/benchmark-metric-establish`
- dry-run 失败 ->Stage 4 Phase 3 `/benchmark-validate-stage4`
- Stage4 输入 manifest 或 cleaned data 字段不足 ->回退 Stage 3 Phase 5 `/benchmark-cleaning-validate`

---

## Expected Outputs

- `~/bench_workspace/workspace{i}/stage4/unit_tests/test_stage4_contract.py`
- `~/bench_workspace/workspace{i}/stage4/unit_tests/results.json`
- `~/bench_workspace/workspace{i}/stage4/STAGE4_UNIT_TEST_REPORT.md`

`STAGE4_UNIT_TEST_REPORT.md` 必须包含
```markdown
# Stage 4 Unit Test Report

**Stage**: 4 ->评测集合成与协议设计
**Date**: [today]
**Verdict**: PASS | FAIL | NEEDS_REVIEW

## Tested Artifacts
[artifact list]

## Test Matrix
| Test ID | Contract | Method | Result | Evidence | Blocking | Fix Target |
|---------|----------|--------|--------|----------|----------|------------|
| ...     | ...      | ...    | ...    | ...      | yes/no   | stage/phase/skill |

## Blocking Failures
- [failure or none]

## Warnings
- [warning or none]

## Required Fix Target
- Stage: [...]
- Phase: [...]
- Skill: [...]
- Artifact: [...]
- Reason: [...]

## Downstream Handoff
- Safe to proceed: yes/no
- Required waiver, if any: [...]
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

- [ ] `STAGE4_UNIT_TEST_REPORT.md` exists and has exactly one verdict.
- [ ] `unit_tests/results.json` is valid JSON and includes every test ID.
- [ ] Tests include metric-library non-empty checks and declared-metric implementation checks.
- [ ] Tests import metric interfaces and run at least one scoring smoke test.
- [ ] Missing metric implementations force verdict `FAIL`.
- [ ] Tests include observation-grounding, GT leakage, and text-only baseline checks.
- [ ] Tests include HuggingFace root files, `data.jsonl`, per-question folders, numbered images, and GT generator reference checks.
- [ ] Ungrounded or leaked questions force verdict `FAIL` with Phase 1 fix target.
- [ ] Any FAIL verdict names the exact artifact and rerun target.
- [ ] Tests do not mutate Stage 4 main artifacts.
- [ ] The parent stage summary references the unit test verdict when available.

---

## Rules

- 不为了通过测试而改写主产物- 不把 warning 隐藏PASS；warning 必须有证据和后续影响说明- 对不可判定项使用 `NEEDS_REVIEW`，并说明缺少什么证据- 如果 Write 因文件过大失败，立即 fallback ->Bash（`cat << 'EOF' > file`）分块写入
---

## Downstream Handoff

- 父级 stage orchestrator 读取本报告的 verdict 决定是否进入下一 stage- Stage 5 灰度评测定位回退时，读取 Stage 1-4 的单元测试报告作为优先证据- Stage 6 根因分析读取本报告中`Required Fix Target` 建立流程缺陷矩阵
