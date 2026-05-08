---
name: benchmark-check-scores
description: "Atomic module: stage5 Phase 4 异常检查与评测报告生成模块。只负责检测模型输出的异常响应模式、分数异常值、模板污染信号，并整合全部评测结果生成面benchmark 目标的完整评测报告，不负责推理执行或指标打分。Use when user says '检查分check scores'生成评测报告'异常检查"
argument-hint: [stage5-context]
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

# Benchmark Check Scores

Execute anomaly detection and evaluation report generation for: **$ARGUMENTS**

This skill is an **atomic single-responsibility skill**.
It must **only** do the work scoped to this module.

---

## Purpose

- 本模块负责对模型推理结果执行三类异常检查：异常响应检测、异常分数检测、模板污染检测- 本模块整合全部评测结果（推理、分数、异常发现），生成面`BENCHMARK_DRAFT.md` 目标结构的完整评测报告- 本模块位Stage 5 第四环节（最后一个执行环节），直接产物是 `EVAL_REPORT.md`- 本模块不负责推理执行、指标打分或修复发现的问题
---

## Inputs

- `$ARGUMENTS`：异常检查的补充要求（如调整 IQR 阈值、指定重点检查维度）- 必需输入->  - `~/bench_workspace/workspace{i}/stage5/RAW_MODEL_OUTPUTS.jsonl` ->模型推理结果（含原始输出->  - `~/bench_workspace/workspace{i}/stage5/SCORES.csv` ->样本级分->  - `~/bench_workspace/workspace{i}/stage5/SCORE_SUMMARY.md` ->汇总级分数
  - `~/bench_workspace/workspace{i}/stage5/EVAL_SYSTEM_PROMPT.md` ->评测 prompt（用于污染检查比对）
  - `~/bench_workspace/workspace{i}/stage4/EVALSET_DATASET/` ->GT 数据（用于污染检查比对）
  - `~/bench_workspace/workspace{i}/stage1/BENCHMARK_DRAFT.md` ->评测目标与能力维度（报告结构框架- 可选输入：
  - `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md` ->维度操作性定义（辅助失败模式分析->  - 父流程Constants：`SCORE_ANOMALY_IQR_FACTOR`、`CONTAMINATION_CHECK`
- **若任一必需输入缺失，应立即停止并报告缺失文件*

---

## Procedure

### Step 1: 异常响应检查
1. 遍历 `RAW_MODEL_OUTPUTS.jsonl`，检测以下异常模式：
   - **空响应或极短响应**：`raw_output` 为空或长度低于合理下->   - **重复/模板化响*：大量样本的 `raw_output` 高度相似（文本相似度超过阈值）
   - **拒绝回答**：模型安全过滤触发（检测拒绝关键词模式->   - **格式违规**：`parse_success = false` 的样本中，原始输出的格式偏差分类
2. 统计每种异常类型的数量与占比
### Step 2: 异常分数检查
3. 读取 `SCORES.csv`，执行以下分析：
   - **IQR 异常值检查*：对每个指标计算 Q1、Q3 ->IQR，标记超Q1 - `SCORE_ANOMALY_IQR_FACTOR` × IQR ->Q3 + `SCORE_ANOMALY_IQR_FACTOR` × IQR 的样->   - **维度间一致*：某维度分数异常低时，检查是否有合理解释（如该维度样本量少、难度集中）
   - **难度-分数单调*：检查每个维度内 easy 均分是否 ->medium ->hard（若违反，标记为需关注->   - **跨仿真器一致*：同一维度不同仿真器来源的样本分数是否存在系统性偏
### Step 3: 模板污染检查（CONTAMINATION_CHECK = true
4. ->`RAW_MODEL_OUTPUTS.jsonl` 中的模型输出执行污染信号检测：
   - **GT 泄露检查*：计算模型输出与对应 GT 的文件结构重叠度，标记异常高重叠的样本
   - **元数据泄*：检查模型输出中是否包含不应暴露的元数据（场ID、维度标签、难度等级等来自 `metadata.json` 的字段）
   - **Prompt 回显**：检查模型输出中是否包含 system prompt 或评分标准的片段
5. 若发现污染信号，标记受影响样本，评估影响范围（受污染样本占比、涉及维度）
### Step 4: 失败模式分析

6. 基于异常响应和低分样本，提炼典型失败模式->   - 按维度聚类失败样本，识别每个维度的主要失败原因   - 识别跨维度的共性失败模板   - 标注每种失败模式的频率和影响范围

### Step 5: 生成评测报告

7. 读取 `BENCHMARK_DRAFT.md` 的能力维度体系，以此为报告骨架8. 整合所有结果，撰写完整`EVAL_REPORT.md`，包含：
   - 评测概览（模型、评测集、配置）
   - 总体结果（overall score + scoring rate->   - 分维度分析（对齐 `BENCHMARK_DRAFT.md` 的维度结构）
   - 失败模式分析
   - 异常报告（响应异+ 分数异常 + 污染检查）
   - 对照 benchmark 目标的评->   - 改进建议

