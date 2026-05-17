---
name: benchmark-canary-localize-rollback
description: "Atomic module: 灰度失败定位与回退计划。只负责把灰度评测失败映射到具体 stage/phase/skill/artifact 并生成回退修复计划，不负责直接修改产物、不负责全量评测、不负责版本控制修改 skill。Use when user says '灰度失败定位'canary rollback'定位回退到相应位."
argument-hint: [stage5-canary-report]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob
metadata:
  openclaw:
    emoji: ""
    requires:
      bins: [python3]
---

## `BENCHCLAW_ROOT` 只读约束

- **BENCHCLAW_READONLY = true**：`BENCHCLAW_ROOT/` 只能作为 BenchClaw 仓库内共享只读资源根，必须从当前 skill 所在的 BenchClaw 仓库位置解析，不能依赖固定 home 路径或机器绝对路径。
- 严禁在 `BENCHCLAW_ROOT/` 下创建、编辑、覆盖、删除、移动、重命名、复制写入、初始化 git、提交、打 tag、写日志、写缓存或写临时文件。
- 所有派生产物、补丁、快照、报告、脚本、配置、日志和测试输出必须写入 active `WORKSPACE_ROOT`。
- 如必须修改 `BENCHCLAW_ROOT/` 中的资源，只能在 workspace 中生成 patch 或修改建议，等待用户在外部处理；当前 skill 不得直接应用。


## Workspace and File Access Boundary

This skill must operate only inside the current run workspace.

- Before reading or writing any run artifact, resolve and record the active `WORKSPACE_ROOT = ~/bench_workspace/workspace{i}` from the current task, parent stage, or pipeline state.
- Read and write only files under the active `WORKSPACE_ROOT` and the explicitly required global resource roots named by this skill, such as `BENCHCLAW_ROOT/simulatorCards/`, `BENCHCLAW_ROOT/benchmarkDatasetCards/`, `BENCHCLAW_ROOT/realdata_cards/`, `BENCHCLAW_ROOT/templates/`, `BENCHCLAW_ROOT/model_api/`, `BENCHCLAW_ROOT/data-juicer_card/`, `BENCHCLAW_ROOT/annotation-tool/`, or `BENCHCLAW_ROOT/skills/` when the current skill explicitly requires them.
- Never read, list, grep, summarize, compare, copy, or infer from any other `~/bench_workspace/workspace{j}` where `j != i`, even if the current artifact is missing or another workspace appears newer or more complete.
- Never scan broad server directories such as `~`, `/`, `/home`, `/mnt`, `/data`, `/tmp`, `C:\Users`, `C:\`, or arbitrary project/download folders to discover context. Only inspect the exact current workspace paths and exact allowlisted resource roots needed for this skill.
- If an expected input is missing from the active workspace or an allowlisted resource root, stop and report the missing path. Do not search unrelated folders or borrow replacement artifacts from another workspace.
- Outputs must be written only to the active `WORKSPACE_ROOT` paths declared by this skill. Do not mirror or cache run artifacts into other workspaces or unrelated server folders.
- If the user explicitly provides an external path, use it only when it is directly relevant to this skill, record it as a user-provided exception, and do not expand access to sibling or parent directories.

This boundary overrides convenience behaviors such as auto-discovery, resume from latest workspace, reuse of previous artifacts, broad recursive grep/list, and fallback search.

# Canary Failure Localization and Rollback Planning

Localize canary failures and produce rollback instructions for: **$ARGUMENTS**

This skill is an **atomic single-responsibility skill**. It must only diagnose canary failures and write a rollback plan.

---

## Purpose

- 本模块负责在 Stage 5 灰度评测失败后，定位问题应回退到哪些stage、phase、skill ->artifact- 本模块直接产物是 `~/bench_workspace/workspace{i}/stage5/CANARY_ROLLBACK_PLAN.md` ->`~/bench_workspace/workspace{i}/stage5/ROLLBACK_STATE_PATCH.json`- 本模块不负责执行回退、不负责改写上游产物、不负责修改 skill 源码；如需后续维护，应由用户另行发起独立诊断或修订流程
---

## Inputs

- `$ARGUMENTS`：`~/bench_workspace/workspace{i}/stage5/CANARY_EVAL_REPORT.md` ->Stage 5 目录- 必需输入->  - `~/bench_workspace/workspace{i}/stage5/CANARY_EVAL_REPORT.md`
  - `~/bench_workspace/workspace{i}/stage5/CANARY_METRICS.json`
  - `~/bench_workspace/workspace{i}/stage5/CANARY_VERDICT.json`
  - `~/bench_workspace/workspace{i}/stage1/STAGE1_UNIT_TEST_REPORT.md`
  - `~/bench_workspace/workspace{i}/stage2/STAGE2_UNIT_TEST_REPORT.md`
  - `~/bench_workspace/workspace{i}/stage3/STAGE3_UNIT_TEST_REPORT.md`
  - `~/bench_workspace/workspace{i}/stage4/STAGE4_UNIT_TEST_REPORT.md`
  - `~/bench_workspace/workspace{i}/stage5/EVAL_SYSTEM_PROMPT.md`
  - `~/bench_workspace/workspace{i}/stage5/RUN_CONFIG.json`
- 可选输入：
  - `~/bench_workspace/workspace{i}/stage5/CANARY_RAW_OUTPUTS.jsonl`
  - `pipeline_state.json`

若灰verdict ->PASS，本模块应写入`NO_ROLLBACK_NEEDED` 报告并结束
---

## Localization Rules

按以下优先级定位
| Symptom | Primary rollback target | Secondary target |
|---------|--------------------------|------------------|
| API 认证、endpoint、payload、rate limit 错误 | Stage 5 Phase 1 `/benchmark-build-eval-system-prompt` | 模型 API 配置 |
| 输出格式大面积不可解| Stage 5 Phase 1 prompt/output schema | Stage 4 `EVALSET_SCHEMA.md` |
| metric runtime 失败 | Stage 4 Phase 2 `/benchmark-metric-establish` | Stage 4 Phase 3 `/benchmark-validate-stage4` |
| sample manifest/schema mismatch | Stage 4 Phase 1 `/benchmark-evalset-generate` | Stage 3 `EVIDENCE_SCHEMA.md` |
| GT 缺失、错位、明显错| Stage 3 Phase 5 `/benchmark-evidence-validate` | Stage 2 Phase 5 `/benchmark-batch-collect` |
| 证据编译后维度覆盖塌| Stage 3 Phase 1/2/3 | Stage 2 补采 |
| 任务设计与能力维度不一| Stage 1 Phase 3/5 | Stage 4 Phase 1 |
| 灰度样本无法覆盖关键维度 | Stage 4 Phase 1 synthesis rules | Stage 2/3 数据不足 |
| GT 泄露到模型输| Stage 4 Phase 1/3 | Stage 5 Phase 1 prompt packaging |

---

## Procedure

1. **读取灰度失败证据**：解`CANARY_EVAL_REPORT.md`、`CANARY_METRICS.json`、`CANARY_VERDICT.json`2. **读取单元测试证据**：汇Stage 1-4 的单元测verdict、warnings、required fix target3. **分类失败类型**：将错误归类API、prompt、schema、metric、data、cleaning、task design、GT leakage、coverage collapse、cost/stability4. **计算回退目标**：按 `Localization Rules` 和单元测试证据给出最小回退点5. **生成执行计划**：列出应重跑stage/phase/skill、应检查的 artifact、保留废弃的下游产物6. **写入 pipeline state patch**：生成可供父 orchestrator 合并`ROLLBACK_STATE_PATCH.json`7. **写入报告**：生成`CANARY_ROLLBACK_PLAN.md`
---

## Expected Outputs

- `~/bench_workspace/workspace{i}/stage5/CANARY_ROLLBACK_PLAN.md`
- `~/bench_workspace/workspace{i}/stage5/ROLLBACK_STATE_PATCH.json`

`CANARY_ROLLBACK_PLAN.md` 必须包含
```markdown
# Canary Rollback Plan

