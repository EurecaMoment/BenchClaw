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
- Stage 2 能从执行计划中读出采集目标、数据 schema 预期、模板种子和最低采集规模。

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
- Stage 6 根因分析读取本报告中的 `Required Fix Target` 建立流程缺陷矩阵。