### Step 6: 校验

9. 确认 `EVAL_REPORT.md` 的维度分析覆盖`BENCHMARK_DRAFT.md` 中的所有能力维度10. 确认异常报告中的样本 ID 都可选`RAW_MODEL_OUTPUTS.jsonl` ->`SCORES.csv` 中找到
---

## Expected Outputs

- `~/bench_workspace/workspace{i}/stage5/EVAL_REPORT.md`

`EVAL_REPORT.md` 结构
```markdown
# Evaluation Report

## 1. Evaluation Overview
- **Benchmark**: [名称, from BENCHMARK_DRAFT.md]
- **Model**: [模型名称与版本]
- **Date**: [today]
- **Evalset scale**: [样本数] samples across [维度数] dimensions
- **Run config**: temp=[T], max_tokens=[N], seed=[S]

## 2. Overall Results
- **Overall score**: [总分] (aggregation: [方式])
- **Effective scoring rate**: [百分比]

## 3. Per-Dimension Analysis
### Dimension: [维度名称]
- Score: mean=[M], median=[M], std=[S]
- By difficulty: easy=[E], medium=[M], hard=[H]
- Key findings: [主要发现]
- Failure patterns: [典型失败模式]

### Dimension: [维度名称]
...

## 4. Failure Mode Analysis
| Failure Mode | Affected Dimensions | Frequency | Example Sample IDs |
|-------------|--------------------|-----------|--------------------|
| ...         | ...                | ...       | ...                |

## 5. Anomaly Report
### 5.1 Response Anomalies
| Anomaly Type | Count | Proportion | Action |
|-------------|-------|-----------|--------|
| Empty response | ... | ... | ... |
| Repetitive output | ... | ... | ... |
| Safety refusal | ... | ... | ... |
| Format violation | ... | ... | ... |

### 5.2 Score Anomalies
| Type | Details | Affected Samples |
|------|---------|-----------------|
| IQR outliers | ... | ... |
| Difficulty monotonicity violation | ... | ... |
| Cross-simulator bias | ... | ... |

### 5.3 Contamination Check
- Status: [clean / suspicious / contaminated]
- Details: [发现摘要]
- Affected samples: [数量]

## 6. Comparison with Benchmark Goals
[对照 BENCHMARK_DRAFT.md 评测目标的评估]

## 7. Recommendations
[改进建议]
```

---

## Completion Criteria

- [ ] `~/bench_workspace/workspace{i}/stage5/EVAL_REPORT.md` 存在且包含完整的 7 个章节- [ ] Per-Dimension Analysis 覆盖 `BENCHMARK_DRAFT.md` 中的所有能力维度- [ ] Anomaly Report 包含响应异常、分数异常和污染检查（`CONTAMINATION_CHECK = true`）三个子章节- [ ] 异常报告中引用的样本 ID 可在 `RAW_MODEL_OUTPUTS.jsonl` ->`SCORES.csv` 中找到- [ ] Comparison with Benchmark Goals 对照`BENCHMARK_DRAFT.md` 的评测目标- [ ] 若必需输入缺失，不得标记完成功
---

## Rules

- 不执行模型推理或指标打分——那Phase 2 ->Phase 3 的职责- 不修复发现的异常——本模块只诊断和报告，修复决策由统筹 skill 或用户做出- 不擅自改`SCORES.csv`、`RAW_MODEL_OUTPUTS.jsonl` 或任何上游产出- 报告结构必须对齐 `BENCHMARK_DRAFT.md` 的能力维度体系——不可自行重新组织维度结构- 污染检查在 `CONTAMINATION_CHECK = false` 时可跳过，但必须在报告中标注"已跳- 异常检测使用统计方法（IQR、文本相似度阈值等），不可仅凭主观判断标记异常- 改进建议必须具有可操作性——应指向具体phase ->stage 调整方向，不可泛泛而谈- 出错时必须明确指出阻塞原因（`SCORES.csv` 格式异常、样ID 无法对齐）- 如果 Write 因文件过大失败，立即 fallback ->Bash 分块写入，不要询问用户许可选
---

## Downstream Handoff

- 父流程`benchmark-stage5-eval` 读取 `~/bench_workspace/workspace{i}/stage5/EVAL_REPORT.md` 展示 Gate 5 checkpoint- 父流程最终报告读`~/bench_workspace/workspace{i}/stage5/EVAL_REPORT.md` 作为最benchmark pipeline 报告的核心内容- 若报告中发现严重异常，统skill 根据 Anomaly Report ->Recommendations 决定是否回退到- 本模块只写交接关系，不调度下游模块