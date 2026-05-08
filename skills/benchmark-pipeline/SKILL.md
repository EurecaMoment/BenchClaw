---
name: benchmark-pipeline
description: "Workflow: 顺序编排 benchmark 六阶段闭环流水线，仅负责依赖校验、阶段调度、I/O 对齐、单元测试门控、灰度评测门控、回退状态管理、Stage 6 诊断维护与摘要汇总。Use when user says '跑 benchmark 全流程'、'benchmark pipeline'、'串联 stage1-stage6'、'先单测再灰度再全量评测'、'从粗糙 idea 到评测结果和 skill 维护'."
argument-hint: [benchmark-idea]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, WebSearch, WebFetch, Skill
metadata: {"openclaw":{"emoji":"🧩","requires":{"bins":["python3","curl","git"]}}}
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

# Benchmark Pipeline Orchestrator

Orchestrate the closed-loop benchmark pipeline for: **$ARGUMENTS**

This skill is an **L1 pipeline orchestrator only**. It must not re-implement, expand, or substitute the internal logic of any stage or atomic skill.

Its responsibilities are limited to:

- 检查输入是否齐全。
- 准备与校验 workspace。
- 顺序调度 Stage 1-6。
- 对齐阶段输入输出。
- 强制执行 Stage 1-4 单元测试门控。
- 强制执行 Stage 5 全量评测前灰度评测门控。
- 灰度发现问题时进入定位回退状态，阻止全量评测。
- Stage 6 对整个流程做全面评价、问题根因定位。
- 写入状态文件、阶段摘要、最终总报告。

---

## Workspace Isolation Rule

本次 pipeline 运行必须与其他 workspace 严格隔离，防止历史生成内容干扰当前生成。

- 只能读取和写入当前 `WORKSPACE_ROOT = ~/bench_workspace/workspace{i}` 及其 `stage1/` 到 `stage6/` 子目录。
- 不得读取、参考、复制、总结、对齐或借鉴其他 `~/bench_workspace/workspace{j}` 的任何产物，其中 `j != i`。
- 不得因为其他 workspace 中已有的 `CAPABILITY_SCOPE.md`、`DATA_SOURCE_MAPPING.md`、`BENCHMARK_DRAFT.md`、`DATA_QUALITY_REPORT.md`、`cleaned_data/`、评测结果或诊断报告而影响本次生成。
- 允许读取的共享资源仅限明确的全局资源目录，例如 `~/benchclaw/simulator_cards/`、`~/benchclaw/dataset_cards/`、`~/benchclaw/realdata_cards/`、`~/benchclaw/templates/`、`~/benchclaw/model_api/`、`~/benchclaw/skills/`。
- 如果需要复用其他 workspace 的内容，必须由用户显式给出该 workspace 路径和复用范围；否则一律视为禁止。
- 每个阶段的输入校验只检查当前 `WORKSPACE_ROOT` 内的上游产物，不得在缺失时自动去其他 workspace 查找替代文件。

该规则优先级高于“自动恢复”“使用最高序号 workspace”“参考已有产物”等便利性行为。若发生冲突，必须选择隔离当前 workspace。

---

## Stage Transition Checkpoint Rule

每完成一个 stage 后，pipeline 必须暂停并用“选项”的方式询问用户下一阶段指示。不得在没有用户选择的情况下自动进入下一 stage。

适用范围：

- Stage 1 完成并通过 Gate 1 后，必须询问是否进入 Stage 2。
- Stage 2 完成并通过 Gate 2 后，必须询问是否进入 Stage 3。
- Stage 3 完成并通过 Gate 3 后，必须询问是否进入 Stage 4。
- Stage 4 完成并通过 Gate 4 后，必须询问是否进入 Stage 5 灰度评测。
- Stage 5 灰度或全量评测完成后，必须询问是否进入 Stage 6 诊断维护。
- Stage 6 完成后，必须询问是否生成最终报告、是否进入下一轮修订或是否结束。

每次询问必须至少提供这些选项：

