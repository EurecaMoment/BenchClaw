---
name: benchmark-literature-survey
description: "Atomic module: stage1 Phase 2 文献与已有 benchmark 调研模块。只负责检索、分析与 benchmark 目标相关的学术论文、已有 benchmark 和公开评测框架，输出结构化调研报告，不负责能力维度划分或草稿生成。Use when user says '调研已有 benchmark'、'survey related work'、'文献调研'。"
argument-hint: [benchmark-context]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, WebSearch, WebFetch
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

# Benchmark Literature Survey

Execute literature and existing benchmark survey for: **$ARGUMENTS**

This skill is an **atomic single-responsibility skill**.
It must **only** do the work scoped to this module.

---

## Purpose

- 本模块负责检索与 benchmark 目标相关的学术论文、已有 benchmark、公开评测集与评测框架，输出结构化调研报告。
- 本模块识别现有方案的结构性缺口、可借鉴的设计模式、重叠风险与对后续维度划分的约束。
- 本模块位于 Stage 1 第二环节，直接产物是 `~/bench_workspace/workspace{i}/stage1/LITERATURE_REVIEW.md`。
- 本模块不负责能力维度划分、数据源选取、评测集设计或草稿生成。

---

## Inputs

- `$ARGUMENTS`：benchmark 调研的补充方向或用户指定的检索重点。
- 必需输入：`~/bench_workspace/workspace{i}/stage1/IDEA_TARGET.md`。
- 可选输入：`~/bench_workspace/workspace{i}/BENCHMARK_BRIEF.md`、用户指定的论文列表或已知 benchmark 名称。
- **若 `~/bench_workspace/workspace{i}/stage1/IDEA_TARGET.md` 缺失，应立即停止并报告缺失文件。**

---

## Procedure

1. **读取目标**：读取 `~/bench_workspace/workspace{i}/stage1/IDEA_TARGET.md`，提取 Core Evaluation Intent、Target Boundary 和 Positioning Statement 作为检索锚点。
2. **构建检索策略**：基于目标定义生成多组检索关键词（覆盖能力维度关键词、benchmark 名称关键词、仿真器/平台关键词）。
3. **检索执行**：
   - 检索学术论文（arXiv、Semantic Scholar、Google Scholar）
   - 检索已有 benchmark（papers with code、benchmark 排行榜、GitHub 仓库）
   - 检索公开评测框架与评测集（Hugging Face Datasets、官方 benchmark 站点）
   - 如有必要，下载论文 PDF 到本地进行深度分析
4. **逐条分析**：对每个已有 benchmark 梳理：
   - 能力覆盖范围与评测维度设计
   - 数据构造方式（仿真生成 / 人工标注 / 自动采集）
   - 指标体系（评测指标类型与计算方式）
   - 局限性（未覆盖的能力、数据偏差、评测盲区）
5. **提炼设计模式**：从已有工作中抽取可复用的评测维度设计、数据构造方式、指标设计模式。
6. **识别结构性缺口**：标注现有工作未覆盖但本 benchmark 应覆盖的区域。
7. **评估重叠风险**：标注与已有工作高度重叠的区域，明确需要在草稿中显式差异化的点。
8. **导出约束**：将调研结论转化为对后续能力维度划分和草稿生成的具体约束条件。
9. **校验**：检查调研覆盖面是否与 `~/bench_workspace/workspace{i}/stage1/IDEA_TARGET.md` 中的 Core Evaluation Intent 匹配。
10. **写入**：写入 `~/bench_workspace/workspace{i}/stage1/LITERATURE_REVIEW.md`。

---

## Expected Outputs

- `~/bench_workspace/workspace{i}/stage1/LITERATURE_REVIEW.md`

输出文件结构：

```markdown
# Literature and Existing Benchmark Survey

## Related Benchmarks
| Benchmark | Capabilities Covered | Data Source | Metrics | Limitations |
|-----------|---------------------|-------------|---------|-------------|
| ...       | ...                 | ...         | ...     | ...         |

## Related Papers
[按相关性排序的论文摘要与关键发现]

## Reusable Design Patterns
[可借鉴的评测维度设计、数据构造方式、指标设计]

## Structural Gaps
[现有工作未覆盖但本 benchmark 应覆盖的区域]

## Duplication and Weak Novelty Risks
[与已有工作高度重叠的区域，需要在草稿中显式差异化的点]

## Constraints Derived from Survey
[调研结论对后续能力维度划分和草稿生成的约束]
```

---

## Completion Criteria

- [ ] `~/bench_workspace/workspace{i}/stage1/LITERATURE_REVIEW.md` 已存在且非空。
- [ ] Related Benchmarks 表至少包含 3 个已有 benchmark 的结构化分析。
- [ ] Structural Gaps 明确列出了至少 1 个现有工作未覆盖的区域。
- [ ] Duplication and Weak Novelty Risks 已标注高重叠区域。
- [ ] Constraints Derived from Survey 为后续 phase 提供了可操作的约束条件。
- [ ] 调研范围与 `~/bench_workspace/workspace{i}/stage1/IDEA_TARGET.md` 中的 Core Evaluation Intent 一致。

---

## Rules

- 不生成 `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md`、`~/bench_workspace/workspace{i}/stage1/BENCHMARK_DRAFT.md` 或任何后续 phase 产物。
- 不擅自改写 `~/bench_workspace/workspace{i}/stage1/IDEA_TARGET.md`。
- 不在调研报告中直接进行能力维度划分——那是 Phase 3 的职责。
- 检索结果不足时必须明确标注"调研覆盖不足"区域，而非编造引用。
- 论文引用必须附真实来源信息（标题、作者、年份、链接），不可虚构。
- 出错时必须明确指出阻塞原因（如检索服务不可用、目标定义过于模糊）。
- 如果 Write 因文件过大失败，立即 fallback 到 Bash 分块写入，不要询问用户许可。

---

## Downstream Handoff

- `benchmark-capability-scope` 读取 `~/bench_workspace/workspace{i}/stage1/LITERATURE_REVIEW.md` 中的 Structural Gaps 和 Constraints 作为维度划分的输入约束。
- `benchmark-draft-gen` 读取 `~/bench_workspace/workspace{i}/stage1/LITERATURE_REVIEW.md` 中的 Related Benchmarks 和 Duplication Risks 生成对比定位。
- `benchmark-execution-plan-gen` 读取 `~/bench_workspace/workspace{i}/stage1/LITERATURE_REVIEW.md` 评估数据获取风险。
- 本模块只写交接关系，不调度下游模块。
