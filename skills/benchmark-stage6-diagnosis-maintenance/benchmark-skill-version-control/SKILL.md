---
name: benchmark-skill-version-control
description: "Atomic module: skill 库版本控制基线。只负责git 初始检查skill 库、创建修订分支、记baseline、生成版本控制日志，不负责判断根因、不负责编辑 skill 内容。Use when user says '用版本控制管skill'git baseline'skill version control'."
argument-hint: [skill-repo-root]
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

# Benchmark Skill Version Control

Prepare git version control baseline for skill maintenance: **$ARGUMENTS**

This skill is an **atomic single-responsibility skill**. It must only manage version-control setup and logs.

---

## Purpose

- 本模块负责在修改 skill 前建git baseline、修订分支和变更白名单- 本模块直接产物是 `~/bench_workspace/workspace{i}/stage6/VERSION_CONTROL_LOG.md`、`~/bench_workspace/workspace{i}/stage6/SKILL_BASELINE_MANIFEST.json`、`~/bench_workspace/workspace{i}/stage6/GIT_BASELINE.diff`- 本模块不负责编辑 skill 内容
---

## Inputs

- `$ARGUMENTS`：skill 仓库根目录；默认 `~/benchclaw/skills`- 必需输入->  - skill repo root 下的 `*/SKILL.md` 文件->  - `~/bench_workspace/workspace{i}/stage6/SKILL_FIX_CANDIDATES.md`
---

## Procedure

1. **定位仓库**：确`$SKILL_REPO_ROOT` 存在，包skill 目录`SKILL.md`2. **检查git 状态*->   ```bash
   cd "$SKILL_REPO_ROOT"
   git rev-parse --is-inside-work-tree || git init
   git status --short
   ```
3. **保存未提交改*：若已有 dirty worktree，先写入 `~/bench_workspace/workspace{i}/stage6/GIT_BASELINE.diff`，并在日志中提醒用户确认；不得覆盖用户改动4. **创建 baseline manifest**：记录所有`SKILL.md` 的路径、大小、mtime、sha2565. **创建修订分支**->   ```bash
   git checkout -b benchclaw/revision/<workspace_id>-<timestamp>
   ```
   若分支已存在，则追加hash 后缀6. **生成允许修改白名*：从 `SKILL_FIX_CANDIDATES.md` 提取目标 skill 文件，写入`~/bench_workspace/workspace{i}/stage6/ALLOWED_SKILL_EDIT_LIST.txt`7. **写入版本控制日志**
---

## Expected Outputs

- `~/bench_workspace/workspace{i}/stage6/VERSION_CONTROL_LOG.md`
- `~/bench_workspace/workspace{i}/stage6/SKILL_BASELINE_MANIFEST.json`
- `~/bench_workspace/workspace{i}/stage6/GIT_BASELINE.diff`
- `~/bench_workspace/workspace{i}/stage6/ALLOWED_SKILL_EDIT_LIST.txt`

`VERSION_CONTROL_LOG.md` 必须包含
```markdown
# Version Control Log

## Repository
- Root: [...]
- Git initialized: yes/no
- Baseline commit: [...]
- Branch: [...]
- Dirty worktree before revision: yes/no

## Allowed Edit List
[skill files]

## Safety Notes
[existing user changes, if any]
```

---

## Completion Criteria

- [ ] skill repo 已确认或初始化为 git 仓库- [ ] 已创确认修订分支- [ ] baseline manifest 存在- [ ] allowed edit list 只包含根因报告指向的 skill 文件