1. `继续下一阶段`：进入下一个 stage。
2. `暂停在当前阶段`：不继续执行，仅保留当前产物和状态。
3. `查看/总结当前阶段结果`：展示当前 stage 的关键产物、verdict、风险和建议。
4. `回退或重跑当前阶段`：用户指定要回退的 phase / skill / artifact。
5. `修改指令后继续`：用户补充约束、规模、数据源、模型 API 或其他偏好后再进入下一阶段。

如果当前 stage 的 gate verdict 是 `FAIL`，不得提供“继续下一阶段”作为可执行选项；只能提供查看结果、回退/重跑、暂停、或由用户显式确认的其他修复动作。

该规则优先级高于 `AUTO_PROCEED`、`ALLOW_STAGE_SKIP`、`ALLOW_RESUME` 和任何 timeout 设置。即使 `AUTO_PROCEED = true`，stage 间也必须询问用户下一步指示。

---

## Constants

- `WORKSPACE_ROOT = ~/bench_workspace/workspace{i}` —— pipeline 工作区根目录，`i` 为递增编号；每次新运行必须遍历现有目录确定新编号。
- `STAGE1_DIR = ~/bench_workspace/workspace{i}/stage1` — Stage 1 输出目录。
- `STAGE2_DIR = ~/bench_workspace/workspace{i}/stage2` — Stage 2 输出目录。
- `STAGE3_DIR = ~/bench_workspace/workspace{i}/stage3` — Stage 3 输出目录。
- `STAGE4_DIR = ~/bench_workspace/workspace{i}/stage4` — Stage 4 输出目录。
- `STAGE5_DIR = ~/bench_workspace/workspace{i}/stage5` — Stage 5 输出目录。
- `STAGE6_DIR = ~/bench_workspace/workspace{i}/stage6` — Stage 6 输出目录。

- `SIMULATORTS_ROOT = ~/benchclaw/simulators` — 已有仿真器类型 benchmark 根目录。
- `SIMULATOR_CARDS_ROOT = ~/benchclaw/simulator_cards` — 仿真器能力卡片目录。
- `DATASETS_ROOT = ~/benchclaw/datasets` — 已有数据集类型 benchmark 根目录。
- `TEMPLATES_ROOT = ~/benchclaw/templates` — 评测集模板参考目录。
- `MODEL_API_ROOT = ~/benchclaw/model_api` — 待评测模型 API 调用脚本目录。
- `SKILL_REPO_ROOT = ~/benchclaw/skills` — BenchClaw skill 库源码目录。

- `PIPELINE_STATE = ~/bench_workspace/workspace{i}/pipeline_state.json` — 流水线状态文件。
- `PIPELINE_SUMMARY = ~/bench_workspace/workspace{i}/pipeline_summary.md` — 流水线滚动摘要。
- `FINAL_REPORT = ~/bench_workspace/workspace{i}/BENCHMARK_PIPELINE_REPORT.md` — 最终总报告。

- `AUTO_PROCEED = false` — 为 `true` 时允许在非阻塞关卡自动继续；为 `false` 时必须等待用户明确确认。
- `STAGE_TRANSITION_CONFIRMATION_REQUIRED = true` — 每个 stage 完成后必须用选项询问用户下一阶段指示；该常量不可被 `AUTO_PROCEED` 覆盖。
- `ALLOW_STAGE_SKIP = false` — 为 `true` 时允许在产物与测试均通过时跳过阶段；为 `false` 时严格按顺序执行。
- `STRICT_IO_CHECK = true` — 每阶段开始前必须校验上阶段关键产物。
- `UNIT_TEST_REQUIRED_STAGE1_TO_4 = true` — Stage 1-4 必须跑单元测试。
- `CANARY_REQUIRED_BEFORE_FULL_EVAL = true` — Stage 5 全量评测前必须跑灰度评测。
- `FULL_EVAL_BLOCKED_ON_CANARY_FAIL = true` — 灰度失败时禁止全量评测。
- `MAX_RETRY_PER_STAGE = 3` — 单阶段自动重试上限。
- `ALLOW_RESUME = true` — 允许用户要求从最近成功阶段恢复。
- `VERSION_CONTROL_REQUIRED_FOR_SKILL_REVISION = true` — Stage 6 修改 skill 前必须建立 git baseline。
- `BUDGET_AWARE = true` — 跟踪 API 次数、样本量、重试数、耗时和成本。
- `LOCAL_MODEL_API_AWARE = true` — Stage 5 缺少 `MODEL_API_CONFIG.json` 时可读取 `model_api/` 下脚本推导配置。

