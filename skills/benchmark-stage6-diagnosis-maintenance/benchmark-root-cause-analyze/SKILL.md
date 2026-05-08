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

## Completion Criteria

- [ ] 每个 blocking defect 都定位到唯一 primary owner- [ ] 每个 skill 修改候选都有对evidence ->regression check- [ ] 低置信度结论必须标为 hypothesis，不得伪装成确定根因- [ ] 不修改任skill 文件