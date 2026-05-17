---
name: benchmark-draft-gen
description: "Atomic module: stage1 Phase 6 benchmark 草稿合成模块。只负责将前序所有 phase 产出整合为一份完整的、内部自洽的 benchmark 草稿文档，不负责执行计划生成或任何 stage2-5 工作。Use when user says '合成 benchmark 草稿'、'draft benchmark spec'、'生成草稿'。"
argument-hint: [benchmark-context]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob
metadata:
  openclaw:
    emoji: ""
    requires:
      bins: [python3]
---

## `BENCHCLAW_ROOT` 只读约束

- **BENCHCLAW_READONLY = true**：`BENCHCLAW_ROOT/` 只能作为 BenchClaw 仓库内共享只读资源根，必须从当前 skill 所在的 BenchClaw 仓库位置解析，不能依赖固定 home 路径或机器绝对路径。
- `BENCHCLAW_ROOT` 必须解析为当前 skill 所在 BenchClaw 仓库的根目录；只允许读取该根目录下、且被当前 skill 明确允许的子目录。
- 严禁在 `BENCHCLAW_ROOT/` 下创建、编辑、覆盖、删除、移动、重命名、复制写入、初始化 git、提交、打 tag、写日志、写缓存或写临时文件。
- 所有派生产物、补丁、快照、报告、脚本、配置、日志和测试输出必须写入 active `WORKSPACE_ROOT`。
- 如必须修改 `BENCHCLAW_ROOT/` 中的资源，只能在 workspace 中生成 patch 或修改建议，等待用户在外部处理；当前 skill 不得直接应用。


## Workspace and File Access Boundary

This skill must operate only inside the current run workspace.

- Before reading or writing any run artifact, resolve and record the active `WORKSPACE_ROOT = ~/bench_workspace/workspace{i}` from the current task, parent stage, or pipeline state.
- Read and write only files under the active `WORKSPACE_ROOT` and the explicitly required global resource roots named by this skill, which must stay inside `BENCHCLAW_ROOT/`, such as `BENCHCLAW_ROOT/simulatorCards/`, `BENCHCLAW_ROOT/benchmarkDatasetCards/`, `BENCHCLAW_ROOT/realdata_cards/`, `BENCHCLAW_ROOT/templates/`, `BENCHCLAW_ROOT/model_api/`, `BENCHCLAW_ROOT/data-juicer_card/`, `BENCHCLAW_ROOT/annotation-tool/`, or `BENCHCLAW_ROOT/skills/` when the current skill explicitly requires them.
- Never read, list, grep, summarize, compare, copy, or infer from any other `~/bench_workspace/workspace{j}` where `j != i`, even if the current artifact is missing or another workspace appears newer or more complete.
- Never scan broad server directories such as `~`, `/`, `/home`, `/mnt`, `/data`, `/tmp`, `C:\Users`, `C:\`, or arbitrary project/download folders to discover context. Only inspect the exact current workspace paths and exact allowlisted resource roots needed for this skill.
- If an expected input is missing from the active workspace or an allowlisted resource root, stop and report the missing path. Do not search unrelated folders or borrow replacement artifacts from another workspace.
- Outputs must be written only to the active `WORKSPACE_ROOT` paths declared by this skill. Do not mirror or cache run artifacts into other workspaces or unrelated server folders.
- If the user explicitly provides an external path, use it only when it is directly relevant to this skill, record it as a user-provided exception, and do not expand access to sibling or parent directories.

This boundary overrides convenience behaviors such as auto-discovery, resume from latest workspace, reuse of previous artifacts, broad recursive grep/list, and fallback search.

# Benchmark Draft Generation

Execute benchmark draft synthesis for: **$ARGUMENTS**

This skill is an **atomic single-responsibility skill**.
It must **only** do the work scoped to this module.

---

## Purpose

- 本模块负责将前序 5 个 phase 的全部产出整合为一份完整的 benchmark 草稿文档。
- 本模块确保草稿内部自洽：能力维度 → 数据源覆盖 → 任务原型 → 指标体系之间有清晰的追溯链。
- 本模块位于 Stage 1 第六环节，直接产物是 `~/bench_workspace/workspace{i}/stage1/BENCHMARK_DRAFT.md`。
- 本模块不负责执行计划生成，不调度 stage2-stage5。

---

## Inputs

- `$ARGUMENTS`：benchmark 草稿的补充要求或用户偏好（如命名偏好、风格要求）。
- 必需输入：
  - `~/bench_workspace/workspace{i}/stage1/IDEA_TARGET.md`
  - `~/bench_workspace/workspace{i}/stage1/LITERATURE_REVIEW.md`
  - `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md`
  - `~/bench_workspace/workspace{i}/stage1/DATA_SOURCE_MAPPING.md`
  - `~/bench_workspace/workspace{i}/stage1/EVALSET_PROTOTYPE.md`
- 可选输入：`~/bench_workspace/workspace{i}/stage1/BENCHMARK_BRIEF.md`、用户给出的格式偏好或已有草稿片段。
- **若任一必需输入缺失，应立即停止并报告缺失文件。**

---

## Procedure

1. **读取全部上游产出**：依次读取 5 个必需输入文件，提取关键信息：
   - `~/bench_workspace/workspace{i}/stage1/IDEA_TARGET.md`：核心意图、定位语句、非目标
   - `~/bench_workspace/workspace{i}/stage1/LITERATURE_REVIEW.md`：结构性缺口、重叠风险、可借鉴模式
   - `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md`：维度体系、新颖性标注、覆盖分析
  - `~/bench_workspace/workspace{i}/stage1/DATA_SOURCE_MAPPING.md`：数据源选择、可行性评估、未覆盖维度
   - `~/bench_workspace/workspace{i}/stage1/EVALSET_PROTOTYPE.md`：任务原型、指标体系、模板复用说明
2. **确定 Benchmark 名称与定位**：基于 `~/bench_workspace/workspace{i}/stage1/IDEA_TARGET.md` 的定位语句，提炼简洁的 benchmark 名称和一句话定位。
3. **撰写动机章节**：基于 `~/bench_workspace/workspace{i}/stage1/LITERATURE_REVIEW.md` 的结构性缺口和重叠风险，构建"为什么需要这个 benchmark"的论证。
4. **整合能力维度体系**：从 `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md` 引用维度体系，突出 novel dimensions。
5. **撰写数据构造方案**：从 `~/bench_workspace/workspace{i}/stage1/DATA_SOURCE_MAPPING.md` 引用仿真器、已有数据集、真实数据的组合选择与补充方案，并明确列出每个选定数据源在 stage2 计划采集的目标数量（如样本数、轨迹数、片段数或任务实例数）。
6. **撰写评测集设计**：从 `~/bench_workspace/workspace{i}/stage1/EVALSET_PROTOTYPE.md` 引用任务原型与指标体系。
7. **撰写对比定位**：基于 `~/bench_workspace/workspace{i}/stage1/LITERATURE_REVIEW.md` 的 Related Benchmarks 表，构建与已有 benchmark 的对比表。
8. **补齐未决项**：将上游产出中尚未定稿但必须在草稿中体现的内容，统一整理为“待下游确认”的说明，不使用标记模板。
9. **自洽性校验**：检查追溯链——草稿中引用的每个维度、仿真器、任务原型、指标是否都能追溯到对应的上游产出文件。
10. **写入**：写入 `~/bench_workspace/workspace{i}/stage1/BENCHMARK_DRAFT.md`。

---

## Expected Outputs

- `~/bench_workspace/workspace{i}/stage1/BENCHMARK_DRAFT.md`

输出文件结构：

```markdown
# [Benchmark Name]: [一句话定位]

