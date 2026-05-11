---
name: benchmark-root-cause-analyze
description: "Atomic module: 流程问题根因定位。只负责把流程评价中的缺陷追溯到 stage/phase/skill/artifact/rule gap，并输出待修 skill 候选；不直接修复skill、不执行 git、不重跑评测。Use when user says '根因分析'定位流程问题'root cause analysis'."
argument-hint: [process-evaluation-report]
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

# Benchmark Root Cause Analysis

Analyze root causes for process defects: **$ARGUMENTS**

This skill is an **atomic single-responsibility skill**. It must only localize root causes and propose minimal skill fix candidates.

---

## Purpose

- 本模块负责把 Stage 6 流程评价中的候选缺陷，追溯到具stage、phase、skill、artifact 和规则缺口- 本模块直接产物是 `~/bench_workspace/workspace{i}/stage6/ROOT_CAUSE_ANALYSIS.md`、`~/bench_workspace/workspace{i}/stage6/DEFECT_TRIAGE_MATRIX.json`、`~/bench_workspace/workspace{i}/stage6/SKILL_FIX_CANDIDATES.md`- 本模块不负责编辑任何 skill 文件
---

## Inputs

- `$ARGUMENTS`：`~/bench_workspace/workspace{i}/stage6/PROCESS_EVALUATION_REPORT.md`- 必需输入->  - `~/bench_workspace/workspace{i}/stage6/PROCESS_EVALUATION_REPORT.md`
  - `~/bench_workspace/workspace{i}/stage6/PROCESS_METRICS.json`
  - Stage 1-4 unit test reports
  - `~/bench_workspace/workspace{i}/stage5/CANARY_EVAL_REPORT.md`
  - `~/bench_workspace/workspace{i}/stage5/CANARY_ROLLBACK_PLAN.md`（若存在->  - `~/bench_workspace/workspace{i}/stage5/EVALUATION_REPORT.md` ->`FAILURE_CASES.md`（若存在
---

## Root Cause Method

对每个defect 执行
1. **Symptom framing**：定义可观测症状，不混同根因2. **Evidence chain**：引用触发该问题的报告、样本、指标、日志3. **Contract comparison**：对照对skill 的输输出契约completion criteria4. **Five Whys / fault tree**：至少分3 层原因；证据不足时标记为 hypothesis5. **Minimal owner selection**：选择最小负责单位：stage ->phase ->skill ->artifact ->rule gap6. **Fix candidate**：只提出最小规则修改，不提出大面积重写入
---

## Expected Outputs

- `~/bench_workspace/workspace{i}/stage6/ROOT_CAUSE_ANALYSIS.md`
- `~/bench_workspace/workspace{i}/stage6/DEFECT_TRIAGE_MATRIX.json`
- `~/bench_workspace/workspace{i}/stage6/SKILL_FIX_CANDIDATES.md`

`ROOT_CAUSE_ANALYSIS.md` 结构
```markdown
# Root Cause Analysis

## Summary
[主要根因]

## Defect Triage Matrix
| Defect ID | Symptom | Root Cause | Stage | Phase | Skill | Artifact | Confidence | Severity |
|-----------|---------|------------|-------|-------|-------|----------|------------|----------|

## Root Cause Details
### RCA-001: [name]
- Symptom: [...]
- Evidence: [...]
- Fault chain: [...]
- Minimal owner: Stage/Phase/Skill/Artifact
- Rule gap: [skill 里缺写错/过宽/过窄的规则]
- Minimal fix: [一句话]
- Regression test: [如何验证]
```

`SKILL_FIX_CANDIDATES.md` 结构
```markdown
# Skill Fix Candidates

| Fix ID | Defect ID | Target Skill File | Current Rule Gap | Surgical Change | Regression Check |
|--------|-----------|-------------------|------------------|------------------|------------------|
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

- [ ] 每个 blocking defect 都定位到唯一 primary owner- [ ] 每个 skill 修改候选都有对evidence ->regression check- [ ] 低置信度结论必须标为 hypothesis，不得伪装成确定根因- [ ] 不修改任skill 文件