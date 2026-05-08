---
name: benchmark-skill-surgical-revision
description: "Atomic module: 手术刀skill 修改。只负责根据根因报告和允许修改白名单，对最小数量的 skill 文件做精确规则修改，并输patch/changelog；不负责重新归因、不负责全量评测、不绕过 git 基线。Use when user says '手术刀式修复skill'surgical skill revision'按根因改 skill'."
argument-hint: [skill-fix-candidates]
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

# Benchmark Surgical Skill Revision

Apply minimal skill revisions based on root causes: **$ARGUMENTS**

This skill is an **atomic single-responsibility skill**. It must only edit approved skill files with minimal, evidence-backed changes.

---

## Purpose

- 本模块负责把 `SKILL_FIX_CANDIDATES.md` 中的候选修复落skill 文件- 本模块直接产物是 `~/bench_workspace/workspace{i}/stage6/SKILL_REVISION_PLAN.md`、`~/bench_workspace/workspace{i}/stage6/SKILL_PATCH.diff`、`~/bench_workspace/workspace{i}/stage6/SKILL_CHANGELOG.md`、`~/bench_workspace/workspace{i}/stage6/UPDATED_SKILL_MANIFEST.json`- 本模块不负责新增无关流程、不负责大面积重写、不负责提交 git commit
---

## Inputs

- `$ARGUMENTS`：`~/bench_workspace/workspace{i}/stage6/SKILL_FIX_CANDIDATES.md`- 必需输入->  - `~/bench_workspace/workspace{i}/stage6/SKILL_FIX_CANDIDATES.md`
  - `~/bench_workspace/workspace{i}/stage6/ALLOWED_SKILL_EDIT_LIST.txt`
  - `~/bench_workspace/workspace{i}/stage6/VERSION_CONTROL_LOG.md`
  - `~/bench_workspace/workspace{i}/stage6/ROOT_CAUSE_ANALYSIS.md`
  - `SKILL_REPO_ROOT` 中的目标 `SKILL.md` 文件

allowed edit list 为空或目标文件不在白名单内，必须停止
---

## Procedure

1. **读取修复候*：解fix id、defect id、target skill file、rule gap、surgical change、regression check2. **确认白名*：只允许修改 `ALLOWED_SKILL_EDIT_LIST.txt` 中列出的文件3. **制定修改计划**：写入`SKILL_REVISION_PLAN.md`，说明每个文件改哪一小段、为什么改、如何回归验证4. **执行最小修复*：使`Edit` ->Bash 文本替换，只修改相关规则、阈值、checkpoint、handoff ->completion criteria5. **生成 diff**：运`git diff -- <changed files>`，写入`~/bench_workspace/workspace{i}/stage6/SKILL_PATCH.diff`6. **changelog**：记defect id、修改文件、修改摘要、预期影响、回归测试7. **更新 manifest**：记录修改后 skill 文件 sha256、mtime、大小
---

## Surgical Revision Rules

- 单个 defect 只修改必skill；不得顺手重写整pipeline- 不得修改与根因无关的 stage ->atomic skill- 修改应优先落在：输入契约、质量门、失败处理、回退规则、completion criteria、downstream handoff- 不得删除已有用户自定义规则，除非根因报告明确指出其错误- 每个修改都必须能力`SKILL_CHANGELOG.md` 中追溯到 defect id
---

## Expected Outputs

- `~/bench_workspace/workspace{i}/stage6/SKILL_REVISION_PLAN.md`
- `~/bench_workspace/workspace{i}/stage6/SKILL_PATCH.diff`
- `~/bench_workspace/workspace{i}/stage6/SKILL_CHANGELOG.md`
- `~/bench_workspace/workspace{i}/stage6/UPDATED_SKILL_MANIFEST.json`

`SKILL_CHANGELOG.md` 结构
```markdown
# Skill Changelog

| Fix ID | Defect ID | File | Change Type | Summary | Regression Check |
|--------|-----------|------|-------------|---------|------------------|

## Diff Summary
[git diff --stat]
```

---

## Completion Criteria

- [ ] 只修改白名单skill 文件- [ ] `SKILL_PATCH.diff` 非空且不包含无关文件- [ ] 每个修改都绑defect id ->regression check- [ ] 未执git commit；commit ->Stage 6 orchestrator 在回归通过后处理由