> Override example: `/benchmark-pipeline "多模态 agent benchmark" — AUTO_PROCEED: false, CANARY_SAMPLE_RATIO: 0.05`

---

## Overview

```text
/benchmark-stage1-draft
→ /benchmark-stage2-data-collect
→ /benchmark-stage3-data-clean
→ /benchmark-stage4-build
→ /benchmark-stage5-eval
→ /benchmark-stage6-diagnosis-maintenance
→ final report
```

Top-level lifecycle mapping:

```text
用户粗糙 idea
→ Stage 1 草稿生成 + 单元测试
→ Stage 2 数据采集 + 单元测试
→ Stage 3 Data-Juicer 清洗 + 单元测试
→ Stage 4 评测集合成与协议设计 + 单元测试
→ Stage 5 灰度评测 → 通过后全量评测；失败则定位回退
→ Stage 6 全流程评价 → 根因定位 → git 版本控制 → 手术刀式 skill 修改 → 回归验证
→ Benchmark Pipeline Report
```

---

## Preconditions

### Required inputs

- 用户给出的 benchmark 粗糙 idea：`$ARGUMENTS`

### Optional inputs

- `~/benchclaw/simulator_cards/` — 仿真器能力卡片目录。
- `~/benchclaw/templates/` — 评测集模板种子目录。
- `~/benchclaw/model_api/` — 模型 API 调用脚本目录。
- `~/benchclaw/skills/` — skill 库源码目录，Stage 6 维护使用。

### Required workspace preparation

若缺失，创建：

- `~/bench_workspace/workspace{i}/`
- `~/bench_workspace/workspace{i}/stage1/`
- `~/bench_workspace/workspace{i}/stage2/`
- `~/bench_workspace/workspace{i}/stage3/`
- `~/bench_workspace/workspace{i}/stage4/`
- `~/bench_workspace/workspace{i}/stage5/`
- `~/bench_workspace/workspace{i}/stage6/`

初始化：

- `~/bench_workspace/workspace{i}/pipeline_state.json`
- `~/bench_workspace/workspace{i}/pipeline_summary.md`

Initial state schema:

```json
{
  "pipeline": "benchmark-pipeline",
  "idea": "$ARGUMENTS",
  "current_stage": "init",
  "completed_stages": [],
  "failed_stage": null,
  "last_error": null,
  "artifacts": {},
  "quality_gates": {
    "stage1_unit_test": null,
    "stage2_unit_test": null,
    "stage3_unit_test": null,
    "stage4_unit_test": null,
    "stage5_canary": null,
    "stage6_regression": null
  },
  "rollback": {
    "required": false,
    "target_stage": null,
    "target_phase": null,
    "target_skill": null,
    "target_artifact": null,
    "invalidate_after_stage": null
  },
  "version_control": {
    "skill_repo_root": "~/benchclaw/skills",
    "branch": null,
    "baseline_commit": null,
    "revision_commit": null
  },
  "started_at": "",
  "updated_at": "",
  "resume_allowed": true
}
```

---

## Pipeline

### Stage 1: 草稿生成 + 单元测试

Invoke:

```text
/benchmark-stage1-draft "$raw_idea"
```

Internal chain:

```text
raw_idea
→ /1-idea-target-refine - 问题扩充重述
→ /2-benchmark-literature-survey - 文献调研
→ /3-benchmark-capability-scope - 能力维度界定
→ /4-benchmark-data-source-selection - 数据源选取
→ /5-benchmark-evalset-prototype-gen - 评测集原型生成
→ /6-benchmark-draft-gen - 草稿生成
→ /7-benchmark-execution-plan-gen - 执行计划生成
→ /8-benchmark-unit-test-stage1 - Stage 1 单元测试
```

