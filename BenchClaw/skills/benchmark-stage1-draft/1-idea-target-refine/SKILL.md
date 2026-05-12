---
name: idea-target-refine
description: "Atomic module: stage1 Phase 1 目标提炼模块。只负责从粗糙 benchmark idea 中提炼精确的目标定义、边界、非目标与定位语句，不负责文献调研、能力维度划分或任何后续 phase 工作。Use when user says '提炼 benchmark 目标'、'refine benchmark target'、'先把 idea 精炼一下'。"
argument-hint: [benchmark-idea]
allowed-tools: Bash(*), Read, Write, Edit
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

# Idea Target Refine

Execute benchmark target refinement for: **$ARGUMENTS**

This skill is an **atomic single-responsibility skill**.
It must **only** do the work scoped to this module.

---

## Purpose

- 本模块负责从用户的粗糙 benchmark idea 中提炼出精确、可操作的 benchmark 目标定义。
- 本模块位于 Stage 1 第一环节，是整条 pipeline 的起点，直接产物是 `~/bench_workspace/workspace{i}/stage1/IDEA_TARGET.md`。
- 本模块不负责文献调研、能力维度划分、数据源选取或任何后续 phase 的工作。
- 本模块不调用任何外部检索工具，仅基于用户输入与自身知识进行目标提炼。

---

## Inputs

- `$ARGUMENTS`：用户的粗糙 benchmark idea 描述（自然语言）。
- 必需输入：`$ARGUMENTS` 不得为空。
- 可选输入：`~/bench_workspace/workspace{i}/BENCHMARK_BRIEF.md`（若用户已有初步文档）、用户给出的领域约束或偏好。
- **若 `$ARGUMENTS` 为空且无任何可选输入，应立即停止并要求用户提供 benchmark idea。**

---

## Procedure

1. **解析**：从 `$ARGUMENTS` 中抽取核心评测意图——要测什么能力、面向什么类型的系统。
2. **界定边界**：明确 benchmark 的目标边界：
   - 测试对象（agent 类型：embodied agent、tool-use agent、multimodal agent 等）
   - 任务场景类别（导航、操控、多模态推理等）
   - 期望产出形式（动作序列、规划文本、状态变化等）
3. **划定非目标**：显式列出本 benchmark 不打算覆盖的方向，防止后续 phase 范围膨胀。
4. **提炼定位语句**：一句话说明这个 benchmark 为什么需要存在、与已有工作的预期差异点。
5. **保留原始 idea**：将用户原始输入原文保留在文档中，供后续回溯与一致性校验。
6. **校验**：检查目标定义是否内部自洽——测试对象、场景类别、产出形式三者是否逻辑兼容。
7. **写入**：写入 `~/bench_workspace/workspace{i}/stage1/IDEA_TARGET.md`。

---

## Expected Outputs

- `~/bench_workspace/workspace{i}/stage1/IDEA_TARGET.md`

输出文件结构：

```markdown
# Benchmark Target Definition

## Core Evaluation Intent
[要测什么能力，面向什么系统]

## Target Boundary
- Test subject: [agent 类型]
- Scenario class: [任务场景类别]
- Expected output form: [期望产出形式]

## Non-Goals
- [非目标1]
- [非目标2]

## Positioning Statement
[一句话定位]

## Raw Idea Trace
[原始 idea 原文保留，供后续回溯]
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

- [ ] `~/bench_workspace/workspace{i}/stage1/IDEA_TARGET.md` 已存在且非空。
- [ ] 文档包含完整的五个章节：Core Evaluation Intent、Target Boundary、Non-Goals、Positioning Statement、Raw Idea Trace。
- [ ] Core Evaluation Intent 明确指出了待测能力与目标系统类型。
- [ ] Non-Goals 至少列出 2 项显式排除的方向。
- [ ] Positioning Statement 为单句，且与 Core Evaluation Intent 逻辑一致。
- [ ] Raw Idea Trace 完整保留了用户原始输入。

---

## Rules

- 不生成 `~/bench_workspace/workspace{i}/stage1/LITERATURE_REVIEW.md`、`~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md` 或任何后续 phase 产物。
- 不执行文献检索或 web 搜索。
- 不擅自扩大或缩小用户原始 idea 的范围，仅做精炼与结构化。
- 不把目标提炼当作最终 benchmark 定义——后续 phase 可能回退修订。
- 出错时必须明确指出阻塞原因（如用户 idea 过于模糊无法提炼）。
- 如果 Write 因文件过大失败，立即 fallback 到 Bash 分块写入，不要询问用户许可。

---

## Downstream Handoff

- `benchmark-literature-survey` 读取 `~/bench_workspace/workspace{i}/stage1/IDEA_TARGET.md` 作为调研方向锚点。
- `benchmark-capability-scope` 读取 `~/bench_workspace/workspace{i}/stage1/IDEA_TARGET.md` 确认能力覆盖完整性。
- `benchmark-draft-gen` 读取 `~/bench_workspace/workspace{i}/stage1/IDEA_TARGET.md` 中的定位语句与边界定义。
- 本模块只写交接关系，不调度下游模块。