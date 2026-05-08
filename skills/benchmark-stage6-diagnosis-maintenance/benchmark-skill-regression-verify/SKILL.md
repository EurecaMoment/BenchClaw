---
name: benchmark-skill-regression-verify
description: "Atomic module: skill 修改回归验证。只负责对被修改 skill 做静态契约检查、模板一致性检查和相关阶段回归计划验证，不负责继续修改 skill、不负责提交 git、不负责重新跑全部benchmark。Use when user says '验证 skill 修改'skill regression'回归测试 skill'."
argument-hint: [skill-patch-diff]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob
metadata:
  openclaw:
    emoji: ""
    requires:
      bins: [git, python3]
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

# Benchmark Skill Regression Verification

Verify modified skills after surgical revision: **$ARGUMENTS**

This skill is an **atomic single-responsibility skill**. It must only validate the skill changes and produce regression reports.

---

## Purpose

- 本模块负责验证手术刀skill 修改不会破坏模板规范、frontmatter、I/O 契约、回退链路和相关单元测试计划- 本模块直接产物是 `~/bench_workspace/workspace{i}/stage6/SKILL_REGRESSION_REPORT.md`、`~/bench_workspace/workspace{i}/stage6/REGRESSION_COMMANDS.sh`、`~/bench_workspace/workspace{i}/stage6/REGRESSION_RESULTS.json`- 本模块不负责继续编辑 skill，不负责 git commit
---

## Inputs

- `$ARGUMENTS`：`~/bench_workspace/workspace{i}/stage6/SKILL_PATCH.diff`- 必需输入->  - `~/bench_workspace/workspace{i}/stage6/SKILL_PATCH.diff`
  - `~/bench_workspace/workspace{i}/stage6/SKILL_CHANGELOG.md`
  - `~/bench_workspace/workspace{i}/stage6/UPDATED_SKILL_MANIFEST.json`
  - 修改后的目标 `SKILL.md` 文件
  - 模板参考文件：`TEMPLATE_L1_pipeline_orchestrator.md`、`TEMPLATE_L2_stage_orchestrator.md`、`TEMPLATE_L3_atomic_skill.md`（若可用
---

## Regression Checks

至少执行以下检查：

1. **Frontmatter check**：每个修改后续`SKILL.md` 仍有 `name`、`description`、`argument-hint`、`allowed-tools`2. **Role boundary check**：orchestrator 仍只调度，不重写 atomic skill 逻辑；atomic skill 仍单一职责3. **I/O contract check**：新增或修改的产物路径在 upstream/downstream handoff 中一致4. **Failure handling check**：灰度失败、单元测试失败、Stage 6 回归失败都有明确停止条件5. **Version-control safety check**：diff 只包allowed edit list 中的 skill 文件6. **Template consistency check**：结构仍符合 L1/L2/L3 模板的关键段落7. **Regression command generation**：写出后续人自动重跑命令，包括相stage unit test、canary eval ->Stage 6 根因分析
---

## Expected Outputs

- `~/bench_workspace/workspace{i}/stage6/SKILL_REGRESSION_REPORT.md`
- `~/bench_workspace/workspace{i}/stage6/REGRESSION_COMMANDS.sh`
- `~/bench_workspace/workspace{i}/stage6/REGRESSION_RESULTS.json`

`SKILL_REGRESSION_REPORT.md` 结构
```markdown
# Skill Regression Report

**Verdict**: PASS | FAIL | NEEDS_REVIEW

## Changed Files
[files]

## Regression Matrix
| Check ID | Scope | Method | Result | Evidence |
|----------|-------|--------|--------|----------|

## Required Follow-up
[if any]

## Commit Readiness
- Safe to commit: yes/no
- Reason: [...]
```

---

## Completion Criteria

- [ ] 报告 verdict 明确- [ ] 每个修改文件至少通过 frontmatter、role boundary、I/O contract 检查- [ ] `REGRESSION_COMMANDS.sh` 包含可执行的后续验证命令- [ ] ->verdict 不是 PASS，明确禁git commit