**Canary verdict**: FAIL | NEEDS_REVIEW | NO_ROLLBACK_NEEDED
**Minimal rollback target**: Stage N / Phase M / Skill `/skill-name`
**Blocking artifact**: [path]

## Evidence
| Evidence Source | Finding | Severity | Supports Target |
|-----------------|---------|----------|-----------------|
| CANARY_EVAL_REPORT | ... | blocking | Stage ... |
| STAGE*_UNIT_TEST_REPORT | ... | warning/fail | Stage ... |

## Root Symptom Classification
- Primary symptom: [...]
- Secondary symptoms: [...]

## Rollback Execution Plan
1. Preserve: [artifacts to keep]
2. Invalidate: [downstream artifacts to regenerate]
3. Rerun from: [stage/phase/skill]
4. Required modification before rerun: [artifact edits or skill issue to defer to a separate manual diagnosis/revision flow]
5. Regression checks after rerun: [unit tests + canary]

## User-Facing Decision
- Recommended action: rollback and rerun from [target]
- Full-scale evaluation allowed now: no
```

`ROLLBACK_STATE_PATCH.json` 必须包含
```json
{
  "current_stage": "rollback_required",
  "failed_stage": "stage5_canary",
  "rollback_target": {
    "stage": "stageN",
    "phase": "phaseM",
    "skill": "/skill-name",
    "artifact": "path"
  },
  "invalidate_after_stage": "stageN",
  "full_eval_allowed": false
}
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

- [ ] 报告中有且只有一minimal rollback target- [ ] 回退目标必须精确stage、phase、skill ->artifact- [ ] 明确列出哪些下游产物需要废弃并重跑- [ ] 不执行全量评测，不修改上游主产物
---

## Downstream Handoff

- 父级 `benchmark-stage5-eval` ->`benchmark-pipeline` 合并 `ROLLBACK_STATE_PATCH.json` ->`pipeline_state.json`- 用户或父流程根据 `CANARY_ROLLBACK_PLAN.md` 回退到目录stage/phase- 如需后续流程规则修订，可把该报告作为独立诊断输入