## 1. Motivation
[动机：基于文献调研的 gap 分析，为什么需要这个 benchmark]

## 2. Capability Dimensions
[能力维度体系概述，引用 CAPABILITY_SCOPE.md]

## 3. Data Construction
### 3.1 Source-Based Generation
[选定数据源组合与生成策略，引用 DATA_SOURCE_MAPPING.md]
### 3.2 Existing Dataset Reuse
[已有数据集复用方案]
### 3.3 Real-Data Integration
[真实采集数据接入与补充方案]

### 3.4 Planned Collection Quotas by Source
| Source Type | Source Name | Planned Collection Amount | Unit | Rationale |
|-------------|-------------|---------------------------|------|-----------|
| ...         | ...         | ...                       | ...  | ...       |

## 4. Eval-Set Design
### 4.1 Task Design
[任务原型概述，引用 EVALSET_PROTOTYPE.md]
### 4.2 Metric System
[指标体系概述]

## 5. Comparison with Existing Benchmarks
[与已有 benchmark 的对比定位表]

## 6. Known Limitations and Future Extensions
[已知局限、后续扩展方向]

## 7. Downstream Handoff Notes
[需要 stage2-stage5 继续完善的内容与对应 stage 的说明]
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

- [ ] `~/bench_workspace/workspace{i}/stage1/BENCHMARK_DRAFT.md` 已存在且非空。
- [ ] 文档包含完整的 7 个章节。
- [ ] Benchmark 名称与定位语句清晰且与 `~/bench_workspace/workspace{i}/stage1/IDEA_TARGET.md` 一致。
- [ ] 能力维度、数据源、任务原型、指标体系之间的追溯链完整——每个引用都可追溯到对应的上游产出文件。
- [ ] `## 3. Data Construction` 明确列出每个选定数据源的计划采集数量，且不得只写“适量”“若干”这类模糊表述。
- [ ] Comparison with Existing Benchmarks 包含至少 3 个已有 benchmark 的对比条目。
- [ ] Downstream Handoff Notes 明确标注了每个后续完善项对应的 stage。
- [ ] 若任一必需输入缺失，不得标记完成。

---

## Rules

- 不生成 `~/bench_workspace/workspace{i}/stage1/EXECUTION_PLAN.md`——那是 Phase 7 的职责。
- 不擅自改写任何上游产出文件（`~/bench_workspace/workspace{i}/stage1/IDEA_TARGET.md`、`~/bench_workspace/workspace{i}/stage1/LITERATURE_REVIEW.md`、`~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md`、`~/bench_workspace/workspace{i}/stage1/DATA_SOURCE_MAPPING.md`、`~/bench_workspace/workspace{i}/stage1/EVALSET_PROTOTYPE.md`）。
- 不把草稿当作最终 benchmark 定义——stage2-stage5 会继续完善未决项并可能修订草稿。
- 不在草稿中虚构上游产出中不存在的维度、数据源或指标。
- 草稿中的数据构造章节必须为每个选定数据源写出明确采集目标数量和计量单位，允许标注为估算值，但不得省略。
- 出错时必须明确指出阻塞文件或不一致条件。
- 如果 Write 因文件过大失败，立即 fallback 到 Bash 分块写入，不要询问用户许可。

---

## Downstream Handoff

- `benchmark-execution-plan-gen` 读取 `~/bench_workspace/workspace{i}/stage1/BENCHMARK_DRAFT.md` 的对应章节生成 stage2-stage5 的执行计划。
- stage2-stage5 各环节读取 `~/bench_workspace/workspace{i}/stage1/BENCHMARK_DRAFT.md` 的对应章节作为工作锚点。
- 本模块只写交接关系，不调度下游模块.