**Required output artifacts:**

- `~/bench_workspace/workspace{i}/stage1/IDEA_TARGET.md` - 问题扩充重述文档
- `~/bench_workspace/workspace{i}/stage1/LITERATURE_REVIEW.md` - 文献调研文档
- `~/bench_workspace/workspace{i}/stage1/CAPABILITY_SCOPE.md` - 能力维度界定文档
- `~/bench_workspace/workspace{i}/stage1/DATA_SOURCE_MAPPING.md` - 数据源选取总表
- `~/bench_workspace/workspace{i}/stage1/SIMULATOR_MAPPING.md` - 仿真器映射文档
- `~/bench_workspace/workspace{i}/stage1/DATASET_MAPPING.md` - 已有数据集映射文档
- `~/bench_workspace/workspace{i}/stage1/REALDATA_MAPPING.md` - 真实采集数据映射文档
- `~/bench_workspace/workspace{i}/stage1/EVALSET_PROTOTYPE.md` - 评测集原型文档
- `~/bench_workspace/workspace{i}/stage1/BENCHMARK_DRAFT.md` - 草稿文档
- `~/bench_workspace/workspace{i}/stage1/EXECUTION_PLAN.md` - 执行计划文档
- `~/bench_workspace/workspace{i}/stage1/STAGE1_UNIT_TEST_REPORT.md` - Stage 1 单元测试报告
- `~/bench_workspace/workspace{i}/stage1/STAGE1_SUMMARY.md` - Stage 1 阶段摘要

**Gate 1 — Stage 1 Unit Test Gate:**

- `~/bench_workspace/workspace{i}/stage1/STAGE1_UNIT_TEST_REPORT.md` verdict 为 `PASS` → 可以进入 Stage 2。
- verdict 为 `NEEDS_REVIEW` → 需要用户确认 waiver。
- verdict 为 `FAIL` → 按报告中的 fix target 回退 Stage 1 对应 phase，不得进入 Stage 2。

---

### Stage 2: 数据采集 + 单元测试

Before Stage 2, verify Stage 1 required artifacts and Gate 1 status.

Invoke:

```text
/benchmark-stage2-data-collect "$STAGE1_DIR"
```

Internal chain:

```text
Stage 1 artifacts
→ /1-benchmark-sim-capability-survey - 仿真器能力调研
→ /2-benchmark-collection-guidance - 采集指导生成
→ /3-benchmark-template-refinement - 模板细化
→ /4-benchmark-collect-codegen - 采集脚本生成
→ /5-benchmark-batch-collect - 批量采集执行
→ /6-benchmark-unit-test-stage2 - Stage 2 单元测试
```

**Required output artifacts:**

- `~/bench_workspace/workspace{i}/stage2/SIM_CAPABILITY_SURVEY.md` - 仿真器能力调研文档
- `~/bench_workspace/workspace{i}/stage2/COLLECTION_GUIDANCE.md` - 采集指导文档
- `~/bench_workspace/workspace{i}/stage2/TEMPLATE_REFINEMENT_REPORT.md` - 模板细化报告
- `~/bench_workspace/workspace{i}/stage2/collection_scripts/` - 采集脚本
- `~/bench_workspace/workspace{i}/stage2/collected_data/` - 采集数据
- `~/bench_workspace/workspace{i}/stage2/DATA_SCHEMA.md` - 数据模式文档
- `~/bench_workspace/workspace{i}/stage2/DATA_QUALITY_REPORT.md` - 数据质量报告
- `~/bench_workspace/workspace{i}/stage2/STAGE2_UNIT_TEST_REPORT.md` - Stage 2 单元测试报告
- `~/bench_workspace/workspace{i}/stage2/STAGE2_SUMMARY.md` - Stage 2 阶段摘要

**Gate 2 — Stage 2 Unit Test Gate:**

