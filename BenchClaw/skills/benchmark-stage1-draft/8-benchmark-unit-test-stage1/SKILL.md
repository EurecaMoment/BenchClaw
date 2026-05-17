---
name: benchmark-unit-test-stage1
description: "Atomic module: Stage 1 单元测试。只负责对 Stage 1 的输出契约、内部一致性、可复现性与下游可用性做可重复测试，不负责生成主产物、修复上游设计或执行下游 stage。Use when user says 'stage1 unit test'、'测试 stage1'、'验证 stage1 产物'."
argument-hint: [stage1-dir]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob
metadata:
  openclaw:
    emoji: ""
    requires:
      bins: [python3]
---

## `BENCHCLAW_ROOT` 只读约束

- **BENCHCLAW_READONLY = true**：`BENCHCLAW_ROOT/` 只能作为 BenchClaw 仓库内共享只读资源根，必须从当前 skill 所在的 BenchClaw 仓库位置解析，不能依赖固定 home 路径或机器绝对路径。
- `BENCHCLAW_ROOT` 必须解析为当前 skill 所在 BenchClaw 仓库的根目录；只允许读取该根目录下、且被当前 skill 明确允许的子目录。
- 严禁在 `BENCHCLAW_ROOT/` 下创建、编辑、覆盖、删除、移动、重命名、复制写入、初始化 git、提交、打 tag、写日志、写缓存或写临时文件。
- 所有派生产物、补丁、快照、报告、脚本、配置、日志和测试输出必须写入 active `WORKSPACE_ROOT`。
- 如必须修改 `BENCHCLAW_ROOT/` 中的资源，只能在 workspace 中生成 patch 或修改建议，等待用户在外部处理；当前 skill 不得直接应用。


## Workspace and File Access Boundary

This skill must operate only inside the current run workspace.

