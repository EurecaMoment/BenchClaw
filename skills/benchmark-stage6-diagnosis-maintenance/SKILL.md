---
name: benchmark-stage6-diagnosis-maintenance
description: "Stage 6 子流程：流程全面评价、根因定位与版本skill 维护。编排benchmark-process-evaluate ->benchmark-root-cause-analyze ->benchmark-skill-version-control ->benchmark-skill-surgical-revision ->benchmark-skill-regression-verify，对 Stage 1-5 运行过程、单元测试、灰度评测、全量评测和失败案例做全流程诊断，并git 进行手术刀skill 修改与回归验证。Use when user says '开始stage6'反思机全面评价流程'定位根因并修复skill'skill revision'."
argument-hint: [workspace-or-stage5-dir]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, WebSearch, WebFetch, Skill
metadata:
  openclaw:
    emoji: ""
    requires:
      bins: [python3, git]
---

## `~/benchclaw` 只读约束

- **BENCHCLAW_READONLY = true**：`~/benchclaw/` 只能作为共享只读资源根。
- 严禁在 `~/benchclaw/` 下创建、编辑、覆盖、删除、移动、重命名、复制写入、初始化 git、提交、打 tag、写日志、写缓存或写临时文件。
- 所有派生产物、补丁、快照、报告、脚本、配置、日志和测试输出必须写入 active `WORKSPACE_ROOT`。
- 如必须修改 `~/benchclaw/` 中的资源，只能在 workspace 中生成 patch 或修改建议，等待用户在外部处理；当前 skill 不得直接应用。


## Workspace and File Access Boundary

This skill must operate only inside the current run workspace.