- `PASS` → 可以进入 Stage 3。
- `NEEDS_REVIEW` → 用户确认 waiver 后才能进入 Stage 3。
- `FAIL` → 根据报告回退到 Stage 2 对应 phase；若数据需求不可实现，回退 Stage 1 data source selection 或 evalset prototype。

---

### Stage 3: Data-Juicer 数据清洗 + 半监督标注 + 单元测试

Before Stage 3, verify Stage 2 required artifacts and Gate 2 status.

Stage 3 必须读取 `~/benchclaw/data-juicer_card/DATAJUICER_AGENT_CAPABILITY_SPEC.md` 作为 Data-Juicer 能力、operator、YAML schema 和 CLI 调用方式的权威依据。若该文件缺失或不可读，不得进入 Data-Juicer 清洗配置与执行。

Invoke:

```text
/benchmark-stage3-data-clean "$STAGE2_DIR"
```

Internal chain:

```text
Stage 2 collected artifacts
→ /1-benchmark-data-cleaning-plan - 数据清洗计划生成
→ /2-benchmark-datajuicer-config-gen - Data-Juicer 配置生成
→ /3-benchmark-datajuicer-run-clean - Data-Juicer 清洗执行
→ /4-benchmark-semisupervised-annotation - 半监督候选标注（按需）
→ /4-benchmark-cleaning-validate - 清洗验证与 final 合并
→ /5-benchmark-unit-test-stage3 - Stage 3 单元测试
```

**Required output artifacts:**

- `~/bench_workspace/workspace{i}/stage3/DATA_CLEANING_PLAN.md` - 数据清洗计划文档
- `~/bench_workspace/workspace{i}/stage3/DATAJUICER_CAPABILITY_SUMMARY.md` 或 `DATA_CLEANING_PLAN.md` 中的 Data-Juicer Capability Summary - 从 capability spec 提取的能力摘要
- `~/bench_workspace/workspace{i}/stage3/datajuicer_configs/` - DataJuicer 配置文件
- `~/bench_workspace/workspace{i}/stage3/DATAJUICER_CONFIG_INDEX.md` - DataJuicer 配置索引文档
- `~/bench_workspace/workspace{i}/stage3/DATAJUICER_RUN_REPORT.md` - DataJuicer 运行报告
- `~/bench_workspace/workspace{i}/stage3/source_work/` - 三类数据源按 source_type/source_name 分开的中间产物
- `~/bench_workspace/workspace{i}/stage3/ANNOTATION_TOOL_RUN_REPORT.md` - 半监督工具运行报告（按需）
- `~/bench_workspace/workspace{i}/stage3/final/STAGE4_INPUT_MANIFEST.jsonl` - Stage 4 权威输入索引
- `~/bench_workspace/workspace{i}/stage3/final/cleaned_data/` - 合并后的清洗数据
- `~/bench_workspace/workspace{i}/stage3/final/rejected_samples/` - 合并后的拒绝样本
- `~/bench_workspace/workspace{i}/stage3/final/CLEANING_LINEAGE.jsonl` - 合并后的清洗血缘关系
- `~/bench_workspace/workspace{i}/stage3/final/CLEANED_DATA_SCHEMA.md` - Stage 4 输入 schema
- `~/bench_workspace/workspace{i}/stage3/CLEANING_QUALITY_REPORT.md` - 清洗质量报告
- `~/bench_workspace/workspace{i}/stage3/STAGE3_UNIT_TEST_REPORT.md` - Stage 3 单元测试报告
- `~/bench_workspace/workspace{i}/stage3/STAGE3_SUMMARY.md` - Stage 3 阶段摘要

**Gate 3 — Stage 3 Unit Test Gate:**

- `PASS` → 可以进入 Stage 4。
- `NEEDS_REVIEW` → 用户确认 waiver 后才能进入 Stage 4。
- `FAIL` → 根据报告回退到 Stage 3 清洗计划、配置、执行或验证；若原始数据有缺陷，回退 Stage 2。

---

### Stage 4: 评测集合成与协议设计 + 单元测试

Before Stage 4, verify Stage 3 required artifacts and Gate 3 status.

Invoke:

```text
/benchmark-stage4-build "$STAGE3_DIR"
```

Internal chain:

```text
Stage 1 scope + Stage 2 templates + Stage 3 cleaned data
→ /1-benchmark-evalset-generate - 评测集生成
→ /2-benchmark-metric-establish - 指标建立
→ /3-benchmark-validate-stage4 - Stage 4 验证
→ /4-benchmark-unit-test-stage4 - Stage 4 单元测试
```

**Required output artifacts:**

- `~/bench_workspace/workspace{i}/stage4/EVALSET_TEMPLATE_LIBRARY/` - 评测集模板库
- `~/bench_workspace/workspace{i}/stage4/EVALSET_SYNTHESIS_RULES.md` - 评测集合成规则
- `~/bench_workspace/workspace{i}/stage4/EVALSET_DATASET/` - 评测集数据集
- `~/bench_workspace/workspace{i}/stage4/EVALSET_SCHEMA.md` - 评测集模式文档
- `~/bench_workspace/workspace{i}/stage4/CAPABILITY_METRIC_MAP.md` - 能力指标映射文档
- `~/bench_workspace/workspace{i}/stage4/METRIC_SPEC.md` - 指标规范文档
- `~/bench_workspace/workspace{i}/stage4/SCORING_RULES.md` - 评分规则文档
- `~/bench_workspace/workspace{i}/stage4/METRIC_LIBRARY/` - 指标库
- `~/bench_workspace/workspace{i}/stage4/VALIDATION_REPORT.md` - 验证报告
- `~/bench_workspace/workspace{i}/stage4/DRY_RUN_RESULTS.md` - 预演结果文档
- `~/bench_workspace/workspace{i}/stage4/STAGE4_UNIT_TEST_REPORT.md` - Stage 4 单元测试报告
- `~/bench_workspace/workspace{i}/stage4/STAGE4_SUMMARY.md` - Stage 4 阶段摘要

**Gate 4 — Stage 4 Unit Test Gate:**

- `PASS` → 可以进入 Stage 5 灰度评测。
- `NEEDS_REVIEW` → 用户确认 waiver 后才能进入 Stage 5。
- `FAIL` → 根据报告回退 Stage 4 合成、指标或验证；若 cleaned data 字段不足，回退 Stage 3。

---

### Stage 5: 灰度评测 → 全量评测

Before Stage 5, verify Stage 1-4 unit test gates and Stage 4 validation status.

Invoke:

```text
/benchmark-stage5-eval "$MODEL_API_CONFIG_OR_STAGE4_DIR"
```

Internal chain:

```text
Stage 4 evalset + metrics + model API config
→ /1-benchmark-build-eval-system-prompt
→ /2-benchmark-canary-eval
→ if FAIL: /3-benchmark-canary-localize-rollback → stop and rollback
→ if PASS: /4-benchmark-call-model-api
→ /5-benchmark-run-metrics
→ /6-benchmark-check-scores
```

**Required output artifacts if canary runs:**

- `~/bench_workspace/workspace{i}/stage5/EVAL_SYSTEM_PROMPT.md` - 评测系统提示
- `~/bench_workspace/workspace{i}/stage5/RUN_CONFIG.json` - 运行配置
- `~/bench_workspace/workspace{i}/stage5/MODEL_API_CONFIG.snapshot.json` - 模型 API 配置快照
- `~/bench_workspace/workspace{i}/stage5/CANARY_SAMPLE_MANIFEST.jsonl` - 灰度样本清单
- `~/bench_workspace/workspace{i}/stage5/CANARY_RAW_OUTPUTS.jsonl` - 灰度原始输出
- `~/bench_workspace/workspace{i}/stage5/CANARY_METRICS.json` - 灰度指标
- `~/bench_workspace/workspace{i}/stage5/CANARY_VERDICT.json` - 灰度判决
- `~/bench_workspace/workspace{i}/stage5/CANARY_EVAL_REPORT.md` - 灰度评测报告

**Additional artifacts if canary fails:**