- Before reading or writing any run artifact, resolve and record the active `WORKSPACE_ROOT = ~/bench_workspace/workspace{i}` from the current task, parent stage, or pipeline state.
- Read and write only files under the active `WORKSPACE_ROOT` and the explicitly required global resource roots named by this skill, which must stay inside `BENCHCLAW_ROOT/`, such as `BENCHCLAW_ROOT/simulatorCards/`, `BENCHCLAW_ROOT/benchmarkDatasetCards/`, `BENCHCLAW_ROOT/realdata_cards/`, `BENCHCLAW_ROOT/templates/`, `BENCHCLAW_ROOT/model_api/`, `BENCHCLAW_ROOT/data-juicer_card/`, `BENCHCLAW_ROOT/annotation-tool/`, or `BENCHCLAW_ROOT/skills/` when the current skill explicitly requires them.
- Never read, list, grep, summarize, compare, copy, or infer from any other `~/bench_workspace/workspace{j}` where `j != i`, even if the current artifact is missing or another workspace appears newer or more complete.
- Never scan broad server directories such as `~`, `/`, `/home`, `/mnt`, `/data`, `/tmp`, `C:\Users`, `C:\`, or arbitrary project/download folders to discover context. Only inspect the exact current workspace paths and exact allowlisted resource roots needed for this skill.
- If an expected input is missing from the active workspace or an allowlisted resource root, stop and report the missing path. Do not search unrelated folders or borrow replacement artifacts from another workspace.
- Outputs must be written only to the active `WORKSPACE_ROOT` paths declared by this skill. Do not mirror or cache run artifacts into other workspaces or unrelated server folders.
- If the user explicitly provides an external path, use it only when it is directly relevant to this skill, record it as a user-provided exception, and do not expand access to sibling or parent directories.

This boundary overrides convenience behaviors such as auto-discovery, resume from latest workspace, reuse of previous artifacts, broad recursive grep/list, and fallback search.

# Benchmark Stage 1 Unit Test

Execute deterministic unit tests for Stage 1 outputs: **$ARGUMENTS**

This skill is an **atomic single-responsibility skill**. It must only validate Stage 1 artifacts and write machine-readable plus human-readable test reports.

---

## Purpose

- 本模块负责对 Stage 1（草稿生成）的关键产物做单元测试，确认其满足本 stage 内部契约和下游输入契约。
- 本模块位于 Stage 1 的最后一个质量门，直接产物是 `~/bench_workspace/workspace{i}/stage1/STAGE1_UNIT_TEST_REPORT.md`。
- 本模块不负责生成 Stage 1 主产物、不负责修改 skill、不负责运行下游 stage。
- 本模块必须给出明确 verdict：`PASS`、`FAIL` 或 `NEEDS_REVIEW`。

---

## Inputs

- `$ARGUMENTS`：Stage 1 目录路径；若为空，默认使用当前 workspace 的 `~/bench_workspace/workspace{i}/stage1/`。
- 必需输入：
  - `~/bench_workspace/workspace{i}/stage1/IDEA_TARGET.md`
  - `~/bench_workspace/workspace{i}/stage1/LITERATURE_REVIEW.md`
  - `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md`
  - `~/bench_workspace/workspace{i}/stage1/DATA_SOURCE_MAPPING.md`
  - `~/bench_workspace/workspace{i}/stage1/data_source_selection/SIMULATOR_MAPPING.md`
  - `~/bench_workspace/workspace{i}/stage1/data_source_selection/DATASET_MAPPING.md`
  - `~/bench_workspace/workspace{i}/stage1/data_source_selection/REALDATA_MAPPING.md`
  - `~/bench_workspace/workspace{i}/stage1/EVALSET_PROTOTYPE.md`
  - `~/bench_workspace/workspace{i}/stage1/BENCHMARK_DRAFT.md`
  - `~/bench_workspace/workspace{i}/stage1/EXECUTION_PLAN.md`
- 上游依赖：
  - 无上游 stage；只依赖用户原始 idea 与可选资源目录。

若任一必需输入缺失，立即停止主测试，写入 FAIL 报告，并列出缺失路径。

---

## Procedure

1. **定位 workspace**：根据 `$ARGUMENTS` 或最近的 `~/bench_workspace/workspace{i}/stage1/` 定位待测目录。
2. **生成测试脚本**：写入 `~/bench_workspace/workspace{i}/stage1/unit_tests/test_stage1_contract.py`，测试必须离线、确定性、可重复运行。
3. **执行契约测试**：至少覆盖以下测试项：

- 关键产物存在且非空；文档标题和核心章节完整。
- 能力维度有 ID、操作性定义、可测 GT 信号、任务类型示例，且维度之间无明显重复。
- `CAPABILITY_SCOPE.md`、`EVALSET_PROTOTYPE.md`、`BENCHMARK_DRAFT.md`、`EXECUTION_PLAN.md` 中维度编号和名称可对齐。
- `DATA_SOURCE_MAPPING.md` 与 `data_source_selection/SIMULATOR_MAPPING.md`、`data_source_selection/DATASET_MAPPING.md`、`data_source_selection/REALDATA_MAPPING.md` 中维度映射一致，且每个必须覆盖的维度至少映射到一个 simulator / dataset / real-world 数据来源，或显式 waiver。
- 检查 `SIMULATOR_MAPPING.md`、`DATASET_MAPPING.md`、`REALDATA_MAPPING.md` 不得直接出现在 `stage1/` 根目录；它们只能位于 `stage1/data_source_selection/`。
- `BENCHMARK_DRAFT.md` 必须在数据构造章节中为每个选定数据源列出计划采集数量与单位。
- Stage 2 能从执行计划中读出按数据源拆分的采集目标、数据 schema 预期、模板种子和最低采集规模。
- `BENCHMARK_DRAFT.md` 与 `EXECUTION_PLAN.md` 中按数据源列出的计划采集数量不得相互冲突。

4. **记录机器可读结果**：写入 `~/bench_workspace/workspace{i}/stage1/unit_tests/results.json`，每条测试记录 `id`、`status`、`evidence`、`blocking`、`fix_target`。
5. **生成报告**：写入 `~/bench_workspace/workspace{i}/stage1/STAGE1_UNIT_TEST_REPORT.md`。
6. **更新阶段摘要**：在 `~/bench_workspace/workspace{i}/stage1/STAGE1_SUMMARY.md` 中追加单元测试 verdict 和阻塞项；若摘要不存在，不创建主摘要，只在报告中说明。

---

## Rollback Target Map

当测试失败时，必须使用以下映射给出精确回退目标：

- 目标定义不清 → Stage 1 Phase 1 `/idea-target-refine`
- 文献证据不足 → Stage 1 Phase 2 `/benchmark-literature-survey`
- 维度缺失/重叠 → Stage 1 Phase 3 `/benchmark-capability-scope`
- 数据源不可实现 → Stage 1 Phase 4 `/benchmark-data-source-selection`
- 原型与维度不一致 → Stage 1 Phase 5 `/benchmark-evalset-prototype-gen`
- 执行计划不可操作 → Stage 1 Phase 7 `/benchmark-execution-plan-gen`

---

## Expected Outputs

- `~/bench_workspace/workspace{i}/stage1/unit_tests/test_stage1_contract.py`
- `~/bench_workspace/workspace{i}/stage1/unit_tests/results.json`
- `~/bench_workspace/workspace{i}/stage1/STAGE1_UNIT_TEST_REPORT.md`

`STAGE1_UNIT_TEST_REPORT.md` 必须包含：

```markdown
# Stage 1 Unit Test Report

**Stage**: 1 — 草稿生成
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

- [ ] `STAGE1_UNIT_TEST_REPORT.md` exists and has exactly one verdict.
- [ ] `unit_tests/results.json` is valid JSON and includes every test ID.
- [ ] Any FAIL verdict names the exact artifact and rerun target.
- [ ] Tests do not mutate Stage 1 main artifacts.
- [ ] The parent stage summary references the unit test verdict when available.

---

## Rules

- 不为了通过测试而改写主产物。
- 不把 warning 隐藏为 PASS；warning 必须有证据和后续影响说明。
- 对不可判定项使用 `NEEDS_REVIEW`，并说明缺少什么证据。
- 如果 Write 因文件过大失败，立即 fallback 到 Bash（`cat << 'EOF' > file`）分块写入。

---

## Downstream Handoff

- 父级 stage orchestrator 读取本报告的 verdict 决定是否进入下一 stage。
- Stage 5 灰度评测定位回退时，读取 Stage 1-4 的单元测试报告作为优先证据。
- 后续若需要独立根因分析，可读取本报告中的 `Required Fix Target` 建立流程缺陷矩阵。