- Before reading or writing any run artifact, resolve and record the active `WORKSPACE_ROOT = ~/bench_workspace/workspace{i}` from the current task, parent stage, or pipeline state.
- Read and write only files under the active `WORKSPACE_ROOT`. The explicitly required global resource roots named by this skill, such as `~/benchclaw/simulator_cards/`, `~/benchclaw/dataset_cards/`, `~/benchclaw/realdata_cards/`, `~/benchclaw/templates/`, `~/benchclaw/model_api/`, `~/benchclaw/data-juicer_card/`, `~/benchclaw/annotation-tool/`, or `~/benchclaw/skills/`, are read-only inputs.
- Never create, edit, overwrite, delete, move, rename, copy files into, initialize git state in, commit, tag, cache, or log under any path inside `~/benchclaw/`.
- Never read, list, grep, summarize, compare, copy, or infer from any other `~/bench_workspace/workspace{j}` where `j != i`, even if the current artifact is missing or another workspace appears newer or more complete.
- Never scan broad server directories such as `~`, `/`, `/home`, `/mnt`, `/data`, `/tmp`, `C:\Users`, `C:\`, or arbitrary project/download folders to discover context. Only inspect the exact current workspace paths and exact allowlisted resource roots needed for this skill.
- If an expected input is missing from the active workspace or an allowlisted resource root, stop and report the missing path. Do not search unrelated folders or borrow replacement artifacts from another workspace.
- Outputs must be written only to the active `WORKSPACE_ROOT` paths declared by this skill. Do not mirror or cache run artifacts into other workspaces or unrelated server folders.
- If the user explicitly provides an external path, use it only when it is directly relevant to this skill, record it as a user-provided exception, and do not expand access to sibling or parent directories.

This boundary overrides convenience behaviors such as auto-discovery, resume from latest workspace, reuse of previous artifacts, broad recursive grep/list, and fallback search.

# Benchmark Stage 6: Diagnosis, Reflection, Revision, and Maintenance

Orchestrate Stage 6 full-process evaluation and version-controlled skill maintenance for: **$ARGUMENTS**

This skill is an **orchestrator only**. It must not re-implement atomic skill logic.

## Overview

```text
STAGE1-5 artifacts + unit tests + canary/full eval reports
->/benchmark-process-evaluate
->/benchmark-root-cause-analyze
->/benchmark-skill-version-control
->/benchmark-skill-surgical-revision
->/benchmark-skill-regression-verify
Stage 6 maintenance summary
(全流程评->  (根因定位)  (git版本控制)  (手术刀式skill修改)  (回归验证)
```

Stage 6 的核心目标不是再评测模型，而是评测**流程本身**：哪里设计得差、哪里造成缺陷、哪些skill 的规则需要最小化修改
## Workspace

所有诊断与维护产出写入
```text
~/bench_workspace/workspace{i}/stage6/
```

Skill 源码仓库默认位置只作为只读诊断对象
```text
SKILL_REPO_ROOT = ~/benchclaw/skills
```

若用户或父流程提供其它非 `~/benchclaw/` 的 skill 根目录，以显式路径为准。只要目标路径位于 `~/benchclaw/` 下，Stage 6 就不得直接修改，只能在 `WORKSPACE_ROOT/stage6/` 生成 patch、changelog、revision plan 和手工应用说明。
## Constants

* **AUTO_PROCEED = false** ->默认需要用户确认后执行 skill 源码修改* **HUMAN_CHECKPOINT = true** ->根因报告和修改计划必须展示给用户* **VERSION_CONTROL_REQUIRED = true** ->修改 skill 前必须存储git baseline* **SKILL_REPO_ROOT = ~/benchclaw/skills** ->skill 库根目录* **REVISION_BRANCH_PREFIX = benchclaw/revision** ->自动创建修订分支前缀* **MAX_SURGICAL_FILES = 6** ->单轮手术刀式修改最多触碰的 skill 文件数据* **REQUIRE_DIFF_REVIEW = true** ->修改后必须生成patch/diff 供审查* **REGRESSION_REQUIRED = true** ->修改后必须执行静态回归和相关 stage 单元测试计划* **COMPACT = false** ->`true` 时写入`STAGE6_COMPACT.md`
* **STAGE_BOUNDARY_STOP = true** ->Stage 6 完成 `STAGE6_SUMMARY.md` 后必须停止，由用户选择下一步；不得自动发布、合并或启动新 pipeline。
* **NO_BENCHCLAW_WRITE = true** ->`~/benchclaw/` 下所有内容只读，严禁增删改；若修复目标位于 `~/benchclaw/`，只能产出 patch 到 workspace，不能直接应用。
---

## Pipeline

### Phase 0: Load Full Pipeline Context

读取并校验以下产物：

* `pipeline_state.json`
* `pipeline_summary.md`
* `~/bench_workspace/workspace{i}/stage1/STAGE1_SUMMARY.md` ->`~/bench_workspace/workspace{i}/stage1/STAGE1_UNIT_TEST_REPORT.md`
* `~/bench_workspace/workspace{i}/stage2/STAGE2_SUMMARY.md` ->`~/bench_workspace/workspace{i}/stage2/STAGE2_UNIT_TEST_REPORT.md`
* `~/bench_workspace/workspace{i}/stage3/STAGE3_SUMMARY.md` ->`~/bench_workspace/workspace{i}/stage3/STAGE3_UNIT_TEST_REPORT.md`
* `~/bench_workspace/workspace{i}/stage4/STAGE4_SUMMARY.md` ->`~/bench_workspace/workspace{i}/stage4/STAGE4_UNIT_TEST_REPORT.md`
* `~/bench_workspace/workspace{i}/stage5/CANARY_EVAL_REPORT.md`
* `~/bench_workspace/workspace{i}/stage5/CANARY_ROLLBACK_PLAN.md`，若灰度失败
* `~/bench_workspace/workspace{i}/stage5/EVALUATION_REPORT.md`、`SCORE_CHECK_REPORT.md`、`FAILURE_CASES.md`，若全量评测完成

Stage 6 可以在两种模式下运行
* **post-full-eval mode**：全量评测已完成，做完整流程复盘skill 维护* **rollback-diagnosis mode**：灰度失败或全量中断，基于失败证据提前做根因定位skill 维护建议
---

### Phase 1: Full Process Evaluation ->全流程评
Invoke:

```text
/benchmark-process-evaluate "$WORKSPACE_ROOT"
```

**Expected output:**

* `~/bench_workspace/workspace{i}/stage6/PROCESS_EVALUATION_REPORT.md`
* `~/bench_workspace/workspace{i}/stage6/PROCESS_METRICS.json`

评价维度必须覆盖：阶段输入输出契约、单元测试有效性、Data-Juicer 清洗收益/损失、评测集覆盖度、灰度拦截能力、全量评测稳定性、成本、失败案例诊断力、流程可复现性
---

### Phase 2: Root Cause Analysis ->根因定位

Invoke:

```text
/benchmark-root-cause-analyze "$STAGE6_DIR/PROCESS_EVALUATION_REPORT.md"
```

**Expected output:**

* `~/bench_workspace/workspace{i}/stage6/ROOT_CAUSE_ANALYSIS.md`
* `~/bench_workspace/workspace{i}/stage6/DEFECT_TRIAGE_MATRIX.json`
* `~/bench_workspace/workspace{i}/stage6/SKILL_FIX_CANDIDATES.md`

根因定位必须把问题映射到
```text
stage ->phase ->skill ->artifact ->rule gap ->proposed minimal fix
```

---

### Phase 3: Version Control Baseline ->建立版本控制基线

Invoke:

```text
/benchmark-skill-version-control "$SKILL_REPO_ROOT"
```

**Expected output:**

* `~/bench_workspace/workspace{i}/stage6/VERSION_CONTROL_LOG.md`
* `~/bench_workspace/workspace{i}/stage6/SKILL_BASELINE_MANIFEST.json`
* `~/bench_workspace/workspace{i}/stage6/GIT_BASELINE.diff`

phase 必须
* 确认 skill 库位git 仓库；如果不是，则初始化 git* 保存 baseline commit ->worktree snapshot* 创建修订分支：`benchclaw/revision/{workspace_id}-{timestamp}`* 写入被允许修改的 skill 文件白名单

如果 `SKILL_REPO_ROOT` 解析后位于 `~/benchclaw/` 下，本 phase 只能读取 git 状态和文件快照，并把 `VERSION_CONTROL_LOG.md`、`SKILL_BASELINE_MANIFEST.json`、`GIT_BASELINE.diff` 写入 `WORKSPACE_ROOT/stage6/`；不得在 `~/benchclaw/` 下初始化 git、创建分支、写入索引、提交、打 tag 或修改工作区。
---

### Phase 4: Surgical Skill Revision ->手术刀式修改流程skill

Invoke:

```text
/benchmark-skill-surgical-revision "$STAGE6_DIR/SKILL_FIX_CANDIDATES.md"
```

**执行要求*

* 只修改根因报告指向的最skill 文件集合* 修改前后必须保留 diff* 每个修改必须绑定一个缺ID、根ID、被修改规则和预期回归测试* 严禁大面积重写无skill

如果候选 skill 文件位于 `~/benchclaw/` 下，本 phase 不得直接编辑这些文件；必须只在 `WORKSPACE_ROOT/stage6/SKILL_PATCH.diff`、`SKILL_CHANGELOG.md` 和 `UPDATED_SKILL_MANIFEST.json` 中描述补丁，由用户在外部确认后自行决定是否应用。
**Expected output:**

* `~/bench_workspace/workspace{i}/stage6/SKILL_REVISION_PLAN.md`
* `~/bench_workspace/workspace{i}/stage6/SKILL_PATCH.diff`
* `~/bench_workspace/workspace{i}/stage6/SKILL_CHANGELOG.md`
* `~/bench_workspace/workspace{i}/stage6/UPDATED_SKILL_MANIFEST.json`

**Checkpoint:** ->`REQUIRE_DIFF_REVIEW = true`，展diff 摘要并等待用户确认后再进入回归验证
---

### Phase 5: Regression Verification ->修改后回归验证
Invoke:

```text
/benchmark-skill-regression-verify "$STAGE6_DIR/SKILL_PATCH.diff"
```

**Expected output:**

* `~/bench_workspace/workspace{i}/stage6/SKILL_REGRESSION_REPORT.md`
* `~/bench_workspace/workspace{i}/stage6/REGRESSION_COMMANDS.sh`
* `~/bench_workspace/workspace{i}/stage6/REGRESSION_RESULTS.json`

回归验证至少覆盖
* frontmatter 解析allowed-tools 合法性* 被修复skill 的输输出契约仍然完整* 相关 Stage 的单元测skill 仍能生成测试计划* 灰度失败定位Stage 6 根因定位链路未断* 不触碰无skill 文件
---

### Phase 6: Finalize Version and Maintenance Summary

完成 git 提交与版本记录：

```bash
git status
git diff --stat
git add <changed-skill-files> ~/bench_workspace/workspace{i}/stage6/*.md ~/bench_workspace/workspace{i}/stage6/*.json
git commit -m "benchclaw: surgical skill revision for <workspace_id>"
git tag "benchclaw-skill-revision-<workspace_id>-<date>"
```

若用户不允许提交，则只生成patch ->changelog，不强制 commit
若 skill repo 位于 `~/benchclaw/` 下，以上 git 写操作全部禁止；只能生成 patch、changelog、regression report 和 `STAGE6_SUMMARY.md` 到 `WORKSPACE_ROOT/stage6/`。
Finalize `~/bench_workspace/workspace{i}/stage6/STAGE6_SUMMARY.md`
```markdown
# Stage6 Summary

## Process Evaluation
[流程质量总体评价]

## Root Causes
[根因列表]

## Skill Revisions
[修改了哪些skill、为什么修改、diff 摘要]

## Version Control
- Branch: [...]
- Baseline commit: [...]
- Revision commit/tag: [...]

## Regression
- Verdict: PASS | FAIL | NEEDS_REVIEW

## Next Iteration Plan
[下一benchmark pipeline 应如何受益于本次 skill 修订]
```

If `COMPACT = true`, also write `~/bench_workspace/workspace{i}/stage6/STAGE6_COMPACT.md`

Stage 6 完成后必须停在这里，展示下一步选项：

1. Publish or merge approved skill revision
2. Continue surgical fixes
3. Start a new pipeline run
4. Review Stage 6 reports and patch only
5. Pause pipeline

不得自动发布、合并、提交、打 tag 或启动新一轮 pipeline。即使回归验证为 `PASS`，也只能说明“可以发布或合并”，必须等待用户选择。
---

## Failure Handling

* 找不skill repo：写入`VERSION_CONTROL_BLOCKED.md`，停止修改，只输出修订建议* git worktree dirty 且未确认：先baseline diff，不覆盖用户改动* 根因证据不足：写 `ROOT_CAUSE_ANALYSIS.md` verdict ->`NEEDS_MORE_EVIDENCE`，不修改 skill* 回归失败：不commit ->tag；写 `SKILL_REGRESSION_REPORT.md` 并保留patch
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

- [ ] `PROCESS_EVALUATION_REPORT.md` 存在- [ ] `ROOT_CAUSE_ANALYSIS.md` 将缺陷定位到 stage/phase/skill/artifact- [ ] `VERSION_CONTROL_LOG.md` 记录 git baseline、branch、diff 状态- [ ] 若发skill 修改，`SKILL_PATCH.diff` ->`SKILL_CHANGELOG.md` 存在- [ ] `SKILL_REGRESSION_REPORT.md` 存在且给verdict- [ ] `STAGE6_SUMMARY.md` 明确说明下一轮流程如何使用修改后续skill- [ ] Stage 6 完成后已停止，并展示用户可选下一步；未自动发布、合并或启动新 pipeline