- `~/bench_workspace/workspace{i}/stage5/CANARY_ROLLBACK_PLAN.md` - 灰度回退计划
- `~/bench_workspace/workspace{i}/stage5/ROLLBACK_STATE_PATCH.json` - 回退状态补丁

**Additional artifacts if canary passes and full eval runs:**

- `~/bench_workspace/workspace{i}/stage5/RAW_MODEL_OUTPUTS.jsonl` - 原始模型输出
- `~/bench_workspace/workspace{i}/stage5/API_RUN_SUMMARY.json` - API 运行摘要
- `~/bench_workspace/workspace{i}/stage5/SCORES.jsonl` - 评分结果
- `~/bench_workspace/workspace{i}/stage5/AGGREGATED_METRICS.json` - 聚合指标
- `~/bench_workspace/workspace{i}/stage5/DIMENSION_WISE_ANALYSIS.md` - 维度分析报告
- `~/bench_workspace/workspace{i}/stage5/SCORE_CHECK_REPORT.md` - 评分检查报告
- `~/bench_workspace/workspace{i}/stage5/FAILURE_CASES.md` - 失败案例分析
- `~/bench_workspace/workspace{i}/stage5/EVALUATION_REPORT.md` - 评测报告
- `~/bench_workspace/workspace{i}/stage5/STAGE5_SUMMARY.md` - Stage 5 阶段摘要

**Gate 5A — Canary Gate:**

- `PASS` → 可以进入全量评测。
- `NEEDS_REVIEW` → 必须用户确认 waiver，否则不得全量。
- `FAIL` → 必须执行 `/benchmark-canary-localize-rollback`，合并 `ROLLBACK_STATE_PATCH.json` 到 `pipeline_state.json`，然后停止。不得启动全量评测。

**灰度失败回退规则：**

1. 将 `pipeline_state.current_stage` 设置为 `rollback_required`。
2. 记录 `rollback.target_stage/phase/skill/artifact`。
3. 标记 `invalidate_after_stage`，说明哪些下游产物必须废弃并重跑。
4. 向用户展示 `CANARY_ROLLBACK_PLAN.md`。
5. 等用户确认后，从最小回退点重跑，而不是从头无脑重跑。

---

### Stage 6: 全流程评价、根因定位、版本化 skill 维护

Stage 6 可在两种情况下运行：

- **post-full-eval mode**：Stage 5 全量评测完成后，做完整流程复盘和 skill 维护。
- **rollback-diagnosis mode**：Stage 5 灰度失败或全量中断后，先做根因定位和 skill 修改建议。

Invoke:

```text
/benchmark-stage6-diagnosis-maintenance "$WORKSPACE_ROOT"
```

Internal chain:

```text
Stage 1-5 artifacts + unit tests + canary/full eval evidence
→ /benchmark-process-evaluate - 全流程过程评价
→ /benchmark-root-cause-analyze - 根因分析
→ /benchmark-skill-version-control - git baseline 和 revision 管理
→ /benchmark-skill-surgical-revision - 手术刀式 skill 修改建议
→ /benchmark-skill-regression-verify - 回归验证
```

**Required output artifacts:**

- `~/bench_workspace/workspace{i}/stage6/PROCESS_EVALUATION_REPORT.md` - 全流程过程评价报告
- `~/bench_workspace/workspace{i}/stage6/PROCESS_METRICS.json` - 全流程过程指标
- `~/bench_workspace/workspace{i}/stage6/ROOT_CAUSE_ANALYSIS.md` - 根因分析报告
- `~/bench_workspace/workspace{i}/stage6/DEFECT_TRIAGE_MATRIX.json` - 缺陷分类矩阵
- `~/bench_workspace/workspace{i}/stage6/SKILL_FIX_CANDIDATES.md` - Skill 修复候选列表
- `~/bench_workspace/workspace{i}/stage6/VERSION_CONTROL_LOG.md` - 版本控制日志
- `~/bench_workspace/workspace{i}/stage6/SKILL_BASELINE_MANIFEST.json` - Skill baseline 清单
- `~/bench_workspace/workspace{i}/stage6/ALLOWED_SKILL_EDIT_LIST.txt` - 允许的 Skill 修改列表
- `~/bench_workspace/workspace{i}/stage6/SKILL_REVISION_PLAN.md` - Skill 修改计划
- `~/bench_workspace/workspace{i}/stage6/SKILL_PATCH.diff` - Skill 补丁
- `~/bench_workspace/workspace{i}/stage6/SKILL_CHANGELOG.md` - Skill 变更日志
- `~/bench_workspace/workspace{i}/stage6/SKILL_REGRESSION_REPORT.md` - Skill 回归报告
- `~/bench_workspace/workspace{i}/stage6/STAGE6_SUMMARY.md` - Stage 6 阶段摘要

