---
name: benchmark-process-evaluate
description: "Atomic module: 全流程质量评价。只负责汇Stage 1-5 的产物、单元测试、灰度评测、全量评测和失败案例，计算流程质量指标并形成流程评价报告；不负责根因归因、不修改 skill、不执行版本控制。Use when user says '评价整个流程'process evaluation'流程质量报告'."
argument-hint: [workspace-root]
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

# Benchmark Process Evaluation

Evaluate the end-to-end benchmark construction process for: **$ARGUMENTS**

This skill is an **atomic single-responsibility skill**. It must only evaluate process quality and produce process-level metrics.

---

## Purpose

- 本模块负责对 Stage 1-5 的执行过程做全面质量评价- 本模块直接产物是 `~/bench_workspace/workspace{i}/stage6/PROCESS_EVALUATION_REPORT.md` ->`~/bench_workspace/workspace{i}/stage6/PROCESS_METRICS.json`- 本模块不负责根因归因、不负责修改 skill、不负责重新评测模型
---

## Inputs

- `$ARGUMENTS`：workspace 根目录；若为空，默认使用最`~/bench_workspace/workspace{i}/`- 必需输入->  - `pipeline_state.json`
  - `pipeline_summary.md`
  - `~/bench_workspace/workspace{i}/stage1/STAGE1_UNIT_TEST_REPORT.md`
  - `~/bench_workspace/workspace{i}/stage2/STAGE2_UNIT_TEST_REPORT.md`
  - `~/bench_workspace/workspace{i}/stage3/STAGE3_UNIT_TEST_REPORT.md`
  - `~/bench_workspace/workspace{i}/stage4/STAGE4_UNIT_TEST_REPORT.md`
  - `~/bench_workspace/workspace{i}/stage5/CANARY_EVAL_REPORT.md`
- 条件输入->  - `~/bench_workspace/workspace{i}/stage5/EVALUATION_REPORT.md`：全量评测完成时必需求  - `~/bench_workspace/workspace{i}/stage5/CANARY_ROLLBACK_PLAN.md`：灰度失败时必需求
---

## Process Metrics

必须评估以下指标
| Metric Family | Required Metrics |
|---------------|------------------|
| Contract quality | 每阶段必需产物完整率、schema 一致率、cross-reference broken count |
| Unit-test effectiveness | Stage 1-4 单元测试 verdict、warning 密度、拦截问题数据|
| Data quality | Stage 2 采集成功率、GT 对齐率、缺失率、Stage 3 清洗保留拒绝原因分布 |
| Coverage | 能力维度覆盖率、样本均衡性、难度分布、仿真器覆盖 |
| Evaluation readiness | Stage 4 dry-run 通过率、metric determinism、GT leakage check |
| Canary effectiveness | 灰度 API 成功率、解析成功率、metric runtime、是否阻断了全量风险 |
| Full-eval stability | API 失败率、重试率、格式错误率、score anomaly rate |
| Cost/reproducibility | token/API 成本、耗时、随机种子、manifest/lineage 完整|
| Diagnostic power | 失败案例是否可定位到能力维度、样本、数据源和流程环境|

---

## Procedure

1. **收集证据**：读Stage 1-5 summary、unit test、canary、full eval、failure cases2. **抽取指标**：从 markdown、json、jsonl 中提取定义定性指标；无法提取时标记为 `unknown`3. **形成评分**：对每个 metric family 给出 `PASS`、`WARN`、`FAIL` 和证据4. **识别流程风险**：列出被单元测试遗漏但被灰度/全量发现的问题5. **写入报告**：生成`PROCESS_EVALUATION_REPORT.md` ->`PROCESS_METRICS.json`
---

## Expected Outputs

- `~/bench_workspace/workspace{i}/stage6/PROCESS_EVALUATION_REPORT.md`
- `~/bench_workspace/workspace{i}/stage6/PROCESS_METRICS.json`

报告结构
```markdown
# Process Evaluation Report

## Executive Verdict
PASS | WARN | FAIL | INCOMPLETE

## Evidence Inventory
[读取到的产物与缺失项]

## Metric Dashboard
| Family | Metric | Value | Verdict | Evidence |
|--------|--------|-------|---------|----------|

## Cross-Stage Findings
[跨阶段问题]

## Unit-Test and Canary Effectiveness
[哪些问题被拦截，哪些没被拦截]

## Candidate Process Defects
| Defect ID | Symptom | Evidence | Suspected Stage | Severity |
|-----------|---------|----------|-----------------|----------|

## Handoff to Root Cause Analysis
[需要继续归因的问题列表]
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

- [ ] 报告覆盖 Stage 1-5- [ ] 每个 metric family 至少有一verdict- [ ] 明确列出候选流程缺陷，不直接断言根因- [ ] `PROCESS_METRICS.json` 可解析，包含 metric family、value、verdict、evidence_path