**Gate 6 — Skill Revision Gate:**

- 修改 skill 前必须有 git baseline 和 revision branch。
- 修改范围必须被 `SKILL_FIX_CANDIDATES.md` 和 `ALLOWED_SKILL_EDIT_LIST.txt` 限制。
- 回归验证 `PASS` 后才允许 commit/tag。
- 回归验证非 PASS 时保留 patch，不提交。

---

## Cross-Stage Rollback Protocol

当任一 quality gate 失败时，按以下规则处理：

1. **精确定位**：必须定位到 stage、phase、skill、artifact。
2. **最小回退**：优先回退到最小责任 skill，不从头重跑。
3. **下游失效**：从回退目标之后的产物全部标记为 invalidated。
4. **重跑顺序**：修复目标 → 对应 stage unit test → 下游 stage → Stage 5 canary。
5. **状态记录**：所有回退都写入 `pipeline_state.json.rollback` 和 `pipeline_summary.md`。
6. **Skill 问题延迟到 Stage 6 修改**：运行中发现是 skill 规则缺陷时，先记录到 `skill_revision_candidates`；不要在 Stage 1-5 中私自改 skill 源码。

---

## Final Report

At the end, write `BENCHMARK_PIPELINE_REPORT.md`:

```markdown
# Benchmark Pipeline Report

## Executive Summary
[benchmark 构建、清洗、评测、诊断维护总体结果]

## Stage Outcomes
| Stage | Main Output | Unit/Canary/Regression Gate | Verdict | Notes |
|-------|-------------|-----------------------------|---------|-------|

## Rollbacks and Re-runs
[所有回退、废弃产物、重跑范围]

## Evaluation Results
[模型评测结果；如灰度失败则说明未全量]

## Process Evaluation
[Stage 6 过程评价摘要]

## Root Causes and Skill Revisions
[根因、修改文件、git branch/commit/tag、回归结果]

## Artifacts
[关键路径清单]

## Next Iteration
[下一轮 benchmark pipeline 的改进建议]
```

---

## Completion Criteria

- [ ] Stage 1-4 均有单元测试报告并被质量门读取。
- [ ] Stage 5 全量评测前存在灰度报告和 verdict。
- [ ] 灰度 FAIL 时不存在新生成的全量评测输出。
- [ ] 灰度 FAIL 时存在回退计划并写入 pipeline state。
- [ ] Stage 6 输出全流程评价、根因分析、版本控制日志、skill patch/changelog 和回归报告。
- [ ] 最终报告包含完整 artifact 清单和下一轮维护建议。

---

## Rules

- 不得跳过 Stage 1-4 单元测试直接进入下游阶段。
- 不得跳过 Stage 5 灰度评测直接全量评测。
- 每完成一个 stage 后，必须暂停并用选项询问用户下一阶段指示；不得自动进入下一 stage。
- stage 间选项至少包括：继续下一阶段、暂停在当前阶段、查看/总结当前阶段结果、回退或重跑当前阶段、修改指令后继续。
- 若当前 stage verdict 为 `FAIL`，不得提供可执行的“继续下一阶段”选项。
- 灰度失败时不得继续全量评测。
- Stage 6 修改 skill 必须经过 git baseline、白名单、diff、回归验证。
- 如果 Write 因文件过大失败，立即 fallback 到 Bash（`cat << 'EOF' > file`）分块写入。
